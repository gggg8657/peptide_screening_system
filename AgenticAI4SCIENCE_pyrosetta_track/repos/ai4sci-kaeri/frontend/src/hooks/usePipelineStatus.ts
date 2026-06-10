import { useState, useEffect, useCallback, useRef } from 'react'
import type {
  PipelineStep,
  RosettaSubstep,
  StepStatus,
  ExecutionMode,
  Agent,
  Candidate,
  QCGate,
  ConvergencePoint,
  TimelineEvent,
  VisualizationImage,
} from '../types'

export interface LiveApiStatus {
  esmfold: string
  molmim: string
}

export interface MoleculeData {
  id: string
  smiles: string
  qed: number
}

export interface BestCandidate {
  id: string
  sequence: string
  ddG: number
  totalScore: number
}

export interface ArchivedRun {
  run_id: string
  started_at: string
  completed: boolean
  iteration: number
  total_iterations: number
  n_candidates: number
  best_ddg: number | null
  label?: string
  llm_model?: string
}

export interface PipelineStatus {
  executionMode: ExecutionMode
  runId: string
  startedAt: string
  updatedAt: string
  iteration: number
  totalIterations: number
  llmModel: string
  target: string
  reference: string
  steps: PipelineStep[]
  rosettaSubsteps: RosettaSubstep[]
  timeline: TimelineEvent[]
  agents: Agent[]
  candidates: Candidate[]
  historicalCandidates: Candidate[]
  qcGates: QCGate[]
  convergence: ConvergencePoint[]
  liveApis: LiveApiStatus
  bestCandidate: BestCandidate | null
  molecules: MoleculeData[]
  visualizationImages: VisualizationImage[]
  completed: boolean
  connected: boolean
  error: string | null
  // Run history
  archivedRuns: ArchivedRun[]
  viewingArchive: string | null
}

const INITIAL_STATE: PipelineStatus = {
  executionMode: 'full',
  runId: '',
  startedAt: '',
  updatedAt: '',
  iteration: 0,
  totalIterations: 5,
  llmModel: '',
  target: '',
  reference: '',
  steps: [],
  rosettaSubsteps: [],
  timeline: [],
  agents: [],
  candidates: [],
  historicalCandidates: [],
  qcGates: [],
  convergence: [],
  liveApis: { esmfold: 'pending', molmim: 'pending' },
  bestCandidate: null,
  molecules: [],
  visualizationImages: [],
  completed: false,
  connected: false,
  error: null,
  archivedRuns: [],
  viewingArchive: null,
}

function normalizeStepStatus(rawStatus: unknown): StepStatus {
  if (rawStatus === 'completed') return 'completed'
  if (rawStatus === 'failed') return 'failed'
  if (rawStatus === 'running' || rawStatus === 'active') return 'running'
  return 'pending'
}

function detectExecutionMode(runId: string, steps: PipelineStep[]): ExecutionMode {
  if (runId.startsWith('sst14_mutdock_')) {
    return 'pyrosettaOnly'
  }

  const hasStep06ActiveOrCompleted = steps.some(
    step =>
      step.id === 'step06' &&
      (step.status === 'running' || step.status === 'completed')
  )
  const onlyStep06Relevant = steps.every(
    step =>
      step.id === 'step06' ||
      step.status === 'pending'
  )

  if (hasStep06ActiveOrCompleted && onlyStep06Relevant) {
    return 'pyrosettaOnly'
  }

  return 'full'
}

function filterStepsForMode(steps: PipelineStep[], mode: ExecutionMode): PipelineStep[] {
  if (mode !== 'pyrosettaOnly') return steps
  const filtered = steps.filter(
    step => step.id === 'step06' || (step.id === 'step07' && step.status !== 'pending')
  )
  return filtered.length > 0 ? filtered : steps
}

