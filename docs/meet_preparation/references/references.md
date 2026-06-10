# References — 2026-06-01

> 검증 기준: 공식 URL fetch 성공(HTTP 200) 또는 PubMed/arXiv/GitHub 직접 확인  
> 접근 확인일: 2026-06-01  
> 할루시네이션 방지: 존재하지 않는 DOI/URL 없음. 미검증 항목은 §근거 부족으로 분리.

---

## 검증 통과 (출처 확인됨)

---

### A-02: 혈청 반감기 예측 도구

---

#### [R01] ProtParam (ExPASy)

- 종류: 웹 도구
- URL: https://web.expasy.org/protparam/
- 제공 기관: SIB Swiss Institute of Bioinformatics (ExPASy)
- 접근 확인: 2026-06-01, HTTP 200 (페이지 정상 렌더링)
- 검증 방법: WebFetch — 페이지 제목 "Expasy - ProtParam", SIB 로고·UniProtKB 연동 확인
- 기능: 분자량, theoretical pI, 아미노산 조성, 소광계수, estimated half-life, Instability Index, Aliphatic Index, GRAVY 산출
- Action Item 매핑: A-02 (반감기 추정 1차 도구)
- 신뢰도: 高 (Swiss-Prot 공식, 수십 년 운영)

---

#### [R02] PlifePred

- 종류: 웹 서버 (IIITD Raghava 그룹)
- URL: https://webs.iiitd.edu.in/raghava/plifepred/
- 논문: Mathur D, Singh S, Mehta A, Agrawal P, Raghava GPS. "In silico approaches for predicting the half-life of natural and modified peptides in blood." PLoS ONE 13(6): e0196829 (2018). DOI: 10.1371/journal.pone.0196829
- 접근 확인: 2026-06-01, WebFetch 성공 — 기능 페이지 정상, 논문 DOI 링크 활성
- 검증 방법: WebFetch + PubMed ID 29856745 교차 확인
- 기능: 혈중(mammalian blood) 펩타이드 반감기 예측 — 자연 펩타이드 서열 기반 3개 모듈 + 변형 펩타이드 구조 기반 2개 모듈; 단일 치환 돌연변이체 전수 스캔
- 성능: 43 PaDEL descriptor 모델 기준 r=0.692 (예측값 vs 실험값)
- Action Item 매핑: A-02
- 신뢰도: 高 (peer-reviewed, PubMed 등재)

---

#### [R03] HLP (Half-Life Prediction — 장내 환경)

- 종류: 웹 서버 (IIITD Raghava 그룹)
- URL: https://webs.iiitd.edu.in/raghava/hlp/
- 논문: Sharma A, Singla D, Rashid M, Raghava GPS. "Designing of peptides with desired half-life in intestine-like environment." BMC Bioinformatics 15:282 (2014). DOI: 10.1186/1471-2105-15-282
- 접근 확인: 2026-06-01, WebFetch 성공 — 페이지 정상, 3개 모듈 확인
- 검증 방법: WebFetch + PubMed ID 25141912 교차 확인
- 기능: 장내 프로테아제 환경(intestine-like)에서 반감기 예측; 단일 돌연변이체 스캔으로 최적 변이 선별
- 참고: PlifePred(혈중)와 상보적 — 경구 투여 검토 시 추가 활용
- Action Item 매핑: A-02
- 신뢰도: 高 (peer-reviewed, BMC 등재)

---

#### [R04] N-end Rule (Bachmair et al. 1986)

- 종류: 기초 생화학 규칙 (원전 논문)
- 논문: Bachmair A, Finley D, Varshavsky A. "In vivo half-life of a protein is a function of its amino-terminal residue." Science 234(4773):179–186 (1986). DOI: 10.1126/science.3018930
- PubMed ID: 3018930
- Semantic Scholar URL: https://www.semanticscholar.org/paper/In-vivo-half-life-of-a-protein-is-a-function-of-its-Bachmair-Finley/55fe00631b806277f43c7547acad1961453872ed
- 검증 방법: PubMed ID 확인 + Science.org DOI 확인 + Semantic Scholar 페이지 확인
- 핵심 내용: N말단 잔기 종류에 따라 단백질 in vivo 반감기가 3분~20시간 이상으로 결정; 유비퀴틴 시스템과 연계된 프로테아제 인식 규칙
- Action Item 매핑: A-02 (N말단 설계 근거)
- 신뢰도: 高 (Science 원전, 1986년 이래 수천 회 인용)

---

#### [R05] PeptideRanker

