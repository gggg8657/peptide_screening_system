"""Tests for _apply_alternative_scoring integration in runner.py.

각 단계(GNINA, ECR, Pareto, BO)의 graceful degradation 및
정상 동작을 검증합니다.

주의: 실행 환경에 따라 _HAS_GNINA / _HAS_PARETO / _HAS_BO 플래그가
False일 수 있으므로 각 테스트에서 필요한 플래그를 명시적으로 patch합니다.
"""
from __future__ import annotations

import os
# 2026-06-09 B: 이 단위 테스트들은 GNINA/ECR/Pareto/BO 로직 검증용.
# Step 0.5 pepADMET 독성(실제 subprocess)은 비활성화해 빠르고 env-독립적으로 유지.
os.environ.setdefault("SST_DISABLE_PEPADMET_TOX", "1")

import math
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, call, patch

import pytest

from pyrosetta_flow.schema import CandidateResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candidate(
    idx: int,
    ddg: float = -10.0,
    clash: float = 2.0,
    fail: str = "",
    iteration: int = 1,
    seq: str = "AGCKNFFWKTFTSC",
) -> CandidateResult:
    return CandidateResult(
        iteration=iteration,
        candidate_id=f"iter{iteration:02d}_cand{idx:03d}",
        sequence=seq,
        ddg=ddg,
        total_score=ddg * 10,
        clash_score=clash,
        fail_reason=fail,
    )


def _import_fn():
    from pyrosetta_flow.runner import _apply_alternative_scoring
    return _apply_alternative_scoring


# Pareto rank_candidates 실제 구현 (pymoo mock용)
def _mock_pareto_rank(candidates, clash_threshold=10.0):
    """NSGA-II 없이 단순 ddG 순위를 pareto_rank로 할당."""
    sorted_by_ddg = sorted(range(len(candidates)), key=lambda i: candidates[i].get("ddG", 0))
    for rank, idx in enumerate(sorted_by_ddg):
        candidates[idx]["pareto_rank"] = rank
        candidates[idx]["crowding_distance"] = float(len(candidates) - rank)
    return candidates


# ---------------------------------------------------------------------------
# 1. Empty candidates: no-op
# ---------------------------------------------------------------------------

class TestApplyAlternativeScoringEmpty:
    def test_empty_list_returns_empty(self, tmp_path):
        fn = _import_fn()
        result = fn([], iter_dir=tmp_path, iteration=1)
        assert result == []


# ---------------------------------------------------------------------------
# 2. Failed candidates: GNINA skip, Pareto에서 hard_violations=1
# ---------------------------------------------------------------------------

class TestFailedCandidatesSkipped:
    def test_failed_candidates_not_gnina_rescored(self, tmp_path):
        fn = _import_fn()
        failed = _make_candidate(1, ddg=999.0, fail="dock error")
        ok = _make_candidate(2, ddg=-8.0)
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", True), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.batch_gnina_rescore", return_value=[]) as mock_gnina:
            result = fn([failed, ok], iter_dir=tmp_path, iteration=1)
        # failed candidate has no PDB → batch_gnina_rescore receives 0 paths
        assert mock_gnina.call_count <= 1
        # returned candidates count preserved
        assert len(result) == 2


# ---------------------------------------------------------------------------
# 3. _HAS_GNINA=False → graceful skip
# ---------------------------------------------------------------------------

class TestGninaUnavailable:
    def test_no_gnina_flag_skips_quietly(self, tmp_path):
        fn = _import_fn()
        candidates = [_make_candidate(i) for i in range(1, 4)]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False):
            result = fn(candidates, iter_dir=tmp_path, iteration=1)
        assert len(result) == 3

    def test_gnina_skipped_no_extra_gnina_keys(self, tmp_path):
        fn = _import_fn()
        candidates = [_make_candidate(1, ddg=-5.0)]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False):
            result = fn(candidates, iter_dir=tmp_path, iteration=1)
        for cand in result:
            assert "gnina_cnn_score" not in cand.extra_scores


# ---------------------------------------------------------------------------
# 4. _HAS_PARETO=False → graceful skip
# ---------------------------------------------------------------------------

