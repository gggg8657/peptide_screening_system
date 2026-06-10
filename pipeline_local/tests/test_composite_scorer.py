"""test_composite_scorer.py
==========================
단위 테스트: A-04 복합 스코어링 체계 (Hard Cutoff + WSS + Pareto + Tier).

테스트 목록 (≥10건):
  [TC-01~05] Hard Cutoff 5개 게이트 — 각 게이트 통과/탈락
  [TC-06]    WSS 가중치 합 = 1.0 검증
  [TC-07]    WSS min-max 정규화 — 최솟값/최댓값, [0,1] 범위
  [TC-08]    Tier-S 분류 (후보 < 50, WSS top 20%)
  [TC-09]    Tier-B 분류 (Hard Cutoff 통과, WSS top 20% 미진입)
  [TC-10]    Tier-FAIL 분류 (Hard Cutoff 탈락)
  [TC-11]    Radiolysis — Cys3-Cys14 SS bond 예외 처리 (SST-14 실측값 확인)
  [TC-12]    Radiolysis — ss_bond_intact = False (Cys 없는 위치)
  [TC-13]    score_candidates — Critic Agent 플래그 (통과율 < 5% 경고)
  [TC-14]    compute_wss — 단일 후보 (division by zero 방지)
  [TC-15]    SST14_SSTR2_REF_DDG — pharmacology_guards에서 로드 확인

참고:
  - 기본 테스트 시퀀스 "AGCAAAKAKTAASC": Cys3+Cys14 SS bond, 민감 잔기 0개 → 모든 게이트 통과 가능
  - SST-14 "AGCKNFFWKTFTSC": 민감 잔기 4개(F×3 + W×1, Cys 제외) → Radiolysis 게이트 탈락
  - 3개 민감 잔기 시퀀스 "AGCKAAFWFTAASC": F×2 + W×1 = 3개
"""
from __future__ import annotations

import warnings
from typing import Any, Dict, List

import pytest

from pipeline_local.scoring.composite_scorer import (
    HARD_CUTOFF_ADMET_TOX,
    HARD_CUTOFF_DDG,
    HARD_CUTOFF_INSTABILITY,
    HARD_CUTOFF_RADIOLYSIS_COUNT,
    HARD_CUTOFF_SELECTIVITY,
    SST14_SSTR2_REF_DDG,
    Tier,
    WSS_WEIGHTS,
    apply_hard_cutoffs,
    compute_wss,
    score_candidates,
)
from pipeline_local.scoring.radiolysis_scorer import (
    HARD_CUTOFF_SENSITIVE_COUNT,
    RADIOLYSIS_SENSITIVITY,
    compute_radiolysis_score,
    passes_hard_cutoff,
)


# ---------------------------------------------------------------------------
# 헬퍼: 유효한 기본 후보 dict 생성
# ---------------------------------------------------------------------------
# "AGCAAAKAKTAASC": Cys3(pos3), Cys14(pos14) SS bond, 민감 잔기 0개
_DEFAULT_SAFE_SEQ = "AGCAAAKAKTAASC"

# 민감 잔기 3개 시퀀스: F(pos7), W(pos8), F(pos9) = F×2 + W×1
_SEQ_3_SENSITIVE = "AGCKAAFWFTAASC"

# SST-14 레퍼런스 (민감 잔기 4개: F×3 + W×1, Cys3/Cys14 제외)
_SST14_SEQ = "AGCKNFFWKTFTSC"


def _good_candidate(
    cand_id: str = "cand_ok",
    ddg: float = -100.0,              # SST14 ref -95.024 보다 낮음 (더 강한 결합)
    selectivity_ratio: float = 200.0,  # ≥ 100
    half_life: float = 10.0,
    admet_tox: float = 0.1,            # ≤ 0.3
    instability: float = 30.0,         # < 40
    sequence: str = _DEFAULT_SAFE_SEQ, # 민감 잔기 0개 → Radiolysis Gate 통과
) -> Dict[str, Any]:
    return {
        "id": cand_id,
        "sequence": sequence,
        "ddg": ddg,
        "selectivity_ratio": selectivity_ratio,
        "half_life": half_life,
        "admet_tox": admet_tox,
        "instability": instability,
    }


