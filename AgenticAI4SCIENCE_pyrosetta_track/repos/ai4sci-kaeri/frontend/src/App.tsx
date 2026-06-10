import React, { Suspense, lazy, useState, useRef, useCallback } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import { FlaskConical, Wifi, WifiOff, Cpu, History, ChevronDown, Dna, GitCompareArrows, Info, Loader2, Settings2, ShieldCheck, BarChart3, Beaker, AlertTriangle, Check, MapPin, SlidersHorizontal } from 'lucide-react'
import { ThemeToggle } from './components/ThemeToggle'
import { usePipelineStatus } from './hooks/usePipelineStatus'
import { PipelineProvider } from './contexts/PipelineContext'
import { useClickOutside } from './hooks/useClickOutside'
import { computePipelineStateFlags } from './utils/pipelineStateFlags'
import './index.css'

// Lazy-loaded pages with ErrorBoundary isolation
const SiloBPage = lazy(() => import('./pages/SiloBPage').then(m => ({ default: m.SiloBPage })))
const SiloAPage = lazy(() => import('./pages/SiloAPage').then(m => ({ default: m.SiloAPage })))
const CombinedPage = lazy(() => import('./pages/CombinedPage').then(m => ({ default: m.CombinedPage })))
const AboutPage = lazy(() => import('./pages/AboutPage').then(m => ({ default: m.AboutPage })))
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const SelectivityPage = lazy(() => import('./pages/SelectivityPage').then(m => ({ default: m.SelectivityPage })))
const RunConsolePage = lazy(() => import('./pages/RunConsolePage').then(m => ({ default: m.RunConsolePage })))
const SelectivityExplorerPage = lazy(() => import('./pages/SelectivityExplorerPage').then(m => ({ default: m.SelectivityExplorerPage })))
const ManualSelectivityPage = lazy(() => import('./pages/ManualSelectivityPage').then(m => ({ default: m.ManualSelectivityPage })))
const CandidatePage = lazy(() => import('./pages/CandidatePage').then(m => ({ default: m.CandidatePage })))
const RunLauncherPage = lazy(() => import('./pages/RunLauncherPage').then(m => ({ default: m.RunLauncherPage })))
const BenchmarkPage = lazy(() => import('./pages/BenchmarkPage').then(m => ({ default: m.BenchmarkPage })))
const WetlabOrderPage = lazy(() => import('./pages/WetlabOrderPage').then(m => ({ default: m.WetlabOrderPage })))
const BindingPocketPage = lazy(() => import('./pages/BindingPocketPage').then(m => ({ default: m.BindingPocketPage })))
const StrategyRunnerPage = lazy(() => import('./pages/StrategyRunnerPage').then(m => ({ default: m.StrategyRunnerPage })))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

function PageLoader() {
  return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="w-6 h-6 text-[var(--accent)] animate-spin" />
    </div>
  )
}

class PageErrorBoundary extends React.Component<
  { children: React.ReactNode; pageName: string },
  { error: Error | null }
> {
  state = { error: null as Error | null }
  static getDerivedStateFromError(error: Error) { return { error } }
  render() {
    if (this.state.error) {
      return (
        <section className="card border border-[var(--neg)]/30 bg-[var(--neg-soft)] mt-4">
          <h2 className="text-sm font-semibold text-[var(--neg)] mb-2">
            {this.props.pageName} crashed
          </h2>
          <pre className="text-xs text-[var(--neg)] font-mono whitespace-pre-wrap">
            {this.state.error.message}
          </pre>
          <button
            onClick={() => this.setState({ error: null })}
            className="mt-2 px-3 py-1 text-xs bg-[var(--neg-soft)] text-[var(--neg)] border border-[var(--neg)]/30 rounded-lg hover:bg-[var(--neg-soft)]"
          >
            Retry
          </button>
        </section>
      )
    }
    return this.props.children
  }
}

