# Phase 4 UI/UX 연동 분석 — 5/28 시연 준비

> 작성일: 2026-05-27 (D-1)
> 작성자: reviewer-uiux
> 입력: phase3-ui-ux-2026-05-27.md / be-p0-fix-2026-05-27.md / demo-scenario-2026-05-28.md / meeting-2026-05-28-narrative-v3.md / 프론트엔드·백엔드 소스 직접 검토
> 목적: Phase 3 보고서를 기준으로 FE-BE 연동 실태를 재검증하고, 5/28 시연에서 박사 청자가 화면에서 막힐 구체적 지점을 도출한다.

---

## 1. FE-BE 연동 문제 매트릭스 — Phase 3 재검증·확장

### 1.1 현재 상태 요약

Phase 3 보고서 이후 P0-A(`llm_benchmark` import 실패)는 수정 완료되었다(`be-p0-fix-2026-05-27.md`). 수정 결과:
- `/api/benchmark/results`는 라우트로 등록되어 있으나 호출 시 HTTP 503을 반환한다.
- 나머지 72개 경로는 정상 응답한다.
- P0-B(포트 false positive) 역시 `/api/health`에 `service: ai4sci-kaeri-backend` 식별자 추가로 해결되었다.

### 1.2 FE가 호출하지만 BE에 없는 endpoint

| endpoint | FE 호출 위치 | BE 확인 결과 | 현재 증상 |
|---------|------------|------------|---------|
| `GET /api/archives/top-k` | `ArchivesTopKSlider.tsx:96` | 라우터 파일 없음 | 에러 메시지 표시 (`HTTP 404`), mock 없음 — 빈 화면 |
| `GET /api/candidate/{id}/report` | `CandidatePage.tsx:82` | 라우터 파일 없음 | `<a download>` 클릭 시 브라우저 404 — UI 내 피드백 없음 |

**ArchivesTopKSlider 사용 위치 추가 확인**: `ManualSelectivityPage.tsx:159`, `SelectivityPage.tsx:316` 양쪽에서 사용된다. 즉 Manual Selectivity 페이지 진입 시 상단에 바로 에러 메시지가 뜬다.

**report download 위험**: `CandidatePage.tsx`는 `reportUrl`이 null이 아닌 경우 `<a href={reportUrl} download>` 앵커를 렌더링한다. `candidate`가 있으면 항상 `reportUrl`이 생성되므로, BE에 해당 엔드포인트가 없어도 "Report" 버튼이 항상 활성 상태로 보인다. 클릭 시 브라우저는 404 응답을 다운로드 시도 결과 빈 파일 또는 오류를 낸다. 화면에는 아무 표시가 없다.

### 1.3 BE에 있지만 FE primary flow에서 사용이 약한 endpoint

| 경로 네임스페이스 | 현황 | 시연 영향 |
|---------------|------|---------|
| `/api/analysis/*` | BE에 있음, FE에서 호출 미확인 | 시연 외 영향 없음 |
| `/api/stability/*` | BE에 있음, FE에서 호출 미확인 | 시연 외 영향 없음 |
| `/api/v1/silo-a/*` | BE에 있음, FE legacy route용 | 시연 경로 아님 |
| `/api/selectivity/structure/{receptor_name}` | BE에 있음, FE useSelectivity 훅이 사용하지 않음 | 선택됨 시 구조 로드 누락 가능성 |

### 1.4 `/api/benchmark/results` 503과 FE 행동

BE fix 후 BenchmarkPage는 503 응답을 수신한다. BenchmarkPage.tsx 코드(`lines 118-124`)를 직접 확인한 결과:

```
benchmarkQuery.isLoading → "Loading benchmark results…"
benchmarkQuery.isError   → "Failed to load benchmark results."   ← 503 수신 시 이 경로
rows.length === 0        → "No benchmark rows available for {phase}."
```

FE는 503을 `isError = true`로 처리하여 빨간색 텍스트 "Failed to load benchmark results."를 표시한다. 에러 원인(llm_benchmark 모듈 없음, 503 코드)은 화면에 나타나지 않는다. 박사 청자가 Benchmark 탭을 누르면 "로드 실패" 메시지만 보인다.

### 1.5 폴링 구조 및 race condition

