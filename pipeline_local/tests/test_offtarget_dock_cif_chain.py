"""
test_offtarget_dock_cif_chain.py — SSTR1-5 CIF/PDB 체인 선택 단위 테스트
==========================================================================

A-10 블로커 해소 검증:
  SSTR3_8XIR은 SSTR3-Gαi 복합체로 Gα 체인(C, 335 aa)이 가장 길었으나,
  _select_receptor_sequence()가 SSTR 서명 우선 선택 로직으로 올바른 체인을 반환함.

SSTR4 오매칭 버그 수정 검증:
  "VILRYAKMKTA" 서명이 SSTR1·SSTR4에 공유되어 SSTR4가 SSTR1로 잘못 매칭됨.
  해당 서명을 SSTR1·SSTR4의 서명 목록에서 제거하여 수정함.

테스트 그룹:
  TestSSTRChainSelectionPDB  — PDB 파일 기반 SSTR1-5 체인 선택
  TestSSTRChainSelectionCIF  — CIF 파일 기반 SSTR1-5 체인 선택
  TestSSTRSignatureNonAmbiguity — 서명 중복 없음 검증
"""
from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
SSTR_DATA = REPO_ROOT / "data" / "somatostatin_receptor"

# (SSTR name, UniProt ID, PDB stem)
SSTR_REGISTRY = [
    ("SSTR1", "P30872", "SSTR1_9IK8"),
    ("SSTR2", "P30874", "SSTR2_7XNA"),
    ("SSTR3", "P32745", "SSTR3_8XIR"),
    ("SSTR4", "P31391", "SSTR4_7XMT"),
    ("SSTR5", "P35346", "SSTR5_8ZBJ"),
]

# 각 수용체의 단량체 잔기 수 예상 범위 (구조별 결정됨)
EXPECTED_LENGTH_RANGES = {
    "SSTR1": (230, 310),
    "SSTR2": (350, 520),  # 7XNA는 Nb 포함 복합체 → 수용체 체인이 길 수 있음
    "SSTR3": (250, 350),
    "SSTR4": (230, 310),
    "SSTR5": (230, 310),
}


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _get_module():
    """offtarget_dock 모듈을 임포트한다. 경로 조정 포함."""
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from pipeline_local.scripts import offtarget_dock as m
    return m


# ---------------------------------------------------------------------------
# PDB 체인 선택 테스트
# ---------------------------------------------------------------------------

class TestSSTRChainSelectionPDB:
    """PDB 파일에서 SSTR1-5 각 수용체 체인을 정확히 선택하는지 검증한다."""

    @pytest.mark.parametrize("sstr_name,uniprot_id,stem", SSTR_REGISTRY)
    def test_correct_sstr_matched_from_pdb(
        self,
        sstr_name: str,
        uniprot_id: str,
        stem: str,
    ) -> None:
        """각 SSTR PDB 파일에서 서열을 추출했을 때 올바른 서브타입이 매칭된다."""
        m = _get_module()
        pdb_path = SSTR_DATA / f"{stem}.pdb"

        if not pdb_path.exists():
            pytest.skip(f"PDB 파일 없음: {pdb_path}")

        seq = m._extract_sequence_from_pdb(str(pdb_path))
        match = m._match_sstr_signature(seq)

        assert match is not None, (
            f"{sstr_name} PDB 서열에서 SSTR 서명 매칭 실패\n"
            f"  파일: {pdb_path}\n"
            f"  추출 서열 앞 50aa: {seq[:50]}"
        )

        matched_sstr, matched_uniprot, sig = match
        assert matched_sstr == sstr_name, (
            f"{sstr_name} PDB가 {matched_sstr}로 잘못 매칭됨 (시그니처: {sig})\n"
            f"  파일: {pdb_path}"
        )
        assert matched_uniprot == uniprot_id, (
            f"{sstr_name} UniProt 불일치: 기대={uniprot_id}, 실제={matched_uniprot}"
        )

    @pytest.mark.parametrize("sstr_name,uniprot_id,stem", SSTR_REGISTRY)
    def test_receptor_chain_length_in_range_pdb(
        self,
        sstr_name: str,
        uniprot_id: str,
        stem: str,
    ) -> None:
        """추출된 수용체 체인 길이가 GPCR 합리적 범위 내에 있다."""
        m = _get_module()
        pdb_path = SSTR_DATA / f"{stem}.pdb"

        if not pdb_path.exists():
            pytest.skip(f"PDB 파일 없음: {pdb_path}")

        seq = m._extract_sequence_from_pdb(str(pdb_path))
        lo, hi = EXPECTED_LENGTH_RANGES[sstr_name]

        assert lo <= len(seq) <= hi, (
            f"{sstr_name} 체인 길이 {len(seq)} aa가 예상 범위 [{lo}, {hi}] 밖\n"
            f"  파일: {pdb_path}"
        )


