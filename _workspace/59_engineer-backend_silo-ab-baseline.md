# 듀얼 파이프라인 베이스라인 — Silo A + Silo B 상태 점검

> 생성: 2026-05-27  
> 작성: engineer-backend  
> 요청: orchestrator Phase 0~5 사전 베이스라인

---

## 1. Silo A 상태 (NIM 잔재 / 로컬 마이그레이션 진행률)

### 1.1 디렉토리 구조

```
pipelines/
  silo_a/src/
    arms.py          — 3-Arm 실행자 (Arm1SmallMol, Arm2FlexPep, Arm3DeNovo)
    clients.py       — Protocol 포트 정의 + NimClientBundle 팩토리
    orchestrator.py  — SiloAOrchestrator (to_unified() 포함)
    scoring.py       — UnifiedScorer
    config.py / models.py

AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/
  AG_src/
    clients/nim_client.py          — NIM REST 클라이언트 (4종 + Registry)
    pipeline/orchestrator.py       — 8-step 오케스트레이터 (Planner→Reporter)
    pipeline/step01~step08.py      — 개별 스텝 구현체
    tools/api/                     — 8종 NIM Tool Wrapper 구현
```

### 1.2 NIM API 잔재 현황

| 위치 | NIM 의존성 | 로컬 전환 상태 |
|------|-----------|---------------|
| `pipelines/silo_a/src/clients.py` | `NimClientBundle` 팩토리가 `bionemo.*_client` import | Protocol(Port) 인터페이스 분리 완료 — 로컬 구현체만 주입하면 NIM 없이 동작 가능 |
| `AG_src/clients/nim_client.py` | REST 직접 호출 (health.api.nvidia.com) | dry-run 모드 내장 (API_KEY 없으면 mock 반환). 로컬 래퍼 미생성 |
| `AG_src/tools/api/*.py` | NIM Tool Wrapper 8종 구현 | 클라우드 엔드포인트 고정. `local_client.py` 전환 예정이나 **미착수** |
| `AG_src/pipeline/step02~05.py` | RFdiffusion/ProteinMPNN/ESMFold/DiffDock NIM 호출 | 코드 완료, UI 미연결. NIM 키 없을 시 step 실행 불가 |

### 1.3 local_models/ 로드 가능 상태

| 모델 | 경로 | 체크포인트 | 로드 가능 여부 |
|------|------|-----------|--------------|
| RFdiffusion | `local_models/RFdiffusion/models/` | `Base_ckpt.pt`, `Complex_base_ckpt.pt` 등 7종 존재 | 설치 완료(setup.py), **Silo A 연결 미작성** |
| DiffPepBuilder | `local_models/DiffPepBuilder/model/` | Python 모듈(embedding.py 등) 존재, 가중치 별도 확인 필요 | 코드만 존재, ckpt 미확인 |
| pepadmet | `local_models/pepadmet/repo/model/` | `toxicity_early_stop.pth` 존재 | pepadmet_runner.py 연결 완료 (Silo B) |
| GenMol | `local_models/genmol/model_v2.ckpt` | 1.3GB 체크포인트 존재 | 연결 미확인 |
| LLM | `local_models/llm/` | DeepSeek-R1-32B, GLM-Z1-32B, Qwen3.5-122B, 27B | runner.py에서 vLLM 통해 사용 중 |
| ESMFold/ProteinMPNN | NIM API 전용 | 로컬 weights 없음 | **로컬 전환 미착수** |

### 1.4 Silo A 마이그레이션 진행률 요약

- **Protocol 인터페이스 분리**: 완료 (`MolMIMPort`, `DiffDockPort` 등 — `clients.py`)
- **NIM 연결 코드 제거**: 미완 — `create_nim_bundle()`이 `bionemo` import 시도
- **로컬 구현체 주입**: 미착수 — `local_client.py` 파일 자체 없음
- **UI 연결**: 미완 — `TODO_NIM_FULL_PIPELINE.md` Phase 1.2 전부 체크 해제 상태

---

## 2. Silo B 상태 (PyRosetta+Boltz+FlexPep)

### 2.1 진입점 및 파이프라인 플로우

```
pyrosetta_flow/runner.py (메인 진입점)
  → adapter.py (mutant 생성: guided / random)
  → AG_src/scripts/flexpep_dock.py (MutateResidue + FlexPepDock)
  → ranking.py (ddG 기반 랭킹)
  → convergence.py (patience early stop)
  → bayesian_optimizer.py (BoTorch GP — 옵션)
  → gnina_rescoring.py (GNINA 재채점 — 옵션)
  → pareto_ranking.py (NSGA-II — 옵션)
  → pepadmet_runner.py (toxicity — 옵션)
```

