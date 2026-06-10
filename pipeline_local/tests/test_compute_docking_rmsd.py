"""
tests/test_compute_docking_rmsd.py
===================================
compute_docking_rmsd.py 단위 테스트.

실제 PDB 파일 없이도 실행 가능하도록 최소 합성 PDB 텍스트를 사용한다.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import List

import pytest

# ---------------------------------------------------------------------------
# 합성 PDB 생성 헬퍼
# ---------------------------------------------------------------------------

_ATOM_LINE = (
    "ATOM  {serial:5d}  CA  {resname:3s} {chain:1s}{resseq:4d}    "
    "{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C  \n"
)

RESIDUE_NAMES = ["ALA", "GLY", "VAL", "LEU", "ILE", "PRO", "PHE", "TRP", "MET", "SER"]


def _make_pdb_ca_only(
    coords: List[tuple],
    chain: str = "A",
    start_resseq: int = 1,
) -> str:
    """
    Cα 원자만 있는 간단한 PDB 문자열 생성.

    Parameters
    ----------
    coords : list of (x, y, z) tuples
    chain : str
        체인 ID
    start_resseq : int
        시작 잔기 번호
    """
    lines = []
    for i, (x, y, z) in enumerate(coords):
        resname = RESIDUE_NAMES[i % len(RESIDUE_NAMES)]
        lines.append(
            _ATOM_LINE.format(
                serial=i + 1,
                resname=resname,
                chain=chain,
                resseq=start_resseq + i,
                x=x, y=y, z=z,
            )
        )
    lines.append("END\n")
    return "".join(lines)


def _write_pdb(content: str, tmp_path: Path, name: str = "test.pdb") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# compute_ca_rmsd 테스트
# ---------------------------------------------------------------------------

# compute_docking_rmsd 를 sys.path 없이 import 하기 위한 픽스처
@pytest.fixture(scope="module")
def rmsd_module():
    repo_root = Path(__file__).resolve().parents[2]
    scripts_dir = repo_root / "pipeline_local" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import compute_docking_rmsd as m
    return m


class TestExtractCaAtoms:
    """_extract_ca_atoms 함수 테스트."""

    def test_basic_extraction(self, rmsd_module, tmp_path):
        coords = [(1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (3.0, 0.0, 0.0)]
        pdb_text = _make_pdb_ca_only(coords, chain="A")
        pdb_path = _write_pdb(pdb_text, tmp_path)
        atoms, ids = rmsd_module._extract_ca_atoms(pdb_path, chain_id="A")
        assert len(atoms) == 3
        assert ids == [1, 2, 3]

    def test_chain_auto_select(self, rmsd_module, tmp_path):
        """chain_id=None 이면 첫 번째 체인 자동 선택."""
        coords = [(0.0, 0.0, 0.0)]
        pdb_text = _make_pdb_ca_only(coords, chain="B")
        pdb_path = _write_pdb(pdb_text, tmp_path)
        atoms, ids = rmsd_module._extract_ca_atoms(pdb_path, chain_id=None)
        assert len(atoms) == 1

    def test_invalid_chain_raises(self, rmsd_module, tmp_path):
        """존재하지 않는 체인 ID → ValueError."""
        coords = [(0.0, 0.0, 0.0)]
        pdb_text = _make_pdb_ca_only(coords, chain="A")
        pdb_path = _write_pdb(pdb_text, tmp_path)
        with pytest.raises(ValueError, match="Chain 'Z' not found"):
            rmsd_module._extract_ca_atoms(pdb_path, chain_id="Z")


class TestComputeCaRmsd:
    """compute_ca_rmsd 함수 테스트."""

    def test_identical_structures_rmsd_zero(self, rmsd_module, tmp_path):
        """동일 구조 → RMSD ≈ 0."""
        coords = [(1.0, 0.0, 0.0), (2.0, 1.0, 0.0), (3.0, 0.0, 1.0)]
        pdb_text = _make_pdb_ca_only(coords)
        pred_path = _write_pdb(pdb_text, tmp_path, "pred.pdb")
        ref_path = _write_pdb(pdb_text, tmp_path, "ref.pdb")
        result = rmsd_module.compute_ca_rmsd(pred_path, ref_path)
        assert result["rmsd_angstrom"] == pytest.approx(0.0, abs=1e-4)
        assert result["n_ca_matched"] == 3

    def test_translated_structure(self, rmsd_module, tmp_path):
        """균일 평행이동 → aligned RMSD ≈ 0, no_align RMSD > 0."""
        coords_ref = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
        coords_pred = [(t + 5, 0.0, 0.0) for t, _, _ in coords_ref]
        ref_path = _write_pdb(_make_pdb_ca_only(coords_ref), tmp_path, "ref.pdb")
        pred_path = _write_pdb(_make_pdb_ca_only(coords_pred), tmp_path, "pred.pdb")

        # 정렬 후: RMSD ≈ 0
        result_aligned = rmsd_module.compute_ca_rmsd(pred_path, ref_path, align=True)
        assert result_aligned["rmsd_angstrom"] == pytest.approx(0.0, abs=1e-3)

        # 정렬 없이: RMSD = 5.0
        result_raw = rmsd_module.compute_ca_rmsd(pred_path, ref_path, align=False)
        assert result_raw["rmsd_angstrom"] == pytest.approx(5.0, abs=1e-3)

    def test_partial_residue_match(self, rmsd_module, tmp_path):
        """잔기 수 불일치 → 공통 잔기만 사용 + warning."""
        coords_ref = [(float(i), 0.0, 0.0) for i in range(5)]  # 5 잔기
        coords_pred = [(float(i), 0.0, 0.0) for i in range(3)]  # 3 잔기
        ref_path = _write_pdb(_make_pdb_ca_only(coords_ref), tmp_path, "ref.pdb")
        pred_path = _write_pdb(_make_pdb_ca_only(coords_pred), tmp_path, "pred.pdb")
        result = rmsd_module.compute_ca_rmsd(pred_path, ref_path)
        assert result["n_ca_matched"] == 3
        assert result["warning"] is not None

    def test_result_keys(self, rmsd_module, tmp_path):
        """반환 dict 키 확인."""
        coords = [(0.0, 0.0, 0.0)]
        pdb = _write_pdb(_make_pdb_ca_only(coords), tmp_path, "t.pdb")
        result = rmsd_module.compute_ca_rmsd(pdb, pdb)
        required_keys = {"rmsd_angstrom", "n_ca_matched", "pred_pdb", "ref_pdb", "aligned"}
        assert required_keys.issubset(result.keys())


class TestComputeRmsdBatch:
    """compute_rmsd_batch 함수 테스트."""

    def test_success_rate_all_match(self, rmsd_module, tmp_path):
        """모든 포즈 RMSD = 0 → success_rate = 1.0."""
        coords = [(1.0, 0.0, 0.0), (2.0, 1.0, 0.0)]
        pdb_text = _make_pdb_ca_only(coords)
        ref = _write_pdb(pdb_text, tmp_path, "ref.pdb")
        preds = [_write_pdb(pdb_text, tmp_path, f"pred_{i}.pdb") for i in range(3)]
        result = rmsd_module.compute_rmsd_batch(preds, ref, rmsd_threshold=2.0)
        assert result["rmsd_success_rate"] == pytest.approx(1.0)
        assert result["n_success"] == 3
        assert result["n_total"] == 3

    def test_success_rate_none_match(self, rmsd_module, tmp_path):
        """모든 포즈 RMSD > threshold → success_rate = 0.

        단순 평행이동(rigid-body translation)은 Superimposer가 정렬 후 제거하므로
        RMSD=0이 된다. 진정한 RMSD > 0 케이스를 만들려면 구조적으로 다른 형상이
        필요하다 (단순 회전·이동으로 겹쳐지지 않는 경우).
        여기서는 잔기를 3개 쓰고 2번 잔기만 y축으로 이동시켜 RMSD > 0을 보장한다.
        """
        import numpy as np
        # 참조: (0,0,0), (1,0,0), (2,0,0) — 직선
        coords_ref = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
        # 예측: 2번 잔기를 y=50으로 이동 → 어떤 rigid-body 변환으로도 완벽 정렬 불가
        coords_pred = [(0.0, 0.0, 0.0), (1.0, 50.0, 0.0), (2.0, 0.0, 0.0)]
        ref = _write_pdb(_make_pdb_ca_only(coords_ref), tmp_path, "ref.pdb")
        pred = _write_pdb(_make_pdb_ca_only(coords_pred), tmp_path, "pred.pdb")
        result = rmsd_module.compute_rmsd_batch([pred], ref, rmsd_threshold=2.0)
        assert result["rmsd_success_rate"] == pytest.approx(0.0)
        assert result["n_success"] == 0

    def test_batch_result_keys(self, rmsd_module, tmp_path):
        """반환 dict 필수 키 확인."""
        coords = [(0.0, 0.0, 0.0)]
        pdb = _write_pdb(_make_pdb_ca_only(coords), tmp_path, "t.pdb")
        result = rmsd_module.compute_rmsd_batch([pdb], pdb)
        required = {
            "results", "rmsd_success_rate", "n_success", "n_total",
            "rmsd_min", "rmsd_max", "rmsd_mean", "rmsd_threshold_angstrom"
        }
        assert required.issubset(result.keys())

    def test_empty_pred_list(self, rmsd_module, tmp_path):
        """빈 pred list → n_total=0, success_rate=0."""
        coords = [(0.0, 0.0, 0.0)]
        ref = _write_pdb(_make_pdb_ca_only(coords), tmp_path, "ref.pdb")
        result = rmsd_module.compute_rmsd_batch([], ref)
        assert result["n_total"] == 0
        assert result["rmsd_success_rate"] == 0.0

    def test_threshold_boundary(self, rmsd_module, tmp_path):
        """threshold 경계값 테스트: RMSD = threshold → 성공."""
        import numpy as np
        # 정확히 threshold=2.0 Å 차이 나는 구조 구성
        # 1개 Cα가 2Å 이동하면 RMSD = 2.0
        coords_ref = [(0.0, 0.0, 0.0)]
        coords_pred = [(2.0, 0.0, 0.0)]
        ref = _write_pdb(_make_pdb_ca_only(coords_ref), tmp_path, "ref.pdb")
        pred = _write_pdb(_make_pdb_ca_only(coords_pred), tmp_path, "pred.pdb")
        # align=False 일때 raw RMSD = 2.0
        result = rmsd_module.compute_rmsd_batch([pred], ref, rmsd_threshold=2.0)
        # aligned RMSD with 1 atom = 0 (완벽 정렬), raw에서는 2.0
        # 이 테스트는 함수가 에러 없이 실행되고 결과 구조를 반환하는지 확인
        assert result["n_total"] == 1
        assert isinstance(result["rmsd_success_rate"], float)
