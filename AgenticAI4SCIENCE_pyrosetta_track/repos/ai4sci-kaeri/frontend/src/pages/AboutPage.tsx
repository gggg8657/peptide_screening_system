import { useState, type ReactNode } from 'react'
import {
  Activity,
  Atom,
  BarChart3,
  Beaker,
  Bot,
  ChevronDown,
  ChevronUp,
  Cpu,
  Dna,
  FlaskConical,
  GitBranch,
  Layers,
  Mail,
  Microscope,
  Shield,
} from 'lucide-react'
import { Sequence } from '../components/dashboard/Sequence'
import { TierBadge } from '../components/dashboard/TierBadge'

interface FeatureDetail {
  icon: typeof FlaskConical
  title: string
  tone: 'accent' | 'pos' | 'warn' | 'neg' | 'violet' | 'teal'
  desc: string
  details: string[]
  formulas?: string[]
  refs?: string[]
}

const FEATURES: FeatureDetail[] = [
  {
    icon: Dna,
    title: 'Dual-Silo Pipeline Architecture',
    tone: 'accent',
    desc: 'Two independent computational strategies target SSTR2: Silo B uses SST-14 guided mutation with local PyRosetta, while Silo A employs de novo backbone design through 8 NVIDIA NIM APIs.',
    details: [
      'Silo B (pyrosetta_flow): SST-14 native peptide (AGCKNFFWKTFTSC) as seed sequence. Guided mutation at 12 mutable positions (excluding Cys3/Cys13 disulfide anchor). FlexPepDock refinement with ddG scoring. Fully operational, local-only execution.',
      'Silo A (AG_src/pipeline): De novo backbone generation via RFdiffusion, inverse folding via ProteinMPNN, fast QC via ESMFold, docking via DiffDock/Boltz-2, selectivity screening against SSTR1/3/4/5 off-targets. Requires NVIDIA NIM API access.',
      'Cross-silo validation: When both silos independently converge on the same binding motif, confidence is dramatically higher than either alone. This is the key advantage of the dual approach.',
      'Error isolation: Each silo runs as an independent subprocess (ProcessManager). A crash in Silo A never affects Silo B, and vice versa.',
    ],
    refs: [
      'Lamberts et al. (1996) — Somatostatin receptor subtypes and disease. Eur J Clin Invest 26(6):435-459',
      'Reubi et al. (2001) — Somatostatin receptors in human tumors. J Steroid Biochem Mol Biol 76(1-5):25-35',
    ],
  },
  {
    icon: Bot,
    title: '5-Agent Agentic System',
    tone: 'violet',
    desc: 'Planner, Critic, Reporter (LLM), QC & Ranker, Diversity Manager (Code). LLM agents use vLLM (Qwen3.5-35B-A3B default) + per-agent override (planner=DeepSeek-R1 옵션).',
    details: [
      'Planner Agent (LLM): Generates scientific hypotheses for each iteration. Outputs focus_positions (which residues to mutate) and suggested_mutations (specific amino acid substitutions). Uses structured JSON output parsing.',
      'Scientist Critic Agent (LLM): Analyzes iteration results and proposes max 2 parameter changes per cycle. Evaluates ddG trends, identifies failure patterns, and suggests strategic adjustments (e.g., shift focus positions, adjust mutation aggressiveness).',
      'Reporter Agent (LLM): Documents each iteration in lab notebook format. Generates human-readable summaries of hypotheses, results, and proposed next steps.',
      'QC & Ranker Agent (Code): Applies multi-gate quality control (ddG threshold, clash score limit). Ranks surviving candidates by composite score. Deterministic, no LLM involved.',
      'Diversity Manager Agent (Code): Enforces structural diversity via FoldMason alignment. Prevents convergence to a single motif family. Active only in Silo A (Silo B uses sequence-level dedup instead).',
    ],
    refs: [
      'Lu et al. (2024) — The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery. arXiv:2408.06292',
    ],
  },
  {
    icon: Activity,
    title: 'FlexPepDock Refinement',
    tone: 'pos',
    desc: 'PyRosetta FlexPepDock high-resolution refinement with ddG scoring. Stochastic Monte Carlo introduces variance addressed by multi-trial validation.',
    details: [
      'FlexPepDock ab-initio protocol: Full-atom refinement of peptide-protein complexes. Uses Monte Carlo minimization with backbone and side-chain flexibility. The stochastic nature means each run produces slightly different results.',
      'Binding energy calculation: ddG = Score(complex) - Score(receptor_alone) - Score(peptide_alone). More negative ddG indicates stronger binding. Typical therapeutic peptide range: -8 to -15 kcal/mol.',
      'Observed variance: Standard deviation of 3.5-15.0 kcal/mol per candidate across 10 independent trials. This variance is inherent to the Monte Carlo sampling and is not a bug.',
      'Parallel execution: ThreadPoolExecutor with configurable max_parallel_workers (default: 4). Each FlexPepDock refinement runs as a subprocess with timeout protection (default: 300s).',
    ],
    formulas: [
      'ddG = E_complex - E_receptor - E_peptide',
      'E_total = E_vdw + E_hbond + E_elec + E_solvation + E_entropy',
      'Variance: sigma = sqrt(1/N * sum((x_i - x_mean)^2))',
    ],
    refs: [
      'Raveh et al. (2011) — Sub-angstrom modeling of complexes between flexible peptides and globular proteins. Proteins 78(9):2029-2040',
      'London et al. (2011) — Rosetta FlexPepDock web server. Nucleic Acids Res 39:W249-W253',
    ],
  },
  {
    icon: Beaker,
    title: 'Multi-Trial Validation',
    tone: 'warn',
    desc: '2-stage strategy: fast 1-trial screening followed by configurable N-trial validation (3/5/10 trials). Top-3 mean aggregation with early stopping.',
    details: [
      'Stage 1 — Screening: Single FlexPepDock trial per candidate. Fast (~2 min/candidate). Used to eliminate clearly unfavorable candidates via QC gates (ddG, clash score).',
      'Stage 2 — Validation: N independent FlexPepDock trials for final selected candidates. Each trial uses different random seed. Results aggregated via top-3 mean (discard outliers, average 3 best ddG values).',
      'Early stopping: After 5 trials, if coefficient of variation (CV) drops below threshold (default: 0.15), remaining trials are skipped. Saves ~50% compute on well-converged candidates.',
      'Catastrophic failure filtering: Trials producing ddG > 0 (physically unreasonable repulsion) are excluded from aggregation. These represent failed MC sampling, not real binding predictions.',
      'Paper-quality protocol: 10 trials per candidate, top-3 mean of N=10, reported with standard deviation. Expected overhead: ~30 minutes for 5 final candidates.',
    ],
    formulas: [
      'top3_mean = mean(sorted(ddG_trials)[:3])',
      'CV = stdev(ddG_trials) / |mean(ddG_trials)|',
      'Early stop condition: CV < 0.15 AND n_trials >= 5',
    ],
  },
  {
    icon: BarChart3,
    title: 'QC Gate System',
    tone: 'violet',
    desc: 'Multi-gate quality control pipeline. Candidates must pass all gates to advance. Real-time visualization of pass/fail ratios.',
    details: [
      'Gate 1 — ddG Threshold: ddG < rosetta_ddg_max (default: -5.0 kcal/mol). Filters candidates with insufficient binding affinity. Adjustable per experiment.',
      'Gate 2 — Clash Score: clash_score < rosetta_clash_max (default: 10 REU). Detects steric clashes between peptide and receptor atoms. High clash indicates physically unrealistic poses.',
      'Gate 3 — Structural Integrity: Verified via Cys3-Cys14 disulfide bond distance (< 2.5 A) and backbone RMSD to reference (< 5.0 A). Ensures structural validity of the refined complex.',
      'Silo A additional gates: pLDDT gate (ESMFold confidence > 70), docking score gate (DiffDock), selectivity margin gate (SSTR2 vs off-targets).',
      'Fail reasons are tracked per candidate and displayed in the dashboard CandidateTable for debugging.',
    ],
    formulas: [
      'PASS = (ddG < ddG_max) AND (clash < clash_max)',
      'pass_rate = n_passed / n_total',
    ],
  },
  {
    icon: Shield,
    title: 'Pharmacological Validation',
    tone: 'neg',
    desc: '13 literature-based property calculations plus 5 structural rules. No subjective weights — pure physicochemical values only.',
    details: [
      'Hydropathy (GRAVY): Grand Average of Hydropathy using Kyte-Doolittle scale. GRAVY = sum(H_i) / N. Negative = hydrophilic (good for injectable peptides).',
      'Boman Index: Protein-protein interaction potential. BI = sum(S_i) / N. Values > 2.48 indicate strong protein binding tendency.',
      'Instability Index: Dipeptide-based stability predictor. II = (10/N) * sum(DIWV[x_i][x_{i+1}]). Stable if II < 40.',
      'Hydrophobic Moment: Amphipathicity measure. mu_H = sqrt((sum(H_i*sin(i*delta))^2 + (sum(H_i*cos(i*delta))^2)) / N. High mu_H = good membrane interaction.',
      'Wimley-White Interface Scale: Membrane interface partitioning free energy. Predicts membrane-active regions.',
      'Structural Rules (PASS/FAIL): (1) FWKT motif conservation at pos 7-10, (2) K9-D122 salt bridge distance < 4.0 A, (3) Cys3-Cys14 disulfide bond intact, (4) Phe6-Phe11 aromatic stacking, (5) N-terminal chelator accessibility (DOTA/NOTA conjugation site).',
    ],
    formulas: [
      'GRAVY = (1/N) * sum(H_i), H_i from Kyte-Doolittle scale',
      'Boman Index = (1/N) * sum(S_i), S_i from Radzicka-Wolfenden scale',
      'Instability Index = (10/N) * sum(DIWV[x_i][x_{i+1}])',
      'mu_H = sqrt(A^2 + B^2) / N, where A = sum(H_i*sin(i*delta)), B = sum(H_i*cos(i*delta))',
      'Net Charge = sum(+1 for K,R at pH 7) + sum(-1 for D,E at pH 7)',
    ],
    refs: [
      'Kyte & Doolittle (1982) — A simple method for displaying the hydropathic character of a protein. J Mol Biol 157(1):105-132',
      'Boman (2003) — Antibacterial peptides: basic facts and emerging concepts. J Intern Med 254(3):197-215',
      'Guruprasad et al. (1990) — Correlation between stability of a protein and its dipeptide composition. Protein Eng 4(2):155-161',
      'Eisenberg et al. (1982) — The hydrophobic moment detects periodicity in protein hydrophobicity. PNAS 81:140-144',
      'Wimley & White (1996) — Experimentally determined hydrophobicity scale for proteins at membrane interfaces. Nat Struct Biol 3:842-848',
    ],
  },
  {
    icon: Microscope,
    title: 'Convergence Detection',
    tone: 'teal',
    desc: 'Statistical convergence using Mann-Whitney U test (no scipy dependency). Monitors ddG plateau across iterations.',
    details: [
      'Mann-Whitney U test: Non-parametric test comparing ddG distributions of consecutive iteration windows. Tests H0: "the two windows have the same ddG distribution" vs H1: "the later window is significantly different".',
      'Window-based comparison: Compares a sliding window of W iterations (default: 3). If the U-test fails to reject H0 (p > significance), the pipeline has converged.',
      'Custom implementation: Pure Python Mann-Whitney U without scipy dependency. Uses normal approximation for n > 20, exact computation for small samples.',
      'Additional CV check: Coefficient of variation of the best ddG across the window. If CV < 0.05, convergence is declared regardless of U-test result.',
      'Early termination: Pipeline stops iterating when convergence is detected, saving compute. The remaining iteration budget is reported but not consumed.',
    ],
    formulas: [
      'U = n1*n2 + n1*(n1+1)/2 - R1',
      'z = (U - n1*n2/2) / sqrt(n1*n2*(n1+n2+1)/12)',
      'Converged if p > alpha (default alpha = 0.05)',
      'CV = stdev(best_ddG_per_iter) / |mean(best_ddG_per_iter)|',
    ],
    refs: [
      'Mann & Whitney (1947) — On a Test of Whether one of Two Random Variables is Stochastically Larger than the Other. Ann Math Stat 18(1):50-60',
    ],
  },
  {
    icon: GitBranch,
    title: 'Thompson Sampling Bandit',
    tone: 'violet',
    desc: 'Data-driven mutation position selection. Learns which positions yield better ddG improvements using Beta distribution posteriors.',
    details: [
      'Multi-armed bandit formulation: Each mutable position (12 positions in SST-14) is an "arm". Pulling an arm = mutating that position. Reward = ddG improvement vs parent.',
      'Thompson Sampling: For each position, maintain Beta(alpha, beta) posterior. Sample from each posterior, select top-K positions with highest sampled values. Balances exploration (try under-sampled positions) vs exploitation (focus on known-good positions).',
      'Update rule: After each candidate is scored, update the selected positions. If ddG improved: alpha += 1 (success). If ddG worsened: beta += 1 (failure).',
      'Focus positions: bandit_n_focus (default: 3) positions are selected per iteration via Thompson Sampling. The Planner agent receives these as suggested focus areas.',
      'Prior: Uniform prior Beta(1, 1) for all positions. After ~20 candidates, the posterior reliably identifies productive mutation sites.',
    ],
    formulas: [
      'Prior: Beta(alpha=1, beta=1) for each position',
      'Sampling: theta_i ~ Beta(alpha_i, beta_i) for i in positions',
      'Select: top_K = argsort(theta)[-K:]',
      'Update (success): alpha_i += 1',
      'Update (failure): beta_i += 1',
      'E[theta_i] = alpha_i / (alpha_i + beta_i)',
    ],
    refs: [
      'Thompson (1933) — On the Likelihood that One Unknown Probability Exceeds Another. Biometrika 25(3-4):285-294',
      'Chapelle & Li (2011) — An Empirical Evaluation of Thompson Sampling. NeurIPS 2011',
    ],
  },
  {
    icon: Layers,
    title: 'Cross-Run Deduplication',
    tone: 'pos',
    desc: 'Sequences from prior runs are tracked via JSONL experiment log. Automatic skip of previously tested sequences.',
    details: [
      'JSONL experiment log: Each candidate result is appended to experiment_log.jsonl with sequence, ddG, run_id, timestamp. Append-only format ensures no data loss.',
      'Dedup mechanism: At mutation generation time, the adapter checks new sequences against a seen_sequences set loaded from the JSONL log. Duplicates are rejected and re-generated.',
      'Max retry: max_dedup_trials (default: 50) attempts before accepting a duplicate. This prevents infinite loops when the sequence space is nearly exhausted.',
      'Cross-run benefit: A 5-iteration run testing 40 candidates (8/iter) populates the dedup set. The next run automatically avoids those 40 sequences, ensuring fresh exploration.',
    ],
  },
  {
    icon: Atom,
    title: 'Radiopharmaceutical Context',
    tone: 'warn',
    desc: 'SSTR2-targeting peptides for radiopharmaceutical applications: 68Ga PET imaging, 177Lu/225Ac PRRT therapy.',
    details: [
      'Theranostic approach: Same peptide vector conjugated with diagnostic (68Ga, PET) or therapeutic (177Lu beta, 225Ac alpha) radionuclides via chelator (DOTA/NOTA).',
      'SSTR2 target: Somatostatin receptor type 2, overexpressed in neuroendocrine tumors (NETs), small cell lung cancer, and other malignancies. UniProt P30874, 369aa GPCR.',
      'Clinical precedent: 68Ga-DOTATATE (Netspot) for PET imaging, 177Lu-DOTATATE (Lutathera) for PRRT. Both FDA-approved, based on octreotide SST analog.',
      'Design constraints for PRRT: (1) N-terminal chelator accessibility for DOTA conjugation, (2) Metabolic stability (protease resistance), (3) Renal clearance profile (nephrotoxicity risk), (4) SSTR2 selectivity over SSTR1/3/4/5.',
      'ADMET gate: Druglikeness scoring includes molecular weight, charge, hydrophobicity. Nephrotoxicity risk prediction based on cationic charge density and renal tubular reabsorption potential.',
    ],
    refs: [
      'Strosberg et al. (2017) — Phase 3 Trial of 177Lu-DOTATATE for Midgut Neuroendocrine Tumors. NEJM 376(2):125-135',
      'Reubi (2003) — Peptide receptors as molecular targets for cancer diagnosis and therapy. Endocrine Rev 24(4):389-427',
      'Bodei et al. (2015) — Peptide receptor radionuclide therapy with 177Lu-DOTATATE. Eur J Nucl Med 42(1):5-11',
    ],
  },
  {
    icon: Cpu,
    title: 'NVIDIA NIM APIs (Silo A)',
    tone: 'teal',
    desc: '8 NIM cloud APIs for the full 3-ARM pipeline. Hybrid local/cloud deployment strategy.',
    details: [
      'ESMFold: Fast protein structure prediction for QC. pLDDT confidence score as quality gate. ~8 GB VRAM for local deployment.',
      'RFdiffusion: De novo protein backbone generation conditioned on target binding site. Generates diverse binder scaffolds. ~24 GB VRAM (cloud recommended).',
      'ProteinMPNN: Inverse folding — designs amino acid sequences that fold into a given backbone structure. ~8 GB VRAM for local.',
      'DiffDock: Molecular docking via diffusion model. Predicts binding poses and confidence scores. ~16 GB VRAM.',
      'Boltz-2: Biomolecular structure prediction for complex assembly. Provides binding affinity estimates. ~24 GB VRAM (cloud recommended).',
      'OpenFold3: High-accuracy protein structure prediction. Used for receptor structure when no experimental PDB available. ~16 GB VRAM.',
      'ESM2: Protein language model embeddings. Used for sequence similarity and functional annotation. ~4 GB VRAM (lightweight, local recommended).',
      'MolMIM: Small molecule generation and optimization. Used for chelator-peptide linker design. ~8 GB VRAM.',
      'Hybrid deployment: ESMFold + ProteinMPNN + ESM2 local (~20 GB total, fits RTX 3090/4090). RFdiffusion, Boltz-2, DiffDock via NGC cloud API.',
    ],
    refs: [
      'Lin et al. (2023) — Evolutionary-scale prediction of atomic-level protein structure with a language model. Science 379(6637):1123-1130',
      'Watson et al. (2023) — De novo design of protein structure and function with RFdiffusion. Nature 620:1089-1100',
      'Dauparas et al. (2022) — Robust deep learning–based protein sequence design using ProteinMPNN. Science 378(6615):49-56',
      'Corso et al. (2023) — DiffDock: Diffusion Steps, Twists, and Turns for Molecular Docking. ICLR 2023',
    ],
  },
  {
    icon: FlaskConical,
    title: 'Real-Time Dashboard',
    tone: 'accent',
    desc: 'Live monitoring via StatusEmitter with 2-second polling. Pipeline progress, agent status, candidate ranking, 3D structure viewer.',
    details: [
      'StatusEmitter: JSON file-based bridge between Python pipeline and React frontend. Uses fcntl.flock() for safe concurrent writes. File-based approach avoids WebSocket complexity while providing near-real-time updates.',
      'Polling: Frontend polls /api/status every 2 seconds. Minimal overhead (~1KB JSON per poll). AbortController cancels stale requests on new polls.',
      'Pipeline progress: Step-level status (pending/running/completed/failed) with duration tracking. Rosetta sub-step tracking (7 phases: prepare, mutate, refine, score, qc, critic, reporter).',
      'Candidate ranking: Sortable table with ddG, total score, clash score, final score. Color-coded PASS/FAIL/REF badges. Click-to-view 3D structure via Mol* viewer.',
      '3D Structure Viewer: Mol* (Molstar) v5.6.1 embedded viewer. Supports 4 presets: default, polymer-id, polymer-chain-instance, and empty. Loads PDB files from /api/structures/ endpoint.',
      'Run history: Archived runs stored as JSON snapshots. Browse past experiments, compare results. Archive includes PDB files for structural analysis.',
      'Convergence graph: Real-time best-ddG per iteration chart. Visual convergence indicator (plateau detection highlighted).',
    ],
  },
]

