# 합성 의뢰서 — PRST-001

**작성일**: 2026-05-19
**의뢰 분류**: Gate-2 진입 후보 (Tier S — 최우선)
**담당**: AI팀 (계산) / RI팀 (합성 협의 필요)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 후보 ID | PRST-001 |
| 서열 (1글자 코드) | AGCKNIIWKTITSC |
| 길이 | 14 aa |
| Tier | **S** (WSS = 1.000, Pareto rank 1) |
| WSS | 1.000 |
| ΔG (SSTR2, Boltz2) | **-105.5 REU** |
| SST-14 ref ΔG | -95.024 REU |
| ΔΔG vs SST-14 | -10.5 REU (개선) |
| Selectivity margin | **250×** (HEURISTIC — dock score 차이 기반, 실측 Ki 상관 미검증) |
| Stability half-life | **4.5** (HEURISTIC ranking score — `predict_half_life` 출처: `step08_stability.py`; 실측 serum t½ 아님) |
| ADMET 독성 확률 | **1.00** (pepADMET 재검증 2026-05-20; 절대값 신뢰도 LOW, 학습 도메인 외 외삽 가능성) |
| Instability Index (II) | **28.5** (Guruprasad 1990 PEDS 4:155 — II < 40 = stable) |
| Radiolysis 민감 잔기 수 | **1** (Hard Cutoff ≤ 3 통과 — W8만 잔존) |
| Hard Cutoff | ADMET 실측 1.00, cutoff 미통과; 외삽 가능성 명시 |

> **ADMET 경고 (A-02 follow-up, HIGH-BLOCKER)**: D-아미노산 또는 비천연 AA 함유 시 pepADMET half-life 적용 불가 확정. 본 서열이 D-AA를 포함할 경우 wet-lab LC-MS/MS serum stability assay 선행 필수.

## ADMET 재검증 (2026-05-20)

| 지표 | 의뢰서 작성 시 (2026-05-19) | 재검증 (2026-05-20) | 출처 |
|-----|--------------------------|--------------------|------|
| 독성 확률 | 0.10 | **1.00** | pepADMET local (PyBioMed estate.py 패치 후) |
| toxicity_type | (미확인) | **hemostasis** | pepADMET 출력 |
| neurotoxicity_type | (미확인) | **Na_inhibitor** | pepADMET 출력 |
| hc50 | (미확인) | -38.6135 | pepADMET 출력 |

의뢰서 작성 시 0.10 값은 `composite_scorer` wrapper 미응답 시 기본값 전파였으며, 실측이 아니었음. 2026-05-20 재검증으로 정정.

### ⚠️ 신뢰도 한계 (반드시 함께 검토)

- pepADMET 학습 데이터(Toxicity.csv 135 row)에 **SST-14 유사체 cyclic 14aa + Cys3-Cys14 SS bond** 학습 도메인 포함 여부 미확인
- 'hemostasis' + 'Na_inhibitor' 예측은 학습 도메인 외 외삽 가능성 있음
- 절대값 신뢰도: LOW (Hard Cutoff 적용 시 H-06 가드 disclaimer 필수)
- 실측 가능 시 in vitro hemolysis assay 또는 in vivo 평가 권고

---

## Gate-2 의뢰 진행 결정 (옵션 B, 2026-05-20)

> **사용자 결정 (2026-05-20)**: pepADMET binary_toxicity=1.00 OOD 가능성을 명시한 채로 합성 의뢰 진행 (옵션 B).
> wet-lab in vitro hemolysis assay 가 결국 정답 — 의뢰 + 측정 병행 원칙 적용.

**결정 근거**:
- pepADMET Toxicity.csv 135 row 학습 데이터에 cyclic 14aa SS bond SST-14 유사체 포함 여부 미확인 → OOD 외삽 가능성
- SST-14 자체 (AGCKNFFWKTFTSC) 는 임상 사용 이력 있음 — 유사체의 실제 독성은 wet-lab에서 판정
- Gate-2 KPI (¹⁷⁷Lu 72h RCP ≥ 90%, Ki(SSTR2) < 10 nM) 달성 여부도 wet-lab 의존
- 계산 ADMET 한계 명시 + 실측 병행이 더 빠른 의사결정 경로

