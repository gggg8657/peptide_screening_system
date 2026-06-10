"""
flexpepdock_worker.py
======================
FlexPepDock 정밀 도킹 워커 프로세스.

역할:
  - runs_local/flexpepdock_jobs/ 큐를 폴링
  - lock 파일로 동시 실행 1개 제한
  - 각 job 디렉토리의 status.json을 업데이트
  - FlexPepDock (PyRosetta) 로 수용체별 도킹 수행
  - 완료 후 result.json / ensemble PDB 저장
  - ETA 학습: eta_history.json 누적 → 다음 job ETA 추정

사용법:
  conda run -n bio-tools python pipeline_local/scripts/flexpepdock_worker.py

또는 main.py lifespan에서 subprocess로 실행.
"""
from __future__ import annotations

import fcntl  # Unix 전용 파일 잠금 (Linux/macOS)
import json
import logging
import os
import signal
import subprocess
import sys
import tarfile
import threading
import time
from pathlib import Path
from typing import Any, Optional

# 프로젝트 루트를 PYTHONPATH에 추가
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("flexpepdock_worker")

# ---------------------------------------------------------------------------
# 경로 상수
# ---------------------------------------------------------------------------

JOBS_DIR = _REPO_ROOT / "runs_local" / "flexpepdock_jobs"
LOCK_FILE = JOBS_DIR / ".lock"
ETA_HISTORY_FILE = JOBS_DIR / "eta_history.json"
PYROSETTA_CONDA_ENV = "bio-tools"

# 수용체 PDB 검색 경로 (우선순위 순)
_RECEPTOR_SEARCH_PATHS: list[tuple[str, str]] = [
    # (레이블, 패턴 포맷) — {name} 에 SSTR1 등이 들어감
    ("somatostatin_receptor_pdb",  str(_REPO_ROOT / "data" / "somatostatin_receptor" / "{name}_{pdb_id}.pdb")),
    ("somatostatin_receptor_cif",  str(_REPO_ROOT / "data" / "somatostatin_receptor" / "{name}_{pdb_id}.cif")),
    ("gpcr_only",                  str(_REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "receptors_gpcr_only" / "{name}_gpcr.pdb")),
]

# 기존 routers/selectivity.py와 동일한 PDB ID 매핑
_RECEPTOR_PDB_IDS: dict[str, str] = {
    "SSTR1": "9IK8",
    "SSTR2": "7XNA",
    "SSTR3": "8XIR",
    "SSTR4": "7XMT",
    "SSTR5": "8ZBJ",
}

# ETA 기본값 (이전 이력 없을 때, 수용체 1개 기준)
_DEFAULT_ETA_PER_RECEPTOR_SEC: int = 30 * 60  # 30분

# 폴링 간격
_POLL_INTERVAL_SEC: float = 2.0

# per-job lock fd 캐시 (프로세스 로컬 — fcntl.flock 잠금 유지용, V4-B)
_job_lock_fds: dict[str, int] = {}

# start_flexpepdock_workers.sh 가 생성하는 PID 파일 디렉토리 및 최대 워커 수 (V5-R4)
_PID_FILE_DIR: Path = Path("/tmp")
_MAX_WORKER_SLOTS: int = 4  # worker-1 ~ worker-4


# ---------------------------------------------------------------------------
# ETA 관리
# ---------------------------------------------------------------------------


