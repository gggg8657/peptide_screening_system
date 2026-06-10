"""
test_stability_predictor_backend.py
=====================================
stability_predictor 백엔드 단위 테스트 (U1 engineer-backend)

U4(reviewer-code)가 작성한 test_stability_predictor.py와 중복 없이
백엔드 구현 특화 테스트를 포함한다.

테스트 목록:
  1. strip_ncaa — NCAA 치환 정확성 (dT/Cha/2Nal/unknown)
  2. _find_protease_sites — trypsin/chymotrypsin/NEP 부위 (SST-14 기준)
  3. _compute_aliphatic_index — Ikai 1980 계수 기반
  4. _fallback_biophysical — Biopython 없이 MW/GRAVY 계산
  5. StabilityResult — to_dict/from_dict 라운드트립
  6. BatchStabilityResult — 라운드트립
  7. compute_stability — fallback 모드 (mock)
  8. compute_stability — NCAA var12_dThr 처리
  9. batch_evaluate — auto seq_ids
  10. batch_evaluate — seq_ids mismatch graceful
  11. to_markdown_table — 헤더 + HEURISTIC disclaimer
  12. pharmacology_guards — Ikai LITERATURE_VALUES 항목 존재
  13. pharmacology_guards — stability_predictor HEURISTIC_FUNCTION_DISCLAIMERS
  14. CANDIDATE_8 — 8 후보 메타데이터 검증
  15. stability router — import 가능성
  16. protease_sites — SST-14 K5/K10/F7,8/W9 취약 부위
  17. _compute_aliphatic_index — 순수 Ala 서열
  18. batch_evaluate — summary 구조
"""

from __future__ import annotations

import asyncio
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline_local.scripts.stability_predictor import (
    CANDIDATE_8,
    BatchStabilityResult,
    StabilityResult,
    _IKAI_ILE,
    _IKAI_LEU,
    _IKAI_VAL,
    _compute_aliphatic_index,
    _fallback_biophysical,
    _find_protease_sites,
    batch_evaluate,
    compute_stability,
    strip_ncaa,
    to_markdown_table,
)
from pipeline_local.scripts.pharmacology_guards import (
    HEURISTIC_FUNCTION_DISCLAIMERS,
    LITERATURE_VALUES,
)

# ---------------------------------------------------------------------------
# 공용 fixture
# ---------------------------------------------------------------------------

def _make_result(seq_id: str = "sst14", sequence: str = "AGCKNFFWKTFTSC") -> StabilityResult:
    # SST-14 실제 1-indexed protease 위치:
    # AGCKNFFWKTFTSC → K@4,K@9 (trypsin), F@6,F@7,W@8,F@11 (chymotrypsin)
    return StabilityResult(
        seq_id=seq_id,
        sequence=sequence,
        canonical_sequence=sequence,
        mw=1617.8,
        gravy=-0.48,
        instability_index=32.5,
        pi=8.2,
        boman=1.2,
        charge_ph74=1.7,
        aliphatic_index=7.1,
        protease_cleavage_sites={"trypsin": [4, 9], "chymotrypsin": [6, 7, 8, 11], "nep": [1, 6]},
        admet_score={"druglikeness_score": 75},
        nephrotox_risk="Low",
        hl_score_heuristic=42.0,
        hl_warnings=["[HEURISTIC] ranking score only"],
        ncaa_warnings=[],
        surrogate_panel={
            "half_life": {"internal_step08": {"score": 42.0}},
            "protease": {"total_sites": 6},
        },
        agreement_profile={
            "consensus_bucket": "mixed",
            "flags": [],
        },
    )


def _mock_patches():
    """Biopython/ADMET/step08 없이 compute_stability 실행을 위한 mock 패치 컨텍스트."""
    return [
        patch("pipeline_local.scripts.stability_predictor._HAS_BIOPYTHON", False),
        patch("pipeline_local.scripts.stability_predictor._HAS_ADMET", False),
        patch("pipeline_local.scripts.stability_predictor._HAS_STEP08", False),
    ]


# ===========================================================================
# 1. strip_ncaa
# ===========================================================================

class TestStripNcaa:
    def test_dThr(self):
        canon, warns = strip_ncaa("AICKNFFWKTFT[dT]C")
        assert "[dT]" not in canon
        assert any("D-Threonine" in w for w in warns)

    def test_Cha(self):
        canon, warns = strip_ncaa("AGC[Cha]NFFWKTFTSC")
        assert "[Cha]" not in canon
        assert any("Cyclohexylalanine" in w for w in warns)

    def test_2Nal(self):
        canon, warns = strip_ncaa("[2Nal]GCKNFFWKTFTSC")
        assert "[2Nal]" not in canon
        assert any("2-Naphthylalanine" in w for w in warns)

    def test_no_ncaa_no_warning(self):
        canon, warns = strip_ncaa("AGCKNFFWKTFTSC")
        assert canon == "AGCKNFFWKTFTSC"
        assert warns == []

    def test_unknown_ncaa_fallback_to_G(self):
        canon, warns = strip_ncaa("AGC[XYZ123]NFFWKTFTSC")
        assert "[" not in canon
        assert any("알 수 없는 NCAA" in w for w in warns)

    def test_multiple_substitutions(self):
        canon, warns = strip_ncaa("[dT][Cha]GCKNFFWKTFTSC")
        assert len(warns) == 2
        assert "[" not in canon


