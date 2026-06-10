# UI 검증 보고서 — FE 5173 + BE 8787 통합

**날짜**: 2026-05-12  
**담당**: reviewer-uiux  
**상태**: CONDITIONAL PASS (High 이슈 3건 수정 필요, 기능 동작 확인됨)  
**검증 방식**: 코드 정적 분석 + `curl` API 응답 캡처 — HEURISTIC-PARTIAL (브라우저 렌더링 없음)

---

## 종합 판정

| 영역 | 판정 | 비고 |
|------|------|------|
| A. 라우트/페이지 | PASS | 6페이지, lazy + ErrorBoundary |
| B. 핵심 UI 컴포넌트 | CONDITIONAL | SILO_B 필터 일부 레이블 불일치 |
| C. 사용성 | PASS | 에러 핸들링·fallback 우수 |
| D. 접근성 | CONDITIONAL | focus trap 1건 누락, aria-expanded 누락 |
| E. FE 코드 품질 | PASS | any 2건, 의도적 eslint-disable 명시됨 |
| F. 개선 후보 | → §6 |  |

---

## §1 페이지/라우트 인벤토리

### 라우터 설정 (`App.tsx:353-359`)
```
BrowserRouter > AppLayout > Routes
  /         → Redirect to /silo-b
  /silo-b   → SiloBPage   (Lazy + PageErrorBoundary)
  /silo-a   → SiloAPage   (Lazy + PageErrorBoundary)
  /combined → CombinedPage (Lazy + PageErrorBoundary)
  /selectivity → SelectivityPage (Lazy + PageErrorBoundary)
  /settings → SettingsPage (Lazy + PageErrorBoundary)
  /about    → AboutPage   (Lazy + PageErrorBoundary)
```

### 페이지 목록

| 파일 | 경로 | 용도 | 상태 관리 |
|------|------|------|---------|
| `SiloBPage.tsx` | `/silo-b` | PyRosetta 파이프라인 메인 대시보드 | `usePipelineContext` (공유 상태) |
| `SiloAPage.tsx` | `/silo-a` | 3-ARM 파이프라인 참조 | `usePipelineContext` |
| `CombinedPage.tsx` | `/combined` | Silo A+B 통합 비교 뷰 | `usePipelineContext` |
| `SelectivityPage.tsx` | `/selectivity` | 수용체 선택성 분석 | 독립 훅 `useSelectivity` |
| `SettingsPage.tsx` | `/settings` | 파이프라인 설정 저장 | 로컬 `useState` + `/api/settings` POST |
| `AboutPage.tsx` | `/about` | 프로젝트 정보 | 정적 |

### 상태 관리 패턴
- `PipelineContext.tsx`: `usePipelineStatus(2000)` 결과를 Context로 공유 → Silo A/B/Combined 페이지가 동일 데이터 소스 사용
- prop drilling 없음 — Context 패턴 일관됨

---

## §2 핵심 UI 컴포넌트 분석

### 2-1. `usePipelineStatus` 결과 → 화면 반영

**파일**: `hooks/usePipelineStatus.ts`

| 항목 | 결과 |
|------|------|
| polling interval | 2000ms |
| AbortController | 사용 (정상 cleanup) |
| mountedRef StrictMode 대응 | 있음 (eslint-disable 주석 명시) |
| switchRun (Archive 전환) | 독립 fetch, viewingArchiveRef로 polling과 분리 |
| error 상태 | `no_status_file` / HTTP 에러 / AbortError 처리 완비 |

**BE 실제 응답 (2026-05-12 02:18 기준)**:
```
run_id:   local_20260512_0213_iter03
iteration: 3 / 3   completed: false
candidates: 0개 (실행 중 임시 상태)
agents: 5개
rosetta_substeps: 7개
```

### 2-2. SILO_B_STEPS 화이트리스트 (`SiloBPage.tsx:35-38`)

```ts
const SILO_B_STEPS = new Set([
  'step01', 'step03b', 'step03b_qc', 'silo_b',
  'step04', 'step05', 'step05b', 'step06', 'step07', 'step08', 'step09',
])
```

**BE 실제 step 레이블 vs. SILO_B_STEPS 적용 결과**:

