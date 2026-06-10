# Peptide Binder Screening 전략 비교: Dock-then-Design vs Mutate-then-Dock

> **대상 시스템**: SSTR2 (Somatostatin Receptor 2, 369 res) + SST14 (Somatostatin-14, 14 res)
> **실험 코드**: `notebooks/comparison_fastdesign_vs_dock.ipynb`
> **실험 일자**: 2026-02-13
> **환경**: bio-tools conda env, PyRosetta 3.12, NVIDIA RTX 4090

---

## 1. 요약 (Executive Summary)

두 가지 펩타이드 바인더 설계 파이프라인을 **동일한 출발점과 스코어링 기준**에서 비교한 결과:

| 차원 | Approach A (Dock→Design) | Approach B (Mutate→Dock) |
|------|--------------------------|--------------------------|
| **결합 에너지 (dG)** | **-54.5 REU** (우수) | -33.6 REU |
| **매몰 표면적 (dSASA)** | **2114.8 Å²** (우수) | 1944.3 Å² |
| **후보당 시간** | 141.7s (느림) | **15.0s** (9.4x 빠름) |
| **서열 다양성** | 평균 거리 10.7 | 평균 거리 4.0 |
| **스크리닝 적합성** | 정밀 최적화에 적합 | **대량 탐색에 적합** |

**핵심 결론**: 두 접근법은 상호 보완적이며, **B로 대량 탐색 → A로 정밀 최적화**하는 2단계 전략이 가장 효율적이다.

---

## 2. 두 파이프라인의 설계 철학

### 2.1 Approach A: Dock-then-Design — "결합 상태에서 최적화"

```
원본 펩타이드 서열 (AGCKNFFWKTFTSC)
       │
       ▼
  Template 기반 복합체 조립 (make_complex_pose)
  ── 기존 결합 구조의 backbone 위치를 유지하면서 서열만 배치
       │
       ▼
  FlexPepDock (1회, 공유)
  ── 펩타이드-수용체 인터페이스 로컬 리파인먼트
  ── 모든 후보가 이 docked pose를 공유
       │
       ▼
  FastDesign (후보당 1회, 반복 수행)
  ── Monte Carlo + 에너지 최소화 사이클
  ── TaskFactory로 변이 위치 제어:
       • Receptor: 완전 고정 (PreventRepacking)
       • Peptide Cys 3,14: 고정 (이황화결합 보존)
       • Design positions: 서열 변이 허용 (20종 AA)
       • 나머지 peptide: repack만 허용
       │
       ▼
  InterfaceAnalyzerMover → dG, dSASA 스코어링
```

**설계 철학**: 수용체와 펩타이드가 **이미 결합된 상태**에서 서열을 변이시킨다. FastDesign의 Monte Carlo 사이클이 매 단계마다 수용체-펩타이드 상호작용 에너지를 평가하므로, 결합에 유리한 변이가 자연스럽게 선택된다.

### 2.2 Approach B: Mutate-then-Dock — "독립 변이 후 결합 평가"

```
원본 펩타이드 서열 (AGCKNFFWKTFTSC)
       │
       ▼
  랜덤 변이 생성 (generate_random_mutant)
  ── Design positions에서 무작위로 1~12개 위치 선택
  ── 각 위치를 Cys 제외 19종 AA 중 무작위로 교체
  ── 수용체 정보를 전혀 사용하지 않음
       │
       ▼
  Template 기반 복합체 조립 (make_complex_pose)
  ── MutateResidue로 sidechain만 교체
       │
       ▼
  FastRelax (펩타이드만)
  ── Receptor: 완전 고정
  ── Peptide backbone + sidechain: 자유
  ── 변이된 sidechain의 구조적 충돌 완화
       │
       ▼
  FlexPepDock (후보당 1회)
  ── 결합 인터페이스 재최적화
       │
       ▼
  InterfaceAnalyzerMover → dG, dSASA 스코어링
```

**설계 철학**: 서열 탐색과 구조 평가를 **분리**한다. 먼저 수용체와 무관하게 다양한 서열을 생성한 뒤, 각각을 독립적으로 도킹하여 결합 능력을 평가한다. 서열 생성에 편향이 없으므로 탐색 공간이 넓다.

