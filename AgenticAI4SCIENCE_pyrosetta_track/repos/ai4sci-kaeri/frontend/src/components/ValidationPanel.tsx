import { useState, useEffect, useCallback, useRef } from 'react'
import { useFocusTrap } from '../hooks/useFocusTrap'
import { cn } from '../lib/utils'
import { Shield, Loader2, ChevronDown, ChevronUp, X, CheckCircle2, XCircle, AlertTriangle, MinusCircle, Eye } from 'lucide-react'
import { HelpTooltip } from './ui/HelpTooltip'
import type {
  Candidate, CriterionDef, CriterionCheck, UnifiedCandidateResult,
  UnifiedValidationResponse, UnifiedVerdict, ValidationPreset,
} from '../types'

// ── Verdict badge ────────────────────────────────────────────────────────────

const VERDICT_STYLES: Record<UnifiedVerdict, string> = {
  PASS: 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30',
  CAUTION: 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30',
  FAIL: 'bg-[var(--neg-soft)] text-[var(--neg)] border-[var(--neg)]/30',
}

function VerdictBadge({ verdict, passRate }: { verdict: UnifiedVerdict; passRate: number }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border', VERDICT_STYLES[verdict])}>
      {verdict === 'PASS' && <CheckCircle2 className="w-3 h-3" />}
      {verdict === 'CAUTION' && <AlertTriangle className="w-3 h-3" />}
      {verdict === 'FAIL' && <XCircle className="w-3 h-3" />}
      {verdict} ({passRate}%)
    </span>
  )
}

// ── Check result row ─────────────────────────────────────────────────────────

function CheckRow({ check }: { check: CriterionCheck }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="border-b border-[var(--border)] last:border-b-0">
      <button
        onClick={() => setExpanded(e => !e)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-[var(--bg-sunk)] transition-colors text-left"
      >
        {check.skipped ? (
          <MinusCircle className="w-3.5 h-3.5 text-[var(--text-mute)] flex-shrink-0" />
        ) : check.passed ? (
          <CheckCircle2 className="w-3.5 h-3.5 text-[var(--pos)] flex-shrink-0" />
        ) : (
          <XCircle className="w-3.5 h-3.5 text-[var(--neg)] flex-shrink-0" />
        )}
        <span className="text-xs text-[var(--text-mute)] flex-1 truncate">{check.label}</span>
        <span className={cn(
          'text-xs font-mono tabular-nums',
          check.skipped ? 'text-[var(--text-mute)]' : check.passed ? 'text-[var(--pos)]' : 'text-[var(--neg)]',
        )}>
          {check.value !== null && check.value !== undefined ? (typeof check.value === 'number' ? check.value.toFixed(2) : check.value) : '--'}
          {check.unit ? ` ${check.unit}` : ''}
        </span>
        {expanded ? <ChevronUp className="w-3 h-3 text-[var(--text-mute)]" /> : <ChevronDown className="w-3 h-3 text-[var(--text-mute)]" />}
      </button>
      {expanded && (
        <div className="px-3 pb-2 pl-8 space-y-1">
          <p className="text-[10px] text-[var(--text-mute)]">{check.description}</p>
          {check.detail && <p className="text-[10px] text-[var(--text-mute)] font-mono">{check.detail}</p>}
          <p className="text-[10px] text-[var(--text-mute)]">
            Threshold: {JSON.stringify(check.threshold)}
          </p>
        </div>
      )}
    </div>
  )
}

// ── Detail modal ─────────────────────────────────────────────────────────────