- 종류: 웹 서버 (University College Dublin)
- URL: http://distilldeep.ucd.ie/PeptideRanker/
- 논문: Mooney C, Haslam NJ, Pollastri G, Shields DC. "Towards the improved discovery and design of functional peptides: common features of diverse classes permit generalized prediction of bioactivity." PLoS ONE 7(10): e45012 (2012). PMID: 23056189
- 검증 방법: WebSearch — UCD 도메인 확인, ResearchGate/PubMed 교차 확인 성공; WebFetch timeout (서버 응답 느림)
- 기능: N-to-1 신경망 기반 펩타이드 생물활성 확률 예측 (0~1 점수); 20aa 미만 short peptide 전용 predictor 자동 적용
- 주의: 서버 응답이 느릴 수 있음 — timeout 경험됨. 본 도구는 반감기가 아닌 bioactivity 예측 도구임을 주의
- Action Item 매핑: A-02 (활성 스크리닝 보조)
- 신뢰도: 中 (논문 확인됨, 서버 응답 불안정)

---

### A-03: Fab-ADMET / pepADMET

---

#### [R06] pepADMET

- 종류: GitHub repo + 웹 서버
- GitHub: https://github.com/ifyoungnet/pepADMET
- 웹 서버: https://pepadmet.ddai.tech/documentation/
- 논문: Tan X et al. "pepADMET: a novel computational platform for systematic ADMET evaluation of peptides." J Chem Inf Model (2025/2026). DOI: 10.1021/acs.jcim.5c02518
- 접근 확인: 2026-06-01, GitHub WebFetch 성공 — repo 존재, 23 stars, GPL-3.0, Python/Jupyter 코드
- 검증 방법: GitHub WebFetch + ACS 검색 결과 교차 확인
- 기능: 선형·고리형·변형 펩타이드 19개 ADMET 엔드포인트 예측; 36,643개 데이터 학습; GNN + RGCN 아키텍처
- Action Item 매핑: A-03
- 신뢰도: 中-高 (논문 ACS 등재, repo 활성)

---

#### [R07] ADMET-AI (Swanson et al.)

- 종류: Python 패키지 + 웹 서버
- GitHub: https://github.com/swansonk14/admet_ai
- 웹 서버: https://admet.ai.greenstonebio.com/
- 논문: Swanson K et al. "ADMET-AI: a machine learning ADMET platform for evaluation of large-scale chemical libraries." Bioinformatics 40(7): btae416 (2024). DOI: 10.1093/bioinformatics/btae416. PMC11226862
- 접근 확인: 2026-06-01, GitHub WebFetch 성공 — 313 stars, MIT License, 최신 릴리스 v_2.0.1 (2026-02-22)
- 검증 방법: GitHub WebFetch + PubMed/Oxford Academic 교차 확인
- 기능: TDC ADMET Leaderboard 최고 평균 순위; Chemprop 기반; 소분자 중심 (펩타이드 적용 범위 검토 필요)
- 주의: 소분자 중심 설계 — SST14 analogues에는 pepADMET(R06)가 더 적합할 수 있음
- Action Item 매핑: A-03
- 신뢰도: 高 (Bioinformatics 등재, Stanford 그룹)

---

#### [R08] ADMETlab 3.0

- 종류: 웹 서버
- URL: https://admetlab3.scbdd.com/
- 제공 기관: Xiangya School of Pharmaceutical Sciences, Central South University
- 접근 확인: 2026-06-01, WebFetch 성공 — "ADMETlab 3.0" 타이틀, 2024-01-31 업데이트, 119개 엔드포인트 확인
- 검증 방법: WebFetch 직접 확인
- 기능: 119개 예측 엔드포인트; DMPNN 기반; 불확실성 정량 기능; API 제공
- Action Item 매핑: A-03
- 신뢰도: 高 (공식 도메인, 활성 서비스)

---

### A-04, A-05: 복합 스코어링 + MM-GBSA/FEP

---

#### [R09] pymoo (Multi-objective Optimization — NSGA-II 포함)

- 종류: Python 라이브러리
- URL: https://pymoo.org/
- GitHub: https://github.com/anyoptimization/pymoo
- 논문: Blank J, Deb K. "pymoo: Multi-objective Optimization in Python." IEEE Access 8:89497-89509 (2020). arXiv:2002.04504
- 접근 확인: 2026-06-01, WebFetch 성공 — 버전 0.6.1.6, NSGA-II 공식 지원 확인
- 검증 방법: 공식 문서 WebFetch + arXiv 검색
- 기능: NSGA-II, NSGA-III, MOEA/D 등; Pareto front 시각화; 성능 지표 (GD, IGD, Hypervolume)
- Action Item 매핑: A-04 (복합 스코어링 Pareto 최적화)
- 신뢰도: 高 (IEEE Access 등재, 활성 유지)

