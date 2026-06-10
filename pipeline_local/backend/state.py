"""
Shared application state — LOCAL MODE
=======================================
로컬 모드 백엔드용 싱글톤 상태 모듈.
NIM API 관련 항목을 모두 제거하고 pipeline_local 전용 경로/설정으로 교체.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------------------------
# 경로 상수
# ---------------------------------------------------------------------------

# pipeline_local/backend/state.py 기준으로 두 단계 올라가면 SST14-M_scr 루트
_THIS_FILE  = Path(__file__).resolve()
_BACKEND_DIR = _THIS_FILE.parent                          # pipeline_local/backend/
_PIPELINE_LOCAL_DIR = _BACKEND_DIR.parent                 # pipeline_local/
REPO_ROOT   = _PIPELINE_LOCAL_DIR.parent                  # SST14-M_scr/

# 원본 AG_src 저장소 (에이전트, LLM 등 공유 모듈용)
AG_SRC_REPO = Path(os.environ.get(
    "AG_SRC_REPO",
    str(REPO_ROOT / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri")
))

# sys.path에 두 경로 모두 추가 (중복 방지)
for _p in (REPO_ROOT, AG_SRC_REPO):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# 로컬 파이프라인 상태 파일 (pipeline_local 전용 경로)
STATUS_FILE = Path(os.environ.get(
    "PIPELINE_STATUS_FILE",
    "/tmp/pipeline_local_status.json",
))

# 결과 아카이브 디렉토리
# PIPELINE_ARCHIVE_DIR 가 설정되면 해당 경로만 사용.
# 미설정 시 PyRosetta 플로(status_emitter)와 pipeline_local 양쪽 기본 위치를 모두 탐색.
def _default_archive_dirs() -> list[Path]:
    # P1-2 (2026-05-13): ad-hoc 실행 결과 노출을 위해 runs_local 하위 경로 확장
    return [
        REPO_ROOT / "runs" / "pyrosetta_flow" / "archives",
        REPO_ROOT / "runs_local" / "archives",
        AG_SRC_REPO / "runs" / "pyrosetta_flow" / "archives",
        REPO_ROOT / "runs_local",                                              # ad-hoc 결과 일괄 노출
        REPO_ROOT / "runs_local" / "archives_boltz_eval",                     # Boltz eval 결과
        REPO_ROOT / "runs_local" / "cand03_variants" / "boltz_dock",          # cand03 변이 도킹
        REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "boltz_batch",  # 선택성 데모
        REPO_ROOT / "runs_local" / "stability",                               # 안정성 실험
    ]


_env_archive = os.environ.get("PIPELINE_ARCHIVE_DIR", "").strip()
if _env_archive:
    ARCHIVE_DIRS: list[Path] = [Path(_env_archive).resolve()]
else:
    ARCHIVE_DIRS = [p.resolve() for p in _default_archive_dirs()]

# 레거시: 첫 번째 디렉터리 (신규 코드는 find_dashboard_archive / list_archive_dashboard_files 사용)
ARCHIVE_DIR = ARCHIVE_DIRS[0]


def list_archive_dashboard_files() -> list[Path]:
    """모든 ARCHIVE_DIRS 에서 *_dashboard.json 을 수집해 수정 시각 내림차순 정렬."""
    files: list[Path] = []
    for d in ARCHIVE_DIRS:
        if not d.is_dir():
            continue
        files.extend(d.glob("*_dashboard.json"))
    try:
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return sorted(files, reverse=True)


def find_dashboard_archive(run_id: str) -> Path | None:
    """run_id 에 해당하는 대시보드 JSON 경로를 아카이브 디렉터리들 중에서 찾는다."""
    if not run_id or any(c in run_id for c in ("/", "\\", "..")):
        return None
    name = f"{run_id}_dashboard.json"
    for base in ARCHIVE_DIRS:
        try:
            candidate = (base / name).resolve()
            candidate.relative_to(base.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None

# 검증 결과 저장 디렉토리
VALIDATION_DIR = Path(os.environ.get(
    "PIPELINE_VALIDATION_DIR",
    str(REPO_ROOT / "runs_local" / "validation"),
))

# 실험 로그 (JSONL)
EXP_LOG = REPO_ROOT / "runs_local" / "experiment_log.jsonl"

# 수신 포트 — Vite 프록시가 8787을 가리킴
PORT = int(os.environ.get("API_PORT", "8787"))

# Ollama 호스트 (로컬 모드 전용 포트)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11435")

# 수신기 PDB 경로 (FlexPepDock 입력)
RECEPTOR_PDB = Path(os.environ.get(
    "RECEPTOR_PDB",
    str(AG_SRC_REPO / "data" / "fold_test1_model_0.pdb"),
))

# ---------------------------------------------------------------------------
# Status 파일 캐시 (mtime 기반 LRU-like)
# ---------------------------------------------------------------------------
_cache_lock = Lock()
_cache: dict = {}
_cache_mtime: float = 0.0


def read_status() -> dict:
    """상태 JSON을 파일 수정 시각 기반으로 캐싱하여 반환한다."""
    global _cache, _cache_mtime

    if not STATUS_FILE.exists():
        return {"error": "no_status_file", "connected": False}

    mtime = STATUS_FILE.stat().st_mtime
    with _cache_lock:
        if mtime == _cache_mtime and _cache:
            return copy.deepcopy(_cache)

    try:
        raw = STATUS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        with _cache_lock:
            _cache = data
            _cache_mtime = mtime
        return copy.deepcopy(data)
    except (json.JSONDecodeError, OSError) as exc:
        return {"error": str(exc), "connected": False}


# ---------------------------------------------------------------------------
# 검증 배치 제한
# ---------------------------------------------------------------------------
MAX_VALIDATION_BATCH   = 50
VALIDATION_TIMEOUT_SEC = 30

validation_executor = ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="validation",
)

# ---------------------------------------------------------------------------
# 실험 프로세스 상태 (전역 뮤텍스 보호)
# ---------------------------------------------------------------------------
experiment_lock = Lock()
experiment_proc: subprocess.Popen | None = None
experiment_run_id: str | None = None

# 기본 실험 설정값
DEFAULT_EXPERIMENT_CONFIG = {
    "max_iterations": 5,
    "n_candidates": 8,
    "top_k": 5,
    "llm_model": "qwen3:8b",
    "llm_provider": "ollama",
    "llm_base_url": None,
    "ollama_host": OLLAMA_HOST,
    "objective_mode": "auto",
}

# ---------------------------------------------------------------------------
# 런타임 설정 (PUT /api/settings 로 갱신 가능)
# ---------------------------------------------------------------------------
runtime_settings: dict = {
    "execution_strategy": "sequential",
    "max_iterations": 5,
    "n_candidates": 8,
    "top_k": 5,
    "llm_model": None,
    "llm_provider": None,
    "llm_base_url": None,
    "ollama_host": OLLAMA_HOST,
    # NIM API 설정 항목은 로컬 모드에서 불필요하므로 제거됨
    "validation_n_trials": 10,
}
