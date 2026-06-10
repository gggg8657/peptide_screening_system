import { Play, Square, Loader2, FlaskConical, AlertCircle, ChevronDown, ChevronUp, FlaskRound } from 'lucide-react'
import { useState } from 'react'
import { cn } from '../lib/utils'
import { HelpTooltip } from './ui/HelpTooltip'
import type { ExperimentState, FeatureToggles } from '../hooks/useExperiment'

const VALIDATION_PRESETS = [
  { value: 1,  label: 'Off',      desc: 'No multi-trial validation' },
  { value: 3,  label: '3 Quick',  desc: '~10 min extra' },
  { value: 5,  label: '5 Std',    desc: '~15 min extra' },
  { value: 10, label: '10 Paper', desc: '~30 min extra' },
]

const OBJECTIVE_MODES = [
  { value: 'auto', label: 'Auto' },
  { value: 'ddg_only', label: 'ΔG Only' },
  { value: 'ddg_plus_constraints', label: 'ΔG + Constraints' },
]

const FEATURE_META: Record<keyof FeatureToggles, { label: string; desc: string; tag: string }> = {
  cross_run_dedup: {
    label: 'Cross-Run Dedup',
    desc: 'Skip sequences already tested in prior runs',
    tag: 'Efficiency',
  },
  bandit_guidance: {
    label: 'Bandit Guidance',
    desc: 'Data-driven mutation position selection (Thompson Sampling)',
    tag: 'Optimization',
  },
  convergence_detection: {
    label: 'Convergence Detection',
    desc: 'Statistical test (Mann-Whitney U) to detect ΔG plateau',
    tag: 'Statistics',
  },
  disulfide_constraint: {
    label: 'Disulfide Constraint',
    desc: 'Enforce Cys3-Cys14 SS bond during FlexPepDock refinement',
    tag: 'Structural',
  },
  admet_gate: {
    label: 'ADMET Gate',
    desc: 'Druglikeness + nephrotoxicity risk scoring for PRRT',
    tag: 'Pharma',
  },
  sar_analysis: {
    label: 'SAR Analysis',
    desc: 'Position-specific mutation impact heatmap from history',
    tag: 'Analysis',
  },
}

const TAG_COLORS: Record<string, string> = {
  Efficiency: 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30',
  Optimization: 'bg-[var(--violet-soft)] text-[var(--violet)] border-[var(--violet)]/30',
  Statistics: 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30',
  Structural: 'bg-[var(--warn-soft)] text-[var(--warn)] border-[var(--warn)]/30',
  Pharma: 'bg-rose-500/20 text-[var(--neg)] border-rose-500/30',
  Analysis: 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30',
}

interface ExperimentControlProps {
  experiment: ExperimentState
  iteration: number
  totalIterations: number
}

