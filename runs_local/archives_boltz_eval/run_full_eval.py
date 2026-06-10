#!/usr/bin/env python3
"""
runs_local/archives_boltz_eval/run_full_eval.py

대규모 archives 재평가 — 329 후보 × 5 SSTR = 1645 페어
4-GPU 병렬 실행 + 체크포인트 + resume 지원

사용법:
    python run_full_eval.py --n-gpus 4          # 본격 실행 (4시간 추정)
    python run_full_eval.py --n-gpus 1          # 단일 GPU (14시간 추정)
    python run_full_eval.py --resume            # 중단된 잡 재개
    python run_full_eval.py --dry-run           # 후보 추출 확인만

주의: 본격 실행 전 GPU 가용성 확인 필요 (nvidia-smi)
"""

import argparse
import json
import multiprocessing as mp
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# 경로 설정
# ============================================================
REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVES_DIR = REPO_ROOT / "runs" / "pyrosetta_flow" / "archives"
TOP10_FILE = REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "top10_candidates.json"
AF_DIR = REPO_ROOT / "runs_local" / "selectivity_demo_20260511" / "alphafold_receptors"
OUT_DIR = Path(__file__).resolve().parent

# ============================================================
# SSTR 설정 (검증된 UniProt + 서열)
# ============================================================
UNIPROT = {
    "SSTR1": "P30872",
    "SSTR2": "P30874",
    "SSTR3": "P32745",
    "SSTR4": "P31391",
    "SSTR5": "P35346",
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


# ============================================================
# 후보 추출
# ============================================================

def extract_candidates():
    """archives dashboard.json → unique 서열 → top10 제외 → 정렬 리스트 반환"""
    dashboard_files = sorted(ARCHIVES_DIR.glob("*_dashboard.json"))
    if not dashboard_files:
        raise FileNotFoundError(f"dashboard.json 없음: {ARCHIVES_DIR}")

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
    return remaining, top10_seqs, len(all_seqs)


# ============================================================
# 완료 페어 로딩 (resume)
# ============================================================

def load_completed_pairs(out_dir: Path, n_gpus: int):
    """기존 partial_*.json 파일에서 완료된 (seq, receptor) 쌍 집합 반환"""
    completed = {}  # (seq, rname) -> result dict
    for gpu_id in range(n_gpus):
        pf = out_dir / f"partial_{gpu_id}.json"
        if pf.exists():
            try:
                data = json.loads(pf.read_text())
                for r in data:
                    key = (r.get("sequence", ""), r.get("receptor", ""))
                    if key[0] and key[1]:
                        completed[key] = r
            except Exception as e:
                print(f"[경고] {pf} 로드 실패: {e}", flush=True)
    return completed


# ============================================================
# Boltz-2 실행 (단일 페어)
# ============================================================

def run_boltz_pair(seq: str, rname: str, yaml_path: Path,
                   run_out: Path, gpu_id: int) -> dict:
    """단일 페어 Boltz-2 실행 → confidence dict 반환"""
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
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600, env=env
        )
    except subprocess.TimeoutExpired:
        return {
            "sequence": seq, "receptor": rname,
            "status": "error", "error": "timeout_600s",
        }

    conf_files = list(run_out.rglob("confidence_*_model_0.json"))
    if conf_files:
        try:
            conf = json.loads(conf_files[0].read_text())
            return {
                "sequence": seq,
                "receptor": rname,
                "iptm": conf.get("iptm"),
                "ptm": conf.get("ptm"),
                "confidence": conf.get("confidence_score"),
                "complex_plddt": conf.get("complex_plddt"),
                "complex_iplddt": conf.get("complex_iplddt"),
                "pair_chains_iptm": (
                    conf.get("pair_chains_iptm", {}).get("0", {}).get("1")
                ),
                "status": "ok",
            }
        except Exception as e:
            return {
                "sequence": seq, "receptor": rname,
                "status": "error", "error": f"conf_parse:{e}",
            }
    else:
        return {
            "sequence": seq, "receptor": rname,
            "status": "error",
            "error": "no_conf_file",
            "stderr_tail": proc.stderr[-600:] if proc.stderr else "",
        }


# ============================================================
# Worker 프로세스 (GPU 1대 담당)
# ============================================================