| Step ID | BE 레이블 | 상태 | SILO_B 포함? | 비고 |
|---------|---------|------|-------------|------|
| step01 | OpenFold3 | completed | ✅ | |
| step02 | RFdiffusion | pending | ❌ 정상 제외 | Silo A 전용 |
| step03 | ProteinMPNN | pending | ❌ 정상 제외 | Silo A 전용 |
| step03b | BLOSUM Mutation | completed | ✅ | |
| step03b_qc | Stability Pre-screen | pending | ✅ | |
| step04 | ESMFold QC | completed | ✅ **⚠️** | Silo A QC step이지만 포함 |
| step05 | **DiffDock** | completed | ✅ **⚠️** | Silo A 전용 step 노출 |
| step05b | Selectivity | pending | ✅ | |
| step06 | PyRosetta | completed | ✅ | |
| step07 | Analysis | completed | ✅ | |
| step08 | Stability | pending | ✅ | |
| step09 | MolMIM | pending | ✅ | |

**⚠️ 이슈**: `step05 (DiffDock)`은 Silo A 전용 단계인데 SILO_B_STEPS에 포함되어 Silo B 뷰에 "DiffDock" 레이블로 표시됨. 소스 주석에는 "step05(Critic)"으로 기재되어 있으나 BE 실제 레이블과 불일치.

### 2-3. `PipelineStatus` 컴포넌트

| 체크 항목 | 결과 |
|---------|------|
| `role="progressbar"` + aria-valuenow/min/max | ✅ 있음 (`PipelineStatus.tsx:144-148`) |
| `role="list"` + `role="listitem"` | ✅ 있음 |
| Legend (completed/running/pending/failed) | ✅ 있음 |
| pyrosettaOnly 모드 Rosetta substeps 표시 | ✅ 있음 (7개 substep 지원) |
| executionMode 감지 및 표시 | ✅ (run_id 접두사 + step 패턴 감지) |

### 2-4. `AgentMonitor` 컴포넌트

| 체크 항목 | 결과 |
|---------|------|
| 에이전트 카드 `aria-label` | ✅ `AgentMonitor.tsx:241` |
| Expand/Collapse All 버튼 | ✅ signal/target 패턴 |
| ConfiguredOnlyBadge (비활성 에이전트) | ✅ `opacity-60` + 툴팁 |
| `isRuntimeActive` 기반 활성/비활성 구분 | ✅ |
| AgentReport 패널 (plan/critic/reporter) | ✅ 3가지 유형 지원 |

---

## §3 사용성 평가

### 강점

1. **PageErrorBoundary 크래시 격리** (`App.tsx:25-52`): 개별 페이지 크래시가 전체 앱을 깨지 않음. Retry 버튼으로 복구 가능.

2. **3-상태 연결 배지** (`App.tsx:136-165`): Live (green pulse) / Archive (amber) / Mock (grey) 헤더에 명확히 표시.

3. **Historical Fallback** (`SiloBPage.tsx:49`): 현재 run 실패 + candidates 없을 때 자동으로 과거 후보 표시. amber 배너로 사용자에게 알림.

4. **한국어 실패 이유 humanize** (`CandidateTable.tsx:13-53`): `humanizeFailReason()` — "시뮬레이션 비정상 종료", "잔기 변이 실패" 등 도메인 맥락 한국어 상세 설명.

5. **모달 Escape 처리**: ValidationDetailModal, MoleculeViewer, VisualizationPanel 모두 Escape 키 닫기 구현됨.

6. **ExperimentControl 실행 중 보호**: 실행 중 폼 `disabled` 처리 + `cursor-not-allowed` + `opacity-40` 시각 피드백.

7. **RunSelector 아카이브 브라우징** (`App.tsx:278-351`): 18개 archived runs 드롭다운, 각 run의 iter/candidates/best_ddg 정보 표시.

8. **DdGCell 이상값 감지** (`CandidateTable.tsx:154-179`): |ΔG| > 80 amber 경고, |ΔG| > 100 red 심각 이상값 표시.

### 약점

1. **candidates=0 빈 상태**: 현재 run이 candidates 0개 반환 중이나 CandidateTable 빈 상태 UI 처리 방식 HEURISTIC 확인 필요 (`§7` 참조).

2. **이중 진행 표시 혼란**: ExperimentControl에 iteration/totalIterations 기반 progress bar, PipelineStatus에 step 완료 기반 % 표시가 공존. 사용자가 어느 것을 기준으로 진행률을 판단해야 하는지 불명확.

3. **SettingsPage 반영 여부 불투명**: `/api/settings` POST 저장 성공 시 "Saved!" 피드백 있음. 그러나 이미 실행 중인 파이프라인에 즉시 적용되는지 여부 UI에서 명시되지 않음.

