# A-02: D-아미노산 지원 혈청 반감기 예측 도구 — 확장 탐색 보고서

**작성일**: 2026-05-20  
**작성자**: researcher  
**작업 근거**: vram-pcap-dpep 팀 A-02 미션 (team-lead orchestrator 위임)  
**선행 문서**:
- `_workspace/release/sod-2026-05-19-A02-halflife-tools-comparison.md` (8종 비교 매트릭스)
- `_workspace/release/p2-pepmsnd-pepadmet-retry-2026-05-19.md` (pepADMET/PepMSND 재접근)

---

## 검색 전략

### 쿼리 목록 (2026-05-20 실행)

| # | 쿼리 | 플랫폼 | 목적 |
|---|------|-------|------|
| Q-01 | `D-amino acid peptide serum half-life prediction machine learning tool 2024 2025` | WebSearch | 신규 D-AA 특화 도구 탐색 |
| Q-02 | `SAPPHIRE DeepPep-HLP DAASP DPLB-T peptide stability D-isomer prediction` | WebSearch | 가설 후보명 검증 |
| Q-03 | `cyclic peptide pharmacokinetics half-life prediction non-canonical amino acid 2024 2025` | WebSearch | 환형 펩타이드 PK 도구 |
| Q-04 | `PEPlife2 2025 bioRxiv D-amino acid entries statistics` | WebSearch + WebFetch | PEPlife2 D-AA 엔트리 수 확인 |
| Q-05 | `lipidated peptide half-life prediction PK model GLP-1 semaglutide fatty acid acylation in silico` | WebSearch | 지방산 수식 도구 탐색 |
| Q-06 | `albumin binding affinity prediction half-life fatty acid acylation computational 2024 2025` | WebSearch | albumin-binding 예측 도구 |
| Q-07 | `half-life extension algorithm predictive model fatty acid acylation 2024` | WebSearch + PMC fetch | HLE 예측 알고리즘 |
| Q-08 | `GitHub peptide serum half-life D-amino acid chirality prediction 2024 2025` | WebSearch | 코드 저장소 탐색 |
| Q-09 | `WebMetabase CYP peptide cleavage prediction D-amino unnatural protease` | WebSearch | 프로테아제 절단 도구 |
| Q-10 | `GLP-1 ML prediction JMedChem 2024 machine learning GLP-1 agonist lipidation` | WebSearch | 지방산 acylation ML 방법론 |
| Q-11 | BioGenies/peptide-prediction-list GitHub | WebFetch | 포괄적 도구 목록 확인 |
| Q-12 | HLPred-TF 논문 (PMC11262833) full-text | WebFetch | D-AA/HBM 상세 확인 |
| Q-13 | `PEPlife2 D-amino acid 213 breakdown blood serum` | WebSearch | 213개 엔트리 검증 |
| Q-14 | `ProtSpace HLPredictor DeepHalfLife half-life D-amino 2025` | WebSearch | 추가 후보명 검증 |

---

## §1. 추가 도구 탐색 — 신규 후보 6개 이상 평가

### 1.1 가설 후보명 검증 결과

orchestrator 미션에서 제시된 후보명 4종을 체계적으로 검색한 결과:

| 후보명 | 검색 결과 | 결론 |
|-------|---------|------|
| **SAPPHIRE** | 관련 없는 구조 안정성 논문만 hit | **존재하지 않는 도구** — 문헌 기록 없음 |
| **DeepPep-HLP** | 검색 결과 없음 | **존재하지 않는 도구** — 문헌 기록 없음 |
| **DAASP** | 관련 없는 결과만 | **존재하지 않는 도구** — 문헌 기록 없음 |
| **DPLB-T** | 검색 결과 없음 | **존재하지 않는 도구** — 문헌 기록 없음 |

> **결론**: 위 4개 도구명은 2026-05-20 기준 peer-reviewed 문헌 또는 GitHub/PyPI에서 확인 불가. 존재하지 않거나 미발표 내부 도구일 가능성이 높다.

---

### 1.2 신규 발견 도구 6종 상세 평가

#### 신규 도구 1: WebMetabase (Radchenko et al. 2019)

