"""Selectivity screening — SSTR1/3/4/5 receptor management + margin calculation."""
from __future__ import annotations

import uuid
import shutil
import threading
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from backend.state import REPO_ROOT, SST_DATA_DIR

router = APIRouter()
logger = logging.getLogger(__name__)

# 옵션 B (2026-05-20): SST_DATA_DIR env 기반 경로 (state.py 에서 import).
# env 미설정 시 기존 경로(REPO_ROOT/data/somatostatin_receptor)와 동일.
_DATA_DIR = SST_DATA_DIR
# 내부 저장용 대문자 키 (파일명 규칙과 일치)
_RECEPTORS = {
    "SSTR1": {"pdb_id": "9IK8", "file": "SSTR1_9IK8.cif"},
    "SSTR2": {"pdb_id": "7XNA", "file": "SSTR2_7XNA.cif"},
    "SSTR3": {"pdb_id": "8XIR", "file": "SSTR3_8XIR.cif"},
    "SSTR4": {"pdb_id": "7XMT", "file": "SSTR4_7XMT.cif"},
    "SSTR5": {"pdb_id": "8ZBJ", "file": "SSTR5_8ZBJ.cif"},
}

# 수정 1: 프론트엔드 useSelectivity.ts:4 와 동일하게 소문자 키 사용
_OFFTARGET_RECEPTORS = ["sstr1", "sstr3", "sstr4", "sstr5"]

# 수정 2: step05b_selectivity.py compute_selectivity_margin 과 동일한 임계값
# gate_thresholds.yaml: selectivity_margin_min=10.0, offtarget_max_allowed=-15.0
_SELECTIVITY_MARGIN_MIN: float = 10.0
_OFFTARGET_MAX_ALLOWED: float = -15.0


@router.get("/selectivity/receptors")
def list_receptors():
    """List all SSTR receptors and their availability.
    Returns both array (legacy) and dict (frontend useSelectivity.ts) formats.
    """
    receptors_dict = {}
    for name, info in _RECEPTORS.items():
        filepath = _DATA_DIR / info["file"]
        exists = filepath.exists()
        size_bytes = filepath.stat().st_size if exists else 0
        receptors_dict[name.lower()] = {
            "name": name,
            "pdb_id": info["pdb_id"],
            "path": str(filepath) if exists else None,
            "format": "cif" if filepath.suffix == ".cif" else "pdb",
            "source": "local",
            "loaded": exists,
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 1) if exists else 0,
        }
    # 옵션 D (2026-05-20): receptor 0개 로드 시 silent 통과 방지.
    # silent estimation fallback 의 원인은 수신자 없이 돌아가는 것이므로 명시 로그 필수.
    loaded_count = sum(1 for v in receptors_dict.values() if v["loaded"])
    if loaded_count == 0:
        logger.error(
            "⚠ selectivity receptors 0/%d loaded — path=%s",
            len(_RECEPTORS),
            _DATA_DIR,
        )
    return {"receptors": receptors_dict}


@router.post("/selectivity/upload")
async def upload_receptor(target: str = Form(...), file: UploadFile = File(...)):
    """Upload a receptor structure file (PDB or CIF)."""
    # 프론트엔드가 소문자로 보낼 수 있으므로 대문자로 정규화
    target_upper = target.upper()
    if target_upper not in _RECEPTORS:
        raise HTTPException(status_code=400, detail=f"Unknown receptor: {target}. Must be one of {list(_RECEPTORS.keys())}")
    target = target_upper

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix.lower() or ".cif"
    dest = _DATA_DIR / f"{target}_{_RECEPTORS[target]['pdb_id']}{suffix}"

    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "status": "uploaded",
        "target": target,
        "path": str(dest),
        "size_kb": round(len(content) / 1024, 1),
    }


