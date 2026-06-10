# Migration Gap Analysis — Design Handoff 2026-05-14

> **목표**: `docs/design-handoff-2026-05-14/` (구 `design_handoff_sstr2_dashboard/`) 의 새 디자인으로 *마이그레이션*. 기존 인터페이스는 *중단* (사용 안 함), *삭제 X* (보존).
>
> **본 문서**: 마이그레이션 *전*에 식별해야 할 두 gap 분석:
> - **Gap A**: 기존에 *있는데* 새 버전에 *없는* 것 — 기능 손실 위험
> - **Gap B**: 새 버전이 *필요로 하는데* BE/FE 인프라에 *없는* 것 — 추가 구현 필수

---

## 0. 마이그레이션 전제 (사용자 결정)

- 기존 UI/페이지/컴포넌트는 *코드 보존* (삭제 X), *라우트 비활성화* (사용 X)
- 신규 디자인이 *primary* UI
- BE는 신규 endpoint 9건 추가 + 기존 6개 응답 shape 조정

---

## 1. 인벤토리 (현재 vs 신규)

### 1.1 기존 FE 페이지 (6)
| 페이지 | 역할 | 신규 매핑 |
|--------|------|----------|
| AboutPage | 프로젝트 소개·docs 링크 | **Gap A** (신규 디자인 누락) |
| CombinedPage | Silo A+B 결합 뷰 | A Run Console (silo=A+B 토글) |
| SelectivityPage | Selectivity 행렬 | B Selectivity Explorer (교체) |
| SettingsPage | 환경·임계값 | D Run Launcher (gate 부분 흡수), 나머지 **Gap A** |
| SiloAPage | Silo A 모니터 | A Run Console (silo=A) |
| SiloBPage | Silo B 모니터 + ADMET + Validation | A Run Console (silo=B) + **부분 Gap A** |

### 1.2 기존 FE 컴포넌트 (30+)
*사용 추적 + 신규 매핑*:

| 컴포넌트 | 사용 페이지 | 신규 디자인 매핑 | 상태 |
|----------|-------------|----------------|------|
| PipelineStatus | Silo A/B + Combined | A Run Console | 흡수 (PipelineFlow 컴포넌트) |
| AgentMonitor | Silo A/B + Combined | A Run Console (agent log) | 흡수 |
| CandidateTable | Silo A/B | A/B/C 화면 표 | 흡수 |
| QCGateChart | Silo A/B | A Run Console gate 패널 | 흡수 |
| ConvergenceGraph | Silo A/B | A Run Console | 흡수 |
| ExperimentControl | Combined + Silo A | D Run Launcher | 흡수 |
| HeuristicBanner | Selectivity | B (HEURISTIC disclaimer) | 흡수 |
| ArchivesTopKSlider | Selectivity | B | 흡수 |
| **PharmacologyPanel** | SiloB | ❓ | **Gap A 후보** |
| **ValidationPanel** | SiloB | ❓ | **Gap A 후보** |
| **RiskMatrix** | SiloB | C Candidate Review? | **Gap A 후보** |
| **ADMETPanel** | (별도) | C Candidate Review (ADMET) | 흡수 |
| **AgentFlowDiagram** | (별도) | A Run Console PipelineFlow와 중복? | **Gap A 후보** |
| **CandidateCompareModal** | (별도) | C Candidate Review? | **Gap A 후보** |
| **ClusterPanel** | (별도) | ❓ (FoldMason cluster) | **Gap A 후보** |
| **DdGDistribution** | (별도) | A 또는 C? | **Gap A 후보** |
| **LoopTimeline** | (별도) | A Run Console timeline? | **Gap A 후보** |
| **MoleculeViewer** | (별도) | C Candidate Review Molstar로 교체 | 흡수 (Molstar) |
| **MutationAnalysis** | (별도) | C Candidate Review? | **Gap A 후보** |
| **PositionEnrichment** | (별도) | C Candidate Review? | **Gap A 후보** |
| **RCSBMatchPanel** | (별도) | C? | **Gap A 후보** |
| **RunComparisonPanel** | (별도) | ❓ | **Gap A 후보** |
| **SARHeatmap** | (별도) | C Candidate Review SAR? | **Gap A 후보** |
| **SequenceLogo** | (별도) | C Candidate Review? | **Gap A 후보** |
| **VisualizationPanel** | (별도) | C Candidate Review? | **Gap A 후보** |
| **PlaceholderState** | Combined | ❓ (loading 상태) | 흡수 가능 |
| **MutationAnalysis** | (별도) | C? | **Gap A 후보** |

