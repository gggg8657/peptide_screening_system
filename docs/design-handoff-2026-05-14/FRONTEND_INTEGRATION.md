# Frontend Integration · TSX 포팅 가이드

> 대상: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/frontend/`
> 스택: React 19 + Vite 7 + TypeScript + Tailwind v4 + Radix UI + Molstar 5.6 + Recharts 3

## 1. Tailwind v4 · 디자인 토큰 등록

`src/styles/tokens.css` 신규:

```css
/* OKLCH 토큰 — 라이트/다크 + accent hue 가변 */
:root {
  --accent-hue: 200;
  --pos-hue: 145;
  --warn-hue: 60;
  --neg-hue: 25;
  --violet-hue: 290;
  --teal-hue: 180;
}

:root,
[data-theme="light"] {
  --bg: #fafaf9;
  --bg-elev: #ffffff;
  --bg-sunk: #f5f5f4;
  --border: #e7e5e4;
  --border-strong: #d6d3d1;
  --text: #1c1917;
  --text-mute: #57534e;
  --text-dim: #a8a29e;
  --accent: oklch(0.58 0.13 var(--accent-hue));
  --accent-soft: oklch(0.94 0.04 var(--accent-hue));
  --accent-text: oklch(0.42 0.13 var(--accent-hue));
  --pos: oklch(0.55 0.13 var(--pos-hue));
  --pos-soft: oklch(0.94 0.06 var(--pos-hue));
  --warn: oklch(0.62 0.15 60);
  --warn-soft: oklch(0.94 0.08 70);
  --neg: oklch(0.55 0.2 var(--neg-hue));
  --neg-soft: oklch(0.94 0.07 var(--neg-hue));
}

[data-theme="dark"] {
  --bg: #0c0a09;
  --bg-elev: #18181b;
  --bg-sunk: #0a0a0a;
  --border: #27272a;
  --border-strong: #3f3f46;
  --text: #f5f5f4;
  --text-mute: #a8a29e;
  --text-dim: #57534e;
  --accent: oklch(0.72 0.13 var(--accent-hue));
  --accent-soft: oklch(0.28 0.05 var(--accent-hue));
  --accent-text: oklch(0.82 0.12 var(--accent-hue));
  --pos: oklch(0.72 0.14 var(--pos-hue));
  --pos-soft: oklch(0.25 0.05 var(--pos-hue));
  --warn: oklch(0.78 0.15 70);
  --warn-soft: oklch(0.28 0.07 70);
  --neg: oklch(0.7 0.18 var(--neg-hue));
  --neg-soft: oklch(0.28 0.08 var(--neg-hue));
}
```

Tailwind v4 (`@theme` 블록 in `src/index.css`):

```css
@import "tailwindcss";
@import "./styles/tokens.css";

@theme {
  --color-bg: var(--bg);
  --color-bg-elev: var(--bg-elev);
  --color-bg-sunk: var(--bg-sunk);
  --color-border-base: var(--border);
  --color-border-strong: var(--border-strong);
  --color-text-base: var(--text);
  --color-text-mute: var(--text-mute);
  --color-text-dim: var(--text-dim);
  --color-accent: var(--accent);
  --color-accent-soft: var(--accent-soft);
  --color-pos: var(--pos);
  --color-pos-soft: var(--pos-soft);
  --color-warn: var(--warn);
  --color-warn-soft: var(--warn-soft);
  --color-neg: var(--neg);
  --color-neg-soft: var(--neg-soft);

  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}
```

이제 `bg-bg-elev`, `text-accent`, `border-border-base`, `font-mono` 등으로 사용 가능.

`@font-face` 또는 `<link>`로 Inter / JetBrains Mono 로드 (이미 frontend 에 있다면 skip).

## 2. Theme 훅

`src/hooks/useTheme.ts`:

```ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ThemeStore {
  theme: 'light' | 'dark';
  accentHue: number;
  density: 'compact' | 'normal' | 'spacious';
  setTheme: (t: 'light' | 'dark') => void;
  setAccentHue: (h: number) => void;
  setDensity: (d: 'compact' | 'normal' | 'spacious') => void;
}

export const useTheme = create<ThemeStore>()(
  persist(
    (set) => ({
      theme: 'light',
      accentHue: 200,
      density: 'normal',
      setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        set({ theme });
      },
      setAccentHue: (accentHue) => {
        document.documentElement.style.setProperty('--accent-hue', String(accentHue));
        set({ accentHue });
      },
      setDensity: (density) => set({ density }),
    }),
    { name: 'sstr2-theme' }
  )
);
```

App 진입점에서 첫 마운트 시 `data-theme` 반영:

```tsx
// src/main.tsx
const { theme, accentHue } = useTheme.getState();
document.documentElement.setAttribute('data-theme', theme);
document.documentElement.style.setProperty('--accent-hue', String(accentHue));
```

## 3. Data hooks · React Query 추천

```bash
npm install @tanstack/react-query
```

`src/hooks/useRunStatus.ts`:

```ts
import { useQuery } from '@tanstack/react-query';

