import { cn } from '../lib/utils'
import { HelpTooltip } from './ui/HelpTooltip'
import type { ExecutionMode, PipelineStep, RosettaSubstep, StepStatus } from '../types'
import { CheckCircle2, XCircle, Loader2, Circle } from 'lucide-react'

function StatusIcon({ status }: { status: StepStatus }) {
  if (status === 'completed') {
    return <CheckCircle2 className="w-5 h-5 text-[var(--pos)]" aria-label="completed" />
  }
  if (status === 'running') {
    return <Loader2 className="w-5 h-5 text-[var(--accent)] animate-spin" aria-label="running" />
  }
  if (status === 'failed') {
    return <XCircle className="w-5 h-5 text-[var(--neg)]" aria-label="failed" />
  }
  return <Circle className="w-5 h-5 text-[var(--text-dim)]" aria-label="pending" />
}

function stepColor(status: StepStatus): string {
  switch (status) {
    case 'completed': return 'border-green-500 bg-[var(--pos-soft)] text-[var(--pos)]'
    case 'running':   return 'border-blue-500 bg-[var(--accent-soft)] text-[var(--accent)]'
    case 'failed':    return 'border-red-500 bg-[var(--neg-soft)] text-[var(--neg)]'
    default:          return 'border-[var(--border)] bg-[var(--bg-elev)] text-[var(--text-dim)]'
  }
}

function connectorColor(step: PipelineStep, next: PipelineStep | undefined): string {
  if (!next) return ''
  if (step.status === 'completed' && (next.status === 'completed' || next.status === 'running')) {
    return 'bg-[var(--pos-soft)]'
  }
  return 'bg-[var(--bg-sunk)]'
}

interface StepCardProps {
  step: PipelineStep
  isLast: boolean
  nextStep: PipelineStep | undefined
}

function StepCard({ step, isLast, nextStep }: StepCardProps) {
  return (
    <div className="flex items-center flex-1 min-w-0">
      <div className="flex flex-col items-center gap-1 min-w-0">
        <div
          className={cn(
            'flex flex-col items-center gap-1 px-3 py-2 rounded-lg border transition-all duration-300',
            stepColor(step.status)
          )}
          role="listitem"
          aria-label={`${step.label}: ${step.status}`}
        >
          <StatusIcon status={step.status} />
          <span className="text-xs font-mono font-semibold whitespace-nowrap">{step.shortLabel}</span>
          <span className="text-[10px] text-center leading-tight whitespace-nowrap opacity-80">{step.label}</span>
          {step.duration && (
            <span className="text-[10px] opacity-60">{step.duration}</span>
          )}
          {step.status === 'running' && (
            <span className="text-[10px] animate-pulse-glow text-[var(--accent)]">In Progress</span>
          )}
        </div>
      </div>

      {!isLast && (
        <div className="flex-1 flex items-center px-1 mt-0">
          <div
            className={cn(
              'h-px w-full transition-all duration-500',
              connectorColor(step, nextStep)
            )}
            aria-hidden="true"
          />
        </div>
      )}
    </div>
  )
}

interface PipelineStatusProps {
  steps: PipelineStep[]
  rosettaSubsteps?: RosettaSubstep[]
  iteration: number
  totalIterations: number
  completed?: boolean
  executionMode?: ExecutionMode
}

export function PipelineStatus({
  steps,
  rosettaSubsteps = [],
  iteration,
  totalIterations,
  completed,
  executionMode = 'full',
}: PipelineStatusProps) {
  const completedCount = steps.filter(s => s.status === 'completed').length
  const progress = steps.length > 0 ? Math.round((completedCount / steps.length) * 100) : 0

  return (
    <section className="card animate-slide-in" aria-label="Pipeline Status">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
            Pipeline Status
            <HelpTooltip title="Pipeline Status">
              <p>파이프라인 각 단계의 진행 상태를 보여줍니다.</p>
              <p>NIM 서열 생성 → PyRosetta 시뮬레이션 → QC 게이트 → 분석 순서로 진행됩니다.</p>
              <p><strong>진행률</strong>: 각 단계의 완료/전체 비율을 나타냅니다.</p>
            </HelpTooltip>
          </h2>
          <p className="text-lg font-bold text-[var(--text-mute)] mt-0.5">
            Iteration{' '}
            <span className="text-[var(--accent)]">{iteration}</span>
            <span className="text-[var(--text-mute)]"> / {totalIterations}</span>
            {completed && (
              <span className="ml-2 text-sm text-[var(--pos)] font-medium">Complete</span>
            )}
          </p>
          {executionMode === 'pyrosettaOnly' && (
            <p className="text-xs text-[var(--accent)] mt-1">
              mutate→dock→QC→Critic→Reporter 루프만 표시 (비활성 단계 숨김)
            </p>
          )}
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-[var(--text-mute)]">{progress}%</div>
          <div className="text-xs text-[var(--text-mute)]">
            {completedCount}/{steps.length} visible steps done
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-[var(--bg-elev)] rounded-full mb-5 overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-700',
            completed
              ? 'bg-gradient-to-r from-green-500 to-emerald-400'
              : 'bg-gradient-to-r from-blue-500 to-green-500'
          )}
          style={{ width: `${progress}%` }}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      {/* Steps */}
      <div
        className="flex items-start overflow-x-auto pb-2"
        role="list"
        aria-label="Pipeline steps"
      >
        {steps.map((step, idx) => (
          <StepCard
            key={step.id}
            step={step}
            isLast={idx === steps.length - 1}
            nextStep={steps[idx + 1]}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-3 flex-wrap">
        {(
          [
            { status: 'completed', label: 'Completed', color: 'bg-green-500' },
            { status: 'running',   label: 'Running',   color: 'bg-blue-500' },
            { status: 'pending',   label: 'Pending',   color: 'bg-[var(--bg-sunk)]' },
            { status: 'failed',    label: 'Failed',    color: 'bg-red-500' },
          ] as const
        ).map(({ label, color }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className={cn('w-2 h-2 rounded-full', color)} aria-hidden="true" />
            <span className="text-xs text-[var(--text-mute)]">{label}</span>
          </div>
        ))}
      </div>

      {executionMode === 'pyrosettaOnly' && rosettaSubsteps.length > 0 && (
        <div className="mt-4 border-t border-[var(--border)] pt-3">
          <div className="text-xs text-[var(--text-mute)] mb-2 uppercase tracking-wider">Rosetta Internal Steps</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2">
            {rosettaSubsteps.map(substep => (
              <div
                key={substep.id}
                className={cn(
                  'rounded-lg border px-2.5 py-2 text-xs',
                  stepColor(substep.status),
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold">{substep.label}</span>
                  <span className="uppercase text-[10px] opacity-80">{substep.status}</span>
                </div>
                {substep.duration && (
                  <div className="text-[10px] opacity-70 mt-1">{substep.duration}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
