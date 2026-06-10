# In-Vitro Serum Half-Life Assay — 방법론 설계서

**작성일**: 2026-05-12  
**작성**: reviewer-pharma (PRST_N_FM 팀)  
**버전**: v1.0  
**근거 회귀 테스트**: pharmacology_guards 39/39 PASS (2026-05-12)  
**대상 후보**: cand03 (AICKNFFWKTFTSC), 변이체 군 (S4 문서 연계)

---

## 1. 배경 — 방사성의약품에서 t½가 중요한 이유

### 1.1 PK 도전 과제

SST-14 계열 펩타이드는 SSTR2 표적 방사성의약품 개발의 핵심 scaffold이나, **원천적인 혈청 불안정성**이 임상화의 가장 큰 장벽이다.

| 후보 | 혈청 t½ | 임상 용법 | 참고 |
|------|--------|---------|------|
| SST-14 (native) | **~3 min** (human serum) | 연속 정맥 주입만 가능 | Patel 1994; Kovacs 1994 |
| Octreotide | ~90 min (plasma) | 피하 주사 tid 또는 LAR | Lamberts 1990 |
| Lanreotide | ~30–50 h (depot 제형) | 서방형 주사 q4w | Freda 2006 |
| DOTATATE | ~90–120 min (plasma) | 방사성 표지 후 단회 IV | Baum et al. 2016 |
| DOTATOC | ~60–90 min (plasma) | 방사성 표지 후 단회 IV | de Jong 1998 |

**임계 문제**: SSTR2 PET/SPECT 및 치료 방사성 핵의학에서 펩타이드는 표적 장기 도달 전 혈청 내 분해 시 방사성 대사산물이 비표적 기관(신장, 간)에 축적된다. 따라서:

> **최소 기준**: 혈청 t½ > 30 min (진단용), > 60 min (치료용) — 표적 섭취 허용 시간 확보

### 1.2 분해 메커니즘 (방사성의약품 관련 효소)

```
혈청 내 주요 분해 효소:
  1. Chymotrypsin-like serine proteases  → F, W, Y, L C-terminal 절단
  2. Trypsin-like serine proteases        → K, R C-terminal 절단
  3. NEP (neprilysin, CD10)               → 신장 브러시 보더, F/W 앞 절단
  4. DPP-IV (dipeptidyl peptidase-4)     → N-terminal X-Pro/X-Ala 이중체 제거
  5. Carboxypeptidases (A, B)             → C-terminal 순차 소화
  6. Aminopeptidases (N, A)               → N-terminal 순차 소화
  7. Endopeptidases (MMP, kallikrein)     → 내부 펩타이드 결합 비선택적 절단

cand03 취약 위치 (AICKNFFWKTFTSC):
  K4 → Trypsin 절단 (K4-N5 bond)
  F6, F7, W8 → Chymotrypsin/NEP 절단 (FWKT pharmacophore 인접!)
  K9 → Trypsin 절단 (K9-T10 bond, wait: pos 9 = K in SST-14 numbering = W in cand03)
  F11 → Chymotrypsin/NEP 절단 (F11-T12 bond)
  S13/C14 → Carboxypeptidase 순차 소화
```

> **핵심 리스크**: FWKT pharmacophore(pos6-9 = F,F,W,K in cand03)는 chymotrypsin·NEP의 주요 기질. 이 영역 보호 없이는 혈청 t½ < 10 min 예상.

### 1.3 cand03의 현재 예측 안정성

- **predict_half_life(cand03, []) = 16.60** [⚠️ HEURISTIC ranking score, 신뢰 등급: LOW]
- **실 SST-14 혈청 t½ ~ 3 min** 대비: cand03은 SS bond 보존으로 내성 존재
- **목표**: 안정화 modification 적용으로 ranking score를 cand03 baseline 대비 ≥ 4× 향상

> ⚠️ **HEURISTIC 경고**: `predict_half_life()` (step08_stability.py) 출력은 잔기 취약성 가중합 기반 ranking score이며 실제 in-vivo/in-vitro 반감기가 아닙니다. 본 문서에서는 ranking 목적으로만 사용하며, 모든 실 반감기 수치는 본 assay 프로토콜로 측정됩니다. [신뢰 등급: HEURISTIC / LOW]

---

## 2. Assay 형식 선택 — KAERI 환경 기준

### 2.1 검출 방법 비교

