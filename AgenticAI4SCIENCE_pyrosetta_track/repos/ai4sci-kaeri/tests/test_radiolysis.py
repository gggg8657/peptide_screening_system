"""
Radiolysis Susceptibility 단위 테스트
======================================
대상 모듈:
  - AG_src/pipeline/pharma_properties.py  (PharmaProperties.calculate_radiolysis_susceptibility)
  - backend/pharmacology.py               (radiolysis_susceptibility)

두 구현이 동일한 숫자를 반환해야 한다.
"""

from __future__ import annotations

import math
import sys
import os

# 프로젝트 루트를 sys.path에 추가
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

import pytest

from AG_src.pipeline.pharma_properties import PharmaProperties
from backend.pharmacology import radiolysis_susceptibility

# ─── fixtures ─────────────────────────────────────────────────────────────────

SST14 = "AGCKNFFWKTFTSC"   # native SST-14
PHARMA = PharmaProperties()


# ─── helpers ──────────────────────────────────────────────────────────────────

def _class_result(seq: str) -> dict:
    return PHARMA.calculate_radiolysis_susceptibility(seq)


def _back_result(seq: str) -> dict:
    return radiolysis_susceptibility(seq)


# ─── SST-14 native tests ───────────────────────────────────────────────────────

class TestSST14Native:
    """SST-14 (AGCKNFFWKTFTSC) 기준값 검증."""

    def test_total_score_class(self):
        """SST-14: total_score == 6.5.

        AGCKNFFWKTFTSC 실제 취약 잔기:
          C3(SS bond → 1.0), F6(0.5), F7(0.5), W8(3.0), F11(0.5), C14(SS bond → 1.0)
          합계 = 1.0 + 0.5 + 0.5 + 3.0 + 0.5 + 1.0 = 6.5
        """
        result = _class_result(SST14)
        assert result["total_score"] == pytest.approx(6.5, abs=1e-9)

    def test_total_score_backend(self):
        result = _back_result(SST14)
        assert result["total_score"] == pytest.approx(6.5, abs=1e-9)

    def test_risk_level_high(self):
        """total_score > 6 → high; == 6 → 경계값(moderate 상한 초과로 high)."""
        # 스펙: 6+ = high
        result = _class_result(SST14)
        assert result["risk_level"] == "high"

    def test_risk_level_high_backend(self):
        result = _back_result(SST14)
        assert result["risk_level"] == "high"

    def test_vulnerable_residue_count(self):
        """C3, F6, F7, W8, F11, C14 → 6개 취약 잔기.

        SST-14 서열: A-G-C-K-N-F-F-W-K-T-F-T-S-C
        pos:         1 2 3 4 5 6 7 8 9 10 11 12 13 14
        """
        result = _class_result(SST14)
        positions = [r["position"] for r in result["vulnerable_residues"]]
        assert sorted(positions) == [3, 6, 7, 8, 11, 14]

    def test_cys_ss_bond_weight(self):
        """Cys3 및 Cys14는 SS 결합 → weight 1.0."""
        result = _class_result(SST14)
        cys_entries = [r for r in result["vulnerable_residues"] if r["residue"] == "C"]
        assert len(cys_entries) == 2
        for entry in cys_entries:
            assert entry["weight"] == pytest.approx(1.0, abs=1e-9)

    def test_trp_weight(self):
        """W8: weight 3.0."""
        result = _class_result(SST14)
        trp_entries = [r for r in result["vulnerable_residues"] if r["residue"] == "W"]
        assert len(trp_entries) == 1
        assert trp_entries[0]["weight"] == pytest.approx(3.0, abs=1e-9)

    def test_phe_weight(self):
        """F6, F7, F11: weight 0.5 each (SST-14에는 Phe가 3개)."""
        result = _class_result(SST14)
        phe_entries = [r for r in result["vulnerable_residues"] if r["residue"] == "F"]
        assert len(phe_entries) == 3
        for entry in phe_entries:
            assert entry["weight"] == pytest.approx(0.5, abs=1e-9)

    def test_critical_positions_contain_w8(self):
        """W8은 FWKT 약리단(pos 7-10) 내 → critical_positions에 포함."""
        result = _class_result(SST14)
        crit_positions = [r["position"] for r in result["critical_positions"]]
        assert 8 in crit_positions

    def test_critical_positions_contain_f7(self):
        """F7은 FWKT 약리단(pos 7-10) 내 → critical_positions에 포함."""
        result = _class_result(SST14)
        crit_positions = [r["position"] for r in result["critical_positions"]]
        assert 7 in crit_positions

    def test_f6_not_in_critical(self):
        """F6은 pos 6 → FWKT(7-10) 밖 → critical_positions에 미포함."""
        result = _class_result(SST14)
        crit_positions = [r["position"] for r in result["critical_positions"]]
        assert 6 not in crit_positions

    def test_class_backend_agree(self):
        """두 구현 total_score 일치."""
        cls_res = _class_result(SST14)
        back_res = _back_result(SST14)
        assert cls_res["total_score"] == pytest.approx(back_res["total_score"], abs=1e-9)

    def test_class_backend_risk_agree(self):
        cls_res = _class_result(SST14)
        back_res = _back_result(SST14)
        assert cls_res["risk_level"] == back_res["risk_level"]


# ─── risk level boundary tests ────────────────────────────────────────────────