# ===========================================================================
# 2. _find_protease_sites (SST-14 기준)
# ===========================================================================

class TestFindProteaseSites:
    # AGCKNFFWKTFTSC — 1-indexed
    # A=1,G=2,C=3,K=4,N=5,F=6,F=7,W=8,K=9,T=10,F=11,T=12,S=13,C=14
    SEQ = "AGCKNFFWKTFTSC"

    def test_K4_trypsin(self):
        """K는 위치 4 (1-indexed)."""
        sites = _find_protease_sites(self.SEQ)
        assert 4 in sites["trypsin"], f"K@4 미검출: {sites['trypsin']}"

    def test_K9_trypsin(self):
        """두 번째 K는 위치 9."""
        sites = _find_protease_sites(self.SEQ)
        assert 9 in sites["trypsin"], f"K@9 미검출: {sites['trypsin']}"

    def test_KP_not_trypsin(self):
        seq = "AKPNFFWKTFTSC"
        sites = _find_protease_sites(seq)
        assert 2 not in sites["trypsin"]

    def test_F_chymotrypsin(self):
        """F@6, F@7 chymotrypsin 부위."""
        sites = _find_protease_sites(self.SEQ)
        chymo = sites["chymotrypsin"]
        assert any(p in chymo for p in [6, 7])

    def test_W8_chymotrypsin(self):
        """W@8 chymotrypsin 부위."""
        sites = _find_protease_sites(self.SEQ)
        assert 8 in sites["chymotrypsin"]

    def test_nep_nonempty(self):
        sites = _find_protease_sites(self.SEQ)
        assert len(sites["nep"]) > 0

    def test_all_keys_present(self):
        sites = _find_protease_sites(self.SEQ)
        assert set(sites.keys()) == {"trypsin", "chymotrypsin", "nep"}

    def test_empty_on_clean_sequence(self):
        sites = _find_protease_sites("GDESTC")
        assert sites["trypsin"] == []
        assert sites["chymotrypsin"] == []


# ===========================================================================
# 3. _compute_aliphatic_index — Ikai 1980
# ===========================================================================

class TestAliphaticIndex:
    def test_all_ala(self):
        ai = _compute_aliphatic_index("AAAA")
        assert abs(ai - 100.0) < 0.01

    def test_all_val(self):
        ai = _compute_aliphatic_index("VVV")
        expected = _IKAI_VAL * 100.0
        assert abs(ai - expected) < 0.01

    def test_avil_mixed(self):
        ai = _compute_aliphatic_index("AVIL")
        expected = (0.25 + _IKAI_VAL * 0.25 + _IKAI_ILE * 0.25 + _IKAI_LEU * 0.25) * 100
        assert abs(ai - expected) < 0.01

    def test_empty(self):
        assert _compute_aliphatic_index("") == 0.0

    def test_sst14_range(self):
        ai = _compute_aliphatic_index("AGCKNFFWKTFTSC")
        assert 0 < ai < 50

    def test_coefficients_from_literature(self):
        assert _IKAI_VAL == 2.9
        assert _IKAI_ILE == 3.9
        assert _IKAI_LEU == 3.9


# ===========================================================================
# 4. _fallback_biophysical
# ===========================================================================

class TestFallbackBiophysical:
    def test_sst14_mw(self):
        props = _fallback_biophysical("AGCKNFFWKTFTSC")
        assert 1400 < props["mw"] < 1900

    def test_single_A(self):
        props = _fallback_biophysical("A")
        assert 80 < props["mw"] < 100

    def test_instability_nan(self):
        props = _fallback_biophysical("AGCKNFFWKTFTSC")
        assert math.isnan(props["instability_index"])

    def test_gravy_range(self):
        props = _fallback_biophysical("AGCKNFFWKTFTSC")
        assert -5.0 < props["gravy"] < 5.0


# ===========================================================================
# 5. StabilityResult 직렬화
# ===========================================================================

