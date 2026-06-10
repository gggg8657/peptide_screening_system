# TODO: NIM Full-Pipeline Integration

> Status: **Planning** | Created: 2026-02-28 | Updated: 2026-03-04
>
> 현재 UI에서는 PyRosetta-only 모드(Silo B)만 연결됨.
> NIM API를 사용하는 전체 3-arm 파이프라인(Silo A, steps 01-09)을 UI에 통합하기 위한 계획.
>
> **참조**: [ARCHITECTURE.md](ARCHITECTURE.md) — 듀얼 파이프라인 설계 문서 (Silo A vs Silo B)

---

## 아키텍처 개요

이 프로젝트는 **듀얼 파이프라인** 구조로 운영된다:

| Silo | 경로 | 설명 | 상태 |
|------|------|------|------|
| **Silo A** (3-ARM) | `AG_src/pipeline/` | De novo backbone → 8 NIM API steps | 코드 완료, UI 미연결 |
| **Silo B** (Mutation) | `pyrosetta_flow/` | SST-14 guided mutation → PyRosetta dock | ✅ UI 연결, 운영 중 |

> NIM API는 **클라우드 엔드포인트** (health.api.nvidia.com)를 사용한다. Docker 컨테이너 불필요 — NGC API 키만 있으면 호출 가능.

---

## 현재 상태 (As-Is)

| 구분 | 구현 상태 | UI 연결 |
|------|----------|---------|
| `pyrosetta_flow/runner.py` (Silo B, PyRosetta-only) | ✅ 완료 (118 tests, 93% cov) | ✅ 연결됨 |
| `AG_src/pipeline/orchestrator.py` (Silo A, Full pipeline) | ✅ 완료 | ❌ 미연결 |
| NIM Tool Wrappers (`AG_src/tools/api/`) | ✅ 8개 구현 | ❌ 미연결 |
| Step01-08 (`AG_src/pipeline/step*.py`) | ✅ 완료 | ❌ 미연결 |
| Step09 MolMIM | ⚠️ Tool만 있음 | ❌ 미연결 |
| Dashboard (React/Vite) | ✅ 12 components, 6 hooks, 32 tests | ✅ Silo B 연결 |
| Backend (FastAPI) | ✅ 리팩토링 완료 | ✅ Silo B 연결 |

### 구현된 NIM Tool Wrappers
- `esmfold_tool.py` — ESMFold 구조 예측
- `rfdiffusion_tool.py` — RFdiffusion backbone 생성
- `proteinmpnn_tool.py` — ProteinMPNN 서열 디자인
- `diffdock_tool.py` — DiffDock 도킹
- `boltz2_tool.py` — Boltz-2 도킹
- `molmim_tool.py` — MolMIM 소분자 생성
- `openfold3_tool.py` — OpenFold3 구조 예측
- `esm2_tool.py` — ESM-2 임베딩

### 구현된 Pipeline Steps
- `step01_receptor.py` — Receptor preparation (PDB fetch & clean)
- `step02_backbone.py` — Backbone generation (RFdiffusion NIM)
- `step03_sequence.py` — Sequence design (ProteinMPNN NIM)
- `step03b_blosum_mutation.py` — BLOSUM mutation fallback
- `step04_qc.py` — Fast QC (ESMFold pLDDT check)
- `step05_docking.py` — Docking (DiffDock + Boltz-2)
- `step05b_selectivity.py` — Selectivity filter (SSTR5 counter-screen)
- `step06_rosetta.py` — Rosetta refinement (FlexPepDock)
- `step07_analysis.py` — Analysis & visualization
- `step08_stability.py` — Stability prediction

---

## Phase 1: Backend — Full Pipeline ↔ StatusEmitter 연결

### 1.1 Orchestrator에 StatusEmitter 통합
- [ ] `AG_src/pipeline/orchestrator.py`에 `StatusEmitter` import 및 초기화
- [ ] 각 step 실행 전후로 `start_step()` / `complete_step()` 호출 추가
- [ ] Step별 substep 정의 (step02: RFdiffusion → ProteinMPNN 등)
- [ ] Agent 상태 (planner, builder, qc-ranker, critic, reporter) emit

