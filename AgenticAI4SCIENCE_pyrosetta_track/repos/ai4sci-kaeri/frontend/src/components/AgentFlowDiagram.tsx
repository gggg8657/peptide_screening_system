import { useState, useMemo } from 'react'
import { HelpTooltip } from './ui/HelpTooltip'
import { X } from 'lucide-react'
import type { Agent, AgentReport, RosettaSubstep } from '../types'

// ── Node definitions matching Figure 1 from the paper ────────────────────────

interface FlowNode {
  id: string
  agentId?: string       // maps to Agent.id for status
  substepId?: string     // maps to RosettaSubstep.id for status (fallback)
  label: string
  subtitle: string
  x: number
  y: number
  color: string     // tailwind-compatible hex for SVG
  glowColor: string
}

interface FlowEdge {
  from: string
  to: string
  label: string
  type: 'solid' | 'dashed'
  color: string
}

const NODES: FlowNode[] = [
  { id: 'planner',        agentId: 'planner',                                label: 'Planner',           subtitle: 'Mutation strategy\nPrior-iteration feedback',   x: 120,  y: 60,  color: '#3b82f6', glowColor: '#60a5fa' },
  { id: 'candidate-gen',  substepId: 'step06_mutate',                        label: 'Candidate Gen',     subtitle: 'Sequence generation\nBLOSUM mutation',          x: 380,  y: 60,  color: '#3b82f6', glowColor: '#60a5fa' },
  { id: 'simulation',     substepId: 'step06_refine',                        label: 'Simulation',        subtitle: 'PyRosetta FlexPepDock\nΔG scoring',              x: 640,  y: 60,  color: '#3b82f6', glowColor: '#60a5fa' },
  { id: 'qc-ranker',      agentId: 'qc-ranker', substepId: 'step06_qc',     label: 'QC Ranker',         subtitle: 'ΔG & clash gates\nCandidate ranking',            x: 640,  y: 220, color: '#8b5cf6', glowColor: '#a78bfa' },
  { id: 'reporter',       agentId: 'reporter',  substepId: 'step06_reporter',label: 'Reporter',          subtitle: 'Iteration artifacts\nRanking summary',           x: 380,  y: 220, color: '#8b5cf6', glowColor: '#a78bfa' },
  { id: 'critic',         agentId: 'critic',    substepId: 'step06_critic',  label: 'Critic',            subtitle: 'Hypothesis review\nProposed changes',            x: 120,  y: 220, color: '#8b5cf6', glowColor: '#a78bfa' },
]

const NODE_W = 160
const NODE_H = 64

const EDGES: FlowEdge[] = [
  { from: 'planner',       to: 'candidate-gen',  label: 'Mutation strategy',          type: 'solid',  color: '#3b82f6' },
  { from: 'candidate-gen', to: 'simulation',      label: 'Mutant candidates',          type: 'solid',  color: '#3b82f6' },
  { from: 'simulation',    to: 'qc-ranker',       label: 'ΔG & clash scores',          type: 'solid',  color: '#3b82f6' },
  { from: 'qc-ranker',     to: 'reporter',        label: 'Ranked candidates',          type: 'dashed', color: '#8b5cf6' },
  { from: 'reporter',      to: 'critic',          label: 'Iteration report',           type: 'dashed', color: '#8b5cf6' },
  { from: 'critic',        to: 'planner',         label: 'Feedback & Iteration Context', type: 'dashed', color: '#f59e0b' },
]

// ── Helpers ──────────────────────────────────────────────────────────────────

function nodeById(id: string): FlowNode {
  return NODES.find(n => n.id === id)!
}

