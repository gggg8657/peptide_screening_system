# Pamphlet Content Spec — SSTR2 AI Co-Scientist Screening System

> **For the designer:** This is the approved, fact-checked content for the HTML product pamphlet.
> Each top-level section maps to one pamphlet **panel**. Headings, taglines, and body copy are
> ready to typeset. Technical claims have been verified against the live codebase — do not alter
> numbers, model names, or units. Tone: product-brochure (benefit-forward) but scientifically honest.
> Primary language is English here for layout flexibility; Korean equivalents are provided where the
> product UI ships in Korean.

---

## PANEL 1 — Cover: Product Name & Tagline

**Product name:**
**SSTR2 AI Co-Scientist** — Autonomous Radiopharmaceutical Peptide Screening Platform

**Tagline (pick one for the hero):**
- "From sequence to selective binder — an AI scientist that designs, docks, and decides."
- "Real physics. Real AI agents. Real candidates."
- "An autonomous loop that screens SST-14 mutants for SSTR2-selective radiopharmaceuticals."

**What is it / who is it for (one paragraph):**
The SSTR2 AI Co-Scientist is an autonomous, agent-driven discovery platform that screens mutants of
the native somatostatin peptide **SST-14 (AGCKNFFWKTFTSC, a 14-residue cyclic peptide with a
Cys3–Cys14 disulfide bond)** to find candidates that bind **somatostatin receptor subtype 2 (SSTR2)**
more tightly, last longer in circulation, and stay selective against the closely related off-targets
SSTR1/3/4/5. It combines local large-language-model "scientist" agents (Planner / Critic / Reporter)
with **real, physics-based PyRosetta FlexPepDock docking** in a closed self-improving loop, and presents
everything through a live web dashboard. It is built for **radiopharmaceutical and peptide-therapeutic
research teams** (e.g., SSTR2-targeted PRRT / DOTATATE-class agents) who want to compress the
early in-silico screening cycle without giving up scientific rigor or auditability.

---

## PANEL 2 — Key Features (the core of the brochure)

> Layout suggestion: a card grid, one card per feature. Each card has **Name / Benefit (what it does)
> / How it works (1–2 lines, smaller type)**.

### 1. Agentic AI Discovery Loop (Planner · Critic · Reporter)
- **Benefit:** The system runs like a tireless research scientist — it forms a hypothesis, runs the
  experiment, reads the results, and adjusts strategy on its own, iteration after iteration.
- **How it works:** Three LLM agents drive an N-iteration loop. The **Planner** sets each iteration's
  goal and objective mode (`auto` / `ddg_only` / `ddg_plus_constraints`); the **Scientist Critic**
  diagnoses failures and proposes up to 2 parameter changes per round (adaptive gating); the
  **Reporter** writes the iteration notebook, ranking, and PyMOL render scripts. All agents are
  served by a **local LLM (Qwen3-32B via vLLM, OpenAI-compatible)** — no external API dependency.

### 2. Real Physics-Based Docking (PyRosetta FlexPepDock ΔG)
- **Benefit:** Binding scores come from genuine all-atom molecular mechanics, not a guessed heuristic —
  so the candidates you trust are grounded in physics.
- **How it works:** Each candidate complex is refined with **PyRosetta FlexPepDock**, then the interface
  binding energy **ΔG** is computed with `InterfaceAnalyzerMover`
  (ΔG = E(complex) − E(receptor) − E(peptide), in kcal/mol / Rosetta Energy Units). A steric **clash
  score** (fa_rep) is reported alongside. Gate: ΔG ≤ −5.0 kcal/mol, clash ≤ 10.

### 3. Multi-Objective Screening (ΔG · Half-life · Selectivity · ADMET)
- **Benefit:** A drug candidate has to be good at many things at once. The platform optimizes all four
  objectives together instead of chasing binding affinity alone.
- **How it works:** A cost-tiered objective stack (`pyrosetta_flow/multiobjective.py`) combines binding
  **ΔG**, a sequence-derived **half-life** estimate, **SSTR2 selectivity margin**, and an **ADMET
  reasonableness** surrogate (built from Instability Index, GRAVY, Boman index, pI). Default objective
  weights: ΔG 40% · Selectivity 25% · Stability/half-life 20% · ADMET 15%.

### 4. SSTR2 Selectivity Off-Target Screening (SSTR1/3/4/5)
- **Benefit:** Selectivity is a safety feature. The platform proves a candidate prefers SSTR2 over its
  four sibling receptors, reducing the risk of off-target effects downstream.