`AG_src/pipeline/orchestrator.py` (8-step 전체 파이프라인, UI 미연결):
- Step01: 수용체 PDB 준비
- Step02: RFdiffusion backbone 생성
- Step03: ProteinMPNN 서열 설계
- Step03b: BLOSUM 변이 폴백
- Step04: ESMFold QC (pLDDT + disulfide gate)
- Step05: DiffDock/Boltz-2 도킹
- Step05b: SSTR1/3/4/5 off-target 선택성 스크리닝
- Step06: Rosetta FlexPepDock 정밀화
- Step07: 분석 + PyMOL 렌더링
- Step08: 안정성 예측

### 2.2 FWKT pharmacophore 보존 현황

`AG_src/pipeline/step04_qc.py`에서 disulfide gate 구현 확인:
- `check_disulfide_bond()` — SG 원자간 거리 계산 (max_distance 기본 2.5 Å)
- `disulfide_cys_positions` config에서 [3, 14] (Cys3-Cys14) 지정
- Gate 실패 시 해당 후보 `passed_gate=False` 처리

`AG_src/pipeline/structure_validation.py`에서 추가 검증:
- `validate_disulfide_bonds()` — CB-SG-SG-CB chi3 dihedral + 거리 복합 체크
- SSTR2 프로젝트 기본 pair: Cys3-Cys14 명시 주석

FWKT(Phe6-Trp7-Lys8-Thr9) pharmacophore 보존:
- `AG_src/tests/test_design_alignment.py` — design alignment 테스트 존재
- `AG_src/llm/prompts.py` — Planner 프롬프트에서 FWKT 보존 강제 명시
- Step04 QC에서 직접 시퀀스 motif 체크는 없음 — prompts.py 레벨에서 soft constraint

### 2.3 최근 runs 실행 결과

`runs/pyrosetta_flow/test_full_pipeline_20260402/` (3 iter, 24개 후보):
- iter01: 8개, 성공 8개 (best: `AGCKWFFWKTFTSC`, ddG=-39.06)
- iter02: 8개, 성공 7개, 실패 1개 (`AVCKGFFWKTFTSW` — 5중변이 clash pre-refine score 1751), best: `IGCKNFFWKTFTST` ddG=-45.62
- iter03: 8개, 성공 8개 (best: `AECVNHFWKTFTSC` ddG=-40.81)

선택성 평가(step05b): off-target PDB 파일 (`ot_SSTR1_9IK8.pdb`, `ot_SSTR3_8XIR.pdb`, `ot_SSTR4_7XMT.pdb`, `ot_SSTR5_8ZBJ.pdb`) — `sst14_agentic_mutdock/` 디렉토리에 존재, git status에서 수정됨(M) 상태

`runs_local/` (로컬 실행):
- `dual_test_01/local_20260331_0930_iter01/silo_b/` 1회 완료

---

## 3. Silo A ↔ Silo B 인계 스키마

### 3.1 공유 스키마: UnifiedCandidate

`pipelines/shared/models.py`에 정의:
```python
@dataclass(frozen=True)
class UnifiedCandidate:
    id: str
    silo: Silo            # "silo_a" | "silo_b"
    modality: Modality    # "small_mol" | "peptide_variant" | "de_novo" | "sst14_mutant"
    structure: str        # SMILES 또는 아미노산 시퀀스
    raw_scores: Dict[str, float]
    bridge_metrics: Dict[str, float]   # 교차비교용 공통 메트릭
    confidence: float
    provenance: Dict[str, Any]
    metadata: Dict[str, Any]
```

### 3.2 변환 경로

- **Silo A → UnifiedCandidate**: `SiloAOrchestrator.to_unified()` (`orchestrator.py:106`)
- **Silo B → UnifiedCandidate**: `SiloBOrchestrator.to_unified()` (`silo_b/src/orchestrator.py:241`)
- **통합 집계**: `pipelines/orchestration/aggregator.py` (cross-silo ranking 포함)
- **정책 결정**: `pipelines/orchestration/policy.py`
- **상태 머신**: `pipelines/orchestration/state_machine.py`

### 3.3 인계 경계 명확성 평가

- **스키마 정의**: 완료 (UnifiedCandidate + CrossSiloManifest)
- **변환 메서드**: 양쪽 모두 구현 완료
- **실제 연동 실행**: 미확인 — `runs_local/dual_test_01`에서 `silo_b/` 디렉토리만 확인됨
- **bridge_metrics 채우기**: Silo A는 ADMET/toxicity 스코어 예정이나 로컬 모델 미연결로 빈 dict 가능성 높음

---

## 4. SS bond / pharmacophore 가드 위치

