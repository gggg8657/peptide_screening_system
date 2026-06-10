import { useState, useEffect, useCallback, useMemo } from 'react'
import { Database, ChevronUp, ChevronDown, ChevronsUpDown, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '../lib/utils'

/**
 * ArchivesTopKSlider
 *
 * 1,615 페어 archives 평가 결과에서 Top-K 후보를 표시.
 * - K 선택: 5/10/20/50/100
 * - 정렬 기준: selectivity_margin / iPTM(SSTR2) / Tier
 * - Tier 필터: T3(≥0.92) / T2(≥0.85) / T1(<0.85)
 * - 후보 클릭 → onSelect 콜백 (부모에서 CompareModal 연동)
 *
 * backend /api/archives/top-k 실제 결과를 표시. API 실패 시 명시적 오류 상태로 둔다.
 */

/* ─── 타입 ─── */
export type SstrReceptor = 'SSTR1' | 'SSTR2' | 'SSTR3' | 'SSTR4' | 'SSTR5'
export type ArchiveTier = 'T3' | 'T2' | 'T1'

export interface ArchiveEntry {
  sequence: string
  receptor: SstrReceptor
  iptm: number
  ptm: number
  confidence: number
  tier: ArchiveTier
  selectivity_index?: number   // SSTR2_iptm / mean(others), SSTR2 행에만 존재
  elapsed_sec?: number
  timestamp?: string
}

type SortKey = 'iptm' | 'selectivity_index' | 'tier'
type SortDir = 'asc' | 'desc'

const K_OPTIONS = [5, 10, 20, 50, 100] as const

const TIER_LABELS: Record<ArchiveTier, { label: string; color: string; bg: string; border: string }> = {
  T3: { label: 'T3', color: 'text-[var(--pos)]', bg: 'bg-[var(--pos-soft)]', border: 'border-[var(--pos)]/30' },
  T2: { label: 'T2', color: 'text-[var(--warn)]', bg: 'bg-[var(--warn-soft)]', border: 'border-[var(--warn)]/30' },
  T1: { label: 'T1', color: 'text-[var(--text-dim)]', bg: 'bg-[var(--bg-sunk)]', border: 'border-[var(--border)]' },
}

function deriveTier(iptm: number): ArchiveTier {
  if (iptm >= 0.92) return 'T3'
  if (iptm >= 0.85) return 'T2'
  return 'T1'
}

/* ─── TierBadge (색맹 친화적 — 색상 + 텍스트) ─── */
function TierBadge({ tier }: { tier: ArchiveTier }) {
  const cfg = TIER_LABELS[tier]
  return (
    <span
      className={cn(
        'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border',
        cfg.color, cfg.bg, cfg.border,
      )}
      aria-label={`등급 ${tier}`}
    >
      {cfg.label}
    </span>
  )
}

/* ─── Sort 아이콘 ─── */
function SortIcon({ col, sortKey, sortDir }: { col: SortKey; sortKey: SortKey; sortDir: SortDir }) {
  if (col !== sortKey) return <ChevronsUpDown className="w-3 h-3 text-[var(--text-dim)]" aria-hidden />
  return sortDir === 'desc'
    ? <ChevronDown className="w-3 h-3 text-[var(--accent)]" aria-hidden />
    : <ChevronUp className="w-3 h-3 text-[var(--accent)]" aria-hidden />
}

/* ─── 메인 컴포넌트 ─── */
interface ArchivesTopKSliderProps {
  onSelect?: (entry: ArchiveEntry) => void
  className?: string
}

export function ArchivesTopKSlider({ onSelect, className }: ArchivesTopKSliderProps) {
  const [k, setK] = useState<number>(20)
  const [sortKey, setSortKey] = useState<SortKey>('iptm')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [tierFilter, setTierFilter] = useState<Set<ArchiveTier>>(new Set(['T3', 'T2']))
  const [entries, setEntries] = useState<ArchiveEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [useMock, setUseMock] = useState(false)

  /* API 호출 또는 mock fallback */
  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ receptor: 'SSTR2', k: String(k) })
      const res = await fetch(`/api/archives/top-k?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json() as { entries: ArchiveEntry[] }
      setEntries(
        (data.entries ?? []).map(e => ({ ...e, tier: deriveTier(e.iptm) })),
      )
      setUseMock(false)
    } catch (err) {
      setEntries([])
      setUseMock(false)
      setError(err instanceof Error ? err.message : 'Archive API request failed')
    } finally {
      setLoading(false)
    }
  }, [k])

  useEffect(() => { load() }, [load])

  /* 필터 + 정렬 */
  const displayed = useMemo(() => {
    const tierOrder: Record<ArchiveTier, number> = { T3: 3, T2: 2, T1: 1 }

    return entries
      .filter(e => tierFilter.has(e.tier))
      .sort((a, b) => {
        let va: number, vb: number
        if (sortKey === 'tier') {
          va = tierOrder[a.tier]
          vb = tierOrder[b.tier]
        } else {
          va = (a[sortKey] as number | undefined) ?? 0
          vb = (b[sortKey] as number | undefined) ?? 0
        }
        return sortDir === 'desc' ? vb - va : va - vb
      })
      .slice(0, k)
  }, [entries, tierFilter, sortKey, sortDir, k])

  /* 정렬 토글 */
  const handleSort = (col: SortKey) => {
    if (sortKey === col) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    } else {
      setSortKey(col)
      setSortDir('desc')
    }
  }

  /* Tier 필터 토글 */
  const toggleTier = (tier: ArchiveTier) => {
    setTierFilter(prev => {
      const next = new Set(prev)
      if (next.has(tier)) next.delete(tier)
      else next.add(tier)
      return next
    })
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <Database className="w-3.5 h-3.5 text-[var(--pos)]" aria-hidden />
        <span className="text-xs font-semibold text-[var(--pos)] uppercase tracking-wider">
          Archive Eval — SSTR2 Top-K
        </span>
        {useMock && (
          <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-[var(--warn-soft)] text-[var(--warn)] border border-[var(--warn)]/30">
            API unavailable
          </span>
        )}
      </div>

      {/* 컨트롤 바 */}
      <div className="flex flex-wrap items-center gap-3">
        {/* K 선택 */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-[var(--text-dim)]">Top-K:</span>
          <div
            role="group"
            aria-label="표시 개수 선택"
            className="flex gap-0.5"
          >
            {K_OPTIONS.map(opt => (
              <button
                key={opt}
                onClick={() => setK(opt)}
                aria-pressed={k === opt}
                className={cn(
                  'px-2 py-1 text-[10px] font-medium rounded transition-colors',
                  k === opt
                    ? 'bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30'
                    : 'bg-[var(--bg-elev)] text-[var(--text-dim)] border border-[var(--border)] hover:bg-[var(--bg-sunk)]',
                )}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>

        {/* Tier 필터 */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-[var(--text-dim)]">Tier:</span>
          <div role="group" aria-label="Tier 필터" className="flex gap-0.5">
            {(['T3', 'T2', 'T1'] as ArchiveTier[]).map(tier => {
              const cfg = TIER_LABELS[tier]
              const active = tierFilter.has(tier)
              return (
                <button
                  key={tier}
                  onClick={() => toggleTier(tier)}
                  aria-pressed={active}
                  className={cn(
                    'px-2 py-1 text-[10px] font-semibold rounded border transition-colors',
                    active
                      ? cn(cfg.color, cfg.bg, cfg.border)
                      : 'bg-[var(--bg-elev)] text-[var(--text-dim)] border-[var(--border)]',
                  )}
                >
                  {tier}
                </button>
              )
            })}
          </div>
        </div>

        {/* 결과 수 */}
        <span className="ml-auto text-[10px] text-[var(--text-dim)]" aria-live="polite">
          {loading ? '로딩 중…' : `${displayed.length}개 표시`}
        </span>
      </div>

      {/* 에러 */}
      {error && (
        <div role="alert" className="flex items-center gap-2 rounded border border-[var(--neg)]/30 bg-[var(--neg-soft)] px-3 py-2 text-xs text-[var(--neg)]">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* 테이블 */}
      <div className="relative rounded-lg border border-[var(--border)] overflow-hidden">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[var(--bg)] backdrop-blur-sm">
            <Loader2 className="w-5 h-5 text-[var(--pos)] animate-spin" aria-label="데이터 로딩 중" />
          </div>
        )}

        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-xs" aria-label="Archives 평가 결과">
            <thead className="sticky top-0 bg-[var(--bg)] backdrop-blur-sm">
              <tr className="border-b border-[var(--border)]">
                <th scope="col" className="px-3 py-2 text-left text-[10px] font-semibold text-[var(--text-dim)] uppercase w-6">
                  #
                </th>
                <th scope="col" className="px-3 py-2 text-left text-[10px] font-semibold text-[var(--text-dim)] uppercase">
                  서열
                </th>
                <th
                  scope="col"
                  className="px-3 py-2 text-right text-[10px] font-semibold text-[var(--text-dim)] uppercase cursor-pointer select-none hover:text-[var(--text-mute)] transition-colors"
                  aria-sort={sortKey === 'iptm' ? (sortDir === 'desc' ? 'descending' : 'ascending') : 'none'}
                  onClick={() => handleSort('iptm')}
                >
                  <span className="flex items-center justify-end gap-1">
                    iPTM (SSTR2)
                    <SortIcon col="iptm" sortKey={sortKey} sortDir={sortDir} />
                  </span>
                </th>
                <th
                  scope="col"
                  className="px-3 py-2 text-right text-[10px] font-semibold text-[var(--text-dim)] uppercase cursor-pointer select-none hover:text-[var(--text-mute)] transition-colors"
                  aria-sort={sortKey === 'selectivity_index' ? (sortDir === 'desc' ? 'descending' : 'ascending') : 'none'}
                  onClick={() => handleSort('selectivity_index')}
                >
                  <span className="flex items-center justify-end gap-1">
                    SI×
                    <SortIcon col="selectivity_index" sortKey={sortKey} sortDir={sortDir} />
                  </span>
                </th>
                <th
                  scope="col"
                  className="px-3 py-2 text-center text-[10px] font-semibold text-[var(--text-dim)] uppercase cursor-pointer select-none hover:text-[var(--text-mute)] transition-colors"
                  aria-sort={sortKey === 'tier' ? (sortDir === 'desc' ? 'descending' : 'ascending') : 'none'}
                  onClick={() => handleSort('tier')}
                >
                  <span className="flex items-center justify-center gap-1">
                    Tier
                    <SortIcon col="tier" sortKey={sortKey} sortDir={sortDir} />
                  </span>
                </th>
                <th scope="col" className="px-3 py-2 text-right text-[10px] font-semibold text-[var(--text-dim)] uppercase">
                  Confidence
                </th>
              </tr>
            </thead>

            <tbody>
              {displayed.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-xs text-[var(--text-dim)]">
                    선택된 Tier에 해당하는 데이터가 없습니다
                  </td>
                </tr>
              ) : (
                displayed.map((entry, i) => (
                  <tr
                    key={`${entry.sequence}-${i}`}
                    className={cn(
                      'border-b border-[var(--border)] transition-colors',
                      onSelect
                        ? 'cursor-pointer hover:bg-[var(--pos-soft)] hover:border-[var(--pos)]/30'
                        : 'hover:bg-[var(--bg-elev)]',
                    )}
                    onClick={() => onSelect?.(entry)}
                    role={onSelect ? 'button' : undefined}
                    tabIndex={onSelect ? 0 : undefined}
                    aria-label={onSelect ? `${entry.sequence} 선택` : undefined}
                    onKeyDown={onSelect
                      ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(entry) } }
                      : undefined
                    }
                  >
                    <td className="px-3 py-2 text-[10px] text-[var(--text-dim)] font-mono">
                      {i + 1}
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px] text-[var(--text-mute)] tracking-wider">
                      {entry.sequence}
                    </td>
                    <td className={cn(
                      'px-3 py-2 text-right font-mono tabular-nums',
                      entry.iptm >= 0.92 ? 'text-[var(--pos)] font-semibold' :
                      entry.iptm >= 0.85 ? 'text-[var(--warn)]' : 'text-[var(--text-dim)]',
                    )}>
                      {entry.iptm.toFixed(4)}
                    </td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-[var(--text-mute)]">
                      {entry.selectivity_index != null
                        ? `${entry.selectivity_index.toFixed(2)}×`
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <TierBadge tier={entry.tier} />
                    </td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-[var(--text-dim)]">
                      {entry.confidence.toFixed(3)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 주석 */}
      <p className="text-[10px] text-[var(--text-dim)]">
        SI× = SSTR2 iPTM / mean(SSTR1,3,4,5 iPTM) — 값이 클수록 SSTR2 선택적.
        {useMock && ' /api/archives/top-k unavailable'}
      </p>
    </div>
  )
}
