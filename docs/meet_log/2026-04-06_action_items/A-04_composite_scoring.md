# A-04: Top-K 후보 선정 복합 스코어링 체계 설계

## 메타
- 회의: KAERI-AIRL-MOM-2026-003 (2026-04-06)
- 담당: AI팀 (스코어링/약리학 도메인)
- 기한: 5월 회의 전
- 상태: **✅ 완료** (PR #62 머지, 7 files, +2.5K — 2026-05-19)
- 구현 위치: `pipeline_local/scoring/composite_scorer.py` + `radiolysis_scorer.py` (TODO/stub 0건, 완전 구현)
- **Tier 체계 (실제)**: `Tier.S / Tier.A / Tier.B / Tier.FAIL` — PR #62 commit 제목의 "S/A/B/C"는 오기재
- 비고: A-02(반감기), A-03(ADMET), A-05(ΔG 기준선) 선행 또는 병행 완료 필요

---

## 배경

현행 파이프라인은 FlexPepDock ΔG(도킹 결합 에너지)를 단일 선별 지표로 사용한다.
그러나 ΔG 단일 지표는 다음 위험을 내포한다:

1. **반감기 극단값**: ΔG는 우수하지만 혈청 반감기가 수 분 이하인 후보 통과
2. **ADMET 불량**: 독성·흡수 프로파일이 불량한 후보가 스크리닝 후반까지 잔류
3. **Radiolysis 취약성**: ¹⁷⁷Lu 방사선에 의해 빠르게 분해되는 잔기를 포함한 후보 통과

전략 보고서의 **13-metric panel** 및 서호성 박사 제안 **7단계 다단계 선별 체계**에 기반한
복합 스코어링 체계 수립이 필요하다.

---

## 수행 방법 (단계별)

### Step 1 — 파이프라인 산출 가능 지표 목록화
현재 `pipeline_local` 에서 실시간 산출 가능한 지표:

| 지표 | 산출 위치 | 형식 |
|------|----------|------|
| ΔG (도킹) | `pipeline_local/steps/step05_docking.py` (Boltz-2) / `step06_rosetta.py::apply_rosetta_gate()` (Rosetta) | kcal/mol (float) |
| 셀렉티비티 (ΔΔG) | `step05b_selectivity.py` | 배수 (float) |
| Radiolysis score | `pipeline_local/scoring/radiolysis_scorer.py` | 민감 잔기 개수 (int) |
| 반감기 예측값 | `pharmacology_guards.py` + A-02 | 시간 (float) |
| ADMET 독성 예측값 | A-03 (Fab-ADMET *(=pepADMET, 2026-05-20 확인)* 또는 대체) | 확률 (float, 0–1) |
| Instability Index | `pharmacology_guards.py` | 수치 (<40 안정) |
| GRAVY | `pharmacology_guards.py` | 수치 |
| Boman Index | `pharmacology_guards.py` | 수치 |

### Step 2 — Hard Cutoff (1차 필터) 설정

모든 후보는 아래 Hard Cutoff를 **전원 통과해야** Weighted Sum 단계로 진입한다.

| 지표 | Hard Cutoff | 근거 |
|------|------------|------|
| ΔG (SSTR2) | ≤ SST14 레퍼런스 ΔG | A-05 산출값 적용 |
| 셀렉티비티 | ≥ 100× (SSTR1/3/4/5 대비) | 회의 확정 |
| Radiolysis-sensitive 잔기 수 | ≤ 3개 | A-04 정의 (Cys·Met·Trp·Tyr·Phe 대상) |
| ADMET 독성 확률 | ≤ 0.3 | A-03 임계값 |
| Instability Index | < 40 | Guruprasad 1990 기준 |

**7단계 선별 체계 매핑**: Step 1 (SSTR2 Specificity) + Step 3 (Toxicity) 조건을 Hard Cutoff로 통합.

### Step 3 — 복합 스코어 산출 (Soft Ranking)

Hard Cutoff 통과 후보에 대해 **두 가지 방식** 병용:

#### 방식 A: Weighted Sum Score (WSS)

```
WSS = w1·norm(ΔG) + w2·norm(selectivity) + w3·norm(half_life)
    + w4·norm(1 - ADMET_tox) + w5·norm(10 - radiolysis_count)
```

기본 가중치 (TPP별 조정 가능):
| 지표 | 기본 가중치 (w) |
|------|--------------|
| ΔG (SSTR2) | 0.35 |
| 셀렉티비티 ΔΔG | 0.25 |
| 반감기 | 0.20 |
| ADMET (비독성) | 0.10 |
| Radiolysis 안전성 | 0.10 |

> 정규화: 각 지표를 후보군 내 min-max 정규화 후 [0,1] 스케일링.
> 가중치 합 = 1.0 (제약 조건).

#### 방식 B: Pareto Front 다목적 최적화

- 목적 함수 (최소화): `(ddg, -selectivity, -half_life, ADMET_tox, radiolysis_count)` — `ddg`는 더 작을수록 유리
- 비지배 해집합(Pareto front) 계산
- NSGA-II 알고리즘 적용 (후보 수가 50개 이상일 때 권장)
- 검증: `reviewer-math` 에이전트에 NSGA-II 수렴 검증 의뢰

#### 최종 순위 결정

| Tier | 조건 | 처리 | 비고 |
|------|------|------|------|
| **S** | WSS 상위 20% ∩ Pareto front 소속 | 합성 우선 추천 | Gate-2 진입 대상 |
| **A** | WSS 상위 20% XOR Pareto front 소속 | 2순위 검토 | S 부족 시 보완 |
| **B** | Hard Cutoff 통과, S/A 외 나머지 | 보류 | 조건 완화 시 재검토 |
| **FAIL** | **Hard Cutoff 미통과** | **탈락 (스코어링 단계 진입 불가)** | 이하 단계 진행 없음 |

> **FAIL 단계 구현 참조**: `pipeline_local/scoring/composite_scorer.py` `class Tier(str, Enum)` — `S / A / B / FAIL`
> PR #62 commit 제목의 "S/A/B/C"는 오기재 — 실제 코드는 `Tier.FAIL = "TIER_FAIL"`이 정확함

- WSS 상위 20% ∩ Pareto front 소속 후보 → **Tier-S** (합성 우선 추천)
- WSS 상위 20% XOR Pareto front 소속 → **Tier-A** (2순위 검토)
- 나머지 Hard Cutoff 통과 후보 → **Tier-B** (보류)
- Hard Cutoff **미통과** 후보 → **Tier-FAIL** (탈락 — 이하 스코어링 단계 진입 불가)

**7단계 선별 체계 매핑**: Step 4 (Lead Compound 확정).

### Step 4 — Critic Agent 자동 검증 + Planner Agent 피드백

```
Critic Agent 역할:
  - 스코어링 결과의 이상값(outlier) 검출
  - 가중치 편향 여부 확인 (단일 지표 과의존 경보)
  - 하드 컷오프 통과율이 5% 미만 시 임계값 재검토 플래그

Planner Agent 역할:
  - Tier-S/A 후보의 공통 서열 모티프 분석
  - 다음 세대 변이 전략(BLOSUM/Radiolysis 수정) 반영 규칙 업데이트
  - A-09 합성 의뢰서 초안 자동 생성 트리거
```

---

## 판단 기준 / KPI / Hard Cutoff

| 구분 | 지표 | 임계값 | 우선순위 |
|------|------|--------|---------|
| Hard Cutoff | ΔG | ≤ SST14 ref | 필수 |
| Hard Cutoff | 셀렉티비티 | ≥ 100× | 필수 |
| Hard Cutoff | Radiolysis 민감 잔기 | ≤ 3개 | 필수 |
| Hard Cutoff | ADMET 독성 | ≤ 0.3 | 필수 |
| Soft KPI | Tier-S 비율 | ≥ 3개 확보 | 목표 |
| 구현 품질 | 단위 테스트 | ≥ 10개 | 수용 기준 |
| 구현 품질 | WSS + Pareto 양방식 구현 | 모두 필수 | 수용 기준 |

### 7단계 다단계 선별 체계 매핑

| A-04 단계 | 7단계 선별 체계 단계 |
|----------|------------------|
| Step 1 (지표 목록화) | (1) SSTR2 Specificity, (2) Serum Stability 준비 |
| Step 2 (Hard Cutoff) | (1) + (3) Toxicity 조건 통합 |
| Step 3 (Soft Ranking) | (4) Lead Compound 확정 |
| Step 4 (Critic/Planner) | (5) Amino Acid Modification 입력 생성 |

---

## Radiolysis 스코어 산출 방법

서호성 박사 제안 민감도 순서 기반 점수화:

| 잔기 | 민감도 등급 | 점수 |
|------|-----------|------|
| Cys, Met | 최고 | 3점/개 |
| Phe, Tyr | 높음 | 2점/개 |
| Trp | 중간-높음 | 2점/개 |
| Pro | 중간 | 1점/개 |
| His, Leu | 낮음 | 1점/개 |

> `radiolysis_score = Σ(위 점수)`. Hard Cutoff는 **민감 잔기 개수 ≤ 3** (점수 합 ≤ 6 권장).
>
> **Cys3-Cys14 SS bond 예외**: SST-14 핵심 고리화 결합은 치환 불가 → 스코어 산출 시 제외하고
> 별도 `ss_bond_intact` 플래그로 관리.

**72시간 RCP ≥ 90% 선별 기준** (실험 검증 단계 — 회의 확정):
- 계산 단계에서는 `radiolysis_score`가 대리 지표(proxy)로 사용
- 실험 확인: ¹⁷⁷Lu 표지 후 시간별 HPLC RCP(%) — 72시간 ≥ 90% 달성 후보만 Gate-2 진출

---

## Quencher DOE 조합 (실험 참고)

서호성 박사 제안 4가지 Quencher 조합:

| 조합 | 성분 | 농도 | 참고 |
|------|------|------|------|
| QC-1 | Gentisic acid + Ascorbic acid + Ethanol | 3.5mM + 3.5mM + 7% | Lutathera® 참조 |
| QC-2 | L-Methionine + Ethanol | 3.5–10mM + 7–10% | 최근 문헌 |
| QC-3 | L-Cysteine + Gentisic acid | 3.5mM + 3.5mM | 최근 문헌 |
| QC-4 | Gentisic acid + Ascorbic acid + L-Methionine + L-Cysteine + Ethanol | 복합 | 서호성 제안 |

> DOE 방식으로 탐색 예정 — A-09 합성 후 실험 의뢰서에 Quencher 조합 선택란 포함.

---

## Radiolysis 대응 아미노산 변형 전략

서호성 박사 제안 (회의 확정):

| 원래 잔기 | 대체 후보 | 비고 |
|---------|---------|------|
| Met | Nle (norleucine) | 산화 저항성 |
| Trp | 5-F-Trp, 5-Me-Trp, 1-Me-Trp | pharmacophore 보존 |
| Tyr | 3-F-Tyr, O-Me-Tyr | |
| Cys-Cys link | Thioether bridge, Lactam bridge, Dicarba bridge | 고리화 안정성 |
| Cys (단독) | α-aminobutyric acid (Abu) | |
| His | 3-Me-His, 1-Me-His, Pyridylalanine (Pal) | |
| Phe | 4-F-Phe, Cyclohexylalanine | |
| Pro | 4-F-Pro | |
| Lys | Ornithine (Orn), Diaminobutyric acid (Dab) | |

---

## 활용 도구 / 알고리즘

| 도구/알고리즘 | 용도 |
|------------|------|
| Weighted Sum (min-max 정규화) | Soft Ranking 방식 A |
| NSGA-II (pymoo 라이브러리) | Pareto front 방식 B |
| Critic Agent (AG_src) | 스코어 이상값 자동 검증 |
| Planner Agent (AG_src) | 다음 세대 후보 생성 규칙 업데이트 |
| `pharmacology_guards.py` | 약리학 KPI 가드 (Stage 5) |
| `pipeline_local/strategies/blosum.py` | BLOSUM 변이 전략 연동 |

---

## 본 프로젝트 매핑

- **실제 구현 위치 (PR #62 머지)**:
  - `pipeline_local/scoring/composite_scorer.py` — Hard Cutoff + WSS + Pareto front Tier 분류 엔진
  - `pipeline_local/scoring/radiolysis_scorer.py` — Radiolysis 민감도 점수 산출
  - `pipeline_local/scripts/composite_scorer.py` + `pipeline_local/scripts/composite_scorer_cli.py` — CLI/래퍼 연동
  - `pipeline_local/tests/test_composite_scorer.py` — 단위 테스트
- **기존 연동**:
  - `pipeline_local/scripts/pharmacology_guards.py` — Instability/GRAVY/Boman 가드
  - `pipeline_local/strategies/blosum.py` — 변이 전략
  - `pipeline_local/steps/step05b_selectivity.py` — 셀렉티비티 입력
  - `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/pipeline/` — Critic/Planner Agent

---

## 의존성 / 연관 액션 아이템

| 관계 | 액션 아이템 | 내용 |
|------|-----------|------|
| 선행 (soft) | **A-02** | 반감기 예측값 산출 |
| 선행 (soft) | **A-03** | ADMET 독성 예측값 산출 |
| 선행 (soft) | **A-05** | SST14 레퍼런스 ΔG 기준선 확정 |
| 후행 | **A-09** | 복합 스코어링 완성 → 최종 후보 3-4개 도출 |
| 연동 | **A-06** | Amino Acid Modification — Radiolysis 변형 전략 적용 |