- **How it works:** Top candidates are docked against curated single-chain **SSTR1, SSTR3, SSTR4, SSTR5**
  receptor structures (AlphaFold-derived, pre-aligned to the SSTR2 frame) with the same FlexPepDock +
  InterfaceAnalyzer pipeline. **selectivity_margin = ΔG(worst off-target) − ΔG(SSTR2)**; positive =
  more SSTR2-specific. Gate: margin ≥ 10 kcal/mol, and no individual off-target stronger than the
  allowed bound.

### 5. Bayesian Optimization + Thompson Sampling
- **Benefit:** The platform learns *where* to mutate, focusing experimental budget on the positions most
  likely to improve binding — smarter search, fewer wasted dockings.
- **How it works:** A **Thompson-sampling multi-armed bandit** keeps a Beta(α, β) belief per mutable
  position and samples focus positions each round (`bandit.py`). A complementary **Gaussian-Process
  Bayesian optimizer** (BoTorch qNEHVI multi-objective acquisition, ESM-2 or one-hot embeddings)
  suggests next mutations (`bayesian_optimizer.py`).

### 6. Multi-Trial Statistical Validation
- **Benefit:** Single docking runs are noisy; the platform re-runs winners across multiple seeds so you
  can trust that a top candidate is genuinely good, not lucky.
- **How it works:** Configurable **N-trial validation** (1 = off, 3 = quick, 5 = standard, 10 = paper
  standard) re-docks the finalists across seeds, reporting median / mean / **stdev** of ΔG with an
  **early-stop on low coefficient of variation (CV)**. The UI flags any sequence with only one
  measurement as "reproducibility unverified."

### 7. Disulfide-Bond Preservation (Cys3–Cys14)
- **Benefit:** The cyclic scaffold that makes SST-14 a drug is protected — candidates stay structurally
  valid peptides, not broken-open chains.
- **How it works:** The mutation engine treats the **Cys3 and Cys14** anchor positions as off-limits;
  only the surrounding positions are mutated, keeping the **Cys3–Cys14 disulfide** intact. Exposed in
  the UI as the **"Disulfide Constraint"** toggle.

### 8. Pharmacophore (FWKT) Constraints
- **Benefit:** The receptor-binding "business end" of the peptide is locked, so mutants keep their core
  SSTR2-recognition ability while you explore everything around it.
- **How it works:** The **FWKT pharmacophore (positions 7–10)** is held invariant. Every proposed
  mutant is checked with `_preserves_pharmacophore()`; violations trigger up to 3 retries before
  fallback (`PHARMACOPHORE_RETRY_LIMIT = 3`).

### 9. Pareto Ranking (NSGA-II)
- **Benefit:** Instead of collapsing everything into one biased score, the platform surfaces the true
  trade-off frontier — the candidates that are not beaten on every objective at once.
- **How it works:** **NSGA-II non-dominated sorting + crowding distance** (pymoo) ranks candidates over
  the objective set {ΔG, stability, druggability, diversity} under clash and hard-violation constraints
  (`pareto_ranking.py`), replacing legacy weighted-sum scoring.

### 10. Web Dashboard — Real-Time Mission Control
- **Benefit:** Watch the AI scientist work live, inspect every candidate in 3D, and start or stop
  experiments with a click — no command line required.
- **How it works:** A **React + Vite** dashboard talks to a **FastAPI** backend. It includes:
  - **Real-time monitoring** — agent timeline, loop progress, convergence graph, ΔG distribution.
  - **3D molecular viewer** — **Mol\*** (molstar 5.6.1) with 4 view modes (complex / cartoon /
    ball-and-stick / surface), plus PyMOL render gallery.
  - **Candidate table** — sortable, with ΔG, Total Score (REU), Clash, Final Score, reproducibility,
    and per-metric tooltips explaining gates and units.
  - **Experiment control** — set iterations, model, candidate count, objective mode, feature toggles;
    Start / Stop a run.

### 11. Pharmacology Guards (Anti-Hallucination)
- **Benefit:** AI can confidently make things up. A dedicated guard layer stops fabricated
  pharmacology numbers from ever reaching your results.
- **How it works:** A standalone declarative guard module (`pharmacology_guards.py`) enforces
  literature ground-truth values, scale ranges, and sign conventions; it labels heuristic functions
  honestly and tags API responses with a confidence grade. Backed by a regression test suite
  (39+ tests).

---

## PANEL 3 — How to Use (step-by-step)

> Layout suggestion: a numbered vertical "getting started" strip.

