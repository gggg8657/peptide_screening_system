import { useEffect, useRef, useState } from 'react'
import { Activity, Bot, CircleAlert, Cpu, Loader2, Radio, Workflow } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { PipelineFlow } from '../components/dashboard/PipelineFlow'
import { HeatmapCell } from '../components/dashboard/HeatmapCell'
import { Sequence } from '../components/dashboard/Sequence'
import { TierBadge } from '../components/dashboard/TierBadge'
import { usePipelineContext } from '../contexts/PipelineContext'
import { useAgentLog, useCandidates, usePipeline, useRunStatus, type AgentEntry, type PipelineResponse, type Silo } from '../hooks/dashboard'

const RECEPTORS = ['SSTR1', 'SSTR2', 'SSTR3', 'SSTR4', 'SSTR5'] as const

export function RunConsolePage() {
  const live = usePipelineContext()
  const [searchParams] = useSearchParams()
  const requestedRunId = searchParams.get('run_id') ?? live.viewingArchive ?? (live.runId || undefined)
  const [silo, setSilo] = useState<Silo>('B')
  const [selectedCand, setSelectedCand] = useState<string | null>(null)
  const [hoverGate, setHoverGate] = useState<string | null>(null)

  const statusQuery = useRunStatus(requestedRunId)
  const runId = requestedRunId ?? statusQuery.data?.run_id
  const log = useAgentLog(runId)
  const pipelineQuery = usePipeline(silo, runId)
  const candidatesQuery = useCandidates(runId)

  const wildType = candidatesQuery.data?.wild_type ?? 'AGCKNFFWKTFTSC'
  const candidates = candidatesQuery.data?.candidates ?? []
  const selectedCandidate = candidates.find((candidate) => candidate.id === selectedCand) ?? candidates[0] ?? null

  useEffect(() => {
    if (!selectedCand && candidates[0]) {
      setSelectedCand(candidates[0].id)
    }
  }, [candidates, selectedCand])

  const pipelineStages = flattenPipeline(pipelineQuery.data)
  const currentStage = pipelineStages.find((stage) => stage.status === 'running') ?? pipelineStages.at(-1) ?? null
  const gateStages = pipelineStages.filter((stage) => stage.gate)
  const generated = computeGeneratedCount(pipelineQuery.data, silo)
  const qcPass = gateStages.find((stage) => stage.id === '04')?.out_count ?? null
  const dockingTop = gateStages.find((stage) => stage.id === '05')?.out_count ?? null
  const liveT2 = candidates.filter((candidate) => candidate.tier === 'T2').length
  const noRunSelected = !runId && !statusQuery.isLoading
  const noCandidates = !candidatesQuery.isLoading && candidates.length === 0

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-4 min-w-0">
        <section className="overflow-hidden rounded-xl border border-border-base bg-bg-elev">
          <div className="flex flex-wrap items-center gap-3 border-b border-border-base px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-md bg-text-base font-mono text-[11px] font-bold text-bg">P*</div>
              <div>
                <h1 className="text-sm font-semibold text-text-base">Run Console</h1>
                <p className="text-[11px] text-text-mute">PRST_N_FM · SSTR2 AI Co-Scientist</p>
              </div>
            </div>
            <div className="ml-auto flex flex-wrap items-center gap-2 text-[11px]">
              <span className="rounded border border-border-base bg-bg-sunk px-2 py-1 font-mono text-text-mute">{runId ?? 'no run selected'}</span>
              <RunStatePill state={statusQuery.data?.state} connected={log.connected} />
            </div>
          </div>

          <div className="grid gap-0 border-b border-border-base lg:grid-cols-[minmax(0,1fr)_280px]">
            <div className="flex flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
              <Meta label="Target" value="SSTR2 · P30874 · 7XNA" />
              <Meta
                label="Silo"
                value={
                  <div className="inline-flex overflow-hidden rounded border border-border-strong">
                    {(['A', 'B', 'A+B'] as const).map((value) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => setSilo(value)}
                        className={`px-3 py-1 text-[11px] transition-colors ${
                          silo === value ? 'bg-text-base text-bg' : 'bg-transparent text-text-mute hover:bg-bg-sunk hover:text-text-base'
                        }`}
                      >
                        {value === 'A' ? 'A · de novo' : value === 'B' ? 'B · mutation' : 'Combined'}
                      </button>
                    ))}
                  </div>
                }
              />
              <Meta label="Iteration" value={`${statusQuery.data?.iteration ?? 0} / ${statusQuery.data?.max_iterations ?? 0}`} />
              <Meta label="LLM" value={statusQuery.data?.llm_model ?? live.llmModel ?? '—'} mono />
              <Meta label="GPU" value={statusQuery.data?.gpus ?? '—'} mono />
              <Meta label="Seed" value={String(statusQuery.data?.seed ?? '—')} mono />
            </div>
            <div className="border-l border-border-base px-4 py-3">
              <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-text-mute">
                <span>{currentStage ? `${currentStage.id} 진행` : 'run progress'}</span>
                <span className="font-mono">{Math.round((statusQuery.data?.progress ?? 0) * 100)}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded bg-bg-sunk">
                <div className="h-full bg-[linear-gradient(90deg,var(--accent)_0%,var(--pos)_100%)]" style={{ width: `${(statusQuery.data?.progress ?? 0) * 100}%` }} />
              </div>
            </div>
          </div>

          <div className="p-4">
            <PipelineFlow silo={silo} runId={runId} selectedStage={currentStage?.id} />
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              <MiniStat label="Generated" value={displayCount(generated)} sub={silo === 'A' ? 'RFdiffusion / MPNN' : silo === 'B' ? 'BLOSUM + dedupe' : 'A + B merged'} />
              <MiniStat label="QC G1 pass" value={displayCount(qcPass)} sub="step04 output" tone="pos" />
              <MiniStat label="Docking top%" value={displayCount(dockingTop)} sub="step05 output" tone="warn" />
              <MiniStat label="T2 후보" value={String(liveT2)} sub={selectedCandidate?.id ?? '—'} tone="pos" />
              <MiniStat label="Log stream" value={String(log.entries.length)} sub={log.connected ? 'SSE connected' : 'reconnecting'} />
            </div>
          </div>
        </section>

        <section className="grid min-h-[420px] overflow-hidden rounded-xl border border-border-base bg-bg-elev xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="min-w-0 border-r border-border-base">
            <div className="flex flex-wrap items-center gap-3 border-b border-border-base px-4 py-3">
              <div>
                <h2 className="text-sm font-semibold text-text-base">Candidates</h2>
                <p className="text-[11px] text-text-mute">run-scoped candidate table · tier / margin / iPTM</p>
              </div>
              <div className="ml-auto text-[11px] text-text-mute">
                {candidatesQuery.isLoading ? 'loading…' : `${candidates.length} candidates`}
              </div>
            </div>
            <div className="overflow-auto">
              {noRunSelected ? (
                <EmptyPanel message="데이터 없음 · 현재 run_id를 찾지 못했습니다." />
              ) : noCandidates ? (
                <EmptyPanel message="데이터 없음 · 이 run에 후보가 없습니다." />
              ) : (
                <table className="w-full min-w-[980px] text-[11px]">
                  <thead className="sticky top-0 z-10 bg-bg-elev">
                    <tr className="border-b border-border-base text-left text-text-dim">
                      <th className="px-4 py-2 font-medium">ID</th>
                      <th className="px-4 py-2 font-medium">Sequence</th>
                      <th className="px-4 py-2 font-medium">Tier</th>
                      <th className="px-4 py-2 font-medium">margin</th>
                      <th className="px-4 py-2 font-medium">SSTR2</th>
                      <th className="px-4 py-2 font-medium">best</th>
                      <th className="px-4 py-2 font-medium">iPTM × 5</th>
                      <th className="px-4 py-2 font-medium">ddG</th>
                      <th className="px-4 py-2 font-medium">source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((candidate) => {
                      const selected = selectedCandidate?.id === candidate.id
                      return (
                        <tr
                          key={candidate.id}
                          onClick={() => setSelectedCand(candidate.id)}
                          className={`cursor-pointer border-b border-border-base/70 transition-colors ${selected ? 'bg-accent-soft/60' : 'hover:bg-bg-sunk'}`}
                        >
                          <td className="px-4 py-2 font-mono font-semibold text-text-base">
                            <div className="flex items-center gap-1.5">
                              <span>{candidate.id}</span>
                              {candidate.recommended && <span className="rounded bg-pos-soft px-1 py-0 text-[9px] text-pos">★</span>}
                              {candidate.wildtype && <span className="rounded border border-border-base px-1 py-0 text-[9px] text-text-dim">WT</span>}
                            </div>
                          </td>
                          <td className="px-4 py-2"><Sequence seq={candidate.seq} wildtype={wildType} /></td>
                          <td className="px-4 py-2"><TierBadge tier={candidate.tier} /></td>
                          <td className={`px-4 py-2 font-mono font-semibold ${candidate.margin > 0 ? 'text-pos' : candidate.margin > -0.05 ? 'text-warn' : 'text-text-mute'}`}>
                            {formatSigned(candidate.margin)}
                          </td>
                          <td className="px-4 py-2 font-mono text-text-base">{candidate.iptm.SSTR2?.toFixed(3) ?? '—'}</td>
                          <td className="px-4 py-2">
                            <span className={`rounded px-2 py-0.5 font-mono text-[10px] ${candidate.best_receptor === 'SSTR2' ? 'bg-pos-soft text-pos' : 'bg-bg-sunk text-text-mute'}`}>
                              {candidate.best_receptor}
                            </span>
                          </td>
                          <td className="px-4 py-2">
                            <div className="flex gap-1">
                              {RECEPTORS.map((receptor) => (
                                <div key={receptor} className="w-6">
                                  <HeatmapCell value={candidate.iptm[receptor] ?? 0} isBest={candidate.best_receptor === receptor} isTarget={receptor === 'SSTR2'} />
                                </div>
                              ))}
                            </div>
                          </td>
                          <td className="px-4 py-2 font-mono text-text-mute">{candidate.ddg != null ? candidate.ddg.toFixed(1) : '—'}</td>
                          <td className="px-4 py-2 font-mono text-text-dim">{candidate.source ?? '—'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          <aside className="flex min-h-0 flex-col">
            <div className="border-b border-border-base px-4 py-3">
              <h2 className="text-sm font-semibold text-text-base">Selected Candidate</h2>
              <p className="text-[11px] text-text-mute">{selectedCandidate?.id ?? '—'}</p>
            </div>
            <div className="flex-1 space-y-4 overflow-auto px-4 py-4">
              {selectedCandidate ? (
                <>
                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Sequence</div>
                    <Sequence seq={selectedCandidate.seq} wildtype={wildType} showRuler big />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <DetailStat label="margin" value={formatSigned(selectedCandidate.margin)} tone={selectedCandidate.margin > 0 ? 'text-pos' : 'text-text-mute'} />
                    <DetailStat label="tier" value={<TierBadge tier={selectedCandidate.tier} />} />
                    <DetailStat label="best receptor" value={<span className="font-mono">{selectedCandidate.best_receptor}</span>} />
                    <DetailStat label="ddG" value={selectedCandidate.ddg != null ? `${selectedCandidate.ddg.toFixed(2)} kcal` : '—'} />
                  </div>

                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">iPTM × receptors</div>
                    <div className="grid grid-cols-5 gap-2">
                      {RECEPTORS.map((receptor) => (
                        <div key={receptor} className="text-center">
                          <div className="mb-1 text-[10px] text-text-mute">{receptor}</div>
                          <HeatmapCell
                            value={selectedCandidate.iptm[receptor] ?? 0}
                            isBest={selectedCandidate.best_receptor === receptor}
                            isTarget={receptor === 'SSTR2'}
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {selectedCandidate.notes && (
                    <div className={`rounded border px-3 py-2 text-[11px] leading-5 ${selectedCandidate.recommended ? 'border-pos bg-pos-soft/50 text-text-base' : 'border-border-base bg-bg-sunk text-text-base'}`}>
                      {selectedCandidate.recommended && <span className="font-semibold text-pos">★ RECOMMENDED · </span>}
                      {selectedCandidate.notes}
                    </div>
                  )}

                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Gate Trail</div>
                    <div className="space-y-2">
                      {gateStages.map((stage) => {
                        const pass = stage.out_count ?? 0
                        const total = stage.in_count ?? pass
                        const ratio = total > 0 ? pass / total : 0
                        return (
                          <button
                            key={stage.id}
                            type="button"
                            onMouseEnter={() => setHoverGate(stage.id)}
                            onMouseLeave={() => setHoverGate((current) => (current === stage.id ? null : current))}
                            className={`w-full rounded border px-3 py-2 text-left transition-colors ${hoverGate === stage.id ? 'border-accent bg-accent-soft/50' : 'border-border-base bg-bg-sunk hover:border-border-strong'}`}
                          >
                            <div className="flex items-center justify-between gap-3">
                              <span className="font-mono text-[11px] font-semibold text-text-base">{stage.id} · {stage.name}</span>
                              <span className="font-mono text-[10px] text-text-mute">{pass}/{total}</span>
                            </div>
                            <div className="mt-1 text-[10px] text-text-mute">{stage.gate}</div>
                            <div className="mt-2 h-1.5 overflow-hidden rounded bg-bg">
                              <div className="h-full bg-pos" style={{ width: `${ratio * 100}%` }} />
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </>
              ) : (
                <EmptyPanel message={candidatesQuery.isLoading ? '후보 로딩 중…' : '표시할 후보가 없습니다.'} />
              )}
            </div>
          </aside>
        </section>
      </div>

      <aside className="flex min-h-[740px] flex-col overflow-hidden rounded-xl border border-border-base bg-bg-elev">
        <div className="flex items-center justify-between border-b border-border-base px-4 py-3">
          <div>
            <h2 className="text-sm font-semibold text-text-base">Agent Log</h2>
            <p className="text-[11px] text-text-mute">SSE stream + recent history</p>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-text-mute">
            <Radio className={`h-3.5 w-3.5 ${log.connected ? 'text-pos' : 'text-warn'}`} />
            <span>{log.connected ? 'connected' : 'retrying'}</span>
          </div>
        </div>
        <AgentSummary entries={log.entries} />
        <AgentLogList entries={log.entries} />
      </aside>
    </div>
  )
}

function AgentSummary({ entries }: { entries: AgentEntry[] }) {
  const lastAgent = entries.at(-1)?.agent ?? '—'
  return (
    <div className="grid grid-cols-3 gap-2 border-b border-border-base px-4 py-3 text-[11px]">
      <SummaryChip icon={<Bot className="h-3.5 w-3.5" />} label="active" value={lastAgent} />
      <SummaryChip icon={<Workflow className="h-3.5 w-3.5" />} label="flow" value="sequential" />
      <SummaryChip icon={<Activity className="h-3.5 w-3.5" />} label="events" value={String(entries.length)} />
    </div>
  )
}

function AgentLogList({ entries }: { entries: AgentEntry[] }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight })
  }, [entries.length])

  if (entries.length === 0) {
    return <EmptyPanel message="에이전트 로그가 아직 없습니다." className="flex-1" />
  }

  return (
    <div ref={ref} className="flex-1 space-y-0.5 overflow-auto px-4 py-3">
      {entries.map((entry, index) => (
        <div key={`${entry.ts}-${index}`} className="grid grid-cols-[64px_72px_1fr] gap-2 border-b border-dashed border-border-base py-2 text-[11px]">
          <span className="font-mono text-text-dim">{formatLogTime(entry.ts)}</span>
          <span className="rounded bg-bg-sunk px-2 py-0.5 text-center font-mono text-[10px] font-semibold text-text-mute">{entry.agent}</span>
          <div>
            <div className={`mb-0.5 text-[10px] uppercase tracking-[0.14em] ${entry.level === 'error' ? 'text-neg' : entry.level === 'warn' ? 'text-warn' : 'text-text-dim'}`}>
              {entry.level}
            </div>
            <p className="leading-5 text-text-base">{entry.text}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

function Meta({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-[0.18em] text-text-dim">{label}</span>
      <span className={`text-[12px] text-text-base ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}

function MiniStat({ label, value, sub, tone }: { label: string; value: string; sub: string; tone?: 'pos' | 'warn' }) {
  return (
    <div className="rounded border border-border-base bg-bg-sunk px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.18em] text-text-dim">{label}</div>
      <div className={`mt-1 font-mono text-[20px] font-semibold leading-none ${tone === 'pos' ? 'text-pos' : tone === 'warn' ? 'text-warn' : 'text-text-base'}`}>
        {value}
      </div>
      <div className="mt-1 text-[10px] text-text-mute">{sub}</div>
    </div>
  )
}

function DetailStat({ label, value, tone }: { label: string; value: React.ReactNode; tone?: string }) {
  return (
    <div className="rounded border border-border-base bg-bg-sunk px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.18em] text-text-dim">{label}</div>
      <div className={`mt-1 font-mono text-[13px] font-semibold ${tone ?? 'text-text-base'}`}>{value}</div>
    </div>
  )
}

function SummaryChip({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded border border-border-base bg-bg-sunk px-2.5 py-2">
      <div className="flex items-center gap-1 text-text-dim">
        {icon}
        <span className="text-[10px] uppercase tracking-[0.18em]">{label}</span>
      </div>
      <div className="mt-1 truncate font-mono text-text-base">{value}</div>
    </div>
  )
}

function RunStatePill({ state, connected }: { state?: string; connected: boolean }) {
  const text = state?.toUpperCase() ?? (connected ? 'STREAMING' : 'IDLE')
  const color = state === 'running' ? 'border-pos bg-pos-soft text-pos' : state === 'failed' ? 'border-neg bg-neg-soft text-neg' : 'border-border-base bg-bg-sunk text-text-mute'
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-semibold ${color}`}>
      {state === 'running' && <Loader2 className="h-3 w-3 animate-spin" />}
      {state === 'failed' && <CircleAlert className="h-3 w-3" />}
      {(state === 'done' || (!state && connected)) && <Cpu className="h-3 w-3" />}
      {text}
    </span>
  )
}

function EmptyPanel({ message, className }: { message: string; className?: string }) {
  return (
    <div className={`grid place-items-center px-4 py-10 text-center text-sm text-text-mute ${className ?? ''}`}>
      {message}
    </div>
  )
}

function flattenPipeline(pipeline: PipelineResponse | undefined) {
  if (!pipeline) return []
  if ('stages' in pipeline) return pipeline.stages
  return [pipeline.input, ...pipeline.tracks.flatMap((track) => track.stages), ...pipeline.converge]
}

function computeGeneratedCount(pipeline: PipelineResponse | undefined, silo: Silo) {
  if (!pipeline) return null
  const stages = flattenPipeline(pipeline)
  if (silo === 'A') return stages.find((stage) => stage.id === '03')?.out_count ?? null
  if (silo === 'B') return stages.find((stage) => stage.id === 'DV')?.out_count ?? stages.find((stage) => stage.id === '03b')?.out_count ?? null
  const aOut = stages.find((stage) => stage.id === '03')?.out_count ?? 0
  const bOut = stages.find((stage) => stage.id === 'DV')?.out_count ?? 0
  return aOut + bOut
}

function displayCount(value: number | null) {
  return value == null ? '—' : String(value)
}

function formatSigned(value: number) {
  return `${value > 0 ? '+' : ''}${value.toFixed(3)}`
}

function formatLogTime(value: string) {
  return value.includes('T') ? new Date(value).toLocaleTimeString('en-GB', { hour12: false }) : value
}
