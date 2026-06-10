import type { SelectivityResult } from '../../hooks/useSelectivity'
import { OFFTARGET_RECEPTORS } from '../../hooks/useSelectivity'

interface Props { candidates: SelectivityResult[]; onRowClick: (c: SelectivityResult) => void }

function DdgCell({ ddg, status, failReason }: { ddg: number | null; status: string; failReason?: string }) {
  if (status === 'pending') return <span className="text-[var(--text-dim)] text-[10px]">...</span>
  if (status === 'failed' || ddg === null) {
    return (
      <span className="text-[var(--neg)]/70 text-[10px]" title={failReason ?? 'Docking failed'}>
        N/A
      </span>
    )
  }
  if (ddg === 0.0) {
    return <span className="text-[var(--text-dim)] text-[10px]" title="No binding detected">0.00</span>
  }
  const color = ddg < -10 ? 'text-[var(--neg)]' : ddg < -3 ? 'text-[var(--warn)]' : 'text-[var(--pos)]'
  return <span className={`${color} text-[10px] tabular-nums`}>{ddg.toFixed(2)}</span>
}

function TierBadge({ tier, passed }: { tier: number; passed: boolean }) {
  if (passed) {
    const colors = tier >= 3 ? 'bg-[var(--pos-soft)] text-[var(--pos)]' : 'bg-[var(--pos-soft)] text-[var(--pos)]'
    return <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${colors}`}>T{tier} PASS</span>
  }
  return <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-[var(--neg-soft)] text-[var(--neg)]">T{tier} FAIL</span>
}

export function SelectivityTable({ candidates, onRowClick }: Props) {
  return (
    <div className="rounded-xl border border-[var(--border)] overflow-x-auto">
      <table className="w-full text-xs">
        <thead className="bg-[var(--bg)]">
          <tr className="border-b border-[var(--border)]">
            <th className="px-3 py-2 text-left text-[10px] text-[var(--text-dim)] whitespace-nowrap">ID</th>
            <th className="px-3 py-2 text-left text-[10px] text-[var(--text-dim)]">Sequence</th>
            <th className="px-3 py-2 text-right text-[10px] text-[var(--accent)] whitespace-nowrap">SSTR2 ΔG</th>
            {OFFTARGET_RECEPTORS.map(r => (
              <th key={r} className="px-3 py-2 text-right text-[10px] text-[var(--text-dim)] whitespace-nowrap">
                {r.toUpperCase()} ΔG
              </th>
            ))}
            <th className="px-3 py-2 text-right text-[10px] text-[var(--text-dim)] whitespace-nowrap">WSM</th>
            <th className="px-3 py-2 text-center text-[10px] text-[var(--text-dim)]">Tier</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map(c => (
            <tr key={c.candidate_id} onClick={() => onRowClick(c)} className="border-b border-[var(--border)] hover:bg-[var(--bg-sunk)] cursor-pointer">
              <td className="px-3 py-1.5 font-mono text-[var(--text-mute)] text-[10px] whitespace-nowrap">{c.candidate_id}</td>
              <td className="px-3 py-1.5 font-mono text-[var(--text-dim)] text-[10px] max-w-[120px] truncate">{c.sequence}</td>
              <td className="px-3 py-1.5 text-right tabular-nums text-[10px] text-[var(--accent)] font-semibold">
                {(c.sstr2_ddg ?? 0).toFixed(2)}
              </td>
              {OFFTARGET_RECEPTORS.map(r => {
                const d = c.receptorDetails?.[r]
                return (
                  <td key={r} className="px-3 py-1.5 text-right">
                    {d ? (
                      <DdgCell ddg={d.ddg} status={d.status} failReason={d.failReason} />
                    ) : (
                      <span className="text-[var(--text-dim)] text-[10px]">-</span>
                    )}
                  </td>
                )
              })}
              <td className={`px-3 py-1.5 text-right tabular-nums text-[10px] font-semibold ${
                (c.selectivity_margin ?? 0) >= 10 ? 'text-[var(--pos)]' : (c.selectivity_margin ?? 0) >= 5 ? 'text-[var(--pos)]' : 'text-[var(--warn)]'
              }`}>
                {(c.selectivity_margin ?? 0).toFixed(2)}
              </td>
              <td className="px-3 py-1.5 text-center">
                <TierBadge tier={c.tier} passed={c.gate_pass} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
