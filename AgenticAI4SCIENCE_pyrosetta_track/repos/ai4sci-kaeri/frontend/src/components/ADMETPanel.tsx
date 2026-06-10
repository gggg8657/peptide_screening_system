import { memo, useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { ChevronDown, Loader2, FlaskConical, CheckCircle2, XCircle } from 'lucide-react'
import { cn } from '../lib/utils'
import { useClickOutside } from '../hooks/useClickOutside'
import { HelpTooltip } from './ui/HelpTooltip'
import type { Candidate, AdmetFullResult, PepadmetToxicityPayload } from '../types'

// ── Local sub-components ──────────────────────────────────────────────────────

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
    <div className={cn('bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-3', className)}>
      <div className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold mb-1.5">
        {label}
      </div>
      <div className="text-sm">{children}</div>
    </div>
  )
})

type BadgeColor = 'green' | 'red' | 'amber' | 'cyan' | 'slate'

const StatusBadge = memo(function StatusBadge({
  label,
  color,
}: {
  label: string
  color: BadgeColor
}) {
  const colors: Record<BadgeColor, string> = {
    green: 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30',
    red: 'bg-[var(--neg-soft)] text-[var(--neg)] border-[var(--neg)]/30',
    amber: 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30',
    cyan: 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30',
    slate: 'bg-[var(--bg-sunk)] text-[var(--text-dim)] border-[var(--border)]',
  }
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border', colors[color])}>
      {label}
    </span>
  )
})

// ── Druglikeness score gauge ──────────────────────────────────────────────────

