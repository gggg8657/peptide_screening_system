# Gate-2 합성 의뢰 발주 액션 리스트

**작성일**: 2026-05-20  
**의뢰 결정**: 옵션 B — pepADMET OOD 명시한 채로 합성 의뢰 진행  
**담당**: AI팀 → RI팀 인계

---

## 1. 즉시 액션 (발주 전 RI팀 협의)

### 1-A. PRST-003 DOTA 접합 방법 변경 (최우선 협의)

> **문제**: PRST-003는 K4→R 치환으로 Lys4 측쇄(Nε)를 통한 표준 DOTA 접합 불가.
> PRST-001/002/004는 Lys4(Nε) 접합 → **PRST-003만 별도 경로 필요**.

협의 항목:
- [ ] N-말단 Nα-DOTA 접합 가능 여부 및 조건 (SPPS on-resin vs. 합성 후 접합)
- [ ] Arg4(Pbf 보호기) 탈보호 TFA 농도 최적화 (Pbf deprotection: TFA:TIS:H2O = 92.5:2.5:5)
- [ ] N-말단 DOTA-SST-14 유사체 SSTR2 결합력 영향 — 문헌 확인 (Reubi JC et al. 1992; Buchegger F et al. 2011)
- [ ] 합성 복잡도 증가에 따른 납기/비용 재확인 (추정: +1주, +500,000 KRW/5 mg)

### 1-B. 4개 공통 발주 조건 확인

- [ ] 합성 업체 선정: Peptron (1순위) 또는 RI팀 지정 업체
- [ ] DOTA 접합 방식: NHS-ester (용액상) vs. solid-phase DOTA (업체 협의)
- [ ] 고리화(SS bond) 방법: 공기 산화 vs. DMSO 산화 (on-resin vs. 용액상)
- [ ] Cys 보호기: Trt (표준) vs. Acm (산화 방법에 따라)
- [ ] 목표 순도: ≥ 95% RP-HPLC (214 nm)
- [ ] 목표 수량: 5–10 mg / 후보
- [ ] 납기 목표: 발주 후 6주 (2026-07-01 목표)

---

## 2. 발주 양식 (Peptron 기준)

### PRST-001: AGCKNIIWKTITSC

| 항목 | 내용 |
|------|------|
| 서열 | Ac-Ala-Gly-Cys-Lys(DOTA)-Asn-Ile-Ile-Trp-Lys-Thr-Ile-Thr-Ser-Cys-NH₂ |
| 고리화 | Cys3-Cys14 이황화결합 (SS bond) |
| DOTA 접합 | Lys4 Nε (측쇄 아민) |
| N-말단 | Ac (아세틸화) 또는 H (RI팀 협의) |
| C-말단 | NH₂ (아미드화) |
| MW (계산) | ~1,740 Da (SS bond, DOTA 포함) |
| 순도 목표 | ≥ 95% HPLC |
| 수량 | 5 mg |

### PRST-002: AGCKNFIWKTITSC

| 항목 | 내용 |
|------|------|
| 서열 | Ac-Ala-Gly-Cys-Lys(DOTA)-Asn-Phe-Ile-Trp-Lys-Thr-Ile-Thr-Ser-Cys-NH₂ |
| 고리화 | Cys3-Cys14 이황화결합 |
| DOTA 접합 | Lys4 Nε |
| hc50 pepADMET | -41.7 (외삽, LOW 신뢰도) |

### PRST-003: AGCRNFIWKTITSC ⚠️ RI팀 특별 협의 필요

| 항목 | 내용 |
|------|------|
| 서열 | Ala-Gly-Cys-**Arg**-Asn-Phe-Ile-Trp-Lys-Thr-Ile-Thr-Ser-Cys |
| 고리화 | Cys3-Cys14 이황화결합 |
| DOTA 접합 | **N-말단 Nα** (Lys4→Arg로 측쇄 경로 불가) — **RI팀 협의 후 확정** |
| 추가 보호기 | Arg4: Pbf 보호기 (TFA 탈보호 조건 최적화 필요) |
| hc50 pepADMET | -43.6 (외삽, LOW 신뢰도) |

### PRST-004: AICKNFIWKTITSC

