import { memo, useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp, Loader2, Layers } from 'lucide-react'
import { cn } from '../lib/utils'
import { HelpTooltip } from './ui/HelpTooltip'
import type { Candidate } from '../types'

// ── Types (mirrors cluster_report.py classify_cluster() output) ───────────────

type ClusterLetter = 'A' | 'B' | 'C' | 'D' | 'E'

interface CriteriaGroup {
  [criterion: string]: boolean
}

interface ClusterClassification {
  cluster: ClusterLetter
  cluster_name: string
  priority: number
  criteria_met: Partial<Record<ClusterLetter, CriteriaGroup>>
  note: string
}

interface ClusterResult {
  id: string
  classification: ClusterClassification
}

interface ClusterDistributionEntry {
  count: number
  percent: number
  name: string
}

interface ClusterBatchResponse {
  results: ClusterResult[]
  statistics: {
    total: number
    distribution: Record<ClusterLetter, ClusterDistributionEntry>
  }
  cluster_groups: Record<ClusterLetter, string[]>
}

// ── API endpoint spec (for backend implementation) ────────────────────────────
//
// POST /api/cluster/classify
// Request body:  { "candidates": [{ "name": string, "sequence": string,
//                    "ddG": number, "clash_score": number, ... }] }
// Response body: ClusterBatchResponse (mirrors batch_classify() output)
//
// The request shape mirrors pyrosetta_flow/cluster_report.py::batch_classify().
// Each candidate object should include all fields consumed by classify_cluster():
//   ddG, clash_score, pLDDT?, structural_rules?, instability_index?,
//   blosum62?, protease_sites?, gravy?, net_charge_ph74?, metal_coordination?,
//   selectivity_margin?
//
// ─────────────────────────────────────────────────────────────────────────────

// ── Mock data (used when API is unavailable) ──────────────────────────────────

function buildMockResponse(candidates: Candidate[]): ClusterBatchResponse {
  const letters: ClusterLetter[] = ['A', 'B', 'C', 'D', 'E']
  const names: Record<ClusterLetter, string> = {
    A: 'High Affinity Core',
    B: 'Selectivity-Optimised',
    C: 'Stability-Enhanced',
    D: 'Radiochemistry-Optimal',
    E: 'Exploratory Candidates',
  }
  const notes: Record<ClusterLetter, string> = {
    A: 'All four A-criteria satisfied: strong ddG, low clash, high pLDDT, FWKT contact maintained.',
    B: 'Selectivity margin ≥ 3.0 with confirmed SSTR2 binding; prioritised for isoform selectivity profiling.',
    C: 'Low instability index, conservative mutations, and reduced protease sites indicate enhanced in vivo stability.',
    D: 'GRAVY and charge in optimal range for 68Ga/177Lu labelling; chelator attachment site confirmed.',
    E: 'Does not meet A–D criteria; includes non-conservative substitutions or Tier 3 exploratory candidates.',
  }

  const mockCriteriaA: CriteriaGroup = {
    ddG_lte_minus8: false,
    clash_lte_5: false,
    pLDDT_gte_75: false,
    fwkt_contact: false,
  }

  const results: ClusterResult[] = candidates.map((c, idx) => {
    // Deterministic mock assignment based on ddG range
    let letter: ClusterLetter
    if (c.ddG <= -8) letter = 'A'
    else if (c.ddG <= -6) letter = 'B'
    else if (c.ddG <= -4) letter = 'C'
    else if (idx % 5 === 3) letter = 'D'
    else letter = 'E'

    const criteriaA: CriteriaGroup = {
      ddG_lte_minus8: c.ddG <= -8,
      clash_lte_5: c.clashScore <= 5,
      pLDDT_gte_75: false,
      fwkt_contact: false,
    }
    const criteriaB: CriteriaGroup = {
      selectivity_margin_gte_3: letter === 'B',
      ddG_binding_present: c.ddG < -5,
    }
    const criteriaC: CriteriaGroup = {
      instability_lt_30: letter === 'C',
      blosum62_nonnegative: true,
      protease_sites_reduced: true,
    }
    const criteriaD: CriteriaGroup = {
      gravy_in_range: letter === 'D',
      net_charge_low: true,
      chelator_site_available: true,
    }

    const criteria_met: Partial<Record<ClusterLetter, CriteriaGroup>> = {
      A: criteriaA,
      B: criteriaB,
      C: criteriaC,
      D: criteriaD,
    }

    // For cluster E: show all evaluated criteria (all failed)
    if (letter === 'E') {
      criteria_met.A = { ...mockCriteriaA }
    }

    return {
      id: c.id,
      classification: {
        cluster: letter,
        cluster_name: names[letter],
        priority: letters.indexOf(letter) + 1,
        criteria_met,
        note: notes[letter],
      },
    }
  })

  const cluster_groups: Record<ClusterLetter, string[]> = { A: [], B: [], C: [], D: [], E: [] }
  const counts: Record<ClusterLetter, number> = { A: 0, B: 0, C: 0, D: 0, E: 0 }

  for (const r of results) {
    const l = r.classification.cluster
    cluster_groups[l].push(r.id)
    counts[l]++
  }

  const total = results.length
  const distribution = {} as Record<ClusterLetter, ClusterDistributionEntry>
  for (const l of letters) {
    distribution[l] = {
      count: counts[l],
      percent: total > 0 ? Math.round((1000 * counts[l]) / total) / 10 : 0,
      name: names[l],
    }
  }

  return { results, statistics: { total, distribution }, cluster_groups }
}