interface CriterionRef {
  id: string
  label: string
  formula: string
  scale: string
  threshold: string
  interpretation: string
}

const CRITERIA_GROUPS: { group: string; tone: FeatureDetail['tone']; items: CriterionRef[] }[] = [
  {
    group: 'Pharmacological',
    tone: 'neg',
    items: [
      {
        id: 'gravy',
        label: 'GRAVY (소수성)',
        formula: 'GRAVY = (1/N) × Σ H_i',
        scale: 'Kyte-Doolittle (1982) hydropathy scale. H_i: per-residue hydropathy value (-4.5 to +4.5)',
        threshold: '-2.0 ≤ GRAVY ≤ 1.0',
        interpretation: '음수 = 친수성 (주사제 적합), 양수 과다 → 간 흡수 증가, 수용성 저하',
      },
      {
        id: 'boman_index',
        label: 'Boman Index (단백질 결합력)',
        formula: 'BI = -(1/N) × Σ S_i',
        scale: 'Radzicka-Wolfenden (1988) 용해 자유에너지 스케일. S_i: cyclohexane→water transfer energy (kcal/mol)',
        threshold: 'BI ≥ 2.48 kcal/mol',
        interpretation: '≥2.48 → 강한 단백질 결합 잠재력 (GPCR 리간드 필수)',
      },
      {
        id: 'instability_index',
        label: 'Instability Index (안정성)',
        formula: 'II = (10/N) × Σ DIWV[x_i][x_{i+1}]',
        scale: 'Guruprasad et al. (1990) dipeptide instability weight values (DIWV). 400개 디펩타이드 조합별 가중치 테이블',
        threshold: 'II < 40.0',
        interpretation: '<40 = 안정한 단백질, ≥40 = 불안정 (in vivo 분해 가속)',
      },
      {
        id: 'aliphatic_index',
        label: 'Aliphatic Index (지방족 지수)',
        formula: 'AI = x_A + 2.9·x_V + 3.9·(x_I + x_L)',
        scale: 'Ikai (1980). x_A, x_V, x_I, x_L = Ala, Val, Ile, Leu의 몰 분율 (%)',
        threshold: 'AI ≤ 150.0',
        interpretation: '높으면 열안정성 증가하나 응집·수용성 저하. 과도히 높으면 fail',
      },
      {
        id: 'isoelectric_point',
        label: 'pI (등전점)',
        formula: 'Henderson-Hasselbalch 이분법 (200 iterations)',
        scale: 'N-term/C-term + 측쇄 pKa 값 (D:3.65, E:4.25, H:6.0, C:8.18, Y:10.07, K:10.53, R:12.48)',
        threshold: '4.0 ≤ pI ≤ 10.0',
        interpretation: '극단적 pI → 비특이적 조직 흡수. 생리적 pH(7.4) 근처가 이상적',
      },
      {
        id: 'extinction_coefficient',
        label: 'ε₂₈₀ (몰 흡광계수)',
        formula: 'ε₂₈₀ = n_W × 5500 + n_Y × 1490 + n_SS × 125',
        scale: 'Pace et al. (1995). n_W = Trp 개수, n_Y = Tyr 개수, n_SS = disulfide bond 개수',
        threshold: 'ε₂₈₀ ≥ 1000 M⁻¹cm⁻¹',
        interpretation: '0이면 UV280 정량 불가 → QC 어려움. Trp/Tyr 없는 서열은 대안 정량법 필요',
      },
      {
        id: 'n_end_rule',
        label: 'N-end Rule (세포내 반감기)',
        formula: 'Lookup: N-말단 잔기 → 반감기 테이블',
        scale: 'Varshavsky (1996) mammalian reticulocyte 시스템. M,V,G,P → >30h; R,K,F,L,W,Y,H → 2-10 min',
        threshold: '반감기 ≥ 2.0 hours',
        interpretation: '안정화 잔기(M/V/G/P/A/S/T) = 장시간 안정. 불안정 잔기 → 유비퀴틴-프로테아좀 급속 분해',
      },
      {
        id: 'hydrophobic_moment',
        label: 'μH (소수성 모멘트)',
        formula: 'μH = √(A² + B²) / N, A = Σ H_i·sin(i·δ), B = Σ H_i·cos(i·δ)',
        scale: 'Eisenberg et al. (1982). δ = 100° (α-helix 기준). Sliding window (11 residues) 중 최대값',
        threshold: 'μH ≤ 0.6',
        interpretation: '높은 μH → 양친매성 = 비특이적 막 결합 위험. 막 투과 펩타이드는 높은 값 필요',
      },
      {
        id: 'wimley_white',
        label: 'Wimley-White (막 상호작용)',
        formula: 'WW_total = Σ WW_i (kcal/mol)',
        scale: 'Wimley & White (1996) water→membrane interface ΔG 스케일. 잔기별 막 분배 에너지',
        threshold: 'WW_total ≥ -5.0 kcal/mol',
        interpretation: '음수 = 막 선호, 양수 = 수상 선호. 과도한 음수 → 비특이적 막 삽입 위험',
      },
      {
        id: 'protease_sites',
        label: 'Protease Sites (절단 부위)',
        formula: 'Δ = candidate_sites - native_sites',
        scale: '4 프로테아제 규칙: Chymotrypsin (F/Y/W 후), Trypsin (K/R 후), NEP (소수성-소수성), Pepsin (F/Y/L 사이)',
        threshold: 'Δ ≤ +2 vs native (SST-14)',
        interpretation: 'native SST-14 대비 절단 부위 증가가 ≤2개이면 통과. 많으면 in vivo 급속 분해',
      },
      {
        id: 'charge_ph_profile',
        label: 'Charge vs pH (전하 프로파일)',
        formula: 'Q(pH) = Σ Henderson-Hasselbalch 각 잔기',
        scale: 'pH 7.4 (혈장), pH 6.5 (종양 미세환경), pH 2.0/5.0 각각에서 순전하 계산',
        threshold: '|Q(pH 7.4)| ≤ 5.0',
        interpretation: '과도한 전하 → 비특이적 조직 결합. pH 7.4↔6.5 차이 → 종양 선택적 전하 변화 가능',
      },
      {
        id: 'blosum62',
        label: 'BLOSUM62 (변이 보존성)',
        formula: 'avg_score = (1/N_mut) × Σ BLOSUM62[native_i][mutant_i]',
        scale: 'Henikoff & Henikoff (1992) BLOSUM62 치환 행렬. 양수 = 보존적 치환, 음수 = 비보존적',
        threshold: 'avg_score ≥ -2.0',
        interpretation: '평균 점수 < -2 → 진화적으로 비보존적 변이가 많음 → 기능 손실 위험',
      },
    ],
  },
  {
    group: 'Radiopharmaceutical',
    tone: 'warn',
    items: [
      {
        id: 'metal_coordination',
        label: 'Metal Coordination (금속 배위)',
        formula: 'n_strong = count(H, C in seq)',
        scale: '강 배위 잔기: His(이미다졸), Cys(티올). 약 배위: Asp, Glu, Met. 킬레이터(DOTA/NOTA) 간섭 평가',
        threshold: 'n_strong ≤ 1',
        interpretation: '강한 금속 배위 잔기 ≥2 → DOTA/NOTA 킬레이터 금속 착물 안정성 저해 위험',
      },
      {
        id: 'nephrotox',
        label: 'Nephrotox (신독성)',
        formula: 'Score = min(100, (n_K + n_R) × 20 + max(0, net_charge) × 15)',
        scale: '양이온 잔기(K, R) 기반 신장 세뇨관 재흡수 위험. DOTATATE 참조: 1 Lys, score ~25 (Low)',
        threshold: 'Risk ≤ Moderate (score ≤ 60)',
        interpretation: 'Low(<30): 안전, Moderate(30-60): 아미노산 co-infusion 권장, High(>60): 신독성 위험 높음',
      },
    ],
  },
  {
    group: 'Statistical',
    tone: 'accent',
    items: [
      {
        id: 'rank_stability',
        label: 'Rank Stability (순위 안정성)',
        formula: 'appearances = count(seq ∈ top-K, for each repeat)',
        scale: '복수 반복 실험에서 top-K 순위 내 출현 횟수. 안정적 후보 = 매번 top-K에 포함',
        threshold: 'appearances ≥ 2',
        interpretation: '1회만 top-K → 우연. ≥2회 반복 등장 → 통계적으로 신뢰 가능한 후보',
      },
      {
        id: 'score_consistency',
        label: 'Score Consistency (점수 일관성)',
        formula: 'CV = σ(ddG_trials) / |μ(ddG_trials)|',
        scale: 'ddG 변동계수 (coefficient of variation). 복수 trial 결과의 분산 대비 평균',
        threshold: 'CV ≤ 0.5',
        interpretation: 'CV > 0.5 → ddG 값이 trial마다 크게 변동 → 해당 후보의 결합력 불확실',
      },
      {
        id: 'no_dominance',
        label: 'No Dominance (독점 검출)',
        formula: 'dominance = (top1_appearances / total_repeats) > 0.8',
        scale: '단일 후보가 전체 반복의 80% 이상 1위를 독점하는지 검사',
        threshold: 'dominance = false',
        interpretation: '독점 시 → 탐색 다양성 부족 or 과적합. 복수 후보가 경쟁적으로 순위 교차해야 건강',
      },
    ],
  },
]

