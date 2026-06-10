# PR: fix(tier3) — T4 SOD 후속 4 minor issues 처리

**브랜치**: `fix/tier3-followup-cleanup` → `main`  
**작성자**: reviewer-code  
**날짜**: 2026-05-12  
**커밋**: 680f19a

---

## Summary

SOD 2026-05-12 T5 리뷰에서 식별된 Tier 3 후속 4 minor issues를 처리합니다.  
T1(데모 실행)과 독립적으로 진행 가능한 코드 품질 개선 작업입니다.

### 변경 파일

| 파일 | 변경 내용 |
|------|---------|
| `pipeline_local/steps/step06_rosetta.py` | `_build_ref_paths()` 헬퍼 추출, `logger.info` 추가 |
| `pipeline_local/tests/test_tier3_reference_complex_fix.py` | `test_returns_none_when_all_paths_missing` 재작성 |

---

## 이슈별 변경 내용

### Issue-1 (Medium) — 테스트 self-call 버그 수정

**파일**: `pipeline_local/tests/test_tier3_reference_complex_fix.py:138-166`

**문제**:
```python
# Before: original_fn 저장 후 미사용, _patched()가 자신을 호출
original_fn = mod._get_reference_complex_path  # 미사용 dead variable
def _patched() -> None:
    # 실 모듈 함수가 아닌 로컬 구현 검증 (의미 없음)
    ...
result = _patched()  # mod._get_reference_complex_path() 미검증
```

**수정**:
```python
# After: monkeypatch로 _build_ref_paths()를 교체, 실 함수 직접 호출
monkeypatch.setattr(mod, "_build_ref_paths", lambda: fake_paths)
monkeypatch.delenv("REFERENCE_COMPLEX_PATH", raising=False)
result = mod._get_reference_complex_path()  # 실 모듈 함수 검증 ✅
assert result is None
```

**신뢰등급**: HIGH (코드 직접 확인)

---

### Issue-2 (Low) — ref_paths DRY 헬퍼 추출

**파일**: `pipeline_local/steps/step06_rosetta.py:475-483` (구), `:619-627` (구)

**문제**: `_get_reference_peptide_com()`과 `_get_reference_complex_path()` 두 함수에  
동일한 4-경로 리스트 (`ref_paths`) 100% 중복.

**수정**: `_build_ref_paths() -> list` 헬퍼 추출 (line 467):
```python
def _build_ref_paths() -> list:
    """참조 복합체 PDB 후보 경로 목록을 반환한다 (F11 fix, DRY).
    
    우선순위: REFERENCE_COMPLEX_PATH env var → 실 위치 1 → 실 위치 2 → stale path.
    호출 시점의 환경변수를 읽으므로 monkeypatch가 정상 동작한다.
    """
    repo_root = Path(__file__).parent.parent.parent
    env_override = os.environ.get("REFERENCE_COMPLEX_PATH")
    return [
        *([Path(env_override)] if env_override else []),
        repo_root / "data" / "fold_test1" / "fold_test1_model_0.pdb",
        repo_root / "AgenticAI4SCIENCE_pyrosetta_track" / ... / "fold_test1_model_0.pdb",
        repo_root / "PRST_N_FM" / "data" / "fold_test1" / "fold_test1_model_0.pdb",
    ]
```

두 함수 모두 `_build_ref_paths()` 호출로 교체.

**부수 효과**: Issue-1 monkeypatch 패치 진입점 제공 (설계 의도).

**신뢰등급**: HIGH

---

### Issue-3 (Low) — `_get_reference_peptide_com()` logger.info 누락

**파일**: `pipeline_local/steps/step06_rosetta.py`

**문제**: `_get_reference_complex_path()` (L630)은 경로 발견 시 `logger.info` 기록하는데,  
`_get_reference_peptide_com()`은 발견해도 아무 로그 없음 (패턴 불일치).