@router.get("/selectivity/structure/{receptor_name}")
def serve_receptor_structure(receptor_name: str):
    """Serve receptor structure file for 3D viewer."""
    # 소문자로 들어올 수 있으므로 대문자로 정규화
    receptor_name = receptor_name.upper()
    if receptor_name not in _RECEPTORS:
        raise HTTPException(status_code=404, detail=f"Unknown receptor: {receptor_name}")

    info = _RECEPTORS[receptor_name]
    filepath = _DATA_DIR / info["file"]
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Structure file not found: {info['file']}")

    from fastapi.responses import Response
    content_type = "chemical/x-cif" if filepath.suffix == ".cif" else "chemical/x-pdb"
    return Response(
        content=filepath.read_bytes(),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=300"},
    )


# ─── Selectivity analysis jobs ─────────────────────────────────────────────────

_JOBS: dict[str, dict[str, Any]] = {}
_job_lock = threading.Lock()


def _get_receptor_pdb(receptor_name_upper: str) -> str | None:
    """Get receptor PDB path — convert CIF→PDB if needed.
    Args:
        receptor_name_upper: 반드시 대문자 (예: "SSTR1"). 내부 _RECEPTORS 키와 일치해야 함.
    """
    info = _RECEPTORS.get(receptor_name_upper)
    if not info:
        return None
    cif_path = _DATA_DIR / info["file"]
    if not cif_path.exists():
        return None
    # PDB 변환 파일 확인 (캐시)
    pdb_path = _DATA_DIR / f"{receptor_name_upper}_{info['pdb_id']}.pdb"
    if pdb_path.exists():
        return str(pdb_path)
    # CIF → PDB 변환
    try:
        from Bio.PDB import MMCIFParser, PDBIO
        parser = MMCIFParser(QUIET=True)
        structure = parser.get_structure(receptor_name_upper, str(cif_path))
        io = PDBIO()
        io.set_structure(structure)
        io.save(str(pdb_path))
        return str(pdb_path)
    except Exception:
        return str(cif_path)  # CIF 직접 사용 시도


def _build_pdb_index(runs_dir: Path) -> tuple[dict[str, str], str]:
    """가장 최근 run에서 candidate_id → PDB 경로 인덱스와 baseline PDB 경로를 반환.

    파일명 규칙: cand_001.pdb, cand_007.pdb (3자리 또는 4자리 숫자)
    candidate_id 추출: "cand_001.pdb" → "001", "cand_007.pdb" → "007"

    G-1 fix (2026-05-20): be-fe-trace 분석 결과 FE 가 실제로 보내는 형식은
    "iter04_cand004" (iter prefix 포함, 4자리 zero-pad). 기존 등록 키와 매칭 안 돼
    항상 estimation fallback 으로 빠지는 root-cause 를 수정.

    등록 키 (per cand_*.pdb 파일):
      "001"              — 숫자 raw (기존)
      "1"                — lstrip("0") (기존)
      "var001"           — var prefix (기존)
      "iter04_cand001"   — FE 실제 형식 (G-1 신규)
      "cand001"          — underscore 없는 변형 (G-1 신규)
      "cand_001"         — underscore 있는 변형 (G-1 신규)

    Returns:
        (pdb_index, sstr2_complex): pdb_index는 {cid: pdb_path}, sstr2_complex은 baseline 경로 (없으면 "")
    """
    pdb_index: dict[str, str] = {}
    sstr2_complex = ""

    def _iter_sort_key(p: Path) -> tuple[int, str]:
        # K-1 fix (2026-05-26): alphabet sort 가 "iter_2" > "iter_10" 으로
        # 잘못 정렬해 가장 최근 iter 가 아닌 엉뚱한 PDB 가 선택되던 버그.
        # 숫자 부분을 int 로 추출해 자연 정렬한다.
        parts = p.name.split("_", 1)
        try:
            return (int(parts[1]) if len(parts) == 2 else -1, p.name)
        except ValueError:
            return (-1, p.name)

    for run_dir in sorted(runs_dir.glob("*/sst14_agentic_mutdock"), reverse=True):
        # 가장 최근 run에서 모든 iter의 cand_*.pdb 수집 (자연 정렬, 최신 iter 우선)
        for iter_dir in sorted(run_dir.glob("iter_*"), key=_iter_sort_key, reverse=True):
            # G-1: iter 번호 추출 — "iter_04" → "04"
            iter_parts = iter_dir.name.split("_", 1)
            iter_str = iter_parts[1] if len(iter_parts) == 2 else iter_dir.name

            for pdb in iter_dir.glob("cand_*.pdb"):
                stem = pdb.stem  # "cand_001", "cand_007.val1" 등
                # 숫자 부분 추출: "cand_001" → "001"
                parts = stem.split("_", 1)
                if len(parts) == 2:
                    cid_raw = parts[1].split(".")[0]  # "001.val1" → "001"
                    pdb_path_str = str(pdb)
                    # 기존 키: 숫자 raw, lstrip 0, var prefix
                    pdb_index.setdefault(cid_raw, pdb_path_str)
                    pdb_index.setdefault(cid_raw.lstrip("0") or "0", pdb_path_str)
                    pdb_index.setdefault(f"var{cid_raw}", pdb_path_str)
                    # G-1 신규 키: FE 실제 형식 "iter04_cand001"
                    pdb_index.setdefault(f"iter{iter_str}_cand{cid_raw}", pdb_path_str)
                    # G-1 신규 키: underscore 없는/있는 변형
                    pdb_index.setdefault(f"cand{cid_raw}", pdb_path_str)
                    pdb_index.setdefault(f"cand_{cid_raw}", pdb_path_str)

        # baseline_refined.pdb 경로 (한 번만 찾으면 됨)
        baseline = run_dir / "baseline_refined.pdb"
        if baseline.exists():
            sstr2_complex = str(baseline)

        # 첫 번째(가장 최근) run만 사용
        if pdb_index:
            break

    logger.info("PDB 인덱스 빌드 완료: %d entries, baseline=%s", len(pdb_index), sstr2_complex or "없음")
    return pdb_index, sstr2_complex


