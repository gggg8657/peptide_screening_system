import { useMemo, useState } from 'react'
import { HelpTooltip } from './ui/HelpTooltip'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { QCGate } from '../types'

const PASS_COLOR = 'var(--pos)'
const FAIL_COLOR = 'var(--neg)'

interface TooltipEntry {
  name?: string
  value?: number
  color?: string
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipEntry[]
  label?: string | number
  gates: QCGate[]
}

function CustomTooltip({ active, payload, label, gates }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null

  const gate = gates.find(g => g.name === label)
  const passed = payload.find((p: TooltipEntry) => p.name === 'Passed')?.value ?? 0
  const failed = payload.find((p: TooltipEntry) => p.name === 'Failed')?.value ?? 0
  const total = (passed as number) + (failed as number)
  const rate = total > 0 ? Math.round(((passed as number) / total) * 100) : 0

  return (
    <div className="bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-3 shadow-xl text-xs">
      <p className="font-semibold text-[var(--text-mute)] mb-1">{label}</p>
      {gate && (
        <p className="text-[var(--text-mute)] mb-2 font-mono">{gate.criterion}</p>
      )}
      <div className="flex flex-col gap-1">
        <div className="flex justify-between gap-4">
          <span className="text-[var(--pos)]">Passed</span>
          <span className="font-bold text-[var(--pos)]">{passed}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-[var(--neg)]">Failed</span>
          <span className="font-bold text-[var(--neg)]">{failed}</span>
        </div>
        <div className="border-t border-[var(--border)] mt-1 pt-1 flex justify-between gap-4">
          <span className="text-[var(--text-mute)]">Pass Rate</span>
          <span className="font-bold text-[var(--text-mute)]">{rate}%</span>
        </div>
      </div>
    </div>
  )
}

interface QCGateChartProps {
  gates: QCGate[]
}

export function QCGateChart({ gates }: QCGateChartProps) {
  const [selectedGate, setSelectedGate] = useState<string>('all')

  const visibleGates = useMemo(
    () => (selectedGate === 'all' ? gates : gates.filter(g => g.name === selectedGate)),
    [gates, selectedGate]
  )

  const chartData = visibleGates.map(g => ({
    name: g.name,
    criterion: g.criterion,
    Passed: g.passed,
    Failed: g.failed,
    total: g.total,
    passRate: g.total > 0 ? Math.round((g.passed / g.total) * 100) : 0,
  }))

  return (
    <section className="card flex flex-col gap-3" aria-label="QC Gate Chart">
      <div>
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          QC Gate Funnel
          <HelpTooltip title="QC Gate Funnel">
            <p>품질 관리(QC) 게이트 통과율을 퍼널 형태로 보여줍니다.</p>
            <p><strong>게이트 순서</strong>: ΔG 임계값 → 입체 충돌 검사 → 약리활성 부위 보존 → 최종 통과.</p>
            <p>각 단계에서 탈락한 후보 수와 비율을 확인할 수 있습니다.</p>
          </HelpTooltip>
        </h2>
        <p className="text-xs text-[var(--text-mute)] mt-0.5">
          Candidate pass-through per quality gate
        </p>
      </div>

      {/* Gate summary badges */}
      <div className="grid grid-cols-4 gap-2">
        <button
          onClick={() => setSelectedGate('all')}
          className={`rounded-lg p-2 text-center border transition-colors ${
            selectedGate === 'all'
              ? 'bg-[var(--accent-soft)] border-[var(--accent)]/30 text-blue-200'
              : 'bg-[var(--bg-elev)] border-[var(--border)] text-[var(--text-dim)] hover:border-[var(--border-strong)]'
          }`}
        >
          <div className="text-[10px] font-medium">All</div>
          <div className="text-[10px] mt-0.5">Reset</div>
        </button>
        {gates.map(gate => {
          const rate = gate.total > 0 ? Math.round((gate.passed / gate.total) * 100) : 0
          return (
            <button
              key={gate.name}
              onClick={() => setSelectedGate(gate.name)}
              className={`rounded-lg p-2 text-center border transition-colors ${
                selectedGate === gate.name
                  ? 'bg-[var(--accent-soft)] border-[var(--accent)]/30 text-cyan-200'
                  : 'bg-[var(--bg-elev)] border-[var(--border)] text-[var(--text-mute)] hover:border-[var(--border-strong)]'
              }`}
            >
              <div className="text-[10px] text-[var(--text-mute)] font-medium">{gate.name}</div>
              <div className="text-lg font-bold text-[var(--text-mute)] my-0.5">{rate}%</div>
              <div className="text-[10px] text-[var(--pos)]">{gate.passed}/{gate.total}</div>
              <div className="mt-1.5 h-1 bg-[var(--bg-sunk)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full transition-all duration-700"
                  style={{ width: `${rate}%` }}
                />
              </div>
            </button>
          )
        })}
      </div>

      {/* Bar Chart */}
      <div className="h-48" role="img" aria-label="QC gate bar chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            barCategoryGap="30%"
            barGap={2}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border)"
              vertical={false}
            />
            <XAxis
              dataKey="name"
              tick={{ fill: 'var(--text-dim)', fontSize: 11 }}
              axisLine={{ stroke: 'var(--border)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: 'var(--text-dim)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={28}
            />
            <Tooltip content={<CustomTooltip gates={visibleGates} />} cursor={{ fill: 'var(--bg-sunk)' }} />
            <Legend
              wrapperStyle={{ fontSize: '11px', color: 'var(--text-dim)', paddingTop: '8px' }}
            />
            <Bar dataKey="Passed" stackId="a" fill={PASS_COLOR} radius={[0, 0, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={PASS_COLOR} fillOpacity={0.75} />
              ))}
            </Bar>
            <Bar dataKey="Failed" stackId="a" fill={FAIL_COLOR} radius={[4, 4, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={FAIL_COLOR} fillOpacity={0.75} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Criterion labels */}
      <div className="grid grid-cols-2 gap-1.5">
        {visibleGates.map(gate => (
          <div key={gate.name} className="flex items-center gap-1.5 text-[10px]">
            <span className="text-[var(--text-mute)] font-semibold w-12 shrink-0">{gate.name}:</span>
            <span className="text-[var(--text-mute)] font-mono">{gate.criterion}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