# ---------------------------------------------------------------------------
# CIF 체인 선택 테스트
# ---------------------------------------------------------------------------

class TestSSTRChainSelectionCIF:
    """CIF 파일에서 SSTR1-5 각 수용체 체인을 정확히 선택하는지 검증한다."""

    @pytest.mark.parametrize("sstr_name,uniprot_id,stem", SSTR_REGISTRY)
    def test_correct_sstr_matched_from_cif(
        self,
        sstr_name: str,
        uniprot_id: str,
        stem: str,
    ) -> None:
        """각 SSTR CIF 파일에서 서열을 추출했을 때 올바른 서브타입이 매칭된다."""
        m = _get_module()
        cif_path = SSTR_DATA / f"{stem}.cif"

        if not cif_path.exists():
            pytest.skip(f"CIF 파일 없음: {cif_path}")

        seq = m._extract_sequence_from_pdb(str(cif_path))
        match = m._match_sstr_signature(seq)

        assert match is not None, (
            f"{sstr_name} CIF 서열에서 SSTR 서명 매칭 실패\n"
            f"  파일: {cif_path}\n"
            f"  추출 서열 앞 50aa: {seq[:50]}"
        )

        matched_sstr, matched_uniprot, sig = match
        assert matched_sstr == sstr_name, (
            f"{sstr_name} CIF가 {matched_sstr}로 잘못 매칭됨 (시그니처: {sig})\n"
            f"  파일: {cif_path}"
        )

    @pytest.mark.parametrize("sstr_name,uniprot_id,stem", SSTR_REGISTRY)
    def test_pdb_and_cif_give_same_sstr_match(
        self,
        sstr_name: str,
        uniprot_id: str,
        stem: str,
    ) -> None:
        """동일 구조의 PDB/CIF에서 추출된 서열이 같은 SSTR 서브타입으로 매칭된다."""
        m = _get_module()
        pdb_path = SSTR_DATA / f"{stem}.pdb"
        cif_path = SSTR_DATA / f"{stem}.cif"

        if not pdb_path.exists() or not cif_path.exists():
            pytest.skip(f"파일 없음: {pdb_path} 또는 {cif_path}")

        seq_pdb = m._extract_sequence_from_pdb(str(pdb_path))
        seq_cif = m._extract_sequence_from_pdb(str(cif_path))

        match_pdb = m._match_sstr_signature(seq_pdb)
        match_cif = m._match_sstr_signature(seq_cif)

        assert match_pdb is not None and match_cif is not None, (
            f"{sstr_name}: PDB 매칭={match_pdb}, CIF 매칭={match_cif}"
        )
        assert match_pdb[0] == match_cif[0], (
            f"{sstr_name}: PDB({match_pdb[0]})와 CIF({match_cif[0]}) 매칭 불일치"
        )


# ---------------------------------------------------------------------------
# SSTR3 복합체 특이 케이스 (A-10 블로커)
# ---------------------------------------------------------------------------

