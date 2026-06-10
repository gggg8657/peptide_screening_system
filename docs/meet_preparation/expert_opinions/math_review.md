# 수학·통계·최적화 전문가 견해
**대상 회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) 후속 6월 보고  
**작성일**: 2026-06-01  
**작성자**: reviewer-math (NSGA-II / BO / 통계 / 수치 알고리즘 도메인)  
**할루시네이션 방지 원칙**: 코드 직접 확인 결과 + 검증된 References만 인용. 미확인 항목은 `[추정]` 명시.

---

## 1. A-04 — Weighted Sum vs Pareto Front: 수학적 Trade-off

### 1.1 현재 구현 확인 결과

`pipeline_local/scoring/composite_scorer.py` 직접 열람 결과:

- **WSS 가중치** (하드코딩, 합계 = 1.0 내부 assert):

$$\text{WSS} = 0.35 \cdot \tilde{\Delta G} + 0.25 \cdot \tilde{\text{sel}} + 0.20 \cdot \tilde{t_{1/2}} + 0.10 \cdot \widetilde{(1-\text{admet})} + 0.10 \cdot \widetilde{(10-\text{rad\_cnt})}$$

  여기서 $\tilde{\cdot}$ 는 후보군 내 min-max 정규화. 모든 dimension을 $[0,1]$로 변환 후 가중합.

- **Pareto front 활성 조건**: 후보 수 $\geq 50$ AND pymoo 설치 시. 현재 운영 조건(PRST-001~004 = 4개)에서는 **Pareto front가 전혀 계산되지 않는다**. Tier-S는 WSS top 20% 기준으로만 결정됨.

- **pyrosetta_flow/pareto_ranking.py** 별도 존재: 목적 함수 4개(ddG, stability, druggability, diversity) + 제약 조건 2개(hard_violations, clash_score). pymoo `NonDominatedSorting` + `calc_crowding_distance` 정상 구현 확인.

### 1.2 Weighted Sum의 수학적 한계

WSS는 **볼록(convex) Pareto front**에서만 전체 front를 탐색한다. 비볼록 front의 경우 아무리 가중치를 바꾸어도 도달 불가능한 영역이 존재한다 (Miettinen 1999, 다목적 최적화 교과서적 사실). 구체적으로:

1. **가중치 민감도**: $w_{\Delta G}$ 를 0.35 → 0.50으로 변경 시 Tier-S 집합이 교란됨. 현재 가중치는 이론적 근거 없이 휴리스틱으로 결정되었음(코드 주석 없음). 민감도 분석(가중치 ±0.05 grid search) 수행 권고.

2. **차원 간 비교 불가 문제**: REU 단위 $\Delta G$ 와 배수 단위 selectivity를 min-max로 공통 척도화할 때, 후보군 분포에 따라 정규화 결과가 달라진다(run-to-run 가변). 후보 20개 집합 vs 200개 집합에서 동일 후보의 WSS가 다를 수 있다.

3. **집합 크기 의존성**: `WSS_TOP_FRACTION = 0.20` 이므로 5개 후보 시 top 1개만 Tier-S, 50개 시 top 10개가 Tier-S. 집합 크기와 독립적인 절대 기준 없음.

### 1.3 Pareto Front (NSGA-II) 도입 권고

pymoo [R09] NSGA-II는 검증된 구현이 이미 `pareto_ranking.py`에 존재한다. 도입 시 이점:

- **가중치 독립**: 의사결정자 선호 없이 비열등 집합 전체를 보존
- **Crowding distance**: front 내 다양성 보장 — 병목 없이 고루 분포된 후보 선택

**단, 운영 조건에서의 현실적 제약**:

현재 PRST-001~004 (n=4)는 Pareto front 활성 기준(n≥50)에 크게 못 미친다. 이는 의도된 설계이나, 발표 시 "Pareto front는 적용되지 않았다"는 사실을 명시해야 한다. n≥50 후보를 생성하는 운영 단계에서 활성화 예정임을 설명할 것.

