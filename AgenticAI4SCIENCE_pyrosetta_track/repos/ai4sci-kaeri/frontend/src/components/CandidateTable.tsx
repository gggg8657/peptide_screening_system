import { useState, useMemo, memo } from 'react'
import { cn } from '../lib/utils'
import type { Candidate, PassFail, NephrotoxRiskLevel } from '../types'
import { ChevronUp, ChevronDown, ChevronsUpDown, Info, Shield, Loader2, AlertTriangle, Box, Check, XCircle } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import { useSelection } from '../hooks/useSelection'
import { useAdmetBatch } from '../hooks/useAdmetBatch'
import { useCandidateSort } from '../hooks/useCandidateSort'
import type { SortKey, SortDir } from '../hooks/useCandidateSort'
import { useValidation } from '../hooks/useValidation'

/** Translate raw fail reasons into human-readable Korean explanations */
function humanizeFailReason(raw: string): { summary: string; detail: string } {
  const r = raw.toLowerCase()
  if (r.includes('script failed') && r.includes('no stderr/stdout')) {
    return {
      summary: '시뮬레이션 비정상 종료',
      detail: 'FlexPepDock 프로세스가 에러 메시지 없이 종료되었습니다. 주요 원인: (1) 변이 펩타이드의 심각한 입체 충돌로 에너지 계산 실패, (2) PyRosetta 내부 segfault (메모리 접근 오류), (3) 불가능한 잔기 배치로 인한 NaN 에너지값. 이 후보는 물리적으로 불안정한 구조일 가능성이 높습니다.',
    }
  }
  if (r.includes('script failed') && r.includes('mutateresidue')) {
    return {
      summary: '잔기 변이 실패',
      detail: '참조 구조에서 MutateResidue 적용 중 오류 발생. 지정된 위치에 해당 아미노산으로의 변이가 입체적으로 불가능하거나, 원본 PDB 좌표와 호환되지 않는 잔기 조합입니다.',
    }
  }
  if (r.includes('timed out')) {
    return {
      summary: '시뮬레이션 시간 초과',
      detail: 'FlexPepDock 정밀화가 제한 시간 내에 수렴하지 못했습니다. 큰 구조적 변화가 필요한 변이이거나, Monte Carlo 샘플링이 에너지 최솟값을 찾지 못한 경우입니다.',
    }
  }
  if (r.includes('ddg') || r.includes('δg') || r.includes('dg')) {
    const match = raw.match(/([-\d.]+)/)
    const val = match ? match[1] : '?'
    return {
      summary: `ΔG 게이트 미통과 (${val} kcal/mol)`,
      detail: `결합 에너지(ΔG)가 임계값(-5.0 kcal/mol)보다 높습니다. 이 펩타이드는 SSTR2와 충분히 강하게 결합하지 않습니다. ΔG 값: ${val} kcal/mol.`,
    }
  }
  if (r.includes('clash')) {
    return {
      summary: '입체 충돌 과다',
      detail: '원자 간 입체 충돌(steric clash)이 허용 기준을 초과합니다. 잔기 간 거리가 너무 가까워 물리적으로 존재할 수 없는 구조입니다.',
    }
  }
  if (r.includes('json') || r.includes('parse')) {
    return {
      summary: '결과 파싱 오류',
      detail: 'FlexPepDock 스크립트의 출력을 읽을 수 없습니다. 시뮬레이션은 완료되었으나 결과 형식이 잘못되었을 수 있습니다.',
    }
  }
  return { summary: 'FAIL', detail: raw }
}

const ResultBadge = memo(function ResultBadge({
  result,
  failReason,
  failedRun,
}: {
  result: PassFail
  failReason?: string
  failedRun?: boolean
}) {
  const [show, setShow] = useState(false)

  return (
    <div className="relative inline-flex items-center gap-1">
      <span
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide',
          result === 'PASS'
            ? 'bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30'
            : result === 'REF'
              ? 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30'
              : 'bg-[var(--neg-soft)] text-[var(--neg)] border border-[var(--neg)]/30'
        )}
      >
        {result}
      </span>
      {failedRun && (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide bg-[var(--warn-soft)] text-[var(--warn)] border border-[var(--warn)]/30">
          FAILED RUN
        </span>
      )}
      {result === 'FAIL' && failReason && (
        <button
          className="text-[var(--text-mute)] hover:text-[var(--text-mute)] transition-colors"
          onMouseEnter={() => setShow(true)}
          onMouseLeave={() => setShow(false)}
          onFocus={() => setShow(true)}
          onBlur={() => setShow(false)}
          onKeyDown={e => { if (e.key === 'Escape') setShow(false) }}
          aria-expanded={show}
          aria-label={`Fail reason: ${failReason}`}
        >
          <Info className="w-3 h-3" />
        </button>
      )}
      {show && failReason && (() => {
        const { summary, detail } = humanizeFailReason(failReason)
        return (
          <div className="absolute left-0 top-6 z-50 w-72 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-[10px] text-[var(--text)] leading-relaxed">
            <span className="font-semibold text-[var(--neg)] block mb-1">{summary}</span>
            <p className="mb-2">{detail}</p>
            <details className="text-[var(--text-dim)]">
              <summary className="cursor-pointer hover:text-[var(--text-mute)] text-[9px]">원본 메시지</summary>
              <pre className="mt-1 text-[9px] whitespace-pre-wrap break-all">{failReason}</pre>
            </details>
          </div>
        )
      })()}
    </div>
  )
})

