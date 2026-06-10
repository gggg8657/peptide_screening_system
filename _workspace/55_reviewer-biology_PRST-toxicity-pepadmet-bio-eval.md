# 생물학 리뷰: PRST-001~004 pepADMET 독성 예측 생물학적 타당성 평가

**작성**: reviewer-biology  
**날짜**: 2026-05-20  
**의뢰**: orchestrator (team-lead), Task #10  
**선행 자료**: `_workspace/pepadmet_local/PRST-candidates_revalidation_2026-05-20.md`  
**검토 대상**: pepADMET `toxicity_type = hemostasis`, `neurotoxicity_type = Na_inhibitor` (binary_toxicity=1.0, 신뢰도 100%)

---

## 1. 구조 타당성 (검토 대상 서열)

pepADMET 입력 서열 4건 및 SST-14 native 비교:

| 후보 | 서열 (14aa) | Cys3-Cys14 SS bond | 실제 변이 (vs SST-14) |
|---|---|---|---|
| SST-14 (native) | AGCKNFFWKTFTSC | ✓ | — |
| PRST-001 | AGCKNI**I**WK**T**I**T**SC | ✓ | F6I, **F7I**, F11I |
| PRST-002 | AGCKNF**I**WK**T**I**T**SC | ✓ | **F7I**, F11I |
| PRST-003 | AGCR**N**F**I**WK**T**I**T**SC | ✓ | **K4R**, F7I, F11I |
| PRST-004 | A**I**CKNF**I**WK**T**I**T**SC | ✓ | **G2I**, F7I, F11I |

> **주석**: 의뢰서 기재 변이 목록(F6I/F11I, K4R 단독 등)은 실제 서열과 불일치.  
> 정확한 변이는 위 표 기준 (자동 diff 결과) 이 보고서에서 사용.

### 물리화학적 특성 (계산값)

| 후보 | GRAVY | Net Charge (pH 7.4) | %Hydrophobic | 이차구조 기대 |
|---|---:|---:|---:|---|
| SST-14 | +0.03 | +2 | 57.1% | β-turn / cyclic loop |
| PRST-001 | +0.39 | +2 | 57.1% | β-turn / cyclic loop |
| PRST-002 | +0.27 | +2 | 57.1% | β-turn / cyclic loop |
| PRST-003 | +0.23 | +2 | 57.1% | β-turn / cyclic loop |
| PRST-004 | **+0.62** | +2 | 57.1% | β-turn / cyclic loop |

> GRAVY 계산: Kyte-Doolittle scale. Phe(2.8) → Ile(4.5) 치환으로 소수성 소폭 증가.  
> PRST-004 (G2I): Gly(-0.4) → Ile(4.5) N-말단 치환으로 가장 높은 GRAVY.

---

## 2. SS Bond 토폴로지

모든 PRST-001~004는 **Cys3-Cys14 SS bond** (SST-14 native와 동일) 보유.  
변이 잔기 중 Cys는 포함되지 않으므로 SS 토폴로지 변화 없음.

- PRST-001/002/003/004 SMILES에서 `CSSC` 서브구조 확인 (재검증 파일 §1)
- PRST-004의 경우 N-말단 G2→I 치환이 링 구조 N-말단 유연성에 영향 가능하나, SS bond 자체는 유지

---

## 3. pepADMET 예측 항목별 생물학적 타당성 분석

### 3-A. `toxicity_type = hemostasis` (confidence 100%)

#### 3-A-1. SST-14 native의 알려진 hemostasis 활성

문헌에서 SST-14의 혈소판 기능 영향은 **실재하지만 방향이 다르다**:

- **친-혈전(pro-hemostatic) 효과**: SST-14는 collagen, ristocetin, arachidonic acid에 의한 혈소판 응집을 **강화(potentiate)**한다 (PMID 598562; PMID 6110570). 이는 출혈 억제 맥락에서 therapeutic 효과로 사용됨.
- **항-혈전(anti-coagulant) 효과 없음**: 위 문헌들에서 SST-14가 혈소판 응집을 억제하거나 항응고 효과를 나타낸다는 보고 없음.
- **임상적 의미**: 위장관 출혈 치료에 Somatostatin을 사용하는 근거 중 하나가 platelet aggregation 촉진임 (PMID 10567784). 이는 safety concern이 아니라 **치료 기전**임.

#### 3-A-2. 직접 용혈(hemolysis) 가능성 평가

