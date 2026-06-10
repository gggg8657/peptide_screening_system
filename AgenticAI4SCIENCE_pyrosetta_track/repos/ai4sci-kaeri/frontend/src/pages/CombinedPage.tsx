import { useMemo } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartTooltip,
  ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine, Legend,
} from 'recharts'
import { GitCompareArrows, FlaskConical, Dna, Activity, CheckCircle2, Clock, AlertTriangle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { PlaceholderState } from '../components/PlaceholderState'
import { ExperimentControl } from '../components/ExperimentControl'
import { PipelineStatus } from '../components/PipelineStatus'
import { AgentMonitor } from '../components/AgentMonitor'
import { usePipelineContext } from '../contexts/PipelineContext'
import { useExperiment } from '../hooks/useExperiment'
import type { Candidate } from '../types'

/* ─── 통합 후보 타입 ─── */
interface UnifiedCandidate extends Candidate {
  silo: 'A' | 'B'
}

/* ─── 실행 상태 도우미 ─── */
function getSiloAStatusLabel(): { label: string; color: string; bg: string; border: string } {
  return {
    label: '미실행',
    color: 'text-[var(--text-dim)]',
    bg: 'bg-[var(--bg-sunk)]',
    border: 'border-[var(--border)]',
  }
}

function getSiloBStatusLabel(
  connected: boolean,
  completed: boolean,
  iteration: number,
  totalIterations: number,
): { label: string; color: string; bg: string; border: string } {
  if (completed) {
    return {
      label: `완료 (${totalIterations} iter)`,
      color: 'text-[var(--pos)]',
      bg: 'bg-[var(--pos-soft)]',
      border: 'border-[var(--pos)]/30',
    }
  }
  if (connected && iteration > 0) {
    return {
      label: `실행 중 (iter ${iteration}/${totalIterations})`,
      color: 'text-[var(--accent)]',
      bg: 'bg-[var(--accent-soft)]',
      border: 'border-[var(--accent)]/30',
    }
  }
  return {
    label: '미실행',
    color: 'text-[var(--text-dim)]',
    bg: 'bg-[var(--bg-sunk)]',
    border: 'border-[var(--border)]',
  }
}

/* ─── 상태 아이콘 ─── */
function StatusIcon({ label }: { label: string }) {
  if (label.startsWith('완료'))
    return <CheckCircle2 className="w-4 h-4 text-[var(--pos)]" />
  if (label.startsWith('실행'))
    return <Activity className="w-4 h-4 text-[var(--accent)] animate-pulse" />
  return <Clock className="w-4 h-4 text-[var(--text-dim)]" />
}

/* ─── Scatter Tooltip ─── */
function ScatterDot(props: Record<string, unknown>) {
  const { cx, cy, fill } = props as { cx: number; cy: number; fill: string }
  return <circle cx={cx} cy={cy} r={4} fill={fill} fillOpacity={0.8} stroke="none" />
}

/* ─── 통합 후보 테이블 ─── */
function UnifiedCandidateTable({ candidates }: { candidates: UnifiedCandidate[] }) {
  if (candidates.length === 0) {
    return (
      <PlaceholderState message="파이프라인 결과가 없습니다. Silo A 또는 B를 실행하세요.">
        <div className="h-16" />
      </PlaceholderState>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--border)] bg-[var(--bg-elev)]">
            <th className="px-3 py-2 text-left text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">Rank</th>
            <th className="px-3 py-2 text-left text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">Source</th>
            <th className="px-3 py-2 text-left text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">Candidate</th>
            <th className="px-3 py-2 text-left text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">Sequence</th>
            <th className="px-3 py-2 text-right text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">ddG</th>
            <th className="px-3 py-2 text-right text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">Total Score</th>
            <th className="px-3 py-2 text-right text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">Final Score</th>
            <th className="px-3 py-2 text-center text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c, i) => (
            <tr
              key={`${c.silo}-${c.id}-${i}`}
              className="border-b border-[var(--border)] hover:bg-[var(--bg-elev)] transition-colors"
            >
              <td className="px-3 py-2 font-mono text-[var(--text-mute)]">{c.rank || i + 1}</td>
              <td className="px-3 py-2">
                {c.source === 'silo_a' ? (
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30">
                    <FlaskConical className="w-2.5 h-2.5" />
                    Silo A
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30">
                    <Dna className="w-2.5 h-2.5" />
                    Silo B
                  </span>
                )}
              </td>
              <td className="px-3 py-2 font-mono text-[var(--text-mute)] text-[10px]">{c.id || '—'}</td>
              <td className="px-3 py-2 font-mono text-[10px] text-[var(--text-mute)] max-w-[160px] truncate" title={c.sequence}>
                {c.sequence || '—'}
              </td>
              <td className="px-3 py-2 text-right font-mono text-[var(--warn)]">{c.ddG?.toFixed(2) ?? '—'}</td>
              <td className="px-3 py-2 text-right font-mono text-[var(--text-mute)]">{c.totalScore?.toFixed(1) ?? '—'}</td>
              <td className="px-3 py-2 text-right font-mono text-[var(--text-mute)]">{c.finalScore?.toFixed(1) ?? '—'}</td>
              <td className="px-3 py-2 text-center">
                <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                  c.result === 'PASS'
                    ? 'bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30'
                    : c.result === 'REF'
                      ? 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30'
                      : 'bg-[var(--neg-soft)] text-[var(--neg)] border border-[var(--neg)]/30'
                }`}>
                  {c.result}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ─── Silo A 공백 안내 배너 ─── */
function SiloAEmptyBanner() {
  const navigate = useNavigate()
  return (
    <div
      role="note"
      className="flex flex-col sm:flex-row items-start sm:items-center gap-3
                 rounded-lg border border-[var(--warn)]/30 bg-[var(--warn-soft)] px-4 py-3"
    >
      <AlertTriangle className="w-4 h-4 text-[var(--warn)] flex-shrink-0 mt-0.5 sm:mt-0" aria-hidden />
      <div className="flex-1 text-xs">
        <span className="text-[var(--warn)] font-medium">Silo A 실행 이력 없음</span>
        <span className="text-[var(--warn)]/80 ml-1.5">
          — 현재 Silo B 단독 데이터만 표시됩니다. Combined 비교를 위해 Silo A를 먼저 실행하세요.
        </span>
      </div>
      <div className="flex gap-2 flex-shrink-0">
        <button
          onClick={() => navigate('/silo-b')}
          className="px-3 py-1.5 rounded-lg text-[10px] font-medium
                     bg-[var(--accent-soft)] border border-[var(--accent)]/30 text-[var(--accent)]
                     hover:bg-[var(--accent-soft)] transition-colors whitespace-nowrap"
        >
          Silo B 실행
        </button>
        <button
          onClick={() => navigate('/silo-a')}
          className="px-3 py-1.5 rounded-lg text-[10px] font-medium
                     bg-[var(--violet-soft)] border border-[var(--violet)]/30 text-[var(--violet)]
                     hover:bg-[var(--violet-soft)] transition-colors whitespace-nowrap"
        >
          Silo A 시작 →
        </button>
      </div>
    </div>
  )
}

/* ─── 메인 컴포넌트 ─── */
export function CombinedPage() {
  const live = usePipelineContext()
  const experiment = useExperiment(3000)
  const isLive = live.connected && live.steps.length > 0

  // approach='dual' 주입
  const experimentDual: typeof experiment = {
    ...experiment,
    startExperiment: (overrides?: Record<string, unknown>) =>
      experiment.startExperiment({ approach: 'dual', ...overrides }),
  }

  /* Silo B 후보 (silo_a가 아닌 모든 후보 — legacy 포함) */
  const siloBCandidates: UnifiedCandidate[] = useMemo(
    () =>
      (isLive ? live.candidates : [])
        .filter(c => c.source !== 'silo_a')
        .map(c => ({ ...c, silo: 'B' as const })),
    [isLive, live.candidates],
  )

  /* Silo A 후보 (silo_a 소스) */
  const siloACandidates: UnifiedCandidate[] = useMemo(
    () =>
      (isLive ? live.candidates : [])
        .filter(c => c.source === 'silo_a')
        .map(c => ({ ...c, silo: 'A' as const })),
    [isLive, live.candidates],
  )

  /* 통합 후보 (ddG 기준 정렬) */
  const unifiedCandidates = useMemo(
    () =>
      [...siloBCandidates, ...siloACandidates]
        .filter(c => c.result !== 'REF')
        .sort((a, b) => a.ddG - b.ddG)
        .map((c, i) => ({ ...c, rank: i + 1 })),
    [siloBCandidates, siloACandidates],
  )

  /* Scatter plot 데이터 */
  const scatterDataB = useMemo(
    () =>
      siloBCandidates
        .filter(c => c.result !== 'REF')
        .map(c => ({ ddG: c.ddG, score: c.totalScore, id: c.id })),
    [siloBCandidates],
  )
  const scatterDataA = useMemo(
    () =>
      siloACandidates
        .filter(c => c.result !== 'REF')
        .map(c => ({ ddG: c.ddG, score: c.totalScore, id: c.id })),
    [siloACandidates],
  )

  /* Bar chart — 상위 10개 ddG */
  const top10 = useMemo(
    () =>
      unifiedCandidates.slice(0, 10).map(c => ({
        id: c.id || `#${c.rank}`,
        ddG: c.ddG,
        silo: c.silo,
      })),
    [unifiedCandidates],
  )

  /* Silo B 상태 */
  const siloBStatus = getSiloBStatusLabel(
    live.connected,
    live.completed,
    live.iteration,
    live.totalIterations,
  )
  const siloAStatus = getSiloAStatusLabel()

  const hasAnyData = unifiedCandidates.length > 0
  /* Silo A 후보가 없으면 공백 배너 표시 */
  const siloAEmpty = siloACandidates.length === 0

  return (
    <div className="space-y-4">
      {/* Silo A 공백 안내 — 항상 최상단 (Silo A 데이터 없을 때) */}
      {siloAEmpty && <SiloAEmptyBanner />}

      {/* ── Experiment Control (dual) ── */}
      <ExperimentControl
        experiment={experimentDual}
        iteration={live.iteration}
        totalIterations={live.totalIterations}
      />

      {/* Header */}
      <section className="card border border-[var(--teal)]/30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[var(--teal-soft)] border border-[var(--teal)]/30 flex items-center justify-center">
            <GitCompareArrows className="w-4 h-4 text-[var(--teal)]" />
          </div>
          <div className="flex-1">
            <h2 className="text-sm font-bold text-[var(--text-mute)]">Combined: Cross-Silo Comparison</h2>
            <p className="text-xs text-[var(--text-mute)]">Unified candidate ranking across Silo A and Silo B</p>
          </div>
        </div>
      </section>

      {/* 실행 상태 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Silo B 상태 */}
        <section className={`card border ${siloBStatus.border} ${siloBStatus.bg}`}>
          <div className="flex items-center gap-2 mb-3">
            <Dna className="w-4 h-4 text-[var(--accent)]" />
            <h3 className="text-sm font-semibold text-[var(--accent)]">Silo B: PyRosetta</h3>
            <StatusIcon label={siloBStatus.label} />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-dim)]">상태</span>
              <span className={`font-medium ${siloBStatus.color}`}>{siloBStatus.label}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-dim)]">후보 수</span>
              <span className="text-[var(--text-mute)] font-mono">{siloBCandidates.filter(c => c.result !== 'REF').length || '—'}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-dim)]">Best ΔG</span>
              <span className="text-[var(--warn)] font-mono">
                {siloBCandidates.length > 0
                  ? `${Math.min(...siloBCandidates.map(c => c.ddG)).toFixed(2)} kcal/mol`
                  : '—'}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-dim)]">전략</span>
              <span className="text-[var(--text-mute)]">SST-14 guided mutation + FlexPepDock</span>
            </div>
          </div>
        </section>

        {/* Silo A 상태 */}
        <section className={`card border ${siloAStatus.border} ${siloAStatus.bg}`}>
          <div className="flex items-center gap-2 mb-3">
            <FlaskConical className="w-4 h-4 text-[var(--violet)]" />
            <h3 className="text-sm font-semibold text-[var(--violet)]">Silo A: 3-ARM NIM</h3>
            <StatusIcon label={siloAStatus.label} />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-dim)]">상태</span>
              <span className={`font-medium ${siloAStatus.color}`}>{siloAStatus.label}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-dim)]">후보 수</span>
              <span className="text-[var(--text-dim)] font-mono">—</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-dim)]">Best ΔG</span>
              <span className="text-[var(--text-dim)] font-mono">—</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-dim)]">전략</span>
              <span className="text-[var(--text-mute)]">De novo backbone + 8 NIM APIs</span>
            </div>
          </div>
        </section>
      </div>

      {/* ── Pipeline Status (Silo A + B 포함) ── */}
      {isLive && live.steps.length > 0 && (
        <PipelineStatus
          steps={live.steps}
          rosettaSubsteps={live.rosettaSubsteps}
          iteration={live.iteration}
          totalIterations={live.totalIterations}
          completed={live.completed}
          executionMode={live.executionMode}
        />
      )}

      {/* ── Agent Monitor + Unified Candidate Table ── */}
      {isLive && live.agents.length > 0 && (
        <AgentMonitor
          agents={live.agents}
          iteration={live.iteration}
          executionMode={live.executionMode}
        />
      )}

      {/* 통합 후보 테이블 */}
      <section className="card border border-[var(--border)]">
        <div className="flex items-center gap-2 mb-3">
          <GitCompareArrows className="w-3.5 h-3.5 text-[var(--teal)]" />
          <span className="text-xs font-semibold text-[var(--teal)] uppercase tracking-wider">Unified Candidate Ranking</span>
          {unifiedCandidates.length > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--teal-soft)] text-[var(--teal)] border border-[var(--teal)]/30 ml-auto">
              {unifiedCandidates.length}개
            </span>
          )}
        </div>
        <UnifiedCandidateTable candidates={unifiedCandidates} />
      </section>

      {/* 비교 차트 */}
      {hasAnyData ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Scatter plot */}
          <section className="card border border-[var(--border)]">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">
                ΔG vs Total Score (Silo 비교)
              </span>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <ScatterChart margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="ddG"
                  name="ΔG"
                  type="number"
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  label={{ value: 'ΔG (kcal/mol)', position: 'insideBottom', offset: -2, fontSize: 9, fill: '#64748b' }}
                  height={28}
                />
                <YAxis
                  dataKey="score"
                  name="Score"
                  type="number"
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  width={40}
                />
                <RechartTooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 6, fontSize: 11 }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(v, name): [string, string] => [typeof v === 'number' ? v.toFixed(2) : '—', String(name ?? '')]}
                />
                <ReferenceLine x={-5} stroke="var(--warn)" strokeDasharray="4 2" strokeWidth={1} />
                <Legend
                  wrapperStyle={{ fontSize: 10, paddingTop: 4 }}
                  formatter={(v) => <span style={{ color: '#94a3b8' }}>{v}</span>}
                />
                {scatterDataB.length > 0 && (
                  <Scatter name="Silo B" data={scatterDataB} fill="var(--pos)" shape={<ScatterDot />} />
                )}
                {scatterDataA.length > 0 && (
                  <Scatter name="Silo A" data={scatterDataA} fill="var(--accent)" shape={<ScatterDot />} />
                )}
              </ScatterChart>
            </ResponsiveContainer>
          </section>

          {/* Bar chart — Top 10 ddG */}
          <section className="card border border-[var(--border)]">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">
                상위 10개 ΔG 비교
              </span>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={top10} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="id"
                  tick={{ fontSize: 9, fill: '#94a3b8' }}
                  height={28}
                  interval={0}
                  tickFormatter={(v: string) => v.slice(0, 8)}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  width={40}
                  label={{ value: 'ΔG', angle: -90, position: 'insideLeft', fontSize: 9, fill: '#64748b' }}
                />
                <RechartTooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 6, fontSize: 11 }}
                  formatter={(v): [string, string] => [typeof v === 'number' ? `${v.toFixed(2)} kcal/mol` : '—', 'ΔG']}
                />
                <Bar dataKey="ddG" name="ΔG" radius={[2, 2, 0, 0]}>
                  {top10.map((entry, i) => (
                    <Cell
                      key={`cell-${i}`}
                      fill={entry.silo === 'A' ? '#60a5fa' : '#4ade80'}
                      fillOpacity={0.85}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex items-center gap-4 mt-1">
              <span className="flex items-center gap-1 text-[10px] text-[var(--text-dim)]">
                <span className="inline-block w-2.5 h-2.5 rounded-sm bg-green-400 opacity-85" />
                Silo B
              </span>
              <span className="flex items-center gap-1 text-[10px] text-[var(--text-dim)]">
                <span className="inline-block w-2.5 h-2.5 rounded-sm bg-blue-400 opacity-85" />
                Silo A
              </span>
            </div>
          </section>
        </div>
      ) : (
        <section className="card border border-[var(--border)]">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-semibold text-[var(--text-dim)] uppercase tracking-wider">비교 차트</span>
          </div>
          <PlaceholderState message="파이프라인 결과가 생성되면 비교 차트가 표시됩니다.">
            <div className="h-20" />
          </PlaceholderState>
        </section>
      )}

      {/* Cross-Silo Validation */}
      <section className="card border border-[var(--border)]">
        <h3 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest mb-3">
          Cross-Silo Validation
        </h3>
        <div className="bg-[var(--bg-elev)] rounded-lg p-4">
          <div className="text-center space-y-3">
            <div className="flex items-center justify-center gap-6">
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[var(--accent-soft)] border border-[var(--accent)]/30 flex items-center justify-center mx-auto mb-1">
                  <Dna className="w-5 h-5 text-[var(--accent)]" />
                </div>
                <span className="text-[10px] text-[var(--accent)] font-medium">Silo B</span>
                <p className="text-[10px] text-[var(--text-mute)]">
                  {siloBCandidates.filter(c => c.result !== 'REF').length} candidates
                </p>
              </div>
              <div className="flex flex-col items-center">
                <GitCompareArrows className="w-6 h-6 text-[var(--teal)]" />
                <span className="text-[10px] text-[var(--teal)] mt-1">motif match?</span>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[var(--violet-soft)] border border-[var(--violet)]/30 flex items-center justify-center mx-auto mb-1">
                  <FlaskConical className="w-5 h-5 text-[var(--violet)]" />
                </div>
                <span className="text-[10px] text-[var(--violet)] font-medium">Silo A</span>
                <p className="text-[10px] text-[var(--text-mute)]">0 candidates</p>
              </div>
            </div>
            <p className="text-xs text-[var(--text-mute)] max-w-md mx-auto">
              두 독립적인 접근법이 동일한 결합 모티프를 발견하면 신뢰도가 크게 향상됩니다.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
