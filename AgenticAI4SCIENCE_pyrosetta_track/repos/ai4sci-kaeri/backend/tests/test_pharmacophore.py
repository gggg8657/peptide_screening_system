"""
backend/tests/test_pharmacophore.py
=====================================
pharmacophore.py + status.py candidate enrichment 단위 테스트.

reviewer-pharma 검증 기반 (2026-05-14):
  - FWKT 위치 정본: seq[6:10] == "FWKT" (0-idx 6-9, 1-idx 7-10)
  - chelator_site_available: (N-term OR Lys) AND SS-bond 보존 (≥2 Cys)
  - 두 함수 모두 HEURISTIC 등급

테스트 범위:
  1. compute_fwkt_contact — FWKT motif 존재/결실/strict 모드/None
  2. compute_chelator_site — Condition A+B+C / SS-bond / Pro N-term
  3. compute_pharmacophore_fields — dict 통합 반환
  4. _enrich_candidates — 6 필드 on-the-fly 머지
  5. HEURISTIC_FUNCTION_DISCLAIMERS 등록 확인
  6. SST-14 wild-type 통합 시나리오 (fwkt_contact=True, chelator_site_available=True)
"""
from __future__ import annotations

import unittest
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# 테스트 대상 import
# ---------------------------------------------------------------------------
from backend.pharmacophore import (
    compute_fwkt_contact,
    compute_chelator_site,
    compute_pharmacophore_fields,
    _FWKT_MOTIF,
    _FWKT_0IDX_START,
    _SST14_WT,
    _SST14_SS_CYS_0IDX,
)


# ---------------------------------------------------------------------------
# 1. compute_fwkt_contact 테스트
# ---------------------------------------------------------------------------


class TestComputeFwktContact(unittest.TestCase):
    """compute_fwkt_contact — FWKT motif 존재 여부 판정."""

    def test_sst14_wildtype_returns_true(self) -> None:
        """SST-14 WT(AGCKNFFWKTFTSC)는 FWKT 모티프 포함 → True."""
        candidate = {"sequence": _SST14_WT}
        self.assertTrue(compute_fwkt_contact(candidate))

    def test_fwkt_position_verified(self) -> None:
        """FWKT 위치 정본 확인: seq[6:10] == 'FWKT' (reviewer-pharma 검증)."""
        seq = _SST14_WT
        self.assertEqual(seq[6:10], "FWKT", "FWKT 0-indexed 위치 6-9 확인")
        self.assertEqual(_FWKT_0IDX_START, 6, "_FWKT_0IDX_START = 6 확인")

    def test_lowercase_sequence_normalized(self) -> None:
        """소문자 서열도 대문자로 정규화하여 모티프 검출."""
        candidate = {"sequence": _SST14_WT.lower()}
        self.assertTrue(compute_fwkt_contact(candidate))

    def test_fwkt_motif_present_in_custom_sequence(self) -> None:
        """FWKT 포함된 임의 서열 → True."""
        candidate = {"sequence": "ACFWKTMGCC"}
        self.assertTrue(compute_fwkt_contact(candidate))

    def test_fwkt_mutated_w_to_a_returns_false(self) -> None:
        """W→A 변이로 FWKT 파괴 (FAKT) → False."""
        mutated = _SST14_WT.replace("FWKT", "FAKT")
        candidate = {"sequence": mutated}
        self.assertFalse(compute_fwkt_contact(candidate))

    def test_fwkt_missing_entirely_returns_false(self) -> None:
        """FWKT가 아예 없는 서열 → False."""
        candidate = {"sequence": "ACDEFGHIKLMNPQRSTVWYCC"}
        self.assertFalse(compute_fwkt_contact(candidate))

    def test_empty_sequence_returns_none(self) -> None:
        """빈 sequence → None (판정 불가)."""
        candidate = {"sequence": ""}
        self.assertIsNone(compute_fwkt_contact(candidate))

    def test_no_sequence_key_returns_none(self) -> None:
        """sequence 키 없음 → None."""
        candidate: Dict[str, Any] = {}
        self.assertIsNone(compute_fwkt_contact(candidate))

    def test_sequence_none_returns_none(self) -> None:
        """sequence=None → None."""
        candidate = {"sequence": None}
        self.assertIsNone(compute_fwkt_contact(candidate))

    def test_fwkt_at_end_detected(self) -> None:
        """서열 끝에 위치한 FWKT도 검출 (flexible mode)."""
        candidate = {"sequence": "AGCKNFFWKT"}
        self.assertTrue(compute_fwkt_contact(candidate))

    def test_partial_fwkt_not_detected_default(self) -> None:
        """FWK만 있고 T 없음 → False (기본 FWKT substring 없음)."""
        candidate = {"sequence": "AGCKNFFWKFTSC"}  # FWKF not FWKT
        self.assertFalse(compute_fwkt_contact(candidate))

    def test_strict_position_mode_correct_position(self) -> None:
        """strict_position=True: 정확한 위치(0-idx 6)의 FWKT → True."""
        candidate = {"sequence": _SST14_WT}
        result = compute_fwkt_contact(candidate, strict_position=True, fwkt_start_0idx=6)
        self.assertTrue(result)

    def test_strict_position_mode_wrong_position(self) -> None:
        """strict_position=True: FWKT가 잘못된 위치에 있으면 → False (또는 min_conserved 미달)."""
        # FWKT를 맨 앞에 두고, 원래 위치(6-9)는 다른 잔기
        candidate = {"sequence": "FWKTAGCKNFFTSC"}
        result = compute_fwkt_contact(candidate, strict_position=True, fwkt_start_0idx=6)
        # 위치 6-9 = "KNFF" (not FWKT) → < 3 보존 → False
        self.assertFalse(result)

    def test_strict_position_partial_conservation(self) -> None:
        """strict_position=True: ≥3개 잔기 보존 시 True."""
        # SST-14 with T10→A mutation: 0-idx 6-9 = "FWKA" → F,W,K 보존(3/4) → True
        mutated = list(_SST14_WT)
        mutated[9] = "A"  # T(0-idx 9) → A
        candidate = {"sequence": "".join(mutated)}
        result = compute_fwkt_contact(candidate, strict_position=True, fwkt_start_0idx=6)
        self.assertTrue(result)  # 3/4 보존

    def test_strict_position_too_short(self) -> None:
        """strict_position=True: 서열이 너무 짧으면 → False."""
        candidate = {"sequence": "AGCFWK"}  # len < fwkt_start(6)+4=10
        result = compute_fwkt_contact(candidate, strict_position=True, fwkt_start_0idx=6)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# 2. compute_chelator_site 테스트 (Condition A+B+C)