export interface RunStatus {
  run_id: string;
  started_at: string;
  duration_seconds: number;
  iteration: number;
  max_iterations: number;
  silo: 'A' | 'B' | 'A+B';
  llm_model: string;
  gpus: string;
  seed: number;
  current_step: string;
  progress: number;
  state: 'running' | 'done' | 'failed';
}

export function useRunStatus(runId: string | undefined) {
  return useQuery<RunStatus>({
    queryKey: ['status', runId],
    queryFn: () => fetch(`/api/status?run_id=${runId}`).then(r => r.json()),
    enabled: !!runId,
    refetchInterval: 5000,  // poll every 5s
  });
}
```

`src/hooks/useAgentLog.ts` (SSE):

```ts
import { useEffect, useState } from 'react';

export interface AgentEntry {
  ts: string;
  agent: string;
  level: 'info' | 'warn' | 'error';
  text: string;
}

export function useAgentLog(runId: string | undefined) {
  const [entries, setEntries] = useState<AgentEntry[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!runId) return;
    // Initial log fetch
    fetch(`/api/agents/${runId}/log`)
      .then(r => r.json())
      .then(d => setEntries(d.entries));

    // SSE stream
    const es = new EventSource(`/api/agents/${runId}/stream`);
    es.addEventListener('agent', (e: MessageEvent) => {
      setEntries(prev => [...prev, JSON.parse(e.data)]);
    });
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    return () => es.close();
  }, [runId]);

  return { entries, connected };
}
```

`src/hooks/useSelectivity.ts`, `useCandidates.ts`, `usePipeline.ts`, `useBenchmark.ts`, `useWetlab.ts` 도 같은 패턴. `frontend/hooks/` 폴더 참조.

## 4. Mol* — npm 패키지 통합

```bash
cd frontend
npm install molstar
```

`src/components/Molstar.tsx`:

```tsx
import { useEffect, useRef } from 'react';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui';
import { renderReact18 } from 'molstar/lib/mol-plugin-ui/react18';
import 'molstar/lib/mol-plugin-ui/skin/light.scss';
import type { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';

interface Props {
  pdbId?: string;
  pdbUrl?: string;
  height?: number;
}

export function Molstar({ pdbId = '7XNA', pdbUrl, height = 320 }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const pluginRef = useRef<PluginUIContext | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!ref.current) return;

    (async () => {
      const plugin = await createPluginUI({
        target: ref.current!,
        render: renderReact18,
        spec: {
          layout: {
            initial: {
              isExpanded: false,
              showControls: false,
            },
          },
          components: {
            remoteState: 'none',
          },
        },
      });
      if (cancelled) {
        plugin.dispose();
        return;
      }
      pluginRef.current = plugin;

      const url = pdbUrl ?? `https://files.rcsb.org/download/${pdbId}.pdb`;
      const data = await plugin.builders.data.download(
        { url, isBinary: false },
        { state: { isGhost: false } }
      );
      const trajectory = await plugin.builders.structure.parseTrajectory(data, 'pdb');
      await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default');
    })();

    return () => {
      cancelled = true;
      pluginRef.current?.dispose();
    };
  }, [pdbId, pdbUrl]);

  return (
    <div
      ref={ref}
      style={{ height, width: '100%' }}
      className="rounded border border-border-base bg-bg-sunk overflow-hidden"
    />
  );
}
```

Per-candidate pose 보기:
```tsx
<Molstar pdbUrl={`/api/static/${runId}/05_docking/pose_a_${candId}.pdb`} />
```

## 5. 컴포넌트 포팅 매핑

각 prototype JSX → TSX 변환 가이드:

| Prototype | → 신규 TSX | 비고 |
|-----------|-----------|------|
| `prototype/shared.jsx::TierBadge` | `src/components/TierBadge.tsx` | 그대로 |
| `prototype/shared.jsx::Sequence` | `src/components/Sequence.tsx` | 그대로, props type 추가 |
| `prototype/shared.jsx::HeatmapCell` | `src/components/HeatmapCell.tsx` | 그대로 |
| `prototype/shared.jsx::ScoreBar` | `src/components/ScoreBar.tsx` | 그대로 |
| `prototype/shared.jsx::GateChip` | `src/components/GateChip.tsx` | Radix Popover 로 hover tooltip 교체 권장 |
| `prototype/shared.jsx::MolViewer` | `src/components/Molstar.tsx` | npm Mol* (위 § 4 참조) |
| `prototype/pipeline_flow.jsx::PipelineFlow` | `src/components/PipelineFlow.tsx` | silo prop, useQuery 로 fetch |
| `prototype/variant_a.jsx::VariantA` | `src/pages/RunConsolePage.tsx` | 라우트 `/runs/:runId` |
| `prototype/variant_b.jsx::VariantB` | `src/pages/SelectivityPage.tsx` | 기존 페이지 교체 |
| `prototype/variant_c.jsx::VariantC` | `src/pages/CandidatePage.tsx` | 라우트 `/candidates/:id` |
| `prototype/screen_launcher.jsx::ScreenLauncher` | `src/pages/RunLauncherPage.tsx` | 라우트 `/runs/new` |
| `prototype/screen_benchmark.jsx::ScreenBenchmark` | `src/pages/BenchmarkPage.tsx` | 라우트 `/benchmark` |
| `prototype/screen_wetlab.jsx::ScreenWetlab` | `src/pages/WetlabOrderPage.tsx` | 라우트 `/wetlab/:orderId` |

## 6. Inline styles → Tailwind 변환 패턴

Prototype은 `style={{}}` inline 위주. 일관성 + 다크모드 위해 Tailwind 로 변환 권장.

```tsx
// Before (prototype)
<div style={{
  background: "var(--bg-elev)",
  border: "1px solid var(--border)",
  borderRadius: 4,
  padding: "8px 10px",
}}>

