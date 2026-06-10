import { memo, useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { cn } from '../lib/utils'
import { useClickOutside } from '../hooks/useClickOutside'
import type { Candidate } from '../types'
import { ChevronDown, Loader2 } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'

// --- Pharmacology API response types ---

interface ExtinctionCoefficient {
  epsilon_280_ss: number
  epsilon_280_reduced: number
  n_trp: number
  n_tyr: number
  n_disulfide: number
}

interface NEndRule {
  n_terminal_residue: string
  predicted_halflife_hours: number
  stability_category: string
}

interface HydrophobicMoment {
  mu_h_max: number
  angle_deg: number
  window: number
}

interface WimleyWhite {
  ww_total_kcal: number
  ww_per_residue: number
  interpretation: string
}

interface ChargePhProfile {
  charge_at_ph74: number
  charge_at_ph65: number
  delta_charge_tumor_vs_plasma: number
  profile: Record<string, number>
}

interface ProteaseSiteEntry {
  count: number
  positions: number[]
}

interface ProteaseSites {
  chymotrypsin: ProteaseSiteEntry
  trypsin: ProteaseSiteEntry
  neprilysin: ProteaseSiteEntry
  pepsin: ProteaseSiteEntry
  total_sites: number
}

interface BlosumMutation {
  position: number
  from: string
  to: string
  blosum62_score: number
  category: string
}

interface Blosum62 {
  n_mutations: number
  total_blosum62_score: number
  avg_score: number
  n_conservative: number
  n_semi_conservative: number
  n_non_conservative: number
  mutations: BlosumMutation[]
}

interface MetalCoordResidue {
  position: number
  residue: string
  coordination_site: string
  preferred_metals: string[]
  binding_strength: string
}

interface MetalCoordination {
  coordinating_residues: MetalCoordResidue[]
  total_count: number
  n_strong: number
  chelator_interference_risk: string
}

interface MolecularWeight {
  mw_average: number
  mw_monoisotopic: number
  n_residues?: number
  n_disulfide?: number
}

interface RadiolysisVulnerableResidue {
  position: number
  residue: string
  mechanism: string
  weight: number
}

interface RadiolysisResult {
  total_score: number
  risk_level: 'low' | 'moderate' | 'high'
  vulnerable_residues: RadiolysisVulnerableResidue[]
  critical_positions?: RadiolysisVulnerableResidue[]
}

interface PharmacologyResult {
  sequence: string
  length: number
  gravy: number
  boman_index: number
  instability_index: number
  instability_classification: string
  aliphatic_index: number
  isoelectric_point: number
  extinction_coefficient: ExtinctionCoefficient
  n_end_rule: NEndRule
  hydrophobic_moment: HydrophobicMoment
  wimley_white: WimleyWhite
  charge_ph_profile: ChargePhProfile
  protease_sites: ProteaseSites
  blosum62: Blosum62
  metal_coordination: MetalCoordination
  molecular_weight?: MolecularWeight
  radiolysis_susceptibility?: RadiolysisResult
}

// --- Helper components ---

const MetricCard = memo(function MetricCard({
  label,
  children,
  className,
}: {
  label: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('bg-[var(--bg-sunk)] border border-[var(--border)] rounded-lg p-3', className)}>
      <div className="text-[10px] text-[var(--text)] uppercase tracking-wider font-semibold mb-1.5">
        {label}
      </div>
      <div className="text-sm">{children}</div>
    </div>
  )
})

const StatusBadge = memo(function StatusBadge({
  label,
  color,
}: {
  label: string
  color: 'green' | 'red' | 'amber' | 'cyan' | 'slate'
}) {
  const colors = {
    green: 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30',
    red: 'bg-[var(--neg-soft)] text-[var(--neg)] border-[var(--neg)]/30',
    amber: 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30',
    cyan: 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30',
    slate: 'bg-[var(--bg-elev)]/40 text-[var(--text-mute)] border-[var(--border)]/30',
  }
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border', colors[color])}>
      {label}
    </span>
  )
})