---

## §4 접근성 점수

### 전반 지표

| 지표 | 수치 | 기준 |
|------|------|------|
| aria-* 속성 (`/components/`) | 101개 | 충분 |
| 키보드 인터랙션 패턴 (tabIndex/onKeyDown/role) | 41개 | 충분 |
| any 타입 사용 | 2개 | 우수 |

### PASS 항목

| 컴포넌트 | aria 패턴 | 비고 |
|---------|---------|------|
| PipelineStatus | role="progressbar", aria-valuenow/min/max, role="list" | 완비 |
| AgentMonitor | role="section" aria-label, 각 card aria-label | 완비 |
| RunSelector | aria-expanded, aria-haspopup, role="listbox" | 완비 |
| ValidationDetailModal | role="dialog", aria-modal, useFocusTrap | 완비 |
| VisualizationPanel | focus trap 직접 구현, trigger 복원 | 완비 |
| ExperimentControl | label-id 연결, role="switch"+aria-checked | 완비 |
| CandidateTable | role="table", aria-label, aria-sort | 완비 |

### FAIL/CAUTION 항목

| 번호 | 심각도 | 파일:라인 | 이슈 | WCAG 기준 |
|------|-------|---------|------|---------|
| A1 | **HIGH** | `MoleculeViewer.tsx:127-136` | dialog에 `useFocusTrap` 없음. Tab키로 포커스 모달 밖 탈출 가능. ESC는 있음. | 2.1.2 No Keyboard Trap |
| A2 | **HIGH** | `ValidationPanel.tsx:37-67` | `CheckRow` 확장 버튼에 `aria-expanded` 없음. 스크린 리더가 접힘/펼침 상태 인식 불가. | 4.1.2 Name, Role, Value |
| A3 | MED | `ExperimentControl.tsx:188` | Objective 모드 `<label>` 태그가 있으나 `htmlFor` 없음. 버튼 그룹에 `role="group"` + `aria-label` 없음. | 1.3.1 Info and Relationships |
| A4 | MED | `MoleculeViewer.tsx:153-167` | View mode 버튼에 `title` 속성만 있고 `aria-label` 없음. 모바일/스크린 리더에서 접근 불가. | 4.1.2 |
| A5 | MED | 전체 | `aria-live` region 없음. 파이프라인 상태 변경(단계 완료, 에러) 시 스크린 리더 알림 없음. | 4.1.3 Status Messages |
| A6 | LOW | `CandidateTable.tsx:140-150` | `ScoreCell` 색상(hsl)만으로 품질 표현. colorblind 미지원. `ClashCell`은 아이콘 추가로 이미 개선됨. | 1.4.1 Use of Color |
| A7 | LOW | `App.tsx:249-266` | `ApiBadge` (ESMFold/MolMIM 상태)에 `aria-label` 없음. | 4.1.2 |

---

## §5 FE 코드 품질

### TypeScript `any` 사용

| 파일 | 라인 | 사용 | 교체 가능 타입 |
|------|------|------|-------------|
| `CombinedPage.tsx` | 375 | Recharts formatter 콜백 `(v: any, name: any)` | `(v: number \| null, name: string)` |
| `CombinedPage.tsx` | 417 | Recharts formatter 콜백 `(v: any)` | `(v: number \| null)` |

**전체 평가**: 매우 낮음 (2개). `Record<string, unknown>` 패턴으로 대부분 any 회피됨.

### useEffect 패턴

| 파일 | 패턴 | 평가 |
|------|------|------|
| `usePipelineStatus.ts:325-351` | `mountedRef`로 StrictMode 이중 마운트 방지. `eslint-disable` 주석 명시 | 의도적, 적절 |
| `AgentMonitor.tsx:221-227` | external signal → local state 동기화. `eslint-disable` 주석 명시 | 의도적, 적절 |
| `ValidationPanel.tsx:175-197` | `fetchedRef`로 중복 fetch 방지 | 적절 |
| `MoleculeViewer.tsx:40-99` | `disposed` flag로 비동기 경쟁 조건 방지 | 우수한 패턴 |
| `VisualizationPanel.tsx:35-65` | focus trap + Escape 직접 구현 | 적절 |

**전체 평가**: deps 배열 누락 없음. 의도적 예외는 eslint-disable 주석으로 명시됨.

### 컴포넌트 분리

