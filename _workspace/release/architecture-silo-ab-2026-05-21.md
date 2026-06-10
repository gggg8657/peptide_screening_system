# PRST_N_FM 전체 아키텍처 — Silo A vs Silo B (2026-05-21 시점)

> **작성**: team-lead (orchestrator), 2026-05-21 D-7 to 5월 28일 회의
> **목적**: 듀얼 파이프라인 (Silo A 3-Arm NIM / Silo B PyRosetta) 의 구현·미구현 명확화
> **선행**: 어제 EOD (`eod-2026-05-20-orchestrator-session.md`) + STATUS_2026-05-20.md + 다른 세션 EOD 3건

---

## 0. 한 줄 정의

- **Silo A** = LLM-driven Agentic Pipeline (NIM 또는 vLLM Qwen). 외부망 deploy.
- **Silo B** = PyRosetta 직접 mutation + dock. 로컬망 (H100 NVL ×4).
- **공통 인프라** = composite_scorer + pharmacology_guards + 5 receptor PDB + FE Manual UI.

---

## 1. Silo A — Agentic LLM Pipeline (외부망)

### 1.1 Flow Chart

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Silo A — Agentic LLM-driven (외부망 deploy)                              │
└─────────────────────────────────────────────────────────────────────────┘

         User Request
              │
              ▼
   ┌──────────────────────┐
   │ FE: SiloAPage        │ (frontend/src/pages/SiloAPage.tsx)
   └──────────────────────┘
              │ POST /api/v1/silo-a/run
              ▼
   ┌──────────────────────┐
   │ BE: silo_a.py        │ (backend/routers/silo_a.py)
   │ - /run               │
   │ - /status/<job>      │
   │ - /results/<job>     │
   │ - /health            │
   └──────────────────────┘
              │
              ▼
   ┌──────────────────────────────────────────────────────┐
   │ AG_src/pipeline/orchestrator.py                       │
   │ PipelineOrchestrator                                  │
   │                                                       │
   │   ┌────────────┐  ┌────────────┐  ┌────────────┐    │
   │   │ planner    │→ │ builder    │→ │ qc_ranker  │    │
   │   │ (LLM)      │  │ (code)     │  │ (code)     │    │
   │   └────────────┘  └────────────┘  └────────────┘    │
   │         │              │                │            │
   │         ▼              ▼                ▼            │
   │   ┌──────────────────────────────────────────┐      │
   │   │ diversity_manager → critic (LLM) →       │      │
   │   │ reporter (LLM)                            │      │
   │   └──────────────────────────────────────────┘      │
   │                                                       │
   │   LLM provider: vLLM Qwen3.5-35B-A3B (PR #80)        │
   │                 또는 ollama qwen3:8b (fallback)       │
   └──────────────────────────────────────────────────────┘
              │
              ▼
   ┌──────────────────────────────────────────────────────┐
   │ AG_src/pipeline/step01-08                             │
   │ step01_receptor  → step02_backbone                    │
   │ → step03_sequence → step04_qc → step05_docking        │
   │ → step05b_selectivity → step06_rosetta                │
   │ → step07_analysis → step08_stability                  │
   └──────────────────────────────────────────────────────┘
              │
              ▼
       Final Candidates → JSON results
```

### 1.2 Silo A Data Flow

```
[Input]                  [Process]                    [Output]
─────────────────        ─────────────────            ───────────
SST-14 reference  ──→ planner (LLM)         ──→ mutation plan
AGCKNFFWKTFTSC         │
                       ▼
                    builder (code)          ──→ candidate sequences
                       │
                       ▼
                    qc_ranker (code)        ──→ filtered candidates
                       │
                       ▼ (LLM-guided)
                    critic (LLM)            ──→ rejected feedback
                       │                        ┌──── loop back ←─┐
                       ▼                        ▼                 │
                    docking (Boltz-2 or NIM) → DockingResult ──→ reporter
                       │                                          │
                       ▼                                          │
                  step06_rosetta (FlexPepDock if enabled) ────────┘
                       │
                       ▼
                  step08_stability → final JSON
```

### 1.3 Silo A 구현 상태

| 컴포넌트 | 파일 | 상태 | 비고 |
|---|---|---|---|
| BE router | `backend/routers/silo_a.py` | ✅ 구현 | run/status/results/health 4 endpoints |
| Orchestrator | `AG_src/pipeline/orchestrator.py` | ✅ 구현 | M3 agent override (PR #80 commit `0ef301d`) |
| LLM provider | `AG_src/llm/provider.py` | ✅ 구현 | vLLM Qwen3.5-35B-A3B (PR #80, open) |
| agents (5종) | `AG_src/agents/*.py` | ✅ 구현 | planner/builder/qc_ranker/critic/reporter/diversity_manager |
| steps (8종) | `AG_src/pipeline/step*.py` | ✅ 구현 | step01~step08 + step05b selectivity |
| FE Silo A | `frontend/src/pages/SiloAPage.tsx` | ✅ 구현 | run/status/results 표시 |
| LLM 비교실험 | `AG_src/tests/test_llm_benchmark.py` | ✅ 구현 (PR #80 M4) | thinking on/off A/B |
| NIM API | (외부 NVIDIA NIM) | 🟡 dry-run 모드 | API key 없으면 fallback (silo_a.py:65-73) |

---

## 2. Silo B — PyRosetta Direct Mutation + Dock (로컬망)

### 2.1 Flow Chart

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Silo B — PyRosetta Direct (로컬 H100 NVL ×4)                             │
└─────────────────────────────────────────────────────────────────────────┘

         User Request
              │
              ▼
   ┌──────────────────────────────┐
   │ FE: StrategyRunnerPage       │ (PR #66)
   │ FE: ManualSelectivityPage    │ (PR #43, #66 통합)
   │ FE: BindingPocketPage        │ (PR #66 cherry-pick)
   └──────────────────────────────┘
              │
              ├─── POST /api/strategies/run ──→ Mutation 전략 선택
              ├─── POST /api/selectivity/run ──→ Selectivity 도킹
              └─── POST /api/flexpepdock/jobs ──→ FlexPepDock 큐
              ▼
   ┌──────────────────────────────────────────────────────┐
   │ BE: strategies.py + selectivity.py + flexpepdock.py  │
   └──────────────────────────────────────────────────────┘
              │
              ▼
   ┌──────────────────────────────────────────────────────┐
   │ Mutation 전략 (PR #54~#59)                            │
   │                                                       │
   │   blosum (default 평가만)                             │
   │   esm_scan (서열 컨텍스트)                            │
   │   proteinmpnn (구조 인식)                             │
   │   dual_b1_b2 (proteinmpnn ∪ esm_scan) ← default      │
   └──────────────────────────────────────────────────────┘
              │
              ▼
   ┌──────────────────────────────────────────────────────┐
   │ Docking Worker Pool (PR #95, worker-1 + worker-2)     │
   │                                                       │
   │   pipeline_local/scripts/flexpepdock_worker.py        │
   │   → 큐에서 job 받아 flexpep_dock.py 호출              │
   │   → per-receptor 6h timeout (PR #94)                  │
   │   → orphan worker auto-cleanup (PR #96)               │
   │   → nstruct sub-progress (PR #98)                     │
   └──────────────────────────────────────────────────────┘
              │
              ▼
   ┌──────────────────────────────────────────────────────┐
   │ flexpep_dock.py (PyRosetta direct)                    │
   │                                                       │
   │   build_peptide_pose_from_sequence                    │
   │   → FlexPepDockingProtocol.apply                      │
   │   → InterfaceAnalyzerMover.get_interface_dG           │
   │   → aggregate_scores (PR #109: silent fallback 제거)  │
   └──────────────────────────────────────────────────────┘
              │
              ▼
   ┌──────────────────────────────────────────────────────┐
   │ pyrosetta_flow/runner.py                              │
   │ run_pyrosetta_agentic_mutdock_flow (Bandit/BO 통합)   │
   │                                                       │
   │   bandit.py (탐험)                                    │
   │   bayesian_optimizer.py (BO)                          │
   │   pareto_ranking.py (다목적)                          │
   │   convergence.py (조기 종료)                          │
   └──────────────────────────────────────────────────────┘
              │
              ▼
       Top-K Candidates → JSON
```

### 2.2 Silo B Data Flow

```
[Input]                  [Process]                    [Output]
─────────────────        ─────────────────            ───────────
SST-14 (or seed)  ──→ mutation strategy (4종)    ──→ variant sequences
                       │                                ↓
                       │                          AGCKNIIWKTITSC ...
                       │
                       ▼
                  Boltz-2 SSTR2-SST14 complex ──→ complex.pdb (PR #67)
                  (iPTM 0.953, PR #91)             ↓
                                                ProteinMPNN receptor_context
                       │
                       ▼
                  FlexPepDock × N receptors (5)  ──→ {receptor: dG, interface_score}
                       │                              ┌─ dG_kcal_mol
                       │                              ├─ pdb_paths
                       │                              └─ stub:False
                       │
                       ▼
                  offtarget_dock.py             ──→ selectivity_matrix
                  (SSTR1/3/4/5)                     (SSTR4 sig fix PR #72)
                       │
                       ▼
                  ranking.py + pareto_ranking   ──→ Top-K + Pareto front
                       │
                       ▼
                  composite_scorer.py           ──→ Tier S/A/B/FAIL
                  (PR #62, enrich PR #68)         (Hard Cutoff 5게이트)
                       │
                       ▼
                  select_final_candidates       ──→ PRST-001~004
                  (A-09)                          ↓
                                            synthesis_orders/PRST-00[1-4].md
                                            (PR #86, 옵션 B OOD 명시)
```

### 2.3 Silo B 구현 상태

| 컴포넌트 | 파일 | 상태 | 비고 |
|---|---|---|---|
| Entry | `pyrosetta_flow/runner.py::run_pyrosetta_agentic_mutdock_flow` | ✅ 구현 | CLI 위주, BE 라우터 없음 |
| Notebook flow | `pyrosetta_flow/runner.py::run_pyrosetta_notebook_flow` | ✅ 구현 | 별도 변형 |
| Mutation BLOSUM | `AG_src/strategies/blosum*` (Phase 1) | ✅ 구현 (PR #54) | 평가만 사용 |
| Mutation ESM-Scan | `AG_src/strategies/esm_scan*` (Phase 2) | ✅ 구현 (PR #55) | |
| Mutation ProteinMPNN | `AG_src/strategies/proteinmpnn*` (Phase 3) | ✅ 구현 (PR #56) | |
| Mutation DualB1B2 | `AG_src/strategies/dual_b1_b2*` (Phase 4) | ✅ 구현 (PR #57), default (PR #59) | proteinmpnn ∪ esm_scan |
| A/B 실험 | `pipeline_local/scripts/strategy_ab_experiment.py` | ✅ 구현 (PR #58) | |
| BE Strategy Runner | `backend/routers/strategies.py` | ✅ 구현 (PR #66) | 7 endpoints |
| BE Selectivity | `backend/routers/selectivity.py` | ✅ 구현 | upload/run/jobs/status/results |
| BE FlexPepDock | `backend/routers/flexpepdock.py` | ✅ 구현 | 큐+워커+ETA |
| BE Binding Pocket | `backend/routers/binding_pocket.py` | ✅ 구현 (PR #66 cherry) | CRUD + extract |
| FE ManualSelectivity | `frontend/src/pages/ManualSelectivityPage.tsx` | ✅ 구현 (PR #43) | |
| FE StrategyRunner | `frontend/src/pages/StrategyRunnerPage.tsx` | ✅ 구현 (PR #66) | mode/complex/variant 선택 |
| FE BindingPocket | `frontend/src/pages/BindingPocketPage.tsx` | ✅ 구현 (PR #66 cherry) | |
| Boltz complex | `runs_local/cand03_variants/boltz_dock/` (PR #67) | ✅ 구현 | iPTM 0.953, SSTR2-SST14 |
| Worker pool | `pipeline_local/scripts/flexpepdock_worker.py` | ✅ 구현 (PR #95 2개 동시) | per-receptor 6h timeout (PR #94) |
| Worker orphan cleanup | (PR #96) | ✅ 구현 | startup hook + PID file GC |
| Sub-progress | (PR #98) | ✅ 구현 | nstruct 단위 세분화 |
| Stub badge FE | (PR #99) | ✅ 구현 | Job 리스트 + Section4 badge |
| 대형 잡 경고 배너 | (PR #97) | ✅ 구현 | 대형 잡 사전 경고 |
| Silent fallback fix | (PR #109, **방금**) | ✅ 구현 | aggregate_scores 빈 ddg → RuntimeError |
| SSTR4 시그니처 fix | (PR #72) | ✅ 구현 | VILRYAKMKTA 중복 제거 |
| Selectivity 재산정 | (PR #81) | ✅ 구현 | PRST-001~004 변동 없음 검증 |
| G-2 margin convention | (PR #82) | ✅ 구현 | 양수=좋음 SSOT |
| G-2 qc_ranker Gate4 | (PR #82 squash 포함) | ✅ 구현 | 방향 반전 fix |
| candidate_id format | (PR #71) | ✅ 구현 | iter*_cand* keys |
| Symlink restore | (PR #69) | ✅ 구현 | broken helloworld → real receptors |
| Silent estimation guard | (PR #70) | ✅ 구현 | SST_DATA_DIR env |

---

## 3. 공통 인프라 (Silo A + Silo B 공유)

### 3.1 Data Flow (전체)

```
┌────────────────────────────────────────────────────────────────────────┐
│ 공통 인프라 — pharmacology_guards / composite_scorer / 5 receptor PDB  │
└────────────────────────────────────────────────────────────────────────┘

[Receptor DB]
data/somatostatin_receptor/
  ├─ SSTR1_9IK8.cif/pdb  (1.8MB)
  ├─ SSTR2_7XNA.cif/pdb  (508KB)
  ├─ SSTR3_8XIR.cif/pdb  (939KB)
  ├─ SSTR4_7XMT.cif/pdb  (988KB)
  └─ SSTR5_8ZBJ.cif/pdb  (880KB)
       │
       │ (Silo A or Silo B 가 docking 호출)
       ▼
[Scoring Pipeline]
pipeline_local/scoring/
  ├─ composite_scorer.py   ← A-04 (PR #62)
  │   ├─ Hard Cutoff 5게이트 (ΔG/selectivity/radiolysis/admet/instability)
  │   ├─ WSS 계산
  │   ├─ Pareto front
  │   └─ Tier 분류 S/A/B/FAIL
  │
  ├─ radiolysis_scorer.py
  │   └─ Cys·Met=3, Phe·Tyr·Trp=2, Pro·His·Leu=1 (PR #62)
  │
  ├─ layer1_ensemble.py    ← PR #85 OPEN (3-Layer Ensemble)
  │   └─ L-AA: PlifePred + HLE regression + pepADMET HBM
  │
  ├─ layer2_ensemble.py    ← PR #85 OPEN
  │   └─ D-AA/cyclic: pepMSND-local (격리 env)
  │
  └─ ensemble_router.py    ← PR #85 OPEN
      └─ route_halflife_prediction(seq, has_dota)
       │
       ▼
[Pharmacology Guards (Stage 5)]
pipeline_local/scripts/pharmacology_guards.py
  ├─ ENDPOINT_CONFIDENCE (PR #74 += webmetabase + HLE)
  │   ├─ halflife_pepmsnd (P1)
  │   ├─ halflife_webmetabase_indirect (P3, D-AA)
  │   ├─ halflife_hle_regression_albumin (P3, lipidation)
  │   ├─ admet_pepadmet (P1, but D-AA OOD)
  │   └─ ...
  ├─ LITERATURE_VALUES
  │   ├─ SST14_SSTR2_ref_ddg_flexpep (553.857, σ=4.024, PR #79)
  │   └─ SST14_SSTR2_ref_ddg_boltz2 (-95.024, PR #79)
  ├─ HEURISTIC_FUNCTION_DISCLAIMERS
  └─ check_*_applicability (D-AA/cyclic/DOTA 가드, PR #108)
       │
       ▼
[Final Output]
runs_local/final_candidates/
  ├─ all_candidates.csv
  ├─ hard_cutoff_pass.csv
  ├─ summary.json
  ├─ tier_s_candidates.csv  ← PRST-001 (AGCKNIIWKTITSC, WSS=1.000)
  ├─ tier_a_candidates.csv
  ├─ tier_b_candidates.csv  ← PRST-002/003/004
  └─ synthesis_orders/
      ├─ PRST-001.md  (ADMET 1.00 OOD, PR #86)
      ├─ PRST-002.md
      ├─ PRST-003.md  (K4→R, N-말단 DOTA 협의 필요)
      └─ PRST-004.md
```

### 3.2 공통 인프라 구현 상태

| 컴포넌트 | 파일 | 상태 |
|---|---|---|
| composite_scorer | `pipeline_local/scoring/composite_scorer.py` | ✅ (PR #62 + PR #68 wrapper × enrichment + PR #108 fallback WARN) |
| radiolysis_scorer | `pipeline_local/scoring/radiolysis_scorer.py` | ✅ |
| pharmacology_guards | `pipeline_local/scripts/pharmacology_guards.py` | ✅ (PR #74 +2 endpoint, PR #79 SST14 ref, PR #108 cyclic SS OOD) |
| **layer1_ensemble** | `pipeline_local/scoring/layer1_ensemble.py` | 🟡 **PR #85 OPEN** (다른 세션 작성) |
| **layer2_ensemble** | `pipeline_local/scoring/layer2_ensemble.py` | 🟡 **PR #85 OPEN** (격리 env 필요) |
| **ensemble_router** | `pipeline_local/scoring/ensemble_router.py` | 🟡 **PR #85 OPEN** |
| flexpep_dock | `pipeline_local/scripts/flexpep_dock.py` | ✅ (PR #109 silent fallback 제거) |
| flexpepdock_worker | `pipeline_local/scripts/flexpepdock_worker.py` | ✅ (PR #95/#96/#98) |
| offtarget_dock | `pipeline_local/scripts/offtarget_dock.py` | ✅ (PR #72 SSTR4 fix) |
| predict_halflife_pepmsnd | `pipeline_local/scripts/predict_halflife_pepmsnd.py` | ✅ (PR #74) |
| predict_admet_pepadmet | `pipeline_local/scripts/predict_admet_pepadmet.py` | ✅ (PR #74) |
| sequence_to_smiles | `pipeline_local/scripts/sequence_to_smiles*.py` | ✅ |
| Local steps 1-8 | `pipeline_local/steps/step01~08.py` | ✅ (step03b BLOSUM = PR #54) |

---

## 4. FE — 5 페이지 (라우트별)

| 페이지 | Route | Silo | 상태 |
|---|---|---|---|
| SiloAPage | `/silo-a` | A | ✅ (LLM-driven run/status) |
| SiloBPage | `/silo-b` | B | ✅ (pyrosetta_flow runner UI) |
| ManualSelectivityPage | `/manual-selectivity` | B | ✅ (PR #43 + PR #66 통합) |
| StrategyRunnerPage | `/strategy-runner` | B | ✅ (PR #66) |
| BindingPocketPage | `/binding-pocket` | 공통 | ✅ (PR #66 cherry-pick) |
| SelectivityExplorerPage | `/selectivity-explorer` | B | ✅ (PR #83) |
| RunConsolePage | `/run-console` | 공통 | ✅ |
| Other (Benchmark, About, Combined, Cand, RunLauncher, Settings, Wetlab) | various | 공통 | ✅ |

---

## 5. 🔴 미구현 / 부분 구현 / 검증 미흡

### 5.1 미구현

| 항목 | 위치 | 비고 |
|---|---|---|
| `select_final_candidates.py` | `pipeline_local/scoring/` (A-09) | **미구현** — 자동화 안 됨. 어제 PRST-001~004 는 수동 작성 |
| `synthesis_checker.py` | `pipeline_local/scoring/` (A-09) | **미구현** — 비천연 AA 조달 가능성 자동 체크 부재 |
| `generate_synthesis_request.py` | `pipeline_local/scoring/` (A-09) | **미구현** — 7개 필수 항목 의뢰서 자동 생성 부재 |
| Silo A ↔ Silo B 교차 검증 자동화 | 없음 | 수동 비교만 가능 |
| `pepMSND-local` 학습된 weights | `_workspace/pepmsnd_local/checkpoints/` | **학습 진행 중** (cursor-agent 어제 07:23 시작, **D-AA 0.6% 희소 한계**) |
| `pepADMET` 25 endpoint local | (저자에게 weights 요청) | 4-task only public, **나머지 25 endpoint local 불가** |
| DOTA 결합 후보 ADMET 예측 도구 | 없음 | wet-lab 필수 |

### 5.2 부분 구현 (제한 있음)

| 항목 | 위치 | 제한 |
|---|---|---|
| **layer1_ensemble + layer2_ensemble** | PR #85 (open) | **main 미머지**. 검토 필요 |
| pepADMET D-AA 처리 | wrapper 등록됨 (PR #74) | OOD 외삽 (PR #108 cyclic SS guard) — 신뢰도 LOW |
| Silo A NIM API 호출 | `silo_a.py:65-73` | API key 없으면 dry-run fallback (실 NIM 호출 X) |
| Silo B Bayesian Optimizer | `pyrosetta_flow/bayesian_optimizer.py` | 코드 존재, 실 운영 검증 미비 |
| Silo B Bandit 탐색 | `pyrosetta_flow/bandit.py` | 동일 |
| Boltz-2 docking | `runs_local/cand03_variants/boltz_dock/` | PRST-001 단일 운영, 4 후보 모두 적용 미완 |
| FlexPepDock 도킹 결과 신뢰도 | 어제 9 done 잡 | 어제까지 silent fallback (0.0) 잠재 — **PR #109 머지 후 audit 필요** |

### 5.3 검증 미흡 / wet-lab 의존

| 항목 | 자동화 가능성 |
|---|---|
| V-A09-01 PRST-001 F6→I 치환 Ki 실측 | NO (wet-lab) |
| V-A09-03 pepADMET selectivity × 실측 Ki | NO (wet-lab) |
| V-A09-05 half-life ranking wet-lab | NO (wet-lab) |
| V-A09-06 Boltz2 ΔG × 실험 IC50 상관 | NO (wet-lab) |
| V-04 pepADMET 29 endpoint 로컬화 | 저자 weights 요청 또는 자체 학습 |
| V-05 pepADMET CC BY-NC-SA KAERI 적용 | 사용자 결정 (저자 메일 발송 안 함) |
| SSTR4 시그니처 fix 후 selectivity 영향 | ✅ PR #81 검증 (변동 없음) |
| Silent fallback (PR #109) 적용 후 9 done 잡 audit | 미완 — 본 세션 후속 |

---

## 6. 데이터 의존성 (Critical Path)

```
Receptor PDB (5종) ──┬─→ FlexPepDock (Silo B) ──→ ΔG, interface_score
                    │
                    ├─→ Boltz-2 (Silo A or B) ──→ complex.pdb, iPTM
                    │
                    └─→ ProteinMPNN (Silo B) ──→ variant sequences

SST-14 reference ──┬─→ Mutation strategies (4종) ──→ candidates
                   │
                   └─→ A-05 SSOT (PR #79) ──→ gate_thresholds rosetta_ddg_max=498.4713

Candidates ──┬─→ composite_scorer ──→ Tier S/A/B/FAIL
            │
            ├─→ pharmacology_guards ──→ ENDPOINT_CONFIDENCE check
            │
            └─→ selectivity matrix ──→ Hard Cutoff 5게이트 (PR #82 양수=좋음)
            │
            ▼
        synthesis_orders/PRST-00[1-4].md (PR #86, 옵션 B OOD 명시)
            │
            ▼
        Gate-2 wet-lab 발주 (사용자 직접 액션)
```

---

## 7. 5월 28일 회의 (D-7) 발표 매트릭스 권고

| Tier | 내용 | 발표 비중 |
|---|---|---|
| **완료** (✅) | A-01/A-04/A-05/A-09/A-10 + Silo A/B 양쪽 핵심 머지 + 의뢰서 4건 | 40% |
| **진행 중** (🟡) | 3-Layer Ensemble PR #85 + pepMSND 자체 학습 (D-AA 0.6% 한계) | 25% |
| **이월·신규** | A-09 자동화 모듈 3건 미구현 + Silo A↔B 교차 자동화 | 15% |
| **OOD/제한** | PRST 4 후보 ADMET=1.00 OOD 외삽 + wet-lab 의존 V-A09 4건 | 15% |
| **요청 사항** | KAERI 법무 검토 (GPL-3.0/CC BY-NC-SA) + DGX 견적 | 5% |

---

## 8. 본 문서 작성 후 즉시 후속 권고

1. **PR #85 (3-Layer Ensemble) 검증 + 머지** — Silo B 핵심 합류
2. **9 done jobs audit** — silent fallback (PR #109 fix) 적용 전 결과 신뢰도 점검
3. **A-09 미구현 3 모듈 신설** — select_final_candidates.py / synthesis_checker.py / generate_synthesis_request.py (Gate-2 재현성)
4. **Silo A NIM API 실 호출 검증** — dry-run fallback 외 실 NIM 동작 한 번 확인
5. **5월 28일 회의 PPTX 18 슬라이드 (PR #91) 갱신** — 본 문서 §5 미구현 항목 반영

---

*최초 작성: 2026-05-21 by team-lead (orchestrator)*
