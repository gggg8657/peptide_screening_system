import { useState, useMemo, memo } from 'react'
import { cn } from '../lib/utils'
import { Database, ExternalLink, Search, Loader2, ChevronDown, ChevronUp, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import type { Candidate } from '../types'

// --- RCSB Search API types ---

interface RCSBHit {
  pdb_id: string
  identifier: string
  identity: number | null
  evalue: number | null
  bitscore: number | null
}

interface CandidateRCSBResult {
  candidate_id: string
  sequence: string
  hits: RCSBHit[]
  searched: boolean
  error?: string
}

interface RCSBMatchSummary {
  checked: number
  matched: number
  identity_cutoff: number
}

// --- Props ---

interface RCSBMatchPanelProps {
  candidates: Candidate[]
}

// --- Helper: identity badge ---

function IdentityBadge({ identity }: { identity: number | null }) {
  if (identity === null) return <span className="text-xs text-[var(--text-dim)]">N/A</span>
  const pct = identity * 100
  const color = pct >= 90 ? 'text-[var(--pos)]' : pct >= 60 ? 'text-[var(--warn)]' : 'text-[var(--neg)]'
  return <span className={cn('text-xs font-mono font-bold tabular-nums', color)}>{pct.toFixed(1)}%</span>
}

// --- Helper: status icon ---

function MatchStatusIcon({ hits, searched, error }: { hits: RCSBHit[]; searched: boolean; error?: string }) {
  if (error) return <AlertTriangle className="w-4 h-4 text-[var(--warn)]" />
  if (!searched) return <Search className="w-4 h-4 text-[var(--text-dim)]" />
  if (hits.length > 0) return <CheckCircle2 className="w-4 h-4 text-[var(--pos)]" />
  return <XCircle className="w-4 h-4 text-[var(--text-dim)]" />
}

// --- Hit row ---

const HitRow = memo(function HitRow({ hit }: { hit: RCSBHit }) {
  return (
    <tr className="border-b border-[var(--border)] last:border-b-0 hover:bg-[var(--bg-elev)] transition-colors">
      <td className="px-3 py-1.5">
        <a
          href={`https://www.rcsb.org/structure/${hit.pdb_id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-mono text-[var(--accent)] hover:text-[var(--accent)] hover:underline inline-flex items-center gap-1"
        >
          {hit.pdb_id}
          <ExternalLink className="w-3 h-3" />
        </a>
      </td>
      <td className="px-3 py-1.5 text-xs text-[var(--text-mute)] font-mono">{hit.identifier}</td>
      <td className="px-3 py-1.5 text-right"><IdentityBadge identity={hit.identity} /></td>
      <td className="px-3 py-1.5 text-right text-xs font-mono text-[var(--text-mute)] tabular-nums">
        {hit.evalue !== null ? hit.evalue.toExponential(1) : '--'}
      </td>
      <td className="px-3 py-1.5 text-right text-xs font-mono text-[var(--text-mute)] tabular-nums">
        {hit.bitscore !== null ? hit.bitscore : '--'}
      </td>
    </tr>
  )
})

// --- Candidate result card ---

const CandidateMatchCard = memo(function CandidateMatchCard({ result }: { result: CandidateRCSBResult }) {
  const [expanded, setExpanded] = useState(result.hits.length > 0)
  const bestIdentity = result.hits.length > 0
    ? Math.max(...result.hits.map(h => h.identity ?? 0))
    : null

  return (
    <div className="border border-[var(--border)] rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-[var(--bg-elev)] transition-colors text-left"
      >
        <MatchStatusIcon hits={result.hits} searched={result.searched} error={result.error} />
        <span className="text-xs font-mono text-[var(--text-mute)] flex-1 truncate">{result.candidate_id}</span>
        <span className="text-[10px] text-[var(--text-dim)] truncate max-w-[120px]">{result.sequence}</span>
        {bestIdentity !== null && (
          <span className="text-[10px] text-[var(--text-dim)]">
            best: <IdentityBadge identity={bestIdentity} />
          </span>
        )}
        <span className={cn(
          'text-[10px] font-mono px-1.5 py-0.5 rounded',
          result.hits.length > 0 ? 'bg-[var(--pos-soft)] text-[var(--pos)]' : 'bg-[var(--bg-sunk)] text-[var(--text-dim)]',
        )}>
          {result.hits.length} hit{result.hits.length !== 1 ? 's' : ''}
        </span>
        {expanded ? <ChevronUp className="w-3.5 h-3.5 text-[var(--text-dim)]" /> : <ChevronDown className="w-3.5 h-3.5 text-[var(--text-dim)]" />}
      </button>

      {expanded && result.hits.length > 0 && (
        <div className="border-t border-[var(--border)]">
          <table className="w-full">
            <thead>
              <tr className="bg-[var(--bg-elev)]">
                <th className="px-3 py-1.5 text-left text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-semibold">PDB</th>
                <th className="px-3 py-1.5 text-left text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-semibold">Entity</th>
                <th className="px-3 py-1.5 text-right text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-semibold">Identity</th>
                <th className="px-3 py-1.5 text-right text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-semibold">E-value</th>
                <th className="px-3 py-1.5 text-right text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-semibold">Bitscore</th>
              </tr>
            </thead>
            <tbody>
              {result.hits.map((hit) => (
                <HitRow key={hit.identifier} hit={hit} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {expanded && result.error && (
        <div className="border-t border-[var(--border)] px-3 py-2">
          <p className="text-[10px] text-[var(--warn)]">{result.error}</p>
        </div>
      )}

      {expanded && result.searched && result.hits.length === 0 && !result.error && (
        <div className="border-t border-[var(--border)] px-3 py-2">
          <p className="text-[10px] text-[var(--text-dim)]">No similar structures found in RCSB PDB (novel candidate)</p>
        </div>
      )}
    </div>
  )
})

// --- Summary bar ---

function SummaryBar({ summary }: { summary: RCSBMatchSummary }) {
  const matchRate = summary.checked > 0 ? Math.round((summary.matched / summary.checked) * 100) : 0
  return (
    <div className="flex items-center gap-4 text-xs">
      <span className="text-[var(--text-dim)]">
        Checked: <span className="text-[var(--text-mute)] font-mono">{summary.checked}</span>
      </span>
      <span className="text-[var(--text-dim)]">
        Matched: <span className={cn('font-mono', summary.matched > 0 ? 'text-[var(--pos)]' : 'text-[var(--text-mute)]')}>{summary.matched}</span>
      </span>
      <span className="text-[var(--text-dim)]">
        Novel: <span className="text-[var(--accent)] font-mono">{summary.checked - summary.matched}</span>
      </span>
      <span className="text-[var(--text-dim)]">
        Identity cutoff: <span className="text-[var(--text-mute)] font-mono">{(summary.identity_cutoff * 100).toFixed(0)}%</span>
      </span>
      <div className="flex-1" />
      <div className="flex items-center gap-1.5">
        <div className="w-16 h-1.5 bg-[var(--bg-sunk)] rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all"
            style={{ width: `${matchRate}%` }}
          />
        </div>
        <span className="text-[10px] text-[var(--text-dim)]">{matchRate}% match</span>
      </div>
    </div>
  )
}

// --- Main panel ---

export function RCSBMatchPanel({ candidates }: RCSBMatchPanelProps) {
  const [results, setResults] = useState<CandidateRCSBResult[]>([])
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<RCSBMatchSummary>({ checked: 0, matched: 0, identity_cutoff: 0.4 })
  const [searchTriggered, setSearchTriggered] = useState(false)

  // Filter PASS candidates only (top 10)
  const passedCandidates = candidates
    .filter(c => c.result === 'PASS')
    .sort((a, b) => a.ddG - b.ddG)
    .slice(0, 10)

  async function handleSearch() {
    if (passedCandidates.length === 0) return
    setLoading(true)
    setSearchTriggered(true)

    const newResults: CandidateRCSBResult[] = []
    let matchedCount = 0

    for (const cand of passedCandidates) {
      try {
        const resp = await fetch('/api/rcsb-search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sequence: cand.sequence,
            identity_cutoff: 0.4,
            max_results: 5,
          }),
        })

        if (resp.ok) {
          const data = await resp.json()
          const hits: RCSBHit[] = data.hits ?? []
          if (hits.length > 0) matchedCount++
          newResults.push({
            candidate_id: cand.id,
            sequence: cand.sequence,
            hits,
            searched: true,
          })
        } else if (resp.status === 503) {
          // Backend RCSB module not available
          newResults.push({
            candidate_id: cand.id,
            sequence: cand.sequence,
            hits: [],
            searched: false,
            error: 'RCSB search unavailable (offline mode)',
          })
        } else {
          newResults.push({
            candidate_id: cand.id,
            sequence: cand.sequence,
            hits: [],
            searched: true,
            error: `API error: ${resp.status}`,
          })
        }
      } catch {
        newResults.push({
          candidate_id: cand.id,
          sequence: cand.sequence,
          hits: [],
          searched: false,
          error: 'Network error — check connectivity',
        })
      }
    }

    setResults(newResults)
    setSummary({
      checked: passedCandidates.length,
      matched: matchedCount,
      identity_cutoff: 0.4,
    })
    setLoading(false)
  }

  // Auto-populate from iteration_manifest rcsb_hits if available
  const preloaded = useMemo(() => {
    if (searchTriggered) return null
    const withHits = candidates.filter(c => c.rcsb_hits && c.rcsb_hits.length > 0)
    if (withHits.length === 0) return null
    return withHits.map(c => ({
      candidate_id: c.id,
      sequence: c.sequence,
      hits: (c.rcsb_hits as RCSBHit[]) ?? [],
      searched: true,
    })) as CandidateRCSBResult[]
  }, [candidates, searchTriggered])

  const displayResults = preloaded ?? results
  const displaySummary = preloaded
    ? { checked: preloaded.length, matched: preloaded.filter(r => r.hits.length > 0).length, identity_cutoff: 0.4 }
    : summary

  return (
    <section className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-[var(--accent)]" />
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest">
            RCSB PDB Match
          </h2>
          <HelpTooltip title="RCSB PDB Match">
            RCSB PDB 서열 유사도 검색 결과. PASS 후보 서열을 RCSB에 검색하여 기존 실험 구조와의 매칭 여부를 확인합니다. identity &ge; 40%인 구조를 표시하며, 매칭된 PDB는 할루시네이션 검증의 참조 구조로 활용됩니다.
          </HelpTooltip>
        </div>
        <div className="flex items-center gap-2">
          {displayResults.length > 0 && (
            <span className="text-[10px] text-[var(--text-dim)]">
              {displayResults.length} candidates
            </span>
          )}
          <button
            onClick={handleSearch}
            disabled={loading || passedCandidates.length === 0}
            className={cn(
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
              loading || passedCandidates.length === 0
                ? 'bg-[var(--bg-sunk)] text-[var(--text-dim)] cursor-not-allowed'
                : 'bg-cyan-600/20 text-[var(--accent)] hover:bg-cyan-600/30 border border-[var(--accent)]/30',
            )}
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5" />
                {searchTriggered ? 'Re-search' : 'Search RCSB'}
              </>
            )}
          </button>
        </div>
      </div>

      {passedCandidates.length === 0 && (
        <p className="text-xs text-[var(--text-dim)] text-center py-6">
          No PASS candidates to search. Run the pipeline first.
        </p>
      )}

      {displaySummary.checked > 0 && (
        <div className="mb-4">
          <SummaryBar summary={displaySummary} />
        </div>
      )}

      {displayResults.length > 0 && (
        <div className="space-y-2">
          {displayResults.map(result => (
            <CandidateMatchCard key={result.candidate_id} result={result} />
          ))}
        </div>
      )}

      {!searchTriggered && passedCandidates.length > 0 && displayResults.length === 0 && (
        <p className="text-xs text-[var(--text-dim)] text-center py-6">
          Click &quot;Search RCSB&quot; to check {passedCandidates.length} PASS candidates against RCSB PDB.
        </p>
      )}
    </section>
  )
}
