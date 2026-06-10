"""Binding Pocket 설정 CRUD endpoint.

사용자가 UI에서 SSTR1~5 binding pocket 좌표·radius·잔기를 직접 설정 가능.

Endpoints:
  GET    /api/binding_pocket/{receptor}          — 현재 설정 조회
  PUT    /api/binding_pocket/{receptor}          — 설정 저장 (user override)
  POST   /api/binding_pocket/{receptor}/extract  — PDB 자동 추출
  DELETE /api/binding_pocket/{receptor}          — 기본값 복원
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parents[1]  # backend/
_REPO_ROOT = _BACKEND_DIR.parents[3]                 # SST14-M_scr/
DATA_DIR: Path = _REPO_ROOT / "data" / "somatostatin_receptor"

# pipeline_local 모듈 접근 (extract_pocket_center 함수 사용)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SSTR_NAMES: List[str] = ["sstr1", "sstr2", "sstr3", "sstr4", "sstr5"]

# SSTR 수용체별 구조 파일 매핑 (PDB 우선, CIF 대안)
_SSTR_PDB_FILES: Dict[str, List[str]] = {
    "sstr1": ["SSTR1_9IK8.pdb", "SSTR1_9IK8.cif"],
    "sstr2": ["SSTR2_7XNA.pdb", "SSTR2_7XNA.cif"],
    "sstr3": ["SSTR3_8XIR.pdb", "SSTR3_8XIR.cif"],
    "sstr4": ["SSTR4_7XMT.pdb", "SSTR4_7XMT.cif"],
    "sstr5": ["SSTR5_8ZBJ.pdb", "SSTR5_8ZBJ.cif"],
}


# ---------------------------------------------------------------------------
# 모델 정의
# ---------------------------------------------------------------------------

class BoxSize(BaseModel):
    """GNINA/AutoDock 도킹 박스 크기 모델.

    size_x/y/z 모두 필수. 범위: 10~80Å.
    잘못된 키(예: wrong_key)는 Pydantic이 422로 거부한다.
    """

    size_x: float = Field(..., ge=10.0, le=80.0)
    size_y: float = Field(..., ge=10.0, le=80.0)
    size_z: float = Field(..., ge=10.0, le=80.0)


class BindingPocketConfig(BaseModel):
    """사용자 입력 binding pocket 설정 모델."""

    receptor: str = Field(..., pattern="^sstr[1-5]$")
    center_x: float
    center_y: float
    center_z: float
    radius_angstrom: float = Field(..., ge=5.0, le=30.0)
    residue_ids: List[int] = Field(default_factory=list)
    box_size: Optional[BoxSize] = None  # None → PUT 시 radius_angstrom 기반 자동 계산
    source: str = "user_override"


class ExtractRequest(BaseModel):
    """자동 추출 요청 모델."""

    residue_ids: List[int] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _pocket_path(receptor: str) -> Path:
    """주 binding pocket JSON 파일 경로 반환."""
    return DATA_DIR / f"binding_pocket_{receptor.upper()}.json"


def _default_path(receptor: str) -> Path:
    """원본 백업 JSON 파일 경로 반환 (user override 이전 원본 보존용)."""
    return DATA_DIR / f"binding_pocket_{receptor.upper()}_default.json"


def _validate_receptor(receptor: str) -> str:
    """수용체 이름 소문자 정규화 및 유효성 검사.

    Args:
        receptor: 수용체 이름 (대소문자 무관)

    Returns:
        소문자 정규화된 수용체 이름

    Raises:
        HTTPException 400: 유효하지 않은 수용체 이름
    """
    name = receptor.lower()
    if name not in SSTR_NAMES:
        raise HTTPException(status_code=400, detail=f"Unknown receptor: {receptor}")
    return name


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/binding_pocket/{receptor}")
def get_pocket(receptor: str) -> Dict[str, Any]:
    """현재 binding pocket 설정 조회.

    Args:
        receptor: 수용체 이름 (sstr1~sstr5, 대소문자 무관)

    Returns:
        저장된 binding pocket JSON

    Raises:
        HTTPException 400: 알 수 없는 수용체
        HTTPException 404: 설정 파일 없음
    """
    name = _validate_receptor(receptor)
    path = _pocket_path(name)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No binding pocket configured for {receptor}",
        )
    return json.loads(path.read_text(encoding="utf-8"))


@router.put("/binding_pocket/{receptor}")
def update_pocket(receptor: str, config: BindingPocketConfig) -> Dict[str, Any]:
    """binding pocket 설정 저장 (user override).

    저장 전 기존 원본 파일을 _default.json 으로 자동 백업한다.
    box_size 미제공 시 radius_angstrom × 2 로 자동 계산 (최소 30Å).

    Args:
        receptor: URL 수용체 이름
        config:   BindingPocketConfig 페이로드

    Returns:
        {"ok": True, "path": str}

    Raises:
        HTTPException 400: 수용체 이름 불일치 또는 유효하지 않은 수용체
    """
    name = _validate_receptor(receptor)
    if config.receptor.lower() != name:
        raise HTTPException(
            status_code=400,
            detail=f"Receptor mismatch: URL={receptor}, body={config.receptor}",
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    main_path = _pocket_path(name)
    default_path = _default_path(name)

    # 기존 파일이 user_override가 아닌 원본이면 _default.json으로 백업
    if main_path.exists() and not default_path.exists():
        existing = json.loads(main_path.read_text(encoding="utf-8"))
        if existing.get("source") != "user_override":
            default_path.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # box_size 자동 계산 (미제공 시): BoxSize 인스턴스로 생성
    if not config.box_size:
        size = max(30.0, config.radius_angstrom * 2)
        config.box_size = BoxSize(size_x=size, size_y=size, size_z=size)

    payload = config.model_dump()
    payload["timestamp"] = datetime.now(tz=timezone.utc).isoformat()

    main_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"ok": True, "path": str(main_path)}


@router.post("/binding_pocket/{receptor}/extract")
def extract_pocket(receptor: str, body: ExtractRequest) -> Dict[str, Any]:
    """PDB에서 binding pocket 자동 추출 후 저장.

    pipeline_local/scripts/extract_binding_pocket.py::extract_pocket_center 를
    호출하여 지정 잔기 기반 포켓 중심·반경을 계산하고 JSON으로 저장한다.

    Args:
        receptor: 수용체 이름 (sstr1~sstr5)
        body:     residue_ids 목록

    Returns:
        추출된 binding pocket 정보 (center, radius, box_size 포함)

    Raises:
        HTTPException 400: 알 수 없는 수용체
        HTTPException 404: PDB/CIF 파일 없음
        HTTPException 422: 잔기 추출 실패 (좌표 없음)
        HTTPException 503: extract_binding_pocket 모듈 로드 실패
    """
    name = _validate_receptor(receptor)

    # 구조 파일 탐색 (PDB 우선, CIF 대안)
    pdb_path: Optional[Path] = None
    candidates = [DATA_DIR / fn for fn in _SSTR_PDB_FILES.get(name, [])]
    for candidate in candidates:
        if candidate.exists():
            pdb_path = candidate
            break

    if pdb_path is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No PDB/CIF file found for {receptor}. "
                f"Searched: {[str(p) for p in candidates]}"
            ),
        )

    try:
        from pipeline_local.scripts.extract_binding_pocket import extract_pocket_center  # type: ignore[import]

        result = extract_pocket_center(
            pdb_path=pdb_path,
            residue_ids=body.residue_ids,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"extract_binding_pocket 모듈 로드 실패: {exc}",
        ) from exc

    # 결과 저장
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    main_path = _pocket_path(name)
    payload: Dict[str, Any] = {
        "receptor": name.upper(),
        "center_x": result["center_x"],
        "center_y": result["center_y"],
        "center_z": result["center_z"],
        "radius_angstrom": result["radius_angstrom"],
        "residue_ids": result["residue_ids"],
        "box_size": result["box_size"],
        "source": "auto_extract",
        "source_pdb": result.get("source_pdb", str(pdb_path)),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    main_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


@router.delete("/binding_pocket/{receptor}")
def reset_pocket(receptor: str) -> Dict[str, Any]:
    """user override 초기화 (default JSON 복원).

    _default.json 백업이 있으면 복원 후 백업 삭제.
    백업이 없으면 현재 파일 삭제 (404 상태로 초기화).

    Args:
        receptor: 수용체 이름

    Returns:
        {"ok": True, "restored": bool, ...}

    Raises:
        HTTPException 400: 알 수 없는 수용체
        HTTPException 404: 설정 파일 없음
    """
    name = _validate_receptor(receptor)
    main_path = _pocket_path(name)
    default_path = _default_path(name)

    if not main_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No binding pocket configured for {receptor}",
        )

    if default_path.exists():
        # 백업에서 원본 복원
        original = default_path.read_text(encoding="utf-8")
        main_path.write_text(original, encoding="utf-8")
        default_path.unlink()
        return {"ok": True, "restored": True, "path": str(main_path)}
    else:
        # 백업 없음: 파일 삭제
        main_path.unlink()
        return {"ok": True, "restored": False, "deleted": True}