class TestStabilityResultSerialization:
    def test_roundtrip(self):
        r = _make_result()
        r2 = StabilityResult.from_dict(r.to_dict())
        assert r2.seq_id == r.seq_id
        assert abs(r2.mw - r.mw) < 0.01
        assert r2.protease_cleavage_sites == r.protease_cleavage_sites

    def test_json_serializable(self):
        r = _make_result()
        data = json.loads(json.dumps(r.to_dict()))
        assert data["seq_id"] == "sst14"
        assert isinstance(data["protease_cleavage_sites"]["trypsin"], list)
        assert "surrogate_panel" in data
        assert "agreement_profile" in data

    def test_boman_none_ok(self):
        r = _make_result()
        r.boman = None
        d = r.to_dict()
        assert d["boman"] is None
        r2 = StabilityResult.from_dict(d)
        assert r2.boman is None


# ===========================================================================
# 6. BatchStabilityResult 직렬화
# ===========================================================================

class TestBatchStabilityResultSerialization:
    def test_roundtrip(self):
        r = _make_result()
        batch = BatchStabilityResult(results=[r], n_total=1, summary={"mean_mw": 1617.8})
        batch2 = BatchStabilityResult.from_dict(batch.to_dict())
        assert batch2.n_total == 1
        assert batch2.results[0].seq_id == r.seq_id


# ===========================================================================
# 7. compute_stability — fallback 모드
# ===========================================================================

class TestComputeStabilityFallback:
    def test_returns_result(self):
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = compute_stability("AGCKNFFWKTFTSC", seq_id="sst14")
        assert r.seq_id == "sst14"
        assert r.mw > 0

    def test_heuristic_warning_in_result(self):
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = compute_stability("AGCKNFFWKTFTSC")
        assert any("HEURISTIC" in w for w in r.hl_warnings)

    def test_canonical_seq_set(self):
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = compute_stability("AGCKNFFWKTFTSC", seq_id="sst14")
        assert r.canonical_sequence == "AGCKNFFWKTFTSC"

    def test_surrogate_panel_present(self):
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = compute_stability("AGCKNFFWKTFTSC", seq_id="sst14")
        assert "biophysical" in r.surrogate_panel
        assert "protease" in r.surrogate_panel
        assert "half_life" in r.surrogate_panel

    def test_agreement_profile_present(self):
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = compute_stability("AGCKNFFWKTFTSC", seq_id="sst14")
        assert "consensus_bucket" in r.agreement_profile
        assert isinstance(r.agreement_profile.get("flags"), list)


# ===========================================================================
# 8. compute_stability — NCAA var12_dThr
# ===========================================================================

class TestComputeStabilityNcaa:
    def test_original_sequence_preserved(self):
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = compute_stability("AICKNFFWKTFT[dT]C", seq_id="var12")
        assert r.sequence == "AICKNFFWKTFT[dT]C"

    def test_canonical_no_brackets(self):
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = compute_stability("AICKNFFWKTFT[dT]C", seq_id="var12")
        assert "[" not in r.canonical_sequence

    def test_ncaa_warnings_populated(self):
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = compute_stability("AICKNFFWKTFT[dT]C", seq_id="var12")
        assert len(r.ncaa_warnings) > 0


# ===========================================================================
# 9. batch_evaluate — auto seq_ids
# ===========================================================================

class TestBatchEvaluateAutoIds:
    def test_auto_ids(self):
        seqs = ["AGCKNFFWKTFTSC", "AICKNFFWKTFTSC"]
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            result = batch_evaluate(seqs)
        assert result.results[0].seq_id == "seq_0"
        assert result.results[1].seq_id == "seq_1"

    def test_custom_ids(self):
        seqs = ["AGCKNFFWKTFTSC"]
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            result = batch_evaluate(seqs, seq_ids=["SST14_ref"])
        assert result.results[0].seq_id == "SST14_ref"


# ===========================================================================
# 10. batch_evaluate — seq_ids 수 불일치
# ===========================================================================

class TestBatchEvaluateSeqIdsMismatch:
    def test_fewer_ids_no_crash(self):
        seqs = ["AGCKNFFWKTFTSC", "AICKNFFWKTFTSC"]
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            result = batch_evaluate(seqs, seq_ids=["only_one"])
        assert result.n_total == 2


# ===========================================================================
# 11. to_markdown_table
# ===========================================================================

class TestToMarkdownTable:
    def test_headers_present(self):
        table = to_markdown_table([_make_result()])
        assert "seq_id" in table
        assert "MW (Da)" in table

    def test_heuristic_disclaimer(self):
        table = to_markdown_table([_make_result()])
        assert "HEURISTIC" in table or "ranking score" in table.lower()

    def test_multiple_rows(self):
        results = [_make_result(f"s{i}") for i in range(3)]
        table = to_markdown_table(results)
        # 헤더 + 구분선 + 3행 + disclaimer 최소 6줄
        lines = [l for l in table.split("\n") if l.strip()]
        assert len(lines) >= 6


