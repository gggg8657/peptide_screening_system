// Pipeline Step Types
export type StepStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface PipelineStep {
  id: string
  label: string
  shortLabel: string
  status: StepStatus
  duration?: string
}

export interface RosettaSubstep {
  id: string
  label: string
  status: StepStatus
  duration?: string
}

export interface TimelineEvent {
  iteration: number
  stage: string
  status: StepStatus
  message: string
  ts: string
}

// Agent Types
export type AgentType = 'LLM' | 'Code'
export type AgentStatus = 'idle' | 'active' | 'error'

export interface AgentReport {
  type: 'plan' | 'critic' | 'reporter'
  iteration: number
  hypothesis?: string
  strategy?: string
  run_id?: string
  proposed_changes?: Array<{
    parameter: string
    old: string
    new: string
    rationale: string
  }>
  summary?: string
}

export interface Agent {
  id: string
  name: string
  type: AgentType
  status: AgentStatus
  lastMessage: string
  taskCount: number
  report?: AgentReport
  lastActiveTs?: string
  isRuntimeActive?: boolean
}

// Candidate Types
export type PassFail = 'PASS' | 'FAIL' | 'REF'

export interface Candidate {
  rank: number
  id: string
  sequence: string
  ddG: number
  totalScore: number
  clashScore: number
  finalScore: number
  result: PassFail
  failReason?: string
  runId?: string
  source?: 'live' | 'historical' | 'silo_a' | 'silo_b'
  pdb_path?: string
  rcsb_hits?: unknown[]
  rcsb_match_summary?: string
  // P05: ClusterPanel 확장 payload — BE가 이 필드를 candidate dict에 포함시킬 때 전달됨
  // instability_index: BE가 NaN 검출 시 null 반환(stability.py:124) → null 허용
  selectivity_margin?: number
  instability_index?: number | null
  gravy?: number
  net_charge_ph74?: number
  fwkt_contact?: boolean
  chelator_site_available?: boolean
  // 2026-06-09 다목적 cheap-objectives (pyrosetta_flow/multiobjective.py Step 0 enrichment)
  half_life_h?: number | null      // 반감기 surrogate (시간, 랭킹용 — 임상 수치 아님)
  admet_score?: number | null      // ADMET 합리성 surrogate (0~1)
  boman_index?: number | null
  pi?: number | null
  mo_score?: number | null         // 다목적 통합 스칼라 (ΔG+선택성+반감기+ADMET, 0~1)
}

// QC Gate Types
export interface QCGate {
  name: string
  criterion: string
  passed: number
  failed: number
  total: number
}

// Convergence Data Types
export interface ConvergencePoint {
  iteration: number
  bestDdG: number
  topCandidates: number
  converged: boolean
}

// Risk Matrix Types
export type RiskPriority = 'P0' | 'P1' | 'P2' | 'P3'
export type RiskProbability = 'Low' | 'Medium' | 'High'
export type RiskImpact = 'Minor' | 'Severe' | 'Critical'

export interface RiskItem {
  id: string
  label: string
  probability: RiskProbability
  impact: RiskImpact
  priority: RiskPriority
  description: string
}

// Visualization Image Types
export interface VisualizationImage {
  label: string
  url: string
  type: 'overview' | 'closeup' | 'interface' | 'electrostatics'
}

export type ExecutionMode = 'full' | 'pyrosettaOnly'

// Validation Types (legacy)
export interface ValidationCheck {
  rule: string
  value: number
  passed: boolean
}

export type ValidationStatus = 'pass' | 'fail' | 'not_found' | 'pending'

export interface ValidationResult {
  id: string
  validation: ValidationStatus
  checks: ValidationCheck[]
}

// Unified Validation Types
export interface CriterionDef {
  label: string
  group: 'pharmacological' | 'radiopharmaceutical' | 'statistical'
  description: string
  default_enabled: boolean
  threshold: Record<string, number | string>
  unit: string
}

export interface CriterionCheck {
  id: string
  label: string
  group: string
  description: string
  unit: string
  threshold: Record<string, number | string>
  value: number | null
  passed: boolean
  detail?: string
  skipped?: boolean
  error?: string
}

export type UnifiedVerdict = 'PASS' | 'CAUTION' | 'FAIL'

export interface UnifiedCandidateResult {
  sequence: string
  verdict: UnifiedVerdict
  pass_rate: number
  n_passed: number
  n_failed: number
  n_skipped: number
  n_total: number
  checks: CriterionCheck[]
}

export interface UnifiedValidationResponse {
  validated_at: string
  criteria_used: string[]
  n_candidates: number
  results: UnifiedCandidateResult[]
}

export interface ValidationPreset {
  label: string
  description: string
  criteria: string[]
}

// ADMET Types
export interface AdmetProperties {
  mw: number
  net_charge_ph74: number
  n_hbd: number
  n_hba: number
  hydrophobicity: number
  amphipathicity_index: number
  druglikeness_score: number
  druglikeness_breakdown: Record<string, { passed: boolean; value: number | boolean; range: string; points: number }>
}

export type NephrotoxRiskLevel = 'Low' | 'Moderate' | 'High'

export interface NephrotoxResult {
  n_lys: number
  n_arg: number
  n_his: number
  cationic_residues: number
  net_charge: number
  renal_risk_score: number
  risk_level: NephrotoxRiskLevel
  warning: string
}

/** pepADMET(JCIM 2026) 독성 — 백엔드가 `pyrosetta_flow.pepadmet_runner`로 채움 */
export interface PepadmetToxicityPayload {
  available: boolean
  sequence?: string
  error?: string
  /** infer 스크립트가 선형 서열 폴백을 썼을 때 */
  graph_note?: string
  binary_toxicity?: number
  is_toxic?: boolean
  toxicity_type?: string
  toxicity_type_confidence?: number
  neurotoxicity_type?: string
  neurotoxicity_confidence?: number
  hc50?: number
}

export interface AdmetFullResult {
  sequence: string
  admet: AdmetProperties
  nephrotox: NephrotoxResult
  /** conda pepadmet env + local clone 있을 때만; 없으면 available=false */
  pepadmet?: PepadmetToxicityPayload
}