- `usePipelineStatus` (App 레벨): 2초 간격 폴링 — `/api/status`, `/api/runs` 병렬 호출
- `useRunStatus` (페이지 레벨): 5초 간격 폴링 — `/api/status` 또는 `/api/runs/{run_id}`
- Agent log: SSE `EventSource` + 초기 한 번 fetch
- 두 훅 모두 `/api/status`를 호출하여 중복 폴링이 발생한다. 동일 코드베이스 주석(`usePipelineStatus.ts:239-245`)에도 이를 인지하고 있다. 시연 중 BE 부하 이슈는 낮지만 WebSocket이 없고 SSE 재연결 로직이 `es.onerror = () => setConnected(false)` 수준이어서 네트워크 끊김 복구는 수동 새로고침 필요.

---

## 2. 페이지별 사용자 시나리오 분석

박사 청자 기준: 화면을 처음 보고 "이 숫자가 무슨 뜻인가"를 즉시 파악할 수 있는가.

### 2.1 Run Console (`/console`)

**진입 시 보이는 것**: P* 로고, run_id, 상태 배지(Live/Mock/Archive), Silo A/B/A+B 전환, 진행도 바, PipelineFlow 다이어그램, 5개 MiniStat 카드, Candidates 테이블, Selected Candidate 패널, Agent Log.

**한 task 완료까지 필요한 조작**: run이 이미 선택되어 있으면 진입 즉시 후보 목록 확인 가능. 원하는 후보 행 클릭(1 click) → 오른쪽 패널에서 iPTM, margin, ddG 확인. 박사 Review 관점에서 2-3 click.

**박사 청자 혼동 가능성**:
- "iPTM"이 무엇인지 레이블 하나만으로 즉시 파악하기 어렵다. 헤더의 "step05c Boltz-2 + AF MSA · geometry-first review" 설명은 Run Console이 아닌 Selectivity Explorer에 있다. Run Console 내 Candidates 테이블 아래에는 iPTM 범례가 없다.
- "margin"이 "SSTR2 iPTM에서 최대 off-target iPTM을 뺀 값"임을 화면에서 직접 알 수 없다 (범례는 Selectivity Explorer 하단에 있음: "tier = SSTR2 − max(off-target) iPTM margin").
- "ddG" 컬럼: 단위 없음. 박사 청자 입장에서 단위(REU 또는 kcal/mol)와 방향(음수가 좋은가)을 알 수 없다.
- Silo A/B/A+B 토글: 현재 Silo B만 실질적으로 동작한다. A를 누르면 데이터가 없는 상태가 될 수 있다. 화면에서 "A는 비활성"임을 나타내는 표시가 없다.
- Run Console 하단 Gate Trail의 숫자(예: `04: QC G1 pass 42/1000`)는 in/out count인데, "어느 게이트가 무슨 조건으로 통과시키는지"가 클릭 호버만으로 보인다. 마우스 없이 화면을 스크롤로 보는 상황(발표 화면 공유)에서는 게이트 의미를 즉시 파악하기 어렵다.

**smoke test 실패 및 "more" button**: App.smoke.test.tsx가 `role="button" name=/more/i`를 기대하는데 현재 NAV_ITEMS는 `More` 버튼 없이 전체 11개 탭을 그대로 나열한다. "More" 드롭다운 메뉴는 코드에 존재하지 않는다. 테스트 기대가 이전 UI 설계를 반영하는 낡은 상태다. 이는 접근성 이름 회귀가 아니라 nav 설계 변경 후 테스트 미갱신이다.

### 2.2 Selectivity Explorer (`/selectivity-explorer`)

**진입 시 보이는 것**: iPTM 매트릭스 테이블, Tier 필터, WT toggle, Margin Distribution 차트, Gate Funnel, 오른쪽 Drawer(iPTM 수치, Docked Pose, 서열).

