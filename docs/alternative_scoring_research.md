# Alternative Scoring Methods — 심층 기술 조사 보고서

> **작성일**: 2026-03-10
> **목적**: NSGA-II, GNINA, ESM-2, Bayesian Optimization 4가지 방법론의 이론적 배경, 벤치마크, 적용 사례 심층 조사
> **관련 문서**: [alternative_scoring_design.md](alternative_scoring_design.md) (구현 설계서)
> **대상 시스템**: SSTR2 AI Co-Scientist — Silo B Pipeline (SST-14 유사체 14-residue cyclic peptide)

---

## 목차

1. [NSGA-II Pareto Ranking](#1-nsga-ii-pareto-ranking)
2. [GNINA CNN Rescoring](#2-gnina-cnn-rescoring)
3. [ESM-2 Pseudo-perplexity](#3-esm-2-pseudo-perplexity)
4. [Bayesian Optimization](#4-bayesian-optimization)
5. [방법론 간 통합 전략](#5-방법론-간-통합-전략)
6. [참고문헌](#6-참고문헌)

---

## 1. NSGA-II Pareto Ranking

### 1.1 알고리즘 상세 (Deb et al., 2002)

NSGA-II(Non-dominated Sorting Genetic Algorithm II)는 초기 NSGA의 세 가지 비판점을 해결하기 위해 개발되었다:
- **O(mN³) → O(mN²)** 시간 복잡도 개선
- **엘리티즘(elitism)** 도입 — 부모+자식 합집합(2N)에서 N개 선택
- **공유 파라미터(sharing parameter) 제거** — crowding distance로 대체

#### Non-Dominated Sorting

1. 각 해(solution)에 대해 지배하는 해의 수(domination count)와 지배당하는 해 목록을 계산
2. Domination count = 0인 해들을 첫 번째 front(F₁)에 배정
3. F₁의 각 해가 지배하는 해들의 domination count를 1씩 감소, 0이 되면 F₂에 배정
4. 모든 해가 front에 배정될 때까지 반복

**시간 복잡도**: O(mN²) — m: 목적 함수 수, N: 인구 크기

#### Crowding Distance 계산

```
CD(i) = Σ_m (f_m(i+1) - f_m(i-1)) / (f_m_max - f_m_min)
```

- 각 front 내에서 각 목적 함수별로 해를 정렬
- 경계 해(최대/최소값): crowding distance = **무한대** (매 세대 보존 보장)
- 중간 해: 인접 두 해의 목적 함수값 차이를 정규화하여 합산
- 본질적으로 목적 공간에서의 **맨해튼 거리(Manhattan Distance)** 기반
- **시간 복잡도**: O(m|F| log |F|) — 정렬 비용이 지배

#### Crowded Comparison Operator

선택 시: front rank가 낮을수록 우선 → 같은 front 내에서는 crowding distance가 클수록 우선

### 1.2 NSGA-II vs NSGA-III 비교

NSGA-III(Deb & Jain, 2014)는 **균일하게 분포된 reference point(방향 벡터)**를 사용하여 다양성을 유지한다. Crowding distance를 사용하지 않으며, 고차원 Pareto front에서 거리 기반 다양성 유지가 비효과적인 문제를 해결한다.

| 항목 | NSGA-II | NSGA-III |
|------|---------|----------|
| 다양성 유지 | Crowding distance | Reference point |
| 2-3 objectives | **우수** | 유사/약간 우수 |
| 4-5 objectives | 성능 저하 | **약간 우수** |
| DTLZ1-4 벤치마크 | 열등 | **우수** |
| 조합 최적화 | **우수** | 열등 |
| 비볼록 Pareto front | 문제 의존 | 문제 의존 |

**본 프로젝트 시사점**: 4개 objective(ddG, stability, druggability, diversity) → NSGA-II로 시작하되, NSGA-III로 업그레이드 경로 확보

### 1.3 Crowding Distance의 한계와 대안

| 지표 | 설명 | 장단점 |
|------|------|--------|
| **Hypervolume (HV)** | Pareto front이 지배하는 목적 공간의 부피 | 유일하게 strict monotonicity 보장. 계산 비용 높음 (#P-hard) |
| **IGD** | 참 Pareto front에서 근사 front까지 평균 거리 | HV 대비 저렴, 참 front 필요 |
| **IGD+** | IGD의 Pareto 지배 일관성 보완 | 이론적으로 IGD보다 우수 |
| **ε-dominance** | ε 범위 내 지배를 허용 | Borg MOEA 등에서 아카이빙에 활용, 계산 저렴 |

### 1.4 Knee Point Detection 알고리즘

| 방법 | 저자 | 핵심 아이디어 | 장단점 |
|------|------|-------------|--------|
| NBI 기반 | Das (1999) | 법선 방향 최대 거리 점 = knee | 기하학적 명확, 고차원 확장 어려움 |
| Marginal Utility | Branke et al. (2004) | 가장 넓은 가중치 범위에서 최적인 해 | 의사결정 이론 기반, 효용 함수 가정 필요 |
| **Kneedle** | Satopaa et al. (2011) | 곡률 기반 자동 탐지 | **자동화 용이, 구현 간단**. 노이즈에 민감 |
| Angle-based | — | 인접 해 벡터의 각도 변화 | 다목적 확장 용이, 계산 비용 증가 |

**권장**: Kneedle 알고리즘 — HMAMP(2025, J. Med. Chem.)에서 항균 펩타이드 Pareto front의 knee point 자동 식별에 성공적으로 활용됨

### 1.5 Drug Discovery에서의 Pareto 최적화 사례

| 연구 | 연도 | 방법 | 적용 대상 |
|------|------|------|----------|
| Graph-based Molecular Pareto Opt. | 2022 | NSGA-II/III | 분자 그래프 기반 다목적 설계 |
| MOMO | 2024 | Pareto + 진화 탐색 | 암묵적 화학 공간 분자 최적화 |
| Pareto MCTS | 2025 | MC Tree Search + Pareto | SMILES 기반 고차원 최적화 |
| **HMAMP** | 2025 | **HV + Kneedle** | **항균 펩타이드 설계** — 가장 유사한 사례 |
| PepZOO | 2024 | Zeroth-order MOO | 항균 펩타이드 (기능+활성+독성+친화도) |

### 1.6 Pareto Front에서 최종 후보 선택 전략

일반적 **2단계 프로세스**: MOEA로 Pareto front 생성 → MCDM으로 최종 후보 순위 매김

| 방법 | 특징 |
|------|------|
| **TOPSIS** | PIS에 가장 가깝고 NIS에 가장 먼 해 선택 (Hwang & Yoon, 1981) |
| **Weighted TOPSIS** | 도메인 전문가 선호도 반영 가능 |
| **Knee Point** | 한 목적의 소량 개선 = 다른 목적의 대폭 악화인 지점. **선호 정보 없을 때 최적** |
| **ELECTRE** | 우월성/열등성 관계 기반 순위 매김 |

### 1.7 Weighted Sum vs Pareto Ranking — 실증 비교

| 측면 | Weighted Sum | Pareto Ranking |
|------|-------------|----------------|
| 비볼록 Pareto front | **탐색 불가** (볼록 영역만 발견) | 완전 탐색 가능 |
| 선호 정보 | 사전 가중치 설정 필수 | **사후 결정 가능** |
| 해의 분포 | 불균일 (가중치 변화에 불균등 반응) | **균일 분포 가능** |
| 계산 비용 | 단일 실행 저렴 | 전체 front 탐색에 더 많은 평가 필요 |
| 정보량 | 단일 해 | **전체 trade-off 구조 파악** |

> 2025년 GuacaMol 벤치마크 연구: 기본적 Pareto 전략이 scalarization을 **데이터 제약 분자 발견 시나리오에서 능가**

### 1.8 Many-Objective 시각화

4+ objective의 Pareto front은 직접 시각화 불가. 주요 기법:

| 기법 | 설명 | pymoo 지원 |
|------|------|-----------|
| **Parallel Coordinates Plot** | m개 평행 축에 각 해를 다각선으로 표현. 가장 널리 사용 | **지원** |
| Radar/Spider Chart | 방사형 배치. 직관적이나 축 수 증가 시 가독성 저하 | 지원 |
| Heatmap | 해 × 목적 행렬 시각화 | 지원 |
| t-SNE/PCA 투영 | 차원 축소 후 2D/3D | 외부 라이브러리 |

### 1.9 pymoo 라이브러리

- **최신 버전**: 0.6.1.6 (Apache 2.0)
- **개발**: Julian Blank, Kalyanmoy Deb (Michigan State University)
- **핵심 아키텍처**: Problem / Algorithm / Termination
- **지원 알고리즘**: NSGA-II, NSGA-III, R-NSGA-III, MOEA/D, SMS-EMOA, CTAEA
- **Mixed Variable**: Integer/Choice 타입으로 아미노산 서열 + Real 타입으로 물성 동시 최적화 가능
- **성능 지표 내장**: HV, IGD, IGD+, GD
- **병렬화**: starmap, dask 지원

---

## 2. GNINA CNN Rescoring

### 2.1 개요

**GNINA**(발음: NEE-na)는 David Ryan Koes 연구그룹(University of Pittsburgh)이 개발한 오픈소스 분자 도킹 소프트웨어로, AutoDock Vina → smina → GNINA 계보의 fork이다.

| 버전 | 연도 | 주요 변경 |
|------|------|----------|
| 1.0 | 2021 | CNN scoring function 앙상블 도입 (Caffe 기반) |
| 1.1 | — | 안정성 개선, Docker 이미지 |
| **1.3** | **2025.03** | **PyTorch 전환**, covalent docking, CrossDocked2020 v1.3, knowledge distillation |

핵심 논문:
- McNutt et al. (2021) "GNINA 1.0: molecular docking with deep learning", *J. Cheminformatics* 13, 43
- McNutt et al. (2025) "GNINA 1.3: the next increment", *J. Cheminformatics*

### 2.2 CNN 아키텍처 및 모델 종류

#### 입력 표현
원자 좌표의 **3D 격자 기반(grid-based) 표현**에 CNN을 적용. 각 원자 유형별 채널로 복셀화하여 3D CNN에 입력.

#### 내장 모델

| 모델명 | 아키텍처 | 학습 데이터 | 특징 |
|--------|---------|-----------|------|
| default2018 | Default2018 | PDBbind General v2016 | 기본 |
| **dense** | Dense (더 큰 모델) | **CrossDocked2020** | 가장 큰 모델+데이터 조합 |
| crossdock_default2018 | Default2018 | CrossDocked2020 | cross-docking 최적화 |
| redock_default2018 | Default2018 | ReDocked2020 | redocking 최적화 |

#### 앙상블 구성

**GNINA 1.0 Default** (5개 모델): dense, general_default2018_3, dense_3, crossdock_default2018, redock_default2018

**GNINA 1.3 Default** (3개 모델): dense_1_3, dense_1_3_PT_KD_3, crossdock_default2018_KD_4 — CrossDocked2020 v1.3 재학습, Knowledge Distillation 적용

**GNINA 1.3 Fast** (`--cnn=fast`): KD로 압축한 단일 모델 — 대량 스크리닝용

#### 학습 데이터셋

- **PDBbind**: 실험적 결합 친화도 보유 단백질-리간드 복합체
- **CrossDocked2020**: 유사 결합 포켓에 cross-dock한 **2,250만 개 pose** — v1.3에서 정렬/타입 오류 수정
- **ReDocked2020**: 동일 수용체 redock 데이터

### 2.3 세 가지 점수의 의미와 해석

| 점수 | 범위/단위 | 의미 | 해석 |
|------|----------|------|------|
| **CNNscore** | 0.0 ~ 1.0 (무차원) | RMSD ≤ 2Å일 확률 (이진 분류) | **높을수록 좋은 pose** |
| **CNNaffinity** | pK 단위 (−log Kd) | CNN 예측 결합 친화도 | **높을수록 강한 결합** (예: 8.0 ≈ Kd ~10nM) |
| **Vina Affinity** | kcal/mol | Vina 경험적 scoring function | **더 음수일수록 강한 결합** |

- 기본 파이프라인: **Vina scoring으로 MCMC 샘플링** → **CNN rescore**로 최종 pose 선택
- CNNscore와 Vina score 간 **불일치가 흔함** — 서로 다른 scoring function이므로 consensus 가치 있음
- CNNaffinity는 **상대적 순위**에 더 유용, 절대값 정확도는 제한적

### 2.4 성능 벤치마크

#### GNINA 1.0 (McNutt et al., 2021)

| 태스크 | Vina Top1 | GNINA CNN Top1 | 개선폭 |
|--------|-----------|----------------|--------|
| Redocking (pocket) | 58% | **73%** | +15%p |
| Cross-docking (pocket) | 27% | **37%** | +10%p |
| Redocking (whole protein) | 31% | **38%** | +7%p |
| Cross-docking (whole protein) | 12% | **16%** | +4%p |

#### GNINA 1.3 (2025)

| 항목 | GNINA 1.0 | GNINA 1.3 |
|------|-----------|-----------|
| Cross-docking Top1 | 37% | **40%** |
| CPU-only 시간 | 30s | **23s** (Default), **16s** (Fast) |

#### Macrocyclic Ligand 성능
- 일반 temporal set: ~60%
- **Macrocycle set: ~35%** — 대형 고리형 리간드에서 상당한 성능 저하

### 2.5 Peptide Docking 적용 현황

GNINA는 **small molecule docking** 목적으로 설계/벤치마킹되었으며, peptide-protein 복합체에 대한 공식 대규모 벤치마크는 없다.

관련 연구:
- **InterPepScore** (Johansson-Akhe & Wallner, 2022): FlexPepDock + GNN rescoring으로 peptide docking 품질 14.8% → 26.1% 개선 — CNN/DL rescoring이 펩타이드에도 효과적임을 시사
- **Macrocyclic ligand study** (2024): GNINA의 macrocycle 성공률 ~35% (일반 ~60%)

### 2.6 FlexPepDock과의 상호 보완성

| 항목 | GNINA | FlexPepDock |
|------|-------|------------|
| 설계 목적 | Small molecule (범용) | **Peptide-protein (전문)** |
| Scoring function | CNN 앙상블 (3D grid + DL) | Rosetta score12 (물리 기반 + 통계적 포텐셜) |
| 에너지 단위 | kcal/mol (Vina) + 무차원 (CNN) | REU (Rosetta Energy Units) |
| 유연성 | 리간드만 유연 (수용체 rigid) | **펩타이드 + 수용체 side-chain 모두 유연** |
| Ab-initio | 불가 | **가능** |
| 속도 | ~16-30초/complex | ~70초/trial (다수 trial 필요) |

**최적 파이프라인**: FlexPepDock으로 pose 생성 → GNINA `--score_only`로 CNN rescoring → consensus scoring

### 2.7 Score-only Mode 상세

```bash
gnina -r receptor.pdb -l ligand.sdf --autobox_ligand ligand.sdf --score_only
```

- 도킹(샘플링)을 수행하지 않고, 입력 pose에 대해 점수만 산출
- **지원 입력**: Receptor: PDB, PDBQT / Ligand: SDF, MOL2, PDB, PDBQT, SMILES

### 2.8 14-Residue Cyclic Peptide 적용 시 한계

1. **Torsional complexity**: 환형 펩타이드의 회전 가능 결합 수 ≫ tractable 한계(~21-23개)
2. **학습 데이터 편향**: CrossDocked2020은 drug-like small molecule (MW < 500) 중심. 14-residue 펩타이드 (MW ~1,600+)는 학습 분포 밖
3. **환형 구조**: 여러 torsional angle의 협동적 움직임(concerted motion) 필요
4. **Grid resolution**: 대형 리간드는 grid box 증가 → 해상도 감소 또는 계산 비용 증가

**결론**: GNINA를 **de novo docking에 사용하는 것은 부적합** → **rescoring 전용**으로 활용

### 2.9 Consensus Scoring 문헌

#### Exponential Consensus Ranking (ECR)
- Palacio-Rodriguez et al. (2019), *Scientific Reports* 9, 5142
- 각 프로그램의 분자 순위에 대한 **지수 분포 합**으로 조합
- **순위 기반(rank-based)** — 점수 단위/스케일/오프셋에 독립적
- 전통적 consensus보다 광범위한 시스템에서 우수

```
ECR(i) = Σ_k exp(-rank_k(i) / (τ × N))
```

#### Reciprocal Rank Fusion (RRF)
- 정보 검색(IR) 분야 유래
- `score(d) = Σ 1/(k + rank_i(d))` (k=60 보통)
- 구현 간단, 상위 1% cutoff 적용 권장

#### 기타 방법

| 방법 | 설명 |
|------|------|
| Rank-by-Rank | 각 프로그램 순위 평균 |
| Rank-by-Vote | 모든 프로그램에서 상위 N%에 든 분자 |
| Z-score | 점수 표준화 후 합산 |
| CompScore (2019) | 개별 SF 구성 요소를 ML 모델에 입력 |

### 2.10 설치 환경

| 방법 | 상세 |
|------|------|
| **Pre-built binary** | GitHub Releases — Linux 바이너리 (권장) |
| **Conda** | `conda install --channel gnina gnina` (**gnina 전용 채널**, conda-forge 아님) |
| **Docker** | `docker pull gnina/gnina:latest` |
| 소스 빌드 | CMake + make, 상당한 빌드 경험 필요 |

- **OS**: Linux 전용 (macOS/Windows 미지원)
- **CUDA**: ≥ 12.0 (v1.3), GPU 가속 지원, CPU-only 가능하나 느림
- **OpenBabel**: 3.1.1+ 필요

---

## 3. ESM-2 Pseudo-perplexity

### 3.1 ESM-2 모델 상세 (Lin et al., Science 2023)

"Evolutionary-scale prediction of atomic-level protein structure with a language model"
— Meta AI / FAIR

#### 모델 크기별 아키텍처

| 모델 | 파라미터 | 레이어 | 임베딩 차원 | 어텐션 헤드 |
|------|---------|--------|------------|------------|
| ESM-2 8M | 8M | 6 | 320 | 20 |
| ESM-2 35M | 35M | 12 | 480 | 20 |
| ESM-2 150M | 150M | 30 | 640 | 20 |
| **ESM-2 650M** | **650M** | **33** | **1280** | **20** |
| ESM-2 3B | 3B | 36 | 2560 | 40 |
| ESM-2 15B | 15B | 48 | 5120 | 40 |

#### 학습 데이터
- **UniRef50**: ~43M 클러스터에서 균일 샘플링
- **UniRef90**: ~138M 서열, UniRef50 클러스터 내 UniRef90 서열을 무작위 대체하여 다양성 확보
- 총 ~65M 고유 서열에 노출 (실제 학습 서열: 187M개)
- **마스킹 전략**: BERT 표준 — 15% 토큰 (80% [MASK], 10% 랜덤, 10% 유지)

#### 모델 크기별 성능
- **650M급 중형 모델**이 대형 모델(15B, 6B)에 비해 약간만 뒤처지면서 일관되게 우수
- 8M, 35M만 유의미하게 성능 저하
- **실용적 권장**: ESM-2 650M이 성능/비용 트레이드오프에서 최적

### 3.2 Masked Marginal Scoring 이론 (Meier et al., NeurIPS 2021)

"Language models enable zero-shot prediction of the effects of mutations on protein function"

#### 핵심 수식

변이 효과 점수:
```
Score(mutant) = Σᵢ [log P(xᵢ_mut | x₋ᵢ) - log P(xᵢ_wt | x₋ᵢ)]
```

Pseudo-log-likelihood (PLL):
```
PLL(x) = Σᵢ log P(xᵢ | x₋ᵢ)
Pseudo-perplexity = exp(-PLL / L)
```

#### 세 가지 스코어링 전략

| 전략 | 방법 | Forward passes | 성능 |
|------|------|---------------|------|
| Wildtype marginal | 야생형 입력, 변이 확률 계산 | 1 | 보통 |
| **Masked marginal** | 변이 위치 마스킹, 조건부 확률 | **1** (동시 마스킹) | **최선** |
| Pseudolikelihood | 모든 위치 순차 마스킹 | L회 | 좋음 |

**Masked marginal이 최선인 이유**: 변이 위치 정보를 가린 상태에서 예측 → 야생형 편향(bias) 제거

### 3.3 DMS 벤치마크 (ProteinGym)

- **구성**: Activity, Binding, Expression, Organismal Fitness, Stability 등 DMS 실험 데이터 집대성
- **평가 지표**: Spearman rank correlation

#### One Fell Swoop (OFS) 방법 (2024)
- 마스킹 없이 **단일 forward pass**로 pseudo-perplexity 근사
- **ProteinGym Indels 벤치마크에서 새로운 SOTA**
- L회 forward pass 대비 L배 빠름

#### 치환 vs 삽입/결실
- **치환(substitution)**: masked marginal 선호
- **삽입/결실(indel)**: pseudo-perplexity (OFS) 우수
- 두 방법 모두 zero-shot으로 supervised 모델에 근접

### 3.4 짧은 펩타이드(14aa)에서의 한계

1. **학습 데이터 편향**: ESM-2는 수백~수천 aa 단백질로 학습. 14aa는 학습 분포의 꼬리(tail)
2. **컨텍스트 부족**: 14개 토큰은 장거리 의존성 학습에 불충분
3. **Cyclic peptide 미지원**: ESM-2 토크나이저는 20개 표준 아미노산만 처리. **Cys3-Cys14 이황화 결합 고리 구조를 직접 인코딩 불가**
4. **비천연 아미노산 미지원**: D-amino acid 등

#### 대안적 접근
- **Cycle-ESM**: ESM-2를 cyclic peptide에 fine-tuning (항진균 펩타이드 분류 사례)
- **GNN 결합**: 고리형 구조를 그래프로 표현하여 보완
- **실용적**: 절대값보다 **변이 간 상대적 순위(ranking)**에 초점 권장

### 3.5 ESM-2 vs ESM-IF1 비교

| 항목 | ESM-2 (Sequence-only) | ESM-IF1 (Structure-conditioned) |
|------|----------------------|-------------------------------|
| 입력 | 아미노산 서열만 | 백본 3D 구조 (좌표) |
| 학습 데이터 | UniRef50/90 (~65M 서열) | AlphaFold2 예측 구조 12M개 |
| DMS 벤치마크 | 10개 중 2개 top 5% 식별 | **10개 중 9개 top 5% 식별** |
| 구조 필요 | **불필요** (가장 큰 장점) | 필수 |

**하이브리드 전략**: ESM-2로 초기 스크리닝 → ESMFold 구조 예측 → ESM-IF1 정밀 재스코어링

### 3.6 Position-wise Log Probability 해석

```
log P(xᵢ | x₋ᵢ) = log softmax(logitsᵢ)[xᵢ]
```

| log P 값 | 의미 |
|----------|------|
| **높음** | 진화적으로 **강하게 보존** — 기능/구조 필수 잔기 |
| **낮음** | **변이 허용적(tolerant)** — 진화적 다양성 관찰 |

ESM-2가 포착하는 정보:
- **공진화(coevolution)**: 상호작용 잔기 쌍의 공동 변이 패턴
- **Position-Specific Probability Matrix**: MSA 기반 PSSM과 유사하지만, **단일 서열로부터 추론**
- Conservation score (Shannon entropy, Rate4Site)와 높은 상관관계

#### Log-Likelihood Ratio (LLR) 활용
```
LLR(i, mut) = log P(mut_i | x₋ᵢ) - log P(wt_i | x₋ᵢ)
```
- LLR > 0: 변이가 야생형보다 "자연스러움" (유리한 변이)
- LLR < 0: 변이가 "부자연스러움" (해로운 변이 가능성)

### 3.7 방사성의약품 맥락: FWKT Pharmacophore와 Log Probability

**FWKT (F7-W8-K9-T10)** 위치의 log prob이 높아야 하는 이유:

1. **진화적 보존 = 기능적 필수성**: 5개 소마토스타틴 수용체 아형 모두에서 보존된 pharmacophore
2. **구조적 제약**: β-turn 형성에 특정 phi/psi 각도와 측쇄 상호작용 필수
3. **방사성의약품 특수 요건**:
   - 68Ga/177Lu/225Ac 킬레이터(DOTA, NOTA)가 N-말단 부착
   - Pharmacophore 변이 = 수용체 결합력 상실 = 방사성의약품 가치 소멸
   - **FWKT position log prob 높은 후보 = 기능 보존 가능성 높음**

**실용적 활용**:
- 22,000 후보의 FWKT 위치 4개 평균 log prob 계산
- FWKT log prob 낮은 후보 → pharmacophore 파괴 위험 → **조기 필터링**
- 비-pharmacophore 위치(1-6, 11-14)의 log prob 변화 → 허용 가능한 변이 공간 탐색

---

## 4. Bayesian Optimization

### 4.1 BoTorch/GPyTorch 상세

**BoTorch**: Meta AI 개발, PyTorch 기반 Bayesian Optimization 프레임워크 (NeurIPS 2020)

#### SingleTaskGP
- 기본 GP 모델: Matérn 5/2 커널 + ARD (Automatic Relevance Determination)
- 관측 노이즈 추정 지원

#### Acquisition Functions

| AF | 수식 | 특성 |
|----|------|------|
| **EI** | E[max(f(x) - f*, 0)] | 보수적 (exploitation 경향) |
| **UCB** | μ(x) + β·σ(x) | β로 탐색/활용 균형 조절 |
| **KG** | 1회 관측 후 최적값 기대 개선 | 이론적 최적, 계산 비용 높음 |
| **qNEHVI** | 다목적 배치 EHVI | **Pareto HV 개선 기대값 — 다목적 최적화용** |

### 4.2 Protein/Peptide 설계에서의 BO 적용 — Wet-lab 검증 사례

| 연구 | 연도 | 방법 | 결과 | 의의 |
|------|------|------|------|------|
| **LaMBO** | 2022 (ICML) | DAE + Multi-task GP | NSGA-2, MTGP+GA 대비 우수 | 형광 단백질 in silico+vitro |
| **BO-EVO** | 2023 | BO + 로봇 실험 | Protein G, PhoQ kinase 최적화 | **로봇 wet-lab 검증** |
| **ALDE** | 2025 | 불확실성 기반 능동 학습 | **3회 wet-lab으로 수율 12%→93%** | **가장 인상적인 검증** |
| **BOES** | 2025 | ESM-2 embedding + GP + EI | pLM+BO 성공적 결합 | **최초 pLM embedding + BO** |
| DMT Loop | — | AF2 구조 + BO | 4-5 사이클 내 μM→최적 결합력 | 펩타이드 특화 |

### 4.3 GP Surrogate 한계와 Sparse GP 대안

#### O(N³) 스케일링 문제
- 정확한 GP: Cholesky 분해 → O(N³) 계산, O(N²) 저장
- N=10,000 이상에서 비실용적
- **Silo B 22,000 후보에 정확한 GP는 비현실적**

#### Sparse GP 대안

| 방법 | 복잡도 | 핵심 아이디어 |
|------|--------|-------------|
| **SVGP** | O(NM²) | M개 유도점(inducing points) 저차원 근사, 변분추론 |
| **KISS-GP** | O(N + M log M) | 균등 격자 유도점, Toeplitz/Kronecker 구조 |
| **LOVE** | 예측 가속 | KISS-GP 결합 시 예측 분포 대폭 가속 |

**실용적 권장**: ESM-2 임베딩(1280D) → PCA(50-100D) → SVGP (500-1000 inducing points)

### 4.4 ESM-2 Embedding + GP 조합

```
서열 → ESM-2 인코더 → 1280D 임베딩 → PCA(50D) → GP surrogate → AF → 다음 후보 제안
```

**장점**:
- 진화적/구조적 정보가 임베딩에 내재 — 수작업 특성 공학 불필요
- GP가 예측 불확실성 자연 제공 → BO 탐색/활용 균형 필수
- 소수 데이터로도 의미 있는 surrogate 구축 (data-efficient)
- ESM-2 pseudo-perplexity로 초기 surrogate 웜스타트 가능

**단점**:
- 1280D 고차원 → GP 커널 거리 계산 비효율 → PCA 필수
- 임베딩 고정 vs 미세조정 트레이드오프
- GP 커널(Matérn, RBF)이 복잡한 비선형 관계 포착 한계 → Deep Kernel Learning(DKL) 고려

### 4.5 Thompson Sampling과 GP-TS

| 측면 | 현재 Thompson Sampling | GP-TS |
|------|----------------------|-------|
| 모델 | 위치별 독립 Beta(α,β) | 서열 전체 GP posterior |
| 상관구조 | 위치 간 독립 가정 | ESM-2 embedding으로 위치 간 상관 학습 |
| 탐색/활용 | Beta 분포 샘플링 | GP posterior에서 함수 샘플링 |
| 배치 병렬화 | 독립 샘플 | 자연스러운 배치 확장 (각 샘플 독립) |
| 계산 비용 | O(1) per position | O(N³) GP fitting + ESM-2 forward |
| 적합 단계 | **초기 탐색** (빠른 위치 선별) | **후기 정밀 최적화** (top-100 이후) |

### 4.6 Multi-objective BO

| 방법 | 핵심 | 장점 | 단점 |
|------|------|------|------|
| **ParEGO** | 랜덤 스칼라화 + EI | 간단, >5 목적 확장 | 비볼록 front 탐색 어려움 |
| **EHVI** | HV 개선 기대값 | 이론적 최적, 균등 탐색 | 목적 수 ↑ → 계산 비용 폭증 |
| **qNEHVI** | Noisy EHVI + 배치 | **노이즈+다목적+병렬** | 높은 계산 비용 |
| **MESMO** | 엔트로피 기반 정보 이득 | Pareto 집합 정보 최대화 | 구현 복잡 |

> 2025년 연구: EHVI가 스칼라화 EI 대비 일관되게 우수 — Pareto front 커버리지, 수렴 속도, 화학적 다양성 모두

**SST-14 프로젝트 적용**: qNEHVI 최적 — 노이즈 있는 FlexPepDock + 다수 목적 + 배치 실험

---

## 5. 방법론 간 통합 전략

### 5.1 전체 파이프라인

```
[Phase 1: 탐색]
  Thompson Sampling Bandit → 위치별 변이 탐색
  ESM-2 PLL → pharmacophore 보존 필터링 (FWKT log prob)
      ↓
[Phase 2: 평가]
  FlexPepDock → pose 생성 + ddG
  GNINA --score_only → CNN rescoring (CNNscore, CNNaffinity)
  13 Pharmacological metrics + ESM-2 Δperplexity
      ↓
[Phase 3: 순위 매김]
  NSGA-II Pareto Ranking → 4 objectives (ddG, stability, ESM-2, GNINA)
  ECR Consensus → FlexPepDock + GNINA rank 통합
      ↓
[Phase 4: 최적화 (iteration 4+)]
  GP-BO (ESM-2 embedding + PCA + qNEHVI)
  → 다음 iteration 후보 제안 (FlexPepDock 호출 10x 절감)
      ↓
[Phase 5: 최종 선택]
  Pareto front → Knee point (Kneedle) or TOPSIS
  → Top-5 최종 후보
```

### 5.2 방사성의약품 다목적 최적화 대상

| 목적 | 측정 방법 | 충돌 관계 |
|------|-----------|-----------|
| SSTR2 결합 친화도 | FlexPepDock ddG + GNINA CNNaffinity | 소수성 ↑ → 용해도 ↓ |
| 서열 자연스러움 | ESM-2 Δ pseudo-perplexity | 급진적 변이 → 결합력 ↑ 가능하나 자연스러움 ↓ |
| 대사 안정성 | Instability Index, 프로테아제 예측 | D-aa/cyclization → 합성 난이도 ↑ |
| 약동학 | ClogP, TPSA, MW | 체내 분포 vs 결합력 |
| 킬레이터 호환성 | N-term DOTA/NOTA 부착 가능성 | N-term 변형 → 결합력 변화 |

### 5.3 구현 우선순위 (최종 권장)

| 순위 | 방법 | 이유 |
|------|------|------|
| **1** | **NSGA-II Pareto** | 추가 모델 불필요, 기존 scoring.py 직접 대체, pymoo 성숙도 높음 |
| **2** | **GNINA Rescoring** | PDB 이미 존재, CLI 래퍼만 작성, consensus scoring으로 ddG 보완 |
| **3** | **ESM-2 PLL** | 서열 기반이라 PDB 불필요, FWKT 필터링에 즉시 유용 |
| **4** | **GP-BO** | Phase 2용, ESM-2 + NSGA-II 완료 후 진행 |

---

## 6. 참고문헌

### NSGA-II / Multi-objective Optimization
- Deb et al. (2002) "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II", *IEEE Trans. Evolutionary Computation*
- Deb & Jain (2014) "An Evolutionary Many-Objective Optimization Algorithm Using Reference-Point-Based Nondominated Sorting Approach", *IEEE Trans. EC*
- Blank & Deb (2020) "pymoo: Multi-Objective Optimization in Python", *IEEE Access*
- Satopaa et al. (2011) "Finding a Kneedle in a Haystack", *ICDCSW*
- Branke et al. (2004) "Finding Knees in Multi-objective Optimization"
- Das (1999) "Normal-Boundary Intersection: A New Method for Generating the Pareto Surface"

### GNINA
- McNutt et al. (2021) "GNINA 1.0: molecular docking with deep learning", *J. Cheminformatics* 13, 43
- McNutt et al. (2025) "GNINA 1.3: the next increment in molecular docking with deep learning", *J. Cheminformatics*
- Palacio-Rodriguez et al. (2019) "Exponential consensus ranking improves the outcome in docking", *Scientific Reports* 9, 5142

### ESM-2
- Lin et al. (2023) "Evolutionary-scale prediction of atomic-level protein structure with a language model", *Science*
- Meier et al. (2021) "Language models enable zero-shot prediction of mutations on protein function", *NeurIPS*
- Johansson-Akhe & Wallner (2022) "InterPepScore: peptide-protein docking scoring", *Bioinformatics*

### Bayesian Optimization
- Stanton et al. (2022) "Accelerating Bayesian Optimization for Biological Sequence Design with Denoising Autoencoders" (LaMBO), *ICML*
- Balandat et al. (2020) "BoTorch: A Framework for Efficient Monte-Carlo Bayesian Optimization", *NeurIPS*

### Peptide Design with Multi-objective Optimization
- HMAMP (2025) "Hypervolume-Driven Multi-Objective Antimicrobial Peptide Design", *J. Med. Chem.*
- PepZOO (2024) "Multi-objective Zeroth-order Optimization for AMP", *Briefings in Bioinformatics*
- Pareto MCTS (2025) *Advanced Science*
- ALDE (2025) "Active Learning-Assisted Directed Evolution", *Nature Communications*
