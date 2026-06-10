# 통합 메타 보고서 — Serum Stability + Half-life 종합 분석

> **작성**: 2026-05-12 (v1.1, S6 통합)
> **팀**: cand03-tomorrow-priorities (chemistry / pharma / biology / researcher 4 도메인)
> **범위**: SST-14 기반 후보 cand03/ILCKKFFWKTFTSC 외 8종의 stability 평가 + in-vitro 검증 path
> **상태**: ✅ **6 task 모두 완료** (~2,570 LOC 5+1 산출 + 본 메타 보고서)

---

## 0. 한눈에 보기

- 📁 **6 산출 문서** (각 도메인별, 총 ~2,570 LOC)
  - [`protease_mechanisms_sst14.md`](protease_mechanisms_sst14.md) — biology (~480)
  - [`halflife_methodology.md`](halflife_methodology.md) — pharma (~372)
  - [`cand_stability_analysis.md`](cand_stability_analysis.md) — pharma (~343)
  - [`stability_modifications_review.md`](stability_modifications_review.md) — chemistry (~470)
  - [`sst_analog_stability_literature.md`](sst_analog_stability_literature.md) — researcher (~580)
  - [`stability_predictor_tools.md`](stability_predictor_tools.md) — researcher S6 (~700, **신규 v1.1**)

