import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { Beaker, Check, FlaskConical, Loader2, Play, Send, SlidersHorizontal, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

type StrategyId = 'blosum' | 'esm_scan' | 'proteinmpnn' | 'dual_b1_b2'
type ProteinMPNNMode = 'peptide_only' | 'receptor_context'

type StrategyMeta = {
  id: StrategyId
  name: string
  description: string
  supports_modes: string[]
  supports_complex_pdb: boolean
}

type ProteinMPNNOptions = {
  modes: { id: ProteinMPNNMode; label: string }[]
  complex_pdbs: string[]
}

type StrategyRunStatus = {
  job_id: string
  strategy: StrategyId
  mode: string | null
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  eta_seconds: number
  message: string
}

type StrategyVariant = {
  id: string
  sequence: string
  score: number
  source_strategy: StrategyId
  mode: string | null
  complex_pdb: string | null
  rank: number
  selected: boolean
  rejected: boolean
  annotations: Record<string, unknown>
}

const API_BASE = '/api'
const STRATEGY_LABELS: Record<StrategyId, string> = {
  blosum: 'BLOSUM',
  esm_scan: 'ESM Scan',
  proteinmpnn: 'ProteinMPNN',
  dual_b1_b2: 'Dual B1/B2',
}

export function StrategyRunnerPage() {
  const navigate = useNavigate()
  const [strategies, setStrategies] = useState<StrategyMeta[]>([])
  const [options, setOptions] = useState<ProteinMPNNOptions>({ modes: [], complex_pdbs: [] })
  const [strategy, setStrategy] = useState<StrategyId>('proteinmpnn')
  const [mode, setMode] = useState<ProteinMPNNMode>('peptide_only')
  const [complexPdb, setComplexPdb] = useState('')
  const [maxVariants, setMaxVariants] = useState(8)
  const [numSeqPerTarget, setNumSeqPerTarget] = useState(4)
  const [temperature, setTemperature] = useState(0.1)
  const [jobId, setJobId] = useState<string | null>(null)
  const [runStatus, setRunStatus] = useState<StrategyRunStatus | null>(null)
  const [variants, setVariants] = useState<StrategyVariant[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [rejectedIds, setRejectedIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)
  const [savingSelection, setSavingSelection] = useState(false)
  const [banner, setBanner] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    async function loadInitial() {
      try {
        const [strategyResp, optionsResp] = await Promise.all([
          fetch(`${API_BASE}/strategies`),
          fetch(`${API_BASE}/strategies/proteinmpnn/options`),
        ])
        if (!strategyResp.ok) throw new Error(`strategies ${strategyResp.status}`)
        if (!optionsResp.ok) throw new Error(`proteinmpnn options ${optionsResp.status}`)
        const strategyData = await strategyResp.json() as StrategyMeta[]
        const optionsData = await optionsResp.json() as ProteinMPNNOptions
        if (!alive) return
        setStrategies(strategyData)
        setOptions(optionsData)
        setComplexPdb(optionsData.complex_pdbs[0] ?? '')
      } catch (error) {
        if (alive) setBanner(error instanceof Error ? error.message : 'strategy metadata 로딩 실패')
      }
    }
    loadInitial()
    return () => { alive = false }
  }, [])

  useEffect(() => {
    if (!jobId) return
    let alive = true
    async function poll() {
      try {
        const statusResp = await fetch(`${API_BASE}/strategies/runs/${jobId}`)
        if (!statusResp.ok) throw new Error(`run status ${statusResp.status}`)
        const statusData = await statusResp.json() as StrategyRunStatus
        if (!alive) return
        setRunStatus(statusData)
        if (statusData.status === 'completed') {
          const variantsResp = await fetch(`${API_BASE}/strategies/runs/${jobId}/variants`)
          if (!variantsResp.ok) throw new Error(`variants ${variantsResp.status}`)
          const variantData = await variantsResp.json() as StrategyVariant[]
          if (!alive) return
          setVariants(variantData)
          setSelectedIds(new Set(variantData.filter((item) => item.selected).map((item) => item.id)))
          setRejectedIds(new Set(variantData.filter((item) => item.rejected).map((item) => item.id)))
        }
      } catch (error) {
        if (alive) setBanner(error instanceof Error ? error.message : 'run status 갱신 실패')
      }
    }
    poll()
    const timer = window.setInterval(poll, 1500)
    return () => {
      alive = false
      window.clearInterval(timer)
    }
  }, [jobId])

  const selectedVariants = useMemo(
    () => variants.filter((variant) => selectedIds.has(variant.id)),
    [selectedIds, variants],
  )

  const compositePayload = useMemo(() => ({
    source: 'strategy_runner',
    job_id: jobId,
    variants: selectedVariants.map((variant) => ({
      id: variant.id,
      sequence: variant.sequence,
      score: variant.score,
      strategy: variant.source_strategy,
      mode: variant.mode,
      complex_pdb: variant.complex_pdb,
    })),
  }), [jobId, selectedVariants])

  async function handleRun() {
    setBanner(null)
    if (strategy === 'proteinmpnn' && mode === 'receptor_context' && !complexPdb) {
      setBanner('receptor_context mode는 complex_pdb 선택이 필요합니다.')
      return
    }
    setLoading(true)
    setVariants([])
    setSelectedIds(new Set())
    setRejectedIds(new Set())
    try {
      const response = await fetch(`${API_BASE}/strategies/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategy,
          mode: strategy === 'proteinmpnn' ? mode : null,
          complex_pdb: strategy === 'proteinmpnn' && mode === 'receptor_context' ? complexPdb : null,
          max_variants: maxVariants,
          num_seq_per_target: numSeqPerTarget,
          config: { temperature },
        }),
      })
      if (!response.ok) throw new Error(await response.text())
      const data = await response.json() as { job_id: string; eta_seconds: number }
      setJobId(data.job_id)
      setBanner(`run ${data.job_id} 생성 완료`)
    } catch (error) {
      setBanner(error instanceof Error ? error.message : 'strategy 실행 실패')
    } finally {
      setLoading(false)
    }
  }

  function toggleSelected(id: string) {
    setSelectedIds((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
    setRejectedIds((current) => {
      const next = new Set(current)
      next.delete(id)
      return next
    })
  }

  function toggleRejected(id: string) {
    setRejectedIds((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
    setSelectedIds((current) => {
      const next = new Set(current)
      next.delete(id)
      return next
    })
  }

  async function saveSelection() {
    if (!jobId) return
    setSavingSelection(true)
    setBanner(null)
    try {
      const response = await fetch(`${API_BASE}/strategies/runs/${jobId}/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_variant_ids: [...selectedIds],
          rejected_variant_ids: [...rejectedIds],
        }),
      })
      if (!response.ok) throw new Error(await response.text())
      setBanner(`selected ${selectedIds.size}개, rejected ${rejectedIds.size}개 저장 완료`)
    } catch (error) {
      setBanner(error instanceof Error ? error.message : 'variant 선택 저장 실패')
    } finally {
      setSavingSelection(false)
    }
  }

  async function createWetlabOrder() {
    const variant = selectedVariants[0]
    if (!variant) {
      setBanner('wetlab order 생성 전 variant를 1개 이상 채택해야 합니다.')
      return
    }
    try {
      const response = await fetch(`${API_BASE}/wetlab/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: variant.id,
          candidate_seq: variant.sequence,
        }),
      })
      if (!response.ok) throw new Error(await response.text())
      const order = await response.json() as { id: string }
      navigate(`/wetlab/orders/${order.id}`)
    } catch (error) {
      setBanner(error instanceof Error ? error.message : 'wetlab order 생성 실패')
    }
  }

  return (
    <div className="rounded-xl border border-border-base bg-bg">
      <header className="flex flex-wrap items-center gap-3 border-b border-border-base bg-bg-elev px-5 py-3">
        <div>
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-accent" />
            <h1 className="text-sm font-semibold text-text-base">Strategy Runner</h1>
          </div>
          <p className="mt-1 text-[11px] text-text-mute">mode, complex, variant 채택 여부를 명시해서 실행합니다.</p>
        </div>
        <button
          type="button"
          onClick={handleRun}
          disabled={loading}
          className="ml-auto inline-flex items-center gap-1 rounded border border-pos bg-pos px-3 py-1.5 text-[11px] font-semibold text-white transition-opacity disabled:opacity-60"
        >
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
          Run
        </button>
      </header>

      {banner && (
        <div className="border-b border-border-base bg-bg-elev px-5 py-3 text-[11px] text-text-mute">
          {banner}
        </div>
      )}

      <div className="grid gap-5 px-6 py-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-4">
          <Panel title="1 · Strategy">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {(strategies.length ? strategies : fallbackStrategies()).map((item) => (
                <button
                  type="button"
                  key={item.id}
                  onClick={() => setStrategy(item.id)}
                  className={`min-h-32 rounded border px-4 py-3 text-left transition-colors ${
                    strategy === item.id
                      ? 'border-accent bg-accent-soft text-text-base'
                      : 'border-border-base bg-bg hover:border-border-strong'
                  }`}
                >
                  <span className="flex items-center gap-2 text-xs font-semibold">
                    <FlaskConical className="h-3.5 w-3.5" />
                    {STRATEGY_LABELS[item.id]}
                  </span>
                  <span className="mt-2 block text-[11px] leading-5 text-text-mute">{item.description}</span>
                </button>
              ))}
            </div>
          </Panel>

          {strategy === 'proteinmpnn' && (
            <Panel title="2 · ProteinMPNN options">
              <div className="grid gap-4 lg:grid-cols-2">
                <Field label="Mode">
                  <div className="inline-flex rounded border border-border-base bg-bg-sunk p-1">
                    {(['peptide_only', 'receptor_context'] as ProteinMPNNMode[]).map((item) => (
                      <button
                        type="button"
                        key={item}
                        onClick={() => setMode(item)}
                        className={`rounded px-3 py-1.5 text-[11px] transition-colors ${
                          mode === item ? 'bg-bg-elev text-text-base shadow-sm' : 'text-text-mute hover:text-text-base'
                        }`}
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                </Field>
                <Field label="complex_pdb">
                  <select
                    value={complexPdb}
                    onChange={(event) => setComplexPdb(event.target.value)}
                    disabled={mode !== 'receptor_context'}
                    className="w-full rounded border border-border-base bg-bg px-3 py-2 font-mono text-xs text-text-base outline-none transition-colors focus:border-accent disabled:opacity-50"
                  >
                    <option value="">complex_pdb 선택</option>
                    {options.complex_pdbs.map((path) => (
                      <option key={path} value={path}>{path}</option>
                    ))}
                  </select>
                </Field>
              </div>
            </Panel>
          )}

          <Panel title="3 · Config">
            <div className="grid gap-3 md:grid-cols-3">
              <Field label="max_variants">
                <NumberInput min={1} max={96} value={maxVariants} onChange={setMaxVariants} />
              </Field>
              <Field label="num_seq_per_target">
                <NumberInput min={1} max={128} value={numSeqPerTarget} onChange={setNumSeqPerTarget} />
              </Field>
              <Field label="temperature">
                <input
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={temperature}
                  onChange={(event) => setTemperature(clampNumber(event.target.value, 0, 1))}
                  className="w-full rounded border border-border-base bg-bg px-3 py-2 font-mono text-xs text-text-base outline-none transition-colors focus:border-accent"
                />
              </Field>
            </div>
          </Panel>

          <Panel title="4 · Variants">
            {variants.length === 0 ? (
              <div className="rounded border border-border-base bg-bg-sunk px-4 py-8 text-center text-xs text-text-mute">
                Run 실행 후 생성된 variants가 표시됩니다.
              </div>
            ) : (
              <div className="overflow-hidden rounded border border-border-base">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-border-base bg-bg-sunk text-[10px] uppercase tracking-wide text-text-mute">
                    <tr>
                      <th className="px-3 py-2">Rank</th>
                      <th className="px-3 py-2">Variant</th>
                      <th className="px-3 py-2">Score</th>
                      <th className="px-3 py-2">채택</th>
                      <th className="px-3 py-2">거부</th>
                    </tr>
                  </thead>
                  <tbody>
                    {variants.map((variant) => (
                      <tr key={variant.id} className="border-b border-border-base last:border-b-0">
                        <td className="px-3 py-2 font-mono text-text-mute">{variant.rank}</td>
                        <td className="px-3 py-2">
                          <div className="font-mono text-text-base">{variant.sequence}</div>
                          <div className="mt-0.5 font-mono text-[10px] text-text-mute">{variant.id}</div>
                        </td>
                        <td className="px-3 py-2 font-mono text-text-base">{variant.score.toFixed(3)}</td>
                        <td className="px-3 py-2">
                          <CheckBox checked={selectedIds.has(variant.id)} onChange={() => toggleSelected(variant.id)} label="채택" />
                        </td>
                        <td className="px-3 py-2">
                          <CheckBox checked={rejectedIds.has(variant.id)} onChange={() => toggleRejected(variant.id)} label="거부" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>

        <aside className="space-y-4">
          <Panel title="Run status">
            <div className="space-y-3 text-xs">
              <KeyValue label="job_id" value={jobId ?? '-'} mono />
              <KeyValue label="status" value={runStatus?.status ?? '-'} />
              <div>
                <div className="mb-1 flex justify-between text-[11px] text-text-mute">
                  <span>progress</span>
                  <span>{runStatus?.progress ?? 0}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded bg-bg-sunk">
                  <div className="h-full bg-accent transition-all" style={{ width: `${runStatus?.progress ?? 0}%` }} />
                </div>
              </div>
              <KeyValue label="message" value={runStatus?.message ?? '-'} />
            </div>
          </Panel>

          <Panel title="Selection handoff">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <Metric label="selected" value={selectedIds.size} />
                <Metric label="rejected" value={rejectedIds.size} />
              </div>
              <button
                type="button"
                onClick={saveSelection}
                disabled={!jobId || savingSelection}
                className="inline-flex w-full items-center justify-center gap-1 rounded border border-accent bg-accent px-3 py-2 text-[11px] font-semibold text-white transition-opacity disabled:opacity-50"
              >
                {savingSelection ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                선택 저장
              </button>
              <button
                type="button"
                onClick={() => setBanner(`composite_scorer payload ready: ${selectedVariants.length} variants`)}
                disabled={selectedVariants.length === 0}
                className="inline-flex w-full items-center justify-center gap-1 rounded border border-border-base px-3 py-2 text-[11px] text-text-base transition-colors hover:bg-bg-sunk disabled:opacity-50"
              >
                <Send className="h-3.5 w-3.5" />
                composite_scorer 입력
              </button>
              <button
                type="button"
                onClick={createWetlabOrder}
                disabled={selectedVariants.length === 0}
                className="inline-flex w-full items-center justify-center gap-1 rounded border border-border-base px-3 py-2 text-[11px] text-text-base transition-colors hover:bg-bg-sunk disabled:opacity-50"
              >
                <Beaker className="h-3.5 w-3.5" />
                wetlab order 생성
              </button>
              <pre className="max-h-60 overflow-auto rounded border border-border-base bg-bg-sunk p-3 text-[10px] leading-5 text-text-mute">
                {JSON.stringify(compositePayload, null, 2)}
              </pre>
            </div>
          </Panel>
        </aside>
      </div>
    </div>
  )
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded border border-border-base bg-bg-elev">
      <div className="border-b border-border-base px-4 py-2">
        <h2 className="text-xs font-semibold text-text-base">{title}</h2>
      </div>
      <div className="p-4">{children}</div>
    </section>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[10px] font-medium uppercase tracking-wide text-text-mute">{label}</span>
      {children}
    </label>
  )
}

function NumberInput({ min, max, value, onChange }: { min: number; max: number; value: number; onChange: (value: number) => void }) {
  return (
    <input
      type="number"
      min={min}
      max={max}
      value={value}
      onChange={(event) => onChange(clampInt(event.target.value, min, max))}
      className="w-full rounded border border-border-base bg-bg px-3 py-2 font-mono text-xs text-text-base outline-none transition-colors focus:border-accent"
    />
  )
}

function CheckBox({ checked, onChange, label }: { checked: boolean; onChange: () => void; label: string }) {
  return (
    <label className="inline-flex items-center gap-2 text-[11px] text-text-mute">
      <input type="checkbox" checked={checked} onChange={onChange} className="h-4 w-4 accent-[var(--accent)]" />
      <span className="sr-only">{label}</span>
      {checked ? <Check className="h-3.5 w-3.5 text-pos" /> : <X className="h-3.5 w-3.5 text-text-mute" />}
    </label>
  )
}

function KeyValue({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-text-mute">{label}</div>
      <div className={`mt-1 break-all text-text-base ${mono ? 'font-mono text-[11px]' : 'text-xs'}`}>{value}</div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded border border-border-base bg-bg-sunk px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-text-mute">{label}</div>
      <div className="mt-1 font-mono text-lg font-semibold text-text-base">{value}</div>
    </div>
  )
}

function clampInt(raw: string, min: number, max: number) {
  const parsed = Number.parseInt(raw, 10)
  if (Number.isNaN(parsed)) return min
  return Math.min(max, Math.max(min, parsed))
}

function clampNumber(raw: string, min: number, max: number) {
  const parsed = Number.parseFloat(raw)
  if (Number.isNaN(parsed)) return min
  return Math.min(max, Math.max(min, parsed))
}

function fallbackStrategies(): StrategyMeta[] {
  return [
    { id: 'blosum', name: 'BLOSUM', description: 'Conservative substitution scan.', supports_modes: [], supports_complex_pdb: false },
    { id: 'esm_scan', name: 'ESM Scan', description: 'ESM-guided mutation scan.', supports_modes: [], supports_complex_pdb: false },
    { id: 'proteinmpnn', name: 'ProteinMPNN', description: 'ProteinMPNN sequence design.', supports_modes: ['peptide_only', 'receptor_context'], supports_complex_pdb: true },
    { id: 'dual_b1_b2', name: 'Dual B1/B2', description: 'Dual branch strategy.', supports_modes: [], supports_complex_pdb: false },
  ]
}
