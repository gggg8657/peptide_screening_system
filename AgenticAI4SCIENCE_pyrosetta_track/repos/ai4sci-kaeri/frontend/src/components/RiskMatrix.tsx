import { useEffect, useState, useRef } from 'react'
import { cn } from '../lib/utils'
import { useFocusTrap } from '../hooks/useFocusTrap'
import type { RiskItem, RiskPriority, RiskProbability, RiskImpact } from '../types'
import { RISK_ITEMS } from '../data/mockData'
import { Shield, AlertTriangle, X } from 'lucide-react'

const PROBABILITIES: RiskProbability[] = ['Low', 'Medium', 'High']
const IMPACTS: RiskImpact[] = ['Critical', 'Severe', 'Minor']

const PRIORITY_STYLES: Record<RiskPriority, { bg: string; text: string; border: string; badge: string }> = {
  P0: {
    bg: 'bg-[var(--neg-soft)]',
    text: 'text-[var(--neg)]',
    border: 'border-[var(--neg)]/30',
    badge: 'bg-[var(--neg-soft)] text-[var(--neg)] border-[var(--neg)]/30',
  },
  P1: {
    bg: 'bg-[var(--warn-soft)]',
    text: 'text-[var(--warn)]',
    border: 'border-[var(--warn)]/30',
    badge: 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30',
  },
  P2: {
    bg: 'bg-[var(--warn-soft)]',
    text: 'text-[var(--warn)]',
    border: 'border-[var(--warn)]/30',
    badge: 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30',
  },
  P3: {
    bg: 'bg-[var(--pos-soft)]',
    text: 'text-[var(--pos)]',
    border: 'border-[var(--pos)]/30',
    badge: 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30',
  },
}

const CELL_BG: Record<string, string> = {
  'High-Critical':   'bg-[var(--neg-soft)] border-[var(--neg)]/30',
  'High-Severe':     'bg-orange-950/50 border-[var(--warn)]/30',
  'High-Minor':      'bg-yellow-950/40 border-yellow-600/20',
  'Medium-Critical': 'bg-orange-950/50 border-[var(--warn)]/30',
  'Medium-Severe':   'bg-yellow-950/40 border-yellow-600/20',
  'Medium-Minor':    'bg-[var(--bg-sunk)] border-[var(--border)]',
  'Low-Critical':    'bg-yellow-950/40 border-yellow-600/20',
  'Low-Severe':      'bg-[var(--bg-sunk)] border-[var(--border)]',
  'Low-Minor':       'bg-[var(--bg)]/60 border-[var(--border)]/40',
}

interface RiskDetailModalProps {
  item: RiskItem
  onClose: () => void
}

function RiskDetailModal({ item, onClose }: RiskDetailModalProps) {
  const styles = PRIORITY_STYLES[item.priority]
  const modalRef = useRef<HTMLDivElement>(null)
  useFocusTrap(modalRef)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={`Risk detail: ${item.label}`}
    >
      <div
        className="absolute inset-0 bg-[var(--bg-sunk)]/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div ref={modalRef} className="relative bg-[var(--bg)] border border-[var(--border)] rounded-xl p-5 max-w-sm w-full shadow-2xl animate-slide-in">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-[var(--text-mute)] hover:text-[var(--text-mute)] transition-colors"
          aria-label="Close"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-start gap-3 mb-3">
          <div className={cn('p-2 rounded-lg border', styles.bg, styles.border)}>
            <AlertTriangle className={cn('w-4 h-4', styles.text)} />
          </div>
          <div>
            <span className={cn('text-[10px] font-bold px-2 py-0.5 rounded-full border', styles.badge)}>
              {item.priority}
            </span>
            <h3 className="text-sm font-semibold text-[var(--text)] mt-1">{item.label}</h3>
          </div>
        </div>

        <p className="text-xs text-[var(--text-mute)] leading-relaxed mb-3">{item.description}</p>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-[var(--bg-elev)] rounded-lg p-2">
            <div className="text-[var(--text-mute)] text-[10px] mb-0.5">Probability</div>
            <div className="font-semibold text-[var(--text)]">{item.probability}</div>
          </div>
          <div className="bg-[var(--bg-elev)] rounded-lg p-2">
            <div className="text-[var(--text-mute)] text-[10px] mb-0.5">Impact</div>
            <div className="font-semibold text-[var(--text)]">{item.impact}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface RiskBadgeProps {
  item: RiskItem
  onClick: () => void
}

function RiskBadge({ item, onClick }: RiskBadgeProps) {
  const styles = PRIORITY_STYLES[item.priority]
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border cursor-pointer transition-all duration-150 hover:scale-105 hover:shadow-lg text-left leading-tight',
        styles.badge
      )}
      aria-label={`${item.priority}: ${item.label}`}
      title={item.description}
    >
      {item.label}
    </button>
  )
}

