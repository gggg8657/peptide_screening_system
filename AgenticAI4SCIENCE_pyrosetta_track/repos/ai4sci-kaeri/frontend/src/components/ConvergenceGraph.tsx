import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { ConvergencePoint } from '../types'
import { TrendingDown, CheckCircle2 } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ name?: string; value?: number; color?: string }>
  label?: string | number
  convergenceData: ConvergencePoint[]
}

function CustomTooltip({ active, payload, label, convergenceData }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null

  const point = convergenceData.find(d => d.iteration === Number(label))

  return (
    <div className="bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-3 shadow-xl text-xs">
      <p className="font-semibold text-[var(--text-mute)] mb-2">Iteration {label}</p>
      {payload.map((entry: { name?: string; value?: number; color?: string }) => (
        <div key={entry.name} className="flex justify-between gap-4 mb-1">
          <span style={{ color: entry.color }}>{entry.name}</span>
          <span className="font-bold text-[var(--text-mute)]">
            {entry.name === 'Best ΔG'
              ? `${Number(entry.value).toFixed(1)} kcal/mol`
              : entry.value}
          </span>
        </div>
      ))}
      {point?.converged && (
        <div className="mt-2 flex items-center gap-1 text-[var(--pos)] border-t border-[var(--border)] pt-2">
          <CheckCircle2 className="w-3 h-3" />
          <span className="font-semibold">Converged</span>
        </div>
      )}
    </div>
  )
}

interface ConvergenceGraphProps {
  data: ConvergencePoint[]
}

export function ConvergenceGraph({ data }: ConvergenceGraphProps) {
  if (data.length === 0) {
    return (
      <section className="card flex flex-col gap-3 items-center justify-center h-64" aria-label="Convergence Graph">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest">
          Convergence Graph
        </h2>
        <p className="text-xs text-[var(--text-mute)]">Waiting for iteration data...</p>
      </section>
    )
  }

  const lastDelta = data.length >= 2
    ? Math.abs(data[data.length - 1].bestDdG - data[data.length - 2].bestDdG)
    : 999
  const isConverged = lastDelta < 0.5
  const bestDdG = Math.min(...data.map(d => d.bestDdG))
  const currentIteration = data[data.length - 1]?.iteration ?? 1

  return (
    <section className="card flex flex-col gap-3" aria-label="Convergence Graph">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
            Convergence Graph
            <HelpTooltip title="Convergence Graph">
              <p>Iteration별 최고 ΔG 추이를 보여줍니다.</p>
              <p><strong>수렴 판정</strong>: 연속 iteration 간 ΔG 변화(ΔΔG)가 0.5 kcal/mol 미만이면 수렴으로 판정합니다.</p>
              <p><strong>Mann-Whitney U 검정</strong>: 연속 window의 ΔG 분포를 비교하여 통계적 수렴을 확인합니다.</p>
              <p><strong>보라색 바</strong>: 해당 iteration에서 QC 통과한 후보 수.</p>
            </HelpTooltip>
          </h2>
          <p className="text-xs text-[var(--text-mute)] mt-0.5">
            Best &Delta;G per iteration &middot; threshold &Delta; &lt; 0.5 kcal/mol
          </p>
        </div>
        <div className="flex gap-2 items-center">
          {isConverged ? (
            <span className="flex items-center gap-1 text-[10px] bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30 px-2 py-0.5 rounded-full font-semibold">
              <CheckCircle2 className="w-3 h-3" />
              Converged
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[10px] bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30 px-2 py-0.5 rounded-full font-semibold">
              <TrendingDown className="w-3 h-3" />
              Optimizing
            </span>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2 text-center">
          <div className="text-[10px] text-[var(--text-mute)]">Best ΔG</div>
          <div className="text-base font-bold text-[var(--accent)] font-mono">{bestDdG.toFixed(1)}</div>
          <div className="text-[10px] text-[var(--text-mute)]">kcal/mol</div>
        </div>
        <div className="bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2 text-center">
          <div className="text-[10px] text-[var(--text-mute)]">Last &Delta;&Delta;G</div>
          <div className={`text-base font-bold font-mono ${lastDelta < 0.5 ? 'text-[var(--pos)]' : 'text-[var(--warn)]'}`}>
            {lastDelta < 100 ? lastDelta.toFixed(2) : '—'}
          </div>
          <div className="text-[10px] text-[var(--text-mute)]">kcal/mol</div>
        </div>
        <div className="bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2 text-center">
          <div className="text-[10px] text-[var(--text-mute)]">Top Candidates</div>
          <div className="text-base font-bold text-[var(--violet)] font-mono">
            {data[data.length - 1]?.topCandidates ?? 0}
          </div>
          <div className="text-[10px] text-[var(--text-mute)]">iter {currentIteration}</div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-52" role="img" aria-label="Convergence line chart">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="iteration"
              tick={{ fill: 'var(--text-dim)', fontSize: 11 }}
              axisLine={{ stroke: 'var(--border)' }}
              tickLine={false}
              label={{ value: 'Iteration', position: 'insideBottom', fill: 'var(--text-dim)', fontSize: 10, offset: -2 }}
            />
            <YAxis
              yAxisId="ddg"
              dataKey="bestDdG"
              orientation="left"
              tick={{ fill: 'var(--text-dim)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(v: number) => `${v}`}
              label={{ value: 'ΔG', angle: -90, position: 'insideLeft', fill: 'var(--text-dim)', fontSize: 10, dx: 12 }}
            />
            <YAxis
              yAxisId="top"
              dataKey="topCandidates"
              orientation="right"
              tick={{ fill: 'var(--text-dim)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={28}
              label={{ value: 'Top N', angle: 90, position: 'insideRight', fill: 'var(--text-dim)', fontSize: 10, dx: -4 }}
            />
            <Tooltip content={<CustomTooltip convergenceData={data} />} cursor={{ stroke: 'var(--border)', strokeWidth: 1 }} />
            <Legend
              wrapperStyle={{ fontSize: '11px', color: 'var(--text-dim)', paddingTop: '4px' }}
            />

            <ReferenceLine
              yAxisId="ddg"
              y={-8.1}
              stroke="var(--teal)"
              strokeDasharray="5 3"
              strokeOpacity={0.5}
              label={{ value: 'Conv. threshold', fill: 'var(--teal)', fontSize: 9, position: 'right' }}
            />

            <ReferenceLine
              yAxisId="ddg"
              x={currentIteration}
              stroke="var(--accent)"
              strokeDasharray="4 2"
              strokeOpacity={0.6}
              label={{ value: 'Current', fill: 'var(--accent)', fontSize: 9, position: 'top' }}
            />

            <Bar
              yAxisId="top"
              dataKey="topCandidates"
              name="Top Candidates"
              fill="var(--violet)"
              fillOpacity={0.3}
              radius={[3, 3, 0, 0]}
            />
            <Line
              yAxisId="ddg"
              type="monotone"
              dataKey="bestDdG"
              name="Best ΔG"
              stroke="var(--teal)"
              strokeWidth={2.5}
              dot={(props) => {
                const { cx, cy, payload } = props
                return (
                  <circle
                    key={`dot-${payload.iteration}`}
                    cx={cx}
                    cy={cy}
                    r={payload.converged ? 6 : 4}
                    fill={payload.converged ? 'var(--pos)' : 'var(--teal)'}
                    stroke={payload.converged ? 'var(--pos)' : 'var(--teal)'}
                    strokeWidth={2}
                    fillOpacity={0.9}
                  />
                )
              }}
              activeDot={{ r: 6, fill: 'var(--teal)', strokeWidth: 0 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