# ===========================================================================
# 12. pharmacology_guards — Ikai LITERATURE_VALUES
# ===========================================================================

class TestPharmacologyGuardsIkai:
    def test_key_exists(self):
        assert "ikai_aliphatic_index" in LITERATURE_VALUES

    def test_val_coefficient(self):
        val, ref, _ = LITERATURE_VALUES["ikai_aliphatic_index"]["Val_coefficient"]
        assert val == 2.9
        assert "Ikai" in ref

    def test_ile_coefficient(self):
        val, *_ = LITERATURE_VALUES["ikai_aliphatic_index"]["Ile_coefficient"]
        assert val == 3.9

    def test_leu_coefficient(self):
        val, *_ = LITERATURE_VALUES["ikai_aliphatic_index"]["Leu_coefficient"]
        assert val == 3.9


# ===========================================================================
# 13. pharmacology_guards — HEURISTIC_FUNCTION_DISCLAIMERS
# ===========================================================================

class TestHeuristicDisclaimers:
    def test_compute_stability_key(self):
        key = "pipeline_local.scripts.stability_predictor.compute_stability"
        assert key in HEURISTIC_FUNCTION_DISCLAIMERS

    def test_batch_evaluate_key(self):
        key = "pipeline_local.scripts.stability_predictor.batch_evaluate"
        assert key in HEURISTIC_FUNCTION_DISCLAIMERS

    def test_confidence_grade_heuristic(self):
        key = "pipeline_local.scripts.stability_predictor.compute_stability"
        assert HEURISTIC_FUNCTION_DISCLAIMERS[key]["confidence_grade"] == "HEURISTIC"

    def test_invalid_use_field(self):
        key = "pipeline_local.scripts.stability_predictor.compute_stability"
        assert "invalid_use" in HEURISTIC_FUNCTION_DISCLAIMERS[key]


# ===========================================================================
# 14. CANDIDATE_8 메타데이터 검증
# ===========================================================================

class TestCandidate8:
    def test_count_is_8(self):
        assert len(CANDIDATE_8) == 8

    def test_sst14_first(self):
        assert CANDIDATE_8[0]["seq_id"] == "SST14_ref"
        assert CANDIDATE_8[0]["sequence"] == "AGCKNFFWKTFTSC"

    def test_cand03_in_list(self):
        ids = [c["seq_id"] for c in CANDIDATE_8]
        assert "cand03" in ids

    def test_var12_has_ncaa(self):
        var12 = next(c for c in CANDIDATE_8 if c["seq_id"] == "var12_dThr")
        assert "[dT]" in var12["sequence"]

    def test_all_have_mods_list(self):
        for c in CANDIDATE_8:
            assert isinstance(c.get("mods"), list)


# ===========================================================================
# 15. stability router import
# ===========================================================================

class TestStabilityRouterImport:
    def test_router_importable(self):
        _ag_path = (
            Path(__file__).resolve().parent.parent.parent
            / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri"
        )
        if _ag_path.exists() and str(_ag_path) not in sys.path:
            sys.path.insert(0, str(_ag_path))
        try:
            from backend.routers.stability import router  # noqa: F401
            assert router is not None
        except ImportError as e:
            pytest.skip(f"backend.routers.stability import 실패: {e}")


class TestStabilityRouterSchema:
    def _load_router_module(self):
        _ag_path = (
            Path(__file__).resolve().parent.parent.parent
            / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri"
        )
        if _ag_path.exists() and str(_ag_path) not in sys.path:
            sys.path.insert(0, str(_ag_path))
        try:
            from backend.routers import stability as stability_router
        except ImportError as e:
            pytest.skip(f"backend.routers.stability import 실패: {e}")
        return stability_router

    def test_predict_schema_matches_batch_result_keys(self):
        stability_router = self._load_router_module()
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            predict_result = asyncio.run(
                stability_router.predict_single("AGCKNFFWKTFTSC")
            )
            batch_result = asyncio.run(
                stability_router.predict_batch(
                    stability_router.BatchRequest(sequences=["AGCKNFFWKTFTSC"])
                )
            )

        assert set(predict_result.keys()) == set(batch_result.results[0].keys())

    def test_predict_exposes_unstable_fields(self):
        stability_router = self._load_router_module()
        unstable_result = _make_result(sequence="ILCKKFFWKTFTSC")
        unstable_result.instability_index = 55.0
        unstable_result.__post_init__()

        with patch.object(
            stability_router,
            "_load_stability_predictor",
            return_value=(lambda seq, seq_id="": unstable_result, None, None, None),
        ):
            predict_result = asyncio.run(
                stability_router.predict_single("ILCKKFFWKTFTSC")
            )

        assert "is_unstable" in predict_result
        assert "stability_class" in predict_result
        assert predict_result["is_unstable"] is True
        assert predict_result["stability_class"] == "unstable"