**후보 n < 50 구간의 대안**: WSS 가중치 민감도 분석(grid search over weight simplex) + 결과 변동 범위를 함께 보고하면 "가중치 의존성"을 투명하게 노출할 수 있다.

---

## 2. A-05 — n회 반복 Mean의 통계적 설계

### 2.1 현재 구현 확인 결과

`gate_thresholds.yaml` 가변 임계값 (`ref * 0.9`) 적용 확인. 그러나 **n 반복 횟수가 코드에 명시되지 않음** (A-05 한계 항목 명시). `data/sst14_reference_dG.json` 파일 존재 확인 필요 상태.

### 2.2 통계적 올바른 레퍼런스 추정 방법

$n$회 반복 도킹에서 SST-14 $\Delta G$ 를 레퍼런스로 사용할 때, **편향 없는 추정량(unbiased estimator)**과 그 불확실성 표기:

$$\hat{\mu}_{\Delta G} = \frac{1}{n} \sum_{i=1}^{n} \Delta G_i \qquad \text{(sample mean, unbiased)}$$

$$\text{SE}(\hat{\mu}) = \frac{s}{\sqrt{n}}, \quad s = \sqrt{\frac{1}{n-1} \sum_{i=1}^{n} (\Delta G_i - \hat{\mu})^2} \qquad \text{(표준오차, Bessel 보정)}$$

$$\text{95\% CI}: \quad \hat{\mu} \pm t_{n-1,\, 0.025} \cdot \frac{s}{\sqrt{n}}$$

**회의 발표 권고**: 현재 보고서에 "n회 반복 Mean 값" 이라고만 기재되어 있으나, **n 값, $\hat{\mu}$, $s$, 95% CI를 함께 표기**해야 레퍼런스 신뢰성을 주장할 수 있다. 예시:

$$\Delta G_{\text{SST14/SSTR2}} = -95.024 \pm 3.2 \text{ REU} \quad (n=10,\; 95\%\text{ CI}: [-101.4,\; -88.6]\text{ REU})$$

숫자는 `[추정]` — 실제 n과 측정 분산 확인 필요.

### 2.3 가변 임계값 `ref * 0.9`의 통계적 해석

`HARD_CUTOFF_DDG = SST14_SSTR2_REF_DDG` (= -95.024 REU)를 게이트 기준으로 사용. "ref × 0.9"는 코드에서 `delta_g_threshold: ref * 0.9`로 기재되어 있으나, REU가 음수이므로 `ref * 0.9 = -85.5 REU`로 **더 느슨한 임계값**이다. 의도가 "10% 완화"라면 `ref * 1.1 = -104.5 REU` (더 엄격)로 수정해야 한다. **부호 방향 재확인 필수**.

### 2.4 MM-GBSA / FEP/TI 수렴 기준 (서호성 의견 연동)

서호성 박사 3단계 정밀 계산 로드맵의 수학적 수렴 기준:

**MM-GBSA (gmx_MMPBSA, [R10])**:
- 수렴 지표: $\Delta G_{\text{MMGBSA}}$ 블록 평균의 블록-크기 수렴 (block averaging). 블록 크기를 늘릴수록 블록 평균의 분산이 줄어드는 plateau에서 수렴 확인.
- 최소 권고: 생산 MD 50–100 ns, 1 ns 간격 스냅샷, 블록 분석 10 블록 이상.

**FEP/TI (OpenFE 1.0, [R12])**:
- 수렴 지표: 각 $\lambda$-window에서 $\partial V/\partial \lambda$ 의 autocorrelation time $\tau$. Effective sample size (ESS) = $N / (1 + 2\tau/\Delta t)$.
- 권고: ESS $\geq$ 50 per window, $\lambda$ 겹침(phase space overlap) $O_{i,i+1} \geq 0.5$.
- Zwanzig 지수 $\langle e^{-\beta \Delta V} \rangle$ 의 분산이 크면 $\lambda$-point 추가 권고.

