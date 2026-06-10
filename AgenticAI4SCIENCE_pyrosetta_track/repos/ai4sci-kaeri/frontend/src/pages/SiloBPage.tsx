import { useState, useCallback } from 'react'
import { PipelineStatus } from '../components/PipelineStatus'
import { AgentMonitor } from '../components/AgentMonitor'
import { CandidateTable } from '../components/CandidateTable'
import { PharmacologyPanel } from '../components/PharmacologyPanel'
import { ValidationPanel } from '../components/ValidationPanel'
import { QCGateChart } from '../components/QCGateChart'
import { ConvergenceGraph } from '../components/ConvergenceGraph'
import { RiskMatrix } from '../components/RiskMatrix'
import { VisualizationPanel } from '../components/VisualizationPanel'
import { AgentFlowDiagram } from '../components/AgentFlowDiagram'
import { SequenceLogo } from '../components/SequenceLogo'
import { MutationAnalysis } from '../components/MutationAnalysis'
import { PositionEnrichment } from '../components/PositionEnrichment'
import { ExperimentControl } from '../components/ExperimentControl'
import { MoleculeViewer } from '../components/MoleculeViewer'
import { LoopTimeline } from '../components/LoopTimeline'
import { DdGDistribution } from '../components/DdGDistribution'
import { SARHeatmap } from '../components/SARHeatmap'
import { RCSBMatchPanel } from '../components/RCSBMatchPanel'
import { RunComparisonPanel } from '../components/RunComparisonPanel'
import { ClusterPanel } from '../components/ClusterPanel'
import { ADMETPanel } from '../components/ADMETPanel'
import type { VisualizationImage } from '../types'
import { usePipelineContext } from '../contexts/PipelineContext'
import { useExperiment } from '../hooks/useExperiment'
import { PIPELINE_STEPS, AGENTS, CANDIDATES, QC_GATES, CONVERGENCE_DATA, CURRENT_ITERATION, TOTAL_ITERATIONS } from '../data/mockData'

const SILO_B_STEPS = new Set(['step01', 'step03b', 'silo_b', 'step06', 'step07'])

