from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RecoveryDecision:
    should_retry: bool
    next_backoff_sec: int
    reason: str


def decide_retry(retry_count: int, retry_max: int, backoff_sec: List[int]) -> RecoveryDecision:
    if retry_count >= retry_max:
        return RecoveryDecision(
            should_retry=False,
            next_backoff_sec=0,
            reason="retry_exceeded",
        )

    if not backoff_sec:
        return RecoveryDecision(
            should_retry=True,
            next_backoff_sec=1,
            reason="retry_allowed_default_backoff",
        )

    idx = min(retry_count, len(backoff_sec) - 1)
    return RecoveryDecision(
        should_retry=True,
        next_backoff_sec=backoff_sec[idx],
        reason="retry_allowed",
    )
