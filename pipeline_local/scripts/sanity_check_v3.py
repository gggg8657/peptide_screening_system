#!/usr/bin/env python3
"""sanity_check_v3.py
======================
A.A5Pd — 재훈련 모델 sanity check (v3 정책)

조건 (모두 충족 필수 — 하나라도 실패 시 abort):
  1. Octreotide binary_toxicity_pred < 0.5 (비독성 기준)
  2. SST-14 binary_toxicity_pred < 0.5 (비독성 기준)
  3. PRST-001~004 예측값 range ≥ 0.2 (모델 변별력 검증)

사용법:
    conda run -n pepadmet-upgrade python scripts/sanity_check_v3.py \\
        --model_path pepADMET/model/toxicity_retrained_2026-05-21.pth

실패 시 sys.exit(1) 반환 → CI/CD에서 abort 트리거 가능.

작성: engineer-backend 2026-05-21 (Task #12)
"""
from __future__ import annotations

import argparse
import os
import sys
import signal
from pathlib import Path
from typing import Optional

# pepADMET 경로 (GPL v3 — _workspace/pepadmet_local/pepADMET/ 에 저장, git 미추적)
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

from utils.build_dataset import construct_RGCN_bigraph_from_smiles
from utils.MY_GNN import MGA

# ---------------------------------------------------------------------------
# 테스트 분자 (SMILES + 기대값)
# ---------------------------------------------------------------------------

# Octreotide (D-Phe, D-Trp) — 비독성, 임상 승인 펩타이드
OCTREOTIDE_SMILES = (
    "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H]("
    "NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)"
    "NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@H](N)Cc1ccccc1"
    ")[C@H](C)O)C(=O)O"
)

# SST-14 linear form (AGCKNFFWKTFTSC) — 비독성 기준 펩타이드
SST14_SMILES = (
    "N[C@@H](C)C(=O)NCC(=O)N[C@@H](CS)C(=O)N[C@@H](CCCCN)C(=O)"
    "N[C@@H](CC(N)=O)C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@@H](Cc1ccccc1)C(=O)"
    "N[C@@H](Cc1c[nH]c2ccccc12)C(=O)N[C@@H](CCCCN)C(=O)"
    "N[C@H](C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@H]("
    "C(=O)N[C@@H](CO)C(=O)N[C@@H](CS)C(=O)O)[C@H](C)O)[C@H](C)O"
)

# PRST-001~004 — pipeline 생성 후보
PRST_SMILES: dict[str, str] = {
    "PRST-001": (
        "C[C@H](N)C(=O)NCC(=O)N[C@@H](CS)C(=O)N[C@@H](CCCCN)C(=O)"
        "N[C@@H](CC(N)=O)C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@@H](Cc1ccccc1)C(=O)"
        "N[C@@H](Cc1c[nH]c2ccccc12)C(=O)N[C@@H](CCCCN)C(=O)"
        "N[C@H](C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@H]("
        "C(=O)N[C@@H](CO)C(=O)N[C@@H](CS)C(=O)O)[C@H](C)O)[C@H](C)O"
    ),
    "PRST-002": (
        "C[C@H](N)C(=O)NCC(=O)N[C@@H](CS)C(=O)N[C@@H](CCCCN)C(=O)"
        "N[C@@H](CC(N)=O)C(=O)N[C@@H](Cc1ccc(O)cc1)C(=O)N[C@@H](Cc1ccccc1)C(=O)"
        "N[C@@H](Cc1c[nH]c2ccccc12)C(=O)N[C@@H](CCCCN)C(=O)"
        "N[C@H](C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@H]("
        "C(=O)N[C@@H](CO)C(=O)N[C@@H](CS)C(=O)O)[C@H](C)O)[C@H](C)O"
    ),
    "PRST-003": (
        "C[C@H](N)C(=O)NCC(=O)N[C@@H](CS)C(=O)N[C@@H](CCCCN)C(=O)"
        "N[C@@H](CC(N)=O)C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@@H](Cc1ccccc1)C(=O)"
        "N[C@@H](Cc1c[nH]c2ccccc12)C(=O)N[C@@H](CCCCN)C(=O)"
        "N[C@H](C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@H]("
        "C(=O)N[C@@H](C)C(=O)N[C@@H](CS)C(=O)O)[C@H](C)O)[C@H](C)O"
    ),
    "PRST-004": (
        "C[C@H](N)C(=O)NCC(=O)N[C@@H](CS)C(=O)N[C@@H](CCCCN)C(=O)"
        "N[C@@H](CC(N)=O)C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@@H](Cc1ccccc1)C(=O)"
        "N[C@@H](Cc1c[nH]c2ccccc12)C(=O)N[C@@H](CCCCN)C(=O)"
        "N[C@H](C(=O)N[C@@H](Cc1ccccc1)C(=O)N[C@H]("
        "C(=O)N[C@@H](CO)C(=O)N[C@@H](CS)C(=O)O)[C@H](C)O)[C@H](C)O"
    ),
}

