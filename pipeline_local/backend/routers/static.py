"""Static file serving — PDB 구조 파일 및 이미지 제공.

runs_local/ 와 원본 data/ 디렉토리에서 파일을 제공한다.
경로 순회(path traversal) 공격 방지 로직 포함.
"""
from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from pipeline_local.backend.state import REPO_ROOT, AG_SRC_REPO

router = APIRouter()

# 검색 기준 디렉토리
_RUNS_DIR  = REPO_ROOT / "runs_local"
_DATA_DIRS = [
    REPO_ROOT / "data",
    AG_SRC_REPO / "data",   # 원본 receptor PDB 포함
]


@router.get("/structures/{rel_path:path}")
def serve_pdb(rel_path: str):
    """runs_local/ 또는 data/ 에서 .pdb 파일을 제공한다."""
    search_dirs = [_RUNS_DIR] + _DATA_DIRS
    for base in search_dirs:
        if not base.exists():
            continue
        file_path = (base / rel_path).resolve()
        try:
            file_path.relative_to(base.resolve())
        except ValueError:
            continue
        if file_path.is_symlink():
            continue
        if file_path.suffix.lower() != ".pdb":
            continue
        if file_path.exists() and file_path.is_file():
            return Response(
                content=file_path.read_bytes(),
                media_type="chemical/x-pdb",
                headers={"Cache-Control": "public, max-age=60"},
            )
    raise HTTPException(status_code=404, detail="PDB 파일을 찾을 수 없습니다.")


@router.get("/images/{rel_path:path}")
def serve_image(rel_path: str):
    """runs_local/ 내 이미지 파일을 제공한다."""
    base = _RUNS_DIR
    file_path = (base / rel_path).resolve()
    try:
        file_path.relative_to(base.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="접근 금지")
    if file_path.is_symlink():
        raise HTTPException(status_code=403, detail="접근 금지")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return Response(
        content=file_path.read_bytes(),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=300"},
    )