def _rad(sequence: str, ss_bond_positions: tuple = (3, 14)) -> Dict[str, Any]:
    """Radiolysis 점수 계산 헬퍼."""
    return compute_radiolysis_score(sequence, ss_bond_positions=ss_bond_positions)


# ===========================================================================
# TC-01: Hard Cutoff Gate 1 — ΔG 기준값
# ===========================================================================
class TestHardCutoffGate1_DDG:
    def test_ddg_above_ref_fails(self):
        """ddg > ref_ddg 이면 Gate 1 탈락."""
        cand = _good_candidate(ddg=-90.0)  # -90 > -95.024 → 탈락
        rad = _rad(cand["sequence"])
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert not passed
        assert any("ddg" in f for f in failures), f"실패 목록: {failures}"

    def test_ddg_equal_ref_passes(self):
        """ddg = ref_ddg 이면 통과 (경계값 ≤)."""
        cand = _good_candidate(ddg=SST14_SSTR2_REF_DDG)  # -95.024 REU
        rad = _rad(cand["sequence"])
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert passed, f"경계값 통과 실패: {failures}"

    def test_ddg_below_ref_passes(self):
        """ddg < ref_ddg (더 강한 결합) 이면 통과."""
        cand = _good_candidate(ddg=-120.0)
        rad = _rad(cand["sequence"])
        passed, _ = apply_hard_cutoffs(cand, rad)
        assert passed


# ===========================================================================
# TC-02: Hard Cutoff Gate 2 — 셀렉티비티
# ===========================================================================
class TestHardCutoffGate2_Selectivity:
    def test_selectivity_below_100_fails(self):
        """selectivity_ratio < 100 이면 Gate 2 탈락."""
        cand = _good_candidate(selectivity_ratio=50.0)
        rad = _rad(cand["sequence"])
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert not passed
        assert any("selectivity" in f for f in failures)

    def test_selectivity_exactly_100_passes(self):
        """selectivity_ratio = 100 이면 통과 (경계값 ≥)."""
        cand = _good_candidate(selectivity_ratio=100.0)
        rad = _rad(cand["sequence"])
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert passed, f"경계값 통과 실패: {failures}"


# ===========================================================================
# TC-03: Hard Cutoff Gate 3 — Radiolysis 민감 잔기 수
# ===========================================================================
class TestHardCutoffGate3_Radiolysis:
    def test_radiolysis_count_4_fails(self):
        """민감 잔기 수 > 3 이면 Gate 3 탈락."""
        # SST-14: F×3 + W×1 = 4 sensitive residues (Cys3/Cys14 제외)
        rad = _rad(_SST14_SEQ, ss_bond_positions=(3, 14))
        assert rad["sensitive_count"] == 4  # 실측값 확인

        cand = _good_candidate(sequence=_SST14_SEQ)
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert not passed
        assert any("radiolysis" in f for f in failures)

    def test_radiolysis_count_3_passes(self):
        """민감 잔기 수 = 3 이면 통과 (경계값 ≤)."""
        # AGCKAAFWFTAASC: F(pos7), W(pos8), F(pos9) = 3 sensitive
        rad = _rad(_SEQ_3_SENSITIVE, ss_bond_positions=(3, 14))
        assert rad["sensitive_count"] == 3  # 실측값 확인

        cand = _good_candidate(sequence=_SEQ_3_SENSITIVE)
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert passed, f"count=3 경계값 통과 실패: {failures}"


# ===========================================================================
# TC-04: Hard Cutoff Gate 4 — ADMET 독성
# ===========================================================================
class TestHardCutoffGate4_ADMET:
    def test_admet_above_threshold_fails(self):
        """admet_tox > 0.3 이면 Gate 4 탈락."""
        cand = _good_candidate(admet_tox=0.35)
        rad = _rad(cand["sequence"])
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert not passed
        assert any("admet" in f for f in failures)

    def test_admet_exactly_threshold_passes(self):
        """admet_tox = 0.3 이면 통과 (경계값 ≤)."""
        cand = _good_candidate(admet_tox=0.3)
        rad = _rad(cand["sequence"])
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert passed, f"admet=0.3 경계값 통과 실패: {failures}"


