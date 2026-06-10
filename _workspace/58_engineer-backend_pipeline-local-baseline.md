# pipeline_local 베이스라인 점검 보고서
생성: 2026-05-27  
작성: engineer-backend

---

## 1. 모듈 책임 매트릭스

### Step 01~08 요약

| Step | 파일 | LOC | 책임 | 입력 | 출력 |
|------|------|-----|------|------|------|
| step01 | steps/step01_receptor.py | 536 | SSTR2 수용체 PDB 준비 + 결합포켓 정의 | FASTA / 기존 PDB | Step01Output (receptor_pdb_path, pocket_residues, chain_id, pocket_json_path) |
| step02 | steps/step02_backbone.py | 329 | RFdiffusion de novo 백본 설계 | Step01Output + config | Step02Output (backbone_pdbs, design_params, n_generated) |
| step03 | steps/step03_sequence.py | 389 | ProteinMPNN 역폴딩 → 시퀀스 생성 | Step02Output + config | Step03Output (sequences: List[SequenceEntry]) |
| step03b | steps/step03b_blosum_mutation.py | 41 | BLOSUM62 기반 변이 생성 (Silo B 진입점) | ref 서열 + config | Step03bOutput (variants: List[VariantEntry]) |
| step04 | steps/step04_qc.py | 675 | ESMFold pLDDT QC 게이트 | List[SequenceEntry] | Step04Output (qc_results: List[QCResult]) |
| step05 | steps/step05_docking.py | 537 | Boltz-2 도킹 + 상위 K% 선별 | qc_passed + receptor_pdb | Step05Output (docking_results) |
| step05b | steps/step05b_selectivity.py | 484 | PyRosetta FlexPepDock off-target 선택성 | Step05Output | Step05bOutput (selectivity_results) |
| step05c | steps/step05c_boltz_cross.py | 737 | Boltz-2 iPTM 기반 교차 검증 (SSTR1~5) | Step05Output + receptors | Step05cOutput (results, passed_candidates) |
| step06 | steps/step06_rosetta.py | 915 | PyRosetta FastRelax+FlexPepDock 정밀 정제 + ddG | top_docking + receptor_pdb | Step06Output (rosetta_results) |
| step07 | steps/step07_analysis.py | 625 | FoldMason 구조 정렬 + PyMOL 렌더링 + lDDT | Step06Output | Step07Output (lddt, interface, images, rank_table) |
| step08 | steps/step08_stability.py | 636 | 반감기 휴리스틱 랭킹 + modification 제안 | 서열 + modifications | List[StabilityResult] (io_schemas 미통합) |

### scoring/ 모듈

| 파일 | LOC | 책임 |
|------|-----|------|
| scoring/composite_scorer.py | 547 | Hard Cutoff + WSS + NSGA-II Pareto → Tier S/A/B/FAIL 분류 (proxy, scripts/에서 구현 위임) |
| scoring/layer1_ensemble.py | 261 | L-AA 혈중 반감기 Layer 1 앙상블 (PlifePred + HLE + pepADMET) |
| scoring/layer2_ensemble.py | 159 | pepMSND-local GAT 반감기 Layer 2 |
| scoring/radiolysis_scorer.py | 117 | 방사성 분해 민감 잔기 계수 |
| scoring/ensemble_router.py | 83 | Layer 1/2/3 라우팅 결정 |

### strategies/ 모듈

| 파일 | LOC | 책임 |
|------|-----|------|
| strategies/blosum.py | 501 | BLOSUM62 기반 치환 전략 |
| strategies/proteinmpnn.py | 600 | ProteinMPNN 역폴딩 전략 |
| strategies/esm_scan.py | 307 | ESM-2 로그-우도 스캐닝 |
| strategies/dual_b1_b2.py | 91 | Dual Silo A+B 통합 전략 |
| strategies/base.py | 25 | AbstractStrategy 인터페이스 |
| strategies/registry.py | 24 | 전략 등록/조회 레지스트리 |

### core/ 모듈

