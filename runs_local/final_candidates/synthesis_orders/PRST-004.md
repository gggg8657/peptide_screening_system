# 합성 의뢰서 — PRST-004

**작성일**: 2026-05-19
**의뢰 분류**: Gate-2 진입 후보 (Tier B — WSS 3위, 서열 다양성 기여)
**담당**: AI팀 (계산) / RI팀 (합성 협의 필요)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 후보 ID | PRST-004 |
| 서열 (1글자 코드) | AICKNFIWKTITSC |
| 길이 | 14 aa |
| Tier | B (WSS = 0.365, Pareto rank 2) |
| WSS | 0.365 |
| ΔG (SSTR2, Boltz2) | **-100.0 REU** |
| SST-14 ref ΔG | -95.024 REU |
| ΔΔG vs SST-14 | -5.0 REU (개선) |
| Selectivity margin | **200×** (HEURISTIC — dock score 차이 기반, 실측 Ki 상관 미검증) |
| Stability half-life | **2.0** (HEURISTIC ranking score — `predict_half_life` 출처: `step08_stability.py`; 실측 serum t½ 아님) |
| ADMET 독성 확률 | **1.00** (pepADMET 재검증 2026-05-20; 절대값 신뢰도 LOW, 학습 도메인 외 외삽 가능성) |
| Instability Index (II) | **32.0** (Guruprasad 1990 PEDS 4:155 — II < 40 = stable) |
| Radiolysis 민감 잔기 수 | **2** (Hard Cutoff ≤ 3 통과 — F6, W8 잔존) |
| Hard Cutoff | ADMET 실측 1.00, cutoff 미통과; 외삽 가능성 명시 |

## ADMET 재검증 (2026-05-20)

| 지표 | 의뢰서 작성 시 (2026-05-19) | 재검증 (2026-05-20) | 출처 |
|-----|--------------------------|--------------------|------|
| 독성 확률 | 0.25 | **1.00** | pepADMET local (PyBioMed estate.py 패치 후) |
| toxicity_type | (미확인) | **hemostasis** | pepADMET 출력 |
| neurotoxicity_type | (미확인) | **Na_inhibitor** | pepADMET 출력 |
| hc50 | (미확인) | -45.3764 | pepADMET 출력 |

의뢰서 작성 시 0.25 값은 `composite_scorer` wrapper 미응답 시 기본값 전파였으며, 실측이 아니었음. 2026-05-20 재검증으로 정정.

### ⚠️ 신뢰도 한계 (반드시 함께 검토)

- pepADMET 학습 데이터(Toxicity.csv 135 row)에 **SST-14 유사체 cyclic 14aa + Cys3-Cys14 SS bond** 학습 도메인 포함 여부 미확인
- 'hemostasis' + 'Na_inhibitor' 예측은 학습 도메인 외 외삽 가능성 있음
- 절대값 신뢰도: LOW (Hard Cutoff 적용 시 H-06 가드 disclaimer 필수)
- 실측 가능 시 in vitro hemolysis assay 또는 in vivo 평가 권고

> **선정 사유**: PRST-002와 유사한 치환 패턴이나 G2→I 치환 추가로 Gly-bend 구조 변경 → 수용체 포켓 fitting 다양성 탐색. cand03(AICKNFFWKTFTSC) 계열 연장선으로 기존 검증 데이터(WO-2026-005) 연계 가능.

---

## Gate-2 의뢰 진행 결정 (옵션 B, 2026-05-20)

> **사용자 결정 (2026-05-20)**: pepADMET binary_toxicity=1.00 OOD 가능성을 명시한 채로 합성 의뢰 진행 (옵션 B).
> wet-lab in vitro hemolysis assay 가 결국 정답 — 의뢰 + 측정 병행 원칙 적용.

**결정 근거**:
- pepADMET OOD 가능성 — 실측값 신뢰 필요
- G2→I 치환 (Ala→Ile N-말단) 구조 변화로 포켓 fitting 다양성 탐색 가치 있음
- PRST-001과 동일 Lys4(Nε) DOTA 접합 경로 유지 — 합성 경로 표준화 가능

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
- **G2 → I** (Ile): Gly2의 유연성 감소 → β-turn geometry 변경. 도킹 score 개선 가능성 탐색 (cand03 AICKNFFWKTFTSC 기반 설계 연장).
- **F6 유지**: pharmacophore Phe6 보존.
- **F7 → I** (Ile): radiolysis 감소.
- **W8 유지**: pharmacophore 핵심.
- **F11 → I** (Ile): radiolysis 감소.
- **연계**: cand03 (WO-2026-005, AICKNFFWKTFTSC)에서 F7, F11 추가 치환. 기존 wet-lab 데이터와의 SAR(structure-activity relationship) 직접 비교 가능.

---

## 수식 (Modification) 상세

