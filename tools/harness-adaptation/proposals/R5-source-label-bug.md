# R5 — `source: "silo_a"` 라벨 버그 fix

> **Status**: 권고 보고 (코드 수정 X)
> **Priority**: Medium
> **출처**: Stage 9 dogfood §3 발견 5
> **관련 VR**: (Stage 9 §6 후속)

---

## 1. 현재 상태

Stage 9 dogfood 명령:
```bash
python -m pipeline_local.run_pipeline_local --approach-b --iterations 5 ...
```

→ Silo B (Approach B, PyRosetta) 단독. 그런데 `06_rosetta/energy_table.json`의 모든 entry:
```json
{
  "seq_id": "var_012",
  ...
  "source": "silo_a"
}
```

`--approach-b`인데 source가 `silo_a`로 표기됨.

## 2. 영향

| 영향 | 정량 |
|------|------|
| 사후 감사 (audit trail) | 운영자가 결과를 silo_a/silo_b로 필터링 시 잘못된 분류 |
| `--dual` 모드와의 비교 | Silo A와 Silo B 결과를 별도 추적할 때 silo_b가 silo_a로 라벨링 → 통계 오염 |
| 코드 영향 정도 | 본 1개 필드 외 다른 silo 분기 로직에 영향 없는 *순수 라벨링* 가능 |

→ **Critical은 아니지만 사후 추적성에 직접 영향**.

## 3. 진단 가설

### 가설 A — `_default_source` 상수가 silo_a로 hard-code

`step06_rosetta.py` 또는 인근 모듈에 `DEFAULT_SOURCE = "silo_a"` 같은 상수. 모든 entry에 이 값 적용.

### 가설 B — silo 분기 함수가 `--approach-b` 인지 못함

```python
# pseudo-code
def determine_source(args):
    if args.dual:
        return "dual"
    elif args.approach_b:  # ← 만약 이 분기가 없으면
        return "silo_b"
    else:
        return "silo_a"  # default
```

가설 B가 가장 가능성 — `--approach-b`만의 경우 fall-through로 silo_a default.

### 가설 C — R3 (silent fallback)의 부수 효과

R3에서 silent fallback path가 silo_a 라벨 적용. compute_binding_ddg가 fallback 모드에서 silo_a로 표기.

## 4. 제안 fix (코드 변경은 별도 PR)

### 4-1. silo 결정 로직 명시화

```python
# pseudo-code
def determine_silo(args) -> str:
    if args.dual:
        return "dual"
    if args.approach_b:
        return "silo_b"
    if args.no_approach_b:
        return "silo_a"  # RFdiffusion + ProteinMPNN
    raise ValueError("silo 결정 불가: --approach-b/--no-approach-b 중 하나 명시")
```

### 4-2. 회귀 테스트

```python
# pseudo-code
@pytest.mark.parametrize("args,expected", [
    ({"approach_b": True}, "silo_b"),
    ({"no_approach_b": True}, "silo_a"),
    ({"dual": True}, "dual"),
])
def test_silo_determination(args, expected):
    assert determine_silo(args) == expected
```

### 4-3. 기존 잘못된 산출물 (Stage 9 dogfood) 메모

`runs_local/dogfood_2026-05-11/local_*_iter*/06_rosetta/energy_table.json`의 `source: "silo_a"`는 *Stage 9 가공 산출*이지 진짜 silo_a 아님. 본 권고가 merge·fix되면 재실행 시 silo_b로 정정.

## 5. 위험·트레이드오프

| 위험 | 완화 |
|------|------|
| source 라벨만 변경, fix가 의미 없는 cosmetic | R2/R3 fix와 묶어서 머지하면 의미 있음 |
| 기존 cached entries의 source 필드 stale | R2 cache invalidation과 함께 |
| 다른 모듈이 `source == "silo_a"`에 의존 | grep으로 호출처 확인 후 fix |

## 6. 의존 관계

- **R2 (cache key) + R3 (silent fallback)** 와 같은 fallback path 가능성 — 한꺼번에 진단·fix 권장
- 독립적으로도 fix 가능

## 7. 예상 영향 메트릭 (fix 후)

| 메트릭 | 현재 | 예상 |
|--------|------|------|
| Stage 9-style dogfood의 source 정확도 | 0% (모두 silo_a 잘못 표기) | 100% (silo_b) |
| `--dual` 모드 결과의 silo 분류 정확도 | 미확인 | 검증됨 (회귀 테스트) |

## 8. 추적

- Stage 9 보고서 §3 F5

---

**End of R5 Proposal Report.**
