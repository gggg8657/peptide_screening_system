# Integration Checklist · SSTR2 Dashboard → SST14-M_scr

> 실제 통합 작업 시 체크리스트. 위에서 아래로 순서대로 진행.

## Phase 0 · 사전 준비 (30분)

- [ ] `design_handoff_sstr2_dashboard/` 전체를 SST14-M_scr 리포 루트에 복사
- [ ] `prototype/SSTR2 Dashboard.html` 을 브라우저에서 열어 디자인 + 인터랙션 확인
- [ ] `README.md` + `API_CONTRACT.md` + `FRONTEND_INTEGRATION.md` 읽기
- [ ] backend conda env (`bio-tools`) 활성 확인 — `uvicorn` 가동 가능해야 함
- [ ] frontend (`ai4sci-kaeri/frontend/`) `npm install` 정상 작동 확인

## Phase 1 · Quick preview (1시간)

빠르게 팀에 보여주고 피드백 받기.

- [ ] `cp -r prototype/ ai4sci-kaeri/frontend/public/prototype/`
- [ ] `App.tsx` 에 라우트 추가:
  ```tsx
  <Route path="/preview" element={
    <iframe src="/prototype/SSTR2 Dashboard.html" style={{ width: '100vw', height: '100vh', border: 0 }} />
  } />
  ```
- [ ] `npm run dev` 후 `http://localhost:5173/preview` 접속 확인
- [ ] PI / 팀에 공유 → 피드백 수집

## Phase 2 · Backend 라우터 마운트 (반나절)

- [ ] `backend/schemas.py` 를 `ai4sci-kaeri/backend/schemas/dashboard.py` 로 복사
- [ ] `backend/routers/*.py` 를 `ai4sci-kaeri/backend/routers/` 로 복사 (6개)
- [ ] `backend/main_patch.py` 참고하여 `backend/main.py` 에 마운트 코드 추가
- [ ] import 경로 조정 (`from ..schemas.dashboard` → 실제 경로)
- [ ] CORS 설정 확인 (vite dev 5173 → backend 8787)
- [ ] `uvicorn backend.main:app --reload` 가동 후 Swagger 확인:
  - `http://127.0.0.1:8787/docs` 에서 신규 6개 라우터 + 엔드포인트 확인
- [ ] 각 endpoint curl 테스트:
  ```bash
  curl http://127.0.0.1:8787/api/cand03_variants/list | jq
  curl http://127.0.0.1:8787/api/pipelines/B | jq
  curl http://127.0.0.1:8787/api/benchmark/results?phase=V2 | jq
  curl http://127.0.0.1:8787/api/wetlab/orders | jq
  curl http://127.0.0.1:8787/api/runs/local_20260512_1430_iter02/predicted_pass_rates | jq
  ```

## Phase 3 · Frontend 디자인 시스템 (반나절)

