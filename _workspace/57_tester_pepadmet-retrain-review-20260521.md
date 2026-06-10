# 코드 리뷰 보고서 — PR #113 `chore/pepadmet-retrain-20260521`

**reviewer**: tester (reviewer-code 역할)  
**날짜**: 2026-05-21  
**대상 PR**: https://github.com/AI-scientist4BIO/SST14-M_scr/pull/113  
**branch**: `chore/pepadmet-retrain-20260521`  
**worktree**: `.worktrees/pepadmet-retrain-20260521` (HEAD: `a444cc5`)

---

## 1. 요약

**판정: ⚠️ REQUEST_CHANGES**

| 체크리스트 항목 | 결과 | 신뢰 등급 |
|---------------|------|---------|
| 1. Sanity 결과 수치 정합성 | ✅ 완전 일치 | HIGH |
| 2. Disclaimer 명시 (5개 항목) | ✅ 모두 포함 | HIGH |
| 3. ood_detection.py 코드 품질 | ⚠️ 데드 코드 존재 (MEDIUM) | HIGH |
| 4. predict_admet_pepadmet.py 하위 호환 | ✅ 완전 보장 | HIGH |
| 5. retrain_toxicity.py 재현성 (EarlyStopping fix + seed) | ✅ 확인 | HIGH |
| 6. pepadmet_infer_ood.py ood_flag enforcement | ✅ CSV 출력 포함 (advisory 수준 설계) | HIGH |
| 7. 60MB .pth 미포함 의도 명시 | ✅ PR description 명기 | HIGH |
| 8. 다른 세션 충돌 | ⚠️ selectivity-guard-20260520 overlap | HIGH |
| **🚨 Critical: `test_ood_detection.py` git 미포함** | **❌ FAIL** | **HIGH** |

---

## 2. Critical 이슈 — REQUEST_CHANGES 사유

### C-1. `test_ood_detection.py` git 미포함 [HIGH 신뢰]

**파일 위치**: `_workspace/pepadmet_local/tests/test_ood_detection.py` (git 미추적)  
**PR description 주장**: "ood_detection.py — 10 pytest PASS (`tests/test_ood_detection.py`)"  

**직접 확인**:
- 해당 파일은 `_workspace/pepadmet_local/tests/`에 로컬로 존재하며 10개 테스트 확인됨
- 그러나 `git diff main...HEAD --name-only` 에 **포함되지 않음**
- `pipeline_local/tests/` 에 해당 파일 없음

**영향**: 다른 개발자(또는 CI)에서 "10 pytest PASS" 검증 불가. `ood_detection.py` 모듈의 회귀 보호 없음.

**필요 조치**: `_workspace/pepadmet_local/tests/test_ood_detection.py` → `pipeline_local/tests/test_ood_detection.py` 복사 + import 경로 수정 후 PR에 추가.

**수정 예시** (import 경로 변경):
```python
# 현재 (로컬 전용)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pepADMET"))
from utils.ood_detection import OODDetector

# 수정 후 (pipeline_local 패키지 기준)
from pipeline_local.pepadmet_ood.ood_detection import OODDetector
```

---

## 3. 체크리스트 상세

### 3-1. Sanity 결과 정합성 ✅

PR description vs `sanity-check-v3-result-2026-05-21.md` Raw JSON 비교:

| 항목 | PR description | JSON raw | 일치 |
|------|---------------|----------|------|
| Octreotide | 0.132 | 0.1322096437... | ✅ |
| SST-14 native | 0.402 | 0.4021983742... | ✅ |
| PRST max-min | 0.217 | 0.4854... - 0.2681... = 0.2174 | ✅ |
| 상태 | PASS | "status": "PASS" | ✅ |
| 타임스탬프 | 2026-05-21T08:30:29 | 동일 | ✅ |

**[HIGH]** 수치 완전 일치. PR description이 JSON을 정확히 인용함.

### 3-2. Disclaimer 5개 항목 ✅

