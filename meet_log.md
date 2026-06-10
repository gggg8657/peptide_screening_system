# Meet Log — 액션 아이템 대응 현황

**원본**: `meet_log_backup.md`  
**갱신일**: 2026-03-24 (코드·보고서와 정합: [`docs/progress_report_20260323.md`](docs/progress_report_20260323.md))  
**Linear 일정**: Cursor MCP `linear`가 401이면 [linear.app](https://linear.app)에서 수동 동기화.

**한곳 관리 허브** (미팅 ↔ Linear ↔ Git): [`docs/bio_linear_ssot.md`](docs/bio_linear_ssot.md) — 프로젝트 링크, A-01~A-10 ↔ `CHA-xx` 매핑, 커밋 규칙.

---

## 액션 아이템 대응표

| ID | 액션 아이템 | 담당 | 기한 | 우선순위 | 대응 상태 | 대응 내용 / 근거 자료 |
|----|-----------|------|------|---------|:---------:|---------------------|
| **A-01** | PepCalc/PeptideCutter를 AI 파이프라인 Step 8에 통합하고 SST-14 변형체 혈청 t½ 예측값 산출 | AI팀 | 2주 | 높음 | ✅ **대체 구현** | PepCalc 자체는 **부적합 판정** (웹 전용, API 없음, 사이클릭 미지원). 대신 `pharma_properties.py` 13개 메서드로 자체 구현 완료. peptides 패키지 대비 8/8 완벽 일치 검증. Instability Index + Protease Sites 3효소로 stability surrogate 제공 중. |
| | | | | | | **근거**: `docs/pharma_properties_verification_report.md`, `docs/serum_stability_admet_tools_report.md` Part 5.1 #1 (PepCalc 부적합 판정) |
| | | | | | | **추가 기회**: pepADMET (펩타이드 전용 ADMET, 2026-03-23 발견) — Half-life 5종 모델 (R²=0.84~0.98) 제공하나 모델 파일 미공개. 독성 모델만 즉시 활용 가능 |
| **A-02** | ADMETlab 3.0 API를 활용하여 상위 21개 후보 ADMET 프로파일 일괄 생성 | AI팀 | 2주 | 높음 | ⚠️ **pepADMET 추론 성공** | ADMETlab 3.0 부적합 (TLS 만료, MW<500 전용). **pepADMET 대체**: `pepadmet` conda env 구축 완료 (DGL 0.4.3), MGA forward pass 성공 (binary toxicity + 6-class 추론 OK). descriptor 계산 파이프라인 연동 진행중. |
| | | | | | | **근거**: `serum_stability_admet_tools_report.md` Part 5.1 #7, Part 5.2 (ADMET 공통 부적합 사유) |
| | | | | | | **대안 진행**: pepADMET 독성 모델 (`toxicity_early_stop.pth`) 로컬 추론 성공. SMILES → descriptor 연동 완료 후 21개 후보 일괄 스크리닝 예정 |
| **A-03** | SSTR1/3/4/5 AlphaFold 구조 다운로드 + 도킹 프로토콜 구성. 선택성 스크리닝 파이프라인 연결 | AI팀 | 2주 | 즉시 | ✅ **완료** | `step05b_selectivity.py`에 SSTR1(P30872)/3(P32745)/4(P31391)/5(P35346) 코드 전부 구현. AlphaFold EBI API 동적 다운로드 + `compute_selectivity_margin()` + `apply_selectivity_gate()`. **SSTR1/3/4/5 실험 구조 CIF 경로 등록 완료** (커밋 `ec4982f`). |
| | | | | | | **근거**: `AG_src/pipeline/step05b_selectivity.py`, `AG_src/config/pipeline_config.yaml`, `AG_src/tests/test_selectivity.py`, 커밋 `ec4982f` (CIF 경로 등록), 커밋 `b54f2d9` (selectivity API 실제 FlexPepDock 도킹 연결, production mode 전환) |
| **A-04** | Critic Agent에 ClusterReport (A~E 분류) 추가 | AI팀 | 1개월 | 높음 | ✅ **구현 완료** | `pyrosetta_flow/cluster_report.py` — `classify_cluster()`, `batch_classify()`, A~E 스펙 반영. 테스트 57개 통과. |
| | | | | | | **A~E 정의**: 결합 엘리트 / 선택성 특화 / 안정성 강화 / 방사화학 최적 / 탐색 후보 — 상세는 progress_report §이슈 4 |
| | | | | | | **근거**: 커밋 `e5790dd`, `pyrosetta_flow/tests/test_cluster_report.py` |
| **A-05** | BLOSUM62 Tier 1 / 물리화학 필터 Tier 2 / 비제한 Tier 3 병렬 후보 생성으로 Step 3B 재설계 | AI팀 | 1개월 | 높음 | ✅ **구현 완료** | `runner.py` Thompson Sampling + BLOSUM62 constraint 기반 mutation. `bayesian_optimizer.py`에서 GP surrogate + UCB로 exploration-exploitation 균형. Pareto ranking으로 다목적 최적화 |
| | | | | | | **근거**: `step03b_blosum_mutation.py`, `bayesian_optimizer.py` (24+3 tests), `pareto_ranking.py` (9 tests), `docs/alternative_scoring_modules.md` |
| | | | | | | **정확한 Tier 1/2/3 구분은 아니지만**, BLOSUM constraint → 물리화학 QC → 비제한 탐색(BO suggest)으로 동등 기능 |
| **A-06** | RI팀: Peptron, HLB PEP, Anygen에 DOTA-펩타이드 합성 견적 문의 | RI팀 | 2주 | 높음 | ⏸️ **RI팀 담당** | AI팀 scope 밖. RI팀 진행 여부 확인 필요 |
| **A-07** | RI팀: 상위 3개 후보 Lys/N-말단 C18 부착 변형체 설계안 → AI팀 구조 검토 미팅 | RI팀 | 1개월 | 보통 | ⏸️ **RI팀 담당** | AI팀 scope 밖. Silo B 대규모 실행 후 Top-K 확정되면 진행 가능 |
| **A-08** | 13-메트릭 패널에 Selectivity Margin Index, Radiolysis Susceptibility, Chelator Binding Compatibility 추가 | AI팀 | 2주 | 높음 | ✅ **3/3 구현** | Chelator: `analyze_metal_coordination()` + 규칙 #5. Selectivity margin: `step05b_selectivity.py`. Radiolysis: `calculate_radiolysis_susceptibility()` (pharma_properties / pharmacology 동기, `tests/test_radiolysis.py`). |
| | | | | | | **근거**: progress_report §이슈 5, 커밋 `e5790dd` |
| **A-09** | 아주대 김민규 교수팀 JCIM 논문 검토 → 파이프라인 적용 가능 항목 정리 | AI+RI팀 | 2주 | 보통 | ✅ **논문 분석 완료** | 김민규 교수팀이 공유한 논문: **pepADMET** (Tan, Liu, Zhou, Fang, Ouyang, Zeng, Dong — Central South Univ.) JCIM 2026, 66, 936-946 전문 분석 완료 |
| | | | | | | **핵심**: 펩타이드 전용 ADMET 플랫폼, 36,643 데이터, 26개 독립 데이터셋, 19개 ADMET endpoint, 17개 예측 모델 |
| | | | | | | **적용 가능 항목**: (1) 독성 모델 즉시 (GitHub .pth 공개), (2) Permeability/Half-life는 웹 API 또는 모델 재현 필요 |
| | | | | | | **근거**: 아래 "pepADMET 논문 분석 결과" 섹션 참조, `serum_stability_admet_tools_report.md` #17 |
| **A-10** | RCP 안정성 예측 모듈 (radiolysis risk 추정) 구현 여부 확인 | AI팀 | 1개월 | 보통 | ✅ **구현 완료** | A-08과 동일: `calculate_radiolysis_susceptibility()` — Met/Trp/Cys/His 등 가중, FWKT critical 잔기 표시. SST-14 예: total 6.5, risk high (W8). |
| | | | | | | **근거**: progress_report §이슈 7, `tests/test_radiolysis.py` |

---

## 대응 요약

```
총 10건 액션 아이템 (2026-04-02 기준):
  ✅ 완료/대체     7건  A-01, A-03, A-04, A-05, A-08, A-09, A-10
  ⚠️ 부분/진행중   1건  A-02 (pepADMET 추론 성공, descriptor 연동 진행중)
  ❌ 부적합(대안 있음) 0건
  ⏸️ RI팀 담당     2건  A-06, A-07
```

## 미해결 → 후속 액션 매핑

| 원본 ID | 미해결 내용 | 현재 후속 액션 | 우선순위 |
|---------|-----------|--------------|---------|
| A-02 | ADMETlab 3.0 부적합 | → **pepADMET 독성 추론 성공** (env 완료, descriptor 연동 진행중) | P1 |
| ~~A-03~~ | ~~SSTR1/3/4/5 코드 완료, PDB 다운로드 + 실행 미완~~ | **✅ 완료** — CIF 경로 등록 완료 (커밋 `ec4982f`) | — |
| A-04 | ~~A~E 구현~~ **완료** | 대시보드/UI 연결·운영 검증은 백로그 (`progress_report` §5) | P2 |
| A-08 | ~~3종 메트릭~~ **완료** | PharmacologyPanel 표시 등 UX는 선택 | P2 |
| A-09 | ~~논문 분석 완료~~ | → **pepADMET 독성 모델 로컬 통합** + 웹 API 파이프라인 (`pepadmet_reproduction_plan.md`) | P1 |
| A-10 | ~~Radiolysis~~ **완료** | 추가 튜닝·임상 상관은 후속 | — |

---

## pepADMET 논문 분석 결과 (A-09)

**논문**: Tan, Liu, Zhou, Fang, Ouyang, Zeng, Dong. "pepADMET: A Novel Computational Platform For Systematic ADMET Evaluation of Peptides." *J. Chem. Inf. Model.* 2026, 66, 936-946.
**소속**: Central South University (Xiangya School of Pharmaceutical Sciences) + ICMS (Macau)
**웹**: https://pepadmet.ddai.tech
**GitHub**: https://github.com/ifyoungnet/pepADMET (독성 모델만 공개)
**분석일**: 2026-03-23

### 1. 19개 ADMET Endpoint 전체 목록 + 성능

#### Absorption (4 endpoints)
| Endpoint | 데이터 수 | 모델 | 핵심 메트릭 |
|----------|----------|------|-----------|
| Permeability (P_app) — RRCK-C | 181 | LightGBM | R^2=0.623, RMSE_t=0.420 |
| Permeability (P_app) — PAMPA-C | 6698 | LightGBM | R^2=0.657, RMSE_t=0.423 |
| Permeability (P_app) — Caco2-A | 886 | LightGBM | R^2=0.476, RMSE_t=0.573 |
| Permeability (P_app) — Caco2-C | 645 | LightGBM | R^2=0.527, RMSE_t=0.472 |
| Permeability (P_app) — Caco2-L | 241 | GNN | R^2=0.435, RMSE_t=0.765 |

#### Distribution (1 endpoint)
| Endpoint | 데이터 수 | 모델 | 핵심 메트릭 |
|----------|----------|------|-----------|
| BBB Penetration | 850 | Classification | AUC=0.900 |

#### Metabolism (1 endpoint)
| Endpoint | 데이터 수 | 모델 | 핵심 메트릭 |
|----------|----------|------|-----------|
| LogD_7.4 | 257 | Regression | R^2=0.818 (test) |

#### Excretion (5 endpoints — Half-life)
| Endpoint | 데이터 수 | 모델 | 핵심 메트릭 |
|----------|----------|------|-----------|
| T_1/2 MIM (Mouse In-vitro Microsome) | 378 | TL (RF) | R^2=0.940, RMSE_t=0.540 |
| T_1/2 MBM (Mouse Blood Microsome) | 187 | TL (RF) | R^2=0.930, RMSE_t=0.490 |
| T_1/2 MBN (Mouse Blood Natural) | 106 | TL (XGBoost) | R^2=0.984, RMSE_t=23.150 |
| T_1/2 HBM (Human Blood Microsome) | 117 | TL (SVR) | R^2=0.900, RMSE_t=147.650 |
| T_1/2 HBN (Human Blood Natural) | 182 | TL (SVR) | R^2=0.840, RMSE_t=272.200 |

#### Toxicity (12 endpoints)
| Endpoint | 데이터 수 | 모델 | 핵심 메트릭 |
|----------|----------|------|-----------|
| Binary Toxicity | 14,660 | MLR-GAT | AUC=0.885 |
| 6-class Toxicity Type | 14,660 | MLR-GAT | ACC=0.885, AUC=0.949 |
| 4-class Neurotoxicity | — | MLR-GAT | ACC=0.794, AUC=0.885 |
| HC_50 (Hemolytic) | 2,423 | Regression | R^2=0.474 |
| Toxin_four (4-class) | — | Classification | AUC_t=0.905 |
| Toxin_six (6-class) | — | Classification | AUC_t=0.949 |
| Cytolysis | 121 | Classification | — |
| Neurotoxin | 848 | Classification | — |
| Cytotoxicity | 622 | Classification | — |
| Hemostasis-impairing toxin | 148 | Classification | — |
| Hemolysis | 6,656 | Classification | — |
| F (경구 생체이용률) | 305 | Classification | AUC=0.900 |

#### Physicochemical Properties (10 endpoints, 직접 계산)
Length, MW, Charge, Aromaticity, pI, ChargeDensity, InstabilityInd, AliphaticInd 등

### 2. 모델 아키텍처 요약

| 카테고리 | 아키텍처 | 핵심 전략 |
|---------|---------|---------|
| **Half-life (5종)** | Transfer Learning | RT DB ~350K 펩타이드로 pre-train → half-life 데이터로 fine-tune. R^2 15% 향상 |
| **Permeability (5종)** | GNN + LightGBM | 분자 그래프 + descriptor/fingerprint 이중 경로. 세포주별 독립 모델 |
| **Toxicity (12종)** | MLR-GAT | Multi-Level Relational Graph Attention. 계층적 분류 (binary → 6-class → mechanism) |
| **Feature 계산** | PyBioMed + modlAMP + RDKit | 소분자 descriptor + 펩타이드 descriptor + 분자 fingerprint + 분자 그래프 |

### 3. Table 1 — 기존 도구 대비 비교

| 도구 | 데이터 수 | endpoints | basic property | ADME | toxicity | types | systematic |
|------|---------|-----------|---------------|------|----------|-------|-----------|
| **pepADMET** | **36,643** | **29** | **10** | **7** | **12** | **N+M** | **yes** |
| BBPred | 238 | 1 | 0 | 1 | 0 | N | no |
| BBPredict | 850 | 1 | 0 | 1 | 0 | N | no |
| SCMB3PP | 538 | 1 | 0 | 1 | 0 | N | no |
| DeepB3P | 7,269 | 1 | 0 | 1 | 0 | N | no |
| PlifePred | 261 | 12 | 10 | 2 | 0 | N | no |
| HemoPI-MOD | 1,166 | 1 | 0 | 0 | 1 | M | no |
| EnDL-HemoLyt | 4,339 | 1 | 0 | 0 | 1 | N+M | no |
| ToxinPred 3.0 | 11,036 | 1 | 0 | 0 | 1 | N | no |

**pepADMET이 유일하게**: (1) N+M (자연+변형 펩타이드) 모두 지원, (2) systematic evaluation 제공, (3) 29개 endpoint 통합

### 4. Case Study 검증 결과

| 펩타이드 | T_1/2 실험값 | T_1/2 예측값 | Permeability | Toxicity | 평가 |
|---------|-----------|-----------|-------------|----------|------|
| **Cyclosporine** (11aa cyclic) | 19.00h (10-27h) | 12.28h | Caco2: -5.64 (실험 -5.38) | Non-toxic | half-life 과소예측, permeability 정확 |
| **Desmopressin** (9aa, SS bond) | 3.00h | 2.46h | PAMPA: -5.84 | Toxic (맞음) | **SS bond 펩타이드에서 양호** |
| **Leuprolide** (9aa) | 3.00h (2-3.11h) | 2.95h | RRCK: -6.20 (실험 -6.20) | Non-toxic | 거의 정확 |

**핵심 발견**: Desmopressin은 SS bond 포함 사이클릭 펩타이드로 SST-14 유사체와 구조적 유사점 있음. pepADMET이 SS bond 펩타이드에서도 합리적 예측을 보임.

### 5. 사이클릭/변형 펩타이드 지원

- **명시적 지원**: 선형, 사이클릭, 변형(modified), 자연(natural) 펩타이드 모두 지원
- **입력 방식**: 서열 + SMILES 이중 입력 (SMILES로 변형 정보 전달)
- **변형 유형**: ~200종 (acetylation, amidation, cyclization, biotinylation, glycosylation, PEGylation)
- **제한**: 2-50 아미노산 (SST-14 = 14aa로 범위 내)
- **SS bond**: Desmopressin case study에서 검증됨. SMILES로 SS bond 표현 가능

### 6. GitHub 공개 현황 (ifyoungnet/pepADMET)

| 항목 | 공개 여부 | 파일 |
|------|---------|------|
| 독성 모델 (.pth) | **공개** | `toxicity_early_stop.pth` 등 |
| Half-life 모델 | **미공개** | — |
| Permeability 모델 | **미공개** | — |
| Feature 계산 코드 | **부분 공개** | PyBioMed, modlAMP, RDKit 조합 |
| 학습 데이터 | **미공개** (DB 참조만) | PEPlife, PepTherDia, THPdb 등 |
| 웹 서비스 | **접속 가능** | https://pepadmet.ddai.tech |

### 7. 우리 파이프라인 적용 가능성 평가

| 항목 | 적용 가능성 | 상세 |
|------|-----------|------|
| **독성 예측** | **즉시 (Tier 1.5)** | GitHub .pth 파일로 로컬 추론 가능. MLR-GAT 아키텍처, DGL 0.4.3 + PyTorch 필요 |
| **Permeability** | **중기 (Tier 2)** | 모델 미공개. 웹 API 자동화 또는 LightGBM 재학습 필요 |
| **Half-life** | **중기 (Tier 2)** | 모델 미공개. Transfer Learning 전략 재현 가능하나 RT DB 350K 필요 |
| **BBB** | **중기 (Tier 2)** | 모델 미공개. 웹 API 활용 가능 |
| **LogD_7.4** | **중기 (Tier 2)** | 모델 미공개. 웹 API 활용 가능 |
| **Physicochemical** | **불필요** | 우리 `pharma_properties.py`가 이미 동일 기능 구현 완료 |
| **Feature 계산** | **즉시 활용** | PyBioMed + modlAMP + RDKit 조합은 우리도 사용 가능. 2,133개 feature |

#### SST-14 유사체 (MW~1600, Cys3-Cys14 SS bond) 특이 고려사항

1. **MW 범위**: pepADMET 학습 데이터 2-50aa (MW ~200-5000). SST-14 14aa MW~1600은 **범위 내**
2. **SS bond**: Desmopressin (Cys1-Cys6) case study에서 검증. SST-14 (Cys3-Cys14)도 SMILES 표현 가능
3. **사이클릭**: 명시적 지원. Cyclosporine (11aa cyclic) case study 포함
4. **SSTR2 관련 펩타이드**: Octreotide, Lanreotide 등 학습 데이터 포함 여부 미확인이나, 유사 크기/구조 펩타이드 다수 포함 추정

### 8. pepADMET 기반 후속 액션

| # | 액션 | 우선순위 | 의존성 | 예상 소요 |
|---|------|---------|-------|---------|
| PA-01 | pepADMET GitHub clone + 독성 모델 로컬 추론 환경 구축 (DGL 0.4.3 + PyTorch) | P1 | 네트워크 (clone) | 1일 |
| PA-02 | SST-14 native + 상위 21개 후보 SMILES 변환 파이프라인 구축 (RDKit) | P1 | 없음 | 0.5일 |
| PA-03 | pepADMET 독성 모델로 21개 후보 binary toxicity + 6-class 분류 실행 | P1 | PA-01, PA-02 | 0.5일 |
| PA-04 | pepADMET 웹 API 자동화 (permeability, half-life, BBB, LogD) | P2 | 네트워크 | 1일 |
| PA-05 | Transfer Learning half-life 모델 재현 시도 (RT DB 확보 가능 시) | P3 | RT DB | 1주 |
| PA-06 | pepADMET 2,133 feature 계산 → Bayesian Optimizer 입력 feature 확장 | P2 | PA-02 | 1일 |

### 9. 기존 ADMET 부적합 판정 대비 pepADMET 차별점

| 기존 6개 ADMET 도구 (부적합) | pepADMET |
|--------------------------|---------|
| MW < 500 소분자 전용 | **2-50aa 펩타이드 전용** (MW ~200-5000) |
| 간 대사 + 신장 배설 모델 | **프로테아제 분해 + 조직별 반감기** 모델 |
| 선형 분자 가정 | **사이클릭 + SS bond + 변형 펩타이드 지원** |
| 온프레미스 전멸 | 독성: **GitHub 공개**, 나머지: **웹 API** |
| SMILES만 지원 | **서열 + SMILES 이중 입력** |
| systematic evaluation 없음 | **19 endpoint 통합 평가** |

> **결론**: pepADMET은 기존 serum_stability_admet_tools_report.md에서 "ADMET 도구 전부 부적합"이라 판정한 근본 사유 (Applicability Domain, 메커니즘 불일치, SS bond, 온프레미스)를 **대부분 해소**하는 유일한 도구. A-02 (ADMETlab 부적합)의 실질적 대안.