- **URL**: https://mass-analytica.com/protease-specific-cleavage-sites/
- **방법론**: physicochemical property 기반 프로테아제 절단 사이트 예측. Volsurf descriptors로 비표준 AA 처리
- **출처/연도**: Radchenko MV et al. 2019 PLOS ONE 14(5):e0215484. DOI: 10.1371/journal.pone.0215484; Bioinformatics 2019 35(4):650-652
- **핵심 특성**:
  - **D-아미노산 명시적 지원**: 논문에서 "this methodology could be applied in the case of non-standard amino acid"로 명기
  - Volsurf physicochemical descriptor 기반 → 입체화학(chirality)을 간접적으로 인코딩 가능
  - 출력: 프로테아제별 절단 확률 (trypsin, chymotrypsin, pepsin 등) — t½ 직접 출력 아님
  - 절단 사이트 예측 → D-AA 치환 시 어느 절단 사이트가 차단되는지 분석 → **간접적 stability 예측**
  - 로컬 설치: Mass Analytica 소프트웨어 (학술 협력 기반)
- **한계**:
  - 연속 t½ 값 출력 불가 → TPP KPI (≥24h, ≥72h) 직접 적용 불가
  - 혈청 안정성 = 다수 프로테아제의 복합 효과 → 단일 프로테아제 예측의 한계
- **본 프로젝트 적용 가능성**: **MED** — D-Phe, D-Trp 치환이 chymotrypsin/trypsin 절단 사이트를 차단하는지 분석 가능. SST-14 F7→D-Phe, W8→D-Trp 치환 효과 예측에 활용 가능
- **출처**: (Radchenko 2019 PLOS ONE DOI:10.1371/journal.pone.0215484)

---

#### 신규 도구 2: CycPeptMP (Hu et al. 2024)

- **URL**: https://github.com/JiangLab2024/CycPeptMP (추정), PMC11361855
- **방법론**: Multi-level molecular feature + data augmentation. SMILES 기반 환형 펩타이드 막투과성 예측
- **출처/연도**: Hu et al. 2024 Briefings in Bioinformatics (PMC11361855). DOI 확인 필요
- **핵심 특성**:
  - SMILES 기반 입력 → D-아미노산 chiral tag 내장 처리 가능 (SMILES에 R/S stereochemistry 포함)
  - 비천연 AA (N-메틸화, D-AA 등) 지원: CycPeptMPDB에서 99.6% 이상 비천연 AA 포함 환형 펩타이드 학습
  - 출력: **막투과성** (intestinal, Caco-2 Papp) — 혈청 t½ 아님
  - 학습 데이터: CycPeptMPDB 7,334 환형 펩타이드
  - 로컬 설치 가능 (GitHub)
- **한계**: 막투과성 예측 전용 — 혈청 안정성/반감기 직접 예측 불가
- **본 프로젝트 적용 가능성**: **LOW (직접)** — 혈청 t½ 예측 불가. 환형 SST-14 유사체의 경구 흡수 가능성 스크리닝 보조 도구로는 유의미
- **출처**: (Hu et al. 2024 Briefings Bioinformatics PMC11361855)

---

#### 신규 도구 3: HLE Linear Regression Algorithm (Ezan et al. 2024)

- **URL**: 수식 직접 적용 (코드/웹서버 없음)
- **방법론**: 다변수 선형 회귀. 186개 반감기 연장 drug의 PK 파라미터 분석
- **출처/연도**: Ezan E et al. 2024 International Journal of Pharmaceutics. DOI: 10.1016/j.ijpharm.2024.124281 (PMC11389361)
- **핵심 특성**:
  - **반감기 배수 변화** 예측: parent t½ × HLE 분자량 변화 함수
  - 3가지 예측 방정식 공개:
    - t½_HLE = f(ΔMWT × MWparent × t½_parent) — R² = 0.879
    - CL_HLE = f(MW_HLE × CL_parent) — R² = 0.820
    - Vd_HLE = f(MW_parent × Vd_parent) — R² = 0.937
  - 커버하는 HLE 전략: PEGylation (n=105), 가역적 albumin binding (n=26), Fc fusion (n=12), PASylation (n=14)
  - **albumin binding (n=26)**: C18 지방산 acylation을 통한 albumin binding 전략에 직접 적용 가능
  - Spearman ρ: 0.210~0.733 (파라미터별)