function mapCandidate(c: Record<string, unknown>, fallbackSource: 'live' | 'historical'): Candidate {
  const siloSource = c.silo_source as string | undefined
  const resolvedSource: Candidate['source'] =
    siloSource === 'silo_a' || siloSource === 'silo_b'
      ? siloSource
      : fallbackSource
  return {
    rank: (c.rank as number) ?? 0,
    id: (c.id as string) ?? '',
    sequence: (c.sequence as string) ?? '',
    ddG: (c.ddG as number) ?? 0,
    totalScore: (c.totalScore as number) ?? 0,
    clashScore: (c.clashScore as number) ?? 0,
    finalScore: (c.finalScore as number) ?? 0,
    result: ((c.result as string) ?? 'FAIL') as Candidate['result'],
    failReason: (c.failReason as string) ?? '',
    source: resolvedSource,
    pdb_path: (c.pdb_path as string) ?? undefined,
    // P05: 확장 필드 — BE candidate dict에 포함 시 전달, 없으면 undefined
    selectivity_margin: c.selectivity_margin !== undefined ? (c.selectivity_margin as number) : undefined,
    instability_index: c.instability_index !== undefined ? (c.instability_index as number) : undefined,
    gravy: c.gravy !== undefined ? (c.gravy as number) : undefined,
    net_charge_ph74: c.net_charge_ph74 !== undefined ? (c.net_charge_ph74 as number) : undefined,
    fwkt_contact: c.fwkt_contact !== undefined ? (c.fwkt_contact as boolean) : undefined,
    chelator_site_available: c.chelator_site_available !== undefined ? (c.chelator_site_available as boolean) : undefined,
  }
}

function parseStatusData(data: Record<string, unknown>): Omit<PipelineStatus, 'connected' | 'error' | 'archivedRuns' | 'viewingArchive'> {
  const runId = (data.run_id as string) ?? ''
  const mappedSteps: PipelineStep[] = ((data.steps ?? []) as Record<string, unknown>[]).map(s => ({
    id: (s.id as string) ?? '',
    label: (s.label as string) ?? '',
    shortLabel: (s.shortLabel as string) ?? '',
    status: normalizeStepStatus(s.status),
    duration: (s.duration as string | undefined) ?? undefined,
  }))
  const executionMode = detectExecutionMode(runId, mappedSteps)

  return {
    executionMode,
    runId,
    startedAt: (data.started_at as string) ?? '',
    updatedAt: (data.updated_at as string) ?? '',
    iteration: (data.iteration as number) ?? 1,
    totalIterations: (data.total_iterations as number) ?? 5,
    llmModel: (data.llm_model as string) ?? '',
    target: (data.target as string) ?? '',
    reference: (data.reference as string) ?? '',
    steps: filterStepsForMode(mappedSteps, executionMode),
    rosettaSubsteps: ((data.rosetta_substeps ?? []) as Record<string, unknown>[]).map(s => ({
      id: (s.id as string) ?? '',
      label: (s.label as string) ?? '',
      status: normalizeStepStatus(s.status),
      duration: (s.duration as string | undefined) ?? undefined,
    })),
    timeline: ((data.timeline ?? []) as Record<string, unknown>[]).map(t => ({
      iteration: (t.iteration as number) ?? 0,
      stage: (t.stage as string) ?? '',
      status: normalizeStepStatus(t.status),
      message: (t.message as string) ?? '',
      ts: (t.ts as string) ?? '',
    })),
    agents: ((data.agents ?? []) as Record<string, unknown>[]).map(a => ({
      id: a.id as string,
      name: a.name as string,
      type: (a.type as 'LLM' | 'Code') ?? 'Code',
      status: (a.status as 'idle' | 'active' | 'error') ?? 'idle',
      lastMessage: (a.lastMessage as string) ?? '',
      taskCount: (a.taskCount as number) ?? 0,
      report: a.report as Agent['report'],
      lastActiveTs: (a.last_active_ts as string) ?? undefined,
      isRuntimeActive: (a.is_runtime_active as boolean) ?? false,
    })),
    candidates: ((data.candidates ?? []) as Record<string, unknown>[]).map(c => mapCandidate(c, 'live')),
    historicalCandidates: ((data.historical_candidates ?? []) as Record<string, unknown>[]).map(c => mapCandidate(c, 'historical')),
    qcGates: ((data.qc_gates ?? []) as Record<string, unknown>[]).map(g => ({
      name: g.name as string,
      criterion: g.criterion as string,
      passed: g.passed as number,
      failed: g.failed as number,
      total: g.total as number,
    })),
    convergence: (data.convergence ?? []) as ConvergencePoint[],
    liveApis: (data.live_apis as LiveApiStatus) ?? { esmfold: 'pending', molmim: 'pending' },
    bestCandidate: (data.best_candidate as BestCandidate) ?? null,
    molecules: (data.molecules ?? []) as MoleculeData[],
    visualizationImages: ((data.visualization_images ?? []) as Record<string, unknown>[]).map(img => ({
      label: img.label as string,
      url: img.url as string,
      type: img.type as 'overview' | 'closeup' | 'interface' | 'electrostatics',
    })),
    completed: (data.completed as boolean) ?? false,
  }
}

