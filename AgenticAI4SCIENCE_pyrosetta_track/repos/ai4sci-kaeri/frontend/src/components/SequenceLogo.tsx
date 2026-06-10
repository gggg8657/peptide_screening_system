import { useMemo } from 'react'
import { HelpTooltip } from './ui/HelpTooltip'
import type { Candidate } from '../types'

const SST14 = 'AGCKNFFWKTFTSC'
const FWKT_START = 6 // 0-indexed positions 6-9

// Chemistry-based amino acid color groups
const AA_COLORS: Record<string, string> = {
  // Hydrophobic — black/dark
  A: 'var(--text-dim)', G: 'var(--text-dim)', V: 'var(--text-dim)', L: 'var(--text-dim)', I: 'var(--text-dim)',
  P: 'var(--text-dim)', F: 'var(--text-dim)', M: 'var(--text-dim)', W: 'var(--text-dim)',
  // Polar — green
  S: 'var(--pos)', T: 'var(--pos)', C: 'var(--pos)', Y: 'var(--pos)', N: 'var(--pos)', Q: 'var(--pos)',
  // Positive — blue
  K: 'var(--accent)', R: 'var(--accent)', H: 'var(--accent)',
  // Negative — red
  D: 'var(--neg)', E: 'var(--neg)',
}

function getAAColor(aa: string): string {
  return AA_COLORS[aa] ?? 'var(--violet)'
}

interface PositionData {
  frequencies: Record<string, number> // aa → fraction
  information: number // bits
  stack: Array<{ aa: string; height: number }> // sorted bottom-to-top
}

function computePositions(sequences: string[], seqLen: number): PositionData[] {
  const n = sequences.length
  if (n === 0) return []

  const positions: PositionData[] = []
  const maxBits = Math.log2(20) // ~4.32 bits

  for (let pos = 0; pos < seqLen; pos++) {
    const counts: Record<string, number> = {}
    let validCount = 0

    for (const seq of sequences) {
      const aa = seq[pos]
      if (aa && aa !== '-') {
        counts[aa] = (counts[aa] ?? 0) + 1
        validCount++
      }
    }

    if (validCount === 0) {
      positions.push({ frequencies: {}, information: 0, stack: [] })
      continue
    }

    const freqs: Record<string, number> = {}
    let entropy = 0

    for (const [aa, count] of Object.entries(counts)) {
      const p = count / validCount
      freqs[aa] = p
      if (p > 0) entropy -= p * Math.log2(p)
    }

    const info = maxBits - entropy

    // Build stack: height = info * freq, sorted ascending (smallest at bottom)
    const stack = Object.entries(freqs)
      .map(([aa, freq]) => ({ aa, height: info * freq }))
      .sort((a, b) => a.height - b.height)

    positions.push({ frequencies: freqs, information: info, stack })
  }

  return positions
}

interface SequenceLogoProps {
  candidates: Candidate[]
  referenceSequence?: string
}