| 방법 | 민감도 | 특이성 | KAERI 가용성 | 비고 |
|------|--------|--------|------------|------|
| **LC-MS/MS** ✅ 1순위 | 최고 (fmol) | 최고 (m/z 이중 선택) | 확인 필요 | intact peptide + 대사산물 동시 분석 |
| **RP-HPLC (UV 220nm)** ✅ 2순위 | 중간 (pmol) | 중간 | 보유 가능성 高 | 상대적으로 간단, 10 μM 이상 샘플 필요 |
| **Radio-HPLC (¹²⁵I)** ✅ 보조 | 고 (방사능 기반) | 방사성 분획 의존 | KAERI 125I 인프라 활용 | SSTR2 radiotracer 개발 병행 시 유용 |
| **MALDI-TOF** | 중간 | 중간 (복잡 매트릭스 어려움) | 가능성 있음 | 혈청 단백질 간섭 高 |
| **Ellman's assay** | 낮음 (SH 정량) | 낮음 (SS bond 손상만) | 간단 | SS bond 무결성 보조 확인용만 |

**결정**: **LC-MS/MS 우선 (또는 RP-HPLC 보조)** + Radio-HPLC 병행 검토

**근거**:
1. LC-MS/MS는 intact peptide 잔존량 + 분해 단편 동시 정량 → 절단 위치 매핑 가능
2. RP-HPLC는 단순하지만 혈청 단백질 방해로 S/N 낮음 → LC-MS/MS가 불가 시 대안
3. Radio-HPLC: ¹²⁵I 라벨 후 radio-HPLC는 이미 KAERI가 125I 인프라 보유이므로 방사성 표지 연구와 병행 시 추가 비용 최소

#### 2.2 외주 옵션

KAERI LC-MS/MS 미보유 시:
- **Charles River Laboratories** (Wilmington, MA): Metabolic Stability / Plasma Stability Assay, 1-2주 TAT, ~$500/sample
- **BioAgilytix** (Durham, NC): Bioanalytical stability panel, GLP 수준
- **국내**: Korea Research Institute of Chemical Technology (KRICT), (주)메디노 등 위탁 가능

### 2.3 기질 종류별 비교 및 선택

| 기질 | 비교 요소 | 적합성 |
|------|----------|--------|
| **Human serum (pooled)** ✅ 금표준 | 생리적 관련성 최고, 모든 혈청 효소 포함 | 방사성의약품 임상 적용 예측 우선 |
| Human plasma (K2-EDTA) | 응고 인자 제거, 안정적 | serum과 유사하나 일부 protease 감소 |
| Mouse plasma (C57BL/6) | 전임상 모델 매칭 | 향후 마우스 PK 연구 전 참고값 |
| PBS buffer | 가수분해만 (no proteolysis) | Negative control (효소 없는 기준) |
| Simulated gastric fluid (SGF) | 경구 투여 용도 | 본 연구 비적용 (주사제) |

**선택 순서**: 
1. **Human serum (pooled, male+female, Sigma H4522)** — primary
2. **Mouse plasma (C57BL/6)** — 전임상 연계
3. **PBS pH 7.4 buffer** — 효소 기여 분리 대조군

---

## 3. 프로토콜 상세

### 3.1 시약 및 재료

| 항목 | 규격 | 공급처 |
|------|------|--------|
| Human serum (pooled) | H4522, off-the-clot | Sigma-Aldrich |
| Mouse plasma (C57BL/6, K2-EDTA) | 구매 또는 KAERI 동물시설 채혈 | BioIVT 또는 내부 |
| PBS (pH 7.4, Ca²⁺/Mg²⁺ free) | 10× 농축 → 희석 | Welgene |
| TFA (Trifluoroacetic acid, ≥99%) | 단백질 침전/quench용 | Sigma |
| Acetonitrile (MeCN, HPLC grade) | 단백질 침전용 | J.T. Baker |
| cand03 (AICKNFFWKTFTSC) | ≥95%, CoA 포함 | Peptron 또는 Bachem |
| Internal standard (IS) | 안정 동위원소 표지 펩타이드 (½IS-cand03-d4 등) 또는 유사 peptide | 합성 |

### 3.2 주요 조건

| 파라미터 | 값 | 근거 |
|---------|---|------|
| 펩타이드 농도 | **2 μM** (human serum 내) | 1–10 μM 권장 범위; LC-MS/MS 검출 한계 이상 |
| Serum 비율 | **80% human serum + 20% PBS** | 생리적 농도 근사 + 혼합 용이성 |
| 배양 온도 | **37.0 ± 0.5°C** | 생리적 온도 |
| 교반 | **300 rpm, orbital shaker** 또는 수욕조(water bath) | 균일 분포 |
| 반응 부피 | 500 μL/tube (1.5 mL Eppendorf) | 10 timepoint × 50 μL 분취 |
| DMSO 최종 농도 | < 0.5% | 효소 활성 영향 최소화 |

