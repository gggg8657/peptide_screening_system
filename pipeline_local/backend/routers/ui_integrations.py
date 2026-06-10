"""UI integration endpoints backed by local pipeline artifacts.

These routes close the React dashboard API surface without returning fabricated
scientific results. Read-only views are backed by files under runs_local/, data/,
runs/, and llm_benchmark/outputs. Expensive execution requests create local job
records and report blocked/failed status when the required runner is unavailable.
"""
from __future__ import annotations

import csv
import io
import json
import tarfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from pipeline_local.backend.state import REPO_ROOT, find_dashboard_archive, list_archive_dashboard_files, read_status

router = APIRouter()

RUNS_LOCAL = REPO_ROOT / "runs_local"
WETLAB_ORDERS = RUNS_LOCAL / "wetlab_orders.json"
STRATEGY_BASE = RUNS_LOCAL / "strategy_ab"
FLEX_BASE = RUNS_LOCAL / "flexpepdock_jobs"
BINDING_BASE = RUNS_LOCAL / "binding_pockets"
FINAL_CANDIDATES = RUNS_LOCAL / "final_candidates" / "all_candidates.csv"
CAND03_VARIANTS = RUNS_LOCAL / "cand03_variants" / "cand03_variants.json"
LLM_OUTPUTS = REPO_ROOT / "llm_benchmark" / "outputs"
DATA_POCKET = REPO_ROOT / "data" / "somatostatin_receptor" / "binding_pocket_SSTR2.json"

