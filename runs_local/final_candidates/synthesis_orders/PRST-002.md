# 합성 의뢰서 — PRST-002

**작성일**: 2026-05-19
**의뢰 분류**: Gate-2 진입 후보 (Tier B — WSS 2위)
**담당**: AI팀 (계산) / RI팀 (합성 협의 필요)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 후보 ID | PRST-002 |
| 서열 (1글자 코드) | AGCKNFIWKTITSC |
| 길이 | 14 aa |
| Tier | B (WSS = 0.582, Pareto rank 2) |
| WSS | 0.582 |
| ΔG (SSTR2, Boltz2) | **-101.8 REU** |
| SST-14 ref ΔG | -95.024 REU |
| ΔΔG vs SST-14 | -6.8 REU (개선) |
| Selectivity margin | **180×** (HEURISTIC — dock score 차이 기반, 실측 Ki 상관 미검증) |
| Stability half-life | **3.8** (HEURISTIC ranking score — `predict_half_life` 출처: `step08_stability.py`; 실측 serum t½ 아님) |
| ADMET 독성 확률 | **1.00** (pepADMET 재검증 2026-05-20; 절대값 신뢰도 LOW, 학습 도메인 외 외삽 가능성) |
| Instability Index (II) | **30.1** (Guruprasad 1990 PEDS 4:155 — II < 40 = stable) |
| Radiolysis 민감 잔기 수 | **2** (Hard Cutoff ≤ 3 통과 — F6, W8 잔존) |
| Hard Cutoff | ADMET 실측 1.00, cutoff 미통과; 외삽 가능성 명시 |

> **ADMET 경고**: 2026-05-20 pepADMET 재검증에서 binary_toxicity=1.00으로 정정됨. 단, SST-14 유사체 cyclic 14aa + Cys3-Cys14 SS bond 학습 도메인 포함 여부가 미확인이라 절대값 신뢰도는 LOW이며 실측 검증 필요.

## ADMET 재검증 (2026-05-20)

| 지표 | 의뢰서 작성 시 (2026-05-19) | 재검증 (2026-05-20) | 출처 |
|-----|--------------------------|--------------------|------|
| 독성 확률 | 0.12 | **1.00** | pepADMET local (PyBioMed estate.py 패치 후) |
| toxicity_type | (미확인) | **hemostasis** | pepADMET 출력 |
| neurotoxicity_type | (미확인) | **Na_inhibitor** | pepADMET 출력 |
| hc50 | (미확인) | -41.7199 | pepADMET 출력 |

의뢰서 작성 시 0.12 값은 `composite_scorer` wrapper 미응답 시 기본값 전파였으며, 실측이 아니었음. 2026-05-20 재검증으로 정정.

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
- pepADMET OOD 가능성 (학습 도메인 외 외삽) — 실측값 신뢰 필요
- SST-14 유사체 임상 이력 존재 → wet-lab 판정이 필수
- Gate-2 wet-lab 진행 중 ADMET 측정 동시 수행 가능

**wet-lab 측정 5종 권고** (의뢰 후 동시 진행):

| # | 측정 항목 | 방법 | 판정 기준 | 우선순위 |
|---|---------|------|---------|---------|
| W-1 | **In vitro hemolysis** HC50 | RBC hemolysis assay (ASTM E2524) | HC50 > 200 μM | **1순위** |
| W-2 | **Cell viability** HepG2/HEK293 | MTT assay, 24h, 10 μM | IC50 > 50 μM | 1순위 |
| W-3 | **Ki binding SSTR2** | ¹²⁵I-Tyr¹¹ SS-14 경쟁 결합 (RBA) | Ki(SSTR2) < 10 nM | **Gate-2 핵심** |
| W-4 | **Serum stability** | LC-MS/MS, human serum 37°C, 0/1/4/24h | t½ > 4h | 2순위 |
| W-5 | **In vivo toxicology** | Rat 7-day repeat dose (SD rat, 3 mg/kg i.v.) | 임상병리 정상 범위 | 3순위 (W-1/W-2 통과 후) |

---

## 치환 근거

SST-14 (AGCKNFFWKTFTSC) 대비:
- **F6 유지**: FWKT pharmacophore의 Phe6 — SSTR2 결합 포켓 접촉 유지 목적.
- **F7 → I** (Ile): Phe7 방향족 고리 제거 → radiolysis 민감도 감소.
- **W8 유지**: pharmacophore 핵심 잔기 (PRST-001과 동일).
- **F11 → I** (Ile): Phe11 방향족 고리 제거 → radiolysis 민감도 감소.
- **결과**: F6(민감)+ W8(민감) = sensitive_count=2 (PRST-001 대비 1 증가하나 cutoff 통과).
- **설계 의도**: F6 유지를 통해 SSTR2 binding pocket과의 π-stacking interaction 보존 → Ki 개선 가능성 탐색.

---

## 수식 (Modification) 상세

| 위치 | 잔기 | 원래 (SST-14) → 변형 | 종류 | 비고 |
|------|------|---------------------|------|------|
| N-말단 | - | H → Ac (선택) | 아세틸화 | RI팀 협의 |
| C-말단 | - | OH → NH2 | 아미드화 | 프로테아제 안정성 |
| Cys3-Cys14 | Cys | SS bond | 이황화 결합 | **치환 불가** |
| N-말단 또는 Lys4 측쇄 | - | DOTA-NHS 접합 | DOTA 킬레이터 | ¹⁷⁷Lu 표지용 — 위치 RI팀 협의 |
| F7 | Phe | → Ile | 자연 AA 치환 | 방향족 제거 |
| F11 | Phe | → Ile | 자연 AA 치환 | 방향족 제거 |