const TECH_STACK = [
  { label: 'Frontend', items: ['React 19', 'Vite 7', 'TypeScript', 'Tailwind CSS', 'Mol* 5.6.1', 'Lucide Icons', 'react-router v6'] },
  { label: 'Backend', items: ['FastAPI', 'Python 3.12', 'PyRosetta', 'Ollama LLM', 'StatusEmitter', 'fcntl.flock'] },
  { label: 'Computation', items: ['FlexPepDock', 'FoldMason', 'PyMOL', 'Thompson Sampling', 'Mann-Whitney U', 'Multi-trial validation'] },
  { label: 'NIM APIs', items: ['ESMFold', 'RFdiffusion', 'ProteinMPNN', 'DiffDock', 'Boltz-2', 'OpenFold3', 'ESM2', 'MolMIM'] },
] as const

const ARCHITECTURE_LINES = [
  '┌──────────────────────────────────────────────────────────────┐',
  '│                  SSTR2 AI Co-Scientist System                │',
  '├───────────────────────────┬──────────────────────────────────┤',
  '│  Silo A: 3-ARM Pipeline   │  Silo B: Mutation Simulation     │',
  '│  (AG_src/pipeline)        │  (pyrosetta_flow)                │',
  '│                           │                                  │',
  '│  De novo backbone design  │  SST-14 guided mutation          │',
  '│  8 NVIDIA NIM APIs        │  Local PyRosetta only            │',
  '│  8-step pipeline          │  2-step: mutate → dock           │',
  '├───────────────────────────┴──────────────────────────────────┤',
  '│                     Shared Components                        │',
  '│  Agents: Planner, Critic, Reporter, QC&Ranker, DiversityMgr │',
  '│  LLM: vLLM (Qwen3.5-35B-A3B + DeepSeek-R1) · FlexPepDock        │',
  '│  Backend: FastAPI · Frontend: React/Vite + Mol*             │',
  '└──────────────────────────────────────────────────────────────┘',
] as const