**wet-lab 측정 5종 권고** (의뢰 후 동시 진행):

| # | 측정 항목 | 방법 | 판정 기준 | 우선순위 |
|---|---------|------|---------|---------|
| W-1 | **In vitro hemolysis** HC50 | RBC hemolysis assay (ASTM E2524) | HC50 > 200 μM (안전 마진 확보) | **1순위** |
| W-2 | **Cell viability** HepG2/HEK293 | MTT assay, 24h, 10 μM | IC50 > 50 μM | 1순위 |
| W-3 | **Ki binding SSTR2** | ¹²⁵I-Tyr¹¹ SS-14 경쟁 결합 (RBA) | Ki(SSTR2) < 10 nM | **Gate-2 핵심** |
| W-4 | **Serum stability** | LC-MS/MS, human serum 37°C, 0/1/4/24h | t½ > 4h | 2순위 |
| W-5 | **In vivo toxicology** | Rat 7-day repeat dose (SD rat, 3 mg/kg i.v.) | 임상병리 정상 범위 | 3순위 (W-1/W-2 통과 후) |

---

## 치환 근거

SST-14 (AGCKNFFWKTFTSC) 대비:
- **F6 → I** (Ile): Phe6 방향족 고리 제거 → radiolysis 민감도 감소. 결합 활성 변화 wet-lab 확인 필요.
- **F7 → I** (Ile): Phe7 방향족 고리 제거 → radiolysis 민감도 감소.
- **W8 유지**: FWKT pharmacophore (F-W-K-T) 핵심 잔기. Trp8 치환 시 SSTR2 결합 활성 ~10× 이상 감소 (문헌: Rai et al. 2009 — 환형 SST 유사체).
- **F11 → I** (Ile): Phe11 제거 → radiolysis 민감도 감소.
- **Cys3-Cys14 SS bond 보존**: 핵심 고리화 결합 (ΔΔG 개선의 주요 구조 기여).

---

## 수식 (Modification) 상세

| 위치 | 잔기 | 원래 (SST-14) → 변형 | 종류 | 비고 |
|------|------|---------------------|------|------|
| N-말단 | - | H (자유 아민) | 또는 Ac (아세틸화) | **RI팀 협의** — DOTA 접합 위치에 따라 결정 |
| C-말단 | - | OH → **NH2** (아미드화) | 아미드화 | 프로테아제 안정성 향상 |
| Cys3-Cys14 | Cys | SS bond (고리화) | 이황화 결합 | **치환 불가** — SSTR2 결합 및 구조 핵심 |
| N-말단 또는 Lys4 측쇄 | - | DOTA-NHS 접합 | DOTA 킬레이터 | **¹⁷⁷Lu 표지용** — 위치는 RI팀 협의 (Lys4 측쇄 Nε 접합 권장) |
| F6 | Phe | → Ile | 자연 AA 치환 | 방향족 제거, radiolysis 감소 |
| F7 | Phe | → Ile | 자연 AA 치환 | 방향족 제거, radiolysis 감소 |
| F11 | Phe | → Ile | 자연 AA 치환 | 방향족 제거, radiolysis 감소 |

**비천연 아미노산**: 없음 (표준 20종만 사용).
**D-아미노산**: 없음 (현 설계 기준). D-AA 추가 시 pepADMET 적용 불가 + RI팀 별도 SPPS 조건 협의 필요.

---

## 합성 사양

| 항목 | 기준 |
|------|------|
| 순도 | ≥ 95% (RP-HPLC, 214 nm) |
| 수량 | 5–10 mg (in vitro SSTR1–5 경쟁 결합 + ¹⁷⁷Lu 표지 실험 고려) |
| 납기 | 협의 예정 (목표: 발주 후 6주) |
| 분자량 확인 | ESI-MS 또는 MALDI-TOF |
| 고리화 확인 | Ellman's reagent test (free Cys 부재 확인) |
| 키랄 순도 | L-아미노산 전용; D-아미노산 추가 시 별도 chiral HPLC 협의 |
| 보호기 전략 | Cys: Trt 또는 Acm (SS bond 형성 방법에 따라 협의) |
| DOTA 접합 | 합성 후 NHS-ester 접합 또는 solid-phase DOTA 도입 (RI팀 선택) |