---

## 3. 핵심 차이점 상세 분석

### 3.1 서열 최적화 메커니즘의 차이

| 측면 | Approach A (FastDesign) | Approach B (랜덤 변이) |
|------|-------------------------|------------------------|
| **변이 생성 방식** | Monte Carlo 기반 수락/거부 | 균일 랜덤 샘플링 |
| **수용체 정보 활용** | 매 Monte Carlo 단계마다 결합 에너지 평가 | 변이 생성 시 수용체 정보 사용 안 함 |
| **에너지 landscape 탐색** | 시작점 근처 local minimum 탐색 | 서열 공간 전체에서 균일 샘플링 |
| **수렴 방향** | 에너지적으로 유리한 방향으로 수렴 | 방향성 없음 (blind) |
| **1회 실행 결과** | 에너지 최적화된 단일 서열 | 미최적화된 단일 서열 |

Approach A의 FastDesign은 Rosetta의 `PackerTask` 시스템을 통해, 각 design position에서 20종 아미노산의 rotamer를 시도하고, 전체 에너지가 낮아지는 조합을 Monte Carlo로 탐색한다. 이 과정에서 **수용체 잔기와의 van der Waals, 수소결합, 정전기 상호작용이 모두 고려**되므로, 결과 서열은 해당 binding pocket에 물리적으로 적합한 경향이 강하다.

반면 Approach B의 `generate_random_mutant()`는 단순한 문자열 치환이다. `random.sample()`로 위치를 선택하고 `random.choice()`로 아미노산을 고르므로, 수용체 구조와는 완전히 독립적이다. 결합 적합성은 이후 FlexPepDock에서만 간접적으로 평가된다.

### 3.2 구조적 처리의 차이

| 단계 | Approach A | Approach B |
|------|-----------|-----------|
| **초기 도킹** | 1회 (모든 후보 공유) | 후보당 1회 |
| **구조 완화** | FastDesign 내부에서 자동 수행 | FastRelax (펩타이드만) 별도 실행 |
| **Backbone 처리** | FastDesign이 backbone + sidechain 동시 최적화 | FastRelax → FlexPepDock 순차 처리 |
| **PDB 라운드트립** | dump → reload (disulfide 정보 손실 위험) | Template에서 직접 변이 (라운드트립 없음) |

중요한 차이는 Approach A에서 **모든 후보가 동일한 docked pose를 공유**한다는 점이다. 초기 FlexPepDock이 찾은 결합 배향(binding orientation)이 모든 후보의 출발점이 되므로, FastDesign이 생성하는 서열들은 모두 **동일한 결합 모드(binding mode) 내에서의 변이**다.

Approach B에서는 각 후보가 독립적으로 FlexPepDock을 수행하므로, 서로 다른 결합 모드를 탐색할 가능성이 있다 (실제로는 template 기반이라 큰 차이는 제한적).

### 3.3 시간 복잡도의 차이

```
Approach A:
  총 시간 = FlexPepDock(1회) + FastDesign × N후보
         = ~2.3s + ~141.7s × N
  20후보 추정: ~2,836s (47.3분)

Approach B:
  총 시간 = (FastRelax + FlexPepDock) × N후보
         = ~15.0s × N
  20후보 추정: ~300s (5.0분)
```

Approach A의 병목은 **FastDesign**이다. 각 후보당 ~142초가 소요되며, 이는 Monte Carlo 사이클 내에서 수천 개의 rotamer 조합을 평가하기 때문이다. 반면 Approach B의 FastRelax + FlexPepDock은 서열 탐색이 아닌 구조 완화와 로컬 도킹만 수행하므로 ~15초로 끝난다.

**확장성(Scalability) 측면**에서, 100개 후보를 생성하려면:
- Approach A: ~4시간 (FlexPepDock 1회 + FastDesign 100회)
- Approach B: ~25분 (파이프라인 100회)
- 속도비: **~9.4배**

---

## 4. 실험 결과: 정량 데이터

### 4.1 후보별 상세 결과