| 위치 | 잔기 | 원래 (SST-14) → 변형 | 종류 | 비고 |
|------|------|---------------------|------|------|
| N-말단 | - | H → Ac (선택) | 아세틸화 | RI팀 협의 |
| C-말단 | - | OH → NH2 | 아미드화 | |
| Cys3-Cys14 | Cys | SS bond | 이황화 결합 | **치환 불가** |
| N-말단 또는 Lys4 측쇄 | - | DOTA-NHS 접합 | DOTA 킬레이터 | ¹⁷⁷Lu 표지용 |
| G2 | Gly | → Ile | 자연 AA 치환 | β-turn 구조 변경 |
| F7 | Phe | → Ile | 자연 AA 치환 | 방향족 제거 |
| F11 | Phe | → Ile | 자연 AA 치환 | 방향족 제거 |

**비천연 아미노산**: 없음.
**D-아미노산**: 없음 (현 설계 기준).

> **cand03 비교**: cand03 = AICKNFFWKTFTSC (G2→I만 치환). PRST-004는 여기서 F7→I, F11→I 추가 치환. SAR 비교 목적으로 cand03 WO-2026-005 결과와 함께 분석 권장.

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
| DOTA 접합 | NHS-ester 또는 solid-phase 도입 |

---

## 가설

| 가설 | 내용 |
|------|------|
| H1 | PRST-004의 G2→I 치환은 cand03 대비 β-turn geometry를 변경하여 SSTR2 결합력을 유지 또는 개선하며 Ki(SSTR2) < 10 nM 달성. F7/F11→I 치환으로 ¹⁷⁷Lu 72시간 RCP ≥ 90% 달성. |
| H0 | PRST-004의 Ki(SSTR2) 및 RCP가 cand03 (WO-2026-005) 대비 통계적으로 유의미한 차이 없음. |

---

## 5-SSTR 예측 Ki 프로파일

> HEURISTIC 추정 (신뢰도 LOW). 실측 RBA 필수.

| 수용체 | SST-14 Ki (nM) | PRST-004 예측 Ki | 방향 |
|--------|----------------|----------------|------|
| SSTR1 | ~0.4 | ≥ 5 nM | 낮춤 |
| SSTR2 | ~0.2 | 1–5 nM | **target** |
| SSTR3 | ~0.8 | ≥ 10 nM | 낮춤 |
| SSTR4 | ~1.6 | ≥ 5 nM | 낮춤 |
| SSTR5 | ~0.3 | ≥ 10 nM | 낮춤 |

---

## Radiolysis 민감도 분석

| 잔기 | 위치 | 민감도 | 비고 |
|------|------|--------|------|
| Cys3 | 3 | 제외 | SS bond |
| Cys14 | 14 | 제외 | SS bond |
| Phe6 | 6 | 2점 (높음) | pharmacophore 유지 |
| Trp8 | 8 | 2점 (높음) | pharmacophore 유지 |

**sensitive_count = 2** (Hard Cutoff ≤ 3 통과)
**Quencher QC-1 적용 권장**.

---

## Quencher 전략

QC-1 (Methionine 5 mM + Ascorbic acid 1 mM) 1순위 적용. PRST-001/PRST-002와 동일 Quencher 조건 적용으로 표지 프로토콜 표준화 가능.

---

## 검증 프로토콜

PRST-001과 동일 프로토콜 (QC-1 ~ QC-6). cand03(WO-2026-005) 결과와 SAR 비교 분석 추가.

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

PRST-001과 동일 (8주 일정). cand03 WO-2026-005와 병행 진행 시 biology 단계 통합 가능 (SSTR1–5 세포 배양 공유).

---

## RI팀 협의 메모

> (RI팀 검토 후 기재)
>
> 협의 필요 항목:
> - G2→I: Gly→Ile 치환 시 β-turn 억제 → SPPS cyclization 수율 변화 예측
> - cand03(AICKNFFWKTFTSC, WO-2026-005) 대비 SPPS 조건 변경 여부
> - DOTA 접합 위치 — cand03 결과와 통일 권장
> - 납기: cand03 배치와 동시 합성 가능성 (비용 절감)

---

## 신뢰도 등급표

| 수치 | 출처 | 신뢰 등급 |
|------|------|---------|
| ΔG = -100.0 REU | Boltz2 도킹 | MED |
| Selectivity 200× | dock score 비율 | HEURISTIC |
| half_life 2.0 | `predict_half_life()` | **HEURISTIC (LOW)** |
| ADMET tox 1.00 | pepADMET local 재검증 (2026-05-20); 기존 0.25는 wrapper 미응답 fallback 전파 | LOW |
| II 32.0 | Guruprasad 1990 | MED |
| radiolysis_count 2 | `compute_radiolysis_score()` | MED |

---

> **면책 고지**: 본 의뢰서의 계산 수치는 pre-wet-lab 스크리닝 HEURISTIC ranking 지표입니다. RI팀 협의 없이 발주 금지.
