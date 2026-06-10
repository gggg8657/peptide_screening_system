from __future__ import annotations

from typing import Any, Dict, List

from pipeline_local.scripts import composite_scorer as scorer_mod
from pipeline_local.scripts.composite_scorer import (
    CompositeScorer,
    contains_d_amino_acid,
    enrich_candidates_from_wrappers,
)


def _candidate(sequence: str = "AGCAAAKAKTAASC") -> Dict[str, Any]:
    return {
        "candidate_id": "PRST-T",
        "sequence": sequence,
        "dg": -110.0,
        "selectivity": 250.0,
        "half_life": 9.9,
        "admet_tox": 0.25,
        "radiolysis_count": 0,
        "instability_index": 25.0,
    }


def test_default_score_preserves_mock_inputs(monkeypatch):
    def fail_halflife(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        raise AssertionError("halflife wrapper should not be called")

    monkeypatch.setattr(
        "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife",
        fail_halflife,
    )

    df = CompositeScorer().score([_candidate()])

    assert df.loc[0, "half_life"] == 9.9
    assert df.loc[0, "admet_tox"] == 0.25
    assert df.loc[0, "enrichment_status"] == ""


def test_enrich_from_wrappers_updates_scores(monkeypatch):
    calls: List[str] = []

    def fake_smiles(sequence: str) -> Dict[str, Any]:
        calls.append("smiles")
        return {"smiles": "NCC(=O)O", "warnings": []}

    def fake_halflife(
        sequence: str,
        seq_id: str = "query",
        use_plifepred2: bool = True,
        use_pepmsnd_web: bool = False,
    ) -> Dict[str, Any]:
        calls.append("halflife")
        return {
            "final_confidence_grade": "P4",
            "plifepred2": {"plifepred2_score": 0.77},
        }

    def fake_admet(
        sequence: str,
        seq_id: str = "query",
        use_modlamp_fallback: bool = True,
        check_pepadmet_web: bool = False,
    ) -> Dict[str, Any]:
        calls.append("admet")
        return {"final_confidence_grade": "P2", "admet_tox": 0.11}

    monkeypatch.setattr(
        "pipeline_local.scripts.sequence_to_smiles.sequence_to_linear_smiles",
        fake_smiles,
    )
    monkeypatch.setattr(
        "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife",
        fake_halflife,
    )
    monkeypatch.setattr(
        "pipeline_local.scripts.predict_admet_pepadmet.predict_admet",
        fake_admet,
    )

    df = CompositeScorer().score([_candidate()], enrich_from_wrappers=True)

    assert calls == ["smiles", "halflife", "admet"]
    assert df.loc[0, "half_life"] == 0.77
    assert df.loc[0, "admet_tox"] == 0.11
    assert df.loc[0, "halflife_confidence_grade"] == "P4"
    assert df.loc[0, "admet_confidence_grade"] == "P2"
    assert df.loc[0, "enrichment_status"] == "ENRICHED"
    assert df.loc[0, "smiles"] == "NCC(=O)O"


def test_d_aa_guard_skips_wrappers(monkeypatch):
    def fail(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        raise AssertionError("wrapper should not be called for D-AA sequences")

    monkeypatch.setattr(
        "pipeline_local.scripts.sequence_to_smiles.sequence_to_linear_smiles",
        fail,
    )
    monkeypatch.setattr(
        "pipeline_local.scripts.predict_halflife_pepmsnd.predict_halflife",
        fail,
    )
    monkeypatch.setattr(
        "pipeline_local.scripts.predict_admet_pepadmet.predict_admet",
        fail,
    )

    enriched = enrich_candidates_from_wrappers([_candidate("AGcAAAKAKTAASC")])

    assert enriched[0]["half_life"] == 9.9
    assert enriched[0]["admet_tox"] == 0.25
    assert enriched[0]["halflife_confidence_grade"] == "UNAVAILABLE"
    assert enriched[0]["admet_confidence_grade"] == "UNAVAILABLE"
    assert enriched[0]["enrichment_status"] == "UNAVAILABLE"


def test_d_aa_detection_covers_lowercase_and_d_dash():
    assert contains_d_amino_acid("AGcAA")
    assert contains_d_amino_acid("D-Phe-AGCAA")
    assert not contains_d_amino_acid("AGCAAA")


def test_scoring_module_exposes_same_enrichment(monkeypatch):
    def fake_enrich(candidates: List[Dict[str, Any]], **kwargs: Any) -> List[Dict[str, Any]]:
        updated = [dict(c) for c in candidates]
        updated[0]["half_life"] = 0.42
        updated[0]["halflife_confidence_grade"] = "P4"
        return updated

    monkeypatch.setattr(scorer_mod, "enrich_candidates_from_wrappers", fake_enrich)

    from pipeline_local.scoring.composite_scorer import score_candidates

    result = score_candidates(
        [
            {
                "id": "x",
                "sequence": "AGCAAAKAKTAASC",
                "ddg": -110.0,
                "selectivity_ratio": 200.0,
                "half_life": 1.0,
                "admet_tox": 0.1,
                "instability": 20.0,
            }
        ],
        enrich_from_wrappers=True,
    )[0]

    assert result.raw["half_life"] == 0.42
    assert result.raw["halflife_confidence_grade"] == "P4"