#### Approach A 후보 (Dock→Design)

| 후보 | 서열 | dG (REU) | dSASA (Å²) | 변이 수 | 소요 시간 |
|------|------|---------|-----------|---------|----------|
| a_cand_001 | `TPCQFWCTHSCISC` | **-55.70** | 2122.1 | 11 | 137.1s |
| a_cand_002 | `TPCQIWCTHVCISC` | -55.08 | **2143.8** | 11 | 147.3s |
| a_cand_003 | `TPCKIWYTHDAISC` | -52.71 | 2078.5 | 10 | 140.6s |

#### Approach B 후보 (Mutate→Dock)

| 후보 | 서열 | dG (REU) | dSASA (Å²) | 변이 수 | 소요 시간 |
|------|------|---------|-----------|---------|----------|
| b_cand_001 | `AGCKNFFWKTFTSK` | **-37.27** | **2017.2** | 1 | 15.1s |
| b_cand_002 | `AVCKGFDWKTMTSS` | -31.25 | 1897.7 | 5 | 14.9s |
| b_cand_003 | `WGCKGGYYKTQTSC` | -32.22 | 1918.1 | 6 | 15.0s |

### 4.2 통계 비교

| 지표 | Approach A | Approach B | 차이 |
|------|-----------|-----------|------|
| 평균 dG (REU) | **-54.50** | -33.58 | A가 20.9 REU 우수 |
| 최고 dG (REU) | **-55.70** | -37.27 | A가 18.4 REU 우수 |
| 평균 dSASA (Å²) | **2114.8** | 1944.3 | A가 170.5 Å² 우수 |
| 평균 소요 시간 | 141.7s | **15.0s** | B가 9.4x 빠름 |
| 전체 소요 시간 | 427.5s (7.1분) | **45.1s (0.8분)** | B가 9.5x 빠름 |
| 고유 서열 비율 | 3/3 (100%) | 3/3 (100%) | 동일 |
| 평균 서열 거리 | **10.7** | 4.0 | A가 더 많이 변이 |

### 4.3 안정성/PK Proxy 비교

| 지표 | Approach A (평균) | Approach B (평균) | 해석 |
|------|-------------------|-------------------|------|
| cleavage_risk | **2.3** (낮음) | 7.7 (높음) | A가 프로테아제 저항성 우수 |
| hydrophobic_fraction | 0.29 | 0.31 | 유사 |
| net_charge_proxy | 1.0 | 2.0 | A가 전하 중립에 가까움 |
| pk_penalty | **0.5** | 1.0 | A가 PK 특성 우수 |

### 4.4 리소스 사용량

| 지표 | Approach A | Approach B |
|------|-----------|-----------|
| Peak CPU | 102% | 102% |
| Avg CPU | 99.7% | 96.7% |
| Peak RSS Memory | 1298.8 MB | 1301.2 MB |
| Peak GPU Utilization | 44% | 34% |
| Peak GPU Memory | 1330.7 MB | 1264.4 MB |

메모리 사용량은 거의 동일하다. 두 접근법 모두 단일 코어 CPU 바운드 작업이며, GPU는 부분적으로만 활용된다.

---

## 5. 스크리닝 관점에서의 전략적 분석

### 5.1 대량 스크리닝에 유리한 접근법: Approach B

펩타이드 바인더 스크리닝의 핵심 요구사항은 다음과 같다:

1. **처리량(Throughput)**: 제한된 시간 내에 최대한 많은 후보를 평가
2. **다양성(Diversity)**: 서열 공간을 넓게 탐색하여 false negative 최소화
3. **랭킹 신뢰도**: 스코어 기반 순위가 실험적 결합력과 상관관계를 가질 것

이 기준에서 **Approach B가 스크리닝에 압도적으로 유리**하다:

**처리량**: 동일한 1시간 내에 Approach A는 ~25개, Approach B는 ~240개의 후보를 평가할 수 있다. 스크리닝에서는 "좋은 후보 하나"보다 "충분히 많은 후보 중 상위 N개"가 중요하므로, 10배의 처리량 차이는 결정적이다.

