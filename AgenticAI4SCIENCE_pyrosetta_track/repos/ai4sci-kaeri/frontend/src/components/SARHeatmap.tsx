import { useMemo } from 'react'
import { Grid3x3 } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import type { Candidate } from '../types'

const SST14 = 'AGCKNFFWKTFTSC'
const AMINO_ACIDS = 'ACDEFGHIKLMNPQRSTVWY'.split('')
const PHARMACOPHORE_POSITIONS = [7, 8, 9, 10] // FWKT (1-indexed)

function interpolateColor(freq: number, maxFreq: number): string {
  if (maxFreq === 0 || freq === 0) return 'var(--bg-sunk)'
  const t = freq / maxFreq
  if (t < 0.5) {
    const s = t / 0.5
    return `color-mix(in oklch, var(--bg-sunk) ${Math.round((1 - s) * 100)}%, var(--accent) ${Math.round(s * 100)}%)`
  }
  const s = (t - 0.5) / 0.5
  return `color-mix(in oklch, var(--accent) ${Math.round((1 - s) * 100)}%, var(--warn) ${Math.round(s * 100)}%)`
}

interface SARHeatmapProps {
  candidates: Candidate[]
}

export function SARHeatmap({ candidates }: SARHeatmapProps) {
  const { matrix, maxFreq } = useMemo(() => {
    const mat: number[][] = Array.from({ length: AMINO_ACIDS.length }, () =>
      Array(SST14.length).fill(0) as number[]
    )
    let max = 0
    for (const c of candidates) {
      if (!c.sequence || c.sequence.length !== SST14.length) continue
      for (let pos = 0; pos < SST14.length; pos++) {
        const aa = c.sequence[pos]
        if (aa === SST14[pos]) continue // skip native residue
        const aaIdx = AMINO_ACIDS.indexOf(aa)
        if (aaIdx >= 0) {
          mat[aaIdx][pos]++
          if (mat[aaIdx][pos] > max) max = mat[aaIdx][pos]
        }
      }
    }
    return { matrix: mat, maxFreq: max }
  }, [candidates])

  if (candidates.length === 0) return null

  const cellW = 28
  const cellH = 16
  const labelW = 24
  const labelH = 24
  const svgW = labelW + SST14.length * cellW + 10
  const svgH = labelH + AMINO_ACIDS.length * cellH + 10

  return (
    <section className="card flex flex-col gap-3" aria-label="SAR Heatmap">
      <div>
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          <Grid3x3 className="w-4 h-4" />
          SAR Heatmap
          <HelpTooltip title="SAR Heatmap">
            <p>구조-활성 관계(SAR) 히트맵입니다.</p>
            <p>각 셀은 특정 위치의 아미노산 변이가 ΔG에 미치는 평균 영향을 색상으로 나타냅니다.</p>
            <p><strong>초록</strong>: ΔG 개선(유리), <strong>빨강</strong>: ΔG 악화(불리).</p>
          </HelpTooltip>
        </h2>
        <p className="text-xs text-[var(--text-mute)] mt-0.5">
          Mutation frequency vs SST-14 native ({SST14}) &middot; FWKT pharmacophore highlighted
        </p>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 text-[10px] text-[var(--text-mute)]">
        <span>Frequency:</span>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded-sm" style={{ background: 'var(--bg-sunk)' }} />
          <span>0</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded-sm" style={{ background: 'var(--accent)' }} />
          <span>mid</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 rounded-sm" style={{ background: 'var(--warn)' }} />
          <span>high</span>
        </div>
        {maxFreq > 0 && <span className="ml-2 text-[var(--text-mute)]">(max: {maxFreq})</span>}
      </div>

      <div className="overflow-x-auto">
        <svg
          width={svgW}
          height={svgH}
          viewBox={`0 0 ${svgW} ${svgH}`}
          className="block"
          role="img"
          aria-label="Position vs amino acid mutation frequency matrix"
        >
          {/* Position labels (x-axis) */}
          {SST14.split('').map((aa, i) => {
            const x = labelW + i * cellW + cellW / 2
            const isPharmacophore = PHARMACOPHORE_POSITIONS.includes(i + 1)
            return (
              <g key={`pos-${i}`}>
                <text
                  x={x}
                  y={labelH - 4}
                  textAnchor="middle"
                  className="text-[10px]"
                  fill={isPharmacophore ? 'var(--warn)' : 'var(--text-dim)'}
                  fontWeight={isPharmacophore ? 'bold' : 'normal'}
                  fontFamily="monospace"
                >
                  {aa}{i + 1}
                </text>
                {isPharmacophore && (
                  <rect
                    x={labelW + i * cellW}
                    y={labelH}
                    width={cellW}
                    height={AMINO_ACIDS.length * cellH}
                    fill="var(--warn)"
                    fillOpacity={0.06}
                  />
                )}
              </g>
            )
          })}

          {/* Amino acid labels (y-axis) + cells */}
          {AMINO_ACIDS.map((aa, aaIdx) => {
            const y = labelH + aaIdx * cellH
            return (
              <g key={`aa-${aa}`}>
                <text
                  x={labelW - 4}
                  y={y + cellH / 2 + 4}
                  textAnchor="end"
                  fill="var(--text-dim)"
                  className="text-[10px]"
                  fontFamily="monospace"
                >
                  {aa}
                </text>
                {SST14.split('').map((nativeAA, posIdx) => {
                  const freq = matrix[aaIdx][posIdx]
                  const isNative = aa === nativeAA
                  const cx = labelW + posIdx * cellW
                  return (
                    <g key={`cell-${aaIdx}-${posIdx}`}>
                      <rect
                        x={cx + 0.5}
                        y={y + 0.5}
                        width={cellW - 1}
                        height={cellH - 1}
                        rx={2}
                        fill={isNative ? 'var(--bg-sunk)' : interpolateColor(freq, maxFreq)}
                        stroke={isNative ? 'var(--text-dim)' : 'none'}
                        strokeWidth={isNative ? 1 : 0}
                        strokeDasharray={isNative ? '2 2' : undefined}
                      />
                      {freq > 0 && !isNative && (
                        <text
                          x={cx + cellW / 2}
                          y={y + cellH / 2 + 4}
                          textAnchor="middle"
                          fill="var(--text)"
                          fontSize={9}
                          fontFamily="monospace"
                        >
                          {freq}
                        </text>
                      )}
                      {isNative && (
                        <text
                          x={cx + cellW / 2}
                          y={y + cellH / 2 + 3}
                          textAnchor="middle"
                          fill="var(--text-dim)"
                          fontSize={8}
                          fontFamily="monospace"
                        >
                          ref
                        </text>
                      )}
                    </g>
                  )
                })}
              </g>
            )
          })}
        </svg>
      </div>
    </section>
  )
}