---

#### [R10] gmx_MMPBSA

- 종류: Python 도구 (GROMACS + AMBER MMPBSA.py 연동)
- GitHub: https://github.com/Valdes-Tresanco-MS/gmx_MMPBSA
- 논문: Valdés-Tresanco MS et al. "gmx_MMPBSA: A New Tool to Perform End-State Free Energy Calculations with GROMACS." J Chem Theory Comput 17(10):6281-6291 (2021). DOI: 10.1021/acs.jctc.1c00645
- 접근 확인: 2026-06-01, GitHub WebFetch 성공 — 311 stars, GPL-3.0, 최신 릴리스 v1.6.5 (2026-05-23), 총 2,185 커밋
- 검증 방법: GitHub WebFetch 직접 확인
- 기능: MM-GBSA/MM-PBSA end-state 자유에너지; GROMACS 모든 버전 + AmberTools>=20 호환; Amber/OPLS/CHARMM force field 지원
- Action Item 매핑: A-05 (MM-GBSA 재채점)
- 신뢰도: 高 (JCTC 등재, 활성 개발 중)

---

#### [R11] OpenMM

- 종류: 분자 시뮬레이션 라이브러리
- URL: https://openmm.org/
- GitHub: https://github.com/openmm/openmm
- 접근 확인: 2026-06-01, WebFetch 성공 — "High performance, customizable molecular simulation", Copyright 2017-현재
- 검증 방법: 공식 URL WebFetch
- 기능: GPU 가속 MD 시뮬레이션; FEP 워크플로 지원; Python API
- Action Item 매핑: A-05 (MD/FEP 기반 자유에너지)
- 신뢰도: 高 (광범위하게 사용되는 공식 오픈소스 라이브러리)

---

#### [R12] OpenFE (Open Free Energy)

- 종류: Python 라이브러리 (alchemical FEP)
- URL: https://openfree.energy/
- GitHub: https://github.com/OpenFreeEnergy/openfe
- 문서: https://docs.openfree.energy/
- 접근 확인: 2026-06-01, WebSearch — v1.0 stable release (2024-05-03) 확인; GitHub 페이지 존재
- 검증 방법: WebSearch + GitHub 확인 (openfree-energy.org → openfree.energy 도메인 변경 주의)
- 기능: alchemical FEP 계산 자동화; OMSF 비영리 컨소시엄 운영; MIT License
- 주의: 당초 제시된 URL https://openfree-energy.org/ 은 도메인 변경됨 — 현행 URL: https://openfree.energy/
- Action Item 매핑: A-05
- 신뢰도: 高 (pharmaceutical 컨소시엄 지원)

---

### A-06: 디퓨전 도킹

---

#### [R13] DiffDock

- 종류: GitHub repo (MIT License)
- GitHub: https://github.com/gcorso/DiffDock
- 논문: Corso G, Stärk H, Jing B, Barzilay R, Jaakkola T. "DiffDock: Diffusion Steps, Twists, and Turns for Molecular Docking." ICLR 2023. arXiv:2210.01776
- 접근 확인: 2026-06-01, GitHub WebFetch 성공 — 1.5k stars, MIT License, 최신 릴리스 v1.1.3 (2024-09-04)
- 검증 방법: GitHub WebFetch + arXiv 2210.01776 검색 확인
- 기능: diffusion 생성 모델 기반 리간드 포즈 예측; PDBBind top-1 성공률 38% (RMSD<2Å); DiffDock-L (2024-02) 개선판 포함
- Action Item 매핑: A-06
- 신뢰도: 高 (ICLR 2023 발표, MIT, 활성 유지)

---

#### [R14] Boltz-2 (jwohlwend/boltz)

- 종류: GitHub repo (MIT License)
- GitHub: https://github.com/jwohlwend/boltz
- 논문 (Boltz-2): Wohlwend J et al. "Boltz-2: Towards Accurate and Efficient Binding Affinity Prediction." bioRxiv 2025.06.14.659707 (2025). URL: https://www.biorxiv.org/content/10.1101/2025.06.14.659707
- PMC (Boltz-2): PMC12262699
- 접근 확인: 2026-06-01, GitHub WebFetch 성공 — MIT License, v2.2.1 (2025-09-08), 437 커밋, Boltz-1(2024-11-19) + Boltz-2(2025-06-14) 모두 포함
- 검증 방법: GitHub WebFetch + bioRxiv + PMC 교차 확인
- 기능: 구조 예측 + binding affinity 예측 통합; FEP 대비 1000배 빠른 속도; CASP16 affinity track 1위; MF-PCBA 벤치마크 최고 성능
- Action Item 매핑: A-06
- 신뢰도: 高 (MIT, 활성 개발, preprint → PMC 등재)

