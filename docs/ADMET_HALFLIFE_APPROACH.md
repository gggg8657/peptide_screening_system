# ADMET · 혈중 반감기(Half-life) 처리 방식

> 2026-06-09 작성. SSTR2 스크리닝 시스템에서 **반감기**와 **ADMET**을 어떻게 다뤘는가.
> 핵심 원칙: **계산 불가능한 것을 계산 가능한 척하지 않는다**(H-06 가드). 실측 물리량(ΔG·선택성)과 **랭킹용 surrogate**(반감기·ADMET)를 명확히 구분한다.

---

## 1. 혈중 반감기 (Blood Half-life)

### 문제
- 실제 임상 혈중 t½는 **in-vitro 혈청 안정성 / in-vivo PK assay 없이는 계산 불가**.
- pepADMET 논문의 half-life ML 모델(T½ HBN/HBM 등, R²=0.84~0.98)은 **GitHub 미공개**(독성 모델만 공개).
- 소분자 ADMET 도구는 펩타이드(MW>500, 사이클릭, SS bond)에 **부적합**.

### 해결 — 서열 기반 휴리스틱 surrogate
`AG_src/pipeline/step08_stability.py : predict_half_life(sequence, modifications) -> float(hours)`
GLP-1 약동학에서 영감을 받은 가산 모델:

| 요소 | 값/규칙 | 근거 |
|------|--------|------|
| base | `_BASE_HALF_LIFE_HOURS = 3.0h` | DOTATATE/SST 유사체의 짧은 신장 청소 반감기(~1.5h) 수준 |
| 프로테아제 취약성 | 잔기별 `_PROTEASE_VULNERABILITY` 평균 → `exp(-0.5·(avg-1.0))` 지수 감쇠 | 절단 속도 ∝ 기질 친화도 → 반감기 반비례 |
| 고리화 | Cys 쌍(≥4잔기 간격) 감지 시 **+24h** | 엑소/엔도펩티다제 부분 차단 (SST-14 Cys3-Cys14) |
| 말단 취약성 | N/C-말단 exopeptidase + dipeptide 절단부위(K/R-X 트립신, F/Y/W-X 키모트립신) 페널티 | aminopeptidase/carboxypeptidase 우선 공격 |
| 잔기 페널티 | Arg/Lys **−12h**(트립신), Met **−8h**(산화) | — |
| modification 보너스 | fatty_acid **+120h**(C18 알부민결합, 세마글루타이드 168h), PEG **+96h**, D-AA **+48h**, cyclization **+24h**, substitution **+12h** | 임상 변형 펩타이드 기준 |

### 통합
`pyrosetta_flow/multiobjective.py : cheap_objectives()`가 **모든 후보**에 저비용으로 `half_life_h`를 계산 → `stability_norm`(0~1, ref 16h 대비 포화 정규화) → **Pareto `stability` objective** + 다목적 스칼라 가중 0.20.

### 정직성 (H-06 가드)
`pipeline_local/scripts/pharmacology_guards.py`의 `HEURISTIC_FUNCTION_DISCLAIMERS`가 명시:
```
"...predict_half_life": { "surface_unit": "hours",
   "actual_meaning": "heuristic ranking score (NOT clinical half-life)" }
```
→ 숫자는 "시간" 단위로 보이지만 실제로는 **변이체 간 상대 순위용 점수**다. 임상 t½ 예측이 아니며 in-vitro assay로 검증되지 않았다. 단, 변별력은 있음(native AGCKNFFWKTFTSC 16.6h vs 말단변이 YGCKNFFWKTFTST 1.5h — 말단 exopeptidase 취약성 반영).

---

## 2. ADMET

### 문제
- **pepADMET 전체 ML 플랫폼**(19 endpoint: 투과도/분포/대사/배설/독성)의 모델 가중치 repo가 **현재 작업 디렉토리에 없음** (`local_models/pepadmet/repo` 부재 — 다른 복사본에 존재하나 침범 금지). `pepadmet` conda env는 존재하나 모델 파일 없이는 추론 불가.
- 소분자 ADMET(ADMETlab 3.0 등): MW<500 전용 + TLS 만료 → 펩타이드 부적합.

### 해결 — 문헌 기반 물성 reasonableness surrogate
`AG_src/pipeline/pharma_properties.py : PharmaProperties` (문헌 검증 계산기) + `multiobjective.py : admet_reasonableness()`:

| 물성 | 출처 | reasonableness 기여 |
|------|------|--------------------|
| Instability Index | Guruprasad 1990 (<40 안정) | 35% — II<40 만점, 40~80 선형 감점 |
| GRAVY | Kyte-Doolittle 1982 | 30% — 친수(음수)일수록 가점(용해도) |
| Boman Index | Radzicka-Wolfenden | 15% — 단백질 결합 경향(2~4 적정) |
| pI | Lehninger pKa (SS bond Cys 제외) | 20% — 중성(6~8) 가점 |

