# Handoff · SSTR2 AI Co-Scientist Dashboard

> **목표**: 본 디자인 prototype을 SST14-M_scr 기존 코드베이스에 통합 — FastAPI(:8787) 백엔드 + React 19 + Vite + Tailwind v4 프론트엔드.

## 1. About the Design Files

`prototype/` 폴더의 HTML/JSX 파일은 **디자인 레퍼런스**입니다. 그대로 production에 배포하는 게 아니라, **기존 코드베이스의 환경 (React 19 + Vite 7 + TS + Tailwind v4 + Molstar 5.6 + Radix UI)** 에서 같은 모양·동작을 재구현하는 것이 목표입니다.

`prototype/SSTR2 Dashboard.html`을 브라우저에서 열면 6개 화면 (Run Console / Selectivity / Candidate Review / Run Launcher / LLM Benchmark / Wetlab Order) 의 디자인과 인터랙션을 확인할 수 있습니다.

## 2. Fidelity

**High-fidelity** — 색, 타이포, 간격, 인터랙션 모두 final. 정확히 복제 권장.

- 폰트: Inter (sans) + JetBrains Mono (mono)
- 색: OKLCH 토큰 (cyan-teal accent 200°, pos 145°, warn 60°, neg 25°)
- 간격: 1px hairline borders, 4px radius, no shadows
- 데이터 표시: tabular-nums, 변이 위치 highlight, 시퀀스 ruler

자세한 토큰은 `prototype/styles.css` 참조 또는 `FRONTEND_INTEGRATION.md` 의 Tailwind config snippet 사용.

## 3. Screens / Views

| ID | 이름 | 용도 | 대상 사용자 | 기존 페이지 매핑 |
|----|------|------|--------------|-------------------|
| A | Run Console | 실행 중 파이프라인 모니터 | Operator | `SiloAPage` + `SiloBPage` 통합 |
| B | Selectivity Explorer | iPTM 매트릭스 + 후보 drill-down | Reviewer | `SelectivityPage` 교체 |
| C | Candidate Review | 단일 후보 (cand03) 깊이 검토 | PI | **신규** `/candidate/:id` |
| D | Run Launcher | 새 실행 설정 + gate 임계값 조정 | Operator | **신규** `/run/new` |
| E | LLM Benchmark | 5 sLLM × 3 flow 비교 | Engineer | `llm_benchmark/ui` 통합 |
| F | Wetlab Order | in-vitro Ki 발주서 + 승인 | Lab manager | **신규** `/wetlab/orders` |

## 4. Integration Plan

### Phase 1 · Quick Preview (1 시간)
- `prototype/` 전체를 `frontend/public/prototype/`에 복사
- `App.tsx` 에 `/prototype` 라우트 추가 (iframe)
- 디자인 검증 + 피드백 수집용

### Phase 2 · Component 포팅 (3–4 일)
- Tailwind theme tokens 적용 (`FRONTEND_INTEGRATION.md` § 1)
- 공통 컴포넌트 추출: `Sequence`, `TierBadge`, `HeatmapCell`, `Panel`, `ScoreBar`, `GateChip`
- `PipelineFlow` 포팅 — silo별 모듈 분기
- 화면 A → B → C 순서로 포팅
- 데이터는 mock(MSW)으로 시작

### Phase 3 · Backend 연결 (2–3 일)
- 신규 router 5개 추가 (`backend/routers/` 참조)
- 기존 router 응답 shape 조정 — `API_CONTRACT.md` § 2 참조
- 프론트 hooks 활성화

### Phase 4 · 신규 화면 (D/E/F) (3 일)
- Run Launcher → `POST /api/runs/start` 연결
- LLM Benchmark → `GET /api/benchmark/results` (기존 `llm_benchmark/analysis/` JSON 서빙)
- Wetlab Order → `GET/POST /api/wetlab/orders/*`

## 5. Layout · 핵심 패턴

```
─────────────────────────────────────────────────
 Header  (44px) — 로고 · 네비 · 실행 status · theme
─────────────────────────────────────────────────
 Subheader (auto) — 메타 (target, silo toggle, iter)
─────────────────────────────────────────────────
 Main grid (flex-1)
   ┌──────────────────────────┬──────────────┐
   │ Pipeline / Heatmap       │ Agent rail   │
   │                          │ (360px)      │
   ├──────────────────────────┤              │
   │ Candidates table         │              │
   └──────────────────────────┴──────────────┘
   detail drawer 380px (slideable)
─────────────────────────────────────────────────
```

- 좌측: scrollable main content
- 우측: sticky agent rail (Variant A only) — 토글 가능
- 하단 drawer: 후보 클릭 시 380px 우측에서 슬라이드

## 6. Components

자세한 spec 은 `prototype/`의 각 jsx 파일 참조. 핵심:

### `PipelineFlow` (`prototype/pipeline_flow.jsx`)
- Props: `silo: "A" | "B" | "Combined"`, `onSelectStage`, `selectedStage`
- 데이터: `PROJECT_DATA.pipelines[silo]` — silo별 다른 stage 배열
- Combined는 parallel tracks → converge 형태
- 각 stage 카드: status dot, ID + name, tool, in/out count, progress bar (running), gate label, time, GPU

### `Sequence` (`prototype/shared.jsx`)
- Props: `seq: string`, `wildtype?: string`, `showRuler?: boolean`, `big?: boolean`
- 14 aa 박스, wildtype 대비 변이 위치 highlight
- Cys (C) 노랑, FWKT pharmacophore (pos 6-9) 보라 highlight

