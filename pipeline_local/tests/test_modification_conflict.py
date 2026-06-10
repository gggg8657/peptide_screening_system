"""test_modification_conflict.py
================================
modification_conflict.py 단위 테스트.

Base 서열: SST-14 = "AGCKNFFWKTFTSC" (14aa, Cys3-Cys14 SS bond)
  Position (1-indexed): A1 G2 C3 K4 N5 F6 F7 W8 K9 T10 F11 T12 S13 C14

각 규칙(C-01 ~ C-06, C-08 ~ C-10)에 대해 정상/이상 케이스 + 통합 케이스로 구성.
Phase 5 추가: A-2 누락 테스트 4건, A-7 C-08~C-10 테스트 8건.
"""
from __future__ import annotations

from pipeline_local.scripts.modification_conflict import (
    Conflict,
    check_conflicts,
    _find_cys_pairs,
)

# ---------------------------------------------------------------------------
# 공통 상수
# ---------------------------------------------------------------------------

SST14 = "AGCKNFFWKTFTSC"
# 위치 참고:
#   K4 (position 4), K9 (position 9)
#   C3 (position 3), C14 (position 14)
#   G2 (position 2)
#   W8 (position 8) — Trp, not Lys


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _rule_ids(conflicts: list[Conflict]) -> list[str]:
    return [c.rule_id for c in conflicts]


def _severities(conflicts: list[Conflict]) -> list[str]:
    return [c.severity for c in conflicts]


# ---------------------------------------------------------------------------
# C-01: 동일 position에 fatty_acid + pegylation
# ---------------------------------------------------------------------------

class TestC01SamePositionFattyPeg:
    """C-01: Lys ε-NH2 단일 부위 — fatty_acid + pegylation 동시 불가."""

    def test_c01_triggers_on_same_position(self) -> None:
        """K4에 fatty_acid + pegylation 동시 지정 → ERROR 1개."""
        mods = [
            {"mod_type": "fatty_acid",  "position": 4},
            {"mod_type": "pegylation",  "position": 4},
        ]
        conflicts = check_conflicts(SST14, mods)
        assert len(conflicts) == 1
        assert conflicts[0].rule_id == "C-01"
        assert conflicts[0].severity == "ERROR"
        # 두 modification 인덱스(0, 1)가 모두 포함되어야 함
        assert set(conflicts[0].mods_involved) == {0, 1}

    def test_c01_no_conflict_different_positions(self) -> None:
        """K4에 fatty_acid, K9에 pegylation → C-01 없음."""
        mods = [
            {"mod_type": "fatty_acid", "position": 4},
            {"mod_type": "pegylation", "position": 9},
        ]
        conflicts = check_conflicts(SST14, mods)
        c01 = [c for c in conflicts if c.rule_id == "C-01"]
        assert len(c01) == 0

    def test_c01_mods_involved_indices_correct(self) -> None:
        """C-01 충돌 시 mods_involved가 정확한 0-based 인덱스를 가리킴."""
        mods = [
            {"mod_type": "d_amino_acid", "position": 6},   # index 0 — 무관
            {"mod_type": "fatty_acid",   "position": 4},   # index 1
            {"mod_type": "pegylation",   "position": 4},   # index 2
        ]
        conflicts = check_conflicts(SST14, mods)
        c01 = [c for c in conflicts if c.rule_id == "C-01"]
        assert len(c01) == 1
        assert set(c01[0].mods_involved) == {1, 2}


# ---------------------------------------------------------------------------
# C-02: fatty_acid를 Lys 아닌 비-N-terminal 위치에 적용
# ---------------------------------------------------------------------------