| 기준 | SST-14 기준값 | 고위험 hemolytic peptide 기준 | 평가 |
|---|---|---|---|
| Net charge | +2 | ≥+4 (potent), ≥+6 (highly hemolytic) | ⚠️ 경계 수준 |
| GRAVY | +0.03~+0.62 | >+0.8 | ✅ 안전 범위 |
| 이차구조 | β-turn loop (cyclic SS) | amphipathic α-helix | ✅ 비해당 |
| Amphipathic helix | 없음 (SS-constrained loop) | 존재 필수 | ✅ 구조적 비해당 |
| 막 삽입 에너지 | SS 고리: 제한적 | 선형→나선 전환으로 막 삽입 | ✅ 불리 |

> 참고 문헌 (Jiang 2008, PMID 18098173): α-helical cationic AMP에서 net charge +8→+9 변화만으로도 용혈활성 32배 증가. SST-14 계열 (+2)은 이 threshold 훨씬 하회.  
> 참고 문헌 (PMID 10604598): cyclic disulfide 도입이 일부 AMPs의 용혈활성을 증가시키나, 대상 펩타이드는 amphipathic α-helical 전구체임 (SST-14의 β-turn 구조와 다름).

#### 3-A-3. SST 임상 유사체의 혈액학적 이상반응

- **Octreotide, Lanreotide**: 주요 부작용은 GI 증상, 담석증, 고혈당. 용혈 관련 이상반응 임상 보고 없음 (LiverTox NBK548368).
- **Pasireotide**: 빈혈 14-26% 보고되나 이는 종양 관련 빈혈(철결핍, 적혈구 생성 억제)로 용혈성 빈혈과 구별. 직접 용혈 사례 없음.
- **방사성 표지 SST 유사체 ([161Tb]/[177Lu]-SSTR 작용제·길항제)**: 전임상에서 적혈구 수 6-12% 감소 관찰됐으나 이는 골수 억제에 기인, 직접 적혈구 막 용해 아님 (PMC11527941).

#### 3-A-4. pepADMET "hemostasis" 분류의 타당성 해석

**핵심 문제**: pepADMET의 "hemostasis" 독성 유형은 혈전/항응고/용혈 관련 peptide 훈련 데이터를 포함한 분류기임. SST-14가 platelet aggregation을 강화한다는 특성이 모델의 "hemostasis" 토큰/패턴을 활성화할 수 있음.

- **진양성 가능성 (True Positive)**: SST-14는 혈소판 응집에 실제로 영향 → 모델이 이 특성을 포착한 것일 수 있음
- **과대 해석 위험 (Overestimation)**: SST-14의 pro-hemostatic 효과는 임상에서 치료 목적으로 사용되며, pepADMET가 이를 "독성"으로 분류하는 것은 기능적으로는 맞지만 독성학적으로는 오해의 소지
- **False Positive 가능성**: 모델이 cyclic SS-bond + 양이온 잔기 패턴을 hemostasis 독성 peptide (예: anticoagulant venom peptide, hirudin 유사체)와 혼동 가능

**생물학적 타당성 등급**: **MED** — hemostasis effect는 실재하나 방향(pro-hemostatic)과 임상 위험성이 pepADMET 예측("toxic")과 불일치.

---

### 3-B. `neurotoxicity_type = Na_inhibitor` (confidence 100%)

#### 3-B-1. Na 채널 차단 peptide의 구조적 요건

알려진 Na 채널 직접 차단제 (µ-Conotoxin, scorpion Na-toxin) 구조 특성:

| 특성 | µ-Conotoxin GIIIA/PIIIA | SST-14 계열 |
|---|---|---|
| 길이 | 22aa 이상 | 14aa |
| 이황화결합 수 | **3개** (C1-C4, C2-C5, C3-C6) | **1개** (Cys3-Cys14) |
| 구조 모티프 | ICK (inhibitor cystine knot) | β-turn loop |
| 핵심 잔기 | **Arg** (양전하 침투 통로 차단) | Trp8 (소수성) |
| 결합 부위 | Nav 외막 구멍 전정 (pore vestibule) | SSTR2 수용체 결합 포켓 |

> SST-14는 Nav 채널의 pore blocking에 필요한 ICK motif, 3중 SS bond, 충분한 크기(22aa 이상) 모두 결여.

#### 3-B-2. SST-14의 알려진 이온 채널 효과

- **Ca²⁺ 채널 억제**: SST-14는 SSTR을 통한 GPCR 시그널링 → cGMP-dependent protein kinase (cGMP-PK) 활성화 → 뉴런 Ca²⁺ current 억제 (Nature 369:336, PMID 7910377). **간접 조절, 직접 채널 차단 아님**.
- **Na⁺ 채널**: SST-14의 직접 Nav 채널 결합 또는 차단 보고 없음 (PubMed 검색, 2026-05-20 기준).
- **K⁺ 채널**: SSTR2 신호를 통한 K⁺ 채널 활성화 (세포 과분극) — 이것도 **GPCR 간접 효과**.

#### 3-B-3. pepADMET Na_inhibitor 예측 타당성

