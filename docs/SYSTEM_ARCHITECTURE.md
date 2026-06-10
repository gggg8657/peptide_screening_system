# PRST_N_FM 시스템 아키텍처

## 1. 시스템 목적 (3줄 요약)
- `SSTR2` 타겟( `P30874`)에 대한 `SST-14 (AGCKNFFWKTFTSC)` 기반 변이/대체 리간드 탐색을 자동화한다.  
- 고성능 후보 탐색은 `SILO A`(3-arm virtual screening)로 병렬 실행하고, 규제 가능한 품질 정련은 `SILO B`(HIL SST-14 mutant generation)로 수행한다.  
- 두 실험 라인은 `YAML config`-기반 오케스트레이션, `NVIDIA NIM API` 클라이언트 추상화, 가중치 기반 점수 정합을 공유한다.  

## 2. 전체 아키텍처(ASCII)
```text
                                    +-------------------------+
                                    | bionemo/                |
                                    | NVIDIABaseClient        |
                                    |                         |
                                    | MolMIMClient            |
                                    | DiffDockClient          |
                                    | RFdiffusionClient       |
                                    | ProteinMPNNClient       |
                                    | ESMFoldClient           |
                                    +------------+------------+
                                                 |
            +------------------------------------+-----------------------------------+
            |                                                                    |
            v                                                                    v
   +--------------------------+                                     +--------------------------+
   | pipelines/silo_a          |                                     | pipelines/silo_b          |
   | Silo A Orchestrator      |                                     | Silo B Orchestrator      |
   |                          |                                     |                          |
   | config: sstr2_a_default  |                                     | config: sst14_mutation_.. |
   +-----------+--------------+                                     +-----------+--------------+
               |                                                            |
     +---------+---------+                                        +---------+---------+
     |                   |                                        |                   |
     v                   v                                        v                   v
 +---------+         +----------+                           +-------------+      +------------+
 | Arm 1   |         | Arm 2    |                           | Constraint  |      | Generator  |
 | MolMIM  |         | FlexPep  |                           | Compiler    |      | Mutant     |
 | Docking |         | +Filter  |                           +-------------+      +------------+
 +----+----+         +----+-----+                                  |                   |
      |                   |                                        v                   v
      +---------+---------+                              +----------------+   +-------------------+
                |                                        | Pre-Dock       |   | Diversity / GA-BO  |
                v                                        | Filters        |   | /Sampling         |
            +----------+                                 +----------------+   +-------------------+
            | Arm 3    |                                           |
            | RFdiff-  |                                           v
            | Protein  |                                   +---------------------+
            | +MPNN    |                                   | Scoring + HIL Gates  |
            | +ESMFold |                                   +----------+----------+
            +----+-----+                                              |
                 |                                                    v
         +-------+--------+                                    +-----------------+
         | Arm Score Rank |                                    | Top Candidates  |
         +-------+--------+                                    | Gate2 / Gate3   |
                 |                                             +--------+--------+
                 v                                                      |
        +----------------------+                                         |
        | outputs/silo_a        |                                         |
        | run_manifest.json     |                                         |
        +----------------------+                                         |
                                                                         |
                                                         +---------------v---------------+
                                                         | outputs/silo_b                  |
                                                         | candidates / manifest / logs    |
                                                         +---------------+---------------+
                                                                         |
                                                         +---------------v---------------+
                                                         | Unified Candidate Outputs      |
                                                         | (상위 레벨 집계/리포트 연동) |
                                                         +-------------------------------+
```

## 3. 디렉토리 구조 설명
- `bionemo/`: NVIDIA NIM API client, 공통 `api_base`, 데모 스크립트.
- `pipelines/silo_a/src/`: SILO A 도메인 코드(`config`, `clients`, `arms`, `scoring`, `orchestrator`, `models`).
- `pipelines/silo_a/configs/`: SILO A 실행 config 템플릿.
- `pipelines/silo_a/tests/`: SILO A 단위/통합 테스트.
- `pipelines/silo_b/src/`: SILO B 도메인 코드(`config`, `constraint_compiler`, `generator`, `filters`, `docking`, `stability`, `scoring`, `gates`, `orchestrator`).
- `pipelines/silo_b/configs/`: SILO B Pydantic schema 기반 config, schema 문서.
- `pipelines/silo_b/docs/`: SILO B 아키텍처/방법론 문서.
- `pipelines/silo_b/tests/`: SILO B 오케스트레이션/제약/스코어 보증 테스트.
- `scripts/`: 실행 쉘 스크립트 (`run_sstr2_pipeline.sh`, `run_arm1.sh`, `run_arm2.sh`, `run_arm3.sh` 등).
- `data/fold_test1/`: AlphaFold3 예측 구조와 템플릿/ MSA 입력 데이터.
- `docs/`: 참조 문서와 아키텍처/실험 가이드.
- `README.md`: 파이프라인 전체 개요.