class TestC02FattyAcidNonLys:
    """C-02: 지방산 아실화 부위 선택성 — Lys/N-terminal 외 ERROR."""

    def test_c02_triggers_on_trp_position(self) -> None:
        """W8(Trp, Lys 아님)에 fatty_acid → ERROR 1개."""
        mods = [{"mod_type": "fatty_acid", "position": 8}]
        conflicts = check_conflicts(SST14, mods)
        c02 = [c for c in conflicts if c.rule_id == "C-02"]
        assert len(c02) == 1
        assert c02[0].severity == "ERROR"

    def test_c02_no_conflict_on_lys(self) -> None:
        """K4(Lys)에 fatty_acid → C-02 없음 (정상 케이스)."""
        mods = [{"mod_type": "fatty_acid", "position": 4}]
        conflicts = check_conflicts(SST14, mods)
        c02 = [c for c in conflicts if c.rule_id == "C-02"]
        assert len(c02) == 0

    def test_c02_allows_n_terminal(self) -> None:
        """A1 (N-terminal, position=1)에 fatty_acid → C-02 없음."""
        mods = [{"mod_type": "fatty_acid", "position": 1}]
        conflicts = check_conflicts(SST14, mods)
        c02 = [c for c in conflicts if c.rule_id == "C-02"]
        assert len(c02) == 0


# ---------------------------------------------------------------------------
# C-03: d_amino_acid를 Gly 위치에 적용
# ---------------------------------------------------------------------------

class TestC03DAminoOnGly:
    """C-03: Gly는 키랄 중심 없음 — D-Gly = L-Gly (no-op WARNING)."""

    def test_c03_triggers_on_gly2(self) -> None:
        """G2에 d_amino_acid → WARNING 1개."""
        mods = [{"mod_type": "d_amino_acid", "position": 2}]
        conflicts = check_conflicts(SST14, mods)
        c03 = [c for c in conflicts if c.rule_id == "C-03"]
        assert len(c03) == 1
        assert c03[0].severity == "WARNING"

    def test_c03_no_conflict_on_non_gly(self) -> None:
        """F6(Phe, Gly 아님)에 d_amino_acid → C-03 없음."""
        mods = [{"mod_type": "d_amino_acid", "position": 6}]
        conflicts = check_conflicts(SST14, mods)
        c03 = [c for c in conflicts if c.rule_id == "C-03"]
        assert len(c03) == 0


# ---------------------------------------------------------------------------
# C-04: d_amino_acid를 Cys SS bond 위치에 적용
# ---------------------------------------------------------------------------

class TestC04DAminoOnCysSS:
    """C-04: SS bond Cys에 D-Cys 치환 → β-turn 손상 위험 ERROR (Phase 5 A-3 격상)."""

    def test_c04_triggers_on_cys3(self) -> None:
        """C3(SS bond Cys, position 3)에 d_amino_acid → ERROR 1개 (A-3 격상)."""
        mods = [{"mod_type": "d_amino_acid", "position": 3}]
        conflicts = check_conflicts(SST14, mods)
        c04 = [c for c in conflicts if c.rule_id == "C-04"]
        assert len(c04) == 1
        assert c04[0].severity == "ERROR"

    def test_c04_triggers_on_cys14(self) -> None:
        """C14(SS bond Cys, position 14)에 d_amino_acid → ERROR 1개 (A-3 격상)."""
        mods = [{"mod_type": "d_amino_acid", "position": 14}]
        conflicts = check_conflicts(SST14, mods)
        c04 = [c for c in conflicts if c.rule_id == "C-04"]
        assert len(c04) == 1
        assert c04[0].severity == "ERROR"

    def test_c04_no_conflict_non_ss_cys(self) -> None:
        """SS bond 없는 서열에서 Cys에 d_amino_acid → C-04 없음."""
        # Cys 하나만 있는 서열 (SS bond 쌍 없음)
        single_cys_seq = "AGCKN"
        mods = [{"mod_type": "d_amino_acid", "position": 3}]  # C3, 쌍 없음
        conflicts = check_conflicts(single_cys_seq, mods)
        c04 = [c for c in conflicts if c.rule_id == "C-04"]
        assert len(c04) == 0


# ---------------------------------------------------------------------------
# C-05: 자연 SS bond 존재 + cyclization modification 추가
# ---------------------------------------------------------------------------