**Step 1 — Start the LLM server (Qwen3-32B on H100).**
```bash
./_launch_vllm.sh          # serves Qwen/Qwen3-32B as "qwen3-32b" on :8000 (OpenAI-compatible)
```

**Step 2 — Start the backend API (FastAPI, port 8787).**
```bash
conda activate bio-tools
uvicorn backend.main:app --host 0.0.0.0 --port 8787 --reload
# Swagger UI: http://localhost:8787/docs
```

**Step 3 — Start the frontend dashboard (Vite, port 5173).**
```bash
cd frontend && npm install && npm run dev
```

**Step 4 — Open the dashboard.**
Go to **http://localhost:5173** (the root path auto-redirects to the main **Silo B** screening view).

**Step 5 — Configure the run** in the **Experiment Control** panel:
- **Iterations (N)** — number of Planner–Critic loops.
- **LLM model / provider** — auto-detects vLLM (Qwen3-32B); Ollama fallback supported.
- **Candidates per iteration**, **objective mode** (Auto / ΔG Only / ΔG + Constraints).
- **Validation trials** — Off / 3 Quick / 5 Std / 10 Paper.
- **Feature toggles** — Disulfide Constraint, Bandit Guidance, Convergence Detection, ADMET Gate,
  Cross-Run Dedup, SAR Analysis.

**Step 6 — Click Start, then monitor live.**
Watch the agent timeline, loop progress bar, convergence graph, and ΔG distribution update in real time.

**Step 7 — Interpret the results.** In the Candidate Table, read each column:
- **ΔG (kcal/mol)** — binding energy; more negative = stronger binding (gate ≤ −5.0).
- **Clash (REU)** — steric clash; lower is better (amber > 5, red > 10; gate ≤ 10).
- **Total Score / Final Score** — Rosetta total energy and the composite ranking score.
- **Half-life / ADMET** — ranking surrogates (see validation note); higher = more favorable.
- **Selectivity margin** — SSTR2 vs. worst off-target; positive ≥ 10 = selective.
- **Reproducibility** — median ΔG and trial count from multi-trial validation.

**Step 8 — Review top candidates.** The Pareto-ranked finalists (and their 3D structures in the Mol\*
viewer) are your shortlist for downstream wet-lab evaluation.

---

## PANEL 4 — Architecture at a Glance

> Layout suggestion: a left-to-right flow diagram. Render the chain below as connected boxes.

```
[ Researcher ]
      │  configure & start run
      ▼
┌─────────────────────────┐        ┌──────────────────────────────┐
│  Web Dashboard          │  HTTP  │  Backend API (FastAPI :8787)  │
│  React + Vite (:5173)   │◄──────►│  experiment / status /        │
│  Mol* 3D · live charts  │  /api  │  selectivity / admet / ...    │
└─────────────────────────┘        └───────────────┬──────────────┘
                                                    │ drives
                                                    ▼
                              ┌─────────────────────────────────────┐
                              │  Agentic Loop (N iterations)         │
                              │  Planner → mutate → dock → ΔG →      │
                              │  Critic → Reporter   (+ Bandit / BO) │
                              └──────────┬───────────────┬──────────┘
                                         │ reasoning      │ physics
                                         ▼                ▼
                               ┌──────────────────┐  ┌──────────────────────┐
                               │ vLLM Qwen3-32B   │  │ PyRosetta FlexPepDock │
                               │ (Planner/Critic/ │  │ ΔG + off-target       │
                               │  Reporter)       │  │ SSTR1/3/4/5 docking   │
                               └──────────────────┘  └──────────────────────┘
                                                    │
                                                    ▼
                              ┌─────────────────────────────────────┐
                              │ Results: Pareto-ranked candidates,   │
                              │ JSON artifacts, PyMOL renders,       │
                              │ reproducibility stats → Dashboard    │
                              └─────────────────────────────────────┘
```

**In words:** The researcher configures and launches a run from the **dashboard**, which calls the
**FastAPI backend**. The backend drives the **agentic loop**: the **Planner** proposes mutations
(guided by the Thompson-sampling bandit and Bayesian optimizer), PyRosetta **docks** each candidate and
computes **ΔG**, the **Critic** analyzes outcomes and adjusts gates, and the **Reporter** records
everything. LLM reasoning runs on **vLLM-served Qwen3-32B**; physics runs on **PyRosetta**. Results —
Pareto-ranked candidates, 3D structures, and reproducibility statistics — stream back to the dashboard.

---

## PANEL 5 — Tech Specs