**박사 청자 혼동 가능성**:
- 배너 "iPTM ≠ Ki: 이 화면은 구조 geometry 기반 1차 필터입니다" — 적절하다. 이 배너는 이미 올바르게 배치되어 있다.
- Drawer의 "Docked Pose" 섹션: `<Molstar pdbUrl={selectedCandidate.poseUrl} height={220} />` 코드에서 `poseUrl`이 없으면 `pdbId`가 기본값 '7XNA'로 폴백한다. 화면에는 SSTR2 7XNA holo 구조가 표시되지만 "이 후보의 docked 구조"로 오해될 수 있다. "Reference PDB (7XNA) — candidate pose 없음" 표시가 없다. `SelectivityExplorerPage.tsx:390-427`의 `buildPoseUrl`은 `candidate.source` 없으면 `toStructureUrl(candidate.source)`를 반환하는데, source가 없을 경우 `undefined`가 되어 Molstar가 7XNA로 폴백한다.
- 매트릭스 최소 너비 `min-w-[980px]` — 발표 화면이 FHD 기준이면 가로 스크롤 없이 보이지만 1366px 이하 노트북에서는 스크롤 발생.

### 2.3 Candidate Review (`/candidate`)

**진입 시 보이는 것**: 후보 ID·서열·Tier 배지, Mol* 3D 구조, PDB 다운로드/Report 다운로드/Wetlab Ki approval 버튼, 서열 비교, 변이체 카탈로그, ADMET 패널, 결정 항목.

**박사 청자 혼동 가능성**:
- `BigStat label="iPTM(SSTR2)"`, `label="margin"`, `label="ddG"` 세 수치가 나란히 있다. ddG 단위가 없다. ADMET 섹션의 `label="GRAVY"`, `label="Boman index"`, `label="aggregation"`는 표준 ProtParam 용어지만 맥락 없이 나열된다. 특히 `GRAVY`는 펩타이드 분야 외 박사 청자에게 즉시 의미 전달이 어렵다.
- "Wetlab Ki approval" 버튼: 버튼 텍스트가 "Wetlab Ki approval"이다. 실제 동작은 wetlab order의 stage를 'approved'로 전환하는 것인데, 화면에서 "어떤 order를 승인하는지"는 옆의 order_id 입력 필드를 봐야 안다. 박사 청자가 실수로 누를 가능성이 있다.
- "Report" 버튼: 항상 활성화되어 있으나 BE에 해당 엔드포인트가 없다(`/api/candidate/{id}/report`는 router 미존재). 클릭 시 브라우저가 404 응답을 받아 빈 파일 또는 오류를 내고 화면에는 아무 피드백이 없다. **시연 중 박사 청자가 "Report"를 눌러보면 아무 일도 안 일어나는 것처럼 보인다.**
- 구조 패널: "구조 · candidate in SSTR2 (7XNA holo)" 제목은 7XNA가 수용체임을 나타내지만, candidate.source(docked PDB path)가 없을 경우 전체가 7XNA만 보인다. `Molstar pdbUrl={candidate.source ? toStructureUrl(candidate.source) : undefined} pdbId="7XNA"`이므로 source 없으면 수용체 단독 구조다.
- `contacts` 배열이 하드코딩(`K4/Asp137`, `W8/Phe294`, `F6/F7`, `T10/Gln138`)되어 선택된 후보와 무관하게 항상 동일하게 표시된다. 시연 시 PRST-001 외 후보를 선택해도 동일한 contact가 나오므로 후보별 분석처럼 오해될 수 있다.

### 2.4 Benchmark (`/benchmark`)

**진입 시**: "Failed to load benchmark results." 빨간 텍스트. 매트릭스 없음, 통계 카드 전부 0 또는 '—'.

**시연 영향**: BE fix로 503이 발생하므로 Benchmark 탭을 여는 순간 에러 화면이 나온다. 박사 청자가 이 탭을 보면 "시스템 고장"으로 인식할 수 있다. 에러 메시지가 원인을 설명하지 않으므로 시연자가 발화로 보완해야 한다.

### 2.5 Manual Selectivity (`/manual-selectivity`)

**진입 시**: ArchivesTopKSlider가 `/api/archives/top-k`를 호출하여 실패하면 "Archive API request failed" 에러 메시지가 상단에 표시된다(ArchivesTopKSlider.tsx:105-108). 그 아래 HeuristicBanner, 서열 입력, 수용체 선택, 설정, 실행 버튼이 있다.

**박사 청자 혼동**: 진입 즉시 에러 메시지가 보인다. 하지만 아래로 내리면 FlexPepDock 수동 실행 기능은 정상 동작 가능하다. 에러가 secondary feature 실패임을 화면에서 알 수 없다.