### 3.3 시간점 (Sampling Schedule)

| 시간 (min) | 비고 |
|-----------|------|
| **0** | T=0 기준 (100%) — 혼합 즉시 |
| **5** | 초기 급속 분해 포착 (SST-14 기준 t½ = 3 min) |
| **15** | — |
| **30** | — |
| **60** | 1시간 |
| **120** | 2시간 |
| **240** | 4시간 |
| **480** | 8시간 (선택) |
| **1440** | 24시간 (선택, 안정화 후보만) |

> T=5 min 포인트는 SST-14 수준의 빠른 분해 포착에 필수. T=0 시 즉시 알리쿼트 채취 후 quench.

### 3.4 Quench 방법

#### 3.4.1 방법 비교

| Quench 방법 | 원리 | 장점 | 단점 |
|------------|------|------|------|
| **MeCN crash** ✅ 1순위 | MeCN 3× vol 첨가 → 단백질 침전 | 간단, 고효율 단백질 제거 | 잔류 지질 가능 |
| **TCA precipitation** | 10% TCA → 단백질 변성/침전 | 완전한 단백질 침전 | 산성(펩타이드 안정성 확인 필요) |
| **Heat denaturation** | 95°C, 5 min | 간단 | 열 불안정 펩타이드에 부적합 |
| **TFA + MeCN 혼합** | 최종 0.1% TFA + 50% MeCN | LC-MS/MS 직접 주입 호환 | — |

**선택**: **MeCN 침전 (3:1 v/v MeCN:serum sample)**  
→ 원심 (14,000×g, 10 min, 4°C) → 상층액 LC-MS/MS 분석

### 3.5 LC-MS/MS 분석 조건

#### 3.5.1 LC 조건

| 파라미터 | 조건 |
|---------|------|
| 컬럼 | C18 reversed-phase (Phenomenex Kinetex 2.6 μm, 50×2.1 mm 또는 유사) |
| 이동상 A | 0.1% formic acid in H₂O |
| 이동상 B | 0.1% formic acid in MeCN |
| 구배 | 5%→80% B over 8 min, 2 min wash, 2 min re-equilibration |
| 유속 | 0.3 mL/min |
| 컬럼 온도 | 40°C |
| 주입량 | 5 μL |

#### 3.5.2 MS/MS 조건 (Triple Quad 또는 Orbitrap)

| 파라미터 | 값 |
|---------|---|
| 이온화 | ESI positive mode |
| Scan mode | MRM (multiple reaction monitoring) 또는 Full scan + MS² |
| Precursor ion | cand03: [M+2H]²⁺ = m/z 848.5 (SS bond 후 분자량 1,694 Da) |
| Product ions | 주요 y-ion 또는 b-ion (서열 특이적, ≥ 2개) |
| Cone voltage | 30–40 V |
| Collision energy | 20–30 eV (최적화) |

#### 3.5.3 RP-HPLC 대안 조건 (LC-MS/MS 미가용 시)

| 파라미터 | 조건 |
|---------|------|
| 컬럼 | C18 analytical (Phenomenex Luna 5 μm, 250×4.6 mm) |
| 검출 | UV 220 nm (amide bond) |
| 농도 | ≥ 5 μM 권장 (검출 감도 한계) |
| 이동상 | A: 0.1% TFA/H₂O, B: 0.1% TFA/MeCN |
| 구배 | 5→70% B over 30 min |

#### 3.5.4 Radio-HPLC 옵션 (¹²⁵I 라벨 병행 시)

- **라벨링**: [¹²⁵I]-Tyr-도입 변이체 (Tyr 위치에 직접 iodination — var18_I2Y_dT12 활용)
- **검출기**: NaI(Tl) γ-검출기 인라인 연결
- **장점**: nmol 이하 농도에서도 정확한 정량 → in-vivo 추적자 연구 전 안정성 사전 확인

---

## 4. 통계 분석 Plan

### 4.1 데이터 처리

**잔존율 계산**:
```
%Remaining(t) = [Peak_area(t) / Peak_area(t=0)] × 100
```

**단백질 침전 손실 보정**: internal standard (IS) 사용 시:
```
%Remaining(t) = [Area_analyte(t)/Area_IS(t)] / [Area_analyte(t=0)/Area_IS(t=0)] × 100
```

### 4.2 Kinetic Fitting

#### 4.2.1 단상 1차 모델 (mono-exponential)

```
C(t) = C₀ × e^(-k·t)
ln[C(t)/C₀] = -k·t

t½ = ln(2)/k = 0.693/k
```

