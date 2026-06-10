import type { ComponentType } from 'react'
import { useMemo, useState } from 'react'
import { BarChart3, Clock3, Coins, Layers3, Sparkles, Target } from 'lucide-react'
import { HeatmapCell } from '../components/dashboard/HeatmapCell'
import { TierBadge } from '../components/dashboard/TierBadge'
import { useBenchmark, type BenchmarkCell as BenchmarkCellData } from '../hooks/dashboard'

const PHASES = ['Phase1', 'Phase2', 'Phase3', 'V2'] as const
const METRICS = [
  { id: 'pass_rate', label: 'Pass rate', icon: Sparkles },
  { id: 'candidates', label: 'Candidates', icon: Layers3 },
  { id: 't2', label: 'T2 hits', icon: Target },
  { id: 'time_min', label: 'Time', icon: Clock3 },
  { id: 'cost', label: 'Cost', icon: Coins },
] as const

type Phase = (typeof PHASES)[number]
type MetricId = (typeof METRICS)[number]['id']

type HoverCell = {
  llmId: string
  flowId: string
  cell: BenchmarkCellData
}

export function BenchmarkPage() {
  const [phase, setPhase] = useState<Phase>('V2')
  const [metric, setMetric] = useState<MetricId>('pass_rate')
  const [hoverCell, setHoverCell] = useState<HoverCell | null>(null)
  const benchmarkQuery = useBenchmark(phase)

  const rows = benchmarkQuery.data?.llms ?? []
  const flows = benchmarkQuery.data?.flows ?? []
  const matrix = benchmarkQuery.data?.matrix ?? {}

  const stats = useMemo(() => {
    const allCells = Object.values(matrix).flatMap((flowMap) => Object.values(flowMap))
    if (allCells.length === 0) {
      return {
        bestModel: '—',
        bestFlow: '—',
        speedModel: '—',
        costModel: '—',
      }
    }

    const modelAverages = rows.map((llm) => {
      const cells = Object.values(matrix[llm.id] ?? {})
      return {
        id: llm.id,
        avgPass: average(cells.map((cell) => cell.pass_rate)),
        avgTime: average(cells.map((cell) => cell.time_min)),
        avgCost: average(cells.map((cell) => cell.cost)),
      }
    })

    const flowAverages = flows.map((flow) => {
      const cells = rows.map((llm) => matrix[llm.id]?.[flow.id]).filter(Boolean) as BenchmarkCellData[]
      return {
        id: flow.id,
        avgPass: average(cells.map((cell) => cell.pass_rate)),
      }
    })

    return {
      bestModel: modelAverages.sort((a, b) => b.avgPass - a.avgPass)[0]?.id ?? '—',
      bestFlow: flowAverages.sort((a, b) => b.avgPass - a.avgPass)[0]?.id ?? '—',
      speedModel: modelAverages.sort((a, b) => a.avgTime - b.avgTime)[0]?.id ?? '—',
      costModel: modelAverages.sort((a, b) => a.avgCost - b.avgCost)[0]?.id ?? '—',
    }
  }, [flows, matrix, rows])

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--warn)]/30 bg-[var(--warn-soft)]">
          <BarChart3 className="h-4 w-4 text-[var(--warn)]" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-text-base">LLM Benchmark</h1>
          <p className="text-[10px] text-text-mute">5 sLLM × 3 flow benchmark matrix with phase and metric toggles</p>
        </div>
        <div className="ml-auto rounded-lg border border-border-base bg-bg px-2.5 py-1 font-mono text-[10px] text-text-mute">
          {benchmarkQuery.data?.total_runs ?? 0} runs · {phase}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total runs" value={String(benchmarkQuery.data?.total_runs ?? 0)} sub="phase aggregate" />
        <StatCard label="Best model" value={stats.bestModel} sub="mean pass rate" tier={scoreTier(rows, matrix, stats.bestModel)} />
        <StatCard label="Best flow" value={stats.bestFlow} sub="across visible LLMs" />
        <StatCard label="Speed champ" value={stats.speedModel} sub="lowest mean time" />
        <StatCard label="Cost champ" value={stats.costModel} sub="lowest mean cost" />
      </div>

      <section className="rounded-xl border border-border-base bg-bg-elev p-4">
        <div className="flex flex-wrap items-center gap-3">
          <ToggleGroup<Phase> value={phase} onChange={setPhase} options={PHASES.map((item) => ({ id: item, label: item }))} />
          <div className="h-5 w-px bg-bg-elev" />
          <ToggleGroup<MetricId>
            value={metric}
            onChange={setMetric}
            options={METRICS.map((item) => ({ id: item.id, label: item.label, icon: item.icon }))}
          />
          <div className="ml-auto font-mono text-[10px] text-text-dim">source: `/api/benchmark/results?phase={phase}`</div>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-border-base bg-bg-elev">
        <div className="flex items-center justify-between border-b border-border-base px-4 py-3">
          <div>
            <h2 className="text-sm font-semibold text-text-base">Model × Flow Matrix</h2>
            <p className="text-[10px] text-text-mute">cell = mean over phase runs · hover for detail</p>
          </div>
          <div className="font-mono text-[10px] text-text-dim">{metricLabel(metric)}</div>
        </div>

        {benchmarkQuery.isLoading ? (
          <div className="px-4 py-10 text-center text-xs text-text-mute">Loading benchmark results…</div>
        ) : benchmarkQuery.isError ? (
          <div className="px-4 py-10 text-center text-xs text-[var(--neg)]">Failed to load benchmark results.</div>
        ) : rows.length === 0 || flows.length === 0 ? (
          <div className="px-4 py-10 text-center text-xs text-text-mute">No benchmark rows available for {phase}.</div>
        ) : (
          <div className="overflow-auto px-4 py-4">
            <div className="min-w-[920px]">
              <div className="grid grid-cols-[220px_repeat(3,minmax(0,1fr))_72px] gap-3 border-b border-border-base pb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">
                <div>model</div>
                {flows.map((flow) => (
                  <div key={flow.id} className="text-center">
                    <div className="font-semibold text-text-mute">{flow.name}</div>
                    <div className="mt-0.5 normal-case tracking-normal text-[10px] text-text-dim">{flow.desc}</div>
                  </div>
                ))}
                <div className="text-right">best</div>
              </div>

              <div className="divide-y divide-border-base">
                {rows.map((llm) => {
                  const bestFlowId = bestFlowForMetric(matrix[llm.id] ?? {}, metric)
                  const avgPass = average(Object.values(matrix[llm.id] ?? {}).map((cell) => cell.pass_rate))
                  return (
                    <div key={llm.id} className="grid grid-cols-[220px_repeat(3,minmax(0,1fr))_72px] gap-3 py-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-semibold text-text-base">{llm.id}</span>
                          <TierBadge tier={tierFromScore(avgPass)} />
                        </div>
                        <div className="font-mono text-[10px] text-text-dim">{llm.vram_gb} GB VRAM · {llm.short}</div>
                      </div>

                      {flows.map((flow) => {
                        const cell = matrix[llm.id]?.[flow.id]
                        if (!cell) {
                          return (
                            <div key={flow.id} className="flex h-full min-h-[78px] items-center justify-center rounded-lg border border-dashed border-border-base bg-bg text-[10px] text-text-dim">
                              n/a
                            </div>
                          )
                        }
                        const meta = metricValue(cell, metric)
                        const normalizedValue = normalizeToHeatmap(meta.normalized)
                        return (
                          <div
                            key={flow.id}
                            className={`rounded-lg border p-2 transition-transform ${bestFlowId === flow.id ? 'border-[var(--warn)]/30 bg-[var(--warn-soft)]' : 'border-border-base bg-bg'} hover:-translate-y-0.5`}
                            onMouseEnter={() => setHoverCell({ llmId: llm.id, flowId: flow.id, cell })}
                            onMouseLeave={() => setHoverCell((current) => (current?.llmId === llm.id && current.flowId === flow.id ? null : current))}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="w-16 shrink-0">
                                <HeatmapCell value={normalizedValue} label={meta.label} title={`${llm.id} × ${flow.name} · ${metricLabel(metric)} ${meta.label}`} />
                              </div>
                              <div className="min-w-0 flex-1 space-y-1 text-[10px] text-text-mute">
                                <div className="flex justify-between">
                                  <span>cand</span>
                                  <span className="font-mono text-text-mute">{cell.candidates}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>T2</span>
                                  <span className="font-mono text-text-mute">{cell.t2}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>time</span>
                                  <span className="font-mono text-text-mute">{cell.time_min.toFixed(1)}m</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>cost</span>
                                  <span className="font-mono text-text-mute">{cell.cost.toFixed(2)}×</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        )
                      })}

                      <div className="flex items-center justify-end font-mono text-xs font-semibold text-[var(--warn)]">
                        {bestFlowId ? bestFlowId.slice(0, 3) : '—'}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        <div className="border-t border-border-base bg-bg px-4 py-3 text-xs text-text-mute">
          {hoverCell ? (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
              <span className="font-mono font-semibold text-text-base">{hoverCell.llmId} × {hoverCell.flowId}</span>
              <span>pass <strong className="font-mono text-[var(--pos)]">{hoverCell.cell.pass_rate.toFixed(1)}%</strong></span>
              <span>time <strong className="font-mono">{hoverCell.cell.time_min.toFixed(1)}m</strong></span>
              <span>cand <strong className="font-mono">{hoverCell.cell.candidates}</strong></span>
              <span>T2 <strong className="font-mono">{hoverCell.cell.t2}</strong></span>
              <span>cost <strong className="font-mono">{hoverCell.cell.cost.toFixed(2)}×</strong></span>
            </div>
          ) : (
            <span className="text-text-dim">Hover a matrix cell to inspect the underlying benchmark summary.</span>
          )}
        </div>
      </section>
    </div>
  )
}

function StatCard({ label, value, sub, tier }: { label: string; value: string; sub: string; tier?: 'T0' | 'T1' | 'T2' | 'T3' }) {
  return (
    <div className="rounded-xl border border-border-base bg-bg-elev p-4">
      <div className="text-[10px] uppercase tracking-[0.18em] text-text-dim">{label}</div>
      <div className="mt-2 flex items-center gap-2">
        <div className="font-mono text-sm font-semibold text-text-base">{value}</div>
        {tier ? <TierBadge tier={tier} /> : null}
      </div>
      <div className="mt-1 text-[11px] text-text-mute">{sub}</div>
    </div>
  )
}

function ToggleGroup<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T
  onChange: (next: T) => void
  options: { id: T; label: string; icon?: ComponentType<{ className?: string }> }[]
}) {
  return (
    <div className="inline-flex flex-wrap overflow-hidden rounded-lg border border-border-base">
      {options.map((option) => {
        const Icon = option.icon
        const active = value === option.id
        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onChange(option.id)}
            className={`inline-flex items-center gap-1.5 border-r border-border-base px-3 py-1.5 text-[11px] last:border-r-0 ${
              active ? 'bg-accent text-white font-semibold' : 'bg-bg text-text-mute hover:bg-bg-elev hover:text-text-base'
            }`}
          >
            {Icon ? <Icon className="h-3 w-3" /> : null}
            {option.label}
          </button>
        )
      })}
    </div>
  )
}

