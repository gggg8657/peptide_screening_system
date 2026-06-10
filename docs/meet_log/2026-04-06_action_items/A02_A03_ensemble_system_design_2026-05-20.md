# A-02/A-03 다중 도구 견제 Ensemble 시스템 설계 — researcher 종합 검토

**조사일**: 2026-05-20  
**조사자**: researcher subagent  
**의뢰**: 사용자 — "serum stability는 중요. 종합·체계 검토 + 대안 ensemble 시스템"  
**연관 파일**: `A-02_serum_halflife_tools.md`, `A-03_research_pepadmet_environment.md`

---

## Part 1. pepADMET 자체 학습 가능성

### 1.1 공개 자산 매트릭스 (실측 기반)

**로컬 디렉토리**: `_workspace/pepadmet_local/pepADMET/` (2026-05-20 `ls -lh` 실측)

#### 가중치 파일 전체 목록

| 파일명 | 크기 | Endpoint 추정 |
|--------|------|--------------|
| `model/toxicity_early_stop.pth` | **44 MB** | Toxicity (4 task: toxicity_nontoxicity, toxicity_type_class, neurotoxicity_type_class, HC50) |
| 기타 `.pth`/`.pt`/`.pkl`/`.h5` | **없음** | — |

**결론: 공개된 가중치는 toxicity 1개뿐.** 나머지 24~28개 endpoint는 가중치 미공개. 웹 플랫폼(pepadmet.ddai.tech)에서만 추론 가능.

#### 학습 스크립트 및 데이터 현황

| 항목 | 존재 | 상세 |
|------|------|------|
| `Train.ipynb` | **있음** | Toxicity endpoint 학습 워크플로우 데모 — GNN 학습 전체 코드 포함 |
| `utils/MY_GNN.py` | **있음** | RGCN (RelGraphConv) + FPN (2133-dim descriptor) 하이브리드 구조 |
| `utils/build_dataset.py` | **있음** | DGL 그래프 빌더 (dgl 0.4 API) |
| `build_graph_dataset.py` | **있음** | `Toxicity.bin`, `Toxicity_group.csv` 생성 |
| `calculate_descriptors.py` | **있음** | 2133개 분자 descriptor 계산 (PyBioMed + modlamp + RDKit 기반) |
| `data/Toxicity.csv` | **있음** | 135행, 컬럼 ~600개 (descriptor pre-computed) |
| `data/Toxicity.bin` | **있음** | 9.6 MB DGL 그래프 바이너리 |
| 반감기/흡수/분포 학습 데이터 | **없음** | Toxicity 이외 endpoint 데이터 미공개 |
| `requirements` | **있음** | 11개 패키지 핀 (Py3.7, torch1.13, dgl0.4.3) |

#### Train.ipynb 핵심 하이퍼파라미터 (실측)

| 파라미터 | 값 |
|----------|-----|
| `num_epochs` | 300 |
| `patience` (EarlyStopping) | 50 |
| `batch_size` | 128 |
| `lr` (log scale) | 3 (→ 10^-3 = 0.001) |
| `weight_decay` (log scale) | 5 (→ 10^-5) |
| `optimizer` | Adam |
| `descriptor_dim` | 2133 |
| `fpn_out` | 2133 |
| `fp_2_dim` | 512 |
| `hidden_size` | 256 |
| `rgcn_hidden_feats` | [64, 64] |
| `classifier_hidden_feats` | 320 |
| `dropout` | 0.2 |
| `in_feats` (원자 피처) | 40 |
| `times` (cross-validation folds) | 5 |

**모델 구조**: MGA (Multi-Graph Attention) = RGCN (분자 그래프, 이분 그래프) + FPN (2133-dim descriptor) 결합 → multi-task head.

#### pepADMET 29개 endpoint 중 공개/비공개 현황

웹 플랫폼 문서(pepadmet.ddai.tech/documentation) 기반:

| 카테고리 | Endpoint | 가중치 공개 | 학습 코드 | 학습 데이터 |
|----------|----------|------------|----------|------------|
| Toxicity | toxicity_nontoxicity, toxicity_type_class, neurotoxicity_type_class, HC50 | **공개** (toxicity_early_stop.pth) | **있음** (Train.ipynb) | **있음** (Toxicity.csv 135행) |
| 반감기 | HBN (human blood natural), HBM (human blood modified), MBN (mouse blood natural), MBM (mouse blood modified), MIM (mouse intestine modified) | **미공개** | 구조 있음 (MY_GNN 재활용) | **미공개** |
| 흡수/투과 | LogD7.4, F (oral bioavailability), Caco-2, PAMPA, RRCK | **미공개** | — | **미공개** |
| 분포 | BBB penetration | **미공개** | — | **미공개** |
| 기타 독성 | Hemolysis, Cytotoxicity | **미공개** | — | **미공개** |
| 나머지 | (기타) | **미공개** | — | **미공개** |

**총 요약**: 29개 endpoint 중 **Toxicity 4개 task만 로컬 재현 가능.** 25개 endpoint는 웹 플랫폼 API 전용.

---

### 1.2 논문 메서드 재현 가능성

**논문**: Tan X et al. 2026 JCIM DOI: 10.1021/acs.jcim.5c02518 (paywall — abstract + supplementary 기반 분석)

#### 모델 구조 (검색 결과 종합)

pepADMET는 endpoint별로 서로 다른 모델 구조를 사용:

| Endpoint 유형 | 모델 구조 |
|-------------|---------|
| Toxicity (HC50 포함) | MGA (RGCN + FPN + attention), multi-task |
| 반감기 (HBN, HBM, MBN, MBM, MIM) | Transfer learning (AlphaPeptDeep RT 사전학습, 351,804 proteomics entries) + 39개 효소 절단 descriptor (PeptideCutter) + RF/XGBoost/SVR/DNN |
| 투과성 (Caco-2, PAMPA) | GNN |
| 전통적 endpoint (LogD, F 등) | Random Forest, XGBoost, LightGBM |

**반감기 모델 아키텍처 (Tan et al. 2024 Briefings in Bioinformatics, bbae350 — 같은 저자 그룹):**
- 사전학습: AlphaPeptDeep RT 아키텍처, 351,804 proteomics 항목, 300 epoch, lr=1e-4
- 미세조정: 50 epoch, 각 endpoint 데이터
- 피처: 서열 인코딩 + 39개 효소 절단 descriptor (PeptideCutter 기반)

#### 학습 데이터 출처 및 크기

| Endpoint | 학습 샘플 수 | 데이터 출처 |
|----------|------------|-----------|
| HBN (human blood, natural) | 117 | PEPlife, 문헌 |
| HBM (human blood, modified) | 187 | PEPlife, PepTherDia |
| MBN (mouse blood, natural) | 106 | 문헌 |
| MBM (mouse blood, modified) | 182 | PEPlife |
| MIM (mouse intestine, modified) | 378 | PEPlife |
| 전체 (모든 endpoint 합계) | 36,643 | PEPlife, PepTherDia, UniProt, DBAASP v3, Hemolytik, CycPeptMPDB |

출처: Tan et al. 2024 *Briefings in Bioinformatics* bbae350; 웹 플랫폼 문서

#### 반감기 모델 성능 (Tan et al. 2024 — 같은 저자 그룹 선행 연구)

| Endpoint | R² (test set) | 비고 |
|----------|-------------|------|
| HBN | 0.84 | 인간 혈액, 자연 AA |
| HBM | 0.90 | 인간 혈액, 수식 펩타이드 |
| MBN | 0.984 | 마우스 혈액, 자연 AA |
| MBM | 0.93 | 마우스 혈액, 수식 펩타이드 |
| MIM | 0.94 | 마우스 장, 수식 펩타이드 |

출처: (Tan et al. 2024 Briefings in Bioinformatics DOI: 10.1093/bib/bbae350)

**주의**: 이 성능치는 train/test 내부 분포에서의 값. 우리 후보처럼 D-AA + SS bond + DOTA 구조는 학습 분포 밖일 가능성 높음.

---

### 1.3 자체 학습 비용·일정 추정

#### 데이터 다운로드 가능 여부

