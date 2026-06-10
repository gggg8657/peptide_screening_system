import { useMemo } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { GitCompareArrows } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import type { Candidate } from '../types'

const SST14 = 'AGCKNFFWKTFTSC'

// BLOSUM62 conservative substitution groups
const CONSERVATIVE_GROUPS = [
  new Set('STA'),
  new Set('NEQK'),
  new Set('NHQK'),
  new Set('NDEQ'),
  new Set('QHRK'),
  new Set('MILV'),
  new Set('MILF'),
  new Set('HY'),
  new Set('FYW'),
  new Set('AG'),
  new Set('DE'),
  new Set('KR'),
  new Set('ST'),
  new Set('NQ'),
]

function isConservative(from: string, to: string): boolean {
  return CONSERVATIVE_GROUPS.some(g => g.has(from) && g.has(to))
}

interface MutationInfo {
  position: number
  original: string
  mutationFreq: number // fraction of candidates mutated at this position
  conservativeCount: number
  nonConservativeCount: number
}

interface MutationAnalysisProps {
  candidates: Candidate[]
  referenceSequence?: string
}

export function MutationAnalysis({ candidates, referenceSequence = SST14 }: MutationAnalysisProps) {
  const seqLen = referenceSequence.length

  const validCandidates = useMemo(() =>
    candidates.filter(c => c.sequence && c.sequence.length === seqLen),
    [candidates, seqLen]
  )

  const mutations = useMemo<MutationInfo[]>(() => {
    if (validCandidates.length === 0) return []
    const n = validCandidates.length

    return Array.from({ length: seqLen }, (_, pos) => {
      let conservative = 0
      let nonConservative = 0

      for (const c of validCandidates) {
        const aa = c.sequence[pos]
        const ref = referenceSequence[pos]
        if (aa !== ref) {
          if (isConservative(ref, aa)) conservative++
          else nonConservative++
        }
      }

      return {
        position: pos + 1,
        original: referenceSequence[pos],
        mutationFreq: (conservative + nonConservative) / n,
        conservativeCount: conservative,
        nonConservativeCount: nonConservative,
      }
    })
  }, [validCandidates, referenceSequence, seqLen])

  const fwktConservation = useMemo(() => {
    if (validCandidates.length === 0) return 0
    const fwkt = referenceSequence.slice(6, 10) // FWKT
    const conserved = validCandidates.filter(c =>
      c.sequence.slice(6, 10) === fwkt
    ).length
    return conserved / validCandidates.length
  }, [validCandidates, referenceSequence])

  const scatterData = useMemo(() => {
    return validCandidates.map(c => {
      let mutCount = 0
      for (let i = 0; i < seqLen; i++) {
        if (c.sequence[i] !== referenceSequence[i]) mutCount++
      }
      return { mutationCount: mutCount, ddG: c.ddG, id: c.id }
    })
  }, [validCandidates, referenceSequence, seqLen])

  const { conservativeTotal, nonConservativeTotal } = useMemo(() => {
    let cons = 0, nonCons = 0
    for (const m of mutations) {
      cons += m.conservativeCount
      nonCons += m.nonConservativeCount
    }
    return { conservativeTotal: cons, nonConservativeTotal: nonCons }
  }, [mutations])

  if (validCandidates.length === 0) {
    return (
      <section className="card" aria-label="Mutation Analysis">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest mb-2">Mutation Analysis</h2>
        <p className="text-xs text-[var(--text-dim)]">No valid sequences to analyze.</p>
      </section>
    )
  }

  const barMaxW = 200

  return (
    <section className="card" aria-label="Mutation Analysis">
      <div className="flex items-center gap-2 mb-4">
        <GitCompareArrows className="w-4 h-4 text-[var(--text-mute)]" />
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          Mutation Analysis
          <HelpTooltip title="Mutation Analysis">
            <p>SST-14 참조 서열 대비 변이 분석입니다.</p>
            <p><strong>보존적 변이</strong> (파랑): BLOSUM62 기준 유사한 아미노산으로의 변이. 구조/기능 보존 가능성 높음.</p>
            <p><strong>비보존적 변이</strong> (주황): 성질이 다른 아미노산으로의 변이. 결합 특성이 크게 바뀔 수 있음.</p>
            <p><strong>FWKT</strong>: 7-10번 위치 약리활성 부위 (pharmacophore). 보존율이 높을수록 SSTR2 결합 유지.</p>
          </HelpTooltip>
        </h2>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="bg-[var(--bg-sunk)] rounded-lg px-3 py-2">
          <span className="text-[10px] text-[var(--text-mute)] uppercase">FWKT Conservation</span>
          <p className={`text-sm font-bold font-mono ${fwktConservation >= 0.9 ? 'text-[var(--pos)]' : fwktConservation >= 0.7 ? 'text-[var(--warn)]' : 'text-[var(--neg)]'}`}>
            {(fwktConservation * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-[var(--bg-sunk)] rounded-lg px-3 py-2">
          <span className="text-[10px] text-[var(--text-mute)] uppercase">Conservative</span>
          <p className="text-sm font-bold font-mono text-[var(--accent)]">{conservativeTotal}</p>
        </div>
        <div className="bg-[var(--bg-sunk)] rounded-lg px-3 py-2">
          <span className="text-[10px] text-[var(--text-mute)] uppercase">Non-Conservative</span>
          <p className="text-sm font-bold font-mono text-[var(--warn)]">{nonConservativeTotal}</p>
        </div>
        <div className="bg-[var(--bg-sunk)] rounded-lg px-3 py-2">
          <span className="text-[10px] text-[var(--text-mute)] uppercase">Candidates</span>
          <p className="text-sm font-bold font-mono text-[var(--text-mute)]">{validCandidates.length}</p>
        </div>
      </div>

      {/* Position mutation frequency bars */}
      <div className="mb-4">
        <h3 className="text-xs text-[var(--text-mute)] mb-2 font-semibold">Position Mutation Frequency</h3>
        <div className="space-y-1">
          {mutations.map(m => {
            const isFWKT = m.position >= 7 && m.position <= 10
            return (
              <div key={m.position} className="flex items-center gap-2 text-xs">
                <span className={`w-6 text-right font-mono ${isFWKT ? 'text-[var(--warn)]' : 'text-[var(--text-mute)]'}`}>{m.position}</span>
                <span className={`w-4 font-mono font-bold ${isFWKT ? 'text-[var(--warn)]' : 'text-[var(--text-mute)]'}`}>{m.original}</span>
                <div className="flex-1 flex items-center gap-0.5" style={{ maxWidth: barMaxW }}>
                  <div
                    className="h-3 bg-[var(--accent-soft)] rounded-l"
                    style={{ width: `${(m.conservativeCount / validCandidates.length) * 100}%` }}
                    title={`Conservative: ${m.conservativeCount}`}
                  />
                  <div
                    className="h-3 bg-[var(--warn-soft)] rounded-r"
                    style={{ width: `${(m.nonConservativeCount / validCandidates.length) * 100}%` }}
                    title={`Non-conservative: ${m.nonConservativeCount}`}
                  />
                </div>
                <span className="text-[var(--text-dim)] w-12 text-right">{(m.mutationFreq * 100).toFixed(0)}%</span>
              </div>
            )
          })}
        </div>
        <div className="flex gap-3 mt-2 text-[10px] text-[var(--text-mute)]">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[var(--accent-soft)] inline-block" /> Conservative</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[var(--warn-soft)] inline-block" /> Non-conservative</span>
        </div>
      </div>

      {/* ΔG vs mutation count scatter */}
      <div>
        <h3 className="text-xs text-[var(--text-mute)] mb-2 font-semibold">ΔG vs Mutation Count</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 8, right: 16, bottom: 20, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                type="number"
                dataKey="mutationCount"
                name="Mutations"
                tick={{ fill: 'var(--text-dim)', fontSize: 10 }}
                label={{ value: 'Mutation count', position: 'insideBottom', offset: -12, fill: 'var(--text-dim)', fontSize: 10 }}
              />
              <YAxis
                type="number"
                dataKey="ddG"
                name="ΔG"
                tick={{ fill: 'var(--text-dim)', fontSize: 10 }}
                label={{ value: 'ΔG (kcal/mol)', angle: -90, position: 'insideLeft', offset: 4, fill: 'var(--text-dim)', fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '11px' }}
                labelStyle={{ color: 'var(--text-dim)' }}
                formatter={(value?: number | string, name?: string) => [Number(value ?? 0).toFixed(2), name ?? '']}
              />
              <Scatter data={scatterData} fill="var(--accent)" fillOpacity={0.7} r={3} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  )
}
