# R6 — Convergence detector degraded-mode 구분

> **Status**: 권고 보고 (코드 수정 X)
> **Priority**: Medium
> **출처**: Stage 9 dogfood §3 발견 6
> **관련 VR**: VR-cycle-14

---

## 1. 현재 상태

Stage 9 dogfood 진행:
```
iter01 → iter02: ddG delta=0.000 < 0.500
iter02 → iter03: ddG delta=0.000 < 0.500. patience 1/2
iter03 → patience 2/2. Pipeline COMPLETE (Converged: False)
```

**Convergence detector는 의도대로 작동** — ddG 개선 없음 → patience trigger → early stop.

**그러나 실제로는**:
- LLM provider 100% 실패 (vLLM 8000 connection refused, R1)
- Critic이 모든 iteration에서 "0개 변경 제안, 가설: 이전 동일 파라미터로 재현성 확인"
- Iteration 간 다양성 0 → ddG도 동일 (또는 cache hit으로 0.0)
- Patience trigger = *진짜 수렴*이 아닌 *LLM 부재로 인한 정체* (degraded mode)

→ **Detector가 두 상태를 구분 못 함**:
- 정상: critic이 실 변경을 제안했고, 변경 후에도 ddG 개선 없음 = 진짜 수렴
- Degraded: LLM 실패로 critic fallback → 0 제안 → ddG 같음 = silent stall

## 2. 영향 (정량)

| 영향 | 정량 |
|------|------|
| 운영자 인지 | "Converged: False" + patience 2/2 — 정상처럼 보임 |
| 자원 사용 | 3 iter × ~3분 = ~10분 silent stall (5 iter 의도) |
| 결과 신뢰도 | 0 — degraded mode 산출물은 분석 가치 X |
| 사후 추적 | scenario report 작성하면서야 인지 (사후) |

→ **시스템이 *정직하게 보고했지만 *조기에* 알리지 못함**. 사용자가 사후에야 LLM 부재 발견.

## 3. 진단 가설

### 가설 A — LLM 실패율 모니터링 부재

`AG_src/llm/provider.py`나 orchestrator가 LLM 호출 실패를 *각 호출마다* 카운트하지만, **누적 비율**을 convergence detector에 신호로 보내지 않음. patience 카운트만으로 종료.

### 가설 B — Critic의 "0 제안" + "동일 파라미터 가설"이 정상 응답으로 해석

Critic 폴백 로직: "LLM 실패 → 0개 변경 제안, 이전 동일 파라미터로 재현성 확인" — 이 출력이 *진짜 critic의 판단*과 동일한 의미로 처리됨. degraded mode 신호 부재.

### 가설 C — Convergence detector의 input이 ddG delta만

```python
# pseudo-code
def should_stop(prev_ddg, current_ddg, patience):
    if abs(current_ddg - prev_ddg) < 0.5:
        patience += 1
    if patience >= 2:
        return True
    return False
```

→ ddG 정체만 보고, *어떤 critic 출력이 그 정체를 만들었는지*는 모름.

## 4. 제안 fix 방향 (코드 변경은 별도 PR)

### 4-1. Provider 폴백률을 convergence 신호로 통합

```python
# pseudo-code
class LLMProvider:
    _call_count = 0
    _fail_count = 0

    @property
    def fallback_ratio(self):
        return self._fail_count / max(1, self._call_count)


class ConvergenceDetector:
    def evaluate(self, iter_data, llm_provider):
        # 1. LLM 폴백률 체크
        if llm_provider.fallback_ratio > 0.5:
            return ConvergenceResult(
                stop=True,
                reason="LLM_DEGRADED",
                message=(
                    f"LLM provider 폴백률 {llm_provider.fallback_ratio:.0%}. "
                    "수렴 판정 불가. --llm-base-url 또는 --ollama-host 확인."
                ),
            )
        # 2. 기존 ddG patience 로직
        ...
```

### 4-2. Critic 폴백 출력에 명시적 degraded 플래그

```python
# pseudo-code
def critic_analyze(iter_data, llm_provider):
    try:
        result = llm_provider.analyze(iter_data)
        return result
    except LLMError:
        return CriticResult(
            param_changes=[],
            hypothesis="이전 iteration과 동일한 파라미터로 재현성 확인",
            degraded_mode=True,  # ← 신규 플래그
        )

# Orchestrator
if critic_result.degraded_mode:
    convergence.degraded_mode_count += 1
```

### 4-3. Pipeline 종료 시 보고서에 명시적 reason

```python
# pseudo-code
final_report = {
    "converged": False,
    "stop_reason": "LLM_DEGRADED",  # ← "PATIENCE_EXCEEDED"가 아닌 명시 이유
    "llm_fallback_ratio": 1.0,
    "recommendation": "see R1 (LLM base_url) for fix",
}
```

## 5. 위험·트레이드오프

| 위험 | 완화 |
|------|------|
| LLM 폴백률 threshold (50%)가 도메인마다 다름 | config화 (`convergence.llm_fallback_max: 0.5`) |
| Degraded mode 신호가 *진짜 LLM 우수 critic*의 "0 제안"과 혼동 | critic_result에 degraded_mode 플래그 명시 (4-2) |
| Convergence detector가 LLM provider를 직접 참조 → 결합도 ↑ | Interface로 추상화 (`FallbackAwareProvider`) |

## 6. 의존 관계

- **R1 (LLM base_url)** 와 강한 시너지: R1이 LLM 부재를 *조기 catch*, R6이 *그래도 진입한 경우* 안전망
- 독립적으로도 fix 가능

## 7. 예상 영향 메트릭 (fix 후)

| 메트릭 | 현재 | 예상 |
|--------|------|------|
| Stage 9-style dogfood에서 degraded mode 인지 | 0% (사후) | 100% (iter 1 직후) |
| Silent stall 자원 낭비 | ~10분 (3 iter × 3) | <5분 (iter 1 후 정지) |
| 사용자에게 명시적 fix 권고 (R1 참조) | 없음 | log + final_report |

## 8. 추적

- Stage 9 보고서 §3 F6

---

**End of R6 Proposal Report.**
