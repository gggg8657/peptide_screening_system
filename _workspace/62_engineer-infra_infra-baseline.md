# 인프라 베이스라인 — Phase 0~5 시스템 점검 사전 스냅샷
작성일: 2026-05-27
작성자: engineer-infra

---

## 1. Conda 환경 (active env, 충돌, deprecated)

### 현재 활성 환경
- `base` (miniforge3) — 현재 셸 active. 작업 중 명시적 activate 없음.

### 전체 환경 목록 (17개 + _workspace 로컬 2개)

| 환경 | Python | 주요 PyTorch | 역할 | 상태 |
|------|--------|-------------|------|------|
| bio-tools | 3.11.15 | 2.10.0+cu124 | PyRosetta + RDKit + peptides | 정상 |
| vllm-server | 3.11.15 | 2.10.0+cu124, vllm 0.18.1 | LLM 서빙 | 정상 |
| esmfold | 3.10.20 | 2.6.0+cu124, fair-esm 2.0.0 | ESMFold | 정상 |
| proteinmpnn | 3.11.15 | 2.2.1 | ProteinMPNN | 정상 |
| boltz | 3.11.0 | 2.5.1+cu121, boltz 2.2.1 | Boltz-1 구조 예측 | 정상 |
| rfdiffusion | 3.9.19 | 2.1.0+cu121 (설계 목표: 1.13.1+cu117) | RFdiffusion | **경고** |
| diffpepbuilder | 3.9.16 | 2.1.0 | DiffPepBuilder | 정상 |
| pepadmet | **3.7.12** | 1.13.1+cu117 | PepADMET 구형 | **위험** |
| pepadmet-upgrade | 3.10.20 | 2.4.1+cu121 | PepADMET 업그레이드 | 정상 |
| peptools | — | — | 펩타이드 유틸리티 | 미확인 |
| genmol | — | — | GenMol | 미확인 |
| openfold3 | — | — | OpenFold3 | 미확인 |
| pybamm-inv, pybamm-inv-cu128 | — | — | 배터리 (프로젝트 무관) | 미확인 |
| _workspace/admet_ai_local/.conda_env | — | — | ADMET-AI 로컬 | 1.7 GB |
| _workspace/pepmsnd_local/.conda_env | — | — | pepMSND 로컬 | **11 GB** |

### 충돌·위험 항목

1. **`pepadmet` — Python 3.7.12 (EOL 2023-06)**
   - Python 3.7은 공식 지원 종료. 보안 패치 없음.
   - torch 1.13.1+cu117: CUDA 11.7 기반 — 현재 서버 CUDA 12.8과 드라이버 호환만 유지됨.
   - 권고: `pepadmet-upgrade` (Python 3.10, torch 2.4.1+cu121) 로 전환 완료 여부 확인 필요.

2. **`rfdiffusion` — torch 버전 드리프트**
   - 설계 목표: `1.13.1+cu117`, 실제 설치: `2.1.0+cu121`
   - torchaudio 0.13.1+cu117 / torchvision 0.14.1+cu117 는 torch 1.13용 — torch 2.1과 **버전 미스매치**.
   - 실제 CUDA 동작(`torch.cuda.is_available() = True, CUDA 12.1`)은 확인되었으나 torchaudio/torchvision 호출 시 런타임 오류 가능.
   - ENVIRONMENT.md는 "GPU 불필요"로 기재되어 있어 — 로컬 GPU 환경 반영 미완료.

3. **`_workspace/pepmsnd_local/.conda_env` — 11 GB 로컬 conda 환경**
   - `_workspace/` 아래 비표준 위치 환경. 재현 가능성 낮음.

---

## 2. GPU 가용성 (nvidia-smi 현재 상태)

스냅샷 시각: 2026-05-27 08:29

| GPU | 모델 | VRAM 사용/전체 | GPU 이용률 | 온도 |
|-----|------|--------------|-----------|------|
| 0 | H100 NVL | 89787 / 95830 MiB (93.7%) | 0% | 47°C |
| 1 | H100 NVL | 89417 / 95830 MiB (93.3%) | 0% | 47°C |
| 2 | H100 NVL | 19187 / 95830 MiB (20.0%) | 75% | 49°C |
| 3 | H100 NVL | 86287 / 95830 MiB (90.0%) | 0% | 44°C |

