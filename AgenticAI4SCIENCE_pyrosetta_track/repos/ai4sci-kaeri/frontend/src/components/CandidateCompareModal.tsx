import { useEffect, useRef } from 'react'
import { X, Download, Dna } from 'lucide-react'
import { cn } from '../lib/utils'
import { useFocusTrap } from '../hooks/useFocusTrap'
import type { Candidate } from '../types'

/**
 * CandidateCompareModal
 *
 * 2~3개 후보를 side-by-side로 비교.
 * - 서열 diff 하이라이트 (위치별 AA 차이 강조)
 * - Boltz iPTM / stability / ddG / protease sites 비교 행
 * - 접근성: focus trap + Escape 키 닫기
 */

/* ─── 타입 ─── */
interface ExtendedCandidate extends Candidate {
  iptm?: number
  // instability_index, gravy: Candidate 베이스에 이미 정의 (types/index.ts P05)
  nephrotox?: string
  hl_score?: number | null
  protease_sites?: number
}

interface CandidateCompareModalProps {
  candidates: ExtendedCandidate[]
  onClose: () => void
}

/* ─── 서열 diff: 기준 서열(첫 번째)과 비교해 다른 위치에 highlight ─── */
function SequenceDiff({
  sequence,
  reference,
}: {
  sequence: string
  reference: string
}) {
  return (
    <span className="font-mono text-[11px] tracking-widest" aria-label={sequence}>
      {sequence.split('').map((aa, i) => {
        const isDiff = reference[i] !== undefined && aa !== reference[i]
        return (
          <span
            key={i}
            className={cn(
              isDiff
                ? 'bg-[var(--warn-soft)] text-[var(--warn)] rounded px-0.5'
                : 'text-[var(--text-mute)]',
            )}
            title={isDiff ? `위치 ${i + 1}: ${reference[i]} → ${aa}` : undefined}
          >
            {aa}
          </span>
        )
      })}
    </span>
  )
}

/* ─── 비교 행 ─── */
function CompareRow({
  label,
  values,
  formatter,
  colorFn,
}: {
  label: string
  values: (string | number | null | undefined)[]
  formatter?: (v: string | number | null | undefined) => string
  colorFn?: (v: string | number | null | undefined) => string
}) {
  const fmt = formatter ?? ((v) => (v == null ? '—' : String(v)))
  return (
    <tr className="border-b border-[var(--border)]/30 hover:bg-[var(--bg-elev)]/30 transition-colors">
      <td className="px-3 py-2 text-[10px] text-[var(--text-mute)] font-medium whitespace-nowrap w-32">
        {label}
      </td>
      {values.map((v, i) => (
        <td
          key={i}
          className={cn(
            'px-3 py-2 text-xs font-mono text-center',
            colorFn ? colorFn(v) : 'text-[var(--text-mute)]',
          )}
        >
          {fmt(v)}
        </td>
      ))}
    </tr>
  )
}

/* ─── iPTM 색상 ─── */
function iptmColor(v: string | number | null | undefined) {
  if (v == null || typeof v !== 'number') return 'text-[var(--text-mute)]'
  if (v >= 0.92) return 'text-[var(--pos)] font-semibold'
  if (v >= 0.85) return 'text-[var(--warn)]'
  return 'text-[var(--text-mute)]'
}

/* ─── ddG 색상 ─── */
function ddgColor(v: string | number | null | undefined) {
  if (v == null || typeof v !== 'number') return 'text-[var(--text-mute)]'
  if (v <= -8.5) return 'text-[var(--pos)] font-semibold'
  if (v <= -5) return 'text-[var(--warn)]'
  return 'text-[var(--neg)]'
}