pepADMET의 Na_inhibitor 분류가 SST-14 계열에서 나타나는 이유 추론:

1. **구조 유사성 오인**: 단일 SS-bond cyclic 14aa peptide → conotoxin 훈련 데이터의 일부 특성 부분 일치
2. **GPCR-mediated 간접 Na 채널 영향**: SST가 Na 항상성에 간접 영향을 미칠 수 있어 일부 신경생리학 논문에서 언급 → 모델 훈련 데이터에 혼입 가능
3. **HC50 이상값**: 보고된 hc50 (-38 to -45)은 물리적으로 불가능한 수치 (log µM 기준이라도 10⁻³⁸ µM은 사실상 0) → 모델이 훈련 분포 외 서열에 extrapolation 중임을 시사하는 아티팩트

**생물학적 타당성 등급**: **LOW** — SST-14 계열 14aa / 1 SS bond / ICK 미보유 펩타이드가 직접 Nav 채널 차단 메커니즘을 갖는다는 구조적 근거 없음. pepADMET 훈련 도메인 외 외삽 가능성 높음.

---

## 4. PRST-001~004 변이 잔기별 hemostasis/Na_inhibitor 영향 평가

| 변이 | 잔기 특성 변화 | hemostasis 활성 변화 | Na_inhibitor 활성 변화 |
|---|---|---|---|
| F6I (PRST-001) | 방향족(π-stack 가능) → 지방족 | 소폭 감소 (소수성 증가지만 Trp8 pharmacophore는 유지) | 변화 없음 (구조 불리) |
| F7I (모든 PRST) | 방향족 → 지방족, 소수성 증가 | 중립 ~ 소폭 감소 | 변화 없음 |
| F11I (모든 PRST) | 방향족 → 지방족 | 중립 ~ 소폭 감소 | 변화 없음 |
| K4R (PRST-003) | Lys → Arg: 양전하 보존, 길이 증가, guanidinium | 중립 (net charge +2 유지) | 이론적 소폭 증가 가능 (Arg이 Na채널 pore와 상호작용할 수 있으나 구조 요건 미충족) |
| G2I (PRST-004) | Gly(유연) → Ile(소수성 강직) | GRAVY 가장 높음(+0.62), 막 친화성 소폭 증가 | 변화 없음 |

> **결론**: 어떤 변이도 hemostasis toxicity 또는 Na_inhibitor 활성을 **임상적으로 의미있는 수준으로 증가**시킬 가능성 없음. Net charge +2 유지, GRAVY < +0.8, β-turn loop 구조 유지.

---

## 5. 종합 생물학적 타당성 판정

### pepADMET 예측 오류 유형 분류

| 예측 항목 | 타당성 | 분류 | 근거 |
|---|---|---|---|
| `binary_toxicity = 1.0` | 부분 타당 | **Partially True** | SST-14의 platelet effect는 실재 / 직접 용혈은 근거 없음 |
| `toxicity_type = hemostasis` | 기능적 타당 + 임상 오해 | **Mechanistically plausible, clinically overestimated** | pro-hemostatic이지 hemostasis-toxic이 아님 |
| `neurotoxicity_type = Na_inhibitor` | 구조적 근거 없음 | **False Positive (High confidence)** | ICK 미보유, 1 SS bond, 14aa로 직접 Nav 차단 불가 |
| `hc50` 음수 (-38 ~ -45) | 물리적 불가능 | **Model artifact / extrapolation artifact** | 훈련 분포 외 서열에 대한 회귀 불안정 신호 |

### 전반 평가

pepADMET의 `binary_toxicity=1.0` 예측은 SST-14 계열 펩타이드에 대해 **중간-높은 위양성(False Positive) 가능성**을 갖는다:

1. **hemostasis**: SST-14의 혈소판 응집 촉진 특성이 모델을 활성화하나, 이는 독성이 아닌 치료 기전임. 직접 용혈 활성은 구조적 분석으로 가능성이 낮음.
2. **Na_inhibitor**: 구조적 요건(ICK, 3SS, Arg pore-blocker)이 모두 결여되어 높은 위양성 가능성.
3. **hc50 이상값**: 모델의 훈련 분포 외 서열에 대한 신뢰도 저하 지표.
4. **4건 모두 100% confidence**: 4개 유사 서열이 모두 동일 분류 + 100% 신뢰도 → 모델이 특정 구조 특성(cyclic SS + cationic)에 일률적으로 반응하는 패턴으로 해석 가능.

---

## 6. 권고: In Vitro Assay 우선순위

### Priority 1 — 직접 용혈 측정 (가장 결정적)

**Hemolysis assay (RBC lysis, HC50 직접 측정)**