class TestSSTR3GProteinComplex:
    """SSTR3_8XIR (SSTR3-Gαi 복합체) 체인 선택 특이 케이스."""

    def test_sstr3_8xir_not_longest_chain_selected(self) -> None:
        """SSTR3_8XIR에서 가장 긴 체인(Gα)이 아닌 SSTR3 체인이 선택된다."""
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from pipeline_local.scripts.offtarget_dock import (
            _extract_sequence_from_pdb,
            _match_sstr_signature,
        )

        pdb_path = SSTR_DATA / "SSTR3_8XIR.pdb"
        if not pdb_path.exists():
            pytest.skip(f"PDB 파일 없음: {pdb_path}")

        seq = _extract_sequence_from_pdb(str(pdb_path))
        match = _match_sstr_signature(seq)

        # SSTR3_8XIR의 Gα 체인(C)은 335 aa로 가장 길다.
        # SSTR3 체인(D)은 274 aa.
        # 올바른 선택: SSTR3 서명이 있는 체인 (Gα보다 짧을 수 있음)
        assert match is not None, "SSTR3_8XIR SSTR 서명 매칭 실패"
        assert match[0] == "SSTR3", (
            f"SSTR3_8XIR에서 SSTR3 대신 {match[0]} 선택됨 — "
            f"가장 긴 체인(Gα) 폴백이 잘못 발동된 것으로 추정"
        )

    def test_sstr3_8xir_uniprot_is_p32745(self) -> None:
        """SSTR3_8XIR 매칭 결과 UniProt ID가 P32745인지 확인한다."""
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from pipeline_local.scripts.offtarget_dock import (
            _extract_sequence_from_pdb,
            _find_sstr_uniprot,
        )

        pdb_path = SSTR_DATA / "SSTR3_8XIR.pdb"
        if not pdb_path.exists():
            pytest.skip(f"PDB 파일 없음: {pdb_path}")

        seq = _extract_sequence_from_pdb(str(pdb_path))
        uniprot = _find_sstr_uniprot(seq)

        assert uniprot == "P32745", (
            f"SSTR3 UniProt 기대 P32745, 실제 {uniprot}"
        )


# ---------------------------------------------------------------------------
# 서명 비중복성 검증 (SSTR4 오매칭 회귀 방지)
# ---------------------------------------------------------------------------

class TestSSTRSignatureNonAmbiguity:
    """_SSTR_SIGNATURES 내 서명이 서브타입 간 고유한지 검증한다."""

    def test_no_signature_shared_across_subtypes(self) -> None:
        """어떤 서명 문자열도 두 개 이상의 SSTR 서브타입에 동시에 등록되어 있지 않다."""
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from pipeline_local.scripts.offtarget_dock import _SSTR_SIGNATURES

        seen: dict[str, str] = {}  # sig → first_sstr_name
        for sstr_name, signatures in _SSTR_SIGNATURES.items():
            for sig in signatures:
                if sig in seen:
                    pytest.fail(
                        f"서명 '{sig}'가 {seen[sig]}와 {sstr_name} 양쪽에 중복 등록됨.\n"
                        f"중복 서명은 서브타입 오매칭을 유발합니다 (SSTR4→SSTR1 버그)."
                    )
                seen[sig] = sstr_name

    def test_sstr4_not_matched_as_sstr1_from_pdb(self) -> None:
        """SSTR4_7XMT PDB에서 추출된 서열이 SSTR1이 아닌 SSTR4로 매칭된다 (회귀 방지)."""
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from pipeline_local.scripts.offtarget_dock import (
            _extract_sequence_from_pdb,
            _match_sstr_signature,
        )

        pdb_path = SSTR_DATA / "SSTR4_7XMT.pdb"
        if not pdb_path.exists():
            pytest.skip(f"PDB 파일 없음: {pdb_path}")

        seq = _extract_sequence_from_pdb(str(pdb_path))
        match = _match_sstr_signature(seq)

        assert match is not None, "SSTR4_7XMT SSTR 서명 매칭 실패"
        assert match[0] != "SSTR1", (
            f"SSTR4_7XMT가 SSTR1으로 오매칭됨 (시그니처: {match[2]}). "
            f"VILRYAKMKTA 공유 서명 제거가 누락된 것으로 추정."
        )
        assert match[0] == "SSTR4", (
            f"SSTR4_7XMT가 {match[0]}로 잘못 매칭됨 (기대: SSTR4)"
        )