| 데이터 | URL | 다운로드 가능 |
|--------|-----|------------|
| Toxicity.csv (pepADMET GitHub) | github.com/ifyoungnet/pepADMET | **가능** (이미 로컬) |
| PEPlife (반감기, 2,229항목) | webs.iiitd.edu.in/raghava/plifepred/ | **가능** (웹서버 + 논문 supplementary) |
| PEPlife2 (반감기, 4,412항목) | webs.iiitd.edu.in/raghava/peplife2/ | **가능** (REST API + bioRxiv 2025) |
| pepADMET 반감기 학습 데이터 | **없음** — 저자 미공개 | 저자 직접 요청 필요 |
| pepMSND 학습 데이터 (635항목) | github.com/hmenghu/PepMSND | **확인 필요** |

**핵심 갭**: pepADMET 반감기 endpoint 학습에 사용된 데이터 자체는 저자 미공개. 그러나 PEPlife2 (4,412항목), pepMSND DB (635항목), Mathur et al. (261항목) 등을 조합하면 자체 학습 데이터셋 구성 가능.

#### H100 학습 시간 추정

**Toxicity endpoint 기준** (134 학습 샘플, 2133 descriptor, RGCN):
- 1 epoch: 약 1~5초 (소규모 데이터)
- 300 epoch (EarlyStopping 포함): 10~30분
- 반복 5회 (CV): 50~150분

**반감기 endpoint 기준** (HBM 187샘플 → 가장 클 경우):
- 데이터 소규모 → 학습 자체는 빠름 (< 1시간/endpoint)
- 문제는 **피처 엔지니어링**: 2133-dim descriptor 계산이 병목 (PyBioMed 에러 현황)
- H100 1장: 반감기 5개 endpoint 전부 학습 = 추정 2~6시간 (환경 구축 제외)

**환경 구축 비용 (현재 블로커)**:
- PyBioMed estate.py 패치 + conda 재구성: 2~8시간 (engineer-infra 위임)
- 이 작업이 선행 되어야 학습 가능

#### ROI 결론

**자체 학습 ROI: MEDIUM (조건부)**

조건:
1. pepADMET 반감기 endpoint 학습 → 데이터 부족 (HBN 117개, HBM 187개) → 과적합 위험 HIGH
2. PEPlife2 (4,412항목) 직접 학습 → **더 효율적 대안 존재**
3. 현재 우선순위는 "작동하는 ensemble" → 자체 학습은 중장기 과제
4. D-AA 지원 커스텀 모델 학습은 **PEPlife2 D-AA 항목(213건)** 활용 시 가능성 있으나 데이터 충분성 검증 필요

**단기 권고**: 자체 학습 시도 전에 PEPlife2 + pepMSND + HLE regression ensemble을 먼저 작동시키는 게 우선.

---

## Part 2. 다중 도구 견제 시스템

### 2.1 현재 도구 종합 매트릭스

> 범례: L-AA=표준 L-아미노산, D-AA=D-아미노산, 환형=SS bond 또는 head-to-tail 고리형, DOTA=DOTA 킬레이터 포함, P1=신뢰도 최고, P4=참고용

