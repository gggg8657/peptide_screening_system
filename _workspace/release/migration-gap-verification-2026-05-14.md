# Migration Gap 검증 보고서 — 2026-05-14

> **범위**: PRST_N_FM 마이그레이션 대비 Gap A(컴포넌트 흡수)·Gap B(신규 BE 데이터 소스) 코드 리드 기반 검증.  
> **전제**: prototype JSX 6종은 디자인 레퍼런스; 실제 구현은 미포함. 코드 변경 없음.

**관련 문서**: `_workspace/release/migration-gap-analysis-2026-05-14.md`  
**프로토타입**: `docs/design-handoff-2026-05-14/prototype/{variant_a,variant_b,variant_c,screen_launcher,screen_benchmark,screen_wetlab}.jsx`  
**신규 BE 스텁**: `docs/design-handoff-2026-05-14/backend/routers/*.py`

---

## 1. Gap A 확정 — 컴포넌트 흡수 (FULL / PARTIAL / NONE)

화면 약어: **A**=`variant_a` (Run Console), **B**=`variant_b` (Selectivity), **C**=`variant_c` (Candidate Review), **D**=`screen_launcher`, **E**=`screen_benchmark`, **W**=`screen_wetlab`.

| # | 컴포넌트 | 표시·입력 데이터 (코드 근거) | 프로토타입 대응 | 흡수 |
|---|----------|------------------------------|-----------------|------|
| 1 | **PharmacologyPanel** | `/api/pharmacology/batch` 기반 GRAVY, Boman, II, 프로테아제, 방사분해 취약점, Blosum, 금속 배위 등 다층 약리 지표 (`PharmacologyPanel.tsx`) | **C** ADMET·안정성 바 일부; **W** in-silico 표는 iPTM/Ki 중심 | **PARTIAL** |
| 2 | **ValidationPanel** | 통합 검증 API 응답: 게이트별 PASS/CAUTION/FAIL, 그룹(pharmacological/radiopharmaceutical/statistical), 임계값·설명 (`ValidationPanel.tsx`) | **A** `RightDetail`의 Gate trail + 칩(개수 요약); **D** 게이트 슬라이더는 *설정* | **PARTIAL** (판정·모달 디테일 미흡) |
| 3 | **RiskMatrix** | 확률×영향 매트릭스, P0–P3, mock `RISK_ITEMS` (`RiskMatrix.tsx`) | 해당 UI 없음 | **NONE** |
| 4 | **CandidateCompareModal** | 2–3명 후보 side-by-side, 서열 diff, iPTM·안정성·ddG·프로테아제 등 비교 행 (`CandidateCompareModal.tsx`) | **C** `SeqDiff` 다중 행(비모달); **A** 테이블 선택 단일 디테일 | **PARTIAL** |
| 5 | **ClusterPanel** | FoldMason/A–E 클러스터 분류, 분포, criteria (`ClusterPanel.tsx`) | 파이프라인 스텝 텍스트에 "Cluster" 언급·로그 문구만 (`data.js`); 전용 패널 없음 | **NONE** |
| 6 | **MutationAnalysis** | 위치별 변이 빈도, 보수/비보수, FWKT 보존, ddG scatter (`MutationAnalysis.tsx`) | 동등 차트 없음 | **NONE** |
| 7 | **PositionEnrichment** | 위치별 Top AA 빈도·평균 ddG 테이블 (`PositionEnrichment.tsx`) | 동등 테이블 없음 | **NONE** |
| 8 | **SARHeatmap** | AA×위치 돌연변이 빈도 히트맵 (`SARHeatmap.tsx`) | **B** 히트맵은 *후보×SSTR iPTM* (다른 축) | **NONE** |
| 9 | **SequenceLogo** | 정보 이론 기반 로고 스택 (`SequenceLogo.tsx`) | **shared.jsx** `Sequence`는 ruler/diff용 | **NONE** |
| 10 | **AgentFlowDiagram** | 논문 Fig.1형 순환 다이어그램, Agent·Rosetta substep 연동 (`AgentFlowDiagram.tsx`) | **A** `PipelineFlow` + **C** `AgentLine` 목록 (다른 정보 구조) | **PARTIAL** |
| 11 | **RunComparisonPanel** | 아카이브 run 목록: 시작 시각, 상태, iter, 후보 수, best ΔG, 트렌드 (`RunComparisonPanel.tsx`) | 없음 | **NONE** |
| 12 | **LoopTimeline** | iteration별 stage 트리, refine 자식 후보 (`LoopTimeline.tsx`) | **A** agent log 스트립(다른 그라뉼러리티) | **NONE** |
| 13 | **DdGDistribution** | ddG 히스토그램, -5 kcal/mol 기준선 (`DdGDistribution.tsx`) | **B** `MarginPlot`은 *iPTM margin*; **A** 표에 ddG 컬럼만 | **NONE** |
| 14 | **RCSBMatchPanel** | 후보별 RCSB 검색 히트(PDB, identity, e-value) (`RCSBMatchPanel.tsx`) | **molstar_viewer.jsx**는 PDB 로드(동일성 검색 패널 아님) | **NONE** |
| 15 | **VisualizationPanel** | PyMOL 렌더 PNG 갤러리·라이트박스 (`VisualizationPanel.tsx`) | **C** Mol* 인터랙티브 (정적 타일 워크플로우 비등가) | **PARTIAL** |

