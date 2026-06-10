# ai4sci-kaeri 코드베이스 대시보드

> AI-Scientist: SSTR2 Peptide Binder Design Pipeline — 전체 구조 문서
>
> 최종 갱신: 2026-03-06

---

## 1. Overview

SSTR2 표적 방사성의약품 후보 펩타이드를 AI Co-Scientist 파이프라인으로 스크리닝하는 프로젝트.
듀얼 사일로(Silo A: 3-ARM de novo 설계, Silo B: SST-14 돌연변이 시뮬레이션) 구조로 운용하며,
5-Agent agentic 시스템이 반복적 가설-실험-비평 루프를 수행한다.

| 항목 | 내용 |
|------|------|
| Target | SSTR2 (UniProt P30874, 369aa GPCR) |
| Reference | SST-14: `AGCKNFFWKTFTSC` (Cys3-Cys14 disulfide, FWKT pharmacophore) |
| Radioisotope | 68Ga (PET), 177Lu (therapy), 225Ac (alpha therapy) |
| Stack | React 19 + TypeScript + Vite 7 / FastAPI 2.0 / PyRosetta / Ollama |
| Dashboard | `http://localhost:5173` (frontend) / `http://localhost:8787` (API) |

### 디렉토리 구조

```
ai4sci-kaeri/
├── frontend/src/          # React SPA (5 pages, 20 components, 6 hooks)
├── backend/               # FastAPI API (7 routers, 30+ endpoints)
├── AG_src/                # 5-Agent system + 8-step pipeline + NIM tools
│   ├── agents/            # 6 agents (base + planner/builder/critic/qc_ranker/reporter/diversity_manager)
│   ├── pipeline/          # 8-step orchestrator + step modules
│   ├── tools/api/         # 8 NVIDIA NIM API wrappers
│   ├── tools/mcp/         # 3 MCP servers (PyMOL/PyRosetta/FoldMason)
│   └── config/            # pipeline_config.yaml, gate_thresholds.yaml
├── pyrosetta_flow/        # Silo B runner (FlexPepDock mutation loop)
│   ├── runner.py          # 메인 실행 엔진 (~995 lines)
│   ├── schema.py          # FlowConfig, CandidateResult dataclasses
│   ├── ranking.py         # JSONL experiment log 관리
│   ├── convergence.py     # Mann-Whitney U + CV 수렴 탐지
│   ├── bandit.py          # Thompson sampling 위치 최적화
│   └── adapter.py         # 돌연변이 생성, config 검증
└── docs/                  # 아키텍처 문서, 이미지
```

---

## 2. Frontend Pages

5개 페이지, React Router v6 lazy-loading + PageErrorBoundary 격리.

| Route | Page | 설명 |
|-------|------|------|
| `/silo-b` (default) | **SiloBPage** | Silo B (PyRosetta) 실시간 모니터링. 20개 컴포넌트 전체 사용. 실험 제어, 파이프라인 스텝, 에이전트 상태, 후보 테이블, 약리학 패널, 검증 패널, 수렴 그래프, SAR 히트맵, 3D 분자 뷰어 등 |
| `/silo-a` | **SiloAPage** | Silo A (3-ARM NIM) 설정/상태. 8-step 파이프라인 정의, 8개 NIM API 서비스 테이블, 5 에이전트 목록. 현재 Design Phase (PlaceholderState) |
| `/combined` | **CombinedPage** | Cross-silo 비교. 양 사일로 파이프라인 진행도, 통합 랭킹 가중치 (ddG 35%, selectivity 20%, stability 15%, PK 15%, chelator 15%), 교차 검증 다이어그램 |
| `/settings` | **SettingsPage** | 실행 전략 선택 (5종), NIM API 키/모드 설정, Silo B 파라미터 (iterations, candidates, top-K, LLM model, validation trials), Silo A 파라미터 |
| `/about` | **AboutPage** | 시스템 아키텍처 문서. 12개 확장형 기능 카드, 기술 스택, 17개 validation criteria 레퍼런스 테이블 |

