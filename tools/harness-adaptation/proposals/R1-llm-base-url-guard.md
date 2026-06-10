# R1 — LLM base_url 옵션 의무화·자동 detect

> **Status**: 권고 보고 (코드 수정 X)
> **Priority**: Critical
> **출처**: Stage 9 dogfood `_workspace/release/scenario-rosetta-flow-2026-05-11.md` §3 발견 1
> **관련 VR**: VR-cycle-10

---

## 1. 현재 상태 (문제 진단)

Stage 9 dogfood 실행 시 다음 명령 사용:

```bash
python -m pipeline_local.run_pipeline_local \
    --approach-b --iterations 5 \
    --llm-model qwen3:8b \
    --config pipeline_local/config/pipeline_config_local_dogfood.yaml \
    --output-dir runs_local/dogfood_2026-05-11
```

`ollama serve`는 백그라운드 가동 (`localhost:11434`)했으나, `--llm-base-url`이나 `--ollama-host` 옵션을 누락. 결과:

```
[AG_src.llm.provider] ERROR: vLLM API error: <urlopen error [Errno 111] Connection refused>
[ScientistCritic] WARNING: LLM 분석 실패, 규칙 기반 폴백
```

→ pipeline_local의 `VLLMProvider`가 기본값(vLLM 8000)으로 호출 시도, 모든 LLM 호출 실패. Planner / Critic / Reporter 모두 규칙 기반 폴백.

## 2. 영향 (정량)

Stage 9 결과에서 측정:

| 영향 | 정량 |
|------|------|
| LLM 호출 실패율 | **100%** (vLLM 8000 모든 시도 connection refused) |
| Critic이 제안한 파라미터 변경 | **0개** (모든 iteration 폴백 → 동일 파라미터 유지) |
| Iteration 간 다양성 | 0 (동일 파라미터로 BLOSUM random — 시드만 변동) |
| 결과 | patience 2/2 트리거 → iter05 못 봄 (의도 5 → 실제 3) |
| 사용자 체감 | "왜 LLM이 작동 안 하는지" silent — 명시적 경고 부재 |

→ **Silent degraded mode**: 시스템이 작동은 하지만 *진짜 의미 있는 결과는 산출 안 함*. 운영자가 인지하기 전까지 계속 자원 소비.

## 3. 제안 fix (코드 변경 X — 방향 제안만)

### 3-1. CLI 옵션 누락 시 명시적 WARNING

`pipeline_local/run_pipeline_local.py`에서 argparse 후 다음 체크 추가 (의사 코드):

```python
# pseudo-code (실 구현은 별도 PR)
if args.llm_model and not (args.llm_base_url or args.ollama_host):
    # 1. ollama 11434 ping 시도
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        logger.warning(
            "LLM base_url 미지정 — ollama localhost:11434 자동 감지·사용. "
            "명시하려면 --ollama-host localhost:11434 추가."
        )
        args.ollama_host = "localhost:11434"
    except Exception:
        logger.error(
            "LLM base_url 미지정 + ollama·vLLM 모두 미응답. "
            "--llm-base-url 또는 --ollama-host 명시 후 재실행."
        )
        sys.exit(2)
```

### 3-2. Provider 폴백 비율 모니터링

`AG_src/llm/provider.py`에 호출 카운터 추가 (의사 코드):

```python
# pseudo-code
class VLLMProvider:
    _call_count = 0
    _fail_count = 0

    def call(self, prompt):
        self._call_count += 1
        try:
            return self._real_call(prompt)
        except urllib.error.URLError:
            self._fail_count += 1
            if self._fail_count >= 3 and self._fail_count / self._call_count >= 0.5:
                logger.error(
                    f"LLM provider 폴백률 {self._fail_count}/{self._call_count} >= 50% — "
                    "이후 결과는 LLM degraded mode. Convergence 결과 신뢰 X."
                )
            return self._rule_based_fallback(prompt)
```

### 3-3. README + CLI help 보강

`pipeline_local/run_pipeline_local.py` 모듈 docstring에:

```markdown
## LLM 연결 의무
`--llm-model` 지정 시 반드시 다음 중 하나 명시:
  - `--ollama-host localhost:11434` (ollama 사용 시)
  - `--llm-base-url http://localhost:8000/v1` (vLLM 사용 시)

누락 시: vLLM 8000 기본값 → ollama만 떠 있으면 silent 폴백 → 결과 신뢰 X.
```

## 4. 위험·트레이드오프

| 위험 | 완화 |
|------|------|
| auto-detect로 인해 사용자가 잘못된 ollama 인스턴스 사용 | WARNING 로그에 명시 (ip + port) |
| 기존 CI/스크립트가 silent 폴백에 의존 (의도된 폴백 사용) | `--allow-llm-fallback` 같은 명시적 opt-in flag 도입 |
| ollama 11434 ping이 추가 latency | timeout=2s 짧게, 단 한 번만 |

## 5. 검증 방법 (별도 PR에서)

- 단위 테스트: `--llm-model` 만 지정, ollama down → exit 2 + 에러 메시지 검증
- 단위 테스트: ollama up → 자동 감지 WARNING + 정상 진행
- E2E: Stage 9 dogfood 재실행 시 LLM 호출 0 실패 확인

## 6. 의존 관계

- **R6 (Convergence detector degraded-mode 구분)** 와 연관: R1으로 LLM 실패를 *조기에 catch* + R6으로 폴백 시 convergence trigger 차단 → 이중 안전.
- 다른 R과 독립적으로 머지 가능.

## 7. 예상 영향 메트릭 (fix 후)

| 메트릭 | 현재 | 예상 |
|--------|------|------|
| LLM 폴백 silent 가능성 | 100% | 0% (WARNING + auto-detect) |
| Stage 9-style dogfood 재현 시 의미 있는 iteration | 0/5 | 5/5 가능 |
| 운영자 인지까지 시간 | 사후 보고서로만 | 즉시 (log) |

## 8. 추적

- 본 권고 fix PR: (아직 생성 안 됨)
- 본 권고 추적 issue: (선택, gh issue로 생성 가능)
- Stage 9 dogfood 보고서: `_workspace/release/scenario-rosetta-flow-2026-05-11.md` §3 발견 1

---

**End of R1 Proposal Report.**