// After (Tailwind v4 + tokens)
<div className="bg-bg-elev border border-border-base rounded p-2">
```

주요 헬퍼 클래스 (위 `tokens.css` 등록 시):

```
bg-bg / bg-bg-elev / bg-bg-sunk
text-text / text-text-mute / text-text-dim
border-border-base / border-border-strong
text-accent / bg-accent / bg-accent-soft
text-pos / text-warn / text-neg
font-mono / font-sans
```

`.bio-panel`, `.bio-table` 같은 prototype 클래스는 `src/components/Panel.tsx`, `src/components/DataTable.tsx` 로 캡슐화 후 import.

## 7. Live data 전환 단계

1. **mock first** — MSW로 `API_CONTRACT.md`의 응답 shape 모킹
   ```bash
   npm install msw -D
   # src/mocks/handlers.ts 에서 각 endpoint mock
   ```
2. **데이터 정합 확인** — prototype 의 hardcoded 값과 mock 일치 확인
3. **실제 backend 연결** — `vite.config.ts` 에 proxy 추가:
   ```ts
   server: {
     proxy: { '/api': 'http://127.0.0.1:8787' }
   }
   ```
4. **에러/로딩 상태** — React Query 의 `isPending`, `isError`, `error.message` 활용

## 8. Routing

`src/App.tsx` 라우트 추가:

```tsx
<Routes>
  <Route path="/" element={<HomePage />} />
  <Route path="/runs/new" element={<RunLauncherPage />} />
  <Route path="/runs/:runId" element={<RunConsolePage />} />
  <Route path="/candidates/:id" element={<CandidatePage />} />
  <Route path="/selectivity" element={<SelectivityPage />} />
  <Route path="/benchmark" element={<BenchmarkPage />} />
  <Route path="/wetlab/:orderId" element={<WetlabOrderPage />} />
</Routes>
```

## 9. 권장 패키지 (npm install)

```bash
npm install \
  molstar \
  @tanstack/react-query \
  zustand \
  date-fns \
  clsx \
  recharts   # 이미 있다면 skip
```

dev 전용:
```bash
npm install -D msw @types/node
```

## 10. 검증 체크리스트

포팅 후 다음을 확인:

- [ ] light/dark 토글이 모든 화면에서 작동
- [ ] silo 토글 시 PipelineFlow stage 배열이 바뀜
- [ ] Selectivity 셀 클릭 → drawer 열림
- [ ] Mol* 가 7XNA 로딩 성공 (RCSB 접근 가능 환경에서)
- [ ] Run Launcher 의 gate slider 변경이 우측 예상 통과율 갱신
- [ ] Wetlab Order 의 stage 토글이 backend 상태 머신 호출
- [ ] Korean labels + English technical terms 혼용 유지 (i18n 도입 X — 그대로 hard-coded)
- [ ] Tabular-nums 가 모든 숫자 컬럼에 적용 (`font-feature-settings: "tnum"`)
