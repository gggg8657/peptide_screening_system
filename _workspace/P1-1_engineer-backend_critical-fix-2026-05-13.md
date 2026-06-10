# P1-1 Critical Fix 보고서
**작성**: engineer-backend  
**날짜**: 2026-05-13  
**대상 이슈**: C-M1-1, C-M1-2, C-M2-1 (M1 검증 보고서에서 식별)

---

## 변경 파일 목록

| 파일 | 변경 유형 | 요약 |
|------|---------|------|
| `pipeline_local/steps/step01_receptor.py` | 수정 | `_call_openfold3_local()` — `mmcif` 키 처리 + CIF→PDB 변환 |
| `pipeline_local/steps/step02_backbone.py` | 수정 | `generate_backbones()` — 백본 0개 시 `RuntimeError` 추가 |
| `pipeline_local/orchestrator.py` | 수정 | step05b/05c 직후 `save_selectivity_results` / `save_step05c_results` 호출 추가 |
| `pipeline_local/tests/test_p1_critical_fixes.py` | 신규 | 회귀 테스트 14건 |

---

## C-M1-1: step01 OpenFold3 키 불일치 수정

### 문제
`run_openfold3.py` wrapper는 `{"mmcif": ..., "confidence": ...}` 형식으로 반환.  
`_call_openfold3_local()`은 `"output_pdb"` / `"pdb"` / `"result.pdb"` 만 검사 → 항상 `RuntimeError` → 항상 data/ fallback.

### 수정 내용 (`step01_receptor.py:_call_openfold3_local()`)

```python
# 기존: pdb_text가 None이면 즉시 RuntimeError
pdb_text: Optional[str] = (
    result.get("output_pdb")
    or result.get("pdb")
    or result.get("result", {}).get("pdb")
)
if not pdb_text:
    raise RuntimeError(...)

# 수정: mmcif 키 처리 추가
pdb_text: Optional[str] = (
    result.get("output_pdb") or result.get("pdb") or result.get("result", {}).get("pdb")
)

if not pdb_text:
    mmcif_text: Optional[str] = result.get("mmcif")
    if mmcif_text:
        logger.info("[Step01] openfold3 결과에서 'mmcif' 키 감지 — CIF→PDB 변환 시도")
        # tempfile에 CIF 내용 저장 후 _convert_cif_to_pdb() 호출
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".cif", prefix="openfold3_")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
                tmp_f.write(mmcif_text)
            pdb_text = _convert_cif_to_pdb(tmp_path, mmcif_text)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

if not pdb_text:
    raise RuntimeError(
        f"[Step01] openfold3 local model returned no PDB or mmCIF. "
        f"Keys: {list(result.keys())}"
    )
```

### 동작 흐름 변경
- `run_openfold3.py` → `{"mmcif": "data_structure\n..."}` 반환
- `_call_openfold3_local()` → `"mmcif"` 키 감지 → 임시 .cif 파일 작성 → `_convert_cif_to_pdb(tmp_path, mmcif_text)` 호출
  - PyRosetta 우선 (파일 경로 사용)
  - 실패 시 BioPython StringIO 폴백
- PDB 텍스트 반환 → `extract_receptor_chain()` → `_finalize_output()`

---

## C-M1-2: step02 백본 0개 silent fail 차단

### 문제
모든 backbone seed가 실패해도 `Step02Output(backbone_pdbs=[], n_generated=0)` 반환.  
orchestrator가 `if not step02_out.backbone_pdbs: return iter_result` (소프트 종료)로 처리.  
사용자에게는 에러 없이 결과만 없는 상황.

### 수정 내용 (`step02_backbone.py:generate_backbones()`)

```python
# 기존: n_generated=0 이어도 그냥 반환
return Step02Output(backbone_pdbs=backbone_paths, design_params=design_params, n_generated=len(backbone_paths))

# 수정: 0개 생성 시 명시적 RuntimeError
if not backbone_paths:
    raise RuntimeError(
        f"[Step02] Backbone generation failed: 0 PDBs generated out of {n_backbone} "
        f"(all {len(failed_seeds)} seeds failed). "
        "Check RFdiffusion logs or conda env."
    )
return Step02Output(...)
```

### 오케스트레이터 연동
orchestrator의 `_execute_step()` wrapper가 RuntimeError를 catch하여:
1. `step02_result.success = False` 설정
2. `_write_status("error", ...)` 호출 → STATUS_FILE 갱신
3. `iter_result.step_results["step02"]` 에 실패 기록
4. `if not step02_result.success: return iter_result` → 조기 종료

---

## C-M2-1: orchestrator step05b/05c save 호출 추가