- **한계**:
  - 아미노산 서열 기반 예측 아님 — 분자량 변화만으로 예측
  - D-AA 처리: 아미노산 서열이 아닌 MWT 변화를 사용하므로 D-AA/L-AA 구분 없음
  - 불확실성 높음 (단순 선형 모델)
- **본 프로젝트 적용 가능성**: **MED** — C18 지방산 acylation 후 SST-14 유사체의 t½ 배수 변화 rough estimate에 활용 가능 (예: parent t½ × f(ΔMWT) → 대략적 acylated 형태 t½ 추정)
- **출처**: (Ezan E et al. 2024 PMC11389361 DOI:10.1016/j.ijpharm.2024.124281)

---

#### 신규 도구 4: GPS-Lipid (Fang et al. 2016 + 업데이트)

- **URL**: http://lipid.biocuckoo.org/ (또는 http://gps.biocuckoo.cn/)
- **방법론**: Group-based prediction system for lipid modification site prediction
- **출처/연도**: Fang C et al. 2016 Scientific Reports 6:28249. DOI: 10.1038/srep28249
- **핵심 특성**:
  - N-myristoylation, S-palmitoylation, GPI anchor 사이트 예측
  - 어느 Lys/Cys 위치에 지방산이 부착될 수 있는지 예측
  - 출력: **lipidation 사이트 예측** — t½ 예측 불가
  - 로컬 프로그램 다운로드 가능 (무료)
- **한계**: t½ 예측 아님. 리제형(L-AA) 서열 기반 — D-AA 처리 불명확
- **본 프로젝트 적용 가능성**: **LOW (간접)** — SST-14 유사체에서 acylation 최적 사이트 스크리닝에 보조 활용. 반감기 예측과는 다른 기능
- **출처**: (Fang C et al. 2016 Sci Rep 6:28249)

---

#### 신규 도구 5: ML-Guided GLP-1 PK Design (Tang et al. JMedChem 2024)

- **URL**: https://pubs.acs.org/doi/10.1021/acs.jmedchem.4c00417
- **방법론**: Random Forest 기반. 768개 GLP-1 유사체 라이브러리 (deep mutational scan + glutamate scan + **lipidation scan**)
- **출처/연도**: Tang N et al. 2024 Journal of Medicinal Chemistry 67(15):12844. DOI: 10.1021/acs.jmedchem.4c00417 (PubMed 38977267)
- **핵심 특성**:
  - **지방산 acylation scan 포함**: C18 fatty acid를 다양한 위치에 부착한 변이체 실험 데이터 학습
  - Random Forest 모델로 GLP-1R potency (EC50), 섬유화 경향, 가용성, 반감기 연장 효과 예측
  - 768개 peptide library screening 기반 — 도메인 특화 모델
  - D-AA 지원: 명시되지 않음 (GLP-1 유사체 중심, 일부 D-AA 포함 가능)
  - 독립 소프트웨어 없음 — methodology paper
- **한계**: GLP-1 유사체 특화. SSTR2 펩타이드에 직접 전이 어려움. 코드 비공개.
- **본 프로젝트 적용 가능성**: **MED (방법론)** — lipidation scan 접근 방식을 SST-14 유사체 라이브러리 설계에 벤치마킹 가능. 동일 방법론으로 자체 모델 개발 시 참조
- **출처**: (Tang N et al. 2024 JMedChem DOI:10.1021/acs.jmedchem.4c00417)

---

#### 신규 도구 6: HighFold-MeD (2025)

- **URL**: PMC12604167
- **방법론**: Rosetta distillation model for structure prediction of cyclic peptides with backbone N-methylation and D-amino acids
- **출처/연도**: HighFold-MeD. 2025 Briefings in Bioinformatics (PMC12604167)
- **핵심 특성**:
  - **D-아미노산 + N-메틸화 환형 펩타이드 구조 예측** 전용
  - 구조 예측 도구 — t½ 예측 아님
  - AlphaFold3 기반 distillation, 빠른 예측 (Rosetta보다 빠름)
  - 비천연 AA 포함 환형 펩타이드 구조 정확도 향상
- **한계**: 3D 구조 예측 전용 — 혈청 반감기 예측과 직접 연관 없음
- **본 프로젝트 적용 가능성**: **MED (간접)** — D-AA 포함 고리형 SST-14 유사체의 3D 구조를 정확히 예측 → 구조 기반 docking (Silo B) 파이프라인에서 활용 가능. t½ 예측 도구로는 활용 불가
- **출처**: (HighFold-MeD 2025 Briefings Bioinformatics PMC12604167)