def _run_analysis_thread(
    job_id: str,
    candidate_ids: list,
    candidate_sequences: list,
    sstr2_ddgs: dict,
) -> None:
    """백그라운드 스레드 — 도킹 계산 수행 후 _JOBS에 결과 저장.

    수정 사항:
    - 수정 1: 소문자 receptor 키 사용 (_OFFTARGET_RECEPTORS = lowercase)
    - 수정 2: margin = worst_ot - sstr2_ddg (step05b 동일 부호 컨벤션)
    - 수정 2: gate_pass = margin >= 10.0 and worst_ot >= -15.0 (gate_thresholds.yaml 값)
    - 수정 3: 루프 진입 전 cid→PDB 인덱스 한 번 빌드, candidate마다 다른 PDB 사용
    """
    try:
        # step05b_selectivity 사용 시도
        try:
            import sys
            sys.path.insert(0, str(REPO_ROOT / "AG_src"))
            from AG_src.pipeline.step05b_selectivity import dock_against_offtarget
            _has_selectivity = True
        except ImportError:
            _has_selectivity = False

        runs_dir = REPO_ROOT / "runs" / "pyrosetta_flow"

        # 수정 3: 루프 전에 cid→PDB 인덱스 한 번만 빌드
        pdb_index, sstr2_complex = _build_pdb_index(runs_dir)

        results = []
        # 옵션 D (2026-05-20): estimation fallback 발생 카운터.
        _estimation_fallback_count = 0

        for cid, seq in zip(candidate_ids, candidate_sequences):
            # Soft cancel 체크: cancel endpoint가 True로 설정하면 루프 중단
            with _job_lock:
                if _JOBS[job_id].get("cancelled"):
                    _JOBS[job_id]["status"] = "cancelled"
                    return

            # 수정 3: candidate별 PDB 매핑 (못 찾으면 빈 문자열 → estimation fallback)
            candidate_pdb = pdb_index.get(cid, "")
            if not candidate_pdb:
                # 마지막 수단: cid의 숫자 부분으로 재시도 (예: "cand_007" → "007")
                numeric_part = "".join(filter(str.isdigit, cid))
                candidate_pdb = pdb_index.get(numeric_part, "")
            if not candidate_pdb:
                logger.warning("candidate_id=%s 에 대한 PDB를 찾지 못함 — estimation 사용", cid)

            offtarget_scores: dict[str, float] = {}
            mode = "estimation"

            for receptor in _OFFTARGET_RECEPTORS:
                # 수정 1: 소문자 키(_OFFTARGET_RECEPTORS)를 대문자로 변환해 _get_receptor_pdb 호출
                receptor_upper = receptor.upper()
                receptor_pdb = _get_receptor_pdb(receptor_upper)

                if _has_selectivity and receptor_pdb:
                    try:
                        score = dock_against_offtarget(
                            candidate_pdb=candidate_pdb,
                            receptor_pdb=receptor_pdb,
                            engine="pyrosetta",
                            config={"selectivity": {"offtarget_timeout_sec": 120}},
                            on_target_score=None,
                            sstr2_complex_pdb=sstr2_complex,
                        )
                        # 수정 1: 결과 dict 키를 소문자로 저장 (프론트와 일치)
                        offtarget_scores[receptor] = round(score, 2)
                        if sstr2_complex and Path(sstr2_complex).exists():
                            mode = "production"
                    except Exception as e:
                        logger.warning("receptor=%s dock 실패: %s — estimation 사용", receptor, e)
                        import random
                        offtarget_scores[receptor] = round(random.gauss(-5.0, 3.0), 2)
                else:
                    import random
                    # 수정 1: 결과 dict 키를 소문자로 저장
                    offtarget_scores[receptor] = round(random.gauss(-5.0, 3.0), 2)

            sstr2_ddg = sstr2_ddgs.get(cid, -15.0)
            worst_ot = min(offtarget_scores.values()) if offtarget_scores else 0.0

            # 수정 2: margin = worst_ot - sstr2_ddg (step05b compute_selectivity_margin:400 동일)
            # 양수 = SSTR2가 off-target보다 강하게 결합 → 선택적
            margin = worst_ot - sstr2_ddg

            # 수정 2: gate_pass = margin >= margin_min AND worst_ot >= offtarget_max_allowed
            # gate_thresholds.yaml: selectivity_margin_min=10.0, offtarget_max_allowed=-15.0
            gate_pass = (margin >= _SELECTIVITY_MARGIN_MIN) and (worst_ot >= _OFFTARGET_MAX_ALLOWED)

            # 수정 1: worst receptor 키도 소문자
            worst_receptor = min(offtarget_scores, key=offtarget_scores.get) if offtarget_scores else ""

            results.append({
                "candidate_id": cid,
                "sequence": seq,
                "sstr2_ddg": round(sstr2_ddg, 2),
                "offtarget_scores": offtarget_scores,  # 소문자 키
                "offtarget_max_receptor": worst_receptor,  # 소문자 키
                "offtarget_max_score": round(worst_ot, 2),
                "selectivity_margin": round(margin, 2),
                "gate_pass": gate_pass,
                "mode": mode,
            })

            # 옵션 D (2026-05-20): estimation fallback 발생 시 카운터 누적
            if mode == "estimation":
                _estimation_fallback_count += 1

            # 진행 상태 갱신
            _JOBS[job_id]["completed_tasks"] += 1

        # 옵션 D (2026-05-20): estimation fallback 1건 이상 시 job 에 warning 필드 누적.
        # 기존 키(status/candidates/error/cancelled) 변경 없이 신규 키만 추가.
        if _estimation_fallback_count > 0:
            logger.warning(
                "job_id=%s — %d/%d candidates 가 estimation fallback 사용",
                job_id,
                _estimation_fallback_count,
                len(candidate_ids),
            )
            _JOBS[job_id]["warning"] = "estimation_fallback"

        _JOBS[job_id]["status"] = "completed"
        _JOBS[job_id]["candidates"] = results

    except Exception as exc:
        logger.exception("job_id=%s 분석 실패", job_id)
        _JOBS[job_id]["status"] = "failed"
        _JOBS[job_id]["error"] = str(exc)


