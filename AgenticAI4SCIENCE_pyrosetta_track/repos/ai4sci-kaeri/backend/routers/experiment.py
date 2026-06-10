"""Experiment control endpoints (start/stop/status/config)."""
from __future__ import annotations

from typing import Optional

import json
import logging
import os
import signal
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.state import (
    REPO_ROOT,
    DEFAULT_EXPERIMENT_CONFIG,
    experiment_lock,
)
import backend.state as state

logger = logging.getLogger(__name__)
router = APIRouter()

# Max runtime in seconds (env-configurable, default 1 hour)
EXPERIMENT_MAX_RUNTIME = int(os.environ.get("EXPERIMENT_MAX_RUNTIME", "3600"))


def _auto_archive(run_id: str) -> Optional[str]:
    """Auto-archive completed experiment: copy dashboard.json to archives/{run_id}_dashboard.json."""
    try:
        import json
        import shutil
        status_file = state.STATUS_FILE if hasattr(state, 'STATUS_FILE') else state.REPO_ROOT / "runs" / "pyrosetta_flow" / "sst14_agentic_mutdock" / "dashboard.json"
        archive_dir = state.ARCHIVE_DIR if hasattr(state, 'ARCHIVE_DIR') else state.REPO_ROOT / "runs" / "pyrosetta_flow" / "archives"
        archive_dir.mkdir(parents=True, exist_ok=True)

        if not status_file.exists():
            return None

        dashboard = json.loads(status_file.read_text(encoding="utf-8"))
        # run_id 설정
        dashboard["run_id"] = run_id
        dashboard["archived_at"] = datetime.now(timezone.utc).isoformat()

        dest = archive_dir / f"{run_id}_dashboard.json"
        dest.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False), encoding="utf-8")

        # 실험 로그에 기록
        exp_log = state.REPO_ROOT / "runs" / "pyrosetta_flow" / "experiment_log.jsonl" if hasattr(state, 'REPO_ROOT') else Path("runs/pyrosetta_flow/experiment_log.jsonl")
        with open(exp_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "run_id": run_id,
                "archived_at": dashboard["archived_at"],
                "candidates": len(dashboard.get("candidates", [])),
                "iterations": dashboard.get("iteration", 0),
                "best_candidate": dashboard.get("best_candidate"),
                "completed": dashboard.get("completed", False),
            }) + "\n")

        logger.info("Auto-archived experiment %s → %s", run_id, dest)
        return str(dest)
    except Exception:
        logger.exception("Auto-archive failed for %s", run_id)
        return None


def _close_log_file() -> None:
    """subprocess 로그 파일 핸들을 닫는다 (있을 경우에만)."""
    lf = getattr(state, "_experiment_log_file", None)
    if lf is not None:
        try:
            lf.close()
        except OSError:
            pass
        state._experiment_log_file = None


def _write_initializing_status(run_id: str, total_iterations: int) -> None:
    """실험 시작 직후 FE가 즉시 읽을 수 있는 최소 status 파일을 기록한다."""
    payload = {
        "run_id": run_id,
        "phase": "initializing",
        "iteration": 0,
        "total_iterations": int(total_iterations),
        "completed": False,
        "connected": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "candidates": [],
        "agent_states": {},
    }
    # 2026-06-09 D2/F04: 원자적 기록(temp+rename under flock) — torn-write 방지
    state.atomic_write_json(state.STATUS_FILE, payload)


def _reap_if_dead() -> None:
    """Clean up state if the experiment process has exited (zombie prevention).
    Auto-archives the run if completed."""
    if state.experiment_proc is not None and state.experiment_proc.poll() is not None:
        # 프로세스 종료됨 — 자동 아카이빙
        if state.experiment_run_id:
            _auto_archive(state.experiment_run_id)
        _close_log_file()
        state.experiment_proc = None


def _watchdog(pid: int, run_id: str, timeout: int) -> None:
    """Background thread that kills the experiment if it exceeds *timeout* seconds."""
    try:
        with experiment_lock:
            proc = state.experiment_proc
        if proc is None:
            return
        try:
            proc.wait(timeout=timeout)
            # 정상 종료 — 자동 아카이빙
            _auto_archive(run_id)
        except subprocess.TimeoutExpired:
            logger.warning(
                "Experiment %s (pid %d) exceeded max runtime %ds — terminating",
                run_id, pid, timeout,
            )
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                proc.wait(timeout=10)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            with experiment_lock:
                if state.experiment_proc is proc:
                    _close_log_file()
                    state.experiment_proc = None
                    state.experiment_run_id = None
    except Exception:
        logger.exception("Watchdog error for experiment %s", run_id)


def _resolve_bio_tools_python() -> str:
    from pathlib import Path
    for base in [
        Path.home() / "miniforge3",
        Path.home() / "miniconda3",
        Path.home() / "anaconda3",
    ]:
        p = base / "envs" / "bio-tools" / "bin" / "python"
        if p.exists():
            return str(p)
    return sys.executable


@router.get("/experiment/config")
def get_config():
    return dict(DEFAULT_EXPERIMENT_CONFIG)


