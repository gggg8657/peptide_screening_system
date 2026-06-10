from __future__ import annotations

from typing import Any, Dict

from pipeline_local.scoring import layer1_ensemble as l1
from pipeline_local.scoring.ensemble_router import route_halflife_prediction
from pipeline_local.scripts import predict_halflife_pepmsnd as ph


def test_l_aa_single_sequence_returns_weighted_ensemble(monkeypatch):
    monkeypatch.setattr(l1, "_predict_plifepred", lambda sequence: {"value": 2.0, "unit": "hours", "confidence": "P2"})
    monkeypatch.setattr(l1, "_predict_hle_regression", lambda sequence: {"value": 4.0, "unit": "hours", "confidence": "P3"})
    monkeypatch.setattr(l1, "_predict_pepadmet_hbm", lambda sequence: {"value": 8.0, "unit": "hours", "confidence": "P1"})

    result = l1.compute_layer1_halflife(
        "AGAKNFFWKTFTSA",
        weights={"plifepred": 1.0, "hle_regression": 1.0, "pepadmet_hbm": 2.0},
    )

    assert result["unavailable"] is False
    assert result["tools_used"] == ["plifepred", "hle_regression", "pepadmet_hbm"]
    assert result["ensemble_halflife_hours"] == 6.0
    assert result["absolute_confidence"] == "P3"


def test_one_unavailable_tool_renormalizes_weights(monkeypatch):
    monkeypatch.setattr(l1, "_predict_plifepred", lambda sequence: {"value": 2.0, "unit": "hours", "confidence": "P1"})
    monkeypatch.setattr(l1, "_predict_hle_regression", lambda sequence: {"unavailable": True, "reason": "not installed"})
    monkeypatch.setattr(l1, "_predict_pepadmet_hbm", lambda sequence: {"value": 6.0, "unit": "hours", "confidence": "P1"})

    result = l1.compute_layer1_halflife(
        "AGAKNFFWKTFTSA",
        weights={"plifepred": 1.0, "hle_regression": 1.0, "pepadmet_hbm": 1.0},
    )

    assert result["tools_used"] == ["plifepred", "pepadmet_hbm"]
    assert result["tools_unavailable"] == ["hle_regression"]
    assert result["ensemble_halflife_hours"] == 4.0
    assert result["individual_predictions"]["plifepred"]["weight"] == 0.5
    assert result["individual_predictions"]["pepadmet_hbm"]["weight"] == 0.5


def test_all_tools_fail_marks_ensemble_unavailable(monkeypatch):
    def fail(sequence: str) -> Dict[str, Any]:
        return {"unavailable": True, "reason": "missing wrapper"}

    monkeypatch.setattr(l1, "_predict_plifepred", fail)
    monkeypatch.setattr(l1, "_predict_hle_regression", fail)
    monkeypatch.setattr(l1, "_predict_pepadmet_hbm", fail)

    result = l1.compute_layer1_halflife("AGAKNFFWKTFTSA")

    assert result["unavailable"] is True
    assert result["ensemble_halflife_hours"] is None
    assert result["tools_used"] == []
    assert set(result["tools_unavailable"]) == {"plifepred", "hle_regression", "pepadmet_hbm"}
    assert all(p["unavailable"] is True for p in result["individual_predictions"].values())


def test_plifepred_hour_conversion_success(monkeypatch):
    monkeypatch.setattr(
        ph,
        "predict_with_plifepred2",
        lambda sequence, seq_id="query", model="1": {
            "plifepred2_score": 0.38,
            "confidence_grade": "P4",
            "input_sequence": sequence,
            "warnings": ["rank score fixture"],
        },
    )

    result = ph.predict_halflife_plifepred("AGCKNFFWKTFTSC")

    assert result["rank_score"] == 0.38
    assert result["predicted_hours"] == 0.05
    assert result["conversion_method"] == "calibration_table"
    assert result["absolute_confidence"] == "P3"


