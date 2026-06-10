# pepADMET 데이터 정제 보고서
## A.A5Pb-data — 2026-05-21 08:06

**작성**: engineer-backend  
**목적**: Toxicity_extended.csv 신규 224 row descriptor 재계산 + 정제 + 분할

---

## 0. 요약

| 항목 | 값 |
|------|-----|
| 입력 (Toxicity_final.csv) | 294 행 |
| SMILES 유효 | 294 |
| SMILES 무효 (제거) | 0 |
| 충돌 라벨 SMILES | 0 |
| descriptor NaN 행 | 26 |
| descriptor NaN 셀 합계 | 55458 |
| SS-bond 행 합계 | 51 |

---

## 1. SMILES 검증

- 입력 총 행: 294
- RDKit `Chem.MolFromSmiles(sanitize=True)` 검증
- 유효: 294
- 무효: 0 → `Toxicity_extended_invalid.csv` 분리

---

## 2. 중복 제거

- 중복 제거 기준: canonical SMILES
- 원본 신규 행 수: 224
- 64개 중복 제거 → 160개 처리 (Step 2에서 이미 적용)

---

## 3. 충돌 라벨

✅ 충돌 라벨 없음

---

## 4. descriptor 잔여 NaN

- NaN 있는 행: **26**
- NaN 셀 합계: **55458**

⚠ NaN 행 원인: descriptor 계산 timeout(90s) 또는 오류
  → MY_GNN.py 학습 시 해당 행 마스크 처리 필요

---

## 5. group 분포

| group | 행 수 | label=0 | label=1 | SS-bond |
|-------|------|---------|---------|---------|
| training | 256 | 92 | 60 | 47 |
| valid | 19 | 11 | 8 | 4 |
| test | 19 | 11 | 8 | 0 |

---

## 6. SS-bond fold 분포

총 SS-bond 행: 51

| fold | SS-bond 행 |
|------|-----------|
| training | 47 (92%) |
| valid | 4 (8%) |
| test | 0 (0%) |

---

## 7. 최종 산출물

- `pepADMET/data/Toxicity_extended_clean.csv` — shape (294, 2139)
- `pepADMET/data/Toxicity_extended_invalid.csv` — 0 행
- 본 보고서: `_workspace/pepadmet_local/data_cleaning_2026-05-21.md`

---

*생성 시각: 2026-05-21 08:06*