### 라우팅 구조 (App.tsx)

```
BrowserRouter
└── AppLayout (PipelineProvider wrapping)
    ├── Header: 로고, 상태 표시 (Live/Archive/Mock), API badges, RunSelector
    ├── TabNav: Silo B | Silo A | Combined | Settings | About
    ├── Routes (Suspense + PageErrorBoundary)
    │   ├── / → redirect → /silo-b
    │   ├── /silo-b → SiloBPage
    │   ├── /silo-a → SiloAPage
    │   ├── /combined → CombinedPage
    │   ├── /settings → SettingsPage
    │   └── /about → AboutPage
    └── Footer: 버전 정보, Run ID
```

---

## 3. UI Components

20개 컴포넌트 (`frontend/src/components/`).

| Component | 역할 |
|-----------|------|
| **AgentFlowDiagram** | SVG 플로우차트: 에이전트 실행 순서 (Planner→Mutator→Critic→Reporter) 상태 표시 |
| **AgentMonitor** | 5 에이전트 상태 사이드바 (status, lastMessage, taskCount, 확장형 리포트) |
| **CandidateTable** | 정렬/필터/페이지네이션 후보 테이블 (ddG, clash, finalScore, PASS/FAIL, 3D 뷰, ADMET) |
| **ConvergenceGraph** | Recharts Line/Bar 오버레이: iteration별 best-ddG 수렴 + Mann-Whitney U 정체 탐지 |
| **DdGDistribution** | ddG 히스토그램 (2.5 kcal/mol 빈), QC threshold (-5.0) 참조선 |
| **ExperimentControl** | Play/Stop 버튼, iteration 표시, feature toggles, validation preset, LLM 모델 선택 |
| **LoopTimeline** | iteration별 이벤트 타임라인 (mutate→dock→QC→critic→reporter) |
| **MoleculeViewer** | Mol* v5.6.1 3D PDB 뷰어 (Complex/Cartoon/Ball&Stick/Surface 4 모드) |
| **MutationAnalysis** | BLOSUM62 conservation score vs ddG improvement 산점도 |
| **PharmacologyPanel** | 13개 약리학 속성 아코디언 (GRAVY, Boman, instability, pI, extinction 등) |
| **PipelineStatus** | 수평 스텝 진행바 + Rosetta substep 확장 |
| **PlaceholderState** | 데이터 미수신 시 "Awaiting pipeline data" 오버레이 |
| **PositionEnrichment** | SST-14 각 위치별 상위 아미노산 빈도 + 평균 ddG 테이블 |
| **QCGateChart** | QC gate별 pass/fail 스택 바차트 |
| **RiskMatrix** | 3x3 확률-영향 매트릭스 (P0/P1/P2 우선순위) |
| **RunComparisonPanel** | 아카이브 런 목록 + 미니 스파크라인 (best ddG 수렴) |
| **SARHeatmap** | 20x15 AA 그리드: 각 SST-14 위치 돌연변이 빈도 히트맵 |
| **SequenceLogo** | 위치별 AA 빈도 바 플롯 + FWKT pharmacophore 하이라이팅 |
| **ValidationPanel** | 통합 검증 결과 (PASS/CAUTION/FAIL), 5 구조 규칙 + 13 약리학 체크 |
| **VisualizationPanel** | PyMOL 렌더링 갤러리 (overview/closeup/interface/electrostatics) + lightbox |

### Hooks (6개)

| Hook | 역할 |
|------|------|
| **usePipelineStatus** | `/api/status` 2초 폴링, 실행 모드 감지 (pyrosettaOnly/full), 라이브/아카이브 전환 |
| **useSelection** | 후보 선택 상태 관리 (Set\<string\>): toggle, togglePage, clear |
| **useValidation** | 선택된 후보 `/api/validate/selected` POST, 결과 Map 관리 |
| **useCandidateSort** | 정렬 (rank/ddG/totalScore/clashScore/finalScore), 필터 (PASS/FAIL/REF), 페이지네이션 (12/page) |
| **useExperiment** | `/api/experiment/*` config/models 조회, status 폴링, feature toggles, start/stop |
| **useAdmetBatch** | `/api/admet/batch` POST (unique sequences), 결과 Map 캐싱 |

