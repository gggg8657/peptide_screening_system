"""ProteinMPNNStrategy 단위 테스트.

테스트 범위:
- Strategy Protocol 준수
- validate_env: proteinmpnn env 미존재 / ligandmpnn 미설치 시 (False, err)
- validate_env: receptor_context + complex_pdb 부재 → (False, err)
- generate: mock ligandmpnn 출력으로 smoke (max_variants=3)
- pharmacophore guard: fixed_positions 위반 시퀀스 제거
- pharmacophore guard: 소수성 위반 시퀀스 제거
- pharmacophore guard: 중복 시퀀스 제거
- pharmacophore guard: seed 동일 시퀀스 제거
- generate: receptor_context + complex_pdb 부재 → RuntimeError
- _make_extended_backbone_pdb: 길이·체인 정합성
- _fixed_positions_to_ligandmpnn_str: 변환 정합성
- _parse_fasta_sequences: seed 제외 파싱
- _parse_confidence: 정규표현식 파싱
- registry: get_strategy('proteinmpnn') 반환 타입
"""

from __future__ import annotations

import os
import tempfile
import textwrap
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from pipeline_local.schemas.io_schemas import Step03bOutput, VariantEntry
from pipeline_local.strategies.base import MutationStrategy
from pipeline_local.strategies.proteinmpnn import (
    ProteinMPNNStrategy,
    _fixed_positions_to_ligandmpnn_str,
    _make_extended_backbone_pdb,
    _parse_confidence,
    _parse_fasta_sequences,
)
from pipeline_local.strategies.registry import get_strategy

# ---------------------------------------------------------------------------
# 공통 픽스처
# ---------------------------------------------------------------------------