function metricValue(cell: BenchmarkCellData, metric: MetricId) {
  if (metric === 'pass_rate') return { raw: cell.pass_rate, normalized: clamp01(cell.pass_rate / 100), label: `${cell.pass_rate.toFixed(0)}%` }
  if (metric === 'candidates') return { raw: cell.candidates, normalized: clamp01(cell.candidates / 16), label: String(cell.candidates) }
  if (metric === 't2') return { raw: cell.t2, normalized: clamp01(cell.t2 / 4), label: String(cell.t2) }
  if (metric === 'time_min') return { raw: cell.time_min, normalized: clamp01(1 - cell.time_min / 120), label: `${cell.time_min.toFixed(0)}m` }
  return { raw: cell.cost, normalized: clamp01(1 - cell.cost / 4), label: `${cell.cost.toFixed(2)}×` }
}

function bestFlowForMetric(flowMap: Record<string, BenchmarkCellData>, metric: MetricId): string | null {
  const entries = Object.entries(flowMap)
  if (entries.length === 0) return null
  return entries
    .map(([flowId, cell]) => ({ flowId, score: metricValue(cell, metric).normalized }))
    .sort((left, right) => right.score - left.score)[0]?.flowId ?? null
}

function metricLabel(metric: MetricId) {
  return METRICS.find((item) => item.id === metric)?.label ?? metric
}

function average(values: number[]) {
  return values.length === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / values.length
}

function tierFromScore(value: number): 'T0' | 'T1' | 'T2' | 'T3' {
  if (value >= 85) return 'T3'
  if (value >= 75) return 'T2'
  if (value >= 65) return 'T1'
  return 'T0'
}

function scoreTier(rows: { id: string }[], matrix: Record<string, Record<string, BenchmarkCellData>>, modelId: string) {
  const found = rows.find((row) => row.id === modelId)
  if (!found) return undefined
  const avg = average(Object.values(matrix[modelId] ?? {}).map((cell) => cell.pass_rate))
  return tierFromScore(avg)
}

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value))
}

function normalizeToHeatmap(value: number) {
  return 0.75 + clamp01(value) * 0.23
}
