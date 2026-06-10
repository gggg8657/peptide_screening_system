import type { SelectivityResult } from '../../hooks/useSelectivity'

interface Props { candidates: SelectivityResult[]; selectedIds: Set<string> }

export function SelectivityChart({ candidates, selectedIds }: Props) {
  if (candidates.length === 0) return null
  const passCount = candidates.filter(c => c.gate_pass).length
  const failCount = candidates.length - passCount
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-elev)] p-4">
      <h3 className="text-xs font-semibold text-[var(--text-mute)] mb-2">Selectivity Summary</h3>
      <div className="flex items-center gap-4 text-xs">
        <div className="text-[var(--pos)]"><span className="text-lg font-bold">{passCount}</span> PASS</div>
        <div className="text-[var(--neg)]"><span className="text-lg font-bold">{failCount}</span> FAIL</div>
        <div className="flex-1 h-2 bg-[var(--bg-sunk)] rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400" style={{ width: `${candidates.length > 0 ? (passCount / candidates.length) * 100 : 0}%` }} />
        </div>
        <span className="text-[var(--text-dim)] text-[10px]">{candidates.length > 0 ? Math.round((passCount / candidates.length) * 100) : 0}% selective</span>
      </div>
      {selectedIds.size > 0 && <p className="text-[10px] text-[var(--text-dim)] mt-2">{selectedIds.size} selected</p>}
    </div>
  )
}