class TestC05DuplicateCyclization:
    """C-05: 이미 Cys-Cys 자연 고리화된 서열에 cyclization 중복 지정."""

    def test_c05_triggers_on_sst14_with_cyclization(self) -> None:
        """SST14(Cys3-Cys14 자연 SS bond) + cyclization → WARNING 1개."""
        mods = [{"mod_type": "cyclization", "position": 1}]
        conflicts = check_conflicts(SST14, mods)
        c05 = [c for c in conflicts if c.rule_id == "C-05"]
        assert len(c05) == 1
        assert c05[0].severity == "WARNING"

    def test_c05_no_conflict_without_natural_ss(self) -> None:
        """Cys 없는 서열(SS bond 없음)에 cyclization → C-05 없음."""
        linear_seq = "AGKNFFWKTFTS"  # Cys 제거
        mods = [{"mod_type": "cyclization", "position": 1}]
        conflicts = check_conflicts(linear_seq, mods)
        c05 = [c for c in conflicts if c.rule_id == "C-05"]
        assert len(c05) == 0


# ---------------------------------------------------------------------------
# C-06: position 범위 밖
# ---------------------------------------------------------------------------

class TestC06OutOfRangePosition:
    """C-06: 1-indexed position이 [1, len(sequence)] 범위 밖."""

    def test_c06_triggers_on_position_zero(self) -> None:
        """position=0 (1-indexed 최솟값 미만) → ERROR."""
        mods = [{"mod_type": "fatty_acid", "position": 0}]
        conflicts = check_conflicts(SST14, mods)
        c06 = [c for c in conflicts if c.rule_id == "C-06"]
        assert len(c06) == 1
        assert c06[0].severity == "ERROR"

    def test_c06_triggers_on_position_exceeding_length(self) -> None:
        """position=15 (SST14 길이 14 초과) → ERROR."""
        mods = [{"mod_type": "d_amino_acid", "position": 15}]
        conflicts = check_conflicts(SST14, mods)
        c06 = [c for c in conflicts if c.rule_id == "C-06"]
        assert len(c06) == 1
        assert c06[0].severity == "ERROR"

    def test_c06_no_conflict_on_valid_boundary(self) -> None:
        """position=14 (SST14 마지막 잔기) → C-06 없음 (C-04는 별도)."""
        mods = [{"mod_type": "substitution", "position": 14}]
        conflicts = check_conflicts(SST14, mods)
        c06 = [c for c in conflicts if c.rule_id == "C-06"]
        assert len(c06) == 0


# ---------------------------------------------------------------------------
# 통합 케이스
# ---------------------------------------------------------------------------

class TestIntegration:
    """복합 modification 조합 통합 테스트."""

    def test_clean_fatty_acid_on_k4(self) -> None:
        """SST14 + fatty_acid at K4 → 전체 conflicts 없음 (정상 케이스)."""
        mods = [{"mod_type": "fatty_acid", "position": 4}]
        conflicts = check_conflicts(SST14, mods)
        assert conflicts == []

    def test_multiple_conflicts_in_one_call(self) -> None:
        """C-01(K4), C-02(W8), C-03(G2) 동시 발생 → 3개 이상 충돌."""
        mods = [
            {"mod_type": "fatty_acid",   "position": 4},  # K4 OK, but…
            {"mod_type": "pegylation",   "position": 4},  # C-01 trigger
            {"mod_type": "fatty_acid",   "position": 8},  # C-02 trigger (W8)
            {"mod_type": "d_amino_acid", "position": 2},  # C-03 trigger (G2)
        ]
        conflicts = check_conflicts(SST14, mods)
        found_rules = _rule_ids(conflicts)
        assert "C-01" in found_rules
        assert "C-02" in found_rules
        assert "C-03" in found_rules

    def test_return_type_is_list_of_conflict(self) -> None:
        """반환 타입이 list[Conflict]임을 확인."""
        mods: list[dict] = []
        result = check_conflicts(SST14, mods)
        assert isinstance(result, list)
        # 빈 modification 목록 → 충돌 없음
        assert result == []

    def test_lowercase_sequence_auto_normalized(self) -> None:
        """소문자 서열 입력 시 자동 대문자 변환 후 올바르게 동작."""
        mods = [{"mod_type": "fatty_acid", "position": 8}]  # W8, not Lys
        conflicts_lower = check_conflicts(SST14.lower(), mods)
        conflicts_upper = check_conflicts(SST14.upper(), mods)
        # 두 결과가 동일해야 함
        assert _rule_ids(conflicts_lower) == _rule_ids(conflicts_upper)
        assert len(conflicts_lower) >= 1
        assert conflicts_lower[0].rule_id == "C-02"


