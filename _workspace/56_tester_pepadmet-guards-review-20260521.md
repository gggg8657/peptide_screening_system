# 코드 리뷰 보고서 — PR #108 `chore/pepadmet-guards-20260520`

**reviewer**: tester (reviewer-code 역할)  
**날짜**: 2026-05-21  
**대상 PR**: https://github.com/AI-scientist4BIO/SST14-M_scr/pull/108  
**branch**: `chore/pepadmet-guards-20260520`  
**worktree**: `.worktrees/pepadmet-guards-20260520` (HEAD: `62fc1ae`)

---

## 1. 요약

**판정: ✅ APPROVE (조건부 권고 2건 — merge blocker 아님)**

| 체크리스트 항목 | 결과 | 신뢰 등급 |
|---------------|------|---------|
| A: `'SS' in smiles` 검출 정확성 | ✅ 통과 (단 한계 명기 권고) | HIGH |
| A: 하위 호환 (smiles=None 호출) | ✅ 완전 보장 | HIGH |
| B: 신규 10건 테스트 실경로 커버 | ✅ mock은 예외만, 실함수 경로 통과 | HIGH |
| 응답 dict 호환 (`cyclic_ss_bond_present` 신규 추가만) | ✅ 기존 키 무변경 | HIGH |
| 다른 세션 워크트리 충돌 가능성 | ⚠️ 7개 브랜치 동일 파일 수정 (orchestrator 조율 필요) | HIGH |
| PR description pharma/bio 근거 인용 | ✅ §2.2, §3.1, §7-C, §3-A/3-B 명시 | HIGH |

---

## 2. Critical 이슈

**없음.** 발견된 모든 이슈는 권고(non-blocking) 수준.

---

## 3. 묶음 A — `check_pepadmet_applicability()` SS-bond 가드

### 3-A. 검출 로직 검증

**파일**: `pipeline_local/scripts/pharmacology_guards.py:554`

```python
cyclic_ss_bond_present = bool(smiles and "SS" in smiles)
```

**직접 검증 결과** (Python 실행):

| SMILES 예시 | 실제 의미 | `"SS" in smiles` | 판정 |
|------------|---------|-----------------|------|
| `CCSSCCC` | 이황화결합 (표준) | `True` | ✅ 올바름 |
| `N[C@@H](CS)CSSCCC` | Cys3-Cys14 유사 | `True` | ✅ 올바름 |
| `CSCC[C@@H](N)C=O` | Met (단일 S) | `False` | ✅ 올바름 |
| `N[C@@H](CS)C(=O)O` | Cys 단량체 | `False` | ✅ 올바름 |
| `CS(=O)C` | DMSO (S≠SS) | `False` | ✅ 올바름 |
| `CC(C)(S)[C@@H](N)C(=O)O` | Penicillamine | `False` | ✅ 올바름 |
| `CSSSCC` | **trisulfide** | `True` | ⚠️ False Positive (보수적 차단, 안전) |
| `C[S+][S-]C` | 하전 표기 이황화결합 | `False` | ⚠️ False Negative (극히 드문 SMILES) |
| `c1cssc1` (aromatic) | 방향족 디티인 (`ss`) | `False` | ✅ uppercase 체크로 무관 |

**[HIGH] 결론**: PRST 후보 (CSSC 패턴 표준 이황화결합) 에 대해 정확히 동작함.  
- **False Positive** (trisulfide) → 보수적 OOD 판정으로 안전한 방향.  
- **False Negative** (charged `[S+][S-]`) → 표준 RDKit SMILES에서 이황화결합은 `SS`로 표기하므로 실제 발생 가능성 극히 낮음.

### 3-B. 권고 (LOW, non-blocking)

`pharmacology_guards.py:551-554` docstring/주석에 검출 방식 한계 명기 권고:

```python
# SS-bond OOD 가드 (2026-05-21 — reviewer-pharma §7-C)
# 검출 방식: 대소문자 구분 서브스트링 (SMARTS 기반 아님).
# 전제: RDKit 표준 SMILES (이황화결합 = 'SS', 소문자 방향족 ss 제외).
# False positive: trisulfide(CSSSCC) → 보수적 OOD 판정 (안전).
# False negative: 하전 표기 [S+][S-] → 실제 발생 가능성 극히 낮음.
cyclic_ss_bond_present = bool(smiles and "SS" in smiles)
```