### 2.6 About (`/about`)

fetch 없음. 순수 정적 문서. 매우 많은 정보량이 단일 스크롤 페이지에 집중되어 있다. 발표 중 즉석 탐색에 적합하지 않으나, 사전에 특정 섹션 앵커를 준비하면 보완 가능하다.

---

## 3. 접근성·반응형 재검증

### 3.1 WCAG 2.1 AA 대비 관련 항목

**`text-[10px]` + `text-text-dim` 조합**: 10px 텍스트는 WCAG AA 기준 4.5:1 대비를 충족하기 위해 배경 대비가 충분해야 한다. `--text-dim` 토큰이 어두운 테마에서 충분한 대비를 제공하는지는 실제 측정 없이는 확인 불가. 특히 Benchmark 매트릭스 셀 내 `text-[10px]` 레이블, BenchmarkPage 하단 `source: /api/benchmark/results?phase={phase}` 문자열은 정보 전달 역할인데 10px에 dim 색조합이다.

**"more" button 접근성 회귀**: smoke test가 기대하는 `role="button" name=/more/i`가 실제 컴포넌트에 없다. 현재 NAV_ITEMS는 11개 탭을 일렬로 나열하며 "More" 드롭다운이 없다. 따라서 테스트 기대는 낡았다. 그러나 11개 탭이 좁은 화면에서 가로 overflow 없이 표시되는지는 별도 확인이 필요하다. `nav`에 overflow 처리가 없으므로 1280px 이하 화면에서 탭이 잘릴 수 있다.

**키보드 접근성**:
- Run Console candidates 테이블: 행이 `onClick`만 있고 `onKeyDown`/`role="row"`/`tabIndex`가 없다. 키보드로 후보를 선택할 수 없다.
- Selectivity Explorer heatmap 셀: `onClick` 핸들러 있음, keyboard 동치 미확인.
- Gate Trail: `<button>` 사용 — keyboard 접근 가능.

**aria 일관성**:
- 긍정: App 상태 배지 `role="status"` `aria-live="polite"`, Run selector `aria-expanded`/`aria-haspopup`, Binding Pocket form/tab.
- 결함: Candidate 테이블 행에 `role="row"` + `tabIndex` 없음. BenchmarkPage hover 세부 정보는 keyboard focus 동치 없음.

### 3.2 반응형

- `min-w-[980px]` (Selectivity iPTM 매트릭스), `min-w-[920px]` (Benchmark), `min-w-[980px]` (Run Console candidates) — 발표 화면이 1080p 이상이면 문제없으나 1366px 미만 노트북 화면 공유 시 가로 스크롤.
- Nav 11개 탭: 1440px에서 각 탭 px-3 py-2 기준 약 1100~1200px 폭 필요. 1440px에서는 ギリギリ 수준. 1280px 이하에서 탭 줄바꿈 또는 잘림 발생 가능.

---

## 4. 5/28 시연 시 박사 청자가 즉시 막힐 가능성 — Step별 분석

시연 시나리오(`demo-scenario-2026-05-28.md`) Step 1~5 기준.

### Step 1 — BE/FE 라이브 부팅 확인 (1분)

**화면**: FE `/console` 진입 — run_id가 없으면 "no run selected", 상태 배지 "Mock".

**위험**: 박사 청자가 "Mock"이라는 배지를 보고 "가짜 데이터를 보여주는 것 아닌가"라고 물을 수 있다. BE가 떠 있어도 run_id가 선택되지 않으면 Mock 상태로 보인다. 발화: "백엔드는 떠 있습니다. run_id를 선택해야 데이터가 로드됩니다."

**시연 대본으로 보완 가능**: 예, BE 터미널과 curl 결과로 "떠 있음"을 보여주면 된다.

### Step 2 — 기존 PRST 산출물 화면 시연 (2~3분)

**화면**: Candidate Page — PRST-001 선택 시 Mol* 구조, ADMET 패널, 변이체 카탈로그, "Wetlab Ki approval" 버튼, "Report" 버튼.

**위험 1 (High)**: "Report" 버튼이 활성화되어 보이는데 클릭하면 아무 일도 안 일어난다. 시연자가 버튼을 누르거나 박사 청자가 "저 버튼은 뭔가요"라고 물을 경우 노출된다.