# ---------------------------------------------------------------------------
# 모델 args (Train.ipynb / retrain_toxicity.py 동기화)
# ---------------------------------------------------------------------------

DEFAULT_ARGS: dict = {
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "atom_data_field": "atom",
    "bond_data_field": "etype",
    "descriptor_dim": 2133,
    "descriptor": 2133,
    "fpn_out": 2133,
    "fp_2_dim": 512,
    "hidden_size": 256,
    "in_feats": 40,
    "rgcn_hidden_feats": [64, 64],
    "classifier_hidden_feats": 320,
    "rgcn_drop_out": 0.2,
    "drop_out": 0.2,
    "loop": True,
    "select_task_list": [
        "toxicity_nontoxicity",
        "toxicity_type_class",
        "neurotoxicity_type_class",
        "HC50",
    ],
}


# ---------------------------------------------------------------------------
# 유틸: 단일 SMILES에 대해 descriptor → dummy zeros (추론 시 descriptor=0)
# ---------------------------------------------------------------------------

def _predict_single(model: MGA, smiles: str, args: dict) -> float:
    """단일 SMILES → task_0 sigmoid 예측값 반환.

    descriptor는 0으로 채운다 (unknown 분자 추론 프록시).
    실제 운영에서는 descriptor를 계산해야 하지만,
    sanity check에서는 descriptor=0 기반으로 상대 비교한다.
    """
    try:
        g = construct_RGCN_bigraph_from_smiles(smiles)
    except Exception as e:
        raise RuntimeError(f"SMILES 그래프 변환 실패: {smiles[:60]} — {e}")

    import dgl
    bg = dgl.batch([g]).to(args["device"])
    descriptor = torch.zeros(1, args["descriptor_dim"])

    atom_feats = bg.ndata.pop(args["atom_data_field"]).float().to(args["device"])
    bond_feats = bg.edata.pop(args["bond_data_field"]).long().to(args["device"])

    model.eval()
    with torch.no_grad():
        logits = model(bg, atom_feats, bond_feats, descriptor)

    pred = float(torch.sigmoid(logits["task_0"]).squeeze().cpu())
    return pred


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
    # EarlyStopping이 {'model_state_dict': ...} 형태로 저장
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    model.load_state_dict(state)
    model.to(args["device"])
    model.eval()
    print(f"[model] 로드: {model_path}", flush=True)
    return model


# ---------------------------------------------------------------------------
# 메인 sanity check
# ---------------------------------------------------------------------------

