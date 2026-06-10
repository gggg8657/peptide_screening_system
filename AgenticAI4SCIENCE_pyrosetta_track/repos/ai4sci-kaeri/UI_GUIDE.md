# PyRosetta Flow Web UI 운영 가이드

> **AI-Scientist: SSTR2 Peptide Binder Design Pipeline**
> Agentic Multi-Step Optimization Monitor v0.3
>
> **최종 업데이트: 2026-03-04**

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [사전 요구사항](#2-사전-요구사항)
3. [설치 방법](#3-설치-방법)
4. [실행 방법](#4-실행-방법)
5. [UI 사용법](#5-ui-사용법)
6. [신규 기능 가이드](#6-신규-기능-가이드)
7. [API 엔드포인트 설명](#7-api-엔드포인트-설명)
8. [CLI 직접 실행법](#8-cli-직접-실행법)
9. [결과 파일 구조](#9-결과-파일-구조)
10. [트러블슈팅](#10-트러블슈팅)

---

## 1. 시스템 개요

PyRosetta Flow Web UI는 SSTR2(Somatostatin Receptor Type 2) 펩타이드 바인더 설계를 위한 에이전트 기반 자동화 파이프라인의 실시간 모니터링 대시보드이다. LLM 에이전트(Planner, Critic, Reporter)와 코드 기반 에이전트(QC Ranker)가 협업하여 반복적 변이-도킹 최적화를 수행하며, 사용자는 웹 브라우저를 통해 전 과정을 실시간으로 관찰하고 제어할 수 있다.

### 아키텍처 다이어그램

```
+-------------------------------------------------------+
|                  사용자 브라우저                          |
|  http://localhost:5173                                 |
|  +---------------------------------------------------+|
|  |            React Frontend (Vite)                   ||
|  |  App.tsx -> ExperimentControl (모드/파라미터 선택)    ||
|  |             PipelineStatus (7-column 진행 바)       ||
|  |             AgentFlowDiagram (에이전트 흐름도)        ||
|  |             AgentMonitor (에이전트 상태 모니터)       ||
|  |             MoleculeViewer (Mol* 3D 뷰어)           ||
|  |             CandidateTable (후보 테이블 + 선택)      ||
|  |             ValidationPanel (통합 검증 패널)         ||
|  |             PharmacologyPanel (약리학 속성 패널)      ||
|  |             QCGateChart / ConvergenceGraph          ||
|  |             LoopTimeline / VisualizationPanel       ||
|  +--------|------------------------------------------+||
|           | GET /api/status  (2초 폴링)                 |
|           | POST /api/experiment/run                   |
|           | POST /api/validate/unified                 |
|           | POST /api/pharmacology/batch               |
|           | GET  /api/structures/{path}                |
+-----------|-------------------------------------------+
            | Vite proxy (/api -> :8787)
            v
+-------------------------------------------------------+
|          Backend API Server (Python)                   |
|          http://localhost:8787                         |
|  +---------------------------------------------------+|
|  | api_server.py                                      ||
|  |   GET  /api/health              -> 헬스체크          ||
|  |   GET  /api/status              -> 상태 JSON 반환    ||
|  |   POST /api/experiment/run      -> 파이프라인 시작    ||
|  |   POST /api/experiment/stop     -> 파이프라인 중지    ||
|  |   GET  /api/structures/{path}   -> PDB 파일 서빙     ||
|  |   POST /api/validate/unified    -> 통합 검증 실행     ||
|  |   GET  /api/validation/criteria -> 검증 기준 목록     ||
|  |   POST /api/pharmacology/batch  -> 약리학 계산        ||
|  |   GET  /api/admet/{seq}         -> ADMET 분석        ||
|  |   GET  /api/analysis/*          -> 통계 분석 API      ||
|  +--------|---------|--------------------------------+||
|           |         |                                  |
|     읽기  |   pharmacology.py / unified_validation.py   |
|           |   admet.py / analysis.py / sar_analysis.py  |
|           v         v                                  |
+-------------------------------------------------------+
|  /tmp/pipeline_local_status.json   (상태 공유 파일)          |
+-------------------------------------------------------+
            ^
            | 쓰기 (StatusEmitter.flush())
            |
+-------------------------------------------------------+
|           Pipeline Runner (subprocess)                 |
|  +---------------------------------------------------+|
|  |  [PyRosetta Flow 모드]                              ||
|  |    scripts/run_pyrosetta_flow.py                   ||
|  |      -> pyrosetta_flow/runner.py                   ||
|  |         -> FlexPepDock (conda run -n bio-tools)    ||
|  |         -> Planner Agent (Qwen 3 8B via Ollama)    ||
|  |         -> QC Ranker Agent (Code, 규칙 기반)        ||
|  |         -> Diversity Manager (FoldMason lDDT)      ||
|  |         -> Critic Agent (Qwen 3 8B)                ||
|  |         -> Reporter Agent (Qwen 3 8B)              ||
|  |                                                    ||
|  |  [NIM API 모드]                                     ||
|  |    run_pipeline_live.py                            ||
|  |      -> ESMFold / DiffDock / MolMIM (NVIDIA NIM)   ||
|  +---------------------------------------------------+||
+-------------------------------------------------------+
```

### 데이터 흐름 요약

1. 사용자가 Web UI에서 파라미터를 설정하고 "Start Run" 버튼을 클릭한다.
2. Frontend가 `POST /api/run/start`로 요청을 보내 Backend에서 파이프라인 프로세스를 시작한다.
3. 파이프라인 프로세스(`run_pyrosetta_flow.py` 또는 `run_pipeline_live.py`)가 `StatusEmitter`를 통해 `/tmp/pipeline_local_status.json` 파일에 진행 상태를 기록한다.
4. Frontend는 2초 간격으로 `GET /api/status`를 폴링하여 상태를 읽고 대시보드를 갱신한다.
5. API Server는 상태 파일을 200ms 캐시와 함께 읽어 반환한다.

---

## 2. 사전 요구사항

### 필수 소프트웨어

| 구분 | 요구사항 | 비고 |
|------|---------|------|
| Python | 3.11 이상 | 파이프라인 백엔드 실행 |
| Node.js | 18 이상 (LTS 권장) | React 프론트엔드 빌드 |
| npm | 9 이상 | Node.js와 함께 설치됨 |
| conda | Miniconda 또는 Anaconda | PyRosetta conda 환경 관리 |
| Ollama | 최신 버전 | 로컬 LLM 서빙 (gemma3:1b) |

### conda 환경: `bio-tools`

PyRosetta가 설치된 conda 환경이 필요하다. 이 환경은 파이프라인 내부에서 `conda run -n bio-tools python ...` 형태로 호출된다.

```bash
# bio-tools 환경 생성 (PyRosetta 라이선스 필요)
conda create -n bio-tools python=3.11 -y
conda activate bio-tools
# PyRosetta 설치 (라이선스에 따라 채널이 다를 수 있음)
conda install -c https://yourpyrosetta.channel pyrosetta -y
```

### Python 패키지 (메인 환경)

```bash
pip install pyyaml
```

### LLM 서버 (Ollama)

파이프라인의 Planner, Critic, Reporter 에이전트가 LLM을 사용한다. 기본 설정은 Ollama + `qwen3:8b` 모델이다 (`gemma3:1b`로 폴백 가능).

```
- Ollama 기본 URL: http://localhost:11434
- vLLM 기본 URL:   http://localhost:8000
- LLM Provider "none" 선택 시: LLM 없이 규칙 기반 모드로 동작
```

---

## 3. 설치 방법

### 3.1 Backend 설정

```bash
# 프로젝트 루트로 이동
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri

# Python 의존성 설치 (메인 환경)
pip install pyyaml
```

Backend는 Python 표준 라이브러리의 `http.server`를 사용하므로 별도의 프레임워크 설치가 필요 없다.

### 3.2 Frontend 설정

```bash
cd frontend

# 의존성 설치
npm install
```

주요 프론트엔드 의존성:
- React 19, React DOM 19
- Vite 7 (dev server + 빌드)
- TailwindCSS 4
- Recharts 3 (차트 라이브러리)
- Lucide React (아이콘)

### 3.3 Ollama + gemma3:1b 설정

```bash
# 1. Ollama 설치 (Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Ollama 서버 시작
ollama serve

# 3. gemma3:1b 모델 다운로드 (별도 터미널)
ollama pull gemma3:1b

# 4. 모델 동작 확인
ollama run gemma3:1b "Hello, are you ready?"
```

Ollama가 정상 구동되면 `http://localhost:11434`에서 API가 응답한다.

> **참고:** LLM 없이 실행하려면 Web UI에서 LLM Provider를 `none`으로 설정하면 된다. 이 경우 규칙 기반 폴백 로직으로 동작한다.

### 3.4 pipeline_config.yaml 확인

파이프라인 설정 파일 경로: `AG_src/config/pipeline_config.yaml`

LLM 관련 핵심 설정:

```yaml
llm:
  provider: "ollama"                  # none | ollama | vllm
  model: "gemma3:1b"                  # Ollama 모델명
  base_url: "http://localhost:11434"  # Ollama 기본 URL
  timeout: 120                        # 요청 타임아웃 (초)
  temperature: 0.3                    # 생성 온도
  max_tokens: 4096                    # 최대 생성 토큰 수
```

---

## 4. 실행 방법

### 4.1 Backend API Server 시작

```bash
# 프로젝트 루트에서 실행
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri

python backend/api_server.py
```

정상 시작 시 출력:

```
[API Server] Starting on http://localhost:8787
[API Server] Status file: /tmp/pipeline_local_status.json
[API Server] Endpoints:
  GET  /api/status  - Pipeline status (frontend polls this)
  POST /api/status  - Update status (pipeline pushes here)
  GET  /api/run/status  - Pipeline process status
  POST /api/run/start  - Start pipeline run
  POST /api/run/stop   - Stop current run
  GET  /api/health  - Health check
```

환경변수로 포트 및 상태 파일 경로를 변경할 수 있다:

```bash
API_PORT=9090 PIPELINE_STATUS_FILE=/tmp/custom_status.json python backend/api_server.py
```

### 4.2 Frontend Dev Server 시작

```bash
# 별도 터미널에서 실행
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend

npm run dev
```

정상 시작 시 출력:

```
  VITE v7.x.x  ready in xxx ms

  ->  Local:   http://localhost:5173/
  ->  Network: http://xxx.xxx.xxx.xxx:5173/
```

Vite dev server는 `/api` 경로 요청을 자동으로 `http://localhost:8787`로 프록시한다 (`vite.config.ts` 설정).

### 4.3 Web UI 접속

브라우저에서 다음 주소로 접속한다:

```
http://localhost:5173
```

파이프라인이 실행 중이 아닐 때는 우측 상단에 **"Mock"** 뱃지가 표시되며 목업 데이터로 대시보드 레이아웃을 확인할 수 있다. 파이프라인이 실행되면 **"Live"** 뱃지(녹색 펄스 애니메이션 포함)로 전환된다.

---

## 5. UI 사용법

### 5.1 전체 화면 구성

Web UI는 상단에서 하단 순서로 다음과 같이 구성되어 있다:

```
+------------------------------------------------------------------+
| Header: 타이틀 / LLM 모델명 / API 상태 뱃지 / Live/Mock 상태       |
+------------------------------------------------------------------+
| Experiment Control: 모드 선택(Full/PyRosetta) + 파라미터 + Start    |
+------------------------------------------------------------------+
| Pipeline Status: 7-column 파이프라인 진행 상태 (서브스텝 포함)       |
+------------------------------------------------------------------+
| Agent Flow Diagram: 에이전트 간 데이터 흐름 시각화                   |
+------------------------------------------------------------------+
| Loop Timeline: 반복별 이벤트 타임라인 (PyRosetta 모드 전용)          |
+------------------------------------------------------------------+
| 3D Molecule Viewer (Mol*): 후보별 PDB 구조 인터랙티브 3D 렌더링     |
+------------------------------------------------------------------+
| Agent Monitor  |  Candidate Table (선택 체크박스 포함)               |
+------------------------------------------------------------------+
| Validation Panel: 프리셋/커스텀 기준 선택 → 통합 검증 → 상세 보기    |
+------------------------------------------------------------------+
| Pharmacology Panel: 13가지 약리학적 속성 계산 결과                   |
+------------------------------------------------------------------+
| QC Gate Chart  |  Convergence Graph                                 |
+------------------------------------------------------------------+
| Risk Matrix                                                        |
+------------------------------------------------------------------+
| Footer: 버전 정보 / Run ID                                         |
+------------------------------------------------------------------+
```

### 5.2 Run Control Panel (실행 제어 패널)

대시보드 상단의 시안색 테두리 영역이 파이프라인 실행 제어 패널이다.

#### 5.2.1 Pipeline Mode 선택

드롭다운 메뉴에서 파이프라인 모드를 선택한다:

| 모드 | 설명 | 필수 요건 |
|------|------|-----------|
| **PyRosetta Flow** | mutate -> FlexPepDock -> QC -> Critic -> Report 루프. NVIDIA NIM API 불필요. | conda `bio-tools` 환경에 PyRosetta 설치 |
| **NIM API Pipeline** | ESMFold + DiffDock + PyRosetta 전체 파이프라인. | `NVIDIA_NIM_API_KEY` 환경변수 필요 |

PyRosetta Flow 모드 선택 시 추가 파라미터(Candidates/Iter, Objective, Seed)가 표시된다.

#### 5.2.2 파라미터 설정

**공통 파라미터:**

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| Iterations (N) | 5 | 에이전트 루프 반복 횟수 (최소 1) |
| LLM Provider | ollama | LLM 백엔드 선택: `ollama`, `vllm`, `none` |
| LLM Model | gemma3:1b | 사용할 LLM 모델명 |

**PyRosetta Flow 전용 파라미터:**

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| Candidates/Iter | 8 | 반복당 생성할 변이 후보 수 (1~50) |
| Objective | auto | 목적 함수 모드: `auto`, `ddG only`, `ddG + constraints` |
| Seed | 1000 | 난수 시드 기본값 (재현성 보장) |

**Objective 모드 상세:**

- **auto**: 시스템이 반복 단계에 따라 자동으로 최적 모드를 선택한다.
- **ddG only**: ddG(결합 자유에너지 변화) 점수만으로 후보를 평가한다. pLDDT/도킹 게이트를 비활성화한다.
- **ddG + constraints**: ddG에 추가로 clash count, constraint violation 등 제약 조건을 함께 평가한다.

#### 5.2.3 Start/Stop 버튼

- **Start Run** (녹색 버튼): 설정된 파라미터로 파이프라인을 시작한다. 이미 실행 중인 프로세스가 있으면 비활성화된다.
- **Stop** (빨간색 버튼): 현재 실행 중인 파이프라인을 중지한다. 실행 중이 아니면 비활성화된다.

버튼 아래에는 현재 프로세스 상태가 표시된다:
- `Process: idle` - 대기 중
- `Process: running (pid=12345)` - 실행 중 (PID 표시)

시작/중지 결과 메시지도 패널 하단에 표시된다 (예: `Started PID 12345`, `Run stopped`).

### 5.3 실시간 모니터링 패널

#### 5.3.1 Pipeline Status (파이프라인 상태)

파이프라인의 각 단계를 수평 진행 바 형태로 보여준다.

- PyRosetta Flow 모드에서는 `Step06 (PyRosetta)` 단계가 핵심이며, 내부적으로 다음 서브스텝이 표시된다:
  - **Prepare** - 기준 구조 준비
  - **Mutate** - 펩타이드 변이체 생성
  - **Refine** - FlexPepDock 정밀화
  - **Score** - ddG/score/clash 메트릭 집계
  - **QC** - 품질 게이트 적용 및 순위 매기기

- 각 단계의 상태 색상:
  - 회색: `pending` (대기)
  - 파란색(애니메이션): `running` (실행 중)
  - 녹색: `completed` (완료)
  - 빨간색: `failed` (실패)

- 현재 반복(iteration) 번호와 전체 반복 횟수가 `Iteration 2 / 5` 형태로 표시된다.

#### 5.3.2 Agent Monitor (에이전트 모니터)

왼쪽 사이드바에 6개 에이전트의 실시간 상태가 표시된다:

| 에이전트 | 유형 | 모델/도구 | 역할 |
|---------|------|----------|------|
| **Planner** | LLM | Qwen 3 8B (Ollama) | 각 반복의 가설 및 전략 JSON 생성 |
| **Builder** | Code | NIM API + PyRosetta | 도구 레지스트리에서 변이·도킹·스코어링 실행 |
| **QC & Ranker** | Code | 다중 게이트 점수 필터 | 후보 품질 검증 및 가중 순위 매기기 |
| **DiversityMgr** | Code | FoldMason lDDT 클러스터링 | 후보 다양성 관리 (서열 동일성 폴백) |
| **Critic** | LLM | Qwen 3 8B | 실패 분석 + 파라미터 변경 제안 |
| **Reporter** | LLM | Qwen 3 8B + PyMOL | 결과 보고서(rank_table.csv, summary.md, .pml) 작성 |

각 에이전트 카드에는 다음이 표시된다:
- 상태 표시등 (idle/active/error)
- 마지막 메시지
- 처리한 작업(task) 수
- 리포트 내용 (있는 경우)

#### 5.3.3 Candidate Table (후보 테이블)

`CandidateTable.tsx` (약 610줄)는 커스텀 훅으로 관심사를 분리한 구조이다:

| 훅 | 파일 | 역할 |
|----|------|------|
| `useSelection` | `hooks/useSelection.ts` | 체크박스 선택 상태 관리 (전체 선택 / 개별 토글) |
| `useCandidateSort` | `hooks/useCandidateSort.ts` | 컬럼별 정렬 + 필터 로직 |
| `useAdmetBatch` | `hooks/useAdmetBatch.ts` | ADMET 일괄 계산 (후보 변경 시 자동 호출) |
| `useValidation` | `hooks/useValidation.ts` | 검증 워크플로우 (선택된 후보 → 통합 검증) |

현재 반복에서 생성된 모든 변이 후보의 상세 정보를 테이블로 보여준다:

| 컬럼 | 설명 |
|------|------|
| ☐ | 체크박스 (Validation/Pharmacology 패널에서 사용할 후보 선택) |
| rank | 순위 (ddG 기준 정렬) |
| id | 후보 ID (예: `iter01_cand001`) |
| sequence | 변이 펩타이드 서열 (14-aa) |
| ddG | 결합 자유에너지 변화 (음수가 좋음, REU) |
| totalScore | Rosetta 전체 에너지 점수 |
| clashScore | 원자 충돌 점수 |
| finalScore | 최종 종합 점수 |
| result | PASS/FAIL/REF (QC 게이트 통과 여부) |

- 페이지 상단의 **전체 선택** 체크박스로 현재 페이지 후보를 일괄 선택할 수 있다.
- 선택된 후보는 하단의 Validation Panel과 Pharmacology Panel에서 자동으로 사용된다.
- 파이프라인 실행이 실패한 경우 이전 실행의 히스토리 데이터가 자동으로 표시된다 (황색 배너와 함께).

#### 5.3.4 QC Gate Chart (품질 게이트 차트)

품질 게이트별 통과/실패 비율을 막대 차트로 보여준다.

기본 게이트:
- **RosettaGate**: `ddG <= -5.0` (설정된 임계값 기준)

차트에서 녹색이 통과(PASS), 빨간색이 실패(FAIL)를 나타낸다.

#### 5.3.5 Convergence Graph (수렴 그래프)

반복별 최적 ddG 값의 변화 추이를 선 그래프로 보여준다.

- X축: 반복(iteration) 번호
- Y축: 최적 ddG 값
- 포인트별 데이터: `bestDdG`, `topCandidates` 수, `converged` 여부

ddG 값이 점점 더 낮아지면(음수 방향으로) 최적화가 진행되고 있음을 의미한다.

#### 5.3.6 Loop Timeline (루프 타임라인)

PyRosetta Flow 모드에서만 표시되며, 각 반복의 세부 이벤트를 시간순으로 나열한다.

반복별로 접힘/펼침이 가능하며, 마지막(최신) 반복이 기본으로 펼쳐져 있다.

이벤트 유형:
- `rosetta.prepare` - 구조 준비
- `rosetta.mutate` - 변이 생성
- `rosetta.refine` - FlexPepDock 정밀화
- `rosetta.score` - 스코어링
- `qc` - 품질 검증
- `planner` - 계획 수립
- `critic` - 비평 분석
- `reporter` - 보고서 작성

각 이벤트는 상태별 색상 태그(COMPLETED/RUNNING/FAILED)와 메시지가 표시된다.

### 5.4 Header 영역 정보

대시보드 상단 헤더에는 다음 정보가 실시간으로 표시된다:

- **LLM 모델명**: 현재 사용 중인 LLM 모델 (예: `gemma3:1b`)
- **PyRosetta-only 뱃지**: PyRosetta Flow 모드일 때 황색 뱃지 표시
- **API 상태 뱃지**: ESMFold / MolMIM API 상태 (live/pending/failed)
- **Last sync**: 마지막 데이터 동기화 시점 (예: `3s ago`, `1m ago`)
- **Target**: 목표 ddG 값 (`ddG <= -8.5`)
- **Live/Mock 표시**: 실시간 데이터 수신 중이면 녹색 `Live`, 아니면 회색 `Mock`

---

## 6. 신규 기능 가이드

### 6.1 Mol* 3D 분자 뷰어 (`MoleculeViewer`)

대시보드에서 후보 펩타이드의 PDB 구조를 인터랙티브 3D로 탐색할 수 있다. 외부 PyMOL 설치 없이 브라우저 내장 Mol* (molstar) 엔진을 사용한다.

**기능:**
- 후보 드롭다운에서 PDB 선택 시 자동 로드 (URL: `GET /api/structures/{path}`)
- **View Mode 전환 버튼** (4가지):
  | 모드 | 설명 | Mol* 프리셋 |
  |------|------|------------|
  | Complex | Cartoon + ligand/water/ion sticks | `polymer-and-ligand` |
  | Cartoon | 깔끔한 backbone ribbon만 표시 | `polymer-cartoon` |
  | Ball & Stick | 모든 원자를 sphere + bond로 표시 | `atomic-detail` |
  | Surface | 분자 표면 표현 | `molecular-surface` |

  > **Mol* v5.6.1 API 패턴:** `plugin.managers.structure.component.applyPreset([struct], provider)` — 구조체를 배열로 감싸고 `PresetStructureRepresentations` 맵에서 provider를 선택한다.

- 마우스 조작: 회전(좌클릭 드래그), 줌(스크롤), 이동(우클릭 드래그)

**PDB 서빙 경로:**

```
GET /api/structures/pyrosetta_flow/sst14_agentic_mutdock/iter_01/cand_001.pdb
```

`runs/` 디렉터리 하위의 PDB 파일을 CORS 헤더와 함께 서빙한다.

### 6.2 통합 검증 패널 (`ValidationPanel`)

후보 펩타이드의 약리학적·방사성의약품·통계적 기준을 통합 검증하는 패널이다.

#### 6.2.1 프리셋 선택

| 프리셋 | 설명 | 포함 기준 수 |
|--------|------|-------------|
| **PRRT 방사성의약품** | 177Lu-표지 펩타이드 치료제 기준 | 11개 |
| **일반 펩타이드** | 범용 펩타이드 의약품 기준 | 8개 |
| **Custom** | 사용자 직접 선택 | 자유 선택 |

#### 6.2.2 검증 기준 목록 (17개)

| ID | 기준 | 그룹 | 기본 임계값 |
|----|------|------|------------|
| `gravy` | GRAVY (소수성 평균) | 약리학 | -2.0 ~ 1.5 |
| `boman_index` | Boman Index (단백질 상호작용 잠재력) | 약리학 | ≤ 2.48 |
| `instability_index` | 불안정성 지수 | 약리학 | ≤ 40 |
| `isoelectric_point` | 등전점 (pI) | 약리학 | 4.0 ~ 10.0 |
| `molar_extinction` | 몰 흡광계수 ε₂₈₀ | 약리학 | ≥ 100 |
| `aliphatic_index` | 지방족 지수 | 약리학 | ≥ 30 |
| `hydrophobic_moment` | 소수성 모멘트 μH | 약리학 | 0.1 ~ 0.8 |
| `wimley_white` | Wimley-White 막 이행 자유에너지 | 약리학 | ≤ 5.0 |
| `n_end_rule` | N-말단 규칙 (생체내 반감기) | 약리학 | stabilizing |
| `protease_sites` | 프로테아제 절단 부위 수 | 약리학 | ≤ 3 |
| `net_charge_ph74` | pH 7.4 순전하 | 방사성의약품 | -2 ~ +3 |
| `renal_risk` | 신장 독성 위험도 | 방사성의약품 | ≤ 3.0 |
| `metal_coordination` | 금속 배위 잔기 수 | 방사성의약품 | ≥ 1 |
| `blosum62_similarity` | BLOSUM62 유사도 점수 | 통계 | ≥ 50 |
| `ddg_threshold` | ddG 임계값 | 통계 | ≤ -5.0 |
| `clash_score` | Clash 점수 | 통계 | ≤ 10 |
| `total_score` | 총 Rosetta 점수 | 통계 | ≤ -100 |

#### 6.2.3 사용 절차

1. Candidate Table에서 검증 대상 후보를 체크박스로 선택한다.
2. Validation Panel에서 프리셋을 선택하거나 커스텀으로 기준을 개별 체크한다.
3. **Run Validation** 버튼을 클릭한다.
4. 결과에 **Verdict 뱃지**가 표시된다:
   - **PASS** (녹색): 통과율 ≥ 80%
   - **CAUTION** (노란색): 통과율 60~80%
   - **FAIL** (빨간색): 통과율 < 60%
5. **상세 보기** 버튼 클릭 시 모달에서 각 기준별 실제 값, 임계값, 통과/실패 여부, 설명을 확인할 수 있다.

### 6.3 약리학 패널 (`PharmacologyPanel`)

13가지 문헌 기반 약리학적 속성을 계산하여 시각적으로 보여주는 패널이다. 서열 정보만으로 순수 Python 연산(외부 API 불필요)을 수행한다.

**13개 계산 항목:**

| # | 속성 | 문헌 참조 | 설명 |
|---|------|----------|------|
| 1 | GRAVY | Kyte-Doolittle (1982) | 잔기별 소수성 평균 |
| 2 | Boman Index | Boman (2003) | 단백질 결합 잠재력 |
| 3 | Instability Index | Guruprasad (1990) | DIWV 기반 안정성 예측 |
| 4 | Aliphatic Index | Ikai (1980) | 열안정성 지표 |
| 5 | Isoelectric Point (pI) | Henderson-Hasselbalch | 순전하=0 pH |
| 6 | Molar Extinction (ε₂₈₀) | Pace (1995) | UV 흡광계수 |
| 7 | N-end Rule | Varshavsky (1996) | 생체내 반감기 예측 |
| 8 | Hydrophobic Moment (μH) | Eisenberg (1982) | 양친매성 지수 |
| 9 | Wimley-White | Wimley-White (1996) | 막 이행 자유에너지 |
| 10 | Charge vs pH | Henderson-Hasselbalch | pH별 순전하 프로파일 |
| 11 | Protease Sites | MEROPS rules | 주요 프로테아제 절단부위 |
| 12 | BLOSUM62 Similarity | Henikoff (1992) | 참조 서열 대비 유사도 |
| 13 | Metal Coordination | Rulísek (1998) | 금속 배위 잔기 분석 |

**사용법:** Candidate Table에서 후보를 선택하면 자동으로 `POST /api/pharmacology/batch`를 호출하여 결과가 카드 형태로 표시된다.

### 6.4 VisualizationPanel 빈 상태 처리

`VisualizationPanel.tsx`는 `visualization_images` 배열이 비어 있을 때 기존의 빈 화면 대신 안내 메시지를 표시한다:

> **"No visualization images available yet"**

이미지가 아직 생성되지 않은 파이프라인 초기 단계에서 사용자에게 명확한 피드백을 제공한다.

### 6.5 PipelineContext (M1)

`contexts/PipelineContext.tsx`는 **prop drilling 없이** 파이프라인 상태를 하위 컴포넌트에 전달하는 React Context이다.

- **타입:** `PipelineContextValue = PipelineStatus & { switchRun: (runId: string | null) => void }`
- **사용:** `usePipelineContext()` 훅으로 접근 (Provider 바깥에서 호출 시 에러)
- **역할:** 아카이브 실행 전환(`switchRun`)을 모든 하위 컴포넌트에서 접근 가능하게 함

### 6.6 usePipelineStatus AbortController (H2)

`hooks/usePipelineStatus.ts`는 **AbortController**를 사용하여 이전 fetch 요청을 자동 취소한다:

- `switchRun()` 호출 시 진행 중인 `/api/status` fetch를 `abort()` 후 새 요청 시작
- `DOMException(AbortError)`를 graceful하게 무시
- 컴포넌트 unmount 시 cleanup으로 메모리 누수 방지

### 6.7 Agent Flow Diagram (`AgentFlowDiagram`)

6개 에이전트 간의 데이터 흐름을 시각적 다이어그램으로 표현한다. 현재 활성 에이전트가 하이라이트되며, 각 에이전트의 상태(idle/active/error)가 색상으로 표시된다.

```
Planner → Builder → QC Ranker → Diversity Mgr → Critic → Reporter
   ↑                                               |
   +------------------ 다음 반복 ←------------------+
```

- 에이전트 카드 클릭 시 최근 리포트(가설, 전략, 제안 변경사항 등) 팝업 표시
- Pipeline substep 상태에 기반하여 자동 상태 매핑

### 6.5 Experiment Control (`ExperimentControl`)

기존 Run Control Panel을 대체하는 실험 제어 패널이다.

**실행 모드:**

| 모드 | 설명 |
|------|------|
| **Full Pipeline** | NIM API + PyRosetta 전체 파이프라인 (NVIDIA API 키 필요) |
| **PyRosetta Only** | PyRosetta FlexPepDock 전용 에이전트 루프 (로컬 실행) |

**제어 기능:**
- 반복 횟수, 후보 수, LLM 모델/프로바이더, 시드, 목적 함수 모드 설정
- Start/Stop 버튼 (프로세스 PID 표시)
- 실행 중 실시간 프로세스 상태 표시

---

## 7. API 엔드포인트 설명

Backend API Server는 `http://localhost:8787`에서 동작하며 다음 엔드포인트를 제공한다.

### 7.1 GET /api/health

서버 상태 확인용 헬스체크 엔드포인트.

**요청:**
```bash
curl http://localhost:8787/api/health
```

**응답:**
```json
{
  "status": "ok",
  "timestamp": 1740441600.123
}
```

### 7.2 GET /api/status

파이프라인 전체 상태를 반환한다. Frontend가 2초 간격으로 폴링하는 핵심 엔드포인트이다.

**요청:**
```bash
curl http://localhost:8787/api/status
```

**응답 (파이프라인 실행 중):**
```json
{
  "run_id": "sst14_mutdock_1000",
  "started_at": "2026-02-25T06:30:00+00:00",
  "updated_at": "2026-02-25T06:35:12+00:00",
  "iteration": 2,
  "total_iterations": 5,
  "llm_model": "OllamaProvider(model='gemma3:1b')",
  "target": "SSTR2",
  "reference": "DOTATATE (AGCKNFFWKTFTSC, 14-aa)",
  "steps": [
    {"id": "step06", "label": "PyRosetta", "shortLabel": "Step06", "status": "running"}
  ],
  "rosetta_substeps": [
    {"id": "step06_prepare", "label": "Prepare", "status": "completed", "duration": "3s"},
    {"id": "step06_mutate", "label": "Mutate", "status": "completed", "duration": "1s"},
    {"id": "step06_refine", "label": "Refine", "status": "running"},
    {"id": "step06_score", "label": "Score", "status": "pending"},
    {"id": "step06_qc", "label": "QC", "status": "pending"}
  ],
  "agents": [
    {"id": "planner", "name": "Planner", "type": "LLM", "status": "idle", "lastMessage": "Iteration 2 planning", "taskCount": 2},
    {"id": "qc-ranker", "name": "QC & Ranker", "type": "Code", "status": "active", "lastMessage": "Ranking candidates", "taskCount": 1}
  ],
  "candidates": [
    {
      "rank": 1,
      "id": "iter01_cand001",
      "sequence": "AGCKVFFWKTFHSC",
      "pLDDT": 85.0,
      "dockScore": -6.162,
      "ddG": -18.376,
      "lDDT": 0.75,
      "finalScore": 18.376,
      "result": "PASS"
    }
  ],
  "historical_candidates": [],
  "qc_gates": [
    {"name": "RosettaGate", "criterion": "ddG <= -5.0", "passed": 3, "failed": 5, "total": 8}
  ],
  "convergence": [
    {"iteration": 1, "bestDdG": -18.376, "topCandidates": 3, "converged": false}
  ],
  "timeline": [
    {"iteration": 1, "stage": "planner", "status": "completed", "message": "Iteration 1 mutate->dock optimization", "ts": "2026-02-25T06:31:00+00:00"}
  ],
  "live_apis": {"esmfold": "pending", "molmim": "pending"},
  "best_candidate": {"id": "iter01_cand001", "sequence": "AGCKVFFWKTFHSC", "plddt": 85.0, "dockScore": -6.162},
  "visualization_images": [],
  "completed": false
}
```

**응답 (상태 파일 없음):**
```json
{
  "error": "no_status_file",
  "connected": false
}
```

### 7.3 GET /api/run/status

파이프라인 프로세스의 OS 레벨 상태를 반환한다.

**요청:**
```bash
curl http://localhost:8787/api/run/status
```

**응답 (실행 중):**
```json
{
  "running": true,
  "pid": 12345,
  "returncode": null,
  "log": "/path/to/ai4sci-kaeri/runs/live_demo/latest_run.log"
}
```

**응답 (실행 중이 아님):**
```json
{
  "running": false,
  "pid": null
}
```

### 7.4 POST /api/run/start

파이프라인 프로세스를 시작한다.

**요청 (PyRosetta Flow 모드):**
```bash
curl -X POST http://localhost:8787/api/run/start \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_mode": "pyrosetta",
    "max_iterations": 5,
    "llm_provider": "ollama",
    "llm_model": "gemma3:1b",
    "n_candidates": 8,
    "seed_base": 1000,
    "objective_mode": "auto",
    "conda_env": "bio-tools",
    "top_k": 5,
    "rosetta_ddg_max": -5.0,
    "rosetta_clash_max": 10,
    "planner_mode": "pyrosetta-only"
  }'
```

**요청 (NIM API 모드):**
```bash
curl -X POST http://localhost:8787/api/run/start \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_mode": "nim",
    "max_iterations": 10,
    "llm_provider": "ollama",
    "llm_model": "gemma3:1b",
    "llm_base_url": "http://localhost:11434",
    "llm_timeout": 120
  }'
```

**응답 (성공):**
```json
{
  "ok": true,
  "pid": 12345,
  "cmd": ["python", "scripts/run_pyrosetta_flow.py", "--input", "data/fold_test1_model_0.pdb", "--max-iterations", "5", "--n-candidates", "8", "--seed-base", "1000", "--conda-env", "bio-tools", "--objective-mode", "auto", "--top-k", "5", "--rosetta-ddg-max", "-5.0", "--rosetta-clash-max", "10", "--planner-mode", "pyrosetta-only"],
  "log": "/path/to/ai4sci-kaeri/runs/live_demo/latest_run.log"
}
```

**응답 (이미 실행 중):**
```json
{
  "ok": false,
  "error": "already_running",
  "pid": 12345
}
```

### 7.5 POST /api/run/stop

현재 실행 중인 파이프라인 프로세스를 중지한다. 먼저 SIGTERM을 보내고, 10초 내에 종료되지 않으면 SIGKILL을 보낸다.

**요청:**
```bash
curl -X POST http://localhost:8787/api/run/stop
```

**응답 (성공):**
```json
{
  "ok": true
}
```

**응답 (실행 중이 아님):**
```json
{
  "ok": false,
  "error": "not_running"
}
```

### 7.6 GET /api/images/{path}

`runs/` 디렉터리 하위의 이미지 파일을 서빙한다. 보안상 `runs/` 디렉터리 바깥 경로에 대한 접근은 403으로 차단된다.

**요청:**
```bash
curl http://localhost:8787/api/images/pyrosetta_flow/sst14_agentic_mutdock/iter_01/07_viz/render.png
```

### 7.7 GET /api/structures/{path}

`runs/` 디렉터리 하위의 PDB 파일을 서빙한다. Mol* 3D 뷰어에서 사용한다.

**요청:**
```bash
curl http://localhost:8787/api/structures/pyrosetta_flow/sst14_agentic_mutdock/iter_01/cand_001.pdb
```

**응답:** PDB 파일 바이너리 (`Content-Type: chemical/x-pdb`, CORS 허용)

### 7.8 POST /api/validate/unified

통합 검증을 실행한다. 선택된 기준에 대해 후보 서열을 평가한다.

**요청:**
```bash
curl -X POST http://localhost:8787/api/validate/unified \
  -H "Content-Type: application/json" \
  -d '{
    "sequences": ["AGCKVFFWKTFHSC", "AGCKNFFWKTFTSC"],
    "criteria": ["gravy", "boman_index", "instability_index", "net_charge_ph74"],
    "thresholds": {},
    "reference": "AGCKNFFWKTFTSC"
  }'
```

**응답:**
```json
{
  "validated_at": "2026-03-03T12:00:00+00:00",
  "criteria_used": ["gravy", "boman_index", "instability_index", "net_charge_ph74"],
  "n_candidates": 2,
  "results": [
    {
      "sequence": "AGCKVFFWKTFHSC",
      "verdict": "PASS",
      "pass_rate": 1.0,
      "n_passed": 4,
      "n_failed": 0,
      "n_skipped": 0,
      "n_total": 4,
      "checks": [
        {
          "id": "gravy",
          "label": "GRAVY (Grand Average of Hydropathicity)",
          "group": "pharmacological",
          "value": -0.45,
          "passed": true,
          "threshold": {"min": -2.0, "max": 1.5},
          "detail": "-0.45 is within [-2.0, 1.5]"
        }
      ]
    }
  ]
}
```

### 7.9 GET /api/validation/criteria

검증 기준 레지스트리와 프리셋 목록을 반환한다. Frontend에서 체크박스 UI를 구성할 때 사용한다.

**요청:**
```bash
curl http://localhost:8787/api/validation/criteria
```

**응답:**
```json
{
  "criteria": {
    "gravy": {
      "label": "GRAVY",
      "group": "pharmacological",
      "description": "Grand Average of Hydropathicity (Kyte-Doolittle, 1982)",
      "default_enabled": true,
      "threshold": {"min": -2.0, "max": 1.5},
      "unit": "kcal/mol"
    }
  },
  "presets": {
    "prrt_radiopharmaceutical": {
      "label": "PRRT 방사성의약품",
      "description": "177Lu-표지 펩타이드 치료제 기준",
      "criteria": ["gravy", "boman_index", "instability_index", ...]
    }
  }
}
```

### 7.10 POST /api/pharmacology/batch

여러 서열에 대해 13가지 약리학적 속성을 일괄 계산한다.

**요청:**
```bash
curl -X POST http://localhost:8787/api/pharmacology/batch \
  -H "Content-Type: application/json" \
  -d '{
    "sequences": ["AGCKVFFWKTFHSC"],
    "reference": "AGCKNFFWKTFTSC"
  }'
```

**응답:**
```json
{
  "results": [
    {
      "sequence": "AGCKVFFWKTFHSC",
      "pharmacology": {
        "gravy": -0.45,
        "boman_index": 1.23,
        "instability_index": 28.5,
        "aliphatic_index": 65.0,
        "isoelectric_point": 8.12,
        "molar_extinction": {"reduced": 5500, "oxidized": 5625},
        "n_end_rule": {"residue": "A", "half_life": "4.4 hr", "stability": "stabilizing"},
        "hydrophobic_moment": 0.42,
        "wimley_white": 2.3,
        "charge_ph_profile": [{"pH": 7.4, "charge": 0.5}],
        "protease_sites": [{"protease": "Trypsin", "position": 4, "site": "K-V"}],
        "blosum62": {"score": 85, "identity": 0.93, "similarity": 0.95},
        "metal_coordination": {"sites": [{"residue": "H", "position": 12}], "total": 1}
      }
    }
  ]
}
```

### 7.11 GET /api/admet/{sequence}

단일 서열에 대한 ADMET(흡수·분포·대사·배설·독성) 분석을 반환한다.

**요청:**
```bash
curl http://localhost:8787/api/admet/AGCKVFFWKTFHSC
```

**응답:**
```json
{
  "sequence": "AGCKVFFWKTFHSC",
  "admet": {
    "mw": 1571.85,
    "net_charge_ph74": 1.0,
    "n_hbd": 12,
    "n_hba": 8,
    "hydrophobicity": -0.45,
    "druglikeness_score": 7
  },
  "nephrotox": {
    "cationic_residues": 2,
    "renal_risk_score": 1.5,
    "risk_level": "Low"
  }
}
```

### 7.12 분석 API (GET /api/analysis/*)

통계적 분석 결과를 반환하는 엔드포인트 그룹이다.

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/analysis/convergence` | 반복별 ddG 수렴 데이터 |
| `GET /api/analysis/rank-stability` | 순위 안정성 분석 |
| `GET /api/analysis/gate-distribution` | QC 게이트 분포 |
| `GET /api/analysis/candidate-evidence` | 후보별 근거 데이터 |
| `GET /api/analysis/cross-run-variance` | 실행 간 분산 분석 |
| `GET /api/analysis/summary` | 종합 분석 요약 |
| `GET /api/analysis/sar-pssm` | SAR PSSM(위치별 치환 점수 행렬) |
| `POST /api/analysis/refresh` | 분석 데이터 새로고침 |

---

## 8. CLI 직접 실행법

Web UI 없이 커맨드라인에서 직접 파이프라인을 실행할 수 있다.

### 8.1 PyRosetta Flow (권장)

```bash
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri

python scripts/run_pyrosetta_flow.py \
  --input data/fold_test1_model_0.pdb \
  --max-iterations 3 \
  --n-candidates 8 \
  --seed-base 1000 \
  --conda-env bio-tools \
  --objective-mode auto \
  --top-k 5 \
  --rosetta-ddg-max -5.0 \
  --rosetta-clash-max 10 \
  --planner-mode pyrosetta-only \
  --output-json runs/pyrosetta_flow/pyrosetta_flow_artifacts.json
```

**CLI 옵션 전체 목록:**

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--input` | (필수) | 템플릿 수용체-펩타이드 복합체 PDB 경로 |
| `--n-candidates` | 8 | 반복당 변이 후보 수 |
| `--seed-base` | 1000 | 기본 난수 시드 |
| `--conda-env` | bio-tools | PyRosetta가 설치된 conda 환경명 |
| `--output-json` | runs/pyrosetta_flow/pyrosetta_flow_artifacts.json | 결과 JSON 출력 경로 |
| `--peptide-chain` | 2 | 펩타이드 체인 번호 |
| `--max-iterations` | 2 | 에이전트 루프 반복 횟수 |
| `--objective-mode` | auto | 목적 함수 모드 (auto/ddg_only/ddg_plus_constraints) |
| `--top-k` | 5 | 반복당 critic/reporter에 전달할 상위 후보 수 |
| `--rosetta-ddg-max` | -5.0 | ddG 게이트 임계값 |
| `--rosetta-clash-max` | 10 | clash 게이트 임계값 |
| `--planner-mode` | pyrosetta-only | 플래너 프롬프트 모드 (default/pyrosetta-only) |

### 8.2 NIM API Pipeline

```bash
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri

# NVIDIA NIM API 키 설정 필수
export NVIDIA_NIM_API_KEY="nvapi-..."

python run_pipeline_live.py \
  --max-iterations 10 \
  --llm-provider ollama \
  --llm-model gemma3:1b
```

### 8.3 CLI 실행 중 Web UI로 모니터링

CLI로 실행하더라도 `/tmp/pipeline_local_status.json`에 상태가 기록되므로, API Server와 Frontend를 별도로 실행하면 Web UI에서 실시간 모니터링이 가능하다.

```bash
# 터미널 1: API Server
python backend/api_server.py

# 터미널 2: Frontend
cd frontend && npm run dev

# 터미널 3: 파이프라인 직접 실행
python scripts/run_pyrosetta_flow.py --input data/fold_test1_model_0.pdb --max-iterations 3
```

브라우저에서 `http://localhost:5173`을 열면 Live 모드로 전환되어 진행 상황을 실시간으로 볼 수 있다.

---

## 9. 결과 파일 구조

파이프라인 실행 결과는 `runs/` 디렉터리 하위에 저장된다.

### 9.1 PyRosetta Flow 결과 디렉터리

```
runs/pyrosetta_flow/
  |
  +-- pyrosetta_flow_artifacts.json    # 전체 실행 결과 요약 JSON
  +-- experiment_log.jsonl             # 실험 로그 (JSONL 형식, 누적 기록)
  |
  +-- sst14_agentic_mutdock/           # 에이전트 mutate-dock 플로우 결과
       |
       +-- baseline_refined.pdb        # 기준 구조 (FlexPepDock 정밀화)
       |
       +-- iter_01/                    # 반복 1 결과
       |    +-- cand_001.pdb           # 후보 1 정밀화 구조
       |    +-- cand_002.pdb           # 후보 2 정밀화 구조
       |    +-- ...                    # (n_candidates 개만큼)
       |    +-- 07_viz/                # 시각화 결과
       |    |    +-- iter01_cand001_render.pml  # PyMOL 렌더링 스크립트
       |    +-- 08_reports/            # 보고서
       |         +-- rank_table.csv    # 후보 순위 테이블
       |         +-- summary.md        # 반복 요약 보고서
       |
       +-- iter_02/                    # 반복 2 결과
       |    +-- cand_001.pdb
       |    +-- cand_002.pdb
       |    +-- 07_viz/
       |    |    +-- iter02_cand002_render.pml
       |    +-- 08_reports/
       |         +-- rank_table.csv
       |         +-- summary.md
       |
       +-- ...                         # 추가 반복 결과
```

### 9.2 주요 결과 파일 상세

#### pyrosetta_flow_artifacts.json

전체 실행의 메타데이터와 결과를 포함하는 JSON 파일:

```json
{
  "created_at": "2026-02-25T06:45:00+00:00",
  "run_id": "sst14_mutdock_1000",
  "config": {
    "template_pdb": "data/fold_test1_model_0.pdb",
    "original_sequence": "AGCKNFFWKTFTSC",
    "n_candidates": 8,
    "seed_base": 1000,
    "max_iterations": 2,
    "objective_mode": "auto"
  },
  "iterations": [...],
  "final_candidates": [...],
  "summary": {
    "mode": "agentic_mutate_then_dock",
    "best_final_ddg": -18.376,
    "run_status": "success"
  }
}
```

#### rank_table.csv

각 반복의 후보 순위 테이블:

```csv
rank,backbone_id,seq_id,candidate_id,sequence,plddt_mean,plddt_interface,dock_score,ddg,clash_count,constraint_violations,lddt,final_score,pass_gates,fail_reasons
1,0,1,iter01_cand001,AGCKVFFWKTFHSC,85.00,82.00,-6.1624,-18.3762,1,0,0.7500,1.000000,True,
```

#### experiment_log.jsonl

모든 실행에 걸친 누적 실험 기록. JSONL(JSON Lines) 형식으로 한 줄에 하나의 레코드가 기록된다:

```jsonl
{"record_type":"candidate","status":"success","run_id":"sst14_mutdock_1000","iteration":1,"candidate_id":"iter01_cand001","sequence":"AGCKVFFWKTFHSC","ddg":-18.376,"clash":1.0,"selected":true,"ts":"2026-02-25T06:35:00+00:00"}
```

### 9.3 NIM API Pipeline 결과

NIM API 모드의 결과는 더 많은 중간 산출물을 포함한다:

```
runs/{run_id}/
  +-- 00_config/        # 설정 파일
  +-- 01_receptor/      # 수용체 PDB, 포켓 잔기 정보
  +-- 02_backbones/     # RFdiffusion 생성 백본
  +-- 03_sequences/     # ProteinMPNN 생성 서열
  +-- 04_esmfold_qc/    # ESMFold 구조 예측 + QC
  +-- 05_docking/       # DiffDock 도킹 결과
  +-- 05b_selectivity/  # Off-target 선택성 스크리닝
  +-- 06_rosetta/       # PyRosetta 정밀화 + ddG
  +-- 07_analysis/      # 분석 보고서, 렌더링
  +-- 08_reports/       # 연구 노트, 의사결정 로그
```

---

## 10. 트러블슈팅

### 10.1 Frontend가 Backend에 연결되지 않는 경우

**증상:** 대시보드에 Mock 뱃지만 표시되고 Live로 전환되지 않음.

**확인 사항:**
1. Backend API Server가 실행 중인지 확인:
   ```bash
   curl http://localhost:8787/api/health
   # 응답: {"status": "ok", "timestamp": ...}
   ```
2. Vite 프록시 설정이 올바른지 확인 (`frontend/vite.config.ts`):
   ```typescript
   server: {
     proxy: {
       '/api': {
         target: 'http://localhost:8787',
         changeOrigin: true,
       },
     },
   }
   ```
3. 포트 충돌 여부 확인:
   ```bash
   # 8787 포트 사용 중인 프로세스 확인
   lsof -i :8787
   # 5173 포트 사용 중인 프로세스 확인
   lsof -i :5173
   ```

### 10.2 파이프라인 시작 후 상태가 갱신되지 않는 경우

**증상:** Start Run 후 PID는 표시되지만 대시보드가 Live로 전환되지 않음.

**확인 사항:**
1. 상태 파일이 생성되었는지 확인:
   ```bash
   ls -la /tmp/pipeline_local_status.json
   cat /tmp/pipeline_local_status.json | python -m json.tool
   ```
2. 파이프라인 로그 확인:
   ```bash
   tail -f runs/live_demo/latest_run.log
   ```
3. 파이프라인 프로세스가 실행 중인지 확인:
   ```bash
   curl http://localhost:8787/api/run/status
   ```

### 10.3 "already_running" 오류

**증상:** Start Run 클릭 시 `Start failed: already_running` 메시지.

**해결:** Stop 버튼을 눌러 기존 프로세스를 중지하거나, 이미 종료된 프로세스가 정리되지 않은 경우 API Server를 재시작한다.

```bash
# 강제 중지
curl -X POST http://localhost:8787/api/run/stop

# 또는 API Server 재시작
# Ctrl+C로 api_server.py 종료 후 다시 실행
python backend/api_server.py
```

### 10.4 Ollama 연결 실패

**증상:** 파이프라인 실행 중 LLM 에이전트가 응답하지 않음. 로그에 `Ollama API error` 출력.

**확인 사항:**
1. Ollama 서버가 실행 중인지 확인:
   ```bash
   curl http://localhost:11434/api/tags
   ```
2. 모델이 다운로드되어 있는지 확인:
   ```bash
   ollama list
   # gemma3:1b 모델이 목록에 있어야 함
   ```
3. 모델이 없으면 다운로드:
   ```bash
   ollama pull gemma3:1b
   ```
4. LLM 없이 실행하려면 Provider를 `none`으로 설정한다 (Web UI 또는 `pipeline_config.yaml`에서 `provider: "none"`).

### 10.5 conda 환경 관련 오류

**증상:** PyRosetta Flow 실행 시 `Script failed: flexpep_dock.py` 오류.

**확인 사항:**
1. `bio-tools` conda 환경이 존재하는지 확인:
   ```bash
   conda env list | grep bio-tools
   ```
2. 해당 환경에서 PyRosetta를 import할 수 있는지 확인:
   ```bash
   conda run -n bio-tools python -c "import pyrosetta; print('OK')"
   ```
3. conda가 시스템 PATH에 있는지 확인:
   ```bash
   which conda
   ```

### 10.6 상태 파일 권한 문제

**증상:** `Permission denied` 오류로 파이프라인 시작 실패.

**해결:**
```bash
# 상태 파일 경로 확인 및 권한 부여
touch /tmp/pipeline_local_status.json
chmod 666 /tmp/pipeline_local_status.json

# 또는 다른 경로 사용
PIPELINE_STATUS_FILE=$HOME/pipeline_status.json python backend/api_server.py
```

### 10.7 Frontend 빌드 오류

**증상:** `npm run dev` 실행 시 의존성 오류.

**해결:**
```bash
cd frontend

# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install

# Node.js 버전 확인 (18 이상 필요)
node --version
```

### 10.8 PyRosetta Flow에서 모든 후보가 FAIL인 경우

**증상:** Candidate Table에서 모든 후보의 result가 FAIL이고 ddG가 999.0.

**원인:** FlexPepDock 정밀화 과정에서 모든 후보가 실패한 경우. 이는 대개 다음이 원인이다:
- 입력 PDB 파일의 구조 문제
- conda 환경의 PyRosetta 버전 불일치
- 메모리 부족

**확인 사항:**
1. 입력 PDB 파일이 존재하고 유효한지 확인:
   ```bash
   ls -la data/fold_test1_model_0.pdb
   ```
2. 로그에서 상세 오류 확인:
   ```bash
   tail -100 runs/live_demo/latest_run.log
   ```
3. 파이프라인은 fail-open 정책으로 부분 실패 시에도 계속 진행하며, `experiment_log.jsonl`에 실패 기록이 남는다.

### 10.9 WSL 환경에서의 포트 접근 문제

**증상:** WSL2에서 실행 시 Windows 브라우저에서 `localhost:5173`에 접속이 안 됨.

**해결:**
```bash
# WSL2의 IP 확인
hostname -I

# Windows 브라우저에서 해당 IP로 접속
# 예: http://172.x.x.x:5173
```

또는 Vite 설정에서 host를 지정한다:
```bash
cd frontend
npx vite --host 0.0.0.0
```

---

## 부록: 기술 스택 요약

| 구분 | 기술 | 버전 |
|------|------|------|
| Frontend Framework | React | 19.2 |
| Build Tool | Vite | 7.x |
| CSS | TailwindCSS | 4.x |
| Chart | Recharts | 3.x |
| Icons | Lucide React | 0.574 |
| 3D Viewer | Mol* (molstar) | 4.x |
| Backend | Python http.server | 3.11+ |
| LLM Provider | Ollama / vLLM | - |
| Default LLM | Qwen 3 8B (gemma3:1b 폴백) | - |
| Molecular Dynamics | PyRosetta | conda bio-tools |
| 약리학 계산 | pharmacology.py (순수 Python) | - |
| 통합 검증 | unified_validation.py | - |
| ADMET 분석 | admet.py | - |
| SAR 분석 | sar_analysis.py | - |
| Process Communication | JSON file (`/tmp/pipeline_local_status.json`) | - |

## 부록: Backend 모듈 구조

```
backend/
  +-- api_server.py          # HTTP API 서버 (port 8787)
  +-- status_emitter.py      # 파이프라인 상태 JSON 기록
  +-- analysis.py            # 통계 분석 (수렴, 순위 안정성 등)
  +-- validation.py          # 레거시 검증 (ddG/clash/score 기반)
  +-- unified_validation.py  # 통합 검증 엔진 (17개 기준, 프리셋)
  +-- pharmacology.py        # 13개 약리학 속성 계산
  +-- admet.py               # ADMET 분석 (약물유사성, 신장독성)
  +-- sar_analysis.py        # SAR PSSM 분석
```

## 부록: Frontend 컴포넌트 구조

```
frontend/src/
  +-- App.tsx                       # 메인 레이아웃 + 상태 관리
  +-- components/
  |     +-- ExperimentControl.tsx    # 실험 제어 (모드/파라미터/실행)
  |     +-- PipelineStatus.tsx       # 7-column 파이프라인 진행 바
  |     +-- AgentFlowDiagram.tsx     # 에이전트 흐름도
  |     +-- AgentMonitor.tsx         # 에이전트 상태 카드
  |     +-- MoleculeViewer.tsx       # Mol* 3D 뷰어
  |     +-- CandidateTable.tsx       # 후보 테이블 (선택/정렬/필터)
  |     +-- ValidationPanel.tsx      # 통합 검증 패널 + 상세 모달
  |     +-- PharmacologyPanel.tsx    # 약리학 속성 패널
  |     +-- QCGateChart.tsx          # QC 게이트 차트
  |     +-- ConvergenceGraph.tsx     # 수렴 그래프
  |     +-- LoopTimeline.tsx         # 반복 타임라인
  |     +-- VisualizationPanel.tsx   # 이미지 시각화
  +-- contexts/
  |     +-- PipelineContext.tsx       # M1: PipelineStatus + switchRun 컨텍스트 (prop drilling 제거)
  +-- hooks/
  |     +-- usePipelineStatus.ts     # H2: 상태 폴링 훅 (AbortController로 이전 fetch 취소)
  |     +-- useExperiment.ts         # 실험 제어 훅
  |     +-- useSelection.ts          # 체크박스 선택 상태 관리
  |     +-- useCandidateSort.ts      # 후보 테이블 정렬/필터
  |     +-- useAdmetBatch.ts         # ADMET 일괄 계산
  |     +-- useValidation.ts         # 통합 검증 워크플로우
  +-- types/
        +-- index.ts                 # TypeScript 타입 정의
```

---

> 본 문서는 `ai4sci-kaeri` 프로젝트의 PyRosetta Flow Web UI 시스템을 기준으로 작성되었다.