### Context

| Context | 역할 |
|---------|------|
| **PipelineContext** | `PipelineStatus & { switchRun }` — 전역 파이프라인 상태 제공 (prop drilling 방지) |

---

## 4. Backend API

FastAPI v2.0.0 — `uvicorn backend.main:app --port 8787`

7개 라우터, 모든 엔드포인트 `/api` 접두사.

### 4.1 Status Router (`/api`)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/status` | 현재 파이프라인 상태 읽기 |
| GET | `/health` | 헬스체크 (`{status: "ok", timestamp}`) |
| POST | `/status` | 파이프라인 상태 push (StatusEmitter가 호출) |
| GET | `/runs` | 아카이브 런 목록 |
| GET | `/runs/{run_id}` | 특정 아카이브 런 전체 데이터 |

### 4.2 Analysis Router (`/api`)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/analysis/convergence` | iteration별 수렴 통계 |
| GET | `/analysis/rank-stability` | Top-k 랭크 안정성 |
| GET | `/analysis/gate-distribution` | QC gate pass/fail 분포 |
| GET | `/analysis/candidate-evidence` | 후보별 evidence score |
| GET | `/analysis/cross-run-variance` | cross-run ddG 분산 |
| GET | `/analysis/summary` | 통합 분석 요약 |
| GET | `/analysis/sar-pssm` | Position-Specific Scoring Matrix |
| POST | `/analysis/refresh` | 전체 분석 재계산 + 디스크 캐시 |

### 4.3 Validation Router (`/api`)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/validation/criteria` | 검증 기준 레지스트리 (17 criteria) |
| GET | `/validation/results` | 최근 검증 결과 |
| POST | `/validation/run` | 통계적 검증 (rank stability, score consistency, dominance) |
| POST | `/validate/selected` | 규칙 기반 검증 (ddG ≤ -5, clash ≤ 10, totalScore ≤ -300) |
| POST | `/validate/unified` | 통합 검증 (약리학 13개 + 통계 3개 + 방사약 2개) |

### 4.4 Experiment Router (`/api`)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/experiment/config` | 기본 실험 설정 |
| GET | `/experiment/models` | 사용 가능 LLM 모델 (Ollama 쿼리) |
| GET | `/experiment/status` | 실행 중 실험 상태 |
| POST | `/experiment/run` | 실험 시작 (subprocess로 runner.py 실행) |
| POST | `/experiment/stop` | 실험 중지 (SIGTERM→SIGKILL) |

### 4.5 ADMET Router (`/api`)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/admet/{sequence}` | 단일 서열 ADMET + 신독성 분석 |
| POST | `/admet/batch` | 배치 ADMET (최대 50 서열) |
| POST | `/pharmacology/batch` | 배치 약리학 속성 (13개 메서드, 최대 50 서열) |

### 4.6 Settings Router (`/api`)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/settings` | 현재 런타임 설정 |
| PUT | `/settings` | 런타임 설정 갱신 (execution_strategy, max_iterations 등) |

### 4.7 Static Router (`/api`)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/structures/{path}` | PDB 파일 서빙 (경로 탐색 방지, symlink 차단, .pdb만) |
| GET | `/images/{path}` | 이미지 파일 서빙 (PyMOL 렌더링 등) |

### 핵심 백엔드 모듈

