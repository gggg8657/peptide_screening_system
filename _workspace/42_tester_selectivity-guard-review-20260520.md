# 코드 리뷰 보고서 — selectivity-guard-20260520

**판정: APPROVE**
**작성일**: 2026-05-20
**리뷰 대상**: `chore/selectivity-guard-20260520` @ `f125e61`
**검토 파일**:
- `backend/state.py` (+12줄, 옵션 B)
- `backend/routers/selectivity.py` (+35줄, 옵션 B+D)
- `backend/tests/test_selectivity_guard.py` (신규 10개)

---

## 1. 요약

| 항목 | 상태 |
|------|------|
| Critical 이슈 | 없음 |
| 기능 변경 | 없음 (가드 추가만) |
| 다른 세션 충돌 | 없음 |
| 테스트 결과 | 155/155 PASS |
| 권고 | 머지 가능 |

---

## 2. 체크리스트

| # | 항목 | 결과 | 신뢰 |
|---|------|------|------|
| 1 | 응답 스키마 호환: 신규 키만, 기존 키/타입 변경 0 | ✓ | HIGH |
| 2 | env 미설정 시 동작 = 기존 동작 (불변) | ✓ | HIGH |
| 3 | `Path.resolve()` / 절대경로 처리 안전 | ✓ | HIGH |
| 4 | `warning` 누적 thread-safety | ✓ | HIGH |
| 5 | pytest selectivity 전부 PASS | ✓ 155/155 | HIGH |
| 6 | `git log main..HEAD` 다른 세션 충돌 | ✓ 없음 | HIGH |
| 7 | 도킹 알고리즘·점수 계산식 변경 0 | ✓ | HIGH |
| 8 | 클린코드: 로그 명확, magic number 없음 | ✓ | HIGH |

---

## 3. 세부 검토

### 3-1. state.py (옵션 B)

```python
# state.py:27-34
OUTER_REPO_ROOT = Path(os.environ.get(
    "SST_OUTER_REPO_ROOT",
    str(REPO_ROOT.parent.parent.parent.parent),
)).resolve()
SST_DATA_DIR = Path(os.environ.get(
    "SST_DATA_DIR",
    str(REPO_ROOT / "data" / "somatostatin_receptor"),
)).resolve()
```

- `.resolve()` 양쪽 모두 적용 → 심링크 경유 경로도 안전 [HIGH]
- 기본값이 기존 `_DATA_DIR = REPO_ROOT / "data" / "somatostatin_receptor"` 와 동일 → 동작 불변 [HIGH]
- 기존 `PIPELINE_STATUS_FILE`, `PIPELINE_ARCHIVE_DIR` 등과 동일한 패턴으로 일관성 유지 [HIGH]

### 3-2. selectivity.py — 옵션 B (경로 교체)

```python
# selectivity.py:13, 20
from backend.state import REPO_ROOT, SST_DATA_DIR
_DATA_DIR = SST_DATA_DIR
```

- 경로 참조 단일화 (state.py → 한 곳에서 관리) [HIGH]
- `REPO_ROOT` import도 유지 (하위 경로 참조용으로 사용 중) [HIGH]

### 3-3. selectivity.py — 옵션 D (silent fallback 차단)

**list_receptors `loaded_count == 0` 가드** (selectivity.py:61-67):
```python
loaded_count = sum(1 for v in receptors_dict.values() if v["loaded"])
if loaded_count == 0:
    logger.error("⚠ selectivity receptors 0/%d loaded — path=%s", ...)
```
- `receptors_dict` 빌드 완료 후 체크 → 순서 무관 [HIGH]
- `return {"receptors": receptors_dict}` 변경 없음 → 기존 응답 스키마 불변 [HIGH]

**`_estimation_fallback_count` 누적** (selectivity.py:225, 300-316):
```python
_estimation_fallback_count = 0
for cid, seq in zip(candidate_ids, candidate_sequences):
    ...
    if mode == "estimation":
        _estimation_fallback_count += 1

if _estimation_fallback_count > 0:
    _JOBS[job_id]["warning"] = "estimation_fallback"
```
- 로컬 변수 (`_estimation_fallback_count`): 단일 스레드에서만 접근 → thread-safe [HIGH]
- `_JOBS[job_id]["warning"]` 쓰기: `_job_lock` 없이 직접 접근. 그러나 기존 `_JOBS[job_id]["status"]`, `_JOBS[job_id]["candidates"]` 등도 동일 패턴 → 기존 코드와 동일한 수준의 thread-safety [HIGH]
- 루프 완료 후 단 1회 쓰기 → race condition 없음 [HIGH]