# ===========================================================================
# 16. protease_sites — SST-14 상세
# ===========================================================================

class TestProteaseSitesSst14:
    # AGCKNFFWKTFTSC — 1-indexed
    # A=1,G=2,C=3,K=4,N=5,F=6,F=7,W=8,K=9,T=10,F=11,T=12,S=13,C=14
    SEQ = "AGCKNFFWKTFTSC"

    def test_K4_present(self):
        """K@4 trypsin 취약 부위."""
        assert 4 in _find_protease_sites(self.SEQ)["trypsin"]

    def test_K9_present(self):
        """K@9 trypsin 취약 부위."""
        assert 9 in _find_protease_sites(self.SEQ)["trypsin"]

    def test_W8_chymotrypsin(self):
        """W@8 chymotrypsin 취약 부위."""
        assert 8 in _find_protease_sites(self.SEQ)["chymotrypsin"]

    def test_positions_1indexed(self):
        """모든 위치가 1-indexed (>0)."""
        sites = _find_protease_sites(self.SEQ)
        for positions in sites.values():
            assert all(p >= 1 for p in positions)


# ===========================================================================
# 17. _compute_aliphatic_index — 순수 Ala
# ===========================================================================

class TestAliphaticIndexPureAla:
    def test_pure_ala_is_100(self):
        ai = _compute_aliphatic_index("A" * 10)
        assert abs(ai - 100.0) < 0.01

    def test_no_aliphatic_residues(self):
        # K, N, E, D 등 aliphatic 아닌 잔기만
        ai = _compute_aliphatic_index("KNEDKNED")
        assert abs(ai) < 1.0  # 거의 0


# ===========================================================================
# 18. batch_evaluate — summary 구조
# ===========================================================================

class TestBatchSummaryStructure:
    def test_summary_has_required_keys(self):
        seqs = ["AGCKNFFWKTFTSC", "AICKNFFWKTFTSC"]
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            result = batch_evaluate(seqs)
        s = result.summary
        assert "n_total" in s
        assert "mean_mw" in s
        assert "heuristic_disclaimer" in s
        assert "surrogate_panel_summary" in s

    def test_heuristic_disclaimer_in_summary(self):
        seqs = ["AGCKNFFWKTFTSC"]
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            result = batch_evaluate(seqs)
        assert "ranking score" in result.summary["heuristic_disclaimer"].lower()

    def test_summary_consensus_counts_present(self):
        seqs = ["AGCKNFFWKTFTSC"]
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            result = batch_evaluate(seqs)
        panel_summary = result.summary["surrogate_panel_summary"]
        assert "consensus_bucket_counts" in panel_summary
        assert isinstance(panel_summary["tools_present"], dict)


# ===========================================================================
# 19. Plugin 패턴 — StabilityCoreEvaluator
# ===========================================================================