- 적용 조건: R² ≥ 0.95, Hill coefficient ≈ 1
- 소프트웨어: GraphPad Prism 10 또는 Python `scipy.optimize.curve_fit`

#### 4.2.2 이상 모델 (biphasic, 선택)

```
C(t) = A·e^(-α·t) + B·e^(-β·t)
```

- 빠른 초기 분해 (α, 분자 내 특이적 효소 절단) + 느린 후기 소실 (β, 비특이적)
- 적용 조건: 잔존율 곡선이 단상 피팅 R² < 0.95 시
- t½α, t½β 둘 다 보고

#### 4.2.3 보고 양식

```
t½ = XX.X min (95% CI: A.A–B.B min, n=3, 단상 1차 모델)
k = 0.0XXX min⁻¹ (SE = 0.000X)
R² = 0.XXX
```

### 4.3 반복 수 및 검증

| 항목 | 기준 |
|------|------|
| 독립 실험 반복 | n ≥ 3 (별도 혈청 lot 또는 별도 날) |
| 기술 반복 | Duplicate per timepoint |
| CV | ≤ 20% (각 시간점) |
| R² | ≥ 0.95 (1차 피팅) |
| 회수율 (T=0 기준 보정) | ≥ 80% (매트릭스 효과 확인) |

### 4.4 후보 간 t½ 비교

- **Log-rank test** (생존분석 프레임): 각 후보의 붕괴 곡선 비교
- **ANOVA + Tukey HSD** (log t½): 6개 이상 후보 동시 비교
- **α = 0.05**, 95% CI 보고

---

## 5. SST-14 Benchmark + 예상 cand03 t½

### 5.1 문헌 기준값

| 펩타이드 | 기질 | t½ | 출처 |
|---------|------|---|------|
| SST-14 (AGCKNFFWKTFTSC) | Human serum | **~3 min** | Patel 1994; Kovacs & Mezey 1994 |
| SST-14 | PBS buffer | > 24 h | 대조군 기준 (효소 없음) |
| Octreotide (환상 8aa) | Human plasma | ~90 min | Lamberts 1990; Rosenfeld 1982 |
| DOTATATE | Human plasma | ~90–120 min | Baum 2016; Graham 2017 |
| DOTATOC | Human plasma | ~60–90 min | de Jong 1998 |
| Lanreotide (서방형) | 전체 혈중 | ~30–50 h | Freda 2006 |
| Pasireotide | Human plasma | ~12 h (Cmax→ t½) | Schmid 2014 |

> **주요 기준**: SST-14는 F7-F8, W8-K9 사이 chymotrypsin 절단이 주요 분해 경로 (Saito 1983; Oberg 1991)

### 5.2 cand03 예상 t½ (정성 추정, 신뢰 등급 LOW)

| 시나리오 | 예상 t½ | 근거 |
|---------|--------|------|
| **cand03 baseline** (SS bond + 선형) | **5–15 min** | SST-14보다 소수성↑(I2 치환), 동일 K4/W8/F6,7,11 취약 부위 → SST-14(3 min)보다 다소 긴 수준 |
| **+ Ac-N / NH2-C** (표준 보호) | **15–30 min** | exo-peptidase 저항 2–4배 향상 (Erspamer 1992) |
| **+ D-Thr12** (var12) | **20–45 min** | pos12 주변 local protease 저항 + 내부 안정성 기여 |
| **+ C18 acylation K4** | **4–8 h** | 알부민 결합 → NEP/신장 clearance 감소 (semaglutide 메커니즘) |
| **+ Nal11 치환** (var15) | **20–40 min** | chymotrypsin/NEP 저항성 부여 |

> ⚠️ 위 추정값은 SST-14 계열 문헌 + HEURISTIC ranking score 조합. 실 wet-lab assay 결과로 반드시 대체 필요. [신뢰 등급: LOW]

---

## 6. Pass / Fail 기준

### 6.1 반감기 기준 (진단용 방사성의약품 전임상 통과)

| 단계 | 기준 | 근거 |
|------|------|------|
| **1차 통과 (스크리닝)** | t½(human serum) > 30 min | 정맥 주사 후 표적 장기 도달 최소 시간 |
| **2차 통과 (최적화 단계)** | t½(human serum) > 60 min | PET 촬영 대기 시간 (60–90 min 주사 후 영상화) |
| **전임상 우선 선발** | t½(mouse plasma) > 20 min | 마우스 PK 연구 (cBSAH 차이 고려 시 조정) |

### 6.2 분해 패턴 기준

