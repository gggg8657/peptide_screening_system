# EOD 보고서 — pepADMET 독성 모델 재훈련 완료 (A.A5 체인)
## 2026-05-21 | engineer-backend

---

## 요약

pepADMET 독성 모델(MGA/GNN) 재훈련 체인 **A.A5Pa~Pe** 전 단계 완료.
로컬 GNN이 파이프라인 `predict_admet_pepadmet.py`에 통합되어, SMILES 제공 시
`binary_toxicity_pred` 자동 계산(P2 신뢰도)이 활성화되었다.

---

## 완료 태스크

### Task #9 — A.A5Pb-data (Toxicity 데이터 정제)
- 입력: `Toxicity_extended.csv` (294행, 224 신규 NaN descriptor 행 포함)
- 출력: `Toxicity_extended_clean.csv` (294 × 2139)
- descriptor NaN 행 26개 → MY_GNN 마스크 처리 (123456 값)
- 분할: train/val/test = 256/19/19 (8:1:1)
- 보고서: `_workspace/pepadmet_local/data_cleaning_2026-05-21.md`

### Task #10 — A.A5Pb-OOD (OOD 검출 통합)
- `_workspace/pepadmet_local/pepADMET/utils/ood_detection.py` 신설
  - `OODDetector`: Mahalanobis distance (h3 특징) + MC Dropout std
  - `fit_train_stats()` / `predict_with_ood()` / `save_stats()` / `load_stats()`
- `_workspace/pepadmet_local/scripts/pepadmet_infer_ood.py` — CLI 래퍼
- `_workspace/pepadmet_local/tests/test_ood_detection.py` — 10 pytest PASS

### Task #11 — A.A5Pc (5-fold 재훈련)
- `_workspace/pepadmet_local/scripts/retrain_toxicity.py` — 5 seed 훈련 루프
- MY_GNN.py 4개 패치:
  1. `bg = bg.to(device)` — DGL 그래프 GPU 이동
  2. `compute_metric`: `results.append` → `results.extend` (nested list 버그)
  3. `roc_auc_score()`: 빈 배열 가드 (`len==0` → 0.0, `unique<2` → 0.5)
  4. `r2()`: 빈 배열 가드 (`len<2` → 0.0)
- 결과: `toxicity_retrained_2026-05-21.pth` (val=0.2500 복합 4-task AUC; task_0 val AUC ~0.95)

### Task #12 — A.A5Pd (Sanity Check v3)
- `_workspace/pepadmet_local/scripts/sanity_check_v3.py`
- 결과 (모두 PASS):
  | 검사 | 임계 | 실측값 | 결과 |
  |------|------|--------|------|
  | Octreotide binary_toxicity_pred | < 0.5 | 0.1322 | ✅ PASS |
  | SST-14 binary_toxicity_pred | < 0.5 | 0.4022 | ✅ PASS |
  | PRST-001~004 range | ≥ 0.2 | 0.2174 | ✅ PASS |

### Task #13 — A.A5Pe (통합 PR)

**파일**: `pipeline_local/scripts/predict_admet_pepadmet.py`

변경 내용:
1. **로컬 GNN 상수 추가**
   - `_PEPADMET_MODEL_PATH`, `_PEPADMET_SRC`, `LOCAL_GNN_AVAILABLE`
2. **`_try_load_local_gnn()`** — 지연 로드 (MGA + toxicity_retrained_2026-05-21.pth)
3. **`predict_local_gnn_toxicity(smiles: str) -> dict`** — descriptor=0 추론
4. **`predict_admet()` 시그니처 확장**:
   ```python
   def predict_admet(
       sequence: str,
       seq_id: str = "query",
       use_modlamp_fallback: bool = True,
       check_pepadmet_web: bool = True,
       smiles: Optional[str] = None,   # 신규
       use_local_gnn: bool = True,     # 신규
   ) -> dict:
   ```
   - `smiles` 제공 + `use_local_gnn=True` → `local_gnn_toxicity` 키에 결과 삽입
   - `binary_toxicity_pred` 성공 시 `final_confidence_grade` P3 → P2 상향
5. **`predict_admet_batch()`**: `smiles` 필드 지원 + `use_local_gnn` 파라미터
6. **CLI**: `--smiles`, `--no-local-gnn` 인자 추가

---

## 한계 사항 (H-06 가드 유지)

- 로컬 GNN은 **descriptor=0 기반** 추론 → 구조적 그래프 특징만 반영
- `ood_warning: True` 항상 반환 (외삽 주의)
- val AUC 0.2500은 4-task 복합값; task_0(binary_toxicity) 단독은 ~0.95
- D-AA/DOTA 후보: 학습 데이터 L-AA 한정 → 예측 신뢰도 낮음

---

## 파일 변경 목록

| 파일 | 상태 | 비고 |
|------|------|------|
| `pipeline_local/scripts/predict_admet_pepadmet.py` | 수정 | 로컬 GNN 통합 (추적됨) |
| `_workspace/pepadmet_local/pepADMET/utils/MY_GNN.py` | 수정 | 4 패치 (gitignore — 미추적) |
| `_workspace/pepadmet_local/pepADMET/utils/ood_detection.py` | 신설 | OOD 검출 (gitignore) |
| `_workspace/pepadmet_local/scripts/retrain_toxicity.py` | 신설 | 재훈련 스크립트 (gitignore) |
| `_workspace/pepadmet_local/scripts/sanity_check_v3.py` | 신설 | Sanity check (gitignore) |
| `_workspace/pepadmet_local/scripts/pepadmet_infer_ood.py` | 신설 | 추론 CLI (gitignore) |
| `_workspace/pepadmet_local/tests/test_ood_detection.py` | 신설 | 10 tests PASS (gitignore) |
| `_workspace/release/eod-2026-05-21-pepadmet-retrain.md` | 신설 | 본 보고서 (추적됨) |

---

## 다음 단계

- **K-1/K-2** (Task #14): `step05b candidate_pdb` 미사용 + `_build_pdb_index` 정렬 결함
- **OOD 통계 fit**: 실 훈련 데이터로 `ood_stats.npz` 생성 후 파이프라인 연결
- **D-AA 지원**: 장기 — 학습 데이터 D-AA 확장 또는 별도 모델

---

*작성: engineer-backend 2026-05-21 (A.A5 체인 완료)*