**수정**: 발견 시 `logger.info` + 부재 시 `logger.warning` 추가:
```python
if pep_cas:
    logger.info("[Step06] Reference peptide COM computed from: %s", ref_path)
    return _center_of_mass(pep_cas)
logger.warning(
    "[Step06] Reference peptide COM not found in any known path. ..."
)
return None
```

**신뢰등급**: HIGH

---

### Issue-4 (Low/Med) — 테스트 카운트 차이 원인 분석

**현상**: backend 보고 117/119, tester 측 155/155, 현재 179 collected

**분석 결과**:

| 시점 | 카운트 | 사유 |
|------|--------|------|
| backend 보고 (어제) | 117/119 | tier1/2/3 + step05c + offtarget 테스트 추가 이전 |
| tester 관찰 (오늘 SOD) | 155/155 | test_tier3_reference_complex_fix.py 신규 추가 직전 |
| 현재 (post-T4) | **173/179** | 이번 PR 포함 전체 |

**세부 카운트**:
- 173 PASSED
- 2 FAILED (Pre-existing: `Bio` 모듈 미설치 환경 — `test_assemble_complex_*` 2건)  
  → `bio-tools` conda env에서는 정상 PASS 예상
- 4 SKIPPED (Boltz 통합 테스트 — GPU/모델 환경 의존)

**회귀 없음**: 기존 통과 테스트 모두 유지. ✅

---

## 테스트 결과

### Tier 3 테스트 (10/10 PASS)
```
test_tier3_reference_complex_fix.py::TestRealPathDiscovery::test_get_reference_complex_path_returns_str PASSED
test_tier3_reference_complex_fix.py::TestRealPathDiscovery::test_get_reference_complex_path_is_pdb PASSED
test_tier3_reference_complex_fix.py::TestRealPathDiscovery::test_get_reference_peptide_com_returns_tuple PASSED
test_tier3_reference_complex_fix.py::TestRealPathDiscovery::test_get_reference_peptide_com_reasonable_coords PASSED
test_tier3_reference_complex_fix.py::TestEnvVarOverride::test_env_var_overrides_default_path PASSED
test_tier3_reference_complex_fix.py::TestEnvVarOverride::test_env_var_peptide_com_override PASSED
test_tier3_reference_complex_fix.py::TestEnvVarOverride::test_env_var_nonexistent_falls_through PASSED
test_tier3_reference_complex_fix.py::TestGracefulNoneOnMissing::test_returns_none_when_all_paths_missing PASSED  ← Issue-1 fix
test_tier3_reference_complex_fix.py::TestGracefulNoneOnMissing::test_warning_logged_when_all_paths_missing PASSED
test_tier3_reference_complex_fix.py::TestSearchPathOrder::test_real_paths_before_stale_path PASSED
```

### 전체 회귀 (173 passed, 2 failed Pre-existing, 4 skipped)
```
2 failed, 173 passed, 4 skipped in 0.31s
```
- 기존 2건 실패: `Bio` 모듈 미설치 (기존과 동일, 회귀 아님)

---

## Checklist

- [x] Issue-1: 테스트 self-call 수정 — 실 모듈 함수 검증
- [x] Issue-2: `_build_ref_paths()` DRY 추출 — 두 함수 중복 제거
- [x] Issue-3: `logger.info` + `logger.warning` 추가
- [x] Issue-4: 카운트 차이 원인 분석 완료
- [x] 10/10 Tier 3 테스트 PASS
- [x] 전체 회귀 없음 (173 pass, 동일 2 fail Pre-existing)
- [x] 함수 시그니처 변경 없음 (호출처 갱신 불필요)
- [x] `git diff main..HEAD --stat` 확인 — 2파일만 변경

---

## 메모

`_build_ref_paths()`의 `list` 반환 타입 힌트는 Python 3.9+의 `list[Path]`  
대신 `list`로 선언함 (기존 코드 스타일과 일관성 유지,  
from `__future__ import annotations` 이미 선언됨).