> Layout suggestion: a clean two-column spec table.

| Layer | Technology |
|-------|-----------|
| **LLM agents** | Qwen3-32B, served by **vLLM** (OpenAI-compatible API, port 8000); Ollama fallback (e.g. qwen3:8b, gemma3:1b) |
| **Docking / physics engine** | **PyRosetta** FlexPepDock + InterfaceAnalyzerMover (real all-atom ΔG) |
| **Structure prediction / QC** | **ESMFold** (pLDDT structure-quality gating) |
| **Optimization** | Thompson-sampling bandit; Bayesian optimization (BoTorch qNEHVI GP); NSGA-II Pareto (pymoo) |
| **Backend** | **FastAPI** + Uvicorn (port 8787), 20+ routers (experiment, status, selectivity, admet, flexpepdock, validation, …) |
| **Frontend** | **React 19 + TypeScript + Vite 7**, React Router 7, Mol\* (molstar 5.6.1), Tailwind-style UI |
| **3D visualization** | **Mol\*** viewer (4 modes) + PyMOL render gallery |
| **Hardware** | **4 × NVIDIA H100 NVL** GPUs (LLM serving on a dedicated H100; physics on CPU/GPU as available) |
| **Environment** | Python 3.12 (`bio-tools` conda env), Node.js 20+, PyRosetta licensed install |
| **Test coverage** | pyrosetta_flow pytest suite (118 tests, ~93% coverage); frontend Vitest (32 tests); pharmacology-guard regression (39+ tests) |

---

## PANEL 6 — Scientific Validation Note (the honesty panel)

> Layout suggestion: a calm, trust-building "How we keep it honest" panel. This is a differentiator,
> not fine print — give it real space.

**What is real, measured physics:**
- **Binding ΔG** is computed by **PyRosetta InterfaceAnalyzerMover** on FlexPepDock-refined complexes
  (kcal/mol / Rosetta Energy Units). These are genuine all-atom interface energies — though they are
  **relative scores, not absolute affinities (Ki/Kd)**.
- **Selectivity margins** come from **real off-target docking** of SSTR1/3/4/5 with the same engine.

**What is a labeled ranking surrogate (clearly disclosed):**
- **Half-life** and the **ADMET reasonableness score** are **sequence-derived ranking surrogates**, not
  clinical pharmacokinetic values. They are **not** validated by in-vitro serum-stability or
  permeability assays. They exist to **prioritize** candidates for downstream testing, and the codebase
  labels them as such (anti-hallucination disclaimer baked into `multiobjective.py`).

**What guards against fabrication:**
- A dedicated **pharmacology guard layer** enforces literature values, valid numeric ranges, and sign
  conventions, and tags every result with a **confidence grade** — so AI-generated numbers cannot
  silently masquerade as ground truth.

**Biological sanity check (it matches known biology):**
- Native **SST-14 is a pan-agonist** that binds all five somatostatin receptor subtypes — i.e., it is
  *not* SSTR2-selective. The platform's selectivity screen recovers exactly this: the unmodified SST-14
  reference shows little-to-no SSTR2 selectivity margin, confirming the pipeline measures real
  receptor-subtype discrimination rather than producing a flattering artifact. Candidates only earn a
  positive selectivity margin when mutations genuinely tilt binding toward SSTR2.

**Bottom line for the reader:** The platform accelerates *prioritization* with honest, physics-grounded
binding and selectivity numbers, while transparently flagging the heuristic estimates — designed to feed
a wet-lab decision, not to replace it.

---

## Designer Notes / Asset Suggestions

- **Brand motif:** a closed loop / cycle icon (the agentic iteration loop) is the strongest visual hook.
- **Color cue for metrics:** green = good (negative ΔG, positive selectivity), amber/red = gate
  warnings (clash > 5 / > 10) — mirror the dashboard's own semantics.
- **Hero imagery:** a Mol\* cartoon of the SST-14–SSTR2 complex, FWKT pharmacophore highlighted, with
  the Cys3–Cys14 disulfide drawn as a bond.
- **Korean UI:** the shipping dashboard uses Korean labels in places (e.g., panel help text); if the
  pamphlet is bilingual, mirror the panel names — Silo B = SST-14 돌연변이 시뮬레이션, PharmacologyPanel,
  VisualizationPanel.
- **Do not change:** model name (Qwen3-32B), ports (8000 / 8787 / 5173), GPU count (4 × H100 NVL),
  ΔG/selectivity gates, or the half-life/ADMET "surrogate" framing — these are load-bearing accuracy
  claims.
```
