import { HelpTooltip } from './ui/HelpTooltip'
import type { TimelineEvent } from '../types'

function eventPill(status: string): string {
  if (status === 'completed') return 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30'
  if (status === 'running') return 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
  if (status === 'failed') return 'bg-[var(--neg-soft)] text-[var(--neg)] border-[var(--neg)]/30'
  return 'bg-[var(--bg-sunk)] text-[var(--text-dim)] border-[var(--border)]'
}

export function LoopTimeline({ events }: { events: TimelineEvent[] }) {
  const grouped = events.reduce<Record<number, TimelineEvent[]>>((acc, event) => {
    if (!acc[event.iteration]) acc[event.iteration] = []
    acc[event.iteration].push(event)
    return acc
  }, {})
  const iterations = Object.keys(grouped).map(Number).sort((a, b) => a - b)

  return (
    <div className="space-y-3">
      {iterations.map(iter => {
        const iterEvents = grouped[iter]
        const parentEvents: TimelineEvent[] = []
        const refineChildren: TimelineEvent[] = []
        for (const ev of iterEvents) {
          if (ev.stage.startsWith('rosetta.refine.')) {
            refineChildren.push(ev)
          } else {
            parentEvents.push(ev)
          }
        }

        const nDone = refineChildren.filter(c => c.status === 'completed').length
        const nFailed = refineChildren.filter(c => c.status === 'failed').length
        const nRunning = refineChildren.filter(c => c.status === 'running').length
        const nTotal = refineChildren.length

        return (
          <details key={iter} className="border border-[var(--border)] rounded-lg p-3" open={iter === iterations[iterations.length - 1]}>
            <summary className="cursor-pointer text-xs text-[var(--text-mute)] font-semibold mb-2 flex items-center gap-1.5">
              Iteration {iter}
              <HelpTooltip title="Loop Timeline">
                <p>각 iteration의 루프 실행 타임라인입니다.</p>
                <p>단계별 소요 시간과 전체 진행 상황을 시각적으로 확인할 수 있습니다.</p>
              </HelpTooltip>
              {nTotal > 0 && (
                <span className="ml-2 text-[10px] text-[var(--text-mute)] font-normal">
                  ({nDone}/{nTotal} docked{nFailed > 0 ? `, ${nFailed} failed` : ''}{nRunning > 0 ? `, ${nRunning} running` : ''})
                </span>
              )}
            </summary>
            <div className="space-y-1 mt-2">
              {parentEvents.map((event, idx) => {
                const isRefineParent = event.stage === 'rosetta.refine'
                return (
                  <div key={`${event.ts}-${idx}`}>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-[var(--text-mute)] select-none">├─</span>
                      <span className={`px-2 py-0.5 rounded-full border font-semibold text-[10px] ${eventPill(event.status)}`}>
                        {event.status.toUpperCase()}
                      </span>
                      <span className="text-[var(--text-mute)] font-mono">{event.stage}</span>
                      {event.message && <span className="text-[var(--text-mute)] truncate max-w-[400px]">{event.message}</span>}
                    </div>
                    {isRefineParent && refineChildren.length > 0 && (
                      <div className="ml-6 mt-1 space-y-0.5">
                        {refineChildren.map((child, cidx) => {
                          const candId = child.stage.replace('rosetta.refine.', '')
                          const isLast = cidx === refineChildren.length - 1
                          return (
                            <div key={`${child.ts}-${cidx}`} className="flex items-center gap-2 text-xs">
                              <span className="text-[var(--text-mute)] select-none">{isLast ? '└─' : '├─'}</span>
                              <span className={`px-1.5 py-0.5 rounded-full border font-semibold text-[10px] ${eventPill(child.status)}`}>
                                {child.status === 'completed' ? '✓' : child.status === 'failed' ? '✗' : child.status === 'running' ? '⟳' : '·'}
                              </span>
                              <span className="text-[var(--text-mute)] font-mono text-[10px]">{candId}</span>
                              {child.message && (
                                <span className={`truncate max-w-[350px] text-[10px] ${
                                  child.status === 'failed' ? 'text-[var(--neg)]' : child.status === 'completed' ? 'text-[var(--pos)]/70' : 'text-[var(--text-mute)]'
                                }`}>
                                  {child.message.replace(`${candId}: `, '')}
                                </span>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </details>
        )
      })}
    </div>
  )
}