# ---------------------------------------------------------------------------
# A-2: 누락 테스트 케이스 4건 추가 (Phase 5)
# ---------------------------------------------------------------------------

class TestEdgeCasesPhase5:
    """Phase 5 A-2 — 누락 테스트 케이스: 비-int position, None, mod_type 누락, 빈 서열."""

    def test_non_int_position_string(self) -> None:
        """position='four' (비-int 문자열) → C-06 ERROR, C-99 없음 (A-6으로 선행 차단됨)."""
        mods = [{"mod_type": "fatty_acid", "position": "four"}]
        conflicts = check_conflicts(SST14, mods)
        c06 = [c for c in conflicts if c.rule_id == "C-06"]
        # C-06이 먼저 실행되어 비-int를 잡아야 함
        assert len(c06) >= 1
        assert c06[0].severity == "ERROR"
        # C-99(내부 예외)는 발생하지 않아야 함 — C-06 선행 차단으로 TypeError가 막혀야 함
        c99 = [c for c in conflicts if c.rule_id == "C-99"]
        assert len(c99) == 0

    def test_position_none_is_silently_skipped(self) -> None:
        """position=None → 모든 규칙에서 조용히 건너뜀, conflicts 없음."""
        mods = [{"mod_type": "fatty_acid", "position": None}]
        conflicts = check_conflicts(SST14, mods)
        assert conflicts == []

    def test_missing_mod_type_key(self) -> None:
        """mod_type 키 누락 → 조용히 무시, conflicts 없음."""
        mods = [{"position": 4}]
        conflicts = check_conflicts(SST14, mods)
        # mod_type이 없으면 어떤 규칙도 트리거하지 않아야 함
        assert conflicts == []

    def test_empty_sequence_c06_fires(self) -> None:
        """빈 서열('') + modification → C-06 ERROR (허용 범위=[1, 0] 어색하더라도 차단)."""
        mods = [{"mod_type": "fatty_acid", "position": 1}]
        conflicts = check_conflicts("", mods)
        c06 = [c for c in conflicts if c.rule_id == "C-06"]
        assert len(c06) >= 1
        assert c06[0].severity == "ERROR"

    def test_c01_c02_simultaneous(self) -> None:
        """W8에 fatty_acid + pegylation 동시 → C-01(같은 위치) + C-02(비-Lys) 동시 발생."""
        mods = [
            {"mod_type": "fatty_acid",  "position": 8},  # W8 non-Lys → C-02
            {"mod_type": "pegylation",  "position": 8},  # same pos → C-01
        ]
        conflicts = check_conflicts(SST14, mods)
        found = _rule_ids(conflicts)
        assert "C-01" in found
        assert "C-02" in found

    def test_bool_position_triggers_c06(self) -> None:
        """position=True (bool — int 서브클래스 트랩) → C-06 ERROR."""
        mods = [{"mod_type": "fatty_acid", "position": True}]
        conflicts = check_conflicts(SST14, mods)
        c06 = [c for c in conflicts if c.rule_id == "C-06"]
        assert len(c06) >= 1
        assert c06[0].severity == "ERROR"


# ---------------------------------------------------------------------------
# Stage 8g (VR-cycle-01 closure): C-07 DOTA chelator stoichiometry
# ---------------------------------------------------------------------------