- [ ] `frontend/styles/tokens.css` 를 `ai4sci-kaeri/frontend/src/styles/tokens.css` 로 복사
- [ ] `src/index.css` 에서 import 추가 (`@import "./styles/tokens.css";`)
- [ ] Tailwind v4 `@theme` 블록에 토큰 등록 (`FRONTEND_INTEGRATION.md § 1` 참조)
- [ ] Google Fonts 로드 — `index.html` 에 `<link>` 추가:
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
  ```
- [ ] `frontend/stores/theme.ts` 복사 → `src/stores/theme.ts`
- [ ] `npm install zustand`
- [ ] `main.tsx` 에 첫 로드 시 theme 반영 코드 추가

## Phase 4 · 공통 컴포넌트 (1일)

- [ ] `frontend/components/*.tsx` (Sequence, TierBadge, HeatmapCell, Molstar, PipelineFlow) 복사
- [ ] `npm install clsx molstar @tanstack/react-query`
- [ ] `vite.config.ts` proxy 설정:
  ```ts
  server: { proxy: { '/api': 'http://127.0.0.1:8787' } }
  ```
- [ ] `App.tsx` 에 QueryClientProvider 감싸기
- [ ] `frontend/hooks/dashboard.ts` 복사 → `src/hooks/dashboard.ts`
- [ ] 각 hook 개별 import test (Storybook 또는 dev 페이지에서)

## Phase 5 · 페이지 포팅 (3-4일)

순서대로 진행.

### 5.1 Variant B — Selectivity Explorer (기존 페이지 교체)
- [ ] `prototype/variant_b.jsx` → `src/pages/SelectivityPage.tsx`
- [ ] `useSelectivity(runId)` + `useCandidates(runId)` 훅으로 데이터 교체
- [ ] `<HeatmapCell>` + `<Sequence>` 컴포넌트 활용
- [ ] 셀 클릭 시 우측 drawer 열기 + `<Molstar pdbUrl={...}>` 로 docked pose 로드
- [ ] tier 필터, WT 토글 동작 확인

### 5.2 Variant A — Run Console
- [ ] `prototype/variant_a.jsx` → `src/pages/RunConsolePage.tsx`
- [ ] `useRunStatus(runId)` + `usePipeline(silo, runId)` + `useAgentLog(runId)` 훅
- [ ] `<PipelineFlow silo={silo}>` 컴포넌트
- [ ] silo 토글 (A / B / A+B) 동작 확인
- [ ] SSE log 스트리밍 확인

### 5.3 Variant C — Candidate Review
- [ ] `prototype/variant_c.jsx` → `src/pages/CandidatePage.tsx`
- [ ] `useCandidates` + `useADMET(seqId)` + `useCand03Variants()` 훅
- [ ] `<Sequence>` diff, `<Molstar>` 3D, decision 패널
- [ ] approval 액션 → `useTransitionWetlabOrder` mutation

### 5.4 Screen D — Run Launcher
- [ ] `prototype/screen_launcher.jsx` → `src/pages/RunLauncherPage.tsx`
- [ ] `useSettings()` + `useUpdateSettings()` 훅으로 gate 값 sync
- [ ] `useStartRun()` mutation으로 실행 시작
- [ ] `usePredictedPassRates()` 로 예상 통과율

### 5.5 Screen E — LLM Benchmark
- [ ] `prototype/screen_benchmark.jsx` → `src/pages/BenchmarkPage.tsx`
- [ ] `useBenchmark(phase)` 훅
- [ ] phase 토글, metric 토글, 셀 hover 동작

### 5.6 Screen F — Wetlab Order
- [ ] `prototype/screen_wetlab.jsx` → `src/pages/WetlabOrderPage.tsx`
- [ ] `useWetlabOrder(orderId)` + `useTransitionWetlabOrder()`
- [ ] 상태 머신 토글 동작 확인

## Phase 6 · 라우팅 + 통합 (0.5일)

- [ ] `App.tsx` 에 라우트 추가 (`FRONTEND_INTEGRATION.md § 8` 참조)
- [ ] 기존 SiloAPage / SiloBPage → RunConsolePage 로 합쳐서 교체
- [ ] 기존 SelectivityPage 교체
- [ ] 메인 nav 메뉴 정리 (Home / Runs / Selectivity / Benchmark / Wetlab)

## Phase 7 · 통합 테스트 (1일)

- [ ] 전체 e2e flow 테스트:
  1. Run Launcher → 새 실행 시작 → Run Console 로 이동
  2. Run Console 에서 pipeline 진행 모니터링 + agent log 확인
  3. Selectivity 페이지에서 결과 확인
  4. 후보 클릭 → Candidate Review 페이지
  5. Wetlab Order 페이지에서 발주서 생성/승인
- [ ] Mol* 3D 모든 페이지에서 로드 확인 (RCSB 7XNA + 로컬 PDB)
- [ ] 라이트/다크 토글 전 페이지 확인
- [ ] 모바일 반응형은 우선순위 낮음 (1440px 이상 dev 화면 가정)

## Phase 8 · 운영 (continuous)

- [ ] 실제 agent process 에서 SSE publish 함수 호출 추가 (`agents.py` 참조):
  ```python
  from backend.routers.agents import publish
  await publish(run_id, {"event": "agent", "data": {...}})
  ```
- [ ] cand03_variants.json 실제 데이터 매핑 (`cand03_variants.py` TODO 부분)
- [ ] benchmark JSON 실제 데이터 매핑 (`benchmark.py` TODO 부분)
- [ ] runs/start subprocess 호출 검증 (`runs.py` _run_pipeline_subprocess)
- [ ] wetlab orders 영구 저장 (JSON → SQLite or Postgres)

## Stretch goals

- [ ] Tweaks 패널 (accent hue / density / font 라이브 조정) — `prototype/tweaks.jsx` 참조, prod 에서는 admin 전용 라우트 권장
- [ ] WebSocket 으로 SSE 대체 (양방향 control 필요 시)
- [ ] PDB diff view — variant 간 backbone overlay (Mol* 의 superposition API)
- [ ] CSV export — 후보 테이블 + selectivity 매트릭스
- [ ] Audit log — gate threshold 변경 이력
- [ ] i18n — Korean / English 토글

---

## 도움 요청 시 빠른 참조

- 디자인 questions → `prototype/SSTR2 Dashboard.html` 의 해당 variant 열어서 확인
- API shape questions → `API_CONTRACT.md`
- Tailwind / TSX 변환 questions → `FRONTEND_INTEGRATION.md`
- Backend stub 구조 questions → `backend/main_patch.py` + 각 router 파일 상단 주석