**selectivity_results 응답** (selectivity.py:407-411):
```python
return {
    "candidates": mapped,
    "mode": job["candidates"][0]["mode"] if job["candidates"] else "estimation",
    "warning": job.get("warning"),
}
```
- `candidates`, `mode` 기존 타입/위치 변경 없음 [HIGH]
- `warning`: `job.get("warning")` → 키 없으면 `None`, 있으면 값 반환 [HIGH]

### 3-4. 테스트 품질

| 테스트 | 검증 대상 | 품질 |
|--------|---------|------|
| B-1 | SST_DATA_DIR 기본값 | ✓ importlib.reload 사용, 올바름 |
| B-2 | SST_DATA_DIR env 설정 시 경로 교체 | ✓ selectivity._DATA_DIR 교차 검증 포함 |
| B-3 | OUTER_REPO_ROOT 기본값 | ✓ |
| D-1 | loaded==0 → logger.error | ✓ caplog 사용 |
| D-2 | 1개 이상 → error 미발생 | ✓ |
| D-3 | estimation fallback → warning 설정 | ✓ 실제 _run_analysis_thread 호출 |
| D-4 | production → warning 없음 | △ 주의 (하단 권장 사항 참조) |
| D-5 | warning 키 응답 포함 (estimation) | ✓ |
| D-6 | warning 키 응답 포함 (None) | ✓ |
| D-7 | 기존 스키마 14개 키 모두 유지 | ✓ 가장 강력한 회귀 테스트 |

---

## 4. 권장 사항 (머지 블로커 아님)

### [LOW] test_d4 — production 경로 실제 검증 부재

`test_d4_production_no_warning` (test_selectivity_guard.py:209)의 `patched_run`은 실제 `_run_analysis_thread`를 실행하지 않고 `_JOBS`에 직접 결과를 하드코딩합니다. 따라서 실제 production 경로에서 `_estimation_fallback_count`가 0인지를 검증하지 못합니다.

현재는 D-3(`_run_analysis_thread` 직접 호출, estimation 검증)으로 카운터 로직 자체는 검증되어 있으므로 기능 정확성에는 영향 없음. 다음 스프린트에서 `dock_against_offtarget`만 mock하고 실제 스레드를 실행하는 방향으로 개선 권장.

### [INFO] OUTER_REPO_ROOT 미사용

`state.py:27-30`에 추가된 `OUTER_REPO_ROOT`는 현재 `selectivity.py`에서 import하지 않음. 미래 확장용으로 보이나, 현재 스코프에서 사용처가 없으면 다음 스프린트에서 정리 고려.

---

## 5. 회귀 테스트 결과

```
pytest backend/tests/ (aiofiles 의존 p1/p2 제외) — 155/155 PASS (1.60s)
  신규 test_selectivity_guard.py: 10/10 PASS
  기존 pharmacophore: 52/52 PASS
  기타 라우터 테스트: 93/93 PASS
```

---

## 6. 다른 세션 충돌 위험

**평가: 없음**

- `git log main..HEAD --oneline`: 커밋 1개 (`f125e61`) — 이번 브랜치 커밋만 존재
- `git log --oneline -10 -- selectivity.py state.py` (main): 최신 커밋이 `4343732 feat(dag-v21-tier0)` — 2026-05-20 이전. 2026-05-19 이후 main에 대상 파일 변경 없음.
- 도킹 알고리즘(`dock_against_offtarget` 파라미터, `margin = worst_ot - sstr2_ddg`, `gate_pass` 조건) 변경 없음.

---

## 7. 판정

**APPROVE** — 변경 없이 머지 가능.

Critical 이슈 없음. 응답 스키마 호환성 확인. env 기본값 동작 불변 확인. 155/155 테스트 PASS. D-4 테스트 약점은 기능 정확성에 영향 없으며 LOW 우선순위 개선 권장으로 분류.
