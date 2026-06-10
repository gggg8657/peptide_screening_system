"""
status_updater.py
=================
CLI ad-hoc 실험 시 STATUS_FILE 자동 갱신 도구.

사용법:
    python -m pipeline_local.scripts.status_updater --start <task_name>
    python -m pipeline_local.scripts.status_updater --end <task_name> --exit-code 0
    python -m pipeline_local.scripts.status_updater --update --message "step 3/5 완료"
    python -m pipeline_local.scripts.status_updater --update --progress 60

출력:
    /tmp/pipeline_local_status.json  — 현재 STATUS_FILE 갱신 (파일 락 보호)
    /tmp/pipeline_events.jsonl       — 이벤트 append 로그

환경변수:
    PIPELINE_STATUS_FILE   기본: /tmp/pipeline_local_status.json
    PIPELINE_EVENTS_JSONL  기본: /tmp/pipeline_events.jsonl
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------
STATUS_FILE = Path(os.environ.get(
    "PIPELINE_STATUS_FILE",
    "/tmp/pipeline_local_status.json",
))
EVENTS_JSONL = Path(os.environ.get(
    "PIPELINE_EVENTS_JSONL",
    "/tmp/pipeline_events.jsonl",
))

_LOCK_FILE = Path("/tmp/.pipeline_status.lock")


# ---------------------------------------------------------------------------
# 파일 락 유틸
# ---------------------------------------------------------------------------

class _FileLock:
    """fcntl 기반 파일 락 (Unix 전용)."""

    def __init__(self, lock_path: Path, timeout: float = 5.0) -> None:
        self._path = lock_path
        self._timeout = timeout
        self._fd: Optional[int] = None

    def __enter__(self) -> "_FileLock":
        self._fd = os.open(str(self._path), os.O_CREAT | os.O_WRONLY, 0o644)
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    os.close(self._fd)
                    raise TimeoutError(f"STATUS_FILE 락 획득 실패 ({self._timeout}s)")
                time.sleep(0.05)
        return self

    def __exit__(self, *_: Any) -> None:
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None


# ---------------------------------------------------------------------------
# STATUS_FILE 읽기/쓰기
# ---------------------------------------------------------------------------

def _read_status() -> dict:
    """STATUS_FILE을 읽어 dict 반환. 없거나 파싱 실패 시 빈 dict."""
    if not STATUS_FILE.exists():
        return {}
    try:
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_status(data: dict) -> None:
    """STATUS_FILE에 atomic write (파일 락 보호)."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _FileLock(_LOCK_FILE):
        STATUS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )


def _append_event(event: dict) -> None:
    """EVENTS_JSONL에 이벤트 1줄 append."""
    EVENTS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _FileLock(_LOCK_FILE), EVENTS_JSONL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001
        # JSONL append 실패는 치명적이지 않음 — 경고만 출력
        print(f"[status_updater] ⚠️  JSONL append 실패: {exc}", file=sys.stderr)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# 명령 핸들러
# ---------------------------------------------------------------------------

def cmd_start(task_name: str) -> None:
    """--start: 작업 시작 기록."""
    with _FileLock(_LOCK_FILE):
        data = _read_status()

    ts = _now_iso()
    run_id = f"adhoc_{task_name}_{int(time.time())}"

    # 기존 ad-hoc 섹션이 없으면 초기화
    adhoc = data.get("adhoc_tasks", {})
    adhoc[task_name] = {
        "run_id":   run_id,
        "status":   "running",
        "started_at": ts,
        "ended_at": None,
        "exit_code": None,
        "progress_pct": 0,
        "message":  f"{task_name} 시작",
    }
    data["adhoc_tasks"] = adhoc
    data["last_adhoc_task"] = task_name
    data["last_adhoc_ts"] = ts
    data["connected"] = True

    _write_status(data)
    _append_event({
        "type": "start", "task": task_name, "run_id": run_id, "ts": ts,
    })
    print(f"[status_updater] ▶ START task='{task_name}' run_id={run_id}")