| 도구 | 입력 형식 | 출력 단위 | L-AA | D-AA | 환형 | DOTA | API/로컬 | 검증 데이터셋 | R² 또는 AUC (문헌) | 신뢰도 등급 | 라이선스 |
|------|---------|---------|------|------|-----|------|---------|-----------|------------------|-----------|---------|
| **ProtParam** (ExPASy) | 서열 (L-AA만) | N-end rule t½ (시간) | ✅ | ❌ | ❌ | ❌ | 웹 API | N-end rule 문헌 (Varshavsky 1996) | n/a (rule-based) | **P4** | 무료 |
| **HLP** (Raghava) | 서열 (10/16mer) | 장내 t½ (분) | ✅ | ❌ | ❌ | ❌ | 웹 전용 | HL10/HL16 SVM 데이터셋 | R²=0.32~0.82 (intestine) | **P3** | 무료 |
| **PlifePred** (Raghava) | 서열 or 수식 코드 | 혈액 t½ (분) | ✅ | 일부 수식 | ❌ | ❌ | 웹 전용 | 261 펩타이드 (PEPlife) | R²=0.743 (natural), 0.692 (modified) | **P2** | 무료 |
| **PeptideRanker** | 서열 | 활성 스코어 (0~1) | ✅ | ❌ | ❌ | ❌ | 웹 전용 | GPCR 활성 펩타이드 | AUC~0.85 | **P4** (간접) | 무료 |
| **PeptideStability** (proteomics) | 서열 (L-AA, <20aa) | 안정성 스코어 | ✅ | ❌ | ❌ | ❌ | GitHub + 웹 | proteomics quantif. | AUC 있음 | **P3** | 오픈소스 |
| **pepMSND** | 서열 or SMILES | 혈액 안정성 (binary: stable/unstable) | ✅ | ✅ (D-치환) | ✅ (107 cyclic) | ❌ (PEG 제외) | 웹 (model.highslab.com) + GitHub | 635 펩타이드 (PubMed+PEPlife+DrugBank+THPdb) | AUC=0.912, Acc=0.867 | **P2** | GitHub 공개 |
| **CAMSOL-PTM** | 서열 + 비천연 AA SMILES | 용해도 점수 | ✅ | ✅ (non-natural AA) | 일부 | ❌ | 웹 전용 (Cambridge) | 37 펩타이드 실험 검증 | 검증됨 | **P2** (용해도 전용) | 무료 |
| **webmetabase** | 서열 | 효소 절단 사이트 분석 | ✅ | 부분 | 부분 | ❌ | 웹 전용 | — | n/a (rule-based) | **P3** (간접) | 무료 |
| **HLE regression** (Cavaco 2021) | 서열 (L-AA) | 혈청 t½ (분) | ✅ | ❌ | ❌ | ❌ | JS/Electron (로컬 빌드) | 129 펩타이드, 51 문헌 | R²=0.76~0.78 | **P2** | 무료 |
| **pepADMET Toxicity** | 서열 + 2133 desc | 독성 (4-class) | ✅ | **불명확** | **불명확** | ❌ | 로컬 (.pth 공개) / 웹 | 135 펩타이드 (Toxicity.csv) | 논문 미공개 (웹에서만 평가) | **P2** (독성) | GPL-3.0 |
| **pepADMET 반감기** (HBM) | 서열 | 인간 혈액 t½ (수식 펩타이드) | ✅ | 부분 지원 추정 | 부분 추정 | ❌ | **웹 전용** (가중치 미공개) | HBM 187, HBN 117 | R²=0.90 (HBM test) | **P1** (웹 전용) | GPL-3.0 |
| **ADMET-AI** (Chemprop) | SMILES | 소분자 ADMET (41 endpoints) | ✅ | ✅ (SMILES 입력) | ✅ (SMILES) | ✅ (SMILES) | pip install + GitHub | TDC 41 datasets | 소분자 기준 상위 | **P3** (펩타이드 미검증) | MIT |
| **FP-ADMET** | SMILES + Fingerprint | ADMET 50개 (분류) | ✅ | ✅ (SMILES) | ✅ (SMILES) | ✅ (SMILES) | GitHub (GPL-3.0) | ADMET 공개 DB | 소분자 기준 | **P3** (펩타이드 미검증) | GPL-3.0 |
| **자체 학습 모델** (미구현) | 자유 | t½ (연속값) | ✅ | ✅ (학습 시) | ✅ (학습 시) | ✅ (SMILES) | 로컬 | PEPlife2 (4,412) | 미지 (구축 후 결정) | **P1 목표** | 자유 |

**우리 핵심 후보 (D-Phe + SS bond + DOTA)에 실질 적용 가능한 도구:**
- 완전 지원: **없음**
- 부분 지원 (D-AA): **pepMSND**, **ADMET-AI/FP-ADMET** (SMILES 우회)
- L-AA 근사 적용 가능: **PlifePred**, **HLE regression**, **pepADMET HBM** (웹)
- SMILES 기반 (DOTA 포함 가능): **ADMET-AI**, **FP-ADMET**

---

### 2.2 Ensemble 옵션 비교

#### 옵션 1: 단순 평균 ensemble

도구 N개의 예측값 단순 평균.

| 항목 | 내용 |
|------|------|
| 장점 | 구현 단순, 즉시 적용 가능 |
| 단점 | 단위 불일치 (t½ 분/시간/점수 혼재), 모든 도구가 동일 후보에 적용 불가 |
| 한계 | D-AA 처리 불가 도구가 포함되면 L-AA 근사값이 평균에 섞임 — **편향 전파** |
| 우리 프로젝트 | **부적합** — 도구 적용 범위가 다름 |

#### 옵션 2: 가중 평균 (신뢰도 기반)

ENDPOINT_CONFIDENCE 등급 (P1~P4) 또는 문헌 R²을 가중치로 사용.

