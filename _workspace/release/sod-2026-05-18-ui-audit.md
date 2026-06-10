# UI/UX 전수 점검 — PRST_N_FM Frontend

> **Task #32** — 사용자 요청: "UI 전체 점검, 가독성, 배경색과 아이콘 색, 폰트 색 전체 점검"
> **수행**: reviewer-uiux (Agent tool, ~165초)
> **날짜**: 2026-05-18

## 판정: CONDITIONAL (조건부 통과)

**전체 일관성 점수**: 5/10

구조적 분리가 명확하지 않음 — 신규 OKLCH 토큰 페이지(ManualSelectivityPage, RunConsolePage, SelectivityExplorerPage, RunLauncherPage, BenchmarkPage, WetlabOrderPage, CandidatePage)와 구형 Tailwind slate 컴포넌트(CandidateTable, PharmacologyPanel, AgentMonitor, ValidationPanel, MutationAnalysis, RiskMatrix, QCGateChart 등)가 동일 화면에서 혼재. **라이트 테마 전환 시 구형 컴포넌트가 심각하게 깨짐.**

## 우선 fix 권장 3건

1. **Tooltip/Popup 배경 (8개 컴포넌트)** — `bg-slate-800 border-slate-700 text-slate-300` → `var(--bg-elev) var(--border) var(--text)` 일괄 교체. 라이트 테마 팝업이 다크로 뜨는 Critical 버그.
2. **Recharts 차트 inline hex (6개 컴포넌트)** — `ConvergenceGraph`, `DdGDistribution`, `QCGateChart`, `MutationAnalysis`, `RunComparisonPanel`, `SequenceLogo` — `#22d3ee`, `#1e293b`, `#64748b` 등 → CSS var.
3. **`text-white` 5곳** — `bg-pos`/`bg-accent` 위 고정 `text-white`. accent 변경 시 대비 보장 X. `var(--bg)` 또는 CSS `color-contrast()` 권장.

## 표 1 — 잔재 하드코딩 색 (Critical/High 우선 15건)

| # | 파일:라인 | 현재 | 권장 | 심각도 |
|---|-----------|------|------|--------|
| 1 | `ValidationPanel.tsx:97` | `bg-black/70` (Modal 오버레이) | `var(--bg-sunk)/80` + backdrop-blur | Critical |
| 2 | `CandidateTable.tsx:103,256,330,386` | `bg-slate-800 border-slate-700 text-slate-300` (tooltip×4) | `bg-[var(--bg-elev)] border-[var(--border)] text-[var(--text)]` | Critical |
| 3 | `AgentMonitor.tsx:35` | `bg-slate-800 border-slate-700 text-slate-300` (tooltip) | 동일 | Critical |
| 4 | `PharmacologyPanel.tsx:143` | `bg-slate-800/50 border-slate-700/60` (MetricCard) | `bg-[var(--bg-sunk)] border-[var(--border)]` | High |
| 5 | `PharmacologyPanel.tsx:303` | `bg-slate-900 border-slate-700` (드롭다운) | `bg-[var(--bg-elev)] border-[var(--border)]` | High |
| 6 | `MutationAnalysis.tsx:135,141,145,149` | `bg-slate-800/60` (summary stat cards×4) | `bg-[var(--bg-sunk)]` | High |
| 7 | `ConvergenceGraph.tsx:134` | `stroke="#1e293b"` (CartesianGrid) | `stroke="var(--border)"` | High |
| 8 | `ConvergenceGraph.tsx:171,180,190` | `stroke="#22d3ee/#3b82f6"`, `fill="#7c3aed"` | `var(--teal)/var(--accent)/var(--violet)` | High |
| 9 | `DdGDistribution.tsx:130,149,154` | `stroke="#1e293b"`, `stroke="#ef4444"`, `fill="#22d3ee"` | `var(--border)/var(--neg)/var(--teal)` | High |
| 10 | `QCGateChart.tsx:151` | `stroke="#1e293b"` | `stroke="var(--border)"` | Medium |
| 11 | `SARHeatmap.tsx:118,130,147,165,175,187` | `fill="#facc15/#64748b/#334155/#f1f5f9"` | `var(--warn)/var(--text-dim)/var(--bg-sunk)/var(--text)` | Medium |
| 12 | `SequenceLogo.tsx:136,137,141` | `fill="#64748b"`, `stroke="#1e293b"` | `var(--text-dim)`, `var(--border)` | Medium |
| 13 | `RunComparisonPanel.tsx:31` | `stroke="#4ade80/#f87171"` | `var(--pos)/var(--neg)` | Medium |
| 14 | `MoleculeViewer.tsx:205` | `backgroundColor: '#0f172a'` | `backgroundColor: 'var(--bg-sunk)'` | Medium |
| 15 | `RiskMatrix.tsx:72`, `CandidateCompareModal.tsx:157`, `ValidationPanel.tsx:100` | `bg-slate-900 border-slate-700` (Modal) | `bg-[var(--bg-elev)] border-[var(--border)]` | Medium |

## 표 2 — 가독성 우려 (WCAG 2.1 AA 기준, 핵심 8건)