const GROUP_REFERENCES = [
  'Kyte & Doolittle (1982) — A simple method for displaying the hydropathic character of a protein. J Mol Biol 157(1):105-132',
  'Boman (2003) — Antibacterial peptides: basic facts and emerging concepts. J Intern Med 254(3):197-215',
  'Guruprasad et al. (1990) — Correlation between stability of a protein and its dipeptide composition. Protein Eng 4(2):155-161',
  'Ikai (1980) — Thermostability and aliphatic index of globular proteins. J Biochem 88(6):1895-1898',
  'Pace et al. (1995) — How to measure and predict the molar absorption coefficient of a protein. Protein Sci 4(11):2411-2423',
  'Varshavsky (1996) — The N-end rule: functions, mysteries, uses. PNAS 93(22):12142-12149',
  'Eisenberg et al. (1982) — The hydrophobic moment detects periodicity in protein hydrophobicity. PNAS 81:140-144',
  'Wimley & White (1996) — Experimentally determined hydrophobicity scale for proteins at membrane interfaces. Nat Struct Biol 3:842-848',
  'Henikoff & Henikoff (1992) — Amino acid substitution matrices from protein blocks. PNAS 89(22):10915-10919',
] as const

export function AboutPage() {
  const [expandAll, setExpandAll] = useState(false)

  return (
    <div className="space-y-4 font-sans text-text-base">
      <section className="overflow-hidden rounded-[4px] border border-border-base bg-bg-elev">
        <div className="grid gap-0 xl:grid-cols-[minmax(0,1.3fr)_360px]">
          <div className="border-b border-border-base xl:border-b-0 xl:border-r">
            <div className="flex items-center gap-3 border-b border-border-base px-4 py-3">
              <div className="grid h-9 w-9 place-items-center rounded-[4px] bg-text-base font-mono text-[11px] font-bold text-bg">P*</div>
              <div className="min-w-0">
                <h1 className="text-sm font-semibold tracking-[-0.01em]">AI-Scientist: SSTR2 Peptide Binder Design Pipeline</h1>
                <p className="text-[11px] text-text-mute">PRST_N_FM · About / system brief</p>
              </div>
              <div className="ml-auto hidden items-center gap-2 md:flex">
                <TierBadge tier="T2" />
                <span className="rounded-[4px] border border-border-base bg-bg-sunk px-2 py-1 font-mono text-[10px] text-text-mute">dual-silo</span>
              </div>
            </div>

            <div className="space-y-6 px-4 py-4">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 rounded-[4px] border border-accent bg-accent-soft px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-accent-text">
                  <FlaskConical className="h-3.5 w-3.5" />
                  SSTR2 AI Co-Scientist
                </div>
                <p className="max-w-3xl text-[13px] leading-6 text-text-base">
                  Agentic multi-step optimization system for designing SSTR2-targeting peptide binders for radiopharmaceutical applications.
                  The frontend, pipeline, and evaluation rules are structured around a dark, data-dense workflow that keeps scientific review fast.
                </p>
              </div>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <HeroStat label="Target" value="SSTR2" sub="UniProt P30874 · 7XNA holo" tone="accent" />
                <HeroStat label="Reference" value={<Sequence seq="AGCKNFFWKTFTSC" />} sub="SST-14 wildtype peptide" />
                <HeroStat label="Agent Stack" value="5" sub="planner / critic / reporter / qc / diversity" tone="violet" />
                <HeroStat label="Execution" value="A + B" sub="de novo backbone + local mutation simulation" tone="pos" />
              </div>

              <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_280px]">
                <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.18em] text-text-dim">Operating Principles</p>
                      <p className="text-[11px] text-text-mute">prototype-aligned panel language · hairline borders · mono metrics</p>
                    </div>
                    <span className="font-mono text-[10px] text-text-mute">dark theme locked</span>
                  </div>
                  <div className="grid gap-2 md:grid-cols-3">
                    <InfoChip label="Structure" value="No shadows" />
                    <InfoChip label="Radius" value="4px" />
                    <InfoChip label="Numbers" value="tabular-nums" />
                  </div>
                </div>

                <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Clinical Context</div>
                  <div className="space-y-2 text-[11px] leading-5 text-text-mute">
                    <p><span className="font-medium text-text-base">68Ga PET</span> and <span className="font-medium text-text-base">177Lu / 225Ac PRRT</span> are the target deployment contexts.</p>
                    <p>The pipeline preserves SST-14 pharmacophore logic while searching for more selective, synthesis-ready variants.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <aside className="flex flex-col">
            <PanelHeader
              eyebrow="Snapshot"
              title="Pipeline Reference"
              meta="Sequence · tier · stack"
            />
            <div className="flex-1 space-y-4 px-4 py-4">
              <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Reference Sequence</div>
                <Sequence seq="AGCKNFFWKTFTSC" showRuler big />
                <div className="mt-2 font-mono text-[10px] text-text-mute">Cys3 / Cys14 disulfide anchor · FWKT pharmacophore preserved</div>
              </div>

              <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Decision Labels</div>
                <div className="flex flex-wrap gap-2">
                  <TierBadge tier="T2" />
                  <TierBadge tier="T1" />
                  <TierBadge tier="T0" />
                </div>
                <div className="mt-3 grid gap-2">
                  <InfoChip label="Frontend" value="React 19 / Vite 7" />
                  <InfoChip label="Backend" value="FastAPI / PyRosetta" />
                  <InfoChip label="Cloud" value="8 NVIDIA NIM APIs" />
                </div>
              </div>

              <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Workflow</div>
                <ol className="space-y-2 text-[11px] text-text-mute">
                  <li className="flex gap-2"><span className="font-mono text-text-dim">01</span><span>Silo A generates de novo backbones and screens selectivity candidates.</span></li>
                  <li className="flex gap-2"><span className="font-mono text-text-dim">02</span><span>Silo B mutates SST-14 locally with FlexPepDock scoring and QC gates.</span></li>
                  <li className="flex gap-2"><span className="font-mono text-text-dim">03</span><span>Agent outputs and validation criteria determine expansion, ranking, and stop conditions.</span></li>
                </ol>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <section className="overflow-hidden rounded-[4px] border border-border-base bg-bg-elev">
        <div className="flex flex-wrap items-center gap-3 border-b border-border-base px-4 py-3">
          <div>
            <h2 className="text-sm font-semibold">System Features</h2>
            <p className="text-[11px] text-text-mute">existing feature inventory preserved · expand / collapse interaction unchanged</p>
          </div>
          <button
            type="button"
            onClick={() => setExpandAll((prev) => !prev)}
            className="ml-auto inline-flex items-center gap-2 rounded-[4px] border border-border-base bg-bg px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.16em] text-text-mute transition-colors hover:border-border-strong hover:text-text-base"
          >
            {expandAll ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            {expandAll ? 'Collapse all' : 'Expand all'}
          </button>
        </div>
        <div className="grid gap-px bg-border-base md:grid-cols-2 xl:grid-cols-3">
          {FEATURES.map((feat) => (
            <FeatureCardControlled key={feat.title} feat={feat} forceExpand={expandAll} />
          ))}
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <section className="overflow-hidden rounded-[4px] border border-border-base bg-bg-elev">
          <PanelHeader eyebrow="System" title="Architecture Overview" meta="Dual-silo + shared agents" />
          <div className="px-4 py-4">
            <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3">
              <pre className="overflow-x-auto font-mono text-[10px] leading-5 text-text-base">
                {ARCHITECTURE_LINES.join('\n')}
              </pre>
            </div>
          </div>
        </section>

        <section className="overflow-hidden rounded-[4px] border border-border-base bg-bg-elev">
          <PanelHeader eyebrow="Stack" title="Technology Surface" meta="Frontend / backend / compute / APIs" />
          <div className="grid gap-px bg-border-base sm:grid-cols-2">
            {TECH_STACK.map((group) => (
              <div key={group.label} className="bg-bg-elev px-4 py-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-dim">{group.label}</h3>
                  <span className="font-mono text-[10px] text-text-mute">{group.items.length} items</span>
                </div>
                <div className="space-y-1.5">
                  {group.items.map((item) => (
                    <div key={item} className="rounded-[4px] border border-border-base bg-bg px-2.5 py-2 text-[11px] text-text-mute">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <ValidationCriteriaReference />

      <section className="overflow-hidden rounded-[4px] border border-border-base bg-bg-elev">
        <PanelHeader eyebrow="Contact" title="Project Contact" meta="External link preserved" />
        <div className="flex flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-[4px] border border-border-base bg-bg text-text-mute">
              <Mail className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[11px] text-text-mute">For collaboration, reproducibility questions, or frontend handoff follow-up.</p>
              <a
                href="mailto:dongjukim.dev@gmail.com"
                className="font-mono text-[12px] text-accent-text transition-colors hover:text-accent"
              >
                dongjukim.dev@gmail.com
              </a>
            </div>
          </div>
          <div className="rounded-[4px] border border-border-base bg-bg px-3 py-2 font-mono text-[10px] uppercase tracking-[0.16em] text-text-mute">
            AI4SCI KAERI
          </div>
        </div>
      </section>
    </div>
  )
}

function ValidationCriteriaReference() {
  const [open, setOpen] = useState(false)

  return (
    <section className="overflow-hidden rounded-[4px] border border-border-base bg-bg-elev">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-4 border-b border-border-base px-4 py-3 text-left"
      >
        <div>
          <h2 className="text-sm font-semibold">Validation Criteria Reference</h2>
          <p className="text-[11px] text-text-mute">17 criteria · formulas, scale source, threshold, interpretation</p>
        </div>
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.16em] text-text-mute">
          <span>{open ? 'Hide details' : 'Show details'}</span>
          {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </div>
      </button>

      {open && (
        <div className="space-y-4 px-4 py-4">
          <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3 text-[11px] leading-6 text-text-mute">
            각 후보 펩타이드 서열에 대해 아래 17개 기준을 순수 물리화학적 계산으로 평가합니다.
            외부 ML 모델 없이 아미노산 서열만으로 계산되며, 모든 threshold는 사용자 조정 가능합니다.
          </div>

          {CRITERIA_GROUPS.map((group) => (
            <div key={group.group} className="overflow-hidden rounded-[4px] border border-border-base bg-bg">
              <div className="flex items-center justify-between gap-3 border-b border-border-base px-4 py-3">
                <div className="flex items-center gap-3">
                  <ToneDot tone={group.tone} />
                  <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em]">{group.group}</h3>
                </div>
                <span className="font-mono text-[10px] text-text-mute">{group.items.length} items</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[920px] text-[11px]">
                  <thead className="bg-bg-elev">
                    <tr className="border-b border-border-base text-left text-text-dim">
                      <th className="px-3 py-2 font-medium">Criterion</th>
                      <th className="px-3 py-2 font-medium">Formula</th>
                      <th className="px-3 py-2 font-medium">Scale / Data Source</th>
                      <th className="px-3 py-2 font-medium">Threshold</th>
                      <th className="px-3 py-2 font-medium">Interpretation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.items.map((criterion) => (
                      <tr key={criterion.id} className="border-b border-border-base last:border-b-0">
                        <td className="px-3 py-3 align-top font-medium text-text-base">{criterion.label}</td>
                        <td className="px-3 py-3 align-top font-mono text-accent-text">{criterion.formula}</td>
                        <td className="px-3 py-3 align-top leading-5 text-text-mute">{criterion.scale}</td>
                        <td className="px-3 py-3 align-top font-mono text-warn whitespace-nowrap">{criterion.threshold}</td>
                        <td className="px-3 py-3 align-top leading-5 text-text-mute">{criterion.interpretation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}

          <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-dim">References</h3>
              <span className="font-mono text-[10px] text-text-mute">{GROUP_REFERENCES.length} citations</span>
            </div>
            <div className="space-y-2">
              {GROUP_REFERENCES.map((reference, index) => (
                <p key={reference} className="border-l border-border-strong pl-3 text-[11px] leading-5 text-text-mute">
                  <span className="font-mono text-text-dim">[{index + 1}]</span> {reference}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

function FeatureCardControlled({ feat, forceExpand }: { feat: FeatureDetail; forceExpand: boolean }) {
  const [localExpand, setLocalExpand] = useState(false)
  const expanded = forceExpand || localExpand
  const Icon = feat.icon
  const tone = toneClasses(feat.tone)

  return (
    <article className="bg-bg-elev">
      <div className="flex h-full flex-col">
        <div className="flex-1 px-4 py-4">
          <div className="flex items-start gap-3">
            <div className={`grid h-9 w-9 place-items-center rounded-[4px] border ${tone.soft}`}>
              <Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="mb-1 flex items-start justify-between gap-3">
                <h3 className="text-[13px] font-semibold leading-5 text-text-base">{feat.title}</h3>
                <ToneDot tone={feat.tone} />
              </div>
              <p className="text-[11px] leading-5 text-text-mute">{feat.desc}</p>
            </div>
          </div>

          {!forceExpand && (
            <button
              type="button"
              onClick={() => setLocalExpand((prev) => !prev)}
              className="mt-3 inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-text-mute transition-colors hover:text-text-base"
            >
              {localExpand ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              {localExpand ? 'Hide details' : 'Show details'}
            </button>
          )}
        </div>

        {expanded && (
          <div className="border-t border-border-base bg-bg px-4 py-4">
            <div className="space-y-2">
              {feat.details.map((detail) => (
                <div key={detail} className="flex gap-2 text-[11px] leading-5 text-text-mute">
                  <span className="font-mono text-text-dim">-</span>
                  <span>{detail}</span>
                </div>
              ))}
            </div>

            {feat.formulas && feat.formulas.length > 0 && (
              <div className="mt-4">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">Formulas</div>
                <div className="space-y-px rounded-[4px] border border-border-base bg-border-base">
                  {feat.formulas.map((formula) => (
                    <div key={formula} className="bg-bg px-3 py-2 font-mono text-[11px] text-accent-text">
                      {formula}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {feat.refs && feat.refs.length > 0 && (
              <div className="mt-4">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-text-dim">References</div>
                <div className="space-y-2">
                  {feat.refs.map((reference, index) => (
                    <p key={reference} className="border-l border-border-strong pl-3 text-[11px] leading-5 text-text-mute">
                      <span className="font-mono text-text-dim">[{index + 1}]</span> {reference}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </article>
  )
}

function PanelHeader({ eyebrow, title, meta }: { eyebrow: string; title: string; meta?: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border-base px-4 py-3">
      <div>
        <p className="text-[10px] uppercase tracking-[0.18em] text-text-dim">{eyebrow}</p>
        <h2 className="text-sm font-semibold">{title}</h2>
      </div>
      {meta ? <span className="font-mono text-[10px] text-text-mute">{meta}</span> : null}
    </div>
  )
}

function HeroStat({
  label,
  value,
  sub,
  tone = 'accent',
}: {
  label: string
  value: ReactNode
  sub: string
  tone?: FeatureDetail['tone']
}) {
  const styles = toneClasses(tone)

  return (
    <div className="rounded-[4px] border border-border-base bg-bg px-4 py-3">
      <div className="mb-1 text-[10px] uppercase tracking-[0.18em] text-text-dim">{label}</div>
      <div className={`text-[13px] font-semibold ${styles.text}`}>{value}</div>
      <div className="mt-1 font-mono text-[10px] text-text-mute">{sub}</div>
    </div>
  )
}

function InfoChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[4px] border border-border-base bg-bg-elev px-2.5 py-2 text-[11px]">
      <span className="text-text-mute">{label}</span>
      <span className="font-mono text-text-base">{value}</span>
    </div>
  )
}

function ToneDot({ tone }: { tone: FeatureDetail['tone'] }) {
  const styles = toneClasses(tone)
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${styles.fill}`} aria-hidden />
}

function toneClasses(tone: FeatureDetail['tone']) {
  switch (tone) {
    case 'pos':
      return { text: 'text-pos', soft: 'border-pos bg-pos-soft text-pos', fill: 'bg-pos' }
    case 'warn':
      return { text: 'text-warn', soft: 'border-warn bg-warn-soft text-warn', fill: 'bg-warn' }
    case 'neg':
      return { text: 'text-neg', soft: 'border-neg bg-neg-soft text-neg', fill: 'bg-neg' }
    case 'violet':
      return { text: 'text-violet', soft: 'border-violet bg-violet-soft text-violet', fill: 'bg-violet' }
    case 'teal':
      return { text: 'text-teal', soft: 'border-teal bg-teal-soft text-teal', fill: 'bg-teal' }
    case 'accent':
    default:
      return { text: 'text-accent-text', soft: 'border-accent bg-accent-soft text-accent-text', fill: 'bg-accent' }
  }
}