| 항목 | 내용 |
|------|------|
| 장점 | 신뢰도 낮은 도구의 영향 감소, 투명성 |
| 단점 | 여전히 적용 범위 불일치 문제 잔존, 가중치 결정이 임의적 |
| 한계 | D-AA 후보에서 L-AA 도구의 가중치를 0으로 설정해야 하지만 규칙이 복잡 |
| 우리 프로젝트 | **조건부 적합** — 옵션 3과 결합 시 효과적 |

#### 옵션 3: 도구별 도메인 분리 (specialist 라우팅)

후보 특성에 따라 다른 도구를 선택.

```
후보 분류 → 라우팅 룰:
  if 후보가 순수 L-AA 선형:
      PlifePred + HLE regression + pepADMET HBM (웹) → 가중 평균
  elif 후보가 D-AA 포함:
      pepMSND (primary) + ADMET-AI SMILES (보조) + H-06 disclaimer
  elif 후보가 환형 (SS bond):
      pepMSND (cyclic 지원) + pepADMET HBM (웹, 환형 포함 추정)
  elif 후보가 DOTA 포함:
      ADMET-AI SMILES (구조 반영) + MD RMSD (stability proxy) + H-06 disclaimer (외삽 경고)
```

| 항목 | 내용 |
|------|------|
| 장점 | 도메인 적합도 보장, 명확한 disclaimer 운영 가능 |
| 단점 | 라우팅 로직 구현 필요 (~200 LOC), 모든 도메인에 적합 도구 없음 |
| 우리 프로젝트 | **권장** — H-06 가드와 직결 |

#### 옵션 4: Stacked ensemble (메타 학습)

각 도구 출력을 feature로 메타 모델 학습.

| 항목 | 내용 |
|------|------|
| 장점 | 이론적으로 최고 성능 |
| 단점 | 메타 학습 데이터 필요 (우리 후보에 대한 실측값 최소 50~100건) |
| 한계 | **현재 wet-lab 실측 없음 → 적용 불가** |
| 우리 프로젝트 | **장기 후보** (wet-lab 결과 축적 후) |

#### 옵션 5: 다수결 (카테고리: stable/unstable)

TPP-B (≥24h) / TPP-C (≥72h) 기준 binary 분류 후 다수결.

| 항목 | 내용 |
|------|------|
| 장점 | 단위 통일 불필요, 해석 직관적 |
| 단점 | 정보 손실 (수치 → binary), pepMSND는 이미 binary이나 다른 도구는 연속값 |
| 우리 프로젝트 | **보조 레이어로 적합** — 최종 판정에 사용 |

#### 우리 프로젝트 추천 옵션: **옵션 3 (도메인 분리) + 옵션 5 (binary 다수결) 결합**

```
1단계: 옵션 3 라우팅으로 도구 선택 (후보 유형별)
2단계: 선택된 도구들의 예측값 → TPP-B/TPP-C 기준 binary 변환
3단계: 옵션 5 다수결로 최종 stable/unstable 판정
4단계: H-06 disclaimer 자동 첨부 (D-AA, DOTA 구조는 외삽 경고)
```

이 구조는 현재 구현 가능하며, `pharmacology_guards.py`의 ENDPOINT_CONFIDENCE + HEURISTIC_FUNCTION_DISCLAIMERS 체계와 직접 연동된다.

---

### 2.3 D-AA 처리 전략

#### 현재 갭

모든 기존 도구 (ProtParam, HLP, PlifePred, HLE regression)는 **L-AA만 지원**. D-AA 입력 시 L-AA로 처리하거나 오류 발생. A-02 문서 기준 D-AA 후보에서 **L-AA 도구가 4.83× 과대 추정**하는 것으로 확인됨.

#### 전략 A: pepMSND 우선 사용 (현실적 단기 전략)

- pepMSND는 D-치환 (D-residue replacement) 명시 지원.
- cyclic peptide 107건 학습 데이터 포함.
- GitHub: https://github.com/hmenghu/PepMSND (Digital Discovery 2025)
- AUC 0.912, Acc 0.867 (635 samples).
- **로컬 설치 가능 여부 확인 필요** (웹 서버 외 GitHub 코드 확인).
- 한계: PEG/DOTA 복잡 수식 제외.