### 1.2 Pipeline Mode 분기
- [ ] `api_server.py`의 `/api/experiment/run`에서 `pipeline_mode` 파라미터 추가
  - `pyrosetta_only` — 현재 `pyrosetta_flow/runner.py` 사용
  - `full_nim` — `AG_src/pipeline/orchestrator.py` 사용
- [ ] Frontend에서 mode 선택 UI 추가

### 1.3 NIM API Key 관리
- [ ] `/api/nim/health` 엔드포인트 — 각 NIM 서비스 연결 확인
- [ ] Frontend 설정 패널에서 API key 입력/검증
- [ ] `NGC_API_KEY` 환경변수 or config file 지원

### 1.4 Step09 MolMIM 통합
- [ ] `AG_src/pipeline/step09_molmim.py` 생성 — MolMIM 도구 래핑
- [ ] Orchestrator에 step09 호출 로직 추가
- [ ] 소분자 리드 최적화 결과를 candidates에 연결

---

## Phase 2: Frontend — Full Pipeline UI

### 2.1 Pipeline Mode 선택
- [ ] 실험 시작 다이얼로그에 Mode Toggle 추가 (PyRosetta-only / Full NIM)
- [ ] Full NIM 선택 시 NIM API 연결 상태 표시
- [ ] Mode에 따라 step 카드 수 조정 (5-step vs 9-step)

### 2.2 PipelineStatus 확장
- [ ] Full mode: step01~step09 표시 (현재 step01~step08만 정의)
- [ ] 각 step의 substep 표시 (예: step05 = DiffDock → Boltz-2)
- [ ] NIM API 호출 상태 실시간 표시 (esmfold, rfdiffusion 등)

### 2.3 AgentFlowDiagram 확장
- [ ] Full mode용 node 배치 추가 (Builder 노드 활성화)
- [ ] Step01-05 진행 시 해당 NIM 서비스 노드 활성화
- [ ] Step간 데이터 흐름 시각화

### 2.4 Visualization Panel
- [ ] `step07_analysis.py` 결과 이미지 표시
  - Ramachandran plot, contact map, ddG landscape 등
- [ ] `runs/<run_id>/figures/` 경로에서 이미지 서빙
- [ ] `/api/structures/` 엔드포인트로 step별 PDB 서빙

### 2.5 Live API Status
- [ ] `usePipelineStatus` hook에서 NIM API 상태 파싱
- [ ] Dashboard 상단에 API health indicator 표시
- [ ] 실패 시 fallback 경로 안내 (예: ESMFold 실패 → local ColabFold)

---

## Phase 3: 고급 기능

### 3.1 Resume / Checkpoint
- [ ] Orchestrator의 checkpoint JSON을 UI에서 로드
- [ ] 중단된 실험 재개 버튼
- [ ] Step 단위 재실행 (특정 step만 다시 돌리기)

### 3.2 Multi-Target 지원
- [ ] SSTR2 외 다른 receptor target 설정
- [ ] Step01에서 PDB ID 직접 입력 지원
- [ ] Target별 설정 프리셋

### 3.3 Hybrid Mode
- [ ] NIM + PyRosetta 혼합 모드
- [ ] NIM이 가용하지 않은 step은 local fallback 사용
- [ ] Step별 NIM/Local 선택 가능

---

## 우선순위

1. **Phase 1.1~1.2** — Backend 파이프라인 모드 분기 (핵심)
2. **Phase 1.3** — NIM API key 관리
3. **Phase 2.1~2.2** — Frontend mode 선택 및 step 표시
4. **Phase 2.3~2.4** — Flow diagram 및 시각화
5. **Phase 1.4** — MolMIM step 통합
6. **Phase 2.5, 3.x** — Live status, resume, multi-target