def cmd_end(task_name: str, exit_code: int) -> None:
    """--end: 작업 종료 기록."""
    with _FileLock(_LOCK_FILE):
        data = _read_status()

    ts = _now_iso()
    adhoc = data.get("adhoc_tasks", {})

    if task_name not in adhoc:
        # start 기록 없이 end만 호출된 경우 — 새로 생성
        adhoc[task_name] = {"run_id": f"adhoc_{task_name}", "started_at": None}

    task = adhoc[task_name]
    task["status"]   = "completed" if exit_code == 0 else "failed"
    task["ended_at"] = ts
    task["exit_code"] = exit_code
    task["progress_pct"] = 100 if exit_code == 0 else task.get("progress_pct", 0)
    task["message"] = (
        f"{task_name} 완료" if exit_code == 0
        else f"{task_name} 실패 (exit={exit_code})"
    )

    # 경과 시간 계산
    if task.get("started_at"):
        try:
            from datetime import datetime as _dt
            started = _dt.fromisoformat(task["started_at"])
            ended   = _dt.fromisoformat(ts)
            elapsed = (ended - started).total_seconds()
            task["elapsed_sec"] = round(elapsed, 1)
        except Exception:  # noqa: BLE001
            pass

    adhoc[task_name] = task
    data["adhoc_tasks"] = adhoc
    data["last_adhoc_ts"] = ts

    _write_status(data)
    _append_event({
        "type": "end", "task": task_name,
        "run_id": task.get("run_id"), "exit_code": exit_code,
        "elapsed_sec": task.get("elapsed_sec"), "ts": ts,
    })
    status_str = "✅ DONE" if exit_code == 0 else f"❌ FAILED (exit={exit_code})"
    print(f"[status_updater] {status_str} task='{task_name}' elapsed={task.get('elapsed_sec', '?')}s")


def cmd_update(task_name: Optional[str], progress: Optional[int], message: Optional[str]) -> None:
    """--update: 진행 중 progress / message 갱신."""
    with _FileLock(_LOCK_FILE):
        data = _read_status()

    ts = _now_iso()

    # task_name 미지정 시 last_adhoc_task 사용
    if not task_name:
        task_name = data.get("last_adhoc_task")
    if not task_name:
        print("[status_updater] ⚠️  task_name 없음 — --task 또는 먼저 --start 필요", file=sys.stderr)
        return

    adhoc = data.get("adhoc_tasks", {})
    if task_name not in adhoc:
        adhoc[task_name] = {"status": "running", "started_at": ts}

    task = adhoc[task_name]
    if progress is not None:
        task["progress_pct"] = max(0, min(100, progress))
    if message:
        task["message"] = message
    task["updated_at"] = ts

    adhoc[task_name] = task
    data["adhoc_tasks"] = adhoc
    data["last_adhoc_ts"] = ts

    _write_status(data)
    _append_event({
        "type": "update", "task": task_name,
        "progress": progress, "message": message, "ts": ts,
    })
    print(f"[status_updater] 🔄 UPDATE task='{task_name}' progress={progress}% msg='{message}'")


# ---------------------------------------------------------------------------
# CLI 진입점
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="파이프라인 STATUS_FILE 갱신 도구 (ad-hoc CLI 실험용)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python -m pipeline_local.scripts.status_updater --start my_task
  python -m pipeline_local.scripts.status_updater --update --progress 50 --message "half done"
  python -m pipeline_local.scripts.status_updater --end my_task --exit-code 0
  python -m pipeline_local.scripts.status_updater --end my_task --exit-code 1

환경변수:
  PIPELINE_STATUS_FILE   (기본: /tmp/pipeline_local_status.json)
  PIPELINE_EVENTS_JSONL  (기본: /tmp/pipeline_events.jsonl)
        """,
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--start",  metavar="TASK_NAME", help="작업 시작 기록")
    mode.add_argument("--end",    metavar="TASK_NAME", help="작업 종료 기록")
    mode.add_argument("--update", action="store_true",  help="진행 상황 갱신")

    parser.add_argument("--exit-code", type=int, default=0, metavar="N",
                        help="--end 시 종료 코드 (기본: 0)")
    parser.add_argument("--task",     metavar="TASK_NAME",
                        help="--update 시 대상 작업명 (생략 시 마지막 start 작업)")
    parser.add_argument("--progress", type=int, metavar="0-100",
                        help="--update 시 진행률 (%)")
    parser.add_argument("--message",  metavar="MSG",
                        help="--update 시 상태 메시지")

    args = parser.parse_args()

    try:
        if args.start:
            cmd_start(args.start)
        elif args.end:
            cmd_end(args.end, args.exit_code)
        elif args.update:
            cmd_update(args.task, args.progress, args.message)
    except TimeoutError as exc:
        print(f"[status_updater] ❌ 락 타임아웃: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"[status_updater] ❌ 오류: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