## 4. SILO A 아키텍처 상세

### 4.1 Config 계층
- 파일: `pipelines/silo_a/configs/sstr2_a_default.yaml`
- 파이프라인 설정 모델: `SiloAConfig`
  - `pocket`: 타깃 복합체 PDB 및 포켓 추출 기준(ligand/receptor chain, cutoff).
  - `arm1`: seed molecule 목록, MolMIM 생성 파라미터, docking top-k 설정.
  - `arm2`: wildtype 시퀀스, 변이 후보, PyRosetta 사용 플래그.
  - `arm3`: 설계 수, sequence-per-backbone, pLDDT 임계치, diffusion 단계 수.
  - `scoring`: arm별 가중치(`qed`, `dock_confidence`, `delta_energy`, `plddt`, `diversity`).
  - `output`: 출력 루트(`outputs/silo_a`)와 manifest 파일명.
- config는 `pydantic` 기반 strict 타입 검증(`extra: forbid`)으로 정합성 보장.
- `load_config`는 `yaml.safe_load`로 읽고, `config_hash`는 canonical YAML SHA-256으로 실행 추적성 제공.

### 4.2 Arm 실행기
- DI 추상화: `ArmRunner` 인터페이스 + `NimClientBundle`.
- `Arm1SmallMolRunner`
  - seed molecule 단위 MolMIM generate 실행.
  - 후보를 `qed` 점수 기준 정렬 후 상위 `top_k_for_docking`만 DiffDock 수행.
  - 후보 레코드에 `dock_confidence`, `dock_success` 추가.
- `Arm2FlexPepRunner`
  - `yaml`의 `variants`를 순회하고 길이/변이 수 분석.
  - `use_pyrosetta=true`이고 PyRosetta import 가능 시 `delta_energy`/`dock_success` 기본값을 설정(현재는 실제 FlexPepDock 계산 호출은 미구현).
  - 길이 mismatch, PyRosetta 미존재 등은 에러 목록에 남김.
- `Arm3DeNovoRunner`
  - RFdiffusion으로 `backbone` 생성.
  - 각 backbone에 대해 ProteinMPNN으로 서열 예측.
  - ESMFold으로 구조 예측 후 `plddt`를 계산해 임계치 이상 후보만 통과.
  - 후보/실패 원인 함께 수집.

### 4.3 Scoring 계층
- 파일: `pipelines/silo_a/src/scoring.py`
- `UnifiedScorer`
  - `normalize(lo, hi)` 후 arm별 feature를 정규화.
  - arm별 점수식:
    - SmallMol: `qed`, `dock_confidence`
    - FlexPep: `delta_energy`(부호 반전)
    - DeNovo: `plddt`
  - `diversity`는 단순 가산항으로 반영.
  - 0~1 구간으로 clamp 후 `rank_candidates` 정렬.

### 4.4 Orchestrator
- 파일: `pipelines/silo_a/src/orchestrator.py`
- 구성
  - `SiloAConfig` 로드 후 Arm 인스턴스 3개 생성.
  - Arm 실행 → 후보 합치기 → 통합 scoring.
  - 각 Arm별 상태/오류 수와 총 순위 개수를 `manifest`에 기록.
- 산출물
  - `PipelineResult`: run_id, config hash, arm_results, ranked_candidates, manifest.
  - manifest 기본 경로: `outputs/silo_a/run_manifest.json`.
- `clients`: `NimClientBundle` DI 주입(실제 구현체 또는 mock 교체용 인터페이스).

## 5. SILO B 아키텍처 상세

### 5.1 Config 계층
- 파일: `pipelines/silo_b/configs/sst14_mutation_default.yaml`
- 최상위 모델: `MutationConfig`
  - `sequence_metadata`: SST-14 템플릿(AGCKNFFWKTFTSC), SSTR2(Uniprot P30874), disulfide/pharmacophore.
  - `constraints`: frozen positions, per-position AA whitelist, pairwise 규칙, pharmacophore 보존 조건.
  - `generator`: strategy(기본 `ga_bo`), fallback 임계치, 예산, diversity 정책, approach A/B 정책.
  - `validation`: drugability 필터/structure 조건/dedupe 옵션.
  - `scoring`: primary objective(dG, stability), auxiliary(druggability, diversity, HIL confidence), penalties.
  - `orchestration`: batch, adaptive step, stop criteria, gate enable, seed lineage, 출력 경로.