| 모듈 | 역할 |
|------|------|
| **state.py** | 공유 상태: STATUS_FILE 캐시 (mtime 기반), experiment process 관리, runtime_settings dict |
| **pharmacology.py** | 13개 약리학 속성 계산 (Kyte-Doolittle GRAVY, Boman, Guruprasad 등) |
| **validation.py** | 수학적 검증: rank stability, score consistency, no-dominance (가중 합산) |
| **unified_validation.py** | 통합 검증 facade: 약리학 + 통계 + 방사약 criteria (23개 총 기준) |
| **admet.py** | ADMET 속성 + 신독성 리스크 스코어링 (Low/Moderate/High) |
| **analysis.py** | 실험 데이터 분석: convergence, cross-run variance, rank stability, gate distribution |
| **sar_analysis.py** | PSSM + epistasis pair 탐지 |
| **status_emitter.py** | runner → STATUS_FILE JSON bridge (fcntl-safe) |

---

## 5. Agent System (AG_src)

6개 에이전트 + 8-step orchestrator.

### 5.1 Agents

| Agent | Type | 역할 |
|-------|------|------|
| **BaseAgent** | ABC | 추상 기반: 메시지 프로토콜 (MessageType: INFO/REQUEST/DECISION/ALERT), LLM 인터페이스 |
| **PlannerAgent** | LLM | 과학적 가설 생성, focus_positions + suggested_mutations 출력. pyrosetta_only 모드 지원 |
| **BuilderAgent** | Code | Step01-07 실행 오케스트레이션. 실패 시 retry (3회, 지수 백오프) + fallback (DiffDock→Boltz2 등) |
| **QCRankerAgent** | Code | 4-gate 순차 필터링 (pLDDT→Docking→Rosetta→Selectivity) + 가중 복합 점수 랭킹 |
| **DiversityManager** | Code | FoldMason lDDT 기반 구조 클러스터링 + 대표 후보 선별 (Silo A 전용, Silo B는 서열 dedup) |
| **ScientistCritic** | LLM | 실패 분류 (6 FailureType) + 파라미터 변경 제안 (iteration당 최대 2개). FAILURE_ACTION_MAP 테이블 |
| **ReporterAgent** | LLM | PyMOL 4-panel 렌더링, CSV/Markdown 리포트, Lab Notebook 생성 |

### 5.2 QC Gate 순서 (AND 로직)

1. **pLDDT Gate**: plddt_mean ≥ 75 AND plddt_interface ≥ 70
2. **Docking Gate**: dock_score 상위 20%
3. **Rosetta Gate**: ddG ≤ -5.0 AND clash ≤ 10 AND constraint_violations ≤ 0
4. **Selectivity Gate**: selectivity_margin + offtarget 임계값

### 5.3 랭킹 가중치

| 모드 | pLDDT | dock_score | ddG | lDDT | selectivity |
|------|-------|-----------|-----|------|-------------|
| Default (Silo A) | 0.15 | 0.25 | 0.25 | 0.15 | 0.20 |
| PyRosetta-only (Silo B) | — | — | 0.70 | — | — |
| (Silo B: total_score=0.20, clash=0.10) |

### 5.4 Pipeline Steps (8-step Orchestrator)

```
Iteration N
├─ 1. Planner → ExperimentPlan (가설 + 파라미터)
├─ 2. Builder (Step01-07)
│   ├─ Step01: Receptor Prep (OpenFold3 / 기존 PDB 로드)
│   ├─ Step02: Backbone Design (RFdiffusion)
│   ├─ Step03: Sequence Design (ProteinMPNN)
│   ├─ Step03b: BLOSUM62 Mutation (Silo B 호환)
│   ├─ Step04: Fast QC (ESMFold pLDDT)
│   ├─ Step05: Docking (DiffDock / Boltz-2)
│   ├─ Step05b: Selectivity Screening (off-target SSTR1/3/4/5)
│   ├─ Step06: Rosetta Refinement (FlexPepDock + ddG)
│   └─ Step07: Analysis (FoldMason lDDT + PyMOL renders)
├─ 3. QC & Ranker → gate 필터링 + 랭킹
├─ 4. Diversity Manager → 구조 클러스터링
├─ 5. Scientist Critic → 실패 분석 + 파라미터 제안 (max 2)
├─ 6. Reporter → PyMOL 렌더링 + Markdown 리포트
└─ Convergence Check → 수렴 시 종료
```

### 5.5 NIM API Tools (8개)

