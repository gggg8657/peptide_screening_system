"""
selectivity.py — Off-target Selectivity 스크리닝 API
=====================================================
SSTR2 후보를 SSTR1/3/4/5 수용체에 도킹하여 선택성 스코어를 반환한다.

엔드포인트:
    GET  /api/selectivity/receptors       — 등록된 수용체 목록 조회
    POST /api/selectivity/receptors       — PDB/CIF 텍스트 업로드 및 저장
    POST /api/selectivity/run             — 비동기 도킹 잡 시작
    GET  /api/selectivity/status/{job_id} — 잡 진행 상태 조회
    GET  /api/selectivity/results/{job_id}— 완료된 결과 조회
    GET  /api/selectivity/jobs            — 잡 목록 조회

P1-4 (2026-05-13): /selectivity/results, /status 응답에 confidence_grade 자동 주입.
  → grade "C": selectivity_margin은 dock_score 차이 기반.
     Boltz iPTM ≠ Ki proxy (Spearman ρ≈-0.3, 순위 일치 0/5 실증).
     정량 선택성은 FEP/MM-GBSA/Ki assay 필요.
  근거: pharmacology_guards.ENDPOINT_CONFIDENCE, step05c.py docstring

실행 흐름:
    1. POST /receptors 로 SSTR1/3/4/5 PDB/CIF 저장 (선택 사항)
       없으면 data/somatostatin_receptor/ CIF 파일을 자동 사용.
    2. POST /run 으로 잡 시작 → background thread 에서 도킹 실행
       candidate_sequences 제공 시: PyRosetta FlexPepDock (production)
       미제공 시: estimation 모드 (노이즈 기반 근사)
    3. GET /status 폴링으로 진행 상태 확인
    4. GET /results 로 최종 결과 수신

결과 저장 경로:
    runs_local/selectivity/{job_id}/status.json
    runs_local/selectivity/{job_id}/results.json
    runs_local/selectivity/receptors/{receptor_name}.pdb|.cif

결과 JSON 형식 (production mode):
    {
      "seq_id": "SST14_v12",
      "sequence": "AGCKNFFWKTFTSC",
      "sstr2_ddg": -8.5,
      "offtarget_ddg": {"sstr1": -5.2, "sstr3": -6.1, "sstr4": -4.8, "sstr5": -5.5},
      "delta_ddg": {"sstr1": -3.3, "sstr3": -2.4, "sstr4": -3.7, "sstr5": -3.0},
      "wsm": -2.4,
      "msm": -3.1,
      "selectivity_ratios": {"sstr1": 214, "sstr3": 49, "sstr4": 406, "sstr5": 134},
      "tier": 2,
      "passed": true
    }
"""
from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from pipeline_local.backend.state import REPO_ROOT
from pipeline_local.scripts.pharmacology_guards import attach_confidence

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# 경로 상수
# ---------------------------------------------------------------------------

SELECTIVITY_BASE = REPO_ROOT / "runs_local" / "selectivity"
RECEPTOR_DIR = SELECTIVITY_BASE / "receptors"

# data/ 디렉토리의 기본 CIF 파일들
_DEFAULT_CIF_DIR = REPO_ROOT / "data" / "somatostatin_receptor"
_DEFAULT_RECEPTOR_FILES = {
    "sstr1": "SSTR1_9IK8.cif",
    "sstr3": "SSTR3_8XIR.cif",
    "sstr4": "SSTR4_7XMT.cif",
    "sstr5": "SSTR5_8ZBJ.cif",
}

# 지원 off-target 수용체
SUPPORTED_RECEPTORS = ("sstr1", "sstr3", "sstr4", "sstr5")

# 파일명 안전 검증 패턴
_SAFE_ID_RE = re.compile(r'^[A-Za-z0-9_\-\.]+$')

# ---------------------------------------------------------------------------
# 인메모리 잡 레지스트리 (상태 조회 최적화)
# ---------------------------------------------------------------------------

_job_lock = threading.Lock()
_jobs: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Pydantic 모델
# ---------------------------------------------------------------------------

