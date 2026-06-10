# PRST-001~004 종합 결과 매트릭스 (실측 파일 기준, 2026-05-21)

발표 준비(5/28)용. **실제로 디스크에 존재한 산출물만** 채웠다. ADMET-AI는 VR-cycle/H-06에 따라 **외삽 신뢰도 LOW**로 취급한다.

## Tier 체계 (코드 근거)

`pipeline_local/scripts/composite_scorer.py` 주석 및 로직 요약:

- **S**: WSS 상위 20% **AND** Pareto rank 1 (Hard Cutoff 통과 가정).
- **A**: 상위 20% **XOR** Pareto rank 1.
- **B**: 그 외 Hard Cutoff 통과 후보.
- **FAIL**: Hard Cutoff 미통과.

아래 행의 **Tier** 필드 값은 사용자가 요청한 **CSV 신뢰 소스**
`runs_local/final_candidates/tier_s_candidates.csv`·`tier_b_candidates.csv`
에 명시된 `tier` 열이다 (PRST-001 = S, 나머지 = B).

## Hard Cutoff `admet_tox_max` 관련 모순(문서화만)

- `composite_scorer.py` 기본치: `admet_tox_max = 0.3`.
- `runs_local/final_candidates/hard_cutoff_pass.csv` 및 `tier_*` CSV의 `hard_cutoff_pass` 열은 **PRST-001~004 모두 `True`**.
- 동시에 합성 의뢰서(`runs_local/final_candidates/synthesis_orders/PRST-00x.md`)와
  `_workspace/pepadmet_local/PRST-candidates_revalidation_2026-05-20.md`는
  **pepADMET 재측 `binary_toxicity = 1.0`**을 기록한다.
- 매트릭스는 **CSV의 bool 값**과 **의뢰서/재검증의 ADMET 서술**을 **둘 다** 보존한다(어느 쪽도 추정으로 덮어쓰지 않음).

---

## 종합 표