**비천연 아미노산**: 없음.
**D-아미노산**: 없음 (현 설계 기준).

---

## 합성 사양

| 항목 | 기준 |
|------|------|
| 순도 | ≥ 95% (RP-HPLC, 214 nm) |
| 수량 | 5–10 mg |
| 납기 | 협의 예정 (목표: 발주 후 6주) |
| 분자량 확인 | ESI-MS 또는 MALDI-TOF |
| 고리화 확인 | Ellman's reagent test |
| 키랄 순도 | L-아미노산 전용 |
| 보호기 전략 | Cys: Trt 또는 Acm |
| DOTA 접합 | NHS-ester 접합 또는 solid-phase 도입 |

---

## 가설

| 가설 | 내용 |
|------|------|
| H1 | PRST-002는 F6 유지로 SSTR2 결합력을 보강하며 Ki(SSTR2) < 10 nM 달성. selectivity ≥ 10× (SSTR2/SSTR1). ¹⁷⁷Lu 72시간 RCP ≥ 90% (Quencher 병행 권고). |
| H0 | PRST-002의 Ki(SSTR2) 및 5-SSTR 프로파일이 SST-14와 통계적으로 유의미한 차이 없음 (ANOVA p > 0.05). |

---

## 5-SSTR 예측 Ki 프로파일

> HEURISTIC 추정 (신뢰도 LOW). 실측 RBA 필수.

| 수용체 | SST-14 Ki (nM) | PRST-002 예측 Ki | 방향 |
|--------|----------------|----------------|------|
| SSTR1 | ~0.4 | ≥ 5 nM | 낮춤 |
| SSTR2 | ~0.2 | 0.5–5 nM | **target** |
| SSTR3 | ~0.8 | ≥ 10 nM | 낮춤 |
| SSTR4 | ~1.6 | ≥ 5 nM | 낮춤 |
| SSTR5 | ~0.3 | ≥ 10 nM | 낮춤 |

---

## Radiolysis 민감도 분석

| 잔기 | 위치 | 민감도 | 비고 |
|------|------|--------|------|
| Cys3 | 3 | 제외 | SS bond |
| Cys14 | 14 | 제외 | SS bond |
| Phe6 | 6 | 2점 (높음) | pharmacophore 유지 목적 — ¹⁷⁷Lu Quencher 필수 |
| Trp8 | 8 | 2점 (높음) | pharmacophore 유지 |

**sensitive_count = 2** (Hard Cutoff ≤ 3 통과)
**Quencher 전략 우선 적용 권고** (count=2로 72h RCP 하락 위험 증가).

---

## Quencher 전략

| QC 조합 | 내용 | 우선순위 |
|---------|------|---------|
| QC-1 | Methionine 5 mM + Ascorbic acid 1 mM | 1순위 |
| QC-2 | Gentisic acid 2.5 mg/mL | 2순위 |
| QC-3 | HSA 0.5% | 보조 |

---

## 검증 프로토콜

PRST-001과 동일 (QC-1 ~ QC-6 적용). 특히 QC-4 (72h RCP) 및 QC-5 (Ki(SSTR2)) 중점 확인.

---

## 수용 기준

| # | 기준 | Pass 조건 |
|---|------|---------|
| AC-1 | 합성 순도 | ≥ 95% HPLC |
| AC-2 | SS bond 고리화 | Ellman's test 통과 |
| AC-3 | ¹⁷⁷Lu 표지 직후 RCP | ≥ 95% ITLC |
| AC-4 | **¹⁷⁷Lu 72h RCP** | **≥ 90%** |
| AC-5 | Ki(SSTR2) | < 10 nM |
| AC-6 | log SI(SSTR1/SSTR2) | > 1.0 |
| AC-7 | CV (replicate) | < 20% |

---

## 타임라인

| 기간 | 업무 | 담당 |
|------|------|------|
| 발주 후 1주 | PO 발주 | 연구원 |
| 2–3주 | PRST-002 합성 + DOTA 접합 | 합성 협력사 |
| 3주 | QC (순도, SS bond) | 화학팀 |
| 4주 | SSTR1–5 세포 배양 | biology |
| 5주 | ¹⁷⁷Lu 표지 + 안정성 | RI팀 |
| 6–7주 | 경쟁 결합 실험 (full) | biology |
| 8주 | 분석, 보고서 | data |

---

## RI팀 협의 메모

> (RI팀 검토 후 기재)
>
> 협의 필요 항목:
> - DOTA 접합 위치 결정 (Lys4 측쇄 권장)
> - F6(Phe) 보존 시 소수성 증가 → 응집(aggregation) 가능성 SPPS 조건 확인
> - Radiolysis count=2: Quencher QC-1 포함 표지 조건 표준화 협의

---

## 신뢰도 등급표

| 수치 | 출처 | 신뢰 등급 |
|------|------|---------|
| ΔG = -101.8 REU | Boltz2 도킹 | MED |
| Selectivity 180× | dock score 비율 | HEURISTIC |
| half_life 3.8 | `predict_half_life()` | **HEURISTIC (LOW)** |
| ADMET tox 1.00 | pepADMET local 재검증 (2026-05-20); 기존 0.12는 wrapper 미응답 fallback 전파 | LOW |
| II 30.1 | Guruprasad 1990 | MED |
| radiolysis_count 2 | `compute_radiolysis_score()` | MED |

---

> **면책 고지**: 본 의뢰서의 계산 수치는 pre-wet-lab 스크리닝 HEURISTIC ranking 지표입니다. RI팀 협의 없이 발주 금지.
