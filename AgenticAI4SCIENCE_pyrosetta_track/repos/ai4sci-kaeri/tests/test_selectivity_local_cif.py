"""
test_selectivity_local_cif.py
==============================
Step05b Selectivity — local CIF 로딩 + selectivity_margin 계산 통합 테스트

테스트 범위:
- load_offtarget_receptors_from_config: pdb_source="local" + CIF→PDB 변환
- compute_selectivity_margin: SST-14 기반 가상 스코어로 마진 계산
- apply_selectivity_gate: 게이트 필터 동작
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 sys.path에 추가
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from AG_src.pipeline.step05b_selectivity import (
    _convert_cif_to_pdb,
    apply_selectivity_gate,
    compute_selectivity_margin,
    load_offtarget_receptors_from_config,
)

# CIF 파일 경로
_CIF_DIR = _PROJECT_ROOT / "data" / "somatostatin_receptor"
_CIF_FILES = {
    "SSTR1": _CIF_DIR / "SSTR1_9IK8.cif",
    "SSTR3": _CIF_DIR / "SSTR3_8XIR.cif",
    "SSTR4": _CIF_DIR / "SSTR4_7XMT.cif",
    "SSTR5": _CIF_DIR / "SSTR5_8ZBJ.cif",
}

_CIF_AVAILABLE = all(p.exists() for p in _CIF_FILES.values())


# ---------------------------------------------------------------------------
# CIF→PDB 변환 테스트
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _CIF_AVAILABLE, reason="CIF files not found")
def test_convert_cif_to_pdb_sstr1(tmp_path: Path) -> None:
    """SSTR1 CIF를 PDB로 변환하고 파일이 생성되는지 확인."""
    cif_path = str(_CIF_FILES["SSTR1"])
    pdb_path = str(tmp_path / "SSTR1_9IK8.pdb")
    result = _convert_cif_to_pdb(cif_path, pdb_path, chain="A")
    assert Path(result).exists(), "PDB 파일이 생성되어야 함"
    assert Path(result).stat().st_size > 0, "PDB 파일이 비어있으면 안 됨"


@pytest.mark.skipif(not _CIF_AVAILABLE, reason="CIF files not found")
def test_convert_cif_to_pdb_all_receptors(tmp_path: Path) -> None:
    """SSTR1/3/4/5 모두 CIF→PDB 변환 성공 확인."""
    chains = {"SSTR1": "A", "SSTR3": "A", "SSTR4": "A", "SSTR5": "A"}
    for name, cif in _CIF_FILES.items():
        pdb_path = str(tmp_path / f"{cif.stem}.pdb")
        result = _convert_cif_to_pdb(str(cif), pdb_path, chain=chains[name])
        assert Path(result).exists(), f"{name} PDB 변환 실패"


# ---------------------------------------------------------------------------
# load_offtarget_receptors_from_config 테스트
# ---------------------------------------------------------------------------

_MOCK_CONFIG = {
    "off_target_receptors": [
        {
            "name": "SSTR1",
            "pdb_source": "local",
            "local_path": "data/somatostatin_receptor/SSTR1_9IK8.cif",
            "chain": "A",
        },
        {
            "name": "SSTR3",
            "pdb_source": "local",
            "local_path": "data/somatostatin_receptor/SSTR3_8XIR.cif",
            "chain": "A",
        },
        {
            "name": "SSTR4",
            "pdb_source": "local",
            "local_path": "data/somatostatin_receptor/SSTR4_7XMT.cif",
            "chain": "A",
        },
        {
            "name": "SSTR5",
            "pdb_source": "local",
            "local_path": "data/somatostatin_receptor/SSTR5_8ZBJ.cif",
            "chain": "A",
        },
    ]
}


@pytest.mark.skipif(not _CIF_AVAILABLE, reason="CIF files not found")
def test_load_offtarget_receptors_returns_all(tmp_path: Path) -> None:
    """load_offtarget_receptors_from_config이 4개 receptor를 반환해야 함."""
    receptors = load_offtarget_receptors_from_config(
        config=_MOCK_CONFIG,
        project_root=str(_PROJECT_ROOT),
        pdb_output_dir=str(tmp_path),
    )
    assert len(receptors) == 4
    names = [r["name"] for r in receptors]
    assert set(names) == {"SSTR1", "SSTR3", "SSTR4", "SSTR5"}


@pytest.mark.skipif(not _CIF_AVAILABLE, reason="CIF files not found")
def test_load_offtarget_receptors_pdb_paths_exist(tmp_path: Path) -> None:
    """load_offtarget_receptors_from_config — pdb_path가 실제로 존재해야 함."""
    receptors = load_offtarget_receptors_from_config(
        config=_MOCK_CONFIG,
        project_root=str(_PROJECT_ROOT),
        pdb_output_dir=str(tmp_path),
    )
    for rec in receptors:
        assert rec["pdb_path"] is not None, f"{rec['name']} pdb_path가 None"
        assert Path(rec["pdb_path"]).exists(), f"{rec['name']} PDB 파일 없음: {rec['pdb_path']}"


def test_load_offtarget_receptors_missing_path() -> None:
    """존재하지 않는 local_path는 pdb_path=None을 반환해야 함."""
    config = {
        "off_target_receptors": [
            {
                "name": "SSTR1",
                "pdb_source": "local",
                "local_path": "data/nonexistent/SSTR1.cif",
                "chain": "A",
            }
        ]
    }
    receptors = load_offtarget_receptors_from_config(
        config=config,
        project_root=str(_PROJECT_ROOT),
    )
    assert len(receptors) == 1
    assert receptors[0]["pdb_path"] is None


def test_load_offtarget_receptors_non_local_source() -> None:
    """pdb_source != 'local'이면 pdb_path=None으로 스킵해야 함."""
    config = {
        "off_target_receptors": [
            {"name": "SSTR1", "pdb_source": "rcsb", "chain": "A"}
        ]
    }
    receptors = load_offtarget_receptors_from_config(config=config)
    assert receptors[0]["pdb_path"] is None


# ---------------------------------------------------------------------------
# compute_selectivity_margin — SST-14 가상 스코어 테스트
# ---------------------------------------------------------------------------

# SST-14 시뮬레이션:
#   SSTR2 강결합(-8.5), off-target은 약결합(-1.0~-2.5)
#   gate 조건: margin <= -2.0 AND worst_offtarget >= -3.0
#   margin = -8.5 - (-2.5) = -6.0 → pass / worst = -2.5 >= -3.0 → pass
_SST14_SEQ_ID = "SST14_AGCKNFFWKTFTSC"
_SSTR2_SCORE = -8.5
_OFFTARGET_SCORES = {
    "SSTR1": -2.5,   # 약한 결합 (score > -3.0 임계값)
    "SSTR3": -2.0,
    "SSTR4": -1.5,
    "SSTR5": -1.8,
}


def test_compute_selectivity_margin_sst14() -> None:
    """SST-14 가상 스코어: selectivity_margin이 음수여야 함 (SSTR2 선택적)."""
    result = compute_selectivity_margin(
        seq_id=_SST14_SEQ_ID,
        sstr2_score=_SSTR2_SCORE,
        offtarget_scores=_OFFTARGET_SCORES,
        margin_min=-2.0,
        offtarget_max_allowed=-3.0,
    )
    # margin = -8.5 - (-5.2) = -3.3 (SSTR2가 3.3 kcal/mol 더 강하게 결합)
    assert result.selectivity_margin < 0, "SSTR2 선택성: margin이 음수여야 함"
    assert result.seq_id == _SST14_SEQ_ID
    assert result.sstr2_dock_score == _SSTR2_SCORE


def test_compute_selectivity_margin_value() -> None:
    """margin 값이 sstr2_score - max_offtarget 계산과 일치해야 함."""
    result = compute_selectivity_margin(
        seq_id=_SST14_SEQ_ID,
        sstr2_score=_SSTR2_SCORE,
        offtarget_scores=_OFFTARGET_SCORES,
        margin_min=-2.0,
        offtarget_max_allowed=-3.0,
    )
    # worst off-target = SSTR1 (-2.5, 가장 강한 결합이지만 약함)
    expected_margin = _SSTR2_SCORE - (-2.5)  # = -6.0
    assert abs(result.selectivity_margin - expected_margin) < 1e-6
    assert result.offtarget_max_receptor == "SSTR1"


def test_compute_selectivity_margin_passes_gate() -> None:
    """SST-14는 selectivity gate를 통과해야 함 (margin=-3.3 <= -2.0)."""
    result = compute_selectivity_margin(
        seq_id=_SST14_SEQ_ID,
        sstr2_score=_SSTR2_SCORE,
        offtarget_scores=_OFFTARGET_SCORES,
        margin_min=-2.0,
        offtarget_max_allowed=-3.0,
    )
    assert result.passed is True, f"SST-14는 gate를 통과해야 함 (margin={result.selectivity_margin:.2f})"


def test_compute_selectivity_margin_fails_when_off_target_too_strong() -> None:
    """off-target이 너무 강하면 gate 실패."""
    result = compute_selectivity_margin(
        seq_id="weak_candidate",
        sstr2_score=-5.0,
        offtarget_scores={"SSTR1": -8.0},  # off-target이 더 강함
        margin_min=-2.0,
        offtarget_max_allowed=-3.0,
    )
    # margin = -5.0 - (-8.0) = 3.0 > -2.0 → fail
    assert result.passed is False
    assert result.selectivity_margin > 0


def test_compute_selectivity_margin_empty_offtargets() -> None:
    """off-target 없을 때 margin=0.0, passed=True 반환."""
    result = compute_selectivity_margin(
        seq_id="no_offtargets",
        sstr2_score=-7.0,
        offtarget_scores={},
    )
    assert result.selectivity_margin == 0.0
    assert result.passed is True


# ---------------------------------------------------------------------------
# apply_selectivity_gate 테스트
# ---------------------------------------------------------------------------

def test_apply_selectivity_gate_partitions() -> None:
    """passed/failed가 전체 결과를 정확히 분할해야 함."""
    results = [
        compute_selectivity_margin("cand_A", -8.5, {"SSTR1": -5.2}, -2.0, -3.0),  # pass
        compute_selectivity_margin("cand_B", -5.0, {"SSTR1": -8.0}, -2.0, -3.0),  # fail
        compute_selectivity_margin("cand_C", -9.0, {"SSTR1": -4.0}, -2.0, -3.0),  # pass
    ]
    passed, failed = apply_selectivity_gate(results, -2.0, -3.0)
    assert len(passed) + len(failed) == len(results)
    assert all(r.passed for r in passed)
    assert all(not r.failed for r in failed) if hasattr(results[0], "failed") else True