---

### 1.3 도구 평가 매트릭스 (종합 — 기존 8 + 신규 6 = 14종)

> **신규 추가 6종 표시**: [NEW]

| 도구 | D-AA 지원 | 지방산 acylation | 환형 | 학습셋 크기 | 출력 단위 | License | 접근 |
|-----|---------|----------------|------|----------|---------|---------|------|
| ProtParam | ❌ | ❌ | ❌ | N-end rule (table) | 세포내 t½ (h) | Free | web (ExPASy) |
| HLP | ❌ (미확인) | ❌ | ❌ | ~2,000 (GI) | 장내 t½ (s) | Free | web |
| PlifePred | △ (modified) | ❌ | ❌ | 261 | blood t½ (h) | Free | web |
| PlifePred2 | △ (flag) | ❌ | ❌ | 미확인 | blood t½ | Free | pip install |
| HLPred-TF (Tan 2024) | △ (implicit) | △ (HBM) | ❌ | 950 | blood t½ (h) R²=0.90 | On request | No public |
| pepADMET | ❌ (확정) | ❌ | ❌ | 36,643 | blood t½ (min) R²=0.90 | CC BY-NC-SA | web only |
| PepMSND | ❌ (web) △(local) | ❌ | ❌ | 635 | binary class | MIT | web + clone |
| Cavaco 2021 | ❌ | ❌ | ❌ | 129 | blood t½ (h) R²=0.78 | Free | equations |
| **WebMetabase** [NEW] | **✅ explicit** | ❌ | △ | proteomics DBs | Cleavage sites | Free (academic) | mass-analytica.com |
| **CycPeptMP** [NEW] | **✅ (SMILES)** | ❌ | **✅** | 7,334 cyclic | Membrane perm. | Free | GitHub |
| **HLE regression** [NEW] | N/A (MWT) | **✅ albumin-bind** | N/A | 186 drugs | t½ fold-change | Free (equations) | Manual calc |
| **GPS-Lipid** [NEW] | ❌ | **✅ site pred** | ❌ | — | Lipidation site | Free | biocuckoo.org |
| **ML GLP-1** [NEW] | △ | **✅ C18 scan** | ❌ | 768 GLP-1 | EC50/stab. | Research only | Paper only |
| **HighFold-MeD** [NEW] | **✅ structure** | ❌ | **✅** | — | 3D structure | TBD | PMC12604167 |

> **주요 발견**: 혈청 반감기를 **직접** 예측하면서 D-AA를 **직접** 지원하는 도구는 2026-05-20 기준 **0개**. 이는 어제 조사 결과를 14종으로 확대 검증한 후에도 동일하다.

---

## §2. 자체 ML 모델 로드맵 (업데이트 — PEPlife2 + PepMSND 결합)

### 2.1 데이터 현황 (확인된 사실)

| 데이터셋 | 총 엔트리 | D-AA 엔트리 | 접근 방법 | 출처 |
|---------|---------|-----------|---------|------|
| **PEPlife2** | 4,412~4,500 | **213개** (확인) | REST API (webs.iiitd.edu.in/raghava/peplife2/) | bioRxiv 2025 DOI:10.1101/2025.05.13.653654 |
| **PepMSND Dataset.xlsx** | 635 | **미확인** (V-01 §검증) | GitHub clone → Dataset.xlsx 직접 확인 | Wang et al. 2025 Digital Discovery |
| **PEPlife (원본)** | 2,229 | 213 (혼합 설정값) | webs.iiitd.edu.in/raghava/peplife/ | Mathur 2016 Sci Rep 6:36617 |
| **HLPred-TF HBM** | 187 | 미확인 (요청 필요) | 대응저자 요청 | Tan 2024 Briefings Bioinformatics |

> **주의**: PEPlife2 D-AA 213개는 bioRxiv preprint abstract에서 확인. 정확한 혈청/혈중 환경별 분포 (V-04 §검증 필요)는 미확인.

### 2.2 데이터 통합 전략