**다양성**: Approach B의 랜덤 변이는 서열 공간을 편향 없이 탐색한다. Approach A의 FastDesign은 에너지 landscape의 local minimum으로 수렴하므로, 3개 후보의 서열이 서로 매우 유사해질 수 있다 (실험에서 a_cand_001과 a_cand_002의 서열이 14자리 중 13자리가 동일).

**비용 효율**: 후보당 15초 vs 142초는 컴퓨팅 비용에서 직접적인 차이를 만든다. 클라우드 환경에서 GPU 인스턴스 비용을 고려하면, 동일 예산으로 Approach B가 ~10배 더 많은 후보를 평가할 수 있다.

### 5.2 정밀 최적화에 유리한 접근법: Approach A

스크리닝 이후 **상위 후보를 정제(refinement)**하는 단계에서는 Approach A가 명확히 우수하다:

**결합 에너지**: Approach A의 평균 dG (-54.5 REU)는 Approach B (-33.6 REU)보다 **약 21 REU 우수**하다. 이는 FastDesign이 수용체 결합 포켓의 형상에 맞는 서열을 물리적으로 최적화하기 때문이다.

**안정성/PK 특성**: Approach A의 후보들은 cleavage_risk가 낮고 (2.3 vs 7.7) pk_penalty도 낮다 (0.5 vs 1.0). FastDesign의 에너지 함수가 간접적으로 물리화학적 안정성도 최적화하는 것으로 보인다.

**매몰 표면적**: dSASA가 평균 170 Å² 더 높다는 것은 수용체-펩타이드 접촉 면적이 더 넓다는 의미이며, 이는 보다 안정적인 결합 복합체를 시사한다.

### 5.3 권장 전략: 2단계 퍼널(Funnel) 접근법

```
Stage 1: 대량 탐색 (Approach B)
─────────────────────────────────
  • 500~1000개 랜덤 변이 서열 생성
  • 각각 FastRelax + FlexPepDock으로 평가
  • 예상 소요 시간: 500개 × 15s = 2.1시간
  • dG + dSASA + stability proxy로 랭킹
  • 상위 20~50개 선정 (Top 5~10%)
         │
         ▼
Stage 2: 정밀 최적화 (Approach A)
─────────────────────────────────
  • Stage 1 상위 후보의 서열을 시작점으로 사용
  • FastDesign으로 결합 상태에서 서열 최적화
  • 예상 소요 시간: 30개 × 142s = 1.2시간
  • 최종 dG/dSASA/rank_score로 최종 후보 선정
         │
         ▼
최종 후보: 5~10개
─────────────────
  • 실험적 검증 (합성 + 결합 어세이) 대상
```

**예상 총 소요 시간**: 500개 탐색 (2.1h) + 30개 최적화 (1.2h) = **약 3.3시간**

비교: Approach A로만 500개를 생성하려면 **약 19.7시간**이 필요하다.

---

## 6. 각 접근법의 한계와 주의사항

### 6.1 Approach A의 한계

1. **Local minimum 편향**: FastDesign은 gradient 기반이 아닌 Monte Carlo 방법이지만, 동일 시작 구조(docked_pose)에서 출발하므로 유사한 local minimum으로 수렴하는 경향이 있다. 실험에서 3개 후보 중 2개의 서열이 거의 동일했다 (`TPCQFWCTHSCISC` vs `TPCQIWCTHVCISC` — 14자리 중 2자리만 다름).

2. **PDB 라운드트립 위험**: docked_pose를 PDB 파일로 저장 후 다시 로딩하는 과정에서 이황화결합(disulfide) 정보, variant type 등의 메타데이터가 손실될 수 있다. 이는 `ResidueType::atom_charge()` 에러의 원인이 될 수 있다.

3. **확장성 제약**: 후보당 ~142초는 대량 스크리닝에 부적합하다. 1000개 후보 생성에 ~39시간이 필요하다.

### 6.2 Approach B의 한계

1. **Blind mutation**: 수용체 정보 없이 생성된 변이 서열은 binding pocket과의 상보성이 보장되지 않는다. 실험에서 dG가 평균 21 REU 나빴다.