---

## 가설

| 가설 | 내용 |
|------|------|
| H1 | PRST-001은 SSTR2에 대해 Ki < 10 nM을 나타내며 SSTR1 대비 selectivity ≥ 10× 달성. ¹⁷⁷Lu 표지 후 72시간 RCP ≥ 90% 유지 (Radiolysis hard cutoff count=1 기반). |
| H0 | PRST-001의 Ki(SSTR2) 및 5-SSTR 프로파일이 SST-14와 통계적으로 유의미한 차이 없음 (ANOVA p > 0.05). |

---

## 5-SSTR 예측 Ki 프로파일

> 하기 예측치는 Boltz2 도킹 score 기반 HEURISTIC 추정 (실측 Ki 아님, 신뢰도 LOW).
> 실측 ground truth: ¹²⁵I-Tyr¹¹ SS-14 방사선 수용체 결합 분석 (RBA) 필수.

| 수용체 | SST-14 Ki (nM, 문헌) | PRST-001 예측 Ki | 방향 |
|--------|---------------------|----------------|------|
| SSTR1 | ~0.4 | ≥ 5 nM (추정) | 낮춤 (selectivity 목적) |
| SSTR2 | ~0.2 | 0.5–5 nM (추정) | **target** |
| SSTR3 | ~0.8 | ≥ 10 nM (추정) | 낮춤 |
| SSTR4 | ~1.6 | ≥ 5 nM (추정) | 낮춤 |
| SSTR5 | ~0.3 | ≥ 10 nM (추정) | 낮춤 |

> SST-14 Ki 출처: Reubi JC et al. 1992 Eur J Pharmacol 215:221-231; Bruns C et al. 1994 Mol Pharmacol 45:77-85.

---

## Radiolysis 민감도 분석

| 잔기 | 위치 | 민감도 | 비고 |
|------|------|--------|------|
| Cys3 | 3 | 제외 | SS bond 구성 — 치환 불가 |
| Cys14 | 14 | 제외 | SS bond 구성 — 치환 불가 |
| Trp8 | 8 | 2점 (높음) | **유일 민감 잔기** — pharmacophore 보존 목적으로 유지 |
| (F6, F7, F11) | 6, 7, 11 | 제거 | → Ile 치환으로 민감도 제거 |

**sensitive_count = 1** (Hard Cutoff ≤ 3 통과)
**¹⁷⁷Lu 72시간 RCP 목표**: ≥ 90% (Quencher 전략 병행 권고 — 아래 참조)

---

## Quencher 전략 (72시간 RCP 유지용, 서호성 박사 제안)

| QC 조합 | 내용 | 우선순위 |
|---------|------|---------|
| QC-1 | Methionine 5 mM + Ascorbic acid 1 mM (Lutathera® 처방 기반) | 1순위 |
| QC-2 | Gentisic acid 2.5 mg/mL | 2순위 |
| QC-3 | Human serum albumin (HSA) 0.5% | 보조 |
| QC-4 | 저산소 완충액 (N2 purge) | 보조 |

> 참고: Bernhardt P et al. 2011 Eur J Nucl Med 38:1785-1795 (Quencher DOE 전략)

---

## 검증 프로토콜

