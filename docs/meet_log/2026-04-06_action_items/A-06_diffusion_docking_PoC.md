# A-06: 디퓨전 모델 기반 도킹 가속화 PoC

## 메타
- 회의: KAERI-AIRL-MOM-2026-003 (2026-04-06)
- 담당: AI팀
- 기한: 5월 회의 전
- 상태: ✅ **완료 — NOT_RECOMMENDED 결론** (2026-05-19 audit, PR #65 PPTX 슬라이드 7)
- **audit 결과 요약**: DiffPepDock 평가 → SS bond(Cys3-Cys14) 처리 불가, 본 프로젝트 적용 부적합. Rosetta FlexPepDock 유지 권장.
- 비고: GPU 가용성 확인 후 착수 (A-07 연동 가능) — 결론이 NOT_RECOMMENDED이므로 A-07 의존성도 자연 해소

---

## 배경

현행 Silo B 파이프라인은 PyRosetta FlexPepDock
(`AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/`)과
Boltz-2(`pipeline_local/scripts/offtarget_dock.py`)를 병용한다.
FlexPepDock은 후보당 수 분 이상 소요되어 대규모 스크리닝의 병목이 된다.

**DiffDock** 등 디퓨전 기반 도킹 모델은 1 inference에 수십 초 내외로 처리되어
1차 필터로 활용 가능성이 있다. 본 PoC는 정확도(RMSD)와 속도(wall-clock time)를
실측하여 파이프라인 통합 여부를 결정하는 검증 실험이다.

---

## 수행 방법 (단계별)

### Step 1 — 모델 선정 및 환경 준비
우선 검토 대상:

| 모델 | 특징 | 논문/리포지토리 |
|------|------|---------------|
| **DiffDock** (1순위) | SE(3) diffusion, blind/site-specific 지원 | [arXiv:2210.01776](https://arxiv.org/abs/2210.01776) |
| DiffDock-L | 경량화 버전, VRAM 절약 | DiffDock 공식 GitHub |
| NeuralPLexer | 단백질-리간드 복합체 전용 | [arXiv:2209.15171](https://arxiv.org/abs/2209.15171) |
| AlphaFold3 (펩타이드) | Boltz-2와 유사, 결합 포즈 예측 | Deepmind |

> DiffDock은 소분자 리간드를 기본으로 설계되어 있어 **펩타이드(14aa)** 적용 시
> 선행 연구 검토 필요. 펩타이드 도킹에 맞게 수정된 DiffDock-PP 변형도 검토할 것.

GPU 준비 확인:
```bash
nvidia-smi  # H100 NVL ×4 확인 (CUDA_VISIBLE_DEVICES=2 기본 설정)
# VRAM 요구사항: DiffDock 기준 ~12-24 GB (모델 크기에 따라 상이)
# 회의록 A-06 원문: VRAM 120 GB 이상 (DGX급) — 서브모델 병렬 실행 시
```

### Step 2 — Ground Truth 준비 (SSTR2–SST14 복합체)
```bash
# SSTR2 수용체 구조
RECEPTOR=data/somatostatin_receptor/SSTR2_7XNA.pdb

# SST14 펩타이드 좌표 (cryo-EM에서 추출 또는 FlexPepDock 최적 포즈 사용)
LIGAND=runs_local/sst14_ref_docking/sst14_best_pose.pdb
```
- Ground truth 포즈: RCSB에서 7T10 또는 7T11의 펩타이드 체인 추출 권장.
- 로컬 7XNA에 펩타이드 체인이 포함되어 있으면 직접 사용 가능.

### Step 3 — DiffDock 도킹 실행
```bash
conda activate diffdock  # 별도 환경 필요 시 engineer-infra 요청

python -m inference \
    --protein_path ${RECEPTOR} \
    --ligand ${LIGAND} \
    --out_dir runs_local/diffdock_poc \
    --inference_steps 20 \
    --samples_per_complex 40 \
    --batch_size 10 \
    --actual_steps 18
```

### Step 4 — RMSD 비교 (DiffDock vs cryo-EM)
```python
from Bio.PDB import PDBParser, Superimposer
import numpy as np

def compute_rmsd(pred_pdb: str, ref_pdb: str) -> float:
    """예측 포즈 vs cryo-EM 참조 포즈 RMSD (Cα 기준)."""
    parser = PDBParser(QUIET=True)
    ref_atoms  = list(parser.get_structure("ref",  ref_pdb).get_atoms())
    pred_atoms = list(parser.get_structure("pred", pred_pdb).get_atoms())
    si = Superimposer()
    si.set_atoms(ref_atoms, pred_atoms)
    return si.rms
```
- 합격 기준: **RMSD ≤ 2.0 Å 재현율 ≥ 80 %** (40 포즈 중 32개 이상)

### Step 5 — 속도 비교 (Wall-clock time)
```python
import time

# DiffDock
t0 = time.perf_counter()
run_diffdock(receptor, ligand, n_poses=10)
diffdock_time = time.perf_counter() - t0

# FlexPepDock (현행)
t0 = time.perf_counter()
run_flexpepdock(receptor, ligand, nstruct=10)
flexpepdock_time = time.perf_counter() - t0

speedup = flexpepdock_time / diffdock_time
print(f"DiffDock speedup: {speedup:.1f}×")
```

### Step 6 — PoC 결과 문서화
결과는 `runs_local/diffdock_poc/poc_report.json`에 저장:
```json
{
  "model": "DiffDock",
  "n_poses": 40,
  "rmsd_success_rate": 0.xx,
  "rmsd_mean": x.xx,
  "diffdock_time_sec": xx.x,
  "flexpepdock_time_sec": xx.x,
  "speedup": x.x,
  "recommendation": "통합 가능 / 재검토 필요 / 기각",
  "notes": ""
}
```

---

## 판단 기준 / KPI

| 지표 | 기준 | 비고 |
|------|------|------|
| Top-1 RMSD ≤ 2.0 Å 성공률 | ≥ 80 % | 40 포즈 중 비율 |
| Wall-clock speedup vs FlexPepDock | 목표 ≥ 10× | 후보 1개 기준 |
| VRAM 사용량 | ≤ 80 GB (H100 NVL 단일) | VRAM 120 GB 불충족 시 A-07 연동 |

---

## 활용 도구 / 기술 스택

| 도구 | 용도 |
|------|------|
| DiffDock (Python) | 펩타이드-수용체 도킹 |
| BioPython (`PDBParser`, `Superimposer`) | RMSD 계산 |
| PyRosetta FlexPepDock | 속도 비교 기준선 (`AgenticAI4SCIENCE_pyrosetta_track/`) |
| `runs_local/diffdock_poc/` | 실험 결과 저장 |
| H100 NVL ×4 | GPU 인프라 (CUDA_VISIBLE_DEVICES=2 기본) |

---

## GPU 요구사항 (회의록 A-06 원문)
- **VRAM ≥ 120 GB** 이상이 원문 기재됨.
- 현재 H100 NVL ×4 서버(서버당 VRAM 94 GB × 4 = 376 GB NVLink 공유) 환경에서
  Multi-GPU 모드로 가능 여부를 먼저 확인할 것.
- 불가 시 **A-07** (DGX 검토) 과 연동하여 조달 방향 결정.

---

## 서호성 박사 의견

- 회의록에서 직접 언급은 없으나 A-06은 AI팀 자체 제안 항목으로,
  **파이프라인 1차 필터 도입 가능 여부**가 핵심 판단 기준임.
- RMSD ≤ 2.0 Å / 80 % 이상 달성 시 → Silo B 파이프라인의 FlexPepDock 전단에
  DiffDock을 빠른 pre-filter로 배치.

---

## 본 프로젝트 매핑

- **관련 디렉토리**:
  - `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/` — FlexPepDock 파이프라인
  - `pipeline_local/scripts/flexpep_dock.py` — FlexPepDock 래퍼 (비교 기준선)
  - `pipeline_local/steps/step05_docking.py` — DiffDock 통합 후 교체 대상
  - `runs_local/diffdock_poc/` — PoC 결과 저장
- **관련 모듈/스크립트**:
  - `dock_with_diffdock()` in `step05_docking.py` — 현행 stub 구현 → 실 구현 대상
  - `LocalModelRunner("diffpepbuilder")` — DiffPepBuilder 기반 포즈 예측 인터페이스

---

## 의존성 / 연관 액션 아이템

| 의존 관계 | 액션 |
|----------|------|
| GPU 가용성 불충족 시 | **A-07** (DGX 증설 검토) |
| PoC 성공 시 통합 대상 | **A-01** (site-directed 도킹 좌표와 연동) |
| 속도 비교 기준 | **A-05** (SST14 레퍼런스 ΔG로 정확도 교차 검증) |