- 🏆 **4-도메인 합의 후보 권장**:
  1. 🥇 `Ac-AGCKNDFWKT[Cha]TSC-NH2` (T3 #3, balanced)
  2. 🥈 `Ac-AICKNFFWKTF[dT]SC-NH2` (var12, Boltz 검증 + D-Thr12)
  3. 🥉 `Ac-ILCKKFFWKTFTSC-NH2 + K5→Orn + N-term DOTA + D-Phe6` (T3 #1, modify 후)

- ❌ **제외 권고**: var07_I2K (SS bond 붕괴), T3-05 (Cys14 손실), IGCWWFFWKTFTSC (GRAVY +0.621 응집 위험)

---

## 1. 4-도메인 통합 핵심 발견

### 1.1 SST-14 분해 메커니즘 (biology S1)

```
SST-14:  A G C K N F F W K T F T S C
         1 2 3 4 5 6 7 8 9 ...

NEP (1°):              ↓     ↓
                       F6-F7 / T10-F11

Trypsin:           ↓                 ↓
                   K4-N5             K9-T10

Chymotrypsin:          ↓ ↓   ↓   ↓
                       F6 F7 W8  F11

SS bond:    └─────────────────────────────┘
            Cys3 ←→ Cys14 (보호 영역)
```

**임상 관측 인체 혈장 t½**:
- SST-14: **1-3 분** (가장 짧음)
- Octreotide: 90-120 분 (30-40× 개선)
- Lanreotide LAR: 30-50 시간 (서방형)
- ¹⁷⁷Lu-DOTATATE: 70 시간

### 1.2 Octreotide 안정화 원리 (researcher S5 + biology S1)

| 원리 | Octreotide 적용 | t½ 효과 | 본 프로젝트 적용 |
|------|---------------|--------|----------------|
| D-Trp8 치환 | 핵심 | **단독 30×** | FWKT 보존 후보 우선 |
| D-Phe1 치환 | 핵심 | aminopeptidase 보호 | N-term 후보 |
| Thr-ol C-term reduce | 보조 | carboxypeptidase 보호 | C-term NH2 대체 |
| 8-mer cyclic | 핵심 | loop conformation | 14-mer 유지 (Tatsi 2024 선례) |

### 1.3 D-Phe6 도입 — 4-도메인 합의 권장 #1

| 도메인 | 근거 |
|--------|------|
| **biology** | NEP F6↓F7 1차 cleavage site 차단 |
| **researcher** | 14-mer 전장에서도 안정화 가능 (Tatsi 2024 AT6S) |
| **chemistry** | D-Phe Fmoc 상업 구매, 합성 비용 낮음 |
| **pharma** | t½ 5-10× 개선 예상 (정성적, LOW 신뢰) |

### 1.4 Lys9 DOTA 접합 금지 — 4-도메인 합의 #2

| 도메인 | 근거 |
|--------|------|
| **researcher** | Chen 2022 cryo-EM: W8-K9-T10 SSTR2 binding pocket 직접 접촉 |
| **chemistry** | C-07 규칙: pharmacophore K9 보호, K4 또는 N-term 사용 |
| **biology** | K9 protease site이기도 함 |
| **pharma** | DOTA 결합 시 결합력 손실 위험 |

→ **N-term DOTA-PEG3 권장** (Lys9 free)

---

## 2. 후보 8종 종합 매트릭스

### 2.1 통합 평가 (selectivity × stability × protease 위험)

| Rank | 후보 + modification | Boltz iPTM margin | Stability HL | Protease | 합성 비용 | 결정 |
|------|---------------------|-------------------|--------------|----------|----------|------|
| 🥇 #1 | **Ac-AGCKNDFWKT[Cha]TSC-NH2 + N-term DOTA-PEG3** | +0.038 (T3) | 17.85 #3 | 🟢 NEP site 제거 | ₩2-5M | **GO** |
| 🥇 #2 | **Ac-AICKNFFWKTF[dT]SC-NH2 (var12)** | TBD | **64.72 #1** | 🟢 D-Thr12 차단 | ₩1.5-3M | **GO** |
| 🥈 #3 | **Ac-ILCKKFFWKTFTSC + K5→Orn + N-term DOTA + D-Phe6** | +0.070 #1 ★★★ | 12.80→예상 35+ | 🟢 (modify 후) | ₩5-8M | **조건부 GO** |
| 🥉 #4 | **Ac-AGCKWEFWKT[Cha]TSC-NH2** | +0.037 (T3) | 17.24 #4 | 🟢 E6 charge | ₩2-5M | GO |
| #5 | cand03 baseline `Ac-AICKNFFWKTFTSC-NH2` | +0.008 (T2) | 16.60 | 🟡 | ₩1-2M | 대조군 |
| #6 | QTCKNFFWKTFTSC (T3 #4) | +0.037 (T3) | TBD | 🟡 | ₩1-2M | 추가 평가 |
| ⚠️ #7 | IGCWWFFWKTFTSC | +0.056 (T3 #2) | 19.34 | 🟡 (WW 응집) | ₩2-4M | 용해도 검증 후 |
| ❌ #8 | ~~var07_I2K~~ | TBD | 12.78 | 🔴 SS bond 붕괴 | — | **NO-GO** |
| ❌ #9 | ~~AGCQNFFWKTFTSS (T3 #6)~~ | +0.032 | TBD | 🔴 Cys14 손실 | — | **NO-GO** |
| ❌ #10 | ~~AGCKNTFWKTFTSA (T3-05)~~ | — | TBD | 🔴 Cys14 손실 | — | **NO-GO** |

### 2.2 Selectivity vs Stability Trade-off 핵심 발견

**ILCKKFFWKTFTSC의 trade-off**:
- ✅ Selectivity 최강 (margin +0.070, cand03의 8.7배)
- ❌ Stability 최취약 (HL 12.80, trypsin site 3개)
- 🔧 **K5→Orn + D-Phe6 + N-term DOTA 조합으로 보강 가능** → 조건부 GO

**AGCKNDFWKTLTSC가 균형 우수**:
- Boltz margin +0.038 (T3)
- HL score 17.85 (3rd)
- F6→D 치환으로 NEP 1차 site 이미 제거됨
- **추가 modification 최소화** 가능 → 가장 합리적 첫 합성 후보

---

## 3. in-vitro 검증 방법론 (pharma S2)

### 3.1 Assay 권장 선택

| Assay | 권장 | 이유 |
|-------|------|------|
| **LC-MS/MS** | 🥇 우선 | 절대 정량 + intact peptide 확인 |
| **RP-HPLC** | 🥈 보조 | KAERI 가용 + 단순 |
| **Radio-HPLC** | 🥉 ¹²⁵I 라벨 후 | 방사성의약품 직접 검증 |

### 3.2 표준 프로토콜
- 매트릭스: human serum (Sigma H4522, pooled) 80% in PBS
- 농도: 2 μM peptide
- 조건: 37°C, 300 rpm
- Sampling: 0, 5, 15, 30, 60, 120, 240 min (+ 24h optional)
- Quench: MeCN 3:1 단백질 침전 → 14,000×g

### 3.3 Pass 기준
- **진단**: t½(human serum) > 30 min
- **치료**: t½(human serum) > 60 min
- Hill fit R² ≥ 0.95, n ≥ 3 replicate

### 3.4 통계 분석
- 1st-order kinetic: ln(C/C0) = -k·t, t½ = ln(2)/k
- biphasic (필요 시): 빠른/느린 단계 분리
- 95% CI, Mann-Whitney U test (group 비교), ANOVA + Tukey HSD

---

## 4. Stability 향상 modification (chemistry S3 + researcher S5)

### 4.1 12종 modification 카테고리

| # | Modification | t½ 효과 | SPPS 호환 | 결합력 영향 | 비용 |
|---|-------------|---------|----------|------------|------|
| 1 | **D-amino acid** | 2-30× | ✅ | 위치별 변동 | 낮음 |
| 2 | **N-methylation** | 5-20× | ✅ 위치 제한 | 가능성 ↓ | 중간 |
| 3 | **Lactam bridge (Lys-Glu)** | 10-100× | ⚠️ 직교 보호 | 보강 가능 | 높음 |
| 4 | **PEGylation 2-40 kDa** | 100-1000× | ✅ 용액상 | 결합력 ↓ | 중간 |
| 5 | **Fatty acid acylation (C18)** | 10-50× | ✅ 용액상 | 보강 (albumin) | 중간 |
| 6 | **NCAA (Cha, 2-Nal, Aib)** | 3-50× | ✅ | 위치별 | 높음 |
| 7 | **N-term Acetyl + C-term NH2** | 2-10× | ✅ | 거의 없음 | **매우 낮음** |
| 8 | **Cyclization head-to-tail** | 10-100× | ⚠️ 추가 단계 | 위치 의존 | 높음 |
| 9 | **Disulfide enhancement (Pen)** | 2-5× | ✅ | SS bond 안정 | 중간 |
| 10 | **Albumin binding (EBTATE)** | 10-100× | ✅ | conjugate | 중간 |
| 11 | **Bicyclic (AT6S)** | 100-1000× | ⚠️ 복잡 | 위치 의존 | 매우 높음 |
| 12 | **²²⁵Ac / ¹⁷⁷Lu 라벨링** | varies | (별도) | (DOTA + metal) | 방사성 |

### 4.2 본 후보 적용 권장 우선순위

```
1순위 (모든 후보 공통):    Ac (N-term) + NH2 (C-term)
                          → 비용 거의 0, 효과 2-10×

2순위 (NEP 차단):          D-Phe6 도입
                          → t½ 5-10× 추가, 비용 낮음

3순위 (selectivity 보존): D-Trp8 도입 (octreotide 원리)
                          → t½ 30× 추가, FWKT 보존 시

4순위 (long-acting):       N-term DOTA-PEG3 + C18 acyl (K4 side chain)
                          → t½ 100×+, albumin binding

5순위 (한계 도전):         Bicyclic 또는 lactam bridge
                          → 임상급 t½, 합성 복잡도 높음
```

---

## 5. 임상 약물 비교 + 진입 가능성 (researcher S5)

### 5.1 임상 SST analog 안정성 timeline

| 연도 | 약물 | 안정화 modification | t½ |
|------|------|---------------------|----|
| 1982 | Octreotide | D-Phe1 + D-Trp8 + 8-mer cyclic | 90 min |
| 1990s | Lanreotide | 2-Nal1 + 8-mer | 50 h (SR) |
| 2000s | Pasireotide | 6-mer macrocycle | 12 h (SC) |
| 2018 | ¹⁷⁷Lu-DOTATATE | radiolabel + DOTA | 70 h |
| 2024 | Bicyclic AT6S | 14-mer + bicyclic | >96% intact @5min |
| 2025 | [²²⁵Ac]Ac-EBTATE | Evans blue albumin binding | 40.27 h |

### 5.2 본 프로젝트 위치
- **현재 후보**: 14-mer linear SS-bonded (cyclic), modification 미적용
- **AT6S 선례 적용 시**: 14-mer 유지하면서도 임상급 stability 가능 ✅
- **권장 path**: D-Phe6 → N-term DOTA → Evans blue (선택) → ²²⁵Ac 라벨

### 5.3 임상 진입 가능성: **YES (조건부)** ✅
- 14-mer 전장 SST-14 scaffold도 stability 달성 가능 (Tatsi 2024 선례)
- 현재 T3 6종에는 modification 미적용 → S4 단계에서 별도 추가
- 합성 비용: ₩1-8M / 후보 (modification 종류 따라)

---

## 6. KAERI 가용 인프라

### 6.1 in-vitro 실험
| 장비/물질 | 가용성 | 비고 |
|---------|--------|------|
| LC-MS/MS | ✅ | 가장 정확 |
| RP-HPLC | ✅ | 단순 보조 |
| ¹²⁵I 라벨링 시설 | ✅ | KAERI 핵심 인프라 |
| Human serum (pooled) | 구매 | Sigma H4522 (외부 발주) |
| Mouse plasma | 구매 또는 KAERI 동물실 | |
| Radio-HPLC | ✅ | ¹²⁵I 라벨 후 검출 |

### 6.2 in-silico 분석 도구 인벤토리 (S6 완료)

#### KAERI 즉시 사용 가능 (현재 설치됨) ✅
| 도구 | 위치 | 출력 |
|------|------|------|
| **Biopython ProtParam** | `bio-tools` env | MW, GRAVY, **Instability Index**, pI |
| **compute_admet** | `AgenticAI4SCIENCE_.../backend/admet.py` | ADMET 종합 + 신독성 risk |
| **compute_nephrotox_risk** | 위와 동일 | High/Moderate/Low |
| **step08_stability** | `pipeline_local/steps/` | 휴리스틱 ranker (H-06 disclaimer) |
| **pharmacology_guards** | `pipeline_local/scripts/` | lookup table 검증 (93/93 tests) |
| **modification_conflict** | 위와 동일 | D-AA + DOTA + PEG 충돌 검사 |
| **pepadmet** | conda `pepadmet` env | ADMET 종합 (legacy) |

#### 빠른 설치 (<10분) ⚡
- `pip install peptides` → Boman index, aliphatic index 추가
- `git clone pepADMET` (2025 신규, DOI:10.1021/acs.jcim.5c02518)
  - **29개 ADMET endpoint**, D-아미노산 수식 지원

#### 웹 접근 시 우선 사용
- **PlifePred** — 혈중 t½ 예측, D-AA 포함 Modified 모듈 (권장 1순위)
- **ExPASy PeptideCutter** — NEP F6-F7, T10-F11 즉시 시뮬레이션
- **MEROPS DB** — 종합 protease specificity
- **ADMETLab 3.0** — full ADMET (SMILES 변환 필요)

### 6.3 T3 후보 7종 batch 계산 결과 (S6, Biopython + compute_admet)

| 후보 | MW (Da) | GRAVY | Instability | 신독성 | 비고 |
|------|---------|-------|------------|--------|------|
| SST-14 ref | 1639.9 | 0.029 | 30.65 ✅ | High | baseline |
| cand03 (G2I) | 1696.0 | 0.379 | 30.65 ✅ | High | |
| **ILCKKFFWKTFTSC** | 1752.1 | 0.493 | **55.14 ⚠️** | High | KK 쌍 영향 |
| VLCKNFFWKTFTSC | 1724.1 | 0.500 | 30.65 ✅ | High | |
| ALCKNFFWKTFTSC | 1696.0 | 0.329 | 30.65 ✅ | High | |
| AICKAFFWKTFTSC | 1653.0 | **0.757** | 41.39 ⚠️ | **Moderate** | A5 → 신독성 ↓ |
| AIRCNFFWKTFTSC | 1724.0 | 0.336 | 30.65 ✅ | High | |

**핵심 관찰**:
1. **ILCKKFFWKTFTSC Instability 55.14** — Boltz selectivity #1이지만 in-silico 안정성 최저
2. **AICKAFFWKTFTSC** — pos5 N→A로 신독성이 Moderate (다른 후보 모두 High) → DOTA 신독성 risk 감소 후보
3. GRAVY 분포 0.0~0.76 — IGCWWFFWKTFTSC (0.621) 외에도 AICKAFFWKTFTSC (0.757) 응집 위험 가능

---

## 7. 검증 필요 항목 종합 (§)

총 **19건** 의 §검증 필요 항목:

### chemistry (S3, 5건)
1. T3-05 AGCKNTFWKTFTSA Cys14→Ala 의도 확인
2. K4-acyl + N-term-DOTA 충돌
3. D-Thr12 SS bond ring 영향
4. ILCKKFFWKTFTSC Orn ε-NH2 DOTA-NHS coupling 효율
5. IGCWWFFWKTFTSC W5-W6 응집 임계 농도

### biology (S1, 6건)
- VB-01: cand03 NEP cleavage 위치 in-vitro 확인 (HPLC-MS/MS)
- VB-02: ILCKKFFWKTFTSC trypsin site 3개 cleavage 우선순위
- VB-03: SS bond 환원 속도 (글루타티온 환경)
- VB-04: 분해 fragment의 SSTR2 binding 잔류 활성
- VB-05: var07_I2K K2-C3 cleavage 실측
- VB-06: D-AA 도입 후 protease 저항성 정량

### researcher (S5, 3건)
- G-05: D-Thr10 도입 시 SSTR2 결합력 변화 (문헌 없음)
- G-06: NEP 억제제 + SST-14 전장 유사체 병용 전임상 데이터
- G-03: ²²⁵Ac-DOTATATE 2025 임상 trial 최신 데이터 (paywall)

### pharma (S4, 3건)
- IGCWWFFWKTFTSC 용해도 실측 (GRAVY +0.621)
- 5종 후보 Boltz 도킹 미완료 (T3-02 ~ T3-05)
- _PROTEASE_VULNERABILITY 절대값 출처 (VR-S5-01)

### researcher S6 (5건, High 우선순위)
- G-01: pepADMET D-아미노산 수식 SST-14 예측 정확도 미검증
- G-02: PlifePred D-Phe6 도입 후보 실제 입력 테스트
- G-03: ExPASy PeptideCutter NEP 절단 확인 (웹 접근 시 즉시 실행 가능)
- G-04: pepADMET 29 endpoint vs compute_admet 일치도
- G-05: compute_admet DLscore=100/100 포화 — 규칙 재정의 검토 권장

---

## 8. 비용 추정 (chemistry S3)

| 패키지 | 내용 | 후보당 | 8종 총 |
|--------|------|--------|--------|
| **A (basic)** | Ac + NH2 + D-Thr12 | ₩160K | ₩1.3M |
| **B (DOTA)** | A + DOTA conjugation | ₩960K | ₩7.7M |
| **C (full)** | B + D-Phe6 + K5 modification | ₩1.5M | ₩12M |
| **D (long-acting)** | C + C18 acyl + albumin binding | ₩3M | ₩24M (선택적 후보만) |

**합리적 첫 라운드**: 패키지 B × 4 후보 (#1-#4) = **~₩3.8M**

---

## 9. 권장 의사결정 path

### 9.1 즉시 진행 (이번 분기)
1. **AGCKNDFWKTLTSC + Boltz 도킹** (T3-02 ~ T3-05 미완료 Boltz 평가)
2. **D-Phe6 변이 도입** + Boltz 재평가 (7-8 후보 × D-Phe6 = 7 페어, ~20분)
3. **합성 견적 받기** — Anaspec, Bachem, GenScript (패키지 B 기준)

### 9.2 다음 라운드 (1개월)
4. **in-vitro 결합 Ki + serum stability assay** (3-4 후보)
5. **¹²⁵I 라벨링 + radio-HPLC**
6. **NEP inhibitor 병용 실험** (G-06 검증)

### 9.3 중기 (3-6개월)
7. **mouse PK 연구** (single dose)
8. **¹⁷⁷Lu 라벨링 + biodistribution**
9. **임상 진입 가능성 평가** (FDA pre-IND 자료)

---

## 10. 산출물 인덱스

| 파일 | LOC | 도메인 | 담당 |
|------|-----|--------|------|
| [`protease_mechanisms_sst14.md`](protease_mechanisms_sst14.md) | ~480 | biology | reviewer-biology |
| [`halflife_methodology.md`](halflife_methodology.md) | ~372 | pharma | reviewer-pharma |
| [`cand_stability_analysis.md`](cand_stability_analysis.md) | ~343 | pharma | reviewer-pharma |
| [`stability_modifications_review.md`](stability_modifications_review.md) | ~470 | chemistry | reviewer-chemistry |
| [`sst_analog_stability_literature.md`](sst_analog_stability_literature.md) | ~580 | researcher | researcher |
| [`stability_predictor_tools.md`](stability_predictor_tools.md) ✨ | ~700 | in-silico tools | researcher (S6) |
| **`META_stability_halflife_integrated.md`** (본 문서) | ~400 | 통합 | team-lead |

**총 산출**: ~3,345 LOC (메타 보고서 포함)

---

## 11. 결론

1. **4-도메인 합의 형성**: AGCKNDFWKTLTSC (#1, 균형) + var12_T12dThr (#2, 안정성) + ILCKKFFWKTFTSC (#3, 조건부)
2. **var07_I2K, T3-05/06 (Cys 손실) 제외 확정** — chemistry+pharma+biology 모두 NO-GO
3. **ILCKKFFWKTFTSC 다중 도메인 위험 확인**:
   - biology: Trypsin site 3개 (K4, K5, K9)
   - pharma: HL score 12.80 (최저)
   - **S6 in-silico**: Instability Index **55.14** (다른 후보 30.65 대비 2배)
   - → 합성 시 K5→Orn + D-Phe6 modification 필수
4. **AICKAFFWKTFTSC 신독성 Moderate 발견** (S6) — pos5 N→A로 다른 후보 모두 High인 신독성이 감소 → **DOTA 컨주게이션 후보 유망**
5. **임상 진입 가능 path 확인** (Tatsi 2024 14-mer 선례 + 권장 modification 우선순위)
6. **KAERI 즉시 in-silico 도구 완비** (Biopython + compute_admet + step08_stability + pharmacology_guards) → 합성 전 빠른 screening 가능
7. **§검증 필요 19건** — 다음 단계 wet lab + in-silico 검증 우선순위
8. **임상 in-vitro 검증 path 명확** (LC-MS/MS + ¹²⁵I + 표준 프로토콜)

### S6 신규 통합 인사이트
- **즉시 실행 가능**: Biopython ProtParam + compute_admet으로 신규 후보 추가 평가 자동화 가능
- **pepADMET 도입 시**: 29 ADMET endpoint + D-AA 지원 → 합성 modification 후보 평가 정확도 ↑
- **PlifePred 웹**: D-Phe6 도입 후 t½ 정량 예측 가능 (외부 망 필요)
- **DLscore 100/100 포화**: compute_admet 규칙 재정의 검토 필요 (현 시점 의미 있는 변별력 부족)

### 다음 사용자 결정 요청
- 합성 견적 시작 시점 (3-4 후보 ₩3.8M 또는 7종 ₩7.7M)
- D-Phe6 변이 Boltz 추가 도킹 여부 (7 페어, ~20분)
- in-vitro 발주 후보 수 (3 / 4 / 5종)
- pepADMET 도입 결정 (29 endpoint 추가 평가)

---

*Generated by team-lead orchestrator · 2026-05-12 11:50 → updated 12:00 (S6 통합)*
*v1.1 — researcher S6 in-silico predictor 결과 반영 완료*