@router.get("/experiment/models")
def list_models():
    """사용 가능한 LLM 모델 목록. 우선 vLLM(OpenAI 호환, port 8000) 조회,
    실패 시 ollama 폴백. 2026-06-09: 본 시스템은 vLLM Qwen3-32B 를 GPU 서빙한다."""
    # 1) vLLM (provider=vllm in pipeline_config.yaml)
    try:
        vllm_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8000")
        req = urllib.request.Request(f"{vllm_url.rstrip('/')}/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
            if models:
                return {"models": models, "provider": "vllm"}
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        pass
    # 2) ollama 폴백
    try:
        ollama_host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
        if "://" not in ollama_host:
            ollama_host = f"http://{ollama_host}"
        req = urllib.request.Request(f"{ollama_host.rstrip('/')}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            return {"models": models, "provider": "ollama"}
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return {"models": ["qwen3-32b"], "error": "vLLM/Ollama not reachable, showing default"}


@router.get("/experiment/status")
def get_status():
    with experiment_lock:
        _reap_if_dead()
        if state.experiment_proc is None:
            return {"running": False, "run_id": state.experiment_run_id}
        return {
            "running": True,
            "run_id": state.experiment_run_id,
            "pid": state.experiment_proc.pid,
        }


@router.post("/experiment/run")
def start_experiment(config: Optional[dict] = None):
    config = config or {}
    with experiment_lock:
        # Reap zombie before checking — avoids "already running" false positive
        _reap_if_dead()

        if state.experiment_proc is not None:
            return {"error": "Experiment already running", "run_id": state.experiment_run_id}

        run_id = f"sst14_mutdock_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        state.experiment_run_id = run_id

        # 2026-06-09: SSTR2-SST14 복합체 템플릿 사용 (이전 fold_test1_model_0.pdb 는
        # 무관한 테스트 구조였음). config 로 override 가능.
        template_pdb = config.get("template_pdb") or str(
            REPO_ROOT / "data" / "somatostatin_receptor" / "SSTR2_SST14_complex_boltz_1.pdb"
        )
        python_bin = _resolve_bio_tools_python()

        # 3-way 폴백: 요청값 → runtime_settings → DEFAULT_EXPERIMENT_CONFIG (P09, 2026-05-14)
        max_iterations = (
            config.get("max_iterations")
            or state.runtime_settings.get("max_iterations")
            or DEFAULT_EXPERIMENT_CONFIG["max_iterations"]
        )
        n_candidates = (
            config.get("n_candidates")
            or state.runtime_settings.get("n_candidates")
            or DEFAULT_EXPERIMENT_CONFIG["n_candidates"]
        )
        top_k = (
            config.get("top_k")
            or state.runtime_settings.get("top_k")
            or DEFAULT_EXPERIMENT_CONFIG["top_k"]
        )

        cmd = [
            python_bin,
            str(REPO_ROOT / "scripts" / "run_pyrosetta_flow.py"),
            "--input", template_pdb,
            "--max-iterations", str(max_iterations),
            "--n-candidates", str(n_candidates),
            "--top-k", str(top_k),
            "--llm-model", str(config.get("llm_model") or state.runtime_settings.get("llm_model") or DEFAULT_EXPERIMENT_CONFIG["llm_model"]),
            "--planner-mode", "pyrosetta-only",
        ]

        features = config.get("features", {})
        env = os.environ.copy()
        for feat_key, feat_val in features.items():
            env[f"FEAT_{feat_key.upper()}"] = "1" if feat_val else "0"

        try:
            # stdout/stderr를 파일로 redirect — PIPE 미소비에 의한 64KB 버퍼 hang 방지.
            # DEVNULL 대신 로그 파일을 사용해 subprocess 오류 시 디버그 가능성 확보.
            log_path = state.STATUS_FILE.parent / f"experiment_{run_id}.log"
            log_file = open(log_path, "w", encoding="utf-8")  # noqa: WPS515
            state.experiment_proc = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
                env=env,
            )
            state._experiment_log_file = log_file  # _reap_if_dead에서 닫음
            pid = state.experiment_proc.pid
            _write_initializing_status(run_id, max_iterations)

            # Launch watchdog thread to enforce max runtime
            max_runtime = int(config.get("max_runtime", EXPERIMENT_MAX_RUNTIME))
            threading.Thread(
                target=_watchdog,
                args=(pid, run_id, max_runtime),
                daemon=True,
                name=f"exp-watchdog-{run_id}",
            ).start()

            return {
                "status": "started",
                "run_id": run_id,
                "pid": pid,
                "max_runtime": max_runtime,
            }
        except (OSError, FileNotFoundError) as exc:
            _close_log_file()
            state.experiment_proc = None
            raise HTTPException(status_code=500, detail=f"Failed to start: {exc}")


@router.post("/experiment/stop")
def stop_experiment():
    with experiment_lock:
        _reap_if_dead()
        if state.experiment_proc is None:
            return {"status": "not_running"}
        try:
            os.killpg(os.getpgid(state.experiment_proc.pid), signal.SIGTERM)
            state.experiment_proc.wait(timeout=10)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(os.getpgid(state.experiment_proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        run_id = state.experiment_run_id
        # 중지 시에도 자동 아카이빙
        if run_id:
            _auto_archive(run_id)
        _close_log_file()
        state.experiment_proc = None
        state.experiment_run_id = None
        return {"status": "stopped", "run_id": run_id}


@router.get("/experiment/history")
def experiment_history():
    """실험 이력 조회 — experiment_log.jsonl에서 읽기."""
    import json as _json
    exp_log = REPO_ROOT / "runs" / "pyrosetta_flow" / "experiment_log.jsonl"
    if not exp_log.exists():
        return {"history": []}
    entries = []
    for line in exp_log.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                entries.append(_json.loads(line))
            except _json.JSONDecodeError:
                continue
    # 최신순
    entries.reverse()
    return {"history": entries, "total": len(entries)}