| 항목 | 현황 | 평가 |
|------|------|------|
| 총 컴포넌트 | 22+ 파일 | 양호 |
| 커스텀 훅 | 9개 (useClickOutside, useFocusTrap, useAdmetBatch, useCandidateSort, useExperiment, usePipelineStatus, useSelectivity, useSelection, useValidation) | 우수 |
| memo 사용 | CandidateTable 내부 5개 (ResultBadge, SortIcon, ScoreCell, DdGCell 등), ADMETPanel, PharmacologyPanel | 적절 |
| SiloBPage 크기 | 200라인, 20+ 임포트 | 과중 (개선 대상) |

---

## §6 개선 후보 우선순위

### HIGH — 접근성 WCAG 위반

- **[HIGH-1] MoleculeViewer dialog focus trap 누락**
  - 위치: `MoleculeViewer.tsx:31-60`
  - 현 상태: Escape 키 처리는 있으나 `useFocusTrap` 미사용. Tab으로 포커스가 다이얼로그 밖으로 탈출.
  - 제안: `const modalRef = useRef<HTMLDivElement>(null)` + `useFocusTrap(modalRef)` 추가. 열릴 때 닫기 버튼으로 초기 포커스 이동.
  - 추정 공수: **S (30분)**
  - 유지보수 가치: 스크린 리더/키보드 전용 사용자 최소 요건. WCAG 2.1.2.

- **[HIGH-2] CheckRow aria-expanded 없음**
  - 위치: `ValidationPanel.tsx:37-67`의 `CheckRow()` 확장 버튼
  - 현 상태: `<button onClick={() => setExpanded(e => !e)}>` — aria-expanded 없음.
  - 제안:
    ```tsx
    <button
      onClick={() => setExpanded(e => !e)}
      aria-expanded={expanded}
      aria-controls={`check-detail-${check.id}`}
      ...
    >
    ```
    펼침 내용 `<div id={`check-detail-${check.id}`}>` 연결.
  - 추정 공수: **S (15분)**

- **[HIGH-3] SILO_B_STEPS 내 step05 "DiffDock" 노출**
  - 위치: `SiloBPage.tsx:35-38`
  - 현 상태: BE `step05` 레이블 = "DiffDock" (Silo A 전용)이 Silo B 뷰에 표시됨. 소스 주석 ("step05(Critic)")과 불일치.
  - 원인 분석: BE `state.py`가 반환하는 step05 레이블이 파이프라인 실행 모드에 따라 다른데, FE 주석은 Silo B 전용 실행 기준 작성.
  - 제안 A (FE): SILO_B_STEPS에서 step05 제외 → Silo B 뷰에서 DiffDock 숨김.
  - 제안 B (BE): BE가 Silo B 파이프라인 실행 시 step05 레이블을 "Critic"으로 반환.
  - 추정 공수: **S FE 단독 (10분)**, **M BE 수정 포함 (2시간)**

### MEDIUM — 사용성·접근성 개선

- **[MED-4] ExperimentControl Objective 그룹 aria 미연결**
  - 위치: `ExperimentControl.tsx:186-209`
  - 현 상태: `<label>Objective</label>` (htmlFor 없음), 버튼 그룹에 role/aria-label 없음.
  - 제안:
    ```tsx
    <div role="group" aria-label="Objective mode">
      <span id="obj-label" className="...">Objective</span>
      {OBJECTIVE_MODES.map(mode => (
        <button aria-pressed={config.objective_mode === mode.value} ...>
      ))}
    </div>
    ```
  - 추정 공수: **S (20분)**

- **[MED-5] MoleculeViewer view mode buttons aria-label 없음**
  - 위치: `MoleculeViewer.tsx:153-167`
  - 현 상태: `title={mode.desc}` 만 있음. 스크린 리더에서 버튼 목적 불명확.
  - 제안: `aria-label={mode.label}` 추가.
  - 추정 공수: **S (10분)**

- **[MED-6] aria-live region 파이프라인 상태 알림**
  - 위치: `PipelineStatus.tsx` 또는 `App.tsx`
  - 현 상태: 단계 완료/에러 시 시각적 변화만, 스크린 리더 알림 없음.
  - 제안: 헤더에 `<div aria-live="polite" className="sr-only">` 추가. `usePipelineStatus`의 상태 변경 시 메시지 업데이트.
  - 추정 공수: **M (1.5시간)**

