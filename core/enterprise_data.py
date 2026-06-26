"""Enterprise data foundation tools for agent grounding and governance.

This module intentionally stays dependency-free. It gives CLAI a durable local
data foundation with interfaces that can later be backed by Neo4j, pgvector,
OpenSearch, Milvus, Weaviate, Pinecone, or enterprise metadata catalogs.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from config import get_settings
from core.metrics import COST_TABLE
from core.tool_registry import ToolParameter, ToolRegistry


SENSITIVITY_ORDER = ("public", "internal", "confidential", "restricted")
ROLE_CLEARANCE = {
    "ba": "internal",
    "qa": "confidential",
    "coder": "confidential",
    "coder_2": "confidential",
    "coder_3": "confidential",
    "senior_dev": "restricted",
    "reviewer": "restricted",
}


def _now() -> float:
    return time.time()


def _normalize_sensitivity(value: str) -> str:
    value = (value or "internal").strip().lower()
    return value if value in SENSITIVITY_ORDER else "internal"


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9][a-z0-9_./:-]*", (text or "").lower())


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text or "") / 4))


@dataclass
class GovernanceDecision:
    allowed: bool
    reason: str
    actor: str
    sensitivity: str


class EnterpriseDataFoundation:
    """Durable local catalog, graph, memory, search index, and audit log."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.catalog_path = self.root / "catalog.json"
        self.graph_path = self.root / "knowledge_graph.json"
        self.index_path = self.root / "semantic_index.json"
        self.memory_path = self.root / "agent_memory.json"
        self.checkpoint_path = self.root / "workflow_checkpoints.json"
        self.prompt_cache_path = self.root / "prompt_cache.json"
        self.audit_path = self.root / "audit.jsonl"

    def _load(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _save(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f"{path.suffix}.tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)

    def _clearance_allows(self, actor: str, sensitivity: str) -> bool:
        clearance = ROLE_CLEARANCE.get(actor, "internal")
        return SENSITIVITY_ORDER.index(clearance) >= SENSITIVITY_ORDER.index(sensitivity)

    def governance_check(
        self,
        actor: str,
        action: str,
        resource: str,
        sensitivity: str = "internal",
        purpose: str = "",
    ) -> GovernanceDecision:
        sensitivity = _normalize_sensitivity(sensitivity)
        allowed = self._clearance_allows(actor, sensitivity)
        if action.startswith("delete") and actor not in ("senior_dev", "reviewer"):
            allowed = False
            reason = "Only senior_dev or reviewer can approve destructive actions."
        elif allowed:
            reason = f"{actor} clearance permits {sensitivity} access."
        else:
            reason = f"{actor} clearance does not permit {sensitivity} access."

        self.audit(
            actor=actor,
            action=action,
            resource=resource,
            allowed=allowed,
            details={"sensitivity": sensitivity, "purpose": purpose, "reason": reason},
        )
        return GovernanceDecision(allowed=allowed, reason=reason, actor=actor, sensitivity=sensitivity)

    def audit(
        self,
        actor: str,
        action: str,
        resource: str,
        allowed: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = {
            "timestamp": _now(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "allowed": allowed,
            "details": details or {},
        }
        with self._lock:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def audit_tail(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.audit_path.exists():
            return []
        lines = self.audit_path.read_text(encoding="utf-8").splitlines()[-max(1, min(limit, 200)) :]
        events: List[Dict[str, Any]] = []
        for line in lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    def register_source(
        self,
        actor: str,
        name: str,
        source_type: str,
        location: str,
        description: str = "",
        owner: str = "",
        sensitivity: str = "internal",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        sensitivity = _normalize_sensitivity(sensitivity)
        decision = self.governance_check(actor, "catalog.register", name, sensitivity, "metadata registration")
        if not decision.allowed:
            return {"ok": False, "reason": decision.reason}

        source_id = hashlib.sha1(f"{name}|{location}".encode("utf-8")).hexdigest()[:12]
        entry = {
            "id": source_id,
            "name": name.strip(),
            "source_type": source_type.strip().lower(),
            "location": location.strip(),
            "description": description.strip(),
            "owner": owner.strip(),
            "sensitivity": sensitivity,
            "tags": sorted(set(tags or [])),
            "updated_at": _now(),
            "updated_by": actor,
        }
        with self._lock:
            catalog = self._load(self.catalog_path, {})
            catalog[source_id] = entry
            self._save(self.catalog_path, catalog)
        self.audit(actor, "catalog.registered", source_id, True, {"name": name})
        return {"ok": True, "source": entry}

    def search_sources(self, actor: str, query: str, limit: int = 10) -> Dict[str, Any]:
        q = Counter(_tokenize(query))
        with self._lock:
            entries = list(self._load(self.catalog_path, {}).values())
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for entry in entries:
            sensitivity = _normalize_sensitivity(entry.get("sensitivity", "internal"))
            if not self._clearance_allows(actor, sensitivity):
                continue
            haystack = " ".join(
                str(entry.get(k, "")) for k in ("name", "source_type", "location", "description", "owner")
            )
            haystack += " " + " ".join(entry.get("tags", []))
            score = _cosine(q, Counter(_tokenize(haystack)))
            if score > 0 or not query.strip():
                scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = [{"score": round(score, 4), **entry} for score, entry in scored[: max(1, min(limit, 50))]]
        self.audit(actor, "catalog.search", query[:120], True, {"results": len(results)})
        return {"results": results}

    def upsert_fact(
        self,
        actor: str,
        subject: str,
        predicate: str,
        obj: str,
        source: str = "",
        confidence: float = 0.8,
        sensitivity: str = "internal",
    ) -> Dict[str, Any]:
        sensitivity = _normalize_sensitivity(sensitivity)
        decision = self.governance_check(actor, "graph.upsert", subject, sensitivity, "knowledge graph write")
        if not decision.allowed:
            return {"ok": False, "reason": decision.reason}
        fact_id = hashlib.sha1(f"{subject}|{predicate}|{obj}|{source}".encode("utf-8")).hexdigest()[:16]
        fact = {
            "id": fact_id,
            "subject": subject.strip(),
            "predicate": predicate.strip(),
            "object": obj.strip(),
            "source": source.strip(),
            "confidence": max(0.0, min(float(confidence), 1.0)),
            "sensitivity": sensitivity,
            "updated_at": _now(),
            "updated_by": actor,
        }
        with self._lock:
            graph = self._load(self.graph_path, {"facts": []})
            facts = [f for f in graph.get("facts", []) if f.get("id") != fact_id]
            facts.append(fact)
            graph["facts"] = facts
            self._save(self.graph_path, graph)
        self.audit(actor, "graph.fact_upserted", fact_id, True, {"subject": subject, "predicate": predicate})
        return {"ok": True, "fact": fact}

    def query_graph(self, actor: str, entity: str, limit: int = 20) -> Dict[str, Any]:
        entity_l = entity.strip().lower()
        with self._lock:
            facts = self._load(self.graph_path, {"facts": []}).get("facts", [])
        results = []
        for fact in facts:
            sensitivity = _normalize_sensitivity(fact.get("sensitivity", "internal"))
            if not self._clearance_allows(actor, sensitivity):
                continue
            if (
                entity_l in fact.get("subject", "").lower()
                or entity_l in fact.get("object", "").lower()
                or entity_l in fact.get("predicate", "").lower()
            ):
                results.append(fact)
        results.sort(key=lambda f: (f.get("confidence", 0), f.get("updated_at", 0)), reverse=True)
        results = results[: max(1, min(limit, 100))]
        self.audit(actor, "graph.query", entity[:120], True, {"results": len(results)})
        return {"facts": results}

    def index_document(
        self,
        actor: str,
        doc_id: str,
        title: str,
        content: str,
        source: str = "",
        sensitivity: str = "internal",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        sensitivity = _normalize_sensitivity(sensitivity)
        decision = self.governance_check(actor, "semantic.index", doc_id, sensitivity, "grounding document index")
        if not decision.allowed:
            return {"ok": False, "reason": decision.reason}
        tokens = Counter(_tokenize(f"{title}\n{content}\n{' '.join(tags or [])}"))
        document = {
            "doc_id": doc_id.strip(),
            "title": title.strip(),
            "content": content.strip(),
            "source": source.strip(),
            "sensitivity": sensitivity,
            "tags": sorted(set(tags or [])),
            "token_counts": dict(tokens),
            "updated_at": _now(),
            "updated_by": actor,
        }
        with self._lock:
            index = self._load(self.index_path, {"documents": []})
            docs = [d for d in index.get("documents", []) if d.get("doc_id") != document["doc_id"]]
            docs.append(document)
            index["documents"] = docs
            self._save(self.index_path, index)
        self.audit(actor, "semantic.indexed", document["doc_id"], True, {"tokens": sum(tokens.values())})
        return {"ok": True, "doc_id": document["doc_id"], "tokens": sum(tokens.values())}

    def semantic_search(self, actor: str, query: str, limit: int = 5) -> Dict[str, Any]:
        q = Counter(_tokenize(query))
        with self._lock:
            docs = self._load(self.index_path, {"documents": []}).get("documents", [])
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for doc in docs:
            sensitivity = _normalize_sensitivity(doc.get("sensitivity", "internal"))
            if not self._clearance_allows(actor, sensitivity):
                continue
            score = _cosine(q, Counter(doc.get("token_counts", {})))
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, doc in scored[: max(1, min(limit, 25))]:
            content = doc.get("content", "")
            results.append(
                {
                    "score": round(score, 4),
                    "doc_id": doc.get("doc_id"),
                    "title": doc.get("title"),
                    "source": doc.get("source"),
                    "sensitivity": doc.get("sensitivity"),
                    "tags": doc.get("tags", []),
                    "snippet": content[:900],
                }
            )
        self.audit(actor, "semantic.search", query[:120], True, {"results": len(results)})
        return {"results": results}

    def write_memory(
        self,
        actor: str,
        namespace: str,
        key: str,
        value: str,
        sensitivity: str = "internal",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        sensitivity = _normalize_sensitivity(sensitivity)
        decision = self.governance_check(actor, "memory.write", f"{namespace}/{key}", sensitivity, "agent memory")
        if not decision.allowed:
            return {"ok": False, "reason": decision.reason}
        entry = {
            "namespace": namespace.strip() or "default",
            "key": key.strip(),
            "value": value,
            "sensitivity": sensitivity,
            "tags": sorted(set(tags or [])),
            "updated_at": _now(),
            "updated_by": actor,
        }
        with self._lock:
            memory = self._load(self.memory_path, {})
            memory.setdefault(entry["namespace"], {})[entry["key"]] = entry
            self._save(self.memory_path, memory)
        self.audit(actor, "memory.written", f"{entry['namespace']}/{entry['key']}", True)
        return {"ok": True, "memory": entry}

    def search_memory(self, actor: str, query: str, namespace: str = "", limit: int = 10) -> Dict[str, Any]:
        q = Counter(_tokenize(query))
        with self._lock:
            memory = self._load(self.memory_path, {})
        pools: Iterable[Dict[str, Any]]
        if namespace:
            pools = memory.get(namespace, {}).values()
        else:
            pools = (entry for ns in memory.values() for entry in ns.values())
        scored = []
        for entry in pools:
            sensitivity = _normalize_sensitivity(entry.get("sensitivity", "internal"))
            if not self._clearance_allows(actor, sensitivity):
                continue
            text = f"{entry.get('namespace')} {entry.get('key')} {entry.get('value')} {' '.join(entry.get('tags', []))}"
            score = _cosine(q, Counter(_tokenize(text)))
            if score > 0 or not query.strip():
                scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = [{"score": round(score, 4), **entry} for score, entry in scored[: max(1, min(limit, 50))]]
        self.audit(actor, "memory.search", query[:120], True, {"results": len(results), "namespace": namespace})
        return {"results": results}

    def write_checkpoint(
        self,
        actor: str,
        workflow_id: str,
        step: str,
        state: str,
        status: str = "in_progress",
    ) -> Dict[str, Any]:
        checkpoint = {
            "workflow_id": workflow_id.strip(),
            "step": step.strip(),
            "state": state,
            "status": status.strip() or "in_progress",
            "updated_at": _now(),
            "updated_by": actor,
        }
        with self._lock:
            data = self._load(self.checkpoint_path, {})
            data.setdefault(checkpoint["workflow_id"], {})[checkpoint["step"]] = checkpoint
            self._save(self.checkpoint_path, data)
        self.audit(actor, "workflow.checkpoint_written", f"{workflow_id}/{step}", True, {"status": status})
        return {"ok": True, "checkpoint": checkpoint}

    def list_checkpoints(self, actor: str, workflow_id: str = "") -> Dict[str, Any]:
        with self._lock:
            data = self._load(self.checkpoint_path, {})
        result = data.get(workflow_id, {}) if workflow_id else data
        self.audit(actor, "workflow.checkpoint_list", workflow_id or "*", True)
        return {"checkpoints": result}

    def prompt_cache_key(self, prompt: str, model: str, namespace: str = "default") -> str:
        digest = hashlib.sha256(f"{namespace}\n{model}\n{prompt}".encode("utf-8")).hexdigest()
        return digest[:24]

    def cache_lookup(self, actor: str, prompt: str, model: str, namespace: str = "default") -> Dict[str, Any]:
        key = self.prompt_cache_key(prompt, model, namespace)
        with self._lock:
            cache = self._load(self.prompt_cache_path, {})
        entry = cache.get(key)
        self.audit(actor, "prompt_cache.lookup", key, bool(entry), {"namespace": namespace, "model": model})
        return {"hit": bool(entry), "key": key, "entry": entry}

    def cache_store(
        self,
        actor: str,
        prompt: str,
        model: str,
        response: str,
        namespace: str = "default",
    ) -> Dict[str, Any]:
        key = self.prompt_cache_key(prompt, model, namespace)
        entry = {
            "key": key,
            "namespace": namespace,
            "model": model,
            "prompt_preview": prompt[:500],
            "response": response,
            "updated_at": _now(),
            "updated_by": actor,
        }
        with self._lock:
            cache = self._load(self.prompt_cache_path, {})
            cache[key] = entry
            self._save(self.prompt_cache_path, cache)
        self.audit(actor, "prompt_cache.store", key, True, {"namespace": namespace, "model": model})
        return {"ok": True, "key": key}


_FOUNDATIONS: Dict[str, EnterpriseDataFoundation] = {}
_FOUNDATIONS_LOCK = threading.Lock()


def get_enterprise_data_foundation(root: Optional[Path] = None) -> EnterpriseDataFoundation:
    if root is None:
        settings = get_settings()
        root = settings.workspace_path / settings.enterprise_data_dir
    resolved = str(root.resolve())
    with _FOUNDATIONS_LOCK:
        if resolved not in _FOUNDATIONS:
            _FOUNDATIONS[resolved] = EnterpriseDataFoundation(Path(resolved))
        return _FOUNDATIONS[resolved]


def _split_tags(tags: str) -> List[str]:
    return [tag.strip() for tag in (tags or "").split(",") if tag.strip()]


def _cost_estimate(model: str, prompt: str, expected_output_tokens: int) -> Dict[str, Any]:
    input_tokens = _estimate_tokens(prompt)
    output_tokens = max(0, int(expected_output_tokens))
    input_rate, output_rate = COST_TABLE.get(model, (0.003, 0.015))
    cost = (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)
    return {
        "model": model,
        "estimated_input_tokens": input_tokens,
        "expected_output_tokens": output_tokens,
        "estimated_cost_usd": round(cost, 6),
    }


def _recommend_model(task_type: str, quality: str, max_cost_usd: float, prompt: str) -> Dict[str, Any]:
    task = (task_type or "general").lower()
    quality = (quality or "balanced").lower()
    if "architecture" in task or "reason" in task:
        candidates = ["claude-opus-4-8", "claude-sonnet-4-6", "gpt-5.5", "gemini-3.1-pro-preview"]
    elif "qa" in task or "test" in task or quality == "economy":
        candidates = ["gemini-3.5-flash", "gpt-5.4-mini", "claude-sonnet-4-6"]
    elif "code" in task:
        candidates = ["claude-sonnet-4-6", "gemini-3.1-pro-preview", "gpt-5.5"]
    else:
        candidates = ["gpt-5.4-mini", "gemini-3.5-flash", "claude-sonnet-4-6", "gpt-5.5"]

    estimates = [_cost_estimate(model, prompt, 1000) for model in candidates]
    affordable = [item for item in estimates if item["estimated_cost_usd"] <= max_cost_usd]
    choice = affordable[0] if affordable else min(estimates, key=lambda item: item["estimated_cost_usd"])
    return {
        "recommended_model": choice["model"],
        "reason": "Selected for task fit within budget." if affordable else "No candidate fit budget; selected lowest estimated cost.",
        "candidates": estimates,
    }


def build_enterprise_data_registry(
    foundation: Optional[EnterpriseDataFoundation],
    role_name: str,
) -> ToolRegistry:
    foundation = foundation or get_enterprise_data_foundation()
    registry = ToolRegistry()

    registry.register(
        name="data_source_register",
        description="Register an enterprise data source in the local metadata catalog with governance tags.",
        parameters=[
            ToolParameter("name", "string", "Human-readable source name", required=True),
            ToolParameter("source_type", "string", "database, api, document, tool, stream, graph, vector_store, etc.", required=True),
            ToolParameter("location", "string", "URI, path, API base URL, table name, or system identifier", required=True),
            ToolParameter("description", "string", "What business knowledge this source contains", required=False),
            ToolParameter("owner", "string", "Business or technical owner", required=False),
            ToolParameter("sensitivity", "string", "public, internal, confidential, restricted", required=False, enum=list(SENSITIVITY_ORDER)),
            ToolParameter("tags", "string", "Comma-separated tags", required=False),
        ],
        handler=lambda name, source_type, location, description="", owner="", sensitivity="internal", tags="": foundation.register_source(
            role_name, name, source_type, location, description, owner, sensitivity, _split_tags(tags)
        ),
    )

    registry.register(
        name="data_source_search",
        description="Search the metadata catalog for authoritative data sources available to this role.",
        parameters=[
            ToolParameter("query", "string", "Search query", required=True),
            ToolParameter("limit", "integer", "Maximum results", required=False),
        ],
        handler=lambda query, limit=10: foundation.search_sources(role_name, query, limit),
    )

    registry.register(
        name="knowledge_fact_upsert",
        description="Add or update a subject-predicate-object fact in the local knowledge graph.",
        parameters=[
            ToolParameter("subject", "string", "Entity or concept", required=True),
            ToolParameter("predicate", "string", "Relationship type", required=True),
            ToolParameter("object", "string", "Related entity, value, or concept", required=True),
            ToolParameter("source", "string", "Source system, document, or evidence", required=False),
            ToolParameter("confidence", "number", "0.0 to 1.0 confidence score", required=False),
            ToolParameter("sensitivity", "string", "public, internal, confidential, restricted", required=False, enum=list(SENSITIVITY_ORDER)),
        ],
        handler=lambda subject, predicate, object, source="", confidence=0.8, sensitivity="internal": foundation.upsert_fact(
            role_name, subject, predicate, object, source, confidence, sensitivity
        ),
    )

    registry.register(
        name="knowledge_graph_query",
        description="Query knowledge graph facts by entity, relation, or object text.",
        parameters=[
            ToolParameter("entity", "string", "Entity/relation/object search text", required=True),
            ToolParameter("limit", "integer", "Maximum facts", required=False),
        ],
        handler=lambda entity, limit=20: foundation.query_graph(role_name, entity, limit),
    )

    registry.register(
        name="semantic_document_index",
        description="Index a grounding document for retrieval. Stores local lexical vectors until an external vector DB is configured.",
        parameters=[
            ToolParameter("doc_id", "string", "Stable document ID", required=True),
            ToolParameter("title", "string", "Document title", required=True),
            ToolParameter("content", "string", "Document text to index", required=True),
            ToolParameter("source", "string", "Source URI/path/reference", required=False),
            ToolParameter("sensitivity", "string", "public, internal, confidential, restricted", required=False, enum=list(SENSITIVITY_ORDER)),
            ToolParameter("tags", "string", "Comma-separated tags", required=False),
        ],
        handler=lambda doc_id, title, content, source="", sensitivity="internal", tags="": foundation.index_document(
            role_name, doc_id, title, content, source, sensitivity, _split_tags(tags)
        ),
    )

    registry.register(
        name="semantic_search",
        description="Retrieve grounded snippets from indexed enterprise documents available to this role.",
        parameters=[
            ToolParameter("query", "string", "Search query", required=True),
            ToolParameter("limit", "integer", "Maximum snippets", required=False),
        ],
        handler=lambda query, limit=5: foundation.semantic_search(role_name, query, limit),
    )

    registry.register(
        name="agent_memory_write",
        description="Persist cross-session agent memory for decisions, user preferences, project facts, and long-running workflows.",
        parameters=[
            ToolParameter("namespace", "string", "Memory namespace such as project name or workflow ID", required=True),
            ToolParameter("key", "string", "Memory key", required=True),
            ToolParameter("value", "string", "Memory value", required=True),
            ToolParameter("sensitivity", "string", "public, internal, confidential, restricted", required=False, enum=list(SENSITIVITY_ORDER)),
            ToolParameter("tags", "string", "Comma-separated tags", required=False),
        ],
        handler=lambda namespace, key, value, sensitivity="internal", tags="": foundation.write_memory(
            role_name, namespace, key, value, sensitivity, _split_tags(tags)
        ),
    )

    registry.register(
        name="agent_memory_search",
        description="Search durable cross-session agent memory visible to this role.",
        parameters=[
            ToolParameter("query", "string", "Search query", required=True),
            ToolParameter("namespace", "string", "Optional namespace filter", required=False),
            ToolParameter("limit", "integer", "Maximum memories", required=False),
        ],
        handler=lambda query, namespace="", limit=10: foundation.search_memory(role_name, query, namespace, limit),
    )

    registry.register(
        name="workflow_checkpoint_write",
        description="Persist workflow state for recovery and long-running multi-step agent workflows.",
        parameters=[
            ToolParameter("workflow_id", "string", "Workflow/session/project identifier", required=True),
            ToolParameter("step", "string", "Step name", required=True),
            ToolParameter("state", "string", "JSON or text state needed to resume", required=True),
            ToolParameter("status", "string", "in_progress, blocked, complete, failed", required=False),
        ],
        handler=lambda workflow_id, step, state, status="in_progress": foundation.write_checkpoint(
            role_name, workflow_id, step, state, status
        ),
    )

    registry.register(
        name="workflow_checkpoint_list",
        description="List persisted workflow checkpoints for recovery or handoff.",
        parameters=[
            ToolParameter("workflow_id", "string", "Optional workflow ID", required=False),
        ],
        handler=lambda workflow_id="": foundation.list_checkpoints(role_name, workflow_id),
    )

    registry.register(
        name="governance_check",
        description="Check whether a data access/tool action is allowed for this role and write an audit event.",
        parameters=[
            ToolParameter("action", "string", "Planned action, e.g. read.customer_table or tool.invoke", required=True),
            ToolParameter("resource", "string", "Resource name/path/source/tool", required=True),
            ToolParameter("sensitivity", "string", "public, internal, confidential, restricted", required=False, enum=list(SENSITIVITY_ORDER)),
            ToolParameter("purpose", "string", "Business reason for the action", required=False),
        ],
        handler=lambda action, resource, sensitivity="internal", purpose="": foundation.governance_check(
            role_name, action, resource, sensitivity, purpose
        ).__dict__,
    )

    registry.register(
        name="audit_log_tail",
        description="Read recent governance, catalog, memory, retrieval, and cache audit events.",
        parameters=[
            ToolParameter("limit", "integer", "Maximum events", required=False),
        ],
        handler=lambda limit=20: {"events": foundation.audit_tail(limit)},
    )

    registry.register(
        name="cost_estimate",
        description="Estimate LLM cost for a prompt/model before running an expensive step.",
        parameters=[
            ToolParameter("model", "string", "Model ID to estimate", required=True),
            ToolParameter("prompt", "string", "Prompt text", required=True),
            ToolParameter("expected_output_tokens", "integer", "Expected completion tokens", required=False),
        ],
        handler=lambda model, prompt, expected_output_tokens=1000: _cost_estimate(
            model, prompt, expected_output_tokens
        ),
    )

    registry.register(
        name="model_route_recommend",
        description="Recommend a cost-aware model for architecture, coding, QA, retrieval, or general tasks.",
        parameters=[
            ToolParameter("task_type", "string", "architecture, coding, qa, retrieval, general", required=True),
            ToolParameter("quality", "string", "economy, balanced, premium", required=False),
            ToolParameter("max_cost_usd", "number", "Soft budget for the call", required=False),
            ToolParameter("prompt", "string", "Prompt text to estimate", required=False),
        ],
        handler=lambda task_type, quality="balanced", max_cost_usd=0.05, prompt="": _recommend_model(
            task_type, quality, max_cost_usd, prompt
        ),
    )

    registry.register(
        name="prompt_cache_lookup",
        description="Look up a reusable prior answer by prompt/model/namespace to avoid repeated LLM spend.",
        parameters=[
            ToolParameter("prompt", "string", "Prompt or normalized task text", required=True),
            ToolParameter("model", "string", "Model ID", required=True),
            ToolParameter("namespace", "string", "Cache namespace", required=False),
        ],
        handler=lambda prompt, model, namespace="default": foundation.cache_lookup(role_name, prompt, model, namespace),
    )

    registry.register(
        name="prompt_cache_store",
        description="Store a reusable answer for a prompt/model/namespace to reduce future LLM spend.",
        parameters=[
            ToolParameter("prompt", "string", "Prompt or normalized task text", required=True),
            ToolParameter("model", "string", "Model ID", required=True),
            ToolParameter("response", "string", "Reusable answer", required=True),
            ToolParameter("namespace", "string", "Cache namespace", required=False),
        ],
        handler=lambda prompt, model, response, namespace="default": foundation.cache_store(
            role_name, prompt, model, response, namespace
        ),
    )

    return registry