`[추정]` — OpenFE 1.0 공식 권장값 기준; 실제 SSTR2-peptide 시스템 specific 파라미터는 시험 실행 후 결정.

---

## 3. A-06 — DiffDock vs Rosetta RMSD 비교의 통계 설계

### 3.1 현재 상태 확인

A-06 PoC 미완 (DiffDock 본격 실행 없음). RMSD 비교 보고서 부재. 회의록 KPI: RMSD ≤ 2.0 Å 재현율 ≥ 80%.

### 3.2 올바른 통계 설계

RMSD 비교에는 **paired test**가 적절하다. 동일 구조(SSTR2-SST14, 7T10)에 두 방법을 각각 적용하므로, 쌍-측정값의 차이를 분석해야 한다:

$$\delta_i = \text{RMSD}_{\text{Rosetta},i} - \text{RMSD}_{\text{DiffDock},i}, \quad i = 1, \ldots, n$$

**Wilcoxon signed-rank test** (RMSD 분포 비정규 가정 시):

$$H_0: \text{median}(\delta) = 0 \quad \text{vs} \quad H_1: \text{median}(\delta) \neq 0$$

**Unpaired test는 부적절**: 동일 단백질·배위에 대한 측정이므로 쌍 구조를 무시하면 검정력(power)이 낮아진다.

**표본 크기 계산** (80% 검정력, $\alpha = 0.05$, 중간 효과 크기 $d = 0.5$ 가정):

$$n \approx \left(\frac{z_{1-\alpha/2} + z_{1-\beta}}{d}\right)^2 = \left(\frac{1.96 + 0.842}{0.5}\right)^2 \approx 31 \text{개 pose}$$

회의록의 "RMSD ≤ 2.0 Å 재현율 ≥ 80%" KPI는 비율 테스트로 검증:

