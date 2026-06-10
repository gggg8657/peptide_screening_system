# pepMSND 격리 설치 시도
일시: 2026-05-20

## 0. 사전 이슈: 디스크·공유 메모리

### 0.1 `conda` 초기 실패 (`NoSpaceLeftError`)
처음 `conda create` / `conda info` 모두 아래로 종료됨.

```
NoSpaceLeftError: No space left on devices.
```

**원인**: `/dev/shm`이 **100% (64M / 64M)** 사용 중이었고(NCCL 임시 파일 `nccl-*` 등 다수), 사용자 소유 `nccl-*` 임시 파일 삭제 후 `/dev/shm` 여유가 생기며 `conda`가 정상 동작함.

- 삭제 전: `df -h /dev/shm` → 100%
- 삭제 후: `df -h /dev/shm` → 약 **1%** 사용

> 주의: 동일 노드에서 GPU/분산 학습이 돌면 `/dev/shm`이 다시 가득 찰 수 있음. 반복 시 **해당 작업과 충돌 여부**를 확인한 뒤 정리하는 것이 안전함.

### 0.2 홈 파티션 여유
작업 전후 (참고):

- 시작 시: `df -h /home/dongjukim` → **약 226G avail**, Use% 97%
- 설치 후: `df -h /home/dongjukim` → **약 211G avail**, Use% 97%

---

## 1. 격리 prefix 생성

- **경로**: `_workspace/pepmsnd_local/.conda_env`
- **명령 (실제 실행)**:

```bash
conda create -y -p /home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/pepmsnd_local/.conda_env python=3.11
```

- **Python 버전** (conda 출력 기준): `python-3.11.15`
- **시스템 base env 변경**: 없음 (`-p` 로컬 prefix만 사용)

추가로, `requirements` 중 `gmpy2` 빌드가 `gmp.h`를 요구하여 **격리 prefix에만** GMP 스택 설치:

```bash
conda install -y -p .../.conda_env -c conda-forge gmp mpfr mpc
```

`gmpy2` 빌드 시 `CPATH`/`LIBRARY_PATH`에 해당 prefix의 `include`/`lib`를 넘겨 빌드 성공.

---

## 2. 의존성 설치 결과

### 2.1 PyTorch (CUDA 12.1 wheel)

```bash
conda run -p .../.conda_env pip install \
  torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 \
  --index-url https://download.pytorch.org/whl/cu121
```

- **결과**: 성공 (다운로드·설치 로그 정상 종료, exit 0)

### 2.2 DGL — 요청 버전 **실패**, 대체 버전 **성공**

요청:

```bash
pip install dgl==2.4.0+cu121 -f https://data.dgl.ai/wheels/cu121/repo.html
```

**실제 stderr (요약)**:

```
ERROR: Could not find a version that satisfies the requirement dgl==2.4.0+cu121 (from versions: ... 2.1.0+cu121)
ERROR: No matching distribution found for dgl==2.4.0+cu121
```

`cu121/repo.html` 및 `curl`로 확인 시, **linux / cp311 / manylinux** 용 휠은 `dgl-2.1.0+cu121`까지 확인됨(상위 2.4.x 휠 없음).

**대체 설치 (성공)**:

```bash
conda run -p .../.conda_env pip install dgl==2.1.0+cu121 \
  -f https://data.dgl.ai/wheels/cu121/repo.html
```

- **설치된 DGL**: `dgl 2.1.0+cu121`

### 2.3 PyG

```bash
conda run -p .../.conda_env pip install torch-geometric
conda run -p .../.conda_env pip install pyg-lib torch-scatter torch-sparse torch-cluster \
  -f https://data.pyg.org/whl/torch-2.2.0+cu121.html
```

- **결과**: 성공  
  - 예: `torch-geometric` → `2.7.0`, `torch_scatter` → `2.1.2+pt22cu121` 등 (pip 로그 기준)

### 2.4 `requirements.txt` 전체 (문서대로) — **실패**

```bash
pip install -r PepMSND/requirements.txt
```

**stderr (핵심)**:

```
ERROR: Could not find a version that satisfies the requirement dgl==2.4.0+cu121
ERROR: No matching distribution found for dgl==2.4.0+cu121
```

### 2.5 필터 설치 (torch/dgl/PyG/mkl_fft/mkl_random 등 제외 + α)

- `dgl`, `torch*`, `triton`, `torch_geometric`, `torch_scatter/sparse/cluster`, `mkl_*` 라인 제거한 목록 + `mkl-service==2.4.0` → **`2.4.1`로 치환** (2.4.0은 PyPI에 없음 → 에러)
- `CPATH`/`LIBRARY_PATH`에 prefix 내 GMP 경로 설정 후 설치

**결과**: exit 0, 대량 패키지 설치 완료 (로그에 “Successfully installed …” 확인)

이후 **PyTorch를 다시 cu121 스택으로 고정**했고, `numpy`는 `scipy`/`MDAnalysis` 호환을 위해 **`numpy==1.26.4`** 로 되돌림.

#### DGL ↔ torchdata 호환 메모
대량 설치 후 `dgl` import 시 초기에는 `torchdata.datapipes` 미존재(패키지 구조 변경) 및 `torchdata 0.11` 문제가 있었음.  
최종적으로 **`torchdata==0.7.1`을 `--no-deps`로** 고정해 torch를 끌어올리지 않도록 하고, PyTorch는 위의 **`2.2.0+cu121`**로 유지.

