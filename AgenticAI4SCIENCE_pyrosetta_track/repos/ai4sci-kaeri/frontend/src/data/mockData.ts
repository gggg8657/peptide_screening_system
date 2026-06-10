import type {
  PipelineStep,
  Agent,
  Candidate,
  QCGate,
  ConvergencePoint,
  RiskItem,
} from '../types'
import { generateSequence, randomInRange } from '../lib/utils'

// ─── Pipeline Steps (Silo B: PyRosetta mutation → dock loop) ─────────────────
export const PIPELINE_STEPS: PipelineStep[] = [
  { id: 'step06', label: 'PyRosetta FlexPepDock', shortLabel: 'Rosetta', status: 'completed', duration: '4m 12s' },
  { id: 'step07', label: 'Analysis', shortLabel: 'Analysis', status: 'running', duration: undefined },
]

export const CURRENT_ITERATION = 3
export const TOTAL_ITERATIONS = 5

// ─── Agents ───────────────────────────────────────────────────────────────────
export const AGENTS: Agent[] = [
  {
    id: 'planner',
    name: 'Planner',
    type: 'LLM',
    status: 'idle',
    lastMessage: 'Iteration 3 strategy: focus mutations on positions 7-10 (FWKT pharmacophore)',
    taskCount: 12,
  },
  {
    id: 'qc-ranker',
    name: 'QC & Ranker',
    type: 'Code',
    status: 'idle',
    lastMessage: 'ddG gate passed: 6/8. Clash gate: 5/6.',
    taskCount: 9,
  },
  {
    id: 'diversity-mgr',
    name: 'DiversityMgr',
    type: 'Code',
    status: 'idle',
    lastMessage: 'Configured only (structural diversity via FoldMason)',
    taskCount: 0,
    isRuntimeActive: false,
  },
  {
    id: 'critic',
    name: 'Scientist Critic',
    type: 'LLM',
    status: 'idle',
    lastMessage: 'Iteration 2 review: ddG improvement +0.8 kcal/mol vs baseline.',
    taskCount: 4,
  },
  {
    id: 'reporter',
    name: 'Reporter',
    type: 'LLM',
    status: 'idle',
    lastMessage: 'Iteration 2 report saved to lab notebook.',
    taskCount: 2,
  },
]

// ─── Candidates ───────────────────────────────────────────────────────────────
function makeCandidates(): Candidate[] {
  const candidates: Candidate[] = []
  for (let i = 0; i < 50; i++) {
    const ddG = randomInRange(-45, -10, 2)
    const totalScore = randomInRange(-700, -300, 1)
    const clashScore = randomInRange(0, 25, 1)
    const finalScore = Math.round(-ddG * 100) / 100

    const gatePass = ddG <= -5 && clashScore <= 10

    let failReason: string | undefined
    if (!gatePass) {
      const reasons: string[] = []
      if (ddG > -5) reasons.push(`ddG ${ddG} > -5`)
      if (clashScore > 10) reasons.push(`Clash ${clashScore} > 10`)
      failReason = reasons.join('; ')
    }

    candidates.push({
      rank: i + 1,
      id: `SSTR2-P${String(i + 1).padStart(3, '0')}`,
      sequence: generateSequence(12 + Math.floor(Math.random() * 6)),
      ddG,
      totalScore,
      clashScore,
      finalScore,
      result: gatePass ? 'PASS' : 'FAIL',
      failReason,
    })
  }
  return candidates
    .sort((a, b) => a.ddG - b.ddG)
    .map((c, idx) => ({ ...c, rank: idx + 1 }))
}

export const CANDIDATES: Candidate[] = makeCandidates()

// ─── QC Gates ─────────────────────────────────────────────────────────────────
export const QC_GATES: QCGate[] = [
  { name: 'Rosetta ΔG', criterion: 'ΔG ≤ -5.0 kcal/mol', passed: 32, failed: 18, total: 50 },
  { name: 'Rosetta Clash', criterion: 'Clash ≤ 10 REU', passed: 28, failed: 4, total: 32 },
]

// ─── Convergence Data ─────────────────────────────────────────────────────────
export const CONVERGENCE_DATA: ConvergencePoint[] = [
  { iteration: 1, bestDdG: -5.2, topCandidates: 4, converged: false },
  { iteration: 2, bestDdG: -6.8, topCandidates: 7, converged: false },
  { iteration: 3, bestDdG: -7.9, topCandidates: 14, converged: false },
  { iteration: 4, bestDdG: -8.4, topCandidates: 18, converged: false },
  { iteration: 5, bestDdG: -8.6, topCandidates: 21, converged: true },
]

// ─── Risk Matrix ──────────────────────────────────────────────────────────────
export const RISK_ITEMS: RiskItem[] = [
  // P0 - Critical
  { id: 'r1', label: 'Off-target toxicity', probability: 'High', impact: 'Critical', priority: 'P0', description: 'Peptide binds non-SSTR2 receptors causing systemic effects' },
  { id: 'r2', label: 'Model hallucination', probability: 'Medium', impact: 'Critical', priority: 'P0', description: 'ESMFold/OpenFold generates physically impossible structures' },

  // P1 - Severe
  { id: 'r3', label: 'Low oral bioavailability', probability: 'High', impact: 'Severe', priority: 'P1', description: 'Peptide degraded in GI tract before absorption' },
  { id: 'r4', label: 'Pipeline divergence', probability: 'Medium', impact: 'Severe', priority: 'P1', description: 'Convergence criterion never met after 5 iterations' },
  { id: 'r5', label: 'Docking pose artifacts', probability: 'Medium', impact: 'Severe', priority: 'P1', description: 'DiffDock predicts non-physiological binding modes' },
  { id: 'r6', label: 'Protease instability', probability: 'High', impact: 'Severe', priority: 'P1', description: 'Peptide cleaved by serum proteases within minutes' },

  // P2 - Minor + High prob / Severe + Low prob
  { id: 'r7', label: 'Slow ESMFold runtime', probability: 'High', impact: 'Minor', priority: 'P2', description: 'Folding >2h per iteration exceeds time budget' },
  { id: 'r8', label: 'Low sequence diversity', probability: 'Medium', impact: 'Minor', priority: 'P2', description: 'Generator collapses to single motif family' },
  { id: 'r9', label: 'Selectivity data gap', probability: 'Low', impact: 'Severe', priority: 'P2', description: 'SSTR1/SSTR3 counter-screen data unavailable' },
  { id: 'r10', label: 'API rate limits', probability: 'Medium', impact: 'Minor', priority: 'P2', description: 'LLM API quota exceeded during critic cycle' },
  { id: 'r11', label: 'Force field inaccuracy', probability: 'Low', impact: 'Severe', priority: 'P2', description: 'PyRosetta ddG calculation systematic bias > 1 kcal/mol' },

  // P3 - Low risk
  { id: 'r12', label: 'Report formatting error', probability: 'Low', impact: 'Minor', priority: 'P3', description: 'Reporter agent output malformed JSON' },
  { id: 'r13', label: 'Version mismatch', probability: 'Low', impact: 'Minor', priority: 'P3', description: 'Docker image dependency version conflicts' },
  { id: 'r14', label: 'Log file overflow', probability: 'Medium', impact: 'Minor', priority: 'P3', description: 'Disk space consumed by verbose pipeline logs' },
  { id: 'r15', label: 'UI rendering lag', probability: 'Low', impact: 'Minor', priority: 'P3', description: 'Dashboard slow with 500+ candidates' },
]