| 후보 ID | 서열 | Tier | WSS | ΔG (Boltz2) | ΔΔG vs SST-14 | Selectivity vs SSTR1/3/4/5 | Radiolysis 민감 잔기 수 | ADMET (pepADMET, Layer 3 ADMET-AI 보조) | Stability (Layer 1/2 평가) | Hard Cutoff PASS | 합성 가능성 | 의뢰서 경로 |
|--------|-----|------|-----|------------|--------------|----------------------------|------------------------|----------------------------------------|------------------------|------------------|-----------|-----------|
| PRST-001 | AGCKNIIWKTITSC | S | 1.0 | -105.5 REU | -10.5 REU (SST-14 ref -95.024) | Boltz2 기반 HEURISTIC Ki 추정표: SST-14 문헌 Ki 대비 PRST 예측 SSTR2 **0.5–5** nM; **SSTR1 ≥5**, **SSTR3 ≥10**, **SSTR4 ≥5**, **SSTR5 ≥10** nM (`§ 5-SSTR`; 실측 Ki 아님) | 1 | **pepADMET** 재검증: `binary_toxicity 1.0`, `is_toxic true`, `hemostasis`, `Na_inhibitor`, `hc50 -38.6135`. **Layer 3**(보조): `Bioavailability_Ma 0.009889113`, `HIA_Hou 9.522536e-05`, `ClinTox 0.078180075`, `hERG 0.48451337`, MW `1535.858` … 104키 (`layer3_*_raw.json`; H-06 LOW) | `half_life 4.5`(heuristic 순위)·`instability_index 28.5`(tier CSV)·의뢰서 표와 일치. **Layer 1**: 환형/SS-bond 라우팅 근거는 `pipeline_local/scoring/layer1_ensemble.py` L182-186 참조; **본 작업 입력 경로에 PRST별 L1/L2 수치 저장물 없음** | **CSV `hard_cutoff_pass=True`**. 재측 1.00은 규격 단정 재적용 시 **불통과 가능**(의뢰서 명시)·상세 상단 참조 | 무D-AA 표준 아미산·Lys DOTA 또는 N-terminal 협의 (의뢰서). RI 협의 전 발주 금지 | `runs_local/final_candidates/synthesis_orders/PRST-001.md` |
| PRST-002 | AGCKNFIWKTITSC | B | 0.5818861024033437 | -101.8 REU | -6.8 REU | `§ 5-SSTR`: SSTR2 **0.5–5** nM, **SSTR1 ≥5**, **SSTR3 ≥10**, **SSTR4 ≥5**, **SSTR5 ≥10** nM (HEURISTIC) | 2 | pepADMET: **1.0 / hemostasis / Na_inhibitor / hc50 -41.7199**. Layer3: `Bioavail 0.012176523`, `HIA_Hou 0.0002415378`, `ClinTox 0.10665116`, `hERG 0.57710791`, MW `1569.875` | `half_life 3.8`, `instability_index 30.1`·L1 근거 PRST-001과 동일(저장 무) | CSV **True**/재측 1.00과 **상충 가능**(상단 § 참조) | Lys DOTA 또는 N-terminal 협의; F6 Phe 유지→aggregation 검토 필요 | `runs_local/final_candidates/synthesis_orders/PRST-002.md` |
| PRST-003 | AGCRNFIWKTITSC | B | 0.27133577150818544 | -99.2 REU | -4.2 REU | `§ 5-SSTR`: SSTR2 **1–10** nM, 나머지 패턴 동일표 | 2 | pepADMET: **1.0 / … / hc50 -43.6220**. Layer3: `Bioavail 0.0041011209`, `HIA_Hou 7.66203e-06`, `ClinTox 0.055506773`, `hERG 0.51860821`, MW `1597.889` | `half_life 2.5`, `instability_index 35.0`·L1 동일 | CSV **True**/재측 1.00 **상충 가능**(상동) | **Lys 제거(Arg)** → DOTA 반드시 N-말단·합성 추가 비용(의뢰서 경고)·발주 전 RI 필수 | `runs_local/final_candidates/synthesis_orders/PRST-003.md` |
| PRST-004 | AICKNFIWKTITSC | B | 0.3650557297109021 | -100.0 REU | -5.0 REU | `§ 5-SSTR`: SSTR2 **1–5** nM, 오프패턴 표와 동일 | 2 | pepADMET: **1.0 / … / hc50 -45.3764**. Layer3: `Bioavail 0.015079178`, `HIA_Hou 0.0010399686`, `ClinTox 0.14845213`, `hERG 0.67260629`, MW `1625.983` | `half_life 2.0`, `instability_index 32.0`·L1 동일 | CSV **True**/재측 상충 동일 가능 | cand03 WO 연계 SAR·β-turn 변경·Lys DOTA 가능 | `runs_local/final_candidates/synthesis_orders/PRST-004.md` |

---

## 차트 교차 참조

- `_workspace/admet_ai_local/charts/README.md`

---

## 인용 근거(경로)

| 항목 | 경로 |
|------|------|
| 의뢰서 4건 | `runs_local/final_candidates/synthesis_orders/PRST-001.md` … |
| ADMET-AI raw | `_workspace/admet_ai_local/layer3_prst001_004_octreotide_raw.json` |
| pepADMET 재검증 | `_workspace/pepadmet_local/PRST-candidates_revalidation_2026-05-20.md` |
| Tier·WSS | `tier_s_candidates.csv`, `tier_b_candidates.csv`, `hard_cutoff_pass.csv` |

> 참고: `runs_local/final_candidates/p1_sprint_prst001_004/all_candidates.csv`의 PRST-002 행은 `tier`가 `A`로 기록되어 있다. **본 매트릭스는 발표용 SSOT로 상위 `tier_*_candidates.csv`만 사용**했다(동일 코호트라도 스코어 실행 시점·입력이 다를 수 있음).

---

## 다양성(WARN) 라벨

- **PRST-003**: K→R 및 **N-terminal DOTA 강제** — 구조 다양성 + 합성 복잡도 상승(의뢰서 블록).
- **PRST-004**: G2→I + cand03 WO 선행 데이터 연결 — 차세대 SAR 비교 루틴 포함.