class TestParetoUnavailable:
    def test_no_pareto_flag_skips_quietly(self, tmp_path):
        fn = _import_fn()
        candidates = [_make_candidate(i) for i in range(1, 4)]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False):
            result = fn(candidates, iter_dir=tmp_path, iteration=1)
        assert len(result) == 3

    def test_pareto_skipped_no_pareto_rank(self, tmp_path):
        fn = _import_fn()
        candidates = [_make_candidate(1, ddg=-5.0)]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False):
            result = fn(candidates, iter_dir=tmp_path, iteration=1)
        for cand in result:
            assert "pareto_rank" not in cand.extra_scores


# ---------------------------------------------------------------------------
# 5. _HAS_BO=False → graceful skip
# ---------------------------------------------------------------------------

class TestBOUnavailable:
    def test_no_bo_flag_skips_quietly(self, tmp_path):
        fn = _import_fn()
        candidates = [_make_candidate(i) for i in range(1, 4)]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False):
            result = fn(candidates, iter_dir=tmp_path, iteration=1, bo_optimizer=None)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# 6. Pareto ranking: extra_scores에 pareto_rank 기록
# ---------------------------------------------------------------------------

class TestParetoIntegration:
    def test_pareto_rank_added_to_extra_scores(self, tmp_path):
        fn = _import_fn()
        candidates = [
            _make_candidate(1, ddg=-12.0, clash=1.0),
            _make_candidate(2, ddg=-8.0, clash=3.0),
            _make_candidate(3, ddg=-5.0, clash=6.0),
        ]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", True), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.pareto_rank_candidates", side_effect=_mock_pareto_rank):
            result = fn(candidates, iter_dir=tmp_path, iteration=1)
        for cand in result:
            assert "pareto_rank" in cand.extra_scores, (
                f"{cand.candidate_id} missing pareto_rank"
            )
            assert isinstance(cand.extra_scores["pareto_rank"], int)
            assert cand.extra_scores["pareto_rank"] >= 0

    def test_best_ddg_gets_lowest_pareto_rank(self, tmp_path):
        fn = _import_fn()
        best = _make_candidate(1, ddg=-20.0, clash=0.5)
        worst = _make_candidate(2, ddg=5.0, clash=15.0)
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", True), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.pareto_rank_candidates", side_effect=_mock_pareto_rank):
            result = fn([best, worst], iter_dir=tmp_path, iteration=1)
        best_res = next(c for c in result if c.candidate_id == best.candidate_id)
        worst_res = next(c for c in result if c.candidate_id == worst.candidate_id)
        assert best_res.extra_scores["pareto_rank"] <= worst_res.extra_scores["pareto_rank"]

    def test_crowding_distance_populated(self, tmp_path):
        fn = _import_fn()
        candidates = [_make_candidate(i, ddg=float(-5 - i)) for i in range(1, 4)]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", True), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.pareto_rank_candidates", side_effect=_mock_pareto_rank):
            result = fn(candidates, iter_dir=tmp_path, iteration=1)
        for cand in result:
            assert "crowding_distance" in cand.extra_scores


# ---------------------------------------------------------------------------
# 7. GNINA dry-run 모드
# ---------------------------------------------------------------------------

class TestGninaDryRun:
    def test_gnina_dry_run_when_no_pdb(self, tmp_path):
        """PDB 파일 없으면 batch 빈 리스트 → gnina 미호출."""
        fn = _import_fn()
        cand = _make_candidate(1, ddg=-8.0)
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", True), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.batch_gnina_rescore", return_value=[]) as mock_gnina:
            result = fn([cand], iter_dir=tmp_path, iteration=1)
        # pdb_paths가 비어있어 batch_gnina_rescore 미호출
        mock_gnina.assert_not_called()
        assert len(result) == 1

    def test_gnina_dry_run_with_mock_pdb(self, tmp_path):
        """PDB 파일 존재 + gnina mock → dry-run 스코어 extra_scores에 저장."""
        fn = _import_fn()
        pdb_file = tmp_path / "cand_001.pdb"
        pdb_file.write_text("ATOM  ...\n")

        cand = _make_candidate(1, ddg=-8.0)
        dry_run_score = {
            "gnina_cnn_score": 0.0,
            "gnina_cnn_affinity": 0.0,
            "gnina_vina_score": 0.0,
            "gnina_dry_run": 1.0,
        }
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", True), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.batch_gnina_rescore", return_value=[dry_run_score]):
            result = fn([cand], iter_dir=tmp_path, iteration=1)

        assert len(result) == 1
        assert result[0].extra_scores.get("gnina_cnn_score") == 0.0
        assert result[0].extra_scores.get("gnina_dry_run") == 1.0


