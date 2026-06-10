# PPTX D-6 갱신 보고 — Action Items Audit deck

> **요청**: 회의 준비 덱 D-6 보강 (5/20 발견 사항 + PR #111 매트릭스 + PR #113 OOD + PR #112 부록 + PR #109)  
> **빌드 실행일**: 2026-05-26 (로컬) — 파일명 `pptx-d6-update-2026-05-22` 는 사용자 지정 보고서 이름  
> **원칙**: 실측 문서·JSON·EOD만 인용, 외삽·OOD 한계 명시

---

## 산출물

| 항목 | 경로 |
|------|------|
| 빌드 스크립트 | `_workspace/pptx/build_action_items_audit_2026-05-28_d6.js` |
| PPTX (20슬라이드, ~736KB) | `_workspace/pptx/PRST_N_FM_ActionItems_Audit_2026-05-28_d6.pptx` |
| Layer3 차트 PNG (선행 생성) | `_workspace/admet_ai_local/charts/admet_ai_tier_scatter_toxicity_vs_absorption_proxy.png` 등 (`build_prst_admet_ai_charts.py`) |

**빌드 커맨드**

```bash
cd _workspace/pptx
# (선행) Layer3 차트 PNG — raw JSON 기준
python3 ../admet_ai_local/charts/build_prst_admet_ai_charts.py
node build_action_items_audit_2026-05-28_d6.js
```

---

## 슬라이드별 변경 요약

| # | 제목/역할 | 변경 |
|---|-----------|------|
| 1 | 타이틀 | PR #85·#111·#113 main 반영, D-6 deck 문구 |
| 2–12 | Audit 본편 | 페이지네이션만 `… / 20` |
| 13 | 브리지 | PR #111·#112·#113·#108·#109 및 MEETING_PREP 정합 문구 |
| **14** | pepADMET 재검증 | 표·막대 유지(의뢰서 vs 1.00). **PR #113** sanity(Oct≈0.132, SST-14≈0.402, PRST 동일≈0.402, max-min≈0.217) **EOD 근거** 추가 |
| 15–16 | Ensemble / L1 | 동형(푸터만 갱신) |
| **17** | Layer 2 | **PR #112** Spearman ρ=0.571, R²=0.022 부록 + 초기 PR #85 수치(ρ=-0.119) 병기 (`eod-2026-05-21-orchestrator-3layer-and-followup`) |
| **18** | Layer 3 | **PR #111** scatter PNG 삽입 + 표·H-06 캡션 |
| **19** | (신규) 결함 매트릭스 | ADMET 양측 보존, Hard Cutoff 상충, #113 OOD, **K-1/K-2 Task #14** + PR #109 부분 fix |
| **20** | (신규) 6월 로드맵 | DGL/L2, HBM·저자 메일, wet-lab assay, A-02 D-AA (MEETING_PREP §4 Q8 정합) |

**푸터**: `Deck 2026-05-28 D-6`, `p / 20`  
**디자인**: Berry & Cream, Palatino + Garamond (기존 스크립트 유지)

---

## 정합성 체크리스트 (요청 대비)

- [x] 슬라이드 19: ADMET=0.10~0.25 vs pepADMET 1.00 **양측 보존** 명시  
- [x] 슬라이드 19: K-1/K-2 잔여 + PR #109 부분 처리 + Task #14  
- [x] 슬라이드 20: 6월 로드맵 **4항목**  
- [x] 슬라이드 14: **#113** OOD·재훈련·sanity 수치 (EOD `eod-2026-05-21-action-items-closure.md`)  
- [x] 슬라이드 17: **#112** ρ=0.571, R²=0.022 (부록, EOD orchestrator-3layer)  
- [x] 슬라이드 18: **#111** 차트(`charts/README.md` 경로, raw JSON)  
- [x] MEETING_PREP §4 Q1·Q7·Q8: 슬라이드 13·18·20에 교차 언급

---

## 인용 SSOT (할루시네이션 방지)

1. `docs/meet_log/2026-04-06_action_items/MEETING_PREP_2026-05-28.md` — Q&A, D-마감, Q8 로드맵  
2. `docs/meet_log/2026-04-06_action_items/PRST_comprehensive_matrix_2026-05-21.md` — 종합 매트릭스, Hard Cutoff 모순 서술  
3. `_workspace/release/eod-2026-05-21-action-items-closure.md` — PR #113 merge, sanity 수치, Mahalanobis+MC Dropout, K-1/K-2  
4. `_workspace/release/eod-2026-05-21-master-integrated.md` — PR #109 silent fallback vs K-1/K-2  
5. `_workspace/release/eod-2026-05-21-orchestrator-3layer-and-followup.md` — PR #112 Spearman ρ 0.571  
6. `_workspace/pepadmet_local/PRST-candidates_revalidation_2026-05-20.md` — 재검증 표 (슬라이드 14)  
7. `_workspace/admet_ai_local/layer3_prst001_004_octreotide_raw.json` + `installation_test_2026-05-20.md` — Layer3 표 및 차트 입력

---

## 후속 제안

- D-3 전에 차트 PNG를 git에 올릴지(용량)·LFS 여부 확정 시 `build_*_d6.js` 경로 불변 유지 권장.  
- 회의 후 PR #112 결과가 변경되면 슬라이드 17 수치만 SSOT 재확인 후 패치.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-26 | D-6 스크립트·PPTX·본 보고서 초안 생성 |
