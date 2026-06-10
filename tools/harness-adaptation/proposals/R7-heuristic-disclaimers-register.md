# R7 — Stage 9 발견을 `HEURISTIC_FUNCTION_DISCLAIMERS`에 등록

> **Status**: 권고 보고 (코드 수정 X)
> **Priority**: Meta — Stage 5 절차 적용
> **출처**: Stage 9 dogfood §3 발견 1~6 + §5 권고 R7
> **관련 VR**: VR-cycle-09 (H-06) 운영 확장

---

## 1. 배경

VR-cycle-09 closure (v0.14.0)에서 도입한 `pharmacology_guards.py::HEURISTIC_FUNCTION_DISCLAIMERS`는 H-06 환각("계산 불가능한 것을 계산 가능한 척") 가드. 현재 5 entries:

```python
HEURISTIC_FUNCTION_DISCLAIMERS = {
    "pipeline_local.steps.step08_stability.predict_half_life": {...},
    "pipeline_local.steps.step08_stability.suggest_modifications": {...},
    "pipeline_local.steps.step08_stability._compute_stability_score": {...},
    "pipeline_local.steps.step08_stability._PROTEASE_VULNERABILITY": {...},
    "pyrosetta.pose_from_sequence_ideal_coord": {...},
}
```

Stage 9 dogfood에서 발견된 6 critical 결함 중 **`HEURISTIC_FUNCTION_DISCLAIMERS`에 등록 안 된 영역**들이 환각의 통로가 됨:
- `compute_binding_ddg()` (R3): silent 0.0 fallback이 *진짜 binding affinity*인 척
- `step06_rosetta._cache_key` (R2): cache hit이 *진짜 새 계산*인 척
- ESMFold pLDDT (R4): 도메인 부적합 임계값이 *임상 의미*인 척
- Convergence trigger (R6): degraded mode가 *진짜 수렴*인 척

→ Stage 5 가드 절차의 *적용 영역 확장*이 필요.

## 2. 현재 상태 vs 제안

| 함수 | 현재 H-06 가드 | 제안 |
|------|----------|------|
| `predict_half_life` | ✅ 등록 (v0.14.0) | 유지 |
| `suggest_modifications` | ✅ 등록 | 유지 |
| `_compute_stability_score` | ✅ 등록 | 유지 |
| `_PROTEASE_VULNERABILITY` | ✅ 등록 (v0.15.0) | 유지 |
| `pose_from_sequence_ideal_coord` | ✅ 등록 (v0.15.0) | 유지 |
| **`compute_binding_ddg`** | ❌ 미등록 | **신규 등록 (R3 연계)** |
| **`step06_rosetta._cache_key`** | ❌ 미등록 | **신규 등록 (R2 연계)** |
| **`step04_qc.esmfold_plddt_gate`** | ❌ 미등록 | **신규 등록 (R4 연계)** |
| **`convergence.patience_trigger`** | ❌ 미등록 | **신규 등록 (R6 연계)** |
| **`step06_rosetta._determine_source`** | ❌ 미등록 | **신규 등록 (R5 연계)** |
| **`AG_src.llm.provider.VLLMProvider`** | ❌ 미등록 | **신규 등록 (R1 연계, degraded mode 가드)** |

## 3. 제안 등록 항목 (의사 코드)