PR description §알려진 약점:

| 항목 | 포함 여부 |
|------|---------|
| PRST-001 = PRST-004 동일 (0.4022) | ✅ 명시 |
| max-min 0.217 간신히 통과 | ✅ "간신히" 표현 포함 |
| val=0.25 약함 | ✅ "val score 0.25 (best, 4-task 복합)" |
| ranking만 사용 | ✅ "절대값보다 ranking만 참고" |
| in vitro 교차검증 필수 | ✅ "in vitro hemolysis assay 와 교차 검증" |

**[HIGH]** 모든 필수 disclaimer 포함.

### 3-3. ood_detection.py 코드 품질 ⚠️

**파일**: `pipeline_local/pepadmet_ood/ood_detection.py`

#### (a) 데드 코드 — `_compute_mc_dropout_batch()` 181-200줄 [MEDIUM]

```python
# ---- pipeline_local/pepadmet_ood/ood_detection.py:179-202 ----
def _compute_mc_dropout_batch(self, data_loader, args):
    self.model.train()
    all_stds: list[float] = []       # ← 선언만 되고 절대 사용 안 됨

    with torch.no_grad():
        for _ in range(self.n_mc_samples):
            batch_preds: list[np.ndarray] = []
            for batch_data in data_loader:
                ...
                batch_preds.append(pred)   # ← inner scope에서만 존재, 집계 안 됨
    # all_stds는 여전히 []
    self.model.eval()

    # --- 실제 구현은 여기서부터 ---
    all_mc_runs: list[np.ndarray] = []
    self.model.train()
    with torch.no_grad():
        for _ in range(self.n_mc_samples):
            ...
```

**문제**: 
- `all_stds`는 선언만 되고 사용되지 않음 (dead variable)  
- 첫 번째 for 루프 전체 (lines 183-200)는 결과를 집계하지 않아 아무 효과 없음  
- **실질적 영향**: `n_mc_samples × len(data_loader)` 회 불필요한 forward pass 추가 실행 (기본 20회면 train set 20회 추가 순회)

**수정 제안**:
```python
def _compute_mc_dropout_batch(self, data_loader, args):
    """MC Dropout으로 예측 std 계산 (train mode dropout 활성화)."""
    # 데드 코드 블록 삭제 후 실제 구현만 유지
    all_mc_runs: list[np.ndarray] = []
    self.model.train()
    with torch.no_grad():
        for _ in range(self.n_mc_samples):
            run_preds: list[np.ndarray] = []
            for batch_data in data_loader:
                ...
            all_mc_runs.append(np.concatenate(run_preds))
    self.model.eval()
    mc_preds = np.stack(all_mc_runs, axis=0)
    return np.std(mc_preds, axis=0)
```

**신뢰 등급**: HIGH (직접 코드 확인)

#### (b) Hook 등록/해제 안전성 ✅

`_register_h3_hooks()` → `_extract_h3_features()` 종료 후 `_remove_hooks()` 항상 호출 ✅  
`predict_with_ood()` 종료 후 `_remove_hooks()` 호출 ✅  
Race condition 없음 (단일 스레드 가정, multi-GPU 환경 미사용) ✅

#### (c) Mahalanobis singular 행렬 가드 ✅

```python
cov += np.eye(cov.shape[0]) * 1e-6  # regularization
try:
    self._train_cov_inv = np.linalg.inv(cov)
except np.linalg.LinAlgError:
    self._train_cov_inv = np.linalg.pinv(cov)  # fallback to pseudo-inverse
```
singular 행렬 처리 견고 ✅

### 3-4. predict_admet_pepadmet.py 하위 호환 ✅

**변경**:
```python
def predict_admet(
    sequence: str,
    seq_id: str = "query",
    use_modlamp_fallback: bool = True,
    check_pepadmet_web: bool = True,
    smiles: Optional[str] = None,          # 신규 (기본값 None)
    use_local_gnn: bool = True,            # 신규 (기본값 True)
) -> dict:
```

