#!/usr/bin/env python3
"""
runs_local/archives_boltz_eval/test_small.py

Mini-test: 5 후보 × 5 SSTR = 25 페어 (단일 GPU)
목적: run_full_eval.py 실행 전 파이프라인 검증 + ETA 추정

소요시간: ~12-15분 (H100, GPU=3)
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVES_DIR = REPO_ROOT / "runs" / "pyrosetta_flow" / "archives"
TOP10_FILE = REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "top10_candidates.json"
AF_DIR = REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "alphafold_receptors"
OUT_DIR = Path(__file__).resolve().parent / "test_small_out"

# ── SSTR 설정 (run_full_eval.py와 동일) ───────────────────────
UNIPROT = {
    "SSTR1": "P30872", "SSTR2": "P30874", "SSTR3": "P32745",
    "SSTR4": "P31391", "SSTR5": "P35346",
}

SSTR_SEQ = {
    "SSTR1": (
        "MFPNGTASSPSSSPSPSPGSCGEGGGSRGPGAGAADGMEEPGRNASQNGTLSEGQGSAILISFIYSVVCLVGLCGNSMVIY"
        "VILRYAKMKTATNIYILNLAIADELLMLSVPFLVTSTLLRHWPFGALLCRLVLSVDGINQFTSIFCLTVMSVDRYLAVVHP"
        "TRSARWRTAPVARTVSAAVWVASAVVVLPVVVFSGVPRGMSTCHMQWPEPAAAWRAGFIIYTAALGFFGPLLVICLCYLLI"
        "VVKVRSAGRRVWAPSCQRRRRSERRVTRMVVAVVALFVLCWMPFYVLNIVNVVCPLPEEPAFFGLYFLVVALPYANSCANP"
        "ILYGFLSYRFKQGFRRVLLRPSRRVRSQEPTVGPPEKTEEDDEEDEEGGGEEDPRPSCRGTPGSARGGPSPRSAEQDARNQ"
        "RRESLPAREPRTASTSDPAKPSPHSGGGTPAHRGSAGSALAQTQVDTHTRGSAGSALAQTQVDTHTKCS"
    ),
    "SSTR2": (
        "MDMADEPLNGSHTWLSIPFDLNGSVVSTNTSNQTEPYYDLTSNAVLTFIYFVVCIIGLCGNTLVIYVILRYAKMKTITNIY"
        "ILNLAIADELFMLGLPFLAMQVALVHWPFGKAICRVVMTVDGINQFTSIFCLTVMSIDRYLAVVHPIKSAKWRRPRTAKMI"
        "TMAVWGVSLLVILPIMIYAGLRSNQWGRSSCTINWPGESGAWYTGFIIYTFILGFLVPLTIICLCYLFIIIKVKSSGIRVG"
        "SSKRKKSEKKVTRMVSIVVAVFIFCWLPFYIFNVSSVSMAISPTPALKGMFDFVVVLTYANSCANPILYAFLSDNFKKSF"
        "QNVLCLVKVSGTDDGERSDSKQDKSRLNETTETQRTLLNGDLQTSI"
    ),
    "SSTR3": (
        "MDMLHPSSVSTTSEPENASSAWPPDATLGNVSAGPSPAGLAVSGVLIPLVYLVVCVVGLLGNSLVIYVVLRHTASPSVTNVY"
        "ILNLALADELFMLGLPFLAAQNALSYWPFGSLMCRLVMAVDGINQFTSIFCLTVMSVDRYLAVVHPTRSARWRTAPVARTV"
        "SAAVWVASAVVVLPVVVFSGVPRGMSTCHMQWPEPAAAWRAGFIIYTAALGFFGPLLVICLCYLLIVVKVRSAGRRVWAPS"
        "CQRRRRSERRVTRMVVAVVALFVLCWMPFYVLNIVNVVCPLPEEPAFFGLYFLVVALPYANSCANPILYGFLSYRFKQGFR"
        "RVLLRPSRRVRSQEPTVGPPEKTEEDDEEDEEGGGEEDPRPSCRGTPGSARGGPSPRSAEQDARNQRRESLPAREPRTASTS"
        "DPAKPSPHSGGGTPAHRGSAGSALAQTQVDTHTRGSAGSALAQTQVDTHTKCS"
    ),
    "SSTR4": (
        "MSAPSTLPPGGEEGLGTAWPSAANASSAPAEAEEAVAGPGDARAAGMVAIQCIYALVCLVGLVGNALVIFVILRYAKMKTAT"
        "NIYLLNLAVADELFMLSVPFVASSAALRHWPFGSVLCRAVLSVDGLNMFTSVFCLTVLSVDRYVAVVHPLRAATYRRPSVA"
        "KLINLGVWLASLLVTLPIAIFADTRPARGGEAVACNLQWPHPAWSAVFVVYTFLLGFLLPVGAICLCYVLIVVKMRMVALK"
        "AGWQQRKRSERKITLMVMMVVMVFVICWMPFYVVNLVNVVCPLPEEPAFFGLYFLVVALPYANSCANPILYGFLSYRFKQG"
        "FRRVLLRPSRRVRSQEPTVGPPEKTEEDDEEDEEGGGEEDPRPSCRGTPGSARGGPSPRSAEQDARNQRRESLPAREPRTAST"
        "SDPAKPSPHSGGGTPAHRGSAGSALAQTQVDTHTRGSAGSALAQTQVDTHTKCS"
    ),
    "SSTR5": (
        "MEPLFPASTPSWNASSPGAASGGGDNRTLVGPAPSAGARAVLVPVLYLLVCAAGLGGNTLVIYVVLRFATVTNIYILNLAV"
        "ADVLYMLGLPFLATQNAASFWPFGSLLCRTVIAVDGFNQFTSIFCLTVMSVDRYLAVVHPTRSARWRTAPVARTVSAAVWV"
        "ASAVVVLPVVVFSGVPRGMSTCHMQWPEPAAAWRAGFIIYTAALGFFGPLLVICLCYLLIVVKVRSAGRRVWAPSCQRRRR"
        "SERRVTRMVVAVVALFVLCWMPFYVLNIVNVVCPLPEEPAFFGLYFLVVALPYANSCANPILYGFLSYRFKQGFRRVLLRP"
        "SRRVRSQEPTVGPPEKTEEDDEEDEEGGGEEDPRPSCRGTPGSARGGPSPRSAEQDARNQRRESLPAREPRTASTSDPAKPS"
        "PHSGGGTPAHRGSAGSALAQTQVDTHTRGSAGSALAQTQVDTHTKCS"
    ),
}

RECEPTOR_ORDER = ["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"]
N_CANDS = 5   # mini-test 후보 수
GPU_ID = 3    # 기본 GPU (변경 가능: --gpu 옵션)


def extract_sample_candidates(n: int = N_CANDS):
    """archives에서 unique 후보 추출 → top10 제외 → 상위 n개 반환"""
    dashboard_files = sorted(ARCHIVES_DIR.glob("*_dashboard.json"))
    all_seqs = set()
    for f in dashboard_files:
        d = json.loads(f.read_text())
        for c in d.get("candidates", []):
            seq = c.get("sequence") or c.get("seq")
            if seq and isinstance(seq, str) and len(seq) >= 6:
                all_seqs.add(seq.strip())

    top10 = json.loads(TOP10_FILE.read_text())["top10"]
    top10_seqs = {c["seq"].strip() for c in top10}

    remaining = sorted(all_seqs - top10_seqs)
    return remaining[:n]


def run_boltz_pair(seq, rname, yaml_path, run_out, gpu_id):
    cmd = [
        "conda", "run", "--no-capture-output", "-n", "boltz",
        "boltz", "predict", str(yaml_path),
        "--out_dir", str(run_out),
        "--recycling_steps", "1",
        "--sampling_steps", "50",
        "--diffusion_samples", "1",
        "--output_format", "pdb",
        "--override",
        "--num_workers", "0",
        "--no_kernels",
    ]
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": str(gpu_id)}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)
    except subprocess.TimeoutExpired:
        return {"sequence": seq, "receptor": rname, "status": "error", "error": "timeout"}

    conf_files = list(run_out.rglob("confidence_*_model_0.json"))
    if conf_files:
        try:
            conf = json.loads(conf_files[0].read_text())
            return {
                "sequence": seq, "receptor": rname,
                "iptm": conf.get("iptm"), "ptm": conf.get("ptm"),
                "confidence": conf.get("confidence_score"),
                "complex_plddt": conf.get("complex_plddt"),
                "status": "ok",
            }
        except Exception as e:
            return {"sequence": seq, "receptor": rname, "status": "error", "error": str(e)}
    else:
        return {
            "sequence": seq, "receptor": rname, "status": "error",
            "error": "no_conf_file", "stderr_tail": proc.stderr[-400:],
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mini-test: 5후보×5SSTR=25페어")
    parser.add_argument("--gpu", type=int, default=GPU_ID, help=f"GPU ID (기본: {GPU_ID})")
    parser.add_argument("--n-cands", type=int, default=N_CANDS,
                        help=f"테스트 후보 수 (기본: {N_CANDS})")
    args = parser.parse_args()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Mini-test 시작")
    print(f"  GPU: {args.gpu} | 후보: {args.n_cands} | 페어: {args.n_cands * 5}")

    # 환경 확인
    for rname, upid in UNIPROT.items():
        msa = AF_DIR / f"AF-{upid}-F1-msa.a3m"
        if not msa.exists():
            print(f"[오류] {rname} MSA 없음: {msa}", file=sys.stderr)
            sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    yaml_dir = OUT_DIR / "yamls"
    yaml_dir.mkdir(exist_ok=True)

    # 후보 추출
    cands = extract_sample_candidates(args.n_cands)
    print(f"  샘플 후보: {cands}\n")

    pairs = [(seq, rname) for seq in cands for rname in RECEPTOR_ORDER]
    total = len(pairs)
    results = []
    timings = []

    for idx, (seq, rname) in enumerate(pairs, 1):
        pep_safe = "".join(c for c in seq if c.isalpha())[:16]
        cid = f"mini_{idx:03d}_{pep_safe}"

        pep_msa = yaml_dir / f"{cid}_pep.a3m"
        pep_msa.write_text(f">query\n{seq}\n")

        rec_msa = (AF_DIR / f"AF-{UNIPROT[rname]}-F1-msa.a3m").resolve()
        rec_seq = SSTR_SEQ[rname]

        yaml_path = yaml_dir / f"{cid}__{rname}.yaml"
        yaml_path.write_text(
            f"version: 1\n"
            f"sequences:\n"
            f"  - protein:\n"
            f"      id: A\n"
            f"      sequence: {seq}\n"
            f"      msa: {pep_msa.resolve()}\n"
            f"  - protein:\n"
            f"      id: B\n"
            f"      sequence: {rec_seq}\n"
            f"      msa: {rec_msa}\n"
        )

        run_out = OUT_DIR / "boltz_out" / f"{cid}__{rname}"
        run_out.mkdir(parents=True, exist_ok=True)

        print(f"[{idx}/{total}] {seq} × {rname} ...", end=" ", flush=True)
        t0 = time.time()
        result = run_boltz_pair(seq, rname, yaml_path, run_out, args.gpu)
        elapsed = time.time() - t0
        timings.append(elapsed)

        result["elapsed_sec"] = round(elapsed, 1)
        results.append(result)

        # ETA
        avg_sec = sum(timings) / len(timings)
        eta_sec = avg_sec * (total - idx)
        eta_str = str(timedelta(seconds=int(eta_sec)))

        if result["status"] == "ok":
            print(f"OK iPTM={result.get('iptm', 'N/A'):.3f} "
                  f"({elapsed:.0f}s) ETA {eta_str}", flush=True)
        else:
            print(f"ERROR: {result.get('error')} ({elapsed:.0f}s) ETA {eta_str}", flush=True)

        # 5페어마다 중간 저장
        if idx % 5 == 0:
            with open(OUT_DIR / "test_results_partial.json", "w") as f:
                json.dump(results, f, indent=2)

    # 최종 저장
    out_path = OUT_DIR / "test_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    # 요약
    ok = [r for r in results if r.get("status") == "ok"]
    err = [r for r in results if r.get("status") == "error"]
    avg_t = sum(timings) / len(timings) if timings else 0

    print(f"\n{'='*55}")
    print(f" Mini-test 완료")
    print(f" 성공: {len(ok)}/{total}  오류: {len(err)}")
    print(f" 평균 페어 시간: {avg_t:.1f}초")
    print(f" 전체 1645페어 추정: {timedelta(seconds=int(avg_t * 1645 / 4))} (4GPU 기준)")
    print(f" 결과: {out_path}")
    print(f"{'='*55}")

    # SSTR2 결과
    sstr2 = [r for r in ok if r["receptor"] == "SSTR2"]
    if sstr2:
        print(f"\n SSTR2 iPTM: {[round(r['iptm'], 3) for r in sstr2]}")


if __name__ == "__main__":
    main()
