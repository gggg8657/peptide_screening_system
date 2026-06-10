# pepMSND 로컬 설치 확인 (Layer 2)

일시: 2026-05-20  
근거: `docs/meet_log/2026-04-06_action_items/A02_A03_ensemble_system_design_2026-05-20.md` (researcher), 내부 문서에 명시된 GitHub URL

## 제한 사항 (검증 범위)

- **WebSearch / WebFetch**: 이 세션에서 도구 호출이 거부되어, GitHub의 **라이브 페이지는 열람하지 못함**. 공식 정보는 **로컬에 클론한 저장소의 `README.md` / `requirements.txt` / 소스 트리**로만 정리함.
- **conda base / 공유 env 변경 없음** (활성 env 조회·`conda run` 스모크만 수행).
- **대용량 GPU 스택(PyTorch 2.2 + DGL cu121 등) 전체 설치는 미실시** — 격리 venv에서 `pip install -r requirements.txt` 1차 시도 후 실패 지점에서 중단.

---

## 1. 본 프로젝트 내 흔적

### 1.1 `find … *pepmsnd*` (상위 일부, 실제 실행)

```text
./docs/environments/pepmsnd_pepadmet.md
./pipeline_local/scripts/predict_halflife_pepmsnd.py
./pipeline_local/scripts/__pycache__/predict_halflife_pepmsnd.cpython-311.pyc
./pipeline_local/scripts/__pycache__/predict_halflife_pepmsnd.cpython-313.pyc
./runs_local/pepmsnd_benchmark
./_workspace/release/p2-binding-pocket-pepmsnd-pepadmet-execution-2026-05-19.md
./_workspace/release/p2-pepmsnd-pepadmet-retry-2026-05-19.md
(.worktrees/… 내 동일 파일 다수 생략)
```

### 1.2 `pipeline_local/scripts/` 내 문자열 검색 결과

| 파일 | 역할 |
|------|------|
| `predict_halflife_pepmsnd.py` | **메인 wrapper** — PlifePred2 로컬 + PepMSND **웹** 시도 분기 (`--pepmsnd-web`). PepMSND **로컬 추론 엔진은 미연동**. |
| `composite_scorer.py` | `predict_halflife` import, 기본 `use_pepmsnd_web=False` |
| `pharmacology_guards.py` | `halflife_pepmsnd` / `external_tool.halflife_pepmsnd` 메타·면책 |

### 1.3 기존 wrapper 동작 스모크 (실제 출력)

실행:

```bash
conda run -n peptools python pipeline_local/scripts/predict_halflife_pepmsnd.py \
  --sequence AGCKNFFWKTFTSC --seq-id SST14 --output /tmp/pepmsnd_wrap_test.json
```

표준 출력:

```text
저장: /tmp/pepmsnd_wrap_test.json
```

`/tmp/pepmsnd_wrap_test.json` 요지: `plifepred2`만 `success`; `pepmsnd_web`는 `null` (웹 미사용 또는 실패 분기와 일치하는 구조).

### 1.4 conda 환경 이름

`conda env list` 기준 **`pepmsnd` 명칭 전용 env는 없음**. 관련 후보:

- `peptools` — PlifePred2·wrapper 실행용 (문서·스크립트 기준)
- `pepadmet`, `bio-tools` — 다른 torch 스택 보유 가능성 (별도 평가)

---

## 2. 공식 정보 (로컬 클론 기준)

### 2.1 GitHub URL

- **`https://github.com/hmenghu/PepMSND.git`** (`git clone` 후 `git remote -v`, HEAD `c0fa695 Add files via upload`)

내부 설계 노트와 동일: `docs/meet_log/2026-04-06_action_items/A02_A03_ensemble_system_design_2026-05-20.md`에 `github.com/hmenghu/PepMSND` 명시됨.

### 2.2 환경 요건 (`requirements.txt` 일부 특성)

실행에 직결되는 패키지 예:

- **`torch==2.2.0`**
- **`dgl==2.4.0+cu121`**, **`dgllife==0.3.2`**
- **`torch_geometric==2.5.3`**, **`torch_scatter` / `torch_cluster`** (메타데이터 상 `+pt22cu121` 빌드)
- **`rdkit==2024.3.6`**, **`MDAnalysis`**, **`numpy==1.26.4`**, 등 대규모 의존 다수

→ **CUDA 12.1 계열 DGL/Torch 바이너리 + PyG 확장 전제**(대용량 다운로드 예상).

### 2.3 라이선스