- **[MED-7] 이중 진행 표시 통합 안내**
  - 위치: `ExperimentControl.tsx:99-106` + `PipelineStatus.tsx:99`
  - 현 상태: ExperimentControl bar = iteration 기반 (3/3 = 100%), PipelineStatus % = step 완료 기반 (다름).
  - 제안: 두 바의 기준 차이를 레이블로 명시. ExperimentControl bar에 "Iterations", PipelineStatus에 "Steps" 레이블 강조.
  - 추정 공수: **S (20분)**

### LOW — 코드 품질

- **[LOW-8] CombinedPage.tsx Recharts formatter `any` 제거**
  - 위치: `CombinedPage.tsx:375, 417`
  - 제안:
    ```tsx
    // 375
    formatter={(v: number | null, name: string): [string, string] =>
      [v != null ? v.toFixed(2) : '—', name ?? '']}
    // 417
    formatter={(v: number | null): [string, string] =>
      [v != null ? `${v.toFixed(2)} kcal/mol` : '—', 'ΔG']}
    ```
  - 추정 공수: **S (10분)**

- **[LOW-9] ScoreCell colorblind 지원**
  - 위치: `CandidateTable.tsx:140-150`
  - 현 상태: `hsl(hue, 70%, 65%)` 색상만 사용. red-green colorblind 미지원.
  - 제안: ClashCell 패턴 참조 — 상위 N% / 하위 N% 에 작은 아이콘 추가.
  - 추정 공수: **M (1시간)**

- **[LOW-10] SiloBPage 컴포넌트 분리**
  - 위치: `SiloBPage.tsx` (200라인, 20+ 임포트)
  - 현 상태: 단일 컴포넌트에 렌더링 로직 집중.
  - 제안: `SiloBAnalysisSection`, `SiloBMutationSection` 등으로 분리. 성능 영향 최소화.
  - 추정 공수: **L (3-4시간)**

---

## §7 HEURISTIC-PARTIAL — 실 브라우저 검증 필요 항목

> 코드 분석 기반 평가의 한계. 아래 항목은 실제 브라우저에서 확인 필요.

| 항목 | 확인 방법 | 예상 리스크 |
|------|---------|-----------|
| CandidateTable candidates=0 빈 상태 UI | BE 0 candidates 상태에서 FE `/silo-b` 접속 후 확인 | Low (PlaceholderState 컴포넌트 존재) |
| MoleculeViewer PDB 로드 (Mol* 3D) | `/api/structures/...` 실제 파일 있는 경우 | Medium (Mol* init 복잡도) |
| 반응형 레이아웃 (모바일 < 640px) | DevTools 375px 시뮬레이션 | Medium (nav overflow 가능) |
| 색상 대비 WCAG AA 4.5:1 | axe DevTools 또는 Lighthouse 실행 | Medium (`text-slate-400` 배경 `bg-slate-800` 대비율 계산 필요) |
| ExperimentControl 실행 중 → 완료 후 상태 전환 | 실제 파이프라인 실행 | Low |
| SettingsPage 저장 → 재기동 반영 | `/api/settings` POST 후 BE 로그 확인 | Medium |
| RunSelector 드롭다운 18개 run 스크롤 | 실제 드롭다운 열어서 오버플로우 확인 | Low |
| aria-live 스크린 리더 알림 | NVDA / VoiceOver 실행 | High (현재 aria-live 없음) |

---

## 부록: 검증 근거 파일 목록

```
App.tsx                           — 라우터, 헤더, ErrorBoundary
hooks/usePipelineStatus.ts        — polling, StrictMode 대응
pages/SiloBPage.tsx               — SILO_B_STEPS, 데이터 흐름
components/PipelineStatus.tsx     — role, aria, progress bar
components/AgentMonitor.tsx       — 에이전트 카드, aria-label
components/ExperimentControl.tsx  — form, label-id, feature toggle
components/ValidationPanel.tsx    — dialog, CheckRow, focus trap
components/MoleculeViewer.tsx     — Mol*, dialog, focus trap 부재
components/VisualizationPanel.tsx — focus trap 직접 구현
components/CandidateTable.tsx     — table, aria-sort, DdGCell
pages/SettingsPage.tsx            — /api/settings POST
types/index.ts                    — 타입 완전성
```

BE API 검증:
```
GET http://localhost:8787/api/status   → 200 OK (run_id: local_20260512_0213_iter03)
GET http://localhost:8787/api/runs     → 200 OK (18개 archived runs)
GET http://localhost:5173/             → 200 OK (FE SPA 정상 서비스)
```