**요약 카운트**: FULL 0 / PARTIAL 6 / NONE 9 — 레거시 고해상도 분석·리스크·런 비교·구조 검색는 신규 6 화면만으로는 **대부분 이월되지 않음**.

---

## 2. Gap A 권고 — NONE (및 PARTIAL 보강) 시 신규 화면 배치

| 컴포넌트 | 권고 배치 | 이유 |
|----------|-----------|------|
| RiskMatrix | **C (Candidate Review)** 하단 또는 "Risk / Governance" 접이 패널 | 후보 단위 의사결정 맥락; PI 리뷰와 인접 |
| ClusterPanel | **A (Run Console)** 파이프라인 Step 07 완료 후 패널 또는 **C** "Structure clusters" | FoldMason은 실행 흐름의 일부이나 후보 세그먼트 설명에도 유효 |
| MutationAnalysis, PositionEnrichment, SARHeatmap, SequenceLogo | **B** Selectivity 탭 확장 *또는* **C** "SAR / library" 서브섹션 | 동일 run의 서열 코호트 분석; **B**가 heatmap·필터 문화와 정합 |
| RunComparisonPanel | **D** Run Launcher 사이드바 또는 **A** 헤더 "Recent runs" | 새 실행 전·후 아카이브 비교 |
| LoopTimeline | **A** 메인 영역(파이프라인 옆/아래) | iter·refine 상태는 콘솔 실시간 모니터링과 정합 |
| DdGDistribution | **A** 미니 대시보드 또는 **B**와 병렬 "Score distributions" | ddG는 Silo B scoring 핵심 |
| RCSBMatchPanel | **C** (구조 탭 옆 "Homology / PDB hits") | Mol*와 같은 *구조 신뢰* 맥락 |
| CandidateCompareModal | **C** 명시 "Compare …" 모달로 유지 | PARTIAL → 기능 보존 가치 높음 |
| PharmacologyPanel | **C** "Pharmacology" 확장 (ADMET 바 옆) | PARTIAL → 배치 레이어 추가 |
| ValidationPanel | **C** 또는 **A** Gate trail을 BE 통합 검증과 연동 | PARTIAL → API 스키마만 맞추면 흡수 용이 |
| VisualizationPanel | 선택: 레거시 PNG가 필요하면 **C** "Static renders" 탭 | Mol*와 병존 가능 |

---

## 3. Gap B 데이터 소스 매핑 (실 검증)

검증 대상은 `docs/design-handoff-2026-05-14/backend/routers/` 스텁 및 기존 레포 경로.