# ---------------------------------------------------------------------------


class TestComputeChelatorSite(unittest.TestCase):
    """compute_chelator_site — reviewer-pharma Condition A+B+C."""

    # ── SST-14 기준 테스트 ────────────────────────────────────────────────

    def test_sst14_wildtype_returns_true(self) -> None:
        """SST-14 WT: N-term=A(non-Pro)+K4,K8+2Cys → True."""
        self.assertTrue(compute_chelator_site(_SST14_WT))

    def test_lowercase_normalized(self) -> None:
        """소문자 서열도 정규화하여 처리."""
        self.assertTrue(compute_chelator_site(_SST14_WT.lower()))

    # ── Condition A: N-term primary amine ───────────────────────────────

    def test_non_pro_n_term_with_two_cys_returns_true(self) -> None:
        """Condition A+C: non-Pro N-term + 2 Cys → True."""
        self.assertTrue(compute_chelator_site("AGCNFFWKTFSC"))  # 2 Cys

    def test_ala_n_term_with_two_cys(self) -> None:
        """Ala N-term (primary amine) + 2 Cys → True."""
        self.assertTrue(compute_chelator_site("ACGNFFWKTFSC"))  # A+2Cys

    # ── Condition B: Lys ε-NH2 ──────────────────────────────────────────

    def test_lys_n_term_with_two_cys_returns_true(self) -> None:
        """Condition B+C: Lys N-term + 2 Cys → True (B AND C)."""
        self.assertTrue(compute_chelator_site("KCNFFWKTFSC"))  # K+2Cys

    def test_pro_n_term_with_lys_and_two_cys_returns_true(self) -> None:
        """Condition B+C: Pro N-term(A=False) + K + 2 Cys → True."""
        self.assertTrue(compute_chelator_site("PAKCNFFWSC"))  # Pro+K+2Cys

    def test_pro_n_term_without_lys_with_two_cys_returns_false(self) -> None:
        """A=False, B=False (no Lys) → False (even with 2 Cys)."""
        self.assertFalse(compute_chelator_site("PAGCNSC"))  # Pro+2Cys, no K

    # ── Condition C: SS-bond 보존 ────────────────────────────────────────

    def test_no_cys_returns_false(self) -> None:
        """Condition C: Cys 없음 → SS-bond 불가 → False."""
        self.assertFalse(compute_chelator_site("AGKNFFWKTFSA"))  # no Cys

    def test_one_cys_returns_false(self) -> None:
        """Condition C: Cys 1개 → SS-bond 불가 → False."""
        self.assertFalse(compute_chelator_site("AGCKNFFWKTFSA"))  # 1 Cys only

    def test_two_cys_ss_bond_maintained(self) -> None:
        """Condition C: Cys ≥2 → SS-bond 가능 → C=True."""
        self.assertTrue(compute_chelator_site("ACGNFFWKTFSC"))  # 2 Cys

    def test_three_cys_still_passes(self) -> None:
        """Cys 3개도 SS-bond 가능 조건 충족 → True (A+C 만족)."""
        self.assertTrue(compute_chelator_site("ACGCNFFWKTFSC"))  # 3 Cys + A N-term

    def test_all_pro_sequence_returns_false(self) -> None:
        """PPP...: A=False(Pro), B=False(no K), C=False(no Cys) → False."""
        self.assertFalse(compute_chelator_site("PPPPP"))

    # ── Edge cases ───────────────────────────────────────────────────────

    def test_empty_string_returns_none(self) -> None:
        """빈 서열 → None."""
        self.assertIsNone(compute_chelator_site(""))

    def test_whitespace_only_returns_none(self) -> None:
        """공백만 있는 서열 → None."""
        self.assertIsNone(compute_chelator_site("   "))

    def test_ss_cys_0idx_parameter(self) -> None:
        """ss_cys_0idx 커스텀 파라미터: 기본값 (2,13)으로 SST-14 검증."""
        result = compute_chelator_site(_SST14_WT, ss_cys_0idx=_SST14_SS_CYS_0IDX)
        self.assertTrue(result)