// --- Main component ---

interface PharmacologyPanelProps {
  candidates: Candidate[]
}

function normSeq(s: string): string {
  return s.toUpperCase().trim()
}

export function PharmacologyPanel({ candidates }: PharmacologyPanelProps) {
  const [pharmaData, setPharmaData] = useState<Map<string, PharmacologyResult>>(new Map())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedSeq, setSelectedSeq] = useState<string>('')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const closeDropdown = useCallback(() => setDropdownOpen(false), [])
  useClickOutside(dropdownRef, closeDropdown, dropdownOpen)
  const fetchedRef = useRef<string>('')

  const uniqueSequences = useMemo(
    () => [...new Set(candidates.map(c => c.sequence).filter(Boolean).map(normSeq))].sort(),
    [candidates],
  )
  const seqKey = uniqueSequences.join(',')

  // Build a map from sequence to best candidate (lowest rank)
  const seqToBestCandidate = useMemo(() => {
    const map = new Map<string, Candidate>()
    for (const c of candidates) {
      if (!c.sequence) continue
      const key = normSeq(c.sequence)
      const existing = map.get(key)
      if (!existing || c.rank < existing.rank) {
        map.set(key, c)
      }
    }
    return map
  }, [candidates])

  /* eslint-disable react-hooks/set-state-in-effect -- init from props + fetch lifecycle */
  useEffect(() => {
    if (!selectedSeq && candidates.length > 0) {
      const best = [...candidates].sort((a, b) => a.rank - b.rank)[0]
      if (best?.sequence) setSelectedSeq(normSeq(best.sequence))
    }
  }, [candidates, selectedSeq])

  useEffect(() => {
    if (!seqKey || seqKey === fetchedRef.current) return
    const sequences = seqKey.split(',')
    if (sequences.length === 0) return
    fetchedRef.current = seqKey

    const controller = new AbortController()
    setLoading(true)
    setError(null)

    fetch('/api/pharmacology/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequences }),
      signal: controller.signal,
    })
      .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then(data => {
        if (!data?.results) return
        const map = new Map<string, PharmacologyResult>()
        for (const r of data.results as PharmacologyResult[]) {
          if (r.sequence) map.set(normSeq(r.sequence), r)
        }
        setPharmaData(map)
      })
      .catch(err => {
        if (err.name !== 'AbortError') {
          setError(err.message ?? 'Failed to fetch pharmacology data')
        }
      })
      .finally(() => {
        setLoading(false)
      })

    return () => controller.abort()
  }, [seqKey])
  /* eslint-enable react-hooks/set-state-in-effect */

  if (candidates.length === 0) return null

  const selectedKey = selectedSeq ? normSeq(selectedSeq) : ''
  const data = selectedKey ? pharmaData.get(selectedKey) : undefined
  const bestCandidate = selectedKey ? seqToBestCandidate.get(selectedKey) : undefined

  return (
    <section className="card flex flex-col gap-3" aria-label="Pharmacology Panel">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
            Pharmacological Properties
            <HelpTooltip title="Pharmacological Properties">
              <p>13가지 문헌 기반 약리학적 특성을 계산하여 표시합니다.</p>
              <p><strong>PASS/FAIL 규칙</strong>: FWKT 보존, K9-D122 염다리, Cys3-Cys14 이황화결합, Phe6-Phe11 스태킹, N-term 킬레이터.</p>
              <p><strong>수치 특성</strong>: 소수성, Boman 지수, 불안정성 지수, 분자량 등 순수 물리화학적 값만 사용.</p>
            </HelpTooltip>
          </h2>
          <p className="text-xs text-[var(--text-mute)] mt-0.5">
            13 computational methods for peptide characterization
          </p>
        </div>

        {/* Candidate selector dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(o => !o)}
            aria-expanded={dropdownOpen}
            aria-haspopup="listbox"
            className="flex items-center gap-2 bg-[var(--bg-elev)] border border-[var(--border)] hover:border-[var(--border-strong)] rounded-lg px-3 py-1.5 text-xs text-[var(--text)] transition-colors"
          >
            <span className="font-mono">
              {bestCandidate ? bestCandidate.id : (selectedSeq ? selectedSeq.slice(0, 10) + '…' : '—')}
            </span>
            {bestCandidate && (
              <span className="text-[10px] text-[var(--text-mute)]">
                Rank {bestCandidate.rank}
              </span>
            )}
            <ChevronDown className="w-3 h-3 text-[var(--text-mute)]" />
          </button>
          {dropdownOpen && (
            <div role="listbox" className="absolute right-0 top-full mt-1 z-50 w-72 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg shadow-xl overflow-hidden max-h-64 overflow-y-auto">
              {uniqueSequences.map(seq => {
                const cand = seqToBestCandidate.get(seq)
                const isCurrent = seq === selectedKey
                return (
                  <button
                    key={seq}
                    role="option"
                    aria-selected={isCurrent}
                    onClick={() => { setSelectedSeq(normSeq(seq)); setDropdownOpen(false) }}
                    className={cn(
                      'w-full text-left px-3 py-2 text-xs border-b border-[var(--border)] transition-colors',
                      isCurrent ? 'bg-[var(--accent-soft)] text-[var(--accent)]' : 'text-[var(--text-mute)] hover:bg-[var(--bg-elev)]',
                    )}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-medium">{cand?.id ?? seq.slice(0, 14)}</span>
                      {isCurrent && <span className="text-[var(--accent)] text-[10px]">(viewing)</span>}
                    </div>
                    <div className="flex gap-3 mt-0.5 text-[10px] text-[var(--text-mute)]">
                      {cand && <span>Rank {cand.rank}</span>}
                      {cand && <span>ΔG {cand.ddG.toFixed(1)}</span>}
                      <span className="font-mono tracking-wider">{seq}</span>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-8 gap-2">
          <Loader2 className="w-4 h-4 text-[var(--accent)] animate-spin" />
          <span className="text-xs text-[var(--text-mute)]">Loading pharmacology data…</span>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="border border-[var(--neg)]/30 bg-[var(--neg-soft)] rounded-lg px-4 py-3 text-xs text-[var(--neg)]">
          {error}
        </div>
      )}

      {/* Data display */}
      {data && !loading && (
        <div className="space-y-3">
          {/* Row 1: Physical Properties */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
            <MetricCard label="GRAVY (Hydropathy)">
              <span className={cn(
                'font-mono tabular-nums font-semibold',
                data.gravy >= -2 && data.gravy <= 1 ? 'text-[var(--pos)]' : 'text-[var(--neg)]',
              )}>
                {data.gravy.toFixed(4)}
              </span>
              <div className="text-[10px] text-[var(--text-mute)] mt-0.5">
                {data.gravy >= -2 && data.gravy <= 1 ? 'Normal range [-2, 1]' : 'Outside normal range'}
              </div>
            </MetricCard>

            <MetricCard label="Boman Index">
              <span className={cn(
                'font-mono tabular-nums font-semibold',
                data.boman_index >= 2.48 ? 'text-[var(--pos)]' : 'text-[var(--warn)]',
              )}>
                {data.boman_index.toFixed(4)}
              </span>
              <div className="text-[10px] text-[var(--text-mute)] mt-0.5">
                {data.boman_index >= 2.48
                  ? 'High protein binding potential'
                  : 'Below GPCR threshold (2.48)'}
              </div>
            </MetricCard>

            <MetricCard label="Instability Index">
              <div className="flex items-center gap-2">
                <span className={cn(
                  'font-mono tabular-nums font-semibold',
                  data.instability_index < 40 ? 'text-[var(--pos)]' : 'text-[var(--neg)]',
                )}>
                  {data.instability_index.toFixed(2)}
                </span>
                <StatusBadge
                  label={data.instability_classification.toUpperCase()}
                  color={data.instability_index < 40 ? 'green' : 'red'}
                />
              </div>
            </MetricCard>

            <MetricCard label="Aliphatic Index">
              <span className="font-mono tabular-nums font-semibold text-[var(--text)]">
                {data.aliphatic_index.toFixed(2)}
              </span>
              <div className="text-[10px] text-[var(--text-mute)] mt-0.5">
                Relative aliphatic side-chain volume
              </div>
            </MetricCard>

            {data.molecular_weight && (
              <MetricCard label="Molecular Weight">
                <span className="font-mono tabular-nums font-semibold text-[var(--text)]">
                  {data.molecular_weight.mw_average.toFixed(2)}
                  <span className="text-[10px] text-[var(--text-mute)] ml-1 font-normal">Da</span>
                </span>
                <div className="text-[10px] text-[var(--text-mute)] mt-0.5">
                  mono: {data.molecular_weight.mw_monoisotopic.toFixed(2)} Da
                </div>
              </MetricCard>
            )}
          </div>

          {/* Row 2: Electrochemistry */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <MetricCard label="pI (Isoelectric Point)">
              <span className="font-mono tabular-nums font-semibold text-[var(--text)]">
                {data.isoelectric_point.toFixed(4)}
              </span>
              <div className="text-[10px] text-[var(--text-mute)] mt-0.5">SS corrected</div>
            </MetricCard>

            <MetricCard label="Extinction Coeff. (280 nm)">
              <div className="space-y-0.5">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-[var(--text-mute)]">SS bonded</span>
                  <span className="font-mono tabular-nums text-[var(--text)] text-xs">
                    {data.extinction_coefficient.epsilon_280_ss.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-[var(--text-mute)]">Reduced</span>
                  <span className="font-mono tabular-nums text-[var(--text)] text-xs">
                    {data.extinction_coefficient.epsilon_280_reduced.toLocaleString()}
                  </span>
                </div>
                <div className="text-[10px] text-[var(--text-mute)] mt-0.5">
                  {data.extinction_coefficient.n_trp}W / {data.extinction_coefficient.n_tyr}Y / {data.extinction_coefficient.n_disulfide}SS
                </div>
              </div>
            </MetricCard>

            <MetricCard label="N-end Rule Half-life">
              <div className="flex items-center gap-2">
                <span className="font-mono tabular-nums font-semibold text-[var(--text)]">
                  {data.n_end_rule.predicted_halflife_hours}h
                </span>
                <StatusBadge
                  label={data.n_end_rule.stability_category.replace('_', ' ').toUpperCase()}
                  color={
                    data.n_end_rule.stability_category === 'stable' ? 'green'
                      : data.n_end_rule.stability_category === 'intermediate' ? 'amber'
                      : 'red'
                  }
                />
              </div>
              <div className="text-[10px] text-[var(--text-mute)] mt-0.5">
                N-term: {data.n_end_rule.n_terminal_residue}
              </div>
            </MetricCard>

            <MetricCard label="Hydrophobic Moment">
              <span className="font-mono tabular-nums font-semibold text-[var(--text)]">
                {data.hydrophobic_moment.mu_h_max.toFixed(4)}
              </span>
              <div className="text-[10px] text-[var(--text-mute)] mt-0.5">
                angle={data.hydrophobic_moment.angle_deg} / win={data.hydrophobic_moment.window}
              </div>
            </MetricCard>
          </div>

          {/* Row 3: Membrane & Stability */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
            <MetricCard label="Wimley-White Transfer">
              <div className="flex items-center gap-2">
                <span className={cn(
                  'font-mono tabular-nums font-semibold',
                  data.wimley_white.interpretation === 'aqueous-favorable' ? 'text-[var(--pos)]' : 'text-[var(--neg)]',
                )}>
                  {data.wimley_white.ww_total_kcal.toFixed(2)} kcal
                </span>
              </div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <StatusBadge
                  label={data.wimley_white.interpretation === 'aqueous-favorable' ? 'AQUEOUS' : 'MEMBRANE'}
                  color={data.wimley_white.interpretation === 'aqueous-favorable' ? 'green' : 'red'}
                />
                <span className="text-[10px] text-[var(--text-mute)]">
                  {data.wimley_white.ww_per_residue.toFixed(3)}/res
                </span>
              </div>
            </MetricCard>

            <MetricCard label="Charge at pH 7.4 vs 6.5">
              <div className="space-y-0.5">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-[var(--text-mute)]">pH 7.4 (plasma)</span>
                  <span className="font-mono tabular-nums text-[var(--text)] text-xs">
                    {data.charge_ph_profile.charge_at_ph74 >= 0 ? '+' : ''}{data.charge_ph_profile.charge_at_ph74.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-[var(--text-mute)]">pH 6.5 (tumor)</span>
                  <span className="font-mono tabular-nums text-[var(--text)] text-xs">
                    {data.charge_ph_profile.charge_at_ph65 >= 0 ? '+' : ''}{data.charge_ph_profile.charge_at_ph65.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center border-t border-[var(--border)]/50 pt-0.5 mt-0.5">
                  <span className="text-[10px] text-[var(--accent)] font-semibold">Tumor selectivity</span>
                  <span className="font-mono tabular-nums text-[var(--accent)] text-xs font-semibold">
                    {data.charge_ph_profile.delta_charge_tumor_vs_plasma >= 0 ? '+' : ''}{data.charge_ph_profile.delta_charge_tumor_vs_plasma.toFixed(3)}
                  </span>
                </div>
              </div>
            </MetricCard>

            <MetricCard label="Protease Cleavage Sites">
              <div className="flex flex-wrap gap-1">
                {(['chymotrypsin', 'trypsin', 'neprilysin', 'pepsin'] as const).map(enzyme => {
                  const entry = data.protease_sites[enzyme]
                  return (
                    <span
                      key={enzyme}
                      className={cn(
                        'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono border',
                        entry.count > 0
                          ? 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30'
                          : 'bg-[var(--bg-elev)]/30 text-[var(--text-mute)] border-[var(--border)]/30',
                      )}
                      title={entry.count > 0 ? `Positions: ${entry.positions.join(', ')}` : 'No sites'}
                    >
                      {enzyme.slice(0, 4)}: {entry.count}
                    </span>
                  )
                })}
              </div>
              <div className="text-[10px] text-[var(--text-mute)] mt-1">
                Total: {data.protease_sites.total_sites} sites
              </div>
            </MetricCard>

            <MetricCard label="Metal Coordination">
              <div className="flex items-center gap-2">
                <span className="font-mono tabular-nums text-[var(--text)]">
                  {data.metal_coordination.total_count} residues
                </span>
                <StatusBadge
                  label={data.metal_coordination.chelator_interference_risk.toUpperCase()}
                  color={
                    data.metal_coordination.chelator_interference_risk === 'low' ? 'green'
                      : data.metal_coordination.chelator_interference_risk === 'moderate' ? 'amber'
                      : 'red'
                  }
                />
              </div>
              <div className="text-[10px] text-[var(--text-mute)] mt-0.5">
                {data.metal_coordination.n_strong} strong binding
              </div>
            </MetricCard>

            {data.radiolysis_susceptibility && (
              <MetricCard label="Radiolysis Susceptibility">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'font-mono tabular-nums font-semibold',
                    data.radiolysis_susceptibility.risk_level === 'low' ? 'text-[var(--pos)]'
                      : data.radiolysis_susceptibility.risk_level === 'moderate' ? 'text-[var(--warn)]'
                      : 'text-[var(--neg)]',
                  )}>
                    {data.radiolysis_susceptibility.total_score.toFixed(2)}
                  </span>
                  <StatusBadge
                    label={data.radiolysis_susceptibility.risk_level.toUpperCase()}
                    color={
                      data.radiolysis_susceptibility.risk_level === 'low' ? 'green'
                        : data.radiolysis_susceptibility.risk_level === 'moderate' ? 'amber'
                        : 'red'
                    }
                  />
                </div>
                {data.radiolysis_susceptibility.vulnerable_residues.length > 0 && (
                  <div className="text-[10px] text-[var(--text-mute)] mt-0.5 font-mono">
                    {data.radiolysis_susceptibility.vulnerable_residues
                      .map(r => `${r.residue}${r.position}`)
                      .join(', ')}
                  </div>
                )}
              </MetricCard>
            )}
          </div>

          {/* Row 4: BLOSUM62 Mutation Analysis (full width) */}
          <div className="bg-[var(--bg-sunk)] border border-[var(--border)] rounded-lg p-3">
            <div className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold mb-2">
              BLOSUM62 Mutation Analysis vs SST-14
            </div>

            {data.blosum62.n_mutations === 0 ? (
              <span className="text-xs text-[var(--text-mute)]">No mutations relative to reference</span>
            ) : (
              <>
                {/* Mutation table */}
                <div className="overflow-x-auto rounded border border-[var(--border)]/50">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-[var(--border)]/50 bg-[var(--bg)]/60">
                        <th className="px-2 py-1.5 text-left text-[var(--text-mute)] font-semibold">Pos</th>
                        <th className="px-2 py-1.5 text-left text-[var(--text-mute)] font-semibold">From</th>
                        <th className="px-2 py-1.5 text-left text-[var(--text-mute)] font-semibold">To</th>
                        <th className="px-2 py-1.5 text-left text-[var(--text-mute)] font-semibold">Score</th>
                        <th className="px-2 py-1.5 text-left text-[var(--text-mute)] font-semibold">Category</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.blosum62.mutations.map((mut, i) => (
                        <tr key={i} className={cn('border-b border-[var(--border)]/30', i % 2 === 0 ? 'bg-[var(--bg)]/20' : '')}>
                          <td className="px-2 py-1 font-mono text-[var(--text-mute)]">{mut.position}</td>
                          <td className="px-2 py-1 font-mono text-[var(--neg)]">{mut.from}</td>
                          <td className="px-2 py-1 font-mono text-[var(--pos)]">{mut.to}</td>
                          <td className={cn(
                            'px-2 py-1 font-mono tabular-nums font-semibold',
                            mut.blosum62_score >= 1 ? 'text-[var(--pos)]'
                              : mut.blosum62_score === 0 ? 'text-[var(--warn)]'
                              : 'text-[var(--neg)]',
                          )}>
                            {mut.blosum62_score}
                          </td>
                          <td className="px-2 py-1">
                            <StatusBadge
                              label={mut.category.replace('-', ' ').toUpperCase()}
                              color={
                                mut.category === 'conservative' ? 'green'
                                  : mut.category === 'semi-conservative' ? 'amber'
                                  : 'red'
                              }
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Summary */}
                <div className="flex items-center gap-3 mt-2 text-[10px]">
                  <span className="text-[var(--text-mute)]">{data.blosum62.n_mutations} mutations</span>
                  <span className="text-[var(--pos)]">{data.blosum62.n_conservative} conservative</span>
                  <span className="text-[var(--warn)]">{data.blosum62.n_semi_conservative} semi-conservative</span>
                  <span className="text-[var(--neg)]">{data.blosum62.n_non_conservative} non-conservative</span>
                  <span className="text-[var(--text-mute)] ml-auto">
                    Avg score: <span className="font-mono font-semibold text-[var(--text-mute)]">{data.blosum62.avg_score.toFixed(2)}</span>
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* No data yet and not loading */}
      {!data && !loading && !error && (
        <div className="text-xs text-[var(--text-mute)] py-4 text-center">
          Select a candidate to view pharmacological properties
        </div>
      )}
    </section>
  )
}
