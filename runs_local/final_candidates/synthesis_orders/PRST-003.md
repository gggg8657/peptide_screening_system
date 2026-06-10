# 합성 의뢰서 — PRST-003

**작성일**: 2026-05-19
**의뢰 분류**: Gate-2 진입 후보 (Tier B — WSS 4위, 서열 다양성 기여)
**담당**: AI팀 (계산) / RI팀 (합성 협의 필요)

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 후보 ID | PRST-003 |
| 서열 (1글자 코드) | AGCRNFIWKTITSC |
| 길이 | 14 aa |
| Tier | B (WSS = 0.271, Pareto rank 3) |
| WSS | 0.271 |
| ΔG (SSTR2, Boltz2) | **-99.2 REU** |
| SST-14 ref ΔG | -95.024 REU |
| ΔΔG vs SST-14 | -4.2 REU (개선) |
| Selectivity margin | **130×** (HEURISTIC — dock score 차이 기반, 실측 Ki 상관 미검증) |
| Stability half-life | **2.5** (HEURISTIC ranking score — `predict_half_life` 출처: `step08_stability.py`; 실측 serum t½ 아님) |
| ADMET 독성 확률 | **1.00** (pepADMET 재검증 2026-05-20; 절대값 신뢰도 LOW, 학습 도메인 외 외삽 가능성) |
| Instability Index (II) | **35.0** (Guruprasad 1990 PEDS 4:155 — II < 40 = stable, 4개 중 최고값) |
| Radiolysis 민감 잔기 수 | **2** (Hard Cutoff ≤ 3 통과 — F6, W8 잔존) |
| Hard Cutoff | ADMET 실측 1.00, cutoff 미통과; 외삽 가능성 명시 |

## ADMET 재검증 (2026-05-20)

| 지표 | 의뢰서 작성 시 (2026-05-19) | 재검증 (2026-05-20) | 출처 |
|-----|--------------------------|--------------------|------|
| 독성 확률 | 0.20 | **1.00** | pepADMET local (PyBioMed estate.py 패치 후) |
| toxicity_type | (미확인) | **hemostasis** | pepADMET 출력 |
| neurotoxicity_type | (미확인) | **Na_inhibitor** | pepADMET 출력 |
| hc50 | (미확인) | -43.6220 | pepADMET 출력 |

의뢰서 작성 시 0.20 값은 `composite_scorer` wrapper 미응답 시 기본값 전파였으며, 실측이 아니었음. 2026-05-20 재검증으로 정정.

### ⚠️ 신뢰도 한계 (반드시 함께 검토)

- pepADMET 학습 데이터(Toxicity.csv 135 row)에 **SST-14 유사체 cyclic 14aa + Cys3-Cys14 SS bond** 학습 도메인 포함 여부 미확인
- 'hemostasis' + 'Na_inhibitor' 예측은 학습 도메인 외 외삽 가능성 있음
- 절대값 신뢰도: LOW (Hard Cutoff 적용 시 H-06 가드 disclaimer 필수)
- 실측 가능 시 in vitro hemolysis assay 또는 in vivo 평가 권고

> **선정 사유**: K4→R 치환은 양전하 보존 + 곁사슬 연장 → SSTR2 포켓 내 이온 상호작용 변화 탐색. 4개 후보 중 가장 보수적인 선정(WSS 4위)이나, II=35.0으로 stable 범위 내 유지하며 selectivity 130× Hard Cutoff(100×) 충족. 다양성 확보 목적.

---

## Gate-2 의뢰 진행 결정 (옵션 B, 2026-05-20)

> **사용자 결정 (2026-05-20)**: pepADMET binary_toxicity=1.00 OOD 가능성을 명시한 채로 합성 의뢰 진행 (옵션 B).

**결정 근거**:
- pepADMET OOD 가능성 — 실측값 신뢰 필요
- K4→R 치환 (Arg)으로 Lys4 측쇄 DOTA 접합 경로 불가 → RI팀 N-말단 DOTA 조건 사전 협의 필수 (아래 참조)

**⚠️ PRST-003 전용 RI팀 사전 협의 필수 (발주 전)**:
- PRST-001/002/004: Lys4(Nε) 측쇄에 DOTA 접합 가능
- **PRST-003: Lys4 → Arg 치환으로 Lys 측쇄 DOTA 접합 불가** → N-말단 Nα-DOTA 접합으로 전환 필요
- Arg 측쇄(Pbf 보호기) 탈보호 조건 및 N-말단 DOTA 접합이 SSTR2 결합력에 미치는 영향 wet-lab 선 검증 권고
- 합성 복잡도 증가 → 납기/비용 재확인 (기준 대비 +1주 / +500,000 KRW 추정)

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
- **K4 → R** (Arg): Lys4→Arg 치환. 양전하 보존, 곁사슬 길이 연장(guanidinium group). SSTR2 Asp/Glu 잔기와 이온 상호작용 변화 가능성.
- **F6 유지**: pharmacophore Phe6 보존.
- **F7 → I** (Ile): radiolysis 감소.
- **W8 유지**: pharmacophore 핵심.
- **F11 → I** (Ile): radiolysis 감소.
- **구조적 특이점**: K→R 치환은 Instability Index를 SST-14 대비 약간 증가시킬 수 있으나 35.0으로 안정 범위 내.

