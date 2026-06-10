import { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ArrowLeft, CheckCircle2, Download, FileText, Loader2, MessageSquarePlus } from 'lucide-react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Molstar } from '../components/dashboard/Molstar'
import { Sequence } from '../components/dashboard/Sequence'
import { TierBadge } from '../components/dashboard/TierBadge'
import { usePipelineContext } from '../contexts/PipelineContext'
import { useADMET, useCand03Variants, useCandidates, useRuns, useRunStatus, useTransitionWetlabOrder, type Candidate as DashboardCandidate, type RunSummary } from '../hooks/dashboard'

const RECEPTORS = ['SSTR1', 'SSTR2', 'SSTR3', 'SSTR4', 'SSTR5'] as const
const CONTACTS = [
  { pos: 'K4', partner: 'Asp137', dist: '2.8 Å', type: 'salt-bridge' },
  { pos: 'W8', partner: 'Phe294', dist: '3.4 Å', type: 'pi-stack' },
  { pos: 'F6/F7', partner: 'hydrophobic', dist: '3.6 Å avg', type: 'cluster' },
  { pos: 'T10', partner: 'Gln138', dist: '2.9 Å', type: 'H-bond' },
] as const

type ViewMode = 'ribbon' | 'surface' | 'stick'

type VariantRecord = {
  id: string
  name: string
  seq: string
  modifications: string[]
  hl_score: number
  chymotrypsin_sites: number
  trypsin_sites: number
  nep_sites: number
  priority: string
  rationale?: string | null
}

type AdmetSummary = {
  halfLifeMinutes: number
  instability: number
  bomanKcal: number
  aggregationScore: number
  gravy: number
  confidence: string
  vulnerabilities: Array<{ site: string; protease: string; severity: string }>
}

