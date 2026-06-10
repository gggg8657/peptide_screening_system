#!/usr/bin/env python3
"""pepadmet_infer_ood.py
========================
A.A5Pb-OOD — pepADMET OOD-포함 추론 스크립트

SMILES + descriptor CSV를 입력으로 받아:
  1. MGA 모델 로드 (--model_path)
  2. train_loader로 OOD 임계값 적합 (--fit_ood, 선택)
  3. 입력 분자에 대해 binary_toxicity 예측 + OOD score 계산
  4. 결과 CSV 출력

사용법:
    # 임계값 fit 없이 (사전 저장된 stats 사용):
    conda run -n pepadmet-upgrade python scripts/pepadmet_infer_ood.py \\
        --model_path pepADMET/model/toxicity_retrained_2026-05-21.pth \\
        --input_csv pepADMET/data/query.csv \\
        --ood_stats_path pepADMET/model/ood_stats.npz \\
        --output_csv results/infer_ood_result.csv

    # 임계값을 train set에서 새로 fit:
    conda run -n pepadmet-upgrade python scripts/pepadmet_infer_ood.py \\
        --model_path pepADMET/model/toxicity_retrained_2026-05-21.pth \\
        --input_csv pepADMET/data/query.csv \\
        --fit_ood \\
        --train_bin pepADMET/data/Toxicity.bin \\
        --train_group pepADMET/data/Toxicity_group.csv \\
        --ood_stats_path pepADMET/model/ood_stats.npz \\
        --output_csv results/infer_ood_result.csv

작성: engineer-backend 2026-05-21 (Task #10)
"""
from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

# pepADMET 패키지 경로 추가 (scripts/ 기준 상위)
_SCRIPT_DIR = Path(__file__).resolve().parent
_PEPADMET_DIR = _SCRIPT_DIR.parent / "pepADMET"
sys.path.insert(0, str(_PEPADMET_DIR))

from utils import build_dataset
from utils.build_dataset import construct_RGCN_bigraph_from_smiles, collate_molgraphs_predict
from utils.MY_GNN import MGA, collate_molgraphs
from utils.ood_detection import OODDetector


# ---------------------------------------------------------------------------
# args 기본값 (Train.ipynb 와 동기화)
# ---------------------------------------------------------------------------
DEFAULT_ARGS: dict = {
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "atom_data_field": "atom",
    "bond_data_field": "etype",
    "descriptor_dim": 2133,
    "descriptor": 2133,
    "fpn_out": 2133,
    "fp_2_dim": 512,
    "dropout": 0.2,
    "hidden_size": 256,
    "in_feats": 40,
    "rgcn_hidden_feats": [64, 64],
    "classifier_hidden_feats": 320,
    "rgcn_drop_out": 0.2,
    "drop_out": 0.2,
    "loop": True,
    "task_class": "classification_regression",
    "classification_num": 3,
    "regression_num": 1,
    "select_task_list": [
        "toxicity_nontoxicity",
        "toxicity_type_class",
        "neurotoxicity_type_class",
        "HC50",
    ],
    "classification_metric_name": "roc_auc",
    "regression_metric_name": "r2",
    "select_task_index": [0, 1, 2, 3],
}


# ---------------------------------------------------------------------------
# 예측 전용 DataLoader 빌더
# ---------------------------------------------------------------------------

def _build_predict_dataset(
    input_csv: str, args: dict
) -> list[tuple]:
    """SMILES + descriptor CSV → (smiles, graph, descriptor) 튜플 리스트."""
    df = pd.read_csv(input_csv)
    df = df.fillna(0)

    # descriptor 컬럼: 6번째 이후
    meta_cols = list(df.columns[:6])
    desc_cols = list(df.columns[6:])

    if "smiles" not in df.columns:
        raise ValueError("input_csv에 'smiles' 컬럼이 없습니다.")

    dataset: list[tuple] = []
    failed = 0
    for _, row in df.iterrows():
        smi = str(row["smiles"])
        try:
            g = construct_RGCN_bigraph_from_smiles(smi)
            desc = torch.tensor(row[desc_cols].values.astype(float), dtype=torch.float32)
            dataset.append((smi, g, desc))
        except Exception as e:
            print(f"  [WARN] SMILES 변환 실패: {smi[:60]} — {e}", flush=True)
            failed += 1
    print(f"  dataset: {len(dataset)} 성공 / {failed} 실패", flush=True)
    return dataset


def _collate_predict(batch: list[tuple]):
    """(smiles, graph, descriptor) 배치 콜레이트."""
    import dgl
    smiles_list, graphs, descs = zip(*batch)
    bg = dgl.batch(graphs)
    descriptor = torch.stack(descs, dim=0)
    return list(smiles_list), bg, descriptor


# ---------------------------------------------------------------------------
# 모델 로드
# ---------------------------------------------------------------------------

