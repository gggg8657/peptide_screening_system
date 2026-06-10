# Architecture — SSTR2 AI Co-Scientist Dual Pipeline

**Date**: 2026-03-04
**Author**: planner (daily-review team)
**Status**: M7 설계 문서 (TODO.md M7)

---

## 1. Overview

이 프로젝트는 SSTR2 (Somatostatin Receptor Type 2) 표적 방사성의약품 후보를 설계하는
듀얼 파이프라인 시스템이다. 두 파이프라인은 동일한 목표(SSTR2-binding peptide 최적화)를
다른 전략으로 접근한다.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    SSTR2 AI Co-Scientist System                      │
├──────────────────────────────┬───────────────────────────────────────┤
│  Silo A: 3-ARM Full Pipeline │  Silo B: Mutation Simulation          │
│  (AG_src/pipeline)            │  (pyrosetta_flow)                     │
│                               │                                       │
│  De novo backbone design      │  SST-14 guided mutation               │
│  8 NVIDIA NIM APIs            │  Local PyRosetta only                 │
│  8-step + selectivity         │  2-step: mutate → dock                │
│  PipelineOrchestrator class   │  run_pyrosetta_agentic_mutdock_flow() │
├──────────────────────────────┴───────────────────────────────────────┤
│                      Shared Components                                │
│  AG_src/agents (Planner, Critic, Reporter, QC&Ranker)                 │
│  AG_src/llm (LLM provider)                                           │
│  AG_src/scripts/flexpep_dock.py                                       │
│  backend/status_emitter.py (Dashboard bridge)                         │
│  backend/ (FastAPI) + frontend/ (React/Vite)                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Silo A: AG_src/pipeline — 8-Step Full NIM API Pipeline

### 2.1 Purpose

De novo 바인더 백본 설계부터 시작하여 시퀀스 설계, QC, 도킹, Rosetta 정제,
선택성 스크리닝, 분석까지 전 과정을 자동화하는 full pipeline.
NVIDIA NIM 클라우드 API 의존적이며, 3-ARM virtual screening (Silo A) 역할을 한다.

### 2.2 Architecture

```
Orchestrator (orchestrator.py)
│
├── Planner Agent  ─── hypothesis / parameter updates
│
├── Builder ── Step01: Receptor prep (OpenFold3 NIM / fallback PDB)
│           ── Step02: Backbone generation (RFdiffusion NIM)
│           ── Step03: Sequence design (ProteinMPNN NIM)
│           ── Step03b: BLOSUM62 text-level mutation (Approach B, 로컬)
│           ── Step04: Fast QC (ESMFold NIM → pLDDT gate)
│           ── Step05: Docking (DiffDock + Boltz-2 NIM)
│           ── Step05b: Selectivity screening (off-target SSTR1/3/4/5)
│           ── Step06: Rosetta refinement (PyRosetta FlexPepDock, 로컬)
│           ── Step07: Analysis (FoldMason lDDT, PyMOL renders)
│           ── Step08: Stability prediction (반감기 예측)
│
├── QC & Ranker Agent ── multi-gate (pLDDT, dock, rosetta, selectivity)
├── Diversity Manager ── structural diversity enforcement
├── Critic Agent ───── proposed changes for next iteration
└── Reporter Agent ── iteration report, lab notebook
```

### 2.3 External API Dependencies

| API | Step | Purpose | Fallback |
|-----|------|---------|----------|
| OpenFold3 | Step01 | 수용체 구조 예측 | data/ PDB fallback |
| RFdiffusion | Step02 | De novo 백본 설계 | - |
| ProteinMPNN | Step03 | 역폴딩 (백본→시퀀스) | - |
| ESMFold | Step04 | 빠른 구조 예측 QC | - |
| DiffDock | Step05 | 분자 도킹 | Boltz-2 fallback |
| Boltz-2 | Step05 | 복합체 구조+친화도 | DiffDock fallback |
| ESM2 | Aux | 단백질 임베딩 | - |
| MolMIM | Aux | 소분자 생성 | - |

### 2.4 Config System

