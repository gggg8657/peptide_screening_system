"""test_ood_detection.py
========================
A.A5Pb-OOD — OODDetector 단위 테스트

모델 실제 학습 없이 Mock을 사용해 OODDetector 로직을 검증한다.
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch
import torch.nn as nn

# pepADMET 경로
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pepADMET"))
from utils.ood_detection import OODDetector


# ---------------------------------------------------------------------------
# Fixture: 더미 모델
# ---------------------------------------------------------------------------

class _DummyFC3(nn.Sequential):
    """fc_layers3[0] 역할 — 64차원 → 64차원 출력."""
    def __init__(self) -> None:
        super().__init__(
            nn.Linear(64, 64),
            nn.ReLU(),
        )


class _DummyModel(nn.Module):
    """BaseGNN/MGA 인터페이스를 흉내내는 최소 모델."""
    def __init__(self) -> None:
        super().__init__()
        self.fc_layers3 = nn.ModuleList([_DummyFC3()])
        self._h3_dim = 64

    def forward(self, bg, atom_feats, bond_feats, descriptor):
        # descriptor shape: (N, any) → fc_layers3[0] 입력에 맞게 프로젝션
        # 여기서는 h3를 직접 반환 (테스트 단순화)
        batch_size = descriptor.shape[0]
        x = torch.ones(batch_size, 64)
        h3 = self.fc_layers3[0](x)
        # task_0 logits: binary classification (N, 1)
        logits = torch.zeros(batch_size, 1)
        return {"task_0": logits}


class _FakeNodeData(dict):
    """DGL bg.ndata / bg.edata 를 흉내내는 dict subclass — pop() 오버라이드 허용."""
    def __init__(self, pop_value: torch.Tensor, **kwargs) -> None:
        super().__init__(**kwargs)
        self._pop_value = pop_value

    def pop(self, key, *args):  # type: ignore[override]
        return self._pop_value


def _make_fake_batch(n: int = 4, desc_dim: int = 64):
    """(smiles_list, bg_mock, descriptor) 튜플 반환."""
    smiles = [f"C{'C'*i}" for i in range(n)]
    bg = MagicMock()
    bg.ndata = _FakeNodeData(
        pop_value=torch.zeros(n * 5, 40),
        atom=torch.zeros(n * 5, 40),
    )
    bg.edata = _FakeNodeData(
        pop_value=torch.zeros(n * 5, dtype=torch.long),
        etype=torch.zeros(n * 5, dtype=torch.long),
    )
    descriptor = torch.randn(n, desc_dim)
    return smiles, bg, descriptor


def _make_fake_loader(n_batches: int = 3, batch_size: int = 4):
    """Mock DataLoader — 매 반복 시 fake batch 반환."""
    batches = [_make_fake_batch(batch_size) for _ in range(n_batches)]
    # 5-tuple: smiles, bg, descriptor, labels, mask
    labeled_batches = []
    for smiles, bg, desc in batches:
        labels = torch.zeros(len(smiles), 1)
        mask = torch.ones(len(smiles), 1)
        labeled_batches.append((smiles, bg, desc, labels, mask))
    return labeled_batches


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOODDetectorInit:
    def test_init_default(self):
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu")
        assert det.n_mc_samples == 20
        assert det.ood_percentile == 95.0
        assert det._train_mean is None
        assert det._maha_threshold is None

    def test_init_custom(self):
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu", n_mc_samples=5, ood_percentile=90.0)
        assert det.n_mc_samples == 5
        assert det.ood_percentile == 90.0


class TestOODDetectorMahalanobis:
    def test_mahalanobis_batch_shape(self):
        """h3 배열에 대한 Mahalanobis distance가 (N,) shape을 반환해야 한다."""
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu")

        # 수동으로 통계 주입
        D = 64
        np.random.seed(42)
        fake_h3 = np.random.randn(100, D).astype(np.float32)
        det._train_mean = np.mean(fake_h3, axis=0)
        cov = np.cov(fake_h3, rowvar=False) + np.eye(D) * 1e-6
        det._train_cov_inv = np.linalg.inv(cov)
        train_maha = det._compute_mahalanobis_batch(fake_h3)
        det._maha_threshold = float(np.percentile(train_maha, 95.0))

        test_h3 = np.random.randn(10, D).astype(np.float32)
        dist = det._compute_mahalanobis_batch(test_h3)
        assert dist.shape == (10,)

    def test_mahalanobis_positive(self):
        """Mahalanobis distance는 항상 ≥ 0이어야 한다."""
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu")
        D = 8
        fake_h3 = np.eye(D).astype(np.float32)
        det._train_mean = np.zeros(D)
        det._train_cov_inv = np.eye(D)
        det._maha_threshold = 10.0
        det._mc_std_threshold = 1.0
        dist = det._compute_mahalanobis_batch(fake_h3)
        assert np.all(dist >= 0)

    def test_fit_raises_before_fit(self):
        """fit_train_stats() 전에 _compute_mahalanobis_batch 호출 시 RuntimeError."""
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu")
        with pytest.raises(RuntimeError, match="fit_train_stats"):
            det._compute_mahalanobis_batch(np.zeros((5, 64)))


class TestOODDetectorHooks:
    def test_register_remove_hooks(self):
        """훅 등록 후 해제 시 _hooks가 비어야 한다."""
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu")
        det._register_h3_hooks()
        assert len(det._hooks) == 1, "task_0용 훅 1개만 등록"
        det._remove_hooks()
        assert len(det._hooks) == 0


class TestOODDetectorSaveLoad:
    def test_save_load_roundtrip(self):
        """save_stats / load_stats 후 값이 동일해야 한다."""
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu")
        D = 16
        det._train_mean = np.ones(D)
        det._train_cov_inv = np.eye(D) * 2.0
        det._maha_threshold = 3.14
        det._mc_std_threshold = 0.25

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ood_stats.npz")
            det.save_stats(path)

            det2 = OODDetector(model=model, device="cpu")
            det2.load_stats(path)

            np.testing.assert_allclose(det2._train_mean, det._train_mean)
            np.testing.assert_allclose(det2._train_cov_inv, det._train_cov_inv)
            assert abs(det2._maha_threshold - det._maha_threshold) < 1e-6
            assert abs(det2._mc_std_threshold - det._mc_std_threshold) < 1e-6


class TestOODDetectorPredictWithOOD:
    def _make_fitted_detector(self, D: int = 64) -> OODDetector:
        """fit된 상태의 OODDetector 반환 (수동 주입)."""
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu")
        np.random.seed(0)
        fake_h3 = np.random.randn(50, D).astype(np.float32)
        det._train_mean = np.mean(fake_h3, axis=0)
        cov = np.cov(fake_h3, rowvar=False) + np.eye(D) * 1e-6
        det._train_cov_inv = np.linalg.inv(cov)
        maha = det._compute_mahalanobis_batch(fake_h3)
        det._maha_threshold = float(np.percentile(maha, 95.0))
        det._mc_std_threshold = 0.5
        return det

    def test_predict_with_ood_returns_list(self):
        """predict_with_ood는 dict 리스트를 반환해야 한다."""
        det = self._make_fitted_detector()
        loader = _make_fake_loader(n_batches=2, batch_size=4)
        args = {
            "atom_data_field": "atom",
            "bond_data_field": "etype",
        }
        # _compute_mc_dropout_batch를 패치 (DataLoader 재순회 문제 회피)
        n_samples = 2 * 4
        mc_stds = np.zeros(n_samples)
        with patch.object(det, "_compute_mc_dropout_batch", return_value=mc_stds):
            results = det.predict_with_ood(loader, args)

        assert isinstance(results, list)
        assert len(results) == n_samples
        for r in results:
            assert "smiles" in r
            assert "binary_toxicity_pred" in r
            assert "ood_maha" in r
            assert "ood_mc_std" in r
            assert "ood_score" in r
            assert "ood_flag" in r

    def test_predict_ood_score_range(self):
        """ood_score = maha / threshold (≥0). in-dist 샘플은 score < 1에 수렴해야 한다."""
        det = self._make_fitted_detector()
        loader = _make_fake_loader(n_batches=1, batch_size=8)
        args = {
            "atom_data_field": "atom",
            "bond_data_field": "etype",
        }
        mc_stds = np.zeros(8)
        with patch.object(det, "_compute_mc_dropout_batch", return_value=mc_stds):
            results = det.predict_with_ood(loader, args)
        for r in results:
            assert r["ood_score"] >= 0

    def test_predict_raises_without_fit(self):
        """fit 없이 predict_with_ood 호출 시 RuntimeError."""
        model = _DummyModel()
        det = OODDetector(model=model, device="cpu")
        loader = _make_fake_loader(n_batches=1, batch_size=2)
        args = {"atom_data_field": "atom", "bond_data_field": "etype"}
        with pytest.raises(RuntimeError, match="fit_train_stats"):
            det.predict_with_ood(loader, args)