**하위 호환 검증**:
- `smiles=None` → `if use_local_gnn and smiles:` = False → GNN 미실행 ✅
- 기존 caller `predict_admet(seq)` 완전 동일 동작 ✅
- 반환 dict에 `"local_gnn_toxicity": None` 신규 키 추가만 (기존 키 무변경) ✅

**PR #108 (`cyclic_ss_bond_present`) 와 정합**:  
PR #108의 `check_pepadmet_applicability()` 의 `smiles` 파라미터와 의미적으로 일관됨.  
그러나 현재 `predict_admet_pepadmet.py`는 PR #108과는 다른 `smiles` 파라미터를 독립적으로 사용 — 두 함수가 같은 smiles 값을 받을 때 일관성 있음 ✅

**주의사항 [MED 신뢰]**:  
`predict_local_gnn_toxicity()`의 `"ood_warning": True` 는 하드코딩된 상수 (실제 OOD 계산 안 함). descriptor=0 기반 추론이 항상 외삽이므로 의도적이지만, 동적 OOD와 혼동 우려. 주석 추가 권고:
```python
"ood_warning": True,  # 항상 True: descriptor=0 기반 추론 = 항상 외삽 경고
                      # 동적 OOD 감지는 pepadmet_infer_ood.py --fit_ood 경로로 별도 운영
```

### 3-5. retrain_toxicity.py 재현성 ✅

**EarlyStopping filename 절대경로 fix** (`retrain_toxicity.py:252-259`):
```python
_ckpt_dir = str(MODEL_DIR)
os.makedirs(_ckpt_dir, exist_ok=True)
stopper = EarlyStopping(
    patience=ARGS["patience"],
    task_name=ARGS["task_name"],
    mode=ARGS["mode"],
    filename=os.path.join(_ckpt_dir, f"{ARGS['task_name']}_early_stop.pth"),  # ✅ 절대경로
)
```

**[HIGH]** 기존 pepADMET `EarlyStopping`의 상대경로 버그 fix 적용됨.

**seed 명시** (`retrain_toxicity.py:181-182`):
```python
for time_id in range(ARGS["times"]):
    seed = 2020 + time_id  # seed: 2020, 2021, 2022, 2023, 2024
    set_random_seed(seed)
```

**[HIGH]** 5 seed 모두 결정론적 (2020~2024), 재현 가능.

**데이터 명시** (`retrain_toxicity.py:66`):
```python
INPUT_CSV = DATA_DIR / "Toxicity_extended_clean.csv"
```
`pipeline_local/data/Toxicity_extended_clean.csv` (294×2139, git 추적됨) ✅

### 3-6. pepadmet_infer_ood.py ood_flag enforcement ✅

CLI 동작:
1. `ood_flag=True` → CSV에 `ood_flag=True` 컬럼 출력
2. 요약 통계에 `OOD 분자: N/M (X.X%)` 출력
3. 결과를 차단하거나 에러를 내지 않음 (advisory 설계)

PR description: "OOD detection 결합 필수 (ood_flag=True 시 결과 신뢰 금지)" → 코드 내 강제 차단 없음이 **의도적인 설계** (연구 목적 도구). 적절한 수준.

단, **개선 권고** [LOW]: CLI에 `--strict_ood` 플래그 추가 시 `ood_flag=True`인 행은 출력에서 제외하거나 WARNING으로 처리하는 선택지를 제공할 수 있음. (현재 PR 범위 밖)

### 3-7. 60MB .pth 미포함 ✅

PR description §비추적 파일:
> `_workspace/pepadmet_local/pepADMET/model/toxicity_retrained_2026-05-21.pth` (58MB) — git LFS 미설치, 로컬 전용

**[HIGH]** 의도적 누락 명시됨. `.gitignore` 또는 `.gitattributes`에 LFS 설정 필요 여부는 별도 트랙.