| Tool | Endpoint | 용도 |
|------|----------|------|
| **ESMFoldTool** | nvidia/esmfold | 구조 예측 + pLDDT 점수 |
| **RFdiffusionTool** | ipd/rfdiffusion | de novo backbone 생성 |
| **ProteinMPNNTool** | ipd/proteinmpnn | 역접힘 (서열 설계) |
| **DiffDockTool** | mit/diffdock | 펩타이드-수용체 도킹 |
| **Boltz2Tool** | — | DiffDock fallback 도킹 |
| **ESM2Tool** | — | 단백질 언어 모델 임베딩 |
| **OpenFold3Tool** | — | 구조 예측 (ESMFold 대안) |
| **MolMIMTool** | — | 소분자 생성 |

모든 도구는 `BaseTool` 상속: NGC API 키 자동 탐색, 지수 백오프 재시도 (429/5xx), `ToolResult` 반환.

### 5.6 MCP Servers (3개)

| Server | Tools | 실행 방식 |
|--------|-------|----------|
| **PyMOLMCPServer** | render_overview, render_closeup, render_interface_contacts, render_electrostatics, render_plddt_spectrum, batch_render, create_comparison_panel | subprocess `pymol -c script.pml` |
| **PyRosettaMCPServer** | relax_structure, compute_ddg, compute_binding_energy, flexpep_dock, fast_design, energy_decomposition, interface_analysis | lazy `pyrosetta.init()` |
| **FoldMasonMCPServer** | compute_lddt_matrix | lDDT pairwise 유사도 |

---

## 6. PyRosetta Flow Pipeline (Silo B)

`pyrosetta_flow/` — Silo B 전용 실행 엔진. **FULLY OPERATIONAL**.

### 6.1 모듈 구성

| 모듈 | 역할 |
|------|------|
| **runner.py** (~995 lines) | 메인 루프: baseline refinement → iteration (planner→mutate→dock→QC→critic→reporter). ThreadPoolExecutor 병렬 FlexPepDock |
| **schema.py** | `FlowConfig` (17 파라미터), `CandidateResult`, `IterationSummary`, `FlowArtifacts` dataclass |
| **ranking.py** | JSONL experiment_log.jsonl 관리: append, load, extract_historical, summarize_top_hits, build_historical_candidates |
| **convergence.py** | Mann-Whitney U 검정 (scipy 비의존, 수동 rank-sum) + CV 계산. 양 조건 충족 시 수렴 판정 |
| **bandit.py** | Thompson Sampling 위치 최적화: Beta(alpha, beta) 사전분포, ddG 개선 시 alpha++, 악화 시 beta++ |
| **adapter.py** | `generate_random_mutant()`, `generate_guided_mutant()`, `validate_config()`, `choose_objective_mode()`, `get_bandit_guidance()` |

### 6.2 FlowConfig 주요 파라미터

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `original_sequence` | `AGCKNFFWKTFTSC` | SST-14 native 서열 |
| `design_positions` | [1,2,4,5,6,7,8,9,10,11,12,14] | 돌연변이 가능 위치 (Cys3/Cys14 제외) |
| `n_candidates` | 8 | iteration당 후보 수 |
| `max_iterations` | 2 | 최대 반복 횟수 |
| `top_k` | 5 | 상위 선발 수 |
| `max_parallel_workers` | 4 | 병렬 FlexPepDock 프로세스 수 |
| `validation_n_trials` | 1 | 다중 시행 검증 (10=논문 표준) |
| `validation_early_stop_cv` | 0.15 | early stopping CV 임계값 |
| `convergence_window_size` | 3 | Mann-Whitney U 윈도우 |
| `bandit_n_focus` | 3 | Thompson sampling 포커스 위치 수 |

### 6.3 실행 흐름

