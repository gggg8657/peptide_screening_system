# PRST 게이트-2 패키지 원페이지 (2026-05-21 · D-7 회의 브리프)

목적: **5/25 슬라이드 프리즈** 전 간단 레퍼런스 한 장 (`PRST_one_page_summary_*`).

---

## 메시지 3

1. **Tier S 후보 단일 헤드**: `runs_local/final_candidates/tier_s_candidates.csv` 기준 **PRST-001** 하나뿐 (WSS=1.0, Pareto rank 1, **`tier = S`**). 나머지 PRST-002/003/004는 같은 조직 출력의 **`tier_b_candidates.csv`**에 **`B`** 행으로 남았다 (`composite_scorer.py` 규격 `S/A/B/FAIL`).
2. **다양성 경고 허용**(WARN): PRST-003(K→R+Nα-DOTA 강제)과 PRST-004(G2→I+cand03 SAR 브리지)는 **선택 순위**(WSS)만으로 기능 대체 증명 되지 않는다고 의뢰서 블록이 이미 명시했다 — 발표 시 **항구적 조건부 패널**(RI 합성·wet-lab)로 처리.
3. **OOD 및 H-06 외삽 한계**(필수 디스클레머):

   - **pepADMET** 재실행 네 종 모두 **`binary_toxicity = 1.0`** 및 `hemostasis`/`Na_inhibitor` 레이블이며, 동 결과는 `_workspace/pepadmet_local/PRST-candidates_revalidation_2026-05-20.md` 원문 표에 존재. **교육 데이터 경계 불명·`hc50` 단위 해석 미결론**(동 MD §4).
   - **ADMET-AI Layer 3**(`layer3_prst001_004_octreotide_raw.json`): **순환 펩티드(SS-bond)** 는 훈련 분포 밖일 가능성(H-06). 발표에서는 **패턴 차트**(히트맵·scatter)까지는 허용, **PASS/FAIL 블링크 판단 금지**.
   - `hard_cutoff_pass.csv`는 **`True`**이나 `admet_tox` 숫자는 과거 입력 잔류 가능·재측값과 불일치 ⇒ **통과 문구 재사용 불가**(매트릭스 상 단락에 상세 명시됨).

---

## 다음 단계(권고)

| 우선순위 | 과제 |
|---|---|
| 필수 wet-lab | 의뢰서 W-* 표 참조 → hemolysis, 세포 viability, **`¹²⁵I`-Tyr¹¹ SS-14 RBA Ki**, 혈청 LC-MS/MS stability·이 중 없이 선택성 증폭 증언 불가. |
| OOD 패널 | pepADMET training scaffold 대비 화합물 존재 조사 결과를 디스크에 남김 여부 무관하게 **외삽·LOW 디스크로저 재사용** 가능. |

---

## 합성 발주 상태

- **문서 존재**: `runs_local/final_candidates/synthesis_orders/PRST-001.md` … `PRST-004.md`.
- **옵션 B 사용자 결정문**(외삽 상태에서도 의뢰 진행)은 각 파일 `Gate-2 의뢰 진행 결정 (옵션 B, 2026-05-20)` 절 표제로 실재.
- 실제 **PO 사인·금액·납기**는 본 경로 출력에 포함되지 않았으므로 **주간 스텀프 결정**(D-7 회의 종료 또는 D-4 전) 필요.

타임라인 가이드(의뢰서 패턴 발췌): **발주 후 8주**(QC·생물 피크 포함) 패턴 존재.

---

## 교차 레퍼런스(오늘 산물)

| 유형 | 경로 |
|------|------|
| 매트릭스 | `docs/meet_log/2026-04-06_action_items/PRST_comprehensive_matrix_2026-05-21.md` |
| 차트 디렉터리 | `_workspace/admet_ai_local/charts/` (+ `README.md`) |
| 작업 보고 | `_workspace/release/prst-matrix-2026-05-21.md` |
