"""Run launcher and predicted gate pass-rate router."""
from __future__ import annotations

import json
import os
import subprocess
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import yaml
from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..schemas.dashboard import (
    PredictedPassRate,
    PredictedPassRatesResponse,
    RunStartRequest,
    RunStartResponse,
)

router = APIRouter()
KST = timezone(timedelta(hours=9))
ACTIVE_RUN_LOCK = threading.Lock()
RUN_TIMEOUT_SECONDS = 4 * 60 * 60
LOCKFILE_NAME = ".active_run.lock"
DEFAULT_BOLTZ_MARGIN_MIN = 0.0


def _now_kst() -> datetime:
    return datetime.now(KST)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _runs_root() -> Path:
    return _repo_root() / "runs_local"


def _gate_thresholds_path() -> Path:
    return _repo_root() / "pipeline_local" / "config" / "gate_thresholds.yaml"


def _lock_path() -> Path:
    return _runs_root() / LOCKFILE_NAME


def _build_run_id(name: str | None = None) -> str:
    ts = _now_kst().strftime("%Y%m%d_%H%M")
    return name or f"local_{ts}_iter01"


def _validate_run_dir(run_id: str) -> Path:
    runs_root = _runs_root().resolve()
    run_dir = (runs_root / run_id).resolve()
    if run_dir.parent != runs_root:
        raise HTTPException(status_code=422, detail="run_id resolves outside runs_local")
    return run_dir


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _write_active_lock(payload: dict[str, Any]) -> None:
    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_active_lock() -> dict[str, Any] | None:
    path = _lock_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        path.unlink(missing_ok=True)
        return None
    return payload if isinstance(payload, dict) else None