export function SiloBPage() {
  const live = usePipelineContext()
  const experiment = useExperiment(3000)
  const isArchive = !!live.viewingArchive
  const isLive = live.connected && (live.steps.length > 0 || isArchive)
  const currentRunFailed = isLive && (
    live.steps.some(step => step.status === 'failed') ||
    live.timeline.some(event => event.status === 'failed')
  )
  const showHistoricalFallback = isLive && currentRunFailed && live.candidates.length === 0 && live.historicalCandidates.length > 0

  // approach='b' 강제: SiloBPage에서 실험 시작 시 항상 Silo B로 고정
  const siloBExperiment = {
    ...experiment,
    startExperiment: (overrides?: Record<string, unknown>) =>
      experiment.startExperiment({ approach: 'b', ...overrides }),
  }

  const [viewerPdb, setViewerPdb] = useState<{ url: string; id: string } | null>(null)
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Set<string>>(new Set())

  const handleView3D = useCallback((candidateId: string) => {
    const allCands = [...live.candidates, ...live.historicalCandidates]
    const cand = allCands.find(c => c.id === candidateId)
    if (cand?.pdb_path) {
      setViewerPdb({ url: `/api/structures/${cand.pdb_path}`, id: candidateId })
      return
    }
    // 아카이브 모드: run_id 기반 경로
    const runId = live.viewingArchive || live.runId || 'sst14_agentic_mutdock'
    const base = `pyrosetta_flow/archives/${runId}`
    let pdbUrl: string
    const iterMatch = candidateId.match(/^iter(\d+)_cand(\d+)$/)
    if (iterMatch) {
      const iterNum = iterMatch[1].padStart(2, '0')
      const candNum = iterMatch[2].padStart(3, '0')
      pdbUrl = `/api/structures/${base}/iter_${iterNum}/cand_${candNum}.pdb`
    } else if (candidateId.startsWith('baseline')) {
      pdbUrl = `/api/structures/${base}/${candidateId}.pdb`
    } else {
      pdbUrl = `/api/structures/${base}/${candidateId}.pdb`
    }
    setViewerPdb({ url: pdbUrl, id: candidateId })
  }, [live.candidates, live.historicalCandidates, live.viewingArchive, live.runId])

  // Silo B 관련 스텝만 표시 (Silo A 전용 스텝 제외)
  const filteredLiveSteps = isLive ? live.steps.filter(s => SILO_B_STEPS.has(s.id)) : PIPELINE_STEPS
  // Silo B 소스 후보만 표시
  const filteredLiveCandidates = isLive
    ? (showHistoricalFallback ? live.historicalCandidates : live.candidates).filter(c => c.source === 'silo_b' || c.source === 'live' || !c.source)
    : CANDIDATES

  const steps = filteredLiveSteps
  const agents = isLive ? live.agents : AGENTS
  const candidates = filteredLiveCandidates
  const qcGates = isLive ? live.qcGates : QC_GATES
  const convergence = isLive ? live.convergence : CONVERGENCE_DATA
  const iteration = isLive ? live.iteration : CURRENT_ITERATION
  const totalIterations = isLive ? live.totalIterations : TOTAL_ITERATIONS
  const executionMode = isLive ? live.executionMode : 'full'
  const rosettaSubsteps = isLive ? live.rosettaSubsteps : []
  const timeline = isLive ? live.timeline : []
  const visualizationImages: VisualizationImage[] = isLive && live.visualizationImages
    ? live.visualizationImages
    : []

  return (
    <>
      {/* Silo B 페이지 타이틀 배지 */}
      <section className="card border border-[var(--violet)]/30 bg-[var(--violet-soft)]">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-[var(--violet)] uppercase tracking-widest">Silo B</span>
          <span className="text-xs text-[var(--text-dim)]">·</span>
          <span className="text-xs text-[var(--text-mute)]">PyRosetta Mutation-Dock</span>
          <span className="ml-auto text-[10px] font-mono text-[var(--violet)] bg-[var(--violet-soft)] px-2 py-0.5 rounded border border-[var(--violet)]/30">
            BLOSUM62 + FlexPepDock
          </span>
        </div>
      </section>

      <ExperimentControl experiment={siloBExperiment} iteration={iteration} totalIterations={totalIterations} />

      <section className="card border border-[var(--border)]">
        <p className="text-xs text-[var(--text-mute)]">
          Iteration loop: <span className="font-mono text-[var(--accent)]">mutate -&gt; dock -&gt; QC -&gt; Critic -&gt; Reporter</span>
        </p>
        <p className="text-xs text-[var(--text-mute)] mt-1">
          Each iteration records reporter output and critic hypotheses before advancing to the next cycle.
        </p>
      </section>

      <PipelineStatus
        steps={steps}
        rosettaSubsteps={rosettaSubsteps}
        iteration={iteration}
        totalIterations={totalIterations}
        completed={isLive ? live.completed : false}
        executionMode={isLive ? live.executionMode : 'full'}
      />

      {showHistoricalFallback && (
        <section className="card border border-[var(--warn)]/30 bg-[var(--warn-soft)]">
          <p className="text-xs text-amber-200">
            Current run failed; showing historical ranking.
          </p>
        </section>
      )}

      {timeline.length > 0 && (
        <section className="card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-[var(--text-mute)] uppercase tracking-widest">
              Loop Timeline
            </h2>
            <span className="text-xs text-[var(--text-mute)]">{timeline.length} events</span>
          </div>
          <LoopTimeline events={timeline} />
        </section>
      )}

      {visualizationImages.length > 0 && (
        <VisualizationPanel images={visualizationImages} iteration={iteration} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-4 items-start">
        <AgentMonitor agents={agents} iteration={iteration} executionMode={executionMode} />
        <CandidateTable candidates={candidates} historicalCandidates={isLive ? live.historicalCandidates : []} onView3D={handleView3D} onSelectionChange={setSelectedCandidateIds} archiveRunId={live.viewingArchive} />
      </div>

      <DdGDistribution candidates={candidates} />

      <ValidationPanel candidates={candidates} selectedIds={selectedCandidateIds} />
      <ClusterPanel candidates={candidates} />
      <ADMETPanel candidates={candidates} />
      <PharmacologyPanel candidates={candidates} />
      <RCSBMatchPanel candidates={candidates} />
      <SARHeatmap candidates={candidates} />
      <AgentFlowDiagram agents={agents} rosettaSubsteps={rosettaSubsteps} iteration={iteration} totalIterations={totalIterations} />

      <SequenceLogo candidates={candidates} />
      <MutationAnalysis candidates={candidates} />
      <PositionEnrichment candidates={candidates} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <QCGateChart gates={qcGates} />
        <ConvergenceGraph data={convergence} />
      </div>

      <RunComparisonPanel runs={isLive ? live.archivedRuns : []} currentRunId={isLive ? live.runId : null} />

      <RiskMatrix />

      {viewerPdb && (
        <MoleculeViewer
          pdbUrl={viewerPdb.url}
          candidateId={viewerPdb.id}
          onClose={() => setViewerPdb(null)}
        />
      )}
    </>
  )
}