class TestC07DotaDoubleConjugation:
    """C-07: DOTA chelator는 펩타이드당 1개만 결합 가능 (theranostic stoichiometry)."""

    def test_c07_single_dota_passes(self) -> None:
        """DOTA 1개만 있으면 충돌 없음 (정상 라벨링)."""
        mods = [{"mod_type": "dota", "position": 1}]
        conflicts = check_conflicts(SST14, mods)
        c07 = [c for c in conflicts if c.rule_id == "C-07"]
        assert c07 == [], "DOTA 1개는 정상이어야 함"

    def test_c07_double_dota_triggers_error(self) -> None:
        """DOTA 2개 → C-07 ERROR."""
        mods = [
            {"mod_type": "dota", "position": 1},
            {"mod_type": "dota", "position": 4},
        ]
        conflicts = check_conflicts(SST14, mods)
        c07 = [c for c in conflicts if c.rule_id == "C-07"]
        assert len(c07) == 1
        assert c07[0].severity == "ERROR"
        assert "stoichiometry" in c07[0].description or "DOTA" in c07[0].description
        assert c07[0].mods_involved == (0, 1)

    def test_c07_case_insensitive_DOTA(self) -> None:
        """mod_type 대문자 'DOTA' 또는 'dota_conjugation'도 매칭."""
        mods = [
            {"mod_type": "DOTA", "position": 1},
            {"mod_type": "dota_conjugation", "position": 4},
        ]
        conflicts = check_conflicts(SST14, mods)
        c07 = [c for c in conflicts if c.rule_id == "C-07"]
        assert len(c07) == 1, "case-insensitive 매칭이 작동해야 함"

    def test_c07_triple_dota_still_one_conflict(self) -> None:
        """DOTA 3개여도 single C-07 conflict (n개 = 1 conflict)."""
        mods = [
            {"mod_type": "dota", "position": 1},
            {"mod_type": "dota", "position": 4},
            {"mod_type": "dota", "position": 7},
        ]
        conflicts = check_conflicts(SST14, mods)
        c07 = [c for c in conflicts if c.rule_id == "C-07"]
        assert len(c07) == 1
        assert c07[0].mods_involved == (0, 1, 2)


# ---------------------------------------------------------------------------
# A-7: C-08~C-10 규칙 테스트 (Phase 5 — reviewer-chemistry 권고)
# ---------------------------------------------------------------------------

class TestC08DoubleDCysOnSSPair:
    """C-08: SS bond 양쪽 Cys에 동시 d_amino_acid → D,D-cystine geometry ERROR."""

    def test_c08_triggers_both_cys(self) -> None:
        """C3 + C14 양쪽 d_amino_acid → C-08 ERROR."""
        mods = [
            {"mod_type": "d_amino_acid", "position": 3},   # C3
            {"mod_type": "d_amino_acid", "position": 14},  # C14
        ]
        conflicts = check_conflicts(SST14, mods)
        c08 = [c for c in conflicts if c.rule_id == "C-08"]
        assert len(c08) == 1
        assert c08[0].severity == "ERROR"
        assert set(c08[0].mods_involved) == {0, 1}

    def test_c08_no_trigger_single_cys(self) -> None:
        """C3만 d_amino_acid (C14 없음) → C-08 없음, C-04만 발생."""
        mods = [{"mod_type": "d_amino_acid", "position": 3}]
        conflicts = check_conflicts(SST14, mods)
        c08 = [c for c in conflicts if c.rule_id == "C-08"]
        assert len(c08) == 0
        # C-04는 단일 Cys D-치환으로 발생해야 함
        c04 = [c for c in conflicts if c.rule_id == "C-04"]
        assert len(c04) == 1

    def test_c08_no_trigger_no_ss_pair(self) -> None:
        """Cys 없는 서열 → C-08 없음."""
        linear_seq = "AGKNFFWKTFTS"
        mods = [
            {"mod_type": "d_amino_acid", "position": 1},
            {"mod_type": "d_amino_acid", "position": 2},
        ]
        conflicts = check_conflicts(linear_seq, mods)
        c08 = [c for c in conflicts if c.rule_id == "C-08"]
        assert len(c08) == 0


