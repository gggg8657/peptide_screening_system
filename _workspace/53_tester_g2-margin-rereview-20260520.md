# PR #82 재검토 보고서 — G-2 margin 부호 컨벤션 통일

**브랜치**: `chore/g2-margin-convention-20260520`  
**검토 대상 커밋**: `d9107dc` (2차 제출) + `cff60a0` (1차)  
**검토 일시**: 2026-05-20  
**검토자**: tester  

---

## 1. 요약

**판정**: ❌ **REQUEST_CHANGES (2차)**

1차 REQUEST_CHANGES에서 지적한 C-1~C-4 (Critical) 및 H-1~H-3 (High) 이슈는 전부 수정 확인됨.  
그러나 **`qc_ranker.py`에서 기존 부호 컨벤션을 그대로 유지하는 Critical 회귀 버그 2건**이 신규 발견됨.  
Gate 4 조건과 selectivity 기여 방향이 모두 반전된 상태로, 병합 불가.

---

## 2. 수정 확인 내역 (1차 이슈)

| 이슈 | 위치 | 수정 내용 | 상태 |
|------|------|----------|------|
| C-1 | `run_pipeline_live.py:783` | `margin = worst_ot - sstr2_ddg` | ✅ FIXED |
| C-2 | `run_pipeline_live.py:792` | `passed=(margin >= sel_margin_min)` | ✅ FIXED |
| C-3 | `run_pipeline_live.py:723` | fallback `10.0` | ✅ FIXED |
| C-4 | `run_pipeline_live.py:838` | criterion `">="` | ✅ FIXED |
| H-1 | `run_pipeline_demo.py:165` | `margin = round(worst - dr.score, 2)` | ✅ FIXED |
| H-2 | `run_pipeline_demo.py:166` | `passed = margin >= 10.0 and worst >= -15.0` | ✅ FIXED |
| H-3 | `run_pipeline_demo.py:267-268` | `10.0 / -15.0` | ✅ FIXED |
| Medium-1 | `README.md:141` | 수식 `ddG(최악의 off-target) - ddG(SSTR2)` | ✅ FIXED |
| Medium-2 | `PIPELINE_GUIDE.md:295` | `selectivity_margin_min: 10.0` | ✅ FIXED |
| Medium-3 | `PIPELINE_GUIDE.md:402` | `마진 >= 10.0` | ✅ FIXED |

---

## 3. Critical 이슈 (신규 발견)

### K-1 — `qc_ranker.py:259` Gate 4 조건 반전 [HIGH IMPACT]

**파일**: `AG_src/agents/qc_ranker.py:259`  
**신뢰 등급**: HIGH (직접 코드 확인)

```python
# 현재 코드 (WRONG — 新컨벤션과 반전)
if c.selectivity_margin != 0.0 and c.selectivity_margin > sel_margin_min:
    c.fail_reasons.append(...)
```

**문제**: `gate_thresholds.yaml`의 `selectivity_margin_min = 10.0`과 조합 시:
- margin = +15 (우수한 선택성) → `15 > 10.0` → **FAIL** ← 완전히 반전!
- margin = +5 (불량 선택성) → `5 > 10.0` is False → **PASS** ← 오통과

**의도된 동작** (新컨벤션): `margin < sel_margin_min` 이면 탈락

```python
# 수정 필요
if c.selectivity_margin != 0.0 and c.selectivity_margin < sel_margin_min:
    c.fail_reasons.append(
        f"selectivity_margin {c.selectivity_margin:.2f} < {sel_margin_min}"
    )
```

**원인**: G-2 PR이 `gate_thresholds.yaml`의 임계값만 변경했으나, `qc_ranker.py`의 gate 비교 방향(`>` → `<`)은 미변경.

---

### K-2 — `qc_ranker.py:334` 정규화 방향 반전 [HIGH IMPACT]

**파일**: `AG_src/agents/qc_ranker.py:334`  
**신뢰 등급**: HIGH (직접 코드 확인)

```python
# 현재 코드 (WRONG)
norm_sel = _normalize(sel_vals, invert=True)     # 낮을수록 좋음 (더 선택적)
```