# ---------------------------------------------------------------------------
# 3. compute_pharmacophore_fields 통합 반환 테스트
# ---------------------------------------------------------------------------


class TestComputePharmacophoreFields(unittest.TestCase):
    """compute_pharmacophore_fields — dict 통합 반환."""

    def test_sst14_wildtype_both_true(self) -> None:
        """SST-14 WT → 두 필드 모두 True."""
        result = compute_pharmacophore_fields({"sequence": _SST14_WT})
        self.assertIn("fwkt_contact", result)
        self.assertIn("chelator_site_available", result)
        self.assertTrue(result["fwkt_contact"])
        self.assertTrue(result["chelator_site_available"])

    def test_keys_present_even_for_empty_sequence(self) -> None:
        """빈 서열도 두 키 반환 (값은 None)."""
        result = compute_pharmacophore_fields({"sequence": ""})
        self.assertIn("fwkt_contact", result)
        self.assertIn("chelator_site_available", result)
        self.assertIsNone(result["fwkt_contact"])
        self.assertIsNone(result["chelator_site_available"])

    def test_no_sequence_key(self) -> None:
        """sequence 키 없는 candidate → 두 값 모두 None."""
        result = compute_pharmacophore_fields({})
        self.assertIsNone(result["fwkt_contact"])
        self.assertIsNone(result["chelator_site_available"])

    def test_fwkt_mutated_chelator_valid(self) -> None:
        """FWKT 변이 + SS-bond 보존 → fwkt=False, chelator=True."""
        mutated = _SST14_WT.replace("FWKT", "FAKT")
        result = compute_pharmacophore_fields({"sequence": mutated})
        self.assertFalse(result["fwkt_contact"])
        self.assertTrue(result["chelator_site_available"])  # 2 Cys 보존


# ---------------------------------------------------------------------------
# 4. _enrich_candidates 테스트 (status.py에서 import)
# ---------------------------------------------------------------------------