class TestStabilityCoreEvaluator:
    """Plugin 패턴 core 평가기 테스트."""

    def test_import_ok(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        assert StabilityCoreEvaluator is not None

    def test_evaluate_returns_stability_core(self):
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, StabilityCore,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            evaluator = StabilityCoreEvaluator()
            core = evaluator.evaluate("AGCKNFFWKTFTSC", seq_id="sst14_test")
        assert isinstance(core, StabilityCore)
        assert core.seq_id == "sst14_test"
        assert core.canonical_sequence == "AGCKNFFWKTFTSC"

    def test_biophysical_props_populated(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate("AGCKNFFWKTFTSC")
        assert core.biophysical.mw > 0
        assert isinstance(core.biophysical.aliphatic_index, float)

    def test_protease_sites_as_object(self):
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, ProteasePredict,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate("AGCKNFFWKTFTSC")
        assert isinstance(core.protease, ProteasePredict)
        assert 4 in core.protease.trypsin   # K@4
        assert 9 in core.protease.trypsin   # K@9

    def test_to_dict_serializable(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate("AGCKNFFWKTFTSC")
        d = core.to_dict()
        json_str = json.dumps(d, default=str)  # NaN → str
        assert "biophysical" in d
        assert "protease" in d

    def test_empty_sequence_raises(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        with pytest.raises(ValueError, match="빈 서열"):
            StabilityCoreEvaluator().evaluate("")

    def test_is_stable_property_false_when_nan(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        import math
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate("AGCKNFFWKTFTSC")
        # fallback mode → instability_index=NaN → is_stable=False
        if math.isnan(core.biophysical.instability_index):
            assert not core.is_stable_biopython


# ===========================================================================
# 20. Plugin 패턴 — SiloBStabilityEvaluator
# ===========================================================================

class TestSiloBStabilityEvaluator:
    """Silo B evaluator (SST-14 SAR) 테스트."""

    def test_import_ok(self):
        from pipeline_local.scripts.stability_predictor import SiloBStabilityEvaluator
        assert SiloBStabilityEvaluator is not None

    def test_evaluate_returns_silo_b_result(self):
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloBStabilityEvaluator, SiloBStabilityResult,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core_eval = StabilityCoreEvaluator()
            evaluator = SiloBStabilityEvaluator(core_eval)
            r = evaluator.evaluate("AICKNFFWKTFTSC", seq_id="cand03")
        assert isinstance(r, SiloBStabilityResult)
        assert r.silo == "B"
        assert r.seq_id == "cand03"

    def test_cand03_mutation_count_one(self):
        """cand03(AICKNFFWKTFTSC)는 SST14(AGCKNFFWKTFTSC) 대비 G→I 1개 변이."""
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloBStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloBStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "AICKNFFWKTFTSC", seq_id="cand03"
            )
        assert r.extras.mutation_count == 1

    def test_cand03_fwkt_conserved(self):
        """cand03는 FWKT pharmacophore (위치 7-10) 보존."""
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloBStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloBStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "AICKNFFWKTFTSC"
            )
        assert r.extras.fwkt_conservation is True
        assert r.extras.fwkt_partial_conservation == 1.0

    def test_sst14_ref_mutation_zero(self):
        """SST14_ref는 자기 자신 대비 0개 변이."""
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloBStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloBStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "AGCKNFFWKTFTSC", seq_id="SST14_ref"
            )
        assert r.extras.mutation_count == 0

    def test_sar_score_range(self):
        """SAR score는 [0, 1] 범위."""
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloBStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloBStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "AGCKNFFWKTFTSC"
            )
        assert 0.0 <= r.extras.sar_consistency_score <= 1.0

    def test_to_dict_has_silo_key(self):
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloBStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloBStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "AGCKNFFWKTFTSC"
            )
        d = r.to_dict()
        assert d["silo"] == "B"
        assert "core" in d
        assert "extras" in d

    def test_fwkt_broken_sequence(self):
        """FWKT 위치 7-10이 모두 다른 서열 → fwkt_conservation=False."""
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloBStabilityEvaluator,
        )
        # AGCKNAAAKTFTSC → pos7=A, pos8=A, pos9=K, pos10=T → F,W 파괴
        broken = "AGCKNAAAKTFTSC"
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloBStabilityEvaluator(StabilityCoreEvaluator()).evaluate(broken)
        assert r.extras.fwkt_conservation is False
        assert r.extras.fwkt_partial_conservation < 1.0


# ===========================================================================
# 21. Plugin 패턴 — SiloAStabilityEvaluator
# ===========================================================================

class TestSiloAStabilityEvaluator:
    """Silo A evaluator (de novo) 테스트."""

    def test_import_ok(self):
        from pipeline_local.scripts.stability_predictor import SiloAStabilityEvaluator
        assert SiloAStabilityEvaluator is not None

    def test_evaluate_returns_silo_a_result(self):
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloAStabilityEvaluator, SiloAStabilityResult,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloAStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "MYVNOVELSEQ", seq_id="novel_01"
            )
        assert isinstance(r, SiloAStabilityResult)
        assert r.silo == "A"

    def test_novelty_with_archives(self):
        """archives 제공 시 backbone_novelty 계산."""
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloAStabilityEvaluator,
        )
        archives = ["AGCKNFFWKTFTSC", "AICKNFFWKTFTSC"]
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloAStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "MYVNOVELSEQ", seq_id="novel_01",
                archive_sequences=archives,
            )
        assert r.extras.backbone_novelty is not None
        assert 0.0 <= r.extras.backbone_novelty <= 1.0

    def test_novelty_none_without_archives(self):
        """archives 없으면 backbone_novelty = None."""
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloAStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloAStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "AGCKNFFWKTFTSC"
            )
        assert r.extras.backbone_novelty is None

    def test_spps_favorable_simple(self):
        """W/P/M 없는 서열 → Favorable."""
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloAStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloAStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "AGCKNFFAKTFTSC"  # W→A 치환
            )
        assert r.extras.de_novo_synthesizability == "Favorable"

    def test_plddt_passed_through(self):
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloAStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            r = SiloAStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                "AGCKNFFWKTFTSC", esmfold_plddt=87.5
            )
        assert r.extras.esmfold_plddt_mean == 87.5


# ===========================================================================
# 22. Plugin 패턴 — combine_silos
# ===========================================================================