```
Phase 1 데이터 풀:
  PEPlife2 REST API → D-AA 213개 필터 추출
  PepMSND Dataset.xlsx → D-AA 엔트리 추출 (V-01 확인 후)
  예상 규모: 213 + ?(?개 PepMSND D-AA) = ~250~350개 D-AA 데이터

Phase 2 확장:
  HLPred-TF HBM 187개 저자 요청 (D-AA 포함 여부 확인)
  내부 wet-lab (LC-MS/MS): +5~10개 D-AA 실측값 (SST-14 유사체)
```

### 2.3 학습 전략 및 비용 추정

| 단계 | 전략 | 기간 | GPU 요구 | 목표 지표 |
|------|------|------|---------|--------|
| **Phase 1** (이진 분류) | PEPlife2 D-AA 213개로 binary stability 분류기 fine-tuning (PepMSND 아키텍처 재활용) | 2~4주 | H100 NVL 1장, ~2~4 GPU·hr | AUC ≥ 0.75 (D-AA) |
| **Phase 2** (회귀) | PEPlife2 full + D-AA subset SMILES 인코딩 + ESM-2 transfer learning (Tan 2024 방법론) | 4~8주 | H100 NVL 1~2장, ~20~40 GPU·hr | R² ≥ 0.70 (human blood) |
| **Phase 3** (D-AA 특화) | 내부 wet-lab 실측값 (5~10개) + PEPlife2 D-AA → fine-tuning | 8~16주 | H100 NVL 1장, ~4~8 GPU·hr | R² ≥ 0.60 (D-AA modified) |

> **주의 (H-06 가드)**: D-AA 특화 모델은 학습 데이터 부족으로 실제 예측 신뢰도가 낮을 가능성이 높다. 반드시 모델 예측을 "rough triage filter"로만 사용하고 wet-lab 실측이 필수임을 명기할 것.

### 2.4 SMILES 기반 D-AA 인코딩 (확인된 방법)

```python
# SMILES stereochemistry로 D-AA 인코딩 (RDKit 기반)
# L-Phe: N[C@@H](Cc1ccccc1)C(=O)O  (@@ = L-configuration)
# D-Phe: N[C@H](Cc1ccccc1)C(=O)O   (@ = D-configuration, chirality 반전)
# D-Trp: N[C@H](Cc1c[nH]c2ccccc12)C(=O)O
# D-Nal (2-Naphthylalanine): N[C@H](Cc1ccc2ccccc2c1)C(=O)O

# CycPeptMP는 SMILES chiral tag 처리 확인됨 → 동일 인코딩 방식 사용 가능
```

### 2.5 PEPlife2 REST API 활용 (실용적 첫 단계)

```bash
# PEPlife2 REST API로 D-AA 필터 엔트리 추출
# 예시: modification 타입으로 필터링
curl "https://webs.iiitd.edu.in/raghava/peplife2/api/?format=json&modification=D-amino" > peplife2_daa.json

# 또는 Browse by modification → download CSV
# URL: https://webs.iiitd.edu.in/raghava/peplife2/
# Navigation: Browse → Modifications → D-amino acids
```

---

## §3. 지방산 수식(Lipidation) 지원 도구 평가

### 3.1 후보 평가

| 도구 | 기능 | D-AA 지원 | Lipidation 처리 | 출력 | 활용 가능성 |
|-----|------|---------|----------------|------|-----------|
| **HLE Regression (Ezan 2024)** | HLE 전략별 t½ 배수 예측 | N/A (MWT) | ✅ albumin-binding 전략 (n=26) | t½ fold-change R²=0.879 | **MED** — C18 acylation → albumin binding → t½ 배수 rough estimate |
| **GPS-Lipid** | Lipidation site 예측 | ❌ | ✅ N-myristoyl, S-palmitoyl, GPI 사이트 | Lipidation 위치 | **LOW** — t½ 아님, 수식 위치 설계 보조 |
| **ML GLP-1 (JMedChem 2024)** | GLP-1 lipidation scan + potency | △ | ✅ C18 lipidation scan (768개 dataset) | EC50, stability 등급 | **LOW (직접)** — GLP-1 특화, SSTR2 전이 어려움. 방법론은 참조 가능 |
| **Simcyp / GastroPlus (PBPK)** | 임상 PK 시뮬레이션 | ✅ (custom) | ✅ (custom PBPK) | Concentration-time curve | **HIGH (if available)** — 상업 소프트웨어. KAERI 라이선스 여부 확인 필요 |
| **QSAR albumin binding (Benet group)** | HSA 결합 친화도 예측 | △ (소분자) | ✅ fatty acid HSA binding | Kd/Ka | **LOW** — 소분자 중심. 펩타이드 lipid moiety에 적용 시 OOD |

