# PRST-001~004 pepADMET binary_toxicity=1.00 약리학 검증 보고서

**작성**: reviewer-pharma  
**일시**: 2026-05-20  
**팀**: selectivity-validation-20260520  
**대상**: Gate-2 합성 의뢰 후보 PRST-001, 002, 003, 004

---

## 0. 전제조건: pharmacology_guards 회귀 테스트

```
pipeline_local/tests/test_pharmacology_guards.py — 70/70 PASSED (0.17s)
```

**외부 도구 등록 상태 확인** (pharmacology_guards.py §EXTERNAL_TOOL_CONFIDENCE):
- `external_tool.pepadmet` → `confidence_grade: HEURISTIC`
- `cyclic_support: False` (Layer 1 Ensemble)
- `absolute_confidence: LOW` (check_pepadmet_applicability)

---

## 1. PASS/FAIL 매트릭스

| 검증 항목 | 결과 | 근거 |
|-----------|------|------|
| 회귀 테스트 (pharmacology_guards.py) | **PASS** 70/70 | pytest 실행 결과 |
| pepADMET 학습 도메인 포함 여부 (binary toxicity) | **FAIL — OOD** | 14aa SS-bond 펩타이드 바이너리 라벨 0건 |
| HC50 물리적 타당성 | **FAIL** | 훈련 범위 0.8-2.61, 예측값 -38 ~ -45 |
| confidence=1.0 신뢰성 | **FAIL** | Octreotide 교차검증 결과 동일 패턴 |
| 변이 영향 구별력 | **FAIL** | 4후보 모두 binary_toxicity=1.0, 차별화 0 |
| 결과 출처 추적 가능성 | **PASS** | infer_script.py → MY_GNN.py 경로 확인 |
| Gate-2 합성 의뢰서 ADMET 값 진위 | **FAIL** | fallback 0.10~0.25 ≠ 실 pepADMET 출력 |

---

## 2. pepADMET 학습 데이터 도메인 분석

### 2.1 데이터셋 구조 (`Toxicity.csv`, 135 rows)

pepADMET는 **멀티태스크 GNN** 으로, 각 태스크의 학습 샘플은 독립적으로 라벨링됨:

| 태스크 | 라벨 수 | 실제 사용 row | 비고 |
|--------|---------|-------------|------|
| binary_toxicity (Task 0) | **30** (toxic=15, non-toxic=15) | 30 | 바이너리 분류 |
| toxicity_type_class (Task 1) | 54 (6 class × 9) | 54 | 다중 분류 |
| neurotoxicity_type_class (Task 2) | 36 (4 class × 9) | 36 | 다중 분류 |
| HC50 regression (Task 3) | **15** | 15 | 회귀 |

총 135 row 중 105 row는 binary_toxicity 라벨 **없음** — 이는 각 태스크가 서로 다른 샘플 부분집합을 사용하는 마스크 기반 다중태스크 학습 구조이기 때문.

### 2.2 PRST 후보군 vs 학습 도메인 : 14aa SS-bond 환형 펩타이드

| 구조 특성 | 학습 데이터 | PRST 후보 | 판정 |
|-----------|------------|-----------|------|
| 14aa 환형 SS-bond (binary label) | **0건** | 4건 | **OOD** |
| 12-16aa SS-bond (모든 태스크) | 5건 (라벨 없음) | 4건 | 부분 OOD |
| SS-bond (binary label 있음) | **1건** (50aa, toxic=1) | 14aa | OOD |
| MW 1400-1700 Da (binary label) | 4건 (SS 없음) | 1534-1624 Da | 부분 OOD |

**결론**: PRST-001~004는 binary toxicity 분류 학습 도메인에서 **구조적으로 가장 가까운 유사체가 존재하지 않음** (cyclic 14aa SS-bond 유형 = 라벨 0건).

### 2.3 Hemostasis / Na_inhibitor 학습 예시 구조 분석

**Hemostasis (toxicity_type=4, 9건)**:

| group | MW | Length | SS bond |
|-------|-----|--------|---------|
| training | 5377 Da | 48aa | 있음 |
| training | 2017 Da | 19aa | 없음 |
| training | 3739 Da | 37aa | 있음 |
| test | 4991 Da | 46aa | 있음 |
| test | 1975 Da | 20aa | 없음 |
| test | 4298 Da | 37aa | 없음 |
| valid | **1639 Da** | **15aa** | **없음** |
| valid | 2193 Da | 19aa | 없음 |
| valid | 5511 Da | 49aa | 있음 |

