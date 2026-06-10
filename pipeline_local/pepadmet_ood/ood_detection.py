"""ood_detection.py
====================
A.A5Pb-OOD — Mahalanobis distance + MC Dropout OOD detection

Task #10: MY_GNN.py/inference wrapper에 OOD detection 추가

사용법:
    from utils.ood_detection import OODDetector

    # 학습 후 train set으로 통계 추정
    detector = OODDetector(model, device, n_mc_samples=20)
    detector.fit_train_stats(train_loader, args)

    # 추론 시
    results = detector.predict_with_ood(data_loader, args)
    # results: [{"smiles": ..., "binary_toxicity": ..., "ood_score": ..., "ood_flag": ...}, ...]

작성: engineer-backend 2026-05-21
"""
from __future__ import annotations

import torch
import torch.nn as nn
import numpy as np
from typing import Optional


class OODDetector:
    """Mahalanobis distance + MC Dropout 기반 OOD 탐지기.

    Args:
        model: MGA (BaseGNN subclass) 모델
        device: 'cuda' 또는 'cpu'
        n_mc_samples: MC Dropout forward pass 횟수 (기본 20)
        ood_percentile: OOD flag 임계값 백분위 (기본 95 — train set 기준)
    """

    def __init__(
        self,
        model: nn.Module,
        device: str,
        n_mc_samples: int = 20,
        ood_percentile: float = 95.0,
    ) -> None:
        self.model = model
        self.device = device
        self.n_mc_samples = n_mc_samples
        self.ood_percentile = ood_percentile

        # Mahalanobis 통계 (fit_train_stats 후 채워짐)
        self._train_mean: Optional[np.ndarray] = None
        self._train_cov_inv: Optional[np.ndarray] = None
        self._maha_threshold: Optional[float] = None
        self._mc_std_threshold: Optional[float] = None

        # h3 hook 저장소
        self._last_h3: dict[str, torch.Tensor] = {}
        self._hooks: list = []

    # ------------------------------------------------------------------
    # Hook 등록 / 해제
    # ------------------------------------------------------------------

    def _register_h3_hooks(self) -> None:
        """BaseGNN.fc_layers3[i] 의 출력을 후킹한다 (task_0 기준)."""
        self._remove_hooks()

        def _hook_fn(module: nn.Module, input: tuple, output: torch.Tensor) -> None:
            self._last_h3["h3"] = output.detach()

        # 모든 fc_layers3 hook 등록 (task_0의 마지막 hidden)
        for i, layer in enumerate(self.model.fc_layers3):
            h = layer.register_forward_hook(_hook_fn)
            self._hooks.append(h)
            break  # task_0만 필요

    def _remove_hooks(self) -> None:
        for h in self._hooks:
            h.remove()
        self._hooks.clear()

    # ------------------------------------------------------------------
    # Train set statistics
    # ------------------------------------------------------------------

    def _extract_h3_features(
        self, data_loader, args: dict
    ) -> np.ndarray:
        """data_loader에서 h3 feature 배열 추출."""
        self._register_h3_hooks()
        self.model.eval()
        feats_list: list[np.ndarray] = []

        with torch.no_grad():
            for batch_data in data_loader:
                if len(batch_data) == 5:
                    smiles, bg, descriptor, labels, mask = batch_data
                elif len(batch_data) == 3:
                    smiles, bg, descriptor = batch_data
                else:
                    smiles, bg, descriptor = batch_data[:3]

                descriptor = descriptor.float().to(self.device)
                atom_feats = bg.ndata.pop(args["atom_data_field"]).float().to(self.device)
                bond_feats = bg.edata.pop(args["bond_data_field"]).long().to(self.device)

                _ = self.model(bg, atom_feats, bond_feats, descriptor)

                if "h3" in self._last_h3:
                    feats_list.append(self._last_h3["h3"].cpu().numpy())

        self._remove_hooks()

        if not feats_list:
            raise RuntimeError("h3 hook이 아무 데이터도 수집하지 못했습니다.")

        return np.vstack(feats_list)

    def fit_train_stats(self, train_loader, args: dict) -> None:
        """학습 데이터셋에서 Mahalanobis + MC Dropout 임계값 추정.

        Args:
            train_loader: 학습 DataLoader
            args: 모델 args dict (atom_data_field, bond_data_field 포함)
        """
        print("[OODDetector] train set h3 feature 추출 중...", flush=True)
        train_h3 = self._extract_h3_features(train_loader, args)
        print(f"[OODDetector] train h3 shape: {train_h3.shape}", flush=True)

        # Mahalanobis: 평균 + 공분산 역행렬
        self._train_mean = np.mean(train_h3, axis=0)
        cov = np.cov(train_h3, rowvar=False)
        # 정규화 조건 수 개선: regularization
        cov += np.eye(cov.shape[0]) * 1e-6
        try:
            self._train_cov_inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            # singular → pseudo-inverse
            self._train_cov_inv = np.linalg.pinv(cov)

        # train set에 대한 Mahalanobis 분포 → threshold = percentile
        train_maha = self._compute_mahalanobis_batch(train_h3)
        self._maha_threshold = float(np.percentile(train_maha, self.ood_percentile))

        # MC Dropout train set std 분포 → threshold
        print("[OODDetector] MC Dropout train set uncertainty 추정 중...", flush=True)
        train_mc_std = self._compute_mc_dropout_batch(train_loader, args)
        self._mc_std_threshold = float(np.percentile(train_mc_std, self.ood_percentile))

        print(
            f"[OODDetector] fit 완료: "
            f"maha_threshold={self._maha_threshold:.4f}, "
            f"mc_std_threshold={self._mc_std_threshold:.4f}",
            flush=True,
        )

    # ------------------------------------------------------------------
    # Mahalanobis distance
    # ------------------------------------------------------------------

    def _compute_mahalanobis_batch(self, h3: np.ndarray) -> np.ndarray:
        """h3 배열에 대한 Mahalanobis distance 계산."""
        if self._train_mean is None or self._train_cov_inv is None:
            raise RuntimeError("fit_train_stats()를 먼저 호출하세요.")
        diff = h3 - self._train_mean  # (N, D)
        # (N,) = sum_i(diff @ Sigma^-1 @ diff^T) diag
        dist = np.sqrt(
            np.clip(np.einsum("ni,ij,nj->n", diff, self._train_cov_inv, diff), 0, None)
        )
        return dist

    # ------------------------------------------------------------------
    # MC Dropout
    # ------------------------------------------------------------------

    def _compute_mc_dropout_batch(
        self, data_loader, args: dict
    ) -> np.ndarray:
        """MC Dropout으로 예측 std 계산.

        model.train() 모드에서 n_mc_samples 회 forward pass → 예측 std 반환.
        """
        # MC Dropout: n_mc_samples 회 forward → std
        all_mc_runs: list[np.ndarray] = []
        self.model.train()
        with torch.no_grad():
            for _ in range(self.n_mc_samples):
                run_preds: list[np.ndarray] = []
                for batch_data in data_loader:
                    if len(batch_data) == 5:
                        smiles, bg, descriptor, labels, mask = batch_data
                    elif len(batch_data) == 3:
                        smiles, bg, descriptor = batch_data
                    else:
                        smiles, bg, descriptor = batch_data[:3]

                    descriptor = descriptor.float().to(self.device)
                    atom_feats = bg.ndata.pop(args["atom_data_field"]).float().to(self.device)
                    bond_feats = bg.edata.pop(args["bond_data_field"]).long().to(self.device)
                    logits = self.model(bg, atom_feats, bond_feats, descriptor)
                    pred = torch.sigmoid(logits["task_0"]).squeeze(-1).cpu().numpy()
                    run_preds.append(pred)
                all_mc_runs.append(np.concatenate(run_preds))

        self.model.eval()
        mc_preds = np.stack(all_mc_runs, axis=0)  # (n_mc_samples, N)
        mc_std = np.std(mc_preds, axis=0)  # (N,)
        return mc_std

    # ------------------------------------------------------------------
    # 통합 추론
    # ------------------------------------------------------------------

    def predict_with_ood(
        self, data_loader, args: dict
    ) -> list[dict]:
        """추론 + OOD score 포함 결과 반환.

        Returns:
            list of dict with keys:
              - smiles: str
              - binary_toxicity_pred: float (sigmoid 확률)
              - ood_maha: float (Mahalanobis distance)
              - ood_mc_std: float (MC Dropout std)
              - ood_score: float (maha normalized, 0~1+ scale)
              - ood_flag: bool (True if OOD)
        """
        if self._maha_threshold is None:
            raise RuntimeError("fit_train_stats()를 먼저 호출하세요.")

        # 1) h3 추출
        self._register_h3_hooks()
        self.model.eval()
        all_smiles: list[str] = []
        all_preds: list[float] = []
        all_h3: list[np.ndarray] = []

        with torch.no_grad():
            for batch_data in data_loader:
                if len(batch_data) == 5:
                    smiles, bg, descriptor, labels, mask = batch_data
                elif len(batch_data) == 3:
                    smiles, bg, descriptor = batch_data
                else:
                    smiles, bg, descriptor = batch_data[:3]

                descriptor = descriptor.float().to(self.device)
                atom_feats = bg.ndata.pop(args["atom_data_field"]).float().to(self.device)
                bond_feats = bg.edata.pop(args["bond_data_field"]).long().to(self.device)
                logits = self.model(bg, atom_feats, bond_feats, descriptor)

                pred = torch.sigmoid(logits["task_0"]).squeeze(-1).cpu().numpy()
                all_preds.extend(pred.tolist())
                all_smiles.extend(list(smiles))
                if "h3" in self._last_h3:
                    all_h3.append(self._last_h3["h3"].cpu().numpy())

        self._remove_hooks()

        all_h3_arr = np.vstack(all_h3) if all_h3 else np.empty((0, 128))

        # 2) Mahalanobis
        maha_scores = self._compute_mahalanobis_batch(all_h3_arr)

        # 3) MC Dropout
        mc_stds = self._compute_mc_dropout_batch(data_loader, args)
        # DataLoader 재순회로 순서 보장

        # 4) OOD flag: Mahalanobis OR MC std 초과
        ood_flags = (maha_scores > self._maha_threshold) | (mc_stds > self._mc_std_threshold)

        # 5) ood_score: normalized Mahalanobis (0=in-dist, 1=threshold, >1=OOD)
        ood_scores = maha_scores / (self._maha_threshold + 1e-8)

        results: list[dict] = []
        for i in range(len(all_smiles)):
            results.append(
                {
                    "smiles": all_smiles[i],
                    "binary_toxicity_pred": float(all_preds[i]),
                    "ood_maha": float(maha_scores[i]),
                    "ood_mc_std": float(mc_stds[i]) if i < len(mc_stds) else float("nan"),
                    "ood_score": float(ood_scores[i]),
                    "ood_flag": bool(ood_flags[i]),
                }
            )

        return results

    # ------------------------------------------------------------------
    # 직렬화
    # ------------------------------------------------------------------

    def save_stats(self, path: str) -> None:
        """Mahalanobis 통계 + threshold 저장 (numpy npz)."""
        np.savez(
            path,
            train_mean=self._train_mean,
            train_cov_inv=self._train_cov_inv,
            maha_threshold=self._maha_threshold,
            mc_std_threshold=self._mc_std_threshold,
        )
        print(f"[OODDetector] stats 저장: {path}", flush=True)

    def load_stats(self, path: str) -> None:
        """저장된 통계 로드."""
        data = np.load(path)
        self._train_mean = data["train_mean"]
        self._train_cov_inv = data["train_cov_inv"]
        self._maha_threshold = float(data["maha_threshold"])
        self._mc_std_threshold = float(data["mc_std_threshold"])
        print(
            f"[OODDetector] stats 로드: maha_thr={self._maha_threshold:.4f}, "
            f"mc_thr={self._mc_std_threshold:.4f}",
            flush=True,
        )
