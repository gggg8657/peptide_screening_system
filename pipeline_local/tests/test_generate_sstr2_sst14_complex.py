"""
test_generate_sstr2_sst14_complex.py
=====================================
Task #38 — generate_sstr2_sst14_complex.py 단위 테스트

순수 계산 함수(geometry, 파싱 유틸)는 실제 파일 없이 테스트.
Boltz CLI 호출 함수는 subprocess mock으로 격리.
"""
from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# 테스트 대상 모듈
from pipeline_local.scripts.generate_sstr2_sst14_complex import (
    _dist3d,
    _parse_atom_coords,
    _parse_model_index,
    check_pocket_placement,
    check_ss_bond,
    parse_results,
    SST14_SEQUENCE,
    IPTM_THRESHOLD,
    SS_BOND_MAX_DIST,
    CYS3_POS,
    CYS14_POS,
)


# ---------------------------------------------------------------------------
# 헬퍼: 미니멀 PDB 생성
# ---------------------------------------------------------------------------

def _make_minimal_pdb(
    atoms: list[dict[str, Any]],
) -> str:
    """atoms 목록으로 PDB 문자열 생성.
    각 dict: {chain, resnum, resname, atom_name, x, y, z}
    """
    lines = []
    for i, a in enumerate(atoms, start=1):
        line = (
            f"ATOM  {i:5d} {a['atom_name']:4s} {a['resname']:3s} {a['chain']}"
            f"{a['resnum']:4d}    "
            f"{a['x']:8.3f}{a['y']:8.3f}{a['z']:8.3f}"
            f"  1.00  0.00\n"
        )
        lines.append(line)
    lines.append("END\n")
    return "".join(lines)


# ---------------------------------------------------------------------------
# _dist3d
# ---------------------------------------------------------------------------

class TestDist3d:
    def test_zero(self):
        assert _dist3d((0, 0, 0), (0, 0, 0)) == pytest.approx(0.0)

    def test_unit_x(self):
        assert _dist3d((0, 0, 0), (1, 0, 0)) == pytest.approx(1.0)

    def test_3d(self):
        assert _dist3d((1, 2, 3), (4, 6, 3)) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# _parse_atom_coords
# ---------------------------------------------------------------------------

class TestParseAtomCoords:
    def test_single_atom(self, tmp_path: Path):
        pdb = _make_minimal_pdb([
            {"chain": "A", "resnum": 3, "resname": "CYS", "atom_name": "SG",
             "x": 1.0, "y": 2.0, "z": 3.0},
        ])
        pdb_path = tmp_path / "test.pdb"
        pdb_path.write_text(pdb)
        coords = _parse_atom_coords(pdb_path)
        assert ("A", 3, "SG") in coords
        assert coords[("A", 3, "SG")] == pytest.approx((1.0, 2.0, 3.0))

    def test_multiple_atoms(self, tmp_path: Path):
        pdb = _make_minimal_pdb([
            {"chain": "A", "resnum": 3, "resname": "CYS", "atom_name": "SG",
             "x": 1.0, "y": 0.0, "z": 0.0},
            {"chain": "A", "resnum": 14, "resname": "CYS", "atom_name": "SG",
             "x": 3.0, "y": 0.0, "z": 0.0},
        ])
        pdb_path = tmp_path / "test.pdb"
        pdb_path.write_text(pdb)
        coords = _parse_atom_coords(pdb_path)
        assert len(coords) == 2

    def test_empty_pdb(self, tmp_path: Path):
        pdb_path = tmp_path / "empty.pdb"
        pdb_path.write_text("END\n")
        coords = _parse_atom_coords(pdb_path)
        assert coords == {}


# ---------------------------------------------------------------------------
# check_ss_bond
# ---------------------------------------------------------------------------