- **방법**: Human RBC 2% in HEPES buffer (150 mM NaCl, 10 mM HEPES, pH 7.4), 1h/37°C
- **농도**: 1, 5, 10, 50, 100, 500, 1000 µM (로그 스케일)
- **대조군**: Triton X-100 (100% lysis), PBS (0%), **SST-14 native 포함 필수**
  - SST-14가 HC50 >100 µM이면 PRST 계열도 동급으로 안전할 가능성 높음
- **판정 기준**: HC50 >100 µM → acceptable; HC50 <10 µM → rejection
- **예상 비용**: ~500-800 USD/후보 (CRO 위탁 기준); SST-14 포함 5개 → ~3,000 USD
- **예상 기간**: 2-3주
- **결정력**: ★★★★★ (pepADMET hemostasis 플래그 직접 해소)

### Priority 2 — 혈소판 응집 측정 (기전 확인)

**Platelet aggregation assay (turbidimetry)**

- **방법**: Platelet-rich plasma (PRP) + 펩타이드 (10, 100 µM) + agonist (collagen 1-5 µg/mL, ADP 5 µM)
- **측정**: 최대 응집율 (%) vs. 펩타이드 단독 (spontaneous aggregation 여부)
- **목적**: SST-14 native와 PRST의 platelet aggregation 강화 비교
- **예상 비용**: ~1,000-2,000 USD/후보 세트
- **예상 기간**: 3-4주
- **결정력**: ★★★☆☆ (SST-14의 platelet effect는 이미 문헌으로 알려진 특성이므로 추가 정보 제공)

### Priority 3 — Na 채널 차단 측정 (낮은 우선순위)

**Nav panel screening (patch clamp 또는 FLIPR assay)**

- **방법**: Nav1.1-Nav1.8 발현 CHO/HEK 세포, voltage-clamp 또는 ion flux assay
- **농도**: 1, 10, 100 µM
- **목적**: Na_inhibitor 예측의 직접 위양성 여부 확인
- **예상 비용**: ~3,000-5,000 USD/후보 (Eurofins, Evotec CRO)
- **예상 기간**: 6-8주
- **결정력**: ★★☆☆☆ (구조적으로 위양성 가능성이 이미 높음 → 자원 효율 낮음)
- **권고**: Priority 1 결과 후 결정. Priority 1에서 HC50 >100 µM이면 Na 채널 측정 Skip 검토 가능.

### 비용/시간 요약

| Assay | 비용 (USD) | 기간 | 우선순위 |
|---|---:|---:|---|
| Hemolysis (5건 + SST-14 대조) | ~3,000 | 2-3주 | **P1 — 필수** |
| Platelet aggregation | ~5,000 | 3-4주 | P2 — 권고 |
| Nav patch clamp | ~15,000-20,000 | 6-8주 | P3 — P1 이후 결정 |

---

## 7. §검증 필요

- **VR-BIO-01**: pepADMET hemostasis 훈련 데이터셋 구성 — "hemostasis" 레이블이 pro-hemostatic peptide를 포함하는지 여부. `pepadmet.ddai.tech` 문서 확인 불완전 (접근 timeout).
- **VR-BIO-02**: PRST-001~004의 3D 구조 (AlphaFold2 또는 Boltz 예측값) 기반 amphipathic score 계산. 현재 2D 서열 기반 GRAVY만 계산.
- **VR-BIO-03**: HC50 음수값의 pepADMET 내부 의미 — regression output scale 문서화 필요. reviewer-pharma와 교차 검토 권고.
- **VR-BIO-04**: PRST-003 (K4R) — Arg 잔기의 guanidinium이 Nav 채널 외막과 정전기 상호작용 가능성. 구조 도킹이 있을 경우 확인.

---

## 참고 문헌

1. PMID 10567784 — Somatostatin safety in GI hemorrhage
2. PMID 598562 — Somatostatin effect on platelets in vitro
3. PMID 6110570 — Circulating platelet aggregates in SST-treated diabetics
4. PMID 7910377 — SST-induced Ca²⁺ current inhibition via cGMP-PK (Nature 369:336)
5. PMID 18098173 — Net charge effects on hemolytic activity of cationic peptides
6. PMID 10604598 — Disulfide bond introduction and hemolytic activity
7. PMC4914623 — Thanatin disulfide bond and antimicrobial activity
8. PMC6669574 — µ-Conotoxin PIIIA disulfide bond and Nav activity
9. PMC5128756 — Role of individual disulfide bonds in µ-Conotoxin GIIIA
10. NCBI LiverTox NBK548368 — Lanreotide adverse effects
11. PMC11527941 — [161Tb]/[177Lu]-SST analog tolerability, preclinical
12. Nature Cell Research 2022 — SSTR2 structural insights (ligand recognition)