| # | 파일:라인 | 이슈 | 권장 fix |
|---|-----------|------|---------|
| 1 | `tokens.css:37` | `--text-dim: #a8a29e` light값 — `bg #fafaf9` 대비 **2.9:1** (AA 미달) | `--text-dim`을 `#78716c`(대비 4.6:1) 또는 `#6b7280`로 상향 |
| 2 | `CandidateTable.tsx:210,462` | `text-amber-400/60-70` (10px, 60-70% 불투명) — 대비비 ≈ **1.8:1** | 투명도 제거 → `text-[var(--warn)]` |
| 3 | `CandidateCompareModal.tsx:212` | `text-cyan-600` (9px) — light 대비 **2.5:1** | `text-[var(--text-dim)]` |
| 4 | `HeuristicBanner.tsx:48` | `text-yellow-300` on light `bg-yellow-900/20` — 실효 대비 **2.4:1** | 테마별 분리 또는 `var(--warn)` |
| 5 | `RiskMatrix.tsx:199,205` | `text-slate-300` (matrix label) — light에서 불가시 | `text-[var(--text-mute)]` |
| 6 | `VisualizationPanel.tsx:83` | `text-slate-300` (loading state) | 동일 |
| 7 | `PipelineStatus.tsx:61` | `text-blue-300 animate-pulse-glow` — pulse 시 **1.8:1** | `text-[var(--accent)]` + min-opacity 0.6 |
| 8 | `MutationAnalysis.tsx:176` | `text-slate-500` (10px on `bg-slate-800/60`) — small text **3.5:1** (미달) | `text-[var(--text-mute)]` |

## 표 3 — 컴포넌트별 일관성 등급

| 컴포넌트 | 등급 | 근거 |
|---------|------|------|
| Header / Nav / Footer (`App.tsx`) | A | 토큰 완전 준수 (status badge 일부 의미적 색 잔재 허용) |
| ThemeToggle | A | 토큰 완전 준수 |
| ManualSelectivityPage | A | 신규 토큰 전면 사용 |
| RunConsolePage / SelectivityExplorerPage / RunLauncherPage | A- | `text-white` 5건 잔재 |
| BenchmarkPage / WetlabOrderPage / CandidatePage | B+ | 일부 amber/emerald/red 하드코딩 |
| TierBadge / HeatmapCell | A | 토큰 완전 준수 |
| HeuristicBanner | B | 배경 Tailwind 하드코딩, light 가독성 이슈 |
| **CandidateTable** | **C** | slate 팔레트 전면, tooltip×4 + 파생 배지 |
| **PharmacologyPanel** | **C** | MetricCard + 드롭다운 slate 사용 |
| **AgentMonitor** | **C** | slate-900/800/950 전반 |
| **ValidationPanel** | **C** | 체크박스 + Modal + 오버레이 slate/black |
| **MutationAnalysis** | **C** | summary card + 차트 inline hex |
| **RiskMatrix** | **C** | Modal + 셀 배경 하드코딩 |
| **ConvergenceGraph / DdGDistribution / QCGateChart** | **C** | Recharts hex 전반 |
| **SARHeatmap** | **C** | SVG fill 전체 hex |
| **RunComparisonPanel / VisualizationPanel** | **C** | slate 사용 |
| CandidateCompareModal | B- | slate + `text-cyan-600 (9px)` |

## 핵심 접근성 이슈 (WCAG 2.1 AA 위반)

1. `--text-dim` light값 2.9:1 — 18px 미만 모두 위반. `ManualSelectivityPage MetaStat`, 테이블 헤더 등 실사용 위치 다수.
2. 투명도 적용 강조 텍스트 (`text-amber-400/60` 10px) — 어떤 배경에서도 AA 미달.
3. focus-visible 누락 — `CandidateTable` tooltip 트리거 등 키보드 포커스 비가시.
4. Modal 오버레이 `bg-black/70` — 토큰 일관성 위반.
5. `text-white` on dynamic bg — accent hue 변경 시 대비 보장 X.

## 보충 관찰

- **이중 토큰 시스템 공존**: 구형 `text-slate-*`/`border-slate-*` 컴포넌트는 `[data-theme="light"]` 전환에 반응 X. **가장 큰 구조적 문제.**
- **Recharts `contentStyle`**: 4개 컴포넌트에서 inline 다크 배경 hex. light에서 반드시 토큰 교체.
- **`card` 클래스 (`index.css`)**: 올바른 토큰 정의. sub-card/tooltip만 깨짐.
- **strokeWidth/icon size**: lucide-react 기본값 사용, 위치 구분 명확 → 허용 수준.

## 후속 작업 권장 우선순위

1. **P0 (Critical)**: Tooltip/Popup 8개 컴포넌트 토큰 교체 + `--text-dim` light값 상향
2. **P1 (High)**: Recharts hex → CSS var (6 컴포넌트)
3. **P1 (High)**: 11개 등급 C 컴포넌트의 배경/테두리 토큰 교체
4. **P2 (Medium)**: focus-visible ring + `text-white` 5건 + 투명도 텍스트
5. **P3 (Low)**: PipelineStatus pulse + Stale 배지 min-opacity