| 파일 | LOC | 책임 |
|------|-----|------|
| core/local_runner.py | 363 | LocalModelRunner — ESMFold/RFdiffusion/ProteinMPNN/Boltz 로컬 subprocess 래퍼 |
| core/selectivity_runner.py | 451 | FlexPepDock off-target 선택성 실행 (PyRosetta conda subprocess) |
| core/config_loader.py | 110 | YAML 설정 로드 + 병합 |
| core/structure_io.py | 89 | PDB/CIF 포맷 감지 + 읽기 |

### orchestrator.py

| 파일 | LOC | 메서드 수 | 책임 |
|------|-----|-----------|------|
| orchestrator.py | 2,479 | 47개 | LocalPipelineOrchestrator — Silo A/B 분기, Step01~07 순차 실행, agent 호출, 수렴 판단, 상태 기록 |

---

## 2. 리팩토링 후보 Top 5

### R1. `orchestrator.py` — 2,479 LOC God-class (최우선)

**우선순위**: Critical  
**근거**: 단일 파일에 47개 메서드, Step 실행 + Agent 호출 + 상태 기록 + 수렴 판단 + 체크포인트 + UI emitter + Silo A/B 분기 로직이 혼재. `_run_silo_a`, `_run_silo_b`, `_run_docking`, `_run_rosetta`, `_run_selectivity_chain`, `_finalize_rosetta_results` 등 150+ LOC 메서드가 다수.  
**영향 범위**: 전체 파이프라인 실행 경로 (모든 테스트 간접 의존)  
**권장 분리안**:
- `SiloARunner` / `SiloBRunner` — Silo 분기 로직 분리
- `AgentBroker` — `_invoke_agent` + `_adapt_agent_context` + `_map_agent_result` + `_invoke_agent_stub` 분리
- `StatusEmitterMixin` — `_write_status`, `_add_timeline`, `_capture_agent_message` 분리

---

### R2. `scripts/composite_scorer.py` (1,118 LOC) ↔ `scoring/composite_scorer.py` (547 LOC) 중복 구현

**우선순위**: High  
**근거**: 동일한 `CompositeScorer`, `ScoringInput`, `ScoringResult` 개념이 두 위치에 존재. `scoring/composite_scorer.py`는 `scripts/composite_scorer.py`에서 `enrich_candidates_from_wrappers`를 런타임 import하는 역방향 의존이 발생 (L101~105). 이는 순환 의존 위험 및 테스트에서 두 파일을 각각 import하는 혼용 상태.  
**영향 범위**: `test_composite_scorer.py`(scoring), `test_composite_scorer_fallback_warn.py`(scripts), `test_p1_sprint_wrapper_integration.py`(scripts) — 서로 다른 모듈 테스트  
**권장 조치**: `scripts/composite_scorer.py`를 CLI entry point 전용으로 축소하고 핵심 로직을 `scoring/composite_scorer.py`로 일원화

---

### R3. `step06_rosetta.py` — PyRosetta stub 잔재 (mock 금지 정책 위반)

**우선순위**: High  
**근거**: `a5f44c7` 커밋 (2026-05-18) "mock 금지 정책" 이후에도 `_stub_rosetta_result()` 함수가 존재하며 PyRosetta 미설치 시 `ddg=0.0`, `clash_score=0.0` 플레이스홀더를 조용히 반환 (L733~743). `compute_binding_ddg()`도 실패 시 `0.0` 반환. 이는 Hard Cutoff 기준(ddG ≤ -95.024 REU)을 우회하는 무음 통과(silent passthrough)로 스크리닝 무결성 위협.  
**영향 범위**: Step06 → composite_scorer Hard Cutoff 게이트 전체  
**권장 조치**: stub 반환 대신 `PyRosettaUnavailableError` 예외 발생으로 변경, 실패 시 명시적 SKIP 처리

---

### R4. `step08_stability.py` — io_schemas 미통합 (독립 dataclass)

