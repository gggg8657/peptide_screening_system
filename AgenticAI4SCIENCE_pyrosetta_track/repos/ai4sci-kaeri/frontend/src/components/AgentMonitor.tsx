import { useEffect, useState } from 'react'
import { HelpTooltip } from './ui/HelpTooltip'
import { cn } from '../lib/utils'
import type { Agent, AgentStatus, AgentType, AgentReport, ExecutionMode } from '../types'
import { Bot, Code2, AlertTriangle, Activity, Clock, ChevronRight, ChevronDown, Lightbulb, GitBranch, FileText, Settings2, Info } from 'lucide-react'

function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 5) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ago`
}

function ConfiguredOnlyBadge({ tooltip }: { tooltip?: string }) {
  const [showTip, setShowTip] = useState(false)
  return (
    <span className="relative inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide bg-[var(--bg-elev)]/40 text-[var(--text-mute)] border border-[var(--border)]/30">
      <Settings2 className="w-2.5 h-2.5" />
      Configured only
      {tooltip && (
        <button
          className="text-[var(--text-mute)] hover:text-[var(--text-mute)] transition-colors"
          onMouseEnter={() => setShowTip(true)}
          onMouseLeave={() => setShowTip(false)}
          aria-label="Why inactive"
        >
          <Info className="w-2.5 h-2.5" />
        </button>
      )}
      {showTip && tooltip && (
        <div className="absolute left-0 top-6 z-50 w-64 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg p-2.5 shadow-xl text-[10px] text-[var(--text)] leading-relaxed font-normal">
          {tooltip}
        </div>
      )}
    </span>
  )
}

function TypeBadge({ type }: { type: AgentType }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide',
        type === 'LLM'
          ? 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent)]/30'
          : 'bg-[var(--bg-elev)]/60 text-[var(--text-mute)] border border-[var(--border)]/40'
      )}
    >
      {type === 'LLM' ? <Bot className="w-2.5 h-2.5" /> : <Code2 className="w-2.5 h-2.5" />}
      {type}
    </span>
  )
}

function StatusIndicator({ status }: { status: AgentStatus }) {
  const config: Record<AgentStatus, { color: string; label: string; pulse: boolean }> = {
    idle:   { color: 'bg-[var(--text-dim)]', label: 'Idle',   pulse: false },
    active: { color: 'bg-green-400', label: 'Active', pulse: true },
    error:  { color: 'bg-red-400',   label: 'Error',  pulse: true },
  }
  const { color, label, pulse } = config[status]

  return (
    <div className="flex items-center gap-1.5">
      <span className="relative flex h-2 w-2">
        <span
          className={cn(
            'absolute inline-flex h-full w-full rounded-full opacity-75',
            pulse && 'animate-ping',
            color
          )}
        />
        <span className={cn('relative inline-flex rounded-full h-2 w-2', color)} />
      </span>
      <span
        className={cn(
          'text-[10px] font-medium',
          status === 'active' && 'text-[var(--pos)]',
          status === 'error'  && 'text-[var(--neg)]',
          status === 'idle'   && 'text-[var(--text-mute)]'
        )}
      >
        {label}
      </span>
    </div>
  )
}

function AgentIcon({ type, status }: { type: AgentType; status: AgentStatus }) {
  const isActive = status === 'active'
  const isError  = status === 'error'

  return (
    <div
      className={cn(
        'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
        isError  && 'bg-[var(--neg-soft)] border border-[var(--neg)]/30',
        isActive && 'bg-[var(--accent-soft)] border border-[var(--accent)]/30',
        !isError && !isActive && 'bg-[var(--bg-elev)] border border-[var(--border)]'
      )}
    >
      {isError ? (
        <AlertTriangle className="w-4 h-4 text-[var(--neg)]" />
      ) : isActive ? (
        <Activity className="w-4 h-4 text-[var(--accent)] animate-pulse-glow" />
      ) : type === 'LLM' ? (
        <Bot className="w-4 h-4 text-[var(--text-mute)]" />
      ) : (
        <Code2 className="w-4 h-4 text-[var(--text-mute)]" />
      )}
    </div>
  )
}

function ReportPanel({ report }: { report: AgentReport }) {
  if (report.type === 'plan') {
    return (
      <div className="bg-[var(--bg-elev)]/80 rounded-lg px-3 py-2 space-y-2">
        <div className="flex items-center gap-1.5 text-[var(--warn)] text-xs font-semibold">
          <Lightbulb className="w-3 h-3" />
          Hypothesis
        </div>
        {report.hypothesis && (
          <p className="text-xs text-[var(--text-mute)] leading-relaxed whitespace-pre-wrap font-mono">
            {report.hypothesis}
          </p>
        )}
        {report.strategy && (
          <div className="mt-1.5">
            <span className="text-[10px] text-[var(--text-mute)] font-semibold uppercase tracking-wide">Strategy: </span>
            <span className="text-xs text-[var(--text-mute)]">{report.strategy}</span>
          </div>
        )}
      </div>
    )
  }

  if (report.type === 'critic') {
    return (
      <div className="bg-[var(--bg-elev)]/80 rounded-lg px-3 py-2 space-y-2">
        <div className="flex items-center gap-1.5 text-[var(--violet)] text-xs font-semibold">
          <GitBranch className="w-3 h-3" />
          Hypothesis
        </div>
        {report.hypothesis && (
          <p className="text-xs text-[var(--text-mute)] leading-relaxed whitespace-pre-wrap font-mono">
            {report.hypothesis}
          </p>
        )}
        {report.proposed_changes && report.proposed_changes.length > 0 && (
          <div className="mt-2 space-y-1.5">
            <p className="text-[10px] text-[var(--text-mute)] font-semibold uppercase tracking-wide">Proposed Changes</p>
            {report.proposed_changes.map((change, i) => (
              <div key={i} className="bg-[var(--bg)]/60 rounded px-2 py-1.5">
                <div className="text-xs font-semibold text-[var(--text-mute)]">
                  {change.parameter}:{' '}
                  <span className="text-[var(--neg)] line-through">{change.old}</span>
                  {' → '}
                  <span className="text-[var(--pos)]">{change.new}</span>
                </div>
                <div className="text-[10px] text-[var(--text-mute)] mt-0.5">{change.rationale}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (report.type === 'reporter') {
    return (
      <div className="bg-[var(--bg-elev)]/80 rounded-lg px-3 py-2 space-y-2">
        <div className="flex items-center gap-1.5 text-[var(--accent)] text-xs font-semibold">
          <FileText className="w-3 h-3" />
          Summary
        </div>
        {report.summary && (
          <pre className="text-xs text-[var(--text-mute)] leading-relaxed whitespace-pre-wrap font-mono break-words">
            {report.summary}
          </pre>
        )}
      </div>
    )
  }

  return null
}

const AGENT_INACTIVE_TOOLTIPS: Record<string, Record<ExecutionMode, string>> = {
  'diversity-mgr': {
    pyrosettaOnly: 'Structural diversity analysis requires FoldMason (not available in PyRosetta-only mode). Sequence-level deduplication is active via seen_sequences set.',
    full: 'DiversityMgr is configured but has not been activated in this run.',
  },
}

function AgentCard({
  agent,
  expandSignal,
  expandTarget,
  iteration,
  executionMode,
}: {
  agent: Agent
  expandSignal: number
  expandTarget: boolean | null
  iteration: number
  executionMode: ExecutionMode
}) {
  const [expanded, setExpanded] = useState(false)
  const isError = agent.status === 'error'
  const hasReport = Boolean(agent.report)
  const isConfiguredOnly = !agent.isRuntimeActive && agent.status === 'idle'
  const inactiveTooltip = isConfiguredOnly
    ? AGENT_INACTIVE_TOOLTIPS[agent.id]?.[executionMode]
    : undefined

  /* eslint-disable react-hooks/set-state-in-effect -- sync external signal → local state */
  useEffect(() => {
    if (expandTarget !== null) {
      setExpanded(expandTarget)
    }
  }, [expandSignal, expandTarget])
  /* eslint-enable react-hooks/set-state-in-effect */

  return (
    <article
      className={cn(
        'rounded-xl border p-3 transition-all duration-200',
        isError
          ? 'bg-[var(--neg-soft)] border-[var(--neg)]/30'
          : agent.status === 'active'
          ? 'bg-blue-950/20 border-[var(--accent)]/30'
          : isConfiguredOnly
          ? 'bg-[var(--bg)] border-[var(--border)]/50 opacity-60'
          : 'bg-[var(--bg)] border-[var(--border)]'
      )}
      aria-label={`Agent: ${agent.name}`}
    >
      <div className="flex items-start gap-2.5 mb-2">
        <AgentIcon type={agent.type} status={agent.status} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-[var(--text)]">{agent.name}</span>
            <TypeBadge type={agent.type} />
            {isConfiguredOnly && <ConfiguredOnlyBadge tooltip={inactiveTooltip} />}
          </div>
          <StatusIndicator status={agent.status} />
        </div>
        <div className="flex flex-col items-end gap-0.5 text-[var(--text-mute)] flex-shrink-0">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span className="text-[10px]">{agent.taskCount} tasks</span>
          </div>
          {agent.taskCount > 0 && iteration > 0 && (
            <span className="text-[10px] text-[var(--text-mute)]">
              ~{(agent.taskCount / iteration).toFixed(1)}/iter
            </span>
          )}
          {agent.lastActiveTs && (
            <span className="text-[10px] text-[var(--text-mute)]">
              {formatRelativeTime(agent.lastActiveTs)}
            </span>
          )}
        </div>
      </div>

      <p
        className={cn(
          'text-xs leading-relaxed rounded-md px-2 py-1.5 font-mono',
          isError
            ? 'text-[var(--neg)] bg-[var(--neg-soft)]'
            : 'text-[var(--text-mute)] bg-[var(--bg-sunk)]'
        )}
      >
        {agent.lastMessage}
      </p>

      {hasReport && (
        <div className="mt-2">
          <button
            onClick={() => setExpanded(prev => !prev)}
            onKeyDown={e => { if (e.key === 'Escape' && expanded) { setExpanded(false); e.stopPropagation() } }}
            aria-expanded={expanded}
            className="flex items-center gap-1 text-[10px] text-[var(--text-mute)] hover:text-[var(--text-mute)] transition-colors"
          >
            {expanded
              ? <ChevronDown className="w-3 h-3" />
              : <ChevronRight className="w-3 h-3" />
            }
            {expanded ? 'Hide Report' : 'View Report'}
          </button>
          {expanded && agent.report && (
            <div className="mt-1.5">
              <ReportPanel report={agent.report} />
            </div>
          )}
        </div>
      )}
    </article>
  )
}

interface AgentMonitorProps {
  agents: Agent[]
  iteration?: number
  executionMode?: ExecutionMode
}

export function AgentMonitor({ agents, iteration = 1, executionMode = 'full' }: AgentMonitorProps) {
  const activeCount = agents.filter(a => a.status === 'active').length
  const errorCount  = agents.filter(a => a.status === 'error').length
  const [expandSignal, setExpandSignal] = useState(0)
  const [expandTarget, setExpandTarget] = useState<boolean | null>(null)

  const expandAllReports = () => {
    setExpandTarget(true)
    setExpandSignal(v => v + 1)
  }

  const collapseAllReports = () => {
    setExpandTarget(false)
    setExpandSignal(v => v + 1)
  }

  return (
    <section className="card flex flex-col gap-3" aria-label="Agent Monitor">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          Agent Monitor
          <HelpTooltip title="Agent Monitor">
            <p>5개 에이전트의 실시간 상태를 모니터링합니다.</p>
            <p><strong>에이전트 역할</strong>: Hypothesis(가설 생성), Ranking(순위 평가), Evolution(진화 전략), Proximity(근접성 분석), Meta-review(메타 리뷰).</p>
            <p><strong>상태</strong>: 🟢 idle, 🔵 running, 🟡 waiting, 🔴 error.</p>
          </HelpTooltip>
        </h2>
        <div className="flex gap-2 items-center">
          <button
            onClick={expandAllReports}
            className="text-[10px] bg-[var(--bg-elev)] text-[var(--text-mute)] border border-[var(--border)] px-2 py-0.5 rounded-full hover:border-[var(--border-strong)] transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAllReports}
            className="text-[10px] bg-[var(--bg-elev)] text-[var(--text-mute)] border border-[var(--border)] px-2 py-0.5 rounded-full hover:border-[var(--border-strong)] transition-colors"
          >
            Collapse All
          </button>
          {activeCount > 0 && (
            <span className="text-[10px] bg-[var(--pos-soft)] text-[var(--pos)] border border-[var(--pos)]/30 px-2 py-0.5 rounded-full font-medium">
              {activeCount} active
            </span>
          )}
          {errorCount > 0 && (
            <span className="text-[10px] bg-[var(--neg-soft)] text-[var(--neg)] border border-[var(--neg)]/30 px-2 py-0.5 rounded-full font-medium">
              {errorCount} error
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {agents.map(agent => (
          <AgentCard
            key={agent.id}
            agent={agent}
            expandSignal={expandSignal}
            expandTarget={expandTarget}
            iteration={iteration}
            executionMode={executionMode}
          />
        ))}
      </div>
    </section>
  )
}