class TestCombineSilos:
    """combine_silos 리포트 병합 테스트."""

    def _make_silo_b(self, seq: str, seq_id: str):
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloBStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            return SiloBStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                seq, seq_id=seq_id
            )

    def _make_silo_a(self, seq: str, seq_id: str):
        from pipeline_local.scripts.stability_predictor import (
            StabilityCoreEvaluator, SiloAStabilityEvaluator,
        )
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            return SiloAStabilityEvaluator(StabilityCoreEvaluator()).evaluate(
                seq, seq_id=seq_id
            )

    def test_import_ok(self):
        from pipeline_local.scripts.stability_predictor import combine_silos
        assert combine_silos is not None

    def test_n_total_correct(self):
        from pipeline_local.scripts.stability_predictor import combine_silos
        ra = self._make_silo_a("AGCKNFFWKTFTSC", "a1")
        rb = self._make_silo_b("AICKNFFWKTFTSC", "b1")
        combined = combine_silos([ra], [rb])
        assert combined["n_total"] == 2
        assert combined["n_silo_a"] == 1
        assert combined["n_silo_b"] == 1

    def test_empty_silos_ok(self):
        from pipeline_local.scripts.stability_predictor import combine_silos
        combined = combine_silos([], [])
        assert combined["n_total"] == 0
        assert "heuristic_disclaimer" in combined

    def test_heuristic_disclaimer_present(self):
        from pipeline_local.scripts.stability_predictor import combine_silos
        combined = combine_silos([], [])
        assert "heuristic" in combined["heuristic_disclaimer"].lower()

    def test_all_results_serializable(self):
        from pipeline_local.scripts.stability_predictor import combine_silos
        rb = self._make_silo_b("AGCKNFFWKTFTSC", "sst14")
        combined = combine_silos([], [rb])
        json_str = json.dumps(combined, default=str)
        assert len(json_str) > 0


# ===========================================================================
# 23. Medium fix M-01 — warnings.warn() 병행 (NCAA 치환 시)
# ===========================================================================

class TestMediumFixM01WarningsWarn:
    """M-01: NCAA 치환 시 Python warnings.warn()도 발행되는지 검증."""

    def test_ncaa_triggers_python_warning(self):
        """NCAA 치환 발생 시 UserWarning이 발행되어야 함."""
        import warnings as _w
        from pipeline_local.scripts.stability_predictor import strip_ncaa
        with _w.catch_warnings(record=True) as w_list:
            _w.simplefilter("always")
            strip_ncaa("AICKNFFWKTFT[dT]C")
        user_warns = [x for x in w_list if issubclass(x.category, UserWarning)]
        assert len(user_warns) >= 1, "NCAA 치환 시 UserWarning 발행 없음 (M-01 실패)"

    def test_no_ncaa_no_python_warning(self):
        """NCAA 없으면 UserWarning 없어야 함."""
        import warnings as _w
        from pipeline_local.scripts.stability_predictor import strip_ncaa
        with _w.catch_warnings(record=True) as w_list:
            _w.simplefilter("always")
            strip_ncaa("AGCKNFFWKTFTSC")
        user_warns = [x for x in w_list if issubclass(x.category, UserWarning)]
        assert len(user_warns) == 0, f"NCAA 없는 서열에서 UserWarning 발행됨: {user_warns}"

    def test_unknown_ncaa_triggers_warning(self):
        """알 수 없는 NCAA도 UserWarning 발행."""
        import warnings as _w
        from pipeline_local.scripts.stability_predictor import strip_ncaa
        with _w.catch_warnings(record=True) as w_list:
            _w.simplefilter("always")
            strip_ncaa("AGC[UNKNOWN99]FTSC")
        user_warns = [x for x in w_list if issubclass(x.category, UserWarning)]
        assert any("NCAA" in str(w.message) or "알 수 없는" in str(w.message) for w in user_warns)

    def test_warning_message_contains_ncaa_notation(self):
        """경고 메시지에 NCAA 표기가 포함되어야 함."""
        import warnings as _w
        from pipeline_local.scripts.stability_predictor import strip_ncaa
        with _w.catch_warnings(record=True) as w_list:
            _w.simplefilter("always")
            strip_ncaa("AICKNFFWKTFT[dT]C")
        msgs = [str(w.message) for w in w_list if issubclass(w.category, UserWarning)]
        assert any("[dT]" in m for m in msgs), f"[dT] 표기가 경고에 없음: {msgs}"


# ===========================================================================
# 24. Medium fix M-02 — ncaa_removed_residues in StabilityCore
# ===========================================================================

