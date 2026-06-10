# R4 — ESMFold pLDDT 임계값 domain-calibrate

> **Status**: 권고 보고 (코드 수정 X)
> **Priority**: High
> **출처**: Stage 9 dogfood §3 발견 4
> **관련 VR**: VR-cycle-13

---

## 1. 현재 상태 (문제 진단)

Stage 9 dogfood iter02/03에서 ESMFold pLDDT ≥ 60 임계값 적용 결과:

| iter | n_variants | QC PASS | PASS 비율 | 설명 |
|------|---------|---------|---------|------|
| 1 | 44 | 5 | 11.4% | 5개 통과 (var_012/024/025/026/027) pLDDT 60~70 범위 |
| 2 | 44 | 0 | 0% | 전수 < 60.0 |
| 3 | 44 | 0 | 0% | 전수 < 60.0 |

**iter01 통과 변이체 pLDDT**:
```
var_012: 62.64
var_024: 64.19
var_025: 67.10
var_026: 69.62
var_027: 60.02
```

거의 모두 60대 초반. 14aa 작은 cyclic peptide (SST-14)에서 **ESMFold가 본질적으로 낮은 pLDDT를 산출**하는 경향.

## 2. 영향 (정량)

| 영향 | 정량 |
|------|------|
| Stage 9 iter02/03 ESMFold gate | 0/44 = 0% — 도킹 단계 진입 못 함 |
| 변이체 다양성 손실 | 변이마다 pLDDT가 native ±5 범위로 분포 — 임계값이 60 absolute floor면 분포 cutoff |
| 결과 신뢰도 | 통과한 5개도 pLDDT 60대 — ESMFold "low confidence" 영역 |

→ **임계값이 *작은 cyclic peptide 도메인*에 부적합**. 큰 단백질용으로 calibrate된 ESMFold pLDDT 60 floor를 그대로 적용.

## 3. 진단 가설

### 가설 A — 작은 cyclic peptide 특성

ESMFold는 50aa 이상의 protein domain에 강하지만, 14aa cyclic peptide(SS bond 포함)는 학습 데이터 분포 외. SST-14 native 자체가 pLDDT ~65 추정.

### 가설 B — pLDDT *interface*가 평균값과 동일

`qc_summary.json`을 보면 `plddt_mean == plddt_interface` (예: var_012 둘 다 62.64). 작은 펩타이드에서는 전체 잔기가 interface라서 동일. 큰 단백질의 interface 분리 개념과 다름.

### 가설 C — Threshold 60.0이 "임상 의미"가 아닌 "휴리스틱"

`pipeline_config_local.yaml` 또는 ESMFold step 코드에 `plddt>=60.0, iface>=45.0` floor. 이 60.0은 어디서 왔는지? — 큰 단백질 best practice일 가능성. 본 도메인에 calibrate된 적 없음.

## 4. 제안 fix 방향 (코드 변경 X)

### 4-1. SST-14 native pLDDT 측정 → 그 값 기반 *상대* threshold

```python
# pseudo-code
# 한 번 실행: SST-14 native AGCKNFFWKTFTSC의 ESMFold pLDDT 측정
NATIVE_PLDDT = 65.0  # 측정 결과 (예시 — 실 측정 필요)

# Threshold: native -5 또는 native × 0.9
PLDDT_THRESHOLD = NATIVE_PLDDT - 5  # 60.0 (현재값과 우연 일치)
# 또는 PLDDT_THRESHOLD = NATIVE_PLDDT * 0.9 = 58.5
```

### 4-2. `pharmacology_guards.py SCALE_RANGES`에 카테고리 추가 (R7과 연계)

```python
SCALE_RANGES = {
    ...
    # VR-cycle-13 closure: 작은 cyclic peptide ESMFold pLDDT 범위
    "esmfold_plddt_sst14_class": (50.0, 80.0),  # 14aa cyclic SS bond peptide
    "esmfold_plddt_threshold_default_protein": (60.0, 90.0),  # 큰 단백질
}
```

### 4-3. config에 도메인-specific threshold

```yaml
# pipeline_config_local.yaml (가설)
qc:
  esmfold_plddt_threshold: 60.0  # 현재
  # 권고:
  esmfold_plddt_threshold_small_cyclic_peptide: 55.0
  esmfold_plddt_threshold_default: 60.0
  domain_class: "small_cyclic_peptide"  # SST-14 class
```

### 4-4. Multi-tier gate (대신)

```python
# pseudo-code: 단일 cutoff 대신 grade
def esmfold_grade(plddt):
    if plddt >= 70: return "high"
    elif plddt >= 60: return "medium"
    elif plddt >= 50: return "low"
    else: return "fail"

# 후속 단계에서 grade 기반 우선순위 (high → docking 우선, low → cutoff)
```

## 5. 위험·트레이드오프

| 위험 | 완화 |
|------|------|
| 임계값 낮춤으로 false positive (잘못된 fold 통과) | 후속 단계(docking, Rosetta)가 필터링 — 본 gate는 *예비* 역할 |
| 도메인-specific threshold 가 다른 시퀀스에 잘못 적용 | config의 `domain_class` 명시 + LITERATURE_VALUES 등록 |
| SST-14 native pLDDT 측정 한 번이 calibration baseline이 되는 *환각 위험* (R7) | 측정 결과의 confidence 등급 명시. Native 자체가 ESMFold heuristic이지 실 구조 X |

## 6. 의존 관계

- **R7 (HEURISTIC_FUNCTION_DISCLAIMERS)**: ESMFold pLDDT를 가드에 등록 — VR-cycle-09 H-06 정신 적용 (pLDDT는 신뢰 가능 metric이 아닌 *heuristic ranking*)
- R1~R3과 독립

## 7. 검증 방법 (별도 PR에서)

1. SST-14 native AGCKNFFWKTFTSC를 ESMFold로 fold → pLDDT 측정 (1회)
2. Stage 9-style dogfood 재실행 — 새 threshold로 PASS 비율 증가 확인
3. False positive 측정 (low pLDDT 통과 후 docking에서 어떻게 동작)

## 8. 예상 영향 메트릭 (fix 후)

| 메트릭 | 현재 | 예상 |
|--------|------|------|
| Stage 9 iter02/03 ESMFold PASS | 0/44 | 10-20/44 (threshold 55 적용 시) |
| 후속 docking 진입 변이체 | 5/44 (iter01만) | 10-20/44 |
| 운영자 인지 | 0/44 silent fail | log + grade 분포 |

## 9. 추적

- Stage 9 보고서 §3 F4

---

**End of R4 Proposal Report.**
