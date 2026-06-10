from __future__ import annotations

from enum import Enum
from typing import Dict, Iterable, List, Optional, Tuple


class RunState(str, Enum):
    RUN_CREATED = "run_created"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    RECOVERING = "recovering"
    JOIN_WAIT = "join_wait"
    JOIN_READY = "join_ready"
    AGGREGATING = "aggregating"
    RUN_ABORTED = "run_aborted"
    RUN_COMPLETED = "run_completed"


class SiloState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SCIENTIFIC_REJECT = "scientific_reject"
    SYSTEM_ERROR = "system_error"
    SYSTEM_ERROR_RECOVERED = "system_error_recovered"
    SYSTEM_FATAL = "system_fatal"


class FailureKind(str, Enum):
    SCIENTIFIC = "scientific"
    SYSTEM = "system"
    UNKNOWN = "unknown"


def classify_failure(reason: str, scientific_reasons: Iterable[str], system_reasons: Iterable[str]) -> FailureKind:
    if reason in set(scientific_reasons):
        return FailureKind.SCIENTIFIC
    if reason in set(system_reasons):
        return FailureKind.SYSTEM
    return FailureKind.UNKNOWN


def is_join_ready(
    silo_states: Dict[str, SiloState],
    required_silos: List[str],
    silo_modes: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Optional[str]]:
    """Return join readiness and blocking silo name.

    Mode-aware all-of join:
    - strict: requires COMPLETED (or SYSTEM_ERROR_RECOVERED after retry)
    - fast: allows COMPLETED, SCIENTIFIC_REJECT, SYSTEM_ERROR_RECOVERED
    """
    strict_ok = {SiloState.COMPLETED, SiloState.SYSTEM_ERROR_RECOVERED}
    fast_ok = {SiloState.COMPLETED, SiloState.SCIENTIFIC_REJECT, SiloState.SYSTEM_ERROR_RECOVERED}

    modes = silo_modes or {}
    for silo in required_silos:
        state = silo_states.get(silo, SiloState.PENDING)
        mode = modes.get(silo, "strict")
        allowed = fast_ok if mode == "fast" else strict_ok
        if state not in allowed:
            return False, silo
    return True, None


def has_system_fatal(silo_states: Dict[str, SiloState]) -> bool:
    return any(state == SiloState.SYSTEM_FATAL for state in silo_states.values())