def _pid_is_running(pid: int | None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _active_run_payload() -> dict[str, Any] | None:
    payload = _read_active_lock()
    if payload is None:
        return None
    status = str(payload.get("status", ""))
    pid = payload.get("pid")
    if status == "running" and _pid_is_running(pid):
        return payload
    if status == "launching":
        return payload
    _lock_path().unlink(missing_ok=True)
    return None


def _clear_active_lock(run_id: str, pid: int | None = None) -> None:
    with ACTIVE_RUN_LOCK:
        payload = _read_active_lock()
        if payload is None:
            return
        if payload.get("run_id") != run_id:
            return
        if pid is not None and payload.get("pid") not in (None, pid):
            return
        _lock_path().unlink(missing_ok=True)


def _render_yaml(req: RunStartRequest) -> str:
    payload = {
        "mode": "local",
        "iteration": {
            "n_backbone": req.n_backbone,
            "k_seq_per_backbone": req.k_seq_per_backbone,
            "top_m_rosetta": req.top_m_rosetta,
            "max_iterations": req.iterations,
        },
        "silo": req.silo,
        "llm_model": req.llm_model,
        "seed": req.seed,
        "mutation_strategy": req.mutation_strategy,
        "off_target_receptors": req.off_targets,
        "boltz_cross": {"enabled": req.boltz_cross_enabled},
        "gates": req.gates.model_dump(by_alias=False) if req.gates else None,
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def _estimate_eta(req: RunStartRequest) -> int:
    per_iter = 28 if req.silo == "B" else 32
    cross = 8 if req.boltz_cross_enabled else 0
    return req.iterations * (per_iter + cross)


def _terminate_process(proc: subprocess.Popen[Any]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=15)
        return
    except subprocess.TimeoutExpired:
        pass
    proc.kill()
    proc.wait(timeout=15)


def _monitor_subprocess(proc: subprocess.Popen[Any], run_id: str) -> None:
    try:
        try:
            proc.wait(timeout=RUN_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            _terminate_process(proc)
            timeout_path = _validate_run_dir(run_id) / "timeout.json"
            timeout_path.write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "timeout_seconds": RUN_TIMEOUT_SECONDS,
                        "terminated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
    finally:
        _clear_active_lock(run_id, proc.pid)


def _run_pipeline_subprocess(run_id: str, req: RunStartRequest) -> None:
    run_dir = _validate_run_dir(run_id)
    log_path = run_dir / "stdout.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "conda",
        "run",
        "-n",
        "bio-tools",
        "python",
        "-m",
        "pipeline_local.run_pipeline_local",
        "--run-id",
        run_id,
        "--iterations",
        str(req.iterations),
        "--silo",
        req.silo,
        "--llm-model",
        req.llm_model,
    ]

    try:
        with log_path.open("a", encoding="utf-8") as logf:
            proc = subprocess.Popen(
                cmd,
                cwd=str(_repo_root()),
                stdout=logf,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except Exception:
        _clear_active_lock(run_id)
        raise

    with ACTIVE_RUN_LOCK:
        _write_active_lock(
            {
                "run_id": run_id,
                "pid": proc.pid,
                "status": "running",
                "started_at": _now_kst().isoformat(),
                "timeout_seconds": RUN_TIMEOUT_SECONDS,
            }
        )

    threading.Thread(target=_monitor_subprocess, args=(proc, run_id), daemon=True).start()


def _coerce_rate(passed: int, total: int) -> float:
    if total <= 0:
        return 0.5
    return max(0.0, min(1.0, passed / total))


def _collect_metric_values(pattern: str, extractor: Callable[[dict[str, Any]], list[float]], run_id: str) -> tuple[list[float], int]:
    values: list[float] = []
    sample_files = 0
    for path in sorted(_runs_root().glob(pattern)):
        current_run_id = path.parents[1].name
        if current_run_id == run_id:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        extracted = extractor(payload)
        if not extracted:
            continue
        values.extend(extracted)
        sample_files += 1
    return values, sample_files


def _extract_rosetta_ddg(payload: dict[str, Any]) -> list[float]:
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    values: list[float] = []
    for item in results:
        if isinstance(item, dict) and isinstance(item.get("ddg"), (int, float)):
            values.append(float(item["ddg"]))
    return values


def _extract_boltz_margin(payload: dict[str, Any]) -> list[float]:
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    values: list[float] = []
    for item in results:
        if isinstance(item, dict) and isinstance(item.get("selectivity_margin"), (int, float)):
            values.append(float(item["selectivity_margin"]))
    return values


@router.post("/start", response_model=RunStartResponse)
async def start_run(req: RunStartRequest, bg: BackgroundTasks) -> RunStartResponse:
    run_id = _build_run_id(req.name)
    started = _now_kst()

    with ACTIVE_RUN_LOCK:
        active_run = _active_run_payload()
        if active_run is not None:
            raise HTTPException(
                status_code=409,
                detail=f"run already active: {active_run.get('run_id', 'unknown')}",
            )

        run_dir = _validate_run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        config_path = run_dir / "00_config" / "pipeline_config_local.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(_render_yaml(req), encoding="utf-8")

        _write_active_lock(
            {
                "run_id": run_id,
                "pid": None,
                "status": "launching",
                "started_at": started.isoformat(),
                "request_id": uuid.uuid4().hex,
                "timeout_seconds": RUN_TIMEOUT_SECONDS,
            }
        )

    bg.add_task(_run_pipeline_subprocess, run_id, req)

    return RunStartResponse(
        run_id=run_id,
        started_at=started,
        estimated_eta_minutes=_estimate_eta(req),
        monitor_url=f"/runs/{run_id}",
    )


@router.get("/{run_id}/predicted_pass_rates", response_model=PredictedPassRatesResponse)
def predicted_pass_rates(run_id: str) -> PredictedPassRatesResponse:
    gate_cfg = _load_yaml(_gate_thresholds_path())
    enabled = gate_cfg.get("gates_enabled", {}) if isinstance(gate_cfg.get("gates_enabled"), dict) else {}

    rosetta_values, rosetta_files = _collect_metric_values(
        "silo_b_*/local_*_iter*/06_rosetta/energy_table.json",
        _extract_rosetta_ddg,
        run_id,
    )
    boltz_values, boltz_files = _collect_metric_values(
        "silo_b_*/local_*_iter*/05c_boltz_cross/boltz_cross_validation.json",
        _extract_boltz_margin,
        run_id,
    )

    predicted: list[PredictedPassRate] = []
    sample_refs: list[str] = []

    if enabled.get("plddt", True):
        predicted.append(PredictedPassRate(gate_id="plddt", name="pLDDT", rate=0.5, warn=True))
    if enabled.get("docking", True):
        predicted.append(PredictedPassRate(gate_id="docking", name="Docking", rate=0.5, warn=True))
    if enabled.get("selectivity", True):
        if boltz_values:
            threshold = float(gate_cfg.get("boltz_iptm_margin_min", DEFAULT_BOLTZ_MARGIN_MIN))
            rate = _coerce_rate(sum(1 for value in boltz_values if value >= threshold), len(boltz_values))
            predicted.append(PredictedPassRate(gate_id="selectivity", name="Boltz iPTM margin", rate=rate))
            sample_refs.append(f"{boltz_files} boltz_cross files")
        else:
            predicted.append(PredictedPassRate(gate_id="selectivity", name="Boltz iPTM margin", rate=0.5, warn=True))
    if enabled.get("rosetta", True):
        if rosetta_values:
            threshold = float(gate_cfg.get("rosetta_ddg_max", -1.0))
            rate = _coerce_rate(sum(1 for value in rosetta_values if value <= threshold), len(rosetta_values))
            predicted.append(PredictedPassRate(gate_id="rosetta", name="Rosetta ddG", rate=rate))
            sample_refs.append(f"{rosetta_files} rosetta files")
        else:
            predicted.append(PredictedPassRate(gate_id="rosetta", name="Rosetta ddG", rate=0.5, warn=True))
    if enabled.get("stability_prescreen", True):
        predicted.append(PredictedPassRate(gate_id="stability_prescreen", name="Stability prescreen", rate=0.5, warn=True))

    based_on = "gate_thresholds.yaml"
    if sample_refs:
        based_on = f"{based_on} + {', '.join(sample_refs)}"
    else:
        based_on = f"{based_on} + fallback defaults"

    return PredictedPassRatesResponse(based_on=based_on, predicted=predicted)