| Endpoint / 기능 | 예상 (1차 분석) | **실 소스 (코드·워크스페이스 확인)** | 검증 결과 |
|-----------------|-----------------|----------------------------------------|----------|
| `GET /api/pipelines/{silo}` | `pipeline_local/config/*.yaml` | 스텁 **`pipelines.py`** 내 `SILO_A_STAGES_TEMPLATE` / `SILO_B_STAGES_TEMPLATE` 하드코딩; 선택적 `run_id`로 `runs_local/{run_id}/{step_dir}` 존재 여부만 hydrate. **YAML 미사용**. | 예상과 **불일치** — 템플릿+디렉터리 휴리스틱 |
| `GET /api/cand03_variants/list` | `runs_local/cand03_variants/cand03_variants.json` | 스텁 경로 동일. **현재 워크스페이스에 `runs_local` 및 `cand03_variants.json` 트리 없음** (글로브 0건) → 스텁은 **파일 없을 때 인메모리 fallback** (`cand03_variants.py`). | 파일 **미검증(부재)**; 로직은 존재 |
| `GET /api/runs/{run_id}/predicted_pass_rates` | `gate_thresholds.yaml` + 후보 통계 | 스텁 **`runs.py`** 는 **고정 `PredictedPassRatesResponse` 반환**, TODO만 "archives 누적". Launcher가 쓰는 임계값은 **POST `/start` 시 `req.gates` YAML**로 저장되나 **예측 계산과 무연결**. `pipeline_local/config/gate_thresholds.yaml` 키 예: `esmfold_plddt_min`, `docking_top_pct`, `rosetta_ddg_max`, `selectivity_margin_min`, `stability_prescreen_min_hours`, `gates_enabled.*` | **산출 미구현**; gate 파일은 별도로 실존 |
| `GET /api/agents/{run_id}/log` | agent 로그 | 스텁: `runs_local/{run_id}/silo_b/experiment_log.jsonl`, JSONL 필드 `agent`, `text`, optional `ts`, `level`. **기존 ai4sci-kaeri**: `backend/state.py` — `runs/pyrosetta_flow/experiment_log.jsonl` (경로 **다름**). | **경로 불일치** — 마이그레이션 시 단일 SSOT 정의 필요 |
| `POST /api/runs/start` | subprocess | **`runs.py`**: `run_dir` 생성, `00_config/pipeline_config_local.yaml` 작성, `BackgroundTasks`에서 `conda run -n bio-tools python -m pipeline_local.run_pipeline_local ...` **`subprocess.Popen`** (stdout `stdout.log`). 주석 `# TODO: conda run 또는 직접 모듈 호출`. | 패턴 있음; **안전성·모듈 존재·환경명** 별도 검증 |
| `GET /api/agents/{run_id}/stream` | SSE | **`agents.py`**: `StreamingResponse` + `text/event-stream`, in-memory `asyncio.Queue` 구독, 타임아웃 시 `: ping`. **파일 tail 미연결** — 실시간 이벤트는 `publish()` 호출 가정. | FastAPI SSE **가능**; 로그 파일과 **연동 TODO** |
| `GET /api/benchmark/results` | `llm_benchmark/` | 스텁: `llm_benchmark/analysis/{phase}_summary.json` (`phase` 소문자 파일명). **실제 코드베이스**: `llm_benchmark/scoring/aggregate.py` 의 데이터 루트는 **`llm_benchmark/outputs/{phase}/`** (run별 디렉터리, `status.json`, `ses_score.json`); 워크스페이스 `llm_benchmark/analysis/` 에는 유틸만 존재. | **경로·스키마 불일치**; `load_phase_results` 등 기존 집계와 매핑 필요 |
| `GET/PATCH /api/wetlab/orders` 등 | 신규 store | **`wetlab.py`**: `runs_local/wetlab_orders.json` JSON 파일, 주석 "실 운영은 DB 권장". 시드 시 파일 생성. | **JSON 단일 파일** (스텁 기준); SQLite 아님 |

### `gate_thresholds.yaml` (확인된 키 일부)

