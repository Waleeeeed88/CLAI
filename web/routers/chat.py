"""Chat router.

POST /api/chat      — start a run, returns {session_id}
GET  /api/chat/{id}/stream — SSE stream for that session
"""
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models.schemas import ChatRequest, SessionResponse
from ..services.session_manager import session_manager
from ..services import runner

router = APIRouter()

MAX_SELECTED_FILES = 8
MAX_PREVIEW_CHARS_PER_FILE = 1200
MAX_TOTAL_PREVIEW_CHARS = 5000


def _load_file_preview(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists() or not path.is_file():
        return "(missing or not a file)"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return "(unable to read file)"
    preview = text[:MAX_PREVIEW_CHARS_PER_FILE]
    if len(text) > MAX_PREVIEW_CHARS_PER_FILE:
        preview += "\n... [truncated]"
    return preview


def _selected_files_context(selected_files: List[str]) -> Dict[str, str]:
    cleaned = [p.strip() for p in selected_files if p and p.strip()]
    if not cleaned:
        return {}

    cleaned = cleaned[:MAX_SELECTED_FILES]
    file_list = "\n".join(f"- {p}" for p in cleaned)

    previews: List[str] = []
    total = 0
    for p in cleaned:
        snippet = _load_file_preview(p)
        block = f"[{p}]\n{snippet}"
        total += len(block)
        if total > MAX_TOTAL_PREVIEW_CHARS:
            previews.append("... [additional selected file previews omitted]")
            break
        previews.append(block)

    return {
        "selected_files": file_list,
        "selected_file_context": "\n\n".join(previews),
    }


def _augment_requirement(requirement: str, selected_ctx: Dict[str, str]) -> str:
    if not selected_ctx:
        return requirement
    selected_list = selected_ctx.get("selected_files", "")
    selected_preview = selected_ctx.get("selected_file_context", "")
    extra = (
        "Selected files from UI:\n"
        f"{selected_list}\n\n"
        "Selected file previews:\n"
        f"{selected_preview}"
    )
    if requirement.strip():
        return f"{requirement.strip()}\n\n{extra}"
    return extra


@router.post("/chat", response_model=SessionResponse)
async def start_chat(req: ChatRequest):
    session_id, bus = session_manager.create_session()
    selected_ctx = _selected_files_context(req.selected_files)

    if req.type == "pipeline":
        base_requirement = req.requirement or req.context.get("requirement", "")
        requirement = _augment_requirement(base_requirement, selected_ctx)
        project_name = req.project_name or req.context.get("project_name", "project")
        runner.run_pipeline_async(
            requirement, project_name, bus,
            workspace_dir=req.workspace_dir,
            use_github=req.use_github,
            selected_phases=req.selected_phases,
            selected_files=req.selected_files,
        )

    else:
        bus.put({
            "type": "error",
            "message": (
                f"Unsupported request type: {req.type!r}. "
                "This web API now supports only 'pipeline' with phases: "
                "planning, implementation, github_mcp."
            ),
        })
        bus.close()

    return SessionResponse(session_id=session_id)


@router.get("/chat/{session_id}/stream")
async def stream_chat(session_id: str):
    bus = session_manager.get_bus(session_id)
    if bus is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return StreamingResponse(
        bus.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