class TestMediumFixM02NcaaRemovedResidues:
    """M-02: StabilityCore.ncaa_removed_residues 기록 검증."""

    def test_field_exists_in_stability_core(self):
        from pipeline_local.scripts.stability_predictor.core import StabilityCore
        assert "ncaa_removed_residues" in StabilityCore.__dataclass_fields__

    def test_ncaa_removed_recorded_for_dThr(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate(
                "AICKNFFWKTFT[dT]C", seq_id="var12"
            )
        assert len(core.ncaa_removed_residues) >= 1
        # [dT] 표기가 기록에 있어야 함
        original_notations = [notation for _, notation in core.ncaa_removed_residues]
        assert any("[dT]" in n or "dT" in n.lower() for n in original_notations), \
            f"[dT] 기록 없음: {core.ncaa_removed_residues}"

    def test_no_ncaa_empty_removed_list(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate("AGCKNFFWKTFTSC")
        assert core.ncaa_removed_residues == []

    def test_removed_residues_is_list_of_tuples(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate("AICKNFFWKTFT[dT]C")
        for item in core.ncaa_removed_residues:
            assert isinstance(item, tuple), f"tuple 아님: {item!r}"
            assert len(item) == 2
            pos, notation = item
            assert isinstance(pos, int) and pos >= 1
            assert isinstance(notation, str)

    def test_position_1indexed(self):
        """position은 1-indexed (0 불허)."""
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate("[dT]GCKNFFWKTFTSC")
        # [dT]가 첫 번째 위치 → pos=1
        positions = [pos for pos, _ in core.ncaa_removed_residues]
        assert all(p >= 1 for p in positions), f"0-indexed 위치 발견: {positions}"


# ===========================================================================
# 25. Medium fix M-03 — BiophysicalProps.molecular_weight alias
# ===========================================================================

class TestMediumFixM03MolecularWeightAlias:
    """M-03: BiophysicalProps.molecular_weight == BiophysicalProps.mw."""

    def test_molecular_weight_property_exists(self):
        from pipeline_local.scripts.stability_predictor.core import BiophysicalProps
        assert hasattr(BiophysicalProps, "molecular_weight")

    def test_molecular_weight_equals_mw(self):
        from pipeline_local.scripts.stability_predictor.core import BiophysicalProps
        props = BiophysicalProps(
            mw=1617.8, gravy=-0.48, instability_index=32.5, pi=8.2,
            boman=1.2, charge_ph74=1.7, aliphatic_index=35.0,
        )
        assert props.molecular_weight == props.mw
        assert props.molecular_weight == 1617.8

    def test_to_dict_includes_molecular_weight(self):
        from pipeline_local.scripts.stability_predictor.core import BiophysicalProps
        props = BiophysicalProps(
            mw=1617.8, gravy=-0.48, instability_index=32.5, pi=8.2,
            boman=1.2, charge_ph74=1.7, aliphatic_index=35.0,
        )
        d = props.to_dict()
        assert "molecular_weight" in d
        assert d["molecular_weight"] == d["mw"]

    def test_stability_core_to_dict_has_molecular_weight(self):
        from pipeline_local.scripts.stability_predictor import StabilityCoreEvaluator
        with _mock_patches()[0], _mock_patches()[1], _mock_patches()[2]:
            core = StabilityCoreEvaluator().evaluate("AGCKNFFWKTFTSC")
        d = core.to_dict()
        assert "molecular_weight" in d["biophysical"]
        assert d["biophysical"]["molecular_weight"] == d["biophysical"]["mw"]


# ===========================================================================
# 26. Medium fix M-04 — sys.path 변이 함수 스코프 분리
# ===========================================================================

class TestMediumFixM04SysPathFunctionScope:
    """M-04: sys.path 변이가 함수 스코프(_ensure_ag_src_on_path) 내에 있는지 검증."""

    def test_ensure_function_exists_in_init(self):
        import pipeline_local.scripts.stability_predictor as sp
        assert hasattr(sp, "_ensure_ag_src_on_path"), \
            "_ensure_ag_src_on_path 함수가 __init__.py에 없음"
        assert callable(sp._ensure_ag_src_on_path)

    def test_ensure_function_exists_in_core(self):
        from pipeline_local.scripts.stability_predictor import core as core_mod
        assert hasattr(core_mod, "_ensure_ag_src_on_path"), \
            "_ensure_ag_src_on_path 함수가 core.py에 없음"
        assert callable(core_mod._ensure_ag_src_on_path)

    def test_ensure_function_idempotent(self):
        """여러 번 호출해도 sys.path 중복 추가 없음."""
        import pipeline_local.scripts.stability_predictor as sp
        path_before = list(sys.path)
        sp._ensure_ag_src_on_path()
        sp._ensure_ag_src_on_path()
        path_after = list(sys.path)
        # 중복이 없어야 함: 추가된 경로는 최대 1개
        new_entries = [p for p in path_after if p not in path_before]
        assert len(new_entries) <= 1, f"sys.path 중복 추가 발생: {new_entries}"

    def test_ensure_function_returns_path(self):
        import pipeline_local.scripts.stability_predictor as sp
        from pathlib import Path
        result = sp._ensure_ag_src_on_path()
        assert isinstance(result, Path)