def worker_process(
    gpu_id: int,
    pairs: list,          # [(seq, rname), ...]
    completed_keys: set,  # 이미 완료된 (seq, rname) 집합
    out_dir: Path,
    progress_queue: mp.Queue,
):
    """GPU gpu_id에서 pairs를 순차 처리"""
    partial_file = out_dir / f"partial_{gpu_id}.json"

    # 기존 partial 결과 불러오기
    if partial_file.exists():
        try:
            existing = json.loads(partial_file.read_text())
        except Exception:
            existing = []
    else:
        existing = []

    results = list(existing)

    yaml_dir = out_dir / f"yamls_gpu{gpu_id}"
    yaml_dir.mkdir(parents=True, exist_ok=True)

    total = len(pairs)
    new_done = 0

    for local_idx, (seq, rname) in enumerate(pairs):
        key = (seq, rname)

        # 이미 완료된 페어 SKIP
        if key in completed_keys:
            progress_queue.put({
                "type": "skip",
                "gpu_id": gpu_id,
                "local_idx": local_idx,
                "total": total,
            })
            continue

        # YAML 작성
        pep_safe = "".join(c for c in seq if c.isalpha())[:16]
        cid = f"g{gpu_id}_{local_idx:04d}_{pep_safe}"

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

        run_out = out_dir / f"boltz_out_gpu{gpu_id}" / f"{cid}__{rname}"
        run_out.mkdir(parents=True, exist_ok=True)

        t0 = time.time()
        result = run_boltz_pair(seq, rname, yaml_path, run_out, gpu_id)
        elapsed = time.time() - t0

        result["elapsed_sec"] = round(elapsed, 1)
        result["gpu_id"] = gpu_id
        result["timestamp"] = datetime.now().isoformat()
        results.append(result)
        new_done += 1

        # 진행 상황 큐 전송
        progress_queue.put({
            "type": "done",
            "gpu_id": gpu_id,
            "local_idx": local_idx,
            "total": total,
            "elapsed_sec": elapsed,
            "seq": seq[:8] + "..",
            "receptor": rname,
            "status": result["status"],
            "iptm": result.get("iptm"),
        })

        # 10개마다 중간 저장
        if new_done % 10 == 0:
            with open(partial_file, "w") as f:
                json.dump(results, f, indent=2)

    # 최종 저장
    with open(partial_file, "w") as f:
        json.dump(results, f, indent=2)

    progress_queue.put({"type": "worker_done", "gpu_id": gpu_id, "count": new_done})


# ============================================================
# GPU 모니터링 스레드
# ============================================================

def gpu_monitor_thread(out_dir: Path, stop_event: threading.Event, interval: int = 300):
    """5분 간격 nvidia-smi 로그 (gpu_monitor_archives.csv)"""
    csv_path = out_dir / "gpu_monitor_archives.csv"
    header_written = csv_path.exists()

    while not stop_event.is_set():
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True, text=True, timeout=30,
            )
            with open(csv_path, "a") as f:
                if not header_written:
                    f.write("timestamp,index,name,gpu_util_%,mem_used_mib,mem_total_mib,temp_c\n")
                    header_written = True
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        f.write(f"{ts},{line}\n")
        except Exception:
            pass
        stop_event.wait(interval)


# ============================================================
# 메인 진행 추적 (progress monitor)
# ============================================================