---

#### [R15] AlphaFold3

- 종류: 모델/논문 (Deepmind/Google)
- 논문: Abramson J et al. "Accurate structure prediction of biomolecular interactions with AlphaFold 3." Nature 630(8016):493-500 (2024). DOI: 10.1038/s41586-024-07487-w
- 서버: https://alphafoldserver.com/ (비상업적 무료 접근)
- GitHub (inference code): https://github.com/google-deepmind/alphafold3
- 검증 방법: WebSearch — Nature DOI 확인, Princeton 협업 페이지, Addendum DOI 10.1038/s41586-024-08416-7 확인
- 기능: 단백질·핵산·소분자·이온·변형 잔기 복합체 구조 예측; 도킹 포함
- Action Item 매핑: A-06
- 신뢰도: 高 (Nature 2024, DeepMind 공식)

---

### A-07: GPU 인프라

---

#### [R16] NVIDIA H100 공식 사양 페이지

- 종류: 공식 제품 페이지
- URL: https://www.nvidia.com/en-us/data-center/h100/
- 접근 확인: 2026-06-01, WebFetch 성공 — H100 SXM(80GB/3.35TB/s, 700W) + H100 NVL(94GB/3.9TB/s) 사양 확인
- 검증 방법: 공식 nvidia.com URL WebFetch
- Action Item 매핑: A-07 (H100 사양 근거)
- 신뢰도: 高 (NVIDIA 공식)

---

### §2.1 인용 논문 (회의록)

---

#### [R17] Gervasoni et al. 2023 (JCIM — SSTR2 radiopharmaceutical MD)

- 논문: Gervasoni S, Öztürk I, Guccione C, Bosin A, Ruggerone P, Malloci G. "Interaction of Radiopharmaceuticals with Somatostatin Receptor 2 Revealed by Molecular Dynamics Simulations." J Chem Inf Model 63(15):4924-4933 (2023). DOI: 10.1021/acs.jcim.3c00712
- PMC: PMC10428218
- PubMed: https://pubmed.ncbi.nlm.nih.gov/ (PMCID PMC10428218로 접근)
- 접근 확인: 2026-06-01, WebSearch — ACS 공식 페이지 + PMC 직접 확인
- 검증 방법: ACS Publications DOI + PubMed Central PMC10428218 교차 확인
- 핵심 내용: 6종 방사성의약품(64Cu/68Ga-DOTATATE, 68Ga-DOTATOC, 64Cu-SARTATE, 68Ga-DOTANOC, 64Cu-TETATATE)의 SSTR2 상호작용을 MD로 분석; 펩타이드·핵종·킬레이터 각 부분의 기여 규명
- Action Item 매핑: 회의록 §2.1 (선행 연구)
- 신뢰도: 高 (JCIM 2023, PMC 공개 접근)

---

#### [R18] Gervasoni et al. 2024 (CSBJ — SSTR selectivity MD)

- 논문: Gervasoni S et al. "Exploring key features of selectivity in somatostatin receptors through molecular dynamics simulations." Comput Struct Biotechnol J (CSBJ) (2024). DOI: 10.1016/j.csbj.2024.03.005
- PMC: PMC11630666
- 접근 확인: 2026-06-01, WebSearch — CSBJ 공식 페이지(csbj.org) + ScienceDirect + PMC 동시 확인
- 검증 방법: CSBJ DOI + ScienceDirect + PMC11630666 교차 확인 (open access)
- 핵심 내용: 5종 SSTR 전체에 대한 μs-scale multi-copy MD; SSTR2 선택성 = 소수성 서브포켓 상호작용; W8 변형으로 SSTR4 선택성 향상; SST14-analogue 설계 가이드라인 제공
- Action Item 매핑: 회의록 §2.1 (선행 연구)
- 신뢰도: 高 (CSBJ 2024, PMC 공개 접근)

---

### Radiolysis Quencher

---

#### [R19] Lutathera FDA 처방 정보 (DailyMed)

