# R3 — `compute_binding_ddg()` silent fallback 진단

> **Status**: 권고 보고 (코드 수정 X)
> **Priority**: **Critical**
> **출처**: Stage 9 dogfood §3 발견 3
> **관련 VR**: VR-cycle-12

---

## 1. 현재 상태 (문제 진단)

Stage 9 dogfood iter01의 `06_rosetta/energy_table.json`:

```json
{
  "seq_id": "var_012",
  "ddg": 0.0,
  "total_score": 0.0,
  "clash_score": 0.0,
  "constraint_violations": 0,
  "refined_pdb": "...refined_var_012.pdb",
  "pre_score": 0.0,
  "score_delta": 0.0,
  "source": "silo_a"
}
```

**모순**:
- `refined_var_012.pdb`는 실측 **232 KB** 정상 생성됨 → PyRosetta는 *실행되었음*
- Boltz docking 같은 시퀀스 `var_012`: score = **-9.65** (좋은 결합)
- 그런데 PyRosetta가 산출한 ddG / total_score / clash_score / pre_score / score_delta **전부 정확히 0.0** → 비현실적

**`step06_rosetta.py:120` 로그**: `[Step06][Cache] STORE key=... (ddG=0.00)` — 첫 STORE 시점부터 이미 0.00. 즉 cache fallback이 아니라 *실 계산에서* 0.00 반환.

## 2. 영향 (정량)

| 영향 | 정량 |
|------|------|
| PyRosetta Rosetta gate 통과 | iter01 0/1, iter02/03 cache (모두 0/1) — **모든 Rosetta gate 결과가 0이라서 fail** |
| 도메인 결정 영향 | "이 후보는 결합 친화도 0" → *임상 의미 없음* 또는 *완전 부적합*으로 오인 |
| Stage 5 환각 가드 적용 | HEURISTIC_FUNCTION_DISCLAIMERS에 미등록 (VR-cycle-09 H-06 사각지대) |
| Boltz score vs Rosetta score 모순 | Boltz -9.65 (강 결합) vs Rosetta 0.0 (계산 안 됨) — 사용자가 두 score 비교 시 혼란 |

→ **PyRosetta가 *fail*도 *success*도 아닌 *silent zero* 반환**. 도메인 사용자가 인지하기 어려움.

## 3. 진단 가설 (코드 변경 X)

### 가설 A — `compute_binding_ddg()` 또는 `score_function()` 호출 실패 시 fallback 0.0

PyRosetta API 호출이 exception 발생 시 try/except가 silent하게 0.0 반환:

```python
# pseudo-code
def compute_binding_ddg(complex_pdb):
    try:
        scorefxn = pyrosetta.create_score_function("ref2015")
        pose = pyrosetta.pose_from_pdb(complex_pdb)
        return scorefxn(pose)
    except Exception as e:
        logger.warning(f"PyRosetta error: {e}")
        return 0.0  # ← silent zero
```

### 가설 B — FlexPepDock 단계가 실행 안 되고 refined PDB만 generic으로 출력

`step06_rosetta.py`의 워크플로우:
1. FastRelax (cartesian)
2. FlexPepDock refinement
3. ddG calculation

1번 또는 2번이 silent fail → 단순 input pose를 그대로 PDB로 저장 → ddG=0.0 (변화 없음).

### 가설 C — Score function 자체가 빈 weight 또는 잘못 초기화

```python
scorefxn = pyrosetta.create_score_function("ref2015")
# 만약 ref2015가 우리 environment에서 weights load 실패 → 빈 score
print(scorefxn(pose))  # → 0.0
```

### 가설 D — `source: "silo_a"` 라벨 버그(R5)와 같은 fallback path

step06_rosetta가 silo_b path 대신 silo_a path를 타고, silo_a path는 *score 계산 안 함*. 그래서 ddG=0.0 + source="silo_a".

### 검증 방법

