import { useState } from 'react'
import { Settings2, Play, Dna, FlaskConical, ArrowRight, ArrowLeftRight, Save, RotateCcw, Server } from 'lucide-react'
import { cn } from '../lib/utils'

type ExecutionStrategy = 'silo_b_only' | 'silo_a_only' | 'parallel' | 'silo_b_then_a' | 'silo_a_then_b'

interface PipelineSettings {
  executionStrategy: ExecutionStrategy
  ollamaHost: string
  // Silo B
  siloBIterations: number
  siloBCandidates: number
  siloBTopK: number
  siloBLlmModel: string
  siloBValidationTrials: number
  // Silo A
  siloABackbones: number
  siloASeqPerBackbone: number
  siloAPlddt: number
  siloADockThreshold: number
}

const DEFAULT_SETTINGS: PipelineSettings = {
  executionStrategy: 'silo_b_only',
  ollamaHost: 'http://localhost:11434',
  siloBIterations: 5,
  siloBCandidates: 8,
  siloBTopK: 5,
  siloBLlmModel: 'qwen3.5-35b-a3b',
  siloBValidationTrials: 1,
  siloABackbones: 10,
  siloASeqPerBackbone: 8,
  siloAPlddt: 70,
  siloADockThreshold: -8.0,
}

const EXECUTION_STRATEGIES: { value: ExecutionStrategy; label: string; icon: React.ReactNode; desc: string }[] = [
  {
    value: 'silo_b_only',
    label: 'Silo B Only',
    icon: <Dna className="w-4 h-4 text-[var(--accent)]" />,
    desc: 'PyRosetta mutation pipeline only. Fast local execution. No cloud API required.',
  },
  {
    value: 'silo_a_only',
    label: 'Silo A Only',
    icon: <FlaskConical className="w-4 h-4 text-[var(--violet)]" />,
    desc: 'Full 3-ARM local pipeline only. De novo backbone design.',
  },
  {
    value: 'parallel',
    label: 'Parallel (A + B)',
    icon: <ArrowLeftRight className="w-4 h-4 text-[var(--teal)]" />,
    desc: 'Both silos run simultaneously. Independent processes, shared StatusEmitter. Best for cross-silo validation.',
  },
  {
    value: 'silo_b_then_a',
    label: 'Silo B -> Silo A',
    icon: <ArrowRight className="w-4 h-4 text-[var(--warn)]" />,
    desc: 'Run Silo B first, then feed top candidates to Silo A for refinement.',
  },
  {
    value: 'silo_a_then_b',
    label: 'Silo A -> Silo B',
    icon: <ArrowRight className="w-4 h-4 text-[var(--warn)] rotate-180" />,
    desc: 'Run Silo A first (de novo design), then refine top hits with Silo B PyRosetta.',
  },
]

const VALIDATION_PRESETS = [
  { value: 1,  label: 'Off' },
  { value: 3,  label: '3 Quick' },
  { value: 5,  label: '5 Std' },
  { value: 10, label: '10 Paper' },
]

