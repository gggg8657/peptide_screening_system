# Silo B 아키텍처 설계 문서

## 시스템 목표
SST-14 서열 `AGCKNFFWKTFTSC`를 기반으로 SSTR2 결합성 향상 변이체를 생성한다.
Approach B의 빠른 Mutate→Dock(15s/candidate) 흐름으로 대규모 후보를 생성한다.
Approach A(142s/candidate) 정제 루프를 핵심 후보에만 적용해 HIL 반응성과 자원 효율을 동시에 확보한다.

## 6-Layer Architecture
```
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 6. Observability & Governance                                   │
│ - Audit log, seed lineage, manifest, compliance, rollback policy       │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────┴──────────────────────────────────────┐
│ Layer 5. Orchestration & Scheduling                                  │
│ - Adaptive step controller, queue broker, HIL gate scheduler           │
│ - Resource policy: Approach B(15s) 우선, Approach A(142s) 우회 적용     │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────┴──────────────────────────────────────┐
│ Layer 4. Evaluation Engine                                          │
│ - Pre-dock filter, docking runner, multi-objective scorer             │
│ - PyRosetta validation + BioNeMo NIM docking interfaces                │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────┴──────────────────────────────────────┐
│ Layer 3. Generation Engine                                           │
│ - Mutation proposer (enum / sampling / GA / BO)                    │
│ - Diversity policy, sequence manifold constraints, pairwise rules      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────┴──────────────────────────────────────┐
│ Layer 2. Knowledge & Template Layer                                  │
│ - SST-14 metadata, disulfide map, pharmacophore, receptor context      │
│ - Constraint graph, historical candidates, HIL feedback memory          │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────┴──────────────────────────────────────┐
│ Layer 1. Contract & Policy                                           │
│ - Pydantic schema validation, config hash, seed lineage, policy gates   │
│ - Risk policy (hard/soft constraints), reproducibility guarantees      │
└──────────────────────────────────────────────────────────────────────┘
```

- Layer 6은 실행 흔적(로그/메니페스트)과 감사 추적을 제공해 문제 재현을 보장한다.
- Layer 5는 적응형 단계 조절과 HIL Gate 실행 타이밍을 담당한다.
- Layer 4는 후보를 빠르게 걸러 정확도와 처리량을 동시에 확보한다.
- Layer 3은 제약 기반 후보 생성의 핵심, Layer 2는 도메인 정보를 정합성 있게 보존한다.
- Layer 1은 규정 준수형 실행을 위해 모든 입력을 스키마로 통제한다.

## 3-Phase Pipeline
```
┌───────────────┐      ┌────────────────┐      ┌────────────────────┐
│ Phase 1       │─────►│ Phase 2        │─────►│ Phase 3            │
│ Candidate     │      │ Pre-Dock +     │      │ Adaptive HIL-       │
│ Synthesis     │      │ Docking        │      │ Controlled Refining │
│               │      │                │      │                    │
│ - Apply       │      │ - Static checks│      │ - HIL Gate 2/3      │
│   constraints │      │ - Approach B   │      │ - Approach A on      │
│ - Generate    │      │   (15s/cand)  │      │   top candidates    │
│   seed pool   │      │ - Dock score    │      │ - Bayesian / GA     │
│ - Diversity   │      │   triage      │      │   updates          │
│   filter      │      │ - Gate-1       │      │ - Freeze +           │
└───────────────┘      └────────────────┘      │   manifest          │
      ▲   │                    ▲   │              └──────────▲─────────┘
      │   └──────┐             │   └───────┐                  │
      │            └─────┐       │           └───────┐          │
      └───────────── Human/Model Feedback ◄─────────────┘──────────┘
```

### Phase 설명
1. Phase 1: 제약 준수 후보 생성 + 경량 필터링.
2. Phase 2: BioNeMo 기반 docking과 약물성 필터로 대량 선별, HIL Gate-1 통과 후보만 다음 단계.
3. Phase 3: HIL Gate-2/3을 거친 상위군을 Approach A 정제(142s/cand)로 정밀 점수화.

## HIL Gates (3 Gates)
- Gate-1 Static Quality Gate
  - 위치 제약, disulfide 보존(C3-C14), 약동학 기본 필터(druggability), dedupe를 사전 점검.
  - 실패시: 후보 폐기 및 reason code 기록.