→ PRST와 가장 가까운 hemostasis 예시: 15aa, MW=1639 Da, **SS bond 없음**. 14aa SS-bond hemostasis 예시 = **0건**.

**Na_inhibitor (neurotype_class=3, 9건)**:

- PRST와 가장 가까운: 12aa MW=1519 Da (SS 없음), 13aa MW=1358 Da (SS 있음)
- 14aa SS-bond Na_inhibitor 예시 = **0건**

### 2.4 OOD 판정 근거 요약

PRST-001~004는 pepADMET binary toxicity 분류에서 **Out-of-Domain (OOD)** 입력이다:
1. 14aa 환형 SS-bond 구조 → 학습 바이너리 라벨 도메인 내 유사체 전무
2. 학습 도메인 내 유일한 SS-bond binary 라벨 예시 = 50aa toxin (구조적으로 완전 상이)
3. 모델이 cyclic SS-bond peptide를 hemostasis/Na_inhibitor로 분류하는 체계적 편향 가능성 (§3 참조)

---

## 3. Confidence=1.0 신뢰성 판단

### 3.1 Octreotide 교차검증 (V02-V03 패치 보고서, 2026-05-20)

**Octreotide** (FDA-승인, Sandostatin®, 8aa 환형 SS-bond 소마토스타틴 유사체):

```json
{
  "binary_toxicity": 1.0,
  "toxicity_type": "hemostasis",
  "toxicity_type_confidence": 1.0,
  "neurotoxicity_type": "Na_inhibitor",
  "neurotoxicity_confidence": 1.0,
  "hc50": -14.4873
}
```

Octreotide는 임상적으로 **안전한 승인 의약품**으로, hemostatic toxicity 또는 Na 채널 억제 독성이 없다. 동일한 confidence=1.0 패턴이 나타나는 것은 **모델의 체계적 OOD 오분류** 를 입증한다.

### 3.2 Confidence=1.0 기술적 원인

**Task 0 (binary_toxicity)**:
```python
bp = 1 / (1 + np.exp(-out["task_0"].item()))  # sigmoid
```
- 학습 도메인 외 입력이 GNN 특성 공간에서 극단적 raw_output 생성 → sigmoid saturation
- raw_output >> 0 → bp = 1.0 (float64 정밀도 한계)

**Task 1,2 (type classification)**:
```python
tp = torch.softmax(out["task_1"], dim=-1)[0].tolist()
# max(tp) = 1.0 when one logit >> others
```
- OOD 입력에서 특정 logit 폭발 → softmax concentration → confidence=1.0

**판정**: confidence=1.0은 **확실한 예측이 아니라 OOD 외삽 실패의 징표**.
신경망의 알려진 over-confidence 문제와 일치 (Guo et al. 2017, ICML; Lakshminarayanan 2017).

### 3.3 신뢰도 등급

| 지표 | 값 | 신뢰도 | 근거 |
|------|-----|--------|------|
| binary_toxicity | 1.00 | **HEURISTIC / OOD** | 학습 도메인 부재 |
| toxicity_type=hemostasis | conf=1.00 | **HEURISTIC / OOD** | Octreotide 교차검증 실패 |
| neurotoxicity=Na_inhibitor | conf=1.00 | **HEURISTIC / OOD** | 동일 |
| hc50 | -38 ~ -45 | **INVALID** | 물리적 불가능 (§4) |

---

## 4. hc50 단위·부호 해석

### 4.1 훈련 데이터 HC50 범위

| 통계 | 값 |
|------|-----|
| 샘플 수 | 15 |
| 최솟값 | **0.80** |
| 최댓값 | **2.61** |
| 음수 값 | **0건** |
| 단위 추정 | log₁₀(HC50 in μM) → 6.3~407 μM |

HC50 = Hemolytic Concentration 50% (용혈 농도). log₁₀ 스케일이면 훈련 범위 = 6.3~407 μM (일반적 항균·용혈 펩타이드 범위).

### 4.2 PRST 후보 HC50 예측값