**신뢰 등급**: HIGH (직접 실행 검증)

### 3-C. 하위 호환 확인

`smiles: Optional[str] = None` 기본값 → `bool(None and ...)` = `False` → `cyclic_ss_bond_present=False` → 기존 호출 동작 완전 보존.

기존 테스트 76건 모두 PASS 확인 ✅ (직접 실행)

---

## 4. 묶음 B — `composite_scorer` fallback WARN 테스트

### 4-A. 실경로 커버 확인

`pipeline_local/tests/test_composite_scorer_fallback_warn.py` 내 핵심 테스트:

```python
# TestCompositeScorerWarnOnWrapperFailure
with patch("pipeline_local.scripts.predict_admet_pepadmet.predict_admet",
           side_effect=RuntimeError("mock admet failure")):
    results = enrich_candidates_from_wrappers([candidate])
```

**[HIGH]** patch는 예외 발생만 시뮬레이션하고 `enrich_candidates_from_wrappers()` 실제 함수 본문이 실행됨.  
`composite_scorer.py:459-462` 의 `except Exception` 분기를 실제로 통과 → `_append_warning(c, notes, ADMET_FALLBACK_WARNING)` 호출 확인.

단순 mock 검증이 아닌 실 경로 통과 ✅

### 4-B. `_append_warning()` 중복 방지 로직

`composite_scorer.py:361-370`:
```python
def _append_warning(candidate, notes, message):
    if message not in notes:        # ← 중복 방지
        notes.append(message)
    warning_list = _coerce_notes(candidate.get("warnings"))
    if message not in warning_list: # ← 중복 방지
        warning_list.append(message)
    candidate["warnings"] = warning_list
    candidate["fallback_admet_tox"] = True
```

`test_no_duplicate_in_notes` 테스트가 중복 추가 방지를 명시적으로 검증 ✅

### 4-C. `_finite_or_none()` 신규 헬퍼

`composite_scorer.py:301-308`:
```python
def _finite_or_none(value):
    score = float(value)
    if not math.isfinite(score):
        return None
    return score
```

기존 `float(value)` 호출에서 `inf`/`NaN` 반환 방지 개선 — 긍정적 변경.  
관련 테스트 미추가이나 기존 테스트가 커버하므로 허용 수준.

---

## 5. 응답 dict 호환성

`check_pepadmet_applicability()` 반환:

| 키 | 상태 |
|----|------|
| `recommended` | 기존 키, 변경 없음 ✅ |
| `reason` | 기존 키, 변경 없음 ✅ |
| `d_amino_acid_present` | 기존 키, 변경 없음 ✅ |
| `dota_chelator_present` | 기존 키, 변경 없음 ✅ |
| `absolute_confidence` | 기존 키, 변경 없음 ✅ |
| `cyclic_ss_bond_present` | **신규 키** — smiles 미제공 시 항상 `False` ✅ |

기존 caller가 신규 키를 무시해도 동작 무결 ✅

---

## 6. 다른 세션 충돌 분석

`git diff main...HEAD --name-only` 검사 결과, `pharmacology_guards.py`를 수정하는 브랜치 목록:

| 워크트리 | 브랜치 | 비고 |
|---------|--------|------|
| `pepadmet-guards-20260520` | `chore/pepadmet-guards-20260520` | **본 PR** |
| `fe-2level-selector` | `feat/fe-2level-selector-20260521` | ⚠️ FE 브랜치가 guards 파일 포함? |
| `fe-candidate-selector` | `feat/fe-candidate-selector-20260521` | ⚠️ 동상 |
| `pr84-rebase` | `docs/meeting-prep-and-post-audit-20260520` | 리베이스 기반 (충돌 낮음) |
| `pr85-rebase` | `feat/layer1-ensemble-framework-20260520` | Layer1 ensemble 관련, 충돌 가능 |
| `selectivity-guard-20260520` | `chore/selectivity-guard-20260520` | 동일 guards 파일 수정, 충돌 높음 |
| `wetlab-prst-integration` | `feat/wetlab-prst-integration-20260521` | 확인 필요 |
| `worker-pool-4` | `feat/worker-pool-4-20260521` | FlexPepDock 위주, 낮음 |

