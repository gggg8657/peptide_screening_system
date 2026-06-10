# UI P0 Fix — Tooltip 토큰화 + text-dim 상향

## 배경
reviewer-uiux 감사 결과 (`_workspace/release/sod-2026-05-18-ui-audit.md`): 신규 OKLCH 토큰 페이지 + 구형 slate 컴포넌트 혼재로 라이트 테마에서 구형이 깨짐. **가장 심각한 두 가지**:

1. **Tooltip/Popup 8개 컴포넌트가 `bg-slate-800 border-slate-700 text-slate-300`** — 라이트 테마에서 팝업이 다크 배경으로 떠 가독성 0
2. **`tokens.css --text-dim: #a8a29e` light값 대비비 2.9:1** — WCAG AA 미달 (4.5:1 필요)

## 작업

### Fix 1: Tooltip 토큰화 (5 파일, 8건)
- `src/components/CandidateTable.tsx` 라인 103, 256, 330, 386 — 4건
- `src/components/AgentMonitor.tsx` 라인 35 — 1건
- `src/components/PharmacologyPanel.tsx` 라인 143 (MetricCard `bg-slate-800/50 border-slate-700/60`) — 1건
- `src/components/PharmacologyPanel.tsx` 라인 303 (드롭다운 `bg-slate-900 border-slate-700`) — 1건
- `src/components/CandidateTable.tsx` 라인 501, 504, 517, 526, 539, 548 (table header tooltip×6 `bg-slate-800 border-slate-700/40`) — 6건 추가 발견

**일괄 치환 규칙**:
- `bg-slate-800` → `bg-[var(--bg-elev)]`
- `bg-slate-900` → `bg-[var(--bg-elev)]`
- `bg-slate-800/50`, `bg-slate-800/40` → `bg-[var(--bg-sunk)]`
- `border-slate-700`, `border-slate-700/60`, `border-slate-700/40` → `border-[var(--border)]`
- `text-slate-300` → `text-[var(--text)]`
- `text-slate-400` → `text-[var(--text-mute)]`

### Fix 2: --text-dim light값 상향
- `src/styles/tokens.css:37` — `--text-dim: #a8a29e` → `#78716c` (대비비 4.6:1, WCAG AA 통과)

## 검증
- `npx tsc --noEmit` 0 에러
- `npx eslint .` 0 에러
- Vite HMR 자동 반영. FE :5173 정상.

## 제약
- **branch 신설**: `fix/ui-p0-tooltip-textdim`
- **PR title**: `fix(fe): UI P0 — Tooltip 토큰화 (8 컴포넌트) + --text-dim 대비비 상향 (WCAG AA)`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 (`src/components/__tests__/*.test.tsx`) 손대지 말 것
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- 마감: PR 생성 (`gh pr create`) 후 PR URL + 변경 파일 리스트 보고
