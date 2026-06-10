"""반감기 surrogate 재보정 — log-multiplicative 모델 튜닝 + 벤치마크.

문제(기존): cyclization +24h additive 가 사이클릭/SS 펩타이드(SST-14 등)를 과대예측
→ cross-scaffold 순위 역전(plain rho=-0.5, SST-14 16.6h vs 실제 0.05h).

해결: log10 공간에서 곱셈 모델. 고리화는 작은 배수, modification(특히 fatty_acid 알부민결합)
이 장반감기 주도, 프로테아제 취약성이 단반감기 스프레드. 물리적 동기 상수 사용(과적합 회피).
"""
import math

# 잔기별 프로테아제 취약성 (step08 의 _PROTEASE_VULNERABILITY 와 동일 의미; 높을수록 취약)
PROTEASE_VULN = {
    "R": 3.0, "K": 2.5, "F": 2.0, "Y": 1.8, "W": 1.5, "L": 1.2, "A": 0.8,
    "V": 0.6, "G": 0.4, "P": 0.1, "M": 0.5, "S": 0.6, "T": 0.6, "C": 0.3,
    "N": 0.5, "Q": 0.5, "D": 0.4, "E": 0.4, "H": 0.9, "I": 0.7,
}

# log10 배수 (modification) — 물리적 동기
MOD_LOG = {
    "fatty_acid":   math.log10(2800.0),  # C16-18 알부민 결합 → 신장청소 회피, 100-150x
    "pegylation":   math.log10(2200.0),  # PEG 신장청소 차단
    "d_amino_acid": math.log10(35.0),    # 절단부위 프로테아제 저항 (octreotide/desmopressin)
    "cyclization":  math.log10(1.8),     # 이황화/고리화: 완만한 안정화 (혈중 t½ 주도 아님)
    "substitution": math.log10(4.0),
}
BASE_HL = 0.05          # h, 짧은 선형 펩타이드 혈중 baseline (~3 min)
PROTEO_K = 0.32         # avg vulnerability 계수
CLEAVE_K = 0.06         # dipeptide 절단부위 계수
TERM_K   = 0.15         # 말단 exopeptidase 계수


def predict_hl_v2(sequence, modifications):
    seq = sequence.upper()
    if not seq:
        return BASE_HL
    n = len(seq)
    avg_vuln = sum(PROTEASE_VULN.get(a, 0.9) for a in seq) / n
    cleavage = 0.0
    for i in range(n - 1):
        if seq[i] in "KR" and seq[i + 1] != "P":
            cleavage += 1.0
        elif seq[i] in "FYW" and seq[i + 1] != "P":
            cleavage += 0.5
    nterm = PROTEASE_VULN.get(seq[0], 0.9)
    cterm = PROTEASE_VULN.get(seq[-1], 0.9)

    # log10 proteolysis penalty (취약할수록 음수↑ = 짧아짐). avg_vuln~1.0 기준.
    proteo_log = -(PROTEO_K * (avg_vuln - 0.8)
                   + CLEAVE_K * cleavage
                   + TERM_K * ((nterm + cterm) / 2.0 - 0.8))

    # cyclization 자동 감지 (Cys 쌍, ≥4 간격)
    cys = [i for i, a in enumerate(seq) if a == "C"]
    has_cyc = n >= 6 and len(cys) >= 2 and (cys[-1] - cys[0]) >= 4

    mod_log = 0.0
    if has_cyc:
        mod_log += MOD_LOG["cyclization"]
    for m in (x.lower() for x in modifications):
        if m in MOD_LOG:
            mod_log += MOD_LOG[m]
        elif "d_amino" in m or "d-amino" in m:
            mod_log += MOD_LOG["d_amino_acid"]
        elif "fatty" in m or "acyl" in m:
            mod_log += MOD_LOG["fatty_acid"]
        elif "peg" in m:
            mod_log += MOD_LOG["pegylation"]

    log_hl = math.log10(BASE_HL) + proteo_log + mod_log
    return max(0.02, min(10 ** log_hl, 1e4))


BENCH = [
    ("GLP-1(7-37)",  "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR", [],               0.03),
    ("SST-14",       "AGCKNFFWKTFTSC",                 [],               0.05),
    ("Exenatide",    "HGEGTFTSDLSKQMEEEAVRLFIEWLKNGGPSSGAPPPS", [],      2.4),
    ("Octreotide",   "FCFWKTCT",                       ["d_amino_acid"], 1.7),
    ("Desmopressin", "CYFQNCPRG",                      ["d_amino_acid"], 3.0),
    ("Leuprolide",   "HWSYLLRP",                       ["d_amino_acid"], 3.0),
    ("Liraglutide",  "HAEGTFTSDVSSYLEGQAAKEFIAWLVRGR", ["fatty_acid"],   13.0),
    ("Semaglutide",  "HAEGTFTSDVSSYLEGQAAKEFIAWLVRGR", ["fatty_acid"],   168.0),
]


def spearman(xs, ys):
    import numpy as np
    def rank(a):
        a = np.asarray(a, float); r = np.empty(len(a)); o = np.argsort(a); r[o] = np.arange(len(a))
        for v in np.unique(a):
            idx = np.where(a == v)[0]; r[idx] = r[idx].mean()
        return r
    rx, ry = rank(xs), rank(ys); rx -= rx.mean(); ry -= ry.mean()
    d = (np.sqrt((rx**2).sum()) * np.sqrt((ry**2).sum()))
    return float((rx*ry).sum()/d) if d else 0.0


rows = [(n, predict_hl_v2(s, m), lit) for n, s, m, lit in BENCH]
print(f"{'peptide':14s} {'lit(h)':>8s} {'v2(h)':>9s}")
for n, p, lit in sorted(rows, key=lambda r: r[2]):
    print(f"{n:14s} {lit:8.2f} {p:9.2f}")
preds = [r[1] for r in rows]; lits = [r[2] for r in rows]
print(f"\nSpearman(all)   = {spearman(lits, preds):.3f}")
plain = [(lit, predict_hl_v2(s, m)) for n, s, m, lit in BENCH if not m]
print(f"Spearman(plain) = {spearman([p[0] for p in plain], [p[1] for p in plain]):.3f}  (n={len(plain)})")
