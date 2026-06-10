import type { Dispatch, ReactNode, SetStateAction } from 'react'
import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Download, FileSpreadsheet, FlaskConical, Loader2, Square, TestTubeDiagonal, XCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { ArchivesTopKSlider, type ArchiveEntry } from '../components/ArchivesTopKSlider'
import { HeuristicBanner } from '../components/HeuristicBanner'
import { Sequence } from '../components/dashboard/Sequence'
import { useCreateWetlabOrder } from '../hooks/dashboard'
import {
  isStubResults,
  useCancelFlexPepDockJob,
  useCreateFlexPepDockJob,
  useFlexPepDockJob,
  useFlexPepDockJobs,
  useFlexPepDockResults,
  useJobsStubStatus,
  type FlexPepDockConfig,
  type FlexPepDockJobSummary,
  type FlexPepDockReceptor,
} from '../hooks/useFlexPepDockJob'
import { classifyJobStatus } from './manualSelectivityJobStatus'

const RECEPTORS: FlexPepDockReceptor[] = ['SSTR1', 'SSTR2', 'SSTR3', 'SSTR4', 'SSTR5']
const DEFAULT_SEQUENCE = 'AGCKNFFWKTFTSC'
const CAND03_SEQUENCE = 'AICKNFFWKTFTSC'
const INITIAL_CONFIG: FlexPepDockConfig = {
  cycles: 10,
  nstruct: 50,
  flex_pep_freedom: 'med',
  ddg_cycle: 5,
}