- `load_config` 및 `config_hash`로 실행 재현성 보장.

### 5.2 Constraint Compiler
- 파일: `pipelines/silo_b/src/constraint_compiler.py`
- `ConstraintCompiler.compile()`
  - 템플릿 길이와 1-based 위치 기준으로 허용 AA 집합 맵 생성.
  - disulfide/Pharmacophore/고정 위치를 freeze 집합으로 병합.
  - mutable positions와 design space size 계산.
- `validate_sequence()`
  - 길이 일치, 허용 AA 검사, frozen 위치 일치, pharmacophore 강제 위치 검사.
  - pairwise 규칙을 `hard/soft`로 판별해 violation 반환.
  - soft violation은 `penalty_score`로 반환.

### 5.3 Generator
- 파일: `pipelines/silo_b/src/generator.py`
- `MutantGenerator`
  - `_select_strategy()`:
    - design space ≤ fallback threshold면 `enumerate`
    - 밀도 추정값이 낮으면 `sampling`
    - 그 외엔 fallback secondary 전략.
  - `sample_diverse(n, seed)`:
    - 전략에 따라 enumerate 또는 random constrained sampling.
    - `DuplicateFilter`로 Hamming distance 기반 중복 제거.
    - 미달 시 enumerate 후보로 채움.
- 목적: 제약을 만족하는 후보 공간을 충분히 탐색하면서 중복도를 낮춤.

### 5.4 Docking 계층
- 파일: `pipelines/silo_b/src/docking.py`
- `DockingRunner` 인터페이스 + 두 구현체
  - `PyRosettaDockingRunner`
    - template complex에서 peptide chain을 mutate 후 FlexPepDockingProtocol 실행.
    - 길이 mismatch/예외를 실패로 처리.
    - `dg`는 score diff(변형 - 원형)로 산출.
  - `MockDockingRunner`
    - 테스트/오프라인용 휴리스틱 scoring.
    - motif 빈도, hydrophobic ratio 기반 `dg`, `dsasa`, `wall_time_s`.
- `dock_batch`는 기본적으로 후보 리스트를 일괄 처리.

### 5.5 Filter/스테빌리티/스코어링
- 파일: `pipelines/silo_b/src/filters.py`
  - `DrugabilityFilter`:
    - `NG`/`DG` 모티프, Met 산화 위험, aggregation 점수로 pass/fail 판단.
  - `DuplicateFilter`: 최소 Hamming distance 기반 중복 체크.
- 파일: `pipelines/silo_b/src/stability.py`
  - `SequenceStabilityEstimator`: 보수적 rule-based score(유체성·전하·proline/glycine/preservation).
  - `PyRosettaStabilityEstimator`: FastRelax 기반 ddG로 정밀 점수화(리포지토리에 PyRosetta 필요).
- 파일: `pipelines/silo_b/src/scoring.py`
  - `MultiObjectiveScorer`:
    - docking, stability, druggability, diversity, hil_confidence를 clip 기반 정규화·가중합.
    - hard/soft violation과 duplicate penalty를 감점.
    - 결과를 `rank_candidates()`로 정렬.

### 5.6 Gate 계층
- 파일: `pipelines/silo_b/src/gates.py`
- `HILGate` 인터페이스 3단계
  - Gate1: static filter review (`pass_rate`, `filter_stats`).
  - Gate2: 상위 점수/pareto/다양성 score review.
  - Gate3: human-refinement 준비 상태 review.
- `DefaultHILGate.request_approval()`는 기본 `True`이므로 현재 플로우는 통상 통과 처리.

### 5.7 Orchestrator
- 파일: `pipelines/silo_b/src/orchestrator.py`
- `SiloBOrchestrator.run()` 실행 순서
  1. `ConstraintCompiler` + `MutantGenerator`로 후보 생성.
  2. static filter 및 constraint validation.
  3. Gate1 통과 여부 결정 및 early return.
  4. docking + stability + druggability + diversity + hil confidence 계산.
  5. multi-objective ranking + Gate2, Gate3 검토.
  6. 최종 상위 후보(`top 1~3`)를 `top_candidates`로 반환.