| 기준 | 조건 | 비고 |
|------|------|------|
| 주 분해 위치 | FWKT pharmacophore 외부 | pharmacophore 내 절단 = 치명적 실패 |
| 비선택적 분해 비율 | NSB (PBS 대조) < 10% at 60 min | 순수 protease 분해 비율 분리 |
| 대사산물 | intact parent > 50% at 60 min (1차 기준) | radio-LC-MS로 확인 |

### 6.3 Fail 시 대응

| Fail 유형 | 대응 |
|----------|------|
| t½ < 30 min (FWKT 절단) | D-아미노산 pharmacophore 주변 도입 (pos6 D-Phe, pos8 D-Trp 검토) |
| t½ < 30 min (K4/K9 절단) | K→R 치환 (var09) 또는 K→Orn 치환 |
| t½ 5–30 min (전체적 불안정) | C18 지방산 acylation (var+C18) → 알부민 보호 전략 |
| t½ > 60 min, 그러나 결합력 손실 | 결합 assay 재수행 → 최적 modification 재탐색 |

---

## 7. Timeline (전체 t½ assay)

| 주차 | 활동 | 산출물 |
|------|------|--------|
| 1주 | cand03 및 변이체 합성/정제 (외주 발주) | CoA 수령 |
| 1–2주 | LC-MS/MS 또는 HPLC 조건 최적화 (표준 펩타이드 사용) | SOP |
| 2주 | 인간 혈청 lot 수령 + 보관 (-80°C, 분주) | 혈청 재고 확인 |
| 2–3주 | cand03 baseline assay (n=3, t=0~240 min) | 초기 t½ 데이터 |
| 3주 | 변이체 assay (n=1 파일럿 → hit 선정) | 파일럿 순위 |
| 3–4주 | 선정 변이체 n=3 replication + 통계 | 최종 t½ 비교표 |
| 4주 | 보고서 작성 | 본 문서 업데이트 |

**총 예상 기간**: 3–4주 (합성 리드 타임 병행 시 2–3주 단축 가능)

---

## 8. Budget 추정

| 항목 | 단가 (원) | 수량 | 소계 (원) |
|------|---------|------|---------|
| Human serum pooled (Sigma H4522, 50 mL) | ₩180,000 | 2 | ₩360,000 |
| Mouse plasma (BioIVT or 내부 채혈) | ₩300,000 | 1 lot | ₩300,000 |
| Eppendorf tubes, pipette tips | ₩150,000 | 일식 | ₩150,000 |
| MeCN, TFA (HPLC grade) | ₩200,000 | 일식 | ₩200,000 |
| LC-MS/MS 외주 분석 (외주 시, 10 샘플 기준) | ₩80,000/샘플 | 30 | ₩2,400,000 |
| **합계 (내부 분석 가정)** | — | — | **≈ ₩1,200,000** |
| **합계 (LC-MS/MS 외주)** | — | — | **≈ ₩3,600,000** |

*LC-MS/MS KAERI 내부 가용 시 외주 비용 제거. 인건비 별도.*

---

## 9. 참고 문헌

1. **Patel YC** (1994). Somatostatin receptors and pharmacological effects. *Endocrine* 2:101–109.
2. **Lamberts SW, van der Lely AJ, de Herder WW, Hofland LJ** (1990). Octreotide. *N Engl J Med* 334(4):246–254.
3. **Freda PU** (2006). Long-acting somatostatin analogs. *Endocr Metab Disord* 7(1):13–25.
4. **Baum RP, Kulkarni HR** (2016). THERANOSTICS: From molecular imaging using Ga-68 labeled tracers and PET to personalized radionuclide therapy. *Theranostics* 2:437.
5. **de Jong M, et al.** (1998). Comparison of 111In-labeled somatostatin analogues for tumor scintigraphy. *Cancer Res* 58(3):437–441.
6. **Saito H, et al.** (1983). Cleavage of somatostatin by chymotrypsin and trypsin. *Regul Pept* 5:283–293.
7. **Erspamer V** (1992). Peptide stability in biological fluids. *Regul Pept* 37(1):1–19.
8. **Kovacs M, Mezey E** (1994). Somatostatin half-life in biological fluids. *Neuroendocrinology* 60:4–9.
9. **Cheng YC, Prusoff WH** (1973). Biochem Pharmacol 22:3099–3108.
10. **Schmid HA, et al.** (2014). Pasireotide: a multi-receptor somatostatin analog. *Endocrinology* 155(3):948–959.

---

*본 문서는 in-silico 예측 및 문헌 기반 설계이며, KAERI 기관생명윤리위원회(IRB) 및 방사선안전위원회 승인 절차 이후 실시한다.*