**위험 2 (High)**: Mol* 구조가 PRST-001의 실제 docked 구조인지, SSTR2 reference 7XNA인지 화면에서 구분 불가. 박사 청자가 "이게 PRST-001이 결합한 구조인가요"라고 물으면 발화로 설명해야 한다.

**위험 3 (Medium)**: ADMET 패널의 GRAVY, Boman index, aggregation score 레이블. 가속기(방사선) 분야 박사에게는 이 지표들이 낯설 수 있다. 레이블 옆에 "(낮을수록 안정)" 등의 한 줄 설명이 없다.

**위험 4 (Low)**: 하드코딩된 contacts(`K4/Asp137` 등)가 모든 후보에서 동일하게 표시된다. 발표 중 여러 후보를 클릭할 때 contact가 바뀌지 않는 것을 박사 청자가 눈치챌 수 있다.

**발화 보완 가능 여부**: 위험 1, 2, 3 모두 발화로 설명 가능하나 시연 흐름이 끊길 수 있다. 위험 1은 버튼을 누르지 않는 것이 최선.

### Step 3 — Silo B PyRosetta 단건 라이브 (~10초)

**화면**: 별도 터미널. UI 화면과 직접 연결 없음.

**위험**: 없음(UI 기준). PyRosetta 환경 이슈는 UI/UX 범위 외.

### Step 4 — 한계 화면 표시 (2분)

**화면**: PPTX Slide 17 (코드 격차). UI 화면 아님.

**위험**: 없음(UI 기준).

### Step 5 — 슈뢰딩거 도입 검토 + 의사결정 요청 (3~4분)

**화면**: PPTX. UI 화면 아님.

**위험**: 없음(UI 기준).

---

## 5. 우선순위별 UX Fix

### P0 — 시연 전 즉시 수정 (오늘, 1~2시간 이내)

**P0-1: Candidate Page "Report" 버튼 비활성화 또는 상태 표시**

현재: `reportUrl`이 candidate만 있으면 항상 생성 → `<a download>` 항상 활성.
수정안: `reportUrl`에 대해 HEAD 또는 정적 확인을 하거나, 단순히 버튼을 disabled 처리하고 tooltip "report endpoint 준비 중"으로 바꾸기.
비용: `CandidatePage.tsx` 20줄 수정. 30분 이내.
위험: 없음. 현재 어차피 클릭해도 동작하지 않는다.
이득: 박사 청자가 클릭해도 아무 일이 없는 상황 차단.

구체적으로: `reportUrl && (...)` 블록에서 `<a>` 대신 `<button disabled title="준비 중">` 또는 `<a>` 에 `onClick={(e) => { e.preventDefault(); /* 피드백 없음 */ }}`을 제거하고 disabled 버튼으로 전환.

**P0-2: Mol* 패널에 "Reference PDB (7XNA) — candidate pose unavailable" 레이블 추가**

현재: `pdbUrl` 없으면 그냥 7XNA 로드, 화면에 표시 없음.
수정안: `SelectivityExplorerPage`의 Drawer와 `CandidatePage`의 구조 패널에서 `poseUrl/pdbUrl`이 없을 때 Mol* 뷰어 아래 또는 위에 `text-[10px] text-text-mute "reference fallback: 7XNA · candidate pose 없음"` 한 줄 추가.
비용: 각 컴포넌트 5줄 수정. 30~45분.
위험: 없음.
이득: 시연 시나리오 Step 2에서 "Mol* 3D는 후보별 docked 구조가 있으면 그걸, 없으면 7XNA를 폴백으로 보여줍니다"라는 발화를 화면이 뒷받침한다.

**P0-3: Benchmark 탭 — 503 에러 메시지 개선**

현재: "Failed to load benchmark results." (원인 없음).
수정안: `benchmarkQuery.isError`일 때 "Benchmark 데이터 미사용(llm_benchmark 모듈 별도 설치 필요)" 또는 "본 시연에서 비활성 (503)" 메시지.
비용: `BenchmarkPage.tsx` 2줄 수정. 15분.
위험: 없음.
이득: 박사 청자가 에러 화면을 보고 "시스템 고장"으로 인식하는 것 방지.

### P1 — 5/28 회의 후 한 주 이내 (5건)

