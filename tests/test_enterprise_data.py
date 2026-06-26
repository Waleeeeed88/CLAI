from pathlib import Path

from core.enterprise_data import EnterpriseDataFoundation, build_enterprise_data_registry


def test_semantic_search_filters_by_role_clearance(tmp_path: Path):
    foundation = EnterpriseDataFoundation(tmp_path)

    public_doc = foundation.index_document(
        actor="ba",
        doc_id="public-roadmap",
        title="Roadmap",
        content="AI agent roadmap for metadata and retrieval systems",
        sensitivity="internal",
    )
    restricted_doc = foundation.index_document(
        actor="senior_dev",
        doc_id="restricted-contract",
        title="Contract",
        content="Restricted customer pricing and contract obligations",
        sensitivity="restricted",
    )

    assert public_doc["ok"] is True
    assert restricted_doc["ok"] is True

    ba_results = foundation.semantic_search("ba", "customer pricing retrieval", limit=5)["results"]
    senior_results = foundation.semantic_search("senior_dev", "customer pricing retrieval", limit=5)["results"]

    assert all(result["doc_id"] != "restricted-contract" for result in ba_results)
    assert any(result["doc_id"] == "restricted-contract" for result in senior_results)


def test_memory_graph_checkpoint_and_cache_are_durable(tmp_path: Path):
    foundation = EnterpriseDataFoundation(tmp_path)

    memory = foundation.write_memory(
        actor="coder",
        namespace="project-x",
        key="retrieval_choice",
        value="Use metadata catalog before vector search.",
        tags=["rag", "cost"],
    )
    fact = foundation.upsert_fact(
        actor="senior_dev",
        subject="AgentPlatform",
        predicate="uses",
        obj="knowledge graph",
        source="architecture",
        sensitivity="internal",
    )
    checkpoint = foundation.write_checkpoint(
        actor="qa",
        workflow_id="wf-1",
        step="verification",
        state='{"tests": "pending"}',
    )
    cache = foundation.cache_store(
        actor="coder",
        prompt="summarize retrieval plan",
        model="gpt-5.4-mini",
        response="Use catalog, graph, then semantic search.",
    )

    reloaded = EnterpriseDataFoundation(tmp_path)
    assert memory["ok"] is True
    assert fact["ok"] is True
    assert checkpoint["ok"] is True
    assert cache["ok"] is True
    assert reloaded.search_memory("coder", "metadata vector", namespace="project-x")["results"]
    assert reloaded.query_graph("qa", "knowledge graph")["facts"]
    assert reloaded.list_checkpoints("qa", "wf-1")["checkpoints"]["verification"]["status"] == "in_progress"
    assert reloaded.cache_lookup("coder", "summarize retrieval plan", "gpt-5.4-mini")["hit"] is True


def test_registry_exposes_cost_and_governance_tools(tmp_path: Path):
    foundation = EnterpriseDataFoundation(tmp_path)
    registry = build_enterprise_data_registry(foundation, "ba")

    estimate = registry.execute(
        "cost_estimate",
        {
            "model": "gpt-5.4-mini",
            "prompt": "Build a RAG workflow",
            "expected_output_tokens": 500,
        },
    )
    decision = registry.execute(
        "governance_check",
        {
            "action": "read.customer_contracts",
            "resource": "contracts",
            "sensitivity": "restricted",
            "purpose": "requirements analysis",
        },
    )

    assert "estimated_cost_usd" in estimate
    assert '"allowed": false' in decision


def test_registry_accepts_stringified_numeric_tool_args(tmp_path: Path):
    foundation = EnterpriseDataFoundation(tmp_path)
    registry = build_enterprise_data_registry(foundation, "senior_dev")

    registry.execute(
        "semantic_document_index",
        {
            "doc_id": "api-guide",
            "title": "API Guide",
            "content": "Grounding retrieval and metadata API design",
        },
    )
    results = registry.execute("semantic_search", {"query": "metadata API", "limit": "1"})
    estimate = registry.execute(
        "model_route_recommend",
        {
            "task_type": "qa",
            "quality": "economy",
            "max_cost_usd": "0.01",
            "prompt": "small validation pass",
        },
    )

    assert '"doc_id": "api-guide"' in results
    assert "recommended_model" in estimate
