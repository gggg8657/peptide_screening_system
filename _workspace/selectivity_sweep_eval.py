"""글로벌 선택성 sweep + 3중 성공기준 평가 (2026-06-10 Step2).

run 아티팩트의 전 iteration 후보 중 글로벌 best(ddG, clash 통과)를 모아
off-target(SSTR1/3/4/5) 실제 도킹으로 selectivity_margin 산출, 3중 기준 평가:
  1) selectivity_margin > 0  2) ddG <= -15  3) ADMET 합리(admet_score)
성공 = 3중 동시만족 ≥3건. 아니면 최선 margin + 정량 입증.

실행: ~/miniforge3/envs/bio-tools/bin/python _workspace/selectivity_sweep_eval.py <artifact.json> [topN]
"""
import sys, json
from pathlib import Path

AI = Path("/home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri")
sys.path.insert(0, str(AI))
from pyrosetta_flow.multiobjective import screen_selectivity, cheap_objectives

ART = Path(sys.argv[1]) if len(sys.argv) > 1 else AI / "runs/pyrosetta_flow/selectivity_breakthrough_20260610.json"
TOPN = int(sys.argv[2]) if len(sys.argv) > 2 else 15
FLOW = AI / "runs/pyrosetta_flow/sst14_agentic_mutdock"
NATIVE = "AGCKNFFWKTFTSC"


def collect(art):
    d = json.load(open(art))
    cands = {}
    iters = d.get("iterations", [])
    blocks = []
    for it in iters:
        if isinstance(it, dict) and "candidates" in it:
            blocks.append((it.get("iteration"), it["candidates"]))
    blocks.append((None, d.get("final_candidates", [])))
    for it_num, lst in blocks:
        for c in lst:
            seq = c.get("sequence")
            ddg = c.get("ddg", c.get("ddG"))
            if not seq or ddg is None or ddg >= 900:
                continue
            it_n = c.get("iteration", it_num)
            cid = c.get("candidate_id", "")
            pdb = None
            if it_n and "cand" in cid:
                try:
                    pdb = FLOW / f"iter_{int(it_n):02d}" / f"cand_{int(cid.split('cand')[1]):03d}.pdb"
                except Exception:
                    pdb = None
            prev = cands.get(seq)
            if prev is None or ddg < prev["ddg"]:
                cands[seq] = {"seq": seq, "ddg": ddg, "clash": c.get("clash_score", 99),
                              "cid": cid, "pdb": str(pdb) if pdb else None,
                              "extra": c.get("extra_scores", {})}
    return list(cands.values())


def main():
    if not ART.exists():
        print(f"artifact 없음: {ART}"); return
    cands = collect(ART)
    # clash 통과 + PDB 존재 + ddG 좋은 순
    pool = [c for c in cands if c["clash"] <= 10 and c["pdb"] and Path(c["pdb"]).exists()]
    pool.sort(key=lambda c: c["ddg"])
    pool = pool[:TOPN]
    print(f"[sweep] 후보 {len(cands)}개 중 clash통과+PDB존재 글로벌 top-{len(pool)} 선택성 도킹")
    nat = cheap_objectives(NATIVE)
    nat_admet = nat["admet_score"]
    print(f"[ref] native admet_score={nat_admet}")

    results = []
    for c in pool:
        # 2026-06-10: 항상 재계산. 아티팩트의 구 selectivity_margin 은 프로토콜 수정(동일 baseline)
        # 이전 값이라 stale → screen_selectivity 로 재측정(SSTR2 same-protocol baseline 포함).
        sel = screen_selectivity(sstr2_complex_pdb=c["pdb"], on_target_ddg=c["ddg"],
                                 conda_env="bio-tools", timeout=600)
        margin = sel.get("selectivity_margin")
        c["extra"]["offtarget_ddg"] = sel.get("offtarget_ddg")
        c["extra"]["sstr2_ddg_sameprotocol"] = sel.get("sstr2_ddg_sameprotocol")
        co = cheap_objectives(c["seq"])
        admet = co["admet_score"]
        rec = {"seq": c["seq"], "ddg": round(c["ddg"], 2), "margin": margin,
               "admet": admet, "toxic": co.get("pepadmet_toxic"),
               "hl_h": co.get("half_life_h"), "offtarget": c["extra"].get("offtarget_ddg")}
        results.append(rec)
        print(f"  {c['seq']}: ddg={rec['ddg']} margin={margin} admet={admet} toxic={rec['toxic']}")

    # 3중 기준 평가
    def ok(r):
        return (r["margin"] is not None and r["margin"] > 0
                and r["ddg"] <= -15
                and r["admet"] is not None and r["admet"] >= 0.8 * nat_admet)
    winners = [r for r in results if ok(r)]
    print(f"\n=== 3중 기준(margin>0 & ddG<=-15 & admet>=0.8*native) 만족: {len(winners)}건 ===")
    for r in sorted(winners, key=lambda x: -x["margin"]):
        print(f"  ✅ {r['seq']}: margin={r['margin']:.2f} ddg={r['ddg']} admet={r['admet']}")
    # 최선 margin (기준 무관)
    valid = [r for r in results if r["margin"] is not None]
    if valid:
        best = max(valid, key=lambda x: x["margin"])
        pos = [r for r in valid if r["margin"] > 0]
        print(f"\n[summary] 최선 margin={best['margin']:.2f} ({best['seq']}), 양의 margin {len(pos)}/{len(valid)}건")
    json.dump({"results": results, "winners": winners, "native_admet": nat_admet,
               "success_count": len(winners)},
              open(ART.parent / "selectivity_sweep_eval.json", "w"), indent=2)
    print(f"saved → {ART.parent/'selectivity_sweep_eval.json'}")
    print("성공" if len(winners) >= 3 else "기준 미달 → fallback(정량 입증) 필요")


if __name__ == "__main__":
    main()