---

## 수식 (Modification) 상세

| 위치 | 잔기 | 원래 (SST-14) → 변형 | 종류 | 비고 |
|------|------|---------------------|------|------|
| N-말단 | - | H → Ac (선택) | 아세틸화 | RI팀 협의 |
| C-말단 | - | OH → NH2 | 아미드화 | |
| Cys3-Cys14 | Cys | SS bond | 이황화 결합 | **치환 불가** |
| N-말단 또는 Lys4 | - | DOTA 접합 | DOTA 킬레이터 | ¹⁷⁷Lu 표지용 — **K4→R 치환으로 Lys4 DOTA 접합 불가** → **N-말단 접합 필수** |
| K4 | Lys | → Arg | 자연 AA 치환 | Lys4 측쇄 Nε DOTA 접합 불가 → N-말단으로 변경 필수 |
| F7 | Phe | → Ile | 자연 AA 치환 | |
| F11 | Phe | → Ile | 자연 AA 치환 | |

**비천연 아미노산**: 없음.
**D-아미노산**: 없음.

> **중요 — DOTA 접합 위치 변경**: K4→R로 인해 Lys4 측쇄 DOTA 접합이 불가능합니다. N-말단 Nα-DOTA 접합으로 전환 필수. RI팀 사전 협의 후 발주.

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
| 보호기 전략 | Cys: Trt 또는 Acm; Arg: Pbf |
| DOTA 접합 | **N-말단 Nα-DOTA** (K4→R로 Lys4 경로 불가) |

---

## 가설

| 가설 | 내용 |
|------|------|
| H1 | PRST-003의 K4→R 치환은 SSTR2 포켓 내 이온 상호작용 최적화로 Ki(SSTR2) < 10 nM 유지. N-말단 DOTA 접합 후 ¹⁷⁷Lu 72시간 RCP ≥ 90% 달성. |
| H0 | PRST-003의 Ki(SSTR2) 및 SSTR 프로파일이 SST-14와 통계적으로 유의미한 차이 없음 (ANOVA p > 0.05). |

---

## 5-SSTR 예측 Ki 프로파일

> HEURISTIC 추정 (신뢰도 LOW). 실측 RBA 필수.

| 수용체 | SST-14 Ki (nM) | PRST-003 예측 Ki | 방향 |
|--------|----------------|----------------|------|
| SSTR1 | ~0.4 | ≥ 5 nM | 낮춤 |
| SSTR2 | ~0.2 | 1–10 nM | **target** |
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

---

## Quencher 전략

QC-1 (Methionine 5 mM + Ascorbic acid 1 mM) 1순위. 다른 후보들과 동일 조건 표준화.

---

## 검증 프로토콜

PRST-001과 동일 (QC-1 ~ QC-6). DOTA 접합 위치가 N-말단이므로 표지 조건 별도 최적화 필요.

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
| 발주 전 | **N-말단 DOTA 접합 조건 RI팀 사전 협의 (필수)** | RI팀 + 화학팀 |
| 발주 후 1주 | PO 발주 | 연구원 |
| 2–3주 | PRST-003 합성 + N-말단 DOTA 접합 | 합성 협력사 |
| 3주 | QC | 화학팀 |
| 4주 | SSTR1–5 세포 배양 | biology |
| 5주 | ¹⁷⁷Lu 표지 (N-말단 조건) | RI팀 |
| 6–7주 | 경쟁 결합 실험 | biology |
| 8주 | 분석, 보고서 | data |

---

## RI팀 협의 메모

> (RI팀 검토 후 기재)
>
> 협의 필요 항목 (PRST-003 우선 협의 사항):
> - **DOTA 접합 위치 변경 (Lys4→Arg로 Lys 측쇄 경로 불가)**: N-말단 Nα-DOTA 접합 조건 확인
> - N-말단 DOTA 접합이 SSTR2 결합력에 미치는 영향 문헌 검토 (Reubi JC 1992 기반)
> - Arg 잔기(Pbf 보호기) 탈보호 조건 TFA 농도 최적화
> - 합성 비용 증가 예상 (Pbf 보호기 + N-말단 DOTA 조건): 견적 재확인

---

## 신뢰도 등급표

| 수치 | 출처 | 신뢰 등급 |
|------|------|---------|
| ΔG = -99.2 REU | Boltz2 도킹 | MED |
| Selectivity 130× | dock score 비율 | HEURISTIC |
| half_life 2.5 | `predict_half_life()` | **HEURISTIC (LOW)** |
| ADMET tox 1.00 | pepADMET local 재검증 (2026-05-20); 기존 0.20은 wrapper 미응답 fallback 전파 | LOW |
| II 35.0 | Guruprasad 1990 | MED |
| radiolysis_count 2 | `compute_radiolysis_score()` | MED |

---

> **면책 고지**: 본 의뢰서의 계산 수치는 pre-wet-lab 스크리닝 HEURISTIC ranking 지표입니다. **K4→R 치환으로 DOTA 접합 위치가 변경되므로 RI팀 사전 협의 없이 발주 절대 금지.**
