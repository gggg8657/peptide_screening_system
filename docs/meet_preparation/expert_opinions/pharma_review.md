# 약리학 전문가 견해 — 향후 방향 및 타개 방법
**작성**: reviewer-pharma | **일자**: 2026-06-01 | **상태**: 초안

> **사전 검증**: `pharmacology_guards.py` 회귀 테스트 **76/76 PASS** (2026-06-01 실행)  
> **부호 규약**: Boman Index 양수 = 친수성/단백질 결합 잠재력 高, Kyte-Doolittle 양수 = 소수성 — `check_sign_convention` PASS  
> **인용 원칙**: 아래 모든 인용은 `references/references.md` 검증 통과 항목(R01~R19)만 사용

---

## 1. 총평

본 프로젝트는 SST-14 유사체 SSTR2 선택적 방사성의약품 후보 스크리닝을 목표로 하며, 약리학 축에서 가장 중요한 성과는 **PRST-001~004 4종 후보 도출 및 합성 의뢰서 완성**(PR #63)이다. 그러나 이 후보들의 약리학적 유효성 판단에 필수적인 두 기반 — 변형 펩타이드 반감기 예측(A-02 D-AA HIGH-BLOCKER)과 DOTA 라벨링 후 ADMET 평가(A-03 Layer 3 STUB) — 이 모두 미완 상태이므로, **현 Tier S 판정은 도킹 점수(ΔG) 및 L-AA 기반 ADMET 휴리스틱에 편중된 잠정 순위**임을 명시해야 한다. 6월 회의의 핵심 결정은 두 블로커의 해소 경로 합의와 wet-lab 착수 시점 확정이다.

---

## 2. Action Item별 견해

### A-02 — 혈청 반감기 도구

**진행 평가**: Layer 1(PlifePred·HLP 기반)/Layer 2(PEPlife2-GAT) wrapper가 단위 테스트를 통과하였고, ProtParam(ExPASy) 1차 도구가 통합되어 있다. 그러나 enrichment 경로(`enrich_candidates_from_wrappers`)가 `run_routed_halflife`를 호출하지 않아(PR #117 미머지, audit §1.1 ①) 실제 파이프라인 내에서 반감기 값이 Tier 산정에 반영되지 않는다.

**미진한 부분**:
- **D-AA HIGH-BLOCKER** (신뢰 등급: HEURISTIC/LOW): D-Phe·Thr(ol) 등 비천연 아미노산이 포함된 펩타이드에 대해 신뢰 가능한 반감기 예측 도구가 현재 없다. Layer 2 PEPlife2-GAT의 D-AA 재학습 결과는 R²=0.022(audit 5/27)로 의사결정 불가 수준이다. `pharmacology_guards.py`의 `test_c04_no_external_tool_supports_d_aa_directly` PASS가 이 현실을 확인한다.
- 벤치마크 세트 정확도 측정 미완: SST-14(t½ ~3분, 회의록 §2.2 p.3), Octreotide(t½ ~100분, 회의록 §2.2 p.3) 대비 도구별 R²/Spearman ρ가 산출되지 않았다.
- `[추정]` pepADMET(GitHub: ifyoungnet/pepADMET, DOI: 10.1021/acs.jcim.5c02518 [R06])의 D-AA 처리 가능성은 미검증이다.

**타개 방법 (구체)**:

1. 단기 (1-2주): 벤치마크 세트 5종 이상(SST-14, Octreotide, Lanreotide, RC-160 + 추가 2-4종)에 PlifePred(DOI: 10.1371/journal.pone.0196829 [R02])·HLP(DOI: 10.1186/1471-2105-15-282 [R03])·ProtParam(ExPASy [R01])을 일괄 적용하여 R²/Spearman ρ를 산출하고 회의 자료로 제출한다. 이 벤치마크는 L-AA 범위의 공정한 성능 기준이 되며, PR #117 머지 여부 결정의 근거가 된다.

2. 중기 (4-8주): N-end rule(Bachmair et al. 1986, DOI: 10.1126/science.3018930 [R04])에 기반한 N-말단 잔기 설계 가이드를 합성 의뢰서에 반영하고, MD(RMSD) 2차 검증을 gmx_MMPBSA(DOI: 10.1021/acs.jctc.1c00645 [R10])·OpenMM([R11]) 환경에서 구현한다(서호성 의견, 회의록 §2.2 p.3). `[추정]` D-AA 펩타이드용 WebMetabase를 검토한다(`pharmacology_guards.py` `test_webmetabase_only_d_aa_supporter_in_external_tools` PASS, 신뢰 등급 확인 필요).

3. 장기 (3-6개월): wet-lab RP-HPLC + LC-MS 기반 시간별 혈청 잔존율 측정을 표준화하고(서호성 의견, 회의록 §2.2 p.3), 이 실측 데이터를 입력으로 pepADMET fine-tuning 또는 신규 D-AA 특화 모델의 active learning 사이클을 설계한다.

**약리학적 의미 (생명공학 청중)**: SST-14의 혈청 t½ ~3분(회의록 §2.2)은 임상 투여가 불가능한 수준이다. Octreotide의 D-Phe(N-말단) + Thr(ol)(C-말단) 변형이 t½를 ~100분(약 33배)으로 연장한 것(회의록 §2.2)은, **D-AA 도입이 선택성 외에 약동학에도 결정적임**을 방증한다. 따라서 D-AA 블로커 해소 없이는 PRST 후보의 약리학적 실현 가능성 평가가 불완전하다.

**참조 출처**: [R01] ExPASy ProtParam, [R02] PlifePred DOI 10.1371/journal.pone.0196829, [R03] HLP DOI 10.1186/1471-2105-15-282, [R04] Bachmair 1986 DOI 10.1126/science.3018930, [R10] gmx_MMPBSA DOI 10.1021/acs.jctc.1c00645

---

### A-03 — Fab-ADMET / pepADMET (Layer 3 STUB)

**진행 평가**: pepADMET(GitHub: ifyoungnet/pepADMET [R06]) 로컬 마이그레이션 완료 및 wrapper(`predict_admet_pepadmet.py`) 단위 테스트 PASS, BE `/api/admet/batch` 200 응답 확인. 외부 API HTTP 403 차단 문제는 로컬 모델 의존으로 전환하여 우회하였다.

**미진한 부분**:
- **Layer 3 STUB**: 함수명 `layer3_dota_admet_ai_md_proxy_stub`이 그대로 남아 있어 DOTA 킬레이터 결합 후보의 ADMET 평가가 공백이다. 본 프로젝트 후보가 방사성의약품으로 기능하려면 DOTA 컨쥬게이트 상태의 ADMET가 필수이나, 현재 이 경로에 대한 검증 도구가 없다(`pharmacology_guards.py` `test_c07_dota_no_tool_supports_dota` PASS가 이를 확인).
- pepADMET의 D-AA 및 SS-bond 환형화 후보 처리 가능성이 `[추정]` 상태이다(`test_check_pepadmet_applicability_cyclic_ss_bond_blocked`, `test_check_pepadmet_applicability_d_aa_still_blocked` PASS).
- `[추정]` pepADMET 자체 학습 시 데이터 요구량·GPU 시간·예상 정확도 향상 미산정.

**타개 방법 (구체)**:

1. 단기 (1-2주): Layer 3 STUB에 OOD 경고 발행 최소 구현을 추가하여 DOTA 후보에 명시적 "평가 불가 — wet-lab 필수" 경고를 반환하도록 한다(반영 계획 R-07). 이는 "한계 노출 framework"(서호성 의견)의 원칙에 부합하며 파이프라인이 침묵으로 환각하는 상황을 막는다.

2. 중기 (4-8주): pepADMET의 19개 ADMET 엔드포인트(DOI: 10.1021/acs.jcim.5c02518 [R06]) 중 hemolysis·cytotoxicity·binary_toxicity 3종을 우선 검증한다. D-AA 및 환형 펩타이드 입력 시 도구의 실제 행동(에러 vs 외삽 경고 vs 부분 지원)을 실험으로 확인하여 `[추정]` 항목을 해소한다. ADMETlab 3.0(URL: admetlab3.scbdd.com [R08])의 API는 차단 환경이므로 사용 불가; ADMET-AI(DOI: 10.1093/bioinformatics/btae416 [R07])는 소분자 중심 설계이므로 SST-14 analogue에는 pepADMET이 우선이다.

3. 장기 (3-6개월): DOTA 컨쥬게이트 ADMET 예측을 위한 자체 학습 데이터 수집 — 기존 DOTATATE/DOTATOC/DOTANOC 문헌 데이터(Gervasoni et al. 2023 JCIM PMC10428218 [R17])를 활용하여 DOTA-펩타이드 복합 구조의 ADMET 모델을 개발하거나 외부 도구와 협력한다.

**약리학적 의미 (생명공학 청중)**: ADMET=1.00(binary_toxicity) 값은 절대 독성 판정이 아니라 학습 도메인 밖(OOD) 외삽 가능성을 나타낸다(audit §1.1 ④, 서호성 의견). `pharmacology_guards.py`의 `test_check_pepadmet_applicability_cyclic_ss_bond_blocked` PASS가 시스템이 이 한계를 이미 내장하고 있음을 확인한다. DOTA 킬레이터를 부착한 펩타이드의 안전성 프로파일은 펩타이드 단독 예측으로 추론할 수 없으며, in vitro 세포 독성 assay가 유일한 결정적 증거이다.

**참조 출처**: [R06] pepADMET DOI 10.1021/acs.jcim.5c02518, [R07] ADMET-AI DOI 10.1093/bioinformatics/btae416, [R08] ADMETlab 3.0 admetlab3.scbdd.com, [R17] Gervasoni 2023 JCIM PMC10428218

---

### A-04 — Top-K 복합 스코어링 (반감기·셀렉티비티·ADMET 통합)

**진행 평가**: Tier S/A/B/FAIL 복합 스코어링 시스템이 PR #62로 머지되어 PRST-001~004 도출에 사용되었다. ΔG, 셀렉티비티(ΔΔG), Radiolysis score, ADMET, 반감기를 종합하는 framework 구조는 방사성의약품 후보 선정의 표준적 다목적 기준에 부합한다.

**미진한 부분**:
- 반감기 입력 격차: enrichment 경로가 `run_routed_halflife`를 호출하지 않아(audit §1.1 ①) 현재 Tier 산정에 반감기가 실질적으로 미반영이다. 즉 복합 스코어링이라고 하지만 약동학 축이 빠진 상태이다.
- K-1/K-2 selectivity 결함(`_build_pdb_index` 정렬 오류)으로 모든 PRST 후보의 off-target ΔG가 동일한 구조물에서 산출되었다. 이는 셀렉티비티 항목의 입력 신뢰성을 훼손한다.
- Layer 3 STUB으로 DOTA 후보 종합 점수의 ADMET 항목이 공백이다.
- `[추정]` Pareto front 최적화(pymoo NSGA-II, DOI 기반 IEEE Access 2020 [R09]) 도입 효과 미검증.

**타개 방법 (구체)**:

1. 단기 (1-2주): R-04(K-1/K-2 selectivity 정정) 완료 후 즉시 R-08(PRST-001~004 ranking 재검증)을 실행하여 selectivity 보정이 Tier 순위에 미치는 영향을 정량화한다. PR #117(ADMET divergence guard) 머지 여부를 R² 재학습 결과에 근거하여 6월 회의에서 결정한다.

2. 중기 (4-8주): enrichment 경로 정합(R-06, Option A vs B) 합의 후 반감기 값이 실제로 Tier 산정에 반영되도록 코드를 수정한다. 이 시점에서 벤치마크 R²(R-12) 결과를 반감기 가중치 설정의 근거로 활용한다.

3. 장기 (3-6개월): `[추정]` pymoo NSGA-II([R09])를 활용한 Pareto front 최적화를 도입하여 반감기·셀렉티비티·ADMET 세 축의 Pareto 최적 후보를 시각화한다. 이는 단일 가중 합산의 가중치 의존성 문제를 해소하는 정통 다목적 최적화 접근이다.

**약리학적 의미 (생명공학 청중)**: ΔG 단일 지표 의존에서 탈피하는 것은 방사성의약품 개발의 표준 요건이다 — Lutathera(lutetium Lu-177 dotatate) FDA 라벨(NDA 208700, DailyMed [R19])에서 확인되듯, 임상 방사성의약품은 결합 친화도 외에 안정성·선택성·독성을 모두 충족해야 한다. 현재 Tier 산정의 약동학 공백은 후보 재순위화를 일으킬 가능성이 있으므로 6월 회의 전 정정이 필요하다.

**참조 출처**: [R09] pymoo DOI arXiv:2002.04504, [R19] Lutathera FDA DailyMed NDA 208700

---

### A-09 — PRST-001~004 (ADMET=1.00 OOD)

**진행 평가**: PRST-001(AGCKNIIWKTITSC, WSS=1.000, ΔG=-105.5 REU)을 포함한 4종 후보 도출 및 합성 의뢰서 작성이 PR #63으로 완료되었다. 본 프로젝트의 in silico 단계가 처음으로 wet-lab 착수 직전까지 도달한 성과이다.

**미진한 부분**:
- **ADMET=1.00 OOD 위험**: PRST-001~004의 binary_toxicity=1.00은 학습 도메인 외 OOD 외삽 신호일 가능성이 높다(audit §1.1 ④). `pharmacology_guards.py`의 `test_check_pepadmet_applicability_cyclic_ss_bond_blocked` PASS가 SS-bond 환형 펩타이드(SST-14 아날로그 공통 구조)에 대한 pepADMET 적용이 차단됨을 확인한다. 따라서 이 수치를 "독성 있음"으로 해석하면 안 된다.
- K-1/K-2 selectivity 결함으로 PRST 후보들의 off-target 비교가 신뢰할 수 없는 상태이다 — SSTR1/3/4/5 선택성 수치가 재검증 대상이다(반영 계획 R-08).
- wet-lab 미착수: 합성 ETA 미확정, binding affinity(Ki) 측정 프로토콜 미설계.

**타개 방법 (구체)**:

1. 단기 (1-2주): PRST-001~004 발표 자료에 ADMET=1.00의 OOD 해석 경고를 명시적으로 포함하고, K-1/K-2 정정 후 selectivity ranking 재검증 결과를 회의 자료에 반영한다. 합성 ETA(KAERI 자체 vs 외부 벤더)를 확정하고 binding affinity assay 설계를 착수한다.

2. 중기 (4-8주): wet-lab 착수 후 in vitro 실측값 — Ki(binding affinity), 세포 독성(hemolysis, cytotoxicity), serum stability — 을 확보하여 in silico Tier 순위의 검증 또는 수정 사이클을 시작한다. Radiolysis Quencher DOE(서호성 의견, Lutathera 겐티스산 0.63 mg/mL + 아스코르브산 2.8 mg/mL 제형 [R19])와 연동하여 표지(Lu-177) 후 radiolysis assay를 병행한다.

3. 장기 (3-6개월): wet-lab Ki 결과를 in silico ΔG와 비교하여 두 지표의 상관관계를 정량화하고(Gervasoni et al. 2023 JCIM [R17], Gervasoni et al. 2024 CSBJ [R18] 비교 framework 참조), 파이프라인의 도킹 스코어 신뢰도를 보정한다. SSTR2 선택성 검증 후 PRST-005 이상의 추가 후보 탐색 사이클을 재개한다.

**약리학적 의미 (생명공학 청중)**: ADMET 모델의 OOD 신호는 "독성 확인"이 아니라 "모델이 이 구조를 평가할 수 없다"는 뜻이다. SS-bond 환형 펩타이드 + 비천연 아미노산 조합은 pepADMET의 학습 도메인과 거리가 있고, 이는 방사성의약품 개발에서 in silico ADMET 도구의 구조적 한계이다. PRST 후보의 실질적 약리학적 판단은 **in vitro assay로만 가능**하다는 것이 약리학 도메인의 명확한 결론이다.

**참조 출처**: [R17] Gervasoni 2023 JCIM PMC10428218, [R18] Gervasoni 2024 CSBJ PMC11630666, [R19] Lutathera FDA DailyMed NDA 208700, [R06] pepADMET DOI 10.1021/acs.jcim.5c02518

---

## 3. 도메인 간 권고 (약리학 → 다른 전문가 의견 요청 사항)

- **합성 (reviewer-chemistry 권고)**: D-AA 치환 위치 선택(N-말단 D-Phe, D-Trp 등)이 SSTR2 결합 포켓에서의 입체화학 적합성과 합성 수율에 모두 영향을 미친다. Octreotide의 D-Phe/Thr(ol) 전략이 반감기를 33배 향상시킨 메커니즘을 근거로, PRST 후보에 적용 가능한 D-AA 치환 전략과 예상 합성 난이도를 reviewer-chemistry에 의뢰한다. PEG화·지방산 아실화의 PK 효과([다른 전문가 의견 권장 — reviewer-chemistry])도 함께 검토가 필요하다.

- **구조 (reviewer-biology 권고)**: SSTR2 결합 포켓에서 W8 변형이 SSTR4 선택성을 향상시킨다는 Gervasoni et al. 2024 CSBJ([R18]) 결과를 PRST 후보 설계에 반영할 때, D-AA/N-methyl 변형과 구조적 충돌 여부를 reviewer-biology와 교차 검토한다. K-1/K-2 selectivity 정정 후 재산정된 SSTR2 vs SSTR1/3/4/5 ΔΔG 해석에서 생물활성 관련 구조 근거를 요청한다.

- **수학·최적화 (reviewer-math 권고)**: pymoo NSGA-II([R09]) 기반 Pareto front 최적화 도입 시 목적함수 정의(ΔG 최소화, 반감기 최대화, ADMET 독성 최소화)의 수학적 구성 및 수렴 조건 설정을 reviewer-math에 의뢰한다. 현재 PEPlife2-GAT R²=0.022의 의미(신호 없음 vs 과적합 vs 데이터 부족)에 대한 통계적 판단도 요청한다.

---

## 4. 6월 회의 핵심 의사결정 권고 (약리학 관점)

1. **PR #117 머지 vs. close 결정**: Layer 2 PEPlife2-GAT R²=0.022 재학습 결과를 근거로, D-AA HIGH-BLOCKER 해소 경로(MD 2차 구현 vs. 외부 도구 도입 vs. 데이터 추가 수집)를 합의하고 PR 처리 방향을 확정한다. 이 결정이 A-02·A-04·A-09 약동학 축 전체의 선행 조건이다.

2. **enrichment 경로 정합 Option A/B 결정**: `enrich_candidates_from_wrappers`가 `run_routed_halflife`를 호출하도록 코드를 수정(Option A)할 것인지, 현재 코드 상태를 기준으로 narrative를 재정의(Option B)할 것인지 결정한다. 약리학 관점에서는 반감기가 실제로 Tier 산정에 반영되어야(Option A) 복합 스코어링의 의미가 충족된다.

3. **PRST-001~004 wet-lab 착수 시점 및 assay 우선순위 확정**: 합성 ETA·벤더·binding affinity Ki 측정 프로토콜을 확정하고, ADMET=1.00 OOD 해석을 발표 자료 및 합성 의뢰서에 명시한다. in vitro serum stability assay(서호성 의견, 회의록 §2.2 p.3)를 wet-lab 착수 단계에 포함시킨다.

---

## 5. 한 줄 결론

> PRST-001~004 도출은 이 프로젝트의 첫 in silico→wet-lab 연결이라는 의미가 있으나, 반감기(D-AA 블로커)와 DOTA ADMET(Layer 3 STUB)이라는 두 약리학 핵심 축이 모두 미완인 상태에서 Tier S 판정을 최종 후보 선정의 근거로 쓰려면, **wet-lab assay(Ki·serum stability·cytotoxicity)가 반드시 병행되어야 한다**.