→ `admet_score` = 0~1 합성 점수. `cheap_objectives()`가 모든 후보에 계산 → **Pareto `druggability` objective** + 다목적 스칼라 가중 0.15.

### 정직성
- ADMET surrogate는 펩타이드의 **물성 "합리성(reasonableness)"** 점수지, pepADMET급 독성/투과도 ML 예측이 **아니다**.
- 침범 금지 제약 하에서 가용한 자원(문헌 물성)으로 만든 **랭킹 보조 지표**임을 명시.

### 향후 경로 (PEND)
- pepADMET 모델 repo(.pth) 확보 시 → `pyrosetta_flow/pepadmet_runner.py`(이미 배선 준비됨, `predict_toxicity_batch`)로 실제 binary/6-class 독성 ML 추론 연결.
- 이때 `multiobjective`에 toxicity endpoint를 추가 objective로 편입.

---

## 3. fail-closed 적용 (D1/F08)
반감기·ADMET는 surrogate지만 **실패 시 가짜값을 내지 않는다**. 서열 계산이 실패하면 `cheap_objectives`가 `half_life_h=NaN`/`admet_score=0.0`을 남기고, 다목적 스칼라/Pareto는 결측을 그대로 반영(가짜 점수로 채우지 않음). 실측 경로(ΔG·선택성 off-target 도킹)는 D1에서 stub/실패→fail-closed(ddg=999/NaN, 랭킹 제외) 처리.

## 요약
| 항목 | 실측 vs surrogate | 모듈 | 정직성 |
|------|------------------|------|--------|
| **ΔG (SSTR2 결합)** | **실측** PyRosetta FlexPepDock + InterfaceAnalyzer | step06 / flexpep_dock.py | REU, 절대 Ki/Kd 아님 |
| **선택성 (SSTR1/3/4/5)** | **실측** off-target 도킹 | step05b / offtarget_dock.py + multiobjective.screen_selectivity | 실 ΔG 비교 |
| **혈중 반감기** | **surrogate** (서열 휴리스틱) | step08.predict_half_life | "랭킹 점수, 임상 t½ 아님" |
| **ADMET** | **surrogate** (문헌 물성) | pharma_properties + admet_reasonableness | "물성 합리성, ML 예측 아님" |

---

## 부록: 2026-06-09 업데이트 (재보정 A + pepADMET 통합 B)

### A. 혈중 반감기 재보정 (log-multiplicative)
기존 additive 모델은 cyclization +24h 가 사이클릭/SS 펩타이드를 과대예측 — 문헌 벤치마크에서
**SST-14 16.6h(실제 ~0.05h), plain Spearman = −0.5(순위 역전)**. log10 곱셈 모델로 교체:
`log10(t½) = log10(0.05) − proteolysis_penalty + Σ modification_log_mult`
- cyclization: +24h additive → **×1.8 배수**(혈중 t½ 주도 아님)
- fatty_acid: ×2800(알부민 결합) 등 modification 이 장반감기 주도
- proteolysis_penalty: 취약성+절단부위+말단 exopeptidase
- **결과: SST-14 0.042h, Spearman 0.86(all)/0.50(plain)**. 회귀: `AG_src/tests/test_halflife_benchmark.py`(5 tests).
- `multiobjective.stability_norm` 도 log10 정규화([0.02h,200h])로 교체 — 재보정 스케일에서 변별력 유지.
- 한계: Exenatide(DPP-4 저항 Gly2)는 서열 휴리스틱이 못 봐 과소예측(유일 miss). fatty-acid C16/C18(liraglutide/semaglutide) 구분 불가(단일 플래그).

### B. pepADMET 실제 독성 ML 통합
`github.com/ifyoungnet/pepADMET` 클론(`local_models/pepadmet/repo`, **독성 모델만 공개**) + `pepadmet` conda env(DGL 0.4.3).
- `multiobjective.predict_toxicity_for_sequences()` → `pepadmet_runner.predict_toxicity_batch` (SMILES 변환 + GNN subprocess 배치 추론) → binary_toxicity/type/hc50.
- `apply_toxicity_to_extra()`: 독성 후보의 `admet_score` ×0.4 페널티. available=False면 미변경(fail-closed).
- `scoring_pipeline` Step 0.5 로 배치 통합 (env `SST_DISABLE_PEPADMET_TOX=1` 로 비활성화 가능; 단위 테스트는 비활성).
- 검증: 단위 3 + 실제 추론 smoke 1. **ADMET 의 독성 차원이 물성 surrogate → 실제 GNN ML 로 격상.**
- 잔여: half-life/투과도 ML 은 pepADMET 미공개 → 반감기는 재보정 휴리스틱 유지(A).