### 3-8. 다른 세션 충돌 ⚠️

`predict_admet_pepadmet.py`를 수정하는 브랜치:
- `chore/pepadmet-retrain-20260521` — **본 PR**
- `chore/selectivity-guard-20260520` — ⚠️ **동일 파일 수정**

`pharmacology_guards.py`도 두 브랜치 모두 수정. merge 순서 조율 필요. PR #108이 먼저 merge되면 PR #113에서 rebase 필요.

---

## 4. 배포 경로 문서화 [MEDIUM]

`pepadmet_infer_ood.py:60`: `from utils.ood_detection import OODDetector`  
→ `_workspace/pepadmet_local/pepADMET/utils/ood_detection.py` 를 찾음

실제 확인:
- `_workspace/pepadmet_local/pepADMET/utils/ood_detection.py` **존재** ✅ (이미 복사됨)
- `pipeline_local/pepadmet_ood/ood_detection.py` = git 추적 "소스 진실" 파일

**현재 상태**: 로컬에서는 동작하지만 배포 절차 미문서화.

**권고**: CONTRIBUTING.md 또는 README에 다음 추가:
```bash
# pepADMET 설치 후 OOD 모듈 배포
cp pipeline_local/pepadmet_ood/ood_detection.py \
   _workspace/pepadmet_local/pepADMET/utils/ood_detection.py
```

---

## 5. 누락된 테스트 케이스

| 항목 | 우선순위 | 비고 |
|------|---------|------|
| **`test_ood_detection.py` git 포함** | **Critical** | 재현성 보장 필수 |
| `predict_local_gnn_toxicity()` 모델 미로드 시 graceful fallback 단위 테스트 | Medium | `_try_load_local_gnn()` False 경로 |
| `_compute_mc_dropout_batch()` 데드 코드 제거 후 MC std 실제 계산 검증 | Medium | 데드 코드 수정 후 신뢰성 테스트 |
| `sanity_check_v3.py` — Octreotide ≥ 0.5 실패 시 `sys.exit(1)` 단위 테스트 | Low | CI 트리거 검증 |

---

## 6. 긍정적 항목

- **EarlyStopping 절대경로 fix**: `pepADMET` 원본 코드의 CWD 의존성 버그 해결 ✅
- **Sanity check v3 조건 명확**: `sys.exit(1)` CI 통합 가능 구조 ✅  
- **Mahalanobis regularization**: singular 행렬 → pinv fallback 견고 ✅
- **MY_GNN.py 패치 4건 명시**: `compute_metric append→extend`, `roc_auc_score` 빈 배열 가드 등 upstream 버그 수정 내역 투명하게 기록 ✅
- **descriptor=0 추론 한계 명시**: 코드와 disclaimer 모두에서 일관되게 경고 ✅

---

## 7. 필요 조치 요약

### 🔴 Required (merge blocker)

1. `pipeline_local/tests/test_ood_detection.py` 파일 git에 추가 (import 경로 수정 포함)

### 🟡 Recommended (non-blocking, 추후 follow-up 허용)

2. `ood_detection.py:181-200` 데드 코드 블록 제거 (불필요한 N번 forward pass 방지)
3. 배포 가이드: `ood_detection.py` → pepADMET utils/ 복사 절차 문서화
4. `predict_local_gnn_toxicity()` `"ood_warning": True` 에 "항상 정적 경고" 주석 추가

### ⚪ Optional (Q3 트랙)

5. `pepadmet_infer_ood.py` `--strict_ood` 플래그 추가
6. git LFS 설정 (`.gitattributes`)

---

## 최종 판정

```
⚠️ REQUEST_CHANGES

필수 수정: test_ood_detection.py (10개 테스트)를 pipeline_local/tests/에 추가
→ 수정 후 re-review 불필요 (테스트 10건만 확인하면 됨)

과학적 근거, disclaimer, sanity 수치 정합성, 하위 호환성 모두 양호.
```
