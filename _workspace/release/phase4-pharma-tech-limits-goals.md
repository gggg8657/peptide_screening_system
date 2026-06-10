# PRST_N_FM 프로젝트 — 약리·생물 기술 한계 분석 및 향후 목표
**reviewer-pharma 산출물**  
작성일: 2026-05-27  
청자: 생명공학 박사 + 가속기(방사선) 박사 (KAERI 내부, 5/28 회의 자료)  
근거 파일: narrative-v3, 3layer-admet-serum-impact-analysis, phase2-dual-silo-smoke, phase3-ui-ux, be-p0-fix, demo-scenario, 회의록 PDF (MOM-003)

---

## 0. 사전 가드 — pharmacology_guards.py 회귀 테스트 결과

```
pipeline_local/tests/test_pharmacology_guards.py: 76/76 PASS (0.16s)
pipeline_local/tests/ 전체 (test_ood_detection.py 제외): 700 passed, 16 skipped, 2 xfailed
```

ENDPOINT_CONFIDENCE 등록 반감기 키: 11개 (halflife_pepmsnd, pepmsnd_local_halflife_hours 등)  
D-AA 지원 True인 키: halflife_webmetabase_indirect 1개 (간접 protease 절단 지표, 혈청 t½ 아님)  
HEURISTIC_FUNCTION_DISCLAIMERS 등록: 16개 (step08_stability.predict_half_life 포함)  
본 보고서의 모든 반감기 수치는 HEURISTIC 신뢰 등급(LOW) 적용. 절대 t½ 단위로 읽지 않는다.

---

## 1. 도메인 기술 한계 — 약리·생물 관점

아래 항목은 회의록 MOM-003 §2.2, narrative-v3 §3·§5, 3layer 분석, phase2 smoke 보고서에서 사실로 확인된 것만 정리한다. 추측 없음.

### 1-1. D-AA 후보의 혈청 반감기 예측 불가 (A-02 미충족 핵심)

SST-14 계열의 임상 가치는 D-아미노산 치환(D-Phe, D-Trp, D-Nal 등)이 protease 인식을 회피함으로써 serum stability를 높이는 데 있다. 그런데 혈청 반감기 예측 도구 11종 전체에서 D-AA support=True인 항목은 halflife_webmetabase_indirect 1건에 불과하고, 이마저도 protease 절단 지표이지 혈청 t½이 아니다 (ENDPOINT_CONFIDENCE 레지스트리 직접 조회).