`README.md` 문구:

```text
This project is governed by the terms of the MIT License … review the LICENSE document
```

하지만 클론 루트에 **`LICENSE` 파일이 존재하지 않음** (`ls LICENSE` 실패). **법무/배포 판단은 파일 미포함 상태로 불명확** — upstream에 LICENSE 추가 여부를 별도 확인할 것.

### 2.4 가중치·추론 스크립트 공개 여부

- 레포 내 **`*.pth` / `*.pt` / `.ckpt` 검색 결과 없음** (`find … -iname '*.pt*'` 공백).
- `README.md`의 “Using PepMSND model”은 **온라인 서비스 링크** (`http://model.highslab.com/static/service`) 안내일 뿐, **추론 전용 단일 진입점·사전학습 체크포인트 지시 없음**.
- `Models/model.py`는 **`for epoch in range(1, 201):`** 형태로 **학습 루프**가 중심 — **즉시 sample inference** 용 CLI는 문서화되어 있지 않음.

추가로, `Models/model.py` 첫 줄 import:

```python
from Transform import TransformerModel
```

실제 파일명은 **`Transformer.py`** 로 보임 → **대소문자 구분 파일시스템(Linux)에서 import 오류 가능성** (코드 그대로 실행 시 리스크).

### 2.5 README 설치 단계 불완전

README는 `./replace.sh` 실행을 명시하지만, **클론본에 `replace.sh` 없음** — 따라서 공식 안내대로 재현 불가 구간 존재.

---

## 3. 환경 적용 평가

### 3.1 기존 conda env 호환 (실측 로그 발췌)

- **`peptools`**: `pip show torch` → **설치되어 있지 않음** (패키지 없음). PlifePred2 경량 스택만 가정 시 PepMSND와 **비호환**.
- **`pepadmet`**: `torch==1.13.1+cu117` 존재 (요구 `torch==2.2.0`과 **메이저 불일치**).
- **`bio-tools`**: `torch==2.10.0` 수준 존재; PepMSND 핀 버전 및 **dgl/pyg 빌드**와 정합성 **미검증**이며 바로 재사용 권하지 않음.

### 3.2 신규 env 필요 여부

- **예 (yes)** — **`python=3.10~3.11` + Torch 2.2 + CUDA 12.1용 DGL + PyG 확장**을 목표로 하는 **프로젝트 전용 conda prefix 또는 독립 venv** 구성이 합리적.  
  기존 `pepadmet`(torch 1.13) / `peptools`(torch 없음)에 끼워 넣기 어렵다.

### 3.3 H100 `sm_90` 호환성 (실측만)

```text
nvidia-smi --query-gpu=name,compute_cap --format=csv
name, compute_cap
NVIDIA H100 NVL, 9.0
…
```

- 하드웨어는 **compute capability 9.0** 확인.
- 논리적 호환 여부는 **설치되는 PyTorch 빌드의 CUDA 버전 및 sm 아키텍처 포함 여부**에 달림.  
  Torch 2.2 + 최신 NVIDIA 스택에서는 일반적으로 H100 지원 범위에 들어오나, **`dgl==2.4.0+cu121` 고정**이 해당 머신의 CUDA 드라이버/`nvidia-smi`에 맞는지는 **설치 후 `python -c "import torch; print(torch.cuda.get_device_capability())"`** 로 재확인 필요.

---

## 4. 설치 시도 결과

### 4.1 clone

- **성공**: 경로 `_workspace/pepmsnd_local/PepMSND/`

### 4.2 env 생성 (`python3 -m venv .venv_try` 후 `pip install -r requirements.txt`)

- 실패 단계 로그 (끝부분 실제 출력):

```text
ERROR: Could not find a version that satisfies the requirement dgl==2.4.0+cu121 (from versions: 0.1.0, 0.1.2, 0.1.3)
ERROR: No matching distribution found for dgl==2.4.0+cu121
```

원인 요약:

- 기본 PyPI 인덱스만으로 **`dgl==2.4.0+cu121` 휠을 해석하지 못함** — DGL은 보통 **`https://data.dgl.ai/wheels/cu121/repo.html`** 등 **추가 `-f`(find-links)** 필요.
- 사용된 인터프리터는 conda base의 **`Python 3.13.12`** 로 보이며(로그에 `cp313` 휠 선택 흔적), **requirements에 핀된 과학 스택 전체와도 ABI 정합 불확실**.

### 4.3 sample run (레포 제공 추론 예시)

