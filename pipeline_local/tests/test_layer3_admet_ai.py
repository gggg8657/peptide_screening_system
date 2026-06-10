from __future__ import annotations

import sys
import types

from pipeline_local.scripts.predict_admet_ai_wrapper import predict_admet_layer3
from pipeline_local.scripts.pharmacology_guards import (
    ENDPOINT_CONFIDENCE,
    HEURISTIC_FUNCTION_DISCLAIMERS,
)


class _FakeADMETModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def predict(self, *, smiles: str):
        assert smiles == "CCO"
        return {"AMES": 0.12, "molecular_weight": 46.069}


def test_layer3_wrapper_forces_extrapolation_warning(monkeypatch):
    fake_module = types.SimpleNamespace(ADMETModel=_FakeADMETModel)
    monkeypatch.setitem(sys.modules, "admet_ai", fake_module)

    result = predict_admet_layer3("CCO", has_dota=False)

    assert result["ok"] is True
    assert result["extrapolation_warning"] is True
    assert result["h06_guard"] is True
    assert result["recommended_for_decision"] is False
    assert result["predictions"] == {"AMES": 0.12, "molecular_weight": 46.069}
    assert result["n_endpoints"] == 2
    assert any("ADMET-AI" in w and "decision" in w for w in result["warnings"])


def test_layer3_wrapper_marks_dota_as_ood(monkeypatch):
    fake_module = types.SimpleNamespace(ADMETModel=_FakeADMETModel)
    monkeypatch.setitem(sys.modules, "admet_ai", fake_module)

    result = predict_admet_layer3("CCO", has_dota=True)

    assert result["extrapolation_warning"] is True
    assert result["recommended_for_decision"] is False
    assert result["has_dota"] is True
    assert any("DOTA" in w and "OOD" in w for w in result["warnings"])


def test_admet_ai_extrapolation_guard_registered():
    endpoint = ENDPOINT_CONFIDENCE["admet_ai_extrapolation"]
    disclaimer = HEURISTIC_FUNCTION_DISCLAIMERS["external_tool.admet_ai"]

    assert endpoint["grade"] == "P4"
    assert endpoint["recommended_for_decision"] is False
    assert endpoint["dota_support"] is False
    assert any("H-06" in w for w in endpoint["warnings"])
    assert disclaimer["confidence_grade"] == "HEURISTIC"
    assert "DOTA" in disclaimer["limitations"]

