import { useState, useEffect, useCallback, useRef } from 'react'

export interface FeatureToggles {
  cross_run_dedup: boolean
  bandit_guidance: boolean
  convergence_detection: boolean
  disulfide_constraint: boolean
  admet_gate: boolean
  sar_analysis: boolean
}

export interface ExperimentConfig {
  max_iterations: number
  n_candidates: number
  top_k: number
  llm_model: string
  objective_mode: string
  validation_n_trials: number
  features: FeatureToggles
}

export interface ExperimentState {
  config: ExperimentConfig
  models: string[]
  running: boolean
  runId: string | null
  error: string | null
  setConfig: (patch: Partial<ExperimentConfig>) => void
  toggleFeature: (key: keyof FeatureToggles) => void
  startExperiment: (overrides?: Record<string, unknown>) => Promise<void>
  stopExperiment: () => Promise<void>
}

const DEFAULT_FEATURES: FeatureToggles = {
  cross_run_dedup: true,
  bandit_guidance: true,
  convergence_detection: true,
  disulfide_constraint: true,
  admet_gate: false,
  sar_analysis: false,
}

const DEFAULT_CONFIG: ExperimentConfig = {
  max_iterations: 5,
  n_candidates: 8,
  top_k: 5,
  llm_model: 'qwen3:8b',
  objective_mode: 'auto',
  validation_n_trials: 1,
  features: DEFAULT_FEATURES,
}

export function useExperiment(pollInterval = 3000): ExperimentState {
  const [config, setConfigState] = useState<ExperimentConfig>(DEFAULT_CONFIG)
  const [models, setModels] = useState<string[]>(['qwen3:8b'])
  const [running, setRunning] = useState(false)
  const [runId, setRunId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Fetch server-side defaults and available models on mount
  useEffect(() => {
    fetch('/api/experiment/config')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setConfigState(prev => ({ ...prev, ...data, features: prev.features })) })
      .catch(() => { setError('Failed to load experiment config') })

    fetch('/api/experiment/models')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.models?.length) setModels(data.models) })
      .catch(() => { setError('Failed to load available models') })
  }, [])

  // Poll experiment status while running
  useEffect(() => {
    const poll = () => {
      fetch('/api/experiment/status')
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data) {
            setRunning(data.running)
            if (data.run_id) setRunId(data.run_id)
            if (!data.running && data.exit_code !== undefined) {
              setRunning(false)
            }
          }
        })
        .catch(() => { setRunning(false) })
    }
    poll()
    intervalRef.current = setInterval(poll, pollInterval)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [pollInterval])

  const setConfig = useCallback((patch: Partial<ExperimentConfig>) => {
    setConfigState(prev => ({ ...prev, ...patch }))
  }, [])

  const toggleFeature = useCallback((key: keyof FeatureToggles) => {
    setConfigState(prev => ({
      ...prev,
      features: { ...prev.features, [key]: !prev.features[key] },
    }))
  }, [])

  const startExperiment = useCallback(async (overrides?: Record<string, unknown>) => {
    setError(null)
    try {
      const body = overrides ? { ...config, ...overrides } : config
      const res = await fetch('/api/experiment/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (data.error) {
        setError(data.error)
      } else {
        setRunning(true)
        setRunId(data.run_id)
      }
    } catch {
      setError('Failed to start experiment')
    }
  }, [config])

  const stopExperiment = useCallback(async () => {
    setError(null)
    try {
      const res = await fetch('/api/experiment/stop', { method: 'POST' })
      const data = await res.json()
      if (data.status === 'stopped' || data.status === 'not_running') {
        setRunning(false)
      }
    } catch {
      setError('Failed to stop experiment')
    }
  }, [])

  return { config, models, running, runId, error, setConfig, toggleFeature, startExperiment, stopExperiment }
}