**CUDA 버전**: 12.8 (Driver 570.211.01)

### 주의 사항

- GPU 0, 1, 3: VRAM 90~94% 점유 중이나 프로세스 목록은 `[Not Found]`. nvidia-smi의 PID가 현재 셸에서 식별 불가 — 다른 사용자 또는 컨테이너 프로세스일 가능성.
- GPU 2 (`CUDA_VISIBLE_DEVICES=2` — 현재 설정): 75% GPU 이용률, 19 GB 점유. 활성 워크로드 존재.
- **즉시 조치 필요**: GPU 0, 1, 3 점유 프로세스 정체 확인 (`sudo nvidia-smi -q -d COMPUTE` 또는 시스템 관리자 확인). GPU 0, 1, 3에 LLM 가중치 상주 가능 (DeepSeek 62G, GLM 61G, Qwen3.5-122B 234G, Qwen3.5-27B 52G 로컬 보유).

---

## 3. 로컬 모델 가중치 inventory

전체 `local_models/` 크기: **416 GB**

| 디렉토리 | 크기 | 주요 내용 | 상태 |
|---------|------|---------|------|
| `llm/DeepSeek-R1-Distill-Qwen-32B/` | 62 GB | LLM 가중치 | 존재 |
| `llm/GLM-Z1-32B-0414/` | 61 GB | LLM 가중치 | 존재 |
| `llm/Qwen3.5-122B-A10B/` | 234 GB | LLM 가중치 | 존재 |
| `llm/Qwen3.5-27B/` | 52 GB | LLM 가중치 | 존재 |
| `DiffPepBuilder/` | 3.7 GB | ActiveSite_ckpt.pt, Base_ckpt.pt, Complex 계열 등 9개 | 존재 (완전) |
| `RFdiffusion/` | 3.7 GB | models/ 디렉토리 다수 (ActiveSite, Base, InpaintSeq 등) | 존재 (완전) |
| `genmol/` | 1.4 GB | GenMol 가중치 | 존재 |
| `genmol-repo/` | 25 MB | repo 코드 | 존재 |
| `pepadmet/` | 97 MB | data/repo/precomputed/tmp | 존재 |
| `msa_db/` | 2.3 MB | MSA 데이터베이스 | 존재 (소형) |

### 주목: ESMFold/ProteinMPNN 가중치 부재
- `local_models/` 아래 `esmfold/` 또는 `proteinmpnn/` 디렉토리 없음.
- 각 conda 환경(`esmfold`, `proteinmpnn`)은 설치되어 있으나 가중치는 사용 시 자동 다운로드 방식으로 추정.
- Phase 5 파이프라인 실행 전 가중치 사전 캐시 여부 확인 권고.

### LLM 서빙 메모
- `vllm-server` 환경(vllm 0.18.1)으로 4종 모델 서빙 가능.
- Qwen3.5-122B-A10B(234 GB): 4× H100 NVL 전체(4×95 = 380 GB) 범위 내이나 현재 GPU 0/1/3 대부분 점유 상태. 가용 슬롯 부족 가능성.

---

## 4. CI/CD 상태 + 최근 실패

### 워크플로우
- 파일: `.github/workflows/ci.yml` (단일 파일, 375 라인)
- 이름: `Bio Pipeline CI`
- 트리거: `push` → `main`, `feature/**` | `pull_request` → `main`

### Job 구성 (7개)

| Job | 역할 |
|-----|------|
| lint | Python 문법 + Flake8 (E9/F63/F7/F82 블로킹) |
| import-test | BioNeMo 클라이언트 import |
| unit-tests | pytest 유닛 테스트 |
| pharmacology-guard | 약리학 가드 (HEURISTIC_FUNCTION_DISCLAIMERS 등) |
| nim-api-smoke | NVIDIA_API_KEY 있을 때 NIM API 헬스체크 |
| frontend | Node.js 20, npm ci/lint/test/build |
| ai4sci-python-lint | ai4sci-kaeri 서브디렉토리 Python lint |

### 최근 실행 현황 (최근 20건)
- **전체 success** — 최근 20건 중 실패 없음.
- 평균 실행 시간: 1분 48초~1분 53초.
- 마지막 main push: 2026-05-26 (docs 커밋).

