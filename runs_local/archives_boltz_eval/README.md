# archives Boltz-2 대규모 재평가

## 개요

- **목적**: archives 539 후보 → unique 333개 → top10 제외 → **~323 후보 × 5 SSTR = ~1615 페어** 재평가
- **기반**: `docs/selectivity_demo_20260511/run_boltz_batch.py` (50쌍 검증 완료)
- **GPU 요구사항**: H100 NVL ×4 (각 96GB), compute capability 8.9

---

## GPU 요구사항 확인

```bash
# GPU 상태 확인 (실행 전 필수)
nvidia-smi

# 예상 출력
# 0  NVIDIA H100 NVL  95830MiB  FREE
# 1  NVIDIA H100 NVL  95830MiB  FREE
# 2  NVIDIA H100 NVL  95830MiB  FREE
# 3  NVIDIA H100 NVL  95830MiB  FREE
```

---

## 실행 순서

### Step 1: Mini-test (필수 — 파이프라인 검증)

```bash
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
python runs_local/archives_boltz_eval/test_small.py
```

- 5 후보 × 5 SSTR = **25 페어**
- 소요: **약 12-15분** (H100 단일, GPU=3)
- 결과: `runs_local/archives_boltz_eval/test_small_out/test_results.json`
- 확인: 평균 페어 시간 → 전체 ETA 자동 추정 출력

```
# 예상 출력 예시
[01/25] AGCKNFFWKTFDSE × SSTR2 ... OK iPTM=0.923 (28s) ETA 0:11:12
...
Mini-test 완료
성공: 25/25  오류: 0
평균 페어 시간: 29.3초
전체 1645페어 추정: 2:00:27 (4GPU 기준)
```

### Step 2: 본격 실행 (사용자 GPU 가용성 확인 후 실행)

```bash
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr

# 4-GPU 풀 실행 (권장, ~4시간)
python runs_local/archives_boltz_eval/run_full_eval.py --n-gpus 4

# 특정 GPU ID 지정
python runs_local/archives_boltz_eval/run_full_eval.py --gpu-ids 0,1,2,3

# 단일 GPU (13-14시간)
python runs_local/archives_boltz_eval/run_full_eval.py --n-gpus 1

# dry-run (후보 추출 통계만 확인)
python runs_local/archives_boltz_eval/run_full_eval.py --dry-run
```

### Step 3: 중단 후 재개

```bash
# Ctrl+C로 중단 후 재개 (완료된 페어 자동 SKIP)
python runs_local/archives_boltz_eval/run_full_eval.py --resume
```

---

## 파일 구조

```
runs_local/archives_boltz_eval/
├── run_full_eval.py          # 메인 배치 스크립트 (4-GPU 병렬)
├── test_small.py             # 25페어 mini-test
├── README.md                 # 이 파일
│
# 실행 중 생성:
├── partial_0.json            # GPU0 체크포인트 (10페어마다 저장)
├── partial_1.json            # GPU1 체크포인트
├── partial_2.json            # GPU2 체크포인트
├── partial_3.json            # GPU3 체크포인트
├── all_results.json          # 최종 머지 결과
├── gpu_monitor_archives.csv  # GPU 사용률/온도 로그 (5분 간격)
│
├── yamls_gpu0/               # GPU0 입력 YAML
├── yamls_gpu1/               # GPU1 입력 YAML
├── yamls_gpu2/               # GPU2 입력 YAML
├── yamls_gpu3/               # GPU3 입력 YAML
│
├── boltz_out_gpu0/           # GPU0 Boltz-2 출력 (PDB + confidence JSON)
├── boltz_out_gpu1/
├── boltz_out_gpu2/
├── boltz_out_gpu3/
│
└── test_small_out/           # mini-test 결과
    ├── test_results.json
    └── boltz_out/
```

---

## 입력 파일 의존성

| 파일/디렉토리 | 용도 | 상태 |
|---|---|---|
| `runs/pyrosetta_flow/archives/*_dashboard.json` | 539 후보 서열 소스 | ✅ 11개 존재 |
| `runs_local/selectivity_demo_20260511/top10_candidates.json` | 제외 목록 (10개) | ✅ |
| `runs_local/selectivity_demo_20260511/alphafold_receptors/AF-*-msa.a3m` | SSTR1-5 MSA | ✅ 5개 |
| `conda env boltz` | Boltz-2 2.2.1 | ✅ (검증 완료) |

---

## 출력 결과 스키마

```json
[
  {
    "sequence": "AGCKNFFWKTFDSE",
    "receptor": "SSTR2",
    "iptm": 0.923,
    "ptm": 0.871,
    "confidence": 0.847,
    "complex_plddt": 0.812,
    "complex_iplddt": 0.803,
    "pair_chains_iptm": 0.931,
    "status": "ok",
    "elapsed_sec": 28.3,
    "gpu_id": 2,
    "timestamp": "2026-05-13T02:31:14"
  }
]
```

---

## 체크포인트 / Resume 동작

- 각 GPU worker가 `partial_{gpu_id}.json` 에 10페어마다 누적 저장
- `--resume` 플래그로 재시작 시, 기존 partial 파일을 스캔하여 완료된 `(sequence, receptor)` 쌍 SKIP
- 완료 후 `all_results.json` 으로 자동 머지

---

## GPU 모니터링

```bash
# 실행 중 실시간 확인
watch -n 30 nvidia-smi

# 로그 확인
tail -f runs_local/archives_boltz_eval/gpu_monitor_archives.csv
```

---

## 예상 소요 시간

| 설정 | 페어 수 | 예상 시간 |
|---|---|---|
| 4-GPU 병렬 | 1615 | ~3.5 시간 |
| 2-GPU 병렬 | 1615 | ~7 시간 |
| 1-GPU | 1615 | ~14 시간 |

> 기준: H100 NVL 1대 = 30초/페어 (recycling_steps=1, sampling_steps=50)

---

## 완료 후 분석

```bash
# all_results.json 기본 분석
python3 - <<'EOF'
import json
from collections import defaultdict

results = json.load(open("runs_local/archives_boltz_eval/all_results.json"))
ok = [r for r in results if r.get("status") == "ok"]
by_rec = defaultdict(list)
for r in ok:
    by_rec[r["receptor"]].append(r["iptm"])
for rec in ["SSTR1","SSTR2","SSTR3","SSTR4","SSTR5"]:
    vals = by_rec[rec]
    print(f"{rec}: n={len(vals)}, avg={sum(vals)/len(vals):.3f}, max={max(vals):.3f}")

# SSTR2 상위 20개
sstr2 = sorted([r for r in ok if r["receptor"]=="SSTR2"], key=lambda x: x["iptm"], reverse=True)
print("\nSSTR2 Top 20:")
for i, r in enumerate(sstr2[:20], 1):
    print(f"{i:3d}. {r['sequence']}  iPTM={r['iptm']:.3f}")
EOF
```

---

## 참고

- **오프라인 우회**: `docs/boltz2_offline_workaround.md` — ColabFold MSA 서버 차단 환경 대응
- **기반 스크립트**: `docs/selectivity_demo_20260511/run_boltz_batch.py` (50쌍 검증)
- **conda env**: `boltz` (boltz 2.2.1, CUDA 11.8+)
- **KAERI 환경**: H100 NVL ×4, CUDA_VISIBLE_DEVICES=0,1,2,3