#### 전략 B: ADMET-AI 또는 FP-ADMET SMILES 우회

- D-아미노산 포함 펩타이드의 SMILES를 RDKit으로 생성하면 D-배치 구조 반영.
- ADMET-AI/FP-ADMET은 SMILES 입력을 그대로 처리 → D-AA 구조적 차이 반영 가능성.
- **단점**: 소분자 훈련 데이터이므로 펩타이드 도메인 외삽. H-06 disclaimer 필수.
- DOTA 포함 SMILES도 이론상 처리 가능.

#### 전략 C: PEPlife2 기반 자체 학습 (중기)

- PEPlife2 (4,412항목, 2025 bioRxiv): 213건이 D-AA 포함 혼합 배치.
  - URL: https://webs.iiitd.edu.in/raghava/peplife2/ (REST API 제공)
- 이 데이터로 D-AA 처리 가능 회귀 모델 학습 가능.
- 학습 프레임워크: Chemprop v2 (SMILES 기반) 또는 HELM-BERT fine-tuning.
- **예상 ROI**: MEDIUM — 213건 D-AA 데이터로 충분한 일반화 어려울 수 있음.
- 필요 시 논문 저자에게 추가 데이터 요청.

#### 전략 D: MD 시뮬레이션 (가장 정확, 가장 느림)

서호성 박사 권고: "Modification 후에는 MD(RMSD)로 Stability 예측."
- OpenMM 또는 GROMACS로 D-AA + SS bond + DOTA 구조 MD 실행.
- 1~10 ns 시뮬레이션에서 RMSD, RMSF, 이황화결합 유지 여부 확인.
- H100 1장 기준: 1 ns = 약 2~10분 (펩타이드 크기 ~1500 원자).
- **현실적 단기 사용**: 최종 후보 5~10개에 대해 50 ns MD → stability 순위화.

**단기 권고 우선순위**: 전략 A (pepMSND) → 전략 B (SMILES 우회, H-06) → 전략 D (MD, top 후보만)

---

### 2.4 SS bond + DOTA 킬레이터 처리 전략

#### 현재 갭

모든 도구가 표준 AA 서열 입력 기반. DOTA (DOTAGAa 킬레이터) 처리 도구 없음. SS bond는 pepMSND가 일부 지원 (disulfide binding sites 입력 필드).

#### 우회 전략

| 구조 | 전략 | 도구 |
|------|------|------|
| SS bond (Cys3-Cys14) | pepMSND 웹 인터페이스의 "disulfide bond binding sites" 입력 필드 활용 | pepMSND |
| SS bond | SMILES에 S-S 브릿지 명시 → ADMET-AI/FP-ADMET | ADMET-AI, FP-ADMET |
| DOTA 킬레이터 | DOTA-펩타이드 SMILES 생성 (RDKit) → ADMET-AI | ADMET-AI (외삽 경고) |
| SS bond + DOTA 동시 | MD 시뮬레이션 (유일한 실질적 대안) | OpenMM/GROMACS |
| 전체 구조 | AlphaFold3 구조 예측 → 구조 기반 안정성 프록시 | AlphaFold3 (별도) |

#### DOTA에 대한 현실적 입장

DOTA 킬레이터가 결합된 펩타이드의 혈청 안정성을 예측하는 공개 AI 도구는 현재 **존재하지 않는다** (2026-05-20 기준 조사 결과). DOTA 결합 위치에 따라 펩타이드의 구조와 프로테아제 접근성이 달라지므로:

1. DOTA 없는 펩타이드로 예측 → H-06 disclaimer 첨부 ("DOTA 미포함 예측값")
2. SMILES 기반 도구로 DOTA 포함 구조 처리 → 외삽 경고 (H-06)
3. MD 시뮬레이션 → 유일한 구조 반영 방법

---

## Part 3. 시스템 통합 권고

### 3.1 최단 경로 (5/28 회의 전까지)

#### 권고 시스템: "3-Layer Ensemble + 자동 disclaimer"