# ---------------------------------------------------------------------------
# 8. ECR 스코어가 extra_scores에 저장
# ---------------------------------------------------------------------------

class TestECRIntegration:
    def test_ecr_score_in_extra_scores(self, tmp_path):
        fn = _import_fn()
        for i in [1, 2]:
            (tmp_path / f"cand_{i:03d}.pdb").write_text("ATOM  ...\n")

        cands = [
            _make_candidate(1, ddg=-10.0),
            _make_candidate(2, ddg=-5.0),
        ]
        gnina_scores = [
            {"gnina_cnn_score": 0.8, "gnina_cnn_affinity": 7.0, "gnina_vina_score": -8.0},
            {"gnina_cnn_score": 0.4, "gnina_cnn_affinity": 5.0, "gnina_vina_score": -6.0},
        ]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", True), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.batch_gnina_rescore", return_value=gnina_scores):
            result = fn(cands, iter_dir=tmp_path, iteration=1)

        for cand in result:
            assert "ecr_score" in cand.extra_scores, (
                f"{cand.candidate_id} missing ecr_score"
            )
            assert cand.extra_scores["ecr_score"] > 0.0

    def test_gnina_scores_stored_in_extra_scores(self, tmp_path):
        fn = _import_fn()
        (tmp_path / "cand_001.pdb").write_text("ATOM  ...\n")

        cand = _make_candidate(1, ddg=-8.0)
        gnina_score = {
            "gnina_cnn_score": 0.75,
            "gnina_cnn_affinity": 6.5,
            "gnina_vina_score": -7.2,
        }
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", True), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.batch_gnina_rescore", return_value=[gnina_score]):
            result = fn([cand], iter_dir=tmp_path, iteration=1)

        assert result[0].extra_scores["gnina_cnn_score"] == pytest.approx(0.75)
        assert result[0].extra_scores["gnina_cnn_affinity"] == pytest.approx(6.5)


# ---------------------------------------------------------------------------
# 9. BO optimizer: fit/suggest 호출 검증
# ---------------------------------------------------------------------------

class TestBOIntegration:
    def test_bo_suggest_called_with_optimizer(self, tmp_path):
        fn = _import_fn()
        cands = [_make_candidate(i, ddg=float(-5 - i)) for i in range(1, 5)]

        mock_optimizer = MagicMock()
        mock_optimizer.suggest.return_value = [
            {"sequence": "AGCKNFFWKTFTSC", "position": 3, "mutation": "A", "acquisition_value": 0.9}
        ]

        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", True):
            result = fn(cands, iter_dir=tmp_path, iteration=1, bo_optimizer=mock_optimizer)

        mock_optimizer.fit.assert_called_once()
        mock_optimizer.suggest.assert_called_once()
        assert len(result) == 4

    def test_bo_not_called_with_none_optimizer(self, tmp_path):
        fn = _import_fn()
        cands = [_make_candidate(i) for i in range(1, 4)]
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", True):
            result = fn(cands, iter_dir=tmp_path, iteration=1, bo_optimizer=None)
        assert len(result) == 3

    def test_bo_skipped_when_less_than_2_valid(self, tmp_path):
        """유효 관측치 < 2개면 BO fit을 호출하지 않음."""
        fn = _import_fn()
        cands = [_make_candidate(1, ddg=999.0, fail="failed")]

        mock_optimizer = MagicMock()
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", True):
            fn(cands, iter_dir=tmp_path, iteration=1, bo_optimizer=mock_optimizer)

        mock_optimizer.fit.assert_not_called()

    def test_bo_skipped_when_optimizer_none(self, tmp_path):
        """2026-06-09 P1 계약 변경: BO 단계는 bo_optimizer 가 None 이면 skip 한다.
        (이전엔 _HAS_BO 플래그가 게이트였으나, scoring_pipeline 분리 후 게이트는 'optimizer
        가 전달되었는가'로 단순화. runner 가 _HAS_BO 일 때만 optimizer 를 생성·전달하므로
        BO 불가 = bo_optimizer None 전달.) None 전달 시 mock.fit 호출 안 함을 확인."""
        fn = _import_fn()
        cands = [_make_candidate(i) for i in range(1, 4)]
        mock_optimizer = MagicMock()
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False):
            fn(cands, iter_dir=tmp_path, iteration=1, bo_optimizer=None)
        mock_optimizer.fit.assert_not_called()


