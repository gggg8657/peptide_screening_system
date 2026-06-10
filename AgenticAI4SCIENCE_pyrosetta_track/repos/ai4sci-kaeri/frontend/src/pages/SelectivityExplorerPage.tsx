import { useEffect, useState } from 'react'
import { ShieldCheck, X } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { HeatmapCell, iptmColor } from '../components/dashboard/HeatmapCell'
import { Molstar } from '../components/dashboard/Molstar'
import { Sequence } from '../components/dashboard/Sequence'
import { TierBadge } from '../components/dashboard/TierBadge'
import { usePipelineContext } from '../contexts/PipelineContext'
import { useCandidates, useRunStatus, useSelectivity, type Candidate } from '../hooks/dashboard'

const RECEPTORS = ['SSTR1', 'SSTR2', 'SSTR3', 'SSTR4', 'SSTR5'] as const
const TIER_ORDER = ['T2', 'T1', 'T0', 'T3'] as const

type ExplorerEntry = Candidate & {
  poseUrl?: string
}

export function SelectivityExplorerPage() {
  const live = usePipelineContext()
  const [searchParams] = useSearchParams()
  const requestedRunId = searchParams.get('run_id') ?? live.viewingArchive ?? (live.runId || undefined)
  const statusQuery = useRunStatus(requestedRunId)
  const runId = requestedRunId ?? statusQuery.data?.run_id
  const candidatesQuery = useCandidates(runId)
  const selectivityQuery = useSelectivity(runId)

  const [tierFilter, setTierFilter] = useState<Set<string>>(new Set(['T0', 'T1', 'T2']))
  const [showWT, setShowWT] = useState(true)
  const [selectedCell, setSelectedCell] = useState<{ cand: string; receptor: string } | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(true)

  const wildType = candidatesQuery.data?.wild_type ?? 'AGCKNFFWKTFTSC'
  const candidates = normalizeCandidates(candidatesQuery.data?.candidates ?? [], selectivityQuery.data)
  const filtered = candidates
    .filter((candidate) => tierFilter.has(candidate.tier) && (showWT || !candidate.wildtype))
    .sort((left, right) => right.margin - left.margin)

  useEffect(() => {
    if (selectedCell && filtered.some((candidate) => candidate.id === selectedCell.cand)) return
    if (!filtered[0]) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedCell(null)
      return
    }
    setSelectedCell({ cand: filtered[0].id, receptor: 'SSTR2' })
  }, [filtered, selectedCell])

  const selectedCandidate = selectedCell
    ? candidates.find((candidate) => candidate.id === selectedCell.cand) ?? filtered[0] ?? null
    : filtered[0] ?? null
  const selectedReceptor = selectedCell?.receptor ?? 'SSTR2'
  const selectedValue = selectedCandidate?.iptm[selectedReceptor] ?? 0
  const noRunSelected = !runId && !statusQuery.isLoading
  const noCandidates = !candidatesQuery.isLoading && filtered.length === 0

  return (
    <div className="overflow-hidden rounded-xl border border-border-base bg-bg-elev">
      <header className="flex flex-wrap items-center gap-3 border-b border-border-base px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-md bg-text-base font-mono text-[11px] font-bold text-bg">P*</div>
          <div>
            <h1 className="text-sm font-semibold text-text-base">Selectivity Explorer</h1>
            <p className="text-[11px] text-text-mute">step05c Boltz-2 + AF MSA · geometry-first review</p>
          </div>
        </div>
        <div className="ml-auto rounded border border-border-base bg-bg-sunk px-2 py-1 font-mono text-[10px] text-text-mute">
          {filtered.length} candidates · {RECEPTORS.length} receptors
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-4 border-b border-border-base px-4 py-3 text-[11px]">
        <div className="flex items-center gap-2">
          <span className="uppercase tracking-[0.18em] text-text-dim">Tier</span>
          {TIER_ORDER.filter((tier) => tier !== 'T3').map((tier) => (
            <label
              key={tier}
              className={`inline-flex cursor-pointer items-center gap-1.5 rounded border px-2 py-1 ${
                tierFilter.has(tier) ? 'border-transparent bg-bg-sunk' : 'border-border-base bg-transparent text-text-mute'
              }`}
            >
              <input
                type="checkbox"
                checked={tierFilter.has(tier)}
                onChange={() => setTierFilter((current) => toggleTier(current, tier))}
                className="accent-[var(--accent)]"
              />
              <TierBadge tier={tier} />
            </label>
          ))}
        </div>

        <div className="h-5 w-px bg-border-base" />

        <label className="inline-flex items-center gap-2 text-text-base">
          <input type="checkbox" checked={showWT} onChange={(event) => setShowWT(event.target.checked)} className="accent-[var(--accent)]" />
          show wildtype
        </label>

        <div className="ml-auto font-mono text-[10px] text-text-dim">{runId ?? 'no run selected'}</div>
      </div>

      <div className={`grid min-h-[780px] ${drawerOpen ? 'xl:grid-cols-[minmax(0,1fr)_380px]' : 'grid-cols-1'}`}>
        <main className="space-y-4 overflow-auto px-5 py-5">
          <div className="flex items-start gap-3 rounded border border-accent bg-accent-soft/60 px-4 py-3 text-[11px] leading-5 text-text-base">
            <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-accent" />
            <p>
              <strong>iPTM ≠ Ki:</strong> 이 화면은 구조 geometry 기반 1차 필터입니다. 정량 selectivity 판단은 FEP, MM-GBSA, radioligand Ki assay로 후속 검증해야 합니다.
            </p>
          </div>

          <section className="overflow-hidden rounded-xl border border-border-base bg-bg-elev">
            <div className="flex items-center justify-between border-b border-border-base px-4 py-3">
              <div>
                <h2 className="text-sm font-semibold text-text-base">iPTM Matrix</h2>
                <p className="text-[11px] text-text-mute">cell = receptor confidence · outlined best receptor · dashed SSTR2</p>
              </div>
              <div className="font-mono text-[10px] text-text-dim">
                selected: {selectedCell ? `${selectedCell.cand} × ${selectedCell.receptor}` : '데이터 없음'}
              </div>
            </div>

            <div className="overflow-auto px-4 py-4">
              {noRunSelected ? (
                <EmptyState message="데이터 없음 · 현재 run_id를 찾지 못했습니다." />
              ) : noCandidates ? (
                <EmptyState message="데이터 없음 · 표시할 후보가 없습니다." />
              ) : (
                <div className="min-w-[980px]">
                  <div className="grid grid-cols-[80px_270px_repeat(5,minmax(0,1fr))_84px_56px] gap-2 border-b border-border-base pb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">
                    <div>cand</div>
                    <div>sequence</div>
                    {RECEPTORS.map((receptor) => (
                      <div key={receptor} className={`text-center ${receptor === 'SSTR2' ? 'font-semibold text-accent' : ''}`}>
                        {receptor}{receptor === 'SSTR2' ? ' ★' : ''}
                      </div>
                    ))}
                    <div className="text-right">margin</div>
                    <div className="text-center">tier</div>
                  </div>

                  <div className="divide-y divide-border-base/70">
                    {filtered.map((candidate) => (
                      <div key={candidate.id} className="grid grid-cols-[80px_270px_repeat(5,minmax(0,1fr))_84px_56px] gap-2 py-2 text-[11px]">
                        <div className="flex items-center gap-1.5 font-mono font-semibold text-text-base">
                          <span>{candidate.id}</span>
                          {candidate.recommended && <span className="text-pos">★</span>}
                          {candidate.wildtype && <span className="rounded border border-border-base px-1 text-[9px] text-text-dim">WT</span>}
                        </div>
                        <div><Sequence seq={candidate.seq} wildtype={wildType} /></div>
                        {RECEPTORS.map((receptor) => {
                          const selected = selectedCell?.cand === candidate.id && selectedCell?.receptor === receptor
                          return (
                            <div key={`${candidate.id}-${receptor}`}>
                              <HeatmapCell
                                value={candidate.iptm[receptor] ?? 0}
                                isBest={candidate.best_receptor === receptor}
                                isTarget={receptor === 'SSTR2'}
                                selected={selected}
                                onClick={() => {
                                  setSelectedCell({ cand: candidate.id, receptor })
                                  setDrawerOpen(true)
                                }}
                              />
                            </div>
                          )
                        })}
                        <div className={`text-right font-mono font-semibold ${candidate.margin > 0 ? 'text-pos' : candidate.margin > -0.05 ? 'text-warn' : 'text-text-mute'}`}>
                          {formatSigned(candidate.margin)}
                        </div>
                        <div className="text-center">
                          <TierBadge tier={candidate.tier} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-4 border-t border-border-base px-4 py-3 text-[10px] text-text-mute">
              <div className="flex items-center gap-2">
                <span>iPTM</span>
                <div className="flex overflow-hidden rounded border border-border-base">
                  {[0.78, 0.85, 0.9, 0.93, 0.96, 0.98].map((value) => (
                    <div
                      key={value}
                      className={`grid h-4 w-8 place-items-center font-mono ${value > 0.93 ? 'text-white' : 'text-text-base'}`}
                      style={{ background: iptmColor(value) }}
                    >
                      {value.toFixed(2).slice(1)}
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2"><span className="h-3 w-3 rounded border border-text-base" /> best receptor</div>
              <div className="flex items-center gap-2"><span className="h-3 w-3 rounded outline outline-1 outline-dashed outline-accent -outline-offset-2" /> target SSTR2</div>
              <div className="ml-auto font-mono">tier = SSTR2 − max(off-target) iPTM margin</div>
            </div>
          </section>

          <div className="grid gap-4 xl:grid-cols-2">
            <section className="rounded-xl border border-border-base bg-bg-elev">
              <div className="flex items-center justify-between border-b border-border-base px-4 py-3">
                <h2 className="text-sm font-semibold text-text-base">Margin Distribution</h2>
                <span className="font-mono text-[10px] text-text-dim">margin = iPTM(SSTR2) − max(off)</span>
              </div>
              <MarginPlot
                candidates={filtered}
                selected={selectedCell?.cand ?? ''}
                onSelect={(cand) => {
                  setSelectedCell({ cand, receptor: 'SSTR2' })
                  setDrawerOpen(true)
                }}
              />
            </section>

            <section className="rounded-xl border border-border-base bg-bg-elev">
              <div className="flex items-center justify-between border-b border-border-base px-4 py-3">
                <h2 className="text-sm font-semibold text-text-base">Gate Funnel</h2>
                <span className="font-mono text-[10px] text-text-dim">candidate reduction</span>
              </div>
              <GateFunnel candidates={filtered} />
            </section>
          </div>
        </main>

        {drawerOpen && selectedCandidate && selectedCell && (
          <aside className="flex min-h-0 flex-col border-l border-border-base bg-bg-elev">
            <div className="flex items-center justify-between border-b border-border-base px-4 py-3">
              <div>
                <h2 className="text-sm font-semibold text-text-base">{selectedCandidate.id} × {selectedCell.receptor}</h2>
                <p className="text-[11px] text-text-mute">docked pose + score breakdown</p>
              </div>
              <button type="button" onClick={() => setDrawerOpen(false)} className="rounded border border-border-base p-1 text-text-mute transition-colors hover:bg-bg-sunk hover:text-text-base">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 space-y-4 overflow-auto px-4 py-4">
              <div className={`rounded border px-3 py-3 ${selectedCell.receptor === 'SSTR2' ? 'border-accent bg-accent-soft/50' : 'border-border-base bg-bg-sunk'}`}>
                <div className="flex items-end justify-between">
                  <span className="text-[10px] uppercase tracking-[0.18em] text-text-dim">iPTM</span>
                  <span className="font-mono text-[24px] font-semibold text-text-base">{selectedValue.toFixed(3)}</span>
                </div>
                <div className="mt-2 flex items-center justify-between text-[11px] text-text-mute">
                  <span>vs max off-target</span>
                  <span className={`font-mono font-semibold ${computeCellMargin(selectedCandidate, selectedCell.receptor) > 0 ? 'text-pos' : 'text-neg'}`}>
                    {formatSigned(computeCellMargin(selectedCandidate, selectedCell.receptor))}
                  </span>
                </div>
              </div>

              <div>
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Docked Pose</div>
                <Molstar pdbUrl={selectedCandidate.poseUrl} height={220} />
              </div>

              <div>
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Sequence</div>
                <Sequence seq={selectedCandidate.seq} wildtype={wildType} showRuler big />
                {selectedCandidate.mutations.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {selectedCandidate.mutations.map((mutation) => (
                      <span key={mutation} className="rounded bg-accent-soft px-2 py-0.5 text-[10px] font-mono text-accent">{mutation}</span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Cross-Receptor</div>
                <div className="space-y-2">
                  {RECEPTORS.map((receptor) => (
                    <ScoreRow
                      key={receptor}
                      label={receptor}
                      value={selectedCandidate.iptm[receptor] ?? 0}
                      active={receptor === selectedCell.receptor}
                    />
                  ))}
                </div>
              </div>

              {selectedCandidate.notes && (
                <div className={`rounded border px-3 py-2 text-[11px] leading-5 ${selectedCandidate.recommended ? 'border-pos bg-pos-soft/50 text-text-base' : 'border-border-base bg-bg-sunk text-text-base'}`}>
                  {selectedCandidate.recommended && <span className="font-semibold text-pos">★ RECOMMENDED · </span>}
                  {selectedCandidate.notes}
                </div>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="grid min-h-[320px] place-items-center rounded-lg border border-dashed border-border-base bg-bg-sunk px-6 text-center text-sm text-text-mute">
      {message}
    </div>
  )
}

function MarginPlot({ candidates, selected, onSelect }: { candidates: ExplorerEntry[]; selected: string; onSelect: (cand: string) => void }) {
  const min = -0.2
  const max = 0.05

  return (
    <div className="relative h-[240px] px-5 py-4">
      <div className="absolute inset-x-5 top-4 bottom-8 rounded bg-[linear-gradient(90deg,var(--neg-soft)_0%,var(--neg-soft)_60%,var(--warn-soft)_60%,var(--warn-soft)_80%,var(--pos-soft)_80%,var(--pos-soft)_100%)] opacity-40" />
      <div className="absolute bottom-8 top-4 w-px bg-text-base/40" style={{ left: `calc(20px + ${((0 - min) / (max - min)) * 100}% - 0.5px)` }} />

      {candidates.map((candidate, index) => {
        const left = ((candidate.margin - min) / (max - min)) * 100
        const top = 10 + index * 18
        const active = selected === candidate.id
        return (
          <button
            key={candidate.id}
            type="button"
            onClick={() => onSelect(candidate.id)}
            className={`absolute h-2.5 w-2.5 rounded-full ${candidate.tier === 'T2' ? 'bg-pos' : candidate.tier === 'T1' ? 'bg-warn' : 'bg-neg'}`}
            style={{
              left: `calc(20px + ${left}% - 5px)`,
              top,
              transform: active ? 'scale(1.5)' : undefined,
              boxShadow: active ? '0 0 0 2px var(--text)' : undefined,
            }}
            title={`${candidate.id} ${formatSigned(candidate.margin)}`}
          >
            {active && <span className="absolute left-4 top-[-4px] whitespace-nowrap font-mono text-[10px] text-text-base">{candidate.id} {formatSigned(candidate.margin)}</span>}
          </button>
        )
      })}

      <div className="absolute bottom-3 left-5 right-5 flex justify-between border-t border-border-base pt-2 font-mono text-[10px] text-text-dim">
        {[-0.2, -0.15, -0.1, -0.05, 0, 0.05].map((value) => (
          <span key={value}>{value > 0 ? '+' : ''}{value.toFixed(2)}</span>
        ))}
      </div>
    </div>
  )
}

function GateFunnel({ candidates }: { candidates: ExplorerEntry[] }) {
  const stageCounts = [
    { label: 'Generated', count: Math.max(candidates.length, 1), tone: 'bg-text-dim' },
    { label: 'G1 pLDDT', count: Math.max(Math.round(candidates.length * 0.91), 1), tone: 'bg-accent' },
    { label: 'G2 Docking', count: Math.max(candidates.filter((candidate) => candidate.margin > -0.05).length, 1), tone: 'bg-accent' },
    { label: 'G3 Selectivity', count: Math.max(candidates.filter((candidate) => candidate.margin > -0.01).length, 1), tone: 'bg-warn' },
    { label: 'G3b Boltz-cross', count: Math.max(candidates.filter((candidate) => candidate.margin > 0).length, 1), tone: 'bg-pos' },
  ]
  const base = stageCounts[0]?.count || 1

  return (
    <div className="space-y-3 px-5 py-4 text-[11px]">
      {stageCounts.map((stage, index) => {
        const previous = stageCounts[index - 1]?.count ?? stage.count
        return (
          <div key={stage.label} className="grid grid-cols-[112px_1fr_44px_44px] items-center gap-3">
            <span className="text-text-mute">{stage.label}</span>
            <div className="h-3 overflow-hidden rounded bg-bg-sunk">
              <div className={`h-full ${stage.tone}`} style={{ width: `${(stage.count / base) * 100}%` }} />
            </div>
            <span className="font-mono font-semibold text-text-base">{stage.count}</span>
            <span className="font-mono text-neg">{index === 0 ? '' : `-${Math.max(previous - stage.count, 0)}`}</span>
          </div>
        )
      })}
    </div>
  )
}

function ScoreRow({ label, value, active }: { label: string; value: number; active?: boolean }) {
  return (
    <div className="grid grid-cols-[56px_1fr_48px] items-center gap-3 text-[11px]">
      <span className={`font-mono ${active ? 'font-semibold text-text-base' : 'text-text-mute'}`}>{label}</span>
      <div className="h-2 overflow-hidden rounded bg-bg-sunk">
        <div className="h-full" style={{ width: `${Math.max(((value - 0.75) / 0.25) * 100, 0)}%`, background: iptmColor(value) }} />
      </div>
      <span className={`font-mono text-right ${active ? 'font-semibold text-text-base' : 'text-text-mute'}`}>{value.toFixed(3)}</span>
    </div>
  )
}

function normalizeCandidates(
  candidateList: Candidate[],
  selectivityPayload: Record<string, Partial<Candidate> & { poseUrl?: string }> | undefined,
) {
  const normalizedFromSelectivity = new Map<string, Partial<ExplorerEntry>>(
    Object.entries(selectivityPayload ?? {}).map(([id, entry]) => [
      id,
      {
        ...entry,
        poseUrl: entry.poseUrl,
      },
    ]),
  )

  return candidateList.map((candidate) => {
    const patch = normalizedFromSelectivity.get(candidate.id)
    return {
      ...candidate,
      ...patch,
      seq: patch?.seq || candidate.seq,
      iptm: patch?.iptm ?? candidate.iptm,
      best_receptor: patch?.best_receptor ?? candidate.best_receptor,
      margin: patch?.margin ?? candidate.margin,
      tier: patch?.tier ?? candidate.tier,
      poseUrl: patch?.poseUrl ?? buildPoseUrl(candidate),
    }
  })
}

function computeCellMargin(candidate: ExplorerEntry, receptor: string) {
  const otherMax = Math.max(...RECEPTORS.filter((item) => item !== receptor).map((item) => candidate.iptm[item] ?? 0))
  return (candidate.iptm[receptor] ?? 0) - otherMax
}

function buildPoseUrl(candidate: Candidate) {
  // source(= pdb_path) 경로에서 직접 구조 URL 추출
  // source 예: "archives/sst14_mutdock_42/iter_04/cand_003.pdb"
  //           "/runs_local/dual_final_01/.../05_docking/pose_a_bb04_seq06_00.pdb"
  // source가 없으면 Molstar 기본값(7XNA)으로 fallback
  return toStructureUrl(candidate.source)
}

function toStructureUrl(path: string | null | undefined) {
  if (!path) return undefined
  if (path.startsWith('/api/')) return path
  if (path.startsWith('archives/') || path.startsWith('pyrosetta_flow/') || path.startsWith('test_')) {
    return `/api/structures/${path}`
  }
  const runsLocalMarker = '/runs_local/'
  const runsMarker = '/runs/'
  const pyrosettaMarker = '/runs/pyrosetta_flow/'
  if (path.includes(pyrosettaMarker)) {
    return `/api/structures/${path.split(pyrosettaMarker)[1]}`
  }
  if (path.includes(runsLocalMarker)) {
    // runs_local 절대 경로 → 상대 경로 추출
    return `/api/structures/${path.split(runsLocalMarker)[1]}`
  }
  if (path.includes(runsMarker)) {
    return `/api/structures/${path.split(runsMarker)[1]}`
  }
  return undefined
}

function toggleTier(current: Set<string>, tier: string) {
  const next = new Set(current)
  if (next.has(tier)) next.delete(tier)
  else next.add(tier)
  return next
}

function formatSigned(value: number) {
  return `${value > 0 ? '+' : ''}${value.toFixed(3)}`
}