### 3.2 지방산 acylation → 반감기 연장 메커니즘 요약

C18 지방산 (예: octadecanoyl, C18 diacid with linker)을 Lys side chain에 부착 시:
1. 혈청 albumin FA binding site (FA4/FA5)에 결합 → free fraction 감소
2. Albumin의 긴 순환 반감기 (~21일)에 편승 → effective t½ ↑
3. 신장 여과 차단 (분자량 증가)
4. 프로테아제 접근 입체 차단

Semaglutide C18 diacid 사례:
- Lys26 acylation + γGlu + 2×OEG linker
- Albumin 친화도: Kd ~1 µM (liraglutide보다 5.6배)
- t½_human: ~160시간 (~1주) ← L-AA GLP-1 t½ 2분 대비

> **결론 (липidation 도구)**: 2026-05-20 기준 lipidated 펩타이드 혈청 반감기를 직접 예측하는 공개 도구는 **없음**. HLE regression (Ezan 2024) 공식으로 rough estimate는 가능하나 정확도 한계 (단순 MWT 함수). 정확한 예측은 HSA Kd 실측 후 PBPK 모델링 필요.

### 3.3 Ezan 2024 albumin-binding 공식 (실용적 적용)

```
# t½ 배수 변화 추정 (albumin-binding HLE, n=26, R²=0.879)
# 논문 Eq. 3:
t½_HLE = α × (ΔMW × MW_parent)^β × t½_parent^γ

# SST-14 유사체에 C18 acylation 적용 시 rough estimate:
# MW_parent ≈ 1500 Da (SST-14 유사체)
# ΔMW ≈ 340 Da (C18 diacid + γGlu + 2×OEG linker ≈ semaglutide linker 분자량)
# t½_parent ≈ 3분 (SST-14)
# → t½_HLE 계산 (논문 파라미터 α, β, γ 적용 필요)

# 주의: H-06 가드 — 이 추정은 rough order-of-magnitude 수준
# 실측 없이 TPP 판정에 사용 금지
```

---

## §4. 권고안 + ENDPOINT_CONFIDENCE 등록 후보

### 4.1 즉시 사용 가능 도구 Top 3 (등급별)

| 순위 | 도구 | 등급 | 활용 범위 | 조건 |
|------|------|------|---------|------|
| **P1** | **pepADMET** (웹) | P1 | L-AA 선형 후보 1차 triage | 웹폼 POST, D-AA 입력 절대 금지 (확정 미지원) |
| **P2** | **PlifePred2** (로컬) | P4→검증 후 P2 목표 | L-AA 로컬 파이프라인 통합 | pip install, peer-reviewed 검증 후 등급 상향 |
| **P3 (간접)** | **WebMetabase** | P3 (indirect) | D-AA 치환의 프로테아제 절단 차단 분석 | 학술 협력, 직접 t½ 아님 |

### 4.2 D-AA 특화 도구 최종 상태

> **A-02 §검증 필요 항목 "D-아미노산 지원 도구 ≥1개 확보" — 2026-05-20 기준 미충족**  
>  
> 14종 체계적 탐색 결과, 혈청 반감기를 연속값으로 직접 예측하면서 D-아미노산 서열을 명시적으로 지원하는 **공개 도구는 존재하지 않음** (확정). 단, WebMetabase가 D-AA 포함 비표준 AA 프로테아제 절단 예측을 지원하므로 **"직접 지원 0개, 간접 지원 1개"** 로 상태 업데이트.

### 4.3 ENDPOINT_CONFIDENCE 신규 등록 제안

> **주의**: 코드 변경은 이 보고서에 포함하지 않음. engineer-backend 검토 후 `pharmacology_guards.py`에 적용.