// 마이그레이션 2026-05-14: 신규 6 화면이 primary. 구형 라우트(/silo-a, /silo-b, /combined, /selectivity)는 코드 보존, URL 직접만 접근.
const NAV_ITEMS = [
  { to: '/console', label: 'Run Console', icon: Dna, color: 'text-[var(--accent)]' },
  { to: '/selectivity-explorer', label: 'Selectivity', icon: ShieldCheck, color: 'text-[var(--pos)]' },
  { to: '/manual-selectivity', label: 'Manual Selectivity', icon: FlaskConical, color: 'text-[var(--warn)]' },
  { to: '/candidate', label: 'Candidate Review', icon: GitCompareArrows, color: 'text-[var(--teal)]' },
  { to: '/run/new', label: 'Run Launcher', icon: FlaskConical, color: 'text-[var(--violet)]' },
  { to: '/strategy-runner', label: 'Strategy Runner', icon: SlidersHorizontal, color: 'text-[var(--accent)]' },
  { to: '/benchmark', label: 'Benchmark', icon: BarChart3, color: 'text-[var(--warn)]' },
  { to: '/wetlab/orders', label: 'Wetlab', icon: Beaker, color: 'text-[var(--neg)]' },
  { to: '/binding-pocket', label: 'Pocket 설정', icon: MapPin, color: 'text-[var(--teal)]' },
  { to: '/settings', label: 'Settings', icon: Settings2, color: 'text-[color:var(--text-mute)]' },
  { to: '/about', label: 'About', icon: Info, color: 'text-[color:var(--text-mute)]' },
]