$$\hat{p} = \frac{\#(\text{RMSD} \leq 2.0\,\text{\AA})}{n}, \quad \text{95\% CI via Wilson interval}$$

$n = 30$, $\hat{p} = 0.80$일 때 Wilson 95% CI: $[0.62,\, 0.91]$. **n < 20이면 신뢰구간이 지나치게 넓어 "80% 재현율" 주장 불가**.

### 3.3 DiffDock 성능 맥락 ([R13])

DiffDock (ICLR 2023, Corso et al.) PDBBind top-1 성공률: RMSD < 2 Å 기준 38%. 펩타이드 시스템은 일반적으로 소분자보다 RMSD 성능이 낮다. SSTR2-SST14 복합체(7T10, 14aa 환형 펩타이드)에서의 성능은 `[추정]`이며 **본 PoC에서 직접 측정 필수**.

Boltz-2 ([R14])는 이미 운영 중이며 CASP16 affinity track 1위이나, RMSD vs Rosetta 비교 데이터 부재. A-06 KPI 충족 여부는 측정 결과 전까지 미결.

---

## 4. 회의록 §2.5 — 7단계 선별 체계의 통계적 일관성

### 4.1 다단계 선별의 누적 오류율 문제

회의록 §2.5 7단계 선별에서 각 단계가 독립적인 통과/탈락 기준을 가질 경우, **다중 비교(multiple testing) 문제**가 발생한다. Gate 5개(Hard Cutoff)를 각각 유의수준 $\alpha = 0.05$로 운용하면:

$$\alpha_{\text{FWER}} = 1 - (1-0.05)^5 \approx 0.226$$

즉, 아무 특성이 없는 후보도 약 23%의 확률로 "모든 게이트 통과"라는 위양성(false positive)이 발생한다. 이는 `composite_scorer.py` Gate 1–5의 임계값이 통계적 검정이 아닌 도메인 상수(예: selectivity ≥ 100×)로 설정되어 있어 이 분석이 직접 적용되지는 않지만, **임계값 자체의 정당화 근거가 취약하다**.

**권고**: 각 Hard Cutoff 임계값의 근거를 문헌에서 명시. 예: selectivity ≥ 100× 기준은 [다른 전문가 의견 권장(biology/pharma 도메인)].

### 4.2 현재 7단계 체계의 수렴 진단 (convergence.py)

`pyrosetta_flow/convergence.py` 직접 확인 결과:

- **Mann-Whitney U test**: 이전 window vs 현재 window의 top-k ddG 분포 비교. $p > 0.05$ (비유의) + CV < 0.15 이면 수렴 판정.
- **정규 근사 조건**: `n_total < 8`이면 `p = 1.0` 반환 (검정력 0). window_size = 3, 즉 세대당 top-k ddG 샘플 수가 6개 미만이면 사실상 수렴 탐지 불가.
- **누적 분산 추정**: CV = $s / |\bar{x}|$ 을 사용하나, $\bar{x} \approx 0$ 근방에서 수치 불안정 가능. 코드에서 `mean_val != 0` 조건으로 방어하나, 극소 평균(예: ddG ≈ -0.1 REU) 시 CV 폭발 가능.

### 4.3 K-1/K-2 Selectivity 결함의 통계적 파급

본 점검 P0 발견: `_build_pdb_index` 정렬 + `candidate_pdb` 미전달로 모든 후보가 동일 off-target에 대해 계산됨.

수학적 영향:

$$\text{selectivity\_ratio} = \frac{\Delta G_{\text{SSTR2}}}{\Delta G_{\text{off-target}}}$$

분모가 모든 후보에서 동일한 단일 값으로 고정되면, selectivity_ratio는 $\Delta G_{\text{SSTR2}}$ 의 단조 변환에 불과하다. 이는:

1. **Hard Cutoff Gate 2** (selectivity ≥ 100×)가 실질적으로 ddG Gate의 변형이 됨 — 독립적 게이트가 아님.
2. **WSS** 의 selectivity 항(가중치 0.25)이 ddG 항(0.35)과 상관관계 1에 근접 — 60%의 가중치가 단일 지표를 과도 반영.
3. **Pareto front** 의 selectivity 목적 함수 축이 의미를 잃음.

이를 수정하지 않으면 PRST-001~004의 순위는 사실상 $\Delta G_{\text{SSTR2}}$ 단일 순위이며, 다목적 최적화의 효과가 없다. **R-04 K-1/K-2 정정 + R-08 ranking 재검증이 수학적으로 선결**.

---

## 5. pymoo NSGA-II/NSGA-III 활용 가능성 ([R09])

pymoo (Blank & Deb 2020, IEEE Access, arXiv:2002.04504) 버전 0.6.1.6 — References 검증 통과.

**현재 프로젝트에서의 사용 현황 (코드 직접 확인)**:

| 위치 | 사용 방식 | 활성 여부 |
|------|----------|----------|
| `composite_scorer.py` | `NonDominatedSorting` (n≥50 조건부) | 조건부 (현재 n<50으로 비활성) |
| `pareto_ranking.py` | `NonDominatedSorting` + `calc_crowding_distance` (n≥1) | 항상 활성 |
| `bayesian_optimizer.py` | `is_non_dominated` (BoTorch) | BoTorch 설치 조건부 |

**NSGA-III 도입 타당성** `[추정]`: 목적 함수가 3개 초과 시 NSGA-II보다 NSGA-III가 유리하다 (Deb & Jain 2014). 현재 5개 목적 함수(ddG, selectivity, half_life, admet, radiolysis)를 사용하므로 NSGA-III 도입이 수학적으로 더 적합할 수 있다. pymoo는 NSGA-III를 지원하며 동일 API로 교체 가능. `§5 검증 권고`.

---

## 6. 베이지안 최적화 (bayesian_optimizer.py) 수렴 진단

`pyrosetta_flow/bayesian_optimizer.py` 직접 확인:

- **BoTorch 경로**: `SingleTaskGP` + `ExactMarginalLogLikelihood` MLE로 kernel hyperparameter 최적화. `fit_gpytorch_mll` 호출로 MLE 수렴 처리됨.
- **Fallback 경로**: `_FallbackGP` (numpy RBF kernel, `lengthscale=1.0` **고정**). MLE 수렴 없음 — hyperparameter 최적화 미수행.
- **Acquisition function**:
  - BoTorch 경로: `qNEHVI` (Noisy Expected Hypervolume Improvement) → 다목적 BO의 이론적으로 올바른 선택.
  - Fallback 경로: UCB with $\beta = 2.0$ (고정) — exploration/exploitation 균형이 데이터 크기에 적응하지 않음.

**결함 발견**: Fallback GP의 `lengthscale=1.0` 고정은 입력 공간 스케일에 의존한다. one-hot embedding (차원 = 14 × 20 = 280) 시 RBF kernel의 effective lengthscale이 과소/과대 추정될 수 있다. **BoTorch 미설치 환경에서는 BO 품질 보장 불가** — 최소한 data-adaptive lengthscale (median heuristic 등) 적용 권고 → engineer-backend 수정 요청 필요.

**GP posterior calibration**: 현재 코드에 posterior calibration 검증(Expected Calibration Error, reliability diagram) 없음. `[추정]` BoTorch SingleTaskGP는 homoskedastic noise 가정 — 실제 도킹 스코어 noise가 heteroskedastic이면 보정 오류 가능.

---

## 7. §검증 필요 (이 리뷰에서 미해결 항목)

| ID | 항목 | 우선순위 | 요청 대상 |
|----|------|---------|----------|
| VR-M-01 | `sst14_reference_dG.json` 의 실제 n 값 + 표준편차 확인 | P0 | engineer-backend |
| VR-M-02 | `gate_thresholds.yaml` 의 `ref * 0.9` 부호 방향 재확인 (완화 vs 엄격) | P0 | engineer-backend |
| VR-M-03 | K-1/K-2 정정 후 PRST ranking 변동 폭 정량화 (selectivity 상관 제거 후 WSS 재계산) | P0 | engineer-backend |
| VR-M-04 | DiffDock PoC n≥31 pose 확보 후 paired Wilcoxon + Wilson CI 보고 | P1 | A-06 실행 후 |
| VR-M-05 | Fallback GP `lengthscale` median heuristic 적용 | P1 | engineer-backend |
| VR-M-06 | WSS 가중치 sensitivity analysis (weight simplex grid) | P1 | engineer-backend |
| VR-M-07 | ConvergenceDetector window ddG 샘플 수 < 8 시 경고 추가 | P2 | engineer-backend |
| VR-M-08 | NSGA-III 전환 타당성 (목적함수 5개 기준) | P2 `[추정]` | researcher 문헌 조사 |

---

## 참고 문헌 (검증 통과 References만 인용)

- [R09] Blank J, Deb K. "pymoo: Multi-objective Optimization in Python." IEEE Access 8:89497-89509 (2020). arXiv:2002.04504. https://pymoo.org/
- [R10] Valdés-Tresanco MS et al. "gmx_MMPBSA." J Chem Theory Comput 17(10):6281-6291 (2021). DOI: 10.1021/acs.jctc.1c00645
- [R12] OpenFE v1.0. https://openfree.energy/ (안정 릴리스 2024-05)
- [R13] Corso G et al. "DiffDock: Diffusion Steps, Twists, and Turns for Molecular Docking." ICLR 2023. arXiv:2210.01776
- [R14] Wohlwend J et al. "Boltz-2." bioRxiv 2025.06.14.659707. PMC12262699

---

*reviewer-math · 2026-06-01 · 수학/통계/최적화 도메인 한정 견해*