def test_plifepred_hour_conversion_unavailable_returns_unavailable(monkeypatch):
    monkeypatch.setattr(
        ph,
        "predict_with_plifepred2",
        lambda sequence, seq_id="query", model="1": {
            "plifepred2_score": 0.77,
            "confidence_grade": "P4",
            "input_sequence": sequence,
            "warnings": [],
        },
    )

    result = ph.predict_halflife_plifepred("AGAKNFFWKTFTSA")

    assert result["rank_score"] == 0.77
    assert result["predicted_hours"] is None
    assert result["conversion_method"] == "unavailable"
    assert result["absolute_confidence"] == "P4"
    assert any("rank" in warning.lower() for warning in result["warnings"])


def test_layer1_uses_plifepred_predicted_hours(monkeypatch):
    monkeypatch.setattr(
        ph,
        "predict_halflife_plifepred",
        lambda sequence: {
            "rank_score": 0.5,
            "predicted_hours": 2.0,
            "conversion_method": "calibration_table",
            "absolute_confidence": "P3",
            "warnings": [],
        },
    )
    monkeypatch.setattr(l1, "_predict_hle_regression", lambda sequence: {"unavailable": True, "reason": "not installed"})
    monkeypatch.setattr(l1, "_predict_pepadmet_hbm", lambda sequence: {"unavailable": True, "reason": "web unavailable"})

    result = l1.compute_layer1_halflife("AGAKNFFWKTFTSA", weights={"plifepred": 1.0})

    assert result["unavailable"] is False
    assert result["tools_used"] == ["plifepred"]
    assert result["ensemble_halflife_hours"] == 2.0
    assert result["individual_predictions"]["plifepred"]["raw"]["raw"]["predicted_hours"] == 2.0


def test_hle_regression_wrapper_callable_unavailable_without_artifact():
    result = ph.predict_halflife_hle_regression("AGAKNFFWKTFTSA")

    assert result["predicted_hours"] is None
    assert result["method"] == "unavailable"
    assert result["unavailable"] is True
    assert result["recommended"] is True
    assert result["absolute_confidence"] == "P4"
    assert any("coefficients" in warning.lower() for warning in result["warnings"])


def test_layer1_uses_hle_regression_predicted_hours(monkeypatch):
    monkeypatch.setattr(l1, "_predict_plifepred", lambda sequence: {"unavailable": True, "reason": "rank only"})
    monkeypatch.setattr(
        ph,
        "predict_halflife_hle_regression",
        lambda sequence: {
            "predicted_hours": 4.5,
            "method": "hle_regression_albumin",
            "absolute_confidence": "P3",
            "warnings": [],
        },
    )
    monkeypatch.setattr(l1, "_predict_pepadmet_hbm", lambda sequence: {"unavailable": True, "reason": "web unavailable"})

    result = l1.compute_layer1_halflife("AGAKNFFWKTFTSA", weights={"hle_regression": 1.0})

    assert result["unavailable"] is False
    assert result["tools_used"] == ["hle_regression"]
    assert result["ensemble_halflife_hours"] == 4.5
    assert result["individual_predictions"]["hle_regression"]["raw"]["raw"]["method"] == "hle_regression_albumin"


def test_hle_regression_rejects_d_aa_input():
    result = ph.predict_halflife_hle_regression("AGcKNFFWKTFTSC")

    assert result["predicted_hours"] is None
    assert result["method"] == "unavailable"
    assert result["recommended"] is False
    assert result["unavailable"] is True
    assert "D-AA" in result["reason"]


def test_d_aa_input_router_rejects_layer1():
    assert route_halflife_prediction("AGcKNFFWKTFTSC") == "layer2_daa_cyclic_pepmsnd"

    result = l1.compute_layer1_halflife("AGcKNFFWKTFTSC")
    assert result["recommended"] is False
    assert result["unavailable"] is True
    assert result["tools_used"] == []


def test_cyclic_input_router_rejects_layer1():
    assert route_halflife_prediction("AGCKNFFWKTFTSC") == "layer2_daa_cyclic_pepmsnd"

    result = l1.compute_layer1_halflife("AGCKNFFWKTFTSC")
    assert result["recommended"] is False
    assert result["unavailable"] is True
