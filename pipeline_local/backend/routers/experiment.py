"""
Experiment control endpoints — LOCAL MODE
==========================================
pipeline_local.run_pipeline_local 을 서브프로세스로 실행하고
pipeline_status.json 을 통해 상태를 스트리밍한다.

NIM API 키 확인 및 scripts/run_pyrosetta_flow.py 호출을 완전히 제거.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from pipeline_local.backend.state import (
    REPO_ROOT,
    RECEPTOR_PDB,
    OLLAMA_HOST,
    DEFAULT_EXPERIMENT_CONFIG,
    experiment_lock,
)
import pipeline_local.backend.state as state

logger = logging.getLogger(__name__)
router = APIRouter()

# 실험 최대 실행 시간 (초) — 환경 변수로 조정 가능
EXPERIMENT_MAX_RUNTIME = int(os.environ.get("EXPERIMENT_MAX_RUNTIME", "3600"))


def _read_pipeline_llm_config() -> Dict[str, Any]:
    """``pipeline_local/config/pipeline_config_local.yaml`` 의 ``llm`` 섹션."""
    p = REPO_ROOT / "pipeline_local" / "config" / "pipeline_config_local.yaml"
    if not p.is_file():
        return {}
    try:
        with p.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return dict(data.get("llm") or {})
    except Exception:
        logger.debug("pipeline LLM 설정 로드 실패", exc_info=True)
        return {}


def _reap_if_dead() -> None:
    """종료된 프로세스의 zombie 상태를 정리한다."""
    if state.experiment_proc is not None and state.experiment_proc.poll() is not None:
        state.experiment_proc = None


def _watchdog(pid: int, run_id: str, timeout: int) -> None:
    """지정된 timeout 초가 지나면 실험 프로세스를 강제 종료하는 백그라운드 스레드."""
    try:
        with experiment_lock:
            proc = state.experiment_proc
        if proc is None:
            return
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning(
                "실험 %s (pid %d) 최대 실행 시간 %d초 초과 — 강제 종료",
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
                    state.experiment_proc = None
                    state.experiment_run_id = None
    except Exception:
        logger.exception("watchdog 오류 (실험 %s)", run_id)


def _resolve_python() -> str:
    """bio-tools conda 환경의 Python 경로를 우선 탐색하고, 없으면 현재 인터프리터 반환."""
    from pathlib import Path
    for base in [
        Path.home() / "miniforge3",
        Path.home() / "miniconda3",
        Path.home() / "anaconda3",
    ]:
        candidate = base / "envs" / "bio-tools" / "bin" / "python"
        if candidate.exists():
            return str(candidate)
    return sys.executable


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class ExperimentRunRequest(BaseModel):
    """POST /api/experiment/run 요청 바디.

    approach: "a" (RFdiffusion + ProteinMPNN + ESMFold + DiffDock) 또는
              "b" (BLOSUM62 텍스트 수준 돌연변이). 기본값은 "b".
    approach_b: bool — 레거시 호환을 위해 유지. approach 필드가 우선.
    """
    max_iterations:  Optional[int]   = Field(None, ge=1, le=999)
    n_candidates:    Optional[int]   = Field(None, ge=1, le=200)
    top_k:           Optional[int]   = Field(None, ge=1, le=50)
    llm_model:       Optional[str]   = Field(None, max_length=100)
    ollama_host:     Optional[str]   = Field(None, max_length=100)
    approach:        Optional[str]   = Field(None, pattern=r"^[abAB]$",
                                             description="'a' = 3-ARM local, 'b' = BLOSUM mutation")
    approach_b:      Optional[bool]  = Field(None, description="레거시. approach 필드가 우선")
    max_runtime:     Optional[int]   = Field(None, ge=60, le=86400)


# ---------------------------------------------------------------------------
# GET /api/experiment/config
# ---------------------------------------------------------------------------

@router.get("/experiment/config")
def get_config():
    """현재 기본 실험 설정을 반환한다 (YAML ``llm`` 과 병합)."""
    base = dict(DEFAULT_EXPERIMENT_CONFIG)
    llm = _read_pipeline_llm_config()
    if llm:
        base["llm_provider"] = str(llm.get("provider", "ollama")).lower()
        if llm.get("base_url"):
            base["llm_base_url"] = llm["base_url"]
        if llm.get("model"):
            base["llm_model"] = llm["model"]
    rs = getattr(state, "runtime_settings", {})
    for k in ("llm_provider", "llm_base_url", "llm_model", "ollama_host"):
        if rs.get(k) is not None and rs.get(k) != "":
            base[k] = rs[k]
    return base


# ---------------------------------------------------------------------------
# GET /api/experiment/models
# ---------------------------------------------------------------------------

@router.get("/experiment/models")
def list_models():
    """LLM 설정(provider)에 따라 Ollama ``/api/tags`` 또는 vLLM ``/v1/models`` 를 조회한다."""
    import urllib.error
    import urllib.request

    llm = _read_pipeline_llm_config()
    rs = getattr(state, "runtime_settings", {})
    provider = str(
        rs.get("llm_provider") or llm.get("provider") or "ollama",
    ).lower()

    if provider == "vllm":
        base = str(
            rs.get("llm_base_url") or llm.get("base_url") or "http://localhost:8000",
        ).rstrip("/")
        url = f"{base}/v1/models"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [
                    item.get("id", "")
                    for item in (data.get("data") or [])
                    if item.get("id")
                ]
                return {"models": models, "provider": "vllm", "base_url": base}
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            return {
                "models": [],
                "provider": "vllm",
                "base_url": base,
                "error": f"vLLM 미응답 ({base}): {e}",
            }

    if provider == "none":
        return {
            "models": [],
            "provider": "none",
            "hint": "LLM 비활성 — 규칙 기반 모드",
        }

    host = str(rs.get("ollama_host") or state.OLLAMA_HOST)
    url = f"http://{host}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            return {"models": models, "provider": "ollama", "ollama_host": host}
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return {
            "models": ["qwen3:8b"],
            "provider": "ollama",
            "error": f"Ollama 미응답 ({host}), 기본값 반환",
            "ollama_host": host,
        }


# ---------------------------------------------------------------------------
# GET /api/experiment/status
# ---------------------------------------------------------------------------

@router.get("/experiment/status")
def get_status():
    """현재 실행 중인 실험의 상태를 반환한다."""
    with experiment_lock:
        _reap_if_dead()
        if state.experiment_proc is None:
            return {"running": False, "run_id": state.experiment_run_id}
        return {
            "running": True,
            "run_id": state.experiment_run_id,
            "pid": state.experiment_proc.pid,
        }


# ---------------------------------------------------------------------------
# POST /api/experiment/run
# ---------------------------------------------------------------------------

@router.post("/experiment/run")
def start_experiment(body: Optional[ExperimentRunRequest] = None):
    """pipeline_local.run_pipeline_local 을 서브프로세스로 실행한다.

    요청 필드:
        max_iterations: int   (기본 5)
        n_candidates:   int   (기본 8, 현재 미사용 — 향후 확장용)
        top_k:          int   (기본 5, 현재 미사용 — 향후 확장용)
        llm_model:      str   (기본 "qwen3:8b")
        ollama_host:    str   (기본 OLLAMA_HOST)
        approach:       "a"|"b"  (기본 "b". "a" = 3-ARM local, "b" = BLOSUM)
        approach_b:     bool  (레거시. approach 필드가 우선)
        max_runtime:    int   (초 단위, 기본 3600)
    """
    req = body or ExperimentRunRequest()

    with experiment_lock:
        # 좀비 프로세스 정리 후 이중 실행 방지
        _reap_if_dead()
        if state.experiment_proc is not None:
            return {"error": "실험이 이미 실행 중입니다.", "run_id": state.experiment_run_id}

        run_id = f"local_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        state.experiment_run_id = run_id

        python_bin = _resolve_python()

        llm_yaml = _read_pipeline_llm_config()
        prov = str(
            state.runtime_settings.get("llm_provider")
            or llm_yaml.get("provider")
            or "ollama",
        ).lower()
        default_model = str(
            req.llm_model
            or state.runtime_settings.get("llm_model")
            or llm_yaml.get("model")
            or "qwen3:8b",
        )

        cmd = [
            python_bin,
            "-m", "pipeline_local.run_pipeline_local",
            "--iterations", str(req.max_iterations or 5),
            "--llm-model", default_model,
        ]
        if prov == "vllm":
            bu = (
                state.runtime_settings.get("llm_base_url")
                or llm_yaml.get("base_url")
                or "http://localhost:8000"
            )
            cmd.extend(["--llm-base-url", str(bu).rstrip("/")])
        else:
            cmd.extend([
                "--ollama-host",
                str(req.ollama_host or state.OLLAMA_HOST),
            ])

        # Approach 분기 처리
        # approach 필드가 명시된 경우 우선 적용; 없으면 레거시 approach_b bool 참조
        approach_str = (req.approach or "").lower()
        if approach_str == "a":
            # Approach A: RFdiffusion + ProteinMPNN + ESMFold + DiffDock (local)
            cmd.append("--no-approach-b")
        elif approach_str == "b":
            # Approach B: BLOSUM62 텍스트 수준 돌연변이
            cmd.append("--approach-b")
        elif req.approach_b is True:
            # 레거시 호환
            cmd.append("--approach-b")
        elif req.approach_b is False:
            cmd.append("--no-approach-b")

        # 환경 변수: 기존 환경 복사 + OLLAMA_HOST 고정
        env = os.environ.copy()
        env["OLLAMA_HOST"] = str(req.ollama_host or state.OLLAMA_HOST)
        env["PIPELINE_LOCAL_RUN_ID"] = run_id  # 상태 파일 식별용

        try:
            state.experiment_proc = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),      # SST14-M_scr/ 에서 실행
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,    # 프로세스 그룹 분리 (SIGTERM 전파용)
                env=env,
            )
            pid = state.experiment_proc.pid

            # 최대 실행 시간 감시 스레드 시작
            max_runtime = int(req.max_runtime or EXPERIMENT_MAX_RUNTIME)
            threading.Thread(
                target=_watchdog,
                args=(pid, run_id, max_runtime),
                daemon=True,
                name=f"exp-watchdog-{run_id}",
            ).start()

            effective_approach = approach_str if approach_str in ("a", "b") else (
                "b" if req.approach_b is True else ("a" if req.approach_b is False else "b")
            )
            logger.info(
                "실험 시작: run_id=%s, pid=%d, approach=%s, cmd=%s",
                run_id, pid, effective_approach, cmd,
            )
            return {
                "status": "started",
                "run_id": run_id,
                "pid": pid,
                "approach": effective_approach,
                "max_runtime": max_runtime,
            }

        except (OSError, FileNotFoundError) as exc:
            state.experiment_proc = None
            raise HTTPException(status_code=500, detail=f"프로세스 실행 실패: {exc}")


# ---------------------------------------------------------------------------
# POST /api/experiment/stop
# ---------------------------------------------------------------------------

@router.post("/experiment/stop")
def stop_experiment():
    """실행 중인 실험을 SIGTERM → SIGKILL 순으로 종료한다."""
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
        state.experiment_proc = None
        state.experiment_run_id = None

        logger.info("실험 중지: run_id=%s", run_id)
        return {"status": "stopped", "run_id": run_id}
