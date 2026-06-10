from pathlib import Path

from pipelines.orchestration.policy import load_orchestration_policy


def test_load_orchestration_policy_defaults() -> None:
    policy = load_orchestration_policy(Path("configs/orchestration_policy.yaml"))
    assert policy.orchestration.join_policy == "all_of"
    assert policy.orchestration.required_silos == ["A", "B", "C"]
    assert policy.orchestration.silo_modes["B"] == "fast"
    assert policy.ranking.fusion.weights["C"] == 0.33