- **미실행** — 의존성 설치 실패 + 학습 코드만 존재 + 사전학습 가중치 미발견.

---

## 5. wrapper 작성 가이드 (Codex 위임용 초안)

**목표**: `pipeline_local/scripts/predict_halflife_pepmsnd.py`에 **선택 경로로 로컬 PepMSND 추론** 추가, 또는 형제 스크립트 `predict_pepmsnd_local.py` 신설 후 composite에서 옵션 연결.

| 항목 | 내용 |
|------|------|
| **입력 형식** | 논문/레포 특성상 **그래프·3D 피처가 필요**(SE3 등). 단일 FASTA만으로 재현 불가 가능성 높음. 공개 레포에는 **학습 파이프의 CSV·PDB 디렉토리**(예 `Dataset/`, `Peptide structure Dataset/`)가 있음 — wrapper는 우선 레포 내 **전처리 `Models/pretreatment.py` 출력 스키마** 역설계 필요. |
| **출력 형식** | 이진 분류·확률 등 (웹 버전 및 논문과 정합 검증 필요). 현재 도메인 가드는 **`binary_classification`** 전제 문구 있음 (`predict_halflife_pepmsnd.py` 및 `pharmacology_guards.py`). |
| **호출 명령어 (가정)** | 별도 conda env 활성 후, 예:  
  `conda run -n pepmsnd-local python Models/<inference_stub>.py --input … --checkpoint …`  
  단, **upstream에 inference stub·체크포인트가 추가되지 않으면 불가능**. |
| **`pipeline_local` 통합 위치** | `predict_halflife_pepmsnd.predict_halflife(...)` 또는 composite 호출 분기 환경 변수 `USE_PEPMSND_LOCAL=1`. **가중치 파일 경로**는 실행 파드별로 `PIPELINE_LOCAL_PEPMSND_CKPT` 같은 SSOT 필요. |

**Codex 패킷에 포함할 검증 과제**:

1. upstream 이슈/레포 최신 확인: **`LICENSE` 누락 여부**, **체크포인트 공개**, **`replace.sh` 존재**, **`Models/model.py` import 경로 수정** PR 가능성.  
2. **D-AA/cyclic 입력**: 논문·데이터 특성 재확인 — 웹 미지원이었던 과거 기록(`docs/environments/pepmsnd_pepadmet.md`)과 Layer 2 권고(D-AA 주력)의 **정합성 재검토 필수**(입력 채널이 SMILES+구조 PDB인지 확인).

---

## 6. 잔여 과제 및 권고

1. **대용량 설치**(Torch+dgl cu121 wheel + PyG): 사용자 승인 후, **`conda create -p <repo>/…/ conda_pepmsnd python=3.11`** 형태로 **prefix 격리** 권장. 설치 명령 예시(참고용, 미실행):
   ```bash
   pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cu121
   pip install dgl -f https://data.dgl.ai/wheels/cu121/repo.html
   # 이후 PyG 확장 버전 매칭
   ```
2. **`docs/environments/pepmsnd_pepadmet.md` 갱신 백로그**: “GitHub/PyPI 없음” 진술은 **현재 레포 존재로 outdated** — 로컬 추론은 여전히 **가중치 미공개**로 막혀 있다는 표현으로 정정하는 것이 정확함.  
3. **Layer 2 “D-AA 주력”** 과 본 레포 가능 범위: 데이터에 cyclic 사례가 있다는 문헌고지와 별개로, **실제 추론 경로 입력 제한**은 코드 전처리·체크포인트 로딩 검증 후에만 단정 가능.

---

## cursor-agent CLI용 한 줄 요약 (붙여넣기)

```text
[EOD-pepMSND-check 2026-05-20] 클론 https://github.com/hmenghu/PepMSND.git 성공(_workspace/pepmsnd_local). README는 MIT·torch2.2+dgl cu121 의존. LICENSE 파일 누락·replace.sh 없음·사전학습 가중치 없음·model.py 학습 코드 위주 격리 venv에서 pip설치 실패(dgl cu121 인덱스 미지정+bad python 버전 가능). 프로젝트에는 predict_halflife_pepmsnd.py(웹+P3 PlifePred)만 있음 신규 prefix env 필요. 상세:_workspace/pepmsnd_local/installation_check_2026-05-20.md
```

**호출 예 (로그 목적)**

```bash
./scripts/agent-wrapper.sh cursor-agent "위 EOD-pepMSND-check 한 줄 로그 확장: Layer2 후속 conda prefix 설치 검토만 backlog"
```