| 항목 | 내용 |
|------|------|
| 서열 | Ala-**Ile**-Cys-Lys(DOTA)-Asn-Phe-Ile-Trp-Lys-Thr-Ile-Thr-Ser-Cys |
| 고리화 | Cys3-Cys14 이황화결합 |
| DOTA 접합 | Lys4 Nε |
| hc50 pepADMET | -45.4 (외삽, LOW 신뢰도) |

---

## 3. Wet-lab 측정 5종 발주 계획

> pepADMET OOD 가능성으로 인해 합성 의뢰와 병행하여 wet-lab 독성 측정이 필수.
> W-3 Ki binding은 Gate-2 핵심 KPI이므로 가장 먼저 발주.

| 우선순위 | 측정 | 방법 | 기관/담당 | 예상 비용 | 납기 |
|---------|------|------|---------|---------|------|
| 1 | In vitro hemolysis HC50 | RBC assay, 4개 후보 | biology팀 또는 CRO | ~200 만원 | 3주 |
| 1 | Cell viability HepG2/HEK293 | MTT, 10 μM, 4개 | biology팀 | ~150 만원 | 3주 |
| 1 | **Ki binding SSTR2** (Gate-2) | ¹²⁵I-Tyr¹¹ SS-14 RBA, 4개 | RI팀 + biology | ~400 만원 | 6주 |
| 2 | Serum stability | LC-MS/MS, 37°C, 4개 | 화학팀 또는 CRO | ~300 만원 | 4주 |
| 3 | In vivo toxicology | Rat 7-day, 2개 (PRST-001 + 1) | 동물실험팀 (W-1/W-2 통과 후) | ~1,000 만원 | 8주 |

**예산 총계 (W-1~W-4)**: ~1,050 만원 / 4 후보  
**예산 (W-5 포함 full)**: ~2,050 만원

---

## 4. ADMET OOD 한계 고지 (의뢰처 전달 필수)

> 4개 후보 모두 pepADMET binary_toxicity=1.00 (hemostasis + Na_inhibitor 분류).
> 단, 학습 데이터(Toxicity.csv 135 row)에 cyclic 14aa SS bond SST-14 유사체 포함 여부 미확인.
> **절대값 신뢰도 LOW** — wet-lab in vitro hemolysis assay(W-1) + cell viability(W-2)가 실측 판정.
> 합성 의뢰는 OOD 가능성을 명시한 채로 진행하며, W-1/W-2 결과 후 최종 Gate-2 통과 여부 결정.

---

## 5. 체크리스트

### 발주 전
- [ ] PRST-003 RI팀 N-말단 DOTA 접합 조건 협의 완료
- [ ] 4건 합성 사양서 (서열 + 변형 + 순도 + 수량) RI팀 확인 서명
- [ ] Peptron(또는 업체) 견적서 수령 + 납기 확인
- [ ] 예산 승인 (합성 4건 + wet-lab W-1~W-4)

### 발주 후
- [ ] 합성 진행 weekly 보고 (Peptron → RI팀 → AI팀)
- [ ] W-1/W-2 hemolysis + cell viability 결과 수령 (3주 내)
- [ ] W-3 Ki binding assay 시작 (SSTR2 membrane 준비 → biology팀)
- [ ] W-4 serum stability LC-MS/MS 의뢰 (4주)
- [ ] 전체 wet-lab 결과 취합 → Gate-2 최종 판정 회의 (8주 후 목표)

---

## 6. 참고 문헌 (RI팀 협의용)

| 문헌 | 내용 | 관련 항목 |
|------|------|---------|
| Reubi JC et al. 1992 Eur J Pharmacol 215:221 | SST-14 Ki SSTR1-5 | W-3 기준값 |
| Bruns C et al. 1994 Mol Pharmacol 45:77 | SMS analogue selectivity | W-3 비교 |
| Maecke HR et al. 2005 J Nucl Med 46:172S | DOTA-SST analogue ¹⁷⁷Lu | DOTA 접합 위치 |
| Buchegger F et al. 2011 Eur J Nucl Med | N-말단 DOTA 결합 활성 | PRST-003 협의 |
| Bernhardt P et al. 2011 Eur J Nucl Med 38:1785 | Quencher DOE 전략 | ¹⁷⁷Lu RCP |
| ASTM E2524 | RBC hemolysis assay 표준 | W-1 방법 |
