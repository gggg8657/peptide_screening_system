import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Loader2, Play, Save } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { PipelineFlow } from '../components/dashboard/PipelineFlow'
import { TierBadge } from '../components/dashboard/TierBadge'
import { usePipelineContext } from '../contexts/PipelineContext'
import { usePredictedPassRates, useRunStatus, useSettings, useStartRun, useUpdateSettings, type Silo } from '../hooks/dashboard'

type LauncherSilo = Silo

type LauncherGates = {
  plddt_mean: number
  plddt_interface: number
  docking_top_percent: number
  rosetta_ddg_max: number
  selectivity_margin_max: number
  boltz_iptm_margin_min: number
  stability_half_life_min: number
}

const DEFAULT_GATES: LauncherGates = {
  plddt_mean: 60,
  plddt_interface: 45,
  docking_top_percent: 20,
  rosetta_ddg_max: -1,
  selectivity_margin_max: -10,
  boltz_iptm_margin_min: 0,
  stability_half_life_min: 50,
}

const DEFAULT_OFF_TARGETS = ['SSTR1', 'SSTR3', 'SSTR4', 'SSTR5']
const OFF_TARGET_META = {
  SSTR1: { uniprot: 'P30872', pdb: '9IK8' },
  SSTR3: { uniprot: 'P32745', pdb: '8XIR' },
  SSTR4: { uniprot: 'P31391', pdb: '7WYV' },
  SSTR5: { uniprot: 'P35346', pdb: '9IKC' },
} as const
type OffTargetName = keyof typeof OFF_TARGET_META
type RunStartResponse = { run_id: string }