- 종류: FDA 승인 처방 정보 (공식 라벨)
- URL: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=72d1a024-00b7-418a-b36e-b2cb48f2ab55
- NDA: 208700 (최초 2018년 승인, 최근 업데이트 2026-01-15)
- 접근 확인: 2026-06-01, WebFetch 성공 — gentisic acid 0.63 mg/mL + ascorbic acid 2.8 mg/mL 비활성 성분 확인
- 검증 방법: NIH DailyMed WebFetch 직접 확인 (FDA 공식 라벨 소스)
- 핵심 내용: Lutathera (lutetium Lu 177 dotatate) 제형에 radiolysis quencher로 겐티스산(0.63 mg/mL)과 아스코르브산(2.8 mg/mL) 포함; SSTR+ 위장췌장 신경내분비종양 치료제
- Action Item 매핑: 회의록 (radiolysis quencher 근거)
- 신뢰도: 高 (FDA 공식 처방 정보, NIH DailyMed)

---

## 근거 부족 / 제외 후보

---

#### [X01] PeptideStability (ML) — 명칭 불명확

- 검색 결과: "PeptideStability"라는 특정 도구명으로 공식 GitHub/논문/웹서버 미발견
- 유사 도구: PlifePred(R02), HLP(R03), PepCalc 등 다수 존재하나 "PeptideStability"와 동일 여부 불확실
- 결정: 인용 제외 — 정확한 도구명/저자/URL 확보 후 재검토 필요
- 대안: R02 (PlifePred) 또는 R03 (HLP) 사용 권고

---

#### [X02] distilledcs.ucd.ie/PeptideRanker (URL 접속 불가)

- 검색 결과: 논문에서 인용된 URL http://distilledcs.ucd.ie/PeptideRanker/ (혹은 distilldeep.ucd.ie)는 WebFetch timeout
- 상태: 서버 응답 불안정 — 도구 자체는 존재하나 안정적 접근 보장 불가
- 결정: 논문 근거로 [R05]에 포함하되, 서버 안정성 주의 표기. 운영 파이프라인 의존 금지
- 대체 URL 후보: http://bioware.ucd.ie/~compass/biowareweb/Server_pages/peptideranker.html (WebSearch에서 발견, 미검증)

---

#### [X03] NVIDIA DGX B200 공식 사양

- 검색 결과: nvidia.com/en-us/data-center/dgx-b200/ 존재 확인됨 (검색 결과에서 언급), 별도 WebFetch 미수행
- 결정: H100 공식 페이지(R16) 검증 완료. B200은 추가 검증 필요 — 현재 미포함

---

#### [X04] openfree-energy.org (구 URL)

- 상태: 해당 도메인(openfree-energy.org)은 WebFetch ECONNREFUSED — 현행 도메인 변경됨
- 현행 URL: https://openfree.energy/ (WebSearch 검증)
- 결정: [R12]에 현행 URL로 수정 반영. 구 URL 사용 금지

---

## 검증 요약

| # | 도구/자료 | 상태 | Action Item |
|---|---------|------|------------|
| R01 | ProtParam (ExPASy) | 통과 | A-02 |
| R02 | PlifePred | 통과 | A-02 |
| R03 | HLP | 통과 | A-02 |
| R04 | N-end Rule (Bachmair 1986) | 통과 | A-02 |
| R05 | PeptideRanker | 통과 (서버 불안정) | A-02 |
| R06 | pepADMET | 통과 | A-03 |
| R07 | ADMET-AI | 통과 | A-03 |
| R08 | ADMETlab 3.0 | 통과 | A-03 |
| R09 | pymoo (NSGA-II) | 통과 | A-04 |
| R10 | gmx_MMPBSA | 통과 | A-05 |
| R11 | OpenMM | 통과 | A-05 |
| R12 | OpenFE | 통과 (URL 변경) | A-05 |
| R13 | DiffDock | 통과 | A-06 |
| R14 | Boltz-2 | 통과 | A-06 |
| R15 | AlphaFold3 | 통과 | A-06 |
| R16 | NVIDIA H100 공식 | 통과 | A-07 |
| R17 | Gervasoni 2023 JCIM | 통과 | §2.1 |
| R18 | Gervasoni 2024 CSBJ | 통과 | §2.1 |
| R19 | Lutathera FDA DailyMed | 통과 | Radiolysis |
| X01 | PeptideStability (ML) | 제외 | A-02 |
| X02 | PeptideRanker URL 불안정 | 조건부 | A-02 |
| X03 | NVIDIA DGX B200 | 미검증 | A-07 |
| X04 | openfree-energy.org | URL 변경 | A-05 |

**검증 통과: 19개 / 제외·조건부: 4개**