```
Layer 1 (즉시 적용 가능, L-AA 후보):
  도구: PlifePred + HLE regression + pepADMET HBM (웹 API)
  출력: t½ (분/시간) 연속값 3개 → 가중 평균 (R² 기반: 0.743 / 0.78 / 0.90)
  → TPP-B/C 판정

Layer 2 (D-AA / 환형 후보):
  도구: pepMSND (primary) + PlifePred modified mode (보조)
  출력: binary (stable/unstable) + t½ 참고값
  → H-06 disclaimer: "D-AA 처리 모델, 학습 데이터 213건, 외삽 신뢰도 MEDIUM"

Layer 3 (DOTA 포함 최종 후보 top-5):
  도구: ADMET-AI SMILES (구조 반영) + MD stability proxy (RMSD)
  출력: 구조 기반 stability 점수
  → H-06 disclaimer: "소분자 훈련 데이터 기반, DOTA 특화 검증 없음"
```

#### pharmacology_guards.py 등록 형식

```python
# 추가 항목 (예시)
ENDPOINT_CONFIDENCE = {
    ...
    "serum_halflife_plifepred": {
        "grade": "P2",
        "r2_literature": 0.743,
        "d_aa_support": False,
        "cyclic_support": False,
        "dota_support": False,
        "disclaimer_key": "H-06-plifepred"
    },
    "serum_halflife_pepmsnd": {
        "grade": "P2",
        "auc_literature": 0.912,
        "d_aa_support": True,
        "cyclic_support": True,
        "dota_support": False,
        "disclaimer_key": "H-06-pepmsnd"
    },
    "serum_halflife_hle_regression": {
        "grade": "P2",
        "r2_literature": 0.78,
        "d_aa_support": False,
        "cyclic_support": False,
        "dota_support": False,
        "disclaimer_key": "H-06-hle"
    },
    ...
}

HEURISTIC_FUNCTION_DISCLAIMERS = {
    ...
    "H-06-pepmsnd": (
        "pepMSND (AUC=0.912): D-AA 지원 (binary). "
        "DOTA/PEG 수식 미지원. 635 펩타이드 학습, 외삽 경고."
    ),
    "H-06-dota-smiles": (
        "ADMET-AI SMILES 기반: DOTA 구조 포함 가능하나 "
        "소분자 훈련 데이터 기반. 펩타이드 반감기 미검증. 참고용."
    ),
}
```

#### 예상 작업량

| 작업 | 위임 대상 | 예상 시간 |
|------|---------|---------|
| pepMSND GitHub 로컬 설치 확인 | engineer-infra | 1~2시간 |
| pepMSND wrapper (`predict_halflife_pepmsnd.py`) 업데이트 | codex | 1시간 |
| ADMET-AI SMILES 래퍼 신규 작성 | codex | 2시간 |
| pharmacology_guards.py ENDPOINT_CONFIDENCE 추가 | codex | 1시간 |
| 라우팅 로직 (후보 유형 → 도구 선택) | engineer-backend | 3시간 |
| SST-14 벤치마크 세트 검증 (4개 펩타이드) | reviewer-science | 2시간 |
| **합계** | | **10~11시간** |

**5/28 회의 전 현실적 목표**: Layer 1 + Layer 2 완성 (Layer 3는 MD 시뮬레이션 시간 필요로 다음 단계).

---

### 3.2 중장기 경로 (5/28 이후)

#### 자체 학습 모델 (ROI MEDIUM)

**조건 충족 시 진행:**
1. PEPlife2 데이터 (4,412항목) REST API로 전체 다운로드
2. D-AA 항목(213건) + 환형 항목 별도 분리
3. SMILES 변환 → Chemprop v2 또는 HELM-BERT fine-tuning
4. 우리 후보 4개 벤치마크로 검증 (SST-14, Octreotide, Lanreotide, RC-160)

**예상 일정**: 2~3주 (데이터 준비 1주 + 학습/검증 1~2주)

#### pepADMET 반감기 endpoint 자체 재구현

데이터 필요 (저자 요청 또는 PEPlife2 대체):
- 저자 연락: Prof. Jie Dong (jiedong@csu.edu.cn) — HBM 187건 데이터 요청
- HBM 데이터 확보 시: Train.ipynb 구조 재활용 → H100 학습 2~6시간
- **ROI**: HIGH (문헌 R²=0.90, 수식 펩타이드 특화) — **데이터 확보가 관건**

---

### 3.3 실험 측정 병행 권고

서호성 박사 권고 이행 방안:

#### In vitro 혈청 안정성 assay