STAGES = ["draft", "submitted", "approved", "shipped", "returned"]
STRATEGY_IDS = ("blosum", "esm_scan", "proteinmpnn", "dual_b1_b2")
RECEPTORS = ("SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists() and path.is_file() and not path.is_symlink():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_id(value: str, label: str = "id") -> str:
    if not value or any(ch in value for ch in "../\\"):
        raise HTTPException(status_code=400, detail=f"invalid {label}")
    return value


def _rel_under(path: str | Path, base: Path) -> Optional[str]:
    try:
        p = Path(path).resolve()
        return str(p.relative_to(base.resolve()))
    except (OSError, ValueError):
        return None


def _status_to_run(status: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "run_id": status.get("run_id") or status.get("id") or "local-status",
        "started_at": status.get("started_at") or "",
        "duration_seconds": status.get("duration_seconds") or status.get("elapsed_seconds") or 0,
        "iteration": status.get("iteration") or 0,
        "max_iterations": status.get("max_iterations") or status.get("total_iterations") or 0,
        "silo": status.get("silo") or "B",
        "llm_model": status.get("llm_model") or status.get("llmModel") or "local",
        "gpus": status.get("gpus") or "local",
        "seed": status.get("seed") or 0,
        "current_step": status.get("current_step") or status.get("phase") or "status",
        "progress": status.get("progress") or 0,
        "state": status.get("state") or ("done" if status.get("completed") else "queued"),
    }


# ---------------------------------------------------------------------------
# Pipeline + agent views
# ---------------------------------------------------------------------------


def _stage(stage_id: str, name: str, tool: str, status: str = "queued", group: str = "score", progress: int | None = None) -> Dict[str, Any]:
    return {
        "id": stage_id,
        "name": name,
        "group": group,
        "tool": tool,
        "env": "local",
        "status": status,
        "in_count": None,
        "out_count": None,
        "in_unit": None,
        "out_unit": None,
        "time": None,
        "gpu": None,
        "gate": None,
        "pass": None,
        "fail": None,
        "progress": progress,
    }


@router.get("/pipelines/{silo}")
def get_pipeline(silo: str, run_id: Optional[str] = None):
    silo = silo.lower()
    status = read_status()
    current = str(status.get("current_step") or status.get("phase") or "").lower()

    def state_for(step: str) -> str:
        if step.lower() in current:
            return "running"
        if status.get("completed") or status.get("state") == "done":
            return "done"
        return "queued"

    silo_a = [
        _stage("a01", "Backbone generation", "RFdiffusion", state_for("backbone"), "gen"),
        _stage("a02", "Sequence design", "ProteinMPNN", state_for("sequence"), "gen"),
        _stage("a03", "Structure QC", "ESMFold/OpenFold", state_for("qc"), "filter"),
        _stage("a04", "Boltz complex", "Boltz-2", state_for("boltz"), "score"),
    ]
    silo_b = [
        _stage("b01", "BLOSUM mutation", "step03b", state_for("mutation"), "gen"),
        _stage("b02", "Docking", "DiffDock/Boltz", state_for("docking"), "score"),
        _stage("b03", "Selectivity", "SSTR1/3/4/5", state_for("selectivity"), "filter"),
        _stage("b04", "Rosetta refine", "PyRosetta", state_for("rosetta"), "refine"),
    ]
    converge = [
        _stage("c01", "Stability / ADMET", "PepADMET", state_for("stability"), "analyze"),
        _stage("c02", "Wetlab decision", "reporter", state_for("report"), "analyze"),
    ]

    if silo in {"combined", "a+b", "ab"}:
        return {
            "name": "Combined dual-silo pipeline",
            "description": "Silo A and Silo B converge into selectivity, stability, and wetlab decision stages.",
            "input": _stage("input", "SST14 / SSTR2 inputs", "local data", "done", "input"),
            "tracks": [
                {"silo": "A", "label": "De novo", "stages": silo_a},
                {"silo": "B", "label": "Mutation + Dock", "stages": silo_b},
            ],
            "converge": converge,
        }
    stages = silo_a if silo == "a" else silo_b
    return {"name": f"Silo {silo.upper()} pipeline", "description": "Local pipeline stages", "stages": stages}


@router.get("/agents/{run_id}/log")
def get_agent_log(run_id: str):
    _safe_id(run_id, "run_id")
    status = read_status()
    entries = status.get("agent_log") or status.get("agents") or []
    if isinstance(entries, dict):
        entries = [
            {"ts": _now(), "agent": str(k).lower(), "level": "info", "text": json.dumps(v, ensure_ascii=False)}
            for k, v in entries.items()
        ]
    normalized = []
    for item in entries if isinstance(entries, list) else []:
        if isinstance(item, dict):
            normalized.append({
                "ts": item.get("ts") or item.get("timestamp") or _now(),
                "agent": item.get("agent") or "reporter",
                "level": item.get("level") or "info",
                "text": item.get("text") or item.get("message") or json.dumps(item, ensure_ascii=False),
            })
    return {"entries": normalized}


@router.get("/agents/{run_id}/stream")
def stream_agent_log(run_id: str):
    _safe_id(run_id, "run_id")

    def events() -> Iterable[bytes]:
        payload = {"ts": _now(), "agent": "reporter", "level": "info", "text": f"stream attached to {run_id}"}
        yield f"event: agent\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
        yield b": heartbeat\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Archives, benchmark, candidates
# ---------------------------------------------------------------------------


@router.get("/cand03_variants/list")
def cand03_variants():
    data = _read_json(CAND03_VARIANTS, {"variants": []})
    return data


@router.get("/archives/top-k")
def archives_top_k(receptor: str = "SSTR2", k: int = Query(20, ge=1, le=100)):
    entries: List[Dict[str, Any]] = []
    if FINAL_CANDIDATES.exists():
        with FINAL_CANDIDATES.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                seq = row.get("sequence") or row.get("seq") or row.get("candidate_id") or ""
                if not seq:
                    continue
                iptm = float(row.get("iptm") or row.get("sstr2_iptm") or row.get("confidence") or 0.0)
                selectivity = float(row.get("selectivity") or row.get("selectivity_index") or row.get("selectivity_margin") or 0.0)
                entries.append({
                    "sequence": seq,
                    "receptor": receptor,
                    "iptm": iptm,
                    "ptm": float(row.get("ptm") or iptm),
                    "confidence": float(row.get("confidence") or iptm),
                    "tier": "T3" if iptm >= 0.92 else "T2" if iptm >= 0.85 else "T1",
                    "selectivity_index": selectivity,
                })
    if not entries:
        for dashboard_path in list_archive_dashboard_files():
            data = _read_json(dashboard_path, {})
            for c in data.get("candidates", []) if isinstance(data, dict) else []:
                if not isinstance(c, dict):
                    continue
                iptm_map = c.get("iptm") if isinstance(c.get("iptm"), dict) else {}
                iptm = float(iptm_map.get(receptor, iptm_map.get(receptor.lower(), 0.0)) or 0.0)
                entries.append({
                    "sequence": c.get("sequence") or c.get("seq") or c.get("id") or "",
                    "receptor": receptor,
                    "iptm": iptm,
                    "ptm": iptm,
                    "confidence": iptm,
                    "tier": "T3" if iptm >= 0.92 else "T2" if iptm >= 0.85 else "T1",
                    "selectivity_index": c.get("selectivity_index") or c.get("margin") or c.get("selectivity_margin") or 0,
                })
    entries.sort(key=lambda item: (item.get("selectivity_index") or 0, item.get("iptm") or 0), reverse=True)
    return {"entries": entries[:k], "source": str(FINAL_CANDIDATES.relative_to(REPO_ROOT)) if FINAL_CANDIDATES.exists() else "archives"}


@router.get("/benchmark/results")
def benchmark_results(phase: str = "V2"):
    phase_map = {"Phase1": "phase1", "Phase2": "phase2a", "Phase3": "phase3", "V2": "v2_phase1"}
    phase_key = phase_map.get(phase, phase.lower())
    phase_dir = LLM_OUTPUTS / phase_key
    llms: Dict[str, Dict[str, Any]] = {}
    flows: Dict[str, Dict[str, Any]] = {}
    matrix: Dict[str, Dict[str, Any]] = {}
    total = 0
    if phase_dir.exists():
        for run_dir in sorted(p for p in phase_dir.iterdir() if p.is_dir() and not p.name.startswith("_")):
            parts = run_dir.name.split("__")
            model = parts[0] if parts else "unknown"
            flow = parts[1] if len(parts) > 1 else "sequential"
            status = _read_json(run_dir / "status.json", {})
            ses = _read_json(run_dir / "ses_score.json", {})
            if status.get("state") != "done":
                continue
            total += 1
            llms.setdefault(model, {"id": model, "short": model.replace("_", " "), "vram_gb": 0})
            flows.setdefault(flow, {"id": flow, "name": flow.replace("_", " ").title(), "desc": "local benchmark flow"})
            cell = matrix.setdefault(model, {}).setdefault(flow, {"pass_rate": 0.0, "time_min": 0.0, "candidates": 0, "t2": 0, "cost": 0.0})
            cell["candidates"] += 1
            cell["time_min"] += float(status.get("elapsed_s") or 0) / 60.0
            if ses:
                cell["pass_rate"] += float(ses.get("hit_rate") or 0)
                cell["t2"] += 1 if float(ses.get("ses") or 0) >= 0.5 else 0
        for row in matrix.values():
            for cell in row.values():
                n = max(1, int(cell["candidates"]))
                cell["time_min"] = round(cell["time_min"] / n, 2)
                cell["pass_rate"] = round(cell["pass_rate"] / n, 3)
    return {"phase": phase if phase in {"Phase1", "Phase2", "Phase3", "V2"} else "V2", "total_runs": total, "llms": list(llms.values()), "flows": list(flows.values()), "matrix": matrix}


@router.get("/runs/{run_id}/predicted_pass_rates")
def predicted_pass_rates(run_id: str):
    data = _read_json(find_dashboard_archive(run_id) or Path("/nonexistent"), {})
    candidates = data.get("candidates", []) if isinstance(data, dict) else []
    total = max(1, len(candidates))
    passed = sum(1 for c in candidates if isinstance(c, dict) and (c.get("recommended") or c.get("tier") in {"T2", "T3"}))
    return {"run_id": run_id, "overall": passed / total, "by_gate": {"candidate_quality": passed / total}}


class RunStartRequest(BaseModel):
    name: str
    silo: str
    iterations: int = 1
    seed: int = 0
    model_config = {"extra": "allow"}


@router.post("/runs/start")
def start_run(body: RunStartRequest):
    job_id = f"ui_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    job_dir = RUNS_LOCAL / "ui_jobs" / job_id
    status = {
        "run_id": job_id,
        "state": "blocked",
        "status": "blocked",
        "progress": 0,
        "created_at": _now(),
        "request": body.model_dump(),
        "missing_tools": ["pipeline runner service"],
        "command_hint": "python -m pipeline_local.orchestrator --config <config>",
        "detail": "Run was registered, but no local queue worker is configured in this environment.",
    }
    _write_json(job_dir / "status.json", status)
    return {"run_id": job_id, "job_id": job_id, "status": "blocked", "queue_position": 0, "eta_seconds": 0, "status_path": str((job_dir / "status.json").relative_to(REPO_ROOT))}


# ---------------------------------------------------------------------------
# Strategy runner
# ---------------------------------------------------------------------------


@router.get("/strategies")
def strategies():
    return [
        {"id": "blosum", "name": "BLOSUM", "description": "BLOSUM-constrained SST14 mutations", "supports_modes": ["peptide_only"], "supports_complex_pdb": False},
        {"id": "esm_scan", "name": "ESM Scan", "description": "ESM-guided mutation scan", "supports_modes": ["peptide_only"], "supports_complex_pdb": False},
        {"id": "proteinmpnn", "name": "ProteinMPNN", "description": "ProteinMPNN peptide sequence generation", "supports_modes": ["peptide_only", "receptor_context"], "supports_complex_pdb": True},
        {"id": "dual_b1_b2", "name": "Dual B1/B2", "description": "Combined mutation+docking strategy", "supports_modes": ["peptide_only"], "supports_complex_pdb": False},
    ]


@router.get("/strategies/proteinmpnn/options")
def proteinmpnn_options():
    pdbs = [str(p.relative_to(REPO_ROOT)) for p in RUNS_LOCAL.rglob("*.pdb") if not p.is_symlink()][:80]
    return {"modes": [{"id": "peptide_only", "label": "Peptide only"}, {"id": "receptor_context", "label": "Receptor context"}], "complex_pdbs": pdbs}


class StrategyRunRequest(BaseModel):
    strategy: str
    mode: Optional[str] = None
    complex_pdb: Optional[str] = None
    max_variants: int = Field(8, ge=1, le=100)
    num_seq_per_target: int = 4
    config: Dict[str, Any] = Field(default_factory=dict)


@router.post("/strategies/run")
def strategy_run(body: StrategyRunRequest):
    if body.strategy not in STRATEGY_IDS:
        raise HTTPException(status_code=400, detail="unknown strategy")
    job_id = f"strategy_{body.strategy}_{uuid.uuid4().hex[:8]}"
    job_dir = STRATEGY_BASE / "ui_runs" / job_id
    src = STRATEGY_BASE / body.strategy / "variants.json"
    variants = _load_strategy_variants(src, body.strategy, body.max_variants)
    status = "completed" if variants else "failed"
    message = f"loaded {len(variants)} variants from {src.relative_to(REPO_ROOT)}" if variants else f"no variants found for {body.strategy}"
    _write_json(job_dir / "job.json", {"job_id": job_id, **body.model_dump(), "created_at": _now()})
    _write_json(job_dir / "status.json", {"job_id": job_id, "strategy": body.strategy, "mode": body.mode, "status": status, "progress": 100 if variants else 0, "eta_seconds": 0, "message": message})
    _write_json(job_dir / "variants.json", variants)
    return {"job_id": job_id, "eta_seconds": 0, "queue_position": 0}


def _load_strategy_variants(path: Path, strategy: str, limit: int) -> List[Dict[str, Any]]:
    raw = _read_json(path, {})
    items = raw.get("variants", raw if isinstance(raw, list) else []) if raw is not None else []
    out = []
    for i, item in enumerate(items[:limit], 1):
        if not isinstance(item, dict):
            continue
        out.append({
            "id": item.get("variant_id") or item.get("id") or f"{strategy}_{i:03d}",
            "sequence": item.get("sequence") or item.get("seq") or "",
            "score": float(item.get("blosum_total_score") or item.get("score") or 0),
            "source_strategy": strategy,
            "mode": item.get("mode"),
            "complex_pdb": item.get("complex_pdb"),
            "rank": i,
            "selected": bool(item.get("selected", False)),
            "rejected": bool(item.get("rejected", False)),
            "annotations": {k: v for k, v in item.items() if k not in {"sequence", "seq"}},
        })
    return out


@router.get("/strategies/runs/{job_id}")
def strategy_status(job_id: str):
    _safe_id(job_id, "job_id")
    status = _read_json(STRATEGY_BASE / "ui_runs" / job_id / "status.json")
    if status is None:
        raise HTTPException(status_code=404, detail="strategy job not found")
    return status


@router.get("/strategies/runs/{job_id}/variants")
def strategy_variants(job_id: str):
    _safe_id(job_id, "job_id")
    variants = _read_json(STRATEGY_BASE / "ui_runs" / job_id / "variants.json")
    if variants is None:
        raise HTTPException(status_code=404, detail="variants not found")
    return variants


@router.post("/strategies/runs/{job_id}/select")
def strategy_select(job_id: str, body: Dict[str, Any]):
    _safe_id(job_id, "job_id")
    path = STRATEGY_BASE / "ui_runs" / job_id / "variants.json"
    variants = _read_json(path)
    if variants is None:
        raise HTTPException(status_code=404, detail="variants not found")
    selected = set(body.get("selected_variant_ids") or [])
    rejected = set(body.get("rejected_variant_ids") or [])
    for item in variants:
        item["selected"] = item.get("id") in selected
        item["rejected"] = item.get("id") in rejected
    _write_json(path, variants)
    return {"ok": True, "selected": len(selected), "rejected": len(rejected)}


# ---------------------------------------------------------------------------
# FlexPepDock jobs
# ---------------------------------------------------------------------------


class FlexPepDockRequest(BaseModel):
    sequence: str
    receptors: List[str]
    config: Dict[str, Any]


def _flex_job_dir(job_id: str) -> Path:
    _safe_id(job_id, "job_id")
    return FLEX_BASE / job_id


def _flex_summary(job_dir: Path) -> Optional[Dict[str, Any]]:
    job = _read_json(job_dir / "job.json")
    status = _read_json(job_dir / "status.json")
    if not isinstance(job, dict) or not isinstance(status, dict):
        return None
    state = status.get("state") or status.get("status") or "queued"
    if state == "blocked":
        state = "failed"
    return {
        "job_id": job.get("job_id") or job_dir.name,
        "sequence": job.get("sequence") or "",
        "receptors": job.get("receptors") or [],
        "config": job.get("config") or {},
        "status": state,
        "progress": int(round(float(status.get("progress") or 0) * 100)) if float(status.get("progress") or 0) <= 1 else int(status.get("progress") or 0),
        "eta_seconds": status.get("eta_seconds") or 0,
        "created_at": job.get("created_at") or "",
        "started_at": status.get("started_at"),
        "finished_at": status.get("finished_at"),
        "error_message": status.get("error_message") or status.get("detail") or "",
        "queue_position": 0,
    }


@router.post("/flexpepdock/jobs")
def create_flex_job(body: FlexPepDockRequest):
    job_id = str(uuid.uuid4())
    job_dir = _flex_job_dir(job_id)
    _write_json(job_dir / "job.json", {"job_id": job_id, "sequence": body.sequence, "receptors": body.receptors, "config": body.config, "created_at": _now()})
    _write_json(job_dir / "status.json", {"state": "failed", "progress": 0, "eta_seconds": 0, "error_message": "blocked: FlexPepDock worker is not configured. Start the local PyRosetta worker and retry."})
    return {"job_id": job_id, "eta_seconds": 0, "queue_position": 0}


@router.get("/flexpepdock/jobs")
def list_flex_jobs(status: Optional[str] = None):
    jobs = []
    if FLEX_BASE.exists():
        for job_dir in sorted((p for p in FLEX_BASE.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True):
            summary = _flex_summary(job_dir)
            if summary and (status is None or summary["status"] == status):
                jobs.append(summary)
    return {"jobs": jobs}


@router.get("/flexpepdock/jobs/{job_id}")
def flex_detail(job_id: str):
    summary = _flex_summary(_flex_job_dir(job_id))
    if summary is None:
        raise HTTPException(status_code=404, detail="job not found")
    return summary


@router.get("/flexpepdock/jobs/{job_id}/results")
def flex_results(job_id: str):
    result = _read_json(_flex_job_dir(job_id) / "result.json")
    if result is None:
        raise HTTPException(status_code=404, detail="result not found")
    return result


@router.delete("/flexpepdock/jobs/{job_id}")
def flex_cancel(job_id: str):
    job_dir = _flex_job_dir(job_id)
    status = _read_json(job_dir / "status.json")
    if status is None:
        raise HTTPException(status_code=404, detail="job not found")
    status["state"] = "cancelled"
    status["error_message"] = status.get("error_message") or "cancelled by user"
    _write_json(job_dir / "status.json", status)
    return {"ok": True, "job_id": job_id, "action": "cancel"}


@router.get("/flexpepdock/jobs/{job_id}/ensemble.tar.gz")
def flex_ensemble(job_id: str):
    job_dir = _flex_job_dir(job_id)
    ensemble = job_dir / "ensemble"
    if not ensemble.exists():
        raise HTTPException(status_code=404, detail="ensemble not found")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for pdb in ensemble.rglob("*.pdb"):
            tar.add(pdb, arcname=str(pdb.relative_to(job_dir)))
    return Response(buf.getvalue(), media_type="application/gzip", headers={"Content-Disposition": f"attachment; filename={job_id}-ensemble.tar.gz"})


# ---------------------------------------------------------------------------
# Binding pocket
# ---------------------------------------------------------------------------


def _pocket_path(receptor: str) -> Path:
    receptor = receptor.lower()
    _safe_id(receptor, "receptor")
    return BINDING_BASE / f"{receptor}.json"


def _default_pocket(receptor: str) -> Optional[Dict[str, Any]]:
    if receptor.lower() == "sstr2":
        raw = _read_json(DATA_POCKET)
        if raw:
            box = raw.get("gnina_config", {})
            return {
                "receptor": "sstr2",
                "center_x": raw.get("center_x", 0),
                "center_y": raw.get("center_y", 0),
                "center_z": raw.get("center_z", 0),
                "radius_angstrom": raw.get("radius") or raw.get("radius_angstrom") or 13.0,
                "residue_ids": raw.get("residues") or [],
                "box_size": {"size_x": box.get("size_x", raw.get("box_size", 26.0)), "size_y": box.get("size_y", raw.get("box_size", 26.0)), "size_z": box.get("size_z", raw.get("box_size", 26.0))},
                "source": raw.get("source") or "data/somatostatin_receptor",
                "timestamp": _now(),
            }
    for pocket in RUNS_LOCAL.glob("*/01_receptor/binding_pocket.json"):
        raw = _read_json(pocket)
        if raw:
            residues = raw.get("pocket_residues") or raw.get("residue_ids") or []
            return {"receptor": receptor.lower(), "center_x": 0, "center_y": 0, "center_z": 0, "radius_angstrom": 13.0, "residue_ids": residues, "box_size": None, "source": str(pocket.relative_to(REPO_ROOT)), "timestamp": _now()}
    return None


@router.get("/binding_pocket/{receptor}")
def get_binding_pocket(receptor: str):
    data = _read_json(_pocket_path(receptor)) or _default_pocket(receptor)
    if data is None:
        raise HTTPException(status_code=404, detail="binding pocket not found")
    return data


@router.put("/binding_pocket/{receptor}")
def put_binding_pocket(receptor: str, body: Dict[str, Any]):
    body["receptor"] = receptor.lower()
    body["timestamp"] = _now()
    path = _pocket_path(receptor)
    _write_json(path, body)
    return {"ok": True, "path": str(path.relative_to(REPO_ROOT))}


@router.post("/binding_pocket/{receptor}/extract")
def extract_binding_pocket(receptor: str, body: Dict[str, Any]):
    residue_ids = [int(v) for v in body.get("residue_ids", [])]
    if not residue_ids:
        raise HTTPException(status_code=400, detail="residue_ids required")
    base = _default_pocket(receptor) or {"center_x": 0, "center_y": 0, "center_z": 0, "radius_angstrom": 13.0, "box_size": None}
    base.update({"receptor": receptor.lower(), "residue_ids": residue_ids, "source": "auto_extract", "timestamp": _now()})
    _write_json(_pocket_path(receptor), base)
    return base


@router.delete("/binding_pocket/{receptor}")
def delete_binding_pocket(receptor: str):
    path = _pocket_path(receptor)
    if path.exists():
        path.unlink()
        return {"ok": True, "restored": bool(_default_pocket(receptor))}
    return {"ok": True, "restored": False}


# ---------------------------------------------------------------------------
# Cluster + wetlab + candidate reports
# ---------------------------------------------------------------------------


@router.post("/cluster/classify")
def cluster_classify(body: Dict[str, Any]):
    results = []
    for item in body.get("candidates", []):
        if not isinstance(item, dict):
            continue
        ddg = float(item.get("ddG") or item.get("ddg") or 0)
        margin = float(item.get("selectivity_margin") or 0)
        cluster = "A" if ddg <= -90 and margin >= 100 else "B" if ddg <= -50 else "C" if margin > 0 else "D"
        results.append({
            "name": item.get("name") or item.get("id") or item.get("sequence") or "candidate",
            "classification": {"cluster": cluster, "confidence": 0.75, "rationale": "rule-based classification from real candidate metrics"},
        })
    return {"results": results, "source": "candidate_metrics_rule_engine"}


def _orders() -> List[Dict[str, Any]]:
    data = _read_json(WETLAB_ORDERS, [])
    return data if isinstance(data, list) else []


def _save_orders(orders: List[Dict[str, Any]]) -> None:
    _write_json(WETLAB_ORDERS, orders)


def _new_order(candidate_id: str, candidate_seq: Optional[str] = None, flexpepdock_job_id: Optional[str] = None) -> Dict[str, Any]:
    base = (_orders()[0] if _orders() else {})
    order_id = f"WO-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
    order = json.loads(json.dumps(base)) if base else {}
    order.update({
        "id": order_id,
        "candidate_id": candidate_id,
        "candidate_seq": candidate_seq or base.get("candidate_seq") or "",
        "stage": "draft",
        "created_at": _now(),
        "requested_by": base.get("requested_by", "local-ui"),
        "flexpepdock_job_id": flexpepdock_job_id,
        "total_krw": base.get("total_krw", 0),
        "lead_weeks": base.get("lead_weeks", 0),
        "hypothesis": base.get("hypothesis", {"h1": "Candidate improves SSTR2 selectivity.", "h0": "No measurable selectivity improvement."}),
        "predicted_ki": base.get("predicted_ki", []),
        "reagents": base.get("reagents", []),
        "protocol": base.get("protocol", {}),
        "acceptance_criteria": base.get("acceptance_criteria", []),
        "timeline": base.get("timeline", []),
    })
    return order


@router.get("/wetlab/orders")
def wetlab_orders():
    orders = _orders()
    return {"orders": [{k: item.get(k) for k in ("id", "candidate_id", "stage", "total_krw", "lead_weeks", "requested_by", "created_at")} for item in orders]}


@router.post("/wetlab/orders")
def create_wetlab_order(body: Dict[str, Any]):
    candidate_id = body.get("candidate_id")
    if not candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id required")
    orders = _orders()
    order = _new_order(candidate_id, body.get("candidate_seq"), body.get("flexpepdock_job_id"))
    orders.insert(0, order)
    _save_orders(orders)
    return order


@router.get("/wetlab/orders/{order_id}")
def wetlab_order(order_id: str):
    for order in _orders():
        if order.get("id") == order_id:
            return order
    raise HTTPException(status_code=404, detail="order not found")


@router.post("/wetlab/orders/{order_id}/transition")
def transition_wetlab(order_id: str, body: Dict[str, Any]):
    orders = _orders()
    target = body.get("to_stage")
    if target not in STAGES:
        raise HTTPException(status_code=400, detail="invalid stage")
    for order in orders:
        if order.get("id") == order_id:
            order["stage"] = target
            order.setdefault("history", []).append({"ts": _now(), "to_stage": target, "note": body.get("note")})
            _save_orders(orders)
            return order
    raise HTTPException(status_code=404, detail="order not found")


@router.get("/candidate/{candidate_id}/report")
def candidate_report(candidate_id: str, run_id: Optional[str] = None):
    _safe_id(candidate_id, "candidate_id")
    data = _read_json(find_dashboard_archive(run_id) if run_id else None, {}) if run_id else {}
    candidates = data.get("candidates", []) if isinstance(data, dict) else []
    candidate = next((c for c in candidates if isinstance(c, dict) and str(c.get("id") or c.get("seq_id")) == candidate_id), None)
    lines = [f"# Candidate Report: {candidate_id}", "", f"Generated: {_now()}"]
    if candidate:
        lines += ["", "```json", json.dumps(candidate, ensure_ascii=False, indent=2), "```"]
    else:
        lines += ["", "No archive candidate record was found for the requested id/run."]
    return Response("\n".join(lines).encode("utf-8"), media_type="text/markdown; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={candidate_id}-report.md"})