export function ManualSelectivityPage() {
  const navigate = useNavigate()
  const [sequenceInput, setSequenceInput] = useState('')
  const [selectedArchive, setSelectedArchive] = useState<ArchiveEntry | null>(null)
  const [selectedReceptors, setSelectedReceptors] = useState<FlexPepDockReceptor[]>([])
  const [config, setConfig] = useState<FlexPepDockConfig>(INITIAL_CONFIG)
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [wetlabMessage, setWetlabMessage] = useState<string | null>(null)

  const createJob = useCreateFlexPepDockJob()
  const jobsQuery = useFlexPepDockJobs()
  const activeJobQuery = useFlexPepDockJob(activeJobId, { polling: true })
  const cancelJob = useCancelFlexPepDockJob()
  const createWetlabOrder = useCreateWetlabOrder()

  // jobs 안정적 참조 보장 (jobsQuery.data?.jobs ?? [] 는 매 render마다 새 [] 생성)
  const jobs = useMemo(() => jobsQuery.data?.jobs ?? [], [jobsQuery.data?.jobs])
  const currentJob = activeJobQuery.data
  const resultsQuery = useFlexPepDockResults(currentJob?.status === 'done' ? activeJobId : null)

  // done 잡의 stub 여부를 병렬 조회 (캐시 공유 — resultsQuery 결과도 재사용)
  const doneJobIds = useMemo(
    () => jobs.filter((j) => j.status === 'done').map((j) => j.job_id),
    [jobs],
  )
  const stubStatusByJob = useJobsStubStatus(doneJobIds)

  // 현재 활성 잡 결과의 stub 여부 (Section 4 배너용)
  const activeResultIsStub = resultsQuery.data ? isStubResults(resultsQuery.data) : false

  useEffect(() => {
    if (activeJobId) return
    const latest = [...jobs].reverse()[0]
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (latest) setActiveJobId(latest.job_id)
  }, [activeJobId, jobs])

  const normalizedSequence = useMemo(
    () => sequenceInput.replace(/\s+/g, '').toUpperCase(),
    [sequenceInput],
  )
  const sequenceError = useMemo(() => validateSequence(normalizedSequence), [normalizedSequence])
  const canRun = normalizedSequence.length > 0 && !sequenceError && selectedReceptors.length > 0 && !createJob.isPending
  const etaSeconds = currentJob?.eta_seconds ?? createJob.data?.eta_seconds ?? 0
  const queuePosition = currentJob?.queue_position ?? createJob.data?.queue_position ?? 0
  const topError = createJob.error?.message ?? activeJobQuery.error?.message ?? resultsQuery.error?.message ?? null

  async function handleRun() {
    setWetlabMessage(null)
    try {
      const created = await createJob.mutateAsync({
        sequence: normalizedSequence,
        receptors: selectedReceptors,
        config,
      })
      setActiveJobId(created.job_id)
    } catch {
      // mutation error is surfaced in UI
    }
  }

  async function handleCreateWetlabOrder() {
    if (!activeJobId) return
    setWetlabMessage(null)
    try {
      const order = await createWetlabOrder.mutateAsync({
        candidate_id: normalizedSequence === CAND03_SEQUENCE ? 'cand03' : normalizedSequence.toLowerCase(),
        flexpepdock_job_id: activeJobId,
      })
      setWetlabMessage(`wetlab order ${order.id} 생성 완료`)
      navigate(`/wetlab/orders/${order.id}`)
    } catch (error) {
      setWetlabMessage(error instanceof Error ? error.message : 'wetlab order 생성 실패')
    }
  }

  function handleArchiveSelect(entry: ArchiveEntry) {
    setSelectedArchive(entry)
    setSequenceInput(entry.sequence)
  }

  function handleExportCsv() {
    const result = resultsQuery.data
    if (!result) return
    const header = ['receptor', 'dG_kcal_mol', 'interface_score', 'pass']
    const rows = result.selectivity_matrix.map((row) => [
      row.receptor,
      row.dG_kcal_mol,
      row.interface_score,
      row.pass,
    ])
    const csv = [header, ...rows].map((cols) => cols.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `flexpepdock_${activeJobId ?? 'results'}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--warn)]/30 bg-[var(--warn-soft)]">
          <FlaskConical className="h-4 w-4 text-[var(--warn)]" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-text-base">Manual Selectivity</h1>
          <p className="text-[10px] text-text-mute">User-triggered FlexPepDock refinement and receptor selectivity matrix</p>
        </div>
      </div>

      <HeuristicBanner
        grade="B"
        warnings={['FlexPepDock는 in-silico estimation입니다. wet-lab 검증 전까지 Ki 절대값으로 가정하지 마세요.']}
      />

      {topError && <ErrorBanner message={topError} />}

      <section className="rounded-xl border border-border-base bg-bg-elev p-4">
        <SectionHeader
          title="Section 1: 후보 선택"
          description="Archive Top-K 후보를 고르거나 14aa 서열을 직접 입력합니다."
        />
        <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_320px]">
          <ArchivesTopKSlider onSelect={handleArchiveSelect} />
          <div className="rounded-xl border border-border-base bg-bg p-4">
            <h3 className="text-xs font-semibold text-text-base">Selected</h3>
            {selectedArchive ? (
              <div className="mt-3 space-y-3">
                <Sequence seq={selectedArchive.sequence} showRuler big />
                <div className="grid grid-cols-2 gap-2 text-[11px] text-text-mute">
                  <MetaStat label="Receptor" value={selectedArchive.receptor} />
                  <MetaStat label="Tier" value={selectedArchive.tier} />
                  <MetaStat label="iPTM" value={selectedArchive.iptm.toFixed(3)} />
                  <MetaStat label="SI" value={selectedArchive.selectivity_index?.toFixed(2) ?? '—'} />
                </div>
              </div>
            ) : (
              <p className="mt-3 text-xs text-text-mute">Archive에서 후보를 클릭하면 여기에 표시됩니다.</p>
            )}
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <label htmlFor="manual-sequence" className="text-xs font-semibold text-text-base">수동 입력</label>
          <textarea
            id="manual-sequence"
            value={sequenceInput}
            onChange={(event) => setSequenceInput(event.target.value)}
            rows={3}
            placeholder={DEFAULT_SEQUENCE}
            className="w-full rounded-xl border border-border-base bg-bg px-3 py-2 font-mono text-sm text-text-base outline-none transition-colors focus:border-border-strong"
          />
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px]">
            <span className={sequenceError ? 'text-[var(--neg)]' : 'text-text-mute'}>
              {sequenceError ?? `validated sequence: ${normalizedSequence || '—'}`}
            </span>
            <span className="text-text-dim">길이 14aa, Cys3-Cys14 필수</span>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-border-base bg-bg-elev p-4">
        <SectionHeader
          title="Section 2: Receptor + Params"
          description="수용체는 기본 off 상태이며, 실행 전 사용자가 명시적으로 선택해야 합니다."
        />
        <div className="mt-4 grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
          <div className="rounded-xl border border-border-base bg-bg p-4">
            <h3 className="text-xs font-semibold text-text-base">Receptors</h3>
            <div className="mt-3 space-y-2">
              {RECEPTORS.map((receptor) => {
                const checked = selectedReceptors.includes(receptor)
                return (
                  <label key={receptor} className="flex items-center justify-between rounded-lg border border-border-base bg-bg px-3 py-2 text-xs text-text-base">
                    <span>{receptor}</span>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleReceptor(receptor, setSelectedReceptors)}
                      className="h-4 w-4 accent-[color:var(--accent)]"
                    />
                  </label>
                )
              })}
            </div>
          </div>

          <div className="rounded-xl border border-border-base bg-bg p-4">
            <h3 className="text-xs font-semibold text-text-base">FlexPepDock Config</h3>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <NumberField
                label="cycles"
                value={config.cycles}
                min={1}
                max={200}
                onChange={(value) => setConfig((prev) => ({ ...prev, cycles: value }))}
              />
              <NumberField
                label="nstruct"
                value={config.nstruct}
                min={1}
                max={500}
                onChange={(value) => setConfig((prev) => ({ ...prev, nstruct: value }))}
              />
              <div className="space-y-1.5">
                <label className="text-[11px] font-medium text-text-mute">flex_pep_freedom</label>
                <select
                  value={config.flex_pep_freedom}
                  onChange={(event) => setConfig((prev) => ({ ...prev, flex_pep_freedom: event.target.value as FlexPepDockConfig['flex_pep_freedom'] }))}
                  className="w-full rounded-lg border border-border-base bg-bg px-3 py-2 text-sm text-text-base outline-none focus:border-border-strong"
                >
                  <option value="low">low</option>
                  <option value="med">med</option>
                  <option value="high">high</option>
                </select>
              </div>
              <NumberField
                label="ddg_cycle"
                value={config.ddg_cycle}
                min={1}
                max={50}
                onChange={(value) => setConfig((prev) => ({ ...prev, ddg_cycle: value }))}
              />
            </div>
          </div>
        </div>
      </section>

      <LargeJobWarningBanner
        nstruct={config.nstruct}
        nReceptors={selectedReceptors.length}
        cycles={config.cycles}
      />

      <section className="rounded-xl border border-border-base bg-bg-elev p-4">
        <SectionHeader
          title="Section 3: 실행 + 진행"
          description="POST 응답 ETA를 먼저 표시하고, 이후 polling으로 eta_seconds와 progress를 갱신합니다."
        />
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleRun}
            disabled={!canRun}
            className="inline-flex items-center gap-2 rounded-xl border border-[var(--pos)]/30 bg-[var(--pos-soft)] px-4 py-2 text-xs font-semibold text-emerald-200 transition-colors hover:bg-[var(--pos-soft)] disabled:cursor-not-allowed disabled:border-border-base disabled:bg-bg disabled:text-text-dim"
          >
            {createJob.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTubeDiagonal className="h-4 w-4" />}
            Run FlexPepDock Selectivity
          </button>
          <span className="text-xs text-text-mute">ETA {formatEta(etaSeconds)}</span>
          {queuePosition > 0 && <span className="text-xs text-text-mute">queue position #{queuePosition}</span>}
        </div>

        {currentJob ? (
          <div className="mt-4 rounded-xl border border-border-base bg-bg p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="font-mono text-text-base">{currentJob.job_id}</div>
              <JobStatusBadge job={currentJob} />
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-bg-sunk">
              <div
                className="h-full rounded-full bg-[color:var(--accent)] transition-all"
                style={{ width: `${Math.max(0, Math.min(100, Math.round(currentJob.progress * 100)))}%` }}
              />
            </div>
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-text-mute">
              <span>progress {(currentJob.progress * 100).toFixed(0)}%</span>
              <span>ETA {formatEta(currentJob.eta_seconds)}</span>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-xs text-text-mute">실행된 job이 아직 없습니다.</p>
        )}
      </section>

      <section className="rounded-xl border border-border-base bg-bg-elev p-4">
        <SectionHeader
          title="Section 4: 결과"
          description="완료된 job의 selectivity matrix와 downstream export 액션입니다."
        />
        {!resultsQuery.data ? (
          <p className="mt-4 text-xs text-text-mute">job 완료 후 결과가 여기에 표시됩니다.</p>
        ) : (
          <div className="mt-4 space-y-4">
            {activeResultIsStub && (
              <div className="flex items-center gap-2 rounded-xl border border-[var(--warn)]/30 bg-[var(--warn-soft)] px-3 py-2 text-xs text-[var(--warn)]">
                <span className="text-sm">⚠</span>
                <span>
                  <strong>STUB 결과</strong> — PyRosetta 미설치 또는 timeout 시 생성된 임의값(구 router 시기)입니다.
                  실 FlexPepDock 결과로 가정하지 마세요.
                </span>
              </div>
            )}
            <div className="overflow-hidden rounded-xl border border-border-base">
              <table className="w-full text-xs">
                <thead className="bg-bg-sunk text-[10px] uppercase tracking-[0.14em] text-text-dim">
                  <tr>
                    <th className="px-3 py-2 text-left">Receptor</th>
                    <th className="px-3 py-2 text-right">ΔG</th>
                    <th className="px-3 py-2 text-right">interface_score</th>
                    <th className="px-3 py-2 text-center">pass</th>
                    <th className="px-3 py-2 text-center">source</th>
                  </tr>
                </thead>
                <tbody>
                  {resultsQuery.data.selectivity_matrix.map((row) => (
                    <tr key={row.receptor} className="border-t border-border-base">
                      <td className="px-3 py-2 font-mono text-text-base">{row.receptor}</td>
                      <td className="px-3 py-2 text-right font-mono text-text-mute">{row.dG_kcal_mol.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right font-mono text-text-mute">{row.interface_score.toFixed(2)}</td>
                      <td className="px-3 py-2 text-center">{row.pass ? 'PASS' : 'FAIL'}</td>
                      <td className="px-3 py-2 text-center">
                        {row.stub ? (
                          <StubBadge title={row.stub_reason} />
                        ) : (
                          <RealBadge />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="rounded-xl border border-border-base bg-bg px-4 py-3 text-sm text-text-base">
              Selectivity Index <span className="ml-2 font-mono">{resultsQuery.data.selectivity_index.toFixed(2)}</span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <ActionButton onClick={handleExportCsv} icon={<FileSpreadsheet className="h-4 w-4" />}>
                CSV Export
              </ActionButton>
              <ActionButton
                as="link"
                href={activeJobId ? `/api/flexpepdock/jobs/${activeJobId}/ensemble.tar.gz` : '#'}
                icon={<Download className="h-4 w-4" />}
                disabled={!activeJobId}
              >
                PDB ensemble Download
              </ActionButton>
              <ActionButton
                onClick={handleCreateWetlabOrder}
                icon={createWetlabOrder.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
                disabled={!activeJobId || createWetlabOrder.isPending}
              >
                Wetlab Order 생성
              </ActionButton>
            </div>
            {wetlabMessage && <p className="text-xs text-text-mute">{wetlabMessage}</p>}
          </div>
        )}
      </section>

      <section className="rounded-xl border border-border-base bg-bg-elev p-4">
        <SectionHeader
          title="Job 리스트"
          description="영구 retention 정책 기준으로 완료 job도 계속 표시합니다."
        />
        {jobsQuery.isLoading ? (
          <div className="mt-4 flex items-center gap-2 text-xs text-text-mute">
            <Loader2 className="h-4 w-4 animate-spin" />
            job 목록을 불러오는 중입니다.
          </div>
        ) : jobs.length === 0 ? (
          <p className="mt-4 text-xs text-text-mute">등록된 FlexPepDock job이 없습니다.</p>
        ) : (
          <div className="mt-4 overflow-hidden rounded-xl border border-border-base">
            <table className="w-full text-xs">
              <thead className="bg-bg-sunk text-[10px] uppercase tracking-[0.14em] text-text-dim">
                <tr>
                  <th className="px-3 py-2 text-left">job</th>
                  <th className="px-3 py-2 text-left">sequence</th>
                  <th className="px-3 py-2 text-left">receptors</th>
                  <th className="px-3 py-2 text-center">status</th>
                  <th className="px-3 py-2 text-center">source</th>
                  <th className="px-3 py-2 text-right">ETA</th>
                  <th className="px-3 py-2 text-right">action</th>
                </tr>
              </thead>
              <tbody>
                {jobs.slice().reverse().map((job) => {
                  const cancellable = job.status === 'queued' || job.status === 'running'
                  const selected = job.job_id === activeJobId
                  const stubStatus = job.status === 'done' ? stubStatusByJob[job.job_id] : undefined
                  return (
                    <tr
                      key={job.job_id}
                      className={`border-t border-border-base ${selected ? 'bg-[color:var(--accent)]/10' : ''}`}
                    >
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => setActiveJobId(job.job_id)}
                          className="font-mono text-left text-text-base hover:text-[color:var(--accent)]"
                        >
                          {job.job_id}
                        </button>
                      </td>
                      <td className="px-3 py-2 font-mono text-text-mute">{job.sequence}</td>
                      <td className="px-3 py-2 text-text-mute">{job.receptors.join(', ')}</td>
                      <td className="px-3 py-2 text-center"><JobStatusBadge job={job} /></td>
                      <td className="px-3 py-2 text-center">
                        {stubStatus === true && <StubBadge />}
                        {stubStatus === false && <RealBadge />}
                        {stubStatus === undefined && <span className="text-[11px] text-text-dim">—</span>}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-text-mute">{formatEta(job.eta_seconds)}</td>
                      <td className="px-3 py-2 text-right">
                        {cancellable ? (
                          <button
                            type="button"
                            onClick={() => cancelJob.mutate(job.job_id)}
                            disabled={cancelJob.isPending}
                            className="inline-flex items-center gap-1 rounded border border-[var(--neg)]/30 bg-[var(--neg-soft)] px-2 py-1 text-[11px] text-[var(--neg)] hover:bg-[var(--neg-soft)] disabled:opacity-60"
                          >
                            {cancelJob.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Square className="h-3.5 w-3.5" />}
                            취소
                          </button>
                        ) : (
                          <span className="text-[11px] text-text-dim">retain</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

function validateSequence(sequence: string): string | null {
  if (!sequence) return 'sequence를 입력하세요.'
  if (sequence.length !== 14) return 'sequence는 정확히 14aa여야 합니다.'
  if (/[^ACDEFGHIKLMNPQRSTVWY]/.test(sequence)) return '허용되지 않은 아미노산 문자가 포함되어 있습니다.'
  if (sequence[2] !== 'C') return '3번 위치는 Cys(C)여야 합니다.'
  if (sequence[13] !== 'C') return '14번 위치는 Cys(C)여야 합니다.'
  return null
}

function toggleReceptor(
  receptor: FlexPepDockReceptor,
  setSelected: Dispatch<SetStateAction<FlexPepDockReceptor[]>>,
) {
  setSelected((prev) => prev.includes(receptor) ? prev.filter((item) => item !== receptor) : [...prev, receptor])
}

function formatEta(etaSeconds: number) {
  if (!etaSeconds || etaSeconds < 0) return '—'
  const hours = Math.floor(etaSeconds / 3600)
  const minutes = Math.round((etaSeconds % 3600) / 60)
  if (hours > 0) return `~${hours}h ${minutes}m`
  return `~${minutes}m`
}

/** Job 리스트·진행 카드 공통 상태 칩 (classifyJobStatus 기반) */
function JobStatusBadge({ job }: { job: Pick<FlexPepDockJobSummary, 'status' | 'error_message'> }) {
  const { label, Icon, spinIcon, badgeClassName } = classifyJobStatus(job)
  return (
    <span className={badgeClassName} title={`status: ${job.status}`}>
      <Icon className={`h-3.5 w-3.5 shrink-0 ${spinIcon ? 'animate-spin' : ''}`} aria-hidden />
      {label}
    </span>
  )
}

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-text-base">{title}</h2>
      <p className="mt-1 text-[11px] text-text-mute">{description}</p>
    </div>
  )
}

function MetaStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border-base bg-bg px-2 py-2">
      <div className="text-[10px] uppercase tracking-[0.14em] text-text-dim">{label}</div>
      <div className="mt-1 font-mono text-text-base">{value}</div>
    </div>
  )
}

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  onChange: (value: number) => void
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-[11px] font-medium text-text-mute">{label}</label>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="w-full rounded-lg border border-border-base bg-bg px-3 py-2 text-sm text-text-base outline-none focus:border-border-strong"
      />
    </div>
  )
}

/** 예상 소요 시간(초) = n_receptors × nstruct × cycles × ~30s */
export function computeEstimatedSeconds(nReceptors: number, nstruct: number, cycles: number): number {
  return nReceptors * nstruct * cycles * 30
}

/** nstruct>20 또는 receptors>2 선택 시 amber 경고 배너 */
export function LargeJobWarningBanner({
  nstruct,
  nReceptors,
  cycles,
}: {
  nstruct: number
  nReceptors: number
  cycles: number
}) {
  const isLargeJob = nstruct > 20 || nReceptors > 2
  if (!isLargeJob) return null

  const estimatedSeconds = computeEstimatedSeconds(nReceptors, nstruct, cycles)
  const estimatedHours = (estimatedSeconds / 3600).toFixed(1)

  return (
    <div
      role="alert"
      aria-label="대형 잡 경고"
      className="flex items-start gap-2 rounded-xl border border-[var(--warn)]/40 bg-[var(--warn-soft)] px-3 py-2.5 text-xs text-[var(--warn)]"
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
      <div className="space-y-0.5">
        <p className="font-semibold">
          이 잡은 ~{estimatedHours}h 예상. 적은 nstruct/receptors로 시작 권장.
        </p>
        <p className="text-[11px] opacity-80">
          최대 6h timeout (환경 변수 <code>FLEXPEPDOCK_TIMEOUT</code>으로 조정). 대형 잡은 큐 대기 시간이 길어질 수 있습니다.
        </p>
      </div>
    </div>
  )
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-[var(--neg)]/30 bg-[var(--neg-soft)] px-3 py-2 text-xs text-[var(--neg)]">
      <XCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
      <span>{message}</span>
    </div>
  )
}

function ActionButton({
  children,
  icon,
  onClick,
  disabled,
  as = 'button',
  href,
}: {
  children: ReactNode
  icon: ReactNode
  onClick?: () => void
  disabled?: boolean
  as?: 'button' | 'link'
  href?: string
}) {
  const className = 'inline-flex items-center gap-2 rounded-xl border border-border-base bg-bg px-3 py-2 text-xs font-medium text-text-base transition-colors hover:bg-bg-sunk disabled:cursor-not-allowed disabled:text-text-dim'
  if (as === 'link') {
    return (
      <a href={disabled ? undefined : href} className={className} aria-disabled={disabled}>
        {icon}
        {children}
      </a>
    )
  }
  return (
    <button type="button" onClick={onClick} disabled={disabled} className={className}>
      {icon}
      {children}
    </button>
  )
}

/**
 * stub 결과 배지 — PyRosetta 미설치 / timeout 시 생성된 임의값 표시.
 * title prop으로 stub_reason 툴팁 제공 가능.
 */
function StubBadge({ title }: { title?: string }) {
  return (
    <span
      title={title ? `stub 원인: ${title}` : '구 router 시기 stub 결과 (실 PyRosetta 아님)'}
      className="inline-flex items-center gap-1 rounded-full bg-[var(--warn-soft)] px-2 py-0.5 text-[10px] font-semibold text-[var(--warn)]"
    >
      ⚠ STUB
    </span>
  )
}

/** 실 PyRosetta 계산 결과 배지. */
function RealBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-[var(--pos-soft)] px-2 py-0.5 text-[10px] font-semibold text-[var(--pos)]">
      ✓ PyRosetta
    </span>
  )
}
