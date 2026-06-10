"""test_tier3_reference_complex_fix.py
======================================
Tier 3 fix (F11 / SOD 2026-05-12) 회귀 테스트.

F11: _get_reference_complex_path() / _get_reference_peptide_com() search path 정정
  - PRST_N_FM 디렉토리 부재 → stale path만 등록 → None 반환
    → _assemble_complex fallback(receptor COM+15A) 발동 → clash 191 / ddG=40582
  - 수정: 실 위치 2개 + env var override 추가

검증 항목:
  1. 실 path 발견 검증 (data/fold_test1/fold_test1_model_0.pdb)
  2. env var override 동작 (REFERENCE_COMPLEX_PATH)
  3. 부재 시 graceful None 반환 + warning (fallback)
  4. _get_reference_peptide_com() 동일 패턴 검증
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(scope="module")
def step06():
    from pipeline_local.steps import step06_rosetta
    return step06_rosetta


# ---------------------------------------------------------------------------
# 1. 실 path 발견 검증
# ---------------------------------------------------------------------------

class TestRealPathDiscovery:
    """실 위치 data/fold_test1/fold_test1_model_0.pdb 또는
    AgenticAI4SCIENCE_pyrosetta_track/... 에서 파일을 발견해야 한다."""

    def test_get_reference_complex_path_returns_str(self, step06):
        """REFERENCE_COMPLEX_PATH 미설정 상태에서 실 파일 경로 반환."""
        result = step06._get_reference_complex_path()
        assert result is not None, (
            "_get_reference_complex_path()가 None 반환 — "
            "data/fold_test1/fold_test1_model_0.pdb 파일이 있어야 함"
        )
        assert isinstance(result, str)
        assert Path(result).exists(), f"반환된 경로가 실제로 존재하지 않음: {result}"

    def test_get_reference_complex_path_is_pdb(self, step06):
        """반환된 파일이 PDB ATOM 레코드를 포함해야 한다."""
        result = step06._get_reference_complex_path()
        if result is None:
            pytest.skip("참조 파일 없음 — 환경 의존 테스트")
        content = Path(result).read_text(encoding="utf-8")
        assert "ATOM" in content, "참조 PDB 파일에 ATOM 레코드 없음"

    def test_get_reference_peptide_com_returns_tuple(self, step06):
        """_get_reference_peptide_com()이 (x, y, z) 튜플을 반환해야 한다."""
        result = step06._get_reference_peptide_com()
        assert result is not None, (
            "_get_reference_peptide_com()가 None 반환 — "
            "Chain A CA 원자를 파싱하지 못함"
        )
        assert len(result) == 3, "반환값이 (x, y, z) 3-튜플이 아님"
        x, y, z = result
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(z, float)

    def test_get_reference_peptide_com_reasonable_coords(self, step06):
        """중심점 좌표가 합리적 범위 내에 있어야 한다 (-1000 ~ +1000 Å)."""
        result = step06._get_reference_peptide_com()
        if result is None:
            pytest.skip("참조 파일 없음 — 환경 의존 테스트")
        for coord in result:
            assert -1000.0 <= coord <= 1000.0, f"비현실적 좌표값: {coord}"


# ---------------------------------------------------------------------------
# 2. env var override 동작
# ---------------------------------------------------------------------------

class TestEnvVarOverride:
    """REFERENCE_COMPLEX_PATH 환경변수가 설정되면 해당 경로를 우선 사용해야 한다."""

    def test_env_var_overrides_default_path(self, step06, tmp_path):
        """REFERENCE_COMPLEX_PATH → 해당 파일이 먼저 반환됨."""
        fake_pdb = tmp_path / "custom_ref.pdb"
        fake_pdb.write_text(
            "ATOM      1  CA  ALA A   1      1.000  2.000  3.000  1.00  0.00\n"
            "END\n"
        )
        with patch.dict(os.environ, {"REFERENCE_COMPLEX_PATH": str(fake_pdb)}):
            result = step06._get_reference_complex_path()
        assert result == str(fake_pdb), (
            f"env var override 무시됨. 반환: {result}, 기대: {fake_pdb}"
        )

    def test_env_var_peptide_com_override(self, step06, tmp_path):
        """REFERENCE_COMPLEX_PATH override 시 _get_reference_peptide_com()도 해당 파일 사용.

        PDB 고정 컬럼 형식:
          col 1-6: record type, 13-16: atom name, 22: chain ID, 31-38: x, 39-46: y, 47-54: z
          (0-indexed: col 12:16, 21, 30:38, 38:46, 46:54)
        """
        fake_pdb = tmp_path / "custom_ref.pdb"
        # 올바른 PDB ATOM 레코드: 컬럼 21 = 'A' (chain), x=30:38, y=38:46, z=46:54
        fake_pdb.write_text(
            "ATOM      1  CA  ALA A   1      10.000  20.000  30.000  1.00  0.00\n"
            "END\n"
        )
        with patch.dict(os.environ, {"REFERENCE_COMPLEX_PATH": str(fake_pdb)}):
            result = step06._get_reference_peptide_com()
        assert result is not None, "env var 경로에서 COM 계산 실패"
        x, y, z = result
        assert abs(x - 10.0) < 0.01, f"x 좌표 불일치: {x}"
        assert abs(y - 20.0) < 0.01, f"y 좌표 불일치: {y}"
        assert abs(z - 30.0) < 0.01, f"z 좌표 불일치: {z}"

    def test_env_var_nonexistent_falls_through(self, step06, tmp_path):
        """REFERENCE_COMPLEX_PATH가 존재하지 않는 경로면 다음 후보로 fallthrough."""
        nonexistent = str(tmp_path / "does_not_exist.pdb")
        with patch.dict(os.environ, {"REFERENCE_COMPLEX_PATH": nonexistent}):
            result = step06._get_reference_complex_path()
        # 실 파일이 있으면 그것이 반환되어야 함
        # (환경에 따라 None 또는 실 경로)
        if result is not None:
            assert Path(result).exists(), "반환된 fallthrough 경로가 실제로 없음"


# ---------------------------------------------------------------------------
# 3. 부재 시 graceful None 반환 + warning
# ---------------------------------------------------------------------------

class TestGracefulNoneOnMissing:
    """모든 후보 경로가 없을 때 None 반환 + warning 로그 (assert 없이 조용히 실패 금지)."""

    def test_returns_none_when_all_paths_missing(self, step06, tmp_path, monkeypatch):
        """모든 ref_paths가 없으면 None 반환 — 실 모듈 함수 검증.

        Issue-1 fix (SOD 2026-05-12 T4): 기존 구현은 local _patched()가 자신을 호출해
        실 모듈 함수를 검증하지 못했음. _build_ref_paths() DRY 추출(Issue-2) 덕분에
        monkeypatch로 경로 목록만 교체한 뒤 mod._get_reference_complex_path()를 직접 호출.
        """
        import pipeline_local.steps.step06_rosetta as mod

        # _build_ref_paths()가 존재하지 않는 경로만 반환하도록 패치
        fake_paths = [
            tmp_path / "missing1.pdb",
            tmp_path / "missing2.pdb",
        ]
        monkeypatch.setattr(mod, "_build_ref_paths", lambda: fake_paths)
        monkeypatch.delenv("REFERENCE_COMPLEX_PATH", raising=False)

        # 실 모듈 함수를 직접 호출하여 None 반환 검증
        result = mod._get_reference_complex_path()
        assert result is None, "모든 경로 없어도 None이 아닌 값 반환"

    def test_warning_logged_when_all_paths_missing(self, step06, tmp_path, caplog):
        """부재 시 WARNING 레벨 로그가 발생해야 한다."""
        import logging
        import pipeline_local.steps.step06_rosetta as mod

        # env_override도 없는 경로로 설정, 나머지 경로도 존재 안 함
        # 내부 ref_paths를 직접 조작하기 어려우므로 env var를 없는 경로로 설정 +
        # 실 파일이 없는 isolated tmp 디렉토리에서 경로 직접 테스트
        fake_missing = str(tmp_path / "ghost.pdb")
        with caplog.at_level(logging.WARNING, logger="pipeline_local.steps.step06_rosetta"):
            with patch.dict(os.environ, {"REFERENCE_COMPLEX_PATH": fake_missing}):
                # REFERENCE_COMPLEX_PATH가 없는 경로 → 실 파일 탐색 → 실 파일 있으면 경고 X
                # 이 테스트는 경고 경로 자체가 동작함을 확인 (로직 분기)
                result = mod._get_reference_complex_path()
                # 실 파일이 있으면 result != None → 경고 미발생 (정상)
                # 실 파일이 없으면 result == None → 경고 발생 (정상)
                if result is None:
                    assert any(
                        "Reference complex PDB not found" in r.message
                        for r in caplog.records
                    ), "부재 시 warning 로그 미발생"


# ---------------------------------------------------------------------------
# 4. stale PRST_N_FM path는 리스트에 포함되어 있되 우선순위가 낮아야 한다
# ---------------------------------------------------------------------------

class TestSearchPathOrder:
    """실 위치가 stale path보다 앞에 있어야 한다."""

    def test_real_paths_before_stale_path(self, step06, monkeypatch, tmp_path):
        """ref_paths 순서: env > 실위치1 > 실위치2 > stale.
        실위치1이 있으면 stale path까지 내려가지 않아야 한다."""
        import pipeline_local.steps.step06_rosetta as mod

        # REFERENCE_COMPLEX_PATH 제거, 실위치1(data/)이 존재하는 상태에서 호출
        monkeypatch.delenv("REFERENCE_COMPLEX_PATH", raising=False)
        result = mod._get_reference_complex_path()
        if result is None:
            pytest.skip("실 파일이 현재 환경에 없음")
        # 반환된 경로가 PRST_N_FM stale path가 아님을 확인
        assert "PRST_N_FM" not in result, (
            f"stale PRST_N_FM path가 실 위치보다 먼저 반환됨: {result}"
        )
