import { Cpu, Server, ArrowRight } from 'lucide-react'
import { PipelineStatus } from '../components/PipelineStatus'
import { AgentMonitor } from '../components/AgentMonitor'
import { CandidateTable } from '../components/CandidateTable'
import { QCGateChart } from '../components/QCGateChart'
import { ConvergenceGraph } from '../components/ConvergenceGraph'
import { ExperimentControl } from '../components/ExperimentControl'
import { usePipelineContext } from '../contexts/PipelineContext'
import { useExperiment } from '../hooks/useExperiment'
import { cn } from '../lib/utils'
import type { PipelineStep, Agent, QCGate, ConvergencePoint } from '../types'

// ──────────────────────────────────────────────────────────────────────────────
// 정적 폴백 데이터 (파이프라인 미실행 시 사용)
// ──────────────────────────────────────────────────────────────────────────────
const SILO_A_STEPS: PipelineStep[] = [
  { id: 'step01', label: 'Receptor Prep (OpenFold3)', shortLabel: 'Receptor', status: 'pending' },
  { id: 'step02', label: 'Backbone Design (RFdiffusion)', shortLabel: 'Backbone', status: 'pending' },
  { id: 'step03', label: 'Sequence Design (ProteinMPNN)', shortLabel: 'SeqDesign', status: 'pending' },
  { id: 'step03b', label: 'BLOSUM62 Mutation (Local)', shortLabel: 'BLOSUM', status: 'pending' },
  { id: 'step04', label: 'Fast QC (ESMFold)', shortLabel: 'QC', status: 'pending' },
  { id: 'step05', label: 'Docking (DiffDock + Boltz-2)', shortLabel: 'Docking', status: 'pending' },
  { id: 'step05b', label: 'Selectivity Screening', shortLabel: 'Select', status: 'pending' },
  { id: 'step06', label: 'Rosetta Refinement (PyRosetta)', shortLabel: 'Rosetta', status: 'pending' },
  { id: 'step07', label: 'Analysis (FoldMason + PyMOL)', shortLabel: 'Analysis', status: 'pending' },
  { id: 'step08', label: 'Stability Prediction', shortLabel: 'Stability', status: 'pending' },
]

const SILO_A_AGENTS: Agent[] = [
  { id: 'planner', name: 'Planner', type: 'LLM', status: 'idle', lastMessage: 'Awaiting pipeline start', taskCount: 0, isRuntimeActive: false },
  { id: 'critic', name: 'Scientist Critic', type: 'LLM', status: 'idle', lastMessage: 'Awaiting pipeline start', taskCount: 0, isRuntimeActive: false },
  { id: 'reporter', name: 'Reporter', type: 'LLM', status: 'idle', lastMessage: 'Awaiting pipeline start', taskCount: 0, isRuntimeActive: false },
  { id: 'qc-ranker', name: 'QC & Ranker', type: 'Code', status: 'idle', lastMessage: 'Multi-gate QC ready', taskCount: 0, isRuntimeActive: false },
  { id: 'diversity-mgr', name: 'Diversity Manager', type: 'Code', status: 'idle', lastMessage: 'FoldMason comparison ready', taskCount: 0, isRuntimeActive: false },
]

const EMPTY_QC: QCGate[] = [
  { name: 'pLDDT Gate', criterion: 'pLDDT > 70', passed: 0, failed: 0, total: 0 },
  { name: 'Dock Score', criterion: 'DiffDock score < -8.0', passed: 0, failed: 0, total: 0 },
  { name: 'Rosetta ΔG', criterion: 'ΔG < -5.0 kcal/mol', passed: 0, failed: 0, total: 0 },
  { name: 'Selectivity', criterion: 'SSTR2 margin > 2.0', passed: 0, failed: 0, total: 0 },
]
const EMPTY_CONVERGENCE: ConvergencePoint[] = []

// 3-ARM 파이프라인 다이어그램 노드
const ARM_NODES: { id: string; label: string; sub: string }[] = [
  { id: 'step02', label: 'RFdiffusion', sub: 'Backbone' },
  { id: 'step03', label: 'ProteinMPNN', sub: 'SeqDesign' },
  { id: 'step04', label: 'ESMFold QC', sub: 'Quality' },
  { id: 'step05', label: 'Boltz-2 Dock', sub: 'Docking' },
  { id: 'step06', label: 'PyRosetta', sub: 'Refine' },
  { id: 'step07', label: 'Analysis', sub: 'FoldMason' },
]

// 모델 서비스 테이블
const MODEL_SERVICES = [
  { stepId: 'step02', name: 'RFdiffusion', vram: '~24 GB', local: false, priority: 'Medium' },
  { stepId: 'step03', name: 'ProteinMPNN', vram: '~8 GB',  local: true,  priority: 'High' },
  { stepId: 'step04', name: 'ESMFold',     vram: '~8 GB',  local: true,  priority: 'High' },
  { stepId: 'step05', name: 'Boltz-2',     vram: '~24 GB', local: false, priority: 'Low' },
  { stepId: 'step06', name: 'PyRosetta',   vram: '~4 GB',  local: true,  priority: 'High' },
  { stepId: 'step01', name: 'OpenFold3',   vram: '~16 GB', local: false, priority: 'Low' },
  { stepId: 'step07', name: 'ESM2',        vram: '~4 GB',  local: true,  priority: 'Low' },
  { stepId: 'step05b',name: 'DiffDock',    vram: '~16 GB', local: false, priority: 'Medium' },
]

