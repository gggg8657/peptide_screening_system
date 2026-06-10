# SSTR2 AI Co-Scientist Dashboard — Frontend

React + TypeScript + Vite 기반 실시간 파이프라인 대시보드.

## Tech Stack

| 항목 | 스택 |
|------|------|
| Framework | React 19 + TypeScript (strict mode) |
| Build | Vite |
| 3D Viewer | Mol\* (Molstar) v5.6.1 |
| Charts | Recharts |
| Styling | Tailwind CSS |
| Testing | Vitest + React Testing Library |

## Components (12)

| Component | 설명 |
|-----------|------|
| `App.tsx` | 루트 레이아웃, Context providers |
| `PipelineStatus.tsx` | 파이프라인 step 진행 카드 |
| `CandidateTable.tsx` | 후보 분자 정렬/필터/선택 테이블 |
| `AgentFlowDiagram.tsx` | 에이전트 흐름 시각화 (DAG) |
| `AgentMonitor.tsx` | 에이전트 상태 실시간 모니터 |
| `ConvergenceGraph.tsx` | ddG 수렴 그래프 (Recharts) |
| `QCGateChart.tsx` | QC 게이트 통과/실패 차트 |
| `MoleculeViewer.tsx` | Mol\* 3D 구조 뷰어 (4-mode preset) |
| `VisualizationPanel.tsx` | PyMOL 렌더링 이미지 패널 |
| `ExperimentControl.tsx` | 실험 시작/중지/설정 컨트롤 |
| `ValidationPanel.tsx` | 약리학적 검증 패널 |
| `PharmacologyPanel.tsx` | 13가지 물성 계산 결과 표시 |
| `RiskMatrix.tsx` | 위험 매트릭스 시각화 |

## Hooks (6, ~660 lines)

| Hook | 설명 |
|------|------|
| `usePipelineStatus.ts` | 백엔드 폴링 + 실시간 상태 관리 (AbortController) |
| `useCandidateSort.ts` | 후보 테이블 정렬/필터 로직 |
| `useAdmetBatch.ts` | ADMET 배치 계산 요청 관리 |
| `useSelection.ts` | 후보 선택 상태 관리 |
| `useValidation.ts` | 검증 데이터 페칭/캐싱 |
| `useExperiment.ts` | 실험 설정/실행 상태 관리 |

## Tests (32 Vitest tests)

```
src/hooks/__tests__/useSelection.test.ts
src/hooks/__tests__/useCandidateSort.test.ts
src/hooks/__tests__/useValidation.test.ts
src/components/__tests__/CandidateTable.test.tsx
```

실행:
```bash
cd frontend
npm run test        # watch mode
npm run test:ci     # CI mode (single run)
```

## Development

```bash
cd frontend
npm install
npm run dev         # http://localhost:5173
npm run build       # production build → dist/
npm run lint        # ESLint check
```

## Architecture Notes

- Backend API: `http://localhost:8787/api/` (FastAPI)
- 라이브 데이터 없을 시 mock 데이터 fallback (명확한 "Mock" 라벨 표시)
- Mol\* 뷰어: `applyPreset` API로 4가지 프리셋 지원 (default, ligand, all-models, polymer-cartoon)
- 전체 시스템 아키텍처: [ARCHITECTURE.md](../ARCHITECTURE.md)