| 후보 | 예측 hc50 | 만약 log₁₀(μM)이면 | 물리적 해석 |
|------|-----------|-------------------|------------|
| PRST-001 | -38.6135 | 10⁻³⁸·⁶ μM | **물리적 불가능** |
| PRST-002 | -41.7199 | 10⁻⁴¹·⁷ μM | **물리적 불가능** |
| PRST-003 | -43.6220 | 10⁻⁴³·⁶ μM | **물리적 불가능** |
| PRST-004 | -45.3764 | 10⁻⁴⁵·⁴ μM | **물리적 불가능** |
| Octreotide | -14.5 | 10⁻¹⁴·⁵ μM | **물리적 불가능** |

### 4.3 HC50 결론

1. 추론 스크립트는 HC50에 역정규화 적용 안 함 (`hc = out["task_3"].item()` 직접 사용)
2. 훈련 데이터 HC50 범위(0.8~2.61)와 예측값(-38~-45) 차이 = **약 40-48 단위** → 극단적 OOD 회귀 실패
3. 음수 HC50은 어떤 단위 해석에서도 물리적으로 불가능한 값
4. **HC50 값은 현재 pepADMET 로컬 추론에서 완전히 무효** (INVALID 등급)

**참고**: Wang (2026) 원 논문 pepADMET 웹 플랫폼의 HC50 정의는 별도 확인 필요 (§검증 필요).

---

## 5. 변이별 독성 예측 영향 분석

### 5.1 4 후보 변이 정리

| 후보 | 서열 | SST-14 대비 변이 | Exact MW |
|------|------|----------------|----------|
| PRST-001 | AGCKNI**I**WKT**I**TSC | N5→I(+F6), T8→I | 1534.8 |
| PRST-002 | AGCKNFI**W**KTITSC | base (F5 복구) | 1568.7 |
| PRST-003 | AGCR**N**FIWKTITSC | K4→R | 1596.8 |
| PRST-004 | A**I**CKNFIWKTITSC | G2→I | 1624.8 |

### 5.2 모델의 변이 구별력

4개 후보 모두:
- `binary_toxicity = 1.0`
- `toxicity_type = hemostasis`
- `toxicity_type_confidence = 1.0`
- `neurotoxicity_type = Na_inhibitor`
- `neurotoxicity_confidence = 1.0`

**단일 잔기 변이가 toxicity 예측에 전혀 영향을 주지 않음** → 모델이 sigmoid/softmax 포화 상태에 있어 섬세한 구조 차이를 구별하지 못함.

### 5.3 HC50 경향 분석

| 후보 | MW | hc50 | HC50 - MW 상관 |
|------|-----|------|-------------|
| PRST-001 | 1534.8 | -38.6 | |
| PRST-002 | 1568.7 | -41.7 | |
| PRST-003 | 1596.8 | -43.6 | |
| PRST-004 | 1624.8 | -45.4 | r ≈ -1.0 |

→ HC50 예측값이 MW와 완전한 음의 상관을 보임 (Δ MW +90 Da → Δ hc50 ≈ -6.8). 이는 회귀 헤드가 OOD 영역에서 MW와 같은 저차원 특성에 과적합된 외삽을 수행하고 있음을 시사함.

### 5.4 약리학 메커니즘 측면 평가

SST-14 유사체의 약리학 프로파일:
- **타겟**: SSTR2 (Gi-coupled GPCR) → cAMP 감소, K+ 채널 활성화, Ca²+ 채널 억제
- **예상 부작용**: GI (오심/구토), 담낭 결석 (장기), 혈당 변화
- **혈액응고(hemostasis) 관련성**: 문헌 증거 없음 (소마토스타틴 계열 화합물)
- **Na 채널 억제(Na_inhibitor) 관련성**: 문헌 증거 없음

→ pepADMET의 hemostasis/Na_inhibitor 분류는 **약리학 메커니즘과 불일치** — OOD 오분류 가설을 지지함.

---

## 6. 종합 신뢰도 평가표

| 지표 | 출처 | 신뢰도 | 판정 |
|------|------|--------|------|
| binary_toxicity=1.00 | pepADMET GNN sigmoid | **HEURISTIC / OOD** | Gate-2 hold 사유 |
| toxicity_type=hemostasis | pepADMET softmax(6) | **HEURISTIC / OOD** | Octreotide 교차검증 실패 |
| neurotoxicity=Na_inhibitor | pepADMET softmax(4) | **HEURISTIC / OOD** | 메커니즘 불일치 |
| hc50=-38~-45 | pepADMET 회귀 헤드 | **INVALID** | 물리적 불가능 |
| 의뢰서 ADMET 0.10~0.25 | composite_scorer fallback | **INVALID** | 실 추론값 아님 |

