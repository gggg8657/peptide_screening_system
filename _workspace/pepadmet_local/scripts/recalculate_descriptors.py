#!/usr/bin/env python3
"""recalculate_descriptors.py
=================================
A.A5Pb-data — Toxicity_extended.csv 신규 224 row descriptor 재계산

실행 방법:
    conda run -n pepadmet-upgrade python scripts/recalculate_descriptors.py

출력:
    _workspace/pepadmet_local/pepADMET/data/Toxicity_recalculated.csv
    _workspace/pepadmet_local/pepADMET/data/Toxicity_final.csv  (원본 135 + 재계산 224 + 정제 + 재분할)
    _workspace/pepadmet_local/scripts/descriptor_calc_report.json

작성: engineer-backend 2026-05-21
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Optional

import builtins as _builtins
_orig_print = _builtins.print

def _print(*args, **kwargs) -> None:
    """flush=True가 기본값인 print wrapper."""
    kwargs.setdefault("flush", True)
    _orig_print(*args, **kwargs)

# 전역 print를 flush=True 버전으로 교체
_builtins.print = _print

import pandas as pd
import numpy as np
from collections import Counter

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(SCRIPT_DIR, "..")
PEPADMET_DIR = os.path.join(WORKSPACE_DIR, "pepADMET")
DATA_DIR = os.path.join(PEPADMET_DIR, "data")

INPUT_CSV = os.path.join(DATA_DIR, "Toxicity_extended.csv")
OUTPUT_RECALC = os.path.join(DATA_DIR, "Toxicity_recalculated.csv")
OUTPUT_FINAL = os.path.join(DATA_DIR, "Toxicity_final.csv")
REPORT_JSON = os.path.join(SCRIPT_DIR, "descriptor_calc_report.json")

HEMOLYTIK2_CSV = "/tmp/hemolytik2_test.csv"

# ---------------------------------------------------------------------------
# 상수: 스킵할 비표준 서열 컴파운드에 대한 표준 아미노산 근사 서열
# FDA 승인 / 내인성 SS-bond cyclic 펩타이드 수동 매핑
# 참고: 비표준 AA(D-아미노산, Mpr, Orn)는 가장 가까운 L-AA로 근사
#        cyclic 구조는 선형 서열로 근사 (PyProtein 제한사항)
# ---------------------------------------------------------------------------

# MW → (compound_name, approx_sequence) 매핑
# 이 매핑은 MW 기반으로 화합물을 식별한다 (±1 Da 허용)
MW_TO_SEQUENCE: dict[str, tuple[str, str]] = {
    # MW range   compound_name             approx_sequence (L-AA near equivalent)
    "1018-1019": ("Octreotide",           "FCFWKTCT"),
    # D-Phe→F, D-Trp→W, Thr(ol)→T, cyclic SS Cys2-Cys7
    "1006-1007": ("Oxytocin",             "CYIQNCPLG"),
    # standard 9aa, cyclic SS Cys1-Cys6
    "1068-1069": ("Desmopressin",         "CYFQNCPRG"),
    # D-Arg→R near equiv, desamino-Cys1→C near equiv
    "993-994":   ("Atosiban",             "CYITNCPRG"),
    # Mpa→C, D-Tyr(Et)→Y, Thr4, Orn8→R (ornithine≈Arg)
    "831-832":   ("Eptifibatide",         "HARGDWPC"),
    # Mpr dropped, cyclic SS
    "1095-1096": ("Lanreotide",           "WCYWKVCT"),
    # D-2Nal→W, D-Trp→W, 8-residue cyclic SS
    "1083-1084": ("Arginine_vasopressin", "CYFQNCPRG"),
    # 9aa, Phe at 3, Arg at 8
    "1636-1637": ("Somatostatin-14",      "AGCKNFFWKTFTSC"),
    # exact known sequence
    "3429-3430": ("Calcitonin_salmon",    "CSNLSTCVLGKLSQELHKLQTYPRTNTGSGTP"),
    # 32aa, exact
    "1046-1047": ("Pasireotide",          "YWKVFY"),
    # synthetic cyclic hexapeptide: D-βNal→W, cycloHex→Y(approx), Tyr(OEt)→Y,
    # Lys→K, Val→V, 2-aminoindanyl→F(approx) — very rough approximation
    # Cyclotides
    "2966-2968": ("Kalata_B2",            "GLPVCGETCVGGTCNTPGCTCSWPVCTRN"),
    # 29aa cyclic cyclotide
    "3137-3139": ("Cycloviolacin_O2",     "GIPCGESCVWIPCISSAIGCSCKSKVCYRN"),
    # 30aa cyclic cyclotide
    "3108-3110": ("Cycloviolacin_H4",     "GIPCAESCVYIPCTVTALLGCSCKNKVCPKN"),
    # 31aa cyclic cyclotide
    "3280-3282": ("Kalata_B8",            "CDPILGLCGETCFGGTCNTPGCSCNYWPIC"),
    # 30aa cyclic cyclotide
    "2086-2088": ("RTD-2",                "RCICGRFCRCICGR"),
    # 13aa theta-defensin cyclic
}

# sequence 유효성: 표준 AA 20자 + 확장 (B=Asn/Asp, Z=Glu/Gln, X=any)
VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")


def mw_lookup_sequence(mw: float) -> Optional[str]:
    """MW로 수동 매핑 서열 반환. 매칭 실패 시 None."""
    for mw_range, (name, seq) in MW_TO_SEQUENCE.items():
        lo, hi = (float(x) for x in mw_range.split("-"))
        if lo <= mw <= hi:
            print(f"  [MW={mw:.1f}] → {name}: {seq[:30]}...")
            return seq
    return None


# ---------------------------------------------------------------------------
# PyBioMed + modlamp 임포트
# ---------------------------------------------------------------------------
try:
    from PyBioMed import Pymolecule
    from PyBioMed.PyProtein import PyProtein
    from modlamp.descriptors import GlobalDescriptor
    from rdkit import Chem
    from rdkit.Chem import Descriptors as RDKitDescriptors
    LIBS_OK = True
except ImportError as e:
    print(f"[ERROR] 필수 라이브러리 임포트 실패: {e}", file=sys.stderr)
    LIBS_OK = False


# ---------------------------------------------------------------------------
# calculate_descriptors (calculate_descriptors.py 기준 재사용)
# ---------------------------------------------------------------------------

def add_suffix_for_duplicates(dicts: list[dict], sources: list[str]) -> dict:
    all_keys: list[str] = []
    for d in dicts:
        all_keys.extend(d.keys())
    counter = Counter(all_keys)
    final_dict: dict = {}
    for d, source in zip(dicts, sources):
        for k, v in d.items():
            new_key = f"{k}_{source}" if counter[k] > 1 else k
            final_dict[new_key] = v
    return final_dict


def calculate_des(seq: str) -> dict:
    protein_class = PyProtein.PyProtein(seq)
    des: dict = {}
    des.update(protein_class.GetAAComp())
    des.update(protein_class.GetMoreauBrotoAuto())
    des.update(protein_class.GetQSO())
    des.update(protein_class.GetSOCN())
    des.update(protein_class.GetTriad())
    des.update(protein_class.GetCTD())
    des.update(protein_class.GetDPComp())
    return des


import signal as _signal


class _TimeoutError(Exception):
    pass


def _timeout_handler(signum: int, frame: object) -> None:
    raise _TimeoutError("descriptor calculation timeout")


def calculate_descriptors_one(smiles: str, sequence: str, timeout_sec: int = 90) -> dict:
    """단일 SMILES+시퀀스 쌍의 descriptor 계산 (signal.alarm timeout, Linux 전용)."""
    _signal.signal(_signal.SIGALRM, _timeout_handler)
    _signal.alarm(timeout_sec)
    try:
        mol = Pymolecule.PyMolecule()
        mol.ReadMolFromSmile(smiles)
        fp_SM = mol.GetAllDescriptor()

        des = calculate_des(sequence)

        desc = GlobalDescriptor(sequence)
        desc.calculate_all(amide=False)
        desc_dic = dict(zip(desc.featurenames, desc.descriptor.flatten().tolist()))

        fp = add_suffix_for_duplicates(
            [fp_SM, des, desc_dic],
            ["Pymolecule", "PyProtein", "modlamp"],
        )
        fp["SMILES"] = smiles
        fp["SEQUENCE"] = sequence
        _signal.alarm(0)  # 타이머 해제
        return fp
    except _TimeoutError:
        _signal.alarm(0)
        return {"Error": f"timeout after {timeout_sec}s", "SMILES": smiles, "SEQUENCE": sequence}
    except Exception as e:
        _signal.alarm(0)
        return {"Error": f"calc failed: {str(e)}", "SMILES": smiles, "SEQUENCE": sequence}


# ---------------------------------------------------------------------------
# SMILES 검증 + 중복 제거
# ---------------------------------------------------------------------------

def validate_and_dedup_smiles(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """SMILES RDKit 검증 + 정규화 + 중복 제거."""
    report: dict = {"total_input": len(df)}

    # RDKit 검증
    valid_mask = df["smiles"].apply(
        lambda s: Chem.MolFromSmiles(str(s)) is not None if pd.notna(s) else False
    )
    invalid_count = (~valid_mask).sum()
    report["invalid_smiles_removed"] = int(invalid_count)
    if invalid_count > 0:
        print(f"  ⚠ 유효하지 않은 SMILES {invalid_count}개 제거")
    df = df[valid_mask].copy()

    # RDKit canonical SMILES 표준화
    df["smiles_canonical"] = df["smiles"].apply(
        lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(str(s)))
    )

    # 중복 제거 (canonical SMILES 기준, 첫 번째 유지)
    before_dedup = len(df)
    df = df.drop_duplicates(subset="smiles_canonical", keep="first")
    report["duplicates_removed"] = before_dedup - len(df)
    if report["duplicates_removed"] > 0:
        print(f"  ⚠ 중복 SMILES {report['duplicates_removed']}개 제거")

    df = df.drop(columns=["smiles_canonical"])
    report["after_validation"] = len(df)
    return df, report


# ---------------------------------------------------------------------------
# train/valid/test 재분할
# ---------------------------------------------------------------------------

def resplit_groups(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """binary_toxicity 라벨 있는 행 기준 8:1:1 stratified split.

    라벨 없는 행(NaN)은 training으로 배정.
    """
    rng = np.random.default_rng(seed)
    df = df.copy()
    df["group"] = "training"  # 초기화

    # 라벨 있는 행 (binary_toxicity, toxicity_nontoxicity 등)
    if "toxicity_nontoxicity" in df.columns:
        label_col = "toxicity_nontoxicity"
    else:
        label_col = None

    if label_col is None:
        return df

    labeled_mask = df[label_col].notna()
    labeled_df = df[labeled_mask].copy()

    # 클래스별 분할
    for label_val in labeled_df[label_col].unique():
        cls_idx = labeled_df[labeled_df[label_col] == label_val].index.tolist()
        n = len(cls_idx)
        shuffled = list(rng.permutation(cls_idx))

        n_test = max(1, round(n * 0.1))
        n_valid = max(1, round(n * 0.1))

        test_idx = shuffled[:n_test]
        valid_idx = shuffled[n_test : n_test + n_valid]

        df.loc[test_idx, "group"] = "test"
        df.loc[valid_idx, "group"] = "valid"
        # 나머지는 training (이미 초기화)

    return df


# ---------------------------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------------------------

def main() -> None:
    if not LIBS_OK:
        print("[ABORT] 라이브러리 임포트 실패. pepadmet-upgrade env 활성화 확인.", file=sys.stderr)
        sys.exit(1)

    report: dict = {"steps": {}}

    # ------------------------------------------------------------------
    # Step 1: 입력 데이터 로드
    # ------------------------------------------------------------------
    print("\n[Step 1] Toxicity_extended.csv 로드")
    df = pd.read_csv(INPUT_CSV)
    print(f"  입력 shape: {df.shape}")

    protein_cols = [c for c in df.columns if "MoreauBroto" in c]
    existing_rows = df[df[protein_cols[0]].notna()].copy()
    new_rows = df[df[protein_cols[0]].isna()].copy().reset_index(drop=True)
    print(f"  기존 행 (descriptor 있음): {len(existing_rows)}")
    print(f"  신규 행 (descriptor NaN): {len(new_rows)}")
    report["steps"]["step1"] = {
        "existing_rows": len(existing_rows),
        "new_rows": len(new_rows),
    }

    # ------------------------------------------------------------------
    # Step 2: 신규 행 SMILES 검증 + 중복 제거
    # ------------------------------------------------------------------
    print("\n[Step 2] 신규 행 SMILES 검증 + 중복 제거")
    new_rows, validation_report = validate_and_dedup_smiles(new_rows)
    report["steps"]["step2"] = validation_report
    print(f"  정제 후 신규 행: {len(new_rows)}")

    # ------------------------------------------------------------------
    # Step 3: 시퀀스 매핑
    # ------------------------------------------------------------------
    print("\n[Step 3] 시퀀스 매핑 (Hemolytik2 SMILES 매칭 + FDA/cyclotide 수동)")
    h2 = pd.read_csv(HEMOLYTIK2_CSV)
    h2_dedup = h2.drop_duplicates(subset="smiles")[["smiles", "seq"]]

    new_rows = new_rows.merge(h2_dedup, on="smiles", how="left")
    h2_matched = new_rows["seq"].notna().sum()
    print(f"  Hemolytik2 SMILES 매칭: {h2_matched}/{len(new_rows)}")

    # MW 기반 수동 매핑
    manual_count = 0
    for idx, row in new_rows[new_rows["seq"].isna()].iterrows():
        mol = Chem.MolFromSmiles(str(row["smiles"]))
        if mol is None:
            continue
        mw = RDKitDescriptors.ExactMolWt(mol)
        seq = mw_lookup_sequence(mw)
        if seq:
            new_rows.at[idx, "seq"] = seq
            manual_count += 1

    still_missing = new_rows["seq"].isna().sum()
    report["steps"]["step3"] = {
        "h2_matched": int(h2_matched),
        "manual_mapped": int(manual_count),
        "still_missing_seq": int(still_missing),
    }
    print(f"  수동 매핑: {manual_count}개")
    if still_missing > 0:
        print(f"  ⚠ 시퀀스 미확보: {still_missing}개 → PyProtein 계산 스킵")

    # ------------------------------------------------------------------
    # Step 4: Descriptor 계산
    # ------------------------------------------------------------------
    print(f"\n[Step 4] Descriptor 계산 (총 {len(new_rows)}개)")

    # 기존 descriptor 컬럼 목록 (정렬 기준용)
    desc_cols = [c for c in df.columns if c not in ["toxicity_nontoxicity", "toxicity_type_class",
                                                      "neurotoxicity_type_class", "HC50", "group", "smiles"]]

    results: list[dict] = []
    errors: list[dict] = []

    for i, (_, row) in enumerate(new_rows.iterrows()):
        smiles = str(row["smiles"])
        seq = str(row["seq"]) if pd.notna(row["seq"]) else None

        if i % 20 == 0:
            print(f"  [{i+1}/{len(new_rows)}] processing...")

        if seq is None:
            # 시퀀스 없음 → PyProtein / modlamp 제외, 분자 descriptor만 계산 후 NaN 패딩
            try:
                mol = Pymolecule.PyMolecule()
                mol.ReadMolFromSmile(smiles)
                fp_SM = mol.GetAllDescriptor()
                fp_SM["SMILES"] = smiles
                fp_SM["SEQUENCE"] = ""
                fp_SM["_calc_partial"] = True
                results.append(fp_SM)
            except Exception as e:
                errors.append({"smiles": smiles, "error": str(e), "row_idx": i})
                results.append({"SMILES": smiles, "SEQUENCE": "", "Error": str(e)})
        else:
            result = calculate_descriptors_one(smiles, seq)
            if "Error" in result:
                errors.append({"smiles": smiles, "error": result["Error"], "seq": seq, "row_idx": i})
            results.append(result)

    calc_errors = [r for r in results if "Error" in r]
    calc_success = len(results) - len(calc_errors)
    report["steps"]["step4"] = {
        "total": len(new_rows),
        "success": calc_success,
        "errors": len(calc_errors),
        "error_details": errors[:10],  # 최대 10개
    }
    print(f"  계산 완료: {calc_success}/{len(new_rows)} (오류: {len(calc_errors)}개)")
    if errors:
        print(f"  ⚠ 오류 상세 (첫 3개):")
        for e in errors[:3]:
            print(f"    - SMILES={e['smiles'][:40]} | {e['error'][:80]}")

    # ------------------------------------------------------------------
    # Step 5: descriptor DataFrame 구성 + 기존 label 컬럼 재결합
    # ------------------------------------------------------------------
    print("\n[Step 5] DataFrame 구성")
    results_df = pd.DataFrame(results)

    # 원본 CSV 컬럼 순서에 맞춰 재구성
    label_cols = ["toxicity_nontoxicity", "toxicity_type_class",
                  "neurotoxicity_type_class", "HC50", "group", "smiles"]

    # 기존 desc_cols에서 SMILES/SEQUENCE 제외
    target_desc_cols = [c for c in df.columns if c not in label_cols]

    # results_df에서 target_desc_cols에 해당하는 컬럼 추출
    available_desc = [c for c in target_desc_cols if c in results_df.columns]
    missing_desc = [c for c in target_desc_cols if c not in results_df.columns]

    print(f"  descriptor 컬럼 매칭: {len(available_desc)}/{len(target_desc_cols)}")
    if missing_desc:
        print(f"  ⚠ 누락 descriptor {len(missing_desc)}개 → NaN 패딩")

    # label 컬럼 + descriptor 컬럼 결합
    new_rows_labels = new_rows[label_cols].copy().reset_index(drop=True)
    results_df = results_df.reset_index(drop=True)

    # descriptor 컬럼 순서 맞춰 추출
    desc_data = results_df.reindex(columns=target_desc_cols)

    new_rows_full = pd.concat([new_rows_labels, desc_data], axis=1)

    # 원본 CSV 컬럼 순서 맞추기
    new_rows_full = new_rows_full.reindex(columns=df.columns)

    report["steps"]["step5"] = {
        "desc_cols_matched": len(available_desc),
        "desc_cols_missing": len(missing_desc),
    }

    # ------------------------------------------------------------------
    # Step 6: 저장 (재계산 행만)
    # ------------------------------------------------------------------
    new_rows_full.to_csv(OUTPUT_RECALC, index=False)
    print(f"\n[Step 6] 재계산 결과 저장: {OUTPUT_RECALC}")
    print(f"  저장 shape: {new_rows_full.shape}")

    # ------------------------------------------------------------------
    # Step 7: 원본 135 + 재계산 224 결합 + train/valid/test 재분할
    # ------------------------------------------------------------------
    print("\n[Step 7] 원본 + 재계산 결합 + 재분할")

    # 기존 135 행 SMILES 검증 + 중복 제거 (reuse validate fn)
    existing_validated, existing_report = validate_and_dedup_smiles(existing_rows)
    report["steps"]["step7_existing_validation"] = existing_report

    combined = pd.concat([existing_validated, new_rows_full], ignore_index=True)
    print(f"  결합 전 총 행: {len(combined)}")

    # 전체 중복 제거 (기존 vs 신규 SMILES 중복)
    combined["smiles_canonical"] = combined["smiles"].apply(
        lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(str(s)))
        if pd.notna(s) and Chem.MolFromSmiles(str(s)) is not None else None
    )
    before_final_dedup = len(combined)
    combined = combined.dropna(subset=["smiles_canonical"])
    combined = combined.drop_duplicates(subset=["smiles_canonical"], keep="first")
    combined = combined.drop(columns=["smiles_canonical"])
    final_dedup_removed = before_final_dedup - len(combined)
    print(f"  최종 중복 제거: {final_dedup_removed}개 → 최종 {len(combined)}행")

    # 재분할
    combined = resplit_groups(combined, seed=42)
    group_dist = combined["group"].value_counts().to_dict()
    print(f"  재분할 결과: {group_dist}")

    combined.to_csv(OUTPUT_FINAL, index=False)
    print(f"\n[Step 8] 최종 파일 저장: {OUTPUT_FINAL}")
    print(f"  최종 shape: {combined.shape}")

    report["steps"]["step7"] = {
        "combined_before_dedup": before_final_dedup,
        "final_dedup_removed": final_dedup_removed,
        "final_rows": len(combined),
        "group_distribution": group_dist,
    }
    report["output_files"] = {
        "recalculated": OUTPUT_RECALC,
        "final": OUTPUT_FINAL,
    }

    # ------------------------------------------------------------------
    # 리포트 저장
    # ------------------------------------------------------------------
    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n[리포트] {REPORT_JSON}")
    print("\n✅ A.A5Pb-data 완료")


if __name__ == "__main__":
    main()