- 토글: `gates_enabled.plddt|docking|rosetta|selectivity|disulfide|stability_prescreen`
- 임계: `esmfold_plddt_min`, `esmfold_interface_plddt_min`, `docking_top_pct`, `rosetta_ddg_max`, `rosetta_clash_max`, `selectivity_margin_min`, `offtarget_max_allowed`, `foldmason_lddt_min`, `stability_prescreen_min_hours`, `final_score_weights.*`

→ **predicted_pass_rates**를 이 파일과 후보 집계에 엄밀히 연결하려면 스텁 외 **별도 구현**이 필요.

---

## 4. 마이그레이션 PR 분해 권고 (우선순위)

| 순위 | 작업 단위 | 포함 내용 | 비고 |
|------|-----------|-----------|------|
| P0 | BE 스텁 통합 + 경로 SSOT | `experiment_log.jsonl` 실경로, `runs_local` vs `runs/pyrosetta` 합의; `wetlab_orders.json` 위치 | FE 깨짐 방지 |
| P0 | `cand03_variants.json` 데이터 공급 | 레포에 샘플 커밋 또는 생성 스크립트; 스키마를 `Cand03Variant`와 정합 | 현재 워크스페이스 부재 |
| P1 | `benchmark` 라우터 | `llm_benchmark/outputs` + `aggregate.load_phase_results` 재사용, 스텁 JSON 형식 폐기 또는 어댑터 | 경로 불일치 해소 |
| P1 | `pipelines` | 문서화: "YAML 아님" 또는 `gate_thresholds`/silo yaml과의 동기 옵션 | 디자인 기대치 조정 |
| P2 | `predicted_pass_rates` | 아카이브 run + 후보 메트릭 집계 또는 단순 히스토리컬 | 비즈니스 로직 |
| P2 | `runs/start` 하드닝 | 작업 디렉터리, 타임아웃, 단일 인스턴스 락, allowlist | 보안·운영 |
| P2 | `agents/stream` + 파일 tail | SSE + `aiofiles` tail 또는 watcher → `publish` | 실시간 정합 |
| P3 | FE: NONE 컴포넌트 슬롯 | §2 표에 따른 탭/모달 이식 우선순위 | Gap A 클로저 |

---

## 5. 미해결 — 사용자 결정 필요

1. **에이전트 로그 단일 경로**: `runs_local/{run_id}/silo_b/experiment_log.jsonl` (스텁) vs `runs/pyrosetta_flow/experiment_log.jsonl` (현행 BE) 통합 방식.
2. **리스크 매트릭스·RCSB 패널**을 primary UI에 포함할지(규제/데이터 요구).
3. **PyMOL 정적 타일**과 Mol*의 장기 병행 여부(VisualizationPanel 유지 vs 폐기).
4. **Wetlab 저장소**: 스텁 JSON 유지 vs SQLite/외부 구매 시스템.
5. **벤치마크 Phase 명명**: 스텁 `Phase1|V2` vs 실제 `outputs` 디렉터리 명 규칙 정렬.
6. **predicted_pass_rates**: 히스토리컬 추정 vs 단순 UI mock 유지 기간.

---

## 6. 핵심 결론 (1–2줄)

- **Gap A**: 신규 6 JSX는 런 콘솔·셀렉티비티·후보 리뷰·런처·벤치마크·웹랩의 **주요 워크플로우는 포괄**하지만, SAR/클러스터/런 비교/RCSB/리스크/ΔG 분포 등 **레거시 9개 컴포넌트는 흡수되지 않았고** 6개는 **부분 흡수**에 그침.  
- **Gap B**: 스텁은 `pipelines`(YAML 아님), `benchmark`(outputs 경로 불일치), `agents`(로그 경로 불일치), `cand03`(데이터 파일 부재 시 fallback), `predicted_pass_rates`(미구현)에서 **1차 분석 가정과 어긋난 부분**이 확인됨; 통합 전 SSOT·경로·스키마 정렬이 선행 과제.

---

**작성**: Cursor 에이전트 (코드 리드 전용, 수정 없음)  
**날짜**: 2026-05-14