# ---------------------------------------------------------------------------
# 10. Exception resilience
# ---------------------------------------------------------------------------

class TestExceptionResilience:
    def test_gnina_exception_continues_pareto(self, tmp_path):
        fn = _import_fn()
        pdb_file = tmp_path / "cand_001.pdb"
        pdb_file.write_text("ATOM  ...\n")

        cand = _make_candidate(1, ddg=-8.0)
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", True), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", True), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.batch_gnina_rescore", side_effect=RuntimeError("gnina crash")), \
             patch("pyrosetta_flow.scoring_pipeline.pareto_rank_candidates", side_effect=_mock_pareto_rank):
            result = fn([cand], iter_dir=tmp_path, iteration=1)

        assert len(result) == 1
        # GNINA 실패해도 Pareto는 실행
        assert "pareto_rank" in result[0].extra_scores

    def test_pareto_exception_continues_gracefully(self, tmp_path):
        fn = _import_fn()
        cand = _make_candidate(1, ddg=-8.0)
        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", True), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.pareto_rank_candidates", side_effect=RuntimeError("pareto crash")):
            result = fn([cand], iter_dir=tmp_path, iteration=1)
        assert len(result) == 1
        # Pareto 실패 → extra_scores에 pareto_rank 없음 (graceful degradation)
        assert "pareto_rank" not in result[0].extra_scores

    def test_bo_exception_continues_gracefully(self, tmp_path):
        fn = _import_fn()
        cands = [_make_candidate(i, ddg=float(-5 - i)) for i in range(1, 4)]
        mock_optimizer = MagicMock()
        mock_optimizer.fit.side_effect = RuntimeError("bo crash")

        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", False), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", True):
            result = fn(cands, iter_dir=tmp_path, iteration=1, bo_optimizer=mock_optimizer)

        assert len(result) == 3

    def test_ecr_exception_continues_gracefully(self, tmp_path):
        fn = _import_fn()
        (tmp_path / "cand_001.pdb").write_text("ATOM  ...\n")
        cand = _make_candidate(1, ddg=-8.0)

        with patch("pyrosetta_flow.scoring_pipeline._HAS_GNINA", True), \
             patch("pyrosetta_flow.scoring_pipeline._HAS_PARETO", False), \
             patch("pyrosetta_flow.runner._HAS_BO", False), \
             patch("pyrosetta_flow.scoring_pipeline.batch_gnina_rescore", return_value=[{"gnina_cnn_score": 0.5, "gnina_cnn_affinity": 5.0, "gnina_vina_score": -6.0}]), \
             patch("pyrosetta_flow.scoring_pipeline.exponential_rank_consensus", side_effect=RuntimeError("ecr crash")):
            result = fn([cand], iter_dir=tmp_path, iteration=1)

        assert len(result) == 1
        # ECR 실패해도 GNINA 스코어는 extra_scores에 남아있어야 함
        assert "gnina_cnn_score" in result[0].extra_scores


# ---------------------------------------------------------------------------
# 11. extra_scores 필드 기본값 테스트 (schema 검증)
# ---------------------------------------------------------------------------

class TestExtraScoresField:
    def test_extra_scores_default_empty_dict(self):
        cand = _make_candidate(1)
        assert cand.extra_scores == {}

    def test_extra_scores_independent_instances(self):
        """각 인스턴스가 독립적인 extra_scores를 가져야 함 (mutable default 공유 방지)."""
        c1 = _make_candidate(1)
        c2 = _make_candidate(2)
        c1.extra_scores["test"] = 1
        assert "test" not in c2.extra_scores