### 문제
`run_selectivity_screening()` / `run_boltz_cross_validation()` 결과가 메모리에만 존재.  
파이프라인 완료 후 해당 데이터를 파일로 접근할 방법 없음.

### 수정 내용 (`orchestrator.py:run_single_iteration()`)

#### step05b 직후 (try/except 블록 이후)
```python
# Step 05b 결과 파일 저장
if step05b_output is not None:
    _out_dirs = self.config.get("output_dirs", {})
    _05b_dir = Path(_out_dirs.get("05b_selectivity", "runs_local/05b_selectivity"))
    try:
        step05b_selectivity.save_selectivity_results(step05b_output, _05b_dir)
        self._logger.info("[Step05b] 선택성 결과 저장 완료: %s", _05b_dir)
    except Exception as _e:
        self._logger.warning("[Step05b] 선택성 결과 저장 실패 (비치명): %s", _e)
```

#### step05c 직후 (try/except/else 블록 이후)
```python
# Step 05c 결과 파일 저장
if step05c_output is not None:
    _out_dirs = self.config.get("output_dirs", {})
    _05c_dir = Path(
        _out_dirs.get(
            "05c_boltz_cross",
            str(Path(_out_dirs.get("05b_selectivity", "runs_local/05b_selectivity")).parent / "05c_boltz_cross"),
        )
    )
    try:
        step05c_boltz_cross.save_step05c_results(step05c_output, _05c_dir)
        self._logger.info("[Step05c] Boltz-2 결과 저장 완료: %s", _05c_dir)
    except Exception as _e:
        self._logger.warning("[Step05c] Boltz-2 결과 저장 실패 (비치명): %s", _e)
```

### 저장 경로
- Step05b: `runs/{run_id}/05b_selectivity/selectivity_scores.json` + `{seq_id}_selectivity.json`
- Step05c: `runs/{run_id}/05c_boltz_cross/boltz_cross_validation.json` + `{seq_id}_boltz_cross.json`
- 저장 실패는 `WARNING` 로그 (비치명 — 파이프라인 계속 진행)

---

## 테스트 결과

```
pipeline_local/tests/test_p1_critical_fixes.py::TestStep01OpenFold3MmcifKey::test_mmcif_key_triggers_cif_to_pdb_conversion PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestStep01OpenFold3MmcifKey::test_output_pdb_key_still_works PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestStep01OpenFold3MmcifKey::test_pdb_key_works PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestStep01OpenFold3MmcifKey::test_no_pdb_or_mmcif_raises_runtime_error PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestStep01OpenFold3MmcifKey::test_sequence_missing_raises_runtime_error PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestStep01OpenFold3MmcifKey::test_mmcif_convert_failure_still_raises PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestStep02ZeroBackboneGuard::test_all_backbones_fail_raises_runtime_error PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestStep02ZeroBackboneGuard::test_partial_failure_continues PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestStep02ZeroBackboneGuard::test_zero_backbone_config_raises PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestOrchestratorSaveResults::test_save_selectivity_results_called_with_correct_dir PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestOrchestratorSaveResults::test_save_step05c_results_called_with_correct_dir PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestOrchestratorSaveResults::test_save_selectivity_results_writes_json PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestOrchestratorSaveResults::test_save_step05c_results_writes_json PASSED
pipeline_local/tests/test_p1_critical_fixes.py::TestOrchestratorSaveResults::test_orchestrator_save_code_path_exists PASSED

14 passed in 0.12s
```

### 전체 회귀 테스트
```
2 failed, 332 passed, 14 skipped, 2 xfailed, 12 warnings in 1.93s
```
- 신규 통과: 14건 (332 - 318 = +14)
- 기존 실패 2건 (TestF1MmcifConversion, pre-existing) 그대로 유지 — P1-1 무관

---

## 잔여 주의사항

1. **C-M1-1 CIF→PDB 변환 품질**: `_convert_cif_to_pdb()`의 PyRosetta 경로 (`pyrosetta.rosetta.core.io.pose_to_pdbstring`) API 정확성이 M1 보고서 M1 항목에서 불확실로 지적됨 → 별도 PyRosetta 단위 테스트 필요 (P1 다음 우선순위)

2. **C-M1-2 orchestrator 중복 guard**: orchestrator에 기존 `if not step02_out.backbone_pdbs: return iter_result` 코드가 남아 있음. RuntimeError 방식이 채택되어 이 guard가 실행될 일은 없으나 dead code 정리 권장 (Low priority)

3. **C-M2-1 05c 경로**: `out_dirs["05c_boltz_cross"]` 키가 `_setup_run()`에 없으므로 현재는 `05b_selectivity` 상위 기반으로 경로 도출. `_setup_run()` 에 `"05c_boltz_cross"` 추가 고려 (Low priority)