// ── Cluster badge ─────────────────────────────────────────────────────────────

const CLUSTER_COLORS: Record<ClusterLetter, string> = {
  A: 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30',
  B: 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30',
  C: 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30',
  D: 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30',
  E: 'bg-[var(--bg-sunk)] text-[var(--text-dim)] border-[var(--border)]',
}

const ClusterBadge = memo(function ClusterBadge({
  letter,
  size = 'sm',
}: {
  letter: ClusterLetter
  size?: 'sm' | 'lg'
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-full font-bold border tabular-nums',
        CLUSTER_COLORS[letter],
        size === 'lg' ? 'w-8 h-8 text-sm' : 'px-2 py-0.5 text-[10px]',
      )}
      aria-label={`Cluster ${letter}`}
    >
      {letter}
    </span>
  )
})

// ── Criteria detail accordion ─────────────────────────────────────────────────

const CriteriaDetail = memo(function CriteriaDetail({
  criteriaGroups,
}: {
  criteriaGroups: Partial<Record<ClusterLetter, CriteriaGroup>>
}) {
  const [open, setOpen] = useState(false)
  const letters: ClusterLetter[] = ['A', 'B', 'C', 'D']

  const totalCriteria = Object.values(criteriaGroups).reduce(
    (sum, g) => sum + (g ? Object.keys(g).length : 0),
    0,
  )
  const metCount = Object.values(criteriaGroups).reduce(
    (sum, g) => sum + (g ? Object.values(g).filter(Boolean).length : 0),
    0,
  )

  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-[10px] text-[var(--text-dim)] hover:text-[var(--text-mute)] transition-colors"
        aria-expanded={open}
      >
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        <span>
          criteria {metCount}/{totalCriteria} met
        </span>
      </button>

      {open && (
        <div className="mt-1.5 space-y-1.5 pl-2 border-l border-[var(--border)]">
          {letters.map(l => {
            const group = criteriaGroups[l]
            if (!group) return null
            return (
              <div key={l} className="space-y-0.5">
                <div className={cn('text-[10px] font-semibold', CLUSTER_COLORS[l].split(' ')[1])}>
                  Cluster {l}
                </div>
                {Object.entries(group).map(([criterion, passed]) => (
                  <div key={criterion} className="flex items-center gap-1.5 text-[10px]">
                    <span
                      className={cn(
                        'w-1.5 h-1.5 rounded-full flex-shrink-0',
                        passed ? 'bg-green-500' : 'bg-[var(--neg-soft)]',
                      )}
                      aria-hidden="true"
                    />
                    <span className={passed ? 'text-[var(--text-mute)]' : 'text-[var(--text-dim)]'}>
                      {criterion.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
})

// ── Cluster stats bar ─────────────────────────────────────────────────────────

const ClusterStats = memo(function ClusterStats({
  distribution,
  total,
  activeFilter,
  onFilter,
}: {
  distribution: Record<ClusterLetter, ClusterDistributionEntry>
  total: number
  activeFilter: ClusterLetter | null
  onFilter: (l: ClusterLetter | null) => void
}) {
  const letters: ClusterLetter[] = ['A', 'B', 'C', 'D', 'E']
  return (
    <div className="flex flex-wrap gap-2">
      {letters.map(l => {
        const d = distribution[l]
        const isActive = activeFilter === l
        return (
          <button
            key={l}
            onClick={() => onFilter(isActive ? null : l)}
            className={cn(
              'flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs transition-all',
              isActive
                ? CLUSTER_COLORS[l] + ' ring-1 ring-offset-1 ring-offset-[var(--bg)]'
                : 'bg-[var(--bg-elev)] border-[var(--border)] text-[var(--text-dim)] hover:border-[var(--border)]',
            )}
            aria-pressed={isActive}
          >
            <ClusterBadge letter={l} />
            <div className="text-left">
              <div className="font-semibold tabular-nums">{d.count}</div>
              <div className="text-[10px] text-[var(--text-dim)]">{d.percent}%</div>
            </div>
          </button>
        )
      })}
      <div className="flex items-center ml-auto text-xs text-[var(--text-dim)]">
        <span className="font-mono tabular-nums font-semibold text-[var(--text-mute)]">{total}</span>
        <span className="ml-1">total</span>
      </div>
    </div>
  )
})

// ── Main component ────────────────────────────────────────────────────────────

interface ClusterPanelProps {
  candidates: Candidate[]
}

export function ClusterPanel({ candidates }: ClusterPanelProps) {
  const [data, setData] = useState<ClusterBatchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeFilter, setActiveFilter] = useState<ClusterLetter | null>(null)
  const fetchedRef = useRef('')

  const seqKey = candidates.map(c => c.id).join(',')

  /* eslint-disable react-hooks/set-state-in-effect -- fetch lifecycle pattern */
  useEffect(() => {
    if (candidates.length === 0 || seqKey === fetchedRef.current) return
    fetchedRef.current = seqKey

    const controller = new AbortController()
    setLoading(true)
    setError(null)

    // P05: 확장 payload — selectivity_margin 등 6개 optional 필드 포함.
    // BE candidate dict에 해당 필드가 없으면 undefined → JSON 직렬화 시 생략됨.
    const payload = {
      candidates: candidates.map(c => ({
        name: c.id,
        sequence: c.sequence,
        ddG: c.ddG,
        clash_score: c.clashScore,
        total_score: c.totalScore,
        selectivity_margin: c.selectivity_margin,
        instability_index: c.instability_index,
        gravy: c.gravy,
        net_charge_ph74: c.net_charge_ph74,
        fwkt_contact: c.fwkt_contact,
        chelator_site_available: c.chelator_site_available,
      })),
    }

    fetch('/api/cluster/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
      .then(r => {
        if (r.status === 404 || r.status === 501) {
          // Endpoint not yet implemented — fall back to mock
          return null
        }
        return r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))
      })
      .then((json: ClusterBatchResponse | null) => {
        setData(json ?? buildMockResponse(candidates))
        setLoading(false)
      })
      .catch(err => {
        if (err.name === 'AbortError') return
        // Network error — use mock so the UI stays functional
        setData(buildMockResponse(candidates))
        setLoading(false)
      })

    return () => controller.abort()
  }, [seqKey, candidates])
  /* eslint-enable react-hooks/set-state-in-effect */

  if (candidates.length === 0) return null

  const letters: ClusterLetter[] = ['A', 'B', 'C', 'D', 'E']

  const filteredResults = data
    ? (activeFilter
      ? data.results.filter(r => r.classification.cluster === activeFilter)
      : data.results)
    : []

  // Representative = first candidate (lowest rank) in each cluster group
  const representativeIds = new Set(
    data
      ? letters
        .map(l => data.cluster_groups[l][0])
        .filter(Boolean)
      : [],
  )

  return (
    <section className="card flex flex-col gap-3" aria-label="Cluster Panel">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-[var(--accent)]" aria-hidden="true" />
            Cluster Classification
            <HelpTooltip title="Cluster Classification">
              <p>cluster_report.py의 classify_cluster() 결과를 시각화합니다.</p>
              <p><strong>A</strong>: ddG ≤ −8, clash ≤ 5, pLDDT ≥ 75, FWKT 유지 (우선순위 최상)</p>
              <p><strong>B</strong>: selectivity_margin ≥ 3.0, SSTR2 결합 확인</p>
              <p><strong>C</strong>: instability_index &lt; 30, blosum62 ≥ 0, protease site 감소</p>
              <p><strong>D</strong>: GRAVY ∈ [−1.0, +0.5], |charge| ≤ 1.0, 킬레이터 사이트 보유</p>
              <p><strong>E</strong>: A–D 기준 미충족 탐색 후보</p>
              <p className="text-[10px] text-[var(--text-dim)] mt-1">API: POST /api/cluster/classify</p>
            </HelpTooltip>
          </h2>
          <p className="text-xs text-[var(--text-dim)] mt-0.5">
            A–E priority assignment · pyrosetta_flow/cluster_report.py
          </p>
        </div>
        {data && (
          <span className="text-[10px] text-[var(--text-dim)] font-mono">
            {data.statistics.total} candidates
          </span>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-6 gap-2">
          <Loader2 className="w-4 h-4 text-[var(--accent)] animate-spin" aria-hidden="true" />
          <span className="text-xs text-[var(--text-dim)]">Classifying clusters…</span>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="border border-[var(--neg)]/30 bg-[var(--neg-soft)] rounded-lg px-4 py-3 text-xs text-[var(--neg)]">
          {error}
        </div>
      )}

      {data && !loading && (
        <>
          {/* Cluster statistics bar */}
          <ClusterStats
            distribution={data.statistics.distribution}
            total={data.statistics.total}
            activeFilter={activeFilter}
            onFilter={setActiveFilter}
          />

          {/* Cluster name legend */}
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {letters.map(l => (
              <span key={l} className="flex items-center gap-1.5 text-[10px] text-[var(--text-dim)]">
                <ClusterBadge letter={l} />
                <span>{data.statistics.distribution[l].name}</span>
              </span>
            ))}
          </div>

          {/* Horizontal bar chart */}
          <div className="space-y-1.5">
            {letters.map(l => {
              const pct = data.statistics.distribution[l].percent
              if (pct === 0) return null
              return (
                <div key={l} className="flex items-center gap-2">
                  <ClusterBadge letter={l} />
                  <div className="flex-1 h-2 bg-[var(--bg-elev)] rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all',
                        l === 'A' ? 'bg-[var(--accent-soft)]'
                          : l === 'B' ? 'bg-[var(--pos-soft)]'
                          : l === 'C' ? 'bg-[var(--warn-soft)]'
                          : l === 'D' ? 'bg-[var(--warn-soft)]'
                          : 'bg-[var(--bg-sunk)]',
                      )}
                      style={{ width: `${pct}%` }}
                      aria-label={`${pct}%`}
                    />
                  </div>
                  <span className="text-[10px] text-[var(--text-dim)] tabular-nums w-10 text-right">
                    {pct}%
                  </span>
                </div>
              )
            })}
          </div>

          {/* Per-candidate list */}
          <div className="bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg overflow-hidden">
            <div className="px-3 py-1.5 border-b border-[var(--border)] bg-[var(--bg-elev)] flex items-center gap-2">
              <span className="text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider">
                Candidates
              </span>
              {activeFilter && (
                <span className={cn('text-[10px] font-bold', CLUSTER_COLORS[activeFilter].split(' ')[1])}>
                  Cluster {activeFilter} · {filteredResults.length}
                </span>
              )}
            </div>

            <div className="divide-y divide-[var(--border)] max-h-80 overflow-y-auto">
              {filteredResults.slice(0, 200).map(r => {
                const { cluster, cluster_name, criteria_met, note } = r.classification
                const isRep = representativeIds.has(r.id)
                return (
                  <div
                    key={r.id}
                    className={cn(
                      'px-3 py-2 flex flex-col gap-1 transition-colors hover:bg-[var(--bg-elev)]',
                      isRep && 'border-l-2',
                      isRep && cluster === 'A' && 'border-l-blue-500/60',
                      isRep && cluster === 'B' && 'border-l-green-500/60',
                      isRep && cluster === 'C' && 'border-l-amber-500/60',
                      isRep && cluster === 'D' && 'border-l-orange-500/60',
                      isRep && cluster === 'E' && 'border-l-[var(--border-strong)]',
                    )}
                  >
                    {/* Row top */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-[var(--text-mute)] font-semibold w-32 truncate">
                        {r.id}
                      </span>
                      <ClusterBadge letter={cluster} />
                      <span className="text-[10px] text-[var(--text-dim)]">{cluster_name}</span>
                      {isRep && (
                        <span className="text-[10px] text-[var(--accent)] border border-[var(--accent)]/30 rounded px-1">
                          representative
                        </span>
                      )}
                    </div>

                    {/* Note */}
                    <p className="text-[10px] text-[var(--text-dim)] leading-relaxed">{note}</p>

                    {/* Criteria accordion */}
                    <CriteriaDetail criteriaGroups={criteria_met} />
                  </div>
                )
              })}

              {filteredResults.length === 0 && (
                <div className="px-4 py-6 text-center text-xs text-[var(--text-dim)]">
                  No candidates in Cluster {activeFilter}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  )
}