// ──────────────────────────────────────────────────────────────────────────────
// 헬퍼
// ──────────────────────────────────────────────────────────────────────────────
type StepStatus = 'pending' | 'running' | 'completed' | 'failed'

function statusBadge(status: StepStatus) {
  switch (status) {
    case 'running':   return 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
    case 'completed': return 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30'
    case 'failed':    return 'bg-[var(--neg-soft)] text-[var(--neg)] border-[var(--neg)]/30'
    default:          return 'bg-[var(--bg-sunk)] text-[var(--text-dim)] border-[var(--border)]'
  }
}

function statusLabel(status: StepStatus) {
  switch (status) {
    case 'running':   return 'running'
    case 'completed': return 'completed'
    case 'failed':    return 'error'
    default:          return 'ready'
  }
}

function nodeStyle(status: StepStatus) {
  switch (status) {
    case 'running':   return 'border-[var(--accent)]/30 bg-blue-950/40 text-[var(--accent)]'
    case 'completed': return 'border-[var(--pos)]/30 bg-green-950/30 text-[var(--pos)]'
    case 'failed':    return 'border-[var(--neg)]/30 bg-[var(--neg-soft)] text-[var(--neg)]'
    default:          return 'border-[var(--border)] bg-[var(--bg-elev)] text-[var(--text-dim)]'
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 컴포넌트
// ──────────────────────────────────────────────────────────────────────────────
export function SiloAPage() {
  const live = usePipelineContext()
  const experiment = useExperiment(3000)
  const isArchive = !!live.viewingArchive
  const isLive = live.connected && (live.steps.length > 0 || isArchive)

  // approach='a' 주입 — ExperimentControl은 내부적으로 startExperiment()를 호출
  const experimentA: typeof experiment = {
    ...experiment,
    startExperiment: (overrides?: Record<string, unknown>) =>
      experiment.startExperiment({ approach: 'a', ...overrides }),
  }

  // Silo A 전용 step ID 집합
  const SILO_A_STEP_IDS = new Set(['step01', 'silo_a', 'step02', 'step03', 'step04', 'step05', 'step07'])

  // live.steps를 사용한 step 상태 조회 (별도 폴링 불필요)
  const getStepStatus = (stepId: string): StepStatus => {
    const step = live.steps.find(s => s.id === stepId)
    return (step?.status ?? 'pending') as StepStatus
  }

  const getStepDuration = (stepId: string): string | undefined => {
    return live.steps.find(s => s.id === stepId)?.duration
  }

  // 라이브 데이터 / 폴백 데이터 선택 (Silo A 관련 step/candidate만 필터링)
  const steps = isLive
    ? live.steps.filter(s => SILO_A_STEP_IDS.has(s.id))
    : SILO_A_STEPS
  const agents = isLive ? live.agents : SILO_A_AGENTS
  const candidates = isLive
    ? live.candidates.filter(c => c.source === 'silo_a')
    : []
  const historicalCandidates = isLive
    ? live.historicalCandidates.filter(c => c.source === 'silo_a')
    : []
  const qcGates = isLive ? live.qcGates : EMPTY_QC
  const convergence = isLive ? live.convergence : EMPTY_CONVERGENCE
  const iteration = isLive ? live.iteration : 0
  const totalIterations = isLive ? live.totalIterations : 1
  const executionMode = isLive ? live.executionMode : 'full'
  const rosettaSubsteps = isLive ? live.rosettaSubsteps : []

  return (
    <div className="space-y-4">
      {/* ── Experiment Control ── */}
      <ExperimentControl experiment={experimentA} iteration={iteration} totalIterations={totalIterations} />

      {/* ── 파이프라인 설명 ── */}
      <section className="card border border-[var(--border)]">
        <p className="text-xs text-[var(--text-mute)]">
          3-ARM pipeline:{' '}
          <span className="font-mono text-[var(--violet)]">
            RFdiffusion → ProteinMPNN → ESMFold QC → Boltz-2 Dock → PyRosetta
          </span>
        </p>
        <p className="text-xs text-[var(--text-mute)] mt-1">
          De novo backbone design with local model services &middot; 10-step pipeline.
        </p>
      </section>

      {/* ── Pipeline Status ── */}
      <PipelineStatus
        steps={steps}
        rosettaSubsteps={rosettaSubsteps}
        iteration={iteration}
        totalIterations={totalIterations}
        completed={isLive ? live.completed : false}
        executionMode={executionMode}
      />

      {/* ── 3-ARM 파이프라인 다이어그램 ── */}
      <section className="card border border-[var(--border)]">
        <div className="flex items-center gap-2 mb-3">
          <h3 className="text-sm font-semibold text-[var(--text-dim)] uppercase tracking-widest">
            3-ARM Pipeline Flow
          </h3>
        </div>

        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          {ARM_NODES.map((node, idx) => {
            const status = getStepStatus(node.id)
            const duration = getStepDuration(node.id)
            return (
              <div key={node.id} className="flex items-center gap-1 flex-shrink-0">
                <div
                  className={cn(
                    'flex flex-col items-center justify-center rounded-lg border px-3 py-2 min-w-[88px] transition-all',
                    nodeStyle(status)
                  )}
                >
                  <span className="text-[10px] font-bold leading-tight text-center">{node.label}</span>
                  <span className="text-[9px] text-[var(--text-dim)] mt-0.5">{node.sub}</span>
                  <div className="flex items-center gap-1 mt-1">
                    {status === 'running' && (
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse inline-block" />
                    )}
                    <span className={cn(
                      'text-[9px] font-medium',
                      status === 'running'   ? 'text-[var(--accent)]'  :
                      status === 'completed' ? 'text-[var(--pos)]' :
                      status === 'failed'    ? 'text-[var(--neg)]'   : 'text-[var(--text-dim)]'
                    )}>
                      {duration ?? statusLabel(status)}
                    </span>
                  </div>
                </div>
                {idx < ARM_NODES.length - 1 && (
                  <ArrowRight className="w-3 h-3 text-[var(--text-dim)] flex-shrink-0" />
                )}
              </div>
            )
          })}
        </div>

        <div className="flex items-center gap-4 mt-3 pt-2 border-t border-[var(--border)]">
          {(['pending','running','completed','failed'] as StepStatus[]).map(s => (
            <div key={s} className="flex items-center gap-1">
              <span className={cn('text-[9px] px-1.5 py-0.5 rounded-full border font-medium', statusBadge(s))}>
                {statusLabel(s)}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Model Services ── */}
      <section className="card border border-[var(--border)]">
        <div className="flex items-center gap-2 mb-3">
          <Server className="w-4 h-4 text-[var(--accent)]" />
          <h3 className="text-sm font-semibold text-[var(--text-dim)] uppercase tracking-widest">
            Model Services
          </h3>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30 font-semibold">
            LOCAL MODE — no cloud API required
          </span>
          {isLive && (
            <span className="text-[10px] text-[var(--text-dim)] ml-auto">실시간 업데이트 중</span>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[var(--text-dim)] text-left border-b border-[var(--border)]">
                <th className="pb-2 font-semibold">Service</th>
                <th className="pb-2 font-semibold">GPU VRAM</th>
                <th className="pb-2 font-semibold">Deploy</th>
                <th className="pb-2 font-semibold">Priority</th>
                <th className="pb-2 font-semibold">Status</th>
                <th className="pb-2 font-semibold">Duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {MODEL_SERVICES.map(svc => {
                const liveStatus = getStepStatus(svc.stepId)
                const duration = getStepDuration(svc.stepId)
                return (
                  <tr key={svc.name}>
                    <td className="py-2">
                      <div className="flex items-center gap-1.5">
                        <Cpu className="w-3 h-3 text-[var(--violet)]" />
                        <span className="font-medium text-[var(--text-mute)]">{svc.name}</span>
                      </div>
                    </td>
                    <td className="py-2 text-[var(--text-dim)] font-mono">{svc.vram}</td>
                    <td className="py-2">
                      <span className={cn(
                        'text-[10px] px-1.5 py-0.5 rounded-full border font-medium',
                        svc.local
                          ? 'bg-[var(--pos-soft)] text-[var(--pos)] border-[var(--pos)]/30'
                          : 'bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent)]/30'
                      )}>
                        {svc.local ? 'local' : 'cloud'}
                      </span>
                    </td>
                    <td className="py-2 text-[var(--text-dim)]">{svc.priority}</td>
                    <td className="py-2">
                      <span className={cn(
                        'text-[10px] px-1.5 py-0.5 rounded-full border font-medium inline-flex items-center gap-1',
                        statusBadge(liveStatus)
                      )}>
                        {liveStatus === 'running' && (
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                        )}
                        {statusLabel(liveStatus)}
                      </span>
                    </td>
                    <td className="py-2 font-mono text-[var(--text-dim)] text-[10px]">
                      {duration ?? '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <p className="text-[10px] text-[var(--text-dim)] mt-3">
          Local models: ESMFold + ProteinMPNN + PyRosetta + ESM2 (~24 GB VRAM). Services marked "cloud" require additional local setup.
        </p>
      </section>

      {/* ── Agent Monitor + Candidate Table ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-4 items-start">
        <AgentMonitor agents={agents} iteration={iteration} executionMode={executionMode} />
        <CandidateTable
          candidates={candidates}
          historicalCandidates={historicalCandidates}
          archiveRunId={live.viewingArchive}
        />
      </div>

      {/* ── QC Gates + Convergence ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <QCGateChart gates={qcGates} />
        <ConvergenceGraph data={convergence} />
      </div>
    </div>
  )
}
