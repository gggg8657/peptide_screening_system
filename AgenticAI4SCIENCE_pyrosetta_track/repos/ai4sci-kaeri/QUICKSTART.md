# QUICKSTART — SSTR2 AI Co-Scientist Pipeline

**최종 업데이트**: 2026-03-05

이 문서는 SSTR2 표적 방사성의약품 후보 스크리닝 시스템을 로컬에서 실행하기 위한 빠른 시작 가이드이다.
전체 아키텍처 개요는 `ARCHITECTURE.md`를 참조한다.

---

## 1. Prerequisites (사전 요구사항)

| 항목 | 버전 | 비고 |
|------|------|------|
| Python | 3.12+ | conda env `bio-tools` 권장 |
| Node.js | 20+ | npm 포함 |
| conda | latest | PyRosetta 설치에 필요 |
| PyRosetta | 2024.x+ | conda env `bio-tools`에 설치 |
| Ollama | latest | LLM agent (Planner, Critic 등) 구동용 |

### conda 환경 생성 (최초 1회)

```bash
conda create -n bio-tools python=3.12 -y
conda activate bio-tools

# PyRosetta 설치 (라이선스 필요 — https://www.pyrosetta.org/downloads)
# 설치 방법은 PyRosetta 공식 문서를 따른다.

# Python 의존성
pip install fastapi uvicorn[standard] pydantic
pip install -r requirements.txt  # 프로젝트 루트에 있는 경우
```

### Ollama 설치 및 모델 준비

```bash
# Ollama 설치 (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# 모델 다운로드 (Planner/Critic agent에서 사용)
ollama pull llama3.1
```

---

## 2. Backend 실행

프로젝트 루트(`ai4sci-kaeri/`)에서 실행한다.

```bash
conda activate bio-tools

# 의존성 설치
pip install fastapi uvicorn[standard]

# 백엔드 서버 시작 (포트 8787)
uvicorn backend.main:app --host 0.0.0.0 --port 8787 --reload
```

서버가 정상 기동되면 다음 URL에서 API 문서를 확인할 수 있다:
- Swagger UI: `http://localhost:8787/docs`
- ReDoc: `http://localhost:8787/redoc`

주요 API 라우터:
- `/api/status` -- 파이프라인 상태 조회
- `/api/analysis` -- 분석 결과 조회
- `/api/validation` -- 검증 결과 조회
- `/api/experiment` -- 실험 제어 (시작/중지)

---

## 3. Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

개발 서버가 `http://localhost:5173`에서 시작된다.
Vite 프록시 설정에 의해 `/api/*` 요청은 자동으로 백엔드(`localhost:8787`)로 전달된다.

> 백엔드가 실행되지 않은 상태에서도 프론트엔드는 mock 모드로 동작하며,
> 더미 데이터로 UI를 확인할 수 있다.

---

## 4. Silo B 파이프라인 실행 (SST-14 Mutation Simulation)

Silo B는 SST-14 네이티브 서열(`AGCKNFFWKTFTSC`)을 기반으로 돌연변이 시뮬레이션을 수행하여
SSTR2 바인딩 최적 후보를 탐색한다. PyRosetta FlexPepDock을 사용한다.

### 4.1 UI에서 실행 (ExperimentControl 패널)

1. 브라우저에서 `http://localhost:5173/silo-b` 접속
2. ExperimentControl 패널에서 파라미터 설정
3. "Start Experiment" 클릭

### 4.2 CLI에서 실행

```bash
conda activate bio-tools
cd ai4sci-kaeri/

python -m pyrosetta_flow.runner
```

### 4.3 주요 설정 파라미터 (FlowConfig)

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `max_iterations` | 2 | 진화 루프 반복 횟수 |
| `n_candidates` | 8 | 반복당 생성 후보 수 |
| `top_k` | 5 | 다음 반복으로 진행할 상위 후보 수 |
| `validation_n_trials` | 1 | 다중 검증 시행 횟수 (1=단일, 10=논문 표준) |
| `validation_max_workers` | 4 | 검증 병렬 워커 수 |
| `objective_mode` | `"auto"` | 목적함수 모드 (`auto`, `ddg_only`, `ddg_plus_constraints`) |
| `seed_base` | 1000 | 난수 시드 기준값 |
| `max_parallel_workers` | 4 | FlexPepDock 병렬 프로세스 수 |
| `script_timeout` | 300 | 서브프로세스 타임아웃 (초) |
| `convergence_window_size` | 3 | 수렴 감지 윈도우 크기 |
| `bandit_n_focus` | 3 | Thompson sampling 집중 위치 수 |

결과물은 `runs/pyrosetta_flow/` 디렉토리에 JSON 형식으로 저장된다.

---

## 5. Silo A (3-ARM Full Pipeline) -- 설계 단계

