"""Read-only filesystem browsing endpoints for local workspace selection."""

from __future__ import annotations

import os
import string
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


def _entry(path: Path, base: Path | None = None) -> Dict[str, Any]:
    is_dir = path.is_dir()
    item: Dict[str, Any] = {
        "name": path.name or str(path),
        "path": str(path),
        "type": "directory" if is_dir else "file",
    }
    if base is not None and base != path:
        item["relative"] = str(path.relative_to(base))
    return item


def _windows_roots() -> List[Path]:
    roots: List[Path] = []
    for drive in string.ascii_uppercase:
        candidate = Path(f"{drive}:/")
        if candidate.exists():
            roots.append(candidate)
    return roots


def _list_roots() -> List[Path]:
    if os.name == "nt":
        return _windows_roots()
    return [Path("/"), Path.home()]


@router.get("/filesystem/roots")
def list_filesystem_roots():
    roots = [_entry(root) for root in _list_roots()]
    return {"roots": roots}


@router.get("/filesystem/list")
def list_filesystem_entries(
    path: str = Query(..., description="Directory path to list"),
    include_files: bool = Query(True, description="Include files in response"),
    show_hidden: bool = Query(False, description="Include hidden entries"),
):
    target = Path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    try:
        children = list(target.iterdir())
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}") from exc

    entries: List[Dict[str, Any]] = []
    for child in children:
        if not show_hidden and child.name.startswith("."):
            continue
        if child.is_file() and not include_files:
            continue
        entries.append(_entry(child, base=target))

    entries.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
    parent = str(target.parent) if target.parent != target else None
    return {
        "path": str(target),
        "name": target.name or str(target),
        "parent": parent,
        "entries": entries,
    }