class ReceptorUploadRequest(BaseModel):
    """POST /api/selectivity/receptors 요청 바디.

    수용체 구조 텍스트를 직접 업로드한다. PDB와 CIF 형식 모두 허용.
    각 필드는 선택 사항이며, 포함된 수용체만 저장된다.
    """
    sstr1_pdb: Optional[str] = Field(None, description="SSTR1 PDB 텍스트")
    sstr3_pdb: Optional[str] = Field(None, description="SSTR3 PDB 텍스트")
    sstr4_pdb: Optional[str] = Field(None, description="SSTR4 PDB 텍스트")
    sstr5_pdb: Optional[str] = Field(None, description="SSTR5 PDB 텍스트")
    # CIF 형식 지원 (원본 확장자 보존)
    sstr1_cif: Optional[str] = Field(None, description="SSTR1 CIF/mmCIF 텍스트")
    sstr3_cif: Optional[str] = Field(None, description="SSTR3 CIF/mmCIF 텍스트")
    sstr4_cif: Optional[str] = Field(None, description="SSTR4 CIF/mmCIF 텍스트")
    sstr5_cif: Optional[str] = Field(None, description="SSTR5 CIF/mmCIF 텍스트")


class SelectivityRunRequest(BaseModel):
    """POST /api/selectivity/run 요청 바디."""

    candidate_ids: List[str] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="도킹할 후보 ID 목록 (Step05 결과의 seq_id)",
    )
    candidate_sequences: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "후보 아미노산 서열 매핑 {candidate_id: sequence}. "
            "제공 시 PyRosetta FlexPepDock production 모드로 실행. "
            "미제공 시 estimation 모드(노이즈 근사) 사용."
        ),
    )
    receptor_pdbs: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "수용체 구조 파일 경로 매핑. 예: {\"sstr1\": \"/path/to/sstr1.cif\"}. "
            "생략 시 사전 업로드된 파일 → data/somatostatin_receptor/ CIF 순으로 탐색."
        ),
    )
    sstr2_score_override: Optional[Dict[str, float]] = Field(
        None,
        description="후보별 SSTR2 도킹 스코어 오버라이드 {candidate_id: score}. "
                    "파이프라인 결과를 찾지 못할 때 수동 입력용.",
    )
    nstruct: int = Field(
        20,
        ge=1,
        le=200,
        description="FlexPepDock 반복 횟수 (production 모드, 기본 20)",
    )
    selectivity_margin_min: float = Field(
        -2.0,
        description="선택성 마진 하한 (기본 -2.0). 이 값 이하여야 통과.",
    )
    offtarget_max_allowed: float = Field(
        -3.0,
        description="off-target 최대 허용 스코어 (기본 -3.0). 이 값 이상이어야 통과.",
    )


# ---------------------------------------------------------------------------
# 기본 수용체 자동 등록
# ---------------------------------------------------------------------------

def _auto_register_default_receptors() -> Dict[str, str]:
    """data/somatostatin_receptor/ CIF 파일을 receptors 디렉토리에 심볼릭 링크로 등록한다.

    runs_local/selectivity/receptors/ 에 이미 파일이 있으면 덮어쓰지 않는다.
    등록된 {receptor_name: path} 딕셔너리를 반환한다.
    """
    RECEPTOR_DIR.mkdir(parents=True, exist_ok=True)
    registered: Dict[str, str] = {}

    for name, filename in _DEFAULT_RECEPTOR_FILES.items():
        src = _DEFAULT_CIF_DIR / filename
        if not src.exists():
            continue
        dest = RECEPTOR_DIR / f"{name}.cif"
        # 이미 존재하면 건너뜀 (업로드한 파일 보호)
        if dest.exists():
            registered[name] = str(dest)
            continue
        try:
            dest.symlink_to(src.resolve())
            registered[name] = str(dest)
            logger.info("[selectivity] 기본 수용체 등록: %s → %s", name, src)
        except OSError as exc:
            # 심볼릭 링크 실패 시 직접 경로 등록
            logger.debug("[selectivity] symlink 실패, 경로 직접 사용 (%s): %s", name, exc)
            registered[name] = str(src)

    return registered


# 서버 시작 시 자동 등록 실행
_auto_register_default_receptors()


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _safe_id(value: str, field: str = "id") -> str:
    """경로 인젝션 방지: 알파벳·숫자·_-. 만 허용."""
    if not _SAFE_ID_RE.match(value):
        raise ValueError(
            f"안전하지 않은 문자가 포함된 {field}: {value!r}. "
            "영문자·숫자·밑줄·하이픈·점만 허용됩니다."
        )
    return value