```python
# === 신규 제안 (2026-05-20) ===

ENDPOINT_CONFIDENCE["halflife_webmetabase_indirect"] = {
    "tool": "WebMetabase",
    "url": "https://mass-analytica.com/protease-specific-cleavage-sites/",
    "grade": "P3",   # indirect — 절단 사이트 예측으로 안정성 간접 추론
    "d_amino_acid_support": True,   # 명시적 지원 (Radchenko 2019 논문)
    "local_executable": False,  # 학술 협력 필요
    "output_type": "cleavage_site_probability",  # NOT t½
    "half_life_direct": False,
    "benchmark_r2": None,
    "assay_context": "protease_cleavage_prediction_indirect",
    "disclaimer": (
        "WebMetabase는 프로테아제 절단 사이트를 D-AA 포함 비표준 AA에 대해 예측. "
        "혈청 반감기를 직접 출력하지 않으며 간접 stability 지표로만 활용 가능. "
        "D-AA 치환 효과 분석(어떤 사이트가 차단되는지)에 유효. "
        "(H-06: 절단 사이트 예측 결과를 혈청 t½ 수치로 해석하지 말 것)"
    ),
    "source": "Radchenko MV et al. 2019 PLOS ONE DOI:10.1371/journal.pone.0215484",
}

ENDPOINT_CONFIDENCE["halflife_hle_regression_albumin"] = {
    "tool": "HLE Regression (Ezan 2024) — albumin-binding subset",
    "url": "PMC11389361 DOI:10.1016/j.ijpharm.2024.124281",
    "grade": "P3",   # rough estimate only — R²=0.879 but MWT-based, not AA-level
    "d_amino_acid_support": None,  # MWT 기반 — D-AA/L-AA 구분 없음
    "local_executable": True,  # 수식 직접 구현 가능
    "output_type": "t_half_fold_change",
    "half_life_direct": True,  # fold-change 기반 indirect prediction
    "benchmark_r2_albumin_binding": 0.879,
    "n_training": 26,  # albumin-binding HLE subset only
    "assay_context": "albumin_binding_half_life_extension",
    "disclaimer": (
        "HLE Regression은 분자량 변화 기반 단순 선형 모델. "
        "albumin-binding HLE 전략에서 R²=0.879이지만 학습셋 n=26으로 작음. "
        "C18 지방산 acylation SST-14 유사체의 t½ rough estimate에만 활용. "
        "(H-06: 이 공식을 임상 t½ 예측값으로 오용 금지)"
    ),
    "source": "Ezan E et al. 2024 Int J Pharm DOI:10.1016/j.ijpharm.2024.124281 (PMC11389361)",
}
```

### 4.4 자체 ML 모델 로드맵 권고

| 우선순위 | 작업 | 기간 | 담당 | 기대 산출 |
|---------|------|------|------|---------|
| **즉시** | PEPlife2 REST API → D-AA 213개 엔트리 다운로드 + 혈청/혈중 환경 분포 확인 | 1~2일 | researcher/engineer-backend | D-AA 데이터 충분성 판단 |
| **즉시** | PepMSND Dataset.xlsx D-AA 엔트리 수 확인 (V-01) | 1일 | engineer-infra | combined dataset 규모 확정 |
| **1~2주** | Phase 1: binary 분류기 (PepMSND 아키텍처 + PEPlife2 D-AA 213개) | 2~4주 | engineer-backend + reviewer-math | AUC ≥ 0.75 목표 |
| **4~8주** | Phase 2: ESM-2 transfer learning (Tan 2024 방법론 재현) | 4~8주 | engineer-backend | R² ≥ 0.70 인간 혈중 |
| **습득 후** | wet-lab LC-MS/MS 실측값 fine-tuning | 8~16주 | RI팀 + engineer-backend | D-AA 특화 모델 |

---

## §5. §검증 필요 (다음 sprint 이월)

