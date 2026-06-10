# A-06 VRAM 검증 보고서 — H100 NVL Multi-GPU 가용성

**작성**: engineer-infra  
**날짜**: 2026-05-20  
**참조**: `docs/meet_log/2026-04-06_action_items/A-06_diffusion_docking_PoC.md`  
**전일 SOD**: `_workspace/release/sod-2026-05-19-A06-diffdock-poc.md`

---

## 검증 결과 요약

| 항목 | 측정값 | 판정 |
|---|---|---|
| 단일 GPU VRAM peak (DiffPepDock, 3 poses) | **2,950 MiB (≈ 2.95 GB)** | ✅ OK (OOM 없음) |
| 단일 GPU VRAM peak (외삽: 10 poses) | **≤ 4 GB 추정** | ✅ OK |
| Multi-GPU 지원 여부 | **DataParallel(DP) + DDP 코드 구현됨** | ✅ 분산 가능 (조건부) |
| 4-GPU 분산 1회 실행 | **N/A** (openmm 이슈 + 코드 수정 금지 제약) | 미실행 |
| **A-07 에스컬레이션 필요?** | **N** | 단일 GPU OK, VRAM 여유 충분 |

---

## Step 1 — 환경 인벤토리

### GPU 상태 (2026-05-20 02:10)

| GPU | 이름 | VRAM 사용 | VRAM 전체 | 가용 여부 |
|---|---|---|---|---|
| 0 | H100 NVL | 89,785 MiB | 95,830 MiB | ❌ 다른 작업 점유 |
| 1 | H100 NVL | 89,417 MiB | 95,830 MiB | ❌ 다른 작업 점유 |
| **2** | H100 NVL | **14 MiB** | **95,830 MiB** | ✅ **가용** |
| **3** | H100 NVL | **14 MiB** | **95,830 MiB** | ✅ **가용** |

- **점유 프로세스**: GPU 0, 1에 프로세스 있음 (nvidia-smi Processes 섹션에 PID 없음으로 표시되나 메모리 점유)
- **활성 uvicorn/flexpepdock 잡**: 없음 (GPU 2, 3 idle 확인)
- **CUDA_VISIBLE_DEVICES**: `2,3` (`~/.zshrc`)
- **환경**: conda `diffpepbuilder` (Python 3.9.16, PyTorch 2.1.0+cu118)

---

## Step 2 — DiffPepDock VRAM 측정 (단일 GPU 2)

### 실행 조건

```bash
CUDA_VISIBLE_DEVICES=2 \
python pipeline_local/scripts/run_diffpepdock_inference.py \
  --metadata-csv runs_local/diffdock_poc/processed/metadata_test.csv \
  --num-poses 3 \
  --gpu-id 0  # CUDA_VISIBLE_DEVICES=2 → env 내 index 0 = 물리 GPU 2
```

### 결과

| 항목 | 값 |
|---|---|
| poses 수 | 3 |
| 실행 시간 | 27.9 sec |
| **VRAM peak** | **3,019 MiB (≈ 2.95 GB)** |
| OOM 발생 | 없음 |
| 종료 코드 | 0 (성공) |

**모니터링 방법**: `nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv -lms 500` 백그라운드 실행, peak 추출 (`sort -n | tail`)

**스케일 추정** (3→10 poses):
- 체크포인트: 1.2 GB (고정)
- 추론 배치 메모리: poses 수에 따라 선형 증가
- 10 poses 기준 **≤ 4 GB 추정** (H100 95 GB 대비 약 4% 사용)

### openmm 이슈 현황

기존 5/19 PoC와 동일:
- `libstdc++.so.6: GLIBCXX_3.4.30 not found` (openmm 8.0 요구)
- 우회: `pipeline_local/scripts/run_diffpepdock_inference.py`의 sys.modules mock으로 처리
- **영향**: Amber/Rosetta postprocess 비활성화 → 도킹 포즈 생성에는 무관

---

## Step 3 — Multi-GPU 분산 가능성 검증

### 소스 코드 분석 결과

**대상 파일**: `local_models/DiffPepBuilder/experiments/run_docking.py`