def load_eta_history() -> list[dict[str, Any]]:
    """eta_history.json을 읽어 이력 목록을 반환한다."""
    if not ETA_HISTORY_FILE.exists():
        return []
    try:
        return json.loads(ETA_HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_eta_history(history: list[dict[str, Any]]) -> None:
    """eta_history.json에 이력을 저장한다."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    ETA_HISTORY_FILE.write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def estimate_eta(n_receptors: int, nstruct: int) -> int:
    """이전 완료 이력 기반으로 ETA(초)를 추정한다.

    Args:
        n_receptors: 도킹할 수용체 수.
        nstruct:     nstruct 파라미터.

    Returns:
        예상 소요 시간(초). 이력 5건 미만이면 보수적 기본값 사용.
    """
    history = load_eta_history()
    if len(history) < 5:
        # 이력 부족 → 보수적 기본값
        return _DEFAULT_ETA_PER_RECEPTOR_SEC * n_receptors

    # 수용체 1개·nstruct 정규화된 평균
    times_per_receptor: list[float] = []
    for entry in history[-20:]:  # 최근 20건
        r = entry.get("n_receptors", 1)
        ns = entry.get("nstruct", 50)
        elapsed = entry.get("elapsed_sec", 0)
        if r > 0 and ns > 0:
            # nstruct 보정: nstruct에 비례하는 시간 가정
            normalized = elapsed / r * (nstruct / ns)
            times_per_receptor.append(normalized)

    if not times_per_receptor:
        return _DEFAULT_ETA_PER_RECEPTOR_SEC * n_receptors

    avg = sum(times_per_receptor) / len(times_per_receptor)
    return int(avg * n_receptors)


def record_eta_history(
    n_receptors: int,
    nstruct: int,
    elapsed_sec: float,
    job_id: str,
) -> None:
    """완료 job의 실행 시간을 이력에 기록한다."""
    history = load_eta_history()
    history.append({
        "job_id": job_id,
        "n_receptors": n_receptors,
        "nstruct": nstruct,
        "elapsed_sec": round(elapsed_sec, 1),
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    # 최근 100건만 유지
    save_eta_history(history[-100:])


# ---------------------------------------------------------------------------
# Lock 관리
# ---------------------------------------------------------------------------


def acquire_lock() -> bool:
    """lock 파일을 획득한다.

    stale lock (PID 없음): 자동 회수 후 획득.

    Returns:
        True if lock acquired, False if another process holds it.
    """
    JOBS_DIR.mkdir(parents=True, exist_ok=True)

    if LOCK_FILE.exists():
        try:
            data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
        except (json.JSONDecodeError, ValueError, OSError):
            pid = 0

        if pid and _pid_alive(pid):
            logger.info("Lock held by PID=%d — 대기", pid)
            return False

        # stale lock → 회수
        logger.warning("Stale lock (PID=%d 없음) 자동 회수", pid)
        LOCK_FILE.unlink(missing_ok=True)

    try:
        LOCK_FILE.write_text(
            json.dumps({"pid": os.getpid(), "acquired_at": time.time()}),
            encoding="utf-8",
        )
        return True
    except OSError as exc:
        logger.error("Lock 파일 쓰기 실패: %s", exc)
        return False


def release_lock() -> None:
    """lock 파일을 해제한다 (본 프로세스 PID 확인 후 삭제)."""
    if not LOCK_FILE.exists():
        return
    try:
        data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        if int(data.get("pid", 0)) == os.getpid():
            LOCK_FILE.unlink(missing_ok=True)
            logger.info("Lock 해제 완료")
    except (json.JSONDecodeError, ValueError, OSError):
        LOCK_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Per-job Lock 관리 (Worker Pool 지원)
# ---------------------------------------------------------------------------


def acquire_job_lock(job_id: str) -> bool:
    """per-job 파일 잠금 획득 (fcntl.flock LOCK_EX|LOCK_NB).

    두 워커가 동일 job에 진입하지 못하도록 원자적으로 잠금한다.
    프로세스 종료 시 커널이 자동으로 잠금을 해제한다.

    Args:
        job_id: 잠글 job ID.

    Returns:
        True if lock acquired, False if another worker holds it or dir missing.
    """
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        return False

    lock_path = job_dir / "worker.lock"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_WRONLY, 0o644)
    except OSError as exc:
        logger.warning("worker.lock 파일 열기 실패 (job=%s): %s", job_id, exc)
        return False

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        # 다른 워커가 이미 잠금 보유 중
        os.close(fd)
        return False
    except OSError as exc:
        logger.warning("flock 획득 실패 (job=%s): %s", job_id, exc)
        os.close(fd)
        return False

    # 잠금 성공 — PID 기록 후 fd 보관 (잠금 유지용)
    try:
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
    except OSError:
        pass  # 기록 실패해도 잠금은 유효

    _job_lock_fds[job_id] = fd
    logger.debug("per-job lock 획득 (job=%s, PID=%d)", job_id, os.getpid())
    return True


def release_job_lock(job_id: str) -> None:
    """per-job 파일 잠금 해제.

    Args:
        job_id: 해제할 job ID.
    """
    fd = _job_lock_fds.pop(job_id, None)
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    logger.debug("per-job lock 해제 (job=%s)", job_id)


def _pid_alive(pid: int) -> bool:
    """주어진 PID가 현재 실행 중인지 확인한다."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


# ---------------------------------------------------------------------------
# Orphan worker PID 파일 정리
# ---------------------------------------------------------------------------


def cleanup_stale_worker_pid_files() -> list[int]:
    """stale(dead) worker PID 파일을 탐지·삭제하고, 연관 lock 파일도 정리한다.

    ``start_flexpepdock_workers.sh`` 가 ``/tmp/flexpepdock_worker_N.pid``
    (N=1..4) 형식으로 PID 파일을 남긴다. 서버 재시작 또는 비정상 종료 시
    PID 파일이 남아 새 worker 기동을 막으므로, startup 시 dead PID를 정리한다.

    알고리즘:
        1. /tmp/flexpepdock_worker_N.pid (N=1..4) 전부 검사
        2. 파일이 없으면 건너뜀
        3. PID를 읽어 ``os.kill(pid, 0)`` 으로 alive 체크
        4. dead PID → PID 파일 삭제 + 로그
        5. lock 파일(.lock) 에 dead PID 기록이 남았으면 함께 삭제

    Returns:
        정리된 dead PID 목록. 빈 리스트이면 모두 살아 있거나 파일 없음.
    """
    cleaned: list[int] = []

    for slot in range(1, _MAX_WORKER_SLOTS + 1):
        pid_path = _PID_FILE_DIR / f"flexpepdock_worker_{slot}.pid"
        if not pid_path.exists():
            continue

        try:
            raw = pid_path.read_text(encoding="utf-8").strip()
            pid = int(raw)
        except (ValueError, OSError) as exc:
            logger.warning(
                "[orphan-cleanup] worker-%d PID 파일 읽기 실패: %s — 파일 삭제",
                slot, exc,
            )
            pid_path.unlink(missing_ok=True)
            continue

        if _pid_alive(pid):
            logger.debug("[orphan-cleanup] worker-%d PID=%d 실행 중 — 유지", slot, pid)
            continue

        # dead PID → 파일 삭제
        logger.warning(
            "[orphan-cleanup] worker-%d PID=%d dead — PID 파일 삭제: %s",
            slot, pid, pid_path,
        )
        pid_path.unlink(missing_ok=True)
        cleaned.append(pid)

    # lock 파일이 dead PID를 가리키면 함께 정리
    _cleanup_stale_lock_if_dead()

    if cleaned:
        logger.info(
            "[orphan-cleanup] stale PID %d건 정리 완료: %s", len(cleaned), cleaned
        )
    else:
        logger.debug("[orphan-cleanup] stale PID 없음 — 정리 불필요")

    return cleaned


def _cleanup_stale_lock_if_dead() -> None:
    """lock 파일 보유 PID가 dead이면 lock을 회수한다.

    acquire_lock() 의 stale-lock 회수 로직과 동일하지만,
    startup 시 명시적으로 호출하기 위해 별도 함수로 분리.
    """
    if not LOCK_FILE.exists():
        return
    try:
        data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        pid = int(data.get("pid", 0))
    except (json.JSONDecodeError, ValueError, OSError):
        pid = 0

    if pid and _pid_alive(pid):
        # 살아 있는 프로세스가 lock 보유 중 — 건드리지 않음
        return

    logger.warning(
        "[orphan-cleanup] lock 파일 보유 PID=%d dead — lock 강제 회수: %s",
        pid, LOCK_FILE,
    )
    LOCK_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Job 파일 I/O
# ---------------------------------------------------------------------------


def read_job(job_id: str) -> Optional[dict[str, Any]]:
    """job.json을 읽어 반환한다. 없으면 None."""
    p = JOBS_DIR / job_id / "job.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def read_status_file(job_id: str) -> Optional[dict[str, Any]]:
    """status.json을 읽어 반환한다."""
    p = JOBS_DIR / job_id / "status.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_status(
    job_id: str,
    state: str,
    progress: float = 0.0,
    eta_seconds: int = 0,
    error_message: str = "",
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
) -> None:
    """status.json을 업데이트한다."""
    p = JOBS_DIR / job_id / "status.json"
    current: dict[str, Any] = {}
    if p.exists():
        try:
            current = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    current.update({
        "state": state,
        "progress": round(progress, 3),
        "eta_seconds": eta_seconds,
        "error_message": error_message,
    })
    if started_at:
        current["started_at"] = started_at
    if finished_at:
        current["finished_at"] = finished_at

    p.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")


