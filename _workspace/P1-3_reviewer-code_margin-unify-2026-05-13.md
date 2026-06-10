# P1-3: selectivity_margin 부호 통일 보고서

**작성**: reviewer-code  
**날짜**: 2026-05-13  
**Phase**: Phase 1 #3  
**상태**: ✅ 완료 — 26/26 테스트 통과

---

## 1. 문제 배경

| 모듈 | 공식 | 부호 | "선택적"의 의미 |
|------|------|------|----------------|
| step05b (변경 전) | `sstr2_ddG - max(off_ddG)` | 음수 | margin ≤ -10 → SSTR2 선택적 |
| step05c | `iPTM(SSTR2) - max(iPTM(off))` | 양수 | margin ≥ +0.03 → T3 (선택적) |

UI 통합 시 동일 `selectivity_margin` 필드를 반대 부호로 해석해야 하는 문제.

---

## 2. 결정 — step05c 기준으로 통일

**새로운 공식 (step05b):**
```
margin = max(ddG_off-target) - ddG(SSTR2)
```

**부호 의미:**
- `margin > 0` : SSTR2가 best off-target보다 강하게 결합 → **선택적** (good)
- `margin < 0` : off-target이 SSTR2보다 강하게 결합 → **비선택적** (bad)

**예시:**
```
SSTR2 ddG = -30 kcal/mol
best off-target (SSTR3) ddG = -20 kcal/mol

margin = -20 - (-30) = +10 → SSTR2 10 kcal/mol 더 선택적 ✓
```

---

## 3. 변경 파일 요약

### 3-1. `pipeline_local/steps/step05b_selectivity.py`

| 위치 | 변경 전 | 변경 후 |
|------|---------|---------|
| 모듈 docstring (L13-17) | `margin = SSTR2 - max(off)`, `lower = selective` | `margin = max(off) - SSTR2`, `higher = selective` |
| `run_selectivity_screening` default (L138) | `margin_min = -2.0` | `margin_min = 2.0` |
| `compute_selectivity_margin` default (L352) | `margin_min = -2.0` | `margin_min = 2.0` |
| `compute_selectivity_margin` 공식 (L389) | `margin = sstr2_score - worst_score` | `margin = worst_score - sstr2_score` |
| gate 조건 (L394) | `margin <= margin_min` | `margin >= margin_min` |
| gate 조건 comment (L392-393) | "must be <= margin_min" | "must be >= margin_min (SSTR2 sufficiently stronger)" |
| `apply_selectivity_gate` default (L413) | `margin_min = -2.0` | `margin_min = 2.0` |

### 3-2. `pipeline_local/config/gate_thresholds.yaml`

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| `selectivity_margin_min` | `-10.0` | `10.0` |
| 부호 규칙 주석 | "margin <= -10 = 우수한 선택성" | "margin >= +10 = 우수한 선택성" |
| 공식 주석 | `margin = ddG(SSTR2) - ddG(off-target)` | `margin = max(ddG_off-target) - ddG(SSTR2)` |
| `final_score_weights.selectivity.direction` | `"lower_is_better"` | `"higher_is_better"` |

### 3-3. `pipeline_local/tests/test_step05b_selectivity.py` (신규)

26개 테스트, 6개 클래스:

| 클래스 | 테스트 수 | 목적 |
|--------|-----------|------|
| `TestComputeSelectivityMargin` | 9 | margin 공식·부호·경계값 검증 |
| `TestApplySelectivityGate` | 4 | 통과/탈락 분류 검증 |
| `TestRunSelectivityScreening` | 2 | estimation mode smoke test |
| `TestSchemaRoundtrip` | 3 | 직렬화 라운드트립 |
| `TestSignConventionAlignment` | 5 | step05b vs step05c 부호 일관성 |
| `TestGateThresholdsYaml` | 3 | gate_thresholds.yaml 값 검증 |

---

## 4. 테스트 결과

```
26 passed in 0.20s
```

**핵심 케이스 확인:**

```python
# SSTR2 강 결합 → 양수 margin → 통과
compute_selectivity_margin("x", sstr2_score=-30.0, {"SSTR1": -20.0},
                           margin_min=10.0, offtarget_max_allowed=-25.0)
# → margin = -20 - (-30) = +10.0 ✓, passed=True ✓

# off-target 강 결합 → 음수 margin → 탈락
compute_selectivity_margin("x", sstr2_score=-10.0, {"SSTR3": -30.0}, margin_min=2.0)
# → margin = -30 - (-10) = -20.0 ✓, passed=False ✓

# step05b vs step05c 부호 일관성
margin_05b > 0  ↔  SSTR2 선택적  ↔  step05c margin > 0 (T2/T3) ✓
```

---

## 5. 영향 분석

### 5-1. 기존 runs_local 데이터

모든 정식 run의 `05b_selectivity/` 디렉토리가 비어 있음 (M2 검증 C-1: save 미호출).  
따라서 **기존 저장 데이터와의 호환성 문제 없음** — 변경 전 실제 파일이 존재하지 않음.

### 5-2. 이미 작성된 보고서 (어제)

`META_stability_halflife_integrated.md`, `STABILITY_HALFLIFE_explainer.md`,  
6-Round selectivity 보고서 — 모두 step05c iPTM 기반(양수 = 선택적) 컨벤션으로 작성됨.  
**변경 후 step05b도 동일 방향 → 보고서 수정 불필요** ✓

### 5-3. UI 영향

`SelectivityResult.selectivity_margin` 양수 ↔ 선택적 → UI 색상 로직 수정 필요:

```
변경 전: margin < -10.0 → 초록 (선택적)
변경 후: margin > +10.0 → 초록 (선택적)
```

`final_score_weights.selectivity.direction = "higher_is_better"` 로 UI 정규화 로직도 자동 반영 가능.

### 5-4. `offtarget_max_allowed` 게이트 — 변경 없음

`worst_score >= offtarget_max_allowed` 조건은 변경 없음.  
의미: "best off-target ddG가 -15 kcal/mol보다 좋으면(더 음수면) 탈락"  
→ 이 조건은 margin 부호와 독립적으로 유지됨.

---

## 6. 주의: offtarget_max_allowed 현실적 값

현재 `offtarget_max_allowed = -15.0` (gate_thresholds.yaml).  
estimation mode에서 off-target 스코어는 `base_score + abs(offset)` (on_target보다 덜 음수).  
실제 ddG 예상 범위: SSTR2 -20~-36, off-target -5~-15 → `-15.0` 적절.  

그러나 테스트에서 확인된 것처럼, 실제 ddG 값 범위(-20)에서 `offtarget_max_allowed=-15.0`는  
**정상 off-target도 탈락**시킬 수 있음. 실측 ddG 수집 후 임계값 보정 권장.

---

## 7. 변경 diff 요약

```
pipeline_local/steps/step05b_selectivity.py   │ 공식 반전 + default 2.0
pipeline_local/config/gate_thresholds.yaml    │ -10.0 → 10.0 + direction 수정
pipeline_local/tests/test_step05b_selectivity.py │ 신규 (26 tests, 전체 통과)
```