```python
# pseudo-code (실제 add는 별도 PR)
HEURISTIC_FUNCTION_DISCLAIMERS.update({
    # R3 — Rosetta ddG silent fallback
    "pipeline_local.steps.step06_rosetta.compute_binding_ddg": {
        "surface_unit": "float (ddG kcal/mol-like)",
        "actual_meaning": "ref2015 score with silent 0.0 fallback path (Stage 9 F3 발견)",
        "limitations": (
            "PyRosetta API 호출 실패 시 silent 0.0 반환 의심 (R3). "
            "Boltz docking score와 비교 시 0.0이 비현실적이면 fail-loud 필요."
        ),
        "valid_use": "정상 호출 시 *상대* score 비교",
        "invalid_use": "0.0 결과를 임상 결합 친화도로 인용",
        "confidence_grade": "HEURISTIC",
        "fix_status": "VR-cycle-12 / R3 — 진단·fix PR 대기",
    },

    # R2 — Rosetta cache key collision
    "pipeline_local.steps.step06_rosetta._cache_key": {
        "surface_unit": "hash string",
        "actual_meaning": "cache key (R2에서 다른 시퀀스 충돌 발견)",
        "limitations": (
            "Stage 9 F2 — 서로 다른 시퀀스(var_012, var_024)가 동일 cache key 충돌. "
            "결과 신뢰성 0."
        ),
        "valid_use": "cache key 결정 후 sequence/receptor/config 모두 포함 검증된 경우",
        "invalid_use": "cache hit 결과를 무비판적으로 사용",
        "confidence_grade": "HEURISTIC",
        "fix_status": "VR-cycle-11 / R2 — 진단·fix PR 대기",
    },

    # R4 — ESMFold pLDDT threshold
    "pipeline_local.steps.step04_qc.esmfold_plddt_gate": {
        "surface_unit": "float pLDDT (0-100)",
        "actual_meaning": "ESMFold 신뢰도 ranking score (작은 cyclic peptide 도메인 부적합 가능)",
        "limitations": (
            "60.0 floor가 14aa cyclic peptide에 너무 엄격 (Stage 9 F4 iter02/03 0% PASS). "
            "absolute threshold 대신 *상대* (native -5) 또는 grade 권장."
        ),
        "valid_use": "큰 단백질 (>50aa) ranking",
        "invalid_use": "작은 cyclic peptide의 임상 신뢰도",
        "confidence_grade": "HEURISTIC",
        "fix_status": "VR-cycle-13 / R4 — calibrate PR 대기",
    },

    # R6 — Convergence detector degraded mode
    "pyrosetta_flow.convergence.ConvergenceDetector.evaluate": {
        "surface_unit": "boolean stop signal",
        "actual_meaning": "ddG patience trigger (LLM degraded mode 구분 불가)",
        "limitations": (
            "Stage 9 F6 — LLM 100% 실패 + Critic 폴백으로 동일 ddG → patience trigger. "
            "진짜 수렴이 아닌 silent stall."
        ),
        "valid_use": "LLM 정상 + critic 실 제안 후 ddG 정체 = 진짜 수렴 신호",
        "invalid_use": "LLM 폴백 비율 미확인 상태에서 patience trigger를 진짜 수렴으로 해석",
        "confidence_grade": "HEURISTIC",
        "fix_status": "VR-cycle-14 / R6 — degraded mode 구분 PR 대기",
    },

    # R5 — Source label
    "pipeline_local.steps.step06_rosetta._determine_source": {
        "surface_unit": "string ('silo_a' | 'silo_b' | 'dual')",
        "actual_meaning": "audit trail용 silo 분류 (Stage 9에서 --approach-b가 silo_a로 잘못 표기 발견)",
        "limitations": "Stage 9 F5 — 분기 함수가 --approach-b 처리 누락 의심",
        "valid_use": "fix 후 정확한 silo 추적",
        "invalid_use": "현재 source 필드를 audit 신뢰값으로 사용",
        "confidence_grade": "HEURISTIC",
        "fix_status": "R5 — fix PR 대기",
    },

    # R1 — LLM provider degraded mode
    "AG_src.llm.provider.VLLMProvider.call": {
        "surface_unit": "string (LLM response)",
        "actual_meaning": "vLLM 호출 (실패 시 silent rule-based 폴백)",
        "limitations": (
            "Stage 9 F1 — --llm-base-url 누락 시 vLLM 8000 connection refused 100%. "
            "모든 호출이 rule-based fallback. "
            "이후 Planner/Critic/Reporter 결과는 LLM 의미 부재."
        ),
        "valid_use": "정상 vLLM/ollama 연결 + fallback_ratio < 0.5",
        "invalid_use": "fallback 결과를 LLM 의미로 인용",
        "confidence_grade": "HEURISTIC",
        "fix_status": "VR-cycle-10 / R1 — auto-detect PR 대기",
    },
})
```

## 4. 회귀 테스트 (별도 PR)

```python
# pseudo-code
class TestStage9DerivedDisclaimers:
    """Stage 9 dogfood 발견들이 HEURISTIC_FUNCTION_DISCLAIMERS에 등록되어야."""

    @pytest.mark.parametrize("qualname", [
        "pipeline_local.steps.step06_rosetta.compute_binding_ddg",
        "pipeline_local.steps.step06_rosetta._cache_key",
        "pipeline_local.steps.step04_qc.esmfold_plddt_gate",
        "pyrosetta_flow.convergence.ConvergenceDetector.evaluate",
        "pipeline_local.steps.step06_rosetta._determine_source",
        "AG_src.llm.provider.VLLMProvider.call",
    ])
    def test_stage9_finding_registered(self, qualname):
        assert is_heuristic_function(qualname), (
            f"{qualname} 미등록 — Stage 9 dogfood 발견이 H-06 가드 누락"
        )
        entry = HEURISTIC_FUNCTION_DISCLAIMERS[qualname]
        assert entry["confidence_grade"] == "HEURISTIC"
        # 각 entry는 본 발견의 fix_status 명시
        assert "R1" in entry["fix_status"] or "R2" in entry["fix_status"] or \
               "R3" in entry["fix_status"] or "R4" in entry["fix_status"] or \
               "R5" in entry["fix_status"] or "R6" in entry["fix_status"]
```

## 5. 위험·트레이드오프

| 위험 | 완화 |
|------|------|
| HEURISTIC_FUNCTION_DISCLAIMERS가 너무 커짐 (현재 5 + 신규 6 = 11) | 카테고리화 (`pharmacology_*`, `pyrosetta_*`, `llm_*`) |
| 등록만 하고 실제 가드 적용 안 됨 | reviewer-pharma + reviewer-code 검토 가이드에 *호출 시 disclaimer 의무 확인* 추가 |
| 모든 휴리스틱 함수 등록하면 신뢰값 없음으로 보임 | "valid_use" 필드로 적절한 사용 방향 제시 |

## 6. 의존 관계

- **R1~R6 fix가 진행되면** 각 fix_status가 "fix PR 대기" → "fixed (PR #N)"로 update
- 본 권고는 *Stage 5 환각 가드 절차의 운영 확장*이지 *기존 fix 대체* 아님
- 본 권고가 먼저 머지되면 R1~R6 fix PR이 disclaimer를 *참조*할 수 있음

## 7. 예상 영향 메트릭 (fix 후)

| 메트릭 | 현재 | 예상 |
|--------|------|------|
| HEURISTIC_FUNCTION_DISCLAIMERS entries | 5 | 11 (+6) |
| Stage 9 발견 가드 커버리지 | 0/6 (F1~F6 미등록) | 6/6 |
| reviewer-pharma 검토 시 H-06 catch율 | 30% (기존 함수만) | 90% (Stage 9 영역까지) |

## 8. 추적

- 본 권고가 R1~R6의 *환각 가드 측면 보완*
- Stage 9 보고서 §5 R7

---

**End of R7 Proposal Report.**