def run_sanity_check(model_path: str) -> None:
    """v3 sanity check 실행. 실패 시 sys.exit(1)."""
    args = dict(DEFAULT_ARGS)
    print(f"\n[A.A5Pd] Sanity Check v3  device={args['device']}", flush=True)

    model = _load_model(model_path, args)

    results: dict[str, float] = {}

    # Octreotide
    print("\n[1/6] Octreotide 추론...", flush=True)
    results["Octreotide"] = _predict_single(model, OCTREOTIDE_SMILES, args)
    print(f"  Octreotide binary_toxicity_pred = {results['Octreotide']:.4f}", flush=True)

    # SST-14
    print("\n[2/6] SST-14 추론...", flush=True)
    results["SST-14"] = _predict_single(model, SST14_SMILES, args)
    print(f"  SST-14 binary_toxicity_pred = {results['SST-14']:.4f}", flush=True)

    # PRST-001~004
    for i, (name, smiles) in enumerate(PRST_SMILES.items(), start=3):
        print(f"\n[{i}/6] {name} 추론...", flush=True)
        results[name] = _predict_single(model, smiles, args)
        print(f"  {name} binary_toxicity_pred = {results[name]:.4f}", flush=True)

    # ---------------------------------------------------------------------------
    # Check 1: Octreotide < 0.5
    # ---------------------------------------------------------------------------
    print("\n" + "="*60, flush=True)
    print("[CHECK 1] Octreotide < 0.5", flush=True)
    oct_score = results["Octreotide"]
    if oct_score >= 0.5:
        print(f"  ❌ FAIL: Octreotide = {oct_score:.4f} ≥ 0.5", flush=True)
        print("  → 모델이 안전한 임상 펩타이드를 독성으로 분류 — 재훈련 필요", flush=True)
        _abort()
    print(f"  ✅ PASS: Octreotide = {oct_score:.4f} < 0.5", flush=True)

    # ---------------------------------------------------------------------------
    # Check 2: SST-14 < 0.5
    # ---------------------------------------------------------------------------
    print("[CHECK 2] SST-14 < 0.5", flush=True)
    sst_score = results["SST-14"]
    if sst_score >= 0.5:
        print(f"  ❌ FAIL: SST-14 = {sst_score:.4f} ≥ 0.5", flush=True)
        print("  → 모델이 SST-14를 독성으로 분류 — 재훈련 필요", flush=True)
        _abort()
    print(f"  ✅ PASS: SST-14 = {sst_score:.4f} < 0.5", flush=True)

    # ---------------------------------------------------------------------------
    # Check 3: PRST range ≥ 0.2
    # ---------------------------------------------------------------------------
    print("[CHECK 3] PRST-001~004 range ≥ 0.2", flush=True)
    prst_scores = [results[k] for k in PRST_SMILES]
    prst_range = max(prst_scores) - min(prst_scores)
    print(
        f"  PRST scores: {[f'{s:.4f}' for s in prst_scores]}\n"
        f"  range = max - min = {max(prst_scores):.4f} - {min(prst_scores):.4f} = {prst_range:.4f}",
        flush=True,
    )
    if prst_range < 0.2:
        print(
            f"  ❌ FAIL: PRST range = {prst_range:.4f} < 0.2\n"
            "  → 모델이 후보 간 변별력 없음 — 재훈련 필요",
            flush=True,
        )
        _abort()
    print(f"  ✅ PASS: PRST range = {prst_range:.4f} ≥ 0.2", flush=True)

    # ---------------------------------------------------------------------------
    # All passed
    # ---------------------------------------------------------------------------
    print("\n" + "="*60, flush=True)
    print("✅ Sanity Check v3 모두 통과", flush=True)
    print("="*60, flush=True)

    # 결과 저장
    _save_results(results, model_path)


def _abort() -> None:
    print("\n[ABORT] Sanity Check 실패 — Task #12 즉시 중단", flush=True)
    sys.exit(1)


def _save_results(results: dict[str, float], model_path: str) -> None:
    """결과를 JSON으로 저장."""
    import json
    out = {
        "model_path": model_path,
        "predictions": results,
        "status": "PASS",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    out_path = Path(model_path).parent / "sanity_check_v3_result.json"
    with open(str(out_path), "w") as f:
        json.dump(out, f, indent=2)
    print(f"[결과] {out_path}", flush=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="pepADMET sanity check v3")
    _default_model = str(
        _REPO_ROOT / "_workspace" / "pepadmet_local" / "pepADMET"
        / "model" / "toxicity_retrained_2026-05-21.pth"
    )
    parser.add_argument(
        "--model_path",
        default=_default_model,
        help="재훈련 모델 체크포인트 경로 (default: _workspace/pepadmet_local/pepADMET/model/toxicity_retrained_2026-05-21.pth)",
    )
    args_ns = parser.parse_args()
    run_sanity_check(args_ns.model_path)


if __name__ == "__main__":
    main()