const DruglikenessGauge = memo(function DruglikenessGauge({
  score,
  breakdown,
}: {
  score: number
  breakdown: AdmetFullResult['admet']['druglikeness_breakdown']
}) {
  const color =
    score >= 75 ? 'text-[var(--pos)]' :
    score >= 50 ? 'text-[var(--warn)]' :
    'text-[var(--neg)]'
  const barColor =
    score >= 75 ? 'bg-green-500' :
    score >= 50 ? 'bg-amber-500' :
    'bg-red-500'

  return (
    <div className="space-y-2">
      {/* Score row */}
      <div className="flex items-center gap-3">
        <span className={cn('text-2xl font-bold tabular-nums font-mono', color)}>
          {score}
        </span>
        <span className="text-xs text-[var(--text-dim)]">/ 100</span>
        <StatusBadge
          label={score >= 75 ? 'DRUG-LIKE' : score >= 50 ? 'MARGINAL' : 'NON-DRUG-LIKE'}
          color={score >= 75 ? 'green' : score >= 50 ? 'amber' : 'red'}
        />
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-[var(--bg-elev)] rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', barColor)}
          style={{ width: `${score}%` }}
          aria-label={`${score}% druglikeness`}
        />
      </div>

      {/* Breakdown rules */}
      <div className="grid grid-cols-2 gap-1">
        {Object.entries(breakdown).map(([key, rule]) => (
          <div key={key} className="flex items-center gap-1.5 text-[10px]">
            {rule.passed
              ? <CheckCircle2 className="w-3 h-3 text-[var(--pos)] flex-shrink-0" aria-hidden="true" />
              : <XCircle className="w-3 h-3 text-[var(--neg)] flex-shrink-0" aria-hidden="true" />
            }
            <span className={rule.passed ? 'text-[var(--text-mute)]' : 'text-[var(--text-dim)]'}>
              {key.replace(/_/g, ' ')}
            </span>
            <span className="text-[var(--text-dim)] ml-auto tabular-nums">
              +{rule.points}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
})

// ── pepADMET (JCIM 2026) ML toxicity ─────────────────────────────────────────

const PepadmetCard = memo(function PepadmetCard({ p }: { p: PepadmetToxicityPayload }) {
  if (!p.available) {
    return (
      <div className="bg-[var(--bg-elev)] border border-[var(--warn)]/30 rounded-lg p-3 space-y-1">
        <div className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold">
          pepADMET toxicity (ML)
        </div>
        <p className="text-[10px] text-amber-200/90 leading-relaxed">
          {p.error ?? 'Unavailable — needs local pepADMET repo + conda env `pepadmet` (see ENVIRONMENT.md).'}
        </p>
      </div>
    )
  }
  return (
    <div className="bg-[var(--bg-elev)] border border-[var(--accent)]/30 rounded-lg p-3 space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold">
          pepADMET toxicity (MLR-GAT)
        </div>
        {p.graph_note === 'linear_sequence_fallback' && (
          <span className="text-[9px] text-[var(--warn)]/90 border border-[var(--warn)]/30 rounded px-1.5 py-0">
            linear graph fallback (SMILES round-trip failed)
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <div>
          <span className="text-[var(--text-dim)] block text-[10px]">Binary P(toxic)</span>
          <span className="font-mono font-semibold text-[var(--accent)]">
            {p.binary_toxicity != null ? p.binary_toxicity.toFixed(4) : '—'}
          </span>
        </div>
        <div>
          <span className="text-[var(--text-dim)] block text-[10px]">Predicted toxic</span>
          <StatusBadge label={p.is_toxic ? 'YES' : 'NO'} color={p.is_toxic ? 'red' : 'green'} />
        </div>
        <div>
          <span className="text-[var(--text-dim)] block text-[10px]">Toxicity class</span>
          <span className="text-[var(--text-mute)] text-[10px]">{p.toxicity_type ?? '—'}</span>
        </div>
        <div>
          <span className="text-[var(--text-dim)] block text-[10px]">HC50</span>
          <span className="font-mono text-[var(--text-mute)]">{p.hc50 != null ? p.hc50.toFixed(4) : '—'}</span>
        </div>
      </div>
      {(p.neurotoxicity_type || p.neurotoxicity_confidence != null) && (
        <div className="text-[10px] text-[var(--text-dim)] border-t border-[var(--border)] pt-2">
          Neurotoxicity: <span className="text-[var(--text-mute)]">{p.neurotoxicity_type}</span>
          {p.neurotoxicity_confidence != null && (
            <span className="text-[var(--text-dim)] ml-2">conf {p.neurotoxicity_confidence.toFixed(3)}</span>
          )}
        </div>
      )}
    </div>
  )
})

// ── Nephrotoxicity risk panel ─────────────────────────────────────────────────

const NephrotoxCard = memo(function NephrotoxCard({
  nephrotox,
}: {
  nephrotox: AdmetFullResult['nephrotox']
}) {
  const riskColor: BadgeColor =
    nephrotox.risk_level === 'Low' ? 'green' :
    nephrotox.risk_level === 'Moderate' ? 'amber' :
    'red'

  return (
    <div className="bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-3 space-y-2">
      <div className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold">
        Renal Retention Risk (PRRT)
      </div>

      {/* Score + badge */}
      <div className="flex items-center gap-3">
        <span className={cn(
          'text-2xl font-bold tabular-nums font-mono',
          nephrotox.risk_level === 'Low' ? 'text-[var(--pos)]' :
          nephrotox.risk_level === 'Moderate' ? 'text-[var(--warn)]' :
          'text-[var(--neg)]',
        )}>
          {nephrotox.renal_risk_score}
        </span>
        <span className="text-xs text-[var(--text-dim)]">/ 100</span>
        <StatusBadge label={nephrotox.risk_level.toUpperCase()} color={riskColor} />
      </div>

      {/* Risk bar */}
      <div className="h-1.5 bg-[var(--bg-elev)] rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all',
            nephrotox.risk_level === 'Low' ? 'bg-green-500' :
            nephrotox.risk_level === 'Moderate' ? 'bg-amber-500' :
            'bg-red-500',
          )}
          style={{ width: `${nephrotox.renal_risk_score}%` }}
        />
      </div>

      {/* Cationic residue breakdown */}
      <div className="flex items-center gap-4 text-xs">
        <span className="text-[var(--text-dim)]">Cationic residues:</span>
        <span className="font-mono text-[var(--text-mute)]">
          {nephrotox.n_lys}K + {nephrotox.n_arg}R + {nephrotox.n_his}H
          <span className="text-[var(--text-dim)] ml-1">= {nephrotox.cationic_residues} total</span>
        </span>
      </div>

      {/* Warning text */}
      {nephrotox.warning && (
        <div className={cn(
          'rounded-md px-3 py-2 text-[10px] leading-relaxed border',
          nephrotox.risk_level === 'Moderate'
            ? 'bg-[var(--warn-soft)] border-[var(--warn)]/30 text-amber-200'
            : 'bg-[var(--neg-soft)] border-[var(--neg)]/30 text-red-200',
        )}>
          {nephrotox.warning}
        </div>
      )}
    </div>
  )
})

// ── Main component ────────────────────────────────────────────────────────────

interface ADMETProps {
  candidates: Candidate[]
}

/** API·상태 JSON은 대문자 서열을 쓰는데 후보는 소문자일 수 있어 맵 조회가 실패하지 않게 통일 */
function normSeq(s: string): string {
  return s.toUpperCase().trim()
}

export function ADMETPanel({ candidates }: ADMETProps) {
  const [admetData, setAdmetData] = useState<Map<string, AdmetFullResult>>(new Map())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedSeq, setSelectedSeq] = useState<string>('')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const closeDropdown = useCallback(() => setDropdownOpen(false), [])
  useClickOutside(dropdownRef, closeDropdown, dropdownOpen)
  const fetchedRef = useRef('')

  const uniqueSequences = useMemo(
    () => [...new Set(candidates.map(c => c.sequence).filter(Boolean).map(normSeq))].sort(),
    [candidates],
  )
  const seqKey = uniqueSequences.join(',')

  const seqToBestCandidate = useMemo(() => {
    const map = new Map<string, Candidate>()
    for (const c of candidates) {
      if (!c.sequence) continue
      const key = normSeq(c.sequence)
      const existing = map.get(key)
      if (!existing || c.rank < existing.rank) map.set(key, c)
    }
    return map
  }, [candidates])

  /* eslint-disable react-hooks/set-state-in-effect -- fetch lifecycle */
  useEffect(() => {
    if (!selectedSeq && candidates.length > 0) {
      const best = [...candidates].sort((a, b) => a.rank - b.rank)[0]
      if (best?.sequence) setSelectedSeq(normSeq(best.sequence))
    }
  }, [candidates, selectedSeq])

  useEffect(() => {
    // 의존성은 seqKey만: candidates 폴링 시 배열 참조가 매번 바뀌면 effect가 재실행·abort되어
    // AbortError에서 로딩이 안 꺼지는 문제가 있었다. 서열 목록은 seqKey에서 복원 (AA 서열에 콤마 없음).
    if (!seqKey || seqKey === fetchedRef.current) return
    const sequences = seqKey.split(',')
    if (sequences.length === 0) return
    fetchedRef.current = seqKey

    const controller = new AbortController()
    setLoading(true)
    setError(null)

    fetch('/api/admet/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequences }),
      signal: controller.signal,
    })
      .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then((data: { results: AdmetFullResult[] }) => {
        if (!data?.results) return
        const map = new Map<string, AdmetFullResult>()
        for (const r of data.results) {
          if (r.sequence) map.set(normSeq(r.sequence), r)
        }
        setAdmetData(map)
      })
      .catch(err => {
        if (err.name !== 'AbortError') {
          setError(err.message ?? 'Failed to fetch ADMET data')
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
  const data = selectedKey ? admetData.get(selectedKey) : undefined
  const bestCandidate = selectedKey ? seqToBestCandidate.get(selectedKey) : undefined

  return (
    <section className="card flex flex-col gap-3" aria-label="ADMET Panel">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
            <FlaskConical className="w-4 h-4 text-[var(--accent)]" aria-hidden="true" />
            ADMET &amp; Nephrotoxicity
            <HelpTooltip title="ADMET & Nephrotoxicity">
              <p>서열 기반 휴리스틱 ADMET + PRRT 신장 위험 + (선택) pepADMET 독성 ML.</p>
              <p><strong>Druglikeness (0-100)</strong>: MW, 전하, 소수성, 반복 잔기 4항목 각 25점.</p>
              <p><strong>신장 보유 위험</strong>: K/R/H 양이온 잔기 + net charge 기반 점수 (0-100).</p>
              <p><strong>pepADMET</strong>: 로컬 repo·conda 구성 시 MLR-GAT 독성 예측이 합쳐집니다.</p>
              <p>Low &lt; 30 / Moderate 30-60 / High &gt; 60</p>
            </HelpTooltip>
          </h2>
          <p className="text-xs text-[var(--text-dim)] mt-0.5">
            Sequence heuristics · PRRT renal risk · optional pepADMET ML toxicity
          </p>
        </div>

        {/* Candidate selector dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(o => !o)}
            aria-expanded={dropdownOpen}
            aria-haspopup="listbox"
            className="flex items-center gap-2 bg-[var(--bg-elev)] border border-[var(--border)] hover:border-[var(--border)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-mute)] transition-colors"
          >
            <span className="font-mono">
              {bestCandidate ? bestCandidate.id : (selectedSeq ? selectedSeq.slice(0, 10) + '…' : '—')}
            </span>
            {bestCandidate && (
              <span className="text-[10px] text-[var(--text-dim)]">Rank {bestCandidate.rank}</span>
            )}
            <ChevronDown className="w-3 h-3 text-[var(--text-dim)]" />
          </button>
          {dropdownOpen && (
            <div
              role="listbox"
              className="absolute right-0 top-full mt-1 z-50 w-72 bg-[var(--bg)] border border-[var(--border)] rounded-lg shadow-xl overflow-hidden max-h-64 overflow-y-auto"
            >
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
                      isCurrent ? 'bg-[var(--accent-soft)] text-[var(--accent)]' : 'text-[var(--text-dim)] hover:bg-[var(--bg-elev)]',
                    )}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-medium">{cand?.id ?? seq.slice(0, 14)}</span>
                      {isCurrent && <span className="text-[var(--accent)] text-[10px]">(viewing)</span>}
                    </div>
                    <div className="flex gap-3 mt-0.5 text-[10px] text-[var(--text-dim)]">
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

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-8 gap-2">
          <Loader2 className="w-4 h-4 text-[var(--accent)] animate-spin" aria-hidden="true" />
          <span className="text-xs text-[var(--text-dim)]">Loading ADMET data…</span>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="border border-[var(--neg)]/30 bg-[var(--neg-soft)] rounded-lg px-4 py-3 text-xs text-[var(--neg)]">
          {error}
        </div>
      )}

      {/* Data display */}
      {data && !loading && (
        <div className="space-y-3">
          {/* Row 1: Druglikeness + key ADMET */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <MetricCard label="Druglikeness Score">
              <DruglikenessGauge
                score={data.admet.druglikeness_score}
                breakdown={data.admet.druglikeness_breakdown}
              />
            </MetricCard>

            <div className="grid grid-cols-2 gap-2">
              <MetricCard label="Molecular Weight">
                <span className="font-mono tabular-nums font-semibold text-[var(--text-mute)]">
                  {data.admet.mw.toFixed(2)}
                  <span className="text-[10px] text-[var(--text-dim)] ml-1 font-normal">Da</span>
                </span>
                <div className="text-[10px] text-[var(--text-dim)] mt-0.5">
                  monoisotopic
                </div>
              </MetricCard>

              <MetricCard label="Net Charge (pH 7.4)">
                <span className={cn(
                  'font-mono tabular-nums font-semibold',
                  Math.abs(data.admet.net_charge_ph74) <= 3 ? 'text-[var(--pos)]' : 'text-[var(--warn)]',
                )}>
                  {data.admet.net_charge_ph74 >= 0 ? '+' : ''}
                  {data.admet.net_charge_ph74}
                </span>
                <div className="text-[10px] text-[var(--text-dim)] mt-0.5">
                  {Math.abs(data.admet.net_charge_ph74) <= 3 ? 'within range' : 'outside range'}
                </div>
              </MetricCard>

              <MetricCard label="H-bond Donors / Acceptors">
                <div className="flex items-center gap-1.5">
                  <span className="font-mono tabular-nums font-semibold text-[var(--text-mute)]">
                    {data.admet.n_hbd}
                  </span>
                  <span className="text-[10px] text-[var(--text-dim)]">HBD</span>
                  <span className="text-[var(--text-dim)]">/</span>
                  <span className="font-mono tabular-nums font-semibold text-[var(--text-mute)]">
                    {data.admet.n_hba}
                  </span>
                  <span className="text-[10px] text-[var(--text-dim)]">HBA</span>
                </div>
              </MetricCard>

              <MetricCard label="Hydrophobicity">
                <span className={cn(
                  'font-mono tabular-nums font-semibold',
                  data.admet.hydrophobicity >= -2 && data.admet.hydrophobicity <= 1
                    ? 'text-[var(--pos)]' : 'text-[var(--warn)]',
                )}>
                  {data.admet.hydrophobicity.toFixed(4)}
                </span>
                <div className="text-[10px] text-[var(--text-dim)] mt-0.5">KD scale</div>
              </MetricCard>
            </div>
          </div>

          {/* Row 2: Amphipathicity */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <MetricCard label="Amphipathicity Index">
              <span className="font-mono tabular-nums font-semibold text-[var(--text-mute)]">
                {data.admet.amphipathicity_index.toFixed(4)}
              </span>
              <div className="text-[10px] text-[var(--text-dim)] mt-0.5">
                KD hydropathy variance
              </div>
            </MetricCard>
          </div>

          {/* Row 3: pepADMET ML (backend merges when env/repo available) */}
          {data.pepadmet && <PepadmetCard p={data.pepadmet} />}

          {/* Row 4: Nephrotox */}
          <NephrotoxCard nephrotox={data.nephrotox} />
        </div>
      )}

      {/* No data */}
      {!data && !loading && !error && (
        <div className="text-xs text-[var(--text-dim)] py-4 text-center">
          Select a candidate to view ADMET properties
        </div>
      )}
    </section>
  )
}