def write_result(job_id: str, result_data: dict[str, Any]) -> None:
    """result.json을 저장한다."""
    p = JOBS_DIR / job_id / "result.json"
    p.write_text(json.dumps(result_data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# 시퀀스 검증
# ---------------------------------------------------------------------------


def validate_sequence(sequence: str) -> tuple[bool, str]:
    """SST-14 시퀀스 사전 검증.

    Args:
        sequence: 14aa 1-letter 코드.

    Returns:
        (is_valid, error_message). is_valid=True이면 error_message="".
    """
    seq = sequence.strip().upper()

    # 길이 확인
    if len(seq) != 14:
        return False, f"시퀀스 길이 {len(seq)}aa — 14aa 필요"

    # 아미노산 1문자 코드 확인
    valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
    invalid_chars = [c for c in seq if c not in valid_aa]
    if invalid_chars:
        return False, f"유효하지 않은 아미노산 코드: {invalid_chars}"

    # Cys3-Cys14 위치 확인 (1-indexed)
    if seq[2] != "C":
        return False, f"Cys3 위치({seq[2]})가 C가 아님 — SST-14 SS bond 위반"
    if seq[13] != "C":
        return False, f"Cys14 위치({seq[13]})가 C가 아님 — SST-14 SS bond 위반"

    return True, ""


# ---------------------------------------------------------------------------
# 수용체 PDB 경로 조회
# ---------------------------------------------------------------------------


def get_receptor_pdb_path(receptor_name: str) -> Optional[str]:
    """수용체 이름(예: "SSTR2")에 대한 PDB 파일 경로를 반환한다.

    검색 경로 우선순위:
    1. data/somatostatin_receptor/{NAME}_{PDB_ID}.pdb
    2. data/somatostatin_receptor/{NAME}_{PDB_ID}.cif
    3. runs_local/selectivity_demo_*/receptors_gpcr_only/{NAME}_gpcr.pdb

    Returns:
        존재하는 PDB/CIF 파일 경로 문자열. 없으면 None.
    """
    name = receptor_name.upper()
    pdb_id = _RECEPTOR_PDB_IDS.get(name, "")

    for label, pattern in _RECEPTOR_SEARCH_PATHS:
        path_str = pattern.format(name=name, pdb_id=pdb_id)
        p = Path(path_str)
        if p.exists():
            logger.debug("수용체 %s → %s (%s)", name, p, label)
            return str(p)

    logger.warning("수용체 %s PDB 파일을 찾지 못함", name)
    return None


def preflight_check(
    sequence: str,
    receptors: list[str],
) -> tuple[bool, str]:
    """사전 검증: 시퀀스 + 수용체 PDB 존재 + PyRosetta 가용성.

    Returns:
        (ok, error_message)
    """
    # 1. 시퀀스 검증
    seq_ok, seq_err = validate_sequence(sequence)
    if not seq_ok:
        return False, f"시퀀스 오류: {seq_err}"

    # 2. 수용체 PDB 존재 확인
    missing: list[str] = []
    for r in receptors:
        if get_receptor_pdb_path(r) is None:
            missing.append(r)
    if missing:
        return False, f"수용체 PDB 없음: {missing}. data/somatostatin_receptor/ 에 파일을 배치하세요."

    # 3. PyRosetta(bio-tools conda env) 가용성 확인
    try:
        proc = subprocess.run(
            ["conda", "run", "-n", PYROSETTA_CONDA_ENV, "python", "-c",
             "import pyrosetta; print('OK')"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0 or "OK" not in proc.stdout:
            # PyRosetta 미설치 시 경고 (estimation fallback 허용)
            logger.warning(
                "PyRosetta bio-tools 환경 미확인 — stub 결과로 fallback 됩니다. "
                "conda activate bio-tools 확인 권장."
            )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("conda 실행 불가 — PyRosetta stub fallback")

    return True, ""


# ---------------------------------------------------------------------------
# FlexPepDock 실행 (PyRosetta subprocess)
# ---------------------------------------------------------------------------


def _run_flexpepdock_for_receptor(
    job_id: str,
    sequence: str,
    receptor_name: str,
    receptor_pdb: str,
    config: dict[str, Any],
    ensemble_dir: Path,
    cancel_flag: list[bool],
) -> dict[str, Any]:
    """단일 수용체에 대해 FlexPepDock을 실행하고 결과를 반환한다.

    PyRosetta가 없으면 stub 결과(ddg 임의값) 반환.

    Args:
        job_id:       Job ID (로깅용).
        sequence:     14aa 펩타이드 시퀀스.
        receptor_name: 수용체 이름 (예: "SSTR2").
        receptor_pdb: 수용체 PDB 경로.
        config:       FlexPepDock 파라미터.
        ensemble_dir: PDB 앙상블 저장 디렉토리.
        cancel_flag:  [False/True] — True로 설정되면 도킹 중단.

    Returns:
        {receptor, dG_kcal_mol, interface_score, pass, pdb_paths}
    """
    if cancel_flag[0]:
        raise InterruptedError("취소 요청")

    cycles: int = int(config.get("cycles", 10))
    nstruct: int = int(config.get("nstruct", 50))
    flex_pep_freedom: str = config.get("flex_pep_freedom", "med")
    ddg_cycle: int = int(config.get("ddg_cycle", 5))

    logger.info("[%s] FlexPepDock 시작: receptor=%s, cycles=%d, nstruct=%d",
                job_id, receptor_name, cycles, nstruct)

    receptor_ens_dir = ensemble_dir / receptor_name
    receptor_ens_dir.mkdir(parents=True, exist_ok=True)

    # PyRosetta script 경로 탐색
    script_candidates = [
        _REPO_ROOT / "pipeline_local" / "scripts" / "flexpep_dock.py",
        _REPO_ROOT / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri" / "AG_src" / "scripts" / "flexpep_dock.py",
        _REPO_ROOT / "bionemo" / "flexpep_dock.py",
        *([Path(os.environ["PYROSETTA_SCRIPTS_DIR"]) / "flexpep_dock.py"]
          if os.environ.get("PYROSETTA_SCRIPTS_DIR") else []),
    ]
    script_path: Optional[Path] = None
    for c in script_candidates:
        if c.exists():
            script_path = c
            break

    if script_path is None:
        logger.warning("[%s] flexpep_dock.py 스크립트 없음 — stub 결과 사용", job_id)
        return _stub_dock_result(receptor_name)

    output_prefix = str(receptor_ens_dir / "docked")
    cmd = [
        "conda", "run", "-n", PYROSETTA_CONDA_ENV,
        "python", str(script_path),
        "--receptor", receptor_pdb,
        "--sequence", sequence,
        "--output-prefix", output_prefix,
        "--cycles", str(cycles),
        "--nstruct", str(nstruct),
        "--flex-pep-freedom", flex_pep_freedom,
        "--ddg-cycle", str(ddg_cycle),
    ]

    # 기본 6시간 (V4-A 2026-05-20): 4시간은 SSTR1 도킹(nstruct=50, cycles=10)에 부족.
    # 사용자 보고 32e8cfe1 잡: SSTR1에서 timeout cancel → SSTR2~5 미진행. 6h로 확장.
    # 큰 잡(nstruct≥100)은 env var FLEXPEPDOCK_TIMEOUT으로 override 가능.
    timeout = int(os.environ.get("FLEXPEPDOCK_TIMEOUT", str(6 * 3600)))  # 기본 6시간

    try:
        t0 = time.monotonic()
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - t0

        if proc.returncode != 0:
            logger.error(
                "[%s] FlexPepDock 실패 receptor=%s (code=%d, %.1fs): %s",
                job_id, receptor_name, proc.returncode, elapsed, proc.stderr[-500:]
            )
            return _stub_dock_result(receptor_name)

        # stdout에서 JSON 결과 파싱
        try:
            scores = json.loads(proc.stdout.strip())
        except json.JSONDecodeError:
            logger.warning("[%s] stdout JSON 파싱 실패: %s", job_id, proc.stdout[:200])
            scores = {}

        dg = float(scores.get("dG_kcal_mol", scores.get("ddg", 0.0)))
        interface_score = float(scores.get("interface_score", 0.0))
        # SSTR2 선택성 게이트: interface_score < -30 을 pass 기준으로 사용
        pass_gate = interface_score < -30.0

        pdb_paths = [str(p) for p in receptor_ens_dir.glob("*.pdb")]

        logger.info(
            "[%s] FlexPepDock 완료 receptor=%s, dG=%.2f, IS=%.2f, pass=%s (%.1fs)",
            job_id, receptor_name, dg, interface_score, pass_gate, elapsed
        )

        return {
            "receptor": receptor_name,
            "dG_kcal_mol": round(dg, 3),
            "interface_score": round(interface_score, 3),
            "pass": pass_gate,
            "pdb_paths": pdb_paths,
        }

    except subprocess.TimeoutExpired:
        logger.error("[%s] FlexPepDock timeout receptor=%s", job_id, receptor_name)
        return _stub_dock_result(receptor_name, error="timeout")
    except InterruptedError:
        raise
    except Exception as exc:
        logger.exception("[%s] FlexPepDock 예외 receptor=%s: %s", job_id, receptor_name, exc)
        return _stub_dock_result(receptor_name, error=str(exc))


def _stub_dock_result(
    receptor_name: str,
    error: str = "",
) -> dict[str, Any]:
    """PyRosetta 미설치 또는 실패 시 stub 결과를 반환한다.

    HEURISTIC_FUNCTION_DISCLAIMERS 정책: 추정값임을 명시.
    """
    import random
    dg = round(random.gauss(-8.0, 3.0), 3)
    interface_score = round(random.gauss(-35.0, 10.0), 3)
    logger.warning(
        "STUB 결과 사용 (receptor=%s, error=%s) — 실 FlexPepDock 아님",
        receptor_name, error or "PyRosetta 미설치"
    )
    return {
        "receptor": receptor_name,
        "dG_kcal_mol": dg,
        "interface_score": interface_score,
        "pass": interface_score < -30.0,
        "pdb_paths": [],
        "stub": True,
        "stub_reason": error or "PyRosetta 미설치",
    }


# ---------------------------------------------------------------------------
# nstruct 단위 sub-progress ticker
# ---------------------------------------------------------------------------


def _start_progress_ticker(
    job_id: str,
    receptor_idx: int,
    total_receptors: int,
    job_start: float,
    job_eta_sec: int,
    eta_per_receptor_sec: float,
    started_at: str,
    interval_sec: float = 15.0,
) -> threading.Event:
    """receptor 내부에서 timer 기반 sub-progress를 주기적으로 업데이트하는 백그라운드 스레드를 시작한다.

    FlexPepDock subprocess는 subprocess.run()으로 블록되므로 worker 측에서
    nstruct 완료 알림을 받을 수 없다. 대신 elapsed / ETA 비율로 sub_progress 를
    추정(Option B)하여 사용자가 "멈춘 것"으로 오인하지 않도록 한다.

    Args:
        job_id:               Job ID (status.json 경로 도출).
        receptor_idx:         현재 수용체 인덱스 (0-based).
        total_receptors:      전체 수용체 수.
        job_start:            워커 루프 시작 time.monotonic() 값.
        job_eta_sec:          전체 job 예상 소요 시간(초).
        eta_per_receptor_sec: 이 수용체 1개의 예상 소요 시간(초).
        started_at:           ISO-8601 시작 타임스탬프 (status.json 유지용).
        interval_sec:         업데이트 주기 (기본 15초).

    Returns:
        stop_event — 호출자가 .set() 하면 스레드가 안전하게 종료된다.
    """
    stop_event = threading.Event()
    receptor_start = time.monotonic()

    def _tick() -> None:
        while not stop_event.wait(interval_sec):
            elapsed_in_receptor = time.monotonic() - receptor_start
            if eta_per_receptor_sec > 0:
                # 0.95 cap: 완료 직전처럼 보이지 않도록 (실제 완료는 caller가 기록)
                sub_progress = min(0.95, elapsed_in_receptor / eta_per_receptor_sec)
            else:
                sub_progress = 0.0

            progress = (receptor_idx + sub_progress) / total_receptors

            # 잔여 ETA: 전체 job ETA − 지금까지 경과 시간
            total_elapsed = time.monotonic() - job_start
            remaining_eta = max(0, int(job_eta_sec - total_elapsed))

            write_status(
                job_id,
                state="running",
                progress=progress,
                eta_seconds=remaining_eta,
                started_at=started_at,
            )

    t = threading.Thread(
        target=_tick,
        daemon=True,
        name=f"progress-ticker-{job_id}-r{receptor_idx}",
    )
    t.start()
    return stop_event


# ---------------------------------------------------------------------------
# 메인 워커 루프
# ---------------------------------------------------------------------------


def _process_job(job_id: str, cancel_flag: list[bool]) -> None:
    """단일 job을 처리한다.

    Args:
        job_id:      처리할 job ID.
        cancel_flag: [False] — 외부에서 True로 설정하면 중간 취소.
    """
    job_dir = JOBS_DIR / job_id
    job = read_job(job_id)
    if job is None:
        logger.error("[%s] job.json 없음 — skip", job_id)
        return

    sequence: str = job.get("sequence", "")
    receptors: list[str] = job.get("receptors", [])
    config: dict[str, Any] = job.get("config", {})
    nstruct: int = int(config.get("nstruct", 50))

    # 루프 시작 전에 취소 상태 선제 체크 (queued→running 전환 전에 이미 cancelling이면 종료)
    pre_status = read_status_file(job_id)
    if pre_status and pre_status.get("state") in ("cancelling", "failed"):
        cancel_flag[0] = True
        write_status(
            job_id,
            state="failed",
            progress=0.0,
            error_message="사용자에 의해 취소됨 (시작 전)",
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        logger.info("[%s] 취소 상태 감지 — 실행 안 함", job_id)
        return

    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    eta = estimate_eta(len(receptors), nstruct)

    write_status(
        job_id,
        state="running",
        progress=0.0,
        eta_seconds=eta,
        started_at=started_at,
    )

    # stdout.log / stderr.log
    stdout_log = open(job_dir / "stdout.log", "w", encoding="utf-8")
    stderr_log = open(job_dir / "stderr.log", "w", encoding="utf-8")

    ensemble_dir = job_dir / "ensemble"
    ensemble_dir.mkdir(parents=True, exist_ok=True)

    selectivity_matrix: list[dict[str, Any]] = []
    total = len(receptors)
    t_start = time.monotonic()

    try:
        for idx, receptor_name in enumerate(receptors):
            # 취소 체크
            status_data = read_status_file(job_id)
            if status_data and status_data.get("state") == "cancelling":
                cancel_flag[0] = True

            if cancel_flag[0]:
                write_status(
                    job_id,
                    state="failed",
                    progress=idx / total,
                    error_message="사용자에 의해 취소됨",
                    finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                logger.info("[%s] 취소 완료 at receptor %s", job_id, receptor_name)
                return

            receptor_pdb = get_receptor_pdb_path(receptor_name)
            if not receptor_pdb:
                write_status(
                    job_id,
                    state="failed",
                    error_message=f"수용체 PDB 없음: {receptor_name}",
                    finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                return

            # 진행률 업데이트 (receptor 시작 시점)
            elapsed_so_far = time.monotonic() - t_start
            remaining_receptors = total - idx
            if idx > 0:
                avg_per_receptor = elapsed_so_far / idx
                remaining_eta = int(avg_per_receptor * remaining_receptors)
                eta_per_receptor_sec = avg_per_receptor
            else:
                remaining_eta = eta
                eta_per_receptor_sec = float(eta) / max(total, 1)

            write_status(
                job_id,
                state="running",
                progress=idx / total,
                eta_seconds=remaining_eta,
                started_at=started_at,
            )

            # nstruct 단위 sub-progress: timer 기반 ticker로 receptor 내부 진행률 세분화
            stop_ticker = _start_progress_ticker(
                job_id=job_id,
                receptor_idx=idx,
                total_receptors=total,
                job_start=t_start,
                job_eta_sec=eta,
                eta_per_receptor_sec=eta_per_receptor_sec,
                started_at=started_at,
            )

            try:
                result_entry = _run_flexpepdock_for_receptor(
                    job_id=job_id,
                    sequence=sequence,
                    receptor_name=receptor_name,
                    receptor_pdb=receptor_pdb,
                    config=config,
                    ensemble_dir=ensemble_dir,
                    cancel_flag=cancel_flag,
                )
            finally:
                stop_ticker.set()  # ticker 스레드 정지 (완료/실패/취소 무관)

            selectivity_matrix.append(result_entry)
            stdout_log.write(f"[{receptor_name}] 완료: {result_entry}\n")
            stdout_log.flush()

        # Selectivity index 계산: ΔG(SSTR2) - max(ΔG(others))
        selectivity_index = _compute_selectivity_index(selectivity_matrix)

        elapsed_total = time.monotonic() - t_start
        record_eta_history(total, nstruct, elapsed_total, job_id)

        # 결과 저장
        write_result(job_id, {
            "selectivity_matrix": selectivity_matrix,
            "selectivity_index": round(selectivity_index, 3),
            "pdb_paths": [
                str(p)
                for r in receptors
                for p in (ensemble_dir / r).glob("*.pdb")
            ],
        })

        finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_status(
            job_id,
            state="done",
            progress=1.0,
            eta_seconds=0,
            finished_at=finished_at,
        )
        logger.info("[%s] Job 완료 (%.1fs)", job_id, elapsed_total)

    except InterruptedError:
        write_status(
            job_id,
            state="failed",
            error_message="취소됨",
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
    except Exception as exc:
        logger.exception("[%s] Job 처리 오류: %s", job_id, exc)
        stderr_log.write(f"오류: {exc}\n")
        write_status(
            job_id,
            state="failed",
            error_message=str(exc),
            finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
    finally:
        stdout_log.close()
        stderr_log.close()


def _compute_selectivity_index(matrix: list[dict[str, Any]]) -> float:
    """Selectivity index = ΔG(SSTR2) - max(ΔG(others)).

    양수 → SSTR2가 다른 수용체보다 더 강하게 결합 (선택적).

    Args:
        matrix: 각 수용체의 {receptor, dG_kcal_mol, ...} 리스트.

    Returns:
        selectivity index (float). SSTR2 없으면 0.0.
    """
    sstr2_dg: Optional[float] = None
    others_dg: list[float] = []

    for entry in matrix:
        dg = entry.get("dG_kcal_mol", 0.0)
        if entry.get("receptor", "").upper() == "SSTR2":
            sstr2_dg = dg
        else:
            others_dg.append(dg)

    if sstr2_dg is None:
        return 0.0
    if not others_dg:
        return 0.0

    # 더 작은(음수) ΔG = 더 강한 결합
    # max(others_dg) = 가장 약한 off-target
    # selectivity_index = max(others_dg) - sstr2_dg
    # 양수이면 SSTR2가 가장 강하게 결합
    return max(others_dg) - sstr2_dg


def build_ensemble_tar(job_id: str) -> Optional[Path]:
    """ensemble/ 디렉토리를 tar.gz로 압축하여 반환한다.

    Args:
        job_id: Job ID.

    Returns:
        tar.gz 파일 경로. ensemble 없으면 None.
    """
    ensemble_dir = JOBS_DIR / job_id / "ensemble"
    if not ensemble_dir.exists():
        return None

    tar_path = JOBS_DIR / job_id / "ensemble.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(ensemble_dir, arcname="ensemble")

    return tar_path


def find_queued_jobs() -> list[str]:
    """queued 상태의 job_id 리스트를 생성 순서(created_at)로 반환한다."""
    if not JOBS_DIR.exists():
        return []

    queued: list[tuple[float, str]] = []
    for job_dir in JOBS_DIR.iterdir():
        if not job_dir.is_dir():
            continue
        status_file = job_dir / "status.json"
        if not status_file.exists():
            continue
        try:
            status = json.loads(status_file.read_text(encoding="utf-8"))
            if status.get("state") == "queued":
                # created_at 기준 정렬
                job_file = job_dir / "job.json"
                created_at_ts = 0.0
                if job_file.exists():
                    job_data = json.loads(job_file.read_text(encoding="utf-8"))
                    created_str = job_data.get("created_at", "")
                    if created_str:
                        try:
                            import datetime
                            dt = datetime.datetime.fromisoformat(
                                created_str.replace("Z", "+00:00")
                            )
                            created_at_ts = dt.timestamp()
                        except ValueError:
                            pass
                queued.append((created_at_ts, job_dir.name))
        except (json.JSONDecodeError, OSError):
            continue

    queued.sort()
    return [jid for _, jid in queued]


# ---------------------------------------------------------------------------
# Worker 메인 루프 (standalone 실행용)
# ---------------------------------------------------------------------------

_shutdown = False


def _handle_sigterm(signum: int, frame: object) -> None:
    """SIGTERM 수신 시 graceful 종료 플래그 설정."""
    global _shutdown
    logger.info("SIGTERM 수신 — graceful 종료 예약")
    _shutdown = True


def run_worker_loop(worker_id: str = "worker-1") -> None:
    """큐를 폴링하며 job을 처리하는 워커 루프 (worker pool 지원).

    복수 worker 동시 가동 시 per-job 파일 잠금(fcntl.flock)으로
    중복 처리를 방지한다. 두 worker가 각각 다른 job을 동시에 처리 가능.

    Args:
        worker_id: 워커 식별자 (로그·PID 파일 구분용). 기본 "worker-1".
    """
    signal.signal(signal.SIGTERM, _handle_sigterm)

    # V5-R4: 자체 시작 전 stale PID / lock 선정리
    cleanup_stale_worker_pid_files()

    logger.info(
        "FlexPepDock 워커 시작 (worker_id=%s, PID=%d)", worker_id, os.getpid()
    )

    while not _shutdown:
        # queued job 목록 가져오기
        queued = find_queued_jobs()

        if not queued:
            time.sleep(_POLL_INTERVAL_SEC)
            continue

        # queued 순서대로 per-job lock 시도 — 다른 워커가 처리 중인 job은 건너뜀
        job_acquired: Optional[str] = None
        for job_id in queued:
            if acquire_job_lock(job_id):
                job_acquired = job_id
                break
            # 이미 다른 워커가 잠금 보유 → 다음 job 시도

        if job_acquired is None:
            # 모든 queued job이 다른 워커에 의해 처리 중
            logger.debug("[%s] 처리 가능한 job 없음 — 대기", worker_id)
            time.sleep(_POLL_INTERVAL_SEC)
            continue

        logger.info("[%s] Job 처리 시작: %s", worker_id, job_acquired)
        cancel_flag: list[bool] = [False]

        try:
            _process_job(job_acquired, cancel_flag)
        except Exception as exc:
            logger.exception(
                "[%s] Job 처리 예외 (job_id=%s): %s", worker_id, job_acquired, exc
            )
        finally:
            release_job_lock(job_acquired)

        if _shutdown:
            break

    logger.info("[%s] FlexPepDock 워커 종료", worker_id)


if __name__ == "__main__":
    import argparse

    _parser = argparse.ArgumentParser(description="FlexPepDock Worker (pool 지원)")
    _parser.add_argument(
        "--worker-id",
        default="worker-1",
        help="워커 식별자 — 로그·PID 파일 구분용 (기본: worker-1)",
    )
    _args = _parser.parse_args()
    run_worker_loop(worker_id=_args.worker_id)
