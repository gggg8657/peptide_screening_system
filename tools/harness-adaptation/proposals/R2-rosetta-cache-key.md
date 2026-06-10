# R2 — PyRosetta cache key 결정 로직 진단·fix

> **Status**: 권고 보고 (코드 수정 X)
> **Priority**: **Critical** — 도메인 결과를 완전 무효화하는 버그
> **출처**: Stage 9 dogfood §3 발견 2
> **관련 VR**: VR-cycle-11

---

## 1. 현재 상태 (문제 진단)

Stage 9 dogfood의 `_workspace/release/scenario-rosetta-flow-2026-05-11.md` §3 발견 2:

**iter01 `energy_table.json`**:
```json
{
  "seq_id": "var_012",
  "ddg": 0.0,
  "refined_pdb": "runs_local/dogfood_2026-05-11/local_20260511_1137_iter01/06_rosetta/refined_var_012.pdb",
  "source": "silo_a"
}
```

**iter02 `energy_table.json`** (다른 시퀀스인데):
```json
{
  "seq_id": "var_024",
  "ddg": 0.0,
  "refined_pdb": "runs_local/dogfood_2026-05-11/local_20260511_1137_iter01/06_rosetta/refined_var_012.pdb",
  "source": "silo_a"
}
```

**iter03 동일** — var_024가 또 iter01 var_012 PDB 가리킴.

**`step06_rosetta.py:120` 로그**:
```
[Step06][Cache] STORE key=765701bbb554abb4020f3e9a (ddG=0.00)
... (iter02/03)
[Step06] var_024: CACHED ddG=0.00, clash=0.0
[Step06] step06_rosetta 완료 (0.0s).
```

→ 서로 다른 시퀀스(`AGCKNFFW...` 변형 var_012 vs var_024)가 동일 cache key로 hit. iter01에서 STORE된 ddG=0.0 entry가 iter02/03의 var_024로 그대로 반환됨.

## 2. 영향 (정량)

| 영향 | 정량 |
|------|------|
| 도메인 결과 신뢰도 | **0** (다른 시퀀스를 동일 시퀀스로 처리) |
| Stage 9 dogfood iter02/03 Rosetta 결과 | 무효 (모두 cached fake) |
| Final report Top Candidates | "var_012/var_024/var_024 모두 ddG=0.00" — 사용자에게 *진짜 결과처럼* 노출 |
| Stage 5 환각 가드 우회 | 가드는 lookup table 무단 변경을 catch하지만 *cache logic 자체*는 검사 안 함 |

→ **이게 머지된 채로 운영되면 신약 후보 선정 결정 자체가 잘못된 데이터에 기반.**

## 3. 진단 가설 (코드 변경 X — 분석만)

`step06_rosetta.py`의 cache key 결정 함수를 조사해야 함. 가설 후보:

### 가설 A — Cache key가 sequence를 포함 안 함

```python
# pseudo-code (실제 코드는 별도 확인 필요)
def _cache_key(receptor_pdb, config, ...):
    # 시퀀스가 빠지면 모든 변이가 동일 key
    return hash((receptor_pdb, config))
```

### 가설 B — Cache key가 빈 input fallback 시 동일 값

```python
def _cache_key(candidate):
    seq = candidate.get("sequence", "")  # 누락 시 빈 문자열
    return hash(seq)  # 빈 문자열 → 같은 hash
```

### 가설 C — Cache TTL/invalidation 부재

iter01에서 STORE된 entry가 iter02/03에서 invalidate 없이 hit. 정상 cache는 input이 다르면 다른 key를 생성해야 하는데, 가설 A/B 둘 중 하나가 진짜 원인.

### 검증 방법

1. `step06_rosetta.py`에서 `_cache_key()` 또는 `_cache_*()` 함수 grep
2. 두 다른 시퀀스(var_012 sequence, var_024 sequence) 입력으로 같은 키 생성되는지 단위 테스트
3. `[Step06][Cache] STORE key=765701bbb554abb4020f3e9a` 로그의 key가 var_012, var_024에 동일한지 grep