export function CandidatePage() {
  const live = usePipelineContext()
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const runsQuery = useRuns()
  const runs = useMemo(() => runsQuery.data?.runs ?? [], [runsQuery.data?.runs])
  const requestedRunId = searchParams.get('run_id') ?? live.viewingArchive ?? (live.runId || undefined) ?? runs[0]?.run_id
  const orderIdFromQuery = searchParams.get('order_id') ?? 'WO-2026-005'
  const statusQuery = useRunStatus(requestedRunId)
  const runId = requestedRunId ?? statusQuery.data?.run_id

  const candidatesQuery = useCandidates(runId)
  const variantsQuery = useCand03Variants()

  const requestedId = searchParams.get('candidate') ?? id
  const [selectedCandidateId, setSelectedCandidateId] = useState(requestedId ?? '')
  const candidateEntries = candidatesQuery.data?.candidates
  const candidates = useMemo(() => candidateEntries ?? [], [candidateEntries])
  const wildType = candidatesQuery.data?.wild_type ?? 'AGCKNFFWKTFTSC'
  const candidate = selectedCandidateId
    ? candidates.find((entry) => entry.id === selectedCandidateId) ?? null
    : candidates[0] ?? null

  const admetQuery = useADMET(candidate?.seq)
  const transitionOrder = useTransitionWetlabOrder()

  const [viewMode, setViewMode] = useState<ViewMode>('ribbon')
  const [selectedVariantId, setSelectedVariantId] = useState<string>('')
  const [orderId, setOrderId] = useState(orderIdFromQuery)
  const [approvalNote, setApprovalNote] = useState('PI 검토 요청 · Candidate Review 화면에서 승인 전환')
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const variants = useMemo(() => normalizeVariants(variantsQuery.data), [variantsQuery.data])
  const selectedVariant = variants.find((entry) => entry.id === selectedVariantId) ?? variants[0] ?? null
  const highlightedVariant = selectHighlightedVariant(variants, selectedVariantId)
  const admet = useMemo(() => normalizeAdmet(admetQuery.data, candidate?.seq), [admetQuery.data, candidate?.seq])
  const bestOffTarget = candidate ? bestOffTargetReceptor(candidate) : null
  const pdbUrl = candidate ? structureUrl(candidate.source) : null
  const reportUrl = candidate ? `/api/candidate/${encodeURIComponent(candidate.id)}/report${runId ? `?run_id=${encodeURIComponent(runId)}` : ''}` : null

  const updateCandidateUrl = useCallback((candidateId: string, options?: { replace?: boolean }) => {
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('candidate', candidateId)
    if (runId && !nextParams.has('run_id')) nextParams.set('run_id', runId)
    navigate(
      {
        pathname: '/candidate',
        search: `?${nextParams.toString()}`,
      },
      { replace: options?.replace ?? false },
    )
  }, [navigate, runId, searchParams])

  const updateRunUrl = useCallback(async (nextRunId: string) => {
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('run_id', nextRunId)
    nextParams.delete('candidate')

    const firstCandidateId = await fetchFirstCandidateId(nextRunId)
    if (firstCandidateId) nextParams.set('candidate', firstCandidateId)

    navigate({
      pathname: '/candidate',
      search: `?${nextParams.toString()}`,
    })
  }, [navigate, searchParams])

  useEffect(() => {
    if (selectedVariantId) return
    if (!variants[0]) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSelectedVariantId(variants[0].id)
  }, [selectedVariantId, variants])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSelectedCandidateId(requestedId ?? '')
  }, [requestedId])

  useEffect(() => {
    if (selectedCandidateId || candidates.length === 0) return
    const firstCandidateId = candidates[0].id
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSelectedCandidateId(firstCandidateId)
    updateCandidateUrl(firstCandidateId, { replace: true })
  }, [candidates, selectedCandidateId, updateCandidateUrl])

  function handleCandidateChange(nextCandidateId: string) {
    setSelectedCandidateId(nextCandidateId)
    updateCandidateUrl(nextCandidateId)
  }

  function handleRunChange(nextRunId: string) {
    void updateRunUrl(nextRunId)
  }

  async function handleApprove() {
    if (!orderId.trim()) {
      setStatusMessage('order id가 필요합니다.')
      return
    }

    try {
      await transitionOrder.mutateAsync({
        orderId: orderId.trim(),
        to_stage: 'approved',
        note: approvalNote.trim() || undefined,
      })
      setStatusMessage(`wetlab order ${orderId.trim()} 를 approval 단계로 전환했습니다.`)
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'approval 전환에 실패했습니다.')
    }
  }

  if (candidatesQuery.isLoading && !candidate) {
    return (
      <div className="grid min-h-[60vh] place-items-center rounded-xl border border-border-base bg-bg-elev">
        <div className="flex items-center gap-2 text-sm text-text-mute">
          <Loader2 className="h-4 w-4 animate-spin" />
          candidate 데이터를 불러오는 중입니다.
        </div>
      </div>
    )
  }

  if (!candidate) {
    return (
      <section className="rounded-xl border border-border-base bg-bg-elev p-6">
        <div className="flex items-start gap-3 text-sm text-text-base">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-warn" />
          <div>
            <div className="font-semibold">candidate를 찾지 못했습니다.</div>
            <p className="mt-1 text-text-mute">
              {runId ? `run \`${runId}\` 에 표시할 후보가 없습니다.` : '데이터 없음 · 현재 run_id를 찾지 못했습니다.'}
            </p>
            <Link to="/console" className="mt-3 inline-flex items-center gap-1 rounded border border-border-base px-3 py-1.5 text-xs text-text-mute transition-colors hover:bg-bg-sunk hover:text-text-base">
              <ArrowLeft className="h-3.5 w-3.5" />
              Run Console
            </Link>
          </div>
        </div>
      </section>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border-base bg-bg">
      <header className="flex flex-wrap items-center gap-3 border-b border-border-base bg-bg-elev px-5 py-3">
        <Link to={runId ? `/selectivity-explorer?run_id=${runId}` : '/selectivity-explorer'} className="inline-flex items-center gap-1 rounded border border-border-base px-2.5 py-1 text-[11px] text-text-mute transition-colors hover:bg-bg-sunk hover:text-text-base">
          <ArrowLeft className="h-3.5 w-3.5" />
          candidates
        </Link>
        <div className="h-5 w-px bg-border-base" />
        <RunSelector value={runId ?? ''} runs={runs} onChange={handleRunChange} loading={runsQuery.isLoading} />
        <div className="h-5 w-px bg-border-base" />
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-base font-semibold text-text-base">{candidate.id}</span>
            <TierBadge tier={candidate.tier} />
            {candidate.recommended && <span className="rounded bg-pos-soft px-2 py-0.5 text-[10px] font-semibold text-pos">★ RECOMMENDED</span>}
            <span className="rounded border border-border-base px-2 py-0.5 text-[10px] text-text-mute">silo B</span>
            <span className="rounded border border-border-base px-2 py-0.5 text-[10px] text-text-mute">{runId ?? 'live run'}</span>
          </div>
          <div className="mt-1 text-[11px] text-text-mute">
            <span className="font-mono">{candidate.seq}</span> · {candidate.mutations.join(', ') || 'WT-like profile'} · source <span className="font-mono">{candidate.source ?? '—'}</span>
          </div>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          {pdbUrl ? (
            <a href={pdbUrl} download className="inline-flex items-center gap-1 rounded border border-border-base px-2.5 py-1 text-[11px] text-text-mute transition-colors hover:bg-bg-sunk hover:text-text-base">
              <Download className="h-3.5 w-3.5" />
              PDB
            </a>
          ) : (
            <button type="button" disabled title="No PDB path is available for this candidate" className="inline-flex cursor-not-allowed items-center gap-1 rounded border border-border-base px-2.5 py-1 text-[11px] text-text-dim opacity-60">
              <Download className="h-3.5 w-3.5" />
              PDB
            </button>
          )}
          {reportUrl && (
            <a href={reportUrl} download className="inline-flex items-center gap-1 rounded border border-border-base px-2.5 py-1 text-[11px] text-text-mute transition-colors hover:bg-bg-sunk hover:text-text-base">
              <FileText className="h-3.5 w-3.5" />
              Report
            </a>
          )}
          <button
            type="button"
            onClick={handleApprove}
            disabled={transitionOrder.isPending}
            className="inline-flex items-center gap-1 rounded border border-pos bg-pos-soft px-3 py-1 text-[11px] font-semibold text-pos transition-colors hover:bg-pos-soft/80 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {transitionOrder.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
            Wetlab Ki approval
          </button>
        </div>
      </header>

      <div className="grid min-h-[920px] lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <section className="border-b border-r border-border-base px-5 py-4 lg:border-b-0">
          <Panel
            title="구조 · candidate in SSTR2 (7XNA holo)"
            right={(
              <div className="flex gap-1">
                {(['ribbon', 'surface', 'stick'] as const).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setViewMode(mode)}
                    className={`rounded border px-2 py-1 text-[10px] font-medium transition-colors ${
                      viewMode === mode
                        ? 'border-border-strong bg-bg-sunk text-text-base'
                        : 'border-border-base text-text-mute hover:bg-bg-sunk'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            )}
          >
            <CandidateSelector value={candidate.id} candidates={candidates} onChange={handleCandidateChange} />
            <Molstar pdbUrl={candidate.source ? toStructureUrl(candidate.source) : undefined} pdbId="7XNA" height={320} />
            <div className="mt-3 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-text-dim">
              <span>Molstar 5.6</span>
              <span>{viewMode}</span>
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
              {CONTACTS.map((contact) => (
                <ContactCard key={contact.pos} {...contact} />
              ))}
            </div>
          </Panel>

          <Panel
            className="mt-4"
            title="서열 비교 · WT vs candidate"
            right={<span className="font-mono text-[10px] text-text-dim">14 aa · disulfide C3-C14</span>}
          >
            <div className="space-y-3">
              <SequenceCompareRow label="SST-14 (WT)" sequence={wildType} wildType={wildType} meta="0.2 nM" />
              <SequenceCompareRow label={candidate.id} sequence={candidate.seq} wildType={wildType} meta={`margin ${formatSigned(candidate.margin)}`} highlight />
              {selectedVariant && (
                <SequenceCompareRow
                  label={selectedVariant.id}
                  sequence={selectedVariant.seq.replace(/\[[^\]]+\]/g, '*')}
                  wildType={wildType}
                  mod={selectedVariant.modifications.join(', ')}
                  meta={selectedVariant.priority}
                />
              )}
              {highlightedVariant && highlightedVariant.id !== selectedVariant?.id && (
                <SequenceCompareRow
                  label={highlightedVariant.id}
                  sequence={highlightedVariant.seq.replace(/\[[^\]]+\]/g, '*')}
                  wildType={wildType}
                  badge={highlightedVariant.priority}
                  meta={highlightedVariant.rationale ?? 'catalog highlight'}
                />
              )}
            </div>
          </Panel>

          <Panel
            className="mt-4"
            title={`${candidate.id} 변이체 카탈로그 · ${variants.length}종`}
            right={<span className="font-mono text-[10px] text-text-dim">cand03_variants.json</span>}
          >
            <div className="overflow-auto">
              <table className="w-full min-w-[760px] text-[11px]">
                <thead>
                  <tr className="border-b border-border-base text-left text-text-dim">
                    <th className="px-3 py-2 font-medium">variant</th>
                    <th className="px-3 py-2 font-medium">modification</th>
                    <th className="px-3 py-2 text-right font-medium">HL score</th>
                    <th className="px-3 py-2 text-right font-medium">chymo</th>
                    <th className="px-3 py-2 text-right font-medium">tryp</th>
                    <th className="px-3 py-2 text-right font-medium">NEP</th>
                    <th className="px-3 py-2 font-medium">priority</th>
                  </tr>
                </thead>
                <tbody>
                  {variants.map((variant) => {
                    const active = variant.id === selectedVariantId
                    return (
                      <tr
                        key={variant.id}
                        onClick={() => setSelectedVariantId(variant.id)}
                        className={`cursor-pointer border-b border-border-base/70 transition-colors ${active ? 'bg-pos-soft/40' : 'hover:bg-bg-sunk'}`}
                      >
                        <td className="px-3 py-2 font-mono font-semibold text-text-base">{variant.id}</td>
                        <td className="px-3 py-2 text-text-mute">{variant.modifications.join(', ') || variant.name}</td>
                        <td className="px-3 py-2 text-right font-mono text-text-base">{variant.hl_score.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right font-mono text-text-mute">{variant.chymotrypsin_sites}</td>
                        <td className="px-3 py-2 text-right font-mono text-text-mute">{variant.trypsin_sites}</td>
                        <td className="px-3 py-2 text-right font-mono text-text-mute">{variant.nep_sites}</td>
                        <td className={`px-3 py-2 ${active ? 'font-semibold text-pos' : 'text-text-mute'}`}>{variant.priority}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            {selectedVariant?.rationale && (
              <div className="mt-3 rounded border border-border-base bg-bg-sunk px-3 py-2 text-[11px] text-text-mute">
                {selectedVariant.rationale}
              </div>
            )}
          </Panel>
        </section>

        <section className="space-y-4 px-5 py-4">
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            <BigStat label="iPTM(SSTR2)" value={(candidate.iptm.SSTR2 ?? 0).toFixed(3)} tone="pos" sub="best receptor" />
            <BigStat label="margin" value={formatSigned(candidate.margin)} tone={candidate.margin > 0 ? 'pos' : 'warn'} sub={`vs ${bestOffTarget?.name ?? 'off-target'}`} />
            <BigStat label="ddG" value={candidate.ddg != null ? candidate.ddg.toFixed(1) : '—'} sub="kcal/mol" />
            <BigStat label="GRAVY" value={admet.gravy.toFixed(3)} tone={admet.gravy > 0.3 ? 'warn' : undefined} sub={`HL ${admet.halfLifeMinutes.toFixed(0)} min`} />
          </div>

          <Panel
            title="Selectivity · 5 SSTR"
            right={<span className="font-mono text-[10px] text-text-dim">iPTM</span>}
          >
            <div className="space-y-2">
              {RECEPTORS.map((receptor) => {
                const value = candidate.iptm[receptor] ?? 0
                const isTarget = receptor === 'SSTR2'
                return (
                  <div key={receptor} className="grid grid-cols-[78px_minmax(0,1fr)_56px_88px] items-center gap-3 text-[11px]">
                    <span className={`font-mono ${isTarget ? 'font-semibold text-accent-text' : 'text-text-mute'}`}>
                      {isTarget ? '★ ' : ''}{receptor}
                    </span>
                    <div className="relative h-4 overflow-hidden rounded bg-bg-sunk">
                      <div className="h-full" style={{ width: `${Math.max(0, Math.min(100, ((value - 0.7) / 0.3) * 100))}%`, background: iptmColor(value) }} />
                      {isTarget && <div className="absolute inset-0 rounded border border-dashed border-accent" />}
                    </div>
                    <span className="text-right font-mono font-semibold text-text-base">{value.toFixed(3)}</span>
                    <span className="text-right font-mono text-[10px] text-text-dim">{estimateKiRange(receptor)}</span>
                  </div>
                )
              })}
            </div>
          </Panel>

          <Panel
            title="5-Agent 결정 트레일"
            right={<span className="rounded bg-pos-soft px-2 py-0.5 text-[10px] font-semibold text-pos">consensus</span>}
          >
            <div className="space-y-2">
              <AgentLine agent="planner" color="violet" text={`${candidate.id} 주변 친수성 변이 확장 · FWKT pharmacophore 보존`} />
              <AgentLine agent="builder" color="accent" text="Boltz-2 batch + PyRosetta refine로 pose/energy 수렴 확인" />
              <AgentLine agent="qcranker" color="teal" text={`${candidate.id} 는 현재 cohort에서 ${candidate.tier} · margin ${formatSigned(candidate.margin)}`} />
              <AgentLine agent="critic" color="warn" text="iPTM 기반 selectivity는 wetlab Ki로 후속 검증 필요" />
              <AgentLine agent="reporter" color="stone" text={`wetlab hypothesis 정리 후 order ${orderId || '미지정'} approval 권장`} />
            </div>
          </Panel>

          <Panel title="ADMET · stability prescreen">
            {admetQuery.isLoading ? (
              <div className="flex items-center gap-2 text-sm text-text-mute">
                <Loader2 className="h-4 w-4 animate-spin" />
                ADMET 계산 중…
              </div>
            ) : (
              <>
                <div className="grid gap-3 sm:grid-cols-2">
                  <MetricBar label="t1/2 (예측)" value={admet.halfLifeMinutes} max={120} unit="min" tone="warn" />
                  <MetricBar label="instability" value={admet.instability} max={100} tone="pos" />
                  <MetricBar label="Boman index" value={admet.bomanKcal} max={2.5} unit="kcal" tone="pos" />
                  <MetricBar label="aggregation" value={admet.aggregationScore} max={1} unit="score" tone="warn" />
                </div>
                <div className="mt-3 rounded border border-border-base bg-bg-sunk px-3 py-2 text-[11px] text-text-mute">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-warn-soft px-1.5 py-0.5 text-[10px] font-semibold text-warn">{admet.confidence}</span>
                    <span>{admet.vulnerabilities[0]?.site ?? 'FWKT motif'} 취약성 기반 heuristic prescreen</span>
                  </div>
                  {admet.vulnerabilities.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {admet.vulnerabilities.map((item) => (
                        <span key={`${item.site}-${item.protease}`} className="rounded border border-border-base px-2 py-0.5 font-mono text-[10px]">
                          {item.site} · {item.protease} · {item.severity}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </Panel>

          <Panel title="다음 액션 · wetlab approval" className="border-pos bg-pos-soft/30">
            <div className="space-y-2">
              <DecisionItem text={`${candidate.id} wetlab Ki 발주 (SSTR1-5 radioligand assay, n=3)`} cost="₩2.5M" time="8주" checked />
              {selectedVariant && (
                <DecisionItem text={`${selectedVariant.id} 추가 합성 · stability 보강`} cost="₩1.2M" time="3주" checked={selectedVariant.id !== 'SST14_ref'} />
              )}
              <DecisionItem text="Boltz-2 변이체 추가 배치로 margin 재추정" cost="—" time="4h GPU" checked />
              <DecisionItem text="step05c cross-val default pipeline 통합 여부 검토" cost="—" time="0.5d eng" />
            </div>

            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              <label className="text-[11px] text-text-mute">
                <div className="mb-1 uppercase tracking-[0.18em] text-text-dim">order id</div>
                <input
                  value={orderId}
                  onChange={(event) => setOrderId(event.target.value)}
                  className="w-full rounded border border-border-base bg-bg px-3 py-2 font-mono text-xs text-text-base outline-none transition-colors focus:border-accent"
                />
              </label>
              <label className="text-[11px] text-text-mute">
                <div className="mb-1 uppercase tracking-[0.18em] text-text-dim">note</div>
                <input
                  value={approvalNote}
                  onChange={(event) => setApprovalNote(event.target.value)}
                  className="w-full rounded border border-border-base bg-bg px-3 py-2 text-xs text-text-base outline-none transition-colors focus:border-accent"
                />
              </label>
            </div>

            {statusMessage && (
              <div className="mt-3 rounded border border-border-base bg-bg px-3 py-2 text-[11px] text-text-mute">
                {statusMessage}
              </div>
            )}

            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button type="button" onClick={() => setApprovalNote('deferred · 추가 계산 필요')} className="rounded border border-border-base px-3 py-1.5 text-[11px] text-text-mute transition-colors hover:bg-bg hover:text-text-base">
                defer
              </button>
              <button type="button" onClick={() => setApprovalNote(`comment · ${candidate.id} rationale 업데이트 필요`)} className="inline-flex items-center gap-1 rounded border border-border-base px-3 py-1.5 text-[11px] text-text-mute transition-colors hover:bg-bg hover:text-text-base">
                <MessageSquarePlus className="h-3.5 w-3.5" />
                comment
              </button>
              <button
                type="button"
                onClick={handleApprove}
                disabled={transitionOrder.isPending}
                className="rounded border border-pos bg-pos px-3 py-1.5 text-[11px] font-semibold text-white transition-opacity disabled:opacity-60"
              >
                approve to wetlab
              </button>
            </div>
          </Panel>
        </section>
      </div>
    </div>
  )
}

function Panel({
  title,
  right,
  children,
  className = '',
}: {
  title: string
  right?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={`rounded-xl border border-border-base bg-bg-elev ${className}`}>
      <div className="flex items-center justify-between gap-3 border-b border-border-base px-4 py-3">
        <h2 className="text-sm font-semibold text-text-base">{title}</h2>
        {right}
      </div>
      <div className="p-4">{children}</div>
    </section>
  )
}

function RunSelector({
  value,
  runs,
  onChange,
  loading = false,
}: {
  value: string
  runs: RunSummary[]
  onChange: (runId: string) => void
  loading?: boolean
}) {
  const disabled = loading || runs.length === 0
  return (
    <label className="flex items-center gap-2 text-[11px] text-text-mute">
      <span className="uppercase tracking-[0.18em] text-text-dim">run</span>
      <select
        aria-label="Run selector"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        className="min-w-[240px] rounded border border-border-base bg-bg px-2.5 py-1 font-mono text-xs font-semibold text-text-base outline-none transition-colors hover:bg-bg-sunk focus:border-accent disabled:cursor-not-allowed disabled:text-text-dim disabled:opacity-60"
      >
        {runs.length === 0 ? (
          <option value="">{loading ? 'loading runs...' : 'no runs'}</option>
        ) : (
          runs.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {run.run_id} · {run.n_candidates} candidates
            </option>
          ))
        )}
      </select>
    </label>
  )
}

function CandidateSelector({
  value,
  candidates,
  onChange,
}: {
  value: string
  candidates: DashboardCandidate[]
  onChange: (candidateId: string) => void
}) {
  return (
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded border border-border-base bg-bg-sunk px-3 py-2">
      <div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-text-dim">candidate</div>
        <div className="mt-0.5 text-[11px] text-text-mute">현 세션 후보 {candidates.length}개</div>
      </div>
      <div role="group" aria-label="Candidate selector" className="flex flex-wrap gap-1">
        {candidates.map((entry, index) => {
          const active = entry.id === value
          return (
            <button
              key={entry.id}
              type="button"
              onClick={() => onChange(entry.id)}
              aria-pressed={active}
              title={entry.id}
              className={`h-8 min-w-8 rounded border px-2 font-mono text-xs font-semibold transition-colors ${
                active
                  ? 'border-accent bg-accent-soft text-accent-text'
                  : 'border-border-base bg-bg text-text-mute hover:bg-bg-elev hover:text-text-base'
              }`}
            >
              {index + 1}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function BigStat({
  label,
  value,
  sub,
  tone,
}: {
  label: string
  value: string
  sub: string
  tone?: 'pos' | 'warn'
}) {
  const toneClass = tone === 'pos' ? 'text-pos' : tone === 'warn' ? 'text-warn' : 'text-text-base'
  return (
    <div className="rounded-xl border border-border-base bg-bg-elev px-3 py-3">
      <div className="text-[10px] uppercase tracking-[0.18em] text-text-dim">{label}</div>
      <div className={`mt-1 font-mono text-2xl font-semibold ${toneClass}`}>{value}</div>
      <div className="mt-1 text-[10px] text-text-mute">{sub}</div>
    </div>
  )
}

function SequenceCompareRow({
  label,
  sequence,
  wildType,
  meta,
  mod,
  badge,
  highlight = false,
}: {
  label: string
  sequence: string
  wildType: string
  meta: string
  mod?: string
  badge?: string
  highlight?: boolean
}) {
  return (
    <div className={`grid gap-3 md:grid-cols-[170px_minmax(0,1fr)_180px] md:items-center ${highlight ? 'rounded border border-accent bg-accent-soft/40 px-2 py-2' : ''}`}>
      <div className={`text-[11px] ${highlight ? 'font-semibold text-accent-text' : 'text-text-mute'}`}>{label}</div>
      <div className="min-w-0 overflow-auto">
        <Sequence seq={sequence} wildtype={wildType} />
      </div>
      <div className="flex flex-wrap items-center justify-end gap-1 text-[10px] text-text-mute">
        {mod && <span className="rounded border border-border-base px-1.5 py-0.5">{mod}</span>}
        {badge && <span className="rounded bg-pos-soft px-1.5 py-0.5 font-semibold text-pos">{badge}</span>}
        <span className="font-mono">{meta}</span>
      </div>
    </div>
  )
}

function ContactCard({ pos, partner, dist, type }: { pos: string; partner: string; dist: string; type: string }) {
  return (
    <div className="rounded border border-border-base bg-bg-sunk px-3 py-2">
      <div className="font-mono text-[11px] font-semibold text-text-base">{pos} · {partner}</div>
      <div className="mt-1 flex items-center justify-between text-[10px] text-text-mute">
        <span>{type}</span>
        <span className="font-mono">{dist}</span>
      </div>
    </div>
  )
}

function AgentLine({ agent, color, text }: { agent: string; color: 'violet' | 'accent' | 'teal' | 'warn' | 'stone'; text: string }) {
  const colorClass = {
    violet: 'bg-violet-soft text-violet',
    accent: 'bg-accent-soft text-accent',
    teal: 'bg-teal-soft text-teal',
    warn: 'bg-warn-soft text-warn',
    stone: 'bg-bg-sunk text-text-mute',
  }[color]
  return (
    <div className="grid gap-2 md:grid-cols-[78px_minmax(0,1fr)]">
      <span className={`inline-flex h-fit items-center justify-center rounded px-2 py-1 font-mono text-[10px] font-semibold ${colorClass}`}>
        {agent.toUpperCase()}
      </span>
      <span className="text-[11px] leading-5 text-text-base">{text}</span>
    </div>
  )
}

function MetricBar({
  label,
  value,
  max,
  unit = '',
  tone,
}: {
  label: string
  value: number
  max: number
  unit?: string
  tone: 'pos' | 'warn'
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  const color = tone === 'pos' ? 'var(--pos)' : 'var(--warn)'
  return (
    <div>
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-text-mute">{label}</span>
        <span className="font-mono font-semibold text-text-base">{value.toFixed(unit ? 0 : 2)}{unit ? ` ${unit}` : ''}</span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded bg-bg-sunk">
        <div className="h-full" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

function DecisionItem({ text, cost, time, checked = false }: { text: string; cost: string; time: string; checked?: boolean }) {
  return (
    <div className="grid grid-cols-[20px_minmax(0,1fr)_60px_60px] items-center gap-2 border-b border-border-base/70 py-2 text-[11px]">
      <span className={`grid h-4 w-4 place-items-center rounded border ${checked ? 'border-pos text-pos' : 'border-border-base text-text-dim'}`}>
        {checked && <CheckCircle2 className="h-3 w-3" />}
      </span>
      <span className="text-text-base">{text}</span>
      <span className="text-right font-mono text-text-mute">{cost}</span>
      <span className="text-right font-mono text-text-mute">{time}</span>
    </div>
  )
}

function normalizeVariants(raw: unknown): VariantRecord[] {
  const payload = raw as { variants?: VariantRecord[] } | undefined
  if (!payload?.variants || !Array.isArray(payload.variants)) return []
  return payload.variants
}

function normalizeAdmet(raw: unknown, sequence?: string): AdmetSummary {
  const payload = raw as Record<string, unknown> | undefined
  const seq = (sequence ?? '').toUpperCase()

  if (payload && 'admet' in payload) {
    const admet = payload.admet as Record<string, unknown>
    return {
      halfLifeMinutes: heuristicHalfLife(seq),
      instability: 100 - numberValue(admet.druglikeness_score, 65),
      bomanKcal: Math.max(0.05, Math.abs(numberValue(admet.hydrophobicity, 0.18))),
      aggregationScore: Math.min(1, Math.max(0.05, Math.abs(numberValue(admet.hydrophobicity, 0.18)) / 2)),
      gravy: numberValue(admet.hydrophobicity, 0.18),
      confidence: 'HEURISTIC / LOW',
      vulnerabilities: inferVulnerabilities(seq),
    }
  }

  return {
    halfLifeMinutes: numberValue(payload?.half_life_minutes, heuristicHalfLife(seq)),
    instability: numberValue(payload?.instability, 30.65),
    bomanKcal: numberValue(payload?.boman_kcal, 0.18),
    aggregationScore: numberValue(payload?.aggregation_score, Math.min(1, Math.abs(numberValue(payload?.gravy, 0.2)) / 2)),
    gravy: numberValue(payload?.gravy, 0.18),
    confidence: typeof payload?.confidence === 'string' ? payload.confidence : 'HEURISTIC / LOW',
    vulnerabilities: Array.isArray(payload?.vulnerabilities)
      ? (payload?.vulnerabilities as Array<{ site: string; protease: string; severity: string }>)
      : inferVulnerabilities(seq),
  }
}

function inferVulnerabilities(sequence: string) {
  if (!sequence) return []
  const entries: Array<{ site: string; protease: string; severity: string }> = []
  if (sequence.includes('FFW')) entries.push({ site: 'F6-F8', protease: 'chymotrypsin', severity: 'high' })
  if (sequence.includes('KT')) entries.push({ site: 'K9-T10', protease: 'trypsin', severity: 'medium' })
  if (sequence.includes('SC')) entries.push({ site: 'S13-C14', protease: 'NEP', severity: 'medium' })
  return entries
}

function heuristicHalfLife(sequence: string) {
  if (!sequence) return 5
  const aromaticPenalty = [...sequence].filter((aa) => aa === 'F' || aa === 'W' || aa === 'Y').length
  return Math.max(5, 60 - aromaticPenalty * 8)
}

function selectHighlightedVariant(variants: VariantRecord[], selectedId: string) {
  if (variants.length === 0) return null
  return variants.find((variant) => variant.id !== selectedId && /1순위|baseline|screening/i.test(variant.priority))
    ?? variants.find((variant) => variant.id !== selectedId)
    ?? variants[0]
}

function bestOffTargetReceptor(candidate: DashboardCandidate) {
  return RECEPTORS
    .filter((receptor) => receptor !== 'SSTR2')
    .map((receptor) => ({ name: receptor, value: candidate.iptm[receptor] ?? 0 }))
    .sort((left, right) => right.value - left.value)[0]
}

function estimateKiRange(receptor: string) {
  switch (receptor) {
    case 'SSTR2': return '0.5-5 nM'
    case 'SSTR1': return '>= 5 nM'
    case 'SSTR4': return '>= 5 nM'
    default: return '>= 10 nM'
  }
}

function iptmColor(value: number) {
  if (value >= 0.95) return 'var(--pos)'
  if (value >= 0.9) return 'var(--accent)'
  if (value >= 0.85) return 'var(--warn)'
  return 'var(--neg)'
}

function toStructureUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined
  if (path.startsWith('/api/')) return path
  if (path.startsWith('runs_local/')) return `/api/structures/${path.slice('runs_local/'.length)}`
  if (path.startsWith('data/')) return `/api/structures/${path.slice('data/'.length)}`
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
    return `/api/structures/${path.split(runsLocalMarker)[1]}`
  }
  if (path.includes(runsMarker)) {
    return `/api/structures/${path.split(runsMarker)[1]}`
  }
  return undefined
}

async function fetchFirstCandidateId(runId: string): Promise<string | null> {
  try {
    const response = await fetch(`/api/runs/${encodeURIComponent(runId)}`)
    if (!response.ok) return null
    const payload = await response.json() as { candidates?: unknown[] }
    const firstCandidate = payload.candidates?.[0]
    if (!firstCandidate || typeof firstCandidate !== 'object') return null
    const entry = firstCandidate as Record<string, unknown>
    const id = entry.id ?? entry.candidate_id
    return typeof id === 'string' && id.length > 0 ? id : null
  } catch {
    return null
  }
}

function numberValue(value: unknown, fallback: number) {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function formatSigned(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(3)}`
}

function structureUrl(source: string | null): string | null {
  if (!source || !source.endsWith('.pdb')) return null
  const marker = '/runs_local/'
  const dataMarker = '/data/'
  if (source.includes(marker)) {
    return `/api/structures/${encodeURI(source.slice(source.indexOf(marker) + marker.length))}`
  }
  if (source.includes(dataMarker)) {
    return `/api/structures/${encodeURI(source.slice(source.indexOf(dataMarker) + dataMarker.length))}`
  }
  if (source.startsWith('runs_local/')) return `/api/structures/${encodeURI(source.slice('runs_local/'.length))}`
  if (source.startsWith('data/')) return `/api/structures/${encodeURI(source.slice('data/'.length))}`
  return null
}