Silo A는 de novo 백본 설계부터 시퀀스 설계, 도킹, 선택성 스크리닝까지 8단계를 자동화하는
전체 파이프라인이다. 현재 **설계 단계(pre-implementation)**이며, `ARCHITECTURE_V2.md`에
상세 설계가 기술되어 있다.

### 사전 요구사항

- **NGC API 키**: NVIDIA NIM 클라우드 API 호출에 필요
  - `https://build.nvidia.com`에서 발급
  - 환경변수 설정: `export NGC_API_KEY=your_key_here`

### 향후 실행 방법 (구현 완료 시)

```bash
# Silo A 단독 실행 (계획)
python -m AG_src.pipeline.orchestrator --config config/silo_a.yaml
```

자세한 내용은 `ARCHITECTURE_V2.md`를 참조한다.

---

## 6. 대시보드 페이지 구성

프론트엔드는 React + React Router 기반이며, 다음 6개 페이지로 구성된다.

| 경로 | 페이지 | 설명 |
|------|--------|------|
| `/` | -- | `/silo-b`로 자동 리다이렉트 |
| `/silo-b` | Silo B | SST-14 돌연변이 시뮬레이션 대시보드 (메인) |
| `/silo-a` | Silo A | 3-ARM 가상 스크리닝 대시보드 |
| `/combined` | Combined | 양 Silo 교차 비교 뷰 |
| `/settings` | Settings | NIM 설정, 파이프라인 파라미터 |
| `/about` | About | 프로젝트 정보 |

Silo B 대시보드 주요 패널:
- **ExperimentControl** -- 실험 시작/중지, 파라미터 설정
- **CandidateTable** -- 후보 서열 목록, ddG 정렬
- **PharmacologyPanel** -- 13종 약리학적 지표 + 5종 구조 규칙
- **VisualizationPanel** -- Mol* 3D 구조 뷰어, PyMOL 렌더링 이미지

---

## 7. 개발 (Development)

### Frontend

```bash
cd frontend

# ESLint 검사
npm run lint

# 테스트 실행 (Vitest + React Testing Library)
npm run test

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

### Backend / Pipeline (Python)

```bash
conda activate bio-tools

# pyrosetta_flow 테스트 실행
cd pyrosetta_flow
python -m pytest tests/ -v

# 특정 테스트 파일 실행
python -m pytest tests/test_schema.py -v
```

---

## 8. Troubleshooting (문제 해결)

### 백엔드 미연결 -- Mock 모드

**증상**: 프론트엔드에서 "Backend disconnected" 또는 데이터가 표시되지 않음

**원인**: 백엔드 서버가 실행되지 않았거나 포트가 다름

**해결**:
1. 백엔드가 포트 8787에서 실행 중인지 확인: `curl http://localhost:8787/docs`
2. 미실행 시 프론트엔드는 자동으로 mock 모드로 전환되어 더미 데이터를 표시한다
3. 실제 데이터를 보려면 백엔드를 먼저 시작한다

### PyRosetta import 오류

**증상**: `ModuleNotFoundError: No module named 'pyrosetta'`

**해결**:
1. conda 환경이 활성화되어 있는지 확인: `conda activate bio-tools`
2. PyRosetta가 설치되어 있는지 확인: `python -c "import pyrosetta; print(pyrosetta.__version__)"`
3. PyRosetta는 pip가 아닌 conda 채널 또는 직접 설치가 필요하다

### Ollama 미실행

**증상**: agent 호출 시 connection refused 오류, LLM 응답 없음

**해결**:
1. Ollama 서비스 상태 확인: `systemctl status ollama` 또는 `ollama list`
2. 서비스 시작: `ollama serve` (별도 터미널)
3. 모델 존재 확인: `ollama list` 에서 사용 모델이 있는지 확인
4. `FlowConfig.llm_model_override`로 모델명을 명시적으로 지정할 수 있다

### 포트 충돌

**증상**: `Address already in use`

**해결**:
```bash
# 포트 사용 프로세스 확인
lsof -i :8787  # 백엔드
lsof -i :5173  # 프론트엔드

# 프로세스 종료
kill -9 <PID>
```

### FlexPepDock 타임아웃

**증상**: 파이프라인이 300초 후 중단됨

**해결**:
- `FlowConfig.script_timeout` 값을 증가시킨다 (기본 300초)
- 대형 구조의 경우 600초 이상 권장
- `max_parallel_workers`를 줄여 시스템 부하를 낮춘다

---

## 참고 문서

- `ARCHITECTURE.md` -- 듀얼 파이프라인 전체 아키텍처
- `ARCHITECTURE_V2.md` -- V2 3-ARM 통합 파이프라인 설계
- `pyrosetta_flow/schema.py` -- FlowConfig 전체 파라미터 정의
- `backend/main.py` -- FastAPI 엔트리포인트
