import { useMemo } from 'react'
import { TableProperties } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import type { Candidate } from '../types'

const SST14 = 'AGCKNFFWKTFTSC'

interface TopAA {
  aa: string
  freq: number     // fraction
  avgDdG: number
}

interface PositionRow {
  position: number
  original: string
  top: TopAA[]
  avgDdG: number   // average ddG across all candidates at this position
}

interface PositionEnrichmentProps {
  candidates: Candidate[]
  referenceSequence?: string
}

export function PositionEnrichment({ candidates, referenceSequence = SST14 }: PositionEnrichmentProps) {
  const seqLen = referenceSequence.length

  const validCandidates = useMemo(() =>
    candidates.filter(c => c.sequence && c.sequence.length === seqLen),
    [candidates, seqLen]
  )

  const rows = useMemo<PositionRow[]>(() => {
    if (validCandidates.length === 0) return []
    const n = validCandidates.length

    return Array.from({ length: seqLen }, (_, pos) => {
      // Count AA frequency and collect ddG values per AA
      const aaCounts: Record<string, number> = {}
      const aaDdGs: Record<string, number[]> = {}

      for (const c of validCandidates) {
        const aa = c.sequence[pos]
        aaCounts[aa] = (aaCounts[aa] ?? 0) + 1
        if (!aaDdGs[aa]) aaDdGs[aa] = []
        aaDdGs[aa].push(c.ddG)
      }

      // Sort by frequency descending, take top 3
      const sorted = Object.entries(aaCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 3)

      const top: TopAA[] = sorted.map(([aa, count]) => ({
        aa,
        freq: count / n,
        avgDdG: aaDdGs[aa].reduce((s, v) => s + v, 0) / aaDdGs[aa].length,
      }))

      const allDdGs = validCandidates.map(c => c.ddG)
      const avgDdG = allDdGs.reduce((s, v) => s + v, 0) / allDdGs.length

      return { position: pos + 1, original: referenceSequence[pos], top, avgDdG }
    })
  }, [validCandidates, referenceSequence, seqLen])

  if (rows.length === 0) {
    return (
      <section className="card" aria-label="Position Enrichment">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest mb-2">Position Enrichment</h2>
        <p className="text-xs text-[var(--text-dim)]">No valid sequences to analyze.</p>
      </section>
    )
  }

  // Find ddG range for color scaling
  const allDdGs = rows.flatMap(r => r.top.map(t => t.avgDdG))
  const minDdG = Math.min(...allDdGs)
  const maxDdG = Math.max(...allDdGs)

  function ddGColor(value: number): string {
    if (maxDdG === minDdG) return 'text-[var(--text-mute)]'
    const norm = (value - minDdG) / (maxDdG - minDdG) // 0=best(min), 1=worst(max)
    // Lower ddG = better = green, higher = red
    if (norm < 0.33) return 'text-[var(--pos)]'
    if (norm < 0.66) return 'text-[var(--warn)]'
    return 'text-[var(--neg)]'
  }

  function ddGBg(value: number): string {
    if (maxDdG === minDdG) return ''
    const norm = (value - minDdG) / (maxDdG - minDdG)
    if (norm < 0.33) return 'bg-[var(--pos-soft)]'
    if (norm < 0.66) return 'bg-[var(--warn-soft)]'
    return 'bg-[var(--neg-soft)]'
  }

  return (
    <section className="card" aria-label="Position Enrichment">
      <div className="flex items-center gap-2 mb-3">
        <TableProperties className="w-4 h-4 text-[var(--text-dim)]" />
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          Position Enrichment
          <HelpTooltip title="Position Enrichment">
            <p>각 서열 위치별 아미노산 빈도와 평균 ΔG를 보여줍니다.</p>
            <p><strong>Top-1/2/3</strong>: 해당 위치에서 가장 빈번한 아미노산과 그 빈도(%). 파란 글씨는 변이, 흰색은 원본 잔기.</p>
            <p><strong>색상</strong>: 초록=유리한 ΔG, 주황=보통, 빨강=불리한 ΔG.</p>
            <p><strong>노란 행</strong>: FWKT 약리활성 부위 (7-10번 위치).</p>
          </HelpTooltip>
        </h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[var(--border)] text-[var(--text-mute)] text-left">
              <th className="px-2 py-1.5 font-semibold">Pos</th>
              <th className="px-2 py-1.5 font-semibold">Ref</th>
              <th className="px-2 py-1.5 font-semibold">Top-1 (freq%)</th>
              <th className="px-2 py-1.5 font-semibold">Top-2</th>
              <th className="px-2 py-1.5 font-semibold">Top-3</th>
              <th className="px-2 py-1.5 font-semibold text-right">Avg ΔG</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(row => {
              const isFWKT = row.position >= 7 && row.position <= 10
              return (
                <tr key={row.position} className={`border-b border-[var(--border)] ${isFWKT ? 'bg-[var(--warn-soft)]' : ''}`}>
                  <td className={`px-2 py-1.5 font-mono ${isFWKT ? 'text-[var(--warn)] font-bold' : 'text-[var(--text-mute)]'}`}>
                    {row.position}
                  </td>
                  <td className="px-2 py-1.5 font-mono font-bold text-[var(--text-mute)]">
                    {row.original}
                  </td>
                  {[0, 1, 2].map(i => {
                    const t = row.top[i]
                    if (!t) return <td key={i} className="px-2 py-1.5 text-[var(--text-dim)]">-</td>
                    const isMutant = t.aa !== row.original
                    return (
                      <td key={i} className={`px-2 py-1.5 ${ddGBg(t.avgDdG)}`}>
                        <span className={`font-mono font-bold ${isMutant ? 'text-[var(--accent)]' : 'text-[var(--text-mute)]'}`}>
                          {t.aa}
                        </span>
                        <span className="text-[var(--text-dim)] ml-1">
                          {(t.freq * 100).toFixed(0)}%
                        </span>
                        <span className={`ml-1 font-mono ${ddGColor(t.avgDdG)}`}>
                          {t.avgDdG.toFixed(1)}
                        </span>
                      </td>
                    )
                  })}
                  <td className={`px-2 py-1.5 text-right font-mono ${ddGColor(row.avgDdG)}`}>
                    {row.avgDdG.toFixed(2)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <p className="text-[10px] text-[var(--text-dim)] mt-2">
        Colors: <span className="text-[var(--pos)]">green</span> = favorable ΔG, <span className="text-[var(--warn)]">amber</span> = moderate, <span className="text-[var(--neg)]">red</span> = unfavorable. FWKT pharmacophore positions highlighted.
      </p>
    </section>
  )
}