정량적 사실:
- pepmsnd_local_halflife_hours: benchmark_test_r2=-0.028 (초기 학습, pepADMET 환경 import 실패 별도 확인)
- 실험 재학습 (PR #112, main 미머지): R²=0.022, Spearman ρ=0.571 — seed/셔플에 따라 부호 흔들림 (narrative-v3 §5.2)
- Octreotide 테스트: D-AA·terminal modification 미반영 시 반감기 4.83배 과대 추정 (narrative-v3 §3 A-02, 회의록 §4 A-02)

결론: 현재 계산 파이프라인으로는 D-AA 후보에 대한 절대 t½ 보고가 불가능하다. 복합 스코어링에서 half-life 항목은 순위 신호(HEURISTIC, LOW 신뢰)로만 사용한다.

### 1-2. ADMET 도구의 OOD 외삽 — D-AA·cyclic·DOTA (A-03 미충족 핵심)

PRST 후보의 구조 특성: 14 aa SST-14 유사 서열, Cys3-Cys14 SS bond cyclic constraint, D-AA 또는 비천연 AA 치환 가능성, DOTA chelator 결합 가능성. 이 조합은 현존 공개 ADMET 도구 학습 분포 밖에 놓인다.

확인된 사실:
- pepADMET REST API: HTTP 403 차단 (narrative-v3 §3 A-03)
- pepADMET local env: `conda run -n pepadmet python -c "import pepadmet"` 실패 (phase2-dual-silo-smoke §6)
- ADMET-AI Layer 3 wrapper: predict_admet_ai_wrapper.py 코드 `recommended_for_decision: False` 항상 고정 (3layer 분석 §2.1)
- PRST-001~004 binary_toxicity=1.00: D-AA·cyclic·DOTA OOD 외삽 가능성 — 절대 독성 판정으로 해석하지 않는다 (narrative-v3 §3 A-03)
- pepADMET 학습 데이터: 공식적으로 환형 펩타이드 포함 여부 미명시, D-AA/비천연 AA 처리 미지원 (회의록 §4 A-03)

ADMET-AI는 Chemprop 기반 소분자 학습 모델이며, 펩타이드에 대한 외삽이 적용된다는 사실이 코드에 경고 문자열로 명시되어 있다 (`ADMET_AI_EXTRAPOLATION_WARNING`).

### 1-3. 3-Layer Ensemble — 코드와 narrative 사이의 격차

PR #85 (3-Layer framework main 머지)는 "모듈·테스트가 저장소에 존재"한다는 의미이지 "표준 후보 enrichment 경로가 이를 호출한다"는 의미가 아니다. 이 격차는 발표에서 명시적으로 노출해야 한다 (narrative-v3 §5.4).

코드 사실 (현재 브랜치 `docs/schrodinger-proposal-d2-20260526` 기준):
- `enrich_candidates_from_wrappers`는 `run_routed_halflife`, `compute_layer1_halflife`, `predict_admet_layer3`를 호출하지 않음
- D-AA 후보는 enrichment 진입 시 전체 스킵: `halflife_confidence_grade=UNAVAILABLE`, `admet_confidence_grade=UNAVAILABLE` (composite_scorer.py:400-408)
- `run_routed_halflife`: Layer 2만 실구현, Layer 1·3은 스텁 메시지 + 경고 반환 (ensemble_router.py:61-76)
- `recommended_for_decision`: ADMET-AI wrapper에서만 `False` 고정, Tier 결정/Hard Cutoff와 자동 결합 없음
- PR #117 (ADMET divergence guard): 현재 브랜치 및 main 양쪽 미포함
- PR #112 (pepMSND Layer 2 재학습): main 머지 커밋 없음, 실험 브랜치 결과만 존재

결론: 5월의 변화는 "코드베이스에 엄격한 실험 모듈이 병렬로 생긴 상태"이다. 합성 패키지 양식은 4월 이후 거의 고정되어 있다. 6월 회의까지 "어느 엔진이 canonical 후보 enrichment 경로인가"를 합의해야 narrative와 코드 격차가 닫힌다.

### 1-4. DiffPepDock — SS bond 처리 불가, NOT_RECOMMENDED

DiffPepDock은 Cys3-Cys14 SS bond 구조적 제약을 안정적으로 유지하지 못한다. RMSD 2.0 Å 이내 재현율 80% 기준(회의록 §4 A-06 KPI)을 충족하지 못했다. 현 단계 파이프라인 도입 NOT_RECOMMENDED (`HEURISTIC_FUNCTION_DISCLAIMERS`에 등록).

### 1-5. Boltz-2 처리량 한계

Phase 2 smoke test 기준: 후보당 40-52초 (log 추정), 55후보 순차 처리에 1500초 초과로 미완 (phase2-dual-silo-smoke §2.3·§7). 라이브 실행에서 step05 진행 중 강제 종료, docking_scores.json 미생성. 이후 단계(Rosetta 등) 산출 없음.

### 1-6. Selectivity 평가의 절대 pose validation 불가

SSTR1/3/4/5 정렬 RMSD: 2.770~3.125 Å (KPI 4Å 이내 충족). 그러나 SST-14:SSTR2 복합체 cryo-EM 구조가 공개되어 있지 않아 absolute pose validation이 불가하다 (narrative-v3 §3 A-05, A-06). 회의록에서 ground truth로 언급된 7T10/7T11은 SSTR2 단독 구조이지 펩타이드 복합체 구조가 아니다.

### 1-7. AA Modification 후보의 Layer 2/3 외삽 위험 증대

A-04 7단계 §5에서 제안된 modification (Met→Nle, Trp→5-F-Trp, Cys-Cys→Thioether bridge 등, 회의록 §4 A-04)은 비천연 AA 또는 구조 변형을 포함한다. 이 후보들은 이미 D-AA·cyclic 조합으로도 OOD인 상황에서, modification이 추가되면 외삽 위험이 더 커진다. Layer 2/3가 이 후보에 대해 유효한 순위 신호를 줄 수 있는지 현재 코드상 보장이 없다 (3layer 분석 §3.5).

### 1-8. Silo A (3-Arm NIM) — NVIDIA NGC API 키 부재로 미검증

pipelines/silo_a Arm1~3 (MolMIM+DiffDock, FlexPepDock, RFdiffusion→ProteinMPNN→ESMFold)는 NGC_CLI_API_KEY 부재로 실행되지 않았다 (phase2-dual-silo-smoke §3.B). Silo A의 실 후보 산출물이 없으므로 Dual Silo 통합 검증도 미완이다.

---

## 2. 한계별 타개 방안

### 한계 1: D-AA 혈청 반감기 예측 도구 부재

**타개 방안 A — 자체 ML 모델 재학습**  
데이터셋: ChEMBL peptide serum stability, PepDB, 사내 wet-lab 측정값 (누적 후)  
아키텍처: Graph Attention Network (PEPlife2-GAT 계열) 또는 Transformer 기반 서열 모델, SMILES 기반 구조 인코딩 포함  
GPU: H100 NVL 단일 (현재 bio-tools env 기준)  
선행 조건: D-AA SMILES 생성 안정화 (현재 composite_scorer.py D-AA 스킵 상태에서는 Layer 2도 실질적 라우팅 불가)  
예상 소요: 데이터 큐레이션 2-3개월, 모델 학습 1개월, 검증 1개월. R² 목표값 합의 필요 (현재 0.022 기준선)  
현실적 한계: 충분한 D-AA 수식 펩타이드 혈청 stability 실측 데이터 없이는 학습 불가. wet-lab 선행 필수.

**타개 방안 B — 상용/공개 도구**  
Schrödinger BioLuminate: D-AA, cyclic peptide, DOTA parameterization 처리 가능성 검토 필요. 문헌 벤치마크에서 parameterization 가능 여부는 실제 적용 시 별도 확인 사항 (narrative-v3 §6.3 단서).  
Desmond: SS bond 유지, RI 표지 후 구조 안정성, solvent exposure를 시간축에서 확인 가능 — serum stability 대리지표로 MD trajectory 사용 가능성 (서호성 박사 A-02 보충 의견: "Modification 진행 후에는 MD로 RMSD 등으로 Stability 예측").  
비용: Schrödinger 라이센스 미확인, 6월 회의 전 검토 승인이 필요한 사항.

**타개 방안 C — wet-lab 병행**  
LC-MS/MS 혈청 안정성 assay (인간 혈장, 37°C, 시간별 HPLC RCP%)  
TPP-B KPI: ≥24h, TPP-C KPI: ≥72h (전략 보고서 기준)  
PRST-001 합성 후 우선 적용. 측정값이 Layer 2 예측 순위와 일치하는지 비교 → 다음 모델 보정 입력.  
assay 단가: 외부 CRO 또는 KAERI RI팀 내부 수행 여부 결정 필요.

**일정**: 단기(1개월) — wet-lab assay 의뢰서 작성 및 발주 결정. 중기(3개월) — 실측 t½ 데이터 수령 및 Layer 2 재학습 재시도. 장기(6개월) — D-AA 포함 학습 모델 R² 목표 달성 또는 Schrödinger Desmond MD trajectory 기반 대리지표 검증.  
**KAERI 비용 영향**: wet-lab assay 외주 비용 (assay 종류·샘플 수에 따라 수백만~수천만 원 범위), GPU는 현재 H100 NVL 활용 가능.

---

### 한계 2: ADMET 도구 OOD 외삽

**타개 방안 A — pepADMET 저자 문의 및 법무 검토**  
pepADMET (Tan et al. 2026 JCIM): GPL-3.0 (GitHub), CC BY-NC-SA 4.0 (웹). KAERI 과제 및 상업화 가능성 기준 법무 검토 필요 (narrative-v3 §7.2).  
저자 문의 내용: D-AA/cyclic/DOTA 포함 학습 데이터 접근 가능성, half-life endpoint 가중치 공개 여부.  
이미 저자 문의 이메일 초안 작성 완료 (narrative-v3 §3 A-03 산출물).

**타개 방안 B — BioLuminate 전처리 + Glide/Desmond 연동**  
BioLuminate: D-AA, chelator 포함 구조를 명시적으로 세팅하고 Glide/Desmond로 넘기는 전처리 축 (narrative-v3 §6.3). Layer 3 OOD 문제를 직접 없애지는 않으나 구조 준비 단계 개선 가능.  
적용 시 선행: parameterization 실제 가능 여부 별도 확인.

**타개 방안 C — in vitro ADMET 패널**  
hemolysis assay, cytotoxicity (MTT/CCK8), SSTR2 binding Ki assay (RI팀 또는 CRO 외주)  
PRST-001 우선 적용. ADMET=1.00 판정이 OOD 아티팩트인지 실제 독성인지 구분하는 유일한 방법.

**일정**: 1개월 — 법무 검토 완료 및 저자 답변 수령. 3개월 — in vitro ADMET 패널 결과 수령. 6개월 — 도메인 특화 ADMET 모델 fine-tuning (데이터 확보 전제).  
**KAERI 비용 영향**: 법무 검토 행정 비용(내부), in vitro assay 외주 비용, Schrödinger 라이센스(별도 견적 필요).

---

### 한계 3: 3-Layer Ensemble — enrichment 경로와의 분리

**타개 방안 A — enrichment 정합 (Phase 5 리팩토링)**  
`enrich_candidates_from_wrappers`가 `run_routed_halflife`, `compute_layer1_halflife`를 실제 호출하도록 연결.  
PR #117 (ADMET divergence guard) main 머지. PR #112 (Layer 2 재학습) 머지 여부 합의.  
선행 조건: "어느 엔진이 canonical인가" 팀 합의 → 6월 회의 의사결정 사항.  
작업 규모: 코드 연결은 비교적 단순 (1-2주 엔지니어링), 단 테스트 커버리지 유지 확인 필요.

**타개 방안 B — 현상 유지 + 수동 H-06 disclaimer**  
현재처럼 사람이 합성 의뢰서에 H-06 경고와 OOD 문구를 수동으로 추가.  
단기 운영 비용은 낮으나, 후보 수가 늘어나면 관리 불가.

**일정**: 1개월 — PR #117 main 머지 및 canonical 경로 합의. 2개월 — enrichment 정합 코드 구현 및 테스트. 3개월 — 전체 파이프라인 재실행으로 PRST-001~004 enrichment 결과 재산출.

---

### 한계 4: DiffPepDock SS bond 처리 불가

**타개 방안 A — Schrödinger Glide enhanced peptide protocol**  
Glide XP + Prime MM-GBSA rescoring: cyclic peptide에 대한 pose prediction 개선 가능성 (Tubert-Brohman et al. 2013 JCIM: enhanced peptide protocol에서 top-10 기준 RMSD ≤2Å 성공률 58%, FlexPepDock 63%와 근사). 단, 이 수치는 우리 SST-14 cyclic SS bond system에 그대로 재현된다는 보장이 없으며 별도 validation 필요 (narrative-v3 §6.3 단서, 부록 C 수치 참조).  
SS bond, D-AA, DOTA 처리: BioLuminate parameterization 후 Glide 입력 가능 여부 확인 필요.

**타개 방안 B — FlexPepDock 현행 유지**  
현재 FlexPepDock (PyRosetta)은 8.6초/건으로 실 동작 확인 (phase2 smoke §4.B.3). SS bond constraint 처리 가능. 단, 처리량 한계는 Boltz 대비 느림.

**일정**: 3-6개월 (Schrödinger 도입 검토 결과 연동).  
**KAERI 비용 영향**: Glide 라이센스 포함 여부 확인 필요 (Schrödinger 패키지 구성).

---

### 한계 5: Boltz-2 처리량 — 순차 처리 병목

**타개 방안 A — 스모크 전용 프로파일 + 처리량 조정**  
Step05 진입 전 QC 통과 후보 수 축소 (현재 55개 전체 순차 Boltz 실행). `docking_top_pct` 파라미터로 조정. 스모크용 최소 프로파일 별도 yaml 작성 (phase2-smoke §9 권고 1·2).  
즉시 적용 가능, 비용 없음.

**타개 방안 B — GPU 병렬화 + DGX 도입**  
A-07 DGX H100(80GB×8) 또는 DGX B200 견적과 연동. Boltz 병렬 실행으로 처리량 개선. Desmond/FEP+ job 병렬화도 동시 확보 가능 (narrative-v3 §6.5).  
비용: 외부 견적 미수집 상태 (A-07 외부 진행 대기).

**일정**: 즉시(스모크 프로파일) / 3-6개월(DGX 구매·납기 기준).

---

### 한계 6: Selectivity — absolute pose validation 불가

**타개 방안 A — SST-14:SSTR2 복합체 구조 정보 활용**  
공개된 SST-14:SSTR2 cryo-EM 복합체 구조가 없다. 대안으로 octreotide:SSTR2 복합체 구조(기존 문헌, SSTR2 cryo-EM 복합체 논문 탐색)를 레퍼런스로 사용하는 방안 검토.  
선행 조사: researcher 에이전트 또는 PubMed/RCSB 탐색으로 SST 유사체:SSTR2 복합체 구조 유무 확인.

**타개 방안 B — WaterMap (Schrödinger) 연동**  
SSTR2와 off-target subtype pocket의 hydration pattern 차이를 selectivity 해석에 연결 (narrative-v3 §6.3). 절대 pose validation을 대체하지는 않으나 selectivity 근거를 보강할 수 있음.

**타개 방안 C — Ki assay (wet-lab)**  
SSTR2 Ki + SSTR1/3/4/5 Ki 동시 측정. 계산 selectivity 배수(ΔΔG 기반)와 실측 Ki 비율 비교. Gate-2 판단의 핵심.

**일정**: 1개월(문헌 구조 탐색) / 3개월(Ki assay 결과) / 6개월(WaterMap 적용, Schrödinger 도입 연동).

---

## 3. 향후 6~12개월 진행 가능 목표 (약리·생물 측면)

"이론적으로 가능"이 아니라 현재 우리 도구·인력·데이터·GPU 환경에서 달성 가능한 것만 기재한다.

### 7단계 선별 체계와의 매핑

| 단계 | 내용 | 6개월 내 현실 목표 |
|------|------|--------------------|
| (1) SSTR2 Specificity | FlexPepDock ΔG, selectivity | 현재 가능. PRST-001 Tier S 유지 검증 |
| (2) Serum Stability | ProtParam + MD RMSD | 계산: HEURISTIC 순위만. 실측: wet-lab assay 의뢰 후 3-4개월 내 결과 |
| (3) Toxicity | pepADMET (OOD 경고) | 계산: 현상 유지. 실측: in vitro hemolysis·cytotoxicity 3개월 내 |
| (4) Lead compound 확정 | WSS + Pareto | 코드 정합 후 PRST-001~004 재산출 (2개월) |
| (5) AA Modification | radiolysis 잔기 치환 | 치환 후보 목록은 완성. 실 치환 후보 도킹은 FlexPepDock으로 가능 |
| (6) RI-MD simulation | MM-GBSA, FEP/TI | 현재 도구로는 OpenMM 기반 가능성만, Schrödinger 도입 여부 결정 전 보류 |
| (7) 기타 예측 | RCY/RCP, 제형 안정성 | RI팀 실험 데이터 없이는 계산 불가 |

### 1개월 단위 마일스톤

**M+1 (2026-06, 6월 회의 전후)**
- PRST-001 합성 발주 결정 확정 (회의 7.1 의사결정 후)
- pepADMET 법무 검토 결과 수령 (회의 7.2 후)
- A-07 GPU 견적 수집 완료 (담당: 안기범 박사)
- PR #117 (ADMET divergence guard) main 머지
- canonical enrichment 경로 팀 합의 (3-Layer vs 구 경로)
- Schrödinger 도입 검토 승인 여부 결정 (회의 7.4)

KPI: 6월 회의에서 "발표 narrative와 코드 enrichment 경로가 동일한가" = YES/NO 판정 가능.  
검증: PR #117 머지 후 `pipeline_local/tests/ 전체 PASS` 유지 확인.

**M+2 (2026-07)**
- PRST-001 합성 진행 상태 확인 (발주 후 리드타임)
- enrichment 정합 코드 구현 완료 (PR #112 Layer 2 머지 포함 또는 대안)
- Schrödinger 라이센스 조건 확인 완료 (도입 검토 승인 시)
- BioLuminate·Glide D-AA/DOTA parameterization 가능성 1차 확인 (도입 시)

KPI: enrichment 재실행 결과에서 PRST-001~004 Tier 변동 없음 확인.  
검증: 재산출된 합성 의뢰서의 반감기·ADMET 항목이 HEURISTIC 등급 명시 유지.

**M+3 (2026-08)**
- PRST-001 합성 완료 예상 (리드타임 2-3개월 가정)
- Ki assay 의뢰 준비 (SSTR2 + off-target)
- serum stability assay 의뢰 (LC-MS/MS 기반 인간 혈장)
- Schrödinger Glide sanity workflow 1차 산출 (도입 시: PRST-001 docking pose)

KPI: Ki assay 결과가 ΔG 계산 순위와 Spearman ρ > 0 이면 계산 파이프라인 1차 신뢰 지점 확보.  
KPI 미충족 위험: 합성 리드타임 지연 시 assay 일정 전체 shift.

**M+4 (2026-09)**
- Ki assay 결과 수령 (SSTR2 selectivity 실측 확인)
- serum stability t½ 실측 결과 수령
- ADMET 실측 패널 (hemolysis, cytotoxicity) 결과 수령
- 계산값 vs 실측값 불일치 분석 보고 (6월 회의 §7.5 에서 요청된 산출물)
- Layer 2 모델 재학습 입력 데이터 구성 (실측 t½ 기반)

KPI: 계산 Tier 순위와 Ki assay 순위가 상위 2건 이상 일치.  
검증 방법: Spearman ρ (예측 ΔG 순위 vs 실측 Ki 역수 순위), 목표 ρ > 0.5.

**M+5 (2026-10)**
- Layer 2 재학습 (실측 t½ 데이터 포함) 1차 결과
- RI 표지 (177Lu-DOTA) 실험 준비 (Gate-2 진입 조건 충족 시)
- Schrödinger FEP+ ΔΔG vs Ki 상관 1차 평가 (도입 시)
- modification 후보 (5-F-Trp, Met→Nle 등) 도킹 재스크리닝

KPI: Layer 2 R² > 0 달성 (기준선 0.022 대비 개선).  
현재 선행 조건이 충족되지 않으면 이 마일스톤 자체가 이동한다.

**M+6 (2026-11)**
- 177Lu 표지 후 RCP/Radiochemical stability 72h 측정 (Gate-2 진입 후보 대상)
- A-04 §5 modification 후보 중 RCP 90% 이상 달성 후보 선별 (회의록 §4 A-04 선별 기준)
- Quencher 조합 DOE 설계 (Gentisic acid + Ascorbic acid + Ethanol 기준, 회의록 §4 A-04 제안)

KPI: 72h RCP ≥ 90% 달성 후보 ≥ 1건.  
검증: RI팀 HPLC 측정 결과.

---

## 4. 5/28 회의에서 박사 청자에게 보고하는 방법 — 한 단락

4월 Action Item 8건 중 6건을 충족했고, 계산 파이프라인 기준으로는 후보 4개와 합성 의뢰서를 내놓았다. 그러나 이 후보들의 ADMET과 혈청 반감기 수치는 절대값으로 읽을 수 없다. D-아미노산과 SS bond cyclic peptide가 기존 예측 도구의 학습 범위 밖에 있다는 것이 이유이고, 이 사실은 코드에도 명시되어 있다. PR #85의 3-Layer Ensemble 모듈은 이 한계를 해결하지 않으며, 한계를 수치와 경고 플래그로 드러내고 단일 도구 출력이 합성 결정으로 직행하지 못하게 막는 구조다. 코드 enrichment 경로가 이 모듈을 아직 호출하지 않는다는 사실도 발표 자료에서 직접 공개한다. 5/28 회의에서 필요한 의사결정은 세 가지다. 첫째, PRST-001 합성 발주 범위 (Tier S 1건 우선인가, 4건 전체인가), 단 합성 발주 시 serum stability·hemolysis·Ki assay·RCP 실험 패키지를 의뢰서에 포함한다. 둘째, Schrödinger 도입 검토를 6월 회의까지 진행할지의 승인 여부 (비용·라이센스·시스템 적용 결과는 6월 정량화). 셋째, A-07 GPU 견적 결과 확인 및 Desmond/FEP+ 연동 여부. 이 세 결정이 없으면 6월 회의의 "예측값과 실측값 불일치 보고"가 시작되지 않는다.

---

## 5. PASS/FAIL 매트릭스 — 약리·생물 항목별 신뢰 등급

| 항목 | 값 (근거) | 신뢰 등급 | 상태 |
|------|----------|-----------|------|
| Kyte-Doolittle lookup | LITERATURE_VALUES 등록 (1982 J Mol Biol 157:105) | HIGH | PASS |
| Boman Index 부호 규약 | 양수=친수성/단백질 결합 잠재력 高 (Boman 2003 J Intern Med 254:197) | HIGH | PASS |
| Guruprasad Instability Index < 40 기준 | PRST-001 II=28.5 (narrative-v3 §3 A-09) | MED | PASS |
| N-end rule Pro = 30h | LITERATURE_VALUES 등록, NOT 20h (Varshavsky 1996 PNAS 93:12142) | HIGH | PASS |
| FlexPepDock SST-14 reference ΔG | 553.857 REU, σ=4.024 (n=10, KAERI A-05 2026-05-19) | MED | PASS |
| Boltz-2 SST-14 reference ΔG | -95.024 REU (KAERI A-05, LITERATURE_VALUES 등록) | MED | PASS |
| pepmsnd_local R² | -0.028 (초기), 0.022 (재학습, seed 의존) | HEURISTIC/LOW | FAIL (의사결정 불가) |
| D-AA 혈청 t½ 예측 | 지원 도구 0개 (ENDPOINT_CONFIDENCE 전수 확인) | LOW/UNAVAILABLE | FAIL |
| ADMET binary_toxicity=1.00 | OOD 외삽 가능성 高 (D-AA+cyclic+DOTA) | LOW | §검증 필요 |
| DiffPepDock RMSD KPI | RMSD ≤2Å 재현율 80% 미충족, SS bond 처리 불가 | — | NOT_RECOMMENDED |
| SSTR1/3/4/5 정렬 RMSD | 2.770~3.125 Å (KPI 4Å 이내 충족) | MED | PASS |
| absolute pose validation | SST-14:SSTR2 cryo-EM 복합체 구조 부재 | LOW | §검증 필요 |
| PRST-001~004 sequence identity | 86~93% (권장 80% 이하 미충족) | MED | WARN |
| Selectivity ≥100× (계산) | ΔΔG 기준 산출, 단위 환산 후 확인 필요 | MED | 조건부 PASS |
| 3-Layer enrichment 정합 | enrichment 경로 미연결 (현재 브랜치) | — | §검증 필요 |
| PR #117 main 포함 여부 | 미포함 (현재 브랜치 및 main 모두) | — | §검증 필요 |
| Boltz 1 iter 완주 | 1500s timeout으로 미완 (55후보 중 32건) | — | FAIL |

---

## 6. 부호 규약 일관성

Boman Index: 양수 = 친수성/단백질 결합 잠재력 高 (Radzicka & Wolfenden 1988 기준에서 부호 반전 — LITERATURE_VALUES `radzicka_wolfenden_boman_convention` 등록, pharmacology_guards.py 76/76 테스트 통과).

Rosetta REU: FlexPepDock fallback 모드에서 양수 출력. candidate < SST14 reference (553.857 REU) = SST14 대비 유리. Boltz-2는 음수 (∆G 물리 기반). 두 값은 단위·스케일이 다르며 직접 비교하지 않는다 (narrative-v3 §3 A-05).

Instability Index: < 40 = stable (Guruprasad 1990 PEDS 4:155). PRST-001 II=28.5 (stable 범위).

---

## 7. 출처 카운트

주요 수치·주장 인용 가능 근거: 회의록 MOM-003 (9페이지), narrative-v3 (596줄), 3layer 분석 (274줄), phase2 smoke (237줄), phase3 UI/UX, be-p0-fix, demo-scenario, pharmacology_guards.py 직접 조회 결과.  
출처 없이 추정된 수치: 0건.

---

## 8. §검증 필요 항목

1. SST-14:SSTR2 cryo-EM 복합체 구조 유무 — RCSB·PubMed 탐색 필요. Octreotide:SSTR2 복합체 구조 대안 활용 가능성.
2. PRST-001~004 ADMET binary_toxicity=1.00 — in vitro hemolysis·cytotoxicity 실측으로만 확인 가능.
3. D-AA 혈청 t½ — wet-lab serum stability assay 선행 필수.
4. Schrödinger BioLuminate D-AA/cyclic/DOTA parameterization 실제 가능 여부 — 라이센스 확보 후 직접 확인.
5. PR #117 main 동기화 — enrichment 정합 작업의 선행 조건.
6. Ki assay (SSTR2 + off-target) — selectivity ≥100× 계산 결과의 실측 검증.
7. PRST-001~004 sequence identity 86~93% — 다양성 부족이 실제 lead diversity에 미치는 영향.

---

## 마지막 stdout 5줄

**가장 결정적 한계 1개**: D-AA 후보에 대한 혈청 반감기 예측 도구가 전무하다. 11종 ENDPOINT_CONFIDENCE 전수 조회에서 D-AA 지원 True 항목이 0건이며 (halflife_webmetabase_indirect는 혈청 t½이 아님), pepmsnd_local R²=-0.028이다. 계산 파이프라인의 핵심 선별 기준(TPP-B ≥24h, TPP-C ≥72h)을 검증할 수단이 없다.

**6월 회의 전까지 최소 closure 가능한 항목 1개**: PR #117 (ADMET divergence guard) main 머지 + canonical enrichment 경로 팀 합의. 코드 변경 규모가 작고 (3layer 분석 §3.5 확인), 완료 시 narrative와 코드 격차 중 가장 명시적인 항목이 닫힌다. 736 passed 회귀 테스트 유지 여부는 즉시 확인 가능.

**KPI 미충족 위험이 가장 높은 항목 1개**: M+3 Ki assay — PRST-001 합성 리드타임 지연 시 전체 wet-lab 일정이 연쇄 shift된다. 합성 발주 결정 지연이 Ki assay 결과 수령을 M+5 이후로 밀 수 있으며, 그 경우 6~12개월 내 실측 기반 모델 보정 자체가 불가능해진다. 5/28 회의에서 합성 발주 범위를 확정하는 것이 전체 wet-lab 일정의 critical path다.

**회의 §7 의사결정 요청에 추가해야 할 항목 1개**: Ki assay 및 serum stability assay 실험 패키지의 담당 기관 확정 (KAERI RI팀 내부 수행 vs 외부 CRO 위탁). 현재 narrative-v3 §7에 합성 범위·ADMET 법무·GPU 견적·Schrödinger 검토는 포함되어 있으나, 실측 assay 패키지의 담당 분장이 빠져 있다. 합성 발주가 결정되면 즉시 assay 일정이 연동되므로 이번 회의에서 결정 주체를 정해야 한다.

**Phase 5 리팩토링 검토 시 본 분석의 활용**: canonical enrichment 경로 결정(enrichment이 3-Layer를 호출하는지 여부), PR #117 머지, D-AA 스킵 로직을 Layer 2 라우팅으로 연결하는 세 작업의 선행 조건을 본 분석의 §3 코드 격차 목록(composite_scorer.py:400-408, ensemble_router.py:61-76)을 리팩토링 태스크의 입력 스펙으로 직접 사용한다.
