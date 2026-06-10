"""Static file serving: PDB structures and images."""
from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.state import REPO_ROOT

router = APIRouter()

_RUNS_DIR = REPO_ROOT / "runs"
_RUNS_PF_DIR = REPO_ROOT / "runs" / "pyrosetta_flow"
_RUNS_LOCAL_DIR = REPO_ROOT / "runs_local"
_DATA_DIR = REPO_ROOT / "data"


@router.get("/structures/{rel_path:path}")
def serve_pdb(rel_path: str):
    for base in (_RUNS_DIR, _RUNS_PF_DIR, _RUNS_LOCAL_DIR, _DATA_DIR):
        file_path = (base / rel_path).resolve()
        # Security: ensure path stays within allowed directory
        try:
            file_path.relative_to(base.resolve())
        except ValueError:
            continue
        if file_path.is_symlink():
            continue
        if not file_path.suffix.lower() == ".pdb":
            continue
        if file_path.exists() and file_path.is_file():
            return Response(
                content=file_path.read_bytes(),
                media_type="chemical/x-pdb",
                headers={"Cache-Control": "public, max-age=60"},
            )
    raise HTTPException(status_code=404, detail="PDB file not found")


@router.get("/images/{rel_path:path}")
def serve_image(rel_path: str):
    base = REPO_ROOT / "runs"
    file_path = (base / rel_path).resolve()
    # Security: ensure path stays within runs/
    try:
        file_path.relative_to(base.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden")
    if file_path.is_symlink():
        raise HTTPException(status_code=403, detail="Forbidden")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return Response(
        content=file_path.read_bytes(),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=300"},
    )