YAML 기반 3개 설정 파일:
- `AG_src/config/pipeline_config.yaml` — 전체 파이프라인 설정
- `AG_src/config/gate_thresholds.yaml` — QC 게이트 임계값
- `AG_src/config/tool_registry.yaml` — 도구 레지스트리 (API/MCP/Library)

### 2.5 Data Schemas

`AG_src/schemas/io_schemas.py`에 Step별 입출력 스키마:
- Step01Output → Step02Output → Step03Output → Step03bOutput
- Step04Output (QCResult) → Step05Output (DockingResult)
- Step05bOutput (SelectivityResult) → Step06Output (RosettaResult)
- Step07Output → RankTableRow, IterationRecord

### 2.6 State Persistence

- JSON 체크포인트: 각 step 후 상태 저장 → 재개 가능 (`--resume`)
- 수렴 검출: ddG delta + patience counter (config-based)

---

## 3. Silo B: pyrosetta_flow — 2-Step Mutation→Dock Pipeline

### 3.1 Purpose

SST-14 (AGCKNFFWKTFTSC) 참조 펩타이드의 변이체를 생성하고 PyRosetta FlexPepDock으로
정제/평가하는 경량 파이프라인. 외부 API 의존 없이 로컬 PyRosetta만 사용.
대시보드 연동이 완전히 구현된 현재 메인 실행 경로이다.

### 3.2 Architecture

```
run_pyrosetta_agentic_mutdock_flow(config: FlowConfig)
│
├── Baseline refinement (best-of-N trials)
│
└── Iteration loop (max_iterations):
    │
    ├── Planner Agent ── hypothesis, mutation guidance
    │
    ├── Mutate step:
    │   ├── Guided mutation (Planner focus_positions + Thompson Sampling bandit)
    │   └── Random mutation (fallback, dedup-aware)
    │
    ├── Dock step:
    │   ├── FlexPepDock refinement (ThreadPoolExecutor, parallel)
    │   └── ddG / total_score / clash_score extraction
    │
    ├── QC & Ranker Agent ── ddG gate + ranking
    ├── Convergence Detector ── Mann-Whitney U + CV threshold
    ├── Critic Agent ── analysis + proposed changes
    ├── Reporter Agent ── iteration artifacts
    │
    └── StatusEmitter ── real-time dashboard updates
```

### 3.3 Modules

| Module | 역할 | 줄 수 |
|--------|------|-------|
| `runner.py` | 메인 실행 함수, 전체 오케스트레이션 | ~860 |
| `adapter.py` | mutation 생성, config 검증, bandit 연동 | ~130 |
| `schema.py` | FlowConfig, CandidateResult, FlowArtifacts | ~110 |
| `convergence.py` | Mann-Whitney U 수렴 검출 | ~144 |
| `bandit.py` | Thompson Sampling 위치 최적화 | ~100 |
| `ranking.py` | JSONL 실험 로그, 히스토리 관리 | ~80 |

### 3.4 Config System

Python dataclass 기반 `FlowConfig`:
```python
@dataclass
class FlowConfig:
    template_pdb: str
    original_sequence: str = "AGCKNFFWKTFTSC"
    design_positions: List[int]  # mutable positions (1-indexed)
    n_candidates: int = 8
    max_iterations: int = 2
    conda_env: str = "bio-tools"
    script_timeout: int = 300
    n_baseline_trials: int = 3
    convergence_window_size: int = 3
    convergence_significance: float = 0.05
    bandit_n_focus: int = 3
    max_dedup_trials: int = 50
    # ... 17 total parameters
```

### 3.5 Dashboard Integration

StatusEmitter를 통한 실시간 대시보드 업데이트:
- `set_iteration()`, `set_candidates()`, `set_baseline()`
- Rosetta sub-step tracking (prepare → mutate → refine → score → qc → critic → reporter)
- `append_timeline_event()` — iteration 타임라인 시각화
- `set_convergence()` — 수렴 상태 표시
- `_save_archive()` — 완료 시 PDB 포함 아카이브 저장

### 3.6 Unique Features