function AppLayout() {
  const live = usePipelineStatus(2000)

  // P04: isLive 단일 boolean → 4-상태 분리 판정
  // 우선순위: Stale > Archive > Active > Completed > Mock
  const { isActiveRun, isArchive, isCompletedSnapshot, isStale } =
    computePipelineStateFlags(live)

  // "실제 파이프라인 데이터를 보고 있음" (비-Mock 상태 전체)
  const isRealData = isActiveRun || isArchive || isCompletedSnapshot

  const timeSince =
    live.connected && live.updatedAt ? formatTimeSince(live.updatedAt) : '—'

  return (
    <PipelineProvider value={live}>
    <div className="min-h-screen" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      {/* Header — 마이그레이션: 신규 OKLCH 토큰 적용 */}
      <header
        className="sticky top-0 z-40 backdrop-blur-md"
        style={{ borderBottom: '1px solid var(--border)', background: 'color-mix(in oklch, var(--bg-elev) 92%, transparent)' }}
      >
        <div className="max-w-[1800px] mx-auto px-5 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-shrink-0">
            <div
              className="w-8 h-8 rounded-[3px] flex items-center justify-center font-mono font-bold text-[11px]"
              style={{ background: 'var(--text)', color: 'var(--bg-elev)' }}
            >
              P*
            </div>
            <div>
              <h1 className="text-sm font-semibold leading-tight tracking-tight" style={{ color: 'var(--text)' }}>
                PRST_N_FM &middot; SSTR2 AI Co-Scientist
              </h1>
              <p className="text-[11px] leading-tight" style={{ color: 'var(--text-mute)' }}>
                Agentic Multi-Step Optimization &middot; AG_src Monitor
              </p>
            </div>
          </div>

          {/* P04: run_id 헤더 중앙 상시 노출 */}
          <div className="flex-1 flex justify-center">
            {live.runId && isRealData && (
              <span
                className="font-mono text-[10px] rounded px-2 py-0.5 hidden md:inline"
                style={{ background: 'var(--bg-sunk)', border: '1px solid var(--border)', color: 'var(--text-mute)' }}
                title={`Run ID: ${live.runId}`}
              >
                {live.runId}
              </span>
            )}
          </div>

          <div className="flex items-center gap-5 text-xs flex-shrink-0">
            {isRealData && live.llmModel && (
              <div
                className="hidden md:flex items-center gap-1.5 rounded-lg px-2.5 py-1.5"
                style={{ background: 'var(--bg-sunk)', border: '1px solid var(--border)' }}
              >
                <Cpu className="w-3 h-3" style={{ color: 'var(--violet)' }} />
                <span className="text-[10px] font-medium" style={{ color: 'var(--violet)' }}>{live.llmModel.split('(')[0].trim()}</span>
              </div>
            )}

            {isRealData && live.executionMode === 'pyrosettaOnly' && (
              <div className="hidden md:flex items-center gap-1.5 bg-[var(--warn-soft)] border border-[var(--warn)]/30 rounded-lg px-2.5 py-1.5">
                <span className="text-[10px] text-[var(--warn)] font-semibold">PyRosetta-only</span>
              </div>
            )}

            {isRealData && (
              <div className="hidden sm:flex gap-1.5">
                <ApiBadge name="ESMFold" status={live.liveApis.esmfold} />
                <ApiBadge name="MolMIM" status={live.liveApis.molmim} />
                {live.executionMode === 'pyrosettaOnly' && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30">
                    PyRosetta-only
                  </span>
                )}
              </div>
            )}

            <div className="hidden sm:flex flex-col items-end">
              <span className="text-[color:var(--text-mute)] text-[10px]">Last sync</span>
              <span className="text-[color:var(--text-mute)] font-medium">{timeSince}</span>
            </div>
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-[color:var(--text-mute)] text-[10px]">Target</span>
              <span className="text-[color:var(--text-mute)] font-mono font-medium">&Delta;G &le; -8.5</span>
            </div>

            {live.archivedRuns.length > 0 && (
              <RunSelector
                runs={live.archivedRuns}
                currentRunId={live.viewingArchive ?? (isRealData ? live.runId : null)}
                isViewingArchive={!!live.viewingArchive}
                onSwitch={live.switchRun}
              />
            )}

            <ThemeToggle />

            {/* P04: 4-상태 배지 (우선순위: Stale > Archive > Active > Completed > Mock) */}
            <div
              role="status"
              aria-live="polite"
              aria-label={
                isStale
                  ? `마지막 갱신 ${timeSince}, 백엔드 응답 지연`
                  : isArchive
                    ? '보관된 run 보기'
                    : isActiveRun
                      ? '현재 실행 중인 run'
                      : isCompletedSnapshot
                        ? '완료된 run 결과'
                        : '연결 없음 (Mock 데이터)'
              }
              className="flex items-center gap-2 border rounded-full px-3 py-1.5"
              style={{
                background: 'var(--bg-elev)',
                borderColor: isStale ? 'var(--warn)'
                  : isArchive ? 'var(--warn)'
                  : isActiveRun ? 'var(--pos)'
                  : isCompletedSnapshot ? 'var(--text-mute)'
                  : 'var(--border)',
              }}
            >
              {isStale ? (
                <>
                  <AlertTriangle className="w-3 h-3 text-[var(--warn)] animate-pulse" aria-hidden="true" />
                  <span className="text-[var(--warn)] font-semibold text-xs">Stale ({timeSince})</span>
                </>
              ) : isArchive ? (
                <>
                  <History className="w-3 h-3 text-[var(--warn)]" aria-hidden="true" />
                  <span className="text-[var(--warn)] font-semibold text-xs">Archive</span>
                </>
              ) : isActiveRun ? (
                <>
                  <span className="relative flex h-2 w-2" aria-hidden="true">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400" />
                  </span>
                  <Wifi className="w-3 h-3 text-[var(--pos)]" aria-hidden="true" />
                  <span className="text-[var(--pos)] font-semibold text-xs">Live</span>
                </>
              ) : isCompletedSnapshot ? (
                <>
                  <Check className="w-3 h-3 text-[color:var(--text-mute)]" aria-hidden="true" />
                  <span className="text-[color:var(--text-mute)] font-semibold text-xs">Completed</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3 text-[color:var(--text-mute)]" aria-hidden="true" />
                  <span className="text-[color:var(--text-mute)] font-semibold text-xs">Mock</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Tab Navigation — 신규 토큰 */}
        <nav className="max-w-[1800px] mx-auto px-5 flex gap-1 -mb-px">
          {NAV_ITEMS.map(item => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors"
                style={({ isActive }) => ({
                  borderBottomColor: isActive ? 'var(--accent)' : 'transparent',
                  color: isActive ? 'var(--text)' : 'var(--text-mute)',
                  fontWeight: isActive ? 600 : 400,
                })}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-5 py-5 space-y-4">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Navigate to="/console" replace />} />
            <Route path="/silo-b" element={
              <PageErrorBoundary pageName="Silo B">
                <SiloBPage />
              </PageErrorBoundary>
            } />
            <Route path="/silo-a" element={
              <PageErrorBoundary pageName="Silo A">
                <SiloAPage />
              </PageErrorBoundary>
            } />
            <Route path="/combined" element={
              <PageErrorBoundary pageName="Combined">
                <CombinedPage />
              </PageErrorBoundary>
            } />
            <Route path="/selectivity" element={
              <PageErrorBoundary pageName="Selectivity">
                <SelectivityPage />
              </PageErrorBoundary>
            } />
            <Route path="/console" element={
              <PageErrorBoundary pageName="Run Console">
                <RunConsolePage />
              </PageErrorBoundary>
            } />
            <Route path="/selectivity-explorer" element={
              <PageErrorBoundary pageName="Selectivity Explorer">
                <SelectivityExplorerPage />
              </PageErrorBoundary>
            } />
            <Route path="/manual-selectivity" element={
              <PageErrorBoundary pageName="Manual Selectivity">
                <ManualSelectivityPage />
              </PageErrorBoundary>
            } />
            <Route path="/candidate/:id" element={
              <PageErrorBoundary pageName="Candidate Review">
                <CandidatePage />
              </PageErrorBoundary>
            } />
            <Route path="/candidate" element={
              <PageErrorBoundary pageName="Candidate Review">
                <CandidatePage />
              </PageErrorBoundary>
            } />
            <Route path="/run/new" element={
              <PageErrorBoundary pageName="Run Launcher">
                <RunLauncherPage />
              </PageErrorBoundary>
            } />
            <Route path="/strategy-runner" element={
              <PageErrorBoundary pageName="Strategy Runner">
                <StrategyRunnerPage />
              </PageErrorBoundary>
            } />
            <Route path="/benchmark" element={
              <PageErrorBoundary pageName="Benchmark">
                <BenchmarkPage />
              </PageErrorBoundary>
            } />
            <Route path="/wetlab/orders" element={
              <PageErrorBoundary pageName="Wetlab Order">
                <WetlabOrderPage />
              </PageErrorBoundary>
            } />
            <Route path="/wetlab/orders/:id" element={
              <PageErrorBoundary pageName="Wetlab Order">
                <WetlabOrderPage />
              </PageErrorBoundary>
            } />
            <Route path="/binding-pocket" element={
              <PageErrorBoundary pageName="Binding Pocket">
                <BindingPocketPage />
              </PageErrorBoundary>
            } />
            <Route path="/settings" element={
              <PageErrorBoundary pageName="Settings">
                <SettingsPage />
              </PageErrorBoundary>
            } />
            <Route path="/about" element={
              <PageErrorBoundary pageName="About">
                <AboutPage />
              </PageErrorBoundary>
            } />
          </Routes>
        </Suspense>
      </main>

      {/* Footer — 신규 토큰 */}
      <footer
        className="mt-6"
        style={{ borderTop: '1px solid var(--border)' }}>
        <div className="max-w-[1800px] mx-auto px-5 py-3 flex items-center justify-between text-xs text-[color:var(--text-mute)]">
          <span>AI4SCI KAERI &middot; Agentic Pipeline Monitor v0.3</span>
          <span className="flex items-center gap-2">
            {isRealData && live.runId && (
              <span className="text-[color:var(--text-mute)]">Run: {live.runId}</span>
            )}
            <span>SSTR2 Peptide Binder Design &middot; 2026</span>
          </span>
        </div>
      </footer>
    </div>
    </PipelineProvider>
  )
}

function ApiBadge({ name, status }: { name: string; status: string }) {
  const color = status === 'live'
    ? 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30'
    : status === 'failed'
      ? 'bg-[var(--neg-soft)] text-[var(--neg)] border-[var(--neg)]/30'
      : 'bg-[color:var(--bg-sunk)] text-[color:var(--text-mute)] border-[color:var(--border)]'

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${color}`}>
      {status === 'live' && (
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-400" />
        </span>
      )}
      {name}
    </span>
  )
}

function formatTimeSince(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 5) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  return `${minutes}m ago`
}

function RunSelector({
  runs,
  currentRunId,
  isViewingArchive,
  onSwitch,
}: {
  runs: { run_id: string; started_at: string; iteration: number; total_iterations: number; n_candidates: number; best_ddg: number | null; label?: string; llm_model?: string }[]
  currentRunId: string | null
  isViewingArchive: boolean
  onSwitch: (runId: string | null) => void
}) {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const closeDropdown = useCallback(() => setOpen(false), [])
  useClickOutside(dropdownRef, closeDropdown, open)

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className="hidden md:flex items-center gap-1.5 bg-[var(--bg-elev)] border border-[var(--border)] hover:border-[var(--border-strong)] rounded-lg px-2.5 py-1.5 text-[10px] text-[color:var(--text-mute)] transition-colors"
      >
        <History className="w-3 h-3 text-[color:var(--text-mute)]" />
        <span className="font-medium">Runs ({runs.length})</span>
        <ChevronDown className="w-3 h-3 text-[color:var(--text-mute)]" />
      </button>
      {open && (
        <div role="listbox" className="absolute right-0 top-full mt-1 z-50 w-72 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg shadow-xl overflow-hidden">
          <button
            onClick={() => { onSwitch(null); setOpen(false) }}
            className={`w-full text-left px-3 py-2 text-xs border-b border-[color:var(--border)] transition-colors ${
              !isViewingArchive
                ? 'bg-[var(--pos-soft)] text-[var(--pos)]'
                : 'text-[color:var(--text-mute)] hover:bg-[color:var(--bg-sunk)]'
            }`}
          >
            <span className="font-semibold">Live Run</span>
            {!isViewingArchive && <span className="ml-2 text-[var(--pos)] text-[10px]">(viewing)</span>}
          </button>
          {runs.map(run => {
            const isCurrent = isViewingArchive && currentRunId === run.run_id
            return (
              <button
                key={run.run_id}
                onClick={() => { onSwitch(run.run_id); setOpen(false) }}
                className={`w-full text-left px-3 py-2 text-xs border-b border-[color:var(--border)]/50 transition-colors ${
                  isCurrent ? 'bg-[var(--warn-soft)] text-amber-200' : 'text-[color:var(--text-mute)] hover:bg-[color:var(--bg-sunk)]'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="font-mono font-medium">{run.run_id}</span>
                  <span className="flex items-center gap-1">
                    {run.run_id.includes('4paper') && (
                      <span className="bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30 rounded px-1 py-0.5 text-[10px] font-semibold">4paper</span>
                    )}
                    {isCurrent && <span className="text-[var(--warn)] text-[10px]">(viewing)</span>}
                  </span>
                </div>
                <div className="flex gap-3 mt-0.5 text-[10px] text-[color:var(--text-mute)]">
                  <span>iter {run.iteration}/{run.total_iterations}</span>
                  <span>{run.n_candidates} candidates</span>
                  {run.best_ddg != null && <span>best ΔG: {run.best_ddg.toFixed(1)}</span>}
                  {run.llm_model && <span className="text-[var(--violet)]">{run.llm_model}</span>}
                </div>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