- 산출물
  - `OrchestratorResult`: generated/filtered/scored 개수, top candidates, manifest.
  - manifest에 gate 리포트와 `generator_strategy` 저장.

## 6. 공유 인프라 (NIM clients)
- `bionemo/api_base.py`: API key 자동 로드(NGC_CLI_API_KEY, NVIDIA_API_KEY, `.env`, `molmim.key`, `ngc.key`)와 재시도 정책(429/5xx exponential backoff).
- 공통 특성
  - `_post`와 `_post_raw` 제공.
  - 최대 재시도 기본 3회.
  - endpoint/path는 클라이언트별 `BASE_URL` 고정.
- 공유 클라이언트
  - `molmim_client.py`: 분자 생성·샘플링.
  - `diffdock_client.py`: 분자 도킹.
  - `rfdiffusion_client.py`: de novo backbone 설계.
  - `proteinmpnn_client.py`: backbone → sequence inverse folding.
  - `esmfold_client.py`: sequence → 3D 구조 및 pLDDT 추출.
- SILO A 통합점
  - `pipelines/silo_a/src/clients.py`의 `NimClientBundle` 프로토콜 집합.
  - `create_nim_bundle(api_key=None)`로 실제 구현체 생성.
- SILO B 통합점
  - SILO B는 현재 NIM client를 직접 주입/대체하지는 않지만, `Approach B/Approach A` 설정과 연동 가능한 확장 지점으로 사용 가능.

## 7. 데이터 흐름도
```text
(1) Input
  - data/fold_test1/fold_test1_model_0.pdb (Sstr2 pocket 기준)
  - SILO A config: sstr2_a_default.yaml
  - SILO B config: sst14_mutation_default.yaml
  - 환경: NVIDIA API key, PyRosetta(optional)
        |
        v
(2) Preprocess/Validation
  - YAML schema/load + config hash 계산
  - SILO B: Constraint compile/sequence/position 검증
  - SILO A: Arm 설정 및 클라이언트 바인딩
        |
        v
(3) Candidate Generation
  - SILO A: Arm1(MolMIM→Dock), Arm2(variant list), Arm3(RFdiffusion→MPNN→ESMFold)
  - SILO B: Constraint 기반 generator + diversity + dedupe
        |
        v
(4) Filtering / Scoring
  - SILO B: Drugability + docking + stability + violation + multi-objective + HIL Gate
  - SILO A: Arm별 통합 score normalization + rank
        |
        v
(5) Stage Outputs
  - SILO A manifest: outputs/silo_a/run_manifest.json
  - SILO B stage_counts/gate 리포트 + top_candidates
        |
        v
(6) Unified view
  - 상위 뷰에서 silos 간 결과를 합산해 비교
  - SILO A/ B 후보의 공통 속성(score, rank, gate/feasible 여부, source arm)을 기준으로 재랭킹/실험 큐 생성
```

## 8. 현재 상태 및 다음 단계
### 현재 상태
- SILO A/ B 모두 YAML schema 기반 실행 설계가 완료되어 있고, 기본 오케스트레이터/클래스 단위 테스트가 존재한다.
- 공유 NIM client는 실제 HTTP 호출까지 감싸고 있으며 재시도/키 관리/응답 파싱 유틸이 정비되어 있다.
- SILO A는 3-arm 생성 파이프라인이 동작하지만 일부 실험 파라미터(예: FlexPepDock 정밀 점수 계산)는 guard/placeholder 성격이 혼재한다.
- SILO B는 `Approach A/B` 설정 필드가 존재하지만 현재 `SiloBOrchestrator`는 실제 실행 흐름에서 approach 별 분기/재투입을 직접 구현하지 않는다.
- gate는 구조적으로 분리되어 있으며, 현재 기본 게이트는 승인 기본값이 `True`인 구현.

### 다음 단계
1. SILO A/ B 결과를 결합하는 상위 오케스트레이터를 추가해 `unified outputs`를 제도화한다.
2. SILO B에서 `approach_a` 정밀 정련 루프를 실제 게이트 통과 후보로 연결한다.
3. FlexPepDock scoring과 PyRosetta 기반 접근(Arm2, stability estimator)을 동일 스코어 척도에 맞춰 정렬한다.
4. gate 의사결정 로그(`request_approval` false case)를 구조적으로 영구 기록해 HIL traceability를 강화한다.
5. `data/fold_test1` 외 실제 AF3 실험 데이터셋과 결합한 실험별 manifest 템플릿을 정규화한다.