export function SequenceLogo({ candidates, referenceSequence = SST14 }: SequenceLogoProps) {
  const seqLen = referenceSequence.length

  const positions = useMemo(() => {
    const sequences = candidates
      .map(c => c.sequence)
      .filter(s => s && s.length === seqLen)
    return computePositions(sequences, seqLen)
  }, [candidates, seqLen])

  if (positions.length === 0) {
    return (
      <section className="card" aria-label="Sequence Logo">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest mb-2 flex items-center gap-1.5">
          Sequence Logo
          <HelpTooltip title="Sequence Logo">
            <p>Top 후보 서열의 위치별 아미노산 보존도를 시각화합니다.</p>
            <p>글자 높이는 해당 위치에서의 아미노산 빈도에 비례합니다.</p>
            <p><strong>높은 글자</strong>: 보존도 높음 (대부분의 후보가 동일 잔기 사용).</p>
          </HelpTooltip>
        </h2>
        <p className="text-xs text-[var(--text-dim)]">No valid sequences to display.</p>
      </section>
    )
  }

  const maxBits = Math.log2(20)
  const colW = 40
  const logoH = 120
  const svgW = seqLen * colW + 60
  const svgH = logoH + 50
  const leftPad = 30

  return (
    <section className="card" aria-label="Sequence Logo">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          Sequence Logo
          <HelpTooltip title="Sequence Logo">
            <p>Top 후보 서열의 위치별 아미노산 보존도를 시각화합니다.</p>
            <p>글자 높이는 해당 위치에서의 아미노산 빈도에 비례합니다.</p>
            <p><strong>높은 글자</strong>: 보존도 높음 (대부분의 후보가 동일 잔기 사용).</p>
          </HelpTooltip>
        </h2>
        <span className="text-xs text-[var(--text-dim)]">{candidates.length} candidates</span>
      </div>

      <div className="w-full overflow-x-auto">
        <svg viewBox={`0 0 ${svgW} ${svgH}`} className="w-full min-w-[500px]" style={{ height: 'auto', maxHeight: '240px' }}>
          {/* Y-axis labels */}
          {[0, 1, 2, 3, 4].map(v => {
            const y = logoH - (v / maxBits) * logoH + 10
            return (
              <g key={v}>
                <text x={leftPad - 4} y={y + 3} textAnchor="end" fill="var(--text-dim)" fontSize="9" fontFamily="system-ui, sans-serif">{v}</text>
                <line x1={leftPad} y1={y} x2={svgW - 10} y2={y} stroke="var(--border)" strokeWidth={0.5} />
              </g>
            )
          })}
          <text x={6} y={logoH / 2 + 10} textAnchor="middle" fill="var(--text-dim)" fontSize="9" fontFamily="system-ui, sans-serif" transform={`rotate(-90, 6, ${logoH / 2 + 10})`}>bits</text>

          {/* FWKT highlight background */}
          <rect
            x={leftPad + FWKT_START * colW}
            y={4}
            width={4 * colW}
            height={logoH + 12}
            rx={4}
            fill="var(--warn)"
            opacity={0.08}
          />
          <text
            x={leftPad + (FWKT_START + 2) * colW}
            y={svgH - 2}
            textAnchor="middle"
            fill="var(--warn)"
            fontSize="8"
            fontFamily="system-ui, sans-serif"
            opacity={0.7}
          >
            FWKT pharmacophore
          </text>

          {/* Stacked letters per position */}
          {positions.map((pos, i) => {
            const x = leftPad + i * colW + colW / 2
            let yOffset = logoH + 10 // bottom of column

            return (
              <g key={i}>
                {pos.stack.map(({ aa, height }, j) => {
                  const h = (height / maxBits) * logoH
                  if (h < 1) return null
                  yOffset -= h
                  return (
                    <text
                      key={j}
                      x={x}
                      y={yOffset + h}
                      textAnchor="middle"
                      fill={getAAColor(aa)}
                      fontSize={Math.min(h * 0.9, colW * 0.7)}
                      fontWeight="bold"
                      fontFamily="monospace"
                      dominantBaseline="auto"
                    >
                      {aa}
                    </text>
                  )
                })}

                {/* Reference sequence label */}
                <text
                  x={x}
                  y={logoH + 26}
                  textAnchor="middle"
                  fill="var(--text-mute)"
                  fontSize="10"
                  fontFamily="monospace"
                  fontWeight="600"
                >
                  {referenceSequence[i]}
                </text>
                <text
                  x={x}
                  y={logoH + 38}
                  textAnchor="middle"
                  fill="var(--text-dim)"
                  fontSize="8"
                  fontFamily="system-ui, sans-serif"
                >
                  {i + 1}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-2 text-[10px] text-[var(--text-mute)]">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[var(--text-dim)] inline-block" /> Hydrophobic</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-400 inline-block" /> Polar</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400 inline-block" /> Positive</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block" /> Negative</span>
      </div>
    </section>
  )
}