- Gate-2 Docking Triage Gate
  - Approach B docking 점수(15s/candidate) 상위군을 대상으로 diversity score / redundancy penalty 반영.
  - 실패시: 파라미터가 약한 생성 전략으로 재투입(phase-level fallback).
- Gate-3 Expert/Model Review Gate
  - HIL 주도 큐(인간/지침 기반 필터) + confidence score 통합 점수 평가.
  - 통과시 Approach A 정제 큐로 이동, 미통과시 보존성 재학습 반영 후 반복.

## Issue Resolution Map (10 issues)
1. Disulfide 무결성 붕괴(C3/C14): Layer 2 template/constraints에서 disulfide 규칙을 hard-constraint로 고정.
2. Phe7-Trp8-Lys9-Thr10 보존 실패: Layer 2 약동점(motif) + constraints `pharmacophore`로 exact motif 강제.
3. 다중 후보 중복 급증: Layer 3 diversity policy와 Layer 4 dedupe로 identity/MCS 중복 제거.
4. Docking 자원 고갈: Layer 5 adaptive scheduling이 Approach B(15s)와 Approach A(142s) 비율을 동적으로 조정.
5. 필터 우회로 인해 품질 저하: Layer 4 multi-stage pre-dock 필터 + Layer 4 penalty model로 리스크 반영.
6. Pairwise 제약 미반영: Layer 2 constraints graph에 pairwise hard/soft rule을 정의하고 생성기에서 사전 검사.
7. YAML 설정 오용: Layer 1 Pydantic schema + schema.md에서 필드 타입/기본값/검증 규칙 명시.
8. 재현성 부족: Layer 1 seed lineage + Layer 6 manifest 생성으로 동일 입력 재실행 보장.
9. HIL 지연/병목: Layer 5 큐 기반 Gate 비동기 처리 및 timeout 정책 적용.
10. Silo 간 지식 전이 미흡: Cross-silo 계약(Silo A)으로 motifs / 실패사례 / 승인 후보를 상호 동기화.

## Cross-Silo Interaction with Silo A
```
Silo A                     Silo B                          Silo A
┌──────────┐              ┌──────────┐                    ┌──────────┐
│ Prior    │─────────────►│ Strategy │◄──────────────┐    │ Refined   │
│ Motifs   │  motif_ref  │ Planner  │   feedback     │    │ Candidates│
└──────────┘              └──────────┘               └──────────┘
     ▲                        │                         ▲
     │ motif_pressure          │ candidate_export         │ docking_score
     │                        ▼                         │
┌──────────┐              ┌──────────┐               ┌──────────┐
│ Motif    │◄─────────────│ Pre-Dock │──────────────►│ Hard      │
│ Guard    │  failure_tag │+Scorer   │  failure_type   │Constraint│
└──────────┘              └──────────┘               └──────────┘
     │                        │                         │
     └───────────── Learning Sync / constraint update ───────────────┘
```
- 공유 인터페이스는 `candidate_export`, `failure_tag`, `motif_pressure`, `HIL_feedback` 4개 이벤트 타입으로 정합.
- Silo A는 통계적으로 강한 motif / hard pattern을 보내고, Silo B는 실패 사유와 성공 패턴을 역피드백.

## Technology Stack
|Layer|Technology|사용 목적|비고|
|---|---|---|---|
|설정/검증|Pydantic|YAML 스키마 검증 및 타입 강제|Schema Hash 기반 재현성|
|생성|PyRosetta|제약 준수 서열 편집, 구조성 제약 평가|후보 구조 plausibility 체크|
|도킹|BioNeMo NIM APIs|Approach B 빠른 도킹 및 scoring|15s/후보 목표|
|정제|BioNeMo / 내부 scoring API|Approach A 정밀 재평가|142s/후보 우선순위 정밀화|
|데이터 저장|JSONL/Parquet|실행 메타데이터, manifest, audit|후보 추적/버전관리|
|실행 관리|Python + Async Worker|Adaptive step, Gate scheduler|HIL 큐, timeout 정책|
|로그|Structured Logger|실패코드/이벤트 추적|Cross-silo 추적 용이|