1. **Thompson Sampling Bandit**: 히스토리 기반 위치 선택 최적화
2. **Cross-run Dedup**: 이전 실행의 시퀀스를 참조하여 중복 방지
3. **Fail-open**: 베이스라인 실패 시에도 iteration 계속
4. **Guided Mutation**: Planner → focus_positions + suggested_mutations
5. **ConvergenceDetector**: Mann-Whitney U test (no scipy dependency)

---

## 4. Shared Components

### 4.1 Agent System (AG_src/agents/)

| Agent | Type | 역할 | 사용처 |
|-------|------|------|--------|
| PlannerAgent | LLM | 가설 생성, 파라미터 업데이트 | A + B |
| ScientistCriticAgent | LLM | 결과 분석, 변경 제안 (max 2) | A + B |
| ReporterAgent | LLM | 보고서 작성, 실험 기록 | A + B |
| QCRankerAgent | Code | multi-gate QC, 후보 랭킹 | A + B |
| DiversityManagerAgent | Code | 구조 다양성 보장 | A only |

### 4.2 StatusEmitter (backend/status_emitter.py)

파이프라인 → 대시보드 브릿지. JSON 파일 기반 상태 공유.
- `fcntl.flock()` 기반 안전한 병렬 쓰기 (C5 fix)
- 아카이브 관리 (PDB 복사 포함, L4 fix)
- Rosetta sub-step tracking (7-step)
- 현재 **Silo B만** 연동. Silo A는 자체 state persistence 사용.

### 4.3 FlexPepDock Script (AG_src/scripts/flexpep_dock.py)

PyRosetta FlexPepDock을 subprocess로 실행하는 공통 스크립트.
- `--protocol flexpep_refine`
- `--target-sequence` 옵션으로 mutation 적용
- JSON 출력 (ddg, total_score, clash_score)
- timeout 보호 (C3 fix)

### 4.4 LLM Provider (AG_src/llm/)

- Ollama (qwen3:8b 기본), OpenAI-compatible API 지원
- `create_provider(config)` — 설정 기반 프로바이더 생성
- `LLM_MODEL` 환경변수 / `--llm-model` CLI 오버라이드

---

## 5. Key Architectural Differences

| Aspect | Silo A (AG_src/pipeline) | Silo B (pyrosetta_flow) |
|--------|--------------------------|-------------------------|
| **Approach** | De novo backbone design | Known peptide mutation |
| **API Dependency** | 8 NVIDIA NIM APIs | None (local only) |
| **Candidate Source** | ProteinMPNN 역폴딩 | SST-14 random/guided mutation |
| **QC Methods** | pLDDT + dock + rosetta + selectivity | ddG only |
| **Config Format** | YAML files | Python dataclass |
| **Dashboard** | No StatusEmitter | Full StatusEmitter |
| **State Persistence** | JSON checkpoint per step | JSONL experiment log |
| **Convergence** | ddG delta + patience | Mann-Whitney U + CV |
| **Parallel Execution** | Sequential steps | ThreadPoolExecutor for docking |
| **Test Coverage** | AG_src/tests (10 files) | 118 tests, 93% coverage |
| **실행 상태** | API 키 필요, 부분 구현 | 완전 동작 (메인 경로) |

---

## 6. Integration Design — Toward 3-ARM Unified Pipeline

### 6.1 Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   UnifiedPipelineRunner                       │
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │  CommonFlowConfig    │  │  CommonStatusEmitter         │  │
│  │  (base config class) │  │  (extended StatusEmitter)    │  │
│  └──────────┬───────────┘  └──────────┬───────────────────┘  │
│             │                          │                      │
│  ┌──────────┴───────────┐             │                      │
│  │  CommonCandidate     │             │                      │
│  │  (unified result)    │             │                      │
│  └──────────┬───────────┘             │                      │
│             │                          │                      │
│  ┌──────────┴──────────────────────────┴──────────────────┐  │
│  │                  PipelineStep (ABC)                      │  │
│  │  execute(config, input) -> StepOutput                    │  │
│  │  validate(input) -> bool                                 │  │
│  │  emit_status(emitter) -> None                            │  │
│  └──────────┬──────────────────────────┬──────────────────┘  │
│             │                          │                      │
│  ┌──────────┴───────────┐   ┌──────────┴───────────────┐    │
│  │  Silo A Steps        │   │  Silo B Steps            │    │
│  │  (NIM API pipeline)  │   │  (PyRosetta mutation)    │    │
│  └──────────────────────┘   └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Common Interfaces

