#!/usr/bin/env python3
"""retrain_toxicity.py
======================
A.A5Pc — pepADMET Toxicity 모델 5-fold 재훈련

Toxicity_extended_clean.csv 기반으로:
  1. DGL .bin 재빌드 (Toxicity_retrained.bin)
  2. 5-fold (5 seed) 훈련
  3. 최고 validation AUC 체크포인트 → toxicity_retrained_2026-05-21.pth
  4. 결과 CSV → result/Toxicity_retrained_result.csv

실행:
    CUDA_VISIBLE_DEVICES=2 conda run -n pepadmet-upgrade \
        python scripts/retrain_toxicity.py

작성: engineer-backend 2026-05-21 (Task #11)
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# pepADMET 디렉토리를 sys.path에 추가
# NOTE: pepADMET 소스는 GPL v3 라이선스로 _workspace/pepadmet_local/pepADMET/ 에 저장
#       (git 추적 제외). 실행 전 해당 디렉토리가 존재해야 함.
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parents[2]  # pipeline_local/scripts/ → repo root
_PEPADMET_DIR = _REPO_ROOT / "_workspace" / "pepadmet_local" / "pepADMET"
if not _PEPADMET_DIR.exists():
    raise RuntimeError(
        f"pepADMET 소스 디렉토리 없음: {_PEPADMET_DIR}\n"
        "pepADMET 소스를 _workspace/pepadmet_local/pepADMET/ 에 준비하세요."
    )
sys.path.insert(0, str(_PEPADMET_DIR))

import numpy as np
import pandas as pd
import torch
from torch.optim import Adam
from torch.utils.data import DataLoader

from utils import build_dataset
from utils.MY_GNN import (
    MGA,
    EarlyStopping,
    Meter,
    collate_molgraphs,
    multi_weight_four,
    multi_weight_six,
    pos_weight,
    run_a_train_epoch_heterogeneous,
    run_an_eval_epoch_heterogeneous,
    set_random_seed,
)

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

DATA_DIR = _PEPADMET_DIR / "data"
MODEL_DIR = _PEPADMET_DIR / "model"
RESULT_DIR = _PEPADMET_DIR / "result"

INPUT_CSV = DATA_DIR / "Toxicity_extended_clean.csv"
BIN_PATH = str(DATA_DIR / "Toxicity_retrained.bin")
GROUP_PATH = str(DATA_DIR / "Toxicity_retrained_group.csv")
CHECKPOINT_PATH = str(MODEL_DIR / "toxicity_retrained_2026-05-21.pth")
RESULT_CSV = str(RESULT_DIR / "Toxicity_retrained_result.csv")

TASK_LIST_SELECTED = [
    "toxicity_nontoxicity",
    "toxicity_type_class",
    "neurotoxicity_type_class",
    "HC50",
]

ARGS: dict = {
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "atom_data_field": "atom",
    "bond_data_field": "etype",
    "descriptor_dim": 2133,
    "descriptor": 2133,
    "fpn_out": 2133,
    "fp_2_dim": 512,
    "dropout": 0.2,
    "hidden_size": 256,
    "classification_metric_name": ["roc_auc"],  # compute_metric()은 list 필요
    "regression_metric_name": ["r2"],
    "num_epochs": 300,
    "patience": 50,
    "batch_size": 128,
    "mode": "higher",
    "in_feats": 40,
    "rgcn_hidden_feats": [64, 64],
    "classifier_hidden_feats": 320,
    "rgcn_drop_out": 0.2,
    "drop_out": 0.2,
    "lr": 3,
    "weight_decay": 5,
    "loop": True,
    "task_name": "Toxicity_retrained",
    "data_name": "Toxicity_retrained",
    "times": 5,
    "select_task_list": TASK_LIST_SELECTED,
}


# ---------------------------------------------------------------------------
# Step 1: bin 재빌드
# ---------------------------------------------------------------------------

def build_bin(force: bool = False) -> tuple[int, list[int]]:
    """Toxicity_extended_clean.csv → .bin + _group.csv.

    Returns:
        (task_number, select_task_index)
    """
    if not force and os.path.exists(BIN_PATH):
        print(f"[bin] 기존 bin 재사용: {BIN_PATH}", flush=True)
    else:
        print("[bin] DGL 그래프 빌드 중...", flush=True)
        os.makedirs(str(DATA_DIR), exist_ok=True)
        build_dataset.built_data_and_save_for_splited(
            origin_path=str(INPUT_CSV),
            save_path=BIN_PATH,
            group_path=GROUP_PATH,
            task_list_selected=TASK_LIST_SELECTED,
        )
        print(f"[bin] 빌드 완료: {BIN_PATH}", flush=True)

    # task 인덱스 산출
    all_task_list = TASK_LIST_SELECTED
    select_task_index = list(range(len(TASK_LIST_SELECTED)))
    classification_num = 3  # toxicity_nontoxicity, toxicity_type_class, neurotoxicity_type_class
    regression_num = 1      # HC50

    ARGS["all_task_list"] = all_task_list
    ARGS["select_task_index"] = select_task_index
    ARGS["classification_num"] = classification_num
    ARGS["regression_num"] = regression_num

    if classification_num > 0 and regression_num > 0:
        ARGS["task_class"] = "classification_regression"
    elif classification_num > 0:
        ARGS["task_class"] = "classification"
    else:
        ARGS["task_class"] = "regression"

    ARGS["bin_path"] = BIN_PATH
    ARGS["group_path"] = GROUP_PATH

    print(
        f"[config] task_class={ARGS['task_class']}, "
        f"classification_num={classification_num}, regression_num={regression_num}",
        flush=True,
    )
    return len(TASK_LIST_SELECTED), select_task_index


# ---------------------------------------------------------------------------
# Step 2: 5-fold 훈련
# ---------------------------------------------------------------------------

def train_5fold(task_number: int) -> None:
    """5 seed 훈련 루프."""
    os.makedirs(str(RESULT_DIR), exist_ok=True)
    os.makedirs(str(MODEL_DIR), exist_ok=True)

    result_pd = pd.DataFrame(
        columns=(
            ARGS["select_task_list"] + ["group"]
        ) * 3
    )

    best_val_score: float = -1.0
    best_model_state = None

    for time_id in range(ARGS["times"]):
        seed = 2020 + time_id
        set_random_seed(seed)
        print(
            f"\n{'='*80}\n"
            f"[train] {ARGS['task_name']}  {time_id + 1}/{ARGS['times']}  seed={seed}\n"
            f"{'='*80}",
            flush=True,
        )

        train_set, val_set, test_set, task_num = (
            build_dataset.load_graph_from_csv_bin_for_splited(
                bin_path=BIN_PATH,
                group_path=GROUP_PATH,
                select_task_index=ARGS["select_task_index"],
            )
        )
        print(f"[data] train={len(train_set)} val={len(val_set)} test={len(test_set)}", flush=True)

        train_loader = DataLoader(
            dataset=train_set, batch_size=ARGS["batch_size"],
            shuffle=True, collate_fn=collate_molgraphs,
        )
        val_loader = DataLoader(
            dataset=val_set, batch_size=ARGS["batch_size"],
            shuffle=False, collate_fn=collate_molgraphs,
        )
        test_loader = DataLoader(
            dataset=test_set, batch_size=ARGS["batch_size"],
            shuffle=False, collate_fn=collate_molgraphs,
        )

        # 가중치
        pw = pos_weight(train_set)
        w1 = multi_weight_six(train_set)
        w2 = multi_weight_four(train_set)

        loss_c0 = torch.nn.BCEWithLogitsLoss(
            reduction="none", pos_weight=pw.to(ARGS["device"])
        )
        loss_c1 = torch.nn.CrossEntropyLoss(
            reduction="none",
            weight=torch.tensor(w1).to(ARGS["device"]),
        )
        loss_c2 = torch.nn.CrossEntropyLoss(
            reduction="none",
            weight=torch.tensor(w2).to(ARGS["device"]),
        )
        loss_r = torch.nn.MSELoss(reduction="none")

        # 모델
        model = MGA(
            in_feats=ARGS["in_feats"],
            descriptor=ARGS["descriptor"],
            descriptor_dim=ARGS["descriptor_dim"],
            rgcn_hidden_feats=ARGS["rgcn_hidden_feats"],
            n_tasks=task_number,
            rgcn_drop_out=ARGS["rgcn_drop_out"],
            fpn_out=ARGS["fpn_out"],
            fp_2_dim=ARGS["fp_2_dim"],
            hidden_size=ARGS["hidden_size"],
            select_task_list=ARGS["select_task_list"],
            device=ARGS["device"],
            classifier_hidden_feats=ARGS["classifier_hidden_feats"],
            dropout=ARGS["drop_out"],
            loop=ARGS["loop"],
        )
        optimizer = Adam(
            model.parameters(),
            lr=10 ** -ARGS["lr"],
            weight_decay=10 ** -ARGS["weight_decay"],
        )
        # EarlyStopping은 상대경로 model/ 사용 → 절대경로로 오버라이드
        _ckpt_dir = str(MODEL_DIR)
        os.makedirs(_ckpt_dir, exist_ok=True)
        stopper = EarlyStopping(
            patience=ARGS["patience"],
            task_name=ARGS["task_name"],
            mode=ARGS["mode"],
            filename=os.path.join(_ckpt_dir, f"{ARGS['task_name']}_early_stop.pth"),
        )
        model.to(ARGS["device"])

        t0 = time.time()
        for epoch in range(ARGS["num_epochs"]):
            run_a_train_epoch_heterogeneous(
                ARGS, epoch, model, train_loader,
                loss_c0, loss_c1, loss_c2, loss_r, optimizer,
            )
            val_result = run_an_eval_epoch_heterogeneous(ARGS, model, val_loader)
            val_score = float(np.mean(val_result))
            early_stop = stopper.step(val_score, model)
            if (epoch + 1) % 10 == 0 or early_stop:
                elapsed = time.time() - t0
                print(
                    f"  epoch {epoch+1:3d}/{ARGS['num_epochs']}  "
                    f"val={val_score:.4f}  best={stopper.best_score:.4f}  "
                    f"elapsed={elapsed:.0f}s",
                    flush=True,
                )
            if early_stop:
                print(f"  [early stop] epoch {epoch+1}", flush=True)
                break

        # 최고 체크포인트 로드
        stopper.load_checkpoint(model)
        val_score_final = float(np.mean(run_an_eval_epoch_heterogeneous(ARGS, model, val_loader)))

        if val_score_final > best_val_score:
            best_val_score = val_score_final
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            print(f"  ★ 최고 모델 갱신: val={best_val_score:.4f}", flush=True)

        test_score = run_an_eval_epoch_heterogeneous(ARGS, model, test_loader)
        train_score = run_an_eval_epoch_heterogeneous(ARGS, model, train_loader)

        val_final_result = run_an_eval_epoch_heterogeneous(ARGS, model, val_loader)
        result = (
            train_score + ["training"]
            + val_final_result + ["valid"]
            + test_score + ["test"]
        )
        result_pd.loc[time_id] = result

        print(
            f"[{time_id+1}/{ARGS['times']}]  "
            f"train={train_score}  val={val_result}  test={test_score}",
            flush=True,
        )

    # 결과 저장
    result_pd.to_csv(RESULT_CSV, index=None)
    print(f"\n[결과] {RESULT_CSV}", flush=True)

    # 최고 모델 저장
    if best_model_state is not None:
        torch.save(best_model_state, CHECKPOINT_PATH)
        print(f"[checkpoint] 최고 모델 저장: {CHECKPOINT_PATH}  val={best_val_score:.4f}", flush=True)
    else:
        raise RuntimeError("학습된 모델 상태 없음 — 훈련 루프 실패")

    print("\n✅ A.A5Pc 재훈련 완료", flush=True)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    start = time.time()
    print(f"[A.A5Pc] pepADMET 재훈련 시작 — device={ARGS['device']}", flush=True)

    task_number, _ = build_bin()
    train_5fold(task_number)

    elapsed = time.time() - start
    h, rem = divmod(int(elapsed), 3600)
    m, s = divmod(rem, 60)
    print(f"[시간] {h:02d}:{m:02d}:{s:02d}", flush=True)


if __name__ == "__main__":
    main()
