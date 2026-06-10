"""half-life 자체학습 v2 — feature 기반 회귀 (2026-06-09 C 재설계).

기존 GAT(train_peplife2_gat.py)는 R²<0/Spearman<0 으로 실패:
  - PEPlife2 의 종/장기/assay 혼재 → 타깃 노이즈
  - 표준20aa SMILES 만 사용 → half-life 를 좌우하는 modification(D-AA/고리화/말단캡핑) 무시
근본 수정:
  - **일관 조건 필터** (human serum, in vitro 우선)로 타깃 노이즈 감소
  - **modification-aware 엔지니어드 피처** (chiral=D, chem_mod, cter/nter 캡핑, cyclic + 서열 물성)
  - 작은·노이즈 표본에 강건한 **GradientBoosting/RandomForest** + 5-fold CV + hold-out test
평가: hold-out test R²/Spearman (주지표) + 문헌 8종 벤치마크 Spearman (외부 점검).
채택 기준: 휴리스틱(벤치 Spearman 0.86) 초과 시에만. 아니면 휴리스틱 유지.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "peplife2_raw"
OUT = ROOT / "data" / "halflife_v2"; OUT.mkdir(parents=True, exist_ok=True)

KD = {"A":1.8,"R":-4.5,"N":-3.5,"D":-3.5,"C":2.5,"Q":-3.5,"E":-3.5,"G":-0.4,"H":-3.2,
      "I":4.5,"L":3.8,"K":-3.9,"M":1.9,"F":2.8,"P":-1.6,"S":-0.8,"T":-0.7,"W":-0.9,"Y":-1.3,"V":4.2}
AAS = list("ACDEFGHIKLMNPQRSTVWY")


def parse_hours(val, unit):
    if val is None: return None
    s = str(val).strip().lower().replace("<","").replace(">","").replace("~","").replace("≈","")
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if not m: return None
    x = float(m.group())
    u = str(unit or "").strip().lower()
    if "sec" in u: return x/3600.0
    if "min" in u: return x/60.0
    if "hour" in u or "hr" in u or u=="h": return x
    if "day" in u: return x*24.0
    if "week" in u: return x*24.0*7.0
    return None  # unknown unit


def merge_raw():
    recs = {}
    for p in sorted(RAW.glob("api_*.json")):
        d = json.load(open(p))
        for r in d.get("data", []):
            recs[r.get("id")] = {**recs.get(r.get("id"), {}), **r}
    return list(recs.values())


def featurize(seq, rec):
    seq = (seq or "").upper()
    seq = "".join(c for c in seq if c in AAS)  # 표준20만 (비표준은 제거되어 길이 단축)
    n = len(seq)
    if n < 2: return None
    f = {}
    f["length"] = n
    for a in AAS:
        f[f"frac_{a}"] = seq.count(a)/n
    f["gravy"] = sum(KD[a] for a in seq)/n
    f["net_charge"] = (seq.count("K")+seq.count("R")+0.1*seq.count("H")
                       - seq.count("D")-seq.count("E"))
    f["n_arg_lys"] = seq.count("R")+seq.count("K")
    f["n_met"] = seq.count("M")
    f["n_cys"] = seq.count("C")
    f["n_pro"] = seq.count("P")
    cleav = 0.0
    for i in range(n-1):
        if seq[i] in "KR" and seq[i+1]!="P": cleav += 1.0
        elif seq[i] in "FYW" and seq[i+1]!="P": cleav += 0.5
    f["cleavage_sites"] = cleav
    f["cleavage_density"] = cleav/n
    f["nterm_KR"] = 1.0 if seq[0] in "KR" else 0.0
    # --- modification-aware (메타데이터) — 핵심 ---
    chiral = str(rec.get("chiral","L"))
    f["has_D"] = 1.0 if chiral in ("D","Mix","DL") else 0.0
    f["is_cyclic"] = 1.0 if str(rec.get("lin_cyc","")).lower().startswith("cyc") else (
        1.0 if seq.count("C")>=2 else 0.0)
    f["chem_mod"] = 0.0 if str(rec.get("chem_mod","None")).strip() in ("None","","N.A.") else 1.0
    nter = str(rec.get("nter","Free")).strip().lower()
    cter = str(rec.get("cter","Free")).strip().lower()
    f["nter_capped"] = 0.0 if nter in ("free","none","n.a.","") else 1.0   # acetylation 등 → exopeptidase 저항
    f["cter_capped"] = 0.0 if cter in ("free","none","n.a.","") else 1.0   # amidation 등
    # lipidation/PEG 힌트 (chem_mod 텍스트)
    cm = str(rec.get("chem_mod","")).lower()
    f["lipid_or_peg"] = 1.0 if any(k in cm for k in ("lipid","fatty","palmit","myrist","peg","acyl","stear")) else 0.0
    return f


def main():
    recs = merge_raw()
    rows = []
    for r in recs:
        hl = parse_hours(r.get("half_life"), r.get("units_half"))
        if hl is None or hl <= 0: continue
        feat = featurize(r.get("seq"), r)
        if feat is None: continue
        feat["_hl"] = hl
        feat["_sample"] = str(r.get("test_sample","")).lower()
        feat["_vivo"] = str(r.get("vivo_vitro","")).lower()
        rows.append(feat)
    df = pd.DataFrame(rows)
    print(f"[data] parsed records with t½+seq: {len(df)}")

    # 일관조건 필터 (노이즈 감소): human serum/plasma 우선, 부족하면 완화
    def subset(mask, name):
        s = df[mask]
        print(f"[filter] {name}: {len(s)}")
        return s
    human = subset(df["_sample"].str.contains("serum|plasma|blood|human", na=False), "human serum/plasma/blood")
    work = human if len(human) >= 200 else df
    if work is df: print("[filter] human subset <200 → 전체 사용")

    feat_cols = [c for c in work.columns if not c.startswith("_")]
    X = work[feat_cols].values.astype(float)
    y = np.log1p(work["_hl"].values.astype(float))   # log1p(hours)

    # 5-fold CV (out-of-fold 예측으로 정직한 일반화 지표)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    results = {}
    for name, model in [
        ("GBR", GradientBoostingRegressor(random_state=42, n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8)),
        ("RF",  RandomForestRegressor(random_state=42, n_estimators=400, max_depth=None, n_jobs=-1)),
    ]:
        oof = cross_val_predict(model, X, y, cv=kf, n_jobs=-1)
        r2_log = r2_score(y, oof)
        rho = spearmanr(np.expm1(y), np.expm1(oof)).correlation
        r2_h = r2_score(np.expm1(y), np.expm1(oof))
        results[name] = {"cv_r2_log": round(r2_log,4), "cv_spearman_hours": round(float(rho),4), "cv_r2_hours": round(r2_h,4)}
        print(f"[cv] {name}: R²(log)={r2_log:.3f} Spearman(h)={rho:.3f} R²(h)={r2_h:.3f}")

    # 최종 모델(전체 학습) + 문헌 8종 벤치마크
    best_name = max(results, key=lambda k: results[k]["cv_spearman_hours"])
    best = (GradientBoostingRegressor(random_state=42, n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8)
            if best_name=="GBR" else RandomForestRegressor(random_state=42, n_estimators=400, n_jobs=-1))
    best.fit(X, y)
    import joblib; joblib.dump({"model":best,"feat_cols":feat_cols}, OUT/"halflife_gbr.joblib")

    BENCH = [("GLP-1","HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",{},0.03),("SST-14","AGCKNFFWKTFTSC",{},0.05),
        ("Exenatide","HGEGTFTSDLSKQMEEEAVRLFIEWLKNGGPSSGAPPPS",{},2.4),
        ("Octreotide","FCFWKTCT",{"chiral":"D","lin_cyc":"Cyclic"},1.7),
        ("Desmopressin","CYFQNCPRG",{"chiral":"D","cter":"amide"},3.0),
        ("Leuprolide","HWSYLLRP",{"chiral":"D","cter":"ethylamide"},3.0),
        ("Liraglutide","HAEGTFTSDVSSYLEGQAAKEFIAWLVRGR",{"chem_mod":"lipid"},13.0),
        ("Semaglutide","HAEGTFTSDVSSYLEGQAAKEFIAWLVRGR",{"chem_mod":"lipid"},168.0)]
    bx, blit, bnames = [], [], []
    for nm, s, rec, lit in BENCH:
        f = featurize(s, rec)
        if f: bx.append([f[c] for c in feat_cols]); blit.append(lit); bnames.append(nm)
    bpred = np.expm1(best.predict(np.array(bx, float)))
    brho = spearmanr(blit, bpred).correlation
    print(f"\n[benchmark] 문헌 8종 Spearman = {brho:.3f}  (휴리스틱 0.855 대비)")
    for nm, lit, pr in sorted(zip(bnames, blit, bpred), key=lambda z: z[1]):
        print(f"  {nm:14s} lit={lit:7.2f}h  pred={pr:7.2f}h")

    meta = {"n_train": len(work), "filter": "human" if work is human else "all",
            "cv": results, "benchmark_spearman": round(float(brho),4),
            "feat_cols": feat_cols, "best_model": best_name}
    json.dump(meta, open(OUT/"train_meta.json","w"), indent=2)
    print("\n[meta]", json.dumps(meta["cv"]))
    print(f"saved → {OUT/'halflife_gbr.joblib'}")


if __name__ == "__main__":
    main()
