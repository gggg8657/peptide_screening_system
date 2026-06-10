// Real data from KAERI SSTR2 AI Co-Scientist project (2026-05-12 snapshot)
// Source: docs/selectivity_demo_20260511/boltz_summary.json + top10_candidates.json + cand03 docs

window.PROJECT_DATA = {
  target: {
    name: "SSTR2",
    uniprot: "P30874",
    pdb: "7XNA",
    wildType: "AGCKNFFWKTFTSC",
    pharmacophore: "FWKT (pos 6-9)",
    disulfide: "Cys3 – Cys14",
  },
  offTargets: [
    { name: "SSTR1", uniprot: "P30872", pdb: "9IK8" },
    { name: "SSTR3", uniprot: "P32745", pdb: "8XIR" },
    { name: "SSTR4", uniprot: "P31391", pdb: "7XMT" },
    { name: "SSTR5", uniprot: "P35346", pdb: "8ZBJ" },
  ],
  receptors: ["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"],
  // Candidates are intentionally empty here. Runtime pages should render
  // backend data only and fall back to explicit empty-state placeholders.
  candidates: [],
  // Legacy flat step list (kept for any references; per-silo data is below)
  steps: [
    { id: "01", name: "Receptor", tool: "PyRosetta + OpenFold3" },
    { id: "02", name: "Backbone", tool: "RFdiffusion" },
    { id: "03", name: "Sequence", tool: "ProteinMPNN" },
    { id: "03b", name: "BLOSUM mutation", tool: "BLOSUM62 + LLM" },
    { id: "04", name: "QC", tool: "ESMFold", gate: "pLDDT ≥ 60" },
    { id: "05", name: "Docking", tool: "DiffDock / Boltz-2", gate: "Top 20%" },
    { id: "05b", name: "Selectivity", tool: "Boltz-2 off-target", gate: "margin ≤ −10" },
    { id: "05c", name: "Boltz cross", tool: "Boltz-2 + AF MSA", gate: "iPTM margin ≥ 0" },
    { id: "06", name: "Rosetta refine", tool: "FastRelax + FlexPepDock", gate: "ddG ≤ −1.0" },
    { id: "07", name: "Cluster", tool: "FoldMason" },
    { id: "08", name: "Stability", tool: "PepADMET + Boman" },
  ],

  // Per-silo pipeline modules — different generation strategies, shared downstream
  pipelines: {
    A: {
      name: "Silo A · De Novo",
      description: "RFdiffusion 백본부터 새로 디자인 — 3-arm screening",
      stages: [
        { id: "01",  name: "Receptor",     group: "input",  tool: "PyRosetta · OpenFold3",   env: "bio-tools",     inN: 1,  outN: 1,   inUnit: "PDB",        outUnit: "sanitized",  status: "done",    time: "0:23",  gate: null },
        { id: "02",  name: "Backbone",     group: "gen",    tool: "RFdiffusion",             env: "rfdiffusion",   inN: 1,  outN: 10,  inUnit: "receptor",   outUnit: "bb·pdb",     status: "done",    time: "4:12",  gpu: "H100×1" },
        { id: "03",  name: "Sequence",     group: "gen",    tool: "ProteinMPNN k=8/bb",      env: "proteinmpnn",   inN: 10, outN: 80,  inUnit: "bb",         outUnit: "fasta",      status: "done",    time: "1:48",  gpu: "H100×1" },
        { id: "04",  name: "QC",           group: "filter", tool: "ESMFold + SS-bond",       env: "esmfold",       inN: 80, outN: 73,  inUnit: "seq",        outUnit: "pass",       status: "done",    time: "3:21",  gpu: "H100×1", gate: "pLDDT ≥ 60", pass: 73, fail: 7 },
        { id: "05",  name: "Docking",      group: "score",  tool: "Boltz-2 SSTR2 7XNA",      env: "boltz",         inN: 73, outN: 16,  inUnit: "seq",        outUnit: "top 20%",    status: "done",    time: "12:08", gpu: "H100×4", gate: "Top 20%", pass: 16, fail: 57 },
        { id: "05b", name: "Selectivity",  group: "score",  tool: "Boltz-2 × 4 off-target",  env: "boltz",         inN: 16, outN: 8,   inUnit: "pose × 4",   outUnit: "margin pass",status: "done",    time: "8:42",  gpu: "H100×4", gate: "margin ≤ −10", pass: 8, fail: 8 },
        { id: "05c", name: "Boltz cross",  group: "score",  tool: "Boltz-2 + AF MSA",        env: "boltz",         inN: 8,  outN: null,inUnit: "pose × 5",   outUnit: "iPTM matrix",status: "running", time: "5:21",  gpu: "H100×4", gate: "iPTM margin ≥ 0", progress: 0.62 },
        { id: "06",  name: "Rosetta refine",group: "refine",tool: "FastRelax + FlexPepDock + ddG", env: "bio-tools", inN: null, outN: null, inUnit: "pose", outUnit: "refined.pdb", status: "queued", time: "—",     gpu: "CPU", gate: "ddG ≤ −1.0" },
        { id: "07",  name: "Cluster",      group: "analyze",tool: "FoldMason lDDT ≥ 0.6",    env: "bio-tools",     status: "queued",  time: "—",                                                  gate: null },
        { id: "08",  name: "Stability",    group: "analyze",tool: "PepADMET + Boman + NEP",  env: "pepadmet",      status: "queued",  time: "—",                                                  gate: "t½ ≥ 50h" },
      ],
    },
    B: {
      name: "Silo B · Mutation+Dock",
      description: "SST-14 baseline에서 BLOSUM + LLM 변이 → HIL gates",
      stages: [
        { id: "01",  name: "Receptor",     group: "input",  tool: "PyRosetta · OpenFold3",   env: "bio-tools",     inN: 1,  outN: 1,   inUnit: "PDB",        outUnit: "sanitized",  status: "done",    time: "0:23" },
        { id: "CC",  name: "Constraint",   group: "input",  tool: "FWKT freeze · C3–C14 SS", env: "—",             inN: 1,  outN: 1,   inUnit: "config",     outUnit: "design space 4M", status: "done", time: "0:02" },
        { id: "03b", name: "Mutation",     group: "gen",    tool: "BLOSUM62 + LLM (qwen3-32b) · ga_bo", env: "vllm-server", inN: 1, outN: 240, inUnit: "SST-14 WT", outUnit: "mutants", status: "done", time: "5:48",  gpu: "H100×1" },
        { id: "DV",  name: "Diversity",    group: "filter", tool: "DuplicateFilter Hamming ≥ 2", env: "—",         inN: 240, outN: 80, inUnit: "mutants",    outUnit: "unique",     status: "done",    time: "0:08" },
        { id: "04",  name: "QC",           group: "filter", tool: "ESMFold + SS-bond",       env: "esmfold",       inN: 80, outN: 73,  inUnit: "seq",        outUnit: "pass",       status: "done",    time: "3:21",  gpu: "H100×1", gate: "pLDDT ≥ 60", pass: 73, fail: 7 },
        { id: "05",  name: "Docking",      group: "score",  tool: "DiffDock + Boltz-2",      env: "boltz",         inN: 73, outN: 16,  inUnit: "seq",        outUnit: "top 20%",    status: "done",    time: "12:08", gpu: "H100×4", gate: "Top 20%", pass: 16, fail: 57 },
        { id: "05b", name: "Selectivity",  group: "score",  tool: "Boltz-2 × 4 off-target",  env: "boltz",         inN: 16, outN: 8,   inUnit: "pose × 4",   outUnit: "margin pass",status: "done",    time: "8:42",  gpu: "H100×4", gate: "margin ≤ −10", pass: 8, fail: 8 },
        { id: "05c", name: "Boltz cross",  group: "score",  tool: "Boltz-2 + AF MSA",        env: "boltz",         inN: 8,  outN: null,inUnit: "pose × 5",   outUnit: "iPTM matrix",status: "running", time: "6:48",  gpu: "H100×4", gate: "iPTM margin ≥ 0", progress: 0.78 },
        { id: "06",  name: "Rosetta refine",group: "refine",tool: "FastRelax + FlexPepDock + ddG", env: "bio-tools", inN: null, outN: null, inUnit: "pose", outUnit: "refined.pdb", status: "queued", time: "—",     gpu: "CPU",    gate: "ddG ≤ −1.0" },
        { id: "07",  name: "Cluster",      group: "analyze",tool: "FoldMason lDDT ≥ 0.6",    env: "bio-tools",     status: "queued",  time: "—" },
        { id: "08",  name: "Stability",    group: "analyze",tool: "PepADMET + Boman + NEP",  env: "pepadmet",      status: "queued",  time: "—",     gate: "t½ ≥ 50h" },
      ],
    },
    // Combined view: two parallel generation tracks → shared scoring & refine
    Combined: {
      name: "Dual Silo · A + B",
      description: "병렬 generation → 통합 scoring · refine · analysis",
      tracks: [
        {
          silo: "A", label: "de novo",
          stages: [
            { id: "02", name: "Backbone",  group: "gen", tool: "RFdiffusion",  status: "done", time: "4:12", outN: 10, outUnit: "bb" },
            { id: "03", name: "Sequence",  group: "gen", tool: "ProteinMPNN",  status: "done", time: "1:48", outN: 80, outUnit: "seq" },
          ],
        },
        {
          silo: "B", label: "mutation",
          stages: [
            { id: "CC",  name: "Constraint", group: "input", tool: "FWKT freeze", status: "done", time: "0:02" },
            { id: "03b", name: "Mutation",   group: "gen",   tool: "BLOSUM62 + LLM ga_bo", status: "done", time: "5:48", outN: 240, outUnit: "mut" },
            { id: "DV",  name: "Diversity",  group: "filter",tool: "Dedupe H≥2",  status: "done", time: "0:08", outN: 80,  outUnit: "uniq" },
          ],
        },
      ],
      // Shared receptor input upstream
      input: { id: "01", name: "Receptor", tool: "PyRosetta · OpenFold3", status: "done", time: "0:23" },
      // Converge — shared downstream
      converge: [
        { id: "04",  name: "QC",            group: "filter", tool: "ESMFold + SS-bond",     status: "done",    time: "3:21",  inN: 160, outN: 146, gate: "pLDDT ≥ 60" },
        { id: "05",  name: "Docking",       group: "score",  tool: "DiffDock + Boltz-2",    status: "done",    time: "12:08", inN: 146, outN: 32,  gate: "Top 20%" },
        { id: "05b", name: "Selectivity",   group: "score",  tool: "Boltz-2 × 4",           status: "done",    time: "8:42",  inN: 32,  outN: 16,  gate: "margin ≤ −10" },
        { id: "05c", name: "Boltz cross",   group: "score",  tool: "Boltz-2 + AF MSA",      status: "running", time: "8:01",  inN: 16,  outN: null, gate: "iPTM margin ≥ 0", progress: 0.7 },
        { id: "06",  name: "Rosetta refine",group: "refine", tool: "FastRelax + FlexPepDock + ddG", status: "queued", gate: "ddG ≤ −1.0" },
        { id: "07",  name: "Cluster",       group: "analyze",tool: "FoldMason",             status: "queued" },
        { id: "08",  name: "Stability",     group: "analyze",tool: "PepADMET",              status: "queued", gate: "t½ ≥ 50h" },
      ],
    },
  },
  // Gates with current run pass/fail counts
  gates: [
    { id: "G1", name: "pLDDT (mean)", threshold: "≥ 60", step: "04", pass: 73, fail: 7 },
    { id: "G1b", name: "pLDDT (interface)", threshold: "≥ 45", step: "04", pass: 68, fail: 12 },
    { id: "G1c", name: "Disulfide SG-SG", threshold: "≤ 2.5 Å", step: "04", pass: 78, fail: 2 },
    { id: "G2", name: "Docking top%", threshold: "≥ top 20%", step: "05", pass: 16, fail: 52 },
    { id: "G2b", name: "DiffDock confidence", threshold: "≤ −1.0", step: "05", pass: 14, fail: 2 },
    { id: "G3", name: "Selectivity margin", threshold: "≤ −10 kcal/mol", step: "05b", pass: 8, fail: 6 },
    { id: "G3b", name: "Boltz iPTM margin", threshold: "≥ 0 (T2+)", step: "05c", pass: 1, fail: 7 },
    { id: "G4", name: "Rosetta ddG", threshold: "≤ −1.0 kcal/mol", step: "06", pass: 1, fail: 0 },
    { id: "G4b", name: "Rosetta clash", threshold: "≤ 10", step: "06", pass: 1, fail: 0 },
    { id: "G5", name: "Stability prescreen", threshold: "t½ ≥ 50h", step: "08", pass: 1, fail: 0 },
  ],
  // 5-agent reasoning sample
  agents: [
    { id: "planner", name: "Planner", role: "실험 설계", color: "violet" },
    { id: "builder", name: "Builder", role: "코드 실행", color: "blue" },
    { id: "qcranker", name: "QCRanker", role: "Gate 평가 + 랭킹", color: "cyan" },
    { id: "diversity", name: "DiversityManager", role: "foldmason 클러스터링", color: "teal" },
    { id: "critic", name: "Critic", role: "실패 진단 + 게이트 조정", color: "amber" },
    { id: "reporter", name: "Reporter", role: "요약 + 결정 기록", color: "stone" },
  ],
  // Live agent log
  agentLog: [
    { t: "14:30:12", agent: "planner", text: "iter02 변이 전략 결정: pos2 G→I/V/L 친수성 변이 확장, FWKT 보존 강제" },
    { t: "14:30:14", agent: "builder", text: "step02_backbone 실행 — RFdiffusion N=10, GPU 0,1" },
    { t: "14:33:48", agent: "builder", text: "step03_sequence 완료 — ProteinMPNN 80 sequences (8/backbone)" },
    { t: "14:35:21", agent: "qcranker", text: "Gate G1 (pLDDT ≥ 60): 73/80 pass (91%)" },
    { t: "14:35:22", agent: "critic", text: "G1 fail 7건 — 모두 disulfide SG-SG > 3 Å. step03 fallback 추천" },
    { t: "14:39:55", agent: "builder", text: "step05_docking 시작 — Boltz-2 batch, SSTR2 holo (7XNA)" },
    { t: "14:52:03", agent: "qcranker", text: "Gate G2 (top 20%): 16/68 pass" },
    { t: "14:52:18", agent: "diversity", text: "foldmason 클러스터링: 16 후보 → 4 cluster (lDDT ≥ 0.6)" },
    { t: "14:53:01", agent: "builder", text: "step05b_selectivity 실행 — off-target Boltz × 4 receptor" },
    { t: "15:08:44", agent: "qcranker", text: "selectivity_margin 평가 완료 — 1개 T2, 4개 T1, 11개 T0" },
    { t: "15:08:45", agent: "critic", text: "T2 후보 cand03 (AICKNFFWKTFTSC) — 유일 SSTR2-selective. Wetlab Ki 발주 권장" },
    { t: "15:09:02", agent: "reporter", text: "iter02 요약 작성 중… cand03 → /docs/wetlab/cand03_binding_assay_design.md" },
  ],
  // Current run metadata
  run: {
    id: "local_20260512_1430_iter02",
    started: "2026-05-12 14:30:12 KST",
    duration: "00:39:18",
    iteration: 2,
    maxIter: 5,
    silo: "B",
    llmModel: "qwen3-32b",
    gpus: "H100 NVL × 4",
    seed: 42,
    currentStep: "05c",
    progress: 0.78,
  },
};