class TestEnrichCandidates(unittest.TestCase):
    """status._enrich_candidates — 6-field on-the-fly 머지."""

    def _enrich(self, candidates):
        from backend.routers.status import _enrich_candidates
        return _enrich_candidates(candidates)

    def test_empty_list_returns_empty(self) -> None:
        """빈 candidates → 빈 리스트 반환."""
        result = self._enrich([])
        self.assertEqual(result, [])

    def test_sst14_wildtype_candidate_gets_6_fields(self) -> None:
        """SST-14 WT candidate → 6 필드 모두 채워짐."""
        candidates = [{"id": "cand001", "sequence": _SST14_WT, "ddG": -12.0}]
        result = self._enrich(candidates)
        self.assertEqual(len(result), 1)
        c = result[0]

        # ① instability_index: float 기대
        self.assertIsNotNone(c.get("instability_index"), "instability_index가 None임")
        self.assertIsInstance(c["instability_index"], float)

        # ② gravy: float 기대
        self.assertIsNotNone(c.get("gravy"), "gravy가 None임")
        self.assertIsInstance(c["gravy"], float)

        # ③ net_charge_ph74: float/int 기대
        self.assertIsNotNone(c.get("net_charge_ph74"), "net_charge_ph74가 None임")

        # ⑤ fwkt_contact: True 기대 (SST-14 WT에는 FWKT at 0-idx 6-9)
        self.assertIs(c.get("fwkt_contact"), True, "SST-14 WT의 fwkt_contact가 True가 아님")

        # ⑥ chelator_site_available: True 기대 (N-term=A, 2Cys, K4,K8)
        self.assertIs(c.get("chelator_site_available"), True,
                      "SST-14 WT의 chelator_site_available이 True가 아님")

    def test_existing_values_not_overwritten(self) -> None:
        """이미 값이 있는 필드는 덮어쓰지 않음."""
        candidates = [{
            "id": "cand002",
            "sequence": _SST14_WT,
            "ddG": -10.0,
            "instability_index": 99.9,   # 이미 있는 값
            "gravy": -5.0,               # 이미 있는 값
            "net_charge_ph74": 3.0,      # 이미 있는 값
            "fwkt_contact": False,       # 이미 있는 값 (False여도 유지)
            "chelator_site_available": False,  # 이미 있는 값
        }]
        result = self._enrich(candidates)
        c = result[0]
        self.assertEqual(c["instability_index"], 99.9)
        self.assertEqual(c["gravy"], -5.0)
        self.assertEqual(c["net_charge_ph74"], 3.0)
        self.assertIs(c["fwkt_contact"], False)
        self.assertIs(c["chelator_site_available"], False)

    def test_original_candidate_not_mutated(self) -> None:
        """원본 candidate dict가 변경되지 않아야 한다 (shallow copy)."""
        original = {"id": "cand003", "sequence": _SST14_WT, "ddG": -8.0}
        original_copy = dict(original)
        self._enrich([original])
        self.assertEqual(original, original_copy)

    def test_no_sequence_skips_computation(self) -> None:
        """sequence 없는 candidate → 계산 생략, dict 그대로 반환."""
        candidates = [{"id": "cand004", "ddG": -5.0}]
        result = self._enrich(candidates)
        c = result[0]
        self.assertIsNone(c.get("fwkt_contact"))
        self.assertIsNone(c.get("chelator_site_available"))

    def test_fwkt_mutated_candidate(self) -> None:
        """FWKT 변이 후보: fwkt_contact=False (2Cys 보존으로 chelator=True)."""
        mutated_seq = _SST14_WT.replace("FWKT", "FAKT")
        candidates = [{"id": "cand005", "sequence": mutated_seq, "ddG": -7.0}]
        result = self._enrich(candidates)
        self.assertIs(result[0]["fwkt_contact"], False)
        self.assertIs(result[0]["chelator_site_available"], True)  # 2 Cys 보존

    def test_multiple_candidates_all_enriched(self) -> None:
        """여러 candidate 모두 enrichment 적용."""
        candidates = [
            {"id": f"cand{i:03d}", "sequence": _SST14_WT, "ddG": -float(i)}
            for i in range(1, 6)
        ]
        result = self._enrich(candidates)
        self.assertEqual(len(result), 5)
        for c in result:
            self.assertIsNotNone(c.get("fwkt_contact"))
            self.assertIsNotNone(c.get("chelator_site_available"))

    def test_no_cys_candidate_chelator_false(self) -> None:
        """Cys 없는 후보: chelator_site_available=False (SS-bond 불가)."""
        no_cys_seq = "AGKNFFWKTFSA"  # no Cys
        candidates = [{"id": "cand006", "sequence": no_cys_seq, "ddG": -6.0}]
        result = self._enrich(candidates)
        self.assertIs(result[0]["chelator_site_available"], False)


# ---------------------------------------------------------------------------
# 5. HEURISTIC_FUNCTION_DISCLAIMERS 등록 확인
# ---------------------------------------------------------------------------