**P1-1: Run Console candidates 테이블 — iPTM·margin·ddG 인라인 범례**

현재: 열 제목 "iPTM × 5", "margin", "ddG" 텍스트만 있음.
수정안: 테이블 헤더 아래 또는 테이블 아래에 `margin = SSTR2 iPTM − max(off-target) · ddG: 음수일수록 강한 결합` 한 줄.
비용: 15분.
이득: 다음 회의 또는 내부 공유 시 용어 설명 비용 절감.

**P1-2: `/api/archives/top-k` 엔드포인트 BE 구현 또는 FE graceful degradation**

현재: `ArchivesTopKSlider`가 실패하면 에러 메시지 출력, mock 없음.
수정안 A: BE에 endpoint 구현(runs 데이터에서 top-k 파생). 수정안 B: 실패 시 에러 대신 "Archive 데이터 없음 — 수동 run_id 입력으로 대체" 안내.
비용: A는 BE 4~8시간. B는 FE 30분.
B를 단기 적용 권장.

**P1-3: `/api/candidate/{id}/report` 엔드포인트 구현**

현재: 404. FE는 항상 "Report" 버튼을 활성화함.
수정안: BE에 후보 데이터를 Markdown/PDF로 반환하는 엔드포인트 구현. 또는 P0-1과 함께 버튼 비활성화 유지.
비용: BE 구현 4~8시간. 비활성 유지는 P0-1에서 커버됨.

**P1-4: smoke test "more" button 기대 수정**

현재: `App.smoke.test.tsx:95`가 `role="button" name=/more/i`를 기대하나 현재 nav 설계에 없음. 테스트 1건 실패.
수정안: 테스트 기대를 현재 nav 구조(11개 NavLink)에 맞게 수정. 또는 더 좁은 화면에서 nav overflow를 대비해 More 드롭다운을 실제로 구현하고 테스트를 살린다.
비용: 테스트 수정 30분. More 드롭다운 구현은 2~4시간.
권장: 테스트 기대를 현재 구조에 맞게 수정(빠른 경로).

**P1-5: Run Console Silo A/B/A+B 토글 — 비활성 silo 시각적 표시**

현재: A/B/A+B 모두 클릭 가능하고 A 선택 시 데이터 없이 빈 화면.
수정안: A와 A+B 탭에 `disabled` + `title="Silo A: NGC API key 미확보 · 비활성"` 처리. 또는 dim 색으로 표시.
비용: 15분.
이득: 발표 중 청자가 A를 누르는 상황 방지.

### P2 — 1개월 이내

- Candidate contacts 패널 하드코딩 제거: 후보별 실제 contact 데이터를 BE에서 받거나 "후보별 contact 계산 미지원" 표시.
- CandidatePage ADMET 레이블 설명 추가: GRAVY, Boman index, aggregation 옆에 parenthetical 설명 또는 tooltip.
- Run Console 후보 테이블 키보드 접근성: `tabIndex={0}` + `onKeyDown={(e) => e.key === 'Enter' && setSelectedCand(candidate.id)}` 추가.
- Selectivity heatmap keyboard focus.
- `usePipelineStatus` / `useRunStatus` 중복 폴링 통합 — BE 부하 및 race condition 개선.
- Benchmark 탭 항목을 Nav에서 secondary 위치(About/Settings 옆)로 이동 — 일상 운영과 무관한 내부 실험 데이터이므로 primary nav에서 위치 재검토.

### P3 — Nice-to-have

- Figma 디자인 시스템 토큰 문서화.
- Storybook 컴포넌트 카탈로그.
- WCAG 대비 자동화 측정 (axe-core 통합).
- About 페이지 섹션별 앵커 링크 + TOC.
- SSE 재연결 자동화 (현재 수동 새로고침 필요).

---

## 6. 5/28 시연 보강 권고 — UI 수정 없이 발화로 보완 가능한 것