#### 6.2.1 CommonFlowConfig (Base Config)

두 config 시스템을 통합하는 base dataclass:

```python
@dataclass
class CommonFlowConfig:
    """Base configuration shared by all pipeline silos."""
    # Identity
    run_id: str
    silo: str                      # "silo_a" | "silo_b" | "unified"

    # Target
    target_receptor: str = "SSTR2"
    reference_sequence: str = "AGCKNFFWKTFTSC"

    # Iteration control
    max_iterations: int = 5
    convergence_window: int = 3
    convergence_threshold: float = 0.05

    # Execution
    conda_env: str = "bio-tools"
    max_parallel_workers: int = 4
    script_timeout: int = 300

    # LLM
    llm_model: str | None = None

    # Output
    output_dir: str = "runs/"
```

Silo-specific config은 이를 상속:
```python
@dataclass
class SiloAConfig(CommonFlowConfig):
    """Silo A: NIM API pipeline specific config."""
    silo: str = "silo_a"
    nim_api_key: str | None = None
    n_backbone: int = 10
    k_seq_per_backbone: int = 8
    gate_thresholds: Dict[str, Any] = field(default_factory=dict)
    off_target_receptors: List[str] = field(default_factory=list)

@dataclass
class SiloBConfig(CommonFlowConfig):
    """Silo B: PyRosetta mutation specific config."""
    silo: str = "silo_b"
    template_pdb: str = ""
    design_positions: List[int] = field(default_factory=list)
    n_candidates: int = 8
    n_baseline_trials: int = 3
    bandit_n_focus: int = 3
```

#### 6.2.2 CommonCandidate (Unified Result Schema)

```python
@dataclass
class CommonCandidate:
    """Unified candidate result across silos."""
    candidate_id: str
    sequence: str
    source_silo: str           # "silo_a" | "silo_b"
    iteration: int

    # Core metrics (all pipelines produce these)
    ddg: float                 # ΔΔG binding energy (primary metric)
    total_score: float         # Rosetta total score
    clash_score: float         # Steric clash score

    # Extended metrics (Silo A only, optional)
    plddt_mean: float = 0.0
    plddt_interface: float = 0.0
    dock_score: float = 0.0
    selectivity_margin: float = 0.0
    lddt: float = 0.0

    # Status
    selected: bool = False
    fail_reason: str = ""
    pdb_path: str = ""
```

#### 6.2.3 PipelineStep (Abstract Base)

```python
from abc import ABC, abstractmethod

class PipelineStep(ABC):
    """Abstract pipeline step interface."""

    @property
    @abstractmethod
    def step_id(self) -> str:
        """Step identifier (e.g., 'step01', 'mutate', 'refine')."""
        ...

    @abstractmethod
    def execute(self, config: CommonFlowConfig, input_data: Any) -> StepOutput:
        """Execute this step and return output."""
        ...

    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Validate step input before execution."""
        ...

    def emit_status(self, emitter: StatusEmitter, status: str, message: str = "") -> None:
        """Emit step status to dashboard."""
        emitter.update_step(self.step_id, status)
        if message:
            emitter.append_timeline_event(0, self.step_id, status, message)
```

#### 6.2.4 Common StatusEmitter Extensions

현재 StatusEmitter는 이미 양쪽에서 사용 가능하나, Silo A는 아직 연동하지 않았다.
통합 시 필요한 확장:

```python
class StatusEmitter:
    # 기존 메서드 유지 + 확장

    def set_active_silo(self, silo: str) -> None:
        """Dashboard에 현재 활성 silo 표시."""
        self._state["active_silo"] = silo
        self.flush()

    def set_silo_progress(self, silo: str, step: str, progress: float) -> None:
        """Silo별 진행률 표시 (0.0 ~ 1.0)."""
        silo_progress = self._state.setdefault("silo_progress", {})
        silo_progress.setdefault(silo, {})[step] = progress
        self.flush()
```

