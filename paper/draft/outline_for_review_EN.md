# Paper Direction Review Request

**Title (Draft)**: Multi-Agent AI Co-Scientist System for SSTR2-Targeted Radiopharmaceutical Candidate Discovery

**Target**: KNS (Korean Nuclear Society) 2026 Spring Conference  
**Deadline**: 2026-02-26  
**Author**: Dongju Kim, Korea Atomic Energy Research Institute (KAERI)

---

## 1. Core Thesis (One Sentence)

> **A multi-agent AI system can automate the entire SSTR2 radiopharmaceutical candidate discovery workflow, and role-differentiated agent collaboration offers superior quality and scalability over monolithic pipelines.**

---

## 2. Motivation & Background

### Why This Research

- SSTR2-targeted radiopharmaceuticals (e.g., ^177Lu-DOTATATE) face limitations: poor tumor penetration, off-target binding to SSTR1/3/4/5
- Discovering novel candidates requires **broad chemical space exploration + manual coordination of multiple computational tools** → expensive and slow
- AI tools (RFdiffusion, DiffDock, ESMFold, etc.) are individually mature, but **no integrated automated pipeline exists**

### Why Multi-Agent

- No single AI model can cover the full pipeline: structure prediction → docking → energy evaluation → selectivity screening
- **Role-specialized agents** handle each stage, with self-improvement loops for iterative optimization
- The development process itself leveraged multi-agent AI collaboration (Cursor + Codex CLI + Claude Code) → "agents building agents"

---

## 3. Proposed System Overview

### 3.1 Dual-Silo Pipeline

```
Silo A: 3-Arm Virtual Screening          Silo B: Constraint-Based Mutation
┌──────────────────────────┐             ┌─────────────────────────┐
│ Arm 1: Small Mol (MolMIM)│             │ SST-14 Template          │
│ Arm 2: Peptide Variants   │             │ → Constraint Compiler    │
│ Arm 3: De Novo            │             │ → MutantGenerator        │
│   (RFdiff→MPNN→ESMFold)  │             │ → 3-Gate HIL Filter      │
└───────────┬──────────────┘             └───────────┬─────────────┘
            └──────────┬─────────────────────────────┘
                       ▼
              Unified Ranking → Top Candidates → Wet Lab
```

### 3.2 6-Agent Hybrid Architecture (Key Contribution 1)

| Agent | Role | LLM/Code | Rationale |
|-------|------|:--------:|-----------|
| Planner | Experiment planning, hypothesis generation | **LLM** | Scientific reasoning required |
| Builder | Execute 7-step pipeline | Code | API calls, deterministic |
| QC&Ranker | 4-stage quality gates | Code | Numerical comparison |
| DiversityMgr | Structure clustering | Code | Sequence similarity |
| Critic | Failure analysis, improvement proposals | **LLM** | Root cause reasoning required |
| Reporter | Report generation | **LLM** | Natural language synthesis |

→ 3 LLM + 3 Code = **50% reduction in LLM calls**, separation of concerns maintained

### 3.3 Competing Hypotheses Pattern (Key Contribution 2)

To ensure objectivity in architecture decisions, **4 AI agents competitively analyzed** the codebase:

- Advocate-6Agent (pro 6-agent)
- Advocate-Hybrid (pro 4-agent)
- LLM-Evaluator (model assessment)
- Devil's Advocate (attacks weaknesses)

→ **3:1 consensus for 6-Agent Hybrid**; Devil's Advocate discovered the most critical bug (P0)

### 3.4 Multi-MCP Development Methodology (Key Contribution 3)

```
Cursor IDE (Primary Orchestrator)
├── Codex CLI (Critical code audit)
└── Claude Code (Autonomous reasoning, architecture validation)
```

→ 3 AI agents analyzed the **same codebase from different perspectives**  
→ Discovered 3 critical (P0) + 3 major (P1) defects

---

## 4. Key Results

### 4.1 Defects Discovered via Agent Collaboration

| Severity | Description | Discovered By |
|:--------:|-------------|:-------------:|
| **P0** | `_invoke_agent()` stub — 6 agents never actually invoked | Devil's Advocate |
| **P0** | LLM output injected into config without validation (security) | LLM-Evaluator |
| **P0** | Step05b selectivity screening not implemented | Advocate-6Agent |
| P1 | Convergence initial value bug | Codex CLI |
| P1 | StopIteration crash | Claude Code |
| P1 | Parameter whitelist not enforced | Cursor |

### 4.2 Pipeline Execution Results

- **Silo A**: 40 small molecules + 13 peptides + 16 de novo → 20 unified-ranked candidates
- **Silo B**: All 33 unit tests passed
- **LLM calls**: 6 → 3 per iteration (**50% reduction**)

---

## 5. Differentiation from Prior Work

| Aspect | Prior Work | This Work |
|--------|-----------|-----------|
| Agent role assignment | Unclear or all-LLM | **Quantitative LLM necessity scoring** |
| Architecture decision | Developer judgment | **AI agent competing hypotheses** |
| Development methodology | Single tool | **Multi-MCP (3 AI agents)** |
| Application domain | General SW / general drug | **Radiopharmaceuticals (SSTR2)** |

---

## 6. Limitations & Future Work

- **No wet-lab validation**: Actual binding affinity of generated candidates unconfirmed → SPR experiments needed
- **LLM hallucination risk**: 7B model performing Critic role may hallucinate
- **NIM API dependency**: NVIDIA NIM API failure halts entire pipeline
- **GLP-1 stability**: Blood stability prediction module (6–10 day half-life) not yet implemented

---

## 7. Questions for Review

1. **Paper direction**: Focus on the AI agent system itself (radiopharmaceuticals as application case) — is this direction appropriate?
2. **Conference fit**: Is this suitable for KNS Spring Conference as an AI/computational paper?
3. **Contribution priority**: Which of the three contributions should be emphasized?
   - (a) 6-Agent Hybrid architecture
   - (b) Competing Hypotheses validation
   - (c) Multi-MCP development methodology
4. **Wet-lab connection**: Feedback on experimental validation plan for candidate compounds