**우선순위**: Medium  
**근거**: `StabilityResult` dataclass가 `steps/step08_stability.py` 내에 직접 정의되어 `schemas/io_schemas.py`에 없음. 반면 step01~07은 모두 `io_schemas.Step0NOutput` 통일. orchestrator에서도 `step08_stability`를 `pipeline_local.steps`가 아닌 `AG_src.pipeline`에서 import하여 로컬 마이그레이션 미완료 상태. `Step08Output` 스키마 부재로 JSON 직렬화 인터페이스 불일치.  
**영향 범위**: step08 → 반감기 Layer 앙상블 → composite_scorer 입력 체인  
**권장 조치**: `Step08Output(step08_results: List[StabilityResult])` io_schemas 등록 + orchestrator import 로컬화

---

### R5. `scripts/flexpepdock_worker.py` (1,140 LOC) — 단일 파일 과부하

**우선순위**: Medium  
**근거**: FlexPepDock worker pool 관리(PID 파일, orphan cleanup), 작업 큐, 진행 상태 추적, subprocess 실행, 결과 파싱이 1,140 LOC 단일 파일에 집중. `test_flexpepdock_worker_pool.py`(483 LOC), `test_flexpepdock_worker_progress.py`(366 LOC), `test_orphan_worker_cleanup.py`(217 LOC) 세 개 별도 테스트가 이를 단편적으로 커버.  
**영향 범위**: Silo B 전체 FlexPepDock 실행 경로  
**권장 조치**: `WorkerPool`, `JobQueue`, `ProgressTracker`, `SubprocessRunner` 클래스로 분리

---

## 3. 스키마 불일치 / 통합 위험

| 위험 | 위치 | 상세 |
|------|------|------|
| Step08 스키마 누락 | step08_stability.py | `StabilityResult`가 io_schemas 외부 정의 → JSON 직렬화 인터페이스 없음 |
| orchestrator → step08 AG_src fallback | orchestrator.py L959 | `from AG_src.pipeline.step08_stability import predict_half_life` — 로컬 마이그레이션 미완료 |
| Step05cOutput.passed_candidates 타입 혼용 | io_schemas.py L456 | `passed_candidates: List[BoltzSelectivityResult]` 필드명이 Step05bOutput의 `passed_candidates()` 메서드와 동명이형 (one is field, other is method) → 호출 코드에서 혼동 가능 |
| scoring/ vs scripts/ composite_scorer 역방향 의존 | scoring/composite_scorer.py L101 | scoring이 scripts를 런타임 import — 패키지 계층 역전 |
| `_run_silo_b` dict/dataclass 이중 파싱 | orchestrator.py L1554-1567 | FlowArtifacts 후보가 `dict` 또는 `dataclass` 두 타입으로 올 수 있어 getattr/get 이중 분기 필요 — 상위 FlowArtifacts 타입 고정 필요 |

---

## 4. Hot-spot (최근 7일, 2026-05-20 ~ 2026-05-27)

| 파일 | 변경 내역 | 관련 커밋 |
|------|---------|---------|
| `pepadmet_ood/ood_detection.py` (신규, 316 LOC) | Mahalanobis + MC Dropout OOD 검출 신설 | f72c48e |
| `scripts/predict_admet_pepadmet.py` (+203 LOC) | `_try_load_local_gnn()`, `predict_local_gnn_toxicity()` 추가, smiles 파라미터 확장 | f72c48e |
| `scoring/layer1_ensemble.py` | HLE regression callable wrapper 추가 (R² 0.879 가중치) | f36a7f9 |
| `tests/test_layer1_ensemble.py` | 테스트 138라인 추가 | f36a7f9 |
| `tests/test_ood_detection.py` (신규, 248 LOC) | OOD 검출 10개 pytest (torch 의존, 현재 수집 오류) | f72c48e |
| `scripts/pharmacology_guards.py` | 사이클릭 OOD 가드 항목 추가 | f6d4990 |
| `tests/test_pharmacology_guards.py` | 회귀 테스트 43라인 추가 | f6d4990, f36a7f9 |

