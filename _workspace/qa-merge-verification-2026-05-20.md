# QA 머지 검증 보고서 — 2026-05-20

> **작성**: qa 에이전트 (team `gate2-closure-20260520`)  
> **대상 PR**: #68 `feat/p1-sprint-integration` → `main`  
> **검증 시각**: 2026-05-20  
> **판정**: ✅ **CONDITIONAL PASS** — 머지 진행 가능

---

## 1. 요약

| 항목 | 결과 | 목표 |
|------|------|------|
| BE (`conda run -n bio-tools pytest -q`) | **152/152 PASS** | 152/152 |
| FE (`npx vitest run`) | **99/99 PASS** | 99/99 |
| Pipeline (`conda run -n bio-tools pytest -q`) | 560 PASS / 5 FAIL / 7 skip / 2 xfail | 신규 FAIL 0건 |
| 신규 회귀 | **0건** | 0건 |
| 판정 | **CONDITIONAL PASS** | PASS |

---

## 2. BE 검증 (152/152)

**실행 명령**: `cd /tmp/SST14-p1-sprint-integration-codex/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri && conda run -n bio-tools python -m pytest backend/tests/ -q`

**결과**:
```
152 passed, 3 warnings in 4.78s
```

**경고 내역** (무시 가능):
- `FutureWarning`: torch.cuda pynvml deprecated (torch 내부 경고)
- `DeprecationWarning`: torch.jit.script deprecated (torch 내부 경고)

**판정**: ✅ PASS (152/152)

---

## 3. FE 검증 (99/99)

**실행 명령**: `cd /tmp/SST14-p1-sprint-integration-codex/.../frontend && npx vitest run`

**결과**:
```
Test Files  9 passed (9)
      Tests  99 passed (99)
   Duration  3.17s
```

**경고 내역** (무시 가능):
- `act()` 미래 경고: CandidateTable, ArchivesTopKSlider 컴포넌트 React 상태 업데이트 — 기존 패턴, FAIL 없음

**신규 테스트 포함**:
- `BindingPocketEditor.test.tsx` 23 tests — 전체 PASS ✅

**판정**: ✅ PASS (99/99)

---

## 4. Pipeline 검증 (신규 회귀 0건)

**실행 명령**: `cd /tmp/SST14-p1-sprint-integration-codex/pipeline_local && conda run -n bio-tools python -m pytest -q --tb=no`

**결과**:
```
5 failed, 560 passed, 7 skipped, 2 xfailed, 15 warnings in 49.52s
```

### 4.1 신규 테스트 (`test_p1_sprint_wrapper_integration.py`) — 5/5 PASS

```
tests/test_p1_sprint_wrapper_integration.py::test_default_score_preserves_mock_inputs PASSED
tests/test_p1_sprint_wrapper_integration.py::test_enrich_from_wrappers_updates_scores PASSED
tests/test_p1_sprint_wrapper_integration.py::test_d_aa_guard_skips_wrappers PASSED
tests/test_p1_sprint_wrapper_integration.py::test_d_aa_detection_covers_lowercase_and_d_dash PASSED
tests/test_p1_sprint_wrapper_integration.py::test_scoring_module_exposes_same_enrichment PASSED
5 passed in 0.37s
```

### 4.2 FAIL 5건 분석 — 모두 기존 BUG

| # | 테스트 | 분류 | 근거 |
|---|--------|------|------|
| 1 | `test_binding_pocket_extract.py::TestExtractPocketCenter::test_pdb_and_cif_give_same_center` | **기존 FAIL** | 현행 main (fix/sstr4-signature-collision)에서도 동일 FAIL 확인 |
| 2 | `test_offtarget_dock_cif_chain.py::TestSSTRChainSelectionPDB[SSTR4-P31391-SSTR4_7XMT]` | **기존 FAIL** | STATUS_2026-05-20.md §3.5 — SSTR4 시그니처 충돌 BUG (Task #3) |
| 3 | `test_offtarget_dock_cif_chain.py::TestSSTRChainSelectionCIF[SSTR4-P31391-SSTR4_7XMT]` | **기존 FAIL** | 위 동일 |
| 4 | `test_offtarget_dock_cif_chain.py::TestSSTRSignatureNonAmbiguity::test_no_signature_shared_across_subtypes` | **기존 FAIL** | 위 동일 |
| 5 | `test_offtarget_dock_cif_chain.py::TestSSTRSignatureNonAmbiguity::test_sstr4_not_matched_as_sstr1_from_pdb` | **기존 FAIL** | 위 동일 |

**SSTR4 FAIL 4건**: `VILRYAKMKTA` 공유 모티프 중복 등록 버그 — `fix/sstr4-signature-collision` 브랜치(Task #3 COMPLETED)에서 수정 완료, 해당 브랜치 머지 시 자동 해소 예정.

**신규 FAIL**: **0건** ✅

### 4.3 테스트 수 차이 설명

| 항목 | 수량 | 설명 |
|------|------|------|
| STATUS_2026-05-20.md 기준 | 626 tests | 일반 python 실행, biopython 미설치 → 12 ERROR |
| p1-sprint (conda bio-tools) | 574 tests | biopython 설치됨 → ERROR 0, 단 fix/sstr4 신규 파일 미포함 |
| main worktree 추가 파일 | +21 tests | `test_generate_sstr2_sst14_complex.py` (fix/sstr4 브랜치 신규) |
| p1-sprint 신규 파일 | +5 tests | `test_p1_sprint_wrapper_integration.py` |
| untracked 파일 | +3 tests | `test_p1_critical_fixes.py` (chore/selectivity-guard 작업물) |

---

## 5. 환경 비고

- **conda 환경**: `bio-tools` (Python 3.11.15, pytest 9.0.2)
- **aiofiles**: pip install 완료 (BE 수집 오류 해소)
- **node_modules**: npm install --prefer-offline 실행 (p1-sprint 워크트리)
- **biopython**: bio-tools 환경에 설치됨 → 12 ERROR 항목이 테스트로 실행됨

---

## 6. CONDITIONAL PASS 조건

✅ BE 152/152 PASS  
✅ FE 99/99 PASS  
✅ Pipeline 신규 FAIL 0건  
✅ Pipeline 신규 ERROR 0건  
⚠️ 잔존 FAIL 5건: 모두 기존 BUG (SSTR4 ×4 + 결합 포켓 ×1) — 별도 fix 브랜치에서 처리 중 또는 완료

**머지 진행 가능**.  
머지 후 main 재검증 예정 (아래 §7).

---

## 7. 머지 후 main 재검증 (be-merger 머지 완료 후 실행)

```bash
git checkout main && git pull
# BE
cd AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri && conda run -n bio-tools python -m pytest backend/tests/ -q
# FE
cd frontend && npx vitest run
# Pipeline
cd /path/to/pipeline_local && conda run -n bio-tools python -m pytest -q --tb=no
```

**기준**: 위 p1-sprint 결과 대비 회귀 없을 것.

---

## 8. 변경 이력

| 시각 | 내용 |
|------|------|
| 2026-05-20 | 초안 작성 (qa 에이전트, PR #68 머지 전 검증) |