def _job_dir(job_id: str) -> Path:
    return SELECTIVITY_BASE / job_id


def _write_status(job_id: str, data: Dict[str, Any]) -> None:
    """상태를 인메모리 및 파일에 동시 기록한다."""
    with _job_lock:
        _jobs[job_id] = data
    path = _job_dir(job_id) / "status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_status_file(job_id: str) -> Optional[Dict[str, Any]]:
    """파일에서 상태를 읽는다 (인메모리 미스 시 폴백)."""
    path = _job_dir(job_id) / "status.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _resolve_receptor_paths(
    receptor_pdbs: Optional[Dict[str, str]],
) -> Dict[str, Optional[str]]:
    """요청의 receptor_pdbs, 업로드 파일, 기본 CIF 순으로 수용체 경로를 결정한다.

    탐색 우선순위:
      1. 요청 바디의 receptor_pdbs 명시 경로
      2. runs_local/selectivity/receptors/ 업로드 파일 (PDB→CIF 순)
      3. data/somatostatin_receptor/ 기본 CIF (심볼릭 링크 또는 직접 경로)
    """
    paths: Dict[str, Optional[str]] = {}
    for name in SUPPORTED_RECEPTORS:
        # 1) 요청에 명시된 경로 우선
        if receptor_pdbs and name in receptor_pdbs:
            paths[name] = receptor_pdbs[name]
            continue
        # 2) 사전 업로드된 파일: PDB 우선, CIF 폴백
        for ext in (".pdb", ".cif", ".mmcif"):
            uploaded = RECEPTOR_DIR / f"{name}{ext}"
            if uploaded.exists():
                paths[name] = str(uploaded)
                break
        else:
            # 3) data/ 디렉토리 기본 CIF 직접 사용
            default_filename = _DEFAULT_RECEPTOR_FILES.get(name)
            if default_filename:
                default_path = _DEFAULT_CIF_DIR / default_filename
                paths[name] = str(default_path) if default_path.exists() else None
            else:
                paths[name] = None
    return paths


def _load_sstr2_scores(
    candidate_ids: List[str],
    candidate_sequences: Optional[Dict[str, str]] = None,
) -> Dict[str, float]:
    """모든 아카이브에서 SSTR2 도킹 스코어를 조회한다.

    1차: candidate_id로 매칭
    2차: sequence로 매칭 (같은 서열이 다른 ID로 저장된 경우)
    """
    from pipeline_local.backend.state import list_archive_dashboard_files

    scores: Dict[str, float] = {}
    seq_to_id: Dict[str, str] = {}
    if candidate_sequences:
        seq_to_id = {seq: cid for cid, seq in candidate_sequences.items()}

    remaining_ids = set(candidate_ids)
    archive_files = list_archive_dashboard_files()  # 전체 탐색

    for archive_path in archive_files:
        if not remaining_ids:
            break
        try:
            data = json.loads(archive_path.read_text(encoding="utf-8"))
            candidates = data.get("candidates", [])
            for c in candidates:
                cid = c.get("id") or c.get("seq_id") or c.get("candidate_id")
                seq = c.get("sequence", "")
                score = c.get("ddG") or c.get("dock_score") or c.get("score")
                if score is None:
                    continue

                # 1차: ID 매칭
                if cid and cid in remaining_ids:
                    scores[cid] = float(score)
                    remaining_ids.discard(cid)
                # 2차: 서열 매칭
                elif seq and seq in seq_to_id and seq_to_id[seq] in remaining_ids:
                    target_id = seq_to_id[seq]
                    scores[target_id] = float(score)
                    remaining_ids.discard(target_id)
        except (json.JSONDecodeError, OSError, KeyError):
            continue

    # 조회 실패한 후보는 기본값
    for cid in candidate_ids:
        scores.setdefault(cid, -5.0)

    return scores


# ---------------------------------------------------------------------------
# 핵심 도킹 실행 (background thread)
# ---------------------------------------------------------------------------

