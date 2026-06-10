"""선택성 3중기준 평가 — 모든 (candidate × receptor) 도킹을 단일 병렬 풀로 (2026-06-10).

동일 프로토콜(transplant+pre-relax+FlexPepDock): SSTR2 + SSTR1/3/4/5 를 후보별로 도킹.
margin = min(offtarget) - SSTR2(same-protocol). 3중기준: margin>0 & ddG_loop<=-15 & ADMET.
글로벌 top-N 후보(ddG·clash 통과)에 적용. 병렬 workers 로 가속.
"""
import json, sys, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

AI = Path('/home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri')
sys.path.insert(0, str(AI))
from pyrosetta_flow.multiobjective import cheap_objectives

FLOW = AI / 'runs/pyrosetta_flow/sst14_agentic_mutdock'
BIOPY = str(Path.home() / 'miniforge3/envs/bio-tools/bin/python')
SCRIPT = str(AI / 'AG_src/scripts/offtarget_dock.py')
RECEPTORS = {
    "SSTR2": "data/somatostatin_receptor/curated/SSTR2_receptor.pdb",
    "SSTR1": "data/somatostatin_receptor/curated/SSTR1_receptor.pdb",
    "SSTR3": "data/somatostatin_receptor/curated/SSTR3_receptor.pdb",
    "SSTR4": "data/somatostatin_receptor/curated/SSTR4_receptor.pdb",
    "SSTR5": "data/somatostatin_receptor/curated/SSTR5_receptor.pdb",
}
ART = Path(sys.argv[1])
TOPN = int(sys.argv[2]) if len(sys.argv) > 2 else 8
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 12
NATIVE = "AGCKNFFWKTFTSC"


def collect(art):
    d = json.load(open(art)); cands = {}
    blocks = [(it.get("iteration"), it["candidates"]) for it in d.get("iterations", [])
              if isinstance(it, dict) and "candidates" in it]
    blocks.append((None, d.get("final_candidates", [])))
    for itn, lst in blocks:
        for c in lst:
            seq = c.get("sequence"); ddg = c.get("ddg", c.get("ddG"))
            if not seq or ddg is None or ddg >= 900:
                continue
            it_n = c.get("iteration", itn); cid = c.get("candidate_id", "")
            pdb = None
            if it_n and "cand" in cid:
                try: pdb = FLOW / f"iter_{int(it_n):02d}" / f"cand_{int(cid.split('cand')[1]):03d}.pdb"
                except Exception: pdb = None
            prev = cands.get(seq)
            if prev is None or ddg < prev["ddg"]:
                cands[seq] = {"seq": seq, "ddg": ddg, "clash": c.get("clash_score", 99),
                              "pdb": str(pdb) if pdb else None}
    return list(cands.values())


def dock(pdb, receptor_rel, tag):
    rec = str(AI / receptor_rel)
    out = f"/tmp/seleval_{tag}.pdb"
    try:
        p = subprocess.run([BIOPY, SCRIPT, "--sstr2-complex", pdb, "--offtarget-receptor", rec,
                            "--output", out], capture_output=True, text=True, timeout=900)
        return float(json.loads(p.stdout.strip().splitlines()[-1])["ddg"])
    except Exception:
        return None


def main():
    cands = collect(ART)
    pool = [c for c in cands if c["clash"] <= 10 and c["pdb"] and Path(c["pdb"]).exists()]
    pool.sort(key=lambda c: c["ddg"]); pool = pool[:TOPN]
    print(f"[eval] global top-{len(pool)} (ddG·clash 통과) × 5 수용체 = {len(pool)*5} 도킹, workers={WORKERS}")
    jobs = []
    for i, c in enumerate(pool):
        for rname, rrel in RECEPTORS.items():
            jobs.append((i, rname, c["pdb"], rrel))
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(dock, pdb, rrel, f"{i}_{rname}"): (i, rname) for i, rname, pdb, rrel in jobs}
        ddg_map = {}
        for f in futs:
            i, rname = futs[f]
            ddg_map[(i, rname)] = f.result()
    nat_admet = cheap_objectives(NATIVE)["admet_score"]
    print(f"[ref] native admet={nat_admet}\n")
    results = []
    for i, c in enumerate(pool):
        s2 = ddg_map.get((i, "SSTR2"))
        offs = {r: ddg_map.get((i, r)) for r in ("SSTR1", "SSTR3", "SSTR4", "SSTR5")}
        offs = {r: v for r, v in offs.items() if v is not None}
        if s2 is None or not offs:
            print(f"  {c['seq']}: dock incomplete"); continue
        worst = min(offs.values()); margin = round(worst - s2, 2)
        co = cheap_objectives(c["seq"]); admet = co["admet_score"]
        ok = (margin > 0 and c["ddg"] <= -15 and admet >= 0.8 * nat_admet)
        results.append({"seq": c["seq"], "ddg_loop": round(c["ddg"], 2), "sstr2_same": round(s2, 2),
                        "worst_off": round(worst, 2), "margin": margin, "admet": admet,
                        "toxic": co.get("pepadmet_toxic"), "hl": co.get("half_life_h"), "pass3": ok})
        print(f"  {c['seq']}: ddg={c['ddg']:.1f} SSTR2={s2:.1f} worst_off={worst:.1f} margin={margin:+.1f} admet={admet} {'✅3중' if ok else ''}")
    winners = [r for r in results if r["pass3"]]
    print(f"\n=== 3중기준(margin>0 & ddG_loop<=-15 & admet>=0.8*native) 충족: {len(winners)}건 ===")
    for r in sorted(winners, key=lambda x: -x["margin"]):
        print(f"  ✅ {r['seq']}: margin=+{r['margin']} ddg={r['ddg_loop']} admet={r['admet']} hl={r['hl']}h")
    pos = [r for r in results if r["margin"] > 0]
    print(f"\n[summary] 양의 margin {len(pos)}/{len(results)}, 3중충족 {len(winners)} → {'성공(≥3)' if len(winners)>=3 else '미달'}")
    json.dump({"results": results, "winners": winners, "success": len(winners) >= 3},
              open(ART.parent / "selectivity_eval_parallel.json", "w"), indent=2)


if __name__ == "__main__":
    main()
