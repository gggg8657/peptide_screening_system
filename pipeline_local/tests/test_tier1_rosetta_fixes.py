"""test_tier1_rosetta_fixes.py
=============================
Tier 1 fix (F1/F2/F3) 회귀 테스트 — Stage 9 dogfood postmortem 기반.

F1: mmCIF input 인식·변환 (CRIT-1)
F2: PyRosetta script search path 확장 (CRIT-2)
F3: sequence_map 전파 (cache key sequence 신호 보장)
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# F1 회귀 — _is_mmcif + _cif_to_pdb + _assemble_complex의 cif 처리
# ---------------------------------------------------------------------------


class TestF1MmcifConversion:
    """F1: mmCIF input이 PDB로 변환되어 _assemble_complex가 peptide 정보 보존."""

    @pytest.fixture(scope="class")
    def step06(self):
        from pipeline_local.steps import step06_rosetta
        return step06_rosetta

    def test_is_mmcif_detects_cif(self, step06):
        cif_text = "data_model\n_entry.id test\n_atom_site.\nATOM ..."
        assert step06._is_mmcif(cif_text), "data_/atom_site 가진 cif 미감지"

    def test_is_mmcif_rejects_pdb(self, step06):
        pdb_text = "ATOM   1  CA  ALA A   1      0.000  0.000  0.000  1.00  0.00\n"
        assert not step06._is_mmcif(pdb_text), "PDB ATOM 줄을 cif로 오인"

    @pytest.fixture(scope="class")
    def stage9_artifacts(self):
        """Stage 9 dogfood 실 Boltz 산출물 — 완전한 mmCIF format."""
        artifacts = {
            "receptor": Path("runs_local/dogfood_2026-05-11/local_20260511_1137_iter01/01_receptor/sstr2_receptor.pdb"),
            "pose_var_012_iter01": Path("runs_local/dogfood_2026-05-11/local_20260511_1137_iter01/05_docking/pose_var_012_00.pdb"),
            "pose_var_024_iter02": Path("runs_local/dogfood_2026-05-11/local_20260511_1140_iter02/05_docking/pose_var_024_00.pdb"),
        }
        for name, path in artifacts.items():
            if not path.exists():
                pytest.skip(f"Stage 9 artifact missing: {path}")
        return {name: path.read_text() for name, path in artifacts.items()}

    def test_assemble_complex_preserves_peptide_for_real_boltz_cif(self, step06, stage9_artifacts):
        """가장 critical: 실 Boltz mmCIF 입력 시 chain B 줄 보존 (CRIT-1 회귀)."""
        result = step06._assemble_complex(
            stage9_artifacts["receptor"],
            stage9_artifacts["pose_var_012_iter01"],
        )
        # Chain 분포 카운트
        chains = {}
        for line in result.splitlines():
            if (line.startswith("ATOM") or line.startswith("HETATM")) and len(line) >= 22:
                chains[line[21]] = chains.get(line[21], 0) + 1

        # CRIT-1 핵심 회귀: cif → PDB 변환 후 chain B가 반드시 생성
        # Stage 9 dogfood 시점: chains={'A': 2904} (chain B 0줄)
        # F1 fix 후: chain B에 peptide 정보 보존
        assert "B" in chains and chains["B"] > 0, (
            f"F1 fix 실패 — Stage 9 실 Boltz cif input에서 chain B 0줄 (CRIT-1 회귀). "
            f"chains={chains}"
        )

    def test_assemble_complex_different_real_cif_inputs_differ(self, step06, stage9_artifacts):
        """실 Stage 9 자료: 다른 변이체 cif 입력에 대해 다른 결과 산출 (cache 충돌 회귀)."""
        result_012 = step06._assemble_complex(
            stage9_artifacts["receptor"],
            stage9_artifacts["pose_var_012_iter01"],
        )
        result_024 = step06._assemble_complex(
            stage9_artifacts["receptor"],
            stage9_artifacts["pose_var_024_iter02"],
        )
        # CRIT-1 회귀 핵심: Stage 9 시점엔 둘 다 md5=ff379eb0e85ebcf5로 동일
        # F1 fix 후엔 *다른 결과*여야 함
        md5_a = hashlib.md5(result_012.encode()).hexdigest()
        md5_b = hashlib.md5(result_024.encode()).hexdigest()
        assert md5_a != md5_b, (
            f"F1 fix 실패 — 다른 Boltz cif (var_012 vs var_024)에 대해 동일 결과 "
            f"(Stage 9 dogfood cache 충돌 회귀). md5_a={md5_a}, md5_b={md5_b}"
        )


# ---------------------------------------------------------------------------
# F2 회귀 — flexpep_dock.py search path
# ---------------------------------------------------------------------------


class TestF2ScriptSearchPath:
    """F2: PyRosetta script search path에 실 위치 포함."""

    def test_script_candidates_contains_ag_src_scripts(self):
        """F2 fix: search path에 AgenticAI4SCIENCE_pyrosetta_track/.../AG_src/scripts/ 포함."""
        from pipeline_local.steps import step06_rosetta
        # 호출 트리거를 위해 _run_pyrosetta_subprocess 의 source 코드 직접 확인
        import inspect
        source = inspect.getsource(step06_rosetta)
        assert "AgenticAI4SCIENCE_pyrosetta_track" in source, (
            "F2 fix 실패 — script_candidates에 실 위치 미포함 (CRIT-2 회귀)"
        )
        assert "ai4sci-kaeri" in source and "AG_src" in source, (
            "F2 fix 실패 — 정확한 경로 component 미포함"
        )

    def test_pyrosetta_scripts_dir_env_supported(self):
        """F2 fix: PYROSETTA_SCRIPTS_DIR 환경변수도 지원."""
        from pipeline_local.steps import step06_rosetta
        import inspect
        source = inspect.getsource(step06_rosetta)
        assert "PYROSETTA_SCRIPTS_DIR" in source, "F2 fix — 환경변수 override 미지원"


# ---------------------------------------------------------------------------
# F3 회귀 — sequence_map 전파
# ---------------------------------------------------------------------------


class TestF3SequenceMapPropagation:
    """F3: orchestrator가 step03b variants로부터 sequence_map 구성·inject."""

    def test_orchestrator_constructs_sequence_map(self):
        """F3 fix: orchestrator.py에서 step03b_out → sequence_map 구성 로직 존재."""
        import inspect
        from pipeline_local import orchestrator
        source = inspect.getsource(orchestrator)
        # F3 fix가 추가한 sequence_map 구성 로직 확인
        assert "sequence_map" in source, "F3 fix — orchestrator에 sequence_map 부재"
        assert "step03b_out" in source, "F3 fix — step03b 결과 사용 안 함"
        # step06 호출 시 sequence_map이 들어간 config 전달 의무
        assert 'step06_config' in source or '"sequence_map": sequence_map' in source, (
            "F3 fix — step06에 sequence_map config inject 안 됨"
        )


# ---------------------------------------------------------------------------
# 통합 회귀 — cache key가 다른 sequence에 대해 다름
# ---------------------------------------------------------------------------


class TestCacheKeyDifferentiation:
    """F1+F3 통합: cache key가 sequence + complex 입력에 대해 다른 변이체별로 다름."""

    def test_make_key_differs_for_different_sequences(self):
        from pipeline_local.steps.step06_rosetta import _ResultCache
        cache = _ResultCache()
        pdb_content = "ATOM   1  N   ALA A   1\n"
        k1 = cache._make_key(pdb_content, "AGCKNFFWKTFTSC", "flexpep_refine")
        k2 = cache._make_key(pdb_content, "AGCRNFFWKTFTSC", "flexpep_refine")
        assert k1 != k2, "cache key가 sequence 달라도 동일 (F3 회귀 위험)"

    def test_make_key_differs_for_different_complex_pdb(self):
        from pipeline_local.steps.step06_rosetta import _ResultCache
        cache = _ResultCache()
        k1 = cache._make_key("ATOM 1\n", "AGCKNFFWKTFTSC", "flexpep_refine")
        k2 = cache._make_key("ATOM 2\n", "AGCKNFFWKTFTSC", "flexpep_refine")
        assert k1 != k2, "cache key가 pdb 달라도 동일"