**문제**: 新컨벤션에서 높은 양수 margin = 좋음. `invert=True`는:
- margin = +15 (우수) → normalized=1.0 → `1.0-1.0=0.0` → 최종 점수 기여 **최저**
- margin = +5 (불량) → normalized=0.0 → `1.0-0.0=1.0` → 최종 점수 기여 **최고**

선택성이 우수한 후보가 ranking에서 페널티를 받음. `gate_thresholds.yaml`의 `direction: "higher_is_better"` 와도 모순.

```python
# 수정 필요
norm_sel = _normalize(sel_vals, invert=False)    # 높을수록 좋음 (G-2: 양수=좋음)
```

---

## 4. Medium 이슈 (신규 발견, 비블로킹)

### M-1 — `orchestrator.py:606-607` fallback 기본값 구버전

**파일**: `AG_src/pipeline/orchestrator.py:606-607`

```python
# 현재
"selectivity_margin_min": self.gate_thresholds.get("selectivity_margin_min", -2.0),  # -2.0 구버전
"offtarget_max_allowed": self.gate_thresholds.get("offtarget_max_allowed", -3.0),    # -3.0 구버전
```

YAML 미로드 시 `-2.0`/`-3.0` (구버전 기본값) 사용. 新컨벤션 기본값(`10.0`/`-15.0`)으로 교체 필요.

---

### M-2 — `README.md` 여러 위치 구버전 컨벤션 잔존

| 라인 | 현재 내용 | 수정 필요 |
|------|---------|---------|
| L135 | `<= -10.0 kcal/mol` (게이트 기준) | `>= 10.0 kcal/mol` |
| L149 | "마진 -10이면 SSTR2 결합이 최고 off-target보다 10 kcal/mol 더 강함. 매우 큰 **음수** 마진(-2000+)..." | **양수** 마진(+2000+) 방향으로 수정 |
| L171 | `+ (-selectivity_margin) * 0.20` | `+ selectivity_margin * 0.20` |
| L184 | "**음수** selectivity margin을 가진 후보가 최상위" | "**양수** selectivity margin" |

---

### M-3 — `PIPELINE_GUIDE.md:818` 예시 설정 구버전

```yaml
# 현재 (WRONG — 구버전 음수 임계값)
selectivity_margin_min: -3.0      # -2.0 → -3.0 (선택성 강화)
```

新컨벤션에서 선택성 강화 = 양수 임계값 상향. 예: `12.0` 또는 `15.0`.

---

## 5. 테스트 커버리지 갭

- `qc_ranker.py` Gate 4 방향을 검증하는 테스트 **없음**  
  → K-1/K-2 회귀가 29/29 PASS에서 검출되지 않은 원인
- 수정 후 아래 테스트 케이스 추가 필요:

```python
def test_gate4_passes_high_positive_margin():
    """margin = +15, threshold = 10.0 → PASS"""
    c = Candidate(..., selectivity_margin=+15.0)
    result = ranker._apply_gates([c], thresholds={"selectivity_margin_min": 10.0})
    assert c not in result.failed

def test_gate4_fails_low_margin():
    """margin = +5, threshold = 10.0 → FAIL"""
    c = Candidate(..., selectivity_margin=+5.0)
    result = ranker._apply_gates([c], thresholds={"selectivity_margin_min": 10.0})
    assert c in result.failed

def test_ranking_higher_margin_gets_higher_score():
    """margin +15 candidate outranks margin +5 candidate"""
    ...
```

---

## 6. 수정 요청 요약

| 우선순위 | 파일 | 라인 | 변경 내용 |
|---------|------|------|---------|
| **Critical** | `qc_ranker.py` | 259 | `> sel_margin_min` → `< sel_margin_min` (게이트 조건 반전 수정) |
| **Critical** | `qc_ranker.py` | 334 | `invert=True` → `invert=False` (정규화 방향 수정) + 주석 수정 |
| Medium | `orchestrator.py` | 606-607 | fallback `-2.0`→`10.0`, `-3.0`→`-15.0` |
| Medium | `README.md` | 135,149,171,184 | 구버전 부호 컨벤션 텍스트 정정 |
| Medium | `PIPELINE_GUIDE.md` | 818 | 예시 설정 구버전 값 수정 |

**Critical 2건(K-1,K-2) 수정 후 재제출 바랍니다.**  
테스트 커버리지(Gate4 방향, ranking 방향) 추가도 함께 요청드립니다.