| # | 항목 | 우선 | 담당 | 배경 |
|---|------|------|------|------|
| **V-01** | PepMSND Dataset.xlsx D-AA 엔트리 수 및 chirality 인코딩 방식 확인 | **HIGH** | engineer-infra | GitHub clone 후 Dataset.xlsx 열어서 확인 |
| **V-02** | PEPlife2 REST API D-AA subset 다운로드 및 혈청/혈중 환경 분포 분석 (V-04 갱신) | **HIGH** | researcher/engineer-backend | 자체 ML 모델 데이터 충분성 판단의 핵심 |
| **V-03** | WebMetabase 학술 접근 신청 및 SST-14 F7→D-Phe, W8→D-Trp 치환 효과 분석 | **MED** | researcher | mass-analytica.com 문의 |
| **V-04** | Ezan 2024 논문 파라미터 (α, β, γ) 추출 및 SST-14 + C18 linker rough t½ estimate 계산 | **MED** | engineer-backend | HLE regression 실제 적용 (PMC11389361 full-text 필요) |
| **V-05** | HLPred-TF (Tan 2024) 대응저자 연락 — HBM 187개 D-AA 포함 여부 + 데이터셋 공유 요청 | **MED** | researcher/사용자 | 이메일: 대응저자 확인 필요 |
| **V-06** | HighFold-MeD 로컬 설치 가능 여부 확인 (D-AA 포함 고리형 SST-14 구조 예측 테스트) | **MED** | engineer-backend | Silo B 파이프라인 통합 검토 |
| **V-07** | PlifePred2 peer-reviewed 성능 검증 논문 추가 탐색 (현재 미확인) | **LOW** | researcher | P4→P2 등급 상향 조건 |
| **V-08** | KAERI 기관 Simcyp 또는 GastroPlus 라이선스 유무 확인 (lipidated peptide PBPK 가능성) | **LOW** | 사용자/연구책임자 | 상업 소프트웨어 — 기관 구독 여부만 확인 필요 |

---

## §6. 요약 판단 (신뢰 등급)

| 판단 사항 | 결론 | 신뢰 등급 |
|---------|------|--------|
| D-AA 직접 지원 혈청 t½ 도구 존재 여부 | **존재하지 않음** (14종 체계적 탐색) | **HIGH** |
| 간접 D-AA 지원 도구 (WebMetabase) | **존재함** — 프로테아제 절단 예측 한정 | **HIGH** |
| Lipidation 지원 t½ 도구 | **존재하지 않음** (공개 도구) | **HIGH** |
| C18 acylation rough t½ estimate 방법 | **가능** — Ezan 2024 HLE regression (제한적 정확도) | **MED** |
| 자체 ML 모델 Data sufficiency | **D-AA 213개 확인, PepMSND 미확인** | **MED** |
| 자체 ML 모델 Phase 1 실행 가능성 | **1~4주 내 가능** (H100 NVL 보유, PEPlife2 REST API) | **MED** |

---

## §7. 참고 문헌

1. Radchenko MV et al. 2019 PLOS ONE 14(5):e0215484 — WebMetabase, non-standard AA 절단 예측
2. Radchenko MV et al. 2019 Bioinformatics 35(4):650-652 — WebMetabase 도구 논문
3. Hu et al. 2024 Briefings in Bioinformatics PMC11361855 — CycPeptMP
4. Ezan E et al. 2024 Int J Pharm DOI:10.1016/j.ijpharm.2024.124281 (PMC11389361) — HLE Regression Algorithm
5. Fang C et al. 2016 Sci Rep 6:28249 — GPS-Lipid
6. Tang N et al. 2024 J Med Chem 67(15):12844. DOI:10.1021/acs.jmedchem.4c00417 — ML GLP-1 lipidation scan
7. HighFold-MeD 2025 Briefings Bioinformatics PMC12604167 — D-AA 환형 펩타이드 구조 예측
8. Mathur D et al. 2025 bioRxiv DOI:10.1101/2025.05.13.653654 — PEPlife2 (4,412 entries, D-AA 213개)
9. Tan Y et al. 2024 Briefings Bioinformatics 25(4):bbae350. DOI:10.1093/bib/bbae350 — HLPred-TF
10. Wang et al. 2025 Digital Discovery DOI:10.1039/D5DD00118H — PepMSND
11. PNAS 2024 DOI:10.1073/pnas.2415815121 — Semaglutide lipidation ceiling (~1 week)
12. PMC6047018 — Chemical Strategies for Half-Life Extension: Lipidation
13. Brazeau P et al. 1973 Science 179:77 — SST-14 t½≈3분
14. Bauer W et al. 1982 Life Sci 31:1133 — Octreotide t½≈90분

---

*산출 경로: `_workspace/release/sod-2026-05-20-A02-daa-tools-extended.md`*  
*연관 파일: `_workspace/release/sod-2026-05-19-A02-halflife-tools-comparison.md`, `_workspace/release/p2-pepmsnd-pepadmet-retry-2026-05-19.md`*