## 4. 제안 fix (코드 변경은 별도 PR)

### 4-1. Cache key에 sequence 포함 보장

```python
# pseudo-code
def _cache_key(candidate, receptor_pdb, config):
    seq = candidate.get("sequence")
    if not seq or not isinstance(seq, str):
        raise ValueError(f"Cache key 생성 실패: invalid sequence {seq!r}")
    receptor_hash = hashlib.sha1(open(receptor_pdb, 'rb').read()).hexdigest()[:8]
    config_hash = hashlib.sha1(repr(config).encode()).hexdigest()[:8]
    return f"{hashlib.sha1(seq.encode()).hexdigest()}_{receptor_hash}_{config_hash}"
```

### 4-2. 회귀 테스트 추가

```python
# pseudo-code (별도 PR test 파일)
def test_cache_key_differs_for_different_sequences():
    cand1 = {"sequence": "AGCRNFFWKTFTSC"}  # var_012
    cand2 = {"sequence": "AGCKNRFWKTFTSC"}  # var_024
    k1 = _cache_key(cand1, receptor, config)
    k2 = _cache_key(cand2, receptor, config)
    assert k1 != k2, f"Cache key collision: {k1} == {k2}"

def test_cache_invalidates_on_sequence_change():
    # iter01 STORE, iter02 다른 seq에 LOAD 시도 → MISS 의무
    ...
```

### 4-3. 기존 cache 파일 invalidation

```bash
# 운영 명령
rm -rf runs_local/*/06_rosetta/.rosetta_cache.json
```

→ Stage 9 dogfood로 생성된 cache 파일은 *오염*되었을 가능성. 모든 cached entries 재계산 권장.

## 5. 위험·트레이드오프

| 위험 | 완화 |
|------|------|
| Cache invalidation으로 기존 모든 run의 재실행 | 1회 비용. 잘못된 결과로 운영하는 것보다 안전 |
| `_cache_key` 변경 시 backward incompat | semver MAJOR, 한 번에 모두 invalidate (위와 동일) |
| 의존 모듈의 `_cache_key` 호출 signature 변경 | 별도 PR로 호출자 모두 update |

## 6. 검증 방법 (별도 PR에서)

1. **회귀 테스트** (4-2 의사 코드)
2. **Stage 9-style E2E**: dogfood config로 3 iter 재실행 → iter02/03이 *진짜 다른 ddG* 보고하는지 확인
3. **Stage 5 환각 가드 통합**: cache key 함수도 `HEURISTIC_FUNCTION_DISCLAIMERS`에 등록 (R7과 연계)

## 7. 의존 관계

- **R3 (ddG=0.0 silent fallback)** 와 강한 연관: 본 버그가 ddG=0.0 모든 결과를 *일관되게 0.0으로 보이게* 함. cache hit이 아닌 *진짜 score 계산*에서도 0.0인지 R3가 진단.
- **R5 (source 라벨 버그)** 도 같은 근본 원인 가능 (cache STORE 시 source 필드도 부정확)
- **R7 (HEURISTIC_FUNCTION_DISCLAIMERS)** 와 연계: 본 cache logic을 가드에 등록

## 8. 예상 영향 메트릭 (fix 후)

| 메트릭 | 현재 | 예상 |
|--------|------|------|
| 다른 sequence 입력의 cache hit 비율 | 100% (가설) | 0% |
| 진짜 Rosetta 계산 수행 비율 | ~33% (iter01만, var_012 1개) | ~100% (모든 입력) |
| Stage 9-style 재실행 시 ddG 다양성 | 0 (모두 0.00) | 도메인 합리 범위 |

## 9. 추적

- 본 권고 fix PR: 미생성
- 본 권고 추적 issue: (선택)
- Stage 9 dogfood 보고서: `_workspace/release/scenario-rosetta-flow-2026-05-11.md` §3 F2

---

**End of R2 Proposal Report.**
