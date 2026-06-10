# UI P1-B Fix — 등급 C 11 컴포넌트 토큰화

## 배경
reviewer-uiux 감사 (`_workspace/release/sod-2026-05-18-ui-audit.md`): 11개 컴포넌트가 slate 팔레트 전반 사용으로 라이트 테마에서 깨짐. 등급 C (실패).

## 대상 11 컴포넌트
1. `src/components/CandidateTable.tsx` — slate 팔레트 + 파생 배지 색
2. `src/components/PharmacologyPanel.tsx` (Tooltip은 P0에서 처리 — 나머지 slate)
3. `src/components/AgentMonitor.tsx` — `bg-slate-900/800/950` 전반
4. `src/components/ValidationPanel.tsx` — 체크박스 `bg-slate-800 border-slate-600` + Modal `bg-slate-900` + 오버레이 `bg-black/70`
5. `src/components/MutationAnalysis.tsx` — summary card `bg-slate-800/60`×4
6. `src/components/RiskMatrix.tsx` — Modal `bg-slate-900 border-slate-700`, 셀 배경
7. `src/components/SARHeatmap.tsx` (P1-A에서 SVG hex 처리, 나머지 잔재)
8. `src/components/RunComparisonPanel.tsx` — `text-slate-300` 전반 + chart hex (P1-A 후 잔재)
9. `src/components/CandidateCompareModal.tsx:157,212` — `bg-slate-900 border-slate-700/60` + `text-cyan-600 (9px)`
10. `src/components/VisualizationPanel.tsx:83,140` — `text-slate-300` (loading) + `bg-slate-950/60` (overlay)
11. `src/components/HeuristicBanner.tsx:40,48` — `text-green-300/yellow-300/orange-300/red-300` → 토큰

## 일괄 치환 규칙 (mechanical)
- `bg-slate-{950,900}` → `bg-[var(--bg)]`
- `bg-slate-{800,700}` → `bg-[var(--bg-elev)]`
- `bg-slate-800/50`, `bg-slate-800/60` → `bg-[var(--bg-sunk)]`
- `text-slate-{100,200}` → `text-[var(--text)]`
- `text-slate-{300,400}` → `text-[var(--text-mute)]`
- `text-slate-{500,600}` → `text-[var(--text-dim)]`
- `border-slate-{600~900}` → `border-[var(--border)]`
- `border-slate-700/{40,60}` → `border-[var(--border)]`
- `bg-black/70`, `bg-black/80` → `bg-[var(--bg-sunk)]/80` + `backdrop-blur`
- `bg-slate-950/60` → `bg-[var(--bg-sunk)]/70`
- `text-green-300` → `text-[var(--pos)]`
- `text-yellow-300`, `text-amber-300` → `text-[var(--warn)]`
- `text-orange-300` → `text-[var(--warn)]`
- `text-red-300` → `text-[var(--neg)]`
- `text-cyan-600` (9px) → `text-[var(--text-dim)]`

## 검증
- `npx tsc --noEmit` 0 에러
- `npx eslint .` 0 에러
- 잔여 slate-* / gray-* 검색 — 11 컴포넌트 합산 0건 확인

## 제약
- **branch 신설**: `fix/ui-p1b-grade-c-components`
- **PR title**: `fix(fe): UI P1-B — 등급 C 11 컴포넌트 slate → OKLCH 토큰 일괄 변환`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 손대지 말 것
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- 마감: PR 생성 후 PR URL + 변경 파일 리스트 + 잔여 slate 카운트 보고