/* ─── 메인 컴포넌트 ─── */
export function CandidateCompareModal({
  candidates,
  onClose,
}: CandidateCompareModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null)
  useFocusTrap(dialogRef, true)

  /* Escape 키로 닫기 */
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  /* 스크롤 잠금 */
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  if (candidates.length === 0) return null

  const reference = candidates[0].sequence ?? ''
  const colCount = candidates.length

  /* Export placeholder */
  const handleExport = () => {
    console.warn('[CandidateCompareModal] PDF export: 미구현 (Phase 2)')
    alert('PDF 내보내기는 Phase 2에서 구현 예정입니다.')
  }

  return (
    /* Overlay */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--bg-sunk)]/80 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-label="후보 비교"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Dialog Panel */}
      <div
        ref={dialogRef}
        className="relative w-full max-w-4xl max-h-[90dvh] overflow-hidden
                   rounded-xl border border-[var(--border)] bg-[var(--bg)] shadow-2xl
                   flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--border)]/50 flex-shrink-0">
          <div className="flex items-center gap-2">
            <Dna className="w-4 h-4 text-[var(--accent)]" aria-hidden="true" />
            <h2 className="text-sm font-bold text-[var(--text)]">
              후보 비교 ({colCount}개)
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium
                         bg-[var(--bg-elev)] border border-[var(--border)] text-[var(--text-mute)]
                         hover:bg-[var(--bg-elev)] transition-colors"
              aria-label="PDF로 내보내기 (미구현)"
            >
              <Download className="w-3 h-3" />
              Export PDF
            </button>
            <button
              onClick={onClose}
              className="flex items-center justify-center w-7 h-7 rounded-lg
                         bg-[var(--bg-elev)] border border-[var(--border)] text-[var(--text-mute)]
                         hover:bg-[var(--bg-elev)] hover:text-[var(--text)] transition-colors"
              aria-label="비교 모달 닫기"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto flex-1">
          <table className="w-full text-xs" aria-label="후보 속성 비교 테이블">
            <thead className="sticky top-0 bg-[var(--bg)]/95 backdrop-blur-sm z-10">
              <tr className="border-b border-[var(--border)]/50">
                <th
                  scope="col"
                  className="px-3 py-3 text-left text-[10px] font-semibold text-[var(--text-mute)] uppercase tracking-wider w-32"
                >
                  속성
                </th>
                {candidates.map((c, i) => (
                  <th
                    key={c.id}
                    scope="col"
                    className={cn(
                      'px-3 py-3 text-center text-[10px] font-semibold uppercase tracking-wider',
                      i === 0 ? 'text-[var(--accent)]' : 'text-[var(--text-mute)]',
                    )}
                  >
                    <div>{c.id}</div>
                    {i === 0 && (
                      <div className="text-[9px] font-normal text-[var(--text-dim)] normal-case tracking-normal mt-0.5">
                        (기준)
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {/* 서열 */}
              <tr className="border-b border-[var(--border)]/30 bg-[var(--bg-elev)]/20">
                <td className="px-3 py-3 text-[10px] text-[var(--text-mute)] font-medium">서열</td>
                {candidates.map((c) => (
                  <td key={c.id} className="px-3 py-3 text-center">
                    <SequenceDiff
                      sequence={c.sequence ?? '—'}
                      reference={reference}
                    />
                  </td>
                ))}
              </tr>

              {/* Result */}
              <CompareRow
                label="Result"
                values={candidates.map((c) => c.result)}
                formatter={(v) => String(v ?? '—')}
                colorFn={(v) =>
                  v === 'PASS'
                    ? 'text-[var(--pos)] font-semibold'
                    : v === 'FAIL'
                      ? 'text-[var(--neg)]'
                      : 'text-[var(--text-mute)]'
                }
              />

              {/* ΔΔG */}
              <CompareRow
                label="ΔΔG (kcal/mol)"
                values={candidates.map((c) => c.ddG)}
                formatter={(v) =>
                  typeof v === 'number' ? v.toFixed(2) : '—'
                }
                colorFn={ddgColor}
              />

              {/* Total Score */}
              <CompareRow
                label="Total Score"
                values={candidates.map((c) => c.totalScore)}
                formatter={(v) =>
                  typeof v === 'number' ? v.toFixed(1) : '—'
                }
              />

              {/* Boltz iPTM */}
              <CompareRow
                label="Boltz iPTM"
                values={candidates.map((c) => c.iptm ?? null)}
                formatter={(v) =>
                  typeof v === 'number' ? v.toFixed(4) : '—'
                }
                colorFn={iptmColor}
              />

              {/* HL Score (HEURISTIC) */}
              <CompareRow
                label="HL score ⚠"
                values={candidates.map((c) => c.hl_score ?? null)}
                formatter={(v) =>
                  typeof v === 'number' ? v.toFixed(3) : '—'
                }
              />

              {/* Instability Index */}
              <CompareRow
                label="Instability Idx"
                values={candidates.map((c) => c.instability_index ?? null)}
                formatter={(v) =>
                  v == null ? 'N/A' : typeof v === 'number' ? v.toFixed(1) : '—'
                }
                colorFn={(v) =>
                  typeof v === 'number'
                    ? v < 40
                      ? 'text-[var(--pos)]'
                      : 'text-[var(--neg)]'
                    : 'text-[var(--text-dim)]'
                }
              />

              {/* GRAVY */}
              <CompareRow
                label="GRAVY"
                values={candidates.map((c) => c.gravy ?? null)}
                formatter={(v) =>
                  typeof v === 'number' ? v.toFixed(3) : '—'
                }
                colorFn={(v) =>
                  typeof v === 'number'
                    ? v < 0
                      ? 'text-[var(--accent)]'
                      : 'text-[var(--warn)]'
                    : 'text-[var(--text-mute)]'
                }
              />

              {/* Nephrotoxicity */}
              <CompareRow
                label="Nephrotox"
                values={candidates.map((c) => c.nephrotox ?? null)}
                formatter={(v) => String(v ?? '—')}
                colorFn={(v) =>
                  v === 'Low'
                    ? 'text-[var(--pos)]'
                    : v === 'Moderate'
                      ? 'text-[var(--warn)]'
                      : v === 'High'
                        ? 'text-[var(--neg)]'
                        : 'text-[var(--text-mute)]'
                }
              />

              {/* Protease sites */}
              <CompareRow
                label="Protease sites"
                values={candidates.map((c) => c.protease_sites ?? null)}
                formatter={(v) =>
                  v == null ? '—' : String(v)
                }
                colorFn={(v) =>
                  typeof v === 'number'
                    ? v === 0
                      ? 'text-[var(--pos)]'
                      : v <= 2
                        ? 'text-[var(--warn)]'
                        : 'text-[var(--neg)]'
                    : 'text-[var(--text-mute)]'
                }
              />

              {/* Clash Score */}
              <CompareRow
                label="Clash Score"
                values={candidates.map((c) => c.clashScore)}
                formatter={(v) =>
                  typeof v === 'number' ? v.toFixed(2) : '—'
                }
                colorFn={(v) =>
                  typeof v === 'number'
                    ? v < 5
                      ? 'text-[var(--pos)]'
                      : v < 10
                        ? 'text-[var(--warn)]'
                        : 'text-[var(--neg)]'
                    : 'text-[var(--text-mute)]'
                }
              />
            </tbody>
          </table>

          {/* HEURISTIC 경고 */}
          <div className="px-5 py-3 border-t border-[var(--border)]/30">
            <p className="text-[10px] text-[var(--text-dim)]">
              ⚠ HL score는 후보 <em>상대 순위</em> 부여용 heuristic score입니다.
              임상 반감기 절대값이 아닙니다. in-vitro serum stability assay 미수행.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