@router.post("/selectivity/run")
def run_selectivity(body: dict):
    """Start selectivity analysis — real FlexPepDock or estimation fallback."""
    candidate_ids = body.get("candidate_ids", [])
    raw_seqs = body.get("candidate_sequences", [])

    # Support both list and dict formats from frontend
    if isinstance(raw_seqs, dict):
        candidate_sequences = [raw_seqs.get(cid, "") for cid in candidate_ids]
    else:
        candidate_sequences = raw_seqs

    if not candidate_ids or not candidate_sequences:
        raise HTTPException(status_code=400, detail="candidate_ids and candidate_sequences required")

    job_id = str(uuid.uuid4())[:8]
    sstr2_ddgs: dict = body.get("sstr2_ddgs", {})

    _JOBS[job_id] = {
        "status": "running",
        "total_tasks": len(candidate_ids),
        "completed_tasks": 0,
        "candidates": [],
        "error": None,
        "cancelled": False,
    }

    threading.Thread(
        target=_run_analysis_thread,
        args=(job_id, candidate_ids, candidate_sequences, sstr2_ddgs),
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "started", "total": len(candidate_ids)}


@router.get("/selectivity/status/{job_id}")
def selectivity_status(job_id: str):
    """Poll job status."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "total_tasks": job["total_tasks"],
        "completed_tasks": job["completed_tasks"],
        "error": job.get("error"),
    }


@router.get("/selectivity/results/{job_id}")
def selectivity_results(job_id: str):
    """Get analysis results — keys mapped for frontend useSelectivity.ts."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=202, detail="Analysis still running")
    # Map backend keys to frontend expected keys
    mapped = []
    for c in job["candidates"]:
        mapped.append({
            "seq_id": c.get("candidate_id", ""),
            "candidate_id": c.get("candidate_id", ""),
            "sequence": c.get("sequence", ""),
            "sstr2_ddg": c.get("sstr2_ddg", 0),
            "offtarget_ddg": c.get("offtarget_scores", {}),  # frontend expects this key
            "offtarget_scores": c.get("offtarget_scores", {}),
            "offtarget_max_receptor": c.get("offtarget_max_receptor", ""),
            "offtarget_max_score": c.get("offtarget_max_score", 0),
            "wsm": c.get("selectivity_margin", 0),  # frontend expects wsm
            "selectivity_margin": c.get("selectivity_margin", 0),
            "tier": 3 if c.get("gate_pass") else 0,
            "passed": c.get("gate_pass", False),  # frontend expects passed
            "gate_pass": c.get("gate_pass", False),
            "mode": c.get("mode", "estimation"),
        })
    # 옵션 D (2026-05-20): warning 필드 포함 (신규 키 추가; 기존 키/타입 변경 없음).
    # None 이면 estimation_fallback 없음, "estimation_fallback" 이면 1건 이상 발생.
    return {
        "candidates": mapped,
        "mode": job["candidates"][0]["mode"] if job["candidates"] else "estimation",
        "warning": job.get("warning"),
    }


@router.post("/selectivity/cancel/{job_id}")
def cancel_selectivity(job_id: str):
    """Soft-cancel a running selectivity job.

    후보 루프의 다음 iteration에서 cancelled 플래그를 감지하고 조기 종료.
    subprocess (dock_against_offtarget) PID kill은 미채택 (G-6 Sprint 결정):
    현재 실행 중인 subprocess는 최대 offtarget_timeout_sec(120s) 대기 후 자연 종료.
    """
    with _job_lock:
        job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        if job["status"] in ("completed", "failed", "cancelled"):
            raise HTTPException(status_code=409, detail=f"Job already {job['status']}")
        job["cancelled"] = True
    return {"ok": True, "job_id": job_id, "status": "cancellation_requested"}


@router.get("/selectivity/jobs")
def list_jobs():
    """List all selectivity jobs (for frontend auto-resume on mount)."""
    jobs = []
    for jid, job in _JOBS.items():
        jobs.append({
            "job_id": jid,
            "status": job["status"],
            "total_tasks": job["total_tasks"],
            "completed_tasks": job["completed_tasks"],
            "progress": round(job["completed_tasks"] / max(job["total_tasks"], 1) * 100),
        })
    return {"jobs": jobs}