| Assay | 방법 | 비용 추정 | 소요 시간 | 결과물 |
|-------|------|---------|---------|--------|
| 혈청 안정성 (HPLC-MS) | 0.1~1 μg 펩타이드 + 인간 혈청 37°C 배양 → 0, 15, 30, 60, 120, 240분 HPLC-MS | 후보당 50~200만원 | 3~5 영업일 | t½ (분), 절단 부위 |
| 마우스 혈청 안정성 | 동일 방법, 마우스 혈청 | 후보당 30~100만원 | 동일 | t½ (분) |

**권고 타이밍**: 최종 후보 3~5개 선정 후 → 5/28 회의 이전 합성 의뢰 시 연동 가능.

**계산 모델 vs 실측 상관관계 구축**: 실측 t½ 데이터가 축적되면 Stacked ensemble (옵션 4) 학습 데이터로 활용 가능 → **장기적 시스템 품질 향상**.

---

## 검증 필요 / 미확인 항목

- [ ] **pepMSND GitHub 로컬 설치 가능 여부**: https://github.com/hmenghu/PepMSND — conda 환경, PyTorch 버전 확인 필요
- [ ] **pepADMET HBM endpoint 웹 API 접근 가능 여부**: pepadmet.ddai.tech 웹 서비스 안정성 및 batch 처리 가능 여부 (TOS 확인 포함)
- [ ] **PEPlife2 REST API 실사용 가능 여부**: https://webs.iiitd.edu.in/raghava/peplife2/ — 전체 4,412항목 다운로드 가능 여부 확인
- [ ] **pepADMET 저자 (jiedong@csu.edu.cn) 에게 HBM 학습 데이터 요청 타당성**: 공동연구 또는 데이터 공유 협의
- [ ] **ADMET-AI SMILES 처리 시 D-AA 펩타이드 실제 성능**: SST-14 변형 후보로 실증 테스트 필요
- [ ] **pepMSND disulfide bond 입력 필드 실사용 방법**: 웹 인터페이스 확인 필요 (로컬 코드에 동일 옵션 있는지)
- [ ] **HLE regression Cavaco 2021 소프트웨어 배포 URL**: 논문에 Electron 앱 언급, 실제 다운로드 링크 미확인 (a9423fe commit 에서 이미 구현 완료 여부 확인 필요)
- [ ] **MD 시뮬레이션 세팅**: DOTA-Ga 킬레이터의 force field 파라미터 (GAFF2 또는 CHARMM CGenFF) 존재 여부

---

## 참고 자료

1. Tan X et al. 2026. "pepADMET: a novel computational platform for systematic ADMET evaluation of peptides." *J. Chem. Inf. Model.* DOI: 10.1021/acs.jcim.5c02518
2. Tan X et al. 2024. "Introducing enzymatic cleavage features and transfer learning realizes accurate peptide half-life prediction across species and organs." *Briefings in Bioinformatics* 25(4): bbae350. DOI: 10.1093/bib/bbae350
3. Mathur D et al. 2018. "In silico approaches for predicting the half-life of natural and modified peptides in blood." *PLOS One*. DOI: 10.1371/journal.pone.0196829. PMC: PMC5983457
4. Cavaco M et al. 2021. "Estimating peptide half-life in serum from tunable, sequence-related physicochemical properties." *Clin. Transl. Sci.* PMC: PMC8301568
5. Meng H et al. 2025. "PepMSND: integrating multi-level feature engineering and comprehensive databases to enhance in vitro/in vivo peptide blood stability prediction." *Digital Discovery*. DOI: 10.1039/D5DD00118H
6. Swanson K et al. 2024. "ADMET-AI: a machine learning ADMET platform for evaluation of large-scale chemical libraries." *Bioinformatics*. PMC: PMC11226862
7. Oliwa T et al. 2023. "Sequence-based prediction of the intrinsic solubility of peptides containing non-natural amino acids." *Nat. Commun.* PMC: PMC10656490 (CamSol-PTM)
8. PEPlife2 (2025). bioRxiv. DOI: 10.1101/2025.05.13.653654. URL: https://webs.iiitd.edu.in/raghava/peplife2/
9. pepADMET GitHub: https://github.com/ifyoungnet/pepADMET (accessed 2026-05-20)
10. pepMSND GitHub: https://github.com/hmenghu/PepMSND (accessed 2026-05-20)