function ValidationDetailModal({
  result,
  onClose,
}: {
  result: UnifiedCandidateResult
  onClose: () => void
}) {
  const modalRef = useRef<HTMLDivElement>(null)
  useFocusTrap(modalRef)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const groups = {
    pharmacological: result.checks.filter(c => c.group === 'pharmacological'),
    radiopharmaceutical: result.checks.filter(c => c.group === 'radiopharmaceutical'),
    statistical: result.checks.filter(c => c.group === 'statistical'),
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--bg-sunk)]/80 backdrop-blur backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div ref={modalRef} role="dialog" aria-modal="true" aria-label="Validation Detail" className="bg-[var(--bg)] border border-[var(--border)] rounded-xl shadow-2xl w-[700px] max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] flex-shrink-0">
          <div className="flex items-center gap-3">
            <Shield className="w-4 h-4 text-[var(--accent)]" />
            <span className="text-sm font-semibold text-[var(--text)]">Validation Detail</span>
            <VerdictBadge verdict={result.verdict} passRate={result.pass_rate} />
          </div>
          <button onClick={onClose} aria-label="Close" className="p-1 rounded-md text-[var(--text-mute)] hover:text-[var(--neg)] hover:bg-[var(--bg-elev)] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Summary bar */}
        <div className="flex items-center gap-4 px-4 py-2 border-b border-[var(--border)] bg-[var(--bg)]/50 flex-shrink-0">
          <span className="text-[10px] text-[var(--text-mute)] font-mono truncate max-w-[200px]">{result.sequence}</span>
          <div className="flex gap-3 text-[10px]">
            <span className="text-[var(--pos)]">{result.n_passed} passed</span>
            <span className="text-[var(--neg)]">{result.n_failed} failed</span>
            {result.n_skipped > 0 && <span className="text-[var(--text-mute)]">{result.n_skipped} skipped</span>}
          </div>
          {/* Pass rate bar */}
          <div className="flex-1 h-1.5 bg-[var(--bg-elev)] rounded-full overflow-hidden">
            <div
              className={cn('h-full rounded-full transition-all', result.verdict === 'PASS' ? 'bg-green-500' : result.verdict === 'CAUTION' ? 'bg-amber-500' : 'bg-red-500')}
              style={{ width: `${result.pass_rate}%` }}
            />
          </div>
        </div>

        {/* Check list */}
        <div className="flex-1 overflow-y-auto">
          {groups.pharmacological.length > 0 && (
            <div>
              <div className="px-4 py-1.5 bg-[var(--bg-sunk)] text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider">Pharmacological</div>
              {groups.pharmacological.map(c => <CheckRow key={c.id} check={c} />)}
            </div>
          )}
          {groups.radiopharmaceutical.length > 0 && (
            <div>
              <div className="px-4 py-1.5 bg-[var(--bg-sunk)] text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider">Radiopharmaceutical</div>
              {groups.radiopharmaceutical.map(c => <CheckRow key={c.id} check={c} />)}
            </div>
          )}
          {groups.statistical.length > 0 && (
            <div>
              <div className="px-4 py-1.5 bg-[var(--bg-sunk)] text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider">Statistical</div>
              {groups.statistical.map(c => <CheckRow key={c.id} check={c} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Criteria config panel ────────────────────────────────────────────────────

interface ValidationPanelProps {
  candidates: Candidate[]
  selectedIds: Set<string>
}

export function ValidationPanel({ candidates, selectedIds }: ValidationPanelProps) {
  const [criteriaRegistry, setCriteriaRegistry] = useState<Record<string, CriterionDef>>({})
  const [presets, setPresets] = useState<Record<string, ValidationPreset>>({})
  const [selectedCriteria, setSelectedCriteria] = useState<Set<string>>(new Set())
  const [activePreset, setActivePreset] = useState<string | null>('prrt_radiopharmaceutical')
  const [showConfig, setShowConfig] = useState(false)
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState<UnifiedCandidateResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const [detailTarget, setDetailTarget] = useState<UnifiedCandidateResult | null>(null)
  const fetchedRef = useRef(false)

  // Load criteria registry on mount
  useEffect(() => {
    if (fetchedRef.current) return
    fetchedRef.current = true
    fetch('/api/validation/criteria')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return
        setCriteriaRegistry(data.criteria ?? {})
        setPresets(data.presets ?? {})
        // Apply default preset
        const prrt = data.presets?.prrt_radiopharmaceutical
        if (prrt) {
          setSelectedCriteria(new Set(prrt.criteria))
        } else {
          // Fallback: all default_enabled
          const defaults = Object.entries(data.criteria ?? {})
            .filter(([, v]) => (v as CriterionDef).default_enabled)
            .map(([k]) => k)
          setSelectedCriteria(new Set(defaults))
        }
      })
      .catch(() => { setError('Failed to load validation criteria') })
  }, [])

  const applyPreset = useCallback((presetKey: string) => {
    const preset = presets[presetKey]
    if (preset) {
      setSelectedCriteria(new Set(preset.criteria))
      setActivePreset(presetKey)
    }
  }, [presets])

  const toggleCriterion = useCallback((id: string) => {
    setSelectedCriteria(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
    setActivePreset(null)
  }, [])

  const handleRun = useCallback(async () => {
    const selected = candidates.filter(c => selectedIds.has(c.id))
    if (selected.length === 0) return

    setRunning(true)
    setResults([])
    setError(null)
    try {
      const sequences = selected.map(c => c.sequence).filter(Boolean)
      const res = await fetch('/api/validate/unified', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sequences,
          criteria: Array.from(selectedCriteria),
        }),
      })
      if (res.ok) {
        const data: UnifiedValidationResponse = await res.json()
        setResults(data.results)
      } else {
        setError(`Validation failed (HTTP ${res.status})`)
      }
    } catch {
      setError('Validation request failed')
    } finally {
      setRunning(false)
    }
  }, [candidates, selectedIds, selectedCriteria])

  const criteriaGroups = {
    pharmacological: Object.entries(criteriaRegistry).filter(([, v]) => v.group === 'pharmacological'),
    radiopharmaceutical: Object.entries(criteriaRegistry).filter(([, v]) => v.group === 'radiopharmaceutical'),
    statistical: Object.entries(criteriaRegistry).filter(([, v]) => v.group === 'statistical'),
  }

  return (
    <div className="bg-[var(--bg)] border border-[var(--border)]/50 rounded-xl overflow-hidden">
      {/* Header with run button */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border)]">
        <div className="flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-[var(--accent)]" />
          <span className="text-sm font-semibold text-[var(--text)]">Unified Validation</span>
          <HelpTooltip title="Unified Validation">
            <p>후보 서열의 다각적 검증 결과를 통합 표시합니다.</p>
            <p><strong>검증 항목</strong>: 구조적 안정성, 약리활성 부위 보존, ADMET 예측, 합성 가능성.</p>
            <p>각 항목을 클릭하면 상세 결과를 확인할 수 있습니다.</p>
          </HelpTooltip>
          <span className="text-[10px] text-[var(--text-mute)]">
            {selectedCriteria.size} criteria selected
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowConfig(s => !s)}
            className="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--bg-elev)] text-[var(--text-mute)] border border-[var(--border)] hover:border-[var(--border)] hover:text-[var(--text-mute)] transition-all"
          >
            {showConfig ? 'Hide Config' : 'Config'}
            {showConfig ? <ChevronUp className="w-3 h-3 inline ml-1" /> : <ChevronDown className="w-3 h-3 inline ml-1" />}
          </button>
          <button
            onClick={handleRun}
            disabled={selectedIds.size === 0 || running}
            className={cn(
              'px-3 py-1 rounded-lg text-xs font-semibold transition-all duration-150 flex items-center gap-1.5',
              selectedIds.size > 0 && !running
                ? 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30 hover:bg-[var(--accent-soft)]'
                : 'bg-[var(--bg-elev)] text-[var(--text-mute)] border border-[var(--border)] cursor-not-allowed',
            )}
          >
            {running ? <Loader2 className="w-3 h-3 animate-spin" /> : <Shield className="w-3 h-3" />}
            Validate{selectedIds.size > 0 ? ` (${selectedIds.size})` : ''}
          </button>
        </div>
      </div>

      {/* Criteria config panel */}
      {showConfig && (
        <div className="border-b border-[var(--border)] p-4 space-y-3">
          {/* Presets */}
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[var(--text-mute)] font-semibold uppercase tracking-wider w-14">Preset</span>
            {Object.entries(presets).map(([key, preset]) => (
              <button
                key={key}
                onClick={() => applyPreset(key)}
                className={cn(
                  'px-3 py-1 rounded-md text-xs font-medium border transition-all',
                  activePreset === key
                    ? 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
                    : 'bg-[var(--bg-elev)] text-[var(--text-mute)] border-[var(--border)] hover:border-[var(--border)]',
                )}
              >
                {preset.label}
              </button>
            ))}
            <button
              onClick={() => setActivePreset(null)}
              className={cn(
                'px-3 py-1 rounded-md text-xs font-medium border transition-all',
                activePreset === null
                  ? 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
                  : 'bg-[var(--bg-elev)] text-[var(--text-mute)] border-[var(--border)] hover:border-[var(--border)]',
              )}
            >
              Custom
            </button>
          </div>

          {/* Checkbox grid */}
          <div className="grid grid-cols-3 gap-4">
            {/* Pharmacological */}
            <div>
              <div className="text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider mb-1.5">Pharmacological</div>
              {criteriaGroups.pharmacological.map(([id, def]) => (
                <label key={id} className="flex items-center gap-2 py-0.5 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={selectedCriteria.has(id)}
                    onChange={() => toggleCriterion(id)}
                    className="w-3 h-3 rounded border-[var(--border)] bg-[var(--bg-elev)] text-[var(--accent)] focus:ring-cyan-500/50"
                  />
                  <span className="text-xs text-[var(--text-mute)] group-hover:text-[var(--text-mute)] transition-colors">{def.label}</span>
                </label>
              ))}
            </div>
            {/* Radiopharmaceutical */}
            <div>
              <div className="text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider mb-1.5">Radiopharmaceutical</div>
              {criteriaGroups.radiopharmaceutical.map(([id, def]) => (
                <label key={id} className="flex items-center gap-2 py-0.5 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={selectedCriteria.has(id)}
                    onChange={() => toggleCriterion(id)}
                    className="w-3 h-3 rounded border-[var(--border)] bg-[var(--bg-elev)] text-[var(--accent)] focus:ring-cyan-500/50"
                  />
                  <span className="text-xs text-[var(--text-mute)] group-hover:text-[var(--text-mute)] transition-colors">{def.label}</span>
                </label>
              ))}
              {/* Statistical */}
              <div className="text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider mb-1.5 mt-3">Statistical</div>
              {criteriaGroups.statistical.map(([id, def]) => (
                <label key={id} className="flex items-center gap-2 py-0.5 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={selectedCriteria.has(id)}
                    onChange={() => toggleCriterion(id)}
                    className="w-3 h-3 rounded border-[var(--border)] bg-[var(--bg-elev)] text-[var(--accent)] focus:ring-cyan-500/50"
                  />
                  <span className="text-xs text-[var(--text-mute)] group-hover:text-[var(--text-mute)] transition-colors">{def.label}</span>
                </label>
              ))}
            </div>
            {/* Info column */}
            <div className="bg-[var(--bg-elev)]/30 rounded-lg p-3">
              <div className="text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider mb-1.5">Selected</div>
              <div className="text-2xl font-bold text-[var(--accent)] tabular-nums">{selectedCriteria.size}</div>
              <div className="text-[10px] text-[var(--text-mute)] mt-1">criteria will be evaluated</div>
              {activePreset && presets[activePreset] && (
                <div className="mt-2 text-[10px] text-[var(--text-mute)]">
                  {presets[activePreset].description}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="px-4 py-2.5 border-b border-[var(--neg)]/30 bg-[var(--neg-soft)] text-xs text-[var(--neg)]">
          {error}
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="divide-y divide-[var(--border)]">
          <div className="px-4 py-1.5 bg-[var(--bg-elev)]/30 flex items-center gap-3">
            <span className="text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider">Results</span>
            <span className="text-[10px] text-[var(--text-mute)]">{results.length} candidates</span>
          </div>
          {results.map((r, i) => {
            const candidate = candidates.find(c => c.sequence === r.sequence)
            return (
              <div key={i} className="flex items-center gap-3 px-4 py-2 hover:bg-[var(--bg-elev)]/30 transition-colors">
                <span className="text-xs font-mono text-[var(--text-mute)] w-28 truncate">{candidate?.id ?? r.sequence.slice(0, 12)}</span>
                <span className="text-[10px] font-mono text-[var(--text-mute)] w-32 truncate">{r.sequence}</span>
                <VerdictBadge verdict={r.verdict} passRate={r.pass_rate} />
                <div className="flex-1 flex items-center gap-1">
                  {r.checks.map(c => (
                    c.skipped ? (
                      // P15: skipped dot uses neutral token contrast for WCAG 1.4.11.
                      <div
                        key={c.id}
                        aria-label="skipped"
                        title="이 검증은 데이터 부족으로 스킵됨"
                        className="w-2 h-2 rounded-full bg-[var(--text-dim)]"
                      />
                    ) : (
                      <div
                        key={c.id}
                        title={`${c.label}: ${c.value} ${c.unit} — ${c.passed ? 'PASS' : 'FAIL'}`}
                        aria-label={c.passed ? 'passed' : 'failed'}
                        className={cn(
                          'w-2 h-2 rounded-full',
                          c.passed ? 'bg-green-500' : 'bg-red-500',
                        )}
                      />
                    )
                  ))}
                </div>
                <button
                  onClick={() => setDetailTarget(r)}
                  className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] text-[var(--text-mute)] hover:text-[var(--accent)] hover:bg-[var(--bg-elev)] border border-[var(--border)] hover:border-[var(--accent)]/30 transition-all"
                >
                  <Eye className="w-3 h-3" />
                  Detail
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* Detail modal */}
      {detailTarget && (
        <ValidationDetailModal result={detailTarget} onClose={() => setDetailTarget(null)} />
      )}
    </div>
  )
}