### `HeatmapCell` (`prototype/shared.jsx`)
- Props: `value: number (0-1)`, `isBest`, `isTarget`, `selected`, `onClick`
- iPTM 색 매핑: oklch 보간, 0.75–1.0 범위
- best receptor 진한 outline, target SSTR2 점선 outline

### `TierBadge` (`prototype/shared.jsx`)
- T2 (pos · 녹색), T1 (warn · amber), T0 (neg · red)

## 7. State Management

각 화면이 관리하는 state:

| Screen | State |
|--------|-------|
| A | `silo` (A/B/Combined), `selectedCandidate`, `hoverGate`, `tick` (animation) |
| B | `selectedCell { cand, receptor }`, `tierFilter: Set`, `showWildtype` |
| C | `viewMode` (ribbon/surface/stick), `selectedVariant` |
| D | `silo`, `iterations`, `nBackbone`, `kSeq`, `topM`, `llm`, `seed`, `gates {...}`, `offTargets: Set` |
| E | `phase`, `metric` (pass_rate/time/candidates/t2/cost), `hoverCell` |
| F | `stage` (draft/review/approval/PO/shipped) |

전역: theme (light/dark), accent hue, density, font — `useTheme()` 훅 1개로 통합 권장.

## 8. Files in This Bundle

```
design_handoff_sstr2_dashboard/
├── README.md                      ← 이 파일
├── API_CONTRACT.md                ← 백엔드 endpoint 응답 shape
├── FRONTEND_INTEGRATION.md        ← Tailwind config + TSX 포팅 가이드
├── prototype/                     ← HTML/JSX 디자인 레퍼런스 (15개 파일)
├── backend/                       ← FastAPI router stub (5개)
│   ├── routers/
│   │   ├── agents.py              ← SSE stream — 5-agent log
│   │   ├── cand03_variants.py     ← 변이체 카탈로그 (기존 JSON 서빙)
│   │   ├── runs.py                ← 새 실행 start/list/status
│   │   ├── benchmark.py           ← LLM benchmark 결과
│   │   └── wetlab.py              ← in-vitro 발주 CRUD
│   └── schemas.py                 ← Pydantic models
└── frontend/                      ← TSX 시작점
    ├── hooks/                     ← 데이터 fetching hooks (6개)
    ├── components/                ← 공통 컴포넌트 (3개 예시)
    └── styles/
        └── tokens.css             ← CSS vars (Tailwind 보조)
```

## 9. Design Tokens

`prototype/styles.css` :root 블록 참조. 핵심:

| Token | Light | Dark |
|-------|-------|------|
| `--bg` | `#fafaf9` | `#0c0a09` |
| `--bg-elev` | `#ffffff` | `#18181b` |
| `--border` | `#e7e5e4` | `#27272a` |
| `--text` | `#1c1917` | `#f5f5f4` |
| `--accent` | `oklch(0.58 0.13 200)` | `oklch(0.72 0.13 200)` |
| `--pos` | `oklch(0.55 0.13 145)` | `oklch(0.72 0.14 145)` |
| `--warn` | `oklch(0.62 0.15 60)` | `oklch(0.78 0.15 70)` |
| `--neg` | `oklch(0.55 0.2 25)` | `oklch(0.7 0.18 25)` |

## 10. Assets

- **Real data**: `docs/selectivity_demo_20260511/boltz_summary.json` (10 cand × 5 SSTR iPTM)
- **PDB**: 7XNA (SSTR2 holo) from RCSB — Mol* 직접 fetch
- **Icons**: 직접 inline SVG (lucide 호환 스타일)
- **Fonts**: Google Fonts CDN — Inter, JetBrains Mono, IBM Plex {Sans,Mono}, Geist {Sans,Mono}, Space Grotesk/Mono, DM Sans/Mono

## 11. Open Items

1. **5-agent live log**: 현재 prototype은 정적 데이터. backend에서 SSE 또는 WebSocket 으로 stream 필요 — `backend/routers/agents.py` stub 참조.
2. **Mol* per-candidate pose**: prototype은 7XNA holo만 로드. 각 후보의 docked pose 보려면 `pose_a_*.pdb` 를 `/api/static/`으로 서빙 + Mol* 에 multi-structure 로드.
3. **Gate hover tooltip**: 현재 hover 시 placeholder text. 실제 fail 사유는 `step_audit_log.json` 참조 필요.
4. **Wetlab order workflow**: backend 신규 — 발주 → PI 승인 → PO → shipped 상태 머신.

---

## Quick start (after reading this)

```bash
# 1. Phase 1 — iframe 으로 임시 통합
cp -r prototype/ <your-frontend>/public/prototype/
# App.tsx 에 라우트 추가:
#   <Route path="/prototype" element={<iframe src="/prototype/SSTR2 Dashboard.html" />} />

# 2. Phase 2 — 백엔드 신규 router 마운트
cp backend/routers/*.py <your-backend>/routers/
cp backend/schemas.py <your-backend>/schemas/dashboard.py
# main.py 에 마운트:
#   from .routers import agents, cand03_variants, runs, benchmark, wetlab
#   app.include_router(agents.router, prefix="/api/agents")
#   ...

# 3. Phase 3 — 프론트 hooks 활성화
cp -r frontend/hooks <your-frontend>/src/hooks/
cp -r frontend/components <your-frontend>/src/components/
cp frontend/styles/tokens.css <your-frontend>/src/styles/

# Tailwind config 에 토큰 추가 — FRONTEND_INTEGRATION.md § 1 참조
```

`API_CONTRACT.md` 와 `FRONTEND_INTEGRATION.md` 를 다음에 읽으세요.