const SortIcon = memo(function SortIcon({ col, sortKey, sortDir }: { col: SortKey; sortKey: SortKey; sortDir: SortDir }) {
  if (col !== sortKey) return <ChevronsUpDown className="w-3 h-3 text-[var(--text-mute)]" />
  return sortDir === 'asc'
    ? <ChevronUp className="w-3 h-3 text-[var(--accent)]" />
    : <ChevronDown className="w-3 h-3 text-[var(--accent)]" />
})

const METRIC_DESCRIPTIONS: Record<string, string> = {
  rank: 'Composite ranking by ΔG (lower = better binding)',
  ddG: 'PyRosetta interface binding energy ΔG (InterfaceAnalyzerMover). ΔG = E(complex) − E(receptor) − E(peptide). More negative = stronger binding. Gate: <= -5.0 kcal/mol. NOTE: Candidate ΔG is single-trial; baseline uses best-of-3. Stdev across seeds can be ~71 kcal/mol.',
  totalScore: 'PyRosetta total Rosetta score after FlexPepDock refinement. More negative = more favorable overall energy',
  clashScore: 'Steric clash score (fa_rep). Lower = fewer atomic clashes. Gate: <= 10. Amber: >5, Red: >10',
  finalScore: 'Ranking metric derived from ΔG. More positive = stronger binding',
}

const COLUMNS: { key: SortKey; label: string; unit?: string; description: string }[] = [
  { key: 'rank',       label: 'Rank',         description: METRIC_DESCRIPTIONS.rank },
  { key: 'ddG',        label: 'ΔG',           unit: 'kcal/mol', description: METRIC_DESCRIPTIONS.ddG },
  { key: 'totalScore', label: 'Total Score',  unit: 'REU',      description: METRIC_DESCRIPTIONS.totalScore },
  { key: 'clashScore', label: 'Clash',        unit: 'REU',      description: METRIC_DESCRIPTIONS.clashScore },
  { key: 'finalScore', label: 'Final Score',  description: METRIC_DESCRIPTIONS.finalScore },
]

const ScoreCell = memo(function ScoreCell({ value, min, max, invert = false }: { value: number; min: number; max: number; invert?: boolean }) {
  const range = max - min
  const normalized = range === 0 ? 0.5 : (value - min) / range
  const good = invert ? 1 - normalized : normalized
  const hue = good * 120 // 0=red, 120=green
  return (
    <span style={{ color: `hsl(${hue}, 70%, 65%)` }} className="font-mono text-xs tabular-nums">
      {value.toFixed(2)}
    </span>
  )
})

/** ΔG cell: no fixed range — lower (more negative) is always greener.
 *  Outlier flagging: |ΔG| > 80 = red warning, |ΔG| > 100 = severe outlier (Finding #3) */
const DdGCell = memo(function DdGCell({ value }: { value: number }) {
  const isOutlier = value < -80 || value > 100
  const isSevereOutlier = value < -100 || value > 200
  // sigmoid-like mapping: -40 → deep green, 0 → red, unbounded
  const t = Math.max(0, Math.min(1, -value / 40))
  const hue = t * 120
  return (
    <span className="inline-flex items-center gap-1">
      <span
        style={{ color: isOutlier ? undefined : `hsl(${hue}, 70%, 65%)` }}
        className={cn(
          'font-mono text-xs tabular-nums',
          isSevereOutlier && 'text-[var(--neg)] font-bold',
          isOutlier && !isSevereOutlier && 'text-[var(--warn)] font-bold',
        )}
      >
        {value.toFixed(2)}
      </span>
      {isOutlier && (
        <span title={`Outlier ΔG (${isSevereOutlier ? 'severe' : 'suspect'}): value outside expected range. May indicate scoring artifact.`}>
          <AlertTriangle className={cn('w-3 h-3', isSevereOutlier ? 'text-[var(--neg)]' : 'text-[var(--warn)]')} />
        </span>
      )}
    </span>
  )
})