| 단계 | 내용 | 기준 |
|------|------|------|
| QC-1 (화학) | RP-HPLC 순도 + ESI-MS 분자량 | 순도 ≥ 95%, MW ±0.5 Da |
| QC-2 (SS bond) | Ellman's reagent → 자유 SH 부재 | OD412 < 0.05 (blank 대비) |
| QC-3 (표지) | ¹⁷⁷Lu-DOTA-PRST-001 ITLC | RCP ≥ 95% (직후) |
| QC-4 (안정성) | ¹⁷⁷Lu-PRST-001 72h HPLC RCP | **RCP ≥ 90%** (acceptance criterion) |
| QC-5 (결합) | SSTR2 경쟁 결합 (¹²⁵I-Tyr¹¹ SS-14) | Ki(SSTR2) < 10 nM |
| QC-6 (선택성) | 5-SSTR 전체 Ki 프로파일 | log SI(SSTR1/SSTR2) > 1.0 |

---

## 수용 기준 (Acceptance Criteria)

| # | 기준 | Pass 조건 |
|---|------|---------|
| AC-1 | 합성 순도 | ≥ 95% HPLC |
| AC-2 | SS bond 고리화 | Ellman's test 통과 |
| AC-3 | ¹⁷⁷Lu 표지 직후 RCP | ≥ 95% ITLC |
| AC-4 | **¹⁷⁷Lu 72h RCP** | **≥ 90%** (Gate-2 핵심 KPI) |
| AC-5 | Ki(SSTR2) | < 10 nM |
| AC-6 | log SI(SSTR1/SSTR2) | > 1.0 |
| AC-7 | CV (replicate) | < 20% |

---

## 타임라인

| 기간 | 업무 | 담당 |
|------|------|------|
| 발주 후 1주 | PO 발주, 시약 입하 추적 | 연구원 |
| 2–3주 | PRST-001 SPPS 합성 + DOTA 접합 | Peptron (또는 협력사) |
| 3주 | QC-1 순도, QC-2 Ellman | 화학팀 |
| 4주 | SSTR1–5 세포 배양, membrane 추출 | biology |
| 5주 | ¹⁷⁷Lu 표지 (QC-3, QC-4) | RI팀 |
| 5–6주 | Pilot Kd binding (n=1) | biology |
| 6–7주 | Full competition (n=3 × 3 biol) | biology |
| 8주 | Ki 계산, 통계, 보고서 | data |

---

## RI팀 협의 메모

> (RI팀 검토 후 기재)
>
> 협의 필요 항목:
> - DOTA 접합 위치: N-말단 vs Lys4(Nε) 측쇄
> - 합성 수율 예상 (목표 ≥ 20%)
> - Cys 보호기 전략 (Trt vs Acm, oxidative 고리화 vs on-resin)
> - Ile 치환이 SPPS 효율에 미치는 영향 (aggregation 가능성)
> - 납기 및 비용 (목표: 발주 후 6주, ≤ 3,000,000 KRW/5 mg)

---

## 신뢰도 등급표

| 수치 | 출처 | 신뢰 등급 | 비고 |
|------|------|---------|------|
| ΔG = -105.5 REU | Boltz2 도킹 (SSTR2 PDB 7XMS) | MED | 실험 IC50 미검증 |
| Selectivity 250× | dock score 비율 | HEURISTIC | 실측 Ki 상관 미검증 |
| half_life 4.5 | `predict_half_life()` heuristic | **HEURISTIC (LOW)** | ranking score 전용; 실측 serum t½ 아님 |
| ADMET tox 1.00 | pepADMET local 재검증 (2026-05-20) | LOW | 기존 0.10은 wrapper 미응답 fallback 전파; hemostasis/Na_inhibitor 예측은 외삽 가능성 |
| II 28.5 | Guruprasad 1990 | MED | 세포 내 안정성 proxy |
| radiolysis_count 1 | `compute_radiolysis_score()` | MED | proxy 지표; 실측 RCP 필요 |

---

> **면책 고지**: 본 의뢰서의 계산 수치(ΔG, selectivity margin, half-life, ADMET)는 pre-wet-lab 스크리닝 단계의 HEURISTIC ranking 지표이며 실험적 검증을 대체하지 않습니다. 최종 후보 승인은 Gate-2 (¹⁷⁷Lu 표지 + RCP + Ki 측정) 결과에 따릅니다. RI팀과의 합성 가능성 협의 없이 발주 금지 (서호성 박사 지침).