SEED = "AGCKNFFWKTFTSC"
FIXED: Dict[int, str] = {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"}


def _base_config(
    mode: str = "peptide_only",
    complex_pdb: Any = None,
    max_variants: int = 3,
    num_seq: int = 5,
) -> dict:
    return {
        "approach_b": {
            "strategy": "proteinmpnn",
            "seed_sequence": SEED,
            "fixed_positions": FIXED,
            "max_variants": max_variants,
            "hydrophobicity_max_delta": 2.0,
            "proteinmpnn_opts": {
                "mode": mode,
                "complex_pdb": complex_pdb,
                "num_seq_per_target": num_seq,
                "sampling_temperature": 0.1,
                "device": "cpu",
            },
        }
    }


def _mock_raw_seqs_ok() -> List[tuple]:
    """pharmacophore 통과하는 raw 시퀀스 목록."""
    # AGCKNFFWKTFTSC 기준: pos3=C, pos7=F, pos8=W, pos9=K, pos10=T, pos14=C 고정
    # pos1=A→G, pos2=G→S 등 가변 위치 변이
    return [
        ("peptide, id=1, T=0.1, seed=1, overall_confidence=0.8000", "SGCKNFFWKTFTSC", 0.8),
        ("peptide, id=2, T=0.1, seed=1, overall_confidence=0.7500", "AGCRNFFWKTFTSC", 0.75),
        ("peptide, id=3, T=0.1, seed=1, overall_confidence=0.7000", "AGCKNFFWKTFLSC", 0.70),
        ("peptide, id=4, T=0.1, seed=1, overall_confidence=0.6500", "SGCRNFFWKTFTSC", 0.65),
    ]


def _mock_raw_seqs_with_violations() -> List[tuple]:
    """pharmacophore 위반 및 중복 포함 raw 시퀀스."""
    return [
        # pharmacophore 위반: pos3=A (Cys→Ala)
        ("peptide, id=1, T=0.1, seed=1, overall_confidence=0.9", "AGAKNFFWKTFTSC", 0.9),
        # OK
        ("peptide, id=2, T=0.1, seed=1, overall_confidence=0.8", "SGCKNFFWKTFTSC", 0.8),
        # 중복
        ("peptide, id=3, T=0.1, seed=1, overall_confidence=0.75", "SGCKNFFWKTFTSC", 0.75),
        # seed와 동일
        ("peptide, id=4, T=0.1, seed=1, overall_confidence=0.7", SEED, 0.7),
        # pharmacophore 위반: pos8=A (Trp→Ala)
        ("peptide, id=5, T=0.1, seed=1, overall_confidence=0.65", "AGCKNFFAKTFTSC", 0.65),
        # OK
        ("peptide, id=6, T=0.1, seed=1, overall_confidence=0.6", "AGCRNFFWKTFTSC", 0.6),
    ]


# ---------------------------------------------------------------------------
# Protocol 준수
# ---------------------------------------------------------------------------

def test_proteinmpnn_strategy_conforms_to_protocol():
    strategy = ProteinMPNNStrategy()
    assert isinstance(strategy, MutationStrategy)
    assert strategy.name == "proteinmpnn"


def test_registry_returns_proteinmpnn_strategy():
    strategy = get_strategy("proteinmpnn")
    assert isinstance(strategy, ProteinMPNNStrategy)


# ---------------------------------------------------------------------------
# validate_env
# ---------------------------------------------------------------------------

def test_validate_env_missing_conda_env(monkeypatch):
    """conda env 미존재 시 (False, 에러 메시지)."""
    mock_result = MagicMock()
    mock_result.stdout = "base\nbio-tools\n"  # proteinmpnn 없음
    mock_result.returncode = 0

    with patch("pipeline_local.strategies.proteinmpnn.subprocess.run", return_value=mock_result):
        ok, err = ProteinMPNNStrategy().validate_env()

    assert ok is False
    assert err is not None
    assert "proteinmpnn" in err.lower() or "conda env" in err.lower()


def test_validate_env_ligandmpnn_not_installed(monkeypatch):
    """proteinmpnn env 있지만 ligandmpnn 미설치 시 (False, 에러 메시지)."""
    call_count = [0]

    def fake_run(cmd, **kwargs):
        mock = MagicMock()
        call_count[0] += 1
        if call_count[0] == 1:
            # conda env list → proteinmpnn 있음
            mock.stdout = "base\nproteinmpnn\n"
            mock.returncode = 0
        else:
            # ligandmpnn import 실패
            mock.stdout = ""
            mock.stderr = "ModuleNotFoundError: No module named 'ligandmpnn'"
            mock.returncode = 1
        return mock

    with patch("pipeline_local.strategies.proteinmpnn.subprocess.run", side_effect=fake_run):
        ok, err = ProteinMPNNStrategy().validate_env()

    assert ok is False
    assert err is not None
    assert "ligandmpnn" in err.lower()


def test_validate_env_receptor_context_missing_complex_pdb():
    """receptor_context 모드에 complex_pdb 없을 때 (False, 에러)."""
    config = _base_config(mode="receptor_context", complex_pdb=None)

    call_count = [0]

    def fake_run(cmd, **kwargs):
        mock = MagicMock()
        call_count[0] += 1
        if call_count[0] == 1:
            mock.stdout = "base\nproteinmpnn\n"
            mock.returncode = 0
        else:
            mock.stdout = "ok\n"
            mock.returncode = 0
        return mock

    with patch("pipeline_local.strategies.proteinmpnn.subprocess.run", side_effect=fake_run):
        ok, err = ProteinMPNNStrategy().validate_env(config)

    assert ok is False
    assert err is not None
    assert "receptor_context" in err or "complex_pdb" in err


def test_validate_env_receptor_context_pdb_not_found(tmp_path):
    """receptor_context 모드에 complex_pdb 경로가 존재하지 않을 때 (False, 에러)."""
    nonexistent = str(tmp_path / "nonexistent.pdb")
    config = _base_config(mode="receptor_context", complex_pdb=nonexistent)

    call_count = [0]

    def fake_run(cmd, **kwargs):
        mock = MagicMock()
        call_count[0] += 1
        if call_count[0] == 1:
            mock.stdout = "base\nproteinmpnn\n"
            mock.returncode = 0
        else:
            mock.stdout = "ok\n"
            mock.returncode = 0
        return mock

    with patch("pipeline_local.strategies.proteinmpnn.subprocess.run", side_effect=fake_run):
        ok, err = ProteinMPNNStrategy().validate_env(config)

    assert ok is False
    assert err is not None
    assert "존재하지 않" in err or "nonexistent" in err


def test_validate_env_ok_peptide_only():
    """정상 환경 (peptide_only 모드)에서 (True, None)."""
    call_count = [0]

    def fake_run(cmd, **kwargs):
        mock = MagicMock()
        call_count[0] += 1
        if call_count[0] == 1:
            mock.stdout = "base\nproteinmpnn\n"
            mock.returncode = 0
        else:
            mock.stdout = "ok\n"
            mock.returncode = 0
        return mock

    with patch("pipeline_local.strategies.proteinmpnn.subprocess.run", side_effect=fake_run):
        ok, err = ProteinMPNNStrategy().validate_env()

    assert ok is True
    assert err is None


# ---------------------------------------------------------------------------
# generate: smoke test (mock _collect_sequences)
# ---------------------------------------------------------------------------

def test_generate_smoke_peptide_only_mock(tmp_path, monkeypatch):
    """peptide_only 모드: mock ligandmpnn 출력으로 smoke 테스트."""
    config = _base_config(mode="peptide_only", max_variants=3, num_seq=5)

    # validate_env 통과
    monkeypatch.setattr(ProteinMPNNStrategy, "validate_env", lambda self, cfg=None: (True, None))
    # _run_ligandmpnn noop
    monkeypatch.setattr(ProteinMPNNStrategy, "_run_ligandmpnn", staticmethod(lambda **kw: None))
    # _collect_sequences → mock 시퀀스
    monkeypatch.setattr(
        ProteinMPNNStrategy,
        "_collect_sequences",
        staticmethod(lambda out_dir: _mock_raw_seqs_ok()),
    )

    result = ProteinMPNNStrategy().generate(config)

    assert isinstance(result, Step03bOutput)
    assert result.total_generated <= 3
    assert len(result.variants) == result.total_generated
    assert result.seed_sequence == SEED
    assert result.fixed_positions == FIXED
    assert all(v.source == "proteinmpnn" for v in result.variants)
    assert all(v.variant_id == f"var_{i:03d}" for i, v in enumerate(result.variants, start=1))


def test_generate_receptor_context_missing_complex_raises(monkeypatch):
    """receptor_context + complex_pdb 없음 → RuntimeError."""
    config = _base_config(mode="receptor_context", complex_pdb=None)

    # validate_env는 에러 반환
    def fake_validate(self, cfg=None):
        if cfg is not None:
            ab = cfg.get("approach_b", cfg)
            opts = ab.get("proteinmpnn_opts", {})
            if opts.get("mode") == "receptor_context" and not opts.get("complex_pdb"):
                return False, "receptor_context 모드에는 complex_pdb가 필요합니다."
        return True, None

    monkeypatch.setattr(ProteinMPNNStrategy, "validate_env", fake_validate)

    with pytest.raises(RuntimeError, match="환경 검사 실패"):
        ProteinMPNNStrategy().generate(config)


# ---------------------------------------------------------------------------
# pharmacophore guard
# ---------------------------------------------------------------------------

def test_pharmacophore_guard_removes_fixed_position_violations():
    """fixed_positions 위반 시퀀스가 제거되는지 확인."""
    raw = _mock_raw_seqs_with_violations()
    variants = ProteinMPNNStrategy._apply_pharmacophore_guard(
        raw_seqs=raw,
        seed=SEED,
        fixed_positions=FIXED,
        max_variants=100,
        max_hydro_delta=2.0,
    )
    sequences = [v.sequence for v in variants]
    # pos3=A (AGAKNFFWKTFTSC) 위반 제거
    assert "AGAKNFFWKTFTSC" not in sequences
    # pos8=A (AGCKNFFAKTFTSC) 위반 제거
    assert "AGCKNFFAKTFTSC" not in sequences


def test_pharmacophore_guard_removes_duplicates():
    """중복 시퀀스가 한 개만 남는지 확인."""
    raw = _mock_raw_seqs_with_violations()
    variants = ProteinMPNNStrategy._apply_pharmacophore_guard(
        raw_seqs=raw,
        seed=SEED,
        fixed_positions=FIXED,
        max_variants=100,
        max_hydro_delta=2.0,
    )
    sequences = [v.sequence for v in variants]
    # 중복 없음
    assert len(sequences) == len(set(sequences))


def test_pharmacophore_guard_removes_seed_sequence():
    """seed와 동일한 시퀀스가 제거되는지 확인."""
    raw = _mock_raw_seqs_with_violations()
    variants = ProteinMPNNStrategy._apply_pharmacophore_guard(
        raw_seqs=raw,
        seed=SEED,
        fixed_positions=FIXED,
        max_variants=100,
        max_hydro_delta=2.0,
    )
    sequences = [v.sequence for v in variants]
    assert SEED not in sequences
    assert SEED.upper() not in sequences


def test_pharmacophore_guard_respects_max_variants():
    """max_variants 제한이 준수되는지 확인."""
    raw = _mock_raw_seqs_ok() * 10  # 40개
    variants = ProteinMPNNStrategy._apply_pharmacophore_guard(
        raw_seqs=raw,
        seed=SEED,
        fixed_positions=FIXED,
        max_variants=2,
        max_hydro_delta=2.0,
    )
    assert len(variants) <= 2


def test_pharmacophore_guard_variant_id_sequential():
    """variant_id가 var_001부터 순번으로 부여되는지 확인."""
    raw = _mock_raw_seqs_ok()
    variants = ProteinMPNNStrategy._apply_pharmacophore_guard(
        raw_seqs=raw,
        seed=SEED,
        fixed_positions=FIXED,
        max_variants=10,
        max_hydro_delta=2.0,
    )
    for i, v in enumerate(variants, start=1):
        assert v.variant_id == f"var_{i:03d}"


def test_pharmacophore_guard_mutations_calculated_correctly():
    """mutations 필드가 seed 대비 변이 목록을 올바르게 계산하는지 확인."""
    raw = [("peptide, id=1, T=0.1, seed=1, overall_confidence=0.8", "SGCKNFFWKTFTSC", 0.8)]
    variants = ProteinMPNNStrategy._apply_pharmacophore_guard(
        raw_seqs=raw,
        seed=SEED,
        fixed_positions=FIXED,
        max_variants=5,
        max_hydro_delta=2.0,
    )
    assert len(variants) == 1
    # A1S
    assert "A1S" in variants[0].mutations
    assert variants[0].n_mutations == 1


# ---------------------------------------------------------------------------
# helper functions
# ---------------------------------------------------------------------------

def test_make_extended_backbone_pdb_line_count():
    """SST-14 14잔기 → 14×4 = 56 ATOM lines + END."""
    pdb = _make_extended_backbone_pdb(SEED, chain="A")
    atom_lines = [l for l in pdb.splitlines() if l.startswith("ATOM")]
    assert len(atom_lines) == len(SEED) * 4  # N, CA, C, O


def test_make_extended_backbone_pdb_chain_id():
    """chain ID가 올바르게 설정되는지 확인."""
    pdb = _make_extended_backbone_pdb(SEED, chain="B")
    for line in pdb.splitlines():
        if line.startswith("ATOM"):
            assert line[21] == "B"


def test_fixed_positions_to_ligandmpnn_str_basic():
    """기본 fixed_positions 변환."""
    result = _fixed_positions_to_ligandmpnn_str({3: "C", 14: "C", 7: "F"}, chain="A")
    # 정렬 순서: A3 A7 A14
    assert result == "A3 A7 A14"


def test_fixed_positions_to_ligandmpnn_str_chain_b():
    """chain B 인수 적용."""
    result = _fixed_positions_to_ligandmpnn_str({3: "C"}, chain="B")
    assert result == "B3"


def test_parse_confidence_normal():
    """overall_confidence 파싱 정상 동작."""
    header = "peptide, id=1, T=0.1, seed=37184, overall_confidence=0.8234"
    assert _parse_confidence(header) == pytest.approx(0.8234)


def test_parse_confidence_missing():
    """overall_confidence 없을 때 0.0 반환."""
    header = "peptide, id=1, T=0.1"
    assert _parse_confidence(header) == 0.0


def test_parse_fasta_sequences_excludes_seed():
    """FASTA 파싱 시 첫 번째 seed 엔트리(id= 없음)가 제외되는지 확인."""
    fasta_content = textwrap.dedent("""\
        >peptide, T=0.1, seed=37184, num_res=14
        AGCKNFFWKTFTSC
        >peptide, id=1, T=0.1, overall_confidence=0.8000
        SGCKNFFWKTFTSC
        >peptide, id=2, T=0.1, overall_confidence=0.7000
        AGCRNFFWKTFTSC
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fa", delete=False) as f:
        f.write(fasta_content)
        fa_path = f.name

    try:
        pairs = _parse_fasta_sequences(fa_path)
    finally:
        os.unlink(fa_path)

    assert len(pairs) == 2
    seqs = [s for _, s in pairs]
    assert "AGCKNFFWKTFTSC" not in seqs
    assert "SGCKNFFWKTFTSC" in seqs
    assert "AGCRNFFWKTFTSC" in seqs
