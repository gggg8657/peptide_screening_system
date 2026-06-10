import { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { BarChart3 } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import type { Candidate } from '../types'

const BIN_WIDTH = 2.5
const BIN_MIN = -50
const BIN_MAX = 0
const QC_THRESHOLD = -5.0

interface BinDatum {
  label: string
  midpoint: number
  count: number
  passing: boolean
}

function computeStats(values: number[]) {
  if (values.length === 0) return { mean: 0, median: 0, std: 0, passPct: 0 }
  const sorted = [...values].sort((a, b) => a - b)
  const n = sorted.length
  const mean = sorted.reduce((s, v) => s + v, 0) / n
  const mid = Math.floor(n / 2)
  const median = n % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
  const variance = sorted.reduce((s, v) => s + (v - mean) ** 2, 0) / n
  const std = Math.sqrt(variance)
  const passPct = (sorted.filter(v => v <= QC_THRESHOLD).length / n) * 100
  return { mean, median, std, passPct }
}

interface TooltipPayloadEntry {
  value?: number
}

function BinTooltip({ active, payload, label }: {
  active?: boolean
  payload?: TooltipPayloadEntry[]
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-xs">
      <p className="font-semibold text-[var(--text-mute)] mb-1">ΔG: {label} kcal/mol</p>
      <p className="text-[var(--text-mute)]">Count: <span className="font-bold text-[var(--accent)]">{payload[0].value}</span></p>
    </div>
  )
}

interface DdGDistributionProps {
  candidates: Candidate[]
}

export function DdGDistribution({ candidates }: DdGDistributionProps) {
  const { bins, stats } = useMemo(() => {
    const ddgValues = candidates.map(c => c.ddG)
    const s = computeStats(ddgValues)

    const numBins = Math.ceil((BIN_MAX - BIN_MIN) / BIN_WIDTH)
    const b: BinDatum[] = Array.from({ length: numBins }, (_, i) => {
      const lo = BIN_MIN + i * BIN_WIDTH
      const hi = lo + BIN_WIDTH
      const mid = lo + BIN_WIDTH / 2
      return {
        label: `${lo.toFixed(1)}`,
        midpoint: mid,
        count: 0,
        passing: hi <= QC_THRESHOLD,
      }
    })

    for (const v of ddgValues) {
      const idx = Math.floor((v - BIN_MIN) / BIN_WIDTH)
      if (idx >= 0 && idx < b.length) b[idx].count++
    }

    return { bins: b, stats: s }
  }, [candidates])

  if (candidates.length === 0) return null

  return (
    <section className="card flex flex-col gap-3" aria-label="ΔG Distribution Histogram">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            ΔG Distribution
            <HelpTooltip title="ΔG Distribution">
              <p>전체 후보의 결합 에너지(ΔG) 분포 히스토그램입니다.</p>
              <p><strong>빨간 점선</strong>: QC 게이트 임계값 (-5.0 kcal/mol). 이 선 왼쪽이 통과 영역.</p>
              <p><strong>해석</strong>: 분포가 왼쪽(더 음수)으로 이동할수록 iteration이 좋은 후보를 생성하고 있다는 의미입니다.</p>
            </HelpTooltip>
          </h2>
          <p className="text-xs text-[var(--text-mute)] mt-0.5">
            Binding energy distribution across {candidates.length} candidates
          </p>
        </div>
      </div>

      {/* Stats summary */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: 'Mean', value: `${stats.mean.toFixed(2)}`, unit: 'kcal/mol' },
          { label: 'Median', value: `${stats.median.toFixed(2)}`, unit: 'kcal/mol' },
          { label: 'Std Dev', value: `${stats.std.toFixed(2)}`, unit: 'kcal/mol' },
          { label: 'Pass Gate', value: `${stats.passPct.toFixed(1)}%`, unit: `<= ${QC_THRESHOLD}` },
        ].map(item => (
          <div key={item.label} className="rounded-lg p-2 bg-[var(--bg-elev)] border border-[var(--border)] text-center">
            <div className="text-[10px] text-[var(--text-mute)] font-medium">{item.label}</div>
            <div className="text-sm font-bold text-[var(--text-mute)] mt-0.5 font-mono tabular-nums">{item.value}</div>
            <div className="text-[10px] text-[var(--text-mute)]">{item.unit}</div>
          </div>
        ))}
      </div>

      {/* Histogram */}
      <div className="h-52" role="img" aria-label="ΔG histogram">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={bins} barCategoryGap="5%">
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: 'var(--text-dim)', fontSize: 10 }}
              axisLine={{ stroke: 'var(--border)' }}
              tickLine={false}
              interval={3}
              label={{ value: 'ΔG (kcal/mol)', position: 'insideBottom', offset: -5, fill: 'var(--text-dim)', fontSize: 10 }}
            />
            <YAxis
              tick={{ fill: 'var(--text-dim)', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              width={30}
              label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: 'var(--text-dim)', fontSize: 10 }}
            />
            <Tooltip content={<BinTooltip />} cursor={{ fill: 'var(--bg-sunk)' }} />
            <ReferenceLine
              x={`${QC_THRESHOLD.toFixed(1)}`}
              stroke="var(--neg)"
              strokeWidth={2}
              strokeDasharray="6 3"
              label={{ value: `Gate: ${QC_THRESHOLD}`, fill: 'var(--neg)', fontSize: 10, position: 'top' }}
            />
            <Bar dataKey="count" fill="var(--teal)" fillOpacity={0.7} radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