**[MEDIUM, HIGH신뢰]** `selectivity-guard-20260520` 와 `pr85-rebase` 는 동일 파일을 독립적으로 수정했을 가능성이 있어 merge 순서 조율 필요. **orchestrator에게 merge 순서 결정 요청.**

---

## 7. 테스트 수 검증

| 출처 | 수 |
|-----|---|
| 직접 실행 (test_pharmacology_guards + test_composite_scorer_fallback_warn) | **86 PASS** ✅ |
| PR description 주장 (+ test_composite_scorer*.py) | 122 PASS (직접 검증 범위 밖) |
| main 전체 suite 비교 기준선 | 1 fail, 12 errors (ESM/biopython 없음 — **pre-existing, PR 무관**) |

pre-existing 실패:
- `test_step03b_reference_peptide.py::test_run_approach_b_uses_reference_peptide_sequence_when_seed_missing` → `RuntimeError: ESM dependencies missing` (main에서도 동일 실패)
- `test_compute_docking_rmsd.py` 12 errors → `No module named 'Bio'` (biopython 미설치, main 동일)

---

## 8. PR description pharma/bio 근거 인용 확인

PR description 원문 인용:

> - **reviewer-pharma** `_workspace/55_reviewer-pharma_prst-admet-ood-analysis.md §2.2`: 14aa SS-bond 펩타이드 binary label 0건
> - **reviewer-pharma §3.1**: Octreotide (FDA-승인) 동일 패턴
> - **reviewer-pharma §7-C**: `check_pepadmet_applicability()` 추가 권고
> - **reviewer-biology** `_workspace/55_reviewer-biology_PRST-toxicity-pepadmet-bio-eval.md §3-A/3-B`: 구조적 근거 없음

**[HIGH]** `_workspace/55_reviewer-pharma_*.md`, `_workspace/55_reviewer-biology_*.md` 모두 인용 ✅

---

## 9. 권장 사항

### 9-1. LOW priority (non-blocking, 선택적 follow-up)

`pharmacology_guards.py:551-554` — `'SS'` 검출 방식 한계를 주석으로 명기:

```python
# [현재]
# SMILES의 'SS' 서브구조 = 이황화결합 (예: Cys3-Cys14: ...CSSC...)
# 감지 조건: smiles 인자 제공 AND 'SS' 포함
cyclic_ss_bond_present = bool(smiles and "SS" in smiles)

# [권고 추가]
# 주의: 대소문자 구분 서브스트링 검출 (SMARTS 아님).
# RDKit 표준 SMILES 전제. trisulfide(CSSSCC) → false positive (보수적, 안전).
# 하전 표기 [S+][S-] → false negative (표준 SMILES에서 극히 드묾).
```

### 9-2. MEDIUM priority (orchestrator 조율 필요)

`pharmacology_guards.py` 를 수정하는 7개 브랜치의 merge 순서 사전 조율.  
특히 `chore/selectivity-guard-20260520` 과 `feat/layer1-ensemble-framework-20260520` 은 같은 파일에 독립 변경 가능성이 높음.

---

## 10. 누락된 테스트 케이스

| 항목 | 우선순위 | 근거 |
|------|---------|------|
| `trisulfide SMILES(CSSSCC)` → `cyclic_ss_bond_present=True` 명시적 검증 | LOW | false positive가 의도적임을 문서화 |
| `smiles=""` (빈 문자열) → `cyclic_ss_bond_present=False` | LOW | `bool("" and ...)` = False, 동작은 맞지만 엣지케이스 미테스트 |
| `_finite_or_none(float('inf'))` → `None` 반환 | LOW | 신규 헬퍼이나 테스트 미추가 |

---

## 최종 판정

```
✅ APPROVE

- Critical 이슈: 없음
- 묶음 A SS-bond 검출: PRST 이황화결합 감지 정확. 보수적 false positive(trisulfide) 안전.
- 묶음 A 하위 호환: smiles=None 기본값으로 완전 보장.
- 묶음 B 테스트: 실 실행 경로 커버 확인.
- 응답 dict: 신규 키 추가만, 기존 키 무변경.
- PR description: reviewer-pharma/biology 근거 인용 완비.

권고사항 (merge blocker 아님):
  [LOW]    pharmacology_guards.py:554 — 'SS' 검출 방식 한계 주석 추가
  [MEDIUM] orchestrator에게 pharmacology_guards.py 수정 브랜치 7개 merge 순서 조율 요청
```