| 가드 유형 | 파일 | 함수 | 위치 레벨 |
|----------|------|------|---------|
| Disulfide 거리 체크 (Cys3-Cys14, ≤2.5 Å) | `AG_src/pipeline/step04_qc.py` | `check_disulfide_bond()` | Step04 (ESMFold QC 직후) |
| Disulfide 기하 검증 (dihedral chi3) | `AG_src/pipeline/structure_validation.py` | `validate_disulfide_bonds()` | 독립 CLI + Step 내 호출 |
| Disulfide 게이트 필터 | `AG_src/pipeline/step04_qc.py` | `predict_and_evaluate()` | gate `passed_gate` 플래그 |
| FWKT soft constraint | `AG_src/llm/prompts.py` | Planner 프롬프트 텍스트 | LLM 설계 단계 (hard gate 없음) |
| SS bond + MW 계산 테스트 | `AG_src/tests/test_ss_bond_and_mw.py` | pytest 회귀 | 테스트 레벨 |
| pharmacology lookup guard | `pipeline_local/scripts/pharmacology_guards.py` | `LITERATURE_VALUES` | Stage 5 환각 차단 |
| Blosum 변이 시 Cys 고정 | `pipeline_local/strategies/blosum.py` | 내부 constraint | Silo B 변이 생성 단계 |

**주의**: FWKT pharmacophore에 대한 hard gate는 존재하지 않음. Planner LLM 프롬프트 수준의 soft constraint만 존재. 향후 Step03 or Step04에 시퀀스 motif 검증 함수 추가 필요.

---

## 5. 최근 산출 후보(PRST-001~004) 추적

### 5.1 후보 정의 위치

`backend/routers/wetlab.py`의 `PRST_CANDIDATES` 하드코딩:

| 후보 ID | 시퀀스 | 예측 ddG | Tier | Selectivity | 출처 |
|--------|--------|---------|------|-------------|------|
| PRST-001 | AGCKNIIWKTITSC | -10.5 | S | 250.0 | wetlab.py 하드코딩 |
| PRST-002 | AGCKNFIWKTITSC | -6.8 | B | 180.0 | wetlab.py 하드코딩 |
| PRST-003 | AGCRNFIWKTITSC | -4.2 | B | 130.0 | wetlab.py 하드코딩 |
| PRST-004 | AICKNFIWKTITSC | -5.0 | B | 200.0 | wetlab.py 하드코딩 |

**야생형 대비 변이 위치**:
- PRST-001: pos6(F→I), pos7(F→I), pos10(F→I), pos11(T→T): SST-14(AGCKNFFWKTFTSC)에서 pos6,7,10 변이
- PRST-002: pos7(F→I), pos10(F→I): 2중 변이
- PRST-003: pos4(K→R), pos7(F→I), pos10(F→I): 3중 변이
- PRST-004: pos2(G→I), pos7(F→I), pos10(F→I): 3중 변이

### 5.2 pepADMET 독성 스코어 (2026-05-21 재학습 모델)

`_workspace/pepadmet_local/pepADMET/model/sanity_check_v3_result.json`:
- SST-14 (야생형): 0.402
- PRST-001: 0.402 (SST-14 동일)
- PRST-002: 0.268 (개선)
- PRST-003: 0.485 (악화)
- PRST-004: 0.402 (SST-14 동일)
- 판정: PASS (임계값 미명시)

### 5.3 Silo B 실행 산출물과 PRST ID 연결

현재 `runs/pyrosetta_flow/` 산출물의 후보 ID는 `iter0X_candYYY` 형식이며, PRST-001~004 ID로의 명시적 매핑 파일이 없음. `wetlab.py`의 PRST 시퀀스는 Silo B runs와 **별도로 수동 하드코딩**된 상태.

---

## 핵심 리스크 요약

### Silo A 핵심 리스크

NIM API → 로컬 전환이 `local_client.py` 파일 자체가 없는 상태로 미착수이며, `bionemo` 패키지 없는 환경에서 `create_nim_bundle()` 호출 시 ImportError가 발생하여 SiloAOrchestrator 초기화 자체가 불가능함. Protocol 인터페이스 분리는 완료되어 있으나 로컬 구현체 주입 코드가 전무하여 Silo A 전체가 사실상 가동 불가 상태.

### Silo B 핵심 리스크

Silo B에서 산출된 후보(iter0X_candYYY)와 습식실험 큐(PRST-001~004) 간 연결이 wetlab.py의 하드코딩으로만 존재하며 자동 추적 파이프라인이 없음. 또한 FWKT pharmacophore(Phe6-Trp7-Lys8-Thr9) 보존 검증에 hard gate가 없어 5중 변이 후보(`AVCKGFFWKTFTSW`)가 게이트 통과 없이 FlexPepDock에 진입하여 pre-refinement score 1751 clash 오류를 유발한 사례가 iter02에서 확인됨.