```bash
# 단순 reproduction
conda activate bio-tools
python -c "
import pyrosetta
pyrosetta.init('-mute all')
pose = pyrosetta.pose_from_pdb('runs_local/dogfood_2026-05-11/local_20260511_1137_iter01/06_rosetta/refined_var_012.pdb')
scorefxn = pyrosetta.create_score_function('ref2015')
print('ref2015 score:', scorefxn(pose))
print('Weights:', scorefxn.get_nonzero_weighted_scoretypes())
"
```

만약 위가 0.0이면 score function 자체 문제 (가설 C). 음수 합리값이면 step06_rosetta의 wrapper 문제 (가설 A/B/D).

## 4. 제안 fix 방향 (코드 변경은 별도 PR)

### 4-1. Silent fallback 제거

```python
# pseudo-code
def compute_binding_ddg(complex_pdb):
    if not Path(complex_pdb).exists():
        raise FileNotFoundError(complex_pdb)
    pose = pyrosetta.pose_from_pdb(complex_pdb)
    if pose.total_residue() == 0:
        raise ValueError(f"Empty pose: {complex_pdb}")
    scorefxn = pyrosetta.create_score_function("ref2015")
    score = scorefxn(pose)
    if score == 0.0:
        raise ValueError(
            f"Suspect score 0.0 for {complex_pdb}. "
            f"Weights: {scorefxn.get_nonzero_weighted_scoretypes()}"
        )
    return score
```

### 4-2. step06 wrapper의 fail-loud 보장

```python
# pseudo-code
def run_rosetta_refinement(candidates, receptor_pdb, config):
    results = []
    for cand in candidates:
        try:
            ddg = compute_binding_ddg(cand.complex_pdb)
            results.append(...)
        except Exception as e:
            logger.error(f"Rosetta refinement failed for {cand.seq_id}: {e}")
            results.append({"seq_id": cand.seq_id, "error": str(e), "ddg": None})
            # ddg=None으로 다음 단계가 fail 인지 가능
    return results
```

### 4-3. 회귀 테스트 (별도 PR)

```python
def test_compute_binding_ddg_nonzero():
    """ref2015 score는 비-trivial pose에 대해 0이 아니어야."""
    pose_pdb = "tests/fixtures/sst14_native_complex.pdb"
    score = compute_binding_ddg(pose_pdb)
    assert score != 0.0, "Suspect silent fallback"
    assert -10000 < score < 1000, "Score 범위 합리적"  # SCALE_RANGES["rosetta_total_score"]와 정합
```

## 5. 위험·트레이드오프

| 위험 | 완화 |
|------|------|
| Fail-loud로 인해 일부 변이체가 실패해도 pipeline 정지 | per-candidate try/except + None 표기 (4-2) |
| 0.0이 *진짜* 합리적 결과인 경우 false positive | weights check + sanity check 결합 |
| 기존 cached entries가 fail-loud로 인해 무효화 | R2 cache invalidation과 함께 (의존) |

## 6. 의존 관계

- **R2 (cache key 충돌)** 와 같은 근본 원인 가능 — *진짜 0.0인지* vs *cache hit인지* 구분 필요. R2 fix 후 R3 진단 권장.
- **R5 (source 라벨)** 도 같은 fallback path 가능
- **R7 (HEURISTIC_FUNCTION_DISCLAIMERS)** — `compute_binding_ddg`를 가드에 등록

## 7. 예상 영향 메트릭 (fix 후)

| 메트릭 | 현재 | 예상 |
|--------|------|------|
| ddG=0.0 silent 반환 비율 | 100% (Stage 9에서) | 0% |
| Boltz/Rosetta score 모순 사례 | iter01 var_012 등 | 0 |
| Fail-loud 활성화 시 사용자 알림 | 없음 | 즉시 (log + error) |

## 8. 추적

- Stage 9 보고서: `_workspace/release/scenario-rosetta-flow-2026-05-11.md` §3 F3

---

**End of R3 Proposal Report.**