export function RunLauncherPage() {
  const navigate = useNavigate()
  const live = usePipelineContext()

  const settingsQuery = useSettings()
  const updateSettings = useUpdateSettings()
  const startRun = useStartRun()

  const requestedRunId = live.viewingArchive ?? (live.runId || undefined)
  const statusQuery = useRunStatus(requestedRunId)
  const predictorRunId = requestedRunId ?? statusQuery.data?.run_id
  const predictedQuery = usePredictedPassRates(predictorRunId)

  const [hydrated, setHydrated] = useState(false)
  const [silo, setSilo] = useState<LauncherSilo>('B')
  const [name, setName] = useState('local_20260514_iter03')
  const [iterations, setIterations] = useState(3)
  const [nBackbone, setNBackbone] = useState(10)
  const [kSeq, setKSeq] = useState(8)
  const [topM, setTopM] = useState(10)
  const [llm, setLlm] = useState('qwen3.5-35b-a3b')
  const [seed, setSeed] = useState(42)
  const [mutationStrategy, setMutationStrategy] = useState<'ga_bo' | 'enumerate' | 'sampling'>('ga_bo')
  const [boltzCross, setBoltzCross] = useState(true)
  const [offTargets, setOffTargets] = useState<Set<string>>(new Set(DEFAULT_OFF_TARGETS))
  const [gates, setGates] = useState<LauncherGates>(DEFAULT_GATES)
  const [banner, setBanner] = useState<string | null>(null)

  const normalizedSettings = useMemo(() => normalizeSettings(settingsQuery.data), [settingsQuery.data])

  useEffect(() => {
    if (hydrated) return
    if (!normalizedSettings) return
    /* eslint-disable react-hooks/set-state-in-effect */
    setIterations(normalizedSettings.iterations)
    setTopM(normalizedSettings.topM)
    setLlm(normalizedSettings.llm)
    setGates(normalizedSettings.gates)
    setOffTargets(new Set(normalizedSettings.offTargets))
    setBoltzCross(normalizedSettings.boltzCross)
    setHydrated(true)
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [hydrated, normalizedSettings])

  const designSpace = silo === 'A' ? nBackbone * kSeq : 240
  const etaMinutes = iterations * ((silo === 'A' ? 32 : 28) + (boltzCross ? 8 : 0))
  const predictedRates = normalizePredicted(predictedQuery.data)

  function toggleOffTarget(receptor: string) {
    setOffTargets((current) => {
      const next = new Set(current)
      if (next.has(receptor)) next.delete(receptor)
      else next.add(receptor)
      return next
    })
  }

  async function handleSaveConfig() {
    try {
      await updateSettings.mutateAsync({
        max_iterations: iterations,
        top_k: topM,
        llm_model: llm,
      })
      setBanner('legacy /api/settings 기본값을 저장했습니다. gate/off-target 변경은 런치 payload에만 반영됩니다.')
    } catch (error) {
      setBanner(error instanceof Error ? error.message : 'settings 저장에 실패했습니다.')
    }
  }

  async function handleStartRun() {
    setBanner(null)
    if (offTargets.size === 0) {
      setBanner('off-target receptor를 최소 1개 선택해야 합니다.')
      return
    }

    try {
      const response = await startRun.mutateAsync({
        name,
        silo,
        iterations,
        seed,
        n_backbone: nBackbone,
        k_seq_per_backbone: kSeq,
        top_m_rosetta: topM,
        llm_model: llm,
        mutation_strategy: mutationStrategy,
        off_targets: [...offTargets],
        boltz_cross_enabled: boltzCross,
        gates,
      }) as RunStartResponse
      setBanner(`run ${response.run_id} 시작 요청을 전송했습니다.`)
      navigate(`/console?run_id=${response.run_id}`)
    } catch (error) {
      setBanner(error instanceof Error ? error.message : 'run 시작에 실패했습니다.')
    }
  }

  return (
    <div className="rounded-xl border border-border-base bg-bg">
      <header className="flex flex-wrap items-center gap-3 border-b border-border-base bg-bg-elev px-5 py-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold text-text-base">새 실행 · run launcher</h1>
            <span className="rounded border border-border-base px-2 py-0.5 text-[10px] text-text-mute">iter03 draft</span>
          </div>
          <p className="mt-1 text-[11px] text-text-mute">실행 전 gate, LLM, off-target, design space를 한 화면에서 검토합니다.</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={handleSaveConfig}
            disabled={updateSettings.isPending}
            className="inline-flex items-center gap-1 rounded border border-border-base px-3 py-1.5 text-[11px] text-text-mute transition-colors hover:bg-bg-sunk hover:text-text-base disabled:opacity-60"
          >
            {updateSettings.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
            save config
          </button>
          <button
            type="button"
            onClick={handleStartRun}
            disabled={startRun.isPending}
            className="inline-flex items-center gap-1 rounded border border-pos bg-pos px-3 py-1.5 text-[11px] font-semibold text-white transition-opacity disabled:opacity-60"
          >
            {startRun.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            실행 시작
          </button>
        </div>
      </header>

      {banner && (
        <div className="border-b border-border-base bg-bg-elev px-5 py-3 text-[11px] text-text-mute">
          {banner}
        </div>
      )}

      <div className="grid gap-5 px-6 py-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          <Panel title="1 · Identity">
            <div className="grid gap-3 md:grid-cols-3">
              <Field label="Run name">
                <input value={name} onChange={(event) => setName(event.target.value)} className="w-full rounded border border-border-base bg-bg px-3 py-2 font-mono text-xs text-text-base outline-none transition-colors focus:border-accent" />
              </Field>
              <Field label="Iterations">
                <input type="number" min={1} max={20} value={iterations} onChange={(event) => setIterations(clampInt(event.target.value, 1, 20))} className="w-full rounded border border-border-base bg-bg px-3 py-2 font-mono text-xs text-text-base outline-none transition-colors focus:border-accent" />
              </Field>
              <Field label="Seed">
                <input type="number" min={0} value={seed} onChange={(event) => setSeed(clampInt(event.target.value, 0, 2147483647))} className="w-full rounded border border-border-base bg-bg px-3 py-2 font-mono text-xs text-text-base outline-none transition-colors focus:border-accent" />
              </Field>
            </div>
          </Panel>

          <Panel title="2 · Silo · 파이프라인 전략">
            <div className="grid gap-3 lg:grid-cols-2">
              <SiloCard
                active={silo === 'A'}
                onClick={() => setSilo('A')}
                id="A"
                name="De Novo"
                tools={['RFdiffusion', 'ProteinMPNN', 'ESMFold', 'Boltz-2']}
                pros="다양성 ↑ · novel scaffold"
                cons="합성 난도 ↑"
              />
              <SiloCard
                active={silo === 'B'}
                onClick={() => setSilo('B')}
                id="B"
                name="Mutation+Dock"
                tools={['BLOSUM62 + LLM', 'DiffDock', 'Boltz-2', 'PyRosetta']}
                pros="안정성 ↑ · 합성 가능성 ↑"
                cons="탐색 다양성 제한"
              />
            </div>
            <div className="mt-3 rounded border border-border-base bg-bg-sunk px-3 py-2 text-[11px] text-text-mute">
              Dual silo preview는 `PipelineFlow`에서 확인 가능하지만, 현재 `POST /api/runs/start` 백엔드 가드는 단일 silo (`A` 또는 `B`)만 허용합니다.
            </div>
          </Panel>

          <Panel title="3 · Generation 파라미터">
            <div className="space-y-3">
              {silo === 'A' && (
                <>
                  <RangeRow label="n_backbone" prefix="A" valueLabel={`${nBackbone} backbones`}>
                    <input type="range" min={2} max={30} value={nBackbone} onChange={(event) => setNBackbone(Number(event.target.value))} className="w-full accent-[var(--accent)]" />
                  </RangeRow>
                  <RangeRow label="k_seq / bb" prefix="A" valueLabel={`${kSeq} seq/bb`}>
                    <input type="range" min={1} max={32} value={kSeq} onChange={(event) => setKSeq(Number(event.target.value))} className="w-full accent-[var(--accent)]" />
                  </RangeRow>
                </>
              )}
              {silo === 'B' && (
                <div className="grid items-center gap-3 md:grid-cols-[120px_minmax(0,1fr)_140px]">
                  <span className="text-[11px] text-text-mute">mutation strategy</span>
                  <select value={mutationStrategy} onChange={(event) => setMutationStrategy(event.target.value as 'ga_bo' | 'enumerate' | 'sampling')} className="w-full rounded border border-border-base bg-bg px-3 py-2 text-xs text-text-base outline-none transition-colors focus:border-accent">
                    <option value="ga_bo">ga_bo · GA + Bayesian opt</option>
                    <option value="enumerate">enumerate · constrained search</option>
                    <option value="sampling">sampling · random constrained</option>
                  </select>
                  <span className="font-mono text-[11px] text-text-dim">silo B default</span>
                </div>
              )}
              <RangeRow label="top_m_rosetta" valueLabel={`${topM} for refine`}>
                <input type="range" min={1} max={30} value={topM} onChange={(event) => setTopM(Number(event.target.value))} className="w-full accent-[var(--accent)]" />
              </RangeRow>
              <div className="grid items-center gap-3 md:grid-cols-[120px_minmax(0,1fr)_140px]">
                <span className="text-[11px] text-text-mute">LLM model</span>
                <select value={llm} onChange={(event) => setLlm(event.target.value)} className="w-full rounded border border-border-base bg-bg px-3 py-2 text-xs text-text-base outline-none transition-colors focus:border-accent">
                  <optgroup label="vLLM (port 8000)">
                    <option value="qwen3.5-35b-a3b">Qwen3.5-35B-A3B · MoE Active 3B · 65K ctx · ⚡ 권장</option>
                  </optgroup>
                  <optgroup label="vLLM (port 8001) — CoT reasoning">
                    <option value="deepseek-r1-distill-32b">DeepSeek-R1-Distill-Qwen-32B · 32B · reasoning</option>
                  </optgroup>
                  <optgroup label="Ollama (Local)">
                    <option value="qwen3:32b">qwen3:32b · 20GB</option>
                    <option value="qwen3:30b-a3b">qwen3:30b-a3b · MoE Active 3B · 18GB</option>
                    <option value="deepseek-r1:70b">deepseek-r1:70b · CoT · 42GB</option>
                    <option value="llama4:scout">llama4:scout · 67GB</option>
                    <option value="qwen3:8b">qwen3:8b · 5.2GB (legacy)</option>
                  </optgroup>
                </select>
                <span className="font-mono text-[11px] text-text-dim">vLLM</span>
              </div>
            </div>
          </Panel>

          <Panel title="4 · Gate 임계값">
            <div className="grid gap-4 md:grid-cols-2">
              <GateSlider label="pLDDT (mean)" value={gates.plddt_mean} min={30} max={90} step={1} unit="" onChange={(value) => setGates((current) => ({ ...current, plddt_mean: value }))} />
              <GateSlider label="pLDDT (interface)" value={gates.plddt_interface} min={30} max={70} step={1} unit="" onChange={(value) => setGates((current) => ({ ...current, plddt_interface: value }))} />
              <GateSlider label="Docking top%" value={gates.docking_top_percent} min={5} max={50} step={1} unit="%" onChange={(value) => setGates((current) => ({ ...current, docking_top_percent: value }))} />
              <GateSlider label="Rosetta ddG" value={gates.rosetta_ddg_max} min={-5} max={0} step={0.1} unit="kcal/mol" onChange={(value) => setGates((current) => ({ ...current, rosetta_ddg_max: value }))} />
              <GateSlider label="Selectivity margin" value={gates.selectivity_margin_max} min={-30} max={0} step={0.5} unit="kcal/mol" onChange={(value) => setGates((current) => ({ ...current, selectivity_margin_max: value }))} />
              <GateSlider label="Boltz iPTM margin" value={gates.boltz_iptm_margin_min} min={-0.05} max={0.1} step={0.005} unit="" onChange={(value) => setGates((current) => ({ ...current, boltz_iptm_margin_min: value }))} />
              <GateSlider label="Stability t1/2" value={gates.stability_half_life_min} min={5} max={200} step={5} unit="h" onChange={(value) => setGates((current) => ({ ...current, stability_half_life_min: value }))} />
            </div>
          </Panel>

          <Panel title="5 · Off-target 수용체 · selectivity">
            <div className="flex flex-wrap gap-2">
              {(DEFAULT_OFF_TARGETS as OffTargetName[]).map((receptor) => (
                <button
                  key={receptor}
                  type="button"
                  onClick={() => toggleOffTarget(receptor)}
                  className={`rounded border px-3 py-2 text-left text-[11px] transition-colors ${
                    offTargets.has(receptor)
                      ? 'border-accent bg-accent-soft/50 text-accent-text'
                      : 'border-border-base bg-bg-sunk text-text-mute'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={offTargets.has(receptor)} readOnly className="accent-[var(--accent)]" />
                    <span className="font-mono font-semibold">{receptor}</span>
                  </div>
                  <div className="mt-1 text-[10px] text-text-dim">
                    {OFF_TARGET_META[receptor].uniprot} · {OFF_TARGET_META[receptor].pdb}
                  </div>
                </button>
              ))}
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-border-base pt-3 text-[11px] text-text-mute">
              <label className="inline-flex items-center gap-2">
                <input type="checkbox" checked={boltzCross} onChange={(event) => setBoltzCross(event.target.checked)} className="accent-[var(--accent)]" />
                step05c Boltz-2 cross-validation 활성
              </label>
              <span className="font-mono">+ ~8 min / iter</span>
            </div>
          </Panel>
        </div>

        <aside className="space-y-4 xl:sticky xl:top-5 xl:self-start">
          <Panel title="Plan · 사전 미리보기">
            <div className="space-y-2">
              <SummaryRow label="silo" value={silo === 'A' ? 'A · de novo' : 'B · mutation+dock'} />
              <SummaryRow label="design space" value={`~${designSpace}`} unit="seq" />
              <SummaryRow label="iterations" value={String(iterations)} unit="× iter" />
              <SummaryRow label="off-target" value={String(offTargets.size)} unit="receptors" />
              <SummaryRow label="LLM" value={llm} mono />
              <SummaryRow label="GPU" value="H100 NVL × 4" mono />
              <SummaryRow label="ETA" value={`${etaMinutes}m`} tone="accent" />
            </div>
            <div className="mt-4 rounded border border-border-base bg-bg-sunk p-3">
              <PipelineFlow silo={silo} runId={predictorRunId} />
            </div>
          </Panel>

          <Panel title="예상 게이트 통과율">
            {predictedQuery.isLoading ? (
              <div className="flex items-center gap-2 text-sm text-text-mute">
                <Loader2 className="h-4 w-4 animate-spin" />
                historical gate statistics 로딩 중…
              </div>
            ) : predictedRates.length > 0 ? (
              <div className="space-y-3">
                {predictedRates.map((rate) => (
                  <PredictBar key={rate.gate_id} label={`${rate.gate_id} ${rate.name}`} value={Math.round(rate.rate * 100)} warn={rate.warn} />
                ))}
                <div className="border-t border-border-base pt-3 text-[10px] text-text-dim">
                  based on {typeof (predictedQuery.data as { based_on?: string } | undefined)?.based_on === 'string'
                    ? (predictedQuery.data as { based_on?: string }).based_on
                    : predictorRunId ?? 'historical archive'}
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-2 rounded border border-border-base bg-bg-sunk px-3 py-2 text-[11px] text-text-mute">
                <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-warn" />
                <span>예측 통과율 데이터가 아직 없습니다. run archive가 생기면 우측 패널이 hydrate 됩니다.</span>
              </div>
            )}
          </Panel>

          <div className="rounded-xl border border-warn bg-warn-soft/40 px-4 py-3 text-[11px] leading-5 text-text-base">
            <div className="font-semibold text-warn">G3b 경고</div>
            <p className="mt-1">
              iPTM margin 게이트는 history 편차가 가장 큽니다. 기본값보다 보수적으로 조정하려면 오른쪽 예측값과 함께 `TierBadge` 변화를 비교한 뒤 시작하는 편이 안전합니다.
            </p>
            <div className="mt-2 flex items-center gap-2">
              <TierBadge tier="T2" />
              <span className="text-text-mute">target-selective 후보 기준선을 유지하면서 gate를 조정합니다.</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border-base bg-bg-elev">
      <div className="border-b border-border-base px-4 py-3">
        <h2 className="text-sm font-semibold text-text-base">{title}</h2>
      </div>
      <div className="p-4">{children}</div>
    </section>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-[11px] text-text-mute">
      <div className="mb-1 uppercase tracking-[0.18em] text-text-dim">{label}</div>
      {children}
    </label>
  )
}

function RangeRow({
  label,
  valueLabel,
  prefix,
  children,
}: {
  label: string
  valueLabel: string
  prefix?: string
  children: React.ReactNode
}) {
  return (
    <div className="grid items-center gap-3 md:grid-cols-[120px_minmax(0,1fr)_140px]">
      <span className="flex items-center gap-2 text-[11px] text-text-mute">
        {prefix && <span className="rounded bg-violet-soft px-1.5 py-0.5 font-mono text-[10px] text-violet">{prefix}</span>}
        {label}
      </span>
      {children}
      <span className="text-right font-mono text-[11px] font-semibold text-text-base">{valueLabel}</span>
    </div>
  )
}

function GateSlider({
  label,
  value,
  min,
  max,
  step,
  unit,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  step: number
  unit: string
  onChange: (value: number) => void
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[11px]">
        <span className="text-text-mute">{label}</span>
        <span className="font-mono font-semibold text-text-base">{value.toFixed(step < 1 ? 3 : 0)} {unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} className="w-full accent-[var(--accent)]" />
    </div>
  )
}

function SiloCard({
  active,
  onClick,
  id,
  name,
  tools,
  pros,
  cons,
}: {
  active: boolean
  onClick: () => void
  id: string
  name: string
  tools: string[]
  pros: string
  cons: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-xl border p-3 text-left transition-colors ${active ? 'border-accent bg-accent-soft/50' : 'border-border-base bg-bg-sunk hover:border-border-strong'}`}
    >
      <div className="flex items-center gap-2">
        <span className={`grid h-6 w-7 place-items-center rounded font-mono text-[10px] font-bold ${active ? 'bg-accent text-white' : 'bg-border-base text-text-base'}`}>
          {id}
        </span>
        <span className="text-sm font-semibold text-text-base">{name}</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {tools.map((tool) => (
          <span key={tool} className="rounded bg-bg px-1.5 py-0.5 font-mono text-[10px] text-text-mute">{tool}</span>
        ))}
      </div>
      <div className="mt-2 text-[11px] text-pos">+ {pros}</div>
      <div className="mt-1 text-[11px] text-neg">- {cons}</div>
    </button>
  )
}

function SummaryRow({
  label,
  value,
  unit,
  mono = false,
  tone,
}: {
  label: string
  value: string
  unit?: string
  mono?: boolean
  tone?: 'accent'
}) {
  return (
    <div className="flex items-baseline justify-between border-b border-dashed border-border-base pb-2 text-[11px]">
      <span className="text-text-mute">{label}</span>
      <span className={`${mono ? 'font-mono' : ''} font-semibold ${tone === 'accent' ? 'text-accent-text' : 'text-text-base'}`}>
        {value} {unit && <span className="font-normal text-text-dim">{unit}</span>}
      </span>
    </div>
  )
}

function PredictBar({ label, value, warn = false }: { label: string; value: number; warn?: boolean }) {
  const color = value > 80 ? 'var(--pos)' : value > 40 ? 'var(--accent)' : warn ? 'var(--warn)' : 'var(--neg)'
  return (
    <div>
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-text-mute">{label}</span>
        <span className="font-mono font-semibold text-text-base">{value}%</span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded bg-bg-sunk">
        <div className="h-full" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  )
}

function normalizeSettings(raw: unknown) {
  const payload = raw as Record<string, unknown> | undefined
  if (!payload) return null

  const gatesRaw = (payload.gates as Record<string, unknown> | undefined) ?? {}
  const receptors = Array.isArray(payload.off_target_receptors)
    ? (payload.off_target_receptors as Array<{ name?: string; enabled?: boolean }>)
        .filter((entry) => entry.enabled !== false && typeof entry.name === 'string')
        .map((entry) => entry.name as string)
    : DEFAULT_OFF_TARGETS

  return {
    iterations: numberValue(payload.max_iterations, 3),
    topM: numberValue(payload.top_k, 10),
    llm: typeof payload.llm_model === 'string' ? payload.llm_model : 'qwen3-32b',
    boltzCross: booleanValue(payload.boltz_cross_enabled, true),
    offTargets: receptors.length > 0 ? receptors : DEFAULT_OFF_TARGETS,
    gates: {
      plddt_mean: numberValue(gatesRaw.plddt_mean, DEFAULT_GATES.plddt_mean),
      plddt_interface: numberValue(gatesRaw.plddt_interface, DEFAULT_GATES.plddt_interface),
      docking_top_percent: numberValue(gatesRaw.docking_top_percent, DEFAULT_GATES.docking_top_percent),
      rosetta_ddg_max: numberValue(gatesRaw.rosetta_ddg_max, DEFAULT_GATES.rosetta_ddg_max),
      selectivity_margin_max: numberValue(gatesRaw.selectivity_margin_max, DEFAULT_GATES.selectivity_margin_max),
      boltz_iptm_margin_min: numberValue(gatesRaw.boltz_iptm_margin_min, DEFAULT_GATES.boltz_iptm_margin_min),
      stability_half_life_min: numberValue(gatesRaw.stability_half_life_min, DEFAULT_GATES.stability_half_life_min),
    },
  }
}

function normalizePredicted(raw: unknown) {
  const payload = raw as { predicted?: Array<{ gate_id: string; name: string; rate: number; warn?: boolean }> } | undefined
  return Array.isArray(payload?.predicted) ? payload.predicted : []
}

function numberValue(value: unknown, fallback: number) {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function booleanValue(value: unknown, fallback: boolean) {
  return typeof value === 'boolean' ? value : fallback
}

function clampInt(value: string, min: number, max: number) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return min
  return Math.max(min, Math.min(max, Math.round(parsed)))
}
