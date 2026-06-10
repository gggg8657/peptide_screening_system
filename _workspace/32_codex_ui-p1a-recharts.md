# UI P1-A Fix — Recharts inline hex → CSS var

## 배경
reviewer-uiux 감사 (`_workspace/release/sod-2026-05-18-ui-audit.md`): 6개 컴포넌트가 Recharts에 inline hex 색상 직접 사용 — 라이트 테마에서 배경과 동화되거나 불가시.

## 작업: 6 파일 일괄 토큰화

### 파일 + 변경 매핑
- `src/components/ConvergenceGraph.tsx:134` — `stroke="#1e293b"` → `stroke="var(--border)"`
- `src/components/ConvergenceGraph.tsx:171` — `stroke="#22d3ee"` → `stroke="var(--teal)"`
- `src/components/ConvergenceGraph.tsx:180` — `stroke="#3b82f6"` → `stroke="var(--accent)"`
- `src/components/ConvergenceGraph.tsx:190` — `fill="#7c3aed"` → `fill="var(--violet)"`
- `src/components/DdGDistribution.tsx:130` — `stroke="#1e293b"` → `stroke="var(--border)"`
- `src/components/DdGDistribution.tsx:149` — `stroke="#ef4444"` → `stroke="var(--neg)"`
- `src/components/DdGDistribution.tsx:154` — `fill="#22d3ee"` → `fill="var(--teal)"`
- `src/components/QCGateChart.tsx:151` — `stroke="#1e293b"` → `stroke="var(--border)"`
- `src/components/QCGateChart.tsx` 기타 `PASS_COLOR`, `FAIL_COLOR` 상수 — CSS var로 교체 (필요 시 `getComputedStyle(document.documentElement).getPropertyValue('--pos')` 등 helper 사용)
- `src/components/MutationAnalysis.tsx:210` — `contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}` → `var(--bg-elev)`, `var(--border)`
- `src/components/MutationAnalysis.tsx` 차트 hex 다수 — 동일 패턴 토큰화
- `src/components/RunComparisonPanel.tsx:31` — `stroke="#4ade80"` → `var(--pos)`, `stroke="#f87171"` → `var(--neg)`
- `src/components/SequenceLogo.tsx:136,137,141` — `fill="#64748b"`, `stroke="#1e293b"` → `var(--text-dim)`, `var(--border)`
- `src/components/SARHeatmap.tsx:118,130` — `fill="#facc15"` → `var(--warn)`
- `src/components/SARHeatmap.tsx:147,165,175,187` — `fill="#64748b/#334155/#f1f5f9"` → `var(--text-dim)/var(--bg-sunk)/var(--text)`
- `src/components/MoleculeViewer.tsx:205` — `style={{ backgroundColor: '#0f172a' }}` → `'var(--bg-sunk)'`

### Recharts contentStyle 처리
inline 값은 CSS var를 직접 받을 수 없는 경우가 있음. helper 사용:
```typescript
const getThemeVar = (name: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim();
```
또는 SVG `currentColor` + CSS로 처리.

## 검증
- `npx tsc --noEmit` 0 에러
- `npx eslint .` 0 에러
- 다크/라이트 두 테마 모두에서 차트 가시성 확인 (사용자 시각 검증은 후속)

## 제약
- **branch 신설**: `fix/ui-p1a-recharts-tokens`
- **PR title**: `fix(fe): UI P1-A — Recharts inline hex → CSS var (6 컴포넌트)`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 손대지 말 것
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