**핵심 활동**: 3-Layer Ensemble 보강 (Layer 1 HLE 추가) + PepADMET OOD 검출 통합이 주요 변경. pharmacology_guards.py가 2회 수정으로 가장 빈도 높음.

---

## 5. 테스트 커버리지 Gap

### 커버된 영역 (733 tests, 703 test functions)

| 영역 | 테스트 파일 | 규모 |
|------|-----------|------|
| composite_scorer (scoring/) | test_composite_scorer.py | 550 LOC |
| composite_scorer (scripts/) | test_composite_scorer_fallback_warn.py | 270 LOC |
| pharmacology_guards | test_pharmacology_guards.py | 668 LOC |
| step05b selectivity | test_step05b_selectivity.py | 650 LOC |
| step05c Boltz cross | test_step05c_boltz_cross.py | 734 LOC |
| stability_predictor (scripts) | test_stability_predictor.py + backend | 1,935 LOC |
| layer1 ensemble | test_layer1_ensemble.py | — |
| FlexPepDock worker pool | test_flexpepdock_worker_pool/progress/orphan | 3개 파일 |
| orchestrator | antipatterns, refactor_helpers, reference_peptide | 3개 파일 |

### 미커버 / 부분 커버 Gap

| 영역 | 현황 | 위험도 |
|------|------|--------|
| **step01_receptor.py** | 전용 테스트 없음 (test_tier3_reference_complex_fix.py에서 일부 경로만 커버) | High |
| **step02_backbone.py** | 전용 테스트 없음 (RFdiffusion subprocess mock 없음) | High |
| **step03_sequence.py** (ProteinMPNN) | 전용 테스트 없음; strategies/proteinmpnn.py 테스트는 있음 | Medium |
| **step06_rosetta.py** | test_tier1_rosetta_fixes.py 있으나 stub 경로만 (실제 PyRosetta subprocess 미커버) | High |
| **step07_analysis.py** | test_step07_foldmason_n_check.py가 n<2 edge case만 커버; FoldMason/PyMOL 실제 경로 미커버 | Medium |
| **step08_stability.py** | test_stability_predictor.py가 scripts/stability_predictor/를 커버하나 steps/step08 직접 테스트 없음 | Medium |
| **Layer 2 ensemble** (layer2_ensemble.py) | 전용 테스트 없음 | Medium |
| **Layer 3 ADMET-AI** | test_layer3_admet_ai.py 있으나 외삽 가드만 59 LOC | Low |
| **test_ood_detection.py** | `torch` 미설치 환경에서 collect 오류 (ModuleNotFoundError) — CI 차단 위험 | Critical |
| **orchestrator run_single_iteration 통합** | antipatterns 테스트 1개 함수뿐; 분기별 통합 시나리오 없음 | High |

### test_ood_detection.py CI 즉시 조치 필요
```
ERROR: ModuleNotFoundError: No module named 'torch'
pipeline_local/tests/test_ood_detection.py:16: in <module>
    import torch
```
`pytest.importorskip("torch")` 또는 `@pytest.mark.skipif(not torch_available)` 가드 누락. 현재 CI 환경에서 733 tests를 수집하지 못하고 오류로 종료됨.

---

## 요약 (300자)

**Top 3 리팩토링 후보**:  
1) `orchestrator.py` 2,479 LOC God-class — Silo A/B 분기·Agent 브로커·Status emitter를 각각 독립 클래스로 분리 필요 (전체 파이프라인 영향).  
2) `scripts/composite_scorer.py`(1,118 LOC) ↔ `scoring/composite_scorer.py`(547 LOC) 역방향 런타임 import 중복 — 패키지 계층 역전으로 테스트 3개 파일이 다른 모듈 참조 혼용.  
3) `step06_rosetta.py` stub fallback `ddg=0.0` 무음 반환 — mock 금지 정책(`a5f44c7`) 이후 잔재로 Hard Cutoff 게이트를 우회하는 스크리닝 무결성 위협. 예외 발생으로 즉시 교체 필요.  
추가 즉시 조치: `test_ood_detection.py` torch skip 가드 미적용으로 CI collect 오류 발생 중.