def _run_selectivity_job(
    job_id: str,
    candidate_ids: List[str],
    candidate_sequences: Dict[str, str],
    receptor_paths: Dict[str, Optional[str]],
    sstr2_scores: Dict[str, float],
    margin_min: float,
    offtarget_max: float,
    nstruct: int,
) -> None:
    """백그라운드 스레드에서 off-target 도킹을 순차 실행한다.

    후보 N개 × 수용체 4개 = 4N 도킹 작업을 순차 실행.
    각 작업 완료 시 status.json 의 progress 를 갱신한다.

    candidate_sequences 가 있으면 SelectivityRunner(PyRosetta)를 사용하고,
    없으면 estimation 모드(노이즈 근사)로 폴백한다.
    """
    from pipeline_local.core.selectivity_runner import (
        SelectivityRunner,
        compute_full_selectivity,
    )
    from pipeline_local.steps.step05b_selectivity import dock_against_offtarget

    total_tasks = len(candidate_ids) * len(SUPPORTED_RECEPTORS)
    completed = 0

    started_at = datetime.now(timezone.utc).isoformat()
    _write_status(job_id, {
        "job_id": job_id,
        "status": "running",
        "progress": 0,
        "total_tasks": total_tasks,
        "completed_tasks": 0,
        "candidate_ids": candidate_ids,
        "started_at": started_at,
        "results": [],
    })

    production_mode = bool(candidate_sequences)
    runner = None
    if production_mode:
        try:
            import subprocess as _sp
            from pipeline_local.core.selectivity_runner import SelectivityRunner as _SR
            _conda = _SR._find_conda()
            _check = _sp.run(
                [_conda, "run", "--no-capture-output", "-n", "bio-tools",
                 "python", "-c", "import pyrosetta; print('ok')"],
                capture_output=True, text=True, timeout=15,
            )
            if _check.returncode == 0 and "ok" in _check.stdout:
                runner = SelectivityRunner(nstruct=nstruct)
            else:
                logger.warning("[selectivity] PyRosetta 사용 불가 → estimation 모드 폴백")
                production_mode = False
        except Exception as exc:
            logger.warning("[selectivity] conda/PyRosetta 확인 실패 (%s) → estimation 모드 폴백", exc)
            production_mode = False

    mode_label = "production (PyRosetta)" if production_mode else "estimation"

    logger.info(
        "[selectivity] 잡 %s 시작 [%s]: 후보 %d개 × 수용체 %d개 = %d 도킹",
        job_id, mode_label, len(candidate_ids), len(SUPPORTED_RECEPTORS), total_tasks,
    )

    estimation_config = {
        "selectivity": {
            "selectivity_margin_min": margin_min,
            "offtarget_max_allowed": offtarget_max,
            "selectivity_noise_std": 2.0,
            "selectivity_seed": 42,
        }
    }

    job_base_dir = _job_dir(job_id)
    partial_results: List[Dict[str, Any]] = []

    try:
        for cand_id in candidate_ids:
            sstr2_score = sstr2_scores.get(cand_id) or -5.0
            sequence = candidate_sequences.get(cand_id, "")
            offtarget_ddgs: Dict[str, Optional[float]] = {}

            for receptor_name in SUPPORTED_RECEPTORS:
                receptor_path = receptor_paths.get(receptor_name) or ""

                try:
                    if production_mode and runner is not None and sequence and receptor_path and Path(receptor_path).exists():
                        # Production: PyRosetta FlexPepDock
                        dock_out = str(job_base_dir / cand_id / receptor_name)
                        Path(dock_out).mkdir(parents=True, exist_ok=True)
                        ot_score: Optional[float] = runner.dock_against_receptor(
                            receptor_path=receptor_path,
                            peptide_sequence=sequence,
                            output_dir=dock_out,
                        )
                    else:
                        # Estimation 폴백
                        ot_score = dock_against_offtarget(
                            candidate_pdb="",
                            receptor_pdb=receptor_path,
                            engine="diffdock",
                            config=estimation_config,
                            on_target_score=sstr2_score,
                        )
                    offtarget_ddgs[receptor_name] = ot_score
                    logger.debug(
                        "[selectivity] %s vs %s → %.3f",
                        cand_id, receptor_name, ot_score,
                    )
                except Exception as exc:
                    logger.warning(
                        "[selectivity] 도킹 실패 (%s vs %s): %s",
                        cand_id, receptor_name, exc,
                    )
                    offtarget_ddgs[receptor_name] = None

                completed += 1
                _write_status(job_id, {
                    "job_id": job_id,
                    "status": "running",
                    "progress": round(completed / total_tasks * 100),
                    "total_tasks": total_tasks,
                    "completed_tasks": completed,
                    "started_at": started_at,
                    "results": partial_results,
                })

            # 후보 1개 완료 — 완전한 selectivity 결과 계산
            result = compute_full_selectivity(
                seq_id=cand_id,
                sequence=sequence,
                sstr2_ddg=sstr2_score,
                offtarget_ddgs=offtarget_ddgs,
            )
            # 하위 호환: estimation 모드에서 None ddG는 0.0으로 대체 후 재계산 (API 일관성)
            partial_results.append(result)

        # 완료
        finished_at = datetime.now(timezone.utc).isoformat()
        final_status = {
            "job_id": job_id,
            "status": "completed",
            "progress": 100,
            "total_tasks": total_tasks,
            "completed_tasks": total_tasks,
            "started_at": started_at,
            "finished_at": finished_at,
            "mode": mode_label,
            "results": partial_results,
        }
        _write_status(job_id, final_status)

        # 결과 파일 별도 저장
        results_path = _job_dir(job_id) / "results.json"
        results_path.write_text(
            json.dumps(
                {
                    "job_id": job_id,
                    "generated_at": finished_at,
                    "mode": mode_label,
                    "candidates": partial_results,
                    "summary": {
                        "total": len(partial_results),
                        "passed": sum(1 for r in partial_results if r["passed"]),
                        "failed": sum(1 for r in partial_results if not r["passed"]),
                        "tier3_count": sum(1 for r in partial_results if r.get("tier", 0) == 3),
                        "tier2_count": sum(1 for r in partial_results if r.get("tier", 0) == 2),
                        "tier1_count": sum(1 for r in partial_results if r.get("tier", 0) == 1),
                        "margin_min_used": margin_min,
                        "offtarget_max_used": offtarget_max,
                        "nstruct": nstruct,
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        logger.info(
            "[selectivity] 잡 %s 완료 [%s]. 통과: %d/%d",
            job_id, mode_label,
            sum(1 for r in partial_results if r["passed"]),
            len(partial_results),
        )

    except Exception as exc:
        logger.exception("[selectivity] 잡 %s 오류: %s", job_id, exc)
        _write_status(job_id, {
            "job_id": job_id,
            "status": "failed",
            "progress": round(completed / total_tasks * 100) if total_tasks else 0,
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "error": str(exc),
            "results": partial_results,
        })


# ---------------------------------------------------------------------------
# GET /api/selectivity/receptors
# ---------------------------------------------------------------------------

@router.get("/selectivity/receptors")
def list_receptors():
    """등록된 off-target 수용체 목록을 반환한다.

    탐색 순서:
      1. runs_local/selectivity/receptors/ 업로드 파일
      2. data/somatostatin_receptor/ 기본 CIF 파일

    응답 예시:
        {
          "receptors": {
            "sstr1": {"path": "/.../sstr1.cif", "format": "cif", "source": "uploaded"},
            "sstr3": {"path": "/.../SSTR3_8XIR.cif", "format": "cif", "source": "default"}
          },
          "available_count": 4,
          "missing": []
        }
    """
    RECEPTOR_DIR.mkdir(parents=True, exist_ok=True)
    receptors: Dict[str, Any] = {}

    for name in SUPPORTED_RECEPTORS:
        info: Optional[Dict[str, Any]] = None

        # 업로드된 파일 우선
        for ext in (".pdb", ".cif", ".mmcif"):
            uploaded = RECEPTOR_DIR / f"{name}{ext}"
            if uploaded.exists():
                info = {
                    "path": str(uploaded),
                    "format": ext.lstrip("."),
                    "source": "uploaded",
                    "size_bytes": uploaded.stat().st_size,
                }
                break

        # 기본 CIF 폴백
        if info is None:
            default_filename = _DEFAULT_RECEPTOR_FILES.get(name)
            if default_filename:
                default_path = _DEFAULT_CIF_DIR / default_filename
                if default_path.exists():
                    info = {
                        "path": str(default_path),
                        "format": "cif",
                        "source": "default",
                        "size_bytes": default_path.stat().st_size,
                    }

        receptors[name] = info

    available = [n for n, v in receptors.items() if v is not None]
    missing = [n for n, v in receptors.items() if v is None]

    return {
        "receptors": receptors,
        "available_count": len(available),
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# POST /api/selectivity/receptors
# ---------------------------------------------------------------------------

@router.post("/selectivity/receptors")
def upload_receptors(body: ReceptorUploadRequest):
    """SSTR1/3/4/5 PDB 텍스트를 업로드하고 파일로 저장한다.

    저장 경로: runs_local/selectivity/receptors/{sstr1,sstr3,sstr4,sstr5}.pdb
    이후 /run 호출 시 receptor_pdbs 를 생략하면 이 파일이 자동으로 사용된다.
    """
    RECEPTOR_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths: Dict[str, str] = {}

    # PDB 필드 (확장자 .pdb 저장)
    pdb_field_map = {
        "sstr1": body.sstr1_pdb,
        "sstr3": body.sstr3_pdb,
        "sstr4": body.sstr4_pdb,
        "sstr5": body.sstr5_pdb,
    }
    # CIF 필드 (확장자 .cif 보존)
    cif_field_map = {
        "sstr1": body.sstr1_cif,
        "sstr3": body.sstr3_cif,
        "sstr4": body.sstr4_cif,
        "sstr5": body.sstr5_cif,
    }

    for name, text, ext in [
        *[(n, t, ".pdb") for n, t in pdb_field_map.items()],
        *[(n, t, ".cif") for n, t in cif_field_map.items()],
    ]:
        if not text:
            continue
        if len(text) > 10 * 1024 * 1024:  # 10 MB 제한
            raise HTTPException(
                status_code=413,
                detail=f"{name} 구조 파일 크기가 10 MB를 초과합니다.",
            )
        dest = RECEPTOR_DIR / f"{name}{ext}"
        dest.write_text(text, encoding="utf-8")
        saved_paths[name] = str(dest)
        logger.info("[selectivity] 수용체 구조 저장 (%s): %s → %s", ext, name, dest)

    if not saved_paths:
        raise HTTPException(
            status_code=400,
            detail="업로드된 PDB 없음. sstr1_pdb / sstr3_pdb / sstr4_pdb / sstr5_pdb 중 하나 이상을 포함해야 합니다.",
        )

    return {
        "saved_paths": saved_paths,
        "message": f"{len(saved_paths)}개 수용체 PDB 저장 완료.",
    }




# ---------------------------------------------------------------------------
# POST /api/selectivity/upload
# ---------------------------------------------------------------------------

@router.post("/selectivity/upload")
async def upload_receptor_file(target: str = Form(...), file: UploadFile = File(...)):
    """Upload one receptor structure from the React selectivity UI.

    The existing /selectivity/receptors endpoint accepts JSON text fields.
    The frontend sends FormData with target + file, so this adapter keeps both
    contracts available without changing the UI call site.
    """
    receptor = target.strip().lower()
    if receptor not in SUPPORTED_RECEPTORS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 수용체입니다: {target}. 허용값: {', '.join(SUPPORTED_RECEPTORS)}",
        )

    filename = Path(file.filename or '').name
    suffix = Path(filename).suffix.lower()
    if suffix not in ('.pdb', '.cif', '.mmcif'):
        raise HTTPException(
            status_code=400,
            detail="지원 파일 형식은 .pdb, .cif, .mmcif 입니다.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="업로드된 파일이 비어 있습니다.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"{receptor} 구조 파일 크기가 10 MB를 초과합니다.")

    try:
        structure_text = content.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="구조 파일은 UTF-8 텍스트여야 합니다.") from exc

    ext = '.cif' if suffix == '.mmcif' else suffix
    RECEPTOR_DIR.mkdir(parents=True, exist_ok=True)
    dest = RECEPTOR_DIR / f"{receptor}{ext}"
    dest.write_text(structure_text, encoding='utf-8')
    logger.info("[selectivity] UI 수용체 파일 업로드: %s (%s) -> %s", receptor, filename, dest)

    return {
        "target": receptor,
        "saved_path": str(dest),
        "format": ext.lstrip('.'),
        "size_bytes": len(content),
        "message": f"{receptor.upper()} 수용체 파일 저장 완료.",
    }

# ---------------------------------------------------------------------------
# POST /api/selectivity/run
# ---------------------------------------------------------------------------

@router.post("/selectivity/run")
def run_selectivity(body: SelectivityRunRequest, background_tasks: BackgroundTasks):
    """Off-target 선택성 도킹 잡을 비동기로 시작한다.

    - 후보당 SSTR1/3/4/5 에 대한 도킹을 BackgroundTask 로 실행
    - 즉시 job_id 를 반환; GET /status/{job_id} 로 진행 상태 폴링
    - candidate_sequences 제공 시 PyRosetta FlexPepDock production 모드
    - SSTR2 스코어는 최근 archive 에서 자동 조회 (없으면 -5.0 기본값)
    - receptor_pdbs 생략 시: 업로드 파일 → data/ CIF → estimation 모드 순서
    """
    # 후보 ID 안전성 검증
    for cid in body.candidate_ids:
        try:
            _safe_id(cid, "candidate_id")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    job_id = f"sel_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    # 수용체 경로 결정
    receptor_paths = _resolve_receptor_paths(body.receptor_pdbs)

    # 후보 서열 맵 (없으면 빈 딕셔너리)
    candidate_sequences = dict(body.candidate_sequences or {})

    # SSTR2 스코어 로드
    sstr2_scores = dict(body.sstr2_score_override or {})
    missing = [cid for cid in body.candidate_ids if cid not in sstr2_scores]
    if missing:
        loaded = _load_sstr2_scores(missing, candidate_sequences)
        sstr2_scores.update(loaded)

    production_mode = bool(candidate_sequences) and any(receptor_paths.values())
    mode_label = "production (PyRosetta)" if production_mode else "estimation"

    # 잡 초기 상태 기록
    _write_status(job_id, {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "total_tasks": len(body.candidate_ids) * len(SUPPORTED_RECEPTORS),
        "completed_tasks": 0,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "candidate_ids": body.candidate_ids,
        "receptor_paths": {k: v for k, v in receptor_paths.items()},
        "mode": mode_label,
        "results": [],
    })

    # BackgroundTask 에 도킹 함수 등록
    background_tasks.add_task(
        _run_selectivity_job,
        job_id=job_id,
        candidate_ids=body.candidate_ids,
        candidate_sequences=candidate_sequences,
        receptor_paths=receptor_paths,
        sstr2_scores=sstr2_scores,
        margin_min=body.selectivity_margin_min,
        offtarget_max=body.offtarget_max_allowed,
        nstruct=body.nstruct,
    )

    logger.info(
        "[selectivity] 잡 %s 등록 [%s]: 후보 %d개, 수용체=%s",
        job_id, mode_label, len(body.candidate_ids),
        {k: bool(v) for k, v in receptor_paths.items()},
    )

    return {
        "job_id": job_id,
        "status": "started",
        "mode": mode_label,
        "total_tasks": len(body.candidate_ids) * len(SUPPORTED_RECEPTORS),
        "candidate_count": len(body.candidate_ids),
        "receptors_available": [k for k, v in receptor_paths.items() if v],
        "nstruct": body.nstruct,
    }


# ---------------------------------------------------------------------------
# GET /api/selectivity/status/{job_id}
# ---------------------------------------------------------------------------

@router.get("/selectivity/status/{job_id}")
def get_selectivity_status(job_id: str):
    """잡 진행 상태를 반환한다.

    응답 필드:
        status:          "queued" | "running" | "completed" | "failed"
        progress:        0~100 (%)
        total_tasks:     전체 도킹 작업 수
        completed_tasks: 완료된 도킹 작업 수
        results:         완료된 후보 부분 결과 (도킹 완료 순)
        confidence_grade: "C" — selectivity_margin은 dock_score 기반 (Ki 상관 미검증)
        confidence_warnings: 해석 주의 사항 목록

    ⚠️ confidence_grade "C": selectivity_margin ≠ Ki selectivity (M5-P4).
    """
    try:
        _safe_id(job_id, "job_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 job_id")

    # 인메모리 우선 조회
    with _job_lock:
        data = _jobs.get(job_id)

    if data is None:
        data = _read_status_file(job_id)

    if data is None:
        raise HTTPException(status_code=404, detail=f"잡을 찾을 수 없습니다: {job_id}")

    return attach_confidence(data, "/selectivity/status/{job_id}")


# ---------------------------------------------------------------------------
# GET /api/selectivity/results/{job_id}
# ---------------------------------------------------------------------------

@router.get("/selectivity/results/{job_id}")
def get_selectivity_results(job_id: str):
    """완료된 선택성 스크리닝 결과를 반환한다.

    응답 필드:
        job_id:     잡 식별자
        candidates: 후보별 상세 결과 리스트
          - candidate_id
          - sstr2_ddg, sstr1_ddg, sstr3_ddg, sstr4_ddg, sstr5_ddg (kcal/mol)
          - selectivity_margin: sstr2 - worst_offtarget (음수 = SSTR2 선택적)
          - selectivity_index:  -selectivity_margin (양수가 좋음, UI용)
          - offtarget_max_score, offtarget_max_receptor
          - passed: 선택성 게이트 통과 여부
        summary:
          - total, passed, failed
          - margin_min_used, offtarget_max_used
    """
    try:
        _safe_id(job_id, "job_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 job_id")

    # 완료 여부 확인
    with _job_lock:
        status_data = _jobs.get(job_id)
    if status_data is None:
        status_data = _read_status_file(job_id)

    if status_data is None:
        raise HTTPException(status_code=404, detail=f"잡을 찾을 수 없습니다: {job_id}")

    job_status = status_data.get("status")
    if job_status not in ("completed",):
        raise HTTPException(
            status_code=202,
            detail=f"잡이 아직 완료되지 않았습니다. 현재 상태: {job_status} ({status_data.get('progress', 0)}%)",
        )

    # 결과 파일 로드
    results_path = _job_dir(job_id) / "results.json"
    result_data = None
    if results_path.exists():
        try:
            result_data = json.loads(results_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("[selectivity] 결과 파일 읽기 실패 (%s): %s", job_id, exc)

    if result_data is None:
        result_data = {
            "job_id": job_id,
            "candidates": status_data.get("results", []),
            "summary": {
                "total": len(status_data.get("results", [])),
                "passed": sum(1 for r in status_data.get("results", []) if r.get("passed")),
                "failed": sum(1 for r in status_data.get("results", []) if not r.get("passed")),
            },
        }

    # sstr2_ddg=-5.0 (기본값)인 후보를 아카이브에서 재조회하여 보정
    candidates = result_data.get("candidates", [])
    stale = [c for c in candidates if c.get("sstr2_ddg") == -5.0]
    if stale:
        seq_map = {c.get("sequence", ""): c for c in stale if c.get("sequence")}
        ids = [c.get("seq_id") or c.get("candidate_id", "") for c in stale]
        refreshed = _load_sstr2_scores(ids, {c.get("seq_id", c.get("candidate_id", "")): c.get("sequence", "") for c in stale})
        for c in stale:
            cid = c.get("seq_id") or c.get("candidate_id", "")
            new_score = refreshed.get(cid, -5.0)
            if new_score != -5.0:
                c["sstr2_ddg"] = new_score

    # P1-4: confidence_grade "C" 자동 주입
    return attach_confidence(result_data, "/selectivity/results/{job_id}")


# ---------------------------------------------------------------------------
# GET /api/selectivity/jobs  (보조: 전체 잡 목록)
# ---------------------------------------------------------------------------

@router.get("/selectivity/jobs")
def list_selectivity_jobs():
    """실행된 selectivity 잡 목록을 반환한다 (최근 20개)."""
    SELECTIVITY_BASE.mkdir(parents=True, exist_ok=True)
    job_dirs = sorted(
        (d for d in SELECTIVITY_BASE.iterdir() if d.is_dir() and d.name.startswith("sel_")),
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )[:20]

    jobs = []
    for d in job_dirs:
        status_file = d / "status.json"
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding="utf-8"))
                jobs.append({
                    "job_id": data.get("job_id", d.name),
                    "status": data.get("status", "unknown"),
                    "progress": data.get("progress", 0),
                    "candidate_count": len(data.get("candidate_ids", data.get("results", []))),
                    "queued_at": data.get("queued_at"),
                    "finished_at": data.get("finished_at"),
                })
            except (json.JSONDecodeError, OSError):
                jobs.append({"job_id": d.name, "status": "unknown"})

    return {"jobs": jobs, "count": len(jobs)}