function getEdgePath(edge: FlowEdge): { path: string; labelX: number; labelY: number } {
  const src = nodeById(edge.from)
  const dst = nodeById(edge.to)

  // Horizontal edges (same y)
  if (src.y === dst.y) {
    const y = src.y + NODE_H / 2
    const x1 = src.x + NODE_W
    const x2 = dst.x
    return {
      path: `M ${x1} ${y} L ${x2} ${y}`,
      labelX: (x1 + x2) / 2,
      labelY: y - 10,
    }
  }

  // Vertical edge on right side: simulation -> qc-ranker
  if (edge.from === 'simulation' && edge.to === 'qc-ranker') {
    const x = src.x + NODE_W / 2
    const y1 = src.y + NODE_H
    const y2 = dst.y
    return {
      path: `M ${x} ${y1} L ${x} ${y2}`,
      labelX: x + 14,
      labelY: (y1 + y2) / 2,
    }
  }

  // Feedback loop: critic -> planner (left side, going up)
  if (edge.from === 'critic' && edge.to === 'planner') {
    const x = src.x + NODE_W / 2
    const y1 = src.y
    const y2 = dst.y + NODE_H
    return {
      path: `M ${x} ${y1} L ${x} ${y2}`,
      labelX: x - 14,
      labelY: (y1 + y2) / 2,
    }
  }

  // Fallback: straight line
  const x1 = src.x + NODE_W / 2
  const y1 = src.y + NODE_H / 2
  const x2 = dst.x + NODE_W / 2
  const y2 = dst.y + NODE_H / 2
  return {
    path: `M ${x1} ${y1} L ${x2} ${y2}`,
    labelX: (x1 + x2) / 2,
    labelY: (y1 + y2) / 2 - 8,
  }
}

// ── Detail Panel ────────────────────────────────────────────────────────────

function DetailPanel({ agent, onClose }: { agent: Agent; onClose: () => void }) {
  return (
    <div className="absolute right-4 top-4 z-20 w-80 max-h-[340px] overflow-y-auto bg-[var(--bg)] border border-[var(--border)] rounded-xl shadow-2xl shadow-black/40 animate-slide-in">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${
            agent.status === 'active' ? 'bg-green-400 animate-ping-slow' :
            agent.status === 'error' ? 'bg-red-400' : 'bg-[var(--bg-sunk)]'
          }`} />
          <span className="text-sm font-semibold text-[var(--text-mute)]">{agent.name}</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${
            agent.status === 'active' ? 'bg-[var(--pos-soft)] text-[var(--pos)]' :
            agent.status === 'error' ? 'bg-[var(--neg-soft)] text-[var(--neg)]' : 'bg-[var(--bg-elev)] text-[var(--text-dim)]'
          }`}>
            {agent.status}
          </span>
        </div>
        <button onClick={onClose} className="text-[var(--text-dim)] hover:text-[var(--text-mute)] transition-colors p-1 -mr-1">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="px-4 py-3 space-y-3">
        {/* Last message */}
        <div>
          <span className="text-[10px] text-[var(--text-mute)] font-semibold uppercase tracking-wide">Latest Message</span>
          <p className="text-xs text-[var(--text-mute)] mt-1 font-mono leading-relaxed bg-[var(--bg-elev)] rounded-md px-2 py-1.5">
            {agent.lastMessage || 'No messages yet'}
          </p>
        </div>

        {/* Report */}
        {agent.report && <ReportDisplay report={agent.report} />}
      </div>
    </div>
  )
}