### CI 주의 사항
- `nim-api-smoke` job은 `NVIDIA_API_KEY` 시크릿 부재 시 `::warning::` 처리 후 skip — 우회 가능 설계. Phase 5 API 연동 검증 시 시크릿 설정 필요.
- `--exit-zero` 사용으로 style 경고 비블로킹 — 코드 품질 경고는 CI 통과에 영향 없음.

---

## 5. 디스크 사용·정리 후보

| 위치 | 크기 | 비고 |
|------|------|------|
| `local_models/` | 416 GB | LLM 409 GB(98.8%), 생물학 모델 7 GB |
| `_workspace/pepmsnd_local/` | 11 GB | 로컬 conda 환경 포함 |
| `_workspace/admet_ai_local/` | 1.8 GB | 로컬 conda 환경 포함 |
| `_workspace/ai4sci-kaeri-fe-ef/` | 1.1 GB | FE 빌드 워크트리 추정 |
| `_workspace/pepadmet_local/` | 244 MB | pepadmet 로컬 데이터 |
| `runs_local/archives_boltz_eval/` | 4.5 GB | Boltz 평가 아카이브 |
| `runs_local/` 전체 | 6.0 GB | dogfood, dual_* 실험 런 다수 |
| `runs/` | 573 MB | 실험 결과 |
| `logs/` | 1.8 MB | 경량 |
| `_workspace/` (md/pptx 등) | ~30 MB | 문서 산출물 |

### 정리 후보 (우선순위)

1. **`_workspace/pepmsnd_local/.conda_env/` (11 GB)**: `pepmsnd_local` conda 환경이 miniforge3/envs 외부 비표준 위치. 사용 여부 확인 후 제거 또는 이관.
2. **`runs_local/archives_boltz_eval/` (4.5 GB)**: 아카이브용 — 필요 시 외부 스토리지 이동.
3. **`runs_local/dual_*/` 계열 (총 ~600 MB)**: dual_test/verify 다중 런 — 최신 런 1개 외 제거 검토.
4. **`local_models/llm/Qwen3.5-122B-A10B/` (234 GB)**: 4× H100 NVL 전체 메모리 필요. 활성 서빙 스케줄이 없으면 오프로드 검토.

---

## 6. 인프라 리스크 Top 3

### Risk 1 (CRITICAL): GPU 0·1·3 점유 프로세스 정체 불명
- 현황: 3개 GPU에 각각 86~90 GB VRAM 점유. PID 식별 불가.
- 영향: `CUDA_VISIBLE_DEVICES=2` 설정으로 현재 파이프라인은 GPU 2만 사용. GPU 2 19 GB (20%)는 가용.
- 그러나 Phase 5에서 다중 GPU 요구 작업(ESMFold, RFdiffusion 병렬) 시 GPU 부족 우려.
- **즉시 조치**: `sudo nvidia-smi -q -d COMPUTE` 또는 시스템 관리자에게 GPU 0/1/3 점유 주체 확인 요청.

### Risk 2 (HIGH): `pepadmet` 환경 Python 3.7 EOL
- Python 3.7은 2023-06 지원 종료. 보안 취약점 패치 없음.
- `pepadmet-upgrade` (Python 3.10, torch 2.4.1)가 존재하나 파이프라인 코드의 실제 호출 env가 여전히 `pepadmet`인지 확인 필요.
- **즉시 조치**: `pipeline_local/` 및 `scripts/` 에서 `conda activate pepadmet` 호출 위치 점검. `pepadmet-upgrade` 로 전환 완료 여부 검증.

### Risk 3 (MEDIUM): `rfdiffusion` torchaudio/torchvision 버전 미스매치
- `torchaudio 0.13.1+cu117` / `torchvision 0.14.1+cu117` 는 PyTorch 1.13 대응 버전.
- 실제 torch는 `2.1.0+cu121` — 주 버전 불일치.
- torch.cuda.is_available()은 True이나 audio/vision 관련 기능 호출 시 런타임 오류 발생 가능.
- RFdiffusion이 torchaudio/torchvision을 직접 사용하지 않으면 무시 가능하나 확인 필요.
- **즉시 조치**: `conda run -n rfdiffusion python -c "import torchaudio"` 실행으로 import 오류 재현 여부 확인.

---

## 부록: Submodule 상태

```
 6400bf6d3ee7 tools/harness-adaptation/reference/harness (heads/main)
```
- 체크아웃 완료, `heads/main` 추적 중. 동기화 정상.