def progress_monitor(
    progress_queue: mp.Queue,
    total_pairs: int,
    already_done: int,
    n_gpus: int,
    eta_start: float,
):
    """큐에서 이벤트를 수신하며 ETA·진행 상황 출력"""
    workers_done = 0
    pairs_done = already_done
    pairs_skipped = 0
    timings = []  # elapsed_sec 리스트 (ETA 계산용)

    while workers_done < n_gpus:
        try:
            msg = progress_queue.get(timeout=120)
        except Exception:
            print("[monitor] 큐 타임아웃 — 계속 대기", flush=True)
            continue

        mtype = msg.get("type")

        if mtype == "skip":
            pairs_skipped += 1
            pairs_done += 1

        elif mtype == "done":
            pairs_done += 1
            elapsed = msg.get("elapsed_sec", 0)
            if elapsed > 0:
                timings.append(elapsed)
                if len(timings) > 200:
                    timings.pop(0)

            # 평균 시간 → ETA
            avg_sec = sum(timings) / len(timings) if timings else 30
            remaining = total_pairs - pairs_done
            eta_sec = avg_sec * remaining
            eta_str = str(timedelta(seconds=int(eta_sec)))

            pct = pairs_done / total_pairs * 100 if total_pairs > 0 else 0
            iptm_str = f" iPTM={msg['iptm']:.3f}" if msg.get("iptm") is not None else ""
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"GPU{msg['gpu_id']} {msg['seq']}×{msg['receptor']} "
                f"→ {msg['status']}{iptm_str} | "
                f"{pairs_done}/{total_pairs} ({pct:.1f}%) ETA {eta_str}",
                flush=True,
            )

        elif mtype == "worker_done":
            workers_done += 1
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"GPU{msg['gpu_id']} 완료 — 신규 처리 {msg['count']}페어",
                flush=True,
            )

    total_elapsed = time.time() - eta_start
    print(f"\n전체 완료: {pairs_done}페어 처리 ({pairs_skipped}개 skip), "
          f"총 소요 {timedelta(seconds=int(total_elapsed))}", flush=True)


# ============================================================
# 결과 머지
# ============================================================

def merge_partials(out_dir: Path, n_gpus: int) -> Path:
    """partial_*.json 머지 → all_results.json"""
    all_results = []
    for gpu_id in range(n_gpus):
        pf = out_dir / f"partial_{gpu_id}.json"
        if pf.exists():
            try:
                data = json.loads(pf.read_text())
                all_results.extend(data)
            except Exception as e:
                print(f"[경고] {pf} 머지 실패: {e}", flush=True)

    out_path = out_dir / "all_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    return out_path


# ============================================================
# 결과 요약 출력
# ============================================================

def print_summary(all_results: list):
    """완료 후 SSTR별 iPTM 평균 + 상위 10개 출력"""
    ok = [r for r in all_results if r.get("status") == "ok" and r.get("iptm") is not None]
    err = [r for r in all_results if r.get("status") == "error"]

    print(f"\n{'='*60}")
    print(f" 결과 요약: 총 {len(all_results)}페어 / 성공 {len(ok)} / 오류 {len(err)}")
    print(f"{'='*60}")

    # SSTR별 평균
    from collections import defaultdict
    by_rec = defaultdict(list)
    for r in ok:
        by_rec[r["receptor"]].append(r["iptm"])
    for rec in RECEPTOR_ORDER:
        vals = by_rec.get(rec, [])
        if vals:
            print(f"  {rec}: n={len(vals)}, avg_iPTM={sum(vals)/len(vals):.3f}, "
                  f"max={max(vals):.3f}, min={min(vals):.3f}")

    # SSTR2 상위 10개
    sstr2 = [r for r in ok if r["receptor"] == "SSTR2"]
    sstr2.sort(key=lambda x: x["iptm"], reverse=True)
    print(f"\n  SSTR2 상위 10개 (iPTM 기준):")
    for i, r in enumerate(sstr2[:10], 1):
        print(f"  {i:2d}. {r['sequence']} iPTM={r['iptm']:.3f}")


# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="archives 후보 × 5 SSTR Boltz-2 대규모 평가 (4-GPU 병렬)"
    )
    parser.add_argument(
        "--n-gpus", type=int, default=4,
        help="사용할 GPU 수 (기본: 4). CUDA_VISIBLE_DEVICES=0,1,...,n-1"
    )
    parser.add_argument(
        "--gpu-ids", type=str, default=None,
        help="GPU ID 직접 지정 (예: '0,2,3'). --n-gpus 무시됨."
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="기존 partial_*.json 기반 재개"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="후보 추출 통계만 출력 (실제 실행 없음)"
    )
    parser.add_argument(
        "--out-dir", type=str, default=None,
        help="결과 저장 디렉토리 (기본: 스크립트 위치)"
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # GPU ID 결정
    if args.gpu_ids:
        gpu_ids = [int(x) for x in args.gpu_ids.split(",")]
    else:
        gpu_ids = list(range(args.n_gpus))
    n_gpus = len(gpu_ids)

    # ── 후보 추출 ──────────────────────────────────────────
    print(f"[{datetime.now().isoformat()}] 후보 추출 중...", flush=True)
    candidates, top10_seqs, total_unique = extract_candidates()
    total_pairs = len(candidates) * 5

    print(f"  archives unique 서열: {total_unique}")
    print(f"  top10 제외 후:       {len(candidates)}")
    print(f"  총 페어:             {total_pairs} ({len(candidates)} × 5 SSTR)")
    print(f"  GPU:                 {n_gpus}대 (ids={gpu_ids})")
    # 병렬 GPU 고려: 총 페어 / GPU 수 × 30초
    eta_sec_parallel = (total_pairs * 30) // n_gpus
    print(f"  예상 시간:           ~{eta_sec_parallel//3600}h {(eta_sec_parallel%3600)//60}m "
          f"(30초/페어, {n_gpus}GPU 병렬 기준)")

    if args.dry_run:
        print("\n[dry-run] 실행 없이 종료.")
        return

    if not AF_DIR.exists():
        print(f"[오류] AlphaFold MSA 디렉토리 없음: {AF_DIR}", file=sys.stderr)
        sys.exit(1)

    for rname, upid in UNIPROT.items():
        msa_file = AF_DIR / f"AF-{upid}-F1-msa.a3m"
        if not msa_file.exists():
            print(f"[오류] {rname} MSA 파일 없음: {msa_file}", file=sys.stderr)
            sys.exit(1)

    # ── Resume: 기존 완료 페어 로딩 ────────────────────────
    if args.resume:
        print("\n[resume] 기존 partial 파일 로딩...", flush=True)
        completed_pairs = load_completed_pairs(out_dir, n_gpus)
        print(f"  이미 완료된 페어: {len(completed_pairs)}개", flush=True)
    else:
        completed_pairs = {}

    completed_keys = set(completed_pairs.keys())

    # ── 페어 생성 & 청크 분할 ────────────────────────────
    all_pairs = [(seq, rname) for seq in candidates for rname in RECEPTOR_ORDER]

    # 각 GPU 청크 (round-robin 분배로 수용체 편중 방지)
    chunks = [[] for _ in range(n_gpus)]
    for i, pair in enumerate(all_pairs):
        chunks[i % n_gpus].append(pair)

    print(f"\n  청크 분할: {[len(c) for c in chunks]} 페어/GPU", flush=True)

    # ── GPU 모니터링 스레드 시작 ────────────────────────
    stop_monitor = threading.Event()
    monitor_t = threading.Thread(
        target=gpu_monitor_thread,
        args=(out_dir, stop_monitor, 300),
        daemon=True,
    )
    monitor_t.start()
    print(f"  GPU 모니터링: {out_dir / 'gpu_monitor_archives.csv'} (5분 간격)", flush=True)

    # ── Worker 프로세스 시작 ────────────────────────────
    progress_queue: mp.Queue = mp.Queue()
    processes = []

    already_done = len(completed_keys)
    eta_start = time.time()

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 워커 프로세스 {n_gpus}개 시작...\n",
          flush=True)

    for i, gpu_id in enumerate(gpu_ids):
        p = mp.Process(
            target=worker_process,
            args=(gpu_id, chunks[i], completed_keys, out_dir, progress_queue),
            daemon=False,
        )
        p.start()
        processes.append(p)

    # ── 진행 모니터 (메인 스레드) ───────────────────────
    progress_monitor(
        progress_queue=progress_queue,
        total_pairs=total_pairs,
        already_done=already_done,
        n_gpus=n_gpus,
        eta_start=eta_start,
    )

    # ── 프로세스 완료 대기 ──────────────────────────────
    for p in processes:
        p.join()

    stop_monitor.set()

    # ── 결과 머지 ────────────────────────────────────────
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 결과 머지 중...", flush=True)
    all_results_path = merge_partials(out_dir, n_gpus)
    all_results = json.loads(all_results_path.read_text())

    print(f"  저장: {all_results_path}", flush=True)

    # ── 요약 출력 ────────────────────────────────────────
    print_summary(all_results)

    # ── 완료 알림 ────────────────────────────────────────
    elapsed_total = time.time() - eta_start
    ok_count = sum(1 for r in all_results if r.get("status") == "ok")
    print(f"\n{'='*60}")
    print(f" 완료! {ok_count}/{len(all_results)}페어 성공")
    print(f" 총 소요시간: {timedelta(seconds=int(elapsed_total))}")
    print(f" 결과 파일: {all_results_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