class TestRiskLevelBoundaries:
    """low/moderate/high 경계값 검증."""

    def test_all_ala_is_low(self):
        """AAAA: 취약 잔기 없음 → total=0, risk=low."""
        result = _class_result("AAAA")
        assert result["total_score"] == pytest.approx(0.0)
        assert result["risk_level"] == "low"

    def test_score_3_is_moderate(self):
        """W 1개만 있는 서열: total=3.0 → 경계(3.0 이하는 low, 초과면 moderate).
        스펙: low (0-3) 즉 ≤3 → low."""
        result = _class_result("AW")
        assert result["total_score"] == pytest.approx(3.0)
        assert result["risk_level"] == "low"

    def test_score_above_3_is_moderate(self):
        """HW: H(2) + W(3) = 5.0 → moderate."""
        result = _class_result("HW")
        assert result["total_score"] == pytest.approx(5.0)
        assert result["risk_level"] == "moderate"

    def test_score_6_is_moderate(self):
        """WW: 3+3=6 → moderate (≤6)."""
        result = _class_result("WW")
        assert result["total_score"] == pytest.approx(6.0)
        assert result["risk_level"] == "moderate"

    def test_score_above_6_is_high(self):
        """WWH: 3+3+2=8 → high."""
        result = _class_result("WWH")
        assert result["total_score"] == pytest.approx(8.0)
        assert result["risk_level"] == "high"


# ─── SS bond Cys protection tests ─────────────────────────────────────────────

class TestCysSSBondProtection:

    def test_single_cys_no_ss(self):
        """Cys가 1개면 SS 파트너 없음 → weight 2.0 (비보호)."""
        result = _class_result("AC")
        cys = [r for r in result["vulnerable_residues"] if r["residue"] == "C"]
        assert cys[0]["weight"] == pytest.approx(2.0)

    def test_two_cys_both_ss(self):
        """Cys 2개 → 모두 SS bond → weight 1.0 each."""
        result = _class_result("ACCA")
        cys = [r for r in result["vulnerable_residues"] if r["residue"] == "C"]
        assert len(cys) == 2
        for c in cys:
            assert c["weight"] == pytest.approx(1.0)

    def test_three_cys_pairs_correctly(self):
        """Cys 3개: 첫-마지막 쌍 → weight 1.0, 가운데 남은 1개 → weight 2.0."""
        result = _class_result("CACACAC")   # C at pos 1, 3, 5, 7 → 4 Cys, all paired
        cys = [r for r in result["vulnerable_residues"] if r["residue"] == "C"]
        weights = sorted(r["weight"] for r in cys)
        # 4 Cys → 2 pairs → all weight 1.0
        assert all(w == pytest.approx(1.0) for w in weights)

    def test_odd_cys_one_unpaired(self):
        """Cys 3개: pos 1,2,3 → pair (1,3), 중간 pos2 미쌍 → weight 2.0."""
        # CCC → lo=0→pos1, hi=2→pos3 pair; lo=1, hi=1 → loop ends (lo not < hi)
        result = _class_result("CCC")
        cys = [r for r in result["vulnerable_residues"] if r["residue"] == "C"]
        weights = sorted(r["weight"] for r in cys)
        # C1 and C3 paired (1.0), C2 unpaired (2.0)
        assert weights == pytest.approx([1.0, 1.0, 2.0])


# ─── edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_empty_sequence_backend(self):
        """빈 서열 → total_score=0, risk=low, 빈 목록."""
        result = _back_result("")
        assert result["total_score"] == pytest.approx(0.0)
        assert result["risk_level"] == "low"
        assert result["vulnerable_residues"] == []
        assert result["critical_positions"] == []

    def test_single_residue_met(self):
        """M 단독: SS 없음, total=3.0, risk=low."""
        result = _class_result("M")
        assert result["total_score"] == pytest.approx(3.0)
        assert result["risk_level"] == "low"

    def test_no_vulnerable_residues(self):
        """GSTK: 취약 잔기 없음."""
        result = _class_result("GSTK")
        assert result["total_score"] == pytest.approx(0.0)
        assert result["vulnerable_residues"] == []
        assert result["critical_positions"] == []

    def test_fwkt_positions_7_to_10_only(self):
        """critical_positions는 오직 7-10 포지션 잔기만 포함."""
        # W at pos 1 (not critical), W at pos 8 (critical)
        seq = "AGCKNFFWKTFTSC"  # W8 is critical
        result = _class_result(seq)
        for r in result["critical_positions"]:
            assert 7 <= r["position"] <= 10

    def test_lowercase_input_class(self):
        """소문자 입력도 처리 가능 (_validate가 upper 처리)."""
        result_upper = _class_result(SST14)
        result_lower = _class_result(SST14.lower())
        assert result_upper["total_score"] == pytest.approx(result_lower["total_score"])

    def test_mechanism_fields_present(self):
        """모든 취약 잔기 항목에 mechanism 필드 존재."""
        result = _class_result(SST14)
        for r in result["vulnerable_residues"]:
            assert "mechanism" in r
            assert isinstance(r["mechanism"], str)
            assert len(r["mechanism"]) > 0

    def test_invalid_aa_raises(self):
        """유효하지 않은 아미노산 코드 → ValueError."""
        with pytest.raises(ValueError):
            _class_result("AGXKNFFWKTFTSC")

    def test_calculate_all_includes_radiolysis(self):
        """calculate_all() 결과에 radiolysis_susceptibility 키 포함."""
        result = PHARMA.calculate_all(SST14)
        assert "radiolysis_susceptibility" in result
        rs = result["radiolysis_susceptibility"]
        assert "total_score" in rs
        assert "risk_level" in rs

    def test_high_risk_sequence(self):
        """Met+Trp+Trp → 3+3+3=9 → high."""
        result = _class_result("MWW")
        assert result["total_score"] == pytest.approx(9.0)
        assert result["risk_level"] == "high"