class TestCheckSsBond:
    def test_valid_ss_bond(self, tmp_path: Path):
        """SG-SG 거리 2.04 Å — 유효한 SS bond."""
        pdb = _make_minimal_pdb([
            {"chain": "A", "resnum": CYS3_POS, "resname": "CYS", "atom_name": "SG",
             "x": 0.0, "y": 0.0, "z": 0.0},
            {"chain": "A", "resnum": CYS14_POS, "resname": "CYS", "atom_name": "SG",
             "x": 2.04, "y": 0.0, "z": 0.0},
        ])
        pdb_path = tmp_path / "ssbond.pdb"
        pdb_path.write_text(pdb)
        result = check_ss_bond(pdb_path)
        assert result["ok"] is True
        assert result["sg3_sg14_dist"] == pytest.approx(2.04, abs=0.01)

    def test_invalid_ss_bond_too_far(self, tmp_path: Path):
        """SG-SG 거리 5.0 Å — SS bond 파괴."""
        pdb = _make_minimal_pdb([
            {"chain": "A", "resnum": CYS3_POS, "resname": "CYS", "atom_name": "SG",
             "x": 0.0, "y": 0.0, "z": 0.0},
            {"chain": "A", "resnum": CYS14_POS, "resname": "CYS", "atom_name": "SG",
             "x": 5.0, "y": 0.0, "z": 0.0},
        ])
        pdb_path = tmp_path / "broken_ss.pdb"
        pdb_path.write_text(pdb)
        result = check_ss_bond(pdb_path)
        assert result["ok"] is False
        assert result["sg3_sg14_dist"] == pytest.approx(5.0, abs=0.01)

    def test_missing_cys_atom(self, tmp_path: Path):
        """Cys14 SG 없음 — ok=False."""
        pdb = _make_minimal_pdb([
            {"chain": "A", "resnum": CYS3_POS, "resname": "CYS", "atom_name": "SG",
             "x": 0.0, "y": 0.0, "z": 0.0},
        ])
        pdb_path = tmp_path / "missing.pdb"
        pdb_path.write_text(pdb)
        result = check_ss_bond(pdb_path)
        assert result["ok"] is False
        assert result["sg3_sg14_dist"] is None


# ---------------------------------------------------------------------------
# check_pocket_placement
# ---------------------------------------------------------------------------

class TestCheckPocketPlacement:
    def _make_pocket_json(self, tmp_path: Path, center: tuple, radius: float) -> Path:
        data = {
            "center_x": center[0],
            "center_y": center[1],
            "center_z": center[2],
            "radius": radius,
            "residues": [],
        }
        p = tmp_path / "pocket.json"
        p.write_text(json.dumps(data))
        return p

    def test_inside_pocket(self, tmp_path: Path):
        """펩타이드 centroid가 pocket 내부 — ok=True."""
        # center를 (0,0,0)이 아닌 명시적 위치로 설정 (fallback 트리거 방지)
        pocket_json = self._make_pocket_json(tmp_path, center=(5.0, 5.0, 5.0), radius=10.0)
        # CA 원자 5개 centroid = (7, 7, 7) → center에서 거리 = sqrt(12) ≈ 3.46 < 10
        pdb = _make_minimal_pdb([
            {"chain": "A", "resnum": i, "resname": "ALA", "atom_name": "CA",
             "x": 7.0, "y": 7.0, "z": 7.0}
            for i in range(1, 6)
        ])
        pdb_path = tmp_path / "inside.pdb"
        pdb_path.write_text(pdb)
        result = check_pocket_placement(pdb_path, pocket_json)
        assert result["ok"] is True
        assert result["dist"] == pytest.approx(math.sqrt(12), abs=0.01)

    def test_outside_pocket(self, tmp_path: Path):
        """펩타이드 centroid가 pocket 외부 — ok=False."""
        pocket_json = self._make_pocket_json(tmp_path, center=(5.0, 5.0, 5.0), radius=5.0)
        pdb = _make_minimal_pdb([
            {"chain": "A", "resnum": i, "resname": "ALA", "atom_name": "CA",
             "x": 20.0, "y": 20.0, "z": 20.0}
            for i in range(1, 6)
        ])
        pdb_path = tmp_path / "outside.pdb"
        pdb_path.write_text(pdb)
        result = check_pocket_placement(pdb_path, pocket_json)
        assert result["ok"] is False

    def test_missing_pocket_json(self, tmp_path: Path):
        """pocket JSON 없음 — ok=False."""
        pdb = _make_minimal_pdb([
            {"chain": "A", "resnum": 1, "resname": "ALA", "atom_name": "CA",
             "x": 0.0, "y": 0.0, "z": 0.0},
        ])
        pdb_path = tmp_path / "test.pdb"
        pdb_path.write_text(pdb)
        missing_json = tmp_path / "nonexistent.json"
        result = check_pocket_placement(pdb_path, missing_json)
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# _parse_model_index
# ---------------------------------------------------------------------------

