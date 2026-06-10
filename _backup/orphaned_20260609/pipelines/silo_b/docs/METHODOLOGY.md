# Silo B Methodology (SST-14 HIL Mutant Generation)

## 개요
Silo B는 SST-14 서열에서 생성 규칙을 엄격히 따르는 후보군을 만들고, Approach B 도킹(15s/cand)으로 대량 스크리닝한 뒤, HIL Gate를 통과한 상위군에만 Approach A(142s/cand) 정밀 정제를 수행한다.
아래 10단계 파이프라인은 구현 기준이 되는 동작 절차이다.

```
[1] Config Load
   |--> [2] Sequence/Constraint Ingestion
          |--> [3] Constraint Graph Build
                 |--> [4] Strategy Selection
                        |--> [5] Candidate Proposal
                               |--> [6] Pre-Dock Filter Pipeline
                                      |--> [7] Docking + Early Scoring
                                             |--> [8] Multi-Objective Scoring
                                                    |--> [9] Adaptive Learning Update
                                                           |--> [10] HIL Gate + Export + Archive
```

## 10-Step Methodology
### 1) Config Load
- Input: `sst14_mutation_default.yaml`
- Process: 스키마 파싱(Pydantic), 필드 기본값 주입, seed lineage 로딩
- Output: validated config object + runtime context
- Tools used: Pydantic, YAML loader, hash util

### 2) Sequence & Template Ingestion
- Input: config의 `sequence_metadata`
- Process: SST-14 template 생성, chain/disulfide/pharmacophore 위치 인덱싱(1-based), receptor context 연결
- Output: immutable template graph node, position index map
- Tools used: PyRosetta (sequence annotation), internal tokenizer

### 3) Constraint Graph Build
- Input: template map + `constraints`
- Process: frozen positions, per-position AA 집합, pairwise 규칙, pharmacophore 조건을 Graph node/edge로 컴파일
- Output: 제약 그래프(검증기) 및 빠른 룩업 캐시
- Tools used: Python dataclass, graph util

### 4) Strategy Selection
- Input: 후보 필요량, 전략 우선순위, 제약 밀집도
- Process: 의사결정 트리 기반 생성 전략 선택(상세는 아래)
- Output: strategy mode(enum/sampling/ga_bo mix), 하위 파라미터
- Tools used: 정책 엔진, rule evaluator

### 5) Candidate Proposal
- Input: 제약 그래프 + 생성 전략
- Process: 후보 시퀀스 생성(변이 제안), 충돌 탐지, 후보 ID 발급
- Output: raw candidate pool
- Tools used: PyRosetta mutation helper, Python random/stateful sampler, GA/BO optimizer

### 6) Pre-Dock Filter Pipeline
- Input: raw candidate pool
- Process: 경량 규칙 순차 적용
  1. disulfide 보존 체크
  2. Phe7-Trp8-Lys9-Thr10 motif 보존 체크
  3. per-position allowed AA 및 pairwise rule 평가
  4. 기본 druggability 휴리스틱(전하, 크기, 모티프 리스크)
  5. dedupe(부분 일치/identity) 및 길이 일치 확인
- Output: gate1_pass candidates
- Tools used: fast sequence filter, Pydantic validators, MMseqs-lite 또는 내부 유사도 인덱서

### 7) Docking + Early Scoring
- Input: gate1_pass candidates
- Process: Approach B로 병렬 도킹 실행(15초/후보 목표)
- Output: docking score, docking pose 메타데이터, 실패 코드
- Tools used: BioNeMo NIM APIs

### 8) Multi-Objective Scoring
- Input: docking 결과 + 약물성 + 구조 안정성 + diversity 메트릭
- Process: multi-objective 합성 점수 계산, 페널티 반영
- Output: 종합 점수, 순위
- Tools used: NumPy/Pandas, optional ML ranker

### 9) Adaptive Learning Update
- Input: 상위/하위 후보 점수 + HIL 피드백
- Process: step별 surrogate update, 제약 강도 보정, 후보분포 업데이트
- Output: 다음 단계 생성분포, 정책 갱신, adaptive state
- Tools used: Bayesian surrogate/GA selector, experiment tracker

