"""Agent log REST + SSE router with runs_local SSOT fallback."""
from __future__ import annotations

import asyncio
import contextlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

import aiofiles
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.state import EXP_LOG

router = APIRouter()


class AgentSpec(BaseModel):
    id: str
    name: str
    role: str
    color: str


class AgentEntry(BaseModel):
    ts: datetime
    agent: str
    level: str = "info"
    text: str


class AgentLogResponse(BaseModel):
    agents: list[AgentSpec]
    entries: list[AgentEntry]


AGENTS: list[AgentSpec] = [
    AgentSpec(id="planner", name="Planner", role="실험 설계", color="violet"),
    AgentSpec(id="builder", name="Builder", role="코드 실행", color="blue"),
    AgentSpec(id="qcranker", name="QCRanker", role="Gate 평가 + 랭킹", color="cyan"),
    AgentSpec(id="diversity", name="DiversityManager", role="foldmason 클러스터링", color="teal"),
    AgentSpec(id="critic", name="Critic", role="실패 진단 + 게이트 조정", color="amber"),
    AgentSpec(id="reporter", name="Reporter", role="요약 + 결정 기록", color="stone"),
]

_subscribers: dict[str, set[asyncio.Queue]] = {}


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _runs_local_root() -> Path:
    return _workspace_root() / "runs_local"


def _candidate_log_paths(run_id: str) -> list[Path]:
    return [
        _runs_local_root() / run_id / "experiment_log.jsonl",
        _runs_local_root() / run_id / "silo_b" / "experiment_log.jsonl",
        EXP_LOG,
    ]


def _resolve_log_path(run_id: str) -> Path | None:
    if not run_id or any(token in run_id for token in ("..", "/", "\\")):
        return None
    for path in _candidate_log_paths(run_id):
        if path.exists():
            return path
    return None


def _coerce_timestamp(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now()


def _load_entries(path: Path) -> list[AgentEntry]:
    entries: list[AgentEntry] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            agent = record.get("agent")
            text = record.get("text")
            if not agent or not text:
                continue
            entries.append(
                AgentEntry(
                    ts=_coerce_timestamp(record.get("ts")),
                    agent=str(agent),
                    level=str(record.get("level", "info")),
                    text=str(text),
                )
            )
    return entries


def _stream_log_path(run_id: str) -> Path | None:
    if not run_id or any(token in run_id for token in ("..", "/", "\\")):
        return None
    return _runs_local_root() / run_id / "experiment_log.jsonl"


def _build_payload(record: dict[str, Any]) -> dict[str, Any] | None:
    agent = record.get("agent")
    text = record.get("text")
    if not agent or not text:
        return None
    return {
        "event": "agent",
        "data": {
            "ts": _coerce_timestamp(record.get("ts")).isoformat(),
            "agent": str(agent),
            "level": str(record.get("level", "info")),
            "text": str(text),
        },
    }


async def _tail_log_file(run_id: str, queue: asyncio.Queue[dict[str, Any]], stop_event: asyncio.Event) -> None:
    path = _stream_log_path(run_id)
    if path is None:
        return

    offset: int | None = None
    while not stop_event.is_set():
        if not path.exists():
            await asyncio.sleep(0.25)
            continue
        current_size = path.stat().st_size
        if offset is None:
            offset = current_size
        elif current_size < offset:
            offset = 0

        async with aiofiles.open(path, "r", encoding="utf-8") as handle:
            await handle.seek(offset)
            while not stop_event.is_set():
                line = await handle.readline()
                if not line:
                    offset = await handle.tell()
                    await asyncio.sleep(0.25)
                    if not path.exists():
                        offset = None
                        break
                    if path.stat().st_size < offset:
                        offset = 0
                        break
                    continue
                offset = await handle.tell()
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                payload = _build_payload(record)
                if payload is None:
                    continue
                await queue.put(payload)


@router.get("/agents/{run_id}/log", response_model=AgentLogResponse)
async def get_agent_log(run_id: str) -> AgentLogResponse:
    path = _resolve_log_path(run_id)
    if path is None:
        return AgentLogResponse(agents=AGENTS, entries=[])
    return AgentLogResponse(agents=AGENTS, entries=_load_entries(path))


async def publish(run_id: str, payload: dict[str, Any]) -> None:
    subs = _subscribers.get(run_id, set())
    for queue in list(subs):
        try:
            await queue.put(payload)
        except Exception:
            subs.discard(queue)


@router.get("/agents/{run_id}/stream")
async def stream_agent_log(run_id: str, request: Request) -> StreamingResponse:
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.setdefault(run_id, set()).add(queue)

    async def event_source() -> AsyncIterator[bytes]:
        stop_event = asyncio.Event()
        tail_task = asyncio.create_task(_tail_log_file(run_id, queue, stop_event))
        try:
            yield b"retry: 3000\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=10.0)
                except asyncio.TimeoutError:
                    yield b": ping\n\n"
                    continue
                event = payload.get("event", "agent")
                data = json.dumps(payload.get("data", payload), default=str)
                yield f"event: {event}\ndata: {data}\n\n".encode("utf-8")
        finally:
            stop_event.set()
            tail_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await tail_task
            _subscribers.get(run_id, set()).discard(queue)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
