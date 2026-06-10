from __future__ import annotations

from pipeline_local.schemas.io_schemas import Step03bOutput
from pipeline_local.strategies.base import MutationStrategy
from pipeline_local.strategies.esm_scan import ESMScanStrategy, ESMSubstitution
from pipeline_local.strategies.registry import get_strategy


def _esm_config(max_variants: int = 5) -> dict:
    return {
        "approach_b": {
            "strategy": "esm_scan",
            "seed_sequence": "AGCKNFFWKTFTSC",
            "fixed_positions": {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"},
            "max_variants": max_variants,
            "esm_scan_opts": {
                "model": "esm2_t33_650M_UR50D",
                "score_quantile": 0.7,
                "device": "cpu",
                "max_mutations_per_variant": 3,
            },
        },
    }


def _mock_scores(seed: str, mutable_positions: list[int], opts: dict) -> list[ESMSubstitution]:
    substitutions: list[ESMSubstitution] = []
    for rank, pos in enumerate(mutable_positions):
        original = seed[pos - 1]
        for offset, sub_aa in enumerate(["A", "S", "T", "V", "Y"]):
            if sub_aa == original:
                continue
            substitutions.append(ESMSubstitution(
                pos=pos,
                original_aa=original,
                sub_aa=sub_aa,
                esm_delta=float(rank * 10 + offset),
            ))
    return substitutions


def test_esm_scan_strategy_conforms_to_protocol():
    strategy = ESMScanStrategy()

    assert isinstance(strategy, MutationStrategy)
    assert strategy.name == "esm_scan"
    assert isinstance(get_strategy("esm_scan"), ESMScanStrategy)


def test_esm_scan_validate_env_missing_dependency(monkeypatch):
    def fake_find_spec(name: str):
        return None

    monkeypatch.setattr("pipeline_local.strategies.esm_scan.importlib.util.find_spec", fake_find_spec)

    ok, error = ESMScanStrategy().validate_env()

    assert ok is False
    assert error is not None
    assert "Missing ESM dependencies" in error
    assert "torch" in error
    assert "fair-esm or transformers" in error


def test_esm_scan_generate_with_mock_scoring_smoke(monkeypatch):
    monkeypatch.setattr(ESMScanStrategy, "_score_substitution_deltas", staticmethod(_mock_scores))

    result = ESMScanStrategy().generate(_esm_config(max_variants=5))

    assert isinstance(result, Step03bOutput)
    assert result.total_generated == 5
    assert len(result.variants) == 5
    assert result.fixed_positions == {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"}
    assert all(v.source == "esm_scan" for v in result.variants)
    assert all(v.variant_id == f"var_{i:03d}" for i, v in enumerate(result.variants, start=1))
    assert all(v.sequence[2] == "C" for v in result.variants)
    assert all(v.sequence[6:10] == "FWKT" for v in result.variants)
    assert all(v.sequence[13] == "C" for v in result.variants)
    assert all(v.n_mutations == len(v.mutations) for v in result.variants)
