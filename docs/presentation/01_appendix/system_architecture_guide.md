# SSTR2 방사성의약품 후보 스크리닝 AI 파이프라인 — 시스템 설명서

> **독자 대상**: 비개발자(약학 박사)도 전체 흐름을 이해할 수 있도록 작성.
> 코드의 실제 수치·기준값을 직접 인용한다.
>
> **작성일**: 2026-04-02 | **업데이트**: 2026-04-02 (ADMET 정확도 분석 + LLM 피드백 로직 상세 반영) | **버전**: 코드 기준 현행

---

## 목차

1. [개요](#1-개요)
2. [전체 아키텍처 — Silo A vs Silo B](#2-전체-아키텍처--silo-a-vs-silo-b)
3. [Silo B 실험 루프 (iteration 단위)](#3-silo-b-실험-루프-iteration-단위)
   - 3.1 Mutation 생성 (Thompson Sampling + BLOSUM62 + FWKT 게이트)
   - 3.2 FlexPepDock 도킹 (ddG, clash, total_score)
   - 3.3 QC 게이트 (PASS/FAIL 기준 — 수치 포함)
   - 3.4 대안 스코어링 (GNINA CNN → ECR → Pareto NSGA-II → BO)
4. [후보 평가 체계](#4-후보-평가-체계)
   - 4.1 A~E 클러스터 분류
   - 4.2 ADMET 프로파일
   - 4.3 약리학적 프로퍼티 15 메서드 (논문 출처·계산식·해석)
   - 4.4 방사선 분해 취약성 (Radiolysis Susceptibility)
   - 4.5 SS 결합 보정 pI + 분자량
5. [LLM 에이전트 시스템](#5-llm-에이전트-시스템)
   - 5.1 Planner (실험 계획 생성/수정)
   - 5.2 Scientist Critic (결과 비평)
   - 5.3 Reporter (보고서 생성)
   - 5.4 피드백 루프 흐름
6. [수렴 판정 — Mann-Whitney U](#6-수렴-판정--mann-whitney-u)
7. [현재 이슈 및 한계](#7-현재-이슈-및-한계)

---

## 1. 개요

이 시스템은 **SSTR2(Somatostatin Receptor Type 2)** 를 표적으로 하는 방사성의약품 펩타이드 후보를 AI로 설계·평가하는 파이프라인이다.

**배경**: SST-14(Somatostatin-14)는 `AGCKNFFWKTFTSC`(14 아미노산)로 구성되며 Cys3–Cys14 이황화 결합과 FWKT(7-10번 위치) 약물단(pharmacophore)을 핵심으로 갖는다. 이 펩타이드의 변이체를 설계하여 SSTR2 친화성·안정성·방사성의약품 적합성이 향상된 후보를 찾는 것이 목표다.

**활용 동위원소**: ⁶⁸Ga(진단, PET), ¹⁷⁷Lu(치료, PRRT), ²²⁵Ac(치료, 알파).

**파이프라인이 자동으로 하는 일**:
1. SST-14에 아미노산 돌연변이를 무수히 넣어본다 (하루 수백~수천 번).
2. 각 변이체가 SSTR2와 얼마나 잘 결합하는지 컴퓨터로 계산한다.
3. 결합력·안정성·독성·방사선 내성을 동시에 고려해 순위를 매긴다.
4. 결과를 분석해 다음 실험 방향을 스스로 제안한다.

---

## 2. 전체 아키텍처 — Silo A vs Silo B

```
┌─────────────────────────────────────────────────────┐
│                PRST_N_FM 프로젝트                     │
│                                                     │
│  ┌──────────────────┐    ┌────────────────────────┐  │
│  │    Silo A         │    │       Silo B           │  │
│  │  (3-Arm NIM)      │    │  (PyRosetta Mutation   │  │
│  │                  │    │     + FlexPepDock)      │  │
│  │  • RFdiffusion   │    │                        │  │
│  │  • ProteinMPNN   │    │  runner.py ← 이 문서   │  │
│  │  • DiffPepDock   │    │  중심 대상             │  │
│  └──────────────────┘    └────────────────────────┘  │
│                                                     │
│           ↓                         ↓               │
│     ┌──────────────────────────────────────┐         │
│     │         공통 평가 레이어              │         │
│     │  PharmaProperties / ADMET / Cluster  │         │
│     └──────────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

| 구분 | Silo A | Silo B |
|------|--------|--------|
| 설계 방식 | 딥러닝 구조 생성 (RFdiffusion) + 서열 설계 (ProteinMPNN) | 기준 서열(SST-14)의 점 돌연변이 탐색 |
| 도킹 엔진 | DiffPepDock (딥러닝 기반) | PyRosetta FlexPepDock (물리 기반) |
| 장점 | 완전히 새로운 서열 발굴 가능 | 결합 에너지(ddG) 계산 신뢰도 높음 |
| 현황 | NIM Cloud → 로컬 모델 전환 진행 중 | **현재 주 운영 파이프라인** |
| 중심 파일 | `AG_src/pipeline/orchestrator.py` | `pyrosetta_flow/runner.py` |

**이 문서는 Silo B (runner.py) 를 중심으로 설명**한다.

---

## 3. Silo B 실험 루프 (iteration 단위)

전체 흐름을 한눈에 보면:

```
[초기화]
  → 기준선(SST-14 원래 서열) FlexPepDock (N회 best-of)
  
[iteration 1, 2, ... max_iterations]
  → Planner: 실험 가설·mutation 안내 생성
  → Mutation 생성 (Thompson Sampling / Random / Guided)
  → FWKT 약물단 보존 게이트 (최대 3회 재시도)
  → 중복 서열 제거 (최대 50회 재시도)
  → FlexPepDock 도킹 (병렬 max 4 프로세스)
  → QC 게이트 적용
  → 대안 스코어링 (GNINA → ECR → Pareto → BO)
  → Critic: 결과 분석 + 다음 가설 제안
  → Reporter: 보고서 저장
  → 수렴 판정 (Mann-Whitney U)
  
[종료]
  → 최종 후보 클러스터 분류 (A~E)
  → 약리학 프로퍼티 계산
  → FlowArtifacts JSON 저장
```

**FlowConfig 주요 설정값** (`pyrosetta_flow/schema.py`):

| 파라미터 | 기본값 | 의미 |
|---------|--------|------|
| `original_sequence` | `"AGCKNFFWKTFTSC"` | SST-14 기준 서열 |
| `design_positions` | `[1,2,4,5,6,7,8,9,10,11,12,14]` | 변이 가능 위치 (1-인덱스) |
| `n_candidates` | 8 | iteration당 생성할 후보 수 |
| `max_iterations` | 2 | 최대 반복 횟수 |
| `rosetta_ddg_max` | `-5.0` | QC 통과 ddG 상한 (kcal/mol) |
| `rosetta_clash_max` | `10` | QC 통과 최대 clash 수 |
| `max_parallel_workers` | 4 | 병렬 FlexPepDock 프로세스 수 |
| `n_baseline_trials` | 3 | 기준선 best-of 시행 횟수 |
| `convergence_window_size` | 3 | 수렴 판정 윈도우 크기 |
| `convergence_significance` | 0.05 | Mann-Whitney U 유의수준 |
| `bandit_n_focus` | 3 | Thompson Sampling 포커스 위치 수 |
| `max_dedup_trials` | 50 | 중복 서열 재시도 한계 |
| `max_random_mutations` | 3 | 후보당 최대 동시 돌연변이 수 |

---

### 3.1 Mutation 생성 — Thompson Sampling + BLOSUM62 + FWKT 게이트

#### 가. FWKT 약물단 보존 (필수 제약)

**SST-14의 FWKT(7~10번 위치: Phe7-Trp8-Lys9-Thr10)는 SSTR2 결합의 핵심**이다.
코드(`runner.py`)는 새 서열을 생성할 때마다 이 위치를 점검한다:

```
PHARMACOPHORE_POSITIONS_1IDX = (7, 8, 9, 10)
```

- 생성된 서열이 FWKT를 보존하지 못하면 최대 **3회**(PHARMACOPHORE_RETRY_LIMIT) 재생성한다.
- 3회 초과 시에도 통과 못 하면 해당 후보를 폐기한다.
- Cys(3번, 14번)도 변이 대상에서 **제외**된다(`AA_NO_CYS` 리스트 사용).

#### 나. Thompson Sampling 밴딧 (`pyrosetta_flow/bandit.py`)

단순 랜덤 탐색 대신, **어느 위치를 바꾸면 ddG가 개선되는지 학습**하는 알고리즘이다.

**원리 (Multi-Armed Bandit)**:
- 변이 가능 위치(1,2,4,5,6,11,12,13번)마다 Beta 분포(α, β)를 유지한다.
- 과거 이력에서 해당 위치 변이가 ddG를 낮췄으면 α를 올리고, 악화시켰으면 β를 올린다.
- 샘플링 시 Beta(α, β)에서 무작위로 값을 뽑아 가장 높은 위치 `bandit_n_focus`개를 선택.
- 초기 prior: α=1.0, β=1.0 (모든 위치 동등)
- WT(야생형) ddG 대비 개선되면 α += 1, 악화되면 β += 1

**결과**: 학습이 진행될수록 '잘 되는 위치'에 집중 탐색한다.

#### 다. 세 가지 Mutation 모드

1. **Random**: `design_positions`에서 1~3개 위치 무작위 선택 후 Cys 제외 19종 중 랜덤 아미노산으로 치환.
2. **Bandit-Guided** (Thompson Sampling): 위에서 학습한 포커스 위치를 우선 탐색.
3. **Planner-Guided**: LLM Planner가 제안한 특정 위치·아미노산 목록을 반영.

---

### 3.2 FlexPepDock 도킹 — ddG, clash, total_score

**FlexPepDock**은 Rosetta 기반의 펩타이드-단백질 도킹 프로토콜로, 펩타이드의 구조적 유연성을 고려하여 결합 포즈와 에너지를 계산한다.

**실행 방식**: `AG_src/scripts/flexpep_dock.py`를 subprocess로 호출 (conda 환경 `bio-tools`), JSON 결과 반환.

**출력 주요 값**:

| 값 | 의미 | 좋은 방향 |
|----|------|---------|
| `ddG` (kcal/mol) | 결합 자유에너지 변화. 음수일수록 결합력 강함 | 낮을수록 좋음 (음수 방향) |
| `total_score` | Rosetta 전체 에너지 함수 점수 | 낮을수록 좋음 |
| `clash_score` | 원자 간 충돌(steric clash) 횟수 | 낮을수록 좋음 (0에 가깝게) |

**기준선 준비**: 원래 SST-14를 `n_baseline_trials=3`회 도킹 후 최고 ddG를 기준선으로 설정.

**병렬 도킹**: `max_parallel_workers=4`개 프로세스를 ThreadPoolExecutor로 동시 실행하여 속도 향상.

**Objective Mode**:
- `ddg_only` (iteration 1): 결합 에너지만으로 평가 (초기 탐색)
- `ddg_plus_constraints` (iteration 2+): 구조 제약 위반 포함 평가 (정밀 검증)

---

### 3.3 QC 게이트 (PASS/FAIL 기준 — 수치 포함)

`AG_src/agents/qc_ranker.py`에서 정의된 4단계 게이트.

**Silo B(pyrosetta_only 모드)에서 활성화되는 게이트**:

#### Gate 1: ESMFold pLDDT (Silo B에서는 비활성)
- `plddt_mean >= 75` AND `plddt_interface >= 70`
- Silo B는 pLDDT를 계산하지 않으므로 이 게이트는 `DISABLED — 전체 통과`.

#### Gate 2: Docking Score (Silo B에서는 비활성)
- dock_score 기준 상위 20% 통과
- Silo B는 별도 docking score 없으므로 `DISABLED`.

#### Gate 3: Rosetta 게이트 (핵심 게이트)
```
ddG <= -5.0 kcal/mol   (rosetta_ddg_max)
clash_count <= 10      (rosetta_clash_max)
constraint_violations == 0
```
→ 세 조건 모두 충족해야 PASS. 하나라도 실패하면 FAIL + 실패 이유 기록.

#### Gate 4: Selectivity 게이트 (현재 미운용)
- SSTR2 vs 다른 서브타입(SSTR1~5) 선택성 마진 >= 3.0
- 데이터가 없을 경우 자동 통과.

**Silo B 가중치** (`PYROSETTA_ONLY_WEIGHTS`):

```python
{
    "plddt":      0.0,
    "dock_score": 0.0,
    "ddg":        0.70,   # 70% — 결합 에너지 중심
    "lddt":       0.0,
    "selectivity": 0.0,
    "total_score": 0.20,  # 20% — 전체 구조 에너지
    "clash":       0.10,  # 10% — 원자 충돌
}
```

---

### 3.4 대안 스코어링 — GNINA → ECR → Pareto NSGA-II → BO

FlexPepDock 이후 선택적으로 적용되는 4단계 추가 스코어링 체인. 각 단계는 독립적으로 실패해도 파이프라인이 계속 진행된다.

#### Step 1: GNINA CNN 재스코어링 (`pyrosetta_flow/gnina_rescoring.py`)

GNINA(v1.3.2)는 딥러닝 CNN을 이용하여 단백질-리간드 결합 점수를 계산하는 도구.

- FlexPepDock 출력 PDB를 수용체/리간드로 분리하여 `gnina --score_only` 실행
- 출력: `gnina_cnn_score`, `gnina_cnn_affinity`, `gnina_vina_score`
- GNINA 바이너리가 없으면 **dry-run 모드**(mock 0.0 값 반환)로 자동 전환 — 하류 파이프라인 계속 실행

#### Step 2: ECR (Exponential Rank Consensus)

여러 스코어 항을 하나로 통합하는 수식:

```
ECR_i = Σ_k  exp(−rank_{i,k} / N)
```

- 각 스코어 항에서 i번 후보의 순위(rank)를 구한 뒤 지수 감쇠 합산
- ddG, gnina_cnn_score, gnina_cnn_affinity, gnina_vina_score 4항 통합
- 낮은 값이 좋은 모든 스코어에 대해 오름차순 순위 배정
- ECR이 높을수록 여러 기준에서 일관되게 좋은 후보

#### Step 3: Pareto NSGA-II (`pyrosetta_flow/pareto_ranking.py`)

4개 목적함수를 동시에 최적화하는 다목적 최적화.

**목적함수** (모두 최소화):
1. `ddG` — 결합 에너지 (낮을수록 좋음)
2. `-stability` — 안정성 proxy (clash_score로부터 계산: `max(0, 40 - clash_score)`)
3. `-druggability` — 약물성 proxy (ECR 점수)
4. `-diversity` — 다양성 (현재 0으로 미계산 — 미구현)

**제약 조건**:
- `hard_violations <= 0` (QC 실패 없음)
- `clash_score <= 10.0`

**출력**: 각 후보에 `pareto_rank`(0=최고 프론트)와 `crowding_distance`(높을수록 다양성 기여) 부여.

**의미**: 단순히 ddG만 좋은 후보가 아니라, 여러 특성이 골고루 우수한 후보를 찾는다.

#### Step 4: Bayesian Optimization 제안 (`pyrosetta_flow/bayesian_optimizer.py`)

GP(Gaussian Process) 서로게이트 모델로 다음 번에 탐색할 위치를 제안.

- 현재 observation(서열 → ddG, ECR)을 GP에 피팅
- 모든 단일점 돌연변이 조합의 획득 함수(Acquisition Function) 계산
- BoTorch 사용 가능 시: qNEHVI (다목적 하이퍼볼륨 개선)
- BoTorch 없을 때: UCB(Upper Confidence Bound) = mean + 2×√variance
- 상위 3개 위치를 Thompson Sampling 보완 정보로 제공

**주의**: BO 결과는 로그에만 기록되며, 현재 iteration 후보 선택에는 직접 반영되지 않음 (다음 iteration Planner에 간접 제공).

---

## 4. 후보 평가 체계

### 4.1 A~E 클러스터 분류 (`pyrosetta_flow/cluster_report.py`)

FlexPepDock + 약리학 분석 결과를 종합하여 각 후보를 5개 등급으로 분류.
우선순위: **A > B > C > D > E** (여러 기준 충족 시 가장 높은 클러스터만 배정).

#### Cluster A — 고친화도 코어 (High Affinity Core)

```
ddG ≤ -8.0 kcal/mol
clash_score ≤ 5
pLDDT ≥ 75
FWKT pharmacophore 유지 (structural_rules.fwkt_pharmacophore.pass == True)
```

의미: 모든 핵심 기준을 만족하는 최우수 후보. 즉시 합성 후보.

#### Cluster B — 선택성 최적화 (Selectivity-Optimised)

```
selectivity_margin ≥ 3.0   (SSTR2 vs 타 서브타입)
ddG < -5.0 kcal/mol
```

의미: SSTR2에 선택적으로 결합하여 부작용 위험이 낮은 후보.

#### Cluster C — 안정성 강화 (Stability-Enhanced)

```
instability_index < 30
BLOSUM62 total_score ≥ 0   (보수적 치환)
total protease sites ≤ 9  (SST-14 native 기준치, _SST14_PROTEASE_BASELINE=9)
```

의미: 생체 내 효소 분해에 내성이 강하여 반감기가 긴 후보.

#### Cluster D — 방사화학 최적 (Radiochemistry-Optimal)

```
GRAVY ∈ [-1.0, +0.5]         (너무 소수성/친수성 아닌 범위)
|net_charge_ph7.4| ≤ 1.0     (전하 중성에 가까움)
metal_coordination.n_strong ≥ 1  (킬레이터 결합 가능 잔기 존재)
```

의미: ⁶⁸Ga/¹⁷⁷Lu 표지 최적화 후보. 킬레이터(DOTA, NOTA) 결합에 적합.

#### Cluster E — 탐색적 후보 (Exploratory Candidates)

A~D 기준을 모두 충족하지 못하는 나머지 후보. 폐기 아님 — 추가 최적화 대상.

---

### 4.2 ADMET 프로파일 (`backend/admet.py`)

서열 정보만으로 계산하는 약동학/독성 지표. 외부 의존성 없음 — 순수 Python 계산.

> **⚠️ 중요 구분**: `druglikeness_score`, `amphipathicity_index`, `renal_risk_score`는 **자체 휴리스틱(in-house surrogate)** 이며 논문 근거가 없다. 보고서에서 반드시 "in-house surrogate"로 명기해야 한다. 학계 표준 13개 메서드(`pharma_properties.py`)와 혼동하지 말 것.

#### /api/admet/{sequence} 전체 반환 구조

```json
{
  "sequence": "AGCKNFFWKTFTSC",
  "admet": {
    "mw": float,                     // 단일동위원소 MW (Da)  ← 학계 표준
    "net_charge_ph74": float,        // 정수 합산 방식        ← ⚠️ 근사치
    "n_hbd": int,                    // H-bond donor 수       ← 학계 표준
    "n_hba": int,                    // H-bond acceptor 수    ← 학계 표준
    "hydrophobicity": float,         // Kyte-Doolittle 평균   ← 학계 표준
    "amphipathicity_index": float,   // KD 분산               ← ⚠️ 비표준
    "druglikeness_score": int,       // 0/25/50/75/100        ← ⚠️ 자체 규칙
    "druglikeness_breakdown": dict
  },
  "nephrotox": {
    "n_lys", "n_arg", "n_his",
    "cationic_residues": int,
    "net_charge": float,
    "renal_risk_score": float,       // ⚠️ 자체 surrogate 공식
    "risk_level": "Low|Moderate|High",
    "warning": str
  }
}
```

#### Druglikeness Score (0~100) — ⚠️ 자체 규칙, 논문 미인용

Lipinski Rule of 5와 **무관**하며, 14-mer SST-14 아날로그에 특화된 임의 기준이다.

| 규칙 | 조건 | 배점 |
|-----|------|-----|
| MW 범위 | 1,200 ≤ MW ≤ 2,000 Da | +25 |
| 전하 범위 | \|net_charge\| ≤ 3 | +25 |
| 소수성 범위 | −2.0 ≤ KD_mean ≤ +1.0 | +25 |
| 반복 없음 | 3개 이상 연속 동일 잔기 없음 | +25 |

#### Amphipathicity Index — ⚠️ 비표준 정의

현재 코드: `Σ(KD_i − mean_KD)² / N` = **KD 분산** (두면성 포착 불가)

학계 표준(Eisenberg et al. 1982)은 나선 각도를 고려한 **소수성 모멘트(μH)**:
`μH = (1/N) × √[(Σ H_i sin(nδ))² + (Σ H_i cos(nδ))²]`

→ `pharma_properties.py`의 `calculate_hydrophobic_moment()`가 올바른 Eisenberg μH 구현.

#### compute_nephrotox_risk() — ⚠️ 자체 surrogate 공식

PRRT에서 가장 큰 부작용은 **신장 재흡수(renal retention)**이다. Lys/Arg가 신세뇨관 메가린(megalin) 수용체 재흡수를 유발한다 (Vegt et al. 2010 계열 발상 기반, 계수 미확인).

```python
renal_risk_score = min(100, (n_lys + n_arg) × 20 + max(0, net_charge) × 15)
```

계수 20과 15는 논문 근거 없는 경험적 값이다.

| 점수 | 위험 수준 | 권고 |
|------|---------|------|
| < 30 | Low | 일반 모니터링 |
| 30~60 | Moderate | 아미노산 공동 주입 고려 |
| > 60 | High | Gelofusine 공동 투여 강력 권고 |

참고: DOTATATE (임상 표준)는 Lys 1개, charge ~+1, 점수 ~25 (Low).

#### net_charge_ph74 계산의 한계 (admet.py vs pharma_properties.py 불일치)

`backend/admet.py`는 **정수 합산** (K/R: +1, D/E: −1, H: +0.1)을 사용한다.
`pharma_properties.py`의 `calculate_net_charge()`는 **Henderson-Hasselbalch** (SS 결합 Cys 보정 포함)를 사용한다.

His(pKa=6.00)는 pH 7.4에서 ~10%만 하전되므로 두 계산값 차이 발생.
Cluster D 기준(|charge| ≤ 1.0) 적용 시 어느 값을 사용하느냐에 따라 통과 여부가 달라질 수 있다.

#### pepADMET 대비 항목 비교

| 기능 | pepADMET | 우리 시스템 | 방사성의약품 중요도 |
|------|---------|-----------|-----------------|
| BBB 투과성 | ✅ | ❌ | 낮음 (i.v. 투여) |
| 혈청 알부민 결합 | ✅ | ❌ | 중간 (반감기 영향) |
| 장 흡수 (Caco-2/HIA) | ✅ | ❌ | 낮음 (주사제) |
| 용혈성 (hemolysis) | ✅ | ❌ | **높음 (i.v.)** |
| 항원성/면역원성 | ✅ | ❌ | 중간 |
| 방사선분해 취약성 | ❌ | ✅ | **방사성의약품 고유** |
| 신독성 위험 (PRRT) | ❌ | ✅ | **방사성의약품 고유** |
| 킬레이터 N-말단 적합성 | ❌ | ✅ | **방사성의약품 고유** |
| 금속 배위 잔기 분석 | ❌ | ✅ | **방사성의약품 고유** |

---

### 4.3 약리학적 프로퍼티 15 메서드 (`AG_src/pipeline/pharma_properties.py`)

모든 계산은 논문 발표 척도(scale)를 사용하며, 주관적 가중치 없이 순수 물리화학 수치를 반환한다.

> **전체 메서드 요약표** — 표준 여부 한눈에 보기

| # | 메서드 | 출처 | 표준 여부 | 주요 한계 |
|---|--------|------|----------|---------|
| 1 | GRAVY | Kyte & Doolittle 1982 | ✅ 학계 표준 | 3D 구조 무시 |
| 2 | Boman Index | Boman 2003 (RW scale: Radzicka-Wolfenden 1988) | ✅ 학계 표준 | BI > 2.48 = 고단백 결합 잠재력 |
| 3 | Instability Index | Guruprasad et al. 1990 | ✅ 학계 표준 | 구형 단백질 기준, 펩타이드엔 근사 |
| 4 | Aliphatic Index | Ikai 1980 | ✅ 학계 표준 | 짧은 펩타이드엔 의미 제한 |
| 5 | Isoelectric Point | Bjellqvist et al. 1993 / Lehninger pKa | ✅ 학계 표준 | SS bond Cys 보정 구현됨 ✓ |
| 6 | Extinction Coefficient (ε₂₈₀) | Pace et al. 1995 | ✅ 학계 표준 | 정확도 ±5% |
| 7 | N-end Rule Half-life | Varshavsky 1996 | ✅ 학계 표준 | 세포 내 예측, 혈중 반감기와 다름 |
| 8 | Hydrophobic Moment (μH) | Eisenberg et al. 1982 | ✅ 학계 표준 | α-나선 100° 기본값 |
| 9 | Wimley-White ΔG | Wimley & White 1996 | ✅ 학계 표준 | 막 삽입 ΔG, 수용성 SSTR2 리간드에 한계 |
| 10 | Net Charge / pI Profile | Henderson-Hasselbalch | ✅ 학계 표준 | SS bond Cys 보정 구현됨 ✓ |
| 10b | Molecular Weight | 표준 생화학 | ✅ 학계 표준 | 단일동위원소 approx. ±0.5 Da |
| 11 | Protease Cleavage Sites | MEROPS DB | ✅ 근사 표준 | 4종 효소 (chymo/trypsin/NEP/DPP-IV) |
| 12 | BLOSUM62 Conservation | Henikoff & Henikoff 1992 | ✅ 학계 표준 | 동일 길이 서열만 비교 가능 |
| 13 | Metal Coordination | Rulísek & Vondrásek 1998 | ✅ 학계 표준 | 결합 친화도 정량화 없음 |
| 14 | Radiolysis Susceptibility | ⚠️ **자체 surrogate** | ❌ 자체 규칙 | 방사화학 ROS 반응속도론 근거 없음 |

---

#### 1. GRAVY (Grand Average of Hydropathy)

**출처**: Kyte & Doolittle, *J Mol Biol* 157:105-132, 1982

**계산식**: GRAVY = Σ(KD_score[aa]) / 서열길이

**KD 척도 예시** (양수=소수성, 음수=친수성):
- Ile(I): +4.5, Val(V): +4.2, Leu(L): +3.8, Phe(F): +2.8, Ala(A): +1.8
- Arg(R): −4.5, Lys(K): −3.9, Asp(D)/Asn(N)/Glu(E)/Gln(Q): −3.5

**해석**: SST-14 GRAVY ≈ −0.26 (약간 친수성). Cluster D 기준 −1.0 ≤ GRAVY ≤ +0.5.
- GRAVY > +1: 지나치게 소수성 → 응집/침전 위험
- GRAVY < −2: 너무 친수성 → 막 투과 불량, 빠른 신장 배출

#### 2. Boman Index (단백질 결합 잠재력)

**출처**: Boman, *J Intern Med* 254:197-215, 2003

**계산식**: BI = Σ(Radzicka-Wolfenden 전달 자유에너지[aa]) / 서열길이

**해석**: BI > 2.48 kcal/mol → 단백질 결합력 높음. SSTR2 결합에는 적절한 BI가 필요하지만, 너무 높으면 비특이적 단백질 결합 증가.

#### 3. 불안정성 지수 (Instability Index)

**출처**: Guruprasad et al., *Protein Eng* 4:155-161, 1990

**계산식**: II = (10/n) × Σ DIWV[aa_i][aa_{i+1}]

여기서 DIWV는 400개(20×20) 다이펩타이드 불안정화 가중치 테이블 (ExPASy ProtParam 동일).

**해석**:
- II < 40 → 안정 단백질 (in vitro 반감기 > 5시간 예측)
- II ≥ 40 → 불안정 단백질
- Cluster C 기준: II < 30 (보수적 기준)

#### 4. 지방족 지수 (Aliphatic Index)

**출처**: Ikai, *J Biochem* 88:1895-1898, 1980

**계산식**: AI = (A%) + 2.9×(V%) + 3.9×(I%+L%)

여기서 A/V/I/L의 몰분율(%)을 사용. 계수(2.9, 3.9)는 Van der Waals 부피 차이 반영.

**해석**: AI 높을수록 열안정성 강함. 방사성의약품 제조 공정(고온 합성)에 유리.

#### 5. 등전점 (Isoelectric Point, pI)

**출처**: Bjellqvist et al. 1993 / Lehninger pKa 세트

**계산법**: Henderson-Hasselbalch 이분법(bisection) 200회 반복으로 순전하=0인 pH 결정.

**pKa 값**:
- N-말단: 9.69, C-말단: 2.34
- 잔기: Asp 3.65, Glu 4.25, His 6.00, Cys 8.18, Tyr 10.07, Lys 10.53, Arg 12.48

**SS 결합 보정**: `ss_bond_cysteines` 파라미터로 이황화 결합 참여 Cys를 이온화에서 제외.
→ SST-14는 Cys3-Cys14가 SS 결합 → 두 Cys의 티올(-SH) pKa 기여 없앰 → pI 상승.

**해석**: pI ≈ 생리 pH(7.4)에 가까울수록 수용성 및 안정성 유리.

#### 6. 몰 흡광계수 (Molar Extinction Coefficient, ε₂₈₀)

**출처**: Pace et al., *Protein Sci* 4:2411-2423, 1995

**계산식**: ε₂₈₀ = W×5500 + Y×1490 + (SS 결합 수)×125 (M⁻¹cm⁻¹)

**해석**: 펩타이드 농도 측정에 사용. SST-14는 W(Trp8), Y 없음: ε = 1×5500 + 0 + 1×125 = 5625.

#### 7. N-말단 규칙 반감기 (N-end Rule Half-life)

**출처**: Varshavsky, *PNAS* 93:12142, 1996

N-말단 아미노산 종류에 따른 포유류(망상적혈구) 세포 내 반감기:

| 카테고리 | N-말단 AA | 반감기 |
|---------|---------|------|
| 안정 | M, S, A, T, V, G, P | 30시간 |
| 중간 | I, C | 1.2~20시간 |
| 불안정 | Y, W, H, L | 2.8~5.5시간 |
| 매우 불안정 | F, D, K, R, E, N, Q | 0.8~1.3시간 |

**SST-14**: N-말단 Ala(A) → "안정" (30시간).

#### 8. 소수성 모멘트 (Hydrophobic Moment, μH)

**출처**: Eisenberg et al., *Nature* 299:371-374, 1982

**계산식**: μH = (1/n)√(Σ H_i×sin(i×δ))² + (Σ H_i×cos(i×δ))²

여기서 δ는 나선 회전각(α-나선: 100°, β-시트: 160°), H_i는 Eisenberg 소수성 척도.

**해석**: μH 높을수록 양친매성(amphipathic) — 소수성 면과 친수성 면이 분리된 구조. 막 결합 성향 예측에 활용.

#### 9. Wimley-White 소수성

**출처**: Wimley & White, *Nat Struct Biol* 3:842-848, 1996

**계산식**: 물→POPC 인터페이스로의 전달 자유에너지(ΔG) 합산

**해석**: 총 ΔG < 0 → 막 계면 친화성 있음. 양이온성 SSTR2 세포외루프와의 상호작용에 영향.

#### 10. pH 7.4에서의 순전하 (Net Charge at pH 7.4)

**출처**: Henderson-Hasselbalch 방정식

Lehninger pKa 세트를 이용, SS 결합 Cys 제외 옵션 포함. (계산 상세는 §5에 서술)

#### 10b. 분자량 (Molecular Weight)

**계산식**: MW = Σ(AA_MW[aa]) − (n−1)×18.015 − n_SS×2.016

- 각 아미노산 잔기 질량은 비공유 형태의 아미노산 질량
- 펩타이드 결합 형성마다 물 1분자 제거 (n−1개)
- 이황화 결합 1개당 수소 2개(= 2.016 Da) 제거

#### 11. 프로테아제 절단 부위 (`count_protease_sites`)

**출처**: MEROPS 데이터베이스 규칙

4종 프로테아제 부위를 카운트:

| 효소 | 절단 규칙 | 임상 의미 |
|-----|---------|---------|
| 키모트립신 | F/W/Y/L/M 잔기 C-말단 (Pro 앞 제외 없음) | 소화기·혈청 분해 |
| 트립신 | K/R 잔기 C-말단 (다음 잔기 Pro면 제외) | 혈청·장관 분해 |
| 넵릴리신 | F/W/Y/L/I/V/M 잔기 N-말단 (2번 위치~) | 신장·혈관 분해 |
| DPP-IV | Pro 또는 Ala 잔기 C-말단 (Pro-Pro 제외) | 혈청 프롤린 특이 분해 |

**SST-14의 native 부위 수**: 9개 (Cluster C 기준으로 사용).

#### 12. BLOSUM62 보존 점수

**출처**: Henikoff & Henikoff, *PNAS* 89:10915-10919, 1992

기준 서열(SST-14)과의 BLOSUM62 치환 행렬 점수 합산.

| 점수 | 분류 |
|-----|------|
| BLOSUM ≥ 1 | 보수적 치환 (conservative) |
| BLOSUM = 0 | 반보수적 (semi-conservative) |
| BLOSUM < 0 | 비보수적 (non-conservative) |

**해석**: total_score ≥ 0 → 전반적으로 보수적 치환. Cluster C 기준.

#### 13. 금속 배위 잔기 분석

**출처**: Rulísek & Vondrásek, *J Inorg Biochem* 71:115-127, 1998

방사성 금속 이온과 결합 가능한 잔기 분류:

| 잔기 | 배위 기작 | 해당 금속 |
|-----|---------|---------|
| H (His) | 이미다졸 질소 | Zn²⁺, Cu²⁺, Ga³⁺ |
| C (Cys) | 티올레이트 황 | Zn²⁺, Cu²⁺ |
| D (Asp) | 카르복실산 산소 | Ca²⁺, Mg²⁺, Lu³⁺, Ac³⁺, Ga³⁺ |
| E (Glu) | 카르복실산 산소 | Ca²⁺, Mg²⁺, Lu³⁺, Ac³⁺, Ga³⁺ |
| M (Met) | 티오에테르 황 | Cu²⁺ |

**`n_strong`** = 강결합 잔기(H, C, D, E, M) 합계. Cluster D 기준: n_strong ≥ 1.

> **참고**: Ga³⁺(⁶⁸Ga)는 산소 친화성이 강한 경성 루이스산이므로 D/E 잔기가 주요 배위 자리.

---

### 4.4 방사선 분해 취약성 (Radiolysis Susceptibility)

방사성의약품은 방사선이 물을 분해해 생성하는 활성산소(ROS: OH·, O₂·⁻ 등)에 의해 자체 손상될 수 있다.

**계산**: 취약 잔기마다 경험적 가중치를 부여하여 총점 계산.

| 잔기 | 가중치 | 산화 기작 |
|-----|-------|---------|
| Met (M) | 3.0 | S → Met-sulfoxide (가장 반응성 높음) |
| Trp (W) | 3.0 | 인돌 고리 → 키뉴레닌 등 |
| Cys (C, 유리 티올) | 2.0 | 티올 산화 |
| Cys (C, SS 결합 참여) | 1.0 | SS 결합으로 보호됨 → 가중치 절감 |
| His (H) | 2.0 | 이미다졸 고리 산화 |
| Tyr (Y) | 1.0 | 페놀 고리 산화, 디티로신 |
| Phe (F) | 0.5 | 방향족 수산화 (가장 낮음) |

**위험 분류**:
- 총점 ≤ 3.0: **low** (위험 낮음)
- 3.0 < 총점 ≤ 6.0: **moderate** (안정화제 첨가 권고)
- 총점 > 6.0: **high** (서열 수정 고려)

**FWKT 위치(7-10번) 내 취약 잔기**는 `critical_positions`로 별도 보고 — 약물단 손상 직접 위험.

**SST-14 예시**: Trp8(W, +3.0), Cys3+Cys14(SS 결합, 각 +1.0), Phe7+Phe11(F, 각 +0.5) → 총점 6.0 (moderate 경계).

---

### 4.5 SS 결합 보정 pI + 분자량

**SS 결합(Cys3-Cys14)이 pI에 미치는 영향**:

SST-14의 Cys3–Cys14는 이황화 결합을 형성하므로 두 Cys의 -SH(pKa 8.18)가 이온화에 참여하지 않는다. 이를 코드로 반영:

```python
calculate_pi(sequence, ss_bond_cysteines={2, 13})   # 0-indexed: Cys3=2, Cys14=13
calculate_net_charge(sequence, ph=7.4, ss_bond_cysteines={2, 13})
```

SS 결합 미보정 시 Cys 두 개의 음전하가 과다 계산되어 pI가 낮게 추정됨.

**분자량에서의 SS 결합 보정**:
```python
calculate_mw(sequence, n_disulfide=1)
# = Σ AA_MW − (n−1)×18.015 − 1×2.016
```

이황화 결합 1개 = 수소 2개 제거 = −2.016 Da.

---

## 5. LLM 에이전트 시스템

### 5.1 Planner — 실험 계획 생성/수정 (`AG_src/agents/planner.py`)

**역할**: Co-Scientist 루프의 첫 번째 에이전트. 각 iteration의 실험 목표·제약·가설을 정의하고 ExperimentPlan을 생성한다.


> 참고: Silo A용 default 모드 프롬프트도 존재하나, 현재 runner는 `planner_mode="pyrosetta_only"`로 동작.

#### 사용자 프롬프트에 포함되는 컨텍스트

- iteration 번호, 수용체명(SSTR2), reference sequence(`AGCKNFFWKTFTSC`)
- design_positions (1-indexed, Cys3/Cys14 고정, Cys 돌연변이 금지)
- **이전 iteration 결과**: best_ddg, n_passed_QC, hypothesis, top-5 후보 서열+ddG
- **critic_feedback**: overall_assessment, primary_failure_type, parameter_changes 목록

#### Planner가 반환하는 Mutation Guidance 형식

```json
{
  "focus_positions": [5, 9, 11],
  "suggested_mutations": {"5": ["W", "F"], "9": ["R", "H"]}
}
```
→ `adapter.py`의 `generate_guided_mutant()`에서 직접 사용.

#### ExperimentPlan 핵심 구성

| 항목 | 내용 |
|-----|------|
| `run_id` | 형식: YYYYMMDD_HHMM_iterXX |
| `hypothesis` | 이번 iteration의 과학적 가설 (자유 문자열) |
| `parameters` | n_backbone, mpnn_temperature, rosetta_ddg_max 등 |
| `gates` | esmfold_plddt_min=75, docking_top_pct=20, rosetta_ddg_max=−5.0 |
| `changes_from_prev` | "param: old → new (rationale)" 형식의 변경 이력 목록 |

**매 iteration 최대 2개 파라미터만 변경** — 원인-결과 추적 가능성(causal traceability) 확보 목적.

---

### 5.2 Scientist Critic — 결과 비평 (`AG_src/agents/critic.py`)

**역할**: QC&Ranker 결과를 분석하고 다음 iteration에서 바꿀 파라미터(최대 2개)를 제안한다.


#### Critic 사용자 프롬프트에 포함되는 데이터

- QC summary: total/passed/failed 수, pass_rate
- Gate-by-gate 결과 (rosetta_ddg, clash 분포)
- Rank table top-5: ddG 값

> **⚠️ 주의**: PyRosetta-only 모드에서 pLDDT=0.0, dock_score=0.0 고정이므로 Critic은 **ddG와 clash만** 실제로 분석한다. 프롬프트에 "top-5 pLDDT, dock_score" 필드가 있어도 모두 0.

#### 실패 유형 분류 및 PyRosetta-only 모드 실효성

| 코드 | 의미 | PyRosetta-only에서 실효성 |
|-----|------|------------------------|
| `high_clash` | 원자 충돌 과다 | ✅ 실효 있음 |
| `good_dock_bad_ddg` | 도킹 포즈는 좋은데 ddG 나쁨 | ⚠️ dock_score=0이므로 LLM 추론만 |
| `low_plddt` | ESMFold 신뢰도 낮음 | ❌ pLDDT=0 → 항상 오탐 가능 |
| `low_sequence_diversity` | 서열 다양성 부족 | ⚠️ LLM 추론만 (수치 없음) |
| `pocket_specific_failure` | 특정 포켓 결합 실패 | ⚠️ LLM 추론만 |
| `poor_selectivity` | 선택성 미달 | ❌ selectivity_margin=0 → 항상 오탐 |

#### Critic → Planner 파라미터 변경 매핑 (FAILURE_ACTION_MAP)

| 실패 유형 | 대응 파라미터 변경 |
|-----------|-----------------|
| `low_plddt` | mpnn_temperature 감소 또는 peptide_length_max 감소 |
| `good_dock_bad_ddg` | hotspot_res 업데이트 또는 rosetta_relax_cycles 증가 |
| `pocket_specific_failure` | contigs 변경 또는 docking_engine 토글 |
| `low_sequence_diversity` | mpnn_temperature 증가 또는 n_backbone 증가 |
| `high_clash` | rosetta_relax_cycles +5 |
| `poor_selectivity` | hotspot_residues 추가 또는 peptide_length_bias 증가 |

---

### 5.3 Reporter — 보고서 생성 (`AG_src/agents/reporter.py`)

**역할**: 각 iteration 종료 후 결과 보고서 작성 및 저장.

#### Reporter 출력 JSON 스키마

```json
{
  "title": str,
  "summary": str,           // 2-3 단락 과학적 기술
  "key_metrics": {
    "n_total", "n_passed",
    "best_pLDDT", "best_dock", "best_ddG", "selectivity_pass_rate"
  },
  "top_candidates": list,
  "recommendations": list
}
```

**저장 경로**: `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_{N:02d}/`
4-panel PyMOL 렌더 이미지도 생성 (`generate_pymol_renders()` 호출).

---

### 5.4 피드백 루프 흐름

```
[iteration N 시작]
  Planner
    ← 이전 iteration Critic 분석
    ← 과거 top-10 히트 서열 (experiment_log.jsonl)
    ← Thompson Sampling 밴딧 통계
    ← BO 제안 위치
    → mutation_guidance 생성
    
  FlexPepDock 도킹 (병렬 4 프로세스)
    → ddG, clash_score, total_score
    
  QCRankerAgent
    → Gate 3 (ddG ≤ -5.0, clash ≤ 10) 적용
    → ddg_primary 랭킹
    
  ScientistCritic
    → 실패 유형 분류 (ddG/clash 기반)
    → 파라미터 변경 제안 (최대 2개)
    → 다음 hypothesis 생성
    
  Reporter
    → Markdown + JSON 보고서 저장
    → PyMOL 렌더
    
  ConvergenceDetector
    → 수렴? → 종료 / 아니면 iteration N+1
```

**실제 데이터 흐름 (runner.py)**:
```
FlexPepDock → QCRanker → ScientistCritic → PlannerAgent (다음 iteration)
```

**LLM 모델 선택**: `LLM_MODEL` 환경변수 > `--llm-model` CLI > `pipeline_config.yaml` 순 우선순위. 현재 운영: Qwen3.5-27B (vLLM GPU 3, port 8002).

---

## 6. 수렴 판정 — Mann-Whitney U (`pyrosetta_flow/convergence.py`)

최적화가 더 이상 진전이 없을 때(plateau) 자동으로 탐색을 중단한다.

### 판정 기준

두 조건을 **동시** 만족해야 수렴으로 판정:

#### 조건 1: Mann-Whitney U 검정 p-value > 0.05

이전 윈도우(iteration k-2w ~ k-w)와 현재 윈도우(iteration k-w ~ k)의 top-k ddG 값 분포를 비교.

```
H₀: 두 분포가 같다 (= 개선이 없다)
p > significance_level(=0.05) → H₀ 채택 → "통계적으로 의미있는 개선 없음"
```

**계산**: scipy 없이 순수 Python으로 구현. n ≥ 8이면 정규 근사(연속성 보정), n < 8이면 p=1.0 반환(판정 불가).

#### 조건 2: 변동계수(CV) < 0.15

현재 윈도우 ddG 값의 변동계수:
```
CV = 표준편차 / |평균|
```
CV < 0.15 → 최근 결과가 15% 이내 변동 (안정됨)

#### 판정 로직

```python
converged = (p_value > 0.05) AND (cv < 0.15)
```

- 수렴 미달 시: 이유 출력 → 다음 iteration 계속
- 수렴 달성 시: `"Consider stopping."` 메시지 출력 → 파이프라인 종료 권고

**최소 필요 iteration**: 2 × window_size = 6회 (기본 window_size=3 기준).

---

## 7. 현재 이슈 및 한계

### 7.1 Cluster A~E에 후보가 거의 들어가지 않는 이유

**근본 원인**: Cluster 분류(`batch_classify`)는 약리학 프로퍼티와 FlexPepDock 결과가 **동일한 dict에 통합**되어 있어야 한다. 현재 파이프라인에서는:

- FlexPepDock 결과 (`ddg`, `clash_score`, `total_score`)는 `CandidateResult`에 저장
- 약리학 프로퍼티 (`pLDDT`, `selectivity_margin`, `instability_index`, `blosum62`, `gravy`, `net_charge_ph74`, `structural_rules`, `metal_coordination`, `protease_sites`)는 **별도 계산** 필요

**Cluster A** 실패 이유:
- `pLDDT`가 Silo B에서 0.0으로 설정됨 → `pLDDT_gte_75` 기준 항상 실패
- 해결: pLDDT 게이트 비활성화 또는 ESMFold로 사후 계산 필요

**Cluster D** 실패 이유:
- `gravy`, `net_charge_ph74`, `metal_coordination` 값이 candidate dict에 없으면 NaN → FAIL
- 해결: 약리학 계산 결과를 FlexPepDock 결과 dict에 merge하는 단계 추가 필요

**권고**: `runner.py`의 최종 후보 처리 단계에서 `PharmaProperties.calculate_all()` 호출 후 결과를 candidate dict에 병합한 뒤 `batch_classify()` 호출해야 함.

---

### 7.2 ADMET 계산 정확도 한계

현재 ADMET 계산(`backend/admet.py`)은 **서열 정보만** 사용하며, 다음 주요 한계를 가진다:

| 항목 | 현재 방법 | 실제 필요한 것 | 오차 수준 |
|-----|---------|-------------|---------|
| 분자량 | 단일동위원소 잔기 질량 합산 | MS 실측 또는 NIST 데이터 | ≤ 0.5 Da (허용) |
| 순전하 (pH 7.4) | K/R/D/E 정수 계산 | Henderson-Hasselbalch (전체 이온화) | ±0.5~1 charge unit |
| H-결합 수 | 사이드체인 + 백본 단순 합산 | 3D 구조 기반 접근성 보정 | 10~30% 과대계산 |
| 소수성 | KD 평균 (GRAVY) | 실측 logP 또는 HPLC retention time | 상관관계 r²≈0.7 |
| 약물성 점수 | 4개 규칙 25점 합산 | BBB 투과, CYP 대사, P-gp 기질 등 | 정성적 참고만 가능 |
| 신독성 점수 | (K+R)×20 + charge×15 경험식 | 실제 신세뇨관 재흡수 측정 | 극도로 단순화 |

**특히**: 현재 `net_charge_ph74` 계산이 Henderson-Hasselbalch를 사용하지 않고 정수 합산을 사용함 → `PharmaProperties.calculate_net_charge()`와 불일치. 서열에 His가 있을 경우 차이 발생 (His pKa=6.00이므로 pH 7.4에서 ~부분 하전).

---

### 7.3 피드백 기준의 적절성

**현재 Critic 피드백의 한계**:

1. **LLM 환각 위험**: Critic의 `structural_insights`는 LLM이 생성하므로 실제 구조 데이터 없이 추론한 것일 수 있음. PyMOL 렌더링(`generate_pymol_renders`)이 연동되어 있으나 이미지 분석은 미구현.

2. **파라미터 변경 범위 제한**: Critic은 최대 2개 파라미터만 변경 제안 → 복합적 실패 패턴에 과소 대응.

3. **Thompson Sampling 수렴 편향**: 특정 위치에서 운 좋게 좋은 결과가 나오면 해당 위치에 과다 집중 → 탐색 다양성 저하. 현재 diversity 목적함수가 Pareto에서 `0.0`으로 미계산 상태.

4. **selectivity_margin 미계산**: SSTR1~5 vs SSTR2 선택성을 계산하지 않아 Cluster B 기준 자동 실패. SSTR1~5 도킹 추가 필요.

5. **ddG 절대값 신뢰도**: FlexPepDock ddG는 제한된 sampling(1 trial)으로 계산되어 노이즈 크음. `validation_n_trials=1`이 기본값 — 논문 표준(10 trial)에 훨씬 못 미침.

6. **Critic이 pharma 메트릭을 미보유**: Critic은 ddG와 clash만 분석. Boman Index, Instability Index, GRAVY 등 약리학 메트릭은 피드백 루프에 전혀 포함되지 않음. `_candidate_to_qc()`에서 pharma 필드 추가 필요.

7. **FWKT 보존 검증이 QC 보고서에 없음**: mutation generation 단계에서 강제되나, QCReport에 `fwkt_conservation_rate` 기록 없어 추적 불가.

---

### 7.4 코드 버그 — rosetta_clash_max 불일치

**발견된 불일치**:

| 위치 | 값 |
|------|-----|
| `pyrosetta_flow/schema.py` FlowConfig | 10 |
| `AG_src/agents/planner.py` _DEFAULT_GATES | **0** ← 불일치 |
| `AG_src/agents/qc_ranker.py` apply_gates fallback | 10 |
| `runner.py` 실제 사용 | FlowConfig 값 10 (정상) |

`runner.py`는 FlowConfig.rosetta_clash_max=10을 직접 전달하므로 런타임 영향 없음.
그러나 Planner가 LLM에게 게이트 정보를 "clash_max=0"으로 전달할 수 있어 부정확한 가설 생성 위험.

**권고**: `planner.py` _DEFAULT_GATES의 `rosetta_clash_max`를 `10`으로 수정.

---

### 7.5 rosetta_ddg_max = -5.0 과학적 적절성

**현재 기준 평가**:
- SST-14↔SSTR2 결합 친화도: Kd ~0.1 nM (Kim et al. 1994) → 이론적 ΔΔG ≈ −13 kcal/mol 이상
- FlexPepDock 상대 스코어는 절대값 결합에너지와 직접 대응하지 않지만, 우수 바인더는 일반적으로 ddG −8 ~ −12 범위
- −5.0 기준은 **초기 탐색(iteration 1-2)에는 적절**하나 후기에는 너무 느슨함

**권고 조정 방향**:
- Iteration 1-2: −5.0 유지 (탐색 단계)
- Iteration 3+: −7.0 ~ −8.0으로 단계적 강화
- FlowConfig에 iteration-aware 조정 파라미터 (`rosetta_ddg_tightening_step: -1.0`) 추가 검토

---

## 참고: 주요 파일 위치

| 파일 | 역할 |
|-----|------|
| `pyrosetta_flow/runner.py` | 메인 파이프라인 루프 |
| `pyrosetta_flow/schema.py` | FlowConfig, CandidateResult 데이터 구조 |
| `pyrosetta_flow/adapter.py` | Mutation 생성, PyRosetta 인터페이스 |
| `pyrosetta_flow/bandit.py` | Thompson Sampling 밴딧 |
| `pyrosetta_flow/convergence.py` | Mann-Whitney U 수렴 판정 |
| `pyrosetta_flow/ranking.py` | JSONL 실험 기록 저장/로드 |
| `pyrosetta_flow/cluster_report.py` | A~E 클러스터 분류 |
| `pyrosetta_flow/gnina_rescoring.py` | GNINA CNN 재스코어링 |
| `pyrosetta_flow/pareto_ranking.py` | NSGA-II Pareto 다목적 순위 |
| `pyrosetta_flow/bayesian_optimizer.py` | GP 서로게이트 + BO 제안 |
| `AG_src/agents/qc_ranker.py` | QC 게이트 + 가중합 순위 |
| `AG_src/agents/planner.py` | LLM Planner 에이전트 |
| `AG_src/agents/critic.py` | LLM Scientist Critic 에이전트 |
| `AG_src/pipeline/pharma_properties.py` | 15 약리학 프로퍼티 계산 |
| `backend/admet.py` | ADMET + 신독성 위험 계산 |
| `backend/routers/admet.py` | REST API 엔드포인트 |
| `AG_src/scripts/flexpep_dock.py` | PyRosetta FlexPepDock 실행 스크립트 |