### 10) HIL Gate + Export + Archive
- Input: 상위군 점수/분포 데이터 + 인간 리뷰 신호
- Process: HIL Gate-2(우선순위), Gate-3(특화 검토) 판정 후 Approach A 정제 큐 적재 및 결과 저장
- Output: 최종 후보패키지 + manifest + audit record
- Tools used: HIL UI/API, storage + manifest generator

## Generation Strategy Decision Tree
```
                                  [Candidate Budget N]
                                        |
                        ┌─────────────── N <= 2000 ───────────────┐
                        |                                         |
               [Constraint density high]                   [Constraint density low]
                        |                                         |
                 ┌──── Enum (exhaustive) ────┐          ┌────┬──────────────┐
                 |                            |          |    |              |
        [Need exact motif exploration?]     no       [Stability model
                 |                            |       confidence < θ]     >= θ
                yes                         no           |                 |
               Enumerate                        Sampling      GA            BO
               full space                                         (surrogate-guided)
```

- 기본값: `hybrid`(`ga_bo`)로 동작하되, 검색 예산이 낮고 규칙이 단순하면 `enum/sampling`으로 fallback.
- Phase 1에서는 sampling 우선, Phase 2/3 adaptive 단계에서는 GA/BO 중심 전환.

## Pre-Dock Filter Pipeline Detail
```
Raw candidates
   │
   ├─(F1) Sequence sanity: 길이/알파벳/chain 검사
   ├─(F2) Disulfide hard check: pos3/14은 항상 C
   ├─(F3) Motif hard check: 7:F,8:W,9:K,10:T
   ├─(F4) Per-position AA policy check
   ├─(F5) Pairwise rule evaluator (hard/soft)
   ├─(F6) Druggability rough checks
   ├─(F7) Dedupe + near-neighbor prune
   └─(PASS) Docking queue or Reject with reason code
```
- `F2`와 `F3`는 하드 게이트로 실패 후보는 즉시 종료.
- `F5` soft 규칙은 점수 감점만 수행하고, 허용 임계치 초과시만 폐기.

## Adaptive Learning Loop Detail
```
t = 1..adaptive_steps
  M_t = objective model(state_t)                # surrogate / ranker
  Q_t = acquisition(M_t, candidate_pool, diversity_weight_t)
  Evaluate_top_k(Q_t)                            # Approach B/selected A
  R_t = collect(docking + HIL signals)
  θ_t+1 = update_policy(θ_t, R_t, seed lineage, constraints)
```
- `diversity_weight_t`는 후반부에서 증가(탐색 수렴 억제)시켜 모드 붕괴 방지.
- HIL 반응이 적은 구간에서는 Approach A 진입 임계치를 상향 보정.

## Multi-Objective Scoring Formula
정규화 점수(`norm(x)`)와 패널티(`P`)를 사용한다.

`S = 0.45*norm(docking) + 0.20*norm(stability) + 0.15*norm(druggability) + 0.10*norm(confidence) + 0.10*norm(diversity) - 0.20*P_hard - 0.10*P_soft`

- `norm(docking)`: 더 낮은 도킹 에너지일수록 높은 점수로 선형 스케일
- `P_hard`: 하드 규칙 위반 비율(0이면 패스)
- `P_soft`: 규칙 위반 가중치 누적
- 최종 후보는 HIL Gate 점수와 함께 저장

## Reproducibility Contract
- Seed Lineage
  - `seed.base`: 상위 실험의 기본 시드
  - `seed.per_stage`: phase/generation_step/worker마다 분기 시드
  - `seed.strategy_seed`: GA/BO/샘플러 각각 독립 시드
- Config Hash
  - canonical YAML dump 후 SHA-256
  - manifest와 run_id에 `config_hash`를 삽입
- Run Manifest
  - 항목: run_id, config_hash, seed_lineage, git_sha, tool versions(PyRosetta/BioNeMo), candidates_before_after counts, all gate fail reasons
- 실패 재현
  - 동일 환경에서 동일 `config_hash + seed_lineage + input snapshot`이면 동일한 candidate stream 생성 가능

## Phase Gate Mapping
- Gate-1 = Pre-dock hard/soft filter (F2~F7)
- Gate-2 = Docking + ranking threshold
- Gate-3 = HIL review + Approach A refinement