export function RiskMatrix() {
  const [selectedRisk, setSelectedRisk] = useState<RiskItem | null>(null)

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedRisk(null)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const getItems = (prob: RiskProbability, impact: RiskImpact): RiskItem[] =>
    RISK_ITEMS.filter(r => r.probability === prob && r.impact === impact)

  const counts: Record<RiskPriority, number> = {
    P0: RISK_ITEMS.filter(r => r.priority === 'P0').length,
    P1: RISK_ITEMS.filter(r => r.priority === 'P1').length,
    P2: RISK_ITEMS.filter(r => r.priority === 'P2').length,
    P3: RISK_ITEMS.filter(r => r.priority === 'P3').length,
  }

  return (
    <section className="card flex flex-col gap-3" aria-label="Risk Matrix">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest">
            Risk Matrix
          </h2>
          <p className="text-xs text-[var(--text-mute)] mt-0.5">
            {RISK_ITEMS.length} risk scenarios &middot; click to view details
          </p>
        </div>
        <div className="flex gap-2">
          {(Object.entries(counts) as [RiskPriority, number][]).map(([p, count]) => (
            <div key={p} className="flex items-center gap-1">
              <span
                className={cn(
                  'text-[10px] font-bold px-1.5 py-0.5 rounded border',
                  PRIORITY_STYLES[p].badge
                )}
              >
                {p}
              </span>
              <span className="text-[10px] text-[var(--text-mute)]">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Matrix grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[480px]">
          {/* Column headers (Probability) */}
          <div className="grid grid-cols-[80px_1fr_1fr_1fr] gap-1 mb-1">
            <div />
            {PROBABILITIES.map(prob => (
              <div key={prob} className="text-center text-[10px] font-semibold text-[var(--text-mute)] py-1">
                {prob}
              </div>
            ))}
          </div>

          {/* Rows (Impact descending: Critical → Minor) */}
          <div className="flex gap-1">
            {/* Row labels */}
            <div className="flex flex-col gap-1 w-20 shrink-0">
              <div className="text-[10px] text-[var(--text-mute)] text-center mb-1">
                Impact →<br />Prob ↓
              </div>
              {IMPACTS.map(impact => (
                <div
                  key={impact}
                  className="flex items-center justify-end pr-2 text-[10px] font-semibold text-[var(--text-mute)]"
                  style={{ minHeight: '80px' }}
                >
                  {impact}
                </div>
              ))}
            </div>

            {/* Cells */}
            <div className="flex-1 grid grid-cols-3 gap-1">
              {IMPACTS.map(impact =>
                PROBABILITIES.map(prob => {
                  const items = getItems(prob, impact)
                  const cellKey = `${prob}-${impact}`
                  return (
                    <div
                      key={cellKey}
                      className={cn(
                        'rounded-lg border p-2 min-h-[80px] flex flex-col gap-1',
                        CELL_BG[cellKey] ?? 'bg-[var(--bg)] border-[var(--border)]'
                      )}
                    >
                      {items.length === 0 ? (
                        <div className="flex-1 flex items-center justify-center">
                          <div className="w-1.5 h-1.5 rounded-full bg-[var(--bg-elev)]" />
                        </div>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {items.map(item => (
                            <RiskBadge
                              key={item.id}
                              item={item}
                              onClick={() => setSelectedRisk(item)}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </div>

          {/* Legend */}
          <div className="flex gap-3 mt-3 flex-wrap items-center">
            <Shield className="w-3 h-3 text-[var(--text-mute)]" />
            {(
              [
                { p: 'P0' as RiskPriority, label: 'Critical — immediate action' },
                { p: 'P1' as RiskPriority, label: 'High — plan mitigation' },
                { p: 'P2' as RiskPriority, label: 'Medium — monitor' },
                { p: 'P3' as RiskPriority, label: 'Low — accept' },
              ]
            ).map(({ p, label }) => (
              <div key={p} className="flex items-center gap-1.5">
                <span className={cn('text-[10px] font-bold px-1.5 py-0.5 rounded border', PRIORITY_STYLES[p].badge)}>
                  {p}
                </span>
                <span className="text-[10px] text-[var(--text-mute)]">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedRisk && (
        <RiskDetailModal
          item={selectedRisk}
          onClose={() => setSelectedRisk(null)}
        />
      )}
    </section>
  )
}
