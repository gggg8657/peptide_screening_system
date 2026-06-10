# PR 본문 초안 — fix/f05-step07-foldmason

**날짜**: 2026-05-12  
**작성**: engineer-backend  
**대상 브랜치**: `main ← fix/f05-step07-foldmason`

---

## 제목

`fix(step07): F-05 FoldMason n<2 skip — success=True + skipped 플래그`

---

## Summary

- **F-05 결함 수정**: `pipeline_local/steps/step07_analysis.py`의 `run_foldmason_alignment()`이 단일 PDB 입력 시 `{"success": false, "error": "Need >= 2 structures for alignment."}` 오류를 `lddt_table.json`에 기록하던 문제 해결
- 처리 방향 **A (skip when n<2)** 적용 — fail-soft 패턴 유지하면서 의미있는 skip 출력 기록
- 회귀 테스트 6케이스 신규 추가 (외부 FoldMason 바이너리 호출 없음)

## 변경 파일

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `pipeline_local/steps/step07_analysis.py` | 수정 | n<2 skip 로직 + FoldMasonResult.skipped 필드 |
| `pipeline_local/tests/test_step07_foldmason_n_check.py` | 신규 | F-05 회귀 테스트 6케이스 |

## 변경 상세

### `FoldMasonResult` 데이터클래스

```python
# Before
@dataclass
class FoldMasonResult:
    lddt_scores: Dict[str, float]
    html_report: str
    success: bool
    error: Optional[str] = None

# After
@dataclass
class FoldMasonResult:
    lddt_scores: Dict[str, float]
    html_report: str
    success: bool
    skipped: bool = False   # ← 신규: 의도적 skip 여부
    error: Optional[str] = None
```

### `run_foldmason_alignment()` n<2 경로

```python
# Before
if len(pdb_paths) < 2:
    logger.info("[Step07] Fewer than 2 PDBs; skipping FoldMason alignment.")
    return FoldMasonResult(lddt_scores={}, html_report="", success=False,
                           error="Need >= 2 structures for alignment.")

# After
if len(pdb_paths) < 2:
    logger.info(
        "[Step07] PDB 파일 수 %d개 < 2 — FoldMason 정렬 생략 (skip).",
        len(pdb_paths),
    )
    return FoldMasonResult(
        lddt_scores={},
        html_report="",
        success=True,
        skipped=True,
    )
```

### `run_analysis()` lddt_table.json 기록

```python
# Before
lddt_json.write_text(
    json.dumps(fm_result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
)

# After
if fm_result.skipped:
    lddt_data: Dict[str, Any] = {"success": True, "skipped": True, "reason": "n<2"}
else:
    lddt_data = fm_result.to_dict()
lddt_json.write_text(
    json.dumps(lddt_data, indent=2, ensure_ascii=False), encoding="utf-8"
)
```

### `_write_summary_md()` 상태 표시

```python
# Before
f"**FoldMason alignment:** {'OK' if fm_result.success else 'FAILED'}",

# After
f"**FoldMason alignment:** {'SKIPPED (n<2)' if fm_result.skipped else ('OK' if fm_result.success else 'FAILED')}",
```

## lddt_table.json 출력 비교

| 시나리오 | Before | After |
|---------|--------|-------|
| n=0 또는 n=1 | `{"success": false, "error": "Need >= 2 structures for alignment."}` | `{"success": true, "skipped": true, "reason": "n<2"}` |
| n≥2 (정상) | `{"success": true, "lddt_scores": {...}, ...}` | 동일 (변경 없음) |
| n≥2 (FoldMason 오류) | `{"success": false, "error": "..."}` | 동일 (변경 없음) |

## 테스트 결과

```
pipeline_local/tests/test_step07_foldmason_n_check.py::TestFoldMasonNCheck::test_n0_returns_skip PASSED
pipeline_local/tests/test_step07_foldmason_n_check.py::TestFoldMasonNCheck::test_n1_returns_skip PASSED
pipeline_local/tests/test_step07_foldmason_n_check.py::TestFoldMasonNCheck::test_n2_calls_subprocess_and_returns_success PASSED
pipeline_local/tests/test_step07_foldmason_n_check.py::TestFoldMasonNCheck::test_n2_subprocess_failure_returns_success_false PASSED
pipeline_local/tests/test_step07_foldmason_n_check.py::TestRunAnalysisLddtTableFormat::test_lddt_table_json_skip_format_when_n0 PASSED
pipeline_local/tests/test_step07_foldmason_n_check.py::TestRunAnalysisLddtTableFormat::test_lddt_table_json_normal_format_when_n2 PASSED

6 passed in 0.11s
```

전체 회귀 (`pipeline_local/tests/ -v`): **113 passed, 2 pre-existing failures** (BioPython 미설치 환경에서의 F1 테스트 — 본 PR과 무관)

## 영향 범위

- **Gate 영향**: 없음 (`gate_thresholds.yaml`의 `gates_enabled`에 `lddt` 항목 없음 — 과학 검토 확인됨)
- **다른 step 모듈**: 영향 없음 (step07_analysis.py 내부만 변경)
- **Backward compatibility**: `FoldMasonResult.skipped` 기본값 `False` — 기존 `to_dict()` 출력과 호환

## Test Plan

- [x] `pytest pipeline_local/tests/test_step07_foldmason_n_check.py -v` — 6/6 PASS
- [x] `pytest pipeline_local/tests/ -v` — 회귀 없음 (113 pass)
- [x] n=0, n=1, n=2+ 케이스 모두 monkeypatch로 외부 호출 없이 검증
- [x] lddt_table.json 포맷 통합 테스트 (skip / normal 모두)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
