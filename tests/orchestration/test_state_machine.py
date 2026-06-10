from pipelines.orchestration.recovery import decide_retry
from pipelines.orchestration.state_machine import (
    FailureKind,
    SiloState,
    classify_failure,
    has_system_fatal,
    is_join_ready,
)


def test_classify_failure() -> None:
    scientific = ["gate_fail", "score_below_threshold"]
    system = ["runtime_error", "timeout"]

    assert classify_failure("gate_fail", scientific, system) == FailureKind.SCIENTIFIC
    assert classify_failure("runtime_error", scientific, system) == FailureKind.SYSTEM
    assert classify_failure("unknown_reason", scientific, system) == FailureKind.UNKNOWN


def test_join_ready_all_of_mode_aware() -> None:
    states = {
        "A": SiloState.COMPLETED,
        "B": SiloState.SCIENTIFIC_REJECT,
        "C": SiloState.SYSTEM_ERROR_RECOVERED,
    }
    ready, blocked = is_join_ready(
        states,
        ["A", "B", "C"],
        silo_modes={"A": "strict", "B": "fast", "C": "strict"},
    )
    assert ready is True
    assert blocked is None


def test_join_wait_when_system_error_exists() -> None:
    states = {
        "A": SiloState.COMPLETED,
        "B": SiloState.SYSTEM_ERROR,
        "C": SiloState.COMPLETED,
    }
    ready, blocked = is_join_ready(
        states,
        ["A", "B", "C"],
        silo_modes={"A": "strict", "B": "fast", "C": "strict"},
    )
    assert ready is False
    assert blocked == "B"


def test_join_strict_mode_blocks_scientific_reject() -> None:
    states = {
        "A": SiloState.COMPLETED,
        "B": SiloState.COMPLETED,
        "C": SiloState.SCIENTIFIC_REJECT,
    }
    ready, blocked = is_join_ready(
        states,
        ["A", "B", "C"],
        silo_modes={"A": "strict", "B": "fast", "C": "strict"},
    )
    assert ready is False
    assert blocked == "C"


def test_has_system_fatal() -> None:
    states = {
        "A": SiloState.COMPLETED,
        "B": SiloState.SYSTEM_FATAL,
        "C": SiloState.RUNNING,
    }
    assert has_system_fatal(states) is True


def test_recovery_retry_decision() -> None:
    d1 = decide_retry(retry_count=0, retry_max=3, backoff_sec=[10, 30, 60])
    assert d1.should_retry is True
    assert d1.next_backoff_sec == 10

    d2 = decide_retry(retry_count=3, retry_max=3, backoff_sec=[10, 30, 60])
    assert d2.should_retry is False
    assert d2.reason == "retry_exceeded"