export function ExperimentControl({ experiment, iteration, totalIterations }: ExperimentControlProps) {
  const { config, models, running, runId, error, setConfig, toggleFeature, startExperiment, stopExperiment } = experiment
  const [showFeatures, setShowFeatures] = useState(false)

  const enabledCount = Object.values(config.features).filter(Boolean).length
  const totalCount = Object.keys(config.features).length

  return (
    <section className="card border border-[var(--border)] animate-slide-in" aria-label="Experiment Control">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          <FlaskConical className="w-4 h-4 text-[var(--accent)]" />
          Experiment Control
          <HelpTooltip title="Experiment Control">
            <p>새로운 실험을 설정하고 실행합니다.</p>
            <p><strong>Iteration 수</strong>: 진화 루프 반복 횟수.</p>
            <p><strong>목적함수</strong>: ΔG Only (결합에너지만) 또는 ΔG + Constraints (약리학적 제약 포함).</p>
            <p><strong>LLM 모델</strong>: 서열 생성에 사용할 언어 모델 선택.</p>
          </HelpTooltip>
        </h2>
        {running && runId && (
          <div className="flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 text-[var(--accent)] animate-spin" />
            <span className="text-xs text-[var(--accent)] font-mono">
              {runId} &middot; iter {iteration}/{totalIterations}
            </span>
          </div>
        )}
      </div>

      {/* Progress bar when running */}
      {running && totalIterations > 0 && (
        <div className="h-1 bg-[var(--bg-elev)] rounded-full mb-4 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-700"
            style={{ width: `${Math.round((iteration / totalIterations) * 100)}%` }}
          />
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-3 items-end">
        {/* Iterations */}
        <div className="space-y-1">
          <label htmlFor="exp-iterations" className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold" title="Planner-Critic feedback loop count. Each iteration generates candidates, docks them, and refines the hypothesis.">
            Iterations
          </label>
          <div className="flex items-center gap-2">
            <input
              id="exp-iterations"
              type="number"
              min={1} max={999}
              value={config.max_iterations}
              onChange={e => setConfig({ max_iterations: Math.max(1, Number(e.target.value) || 1) })}
              disabled={running}
              className="w-16 text-xs font-mono bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg px-2 py-1 text-[var(--accent)] focus:border-cyan-500 focus:outline-none disabled:opacity-40 text-center"
            />
            <span className="text-[10px] text-[var(--text-mute)] leading-tight">mutate-dock-score loops</span>
          </div>
        </div>

        {/* Candidates */}
        <div className="space-y-1">
          <label htmlFor="exp-candidates" className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold" title="Number of peptide mutant variants generated per iteration. Each candidate undergoes FlexPepDock refinement and ΔG scoring.">
            Candidates
          </label>
          <div className="flex items-center gap-2">
            <input
              id="exp-candidates"
              type="range"
              min={2} max={32}
              value={config.n_candidates}
              onChange={e => setConfig({ n_candidates: Number(e.target.value) })}
              disabled={running}
              className="flex-1 h-1.5 bg-[var(--bg-sunk)] rounded-full appearance-none cursor-pointer accent-cyan-500 disabled:opacity-40"
            />
            <span className="text-xs font-mono text-[var(--accent)] w-5 text-right">{config.n_candidates}</span>
          </div>
          <p className="text-[10px] text-[var(--text-mute)] leading-tight">mutants per iteration</p>
        </div>

        {/* Top-K */}
        <div className="space-y-1">
          <label htmlFor="exp-topk" className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold" title="After QC gating, the top-K candidates by ΔG are passed to the Critic agent for analysis and to the next iteration as seed sequences.">
            Top-K
          </label>
          <div className="flex items-center gap-2">
            <input
              id="exp-topk"
              type="range"
              min={1} max={20}
              value={config.top_k}
              onChange={e => setConfig({ top_k: Number(e.target.value) })}
              disabled={running}
              className="flex-1 h-1.5 bg-[var(--bg-sunk)] rounded-full appearance-none cursor-pointer accent-cyan-500 disabled:opacity-40"
            />
            <span className="text-xs font-mono text-[var(--accent)] w-5 text-right">{config.top_k}</span>
          </div>
          <p className="text-[10px] text-[var(--text-mute)] leading-tight">best passed to critic</p>
        </div>

        {/* LLM Model dropdown */}
        <div className="space-y-1">
          <label htmlFor="exp-llm-model" className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold">
            LLM Model
          </label>
          <select
            id="exp-llm-model"
            value={config.llm_model}
            onChange={e => setConfig({ llm_model: e.target.value })}
            disabled={running}
            className="w-full text-xs bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg px-2 py-1.5 text-[var(--text-mute)] focus:border-cyan-500 focus:outline-none disabled:opacity-40 cursor-pointer"
          >
            {models.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        {/* Objective mode */}
        <div className="space-y-1">
          <label className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold">
            Objective
          </label>
          <div className="flex gap-1">
            {OBJECTIVE_MODES.map(mode => (
              <button
                key={mode.value}
                onClick={() => setConfig({ objective_mode: mode.value })}
                disabled={running}
                className={cn(
                  'px-2 py-1 rounded text-[10px] font-medium transition-all border',
                  config.objective_mode === mode.value
                    ? 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
                    : 'bg-[var(--bg-elev)] text-[var(--text-dim)] border-[var(--border)] hover:border-[var(--border)]',
                  running && 'opacity-40 cursor-not-allowed'
                )}
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>

        {/* Validation Trials */}
        <div className="space-y-1">
          <label className="text-[10px] text-[var(--text-mute)] uppercase tracking-wider font-semibold flex items-center gap-1" title="Multi-trial validation for final candidates. Higher trial counts reduce FlexPepDock stochastic variance via top-3 mean aggregation.">
            <FlaskRound className="w-2.5 h-2.5" />
            Validation
          </label>
          <div className="flex gap-1 flex-wrap">
            {VALIDATION_PRESETS.map(preset => (
              <button
                key={preset.value}
                onClick={() => setConfig({ validation_n_trials: preset.value })}
                disabled={running}
                title={preset.desc}
                className={cn(
                  'px-1.5 py-1 rounded text-[10px] font-medium transition-all border',
                  config.validation_n_trials === preset.value
                    ? 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
                    : 'bg-[var(--bg-elev)] text-[var(--text-dim)] border-[var(--border)] hover:border-[var(--border)]',
                  running && 'opacity-40 cursor-not-allowed'
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Run / Stop buttons */}
        <div className="flex gap-2 items-end">
          {!running ? (
            <button
              onClick={() => startExperiment()}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30 hover:bg-[var(--pos-soft)] transition-all"
            >
              <Play className="w-3.5 h-3.5" />
              Run
            </button>
          ) : (
            <button
              onClick={stopExperiment}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-[var(--neg-soft)] text-[var(--neg)] border border-[var(--neg)]/30 hover:bg-[var(--neg-soft)] transition-all"
            >
              <Square className="w-3 h-3" />
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Feature Toggles - collapsible */}
      <div className="mt-3 border-t border-[var(--border)] pt-2">
        <button
          onClick={() => setShowFeatures(!showFeatures)}
          className="flex items-center gap-1.5 text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-semibold hover:text-[var(--text-dim)] transition-colors w-full"
        >
          {showFeatures ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          Add-on Features
          <span className="text-[10px] font-mono text-[var(--text-mute)] ml-1">
            ({enabledCount}/{totalCount} on)
          </span>
        </button>

        {showFeatures && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
            {(Object.entries(FEATURE_META) as [keyof FeatureToggles, typeof FEATURE_META[keyof FeatureToggles]][]).map(
              ([key, meta]) => (
                <button
                  key={key}
                  onClick={() => toggleFeature(key)}
                  disabled={running}
                  role="switch"
                  aria-checked={config.features[key]}
                  aria-label={meta.label}
                  className={cn(
                    'flex flex-col gap-0.5 p-2 rounded-lg border text-left transition-all',
                    config.features[key]
                      ? 'bg-[var(--bg-elev)] border-[var(--accent)]/30'
                      : 'bg-[var(--bg)] border-[var(--border)] opacity-60',
                    running && 'cursor-not-allowed opacity-40'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-semibold text-[var(--text-mute)]">{meta.label}</span>
                    <div className="flex items-center gap-1.5">
                      <span className={cn(
                        'text-[10px] px-1.5 py-0.5 rounded-full border font-medium',
                        TAG_COLORS[meta.tag] ?? 'bg-[var(--bg-sunk)] text-[var(--text-dim)] border-[var(--border)]'
                      )}>
                        {meta.tag}
                      </span>
                      <div className={cn(
                        'w-6 h-3 rounded-full transition-colors relative',
                        config.features[key] ? 'bg-cyan-500' : 'bg-[var(--bg-sunk)]'
                      )}>
                        <div className={cn(
                          'absolute top-0.5 w-2 h-2 rounded-full bg-white transition-transform',
                          config.features[key] ? 'translate-x-3' : 'translate-x-0.5'
                        )} />
                      </div>
                    </div>
                  </div>
                  <span className="text-[10px] text-[var(--text-mute)] leading-tight">{meta.desc}</span>
                </button>
              ),
            )}
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-[var(--neg)]">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          {error}
        </div>
      )}
    </section>
  )
}