function ReportDisplay({ report }: { report: AgentReport }) {
  if (report.type === 'plan') {
    return (
      <div className="space-y-1.5">
        <span className="text-[10px] text-[var(--warn)] font-semibold uppercase tracking-wide">Planner Hypothesis</span>
        {report.hypothesis && (
          <p className="text-xs text-[var(--text-mute)] font-mono leading-relaxed bg-[var(--bg-elev)] rounded-md px-2 py-1.5 whitespace-pre-wrap">
            {report.hypothesis}
          </p>
        )}
        {report.strategy && (
          <div>
            <span className="text-[10px] text-[var(--text-mute)]">Strategy: </span>
            <span className="text-xs text-[var(--text-mute)]">{report.strategy}</span>
          </div>
        )}
      </div>
    )
  }

  if (report.type === 'critic') {
    return (
      <div className="space-y-1.5">
        <span className="text-[10px] text-[var(--violet)] font-semibold uppercase tracking-wide">Critic Hypothesis</span>
        {report.hypothesis && (
          <p className="text-xs text-[var(--text-mute)] font-mono leading-relaxed bg-[var(--bg-elev)] rounded-md px-2 py-1.5 whitespace-pre-wrap">
            {report.hypothesis}
          </p>
        )}
        {report.proposed_changes && report.proposed_changes.length > 0 && (
          <div className="space-y-1">
            <span className="text-[10px] text-[var(--text-mute)] font-semibold uppercase tracking-wide">Proposed Changes</span>
            {report.proposed_changes.map((ch, i) => (
              <div key={i} className="bg-[var(--bg-elev)] rounded-md px-2 py-1.5 text-[10px]">
                <span className="text-[var(--text-mute)] font-semibold">{ch.parameter}: </span>
                <span className="text-[var(--neg)] line-through">{ch.old}</span>
                <span className="text-[var(--text-mute)]"> → </span>
                <span className="text-[var(--pos)]">{ch.new}</span>
                <p className="text-[var(--text-mute)] mt-0.5">{ch.rationale}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (report.type === 'reporter') {
    return (
      <div className="space-y-1.5">
        <span className="text-[10px] text-[var(--accent)] font-semibold uppercase tracking-wide">Reporter Summary</span>
        {report.summary && (
          <pre className="text-xs text-[var(--text-mute)] font-mono leading-relaxed bg-[var(--bg-elev)] rounded-md px-2 py-1.5 whitespace-pre-wrap break-words">
            {report.summary}
          </pre>
        )}
      </div>
    )
  }

  return null
}

// ── Main Component ──────────────────────────────────────────────────────────

interface AgentFlowDiagramProps {
  agents: Agent[]
  rosettaSubsteps?: RosettaSubstep[]
  iteration: number
  totalIterations: number
}

export function AgentFlowDiagram({ agents, rosettaSubsteps = [], iteration, totalIterations }: AgentFlowDiagramProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)

  // Build agentId -> Agent lookup
  const agentMap = useMemo(() => {
    const map: Record<string, Agent> = {}
    for (const a of agents) {
      map[a.id] = a
    }
    return map
  }, [agents])

  // Build substepId -> RosettaSubstep lookup
  const substepMap = useMemo(() => {
    const map: Record<string, RosettaSubstep> = {}
    for (const s of rosettaSubsteps) {
      map[s.id] = s
    }
    return map
  }, [rosettaSubsteps])

  // Find the selected agent for the detail panel
  const selectedAgent = useMemo(() => {
    if (!selectedNodeId) return null
    const node = NODES.find(n => n.id === selectedNodeId)
    if (!node) return null
    if (node.agentId) return agentMap[node.agentId] ?? null
    return null
  }, [selectedNodeId, agentMap])

  const getNodeStatus = (node: FlowNode): 'active' | 'completed' | 'error' | 'idle' => {
    // Check agent status first
    if (node.agentId) {
      const agent = agentMap[node.agentId]
      if (agent?.status === 'active') return 'active'
      if (agent?.status === 'error') return 'error'
    }
    // Fallback to substep status
    if (node.substepId) {
      const substep = substepMap[node.substepId]
      if (substep?.status === 'running') return 'active'
      if (substep?.status === 'completed') return 'completed'
      if (substep?.status === 'failed') return 'error'
    }
    return 'idle'
  }

  const SVG_W = 800
  const SVG_H = 300

  return (
    <section className="card relative overflow-hidden" aria-label="Agent Flow Diagram">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest flex items-center gap-1.5">
          Agent Flow Diagram
          <HelpTooltip title="Agent Flow Diagram">
            <p>에이전트 간 데이터 흐름을 시각화합니다.</p>
            <p>노드는 각 에이전트, 엣지는 데이터 전달 경로를 나타냅니다.</p>
            <p><strong>색상</strong>: 활성 에이전트는 밝게, 비활성은 어둡게 표시됩니다.</p>
          </HelpTooltip>
        </h2>
        <div className="flex items-center gap-3">
          {/* Legend */}
          <div className="hidden sm:flex items-center gap-3 text-[10px] text-[var(--text-mute)]">
            <span className="flex items-center gap-1">
              <span className="w-4 h-0 border-t-2 border-blue-500 inline-block" /> Generation
            </span>
            <span className="flex items-center gap-1">
              <span className="w-4 h-0 border-t-2 border-dashed border-purple-500 inline-block" /> Evaluation
            </span>
            <span className="flex items-center gap-1">
              <span className="w-4 h-0 border-t-2 border-dashed border-amber-500 inline-block" /> Feedback
            </span>
          </div>
          {/* Iteration badge */}
          <div className="flex items-center gap-1.5 bg-[var(--bg-elev)] border border-[var(--border)] rounded-lg px-2.5 py-1">
            <span className="text-[10px] text-[var(--text-mute)]">Iteration</span>
            <span className="text-sm font-bold text-[var(--accent)] font-mono">{iteration}</span>
            <span className="text-[10px] text-[var(--text-mute)]">/ {totalIterations}</span>
          </div>
        </div>
      </div>

      {/* SVG diagram */}
      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          className="w-full min-w-[600px]"
          style={{ height: 'auto', maxHeight: '380px' }}
        >
          <defs>
            {/* Arrow markers */}
            <marker id="arrow-blue" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 4 L 0 8 z" fill="var(--accent)" />
            </marker>
            <marker id="arrow-purple" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 4 L 0 8 z" fill="var(--violet)" />
            </marker>
            <marker id="arrow-amber" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 4 L 0 8 z" fill="var(--warn)" />
            </marker>

            {/* Glow filters for active nodes */}
            <filter id="glow-blue" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feFlood floodColor="var(--accent)" floodOpacity="0.4" />
              <feComposite in2="blur" operator="in" />
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="glow-purple" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feFlood floodColor="var(--violet)" floodOpacity="0.4" />
              <feComposite in2="blur" operator="in" />
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="glow-red" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feFlood floodColor="var(--neg)" floodOpacity="0.4" />
              <feComposite in2="blur" operator="in" />
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Animated dash for data flow */}
            <style>{`
              @keyframes dash-flow {
                to { stroke-dashoffset: -20; }
              }
              .edge-flow {
                animation: dash-flow 1.2s linear infinite;
              }
              @keyframes node-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
              }
              .node-active-pulse {
                animation: node-pulse 2s ease-in-out infinite;
              }
            `}</style>
          </defs>

          {/* Edges */}
          {EDGES.map(edge => {
            const { path, labelX, labelY } = getEdgePath(edge)
            const markerId = edge.color === '#3b82f6' ? 'arrow-blue' : edge.color === '#f59e0b' ? 'arrow-amber' : 'arrow-purple'
            const isVertical = (edge.from === 'simulation' && edge.to === 'qc-ranker') || (edge.from === 'critic' && edge.to === 'planner')
            const textAnchor = isVertical
              ? (edge.from === 'critic' ? 'end' : 'start')
              : 'middle'

            return (
              <g key={`${edge.from}-${edge.to}`}>
                {/* Animated flow indicator (subtle dashed overlay) */}
                <path
                  d={path}
                  fill="none"
                  stroke={edge.color}
                  strokeWidth={1.5}
                  strokeDasharray={edge.type === 'dashed' ? '6 4' : 'none'}
                  strokeOpacity={0.6}
                  markerEnd={`url(#${markerId})`}
                />
                {/* Animated particles on top */}
                <path
                  d={path}
                  fill="none"
                  stroke={edge.color}
                  strokeWidth={2}
                  strokeDasharray="4 16"
                  strokeOpacity={0.9}
                  className="edge-flow"
                />

                {/* Edge label */}
                <text
                  x={labelX}
                  y={labelY}
                  textAnchor={textAnchor}
                  className="text-[8px]"
                  fill="var(--text-mute)"
                  fontFamily="system-ui, sans-serif"
                  fontSize="8"
                >
                  {edge.label}
                </text>
              </g>
            )
          })}

          {/* Nodes */}
          {NODES.map(node => {
            const status = getNodeStatus(node)
            const isActive = status === 'active'
            const isCompleted = status === 'completed'
            const isError = status === 'error'
            const isSelected = selectedNodeId === node.id

            const fillColor = isError ? '#1e1115' : isActive ? '#0c1929' : isCompleted ? '#0a1a12' : '#0f172a'
            const strokeColor = isError ? '#ef4444' : isActive ? node.glowColor : isCompleted ? '#4ade80' : isSelected ? node.color : '#334155'
            const filterAttr = isActive ? `url(#glow-${node.color === '#3b82f6' ? 'blue' : 'purple'})` : isError ? 'url(#glow-red)' : undefined

            return (
              <g
                key={node.id}
                className={`cursor-pointer ${isActive ? 'node-active-pulse' : ''}`}
                onClick={() => setSelectedNodeId(selectedNodeId === node.id ? null : node.id)}
                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelectedNodeId(selectedNodeId === node.id ? null : node.id) } }}
                role="button"
                tabIndex={0}
                aria-label={`${node.label}: ${status}`}
              >
                {/* Node box */}
                <rect
                  x={node.x}
                  y={node.y}
                  width={NODE_W}
                  height={NODE_H}
                  rx={10}
                  ry={10}
                  fill={fillColor}
                  stroke={strokeColor}
                  strokeWidth={isActive || isSelected ? 2 : 1}
                  filter={filterAttr}
                />

                {/* Status dot */}
                <circle
                  cx={node.x + 14}
                  cy={node.y + 16}
                  r={4}
                  fill={isError ? '#ef4444' : isActive ? '#4ade80' : isCompleted ? '#22d3ee' : '#64748b'}
                >
                  {isActive && (
                    <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
                  )}
                </circle>

                {/* Agent label */}
                <text
                  x={node.x + 26}
                  y={node.y + 20}
                  fill={isError ? '#fca5a5' : '#e2e8f0'}
                  fontFamily="system-ui, sans-serif"
                  fontSize="12"
                  fontWeight="600"
                >
                  {node.label}
                </text>

                {/* Subtitle (line 1) */}
                <text
                  x={node.x + 14}
                  y={node.y + 38}
                  fill="var(--text-mute)"
                  fontFamily="system-ui, sans-serif"
                  fontSize="8"
                >
                  {node.subtitle.split('\n')[0]}
                </text>
                {/* Subtitle (line 2) */}
                {node.subtitle.split('\n')[1] && (
                  <text
                    x={node.x + 14}
                    y={node.y + 50}
                    fill="var(--text-mute)"
                    fontFamily="system-ui, sans-serif"
                    fontSize="8"
                  >
                    {node.subtitle.split('\n')[1]}
                  </text>
                )}

                {/* Click hint (small icon area) */}
                <text
                  x={node.x + NODE_W - 14}
                  y={node.y + 16}
                  fill="var(--text-dim)"
                  fontFamily="system-ui, sans-serif"
                  fontSize="10"
                  textAnchor="end"
                >
                  {isSelected ? '−' : '+'}
                </text>
              </g>
            )
          })}

          {/* Pipeline flow labels */}
          <text x={380} y={25} textAnchor="middle" fill="var(--accent)" fontSize="9" fontWeight="600" fontFamily="system-ui, sans-serif" opacity={0.6}>
            Generation Pipeline
          </text>
          <text x={380} y={SVG_H - 8} textAnchor="middle" fill="var(--violet)" fontSize="9" fontWeight="600" fontFamily="system-ui, sans-serif" opacity={0.6}>
            Evaluation Pipeline
          </text>
        </svg>
      </div>

      {/* Detail panel (overlay) */}
      {selectedAgent && (
        <DetailPanel agent={selectedAgent} onClose={() => setSelectedNodeId(null)} />
      )}
    </section>
  )
}