class TestParseModelIndex:
    def test_standard_pdb(self):
        p = Path("SSTR2_SST14_complex_model_2.pdb")
        assert _parse_model_index(p) == 2

    def test_confidence_json(self):
        p = Path("confidence_SSTR2_SST14_complex_model_0.json")
        assert _parse_model_index(p) == 0

    def test_no_model_in_name(self):
        p = Path("random_file.pdb")
        assert _parse_model_index(p) == 0


# ---------------------------------------------------------------------------
# parse_results (mock filesystem)
# ---------------------------------------------------------------------------

class TestParseResults:
    def _make_confidence_json(self, path: Path, iptm: float, ptm: float) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({"iptm": iptm, "ptm": ptm, "confidence_score": iptm * 0.9}, f)

    def _make_pdb(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ATOM  1  CA  ALA A   1  0.0  0.0  0.0  1.00  0.00\nEND\n")

    def test_parse_multiple_models(self, tmp_path: Path):
        """3개 모델 결과 파싱 + iPTM 내림차순 정렬."""
        yaml_stem = "SSTR2_SST14_complex"
        pred_dir = tmp_path / f"boltz_results_{yaml_stem}" / "predictions" / yaml_stem

        for model_idx, iptm in [(0, 0.85), (1, 0.92), (2, 0.78)]:
            self._make_confidence_json(
                pred_dir / f"confidence_{yaml_stem}_model_{model_idx}.json",
                iptm=iptm,
                ptm=0.8,
            )
            self._make_pdb(pred_dir / f"{yaml_stem}_model_{model_idx}.pdb")

        results = parse_results(tmp_path, yaml_stem)
        assert len(results) == 3
        # iPTM 내림차순
        assert results[0]["iptm"] == pytest.approx(0.92)
        assert results[1]["iptm"] == pytest.approx(0.85)
        assert results[2]["iptm"] == pytest.approx(0.78)

    def test_empty_output_dir(self, tmp_path: Path):
        """결과 파일 없음 — 빈 리스트 반환."""
        results = parse_results(tmp_path, "SSTR2_SST14_complex")
        assert results == []


# ---------------------------------------------------------------------------
# 상수 검증
# ---------------------------------------------------------------------------

class TestConstants:
    def test_sst14_sequence(self):
        assert SST14_SEQUENCE == "AGCKNFFWKTFTSC"
        assert len(SST14_SEQUENCE) == 14

    def test_cys_positions(self):
        """SST-14에서 Cys 위치 확인 (1-indexed)."""
        assert SST14_SEQUENCE[CYS3_POS - 1] == "C"
        assert SST14_SEQUENCE[CYS14_POS - 1] == "C"

    def test_iptm_threshold(self):
        assert IPTM_THRESHOLD == 0.7

    def test_ss_bond_threshold(self):
        assert SS_BOND_MAX_DIST <= 2.5  # 이상적 SS bond < 2.1 Å, 허용 < 2.5 Å