export function SettingsPage() {
  const [settings, setSettings] = useState<PipelineSettings>(DEFAULT_SETTINGS)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const update = <K extends keyof PipelineSettings>(key: K, value: PipelineSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    setSaved(false)
    setSaveError(null)
  }

  const handleSave = async () => {
    setSaveError(null)
    const payload = {
      execution_strategy:  settings.executionStrategy === 'silo_b_only' ? 'sequential' : 'parallel',
      max_iterations:      settings.siloBIterations,
      n_candidates:        settings.siloBCandidates,
      top_k:               settings.siloBTopK,
      llm_model:           settings.siloBLlmModel,
      validation_n_trials: settings.siloBValidationTrials,
      ollama_host:         settings.ollamaHost,
    }
    try {
      const res = await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const text = await res.text()
        setSaveError(`Save failed (${res.status}): ${text}`)
        return
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setSaveError(`Network error: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS)
    setSaved(false)
    setSaveError(null)
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <section className="card border border-border-base/80">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-bg-elev border border-border-base flex items-center justify-center">
              <Settings2 className="w-4 h-4 text-text-mute" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-text-base">Pipeline Settings</h2>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30 font-semibold">
                  LOCAL MODE
                </span>
              </div>
              <p className="text-xs text-text-mute">Execution strategy and pipeline parameters &mdash; all models run locally via Ollama</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {saveError && (
              <span className="text-[10px] text-[var(--neg)] max-w-xs truncate">{saveError}</span>
            )}
            <button
              onClick={handleReset}
              className="flex items-center gap-1 px-3 py-1.5 text-xs text-text-mute border border-border-base rounded-lg hover:border-border-strong transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              Reset
            </button>
            <button
              onClick={handleSave}
              className={cn(
                'flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all',
                saved
                  ? 'bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30'
                  : 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30 hover:bg-[var(--accent-soft)]'
              )}
            >
              <Save className="w-3 h-3" />
              {saved ? 'Saved!' : 'Save Settings'}
            </button>
          </div>
        </div>
      </section>

      {/* Local Runtime Configuration */}
      <section className="card border border-[var(--pos)]/30">
        <div className="flex items-center gap-2 mb-3">
          <Server className="w-4 h-4 text-[var(--pos)]" />
          <h3 className="text-sm font-semibold text-text-mute uppercase tracking-widest">
            Local Runtime
          </h3>
        </div>
        <div className="space-y-1 max-w-sm">
          <label htmlFor="settings-ollama-host" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">
            Ollama Host
          </label>
          <input
            id="settings-ollama-host"
            type="text"
            value={settings.ollamaHost}
            onChange={e => update('ollamaHost', e.target.value)}
            placeholder="http://localhost:11434"
            className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-3 py-2 text-text-mute focus:border-green-500 focus:outline-none placeholder:text-text-dim"
          />
          <p className="text-[10px] text-text-mute">
            Ollama API endpoint for local LLM inference. Ensure Ollama is running before starting the pipeline.
          </p>
        </div>
      </section>

      {/* Execution Strategy */}
      <section className="card border border-border-base/80">
        <h3 className="text-sm font-semibold text-text-mute uppercase tracking-widest mb-3">
          Execution Strategy
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {EXECUTION_STRATEGIES.map(strat => (
            <button
              key={strat.value}
              onClick={() => update('executionStrategy', strat.value)}
              className={cn(
                'flex items-start gap-2.5 p-3 rounded-lg border text-left transition-all',
                settings.executionStrategy === strat.value
                  ? 'bg-[var(--accent-soft)] border-[var(--accent)]/30'
                  : 'bg-bg-elev border-border-base hover:border-border-base'
              )}
            >
              <div className="flex-shrink-0 mt-0.5">{strat.icon}</div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-text-base">{strat.label}</span>
                  {settings.executionStrategy === strat.value && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30">
                      selected
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-text-mute mt-0.5 leading-relaxed">{strat.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Silo B Parameters */}
      <section className="card border border-[var(--accent)]/30">
        <div className="flex items-center gap-2 mb-3">
          <Dna className="w-4 h-4 text-[var(--accent)]" />
          <h3 className="text-sm font-semibold text-text-mute uppercase tracking-widest">
            Silo B: PyRosetta Parameters
          </h3>
          {settings.executionStrategy === 'silo_a_only' && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-bg-elev text-text-mute border border-border-base">
              disabled in current strategy
            </span>
          )}
        </div>
        <div className={cn(
          'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4',
          settings.executionStrategy === 'silo_a_only' && 'opacity-40 pointer-events-none'
        )}>
          <div className="space-y-1">
            <label htmlFor="settings-silob-iterations" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">Iterations</label>
            <input
              id="settings-silob-iterations"
              type="number" min={1} max={999}
              value={settings.siloBIterations}
              onChange={e => update('siloBIterations', Math.max(1, Number(e.target.value) || 1))}
              className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-2 py-1.5 text-[var(--accent)] focus:border-cyan-500 focus:outline-none text-center"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="settings-silob-candidates" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">Candidates/iter</label>
            <input
              id="settings-silob-candidates"
              type="number" min={2} max={32}
              value={settings.siloBCandidates}
              onChange={e => update('siloBCandidates', Math.max(2, Number(e.target.value) || 8))}
              className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-2 py-1.5 text-[var(--accent)] focus:border-cyan-500 focus:outline-none text-center"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="settings-silob-topk" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">Top-K</label>
            <input
              id="settings-silob-topk"
              type="number" min={1} max={20}
              value={settings.siloBTopK}
              onChange={e => update('siloBTopK', Math.max(1, Number(e.target.value) || 5))}
              className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-2 py-1.5 text-[var(--accent)] focus:border-cyan-500 focus:outline-none text-center"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="settings-silob-llm" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">LLM Model</label>
            <input
              id="settings-silob-llm"
              type="text"
              value={settings.siloBLlmModel}
              onChange={e => update('siloBLlmModel', e.target.value)}
              className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-2 py-1.5 text-[var(--accent)] focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">Validation Trials</label>
            <div className="flex gap-1">
              {VALIDATION_PRESETS.map(p => (
                <button
                  key={p.value}
                  onClick={() => update('siloBValidationTrials', p.value)}
                  className={cn(
                    'flex-1 py-1.5 rounded text-[10px] font-medium border transition-all',
                    settings.siloBValidationTrials === p.value
                      ? 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
                      : 'bg-bg-elev text-text-mute border-border-base hover:border-border-base'
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Silo A Parameters */}
      <section className="card border border-[var(--violet)]/30">
        <div className="flex items-center gap-2 mb-3">
          <FlaskConical className="w-4 h-4 text-[var(--violet)]" />
          <h3 className="text-sm font-semibold text-text-mute uppercase tracking-widest">
            Silo A: 3-ARM Pipeline Parameters
          </h3>
          {settings.executionStrategy === 'silo_b_only' && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-bg-elev text-text-mute border border-border-base">
              disabled in current strategy
            </span>
          )}
        </div>
        <div className={cn(
          'grid grid-cols-2 md:grid-cols-4 gap-4',
          settings.executionStrategy === 'silo_b_only' && 'opacity-40 pointer-events-none'
        )}>
          <div className="space-y-1">
            <label htmlFor="settings-siloa-backbones" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">Backbones</label>
            <input
              id="settings-siloa-backbones"
              type="number" min={1} max={100}
              value={settings.siloABackbones}
              onChange={e => update('siloABackbones', Math.max(1, Number(e.target.value) || 10))}
              className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-2 py-1.5 text-[var(--violet)] focus:border-purple-500 focus:outline-none text-center"
            />
            <p className="text-[10px] text-text-mute">RFdiffusion backbone count</p>
          </div>
          <div className="space-y-1">
            <label htmlFor="settings-siloa-seq-per-backbone" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">Seq/Backbone</label>
            <input
              id="settings-siloa-seq-per-backbone"
              type="number" min={1} max={32}
              value={settings.siloASeqPerBackbone}
              onChange={e => update('siloASeqPerBackbone', Math.max(1, Number(e.target.value) || 8))}
              className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-2 py-1.5 text-[var(--violet)] focus:border-purple-500 focus:outline-none text-center"
            />
            <p className="text-[10px] text-text-mute">ProteinMPNN designs per backbone</p>
          </div>
          <div className="space-y-1">
            <label htmlFor="settings-siloa-plddt" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">pLDDT Gate</label>
            <input
              id="settings-siloa-plddt"
              type="number" min={50} max={95}
              value={settings.siloAPlddt}
              onChange={e => update('siloAPlddt', Math.max(50, Number(e.target.value) || 70))}
              className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-2 py-1.5 text-[var(--violet)] focus:border-purple-500 focus:outline-none text-center"
            />
            <p className="text-[10px] text-text-mute">ESMFold confidence threshold</p>
          </div>
          <div className="space-y-1">
            <label htmlFor="settings-siloa-dock" className="text-[10px] text-text-mute uppercase tracking-wider font-semibold">Dock Threshold</label>
            <input
              id="settings-siloa-dock"
              type="number" step={0.5}
              value={settings.siloADockThreshold}
              onChange={e => update('siloADockThreshold', Number(e.target.value) || -8.0)}
              className="w-full text-xs font-mono bg-bg-elev border border-border-base rounded-lg px-2 py-1.5 text-[var(--violet)] focus:border-purple-500 focus:outline-none text-center"
            />
            <p className="text-[10px] text-text-mute">DiffDock score cutoff</p>
          </div>
        </div>
      </section>

      {/* Run Pipeline */}
      <section className="card border border-border-base/80">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-text-base">Run Pipeline</h3>
            <p className="text-xs text-text-mute mt-0.5">
              Strategy: <span className="text-[var(--accent)] font-medium">
                {EXECUTION_STRATEGIES.find(s => s.value === settings.executionStrategy)?.label}
              </span>
              <span className="text-[var(--pos)] ml-2 text-[10px]">LOCAL MODE</span>
            </p>
          </div>
          <button
            className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30 hover:bg-[var(--pos-soft)] transition-all"
          >
            <Play className="w-4 h-4" />
            Start Pipeline
          </button>
        </div>
      </section>
    </div>
  )
}
