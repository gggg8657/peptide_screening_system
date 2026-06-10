"""혈중 반감기 surrogate 정합성 벤치마크.

문헌에 혈중/혈장 t½ 가 공개된 펩타이드들에 predict_half_life 를 적용하고,
예측 순위와 문헌 순위의 Spearman 순위상관을 계산한다. (절대값이 아닌 **상대 순위** 검증)

주의: predict_half_life 는 표준 20 AA + modification 플래그(fatty_acid/d_amino_acid/cyclization)
기반 surrogate. 비표준 잔기(Aib 등)는 표현 못 함. fatty_acid 보너스는 단일 가산이라
liraglutide vs semaglutide(둘 다 지방산) 구분은 한계.
"""
import sys
from pathlib import Path

AI4SCI = Path("/home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri")
sys.path.insert(0, str(AI4SCI))
from AG_src.pipeline.step08_stability import predict_half_life

# (name, sequence[표준AA], modifications, 문헌 t½ hours, 출처메모)
BENCH = [
    ("GLP-1(7-37)",  "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR", [],               0.03, "~1.5-2 min, DPP-4 분해"),
    ("SST-14",       "AGCKNFFWKTFTSC",                 [],               0.05, "~1.5-3 min"),
    ("Exenatide",    "HGEGTFTSDLSKQMEEEAVRLFIEWLKNGGPSSGAPPPS", [],      2.4,  "~2.4 h"),
    ("Octreotide",   "FCFWKTCT",                       ["d_amino_acid"], 1.7,  "~90-120 min, 사이클릭"),
    ("Desmopressin", "CYFQNCPRG",                      ["d_amino_acid"], 3.0,  "~3 h, Cys1-6 + dArg"),
    ("Leuprolide",   "HWSYLLRP",                       ["d_amino_acid"], 3.0,  "~3 h, LHRH 유사체"),
    ("Liraglutide",  "HAEGTFTSDVSSYLEGQAAKEFIAWLVRGR", ["fatty_acid"],   13.0, "~13 h, C16 지방산"),
    ("Semaglutide",  "HAEGTFTSDVSSYLEGQAAKEFIAWLVRGR", ["fatty_acid"],   168.0,"~168 h, C18 지방산+링커"),
]


def spearman(xs, ys):
    """Spearman rank correlation (scipy 없이 numpy 로)."""
    import numpy as np
    def rank(a):
        order = np.argsort(a)
        r = np.empty(len(a), float)
        r[order] = np.arange(len(a))
        # 동순위 평균 처리
        a = np.asarray(a, float)
        for v in np.unique(a):
            idx = np.where(a == v)[0]
            r[idx] = r[idx].mean()
        return r
    rx, ry = rank(xs), rank(ys)
    rx -= rx.mean(); ry -= ry.mean()
    denom = (np.sqrt((rx**2).sum()) * np.sqrt((ry**2).sum()))
    return float((rx*ry).sum()/denom) if denom else 0.0


rows = []
for name, seq, mods, lit, note in BENCH:
    pred = predict_half_life(seq, mods)
    rows.append((name, seq, mods, lit, pred, note))

# 문헌 t½ 기준 정렬 + 예측 순위 표시
rows_by_lit = sorted(rows, key=lambda r: r[3])
print(f"{'peptide':14s} {'lit_t½(h)':>9s} {'pred(h)':>9s}  mods")
print("-" * 70)
for name, seq, mods, lit, pred, note in rows_by_lit:
    print(f"{name:14s} {lit:9.2f} {pred:9.2f}  {','.join(mods) or '-':20s} {note}")

lits = [r[3] for r in rows]
preds = [r[4] for r in rows]
rho = spearman(lits, preds)
print("\n=== Spearman 순위상관 (lit vs pred) ===")
print(f"  rho = {rho:.3f}   (1.0=완벽 순위일치, >0.7 강함, >0.5 보통)")

# 표준-AA(modification 無)만 따로 — 서열 휴리스틱 순수 검증
plain = [(r[3], r[4]) for r in rows if not r[2]]
if len(plain) >= 3:
    rho_plain = spearman([p[0] for p in plain], [p[1] for p in plain])
    print(f"  rho(plain, mod 無 {len(plain)}종) = {rho_plain:.3f}  ← 서열 휴리스틱 순수 검증")