| 화면 요소 | 발화 보완 내용 |
|---------|-------------|
| Mol* 3D 구조 (Candidate, Selectivity Drawer) | "지금 보이는 3D는 SSTR2 reference 구조 7XNA입니다. PRST-001 docked PDB가 있으면 자동으로 후보 구조로 교체됩니다. 오늘은 reference fallback입니다." |
| "Report" 버튼 | 언급하지 않거나 클릭하지 않는다. 불가피하게 언급 시 "보고서 다운로드 기능은 다음 스프린트 목표입니다." |
| Benchmark 탭 에러 | "LLM Benchmark 탭은 별도 모듈 의존성으로 현재 시연에서 비활성입니다. 실험 결과는 PPTX 슬라이드에 포함했습니다." |
| ArchivesTopKSlider 에러 (Manual Selectivity) | 시연 시나리오에서 Manual Selectivity 탭을 여는 계획이 없으면 미노출. 노출 시 "상단 Archive 섹션은 BE 구현 중이며, 하단 수동 실행 기능은 정상 동작합니다." |
| "margin" / "iPTM" 용어 | "margin은 SSTR2 결합 신뢰도에서 가장 강한 off-target을 뺀 selectivity 점수입니다. 양수일수록 SSTR2 선택성이 높습니다." |
| ADMET 수치 | "이 수치들은 학습 분포 밖(OOD) 외삽 가능성이 크므로 참고값입니다. 합성 의뢰서에 wet-lab 실측 항목을 별도로 명시했습니다." |
| Silo A 탭 | 시연 중 A 탭 클릭하지 않는다. 질문 시 "Silo A는 NVIDIA NGC API key 확보 후 활성화 예정입니다." |
| PRST-001 contacts 패널 (K4/Asp137 등) | "이 contact residue들은 FlexPepDock 분석에서 식별된 주요 상호작용 잔기입니다. 현재는 PRST-001 기준 고정 표시이며 후보별 동적 계산은 다음 단계입니다." |

---

## 7. 결론 — 5/28 시연 가능성 평가

| 항목 | 평가 |
|------|------|
| BE 부팅 가능 | Y — P0 fix 후 uvicorn 정상, 72개 경로 응답 |
| FE 빌드 가능 | Y |
| PRST-001 후보 화면 표시 | Y (Candidate Review 진입, run_id 지정 필요) |
| Mol* 3D 구조 | Y — 단, docked PDB 없으면 7XNA reference (발화 보완 필요) |
| Selectivity Explorer iPTM 매트릭스 | Y (runId 있으면 표시) |
| Benchmark 탭 | N — 503 에러 메시지 (P0-3으로 메시지 개선 권고) |
| Manual Selectivity ArchivesTopKSlider | N — 404 에러 표시 (시연 경로 제외 권고) |
| Report 버튼 클릭 | N — 404, 화면 피드백 없음 (P0-1 수정 또는 버튼 미클릭 권고) |

**전체 시연 가능 여부**: Conditional — P0 3건 수정 후 Step 1~2 시연 가능. Benchmark와 Manual Selectivity ArchivesTopKSlider는 시연 경로에서 제외하거나 발화로 사전 안내 필요.

---

## 마지막 stdout 5줄

1. **5/28 시연에서 가장 큰 인지 부하 1개**: "Report" 버튼이 활성화되어 있으나 클릭해도 아무 반응이 없는 상황 — 화면이 망가진 것처럼 보일 수 있고 발표 흐름이 끊린다.

2. **즉시 수정 가능한 P0 1개 + 예상 시간**: P0-1 — CandidatePage.tsx의 "Report" `<a download>` 버튼을 `disabled` 버튼으로 전환 + tooltip "준비 중". 예상 시간: 30분.

3. **BE fix(`/api/benchmark/results` 503)가 FE에 어떻게 보이는지**: BenchmarkPage가 `isError=true` 분기를 타며 빨간 텍스트 "Failed to load benchmark results."만 표시됨 — 에러 원인은 표시되지 않음.

4. **박사 청자가 한 task 끝내는 평균 click 수 (예상)**: Run Console에서 후보 확인 2-3 click, Selectivity Explorer에서 셀 선택 후 Drawer 열기 2 click, Candidate Review에서 후보 변경 1 click — 평균 2~3 click (BE 응답 정상 시 기준).

5. **본 분석을 narrative v3 어디에 반영하면 좋을지**: narrative v3 §5.4 "코드 실태와 narrative의 격차" 테이블에 "FE Report 버튼 — BE endpoint 미존재", "Mol* 3D — candidate pose 없으면 7XNA reference 표시" 두 행을 추가하면 발표 시 발화 준비와 일치한다.
