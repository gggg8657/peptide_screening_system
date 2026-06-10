"""
5-Agent log + SSE stream router.

마운트:
  from .routers.agents import router as agents_router
  app.include_router(agents_router, prefix="/api/agents", tags=["agents"])

엔드포인트:
  GET /api/agents/{run_id}/log           — 전체 로그 (REST)
  GET /api/agents/{run_id}/stream        — SSE live stream

데이터 소스:
  - 실행 중 agent stdout/jsonl 파일 (예: runs_local/{run_id}/silo_b/experiment_log.jsonl)
  - 또는 in-process pubsub (asyncio.Queue per run)
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..schemas.dashboard import (  # type: ignore — adjust import path to match
    AgentLogResponse, AgentSpec, AgentEntry,
)

router = APIRouter()


AGENTS: list[AgentSpec] = [
    AgentSpec(id="planner",   name="Planner",          role="실험 설계",                 color="violet"),
    AgentSpec(id="builder",   name="Builder",          role="코드 실행",                 color="blue"),
    AgentSpec(id="qcranker",  name="QCRanker",         role="Gate 평가 + 랭킹",          color="cyan"),
    AgentSpec(id="diversity", name="DiversityManager", role="foldmason 클러스터링",      color="teal"),
    AgentSpec(id="critic",    name="Critic",           role="실패 진단 + 게이트 조정",   color="amber"),
    AgentSpec(id="reporter",  name="Reporter",         role="요약 + 결정 기록",          color="stone"),
]


def _runs_root() -> Path:
    """runs_local/ 의 절대 경로. 환경변수 또는 config에서 읽도록 교체."""
    return Path(__file__).resolve().parents[3] / "runs_local"


def _log_path(run_id: str) -> Path:
    return _runs_root() / run_id / "silo_b" / "experiment_log.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{run_id}/log", response_model=AgentLogResponse)
async def get_agent_log(run_id: str) -> AgentLogResponse:
    """전체 누적 로그 (페이지 초기 로드용)."""
    path = _log_path(run_id)
    if not path.exists():
        # TODO: in-memory store가 있다면 거기서 로드. 없으면 빈 리스트 반환.
        return AgentLogResponse(agents=AGENTS, entries=[])

    entries: list[AgentEntry] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
                entries.append(AgentEntry(
                    ts=e.get("ts") or datetime.now(),
                    agent=e["agent"],
                    level=e.get("level", "info"),
                    text=e["text"],
                ))
            except Exception:
                continue
    return AgentLogResponse(agents=AGENTS, entries=entries)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory pub/sub. Replace with Redis pubsub or asyncio file-tail.
_subscribers: dict[str, set[asyncio.Queue]] = {}


async def publish(run_id: str, payload: dict) -> None:
    """agent / status 이벤트를 모든 구독자에게 push. agent 코드에서 호출."""
    subs = _subscribers.get(run_id, set())
    for q in list(subs):
        try:
            await q.put(payload)
        except Exception:
            subs.discard(q)


@router.get("/{run_id}/stream")
async def stream_agent_log(run_id: str, request: Request) -> StreamingResponse:
    """SSE — live agent log + status updates."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.setdefault(run_id, set()).add(queue)

    async def event_source() -> AsyncIterator[bytes]:
        try:
            # send retry hint
            yield b"retry: 3000\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    # keepalive
                    yield b": ping\n\n"
                    continue
                event = payload.get("event", "agent")
                data = json.dumps(payload.get("data", payload), default=str)
                yield f"event: {event}\ndata: {data}\n\n".encode("utf-8")
        finally:
            _subscribers.get(run_id, set()).discard(queue)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Example helper for agent code:
#
#   await publish("local_20260512_1430_iter02", {
#       "event": "agent",
#       "data": {
#           "ts": datetime.now().isoformat(),
#           "agent": "critic",
#           "text": "T2 후보 cand03 - 유일 SSTR2-selective"
#       }
#   })