# ===========================================================================
# TC-05: Hard Cutoff Gate 5 — Instability Index
# ===========================================================================
class TestHardCutoffGate5_Instability:
    def test_instability_40_fails(self):
        """instability = 40.0 이면 Gate 5 탈락 (< 40 기준)."""
        cand = _good_candidate(instability=40.0)
        rad = _rad(cand["sequence"])
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert not passed
        assert any("instability" in f for f in failures)

    def test_instability_39_passes(self):
        """instability = 39.9 이면 통과."""
        cand = _good_candidate(instability=39.9)
        rad = _rad(cand["sequence"])
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert passed, f"instability=39.9 통과 실패: {failures}"


# ===========================================================================
# TC-06: WSS 가중치 합 = 1.0
# ===========================================================================
class TestWSSWeights:
    def test_weights_sum_to_one(self):
        """WSS_WEIGHTS 합계가 정확히 1.0 (제약 조건)."""
        total = sum(WSS_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"가중치 합 = {total} ≠ 1.0"

    def test_all_weights_positive(self):
        """모든 가중치는 양수."""
        for k, v in WSS_WEIGHTS.items():
            assert v > 0, f"WSS_WEIGHTS[{k}] = {v} ≤ 0"

    def test_weight_keys_present(self):
        """5개 가중치 키 모두 존재."""
        expected = {"ddg", "selectivity", "half_life", "admet_tox", "radiolysis"}
        assert set(WSS_WEIGHTS.keys()) == expected


# ===========================================================================
# TC-07: WSS min-max 정규화
# ===========================================================================
class TestWSSNormalization:
    def _make_two_candidates(self) -> List[Dict[str, Any]]:
        """최솟값/최댓값이 명확한 두 후보 (민감 잔기 0개 시퀀스 사용)."""
        best  = _good_candidate("best",  ddg=-120.0, selectivity_ratio=500.0,
                                half_life=30.0, admet_tox=0.0, instability=10.0)
        worst = _good_candidate("worst", ddg=-96.0,  selectivity_ratio=110.0,
                                half_life=1.0,  admet_tox=0.29, instability=39.0)
        return [best, worst]

    def test_wss_best_gt_worst(self):
        """최고 후보의 WSS > 최저 후보의 WSS."""
        cands = self._make_two_candidates()
        rads = [_rad(c["sequence"]) for c in cands]
        wss = compute_wss(cands, rads)
        assert len(wss) == 2
        assert wss[0] > wss[1], f"best WSS={wss[0]} ≤ worst WSS={wss[1]}"

    def test_wss_range_0_to_1(self):
        """WSS 값은 [0, 1] 범위 내."""
        cands = self._make_two_candidates()
        rads = [_rad(c["sequence"]) for c in cands]
        wss = compute_wss(cands, rads)
        for v in wss:
            assert 0.0 <= v <= 1.0, f"WSS = {v} out of [0, 1]"

    def test_wss_single_candidate_no_error(self):
        """단일 후보 WSS 계산 — division by zero 없이 0.5 반환."""
        cand = _good_candidate()
        rad = [_rad(cand["sequence"])]
        wss = compute_wss([cand], rad)
        assert len(wss) == 1
        # 단일 후보: min=max → 0.5 반환
        assert wss[0] == pytest.approx(0.5)


# ===========================================================================
# TC-08: Tier-S 분류 (후보 < 50, Pareto 미계산 → WSS top 20%)
# ===========================================================================
class TestTierS:
    def test_tier_s_top_wss_small_pool(self):
        """후보 5개 중 WSS 최상위 후보 → Tier-S (후보 < 50, Pareto 미계산)."""
        cands = [
            _good_candidate("s",   ddg=-120.0, selectivity_ratio=500.0,
                            half_life=30.0, admet_tox=0.0,  instability=10.0),
            _good_candidate("b1",  ddg=-96.0,  selectivity_ratio=110.0,
                            half_life=2.0,  admet_tox=0.25, instability=35.0),
            _good_candidate("b2",  ddg=-97.0,  selectivity_ratio=120.0,
                            half_life=3.0,  admet_tox=0.20, instability=32.0),
            _good_candidate("b3",  ddg=-98.0,  selectivity_ratio=130.0,
                            half_life=4.0,  admet_tox=0.15, instability=28.0),
            _good_candidate("b4",  ddg=-99.0,  selectivity_ratio=140.0,
                            half_life=5.0,  admet_tox=0.10, instability=25.0),
        ]
        results = score_candidates(cands)

        # 5개 모두 Hard Cutoff 통과 확인
        for r in results:
            assert r.passed_hard_cutoff, (
                f"{r.candidate_id} Hard Cutoff 탈락: {r.hard_cutoff_failures}"
            )

        # 후보 < 50 → Pareto 미계산, top 20% (= 1/5 = 최상위 1명) = Tier-S
        tier_s = [r for r in results if r.tier == Tier.S]
        assert len(tier_s) >= 1
        assert tier_s[0].candidate_id == "s", (
            f"Tier-S 후보가 's'가 아님: {[r.candidate_id for r in tier_s]}"
        )


# ===========================================================================
# TC-09: Tier-B 분류 (Hard Cutoff 통과, WSS top 20% 미진입)
# ===========================================================================
class TestTierB:
    def test_tier_b_below_top20(self):
        """WSS 하위 후보는 Tier-B (후보 < 50, Pareto 미계산)."""
        cands = [
            _good_candidate("best", ddg=-120.0, selectivity_ratio=500.0,
                            half_life=30.0, admet_tox=0.0,  instability=10.0),
            _good_candidate("mid",  ddg=-97.0,  selectivity_ratio=110.0,
                            half_life=5.0,  admet_tox=0.25, instability=35.0),
        ]
        results = score_candidates(cands)

        # 2개 모두 Hard Cutoff 통과 확인
        for r in results:
            assert r.passed_hard_cutoff, (
                f"{r.candidate_id} 탈락: {r.hard_cutoff_failures}"
            )

        # top 20%: max(1, int(2*0.2)) = 1 → "best"만 Tier-S
        # "mid"는 Tier-B
        mid_result = next(r for r in results if r.candidate_id == "mid")
        assert mid_result.tier == Tier.B
        assert mid_result.wss is not None
        assert mid_result.passed_hard_cutoff


# ===========================================================================
# TC-10: Tier-FAIL 분류 (Hard Cutoff 탈락)
# ===========================================================================
class TestTierFail:
    def test_tier_fail_on_cutoff_failure(self):
        """Hard Cutoff 탈락 후보 → Tier-FAIL, WSS=None, is_pareto=None."""
        fail_cand = _good_candidate("fail", ddg=-50.0)  # Gate 1 탈락
        ok_cand   = _good_candidate("ok")
        results   = score_candidates([fail_cand, ok_cand])

        fail_result = next(r for r in results if r.candidate_id == "fail")
        ok_result   = next(r for r in results if r.candidate_id == "ok")

        assert fail_result.tier == Tier.FAIL
        assert not fail_result.passed_hard_cutoff
        assert fail_result.wss is None
        assert fail_result.is_pareto is None
        assert len(fail_result.hard_cutoff_failures) >= 1

        assert ok_result.passed_hard_cutoff
        assert ok_result.tier != Tier.FAIL
        assert ok_result.wss is not None

    def test_multiple_gate_failures_all_listed(self):
        """여러 게이트 탈락 시 failures 목록에 모두 기록."""
        cand = _good_candidate(
            "multi_fail",
            ddg=-50.0,            # Gate 1 탈락
            selectivity_ratio=5.0,  # Gate 2 탈락
            admet_tox=0.99,         # Gate 4 탈락
            instability=95.0,       # Gate 5 탈락
        )
        rad = _rad(cand["sequence"])  # count=0 → Gate 3 통과
        passed, failures = apply_hard_cutoffs(cand, rad)
        assert not passed
        # Gate 1, 2, 4, 5 = 4개 탈락 (Gate 3은 통과)
        assert len(failures) == 4


# ===========================================================================
# TC-11: Radiolysis — SS bond 예외 처리 & 실측값 검증
# ===========================================================================
class TestRadiolysisSSBond:
    def test_sst14_actual_sensitive_count_is_4(self):
        """SST-14 AGCKNFFWKTFTSC: Cys3+Cys14 제외 후 민감 잔기 = 4개 (F×3 + W×1)."""
        result = compute_radiolysis_score(_SST14_SEQ, ss_bond_positions=(3, 14))
        assert result["sensitive_count"] == 4
        assert result["details"]["F"] == 3
        assert result["details"]["W"] == 1
        assert result["ss_bond_intact"] is True
        # SS bond Cys는 details에 포함되지 않음
        assert result["details"].get("C", 0) == 0

    def test_ss_bond_intact_false_when_cys_missing(self):
        """SS bond 위치에 Cys가 없으면 ss_bond_intact = False."""
        # AGAKNFFWKTFTSC: pos3 = A (Cys 아님)
        seq = "AGAKNFFWKTFTSC"
        result = compute_radiolysis_score(seq, ss_bond_positions=(3, 14))
        assert result["ss_bond_intact"] is False

    def test_ss_bond_cys_excluded_from_count(self):
        """SS bond 위치 Cys는 sensitive_count에 포함되지 않는다."""
        # "CA": pos1 = C (SS bond 제외), pos2 = A (비민감)
        seq = "CA"
        result = compute_radiolysis_score(seq, ss_bond_positions=(1,))
        assert result["sensitive_count"] == 0
        assert result["ss_bond_intact"] is True

    def test_non_ss_cys_is_counted(self):
        """SS bond 외 위치의 Cys는 민감 잔기로 계산."""
        # "ACK": pos2 = C (SS bond 아님), ss_bond_positions=(1,) → pos1=A
        seq = "ACK"
        result = compute_radiolysis_score(seq, ss_bond_positions=(1,))
        # C at pos2 (idx1) is not in ss_bond_positions → counted (score=3)
        assert result["sensitive_count"] == 1
        assert result["details"]["C"] == 1


# ===========================================================================
# TC-12: Radiolysis 민감도 테이블 검증
# ===========================================================================
class TestRadiolysisTable:
    def test_sensitivity_scores_are_positive_integers(self):
        """모든 민감도 점수는 양의 정수."""
        for aa, score in RADIOLYSIS_SENSITIVITY.items():
            assert isinstance(score, int) and score > 0, (
                f"RADIOLYSIS_SENSITIVITY[{aa}] = {score}"
            )

    def test_high_sensitivity_residues(self):
        """C, M 최고점(3), F/Y/W 2점, P/H/L 1점."""
        assert RADIOLYSIS_SENSITIVITY["C"] == 3
        assert RADIOLYSIS_SENSITIVITY["M"] == 3
        assert RADIOLYSIS_SENSITIVITY["W"] == 2
        assert RADIOLYSIS_SENSITIVITY["F"] == 2
        assert RADIOLYSIS_SENSITIVITY["Y"] == 2
        assert RADIOLYSIS_SENSITIVITY["P"] == 1
        assert RADIOLYSIS_SENSITIVITY["H"] == 1
        assert RADIOLYSIS_SENSITIVITY["L"] == 1

    def test_passes_hard_cutoff_helper(self):
        """passes_hard_cutoff 헬퍼 — count ≤ 3이면 True."""
        assert passes_hard_cutoff({"sensitive_count": 3}) is True
        assert passes_hard_cutoff({"sensitive_count": 4}) is False
        assert passes_hard_cutoff({"sensitive_count": 0}) is True


# ===========================================================================
# TC-13: Critic Agent 플래그 — Hard Cutoff 통과율 < 5% 경고
# ===========================================================================
class TestCriticAgentFlag:
    def test_low_pass_rate_emits_warning(self):
        """Hard Cutoff 통과율 < 5% 시 UserWarning 발생."""
        # 20개 후보 중 0개 통과 → 0% < 5%
        bad_cands = [
            _good_candidate(f"bad_{i}", ddg=-50.0)  # Gate 1 탈락
            for i in range(20)
        ]
        ok_cand = _good_candidate("ok_00")  # 1개 통과 (5% = 경계)
        # 21개 중 1개 통과 = 4.76% < 5%
        all_cands = bad_cands + [ok_cand]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            score_candidates(all_cands)
            cutoff_warnings = [
                x for x in w
                if issubclass(x.category, UserWarning)
                and "통과율" in str(x.message)
            ]
        assert len(cutoff_warnings) >= 1, "통과율 < 5% 경고 미발생"


# ===========================================================================
# TC-14: score_candidates — 입력 순서 보존 + 결과 완전성
# ===========================================================================
class TestScoreCandidatesOrdering:
    def test_result_order_matches_input(self):
        """score_candidates 결과 순서가 입력 순서와 동일."""
        cands = [_good_candidate(f"c{i}") for i in range(5)]
        results = score_candidates(cands)
        assert len(results) == 5
        for i, r in enumerate(results):
            assert r.candidate_id == f"c{i}"

    def test_empty_candidates_raises(self):
        """빈 candidates 목록 → ValueError."""
        with pytest.raises(ValueError):
            score_candidates([])

    def test_all_results_have_tier(self):
        """모든 결과에 Tier가 설정된다."""
        cands = [_good_candidate(f"c{i}") for i in range(3)]
        results = score_candidates(cands)
        for r in results:
            assert isinstance(r.tier, Tier)


# ===========================================================================
# TC-15: ADMET wrapper fallback — 명시적 WARN + 계속 진행
# ===========================================================================
class TestAdmetWrapperFallbackWarning:
    _WARN = "admet_tox_wrapper_failed: fallback value used (REAL_MEASUREMENT_MISSING)"

    def _patch_wrappers(self, monkeypatch):
        def fake_smiles(sequence: str) -> Dict[str, Any]:
            return {"smiles": "NCC(=O)O", "warnings": []}

        def fake_halflife(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            return {"final_confidence_grade": "P4", "halflife_score": 9.0}

        def fake_admet_none(*args: Any, **kwargs: Any) -> None:
            return None

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
            fake_admet_none,
        )

    def test_composite_scorer_warn_on_wrapper_failure(self, monkeypatch, caplog):
        """ADMET wrapper가 None을 반환하면 warnings에 fallback WARN을 남긴다."""
        self._patch_wrappers(monkeypatch)
        caplog.set_level("WARNING", logger="pipeline_local.scripts.composite_scorer")
        result = score_candidates(
            [_good_candidate("fallback_admet", admet_tox=0.1)],
            enrich_from_wrappers=True,
        )[0]

        assert result.fallback_admet_tox is True
        assert any("admet_tox_wrapper_failed" in w for w in result.warnings)
        assert "admet_tox_wrapper_failed" in caplog.text
        assert result.raw["admet_tox"] == pytest.approx(0.1)
        assert result.tier is not Tier.FAIL

    def test_composite_scorer_no_silent_fallback(self, monkeypatch):
        """fallback 사용 시 enrichment_notes에 명시적 WARN 메시지를 남긴다."""
        self._patch_wrappers(monkeypatch)
        result = score_candidates(
            [_good_candidate("fallback_notes", admet_tox=0.1)],
            enrich_from_wrappers=True,
        )[0]

        assert self._WARN in result.raw["enrichment_notes"]
        assert result.raw["fallback_admet_tox"] is True
        assert self._WARN in result.raw["warnings"]


# ===========================================================================
# TC-16: SST14_SSTR2_REF_DDG — pharmacology_guards 로드 확인
# ===========================================================================
class TestRefDDGFromLiteratureValues:
    def test_ref_ddg_exact_value(self):
        """SST14_SSTR2_REF_DDG = -95.024 REU (P0 commit ed86fa0)."""
        from pipeline_local.scripts.pharmacology_guards import LITERATURE_VALUES
        ref_val = LITERATURE_VALUES["SST14_SSTR2_ref_ddg_boltz2"]["ref_ddg_reu"][0]
        assert ref_val == pytest.approx(-95.024)
        assert SST14_SSTR2_REF_DDG == pytest.approx(-95.024)

    def test_hard_cutoff_ddg_equals_ref(self):
        """HARD_CUTOFF_DDG == SST14_SSTR2_REF_DDG."""
        assert HARD_CUTOFF_DDG == pytest.approx(SST14_SSTR2_REF_DDG)