// NOTE: Polling overlap with useExperiment
// usePipelineStatus polls /api/status (every 2s) for full pipeline state (steps, candidates, agents).
// useExperiment polls /api/experiment/status (every 3s) for lightweight run/stop state (running, run_id).
// The two hooks serve distinct purposes and are intentionally separate:
//   - usePipelineStatus drives the main dashboard visualization.
//   - useExperiment drives ExperimentControl (start/stop/config).
// If backend load becomes a concern, consider a single unified /api/status endpoint that returns
// both datasets so only one polling loop is needed.
export function usePipelineStatus(pollInterval = 2000): PipelineStatus & { switchRun: (runId: string | null) => void } {
  const [status, setStatus] = useState<PipelineStatus>(INITIAL_STATE)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const viewingArchiveRef = useRef<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const fetchArchivedRuns = useCallback(async () => {
    try {
      const res = await fetch('/api/runs')
      if (res.ok) {
        const data = await res.json()
        setStatus(prev => ({ ...prev, archivedRuns: data.runs ?? [] }))
      }
    } catch { /* ignore */ }
  }, [])

  const fetchLiveStatus = useCallback(async () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    try {
      const res = await fetch('/api/status', { signal: controller.signal })
      if (!res.ok) {
        setStatus(prev => ({ ...prev, connected: false, error: `HTTP ${res.status}` }))
        return
      }
      const data = await res.json() as Record<string, unknown>
      // 백엔드에 상태 파일이 없으면 파이프라인 미실행 — Live 대시보드로 오인하지 않도록
      if (data.error === 'no_status_file' || data.connected === false) {
        setStatus(prev => ({
          ...INITIAL_STATE,
          connected: false,
          error: typeof data.error === 'string' ? data.error : 'no pipeline status',
          archivedRuns: prev.archivedRuns,
          viewingArchive: prev.viewingArchive,
        }))
        return
      }
      const parsed = parseStatusData(data)
      setStatus(prev => ({
        ...parsed,
        connected: true,
        error: null,
        archivedRuns: prev.archivedRuns,
        viewingArchive: prev.viewingArchive,
      }))
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      setStatus(prev => ({ ...prev, connected: false, error: 'Connection failed' }))
    }
  }, [])

  const switchRun = useCallback(async (runId: string | null) => {
    abortRef.current?.abort()
    viewingArchiveRef.current = runId
    if (runId === null) {
      // Switch back to live
      setStatus(prev => ({ ...prev, viewingArchive: null }))
      await fetchLiveStatus()
      return
    }
    // Fetch archived run
    try {
      const res = await fetch(`/api/runs/${runId}`)
      if (!res.ok) {
        viewingArchiveRef.current = null
        return
      }
      const data = await res.json()
      const parsed = parseStatusData(data)
      setStatus(prev => ({
        ...parsed,
        connected: true,
        error: null,
        archivedRuns: prev.archivedRuns,
        viewingArchive: runId,
      }))
    } catch {
      viewingArchiveRef.current = null
    }
  }, [fetchLiveStatus])

  /* eslint-disable react-hooks/set-state-in-effect -- bootstrap polling on mount */
  useEffect(() => {
    fetchLiveStatus()
    fetchArchivedRuns()
    intervalRef.current = setInterval(() => {
      if (!viewingArchiveRef.current) {
        fetchLiveStatus()
      }
      fetchArchivedRuns()
    }, pollInterval)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      abortRef.current?.abort()
    }
  }, [fetchLiveStatus, fetchArchivedRuns, pollInterval])
  /* eslint-enable react-hooks/set-state-in-effect */

  return { ...status, switchRun }
}
