"""
Shared application state
=========================
Holds mutable singletons (cache, locks, process handles) shared across routers.
Avoids global state scattered in handler classes.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

# 옵션 B (2026-05-20): 외부 env 기반 경로 — 미설정 시 기존 경로와 동일.
# SST_OUTER_REPO_ROOT : 레포 외부에서 실행할 때 최상위 루트를 명시.
# SST_DATA_DIR        : receptor CIF 파일 디렉토리를 심링크 없이 직접 지정.
# 2026-06-09 fix: ai4sci-kaeri 에서 최상위 SST14-M_scr 까지는 parent ×3
# (repos→AgenticAI4SCIENCE_pyrosetta_track→SST14-M_scr). 이전 ×4 는 /tmp 를 가리켜
# pipeline_local(컴퓨트 레이어)을 못 찾아 flexpepdock/binding_pocket/stability
# 엔드포인트가 ModuleNotFoundError 로 깨졌다.
OUTER_REPO_ROOT = Path(os.environ.get(
    "SST_OUTER_REPO_ROOT",
    str(REPO_ROOT.parent.parent.parent),
)).resolve()
SST_DATA_DIR = Path(os.environ.get(
    "SST_DATA_DIR",
    str(REPO_ROOT / "data" / "somatostatin_receptor"),
)).resolve()

STATUS_FILE = Path(os.environ.get(
    "PIPELINE_STATUS_FILE",
    # pipeline_local 정식 경로로 통일 (P1-2, 2026-05-13)
    # 레거시: /tmp/ag_pipeline_status.json → /tmp/pipeline_local_status.json
    "/tmp/pipeline_local_status.json",
))
ARCHIVE_DIR = Path(os.environ.get(
    "PIPELINE_ARCHIVE_DIR",
    str(REPO_ROOT / "runs" / "pyrosetta_flow" / "archives"),
))
VALIDATION_DIR = Path(os.environ.get(
    "PIPELINE_VALIDATION_DIR",
    str(REPO_ROOT / "runs" / "pyrosetta_flow" / "09_validation"),
))
EXP_LOG = REPO_ROOT / "runs" / "pyrosetta_flow" / "experiment_log.jsonl"

PORT = int(os.environ.get("API_PORT", "8787"))

# Ensure project root is importable
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
# 2026-06-09 fix: 최상위 루트를 path **끝에 append** — backend 가 pipeline_local.scripts.*
# (컴퓨트 레이어 워커)를 import 할 수 있도록. **insert(0) 금지**: 최상위에도 동명 패키지
# (pyrosetta_flow, scripts)가 있어 0번에 넣으면 중첩 ai4sci-kaeri 모듈을 shadow 해
# runner import 가 깨진다. append 로 중첩 우선 + pipeline_local(최상위 전용) 해결.
if str(OUTER_REPO_ROOT) not in sys.path:
    sys.path.append(str(OUTER_REPO_ROOT))

# ---------------------------------------------------------------------------
# Atomic JSON write (D2/F04, 2026-06-09)
# ---------------------------------------------------------------------------
def atomic_write_json(path: "Path", data: dict, *, indent: int = 2) -> None:
    """JSON 을 원자적으로 기록한다 (temp write + os.replace, flock 직렬화).

    상태 파일(STATUS_FILE)을 쓰는 모든 경로가 이 함수를 경유해야 한다.
    in-place write_text 는 torn-write 를 일으켜 동시 읽는 백엔드가 부분 JSON 을 보게 된다.
    StatusEmitter.flush 와 동일 정책(temp+rename under flock)으로 일관화.
    """
    import fcntl
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=indent)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    lock_path = path.with_suffix(path.suffix + ".lock")
    with open(lock_path, "w") as lock_fd:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        try:
            tmp_path.write_text(content, encoding="utf-8")
            os.replace(tmp_path, path)  # atomic on POSIX
        finally:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# Status file cache
# ---------------------------------------------------------------------------
_cache_lock = Lock()
_cache: dict = {}
_cache_mtime: float = 0.0


def _with_runtime_fields(data: dict) -> dict:
    """보조 상태 필드(is_active_run/server_time)를 주입한다.

    P03 규칙:
    - is_active_run: error/disconnected 케이스 → False,
                     그 외 → (not completed) AND (steps 또는 candidates 존재)
    - server_time: 캐시 hit 여부와 무관하게 항상 현재 시각으로 갱신
    """
    enriched = copy.deepcopy(data)
    if enriched.get("error") or enriched.get("connected") is False:
        enriched["is_active_run"] = False
    else:
        completed = bool(enriched.get("completed", False))
        # 2026-06-09 (P5 smoke 발견): candidates/steps 가 null 일 수 있다 (POST /status 가
        # exclude_none=False 로 None 필드를 기록하면 JSON 에 null 로 남음) → len(None) TypeError.
        # `or []` 로 null·결측 모두 빈 리스트로 정규화.
        has_steps = (
            len(enriched.get("steps") or []) > 0
            or len(enriched.get("candidates") or []) > 0
        )
        enriched["is_active_run"] = (not completed) and has_steps
    # server_time은 캐시 hit 후에도 항상 현재 시각으로 갱신 (stale 방지)
    enriched["server_time"] = datetime.now(timezone.utc).isoformat()
    return enriched


def read_status() -> dict:
    """Read status JSON with file-level caching.

    캐시 메커니즘:
    - STATUS_FILE mtime이 변하지 않으면 파싱 스킵 (I/O 절약)
    - 단, server_time은 캐시 hit 후에도 후처리로 매번 갱신
    """
    global _cache, _cache_mtime

    if not STATUS_FILE.exists():
        return _with_runtime_fields({"error": "no_status_file", "connected": False})

    mtime = STATUS_FILE.stat().st_mtime
    with _cache_lock:
        if mtime == _cache_mtime and _cache:
            # P03: 캐시 hit이어도 server_time 갱신을 위해 _with_runtime_fields 경유
            return _with_runtime_fields(_cache)

    try:
        raw = STATUS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        with _cache_lock:
            _cache = data
            _cache_mtime = mtime
        return _with_runtime_fields(data)
    except (json.JSONDecodeError, OSError) as exc:
        return _with_runtime_fields({"error": str(exc), "connected": False})


# ---------------------------------------------------------------------------
# Constants / limits
# ---------------------------------------------------------------------------
MAX_VALIDATION_BATCH = 50
VALIDATION_TIMEOUT_SEC = 30

validation_executor = ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="validation",
)

# ---------------------------------------------------------------------------
# Experiment process state
# ---------------------------------------------------------------------------
experiment_lock = Lock()
experiment_proc: subprocess.Popen | None = None
experiment_run_id: str | None = None

DEFAULT_EXPERIMENT_CONFIG = {
    "max_iterations": 5,
    "n_candidates": 8,
    "top_k": 5,
    "llm_model": "qwen3-32b",  # 2026-06-09: vLLM(port 8000) served model (provider=vllm in pipeline_config.yaml)
    "objective_mode": "auto",
}

# ---------------------------------------------------------------------------
# Runtime settings (mutable, updated via /api/settings)
# ---------------------------------------------------------------------------
runtime_settings: dict = {
    "execution_strategy": "sequential",
    "max_iterations": 5,
    "n_candidates": 8,
    "top_k": 5,
    "llm_model": "qwen3:8b",
    "nim_api_key": os.environ.get("NVIDIA_NIM_API_KEY", ""),
    "nim_endpoint_mode": "cloud",
    "validation_n_trials": 10,
}