```python
# DataParallel 임포트
from torch.nn import DataParallel as DP

# num_gpus > 1 → DataParallel 또는 DDP 분기
elif self._exp_conf.num_gpus > 1:
    device_ids = [f"cuda:{i}" for i in self._available_gpus[:self._exp_conf.num_gpus]]
    if self._use_ddp:
        # DDP mode: torchrun --nproc-per-node=N 필요
        ...
    else:
        # DataParallel mode: 단일 프로세스 Multi-GPU
        self._model = DP(self._model, device_ids=device_ids)

# GPU 탐지: GPUtil.getAvailable(order='memory', limit=8)
# CUDA_VISIBLE_DEVICES=2,3 → env idx [0,1] 자동 탐지됨
```

**지원 여부 판정**:

| 항목 | 결과 |
|---|---|
| DataParallel(DP) 코드 구현 | ✅ 완료 (run_docking.py, run_inference.py) |
| DistributedDataParallel(DDP) 코드 구현 | ✅ 완료 (torchrun --nproc-per-node 필요) |
| GPU 자동 탐지 | ✅ `GPUtil.getAvailable()` 기반 |
| `num_gpus=2` (GPU 2+3) DP 실행 가능성 | ✅ 코드 지원, CUDA_VISIBLE_DEVICES=2,3 기준 |
| `num_gpus=4` DDP (4개 전체) | ⚠️ GPU 0,1 점유 중 → 현재 불가 |

### 4-GPU 분산 실행 결과

**실행 시도**: N/A

**이유**:
1. GPU 0, 1 현재 다른 작업 점유 (~89 GB 각)
2. 우회 스크립트 `run_diffpepdock_inference.py`에 `num_gpus=1` 하드코딩 (코드 수정 금지 제약)
3. 원본 `run_docking.py`는 openmm GLIBCXX 이슈로 직접 실행 불가

**가용 GPU만 사용 시 (GPU 2+3, 2-GPU DP)**: 코드 지원 확인됨, infra 수정 후 실행 가능

---

## Step 4 — 결론 및 A-07 에스컬레이션 판단

### 종합 표

| 항목 | 측정값 | 판정 |
|---|---|---|
| 단일 GPU VRAM peak (DiffPepDock 1 sample, 3 poses) | **~2.95 GB (3,019 MiB)** | ✅ OK — H100 95GB 대비 3% |
| 단일 GPU OOM | 없음 | ✅ |
| Multi-GPU 지원 여부 | DataParallel + DDP 코드 구현됨 | ✅ 분산 가능 (코드 레벨) |
| 4-GPU 분산 1회 실행 | N/A (GPU 0,1 점유 + openmm 이슈) | 미검증 |
| 회의록 §A-06 VRAM 120 GB 요건 충족 | 단일 GPU 3GB → 충분 초과 | ✅ |
| **A-07 에스컬레이션 필요?** | **N** | **단일 H100 95GB로 충분** |

### A-07 에스컬레이션 결정: **N (불필요)**

**근거**:
- DiffPepDock VRAM peak ≈ 3 GB (10 poses 기준 ≤ 4 GB 추정)
- 단일 H100 NVL (95 GB) 으로 여유 있음
- GPU 2, 3 (각 ~95 GB) 모두 가용 → 병렬 스크리닝 2배 가능
- 단, DiffPepDock 자체는 SS bond 미지원, 점수 없음으로 **운영 도입 기각 결정 유지** (5/19 PoC 결론)

---

## engineer-infra 액션 아이템

| 항목 | 우선순위 | 내용 |
|---|---|---|
| **openmm GLIBCXX 수정** | Medium | `conda install -c conda-forge libstdcxx-ng>=12` 또는 openmm 다운그레이드 → run_docking.py 직접 실행 가능화 |
| **2-GPU DP 실행 검증** | Low | GPU 2+3으로 `run_diffpepdock_inference.py`에 `num_gpus=2` 지원 추가 후 재검증 |
| **GPU 0,1 점유 확인** | Background | 현재 89 GB 점유 프로세스 정체 파악 (프로세스 목록에 PID 없음 — 좀비/캐시 가능성) |

---

## 참고 파일

| 파일 | 경로 |
|---|---|
| GPU 모니터링 로그 | `/tmp/gpu_monitor_a06.csv` |
| VRAM 측정 출력 | `/tmp/diffpepdock_vram_test/` |
| 기존 PoC 보고서 | `runs_local/diffdock_poc/poc_report.md` |
| DiffPepBuilder 소스 | `local_models/DiffPepBuilder/experiments/run_docking.py` |
| 추론 스크립트 | `pipeline_local/scripts/run_diffpepdock_inference.py` |

---

*보고서 작성: 2026-05-20 engineer-infra*