### 6.3 Experiment Log Unification

현재 두 시스템의 실험 로그 형식이 다르다:

| 항목 | Silo A | Silo B |
|------|--------|--------|
| 형식 | JSON checkpoint per iteration | JSONL per candidate |
| 위치 | `runs/{run_id}/state.json` | `runs/pyrosetta_flow/experiment_log.jsonl` |
| 필드 | StepResult, IterationResult | candidate record (run_id, ddg, sequence...) |

통합 방향: **JSONL을 공통 형식으로 채택** (Silo B 방식)
- record_type: "candidate" | "iteration_summary" | "step_result"
- source_silo: "silo_a" | "silo_b"
- 공통 필드: run_id, iteration, sequence, ddg, timestamp

### 6.4 3-ARM Dashboard Integration

```
┌──────────────────────────────────────────────┐
│            Unified Dashboard                  │
│                                               │
│  ┌─────────────┐  ┌───────────────────────┐  │
│  │ Silo Tabs   │  │ Combined Ranking      │  │
│  │ [A] [B] [*] │  │ All candidates,       │  │
│  └─────────────┘  │ color by source silo  │  │
│                    └───────────────────────┘  │
│  ┌───────────────────────────────────────┐   │
│  │ Step Progress (silo-specific)         │   │
│  │ A: ■■■■□□□□ Step05/Step08            │   │
│  │ B: ■■■■■■■□ iter 7/8                 │   │
│  └───────────────────────────────────────┘   │
│  ┌───────────────────────────────────────┐   │
│  │ Convergence (shared graph)            │   │
│  │ ─── Silo A  ─── Silo B               │   │
│  └───────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

---

## 7. Migration Strategy

### Phase 1: Interface Extraction (이번 세션)
1. `CommonFlowConfig` base class 정의
2. `CommonCandidate` 스키마 정의
3. Silo B의 `FlowConfig` → `SiloBConfig(CommonFlowConfig)` 상속으로 변경
4. 기존 동작 유지 (backward compatible)

### Phase 2: StatusEmitter 통합 (다음 세션)
1. Silo A orchestrator에 StatusEmitter 연동
2. `set_active_silo()`, `set_silo_progress()` 확장
3. 프론트엔드에 silo 탭 추가

### Phase 3: Unified Dashboard (이후)
1. Combined ranking table (양 silo 후보 통합 비교)
2. Convergence overlay graph
3. Cross-silo candidate comparison view

### Phase 4: 3-ARM Pipeline Runner (장기)
1. `UnifiedPipelineRunner`: Silo A + B 순차/병렬 실행
2. Cross-silo 후보 교환 (Silo A 상위 → Silo B refinement, 또는 역방향)
3. 통합 QC gate (양쪽 결과 종합 평가)

---

## 8. File Map

```
ai4sci-kaeri/
├── AG_src/                          # Silo A 코드
│   ├── agents/                      # 공유 에이전트 (5개)
│   │   ├── planner.py               #   LLM 기반 가설 생성
│   │   ├── critic.py                #   LLM 기반 결과 분석
│   │   ├── reporter.py              #   LLM 기반 보고서
│   │   ├── qc_ranker.py             #   Code 기반 QC+랭킹
│   │   └── diversity_manager.py     #   Code 기반 다양성 관리
│   ├── pipeline/                    # Silo A 8-step 파이프라인
│   │   ├── orchestrator.py          #   PipelineOrchestrator (~1400줄)
│   │   ├── step01_receptor.py       #   OpenFold3 NIM / fallback
│   │   ├── step02_backbone.py       #   RFdiffusion NIM
│   │   ├── step03_sequence.py       #   ProteinMPNN NIM
│   │   ├── step03b_blosum_mutation.py #  BLOSUM62 text mutation
│   │   ├── step04_qc.py            #   ESMFold NIM QC
│   │   ├── step05_docking.py        #   DiffDock + Boltz-2 NIM
│   │   ├── step05b_selectivity.py   #   Off-target screening
│   │   ├── step06_rosetta.py        #   PyRosetta refinement
│   │   ├── step07_analysis.py       #   FoldMason + PyMOL
│   │   └── step08_stability.py      #   Half-life prediction
│   ├── clients/                     # API 클라이언트
│   │   └── nim_client.py            #   NVIDIA NIM REST client
│   ├── tools/                       # MCP 서버 + API 도구
│   │   ├── api/                     #   NIM API 래퍼 (7개)
│   │   └── mcp/                     #   PyRosetta/FoldMason/PyMOL 서버
│   ├── schemas/                     # I/O 스키마
│   │   ├── io_schemas.py            #   Step별 입출력 dataclass
│   │   ├── rank_table.py            #   RankTable 스키마
│   │   └── lab_notebook.py          #   실험 노트 스키마
│   ├── llm/                         # LLM 프로바이더
│   │   ├── provider.py              #   Ollama/OpenAI compatible
│   │   └── prompts.py               #   에이전트 프롬프트
│   ├── config/                      # YAML 설정
│   │   ├── pipeline_config.yaml     #   전체 파이프라인 설정
│   │   ├── gate_thresholds.yaml     #   QC 게이트 임계값
│   │   └── tool_registry.yaml       #   도구 레지스트리
│   ├── scripts/                     # 실행 스크립트
│   │   ├── flexpep_dock.py          #   FlexPepDock 래퍼 (공유)
│   │   ├── fast_design.py           #   FastDesign 래퍼
│   │   └── offtarget_dock.py        #   Off-target 도킹
│   └── tests/                       # AG_src 테스트 (10개)
│
├── pyrosetta_flow/                  # Silo B 코드
│   ├── runner.py                    #   메인 실행 (~860줄)
│   ├── adapter.py                   #   mutation 생성, config 검증
│   ├── schema.py                    #   FlowConfig, CandidateResult
│   ├── convergence.py               #   Mann-Whitney U 수렴 검출
│   ├── bandit.py                    #   Thompson Sampling 위치 최적화
│   ├── ranking.py                   #   JSONL 실험 로그
│   └── tests/                       #   118 tests, 93% coverage
│
├── backend/                         # FastAPI 서버
│   ├── main.py                      #   create_app() factory
│   ├── state.py                     #   공유 상태/경로
│   ├── status_emitter.py            #   파이프라인→대시보드 브릿지
│   ├── validation_facade.py         #   통합 검증 (H5)
│   └── routers/                     #   6개 라우터
│       ├── status.py                #     /api/status, /api/runs
│       ├── analysis.py              #     /api/analysis/*
│       ├── validation.py            #     /api/validate/*
│       ├── experiment.py            #     /api/experiment/*
│       ├── admet.py                 #     /api/admet/*
│       └── static.py                #     /api/structures, /api/images
│
├── frontend/                        # React/Vite 대시보드
│   └── src/
│       ├── components/              #   12개 컴포넌트
│       ├── hooks/                   #   5개 커스텀 훅
│       └── contexts/                #   PipelineContext
│
└── runs/pyrosetta_flow/             # 실행 결과
    ├── experiment_log.jsonl         #   실험 로그
    └── archives/                    #   PDB 포함 아카이브
```

---

## 9. Design Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | JSONL을 공통 실험 로그 형식으로 | Append-only, 스트리밍 친화적, Silo B에서 검증됨 |
| D2 | StatusEmitter를 공통 브릿지로 | 이미 동작 중, fcntl.flock 안전, 아카이브 지원 |
| D3 | CommonFlowConfig 상속 패턴 | 기존 코드 최소 변경, 하위 호환성 유지 |
| D4 | PipelineStep ABC 도입 | Step 수준 교환 가능성 (Silo A Step06 = Silo B Dock) |
| D5 | 공통 에이전트 계층 유지 | 이미 양쪽에서 사용 중, LLM provider 공유 |
| D6 | Phase별 점진적 통합 | Big-bang 리팩토링 위험 방지, 각 phase 독립 배포 가능 |