class TestPharmacologyGuardsRegistration(unittest.TestCase):
    """pharmacology_guards에 fwkt/chelator 항목이 등록되었는지 확인."""

    def test_fwkt_contact_registered(self) -> None:
        from pipeline_local.scripts.pharmacology_guards import HEURISTIC_FUNCTION_DISCLAIMERS
        self.assertIn(
            "backend.pharmacophore.compute_fwkt_contact",
            HEURISTIC_FUNCTION_DISCLAIMERS,
        )

    def test_chelator_site_registered(self) -> None:
        from pipeline_local.scripts.pharmacology_guards import HEURISTIC_FUNCTION_DISCLAIMERS
        self.assertIn(
            "backend.pharmacophore.compute_chelator_site",
            HEURISTIC_FUNCTION_DISCLAIMERS,
        )

    def test_heuristic_entries_have_required_keys(self) -> None:
        from pipeline_local.scripts.pharmacology_guards import HEURISTIC_FUNCTION_DISCLAIMERS
        required_keys = {
            "surface_unit", "actual_meaning", "limitations",
            "valid_use", "invalid_use", "confidence_grade", "fix_status"
        }
        for fn_name in [
            "backend.pharmacophore.compute_fwkt_contact",
            "backend.pharmacophore.compute_chelator_site",
        ]:
            entry = HEURISTIC_FUNCTION_DISCLAIMERS.get(fn_name, {})
            missing = required_keys - set(entry.keys())
            self.assertEqual(missing, set(), f"{fn_name} 누락 키: {missing}")

    def test_confidence_grade_is_heuristic(self) -> None:
        from pipeline_local.scripts.pharmacology_guards import HEURISTIC_FUNCTION_DISCLAIMERS
        for fn_name in [
            "backend.pharmacophore.compute_fwkt_contact",
            "backend.pharmacophore.compute_chelator_site",
        ]:
            grade = HEURISTIC_FUNCTION_DISCLAIMERS.get(fn_name, {}).get("confidence_grade")
            self.assertEqual(grade, "HEURISTIC", f"{fn_name} grade != HEURISTIC: {grade}")


# ---------------------------------------------------------------------------
# 6. 통합 시나리오 — 약리학적 일관성 확인
# ---------------------------------------------------------------------------


class TestPharmacologicalConsistency(unittest.TestCase):
    """reviewer-pharma 정의의 약리학적 일관성 테스트."""

    def test_fwkt_0idx_constant_matches_sst14(self) -> None:
        """_FWKT_0IDX_START=6이 SST-14에서 'FWKT' 시작 위치임을 확인."""
        self.assertEqual(_SST14_WT[_FWKT_0IDX_START:_FWKT_0IDX_START + 4], _FWKT_MOTIF)

    def test_sst14_ss_cys_positions(self) -> None:
        """_SST14_SS_CYS_0IDX = (2, 13) — C3(0-idx 2), C14(0-idx 13) 확인."""
        c_idx1, c_idx2 = _SST14_SS_CYS_0IDX
        self.assertEqual(_SST14_WT[c_idx1], "C", f"0-idx {c_idx1} should be C")
        self.assertEqual(_SST14_WT[c_idx2], "C", f"0-idx {c_idx2} should be C")

    def test_dotatate_analogue_fwkt_plus_chelator(self) -> None:
        """DOTATATE 타입 analogue: FWKT 보존 + chelation 가능."""
        # Octreotide-like: FWKT 보존 + N-term + 2 Cys
        analogue = "ACFWKTFSC"  # short SST-14 like, 2 Cys
        self.assertTrue(compute_fwkt_contact({"sequence": analogue}))
        self.assertTrue(compute_chelator_site(analogue))

    def test_non_sstr2_peptide_no_fwkt(self) -> None:
        """비SSTR2 펩타이드: FWKT 없음 → fwkt_contact=False."""
        non_sstr2 = "DYKDDDDKCC"  # FLAG-tag like + 2 Cys
        self.assertFalse(compute_fwkt_contact({"sequence": non_sstr2}))
        self.assertTrue(compute_chelator_site(non_sstr2))  # chelation은 가능

    def test_cluster_a_criteria_consistency(self) -> None:
        """Cluster A 후보는 FWKT 접촉 유지되어야 함 (SST-14 WT)."""
        # SST-14 WT는 클러스터 A 기대값 = fwkt_contact True
        result = compute_pharmacophore_fields({"sequence": _SST14_WT})
        self.assertTrue(result["fwkt_contact"],
                        "Cluster A 후보의 fwkt_contact는 True여야 함")

    def test_ss_bond_required_for_chelator(self) -> None:
        """SS-bond 없는 선형 펩타이드: chelator_site는 False (SSTR2 context)."""
        # SS-bond 없으면 SSTR2 conformational 요구 미충족 → False
        linear_no_ss = "AGKNFFWKTFSA"  # no Cys, good N-term and Lys
        self.assertFalse(compute_chelator_site(linear_no_ss))


if __name__ == "__main__":
    unittest.main()