def _load_model(model_path: str, args: dict) -> MGA:
    """체크포인트에서 MGA 모델 로드."""
    task_number = len(args["select_task_list"])
    model = MGA(
        in_feats=args["in_feats"],
        descriptor=args["descriptor"],
        descriptor_dim=args["descriptor_dim"],
        rgcn_hidden_feats=args["rgcn_hidden_feats"],
        n_tasks=task_number,
        rgcn_drop_out=args["rgcn_drop_out"],
        fpn_out=args["fpn_out"],
        fp_2_dim=args["fp_2_dim"],
        hidden_size=args["hidden_size"],
        select_task_list=args["select_task_list"],
        device=args["device"],
        classifier_hidden_feats=args["classifier_hidden_feats"],
        dropout=args["drop_out"],
        loop=args["loop"],
    )
    state = torch.load(model_path, map_location=args["device"])
    model.load_state_dict(state)
    model.to(args["device"])
    model.eval()
    print(f"[model] 로드 완료: {model_path}", flush=True)
    return model


# ---------------------------------------------------------------------------
# train_loader 빌더 (OOD fit용)
# ---------------------------------------------------------------------------

def _build_train_loader(
    bin_path: str, group_path: str, args: dict, batch_size: int = 64
) -> DataLoader:
    """bin/group CSV에서 train split DataLoader 생성."""
    train_set, _, _, _ = build_dataset.load_graph_from_csv_bin_for_splited(
        bin_path=bin_path,
        group_path=group_path,
        select_task_index=args["select_task_index"],
    )
    loader = DataLoader(
        dataset=train_set,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_molgraphs,
    )
    print(f"[train_loader] {len(train_set)} 샘플", flush=True)
    return loader


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="pepADMET OOD-포함 추론")
    parser.add_argument("--model_path", required=True, help="MGA 체크포인트 (.pth)")
    parser.add_argument("--input_csv", required=True, help="추론 대상 CSV (SMILES + descriptor)")
    parser.add_argument("--output_csv", required=True, help="결과 CSV 저장 경로")
    parser.add_argument(
        "--ood_stats_path", default="pepADMET/model/ood_stats.npz",
        help="OOD 통계 저장/로드 경로 (.npz)"
    )
    parser.add_argument("--fit_ood", action="store_true", help="OOD 임계값을 train set에서 새로 fit")
    parser.add_argument("--train_bin", default="pepADMET/data/Toxicity.bin", help="학습 graph bin")
    parser.add_argument("--train_group", default="pepADMET/data/Toxicity_group.csv", help="학습 group CSV")
    parser.add_argument("--n_mc_samples", type=int, default=20, help="MC Dropout forward 횟수")
    parser.add_argument("--ood_percentile", type=float, default=95.0, help="OOD flag 임계값 백분위")
    parser.add_argument("--batch_size", type=int, default=32, help="배치 크기")
    parser.add_argument("--device", type=str, default=None, help="cuda / cpu (기본: 자동 감지)")
    args_ns = parser.parse_args()

    args = dict(DEFAULT_ARGS)
    if args_ns.device:
        args["device"] = args_ns.device

    print(f"[config] device={args['device']}", flush=True)

    # 1) 모델 로드
    model = _load_model(args_ns.model_path, args)

    # 2) OOD Detector
    detector = OODDetector(
        model=model,
        device=args["device"],
        n_mc_samples=args_ns.n_mc_samples,
        ood_percentile=args_ns.ood_percentile,
    )

    if args_ns.fit_ood:
        print("[OOD] train set에서 통계 fit 중...", flush=True)
        train_loader = _build_train_loader(
            args_ns.train_bin, args_ns.train_group, args, batch_size=args_ns.batch_size
        )
        detector.fit_train_stats(train_loader, args)
        detector.save_stats(args_ns.ood_stats_path)
    else:
        if not os.path.exists(args_ns.ood_stats_path):
            raise FileNotFoundError(
                f"OOD stats 파일 없음: {args_ns.ood_stats_path}\n"
                "--fit_ood 플래그로 먼저 fit하거나 stats 파일을 제공하세요."
            )
        detector.load_stats(args_ns.ood_stats_path)

    # 3) 예측 DataLoader
    predict_dataset = _build_predict_dataset(args_ns.input_csv, args)
    predict_loader = DataLoader(
        dataset=predict_dataset,
        batch_size=args_ns.batch_size,
        shuffle=False,
        collate_fn=_collate_predict,
    )

    # 4) OOD-포함 추론
    print("[infer] OOD-포함 추론 실행 중...", flush=True)
    results = detector.predict_with_ood(predict_loader, args)

    # 5) 결과 저장
    out_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(os.path.abspath(args_ns.output_csv)), exist_ok=True)
    out_df.to_csv(args_ns.output_csv, index=False)
    print(f"[결과] {len(out_df)} 행 저장: {args_ns.output_csv}", flush=True)

    # 요약 통계
    ood_cnt = out_df["ood_flag"].sum()
    print(
        f"[요약] OOD 분자: {ood_cnt}/{len(out_df)} "
        f"({ood_cnt/max(len(out_df),1)*100:.1f}%)",
        flush=True,
    )
    print("✅ 추론 완료", flush=True)


if __name__ == "__main__":
    main()