2. **구조적 단순성**: FastRelax + FlexPepDock은 기존 backbone 근처의 로컬 최적화만 수행한다. Template 기반 조립이므로 근본적으로 새로운 결합 모드를 탐색하지는 못한다.

3. **변이 수 불균형**: `generate_random_mutant()`의 n_mutations가 `randint(1, 12)`로 설정되어, 변이 수가 균일하지 않다. 실험에서 b_cand_001은 1개 변이만 가졌고, 이것이 가장 높은 dG를 보였다 — 변이가 적을수록 원래 결합력에 가깝기 때문이다.

### 6.3 공통 한계

1. **샘플 크기**: 각 접근법당 3개 후보만으로는 통계적 결론을 내리기 어렵다. 최소 20~30개의 후보로 재검증이 필요하다.

2. **Rosetta 스코어 vs 실험적 결합력**: dG (REU)는 Rosetta의 에너지 단위이며, 실제 결합 자유 에너지(kcal/mol)와 정확히 비례하지 않을 수 있다. 실험적 검증 없이 스코어만으로 최종 판단하면 안 된다.

3. **이황화결합 처리**: Cys3-Cys14 이황화결합은 코드에서 "고정"으로 처리되지만, PDB 라운드트립이나 FastRelax/FastDesign 과정에서 이 제약이 완벽히 보존되는지 추가 검증이 필요하다.

---

## 7. 향후 개선 방향

### 7.1 Approach B 개선

- **Guided mutation**: 수용체 binding pocket의 잔기 특성(전하, 소수성)을 분석하여 변이 확률을 편향시키면, 랜덤 대비 적중률을 높일 수 있다
- **Genetic Algorithm**: 랜덤 변이 대신, 상위 후보의 서열을 교차/변이시키는 진화적 탐색으로 다양성과 품질을 동시에 개선
- **에너지 기반 필터링**: FastRelax 전에 간단한 에너지 체크로 명확히 불리한 변이를 조기 제거

### 7.2 Approach A 개선

- **Multi-start**: 서로 다른 초기 도킹 결과에서 FastDesign을 수행하여 local minimum 편향 완화
- **직접 clone 사용**: PDB dump/reload 대신 `pose.clone()`으로 이황화결합 정보 보존
- **Reduced design space**: 핵심 접촉 잔기만 design position으로 제한하여 시간 단축

### 7.3 하이브리드 전략

- **Stage 1**: Approach B + Guided mutation으로 500~1000개 후보 생성 (~2h)
- **Stage 1.5**: 상위 50개에 대해 ML 기반 binding affinity 예측 (ProteinMPNN, ESM-IF 등)으로 재순위
- **Stage 2**: 상위 10~20개에 Approach A (FastDesign) 적용 (~0.5h)
- **Stage 3**: 최종 5개를 MD simulation으로 추가 검증 (선택적)

---

## 8. 재현을 위한 환경 정보

```bash
# 환경 활성화
conda activate bio-tools

# 실행 (notebooks/ 디렉토리에서)
cd notebooks/
jupyter notebook comparison_fastdesign_vs_dock.ipynb

# 전제 조건
# - standardized_relaxed.pdb가 notebooks/ 디렉토리에 존재해야 함
# - PyRosetta 라이선스가 유효해야 함
```

### 출력 파일

| 파일 | 설명 |
|------|------|
| `comparison_results/comparison_all_candidates.csv` | 전체 후보 데이터 (A 3개 + B 3개) |
| `comparison_results/resource_timeseries.csv` | 0.5초 간격 CPU/Memory/GPU 시계열 |
| `comparison_results/quality_comparison.png` | dG / dSASA / Time 비교 (box plot) |
| `comparison_results/resource_timeseries.png` | 리소스 사용량 시계열 (4패널) |
| `comparison_results/efficiency_frontier.png` | dG vs Wall Time 효율 프론티어 |
| `comparison_results/per_candidate_resources.png` | 후보별 리소스 소비 (bar chart) |
| `comparison_results/diversity_analysis.png` | 서열 다양성 분석 (Hamming distance) |