#### Graphbolt `libnvrtc.so.12`
`import dgl` 시 `OSError: libnvrtc.so.12: cannot open shared object file` 발생.  
prefix 내부 경로 `site-packages/nvidia/cuda_nvrtc/lib` 등을 **`LD_LIBRARY_PATH`에 추가**하면 import 성공.

---

## 3. import 검증 (실제 출력)

다음은 **Graphbolt 로딩을 위해 `LD_LIBRARY_PATH` 설정**을 포함한 검증.

**명령env 요약**:

```bash
LP="${CONDA_PREFIX}/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib:\
${CONDA_PREFIX}/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:\
${CONDA_PREFIX}/lib/python3.11/site-packages/nvidia/cudnn/lib:\
${CONDA_PREFIX}/lib"
conda run -p .../.conda_env env LD_LIBRARY_PATH="$LP" python -c "..."
```

**출력**:

```
torch 2.2.0+cu121
True
(9, 0)
```

```
dgl 2.1.0+cu121
```

```
pyg 2.7.0
```

- **H100 sm_90**: `torch.cuda.get_device_capability()` → **`(9, 0)`**
- **CUDA 사용 가능**: `torch.cuda.is_available()` → **`True`**

**운영 권고**: `conda run`/`python` 실행 전에 위 `LD_LIBRARY_PATH`를 셸 래퍼나 `activation hook`으로 고정하는 편이 안전함.

---

## 4. 체크포인트 검색

### 4.1 레포 내 (`PepMSND`)

```bash
find PepMSND -type f \( -name '*.pth' -o -name '*.pt' -o -name '*.ckpt' \)
```

- **결과**: (출력 없음) — **체크포인트 파일 없음**

`Models/model.py`에는 학습 후 저장 코드가 **주석 처리**되어 있음 (`torch.save` 줄들 주석).

### 4.2 README / 외부 링크

`README.md`에 **Zenodo / Hugging Face 등 모델 weight URL은 없음**.  
대신 다음이 기술됨.

- 데이터 브라우저: `http://model.highslab.com/static/Database.html`
- 웹 서비스: `http://model.highslab.com/static/service`

### 4.3 링크 접속 시도 (HTTP)

```bash
curl -sI --max-time 15 http://model.highslab.com/static/service
curl -sI --max-time 15 https://model.highslab.com/static/service
```

- `http`: **exit code 7** (연결 실패)
- `https`: **exit code 28** (타임아웃, 응답 헤더 없음)

→ 이 환경에서는 **README에 적힌 온라인 서비스 URL에 대한 실제 데이터 흐름 검증 불가**로 기록.

---

## 5. 디스크 사용량

```bash
du -sh _workspace/pepmsnd_local/.conda_env
```

- **`.conda_env`**: **약 11G**

---

## 6. 결론 + 다음 단계

### 6.1 설치 상태
- **격리 conda prefix + PyTorch cu121 + DGL CUDA wheel + PyG(cu121)**: **가능**, import 검증 완료 (위 `LD_LIBRARY_PATH` 필요).
- **원본 `requirements.txt` 고정(특히 `dgl==2.4.0+cu121`)**: **공개 휠 기준으로는 불가능** (해당 버전 휠 미존재).
- **문서 그대로의 단일 커맨드로 전체 동일 버전 재현**: **불가** — 필터 설치·핀 완화·경로 수정 필요.

### 6.2 추론 가능성
- 레포에 **학습된 weight 없음** + 온라인 서비스 URL **이 환경에서 접속 실패** → **즉시 로컬 추론 재현은 불가에 가깝고**, 학습 또는 접근 가능한 배포 채널 확보가 필요.

### 6.3 다음 단계 제안 (사용자 옵션 정렬)

| 옵션 | 메모 |
|------|------|
| **(A) 자체 학습** | `README`의 `python ./Models/model.py` 및 `Dataset` 경로 확인 후 학습 파이프라인 가동. H100 4장 기준 시간·ROI는 데이터·epoch·배치에 따름 — 별도 벤치마크 필요. |
| **(B) 웹 wrapper** | `model.highslab.com` — 이번 `curl` 기준으로는 **연결/타임아웃**, 방화벽·DNS·서비스 가용성 확인 후 재시도. |
| **(C) Layer 2 대체 도구** | D-AA/안정성 측면에서 동등 목적의 다른 스택 검토(프로젝트 L2 앙상블 요구와 정합성 점검). |

### 6.4 재현 시 필수 shell 스니펫 (요약)

```bash
export ENV_ROOT="/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/pepmsnd_local/.conda_env"
export LD_LIBRARY_PATH="${ENV_ROOT}/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib:${ENV_ROOT}/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:${ENV_ROOT}/lib/python3.11/site-packages/nvidia/cudnn/lib:${ENV_ROOT}/lib:${LD_LIBRARY_PATH}"
conda run -p "$ENV_ROOT" python -c "import torch, dgl, torch_geometric; print(torch.__version__, dgl.__version__)"
```

---

## 부록: 원본 명령 로그 파일 위치 (참고)

- 필터 `requirements` 1차 실패 (`gmpy2`): 에이전트 로그 `…/agent-tools/6bf7b7bd-21cc-4377-bc50-d65ee897f76e.txt`
- 필터 `requirements` 성공: `…/agent-tools/0aabb3ae-f7f9-4c66-959b-76071615f756.txt`