class TestC09LactamNtermMod:
    """C-09: cyclization(lactam) + N-terminal fatty_acid/pegylation 충돌 ERROR."""

    def test_c09_triggers_cyclization_and_fatty_nterm(self) -> None:
        """cyclization + position=1 fatty_acid → C-09 ERROR."""
        mods = [
            {"mod_type": "cyclization", "position": 5},
            {"mod_type": "fatty_acid",  "position": 1},  # N-terminal
        ]
        conflicts = check_conflicts(SST14, mods)
        c09 = [c for c in conflicts if c.rule_id == "C-09"]
        assert len(c09) == 1
        assert c09[0].severity == "ERROR"

    def test_c09_triggers_cyclization_and_peg_nterm(self) -> None:
        """cyclization + position=1 pegylation → C-09 ERROR."""
        mods = [
            {"mod_type": "cyclization", "position": 5},
            {"mod_type": "pegylation",  "position": 1},
        ]
        conflicts = check_conflicts(SST14, mods)
        c09 = [c for c in conflicts if c.rule_id == "C-09"]
        assert len(c09) == 1
        assert c09[0].severity == "ERROR"

    def test_c09_no_trigger_cyclization_without_nterm(self) -> None:
        """cyclization만 있고 N-term mod 없음 → C-09 없음 (C-05는 별도)."""
        mods = [{"mod_type": "cyclization", "position": 5}]
        conflicts = check_conflicts(SST14, mods)
        c09 = [c for c in conflicts if c.rule_id == "C-09"]
        assert len(c09) == 0

    def test_c09_no_trigger_fatty_acid_on_lys_not_nterm(self) -> None:
        """fatty_acid @ position=4 (K4, 비-N-terminal) → C-09 없음."""
        mods = [
            {"mod_type": "cyclization", "position": 5},
            {"mod_type": "fatty_acid",  "position": 4},  # K4 not position 1
        ]
        conflicts = check_conflicts(SST14, mods)
        c09 = [c for c in conflicts if c.rule_id == "C-09"]
        assert len(c09) == 0


class TestC10SubstitutionAndDAmino:
    """C-10: 동일 position에 substitution + d_amino_acid 의미 충돌 ERROR."""

    def test_c10_triggers_same_position(self) -> None:
        """K4에 substitution + d_amino_acid 동시 → C-10 ERROR."""
        mods = [
            {"mod_type": "substitution",  "position": 4},
            {"mod_type": "d_amino_acid",  "position": 4},
        ]
        conflicts = check_conflicts(SST14, mods)
        c10 = [c for c in conflicts if c.rule_id == "C-10"]
        assert len(c10) == 1
        assert c10[0].severity == "ERROR"
        assert set(c10[0].mods_involved) == {0, 1}

    def test_c10_no_trigger_different_positions(self) -> None:
        """K4 substitution, K9 d_amino_acid (다른 position) → C-10 없음."""
        mods = [
            {"mod_type": "substitution", "position": 4},
            {"mod_type": "d_amino_acid", "position": 9},
        ]
        conflicts = check_conflicts(SST14, mods)
        c10 = [c for c in conflicts if c.rule_id == "C-10"]
        assert len(c10) == 0


# ---------------------------------------------------------------------------
# _find_cys_pairs 단위 테스트
# ---------------------------------------------------------------------------

class TestFindCysPairs:
    """_find_cys_pairs 내부 헬퍼 단위 테스트."""

    def test_sst14_has_one_pair(self) -> None:
        """SST-14 서열 → (2, 13) 쌍 하나."""
        pairs = _find_cys_pairs("AGCKNFFWKTFTSC")
        assert len(pairs) == 1
        assert pairs[0] == (2, 13)

    def test_no_cys_returns_empty(self) -> None:
        """Cys 없는 서열 → 빈 리스트."""
        pairs = _find_cys_pairs("AGKNFFWKTFTS")
        assert pairs == []

    def test_single_cys_returns_empty(self) -> None:
        """Cys 1개 → 쌍 없음."""
        pairs = _find_cys_pairs("AGCKNFFWKTFTS")
        assert pairs == []