→ **Gap A 후보 15+ 컴포넌트** — 신규 디자인이 *명시적으로* 흡수했는지 *각 화면별 컨테이너* 분석 필요.

### 1.3 기존 BE 라우터 (12)
| 라우터 | endpoint 수 | 신규 디자인 활용 |
|--------|-----------|-----------------|
| admet | 3 | ✅ (/api/admet/{seq_id}) — 응답 shape 조정 |
| analysis | 8 | 부분 (rank table 등) — 매핑 확인 필요 |
| cluster | 1 | ✅ (/api/cluster/{run_id}) |
| experiment | 6 | ✅ (/api/experiment/{run_id}/candidates) — 응답 shape 조정 |
| rcsb | 1 | (검색 용도) — 신규 디자인 미명시 |
| selectivity | 8 | ✅ (/api/selectivity/{run_id} + run) |
| settings | 2 | ✅ (/api/settings GET/PATCH) |
| stability | 5 | (PR #20+#23 후) — 신규 디자인에 등장 |
| static | 2 | (정적 파일) — 유지 |
| status | 5 | ✅ (/api/status) — 응답 shape 조정 |
| validation | 5 | ❓ — 신규 디자인 미명시 |

### 1.4 design_handoff 신규 BE (6 stub 파일, 8개 router)
- `agents.py` — log REST + SSE stream
- `pipelines.py` — silo별 파이프라인 구조
- `cand03_variants.py` — 변이체 카탈로그
- `runs.py` — runs/start + predicted_pass_rates
- `benchmark.py` — LLM 5 모델 × 3 flow 결과
- `wetlab.py` — orders CRUD + 상태 머신

→ 모두 *마운트만* 하면 됨 (codex 위임 가능).

### 1.5 design_handoff 신규 FE (5 컴포넌트 + 1 hook + tokens + theme store)
- `Sequence.tsx` — 시퀀스 ruler + diff
- `TierBadge.tsx` — T0~T3 색상 표시
- `HeatmapCell.tsx` — 셀 (iPTM/selectivity)
- `Molstar.tsx` — 3D viewer (npm `molstar` 사용)
- `PipelineFlow.tsx` — 파이프라인 다이어그램
- `dashboard.ts` — 15 hooks (모든 화면용)

### 1.6 신규 디자인 6 화면 ↔ 15 hooks 매핑

| 화면 | hooks 사용 |
|------|-----------|
| A Run Console | `useRunStatus`, `useAgentLog`, `usePipeline` |
| B Selectivity Explorer | `useSelectivity`, `useCandidates` |
| C Candidate Review | `useCandidates`, `useADMET`, `useCand03Variants` |
| D Run Launcher | `useSettings`, `useUpdateSettings`, `useStartRun`, `usePredictedPassRates` |
| E LLM Benchmark | `useBenchmark` |
| F Wetlab Order | `useWetlabOrders`, `useWetlabOrder`, `useTransitionWetlabOrder` |

---

## 2. Gap A — 기존에 있는데 신규에 없는 것 (기능 손실 위험)

### A-1 페이지·기능
- **AboutPage**: 프로젝트 정보 페이지 — 신규 디자인 누락 → 신규에서 메뉴 또는 footer link로 보존 가능
- **SettingsPage의 일부**: gate 임계값은 D Run Launcher에 흡수, *그 외* 환경 설정 (예: ollama host, vLLM port, conda env 등)은 명시 없음 — 신규에 별도 설정 페이지 또는 launcher 확장 필요

### A-2 컴포넌트 (15+ Gap A 후보)
*각 컴포넌트가 신규 화면 컨테이너에 흡수됐는지 cursor-agent로 검증 필요*. 우선순위:

| 우선순위 | 컴포넌트 | 추정 흡수처 | 검증 방법 |
|----------|---------|-----------|----------|
| HIGH | PharmacologyPanel | C Candidate Review | 신규 prototype에 pharmacology 데이터 표시 있는지 |
| HIGH | ValidationPanel | C Candidate Review | 신규 prototype validation 패널 있는지 |
| HIGH | RiskMatrix | C Candidate Review | 신규 prototype risk 표시 있는지 |
| MED | CandidateCompareModal | C Candidate Review | 두 후보 비교 기능 흡수 |
| MED | ClusterPanel | A 또는 B | FoldMason cluster 표시 |
| MED | MutationAnalysis / PositionEnrichment / SARHeatmap | C Candidate Review | SAR 분석 흡수 |
| MED | SequenceLogo | C Candidate Review | 시퀀스 로고 흡수 |
| LOW | AgentFlowDiagram | A Run Console (PipelineFlow 중복?) | 다이어그램 두 종류면 중복 |
| LOW | RunComparisonPanel | (Run 비교 — 신규 명시 없음) | 신규 화면에 비교 기능 부재 |
| LOW | LoopTimeline | A Run Console timeline | iteration history 흡수 |
| LOW | DdGDistribution | A 또는 C | 분포 차트 흡수 |
| LOW | RCSBMatchPanel | C? 또는 별도 | RCSB 매칭 기능 보존 |

**조치**: cursor-agent 위임으로 신규 prototype 각 화면을 *데이터별로* 분석 → 흡수 여부 매핑

### A-3 BE 라우터
- **validation** (5 endpoints): 신규 디자인 명시 없음 → 어디로 매핑되는지 확인
- **rcsb** (1 endpoint): 검색 기능 — 신규에서 활용 안 하면 비활성화

---

## 3. Gap B — 새 버전이 필요로 하는데 BE에 없는 것 (추가 구현 필수)

### B-1 신규 BE Endpoint 9건 (구현 필요)

handoff의 backend/routers/ 가 *stub*으로 제공 — *복사 + import 조정* 만으로 가동 가능.

| Endpoint | 라우터 stub | 데이터 source | 구현 난이도 |
|----------|------------|--------------|------------|
| `/api/pipelines/{silo}` | pipelines.py | 정적 구조 (config 기반) | **Low** |
| `/api/cand03_variants/list` | cand03_variants.py | `runs_local/cand03_variants/cand03_variants.json` | **Low** |
| `/api/runs/{run_id}/predicted_pass_rates` | runs.py | 통계 계산 (gate 임계값 + 후보 메트릭) | **Med** |
| `/api/agents/{run_id}/log` | agents.py | `_workspace/release/...` agent 로그 | **Med** |
| `/api/runs/start` | runs.py | 파이프라인 실행 (subprocess) | **High** (실행 트리거) |
| `/api/agents/{run_id}/stream` (SSE) | agents.py | SSE 구현 | **High** (FastAPI SSE) |
| `/api/benchmark/results` | benchmark.py | `llm_benchmark/` 결과 | **Med** |
| `/api/wetlab/orders` (CRUD) | wetlab.py | 신규 SQLite 또는 JSON 파일 store | **Med** |
| `/api/wetlab/orders/{id}/transition` | wetlab.py | 상태 머신 (Draft→Submitted→Approved→...) | **Med** |

### B-2 기존 Endpoint 응답 shape 조정 (6건)
| Endpoint | 변경 | 영향도 |
|----------|------|-------|
| `/api/status` | 신규 dashboard 형식 (silo, run_id, iteration, gates) | Med |
| `/api/experiment/{run_id}/candidates` | data.js 의 candidates 배열 형식 | Med |
| `/api/selectivity/{run_id}` | boltz_summary.json 형식 유지 (기존 동일) | Low |
| `/api/cluster/{run_id}` | 기존 응답 유지 | None |
| `/api/admet/{seq_id}` | 기존 응답 + design hook 형식 | Low |
| `/api/settings` / PATCH | 기존 형식 유지 (gate keys 확장) | Low |

→ **기존 FE 보존* 결정으로 *legacy 호환* 불필요 (사용자 결정). BE 응답 *완전 교체* 가능.

### B-3 FE 의존성 추가
- `npm install molstar @tanstack/react-query zustand clsx`
- Tailwind v4 `@theme` 블록 (tokens.css)
- Google Fonts: Inter + JetBrains Mono
- Vite config proxy: `/api → 127.0.0.1:8787`

### B-4 데이터 source 가능 여부
- `cand03_variants.json` ✅ 있음 (`runs_local/cand03_variants/`)
- `selectivity` ✅ 기존 `boltz_summary.json`
- `predicted_pass_rates` ⚠️ 신규 계산 로직 필요
- `agent log` ⚠️ 현재 로그 형식과 매칭 확인 필요
- `benchmark results` ⚠️ `llm_benchmark/` 결과 형식 매핑 필요
- `wetlab orders` ❌ 신규 데이터 store 필요 (SQLite or JSON)

---

## 4. 마이그레이션 제약 (사용자 결정)

- 기존 FE 라우트는 *제거* 안 함 (`/about`, `/silo-a`, `/silo-b`, `/selectivity`, `/settings`)
- App.tsx에 신규 라우트 추가:
  - `/` → 신규 Run Console로 redirect (기존 `/silo-b` redirect 교체)
  - `/console`, `/selectivity-explorer`, `/candidate/:id`, `/run/new`, `/benchmark`, `/wetlab/orders`
- 메뉴는 신규 6 화면만 노출 (기존 페이지는 *URL 직접 입력*으로만 접근 가능)
- 기존 페이지 코드 *유지* (참조 자료 + 잠재적 fallback)

---

## 5. 다음 단계 권고

### 5.1 즉시 (본 세션)
- ✅ `docs/design-handoff-2026-05-14/` 이동 (완료)
- ⏳ cursor-agent 위임 — Gap A 검증 (각 컴포넌트가 신규 화면에 흡수됐는지 prototype JSX 분석)
- ⏳ cursor-agent 위임 — Gap B 정확 데이터 source 매핑

### 5.2 단기 (codex 위임 PR)
1. **BE 신규 라우터 마운트** (1 PR) — handoff/backend/* → ai4sci-kaeri/backend/routers/ 복사 + main.py mount
2. **FE 디자인 토큰 + theme** (1 PR) — Tailwind v4 + tokens.css + theme.ts
3. **FE 공통 컴포넌트** (1 PR) — Sequence/TierBadge/HeatmapCell/Molstar/PipelineFlow
4. **FE 페이지 6개** (6 PR 또는 2-3 PR로 그룹화)
5. **라우팅 통합** (1 PR) — App.tsx 신규 라우트 + 기존 라우트 보존
6. **E2E 테스트** — Playwright

### 5.3 중기 (1-2주)
- 모든 6 화면 dogfood
- 신규 라우트 default로 전환
- 기존 라우트는 *deprecated* 표시 (코드 보존)

---

## 6. 미해결·확인 필요

| ID | 항목 | 확인 방법 |
|----|------|----------|
| ? | 15+ 컴포넌트 Gap A 매핑 | cursor-agent 위임 |
| ? | `runs/start` BE 구현 (실행 트리거) | 보안·sandbox 설계 필요 (subprocess 위험) |
| ? | `agents/stream` SSE 구현 | FastAPI SSE 패턴 + 현재 로그 source 어떻게 stream으로 |
| ? | `wetlab/orders` 데이터 store | SQLite vs JSON file vs 외부 system |
| ? | `validation` 라우터 매핑 | 신규 디자인 어디서 사용? |
| ? | `rcsb` 라우터 | 비활성화 가능? |
| ? | 기존 페이지 코드 보존 — *영구* or *N개월 후 삭제*? | 사용자 결정 |

---

**작성**: orchestrator (1차 인벤토리)
**다음 단계**: cursor-agent 위임으로 Gap A 컴포넌트별 흡수 매핑 검증
