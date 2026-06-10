#!/usr/bin/env python3
"""PEPlife2 merged JSON → 학습용 CSV (t½ → 시간 단위, SMILES 시도).

동작 범위: _workspace/pepmsnd_local/ 만 사용.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from rdkit import Chem
except ImportError:
    Chem = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "peplife2_raw" / "peplife2_merged.json"
PROC = ROOT / "data" / "peplife2_processed"


def _first_float(text: str) -> float | None:
    if not text or not isinstance(text, str):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", text.replace("±", " "))
    if not m:
        return None
    return float(m.group(1))


def to_hours(value: float, units: str | None) -> float | None:
    if units is None:
        return None
    u = units.strip().lower()
    if u in ("n.a.", "no units", ""):
        return None
    if "hour" in u:
        return value
    if "minute" in u or u == "minute":
        return value / 60.0
    if "second" in u:
        return value / 3600.0
    if "day" in u:
        return value * 24.0
    return None


def seq_to_smiles(seq: str | None) -> str | None:
    if Chem is None or not seq:
        return None
    s = seq.strip()
    if not s:
        return None
    # 표준 20aa 한 글자만 (소문자/비표준 제외)
    if re.search(r"[^ACDEFGHIKLMNPQRSTVWY]", s.upper()) or s != s.upper():
        return None
    try:
        mol = Chem.MolFromSequence(s)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol)
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--splits", default="0.8,0.1,0.1", help="train,val,test")
    args = ap.parse_args()
    tr, va, te = map(float, args.splits.split(","))
    if abs(tr + va + te - 1.0) > 1e-6:
        print("splits must sum to 1", file=sys.stderr)
        sys.exit(1)

    with RAW.open() as f:
        payload = json.load(f)
    rows = payload["data"]

    records = []
    for r in rows:
        hl = r.get("half_life")
        units = r.get("units_half")
        v = _first_float(str(hl)) if hl is not None else None
        if v is None:
            continue
        hrs = to_hours(v, str(units) if units else None)
        if hrs is None or hrs <= 0:
            continue
        seq = r.get("seq")
        smi = seq_to_smiles(seq)
        if smi is None:
            continue
        records.append(
            {
                "id": r.get("id"),
                "pmid": r.get("pmid"),
                "seq": seq,
                "smiles": smi,
                "half_life_hours": hrs,
                "units_raw": units,
                "half_life_raw": hl,
                "chiral": r.get("chiral"),
                "lin_cyc": r.get("lin_cyc"),
                "chem_mod": r.get("chem_mod"),
            }
        )

    df = pd.DataFrame.from_records(records)
    PROC.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    idx = list(range(len(df)))
    rng.shuffle(idx)
    df = df.iloc[idx].reset_index(drop=True)
    n = len(df)
    nt = int(n * tr)
    nv = int(n * va)
    train = df.iloc[:nt]
    val = df.iloc[nt : nt + nv]
    test = df.iloc[nt + nv :]

    train.to_csv(PROC / "train.csv", index=False)
    val.to_csv(PROC / "val.csv", index=False)
    test.to_csv(PROC / "test.csv", index=False)
    df.to_csv(PROC / "all_filtered.csv", index=False)

    parseable = 0
    for r in rows:
        hl = r.get("half_life")
        vf = _first_float(str(hl)) if hl is not None else None
        if vf is None:
            continue
        if to_hours(vf, str(r.get("units_half") or "")) is not None:
            parseable += 1

    meta = {
        "source_json": str(RAW),
        "api_base": "https://webs.iiitd.edu.in/raghava/peplife2/api/api.php",
        "merged_unique_ids": len(rows),
        "rows_parseable_half_life_numeric": parseable,
        "rows_after_smiles_standard_aa_filter": int(len(df)),
        "d_aa_chiral_count_in_filtered": int((df["chiral"] == "D").sum()),
        "mix_chiral_count_in_filtered": int((df["chiral"] == "Mix").sum()),
    }
    (PROC / "preprocess_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
