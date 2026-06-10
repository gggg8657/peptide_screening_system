# PR #82 최종 승인 보고서 — G-2 margin 부호 컨벤션 통일

**브랜치**: `chore/g2-margin-convention-20260520`  
**최종 커밋**: `c32c718` (3차 제출)  
**검토 일시**: 2026-05-20  
**검토자**: tester  

---

## 1. 요약

**판정**: ✅ **APPROVE**

3차 제출에서 2차 REQUEST_CHANGES의 모든 이슈(K-1/K-2 Critical + 5개 Medium)가 정확하게 수정됨.  
코드 정확성, 게이트 방향, 랭킹 기여, 문서 일관성 모두 G-2 SSOT(`양수=좋음`) 기준으로 통일됨.

---

## 2. 전체 이슈 해결 확인 이력

| 라운드 | 이슈 | 파일:라인 | 상태 |
|--------|------|----------|------|
| 1차 | C-1 수식 반전 | `run_pipeline_live.py:783` | ✅ |
| 1차 | C-2 게이트 조건 | `run_pipeline_live.py:792` | ✅ |
| 1차 | C-3 fallback 10.0 | `run_pipeline_live.py:723` | ✅ |
| 1차 | C-4 criterion ">=" | `run_pipeline_live.py:838` | ✅ |
| 1차 | H-1 수식 | `run_pipeline_demo.py:165` | ✅ |
| 1차 | H-2 게이트 | `run_pipeline_demo.py:166` | ✅ |
| 1차 | H-3 임계값 | `run_pipeline_demo.py:267-268` | ✅ |
| 1차 | Medium-1~3 | README/PIPELINE_GUIDE 일부 | ✅ |
| **2차** | **K-1 Gate4 반전** | **`qc_ranker.py:259`** | ✅ |
| **2차** | **K-2 invert 반전** | **`qc_ranker.py:334`** | ✅ |
| 2차 | M-1 orchestrator fallback | `orchestrator.py:606-607` | ✅ |
| 2차 | M-2~6 README 잔존 5곳 | `README.md:133,135,149,171,184` | ✅ |
| 2차 | M-7 PIPELINE_GUIDE 예시 | `PIPELINE_GUIDE.md:818` | ✅ |

---

## 3. 3차 수정 코드 직접 확인

### K-1 — `qc_ranker.py:259` ✅

```python
# G-2: 양수=좋음 컨벤션 — margin < sel_margin_min 이면 탈락
if c.selectivity_margin != 0.0 and c.selectivity_margin < sel_margin_min:
    c.fail_reasons.append(
        f"selectivity_margin {c.selectivity_margin:.2f} < {sel_margin_min}"
    )
```

- 조건 방향 정상 (`<` = 임계값 미달 시 탈락)
- fail_reasons 텍스트도 `<` 로 일치 ✅

### K-2 — `qc_ranker.py:334-335` ✅

```python
norm_sel = _normalize(sel_vals, invert=False)  # G-2: 높을수록 좋음 (양수=더 선택적)
```

- `invert=False`: 높은 margin → 높은 정규화 점수 → 높은 final_score ✅
- 주석도 G-2 컨벤션 명시 ✅

### orchestrator.py:606-607 ✅

```python
"selectivity_margin_min": self.gate_thresholds.get("selectivity_margin_min", 10.0),   # G-2: 양수=좋음
"offtarget_max_allowed": self.gate_thresholds.get("offtarget_max_allowed", -15.0),
```

### README.md 수정 ✅

| 라인 | 수정 내용 |
|------|---------|
| 133 | 방향: `더 양수일수록 좋음 (G-2 SSOT)` |
| 135 | 게이트 기준: `>= 10.0 kcal/mol` |
| 149 | 해석: `마진 +10이면 ... (양수=좋음; G-2 SSOT)` |
| 171 | 공식: `+ selectivity_margin * 0.20` (부호 반전 제거) |
| 184 | 해석: `양수 selectivity margin(G-2 SSOT)` |

### PIPELINE_GUIDE.md:818 ✅

```yaml
selectivity_margin_min: 12.0      # 10.0 → 12.0 (선택성 강화; G-2: 양수=좋음)
```

---

## 4. 테스트 결과

```
AG_src/tests/test_selectivity.py             23/23 PASS
pipeline_local/tests/test_step05b_selectivity.py  38/38 PASS
```

신규 `TestQCRankerGate4G2` (3개) 모두 PASS:
- `test_k1_high_margin_passes_gate4`: margin=+15 >= 10.0 → PASS ✅
- `test_k1_low_margin_fails_gate4`: margin=+5 < 10.0 → FAIL + fail_reasons ✅
- `test_k2_higher_margin_gets_higher_final_score`: margin+15 final_score > margin+5, rank[0]="good" ✅

---

## 5. 비고

- `qc_ranker.py:80` `datetime.utcnow()` DeprecationWarning: G-2 PR과 무관한 기존 이슈 (별도 처리 권장)
- G-2 SSOT(`양수=좋음`) 컨벤션이 파이프라인 전체에 일관되게 적용됨
  - `step05b_selectivity.py` → `qc_ranker.py` → `orchestrator.py` → `run_pipeline_live.py` → YAML → 문서

**병합 승인.**
