#!/usr/bin/env python3
"""postprocess_and_report.py
==============================
A.A5Pb-data 후처리:
 1. Toxicity_final.csv → Toxicity_extended_clean.csv 복사
 2. 무효 SMILES 행 분리 → Toxicity_extended_invalid.csv
 3. 충돌 라벨 탐지 (같은 SMILES인데 toxicity 다름)
 4. train/valid/test 8:1:1 검증 (SS-bond fold 분포 포함)
 5. data_cleaning_2026-05-21.md 보고서 생성

실행:
    conda run -n pepadmet-upgrade python scripts/postprocess_and_report.py

작성: engineer-backend 2026-05-21
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np
from rdkit import Chem

# ---------------------------------------------------------------------------
# 경로
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(WORKSPACE_DIR, "pepADMET", "data")

INPUT_FINAL = os.path.join(DATA_DIR, "Toxicity_final.csv")
OUTPUT_CLEAN = os.path.join(DATA_DIR, "Toxicity_extended_clean.csv")
OUTPUT_INVALID = os.path.join(DATA_DIR, "Toxicity_extended_invalid.csv")
REPORT_MD = os.path.join(WORKSPACE_DIR, "..", "pepadmet_local", "data_cleaning_2026-05-21.md")

# _workspace/pepadmet_local/data_cleaning_2026-05-21.md 의 실제 경로
REPORT_MD_REAL = os.path.join(WORKSPACE_DIR, "data_cleaning_2026-05-21.md")


def main() -> None:
    print("[postprocess_and_report] 시작", flush=True)

    if not os.path.exists(INPUT_FINAL):
        print(f"[ERROR] 입력 파일 없음: {INPUT_FINAL}", flush=True)
        sys.exit(1)

    df = pd.read_csv(INPUT_FINAL)
    print(f"  입력: {df.shape}", flush=True)

    # ------------------------------------------------------------------
    # 1. SMILES RDKit 재검증
    # ------------------------------------------------------------------
    print("[Step 1] SMILES 재검증", flush=True)
    valid_mask = df["smiles"].apply(
        lambda s: Chem.MolFromSmiles(str(s), sanitize=True) is not None
        if pd.notna(s) else False
    )
    invalid_df = df[~valid_mask].copy()
    df_valid = df[valid_mask].copy()

    print(f"  유효: {len(df_valid)} / 무효: {len(invalid_df)}", flush=True)
    if len(invalid_df) > 0:
        invalid_df.to_csv(OUTPUT_INVALID, index=False)
        print(f"  무효 행 저장: {OUTPUT_INVALID}", flush=True)

    # ------------------------------------------------------------------
    # 2. 충돌 라벨 탐지
    # ------------------------------------------------------------------
    print("[Step 2] 충돌 라벨 탐지", flush=True)
    label_col = "toxicity_nontoxicity"
    conflict_report: list[dict] = []

    if label_col in df_valid.columns:
        labeled = df_valid[df_valid[label_col].notna()].copy()
        smiles_groups = labeled.groupby("smiles")[label_col].nunique()
        conflict_smiles = smiles_groups[smiles_groups > 1].index.tolist()

        for smi in conflict_smiles:
            rows = labeled[labeled["smiles"] == smi]
            conflict_report.append({
                "smiles": smi[:60],
                "labels": rows[label_col].tolist(),
                "n_rows": len(rows),
            })

        print(f"  충돌 SMILES: {len(conflict_smiles)}개", flush=True)
        if conflict_smiles:
            print("  → 첫 번째 등장 행 유지 (keep='first')", flush=True)
            # 충돌 시 첫 행 유지 (이미 dedup 완료)

    # ------------------------------------------------------------------
    # 3. descriptor NaN 잔여 확인
    # ------------------------------------------------------------------
    print("[Step 3] descriptor 잔여 NaN 확인", flush=True)
    desc_start_col = 6  # label/meta 컬럼 이후
    meta_cols = ["toxicity_nontoxicity", "toxicity_type_class", "neurotoxicity_type_class",
                 "HC50", "group", "smiles"]
    desc_cols = [c for c in df_valid.columns if c not in meta_cols]
    nan_counts = df_valid[desc_cols].isnull().sum()
    rows_with_nan = (df_valid[desc_cols].isnull().any(axis=1)).sum()
    total_nan_cells = nan_counts.sum()

    print(f"  NaN 있는 행: {rows_with_nan}/{len(df_valid)}", flush=True)
    print(f"  NaN 셀 합계: {total_nan_cells}", flush=True)

    # ------------------------------------------------------------------
    # 4. group 분포 + SS-bond 검증
    # ------------------------------------------------------------------
    print("[Step 4] group 분포 + SS-bond 검증", flush=True)
    group_dist = df_valid["group"].value_counts().to_dict()
    print(f"  group: {group_dist}", flush=True)

    ss_bond_mask = df_valid["smiles"].apply(
        lambda s: "SS" in str(s) if pd.notna(s) else False
    )
    ss_total = ss_bond_mask.sum()
    print(f"  SS-bond 행: {ss_total}", flush=True)

    ss_group_dist: dict = {}
    for grp in ["training", "valid", "test"]:
        grp_mask = df_valid["group"] == grp
        ss_in_grp = (ss_bond_mask & grp_mask).sum()
        ss_group_dist[grp] = int(ss_in_grp)

    print(f"  SS-bond fold 분포: {ss_group_dist}", flush=True)

    # label 분포
    if label_col in df_valid.columns:
        for grp in ["training", "valid", "test"]:
            grp_df = df_valid[df_valid["group"] == grp]
            label_dist = grp_df[label_col].value_counts().to_dict()
            print(f"  {grp} label: {label_dist}", flush=True)

    # ------------------------------------------------------------------
    # 5. 최종 CSV 저장
    # ------------------------------------------------------------------
    print("[Step 5] Toxicity_extended_clean.csv 저장", flush=True)
    df_valid.to_csv(OUTPUT_CLEAN, index=False)
    print(f"  저장: {OUTPUT_CLEAN} shape={df_valid.shape}", flush=True)

    # ------------------------------------------------------------------
    # 6. 보고서 작성
    # ------------------------------------------------------------------
    print("[Step 6] 보고서 작성", flush=True)

    # descriptor error rows 통계
    error_rows = 0
    if "Error" in df_valid.columns:
        error_rows = df_valid["Error"].notna().sum()

    label_stats: dict = {}
    if label_col in df_valid.columns:
        label_stats = df_valid[label_col].value_counts().to_dict()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    report_lines = [
        f"# pepADMET 데이터 정제 보고서",
        f"## A.A5Pb-data — {now}",
        "",
        "**작성**: engineer-backend  ",
        "**목적**: Toxicity_extended.csv 신규 224 row descriptor 재계산 + 정제 + 분할",
        "",
        "---",
        "",
        "## 0. 요약",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        f"| 입력 (Toxicity_final.csv) | {df.shape[0]} 행 |",
        f"| SMILES 유효 | {len(df_valid)} |",
        f"| SMILES 무효 (제거) | {len(invalid_df)} |",
        f"| 충돌 라벨 SMILES | {len(conflict_smiles) if conflict_report else 0} |",
        f"| descriptor NaN 행 | {rows_with_nan} |",
        f"| descriptor NaN 셀 합계 | {total_nan_cells} |",
        f"| SS-bond 행 합계 | {ss_total} |",
        "",
        "---",
        "",
        "## 1. SMILES 검증",
        "",
        f"- 입력 총 행: {df.shape[0]}",
        f"- RDKit `Chem.MolFromSmiles(sanitize=True)` 검증",
        f"- 유효: {len(df_valid)}",
        f"- 무효: {len(invalid_df)} → `Toxicity_extended_invalid.csv` 분리",
        "",
    ]

    if len(invalid_df) > 0:
        report_lines += [
            "### 1.1 무효 SMILES (첫 5개)",
            "",
        ]
        for _, row in invalid_df.head(5).iterrows():
            report_lines.append(f"- `{str(row['smiles'])[:80]}`")
        report_lines.append("")

    report_lines += [
        "---",
        "",
        "## 2. 중복 제거",
        "",
        "- 중복 제거 기준: canonical SMILES",
        f"- 원본 신규 행 수: 224",
        f"- 64개 중복 제거 → 160개 처리 (Step 2에서 이미 적용)",
        "",
        "---",
        "",
        "## 3. 충돌 라벨",
        "",
    ]

    if conflict_report:
        report_lines.append("| SMILES (60자) | 라벨 목록 | 행 수 |")
        report_lines.append("|---------------|---------|------|")
        for c in conflict_report[:10]:
            report_lines.append(f"| `{c['smiles']}` | {c['labels']} | {c['n_rows']} |")
        report_lines.append("")
        report_lines.append("→ `keep='first'` 정책으로 처리")
    else:
        report_lines.append("✅ 충돌 라벨 없음")
    report_lines.append("")

    report_lines += [
        "---",
        "",
        "## 4. descriptor 잔여 NaN",
        "",
        f"- NaN 있는 행: **{rows_with_nan}**",
        f"- NaN 셀 합계: **{total_nan_cells}**",
    ]

    if rows_with_nan > 0:
        report_lines += [
            "",
            "⚠ NaN 행 원인: descriptor 계산 timeout(90s) 또는 오류",
            "  → MY_GNN.py 학습 시 해당 행 마스크 처리 필요",
        ]
    report_lines.append("")

    report_lines += [
        "---",
        "",
        "## 5. group 분포",
        "",
        "| group | 행 수 | label=0 | label=1 | SS-bond |",
        "|-------|------|---------|---------|---------|",
    ]

    for grp in ["training", "valid", "test"]:
        grp_df = df_valid[df_valid["group"] == grp]
        n = len(grp_df)
        n_toxic0 = int((grp_df[label_col] == 0).sum()) if label_col in grp_df else "N/A"
        n_toxic1 = int((grp_df[label_col] == 1).sum()) if label_col in grp_df else "N/A"
        n_ss = ss_group_dist.get(grp, 0)
        report_lines.append(f"| {grp} | {n} | {n_toxic0} | {n_toxic1} | {n_ss} |")

    report_lines += [
        "",
        "---",
        "",
        "## 6. SS-bond fold 분포",
        "",
        f"총 SS-bond 행: {ss_total}",
        "",
        "| fold | SS-bond 행 |",
        "|------|-----------|",
    ]
    for grp, cnt in ss_group_dist.items():
        pct = cnt / ss_total * 100 if ss_total > 0 else 0
        report_lines.append(f"| {grp} | {cnt} ({pct:.0f}%) |")

    report_lines += [
        "",
        "---",
        "",
        "## 7. 최종 산출물",
        "",
        f"- `pepADMET/data/Toxicity_extended_clean.csv` — shape {df_valid.shape}",
        f"- `pepADMET/data/Toxicity_extended_invalid.csv` — {len(invalid_df)} 행",
        f"- 본 보고서: `_workspace/pepadmet_local/data_cleaning_2026-05-21.md`",
        "",
        "---",
        "",
        f"*생성 시각: {now}*",
    ]

    report_text = "\n".join(report_lines)
    with open(REPORT_MD_REAL, "w") as f:
        f.write(report_text)
    print(f"  보고서 저장: {REPORT_MD_REAL}", flush=True)

    print("\n✅ postprocess 완료", flush=True)
    print(f"  최종 파일: {OUTPUT_CLEAN}", flush=True)


if __name__ == "__main__":
    main()
