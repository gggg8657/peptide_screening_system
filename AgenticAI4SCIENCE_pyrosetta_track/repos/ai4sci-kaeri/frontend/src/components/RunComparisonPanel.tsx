import { useMemo } from 'react'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { GitCompareArrows } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import type { ArchivedRun } from '../hooks/usePipelineStatus'
import { cn } from '../lib/utils'

interface RunComparisonPanelProps {
  runs: ArchivedRun[]
  currentRunId: string | null
}

function MiniSparkline({ value }: { value: number | null }) {
  if (value === null) return <span className="text-[10px] text-[var(--text-mute)]">--</span>

  // Simple sparkline showing a single-point trend vs zero
  const data = [
    { v: 0 },
    { v: value * 0.3 },
    { v: value * 0.7 },
    { v: value },
  ]

  return (
    <div className="w-16 h-5">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey="v"
            stroke={value <= -5 ? 'var(--pos)' : 'var(--neg)'}
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RunComparisonPanel({ runs, currentRunId }: RunComparisonPanelProps) {
  const sortedRuns = useMemo(
    () => [...runs].sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()),
    [runs]
  )

  if (sortedRuns.length === 0) return null

  return (
    <section className="card flex flex-col gap-3" aria-label="Run Comparison Panel">
      <div>
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          <GitCompareArrows className="w-4 h-4" />
          Run Comparison
          <HelpTooltip title="Run Comparison">
            <p>여러 실험 실행(Run)의 결과를 비교합니다.</p>
            <p>각 실행의 최고 ΔG, 후보 수, 수렴 여부를 한눈에 비교할 수 있습니다.</p>
          </HelpTooltip>
        </h2>
        <p className="text-xs text-[var(--text-mute)] mt-0.5">
          Archived experiment runs &middot; {sortedRuns.length} runs
        </p>
      </div>

      <div className="overflow-x-auto overflow-y-auto max-h-80 rounded-lg border border-[var(--border)]">
        <table className="w-full text-xs" role="table" aria-label="Archived run comparison">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[var(--bg)]/80">
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)]">Run ID</th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)]">Started</th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)]">Status</th>
              <th className="px-3 py-2.5 text-right font-semibold text-[var(--text-mute)]">Iterations</th>
              <th className="px-3 py-2.5 text-right font-semibold text-[var(--text-mute)]">Candidates</th>
              <th className="px-3 py-2.5 text-right font-semibold text-[var(--text-mute)]">Best ΔG</th>
              <th className="px-3 py-2.5 text-center font-semibold text-[var(--text-mute)]">Trend</th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)]">Model</th>
            </tr>
          </thead>
          <tbody>
            {sortedRuns.map((run, idx) => {
              const isCurrent = run.run_id === currentRunId
              return (
                <tr
                  key={run.run_id}
                  className={cn(
                    'border-b border-[var(--border)]/50 transition-colors duration-100',
                    isCurrent
                      ? 'bg-[var(--accent-soft)] border-l-2 border-l-cyan-500'
                      : idx % 2 === 0
                        ? 'bg-[var(--bg)]/20'
                        : 'bg-transparent',
                    'hover:bg-[var(--bg-elev)]/40'
                  )}
                >
                  <td className="px-3 py-2 font-mono text-[var(--text-mute)] whitespace-nowrap">
                    {run.run_id.slice(0, 12)}
                    {isCurrent && (
                      <span className="ml-1.5 inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30">
                        current
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-[var(--text-mute)] whitespace-nowrap">
                    {new Date(run.started_at).toLocaleDateString('ko-KR', {
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={cn(
                        'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold',
                        run.completed
                          ? 'bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30'
                          : 'bg-[var(--warn-soft)] text-[var(--warn)] border border-[var(--warn)]/30'
                      )}
                    >
                      {run.completed ? 'DONE' : 'RUNNING'}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-[var(--text-mute)] tabular-nums">
                    {run.iteration}/{run.total_iterations}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-[var(--text-mute)] tabular-nums">
                    {run.n_candidates}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {run.best_ddg !== null ? (
                      <span
                        className={cn(
                          'font-mono tabular-nums font-bold',
                          run.best_ddg <= -5 ? 'text-[var(--pos)]' : 'text-[var(--neg)]'
                        )}
                      >
                        {run.best_ddg.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-[var(--text-mute)]">--</span>
                    )}
                  </td>
                  <td className="px-3 py-2 flex justify-center">
                    <MiniSparkline value={run.best_ddg} />
                  </td>
                  <td className="px-3 py-2 text-[var(--text-mute)] font-mono text-[10px] whitespace-nowrap">
                    {run.llm_model ?? '--'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