/** Clash cell with amber (>5) / red (>10) highlighting + colorblind-safe icons (Finding #5) */
const ClashCell = memo(function ClashCell({ value }: { value: number }) {
  const isRed = value > 10
  const isAmber = value > 5 && value <= 10
  return (
    <span className={cn(
      'inline-flex items-center gap-1 font-mono text-xs tabular-nums',
      isRed && 'text-[var(--neg)] font-bold',
      isAmber && 'text-[var(--warn)] font-bold',
      !isRed && !isAmber && 'text-[var(--pos)]',
    )}>
      {/* Colorblind-safe icon: check / warning / x */}
      {isRed ? (
        <XCircle className="w-3 h-3 shrink-0" aria-hidden="true" />
      ) : isAmber ? (
        <AlertTriangle className="w-3 h-3 shrink-0" aria-hidden="true" />
      ) : (
        <Check className="w-3 h-3 shrink-0" aria-hidden="true" />
      )}
      {value.toFixed(2)}
      {isRed && <span className="text-[10px] ml-0.5 text-[var(--neg)]">FAIL</span>}
    </span>
  )
})

/** Single-trial badge for candidate ΔG (Finding #4) */
const TrialBadge = memo(function TrialBadge({ source }: { source?: 'live' | 'historical' | 'silo_a' | 'silo_b' }) {
  if (source === 'historical') return null
  return (
    <span className="text-[10px] text-[var(--warn)]/70 font-semibold ml-1" title="Single-trial measurement. Baseline uses best-of-3 trials. ΔG variance across seeds can be significant.">
      1-trial
    </span>
  )
})

