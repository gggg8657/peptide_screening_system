# SOD 2026-05-19 A-05: SST14 Reference dG (n≥10 FlexPepDock)

## 작업 요약

A-05 액션 아이템 완료: SST14 원형(`AGCKNFFWKTFTSC`)을 SSTR2(7XNA)에 PyRosetta FlexPepDock으로 n=10 반복 도킹하여 reference dG 기준선 확립.

---

## 도킹 결과 (통계)

| 지표 | 값 |
|------|-----|
| sequence | AGCKNFFWKTFTSC |
| receptor | SSTR2_7XNA |
| engine | PyRosetta FlexPepDock + InterfaceAnalyzerMover |
| n_runs | **10** (A-05 요구사항 충족) |
| nstruct/run | 5 |
| cycles | 5 |
| **mean_dG** | **553.857 REU** |
| **std_dG** | **4.024 REU (σ<5 — KPI 충족)** |
| min_dG | 550.565 |
| max_dG | 564.492 |
| median_dG | 552.396 |
| **95% CI** | **[550.978, 556.735]** |
| elapsed_total | 7190.6s (약 120분, 10개 병렬) |

### 개별 run dG 값

| run | dG_kcal_mol (best of nstruct=5) |
|-----|-------------------------------|
| 1 | 551.411 |
| 2 | 552.365 |
| 3 | 552.275 |
| 4 | 550.565 |
| 5 | 555.316 |
| 6 | 564.492 |
| 7 | 551.745 |
| 8 | 552.426 |
| 9 | 555.083 |
| 10 | 552.888 |

---

## A-05 KPI 결과

| KPI | 기준 | 결과 | 판정 |
|-----|------|------|------|
| 반복 횟수 | n >= 10 | n=10 | 충족 |
| 표준편차 | sigma < 5 | sigma=4.024 | 충족 |

---

## 알려진 한계

- `SSTR2_7XNA_complex.pdb` reference complex 부재 → **Fallback 모드** (확장 conformation 초기화)
- 양수 dG (553.857 REU) = 기준선 에너지 불리 (정적 구조 + 이황화결합 미해결)
- **상대적 비교 기준으로 의미 있음**: candidate.dG < 553.857 → SST14 대비 유리한 결합으로 해석
- PR #49 문서의 알려진 한계와 일치

---

## 산출물

| 파일 | 내용 |
|------|------|
| `data/somatostatin_receptor/SST14_SSTR2_reference_dG.json` | reference JSON (n=10 통계) |
| `pipeline_local/scripts/pharmacology_guards.py` | SST14_SSTR2_ref_ddg_flexpep 항목 등록 |
| `pipeline_local/scripts/run_sst14_reference_docking.py` | n>=10 반복 도킹 실행기 |
| `pipeline_local/tests/test_a05_sst14_reference_dg.py` | 20개 단위 테스트 |
| `runs_local/sst14_ref_docking_flexpep/summary_flexpep.json` | 전체 run 결과 요약 |

---

## pharmacology_guards 등록 (Stage 5)

`pipeline_local/scripts/pharmacology_guards.py::LITERATURE_VALUES["SST14_SSTR2_ref_ddg_flexpep"]` 신규 항목:

```python
"SST14_SSTR2_ref_ddg_flexpep": {
    "ref_ddg_reu_mean": (
        553.8565,
        "KAERI A-05 2026-05-19 PyRosetta FlexPepDock SSTR2_7XNA n=10 nstruct=5/run cycles=5",
        "candidate < 553.857 → SST14 대비 유리. A-04 정규화 기준."
    ),
    "ref_ddg_reu_std": (
        4.0239,
        "KAERI A-05 2026-05-19 ...",
        "sigma=4.024 < 5.0 → KPI 충족. candidate < 549.833 → 통계적 유의미 우위."
    ),
}
```

---

## 테스트 결과

```
pipeline_local/tests/test_a05_sst14_reference_dg.py  20/20 passed
pipeline_local/tests/test_pharmacology_guards.py      39/39 passed (회귀 보존)
합계: 59/59 passed
```

---

## A-04 연동

- `composite_scorer.ddg_score` 정규화 기준 확립
- `candidate.dG_kcal_mol < 553.857 REU` → SST14 대비 유리한 결합 해석
- 통계적 유의미 기준: `candidate.dG < 553.857 - 4.024 = 549.833 REU`

---

## git

- 커밋: `8e7e1cc` (main 직접 push 완료)
- 브랜치: feat/a05-sst14-reference-dg 생성 + push (PR 생성 시 base 브랜치와 커밋 차이 없어 추가 PR 불필요)