```
run_pyrosetta_agentic_mutdock_flow(config)
│
├─ Baseline Refinement (n_baseline_trials, best-of-N)
│
└─ Iteration Loop (max_iterations)
   ├─ PlannerAgent.execute() → 가설 + focus_positions
   ├─ Mutation Generation
   │   ├─ Bandit-guided: Thompson sampling top-3 positions
   │   └─ Random fallback: 1-3 random mutations (dedup 50회 시도)
   ├─ FlexPepDock (ThreadPoolExecutor, max_parallel_workers)
   │   └─ subprocess: conda bio-tools → flexpep_dock.py
   ├─ QCRankerAgent → ddG ≤ -5.0 gate + composite ranking
   ├─ ConvergenceDetector → Mann-Whitney U + CV < 0.15
   ├─ ScientistCriticAgent → 실패 분석 + 파라미터 제안
   ├─ ReporterAgent → PyMOL 4-panel + Markdown
   ├─ StatusEmitter → /tmp/ag_pipeline_status.json → dashboard
   └─ JSONL append (experiment_log.jsonl)
```

---

## 7. Test Coverage

### 7.1 pyrosetta_flow (Backend Python)

118 tests, 93% coverage, 7 test files + conftest.

| 파일 | 테스트 수 | 대상 |
|------|----------|------|
| `test_adapter.py` | 25 | 돌연변이 생성, config 검증 |
| `test_bandit.py` | 21 | Thompson sampling, arm 갱신, 초기화 |
| `test_convergence.py` | 20 | Mann-Whitney U, CV, 수렴 탐지 |
| `test_ranking.py` | 21 | JSONL I/O, 랭킹 집계 |
| `test_runner_helpers.py` | 11 | helper 함수 (_resolve_conda_python 등) |
| `test_runner_integration.py` | 8 | FlowConfig, runner 통합 |
| `test_schema.py` | 12 | dataclass 직렬화, FlowArtifacts.to_dict() |

### 7.2 Frontend (Vitest + RTL)

4 test files, 36 test cases.

| 파일 | 테스트 수 | 대상 |
|------|----------|------|
| `useSelection.test.ts` | 8 | 선택 상태 관리 |
| `useCandidateSort.test.ts` | 9 | 정렬/필터/페이지네이션 |
| `useValidation.test.ts` | 8 | 검증 API 호출 |
| `CandidateTable.test.tsx` | 11 | 테이블 렌더링 + 인터랙션 |

### 7.3 CI/CD

`.github/workflows/ci.yml` — 7 jobs 전체 통과 (2026-03-05).

| Job | 대상 |
|-----|------|
| 1 | Python lint (flake8) |
| 2 | BioNeMo 의존성 체크 |
| 3 | PDB/CIF 파일 검증 |
| 4 | 문서 정합성 |
| 5 | NIM smoke test |
| 6 | Frontend (ESLint + Vitest) |
| 7 | ai4sci-kaeri (pytest + coverage) |

---

## 8. 기존 문서 요약

| 문서 | 내용 |
|------|------|
| **README.md** (356 lines) | 프로젝트 개요, 듀얼 사일로, 6 scoring metrics, 13 약리학 속성, 프로젝트 구조, Quick start |
| **ARCHITECTURE.md** (571 lines) | 듀얼 파이프라인 설계서 (Production). Silo A vs B 비교, 5 공유 에이전트, 상태 지속, 출력 구조 |
| **ARCHITECTURE_V2.md** (352 lines) | 3-ARM 통합 설계서 (Pre-implementation). PipelineRegistry, ProcessManager, NIMEndpointResolver, 4 Phase 로드맵 |
| **QUICKSTART.md** (270 lines) | 실행 가이드. Prerequisites, Backend/Frontend/Silo B CLI 실행법, 6 대시보드 페이지, 파라미터 설명 |
| **UI_GUIDE.md** (1440 lines) | Web UI 운영 매뉴얼. 12 패널 상세 설명, 17 검증 기준, 12 API 엔드포인트, 10 트러블슈팅 섹션 |
| **TODO.md** (125 lines) | 상태 트래커. 완료 항목 (CI/CD, refactoring, tests), 남은 항목 (3-ARM 통합, wet-lab 제안, Combined 탭) |