const ValidationBadge = memo(function ValidationBadge({ result }: { result?: import('../types').ValidationResult }) {
  const [showDetail, setShowDetail] = useState(false)

  if (!result) return <span className="text-[10px] text-[var(--text-mute)]">--</span>
  if (result.validation === 'pending') {
    return <Loader2 className="w-3 h-3 text-[var(--text-mute)] animate-spin" />
  }

  const passed = result.validation === 'pass'

  return (
    <div className="relative inline-flex items-center gap-1">
      <span
        className={cn(
          'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide',
          passed
            ? 'bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30'
            : result.validation === 'not_found'
            ? 'bg-[var(--bg-elev)]/40 text-[var(--text-mute)] border border-[var(--border)]/30'
            : 'bg-[var(--warn-soft)] text-[var(--warn)] border border-[var(--warn)]/30'
        )}
      >
        <Shield className="w-2.5 h-2.5" />
        {result.validation.toUpperCase()}
      </span>
      {result.checks.length > 0 && (
        <button
          className="text-[var(--text-mute)] hover:text-[var(--text-mute)] transition-colors"
          onMouseEnter={() => setShowDetail(true)}
          onMouseLeave={() => setShowDetail(false)}
          onFocus={() => setShowDetail(true)}
          onBlur={() => setShowDetail(false)}
          onKeyDown={e => { if (e.key === 'Escape') setShowDetail(false) }}
          aria-expanded={showDetail}
          aria-label="Validation details"
        >
          <Info className="w-3 h-3" />
        </button>
      )}
      {showDetail && result.checks.length > 0 && (
        <div className="absolute left-0 top-6 z-50 w-64 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-[10px] text-[var(--text)] leading-relaxed">
          <span className="font-semibold block mb-1.5">Validation Checks:</span>
          {result.checks.map((check, i) => (
            <div key={i} className="flex items-center gap-1.5 mb-1">
              <span className={check.passed ? 'text-[var(--pos)]' : 'text-[var(--neg)]'}>
                {check.passed ? 'PASS' : 'FAIL'}
              </span>
              <span className="text-[var(--text-mute)]">{check.rule}</span>
              <span className="text-[var(--text-mute)] ml-auto">{check.value.toFixed(2)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
})

interface DdGStats {
  count: number
  min: number
  median: number
  max: number
}

function computeDdGStatsBySequence(allCandidates: Candidate[]): Map<string, DdGStats> {
  const bySeq = new Map<string, number[]>()
  for (const c of allCandidates) {
    if (!c.sequence) continue
    const vals = bySeq.get(c.sequence) ?? []
    vals.push(c.ddG)
    bySeq.set(c.sequence, vals)
  }
  const stats = new Map<string, DdGStats>()
  for (const [seq, vals] of bySeq) {
    if (vals.length < 2) continue
    vals.sort((a, b) => a - b)
    const mid = Math.floor(vals.length / 2)
    const median = vals.length % 2 === 0 ? (vals[mid - 1] + vals[mid]) / 2 : vals[mid]
    stats.set(seq, { count: vals.length, min: vals[0], median, max: vals[vals.length - 1] })
  }
  return stats
}

const ReproducibilityBadge = memo(function ReproducibilityBadge({ stats }: { stats?: DdGStats }) {
  const [showDetail, setShowDetail] = useState(false)
  if (!stats) {
    return (
      <span className="text-[10px] text-[var(--warn)]/60 font-semibold" title="Only 1 measurement available for this sequence. Reproducibility unverified.">
        unverified
      </span>
    )
  }
  const range = stats.max - stats.min
  return (
    <div className="relative inline-flex items-center gap-1">
      <span
        className={cn(
          'text-[10px] font-mono tabular-nums cursor-default',
          range > 50 ? 'text-[var(--neg)]' : range > 20 ? 'text-[var(--warn)]' : 'text-[var(--pos)]',
        )}
        tabIndex={0}
        role="button"
        aria-expanded={showDetail}
        aria-label={`Reproducibility: median ${stats.median.toFixed(1)}, ${stats.count} trials`}
        onMouseEnter={() => setShowDetail(true)}
        onMouseLeave={() => setShowDetail(false)}
        onFocus={() => setShowDetail(true)}
        onBlur={() => setShowDetail(false)}
        onKeyDown={e => { if (e.key === 'Escape') setShowDetail(false) }}
      >
        {stats.median.toFixed(1)}
        <span className="text-[10px] text-[var(--text-mute)] ml-0.5">({stats.count}x)</span>
      </span>
      {showDetail && (
        <div className="absolute left-0 top-5 z-50 w-48 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2 shadow-xl text-[10px] text-[var(--text)] leading-relaxed">
          <span className="font-semibold block mb-1">ΔG Reproducibility ({stats.count} trials):</span>
          <div className="flex justify-between"><span>Min:</span><span className="font-mono">{stats.min.toFixed(2)}</span></div>
          <div className="flex justify-between"><span>Median:</span><span className="font-mono">{stats.median.toFixed(2)}</span></div>
          <div className="flex justify-between"><span>Max:</span><span className="font-mono">{stats.max.toFixed(2)}</span></div>
          <div className="flex justify-between mt-1 border-t border-[var(--border)] pt-1"><span>Range:</span><span className={cn('font-mono font-bold', range > 50 ? 'text-[var(--neg)]' : range > 20 ? 'text-[var(--warn)]' : 'text-[var(--pos)]')}>{range.toFixed(2)}</span></div>
        </div>
      )}
    </div>
  )
})

const DruglikenessBadge = memo(function DruglikenessBadge({ score }: { score?: number }) {
  if (score === undefined) return <span className="text-[10px] text-[var(--text-mute)]">--</span>
  const color = score >= 75 ? 'text-[var(--pos)] bg-[var(--pos-soft)] border-[var(--pos)]/30'
    : score >= 50 ? 'text-[var(--warn)] bg-[var(--warn-soft)] border-[var(--warn)]/30'
    : 'text-[var(--neg)] bg-[var(--neg-soft)] border-[var(--neg)]/30'
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tabular-nums border', color)}>
      {score}
    </span>
  )
})

const NEPHROTOX_COLORS: Record<NephrotoxRiskLevel, string> = {
  Low: 'text-[var(--pos)]',
  Moderate: 'text-[var(--warn)]',
  High: 'text-[var(--neg)]',
}

const NephrotoxBadge = memo(function NephrotoxBadge({ risk }: { risk?: { risk_level: NephrotoxRiskLevel; renal_risk_score: number; warning: string } }) {
  const [showTip, setShowTip] = useState(false)
  if (!risk) return <span className="text-[10px] text-[var(--text-mute)]">--</span>
  const color = NEPHROTOX_COLORS[risk.risk_level]
  return (
    <div className="relative inline-flex items-center gap-1">
      <span
        className={cn('text-sm cursor-default', color)}
        tabIndex={0}
        role="button"
        aria-expanded={showTip}
        aria-label={`Renal risk: ${risk.risk_level} (${risk.renal_risk_score})`}
        onMouseEnter={() => setShowTip(true)}
        onMouseLeave={() => setShowTip(false)}
        onFocus={() => setShowTip(true)}
        onBlur={() => setShowTip(false)}
        onKeyDown={e => { if (e.key === 'Escape') setShowTip(false) }}
        title={`Renal risk: ${risk.risk_level} (${risk.renal_risk_score})`}
      >
        {/* Kidney SVG icon */}
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
          <path d="M12 2C9.5 2 7.5 3.5 6.5 5.5C5 4.5 3 5 2 7C1 9 2 11.5 4 12.5C3 14 3 16 4.5 17.5C6 19 8 19 9.5 18C10 20 11 22 12 22C13 22 14 20 14.5 18C16 19 18 19 19.5 17.5C21 16 21 14 20 12.5C22 11.5 23 9 22 7C21 5 19 4.5 17.5 5.5C16.5 3.5 14.5 2 12 2Z" />
        </svg>
      </span>
      <span className={cn('text-[10px] font-bold', color)}>{risk.risk_level[0]}</span>
      {showTip && risk.warning && (
        <div className="absolute left-0 top-6 z-50 w-64 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-[10px] text-[var(--text)] leading-relaxed">
          <span className={cn('font-semibold block mb-1', color)}>Renal Risk: {risk.risk_level} ({risk.renal_risk_score})</span>
          {risk.warning}
        </div>
      )}
    </div>
  )
})

interface CandidateTableProps {
  candidates: Candidate[]
  historicalCandidates?: Candidate[]
  onView3D?: (candidateId: string) => void
  onSelectionChange?: (selectedIds: Set<string>) => void
  archiveRunId?: string | null
}

export function CandidateTable({ candidates, historicalCandidates = [], onView3D, onSelectionChange, archiveRunId }: CandidateTableProps) {
  const selection = useSelection(onSelectionChange)
  const { admetData } = useAdmetBatch(candidates)
  const sort = useCandidateSort(candidates)
  const validation = useValidation({
    selectedIds: selection.selectedIds,
    archiveRunId,
    onValidationComplete: selection.clearSelection,
  })

  const ddGStats = useMemo(
    () => computeDdGStatsBySequence([...candidates, ...historicalCandidates]),
    [candidates, historicalCandidates],
  )

  const handleFilterClick = (f: 'all' | 'PASS' | 'FAIL' | 'REF') => {
    sort.setFilter(f)
    sort.setPage(0)
  }

  const handleSelectAll = () => {
    selection.toggleSelectPage(sort.paged.map(c => c.id))
  }

  const handlePrevPage = () => {
    sort.setPage(p => Math.max(0, p - 1))
  }

  const handleNextPage = () => {
    sort.setPage(p => Math.min(sort.totalPages - 1, p + 1))
  }

  return (
    <section className="card flex flex-col gap-3" aria-label="Candidate Ranking Table">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
            Candidate Ranking
            <HelpTooltip title="Candidate Ranking Table">
              <p>FlexPepDock 시뮬레이션 결과 후보 펩타이드 목록입니다.</p>
              <p><strong>ΔG</strong>: 결합 자유 에너지. 음수일수록 강한 결합 (게이트: ≤ -5.0 kcal/mol)</p>
              <p><strong>Clash</strong>: 원자 간 입체 충돌 점수 (게이트: ≤ 10)</p>
              <p><strong>PASS/FAIL</strong>: QC 게이트 통과 여부. FAIL 옆 <span className="text-[var(--text-mute)]">ⓘ</span> 아이콘에 커서를 올리면 실패 원인이 한국어로 표시됩니다.</p>
              <p><strong>1T</strong> 뱃지: 단일 trial 측정값. Baseline은 best-of-3 trial 사용.</p>
            </HelpTooltip>
          </h2>
          <p className="text-xs text-[var(--text-mute)] mt-0.5">
            {candidates.length} candidates &middot;
            <span className="text-[var(--pos)] ml-1">{sort.passCount} pass</span>
            <span className="text-[var(--text-mute)] mx-1">/</span>
            <span className="text-[var(--neg)]">{sort.failCount} fail</span>
            {sort.refCount > 0 && (
              <>
                <span className="text-[var(--text-mute)] mx-1">/</span>
                <span className="text-[var(--accent)]">{sort.refCount} ref</span>
              </>
            )}
          </p>
          <p className="text-[10px] text-[var(--warn)]/60 mt-0.5">
            &Delta;G: single-trial per candidate &middot; baseline: best-of-3 trials
          </p>
        </div>
        <div className="flex gap-1.5 items-center flex-wrap" role="group" aria-label="Filter and actions">
          {(['all', 'PASS', 'FAIL', 'REF'] as const).map(f => (
            <button
              key={f}
              onClick={() => handleFilterClick(f)}
              className={cn(
                'px-3 py-1 rounded-lg text-xs font-medium transition-all duration-150',
                sort.filter === f
                  ? f === 'PASS' ? 'bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30'
                    : f === 'FAIL' ? 'bg-[var(--neg-soft)] text-[var(--neg)] border border-[var(--neg)]/30'
                    : f === 'REF' ? 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30'
                    : 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30'
                  : 'bg-[var(--bg-elev)] text-[var(--text-mute)] border border-[var(--border)] hover:border-[var(--border)]'
              )}
            >
              {f === 'all' ? 'All' : f}
            </button>
          ))}
          <button
            onClick={validation.handleValidate}
            disabled={selection.selectedIds.size === 0 || validation.validating}
            className={cn(
              'px-3 py-1 rounded-lg text-xs font-semibold transition-all duration-150 flex items-center gap-1.5',
              selection.selectedIds.size > 0 && !validation.validating
                ? 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30 hover:bg-[var(--accent-soft)]'
                : 'bg-[var(--bg-elev)] text-[var(--text-mute)] border border-[var(--border)] cursor-not-allowed opacity-50'
            )}
          >
            {validation.validating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Shield className="w-3 h-3" />}
            Validate{selection.selectedIds.size > 0 ? ` (${selection.selectedIds.size})` : ''}
          </button>
        </div>
      </div>

      {/* Desktop Table (sm and above) */}
      <div className="hidden sm:block overflow-x-auto rounded-lg border border-[var(--border)]">
        <table className="w-full text-xs" role="table" aria-label="Candidate scores">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[var(--bg)]/80">
              <th className="px-2 py-2.5 w-8">
                <input
                  type="checkbox"
                  checked={sort.paged.length > 0 && sort.paged.every(c => selection.selectedIds.has(c.id))}
                  onChange={handleSelectAll}
                  className="w-3.5 h-3.5 rounded border-[var(--border)] bg-[var(--bg-elev)] text-[var(--accent)] focus:ring-cyan-500/30 focus:ring-offset-0 cursor-pointer"
                  aria-label="Select all on page"
                />
              </th>
              {COLUMNS.map(col => (
                <th
                  key={col.key}
                  className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)] cursor-pointer select-none hover:text-[var(--text)] transition-colors whitespace-nowrap group/th relative"
                  onClick={() => sort.handleSort(col.key)}
                  aria-sort={sort.sortKey === col.key ? (sort.sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                >
                  <div className="flex items-center gap-1">
                    <span>{col.label}</span>
                    {col.unit && <span className="text-[var(--text-mute)] text-[10px]">({col.unit})</span>}
                    <SortIcon col={col.key} sortKey={sort.sortKey} sortDir={sort.sortDir} />
                  </div>
                  <div className="absolute left-0 top-full mt-1 z-50 w-64 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-[10px] text-[var(--text)] leading-relaxed font-normal hidden group-hover/th:block">
                    {col.description}
                  </div>
                </th>
              ))}
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)] whitespace-nowrap">ID</th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)]">Sequence</th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)]">Result</th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)] whitespace-nowrap group/th relative">
                <div className="flex items-center gap-1">
                  <span>Repro.</span>
                  <span className="text-[var(--text-mute)] text-[10px]">(ΔG)</span>
                </div>
                <div className="absolute left-0 top-full mt-1 z-50 w-64 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-[10px] text-[var(--text)] leading-relaxed font-normal hidden group-hover/th:block">
                  ddG reproducibility across multiple trials/seeds for the same sequence. Shows median and trial count. &quot;unverified&quot; = single trial only. Range &gt;50 is red, &gt;20 is amber.
                </div>
              </th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)] whitespace-nowrap">Validation</th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)] whitespace-nowrap group/th relative">
                <div className="flex items-center gap-1">
                  <span>Drug-like</span>
                </div>
                <div className="absolute left-0 top-full mt-1 z-50 w-64 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-[10px] text-[var(--text)] leading-relaxed font-normal hidden group-hover/th:block">
                  Peptide druglikeness score (0-100). Criteria: MW range, net charge, hydrophobicity, no repeat residues. Green &gt;=75, Amber &gt;=50, Red &lt;50.
                </div>
              </th>
              <th className="px-3 py-2.5 text-left font-semibold text-[var(--text-mute)] whitespace-nowrap group/th relative">
                <div className="flex items-center gap-1">
                  <span>Nephrotox</span>
                </div>
                <div className="absolute left-0 top-full mt-1 z-50 w-64 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-[10px] text-[var(--text)] leading-relaxed font-normal hidden group-hover/th:block">
                  PRRT renal retention risk. Based on cationic residue count (Lys+Arg) and net charge. Low &lt;30, Moderate 30-60, High &gt;60.
                </div>
              </th>
              {onView3D && (
                <th className="px-3 py-2.5 text-center font-semibold text-[var(--text-mute)] whitespace-nowrap w-10">3D</th>
              )}
            </tr>
          </thead>
          <tbody>
            {sort.paged.map((c, idx) => (
              <tr
                key={c.id}
                className={cn(
                  'border-b border-[var(--border)]/50 transition-colors duration-100',
                  idx % 2 === 0 ? 'bg-[var(--bg)]/20' : 'bg-transparent',
                  selection.selectedIds.has(c.id) ? 'bg-[var(--accent-soft)]' : 'hover:bg-[var(--bg-elev)]/40'
                )}
              >
                <td className="px-2 py-2">
                  <input
                    type="checkbox"
                    checked={selection.selectedIds.has(c.id)}
                    onChange={() => selection.toggleSelect(c.id)}
                    className="w-3.5 h-3.5 rounded border-[var(--border)] bg-[var(--bg-elev)] text-[var(--accent)] focus:ring-cyan-500/30 focus:ring-offset-0 cursor-pointer"
                    aria-label={`Select ${c.id}`}
                  />
                </td>
                <td className="px-3 py-2 font-bold text-[var(--text-mute)] tabular-nums">
                  {c.rank <= 3 ? (
                    <span className={cn(
                      'inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold',
                      c.rank === 1 ? 'bg-[var(--warn-soft)] text-[var(--warn)]' :
                      c.rank === 2 ? 'bg-[var(--bg-sunk)]/20 text-[var(--text-mute)]' :
                      'bg-[var(--warn-soft)] text-[var(--warn)]'
                    )}>
                      {c.rank}
                    </span>
                  ) : (
                    <span className="text-[var(--text-mute)]">{c.rank}</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <DdGCell value={c.ddG} />
                  <TrialBadge source={c.source} />
                </td>
                <td className="px-3 py-2">
                  <ScoreCell value={c.totalScore} min={-800} max={-200} invert />
                </td>
                <td className="px-3 py-2">
                  <ClashCell value={c.clashScore} />
                </td>
                <td className="px-3 py-2">
                  <ScoreCell value={c.finalScore} min={0} max={50} />
                </td>
                <td className="px-3 py-2 font-mono text-[var(--text-mute)] whitespace-nowrap">{c.id}</td>
                <td className="px-3 py-2 font-mono text-[var(--text-mute)] tracking-wider whitespace-nowrap">
                  {c.sequence}
                </td>
                <td className="px-3 py-2">
                  <ResultBadge
                    result={c.result}
                    failReason={c.failReason}
                    failedRun={c.result === 'FAIL' && c.source === 'historical'}
                  />
                </td>
                <td className="px-3 py-2">
                  <ReproducibilityBadge stats={ddGStats.get(c.sequence)} />
                </td>
                <td className="px-3 py-2">
                  <ValidationBadge result={validation.validationResults.get(c.id)} />
                </td>
                <td className="px-3 py-2">
                  <DruglikenessBadge score={admetData.get(c.sequence)?.admet?.druglikeness_score} />
                </td>
                <td className="px-3 py-2">
                  <NephrotoxBadge risk={admetData.get(c.sequence)?.nephrotox} />
                </td>
                {onView3D && (
                  <td className="px-3 py-2 text-center">
                    <button
                      onClick={() => onView3D(c.id)}
                      className="inline-flex items-center justify-center w-7 h-7 rounded-md bg-[var(--bg-elev)] border border-[var(--border)] hover:border-[var(--accent)]/30 hover:bg-[var(--accent-soft)] text-[var(--text-mute)] hover:text-[var(--accent)] transition-all"
                      title={`View 3D structure: ${c.id}`}
                    >
                      <Box className="w-3.5 h-3.5" />
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View (below sm) */}
      <div className="block sm:hidden space-y-2" role="list" aria-label="Candidate cards">
        {sort.paged.map(c => (
          <div
            key={c.id}
            role="listitem"
            className={cn(
              'rounded-lg border p-3 space-y-2 transition-colors duration-100',
              selection.selectedIds.has(c.id)
                ? 'bg-[var(--accent-soft)] border-[var(--accent)]/30'
                : 'bg-[var(--bg)]/40 border-[var(--border)] hover:border-[var(--border)]'
            )}
          >
            {/* Card Header: checkbox + rank + ID + result */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selection.selectedIds.has(c.id)}
                onChange={() => selection.toggleSelect(c.id)}
                className="w-4 h-4 rounded border-[var(--border)] bg-[var(--bg-elev)] text-[var(--accent)] focus:ring-cyan-500/30 focus:ring-offset-0 cursor-pointer shrink-0"
                aria-label={`Select ${c.id}`}
              />
              <span className="font-bold text-[var(--text-mute)] tabular-nums text-sm">
                {c.rank <= 3 ? (
                  <span className={cn(
                    'inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold',
                    c.rank === 1 ? 'bg-[var(--warn-soft)] text-[var(--warn)]' :
                    c.rank === 2 ? 'bg-[var(--bg-sunk)]/20 text-[var(--text-mute)]' :
                    'bg-[var(--warn-soft)] text-[var(--warn)]'
                  )}>
                    #{c.rank}
                  </span>
                ) : (
                  <span className="text-[var(--text-mute)]">#{c.rank}</span>
                )}
              </span>
              <span className="font-mono text-xs text-[var(--text-mute)]">{c.id}</span>
              <span className="ml-auto">
                <ResultBadge
                  result={c.result}
                  failReason={c.failReason}
                  failedRun={c.result === 'FAIL' && c.source === 'historical'}
                />
              </span>
            </div>

            {/* Sequence */}
            <div className="font-mono text-[11px] text-[var(--text-mute)] tracking-wider break-all bg-[var(--bg-sunk)] rounded px-2 py-1">
              {c.sequence}
            </div>

            {/* Scores Grid */}
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-[var(--text-mute)]">ΔG</span>
                <span><DdGCell value={c.ddG} /><TrialBadge source={c.source} /></span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-mute)]">Total</span>
                <ScoreCell value={c.totalScore} min={-800} max={-200} invert />
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-mute)]">Clash</span>
                <ClashCell value={c.clashScore} />
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-mute)]">Final</span>
                <ScoreCell value={c.finalScore} min={0} max={50} />
              </div>
            </div>

            {/* Badges Row */}
            <div className="flex items-center gap-2 flex-wrap text-xs">
              <ReproducibilityBadge stats={ddGStats.get(c.sequence)} />
              <ValidationBadge result={validation.validationResults.get(c.id)} />
              <DruglikenessBadge score={admetData.get(c.sequence)?.admet?.druglikeness_score} />
              <NephrotoxBadge risk={admetData.get(c.sequence)?.nephrotox} />
              {onView3D && (
                <button
                  onClick={() => onView3D(c.id)}
                  className="ml-auto inline-flex items-center justify-center w-7 h-7 rounded-md bg-[var(--bg-elev)] border border-[var(--border)] hover:border-[var(--accent)]/30 hover:bg-[var(--accent-soft)] text-[var(--text-mute)] hover:text-[var(--accent)] transition-all"
                  title={`View 3D structure: ${c.id}`}
                >
                  <Box className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-xs text-[var(--text-mute)]">
        <span>
          Showing {sort.sorted.length === 0 ? 0 : sort.page * 12 + 1}–{Math.min((sort.page + 1) * 12, sort.sorted.length)} of {sort.sorted.length}
        </span>
        <div className="flex gap-1">
          <button
            onClick={handlePrevPage}
            disabled={sort.page === 0}
            className="px-2.5 py-1 rounded-md bg-[var(--bg-elev)] border border-[var(--border)] hover:border-[var(--border)] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            aria-label="Previous page"
          >
            ←
          </button>
          {(() => {
            const pages: (number | 'ellipsis')[] = []
            const total = sort.totalPages
            const current = sort.page
            if (total <= 7) {
              for (let i = 0; i < total; i++) pages.push(i)
            } else {
              pages.push(0)
              if (current > 3) pages.push('ellipsis')
              for (let i = Math.max(1, current - 1); i <= Math.min(total - 2, current + 1); i++) pages.push(i)
              if (current < total - 4) pages.push('ellipsis')
              pages.push(total - 1)
            }
            return pages.map((p, idx) =>
              p === 'ellipsis' ? (
                <span key={`e${idx}`} className="px-1.5 py-1 text-[var(--text-dim)]">...</span>
              ) : (
                <button
                  key={p}
                  onClick={() => sort.setPage(p)}
                  className={cn(
                    'px-2.5 py-1 rounded-md border transition-all',
                    p === current
                      ? 'bg-[var(--accent-soft)] border-[var(--accent)]/30 text-[var(--accent)]'
                      : 'bg-[var(--bg-elev)] border-[var(--border)] hover:border-[var(--border)]'
                  )}
                  aria-label={`Page ${p + 1}`}
                  aria-current={p === current ? 'page' : undefined}
                >
                  {p + 1}
                </button>
              )
            )
          })()}
          <button
            onClick={handleNextPage}
            disabled={sort.page >= sort.totalPages - 1 || sort.totalPages === 0}
            className="px-2.5 py-1 rounded-md bg-[var(--bg-elev)] border border-[var(--border)] hover:border-[var(--border)] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            aria-label="Next page"
          >
            →
          </button>
        </div>
      </div>
    </section>
  )
}