---

## 7. 권고사항

### 7-A. Gate-2 합성 발주 Hold (강권고)

**사유**:
1. binary_toxicity=1.00은 pepADMET OOD 외삽 아티팩트이며 실 독성 예측이 아님
2. Octreotide (FDA-승인) 동일 결과 → 모델의 체계적 편향 입증
3. 합성 의뢰서의 ADMET 0.10~0.25값은 composite_scorer wrapper 실패 시의 fallback 입력값으로 실측값이 아님
4. 신뢰할 수 있는 ADMET 예측이 현재 없는 상태

### 7-B. 즉시 수행 가능한 대안 검증 (병렬 진행 권장)

| 순위 | 검증 | 소요 | 신뢰도 |
|------|------|------|--------|
| 1 | **In vitro 용혈성 검사** (RBC hemolysis assay, 4 후보 중 2건) | 1-2주 | HIGH |
| 2 | **modlamp hemolysis 예측** (HemoPI/HemoPDB 학습, L-AA 선형 근사) | 즉시 | MED |
| 3 | **ADMET-AI 또는 SwissADME** (소분자용, 펩타이드 OOD 단서 별도 해석) | 즉시 | LOW |
| 4 | **Octreotide/Lanreotide 공개 hemolysis 데이터** 비교 (문헌) | 즉시 | REF |

### 7-C. pepADMET 파이프라인 보완 (중기)

1. `check_pepadmet_applicability()` 에 **cyclic SS-bond 감지 로직** 추가:
   - SMILES 내 `SS` 패턴 또는 `cyclic=True` 플래그 → `recommended=False`
   - 이유: 현재 함수는 D-AA와 DOTA만 감지, cyclic SS-bond 미감지
2. pharmacology_guards.py에 OOD 경고 신뢰도 등급 `INVALID` 추가 (현재는 HEURISTIC까지)
3. pepADMET 재훈련 시 SS-bond 14aa 유형 샘플 보강 (Octreotide, Lanreotide, 합성 SST 유사체)

---

## 8. §검증 필요

| 항목 | 이유 | 우선순위 |
|------|------|---------|
| Wang (2026) JCIM 원 논문 HC50 정의 (단위) | 로그 스케일 vs 선형 확인 필요 | HIGH |
| pepADMET 학습 데이터 내 D-AA 비율 | 비공개 (GitHub 기준 미기재) | MED |
| SST-14 자체 pepADMET 예측 | PRST 후보와 기저 비교용 | MED |
| 상업적 cyclic peptide toxicity DB (DBAASP, APD3) 비교 | 독립 검증 | MED |

---

## 부록: 학습 데이터 핵심 통계 요약

```
총 샘플: 135행 (train:45 / test:45 / valid:45)
binary toxicity 라벨: 30건 (toxic=15, non-toxic=15)
SS-bond 포함: 38건
  - binary label 있음: 1건 (50aa, toxic=1)
  - 14aa SS-bond binary label: 0건 ← PRST OOD 핵심 근거

HC50 범위 (훈련): 0.80 ~ 2.61 (양수, 15건)
HC50 예측 (PRST): -38.6 ~ -45.4 (음수, 물리적 불가능)
HC50 예측 (Octreotide): -14.5 (음수, 물리적 불가능)

hemostasis(type=4) 학습 예시 (n=9):
  - 14aa SS-bond: 0건
  - 15aa SS-없음: 1건 (가장 유사)

CLASS MAPPING:
  toxicity_type: [cytolysis, GPCR_toxin, neurotoxin, cytotoxicity, hemostasis, hemolysis]
  neurotoxicity_type: [AChR_inhibitor, Ca_inhibitor, K_inhibitor, Na_inhibitor]
```

---

**산출물 위치**: `_workspace/55_reviewer-pharma_prst-admet-ood-analysis.md`  
**작성자**: reviewer-pharma (selectivity-validation-20260520 팀)  
**다음 수신자**: team-lead (orchestrator)
