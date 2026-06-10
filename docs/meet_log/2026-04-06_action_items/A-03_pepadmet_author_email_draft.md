# pepADMET 저자 이메일 초안 — Prof. Jie Dong (Central South University)

## 메타
- **수신자**: jiedong@csu.edu.cn (Prof. Jie Dong, Xiangya School of Pharmaceutical Sciences, CSU)
- **CC**: (KAERI 행정 담당자 / RI팀 공동연구자 추가 필요)
- **발송 시점 권고**: 2026-05-21 ~ 5/25 사이 (회의 5/28 D-3 이전 응답 요청)
- **목적**: HBM 반감기 모델 가중치 + 25 endpoint 학습 데이터 요청 (ROI 최고 항목)
- **작성일**: 2026-05-21 (researcher 초안)
- **참조 파일**:
  - `_workspace/release/pepadmet-author-inquiry-letter-2026-05-20-EN.md` (1차 초안)
  - `_workspace/release/pepadmet-author-inquiry-letter-2026-05-20.md` (한국어 배경)
  - `docs/meet_log/2026-04-06_action_items/A-03_research_pepadmet_environment.md` (로컬 실행 결과)

---

## 1. 영문 본문 (저자 발송용)

---

**Subject**: Academic Data Collaboration Request — pepADMET Half-Life Model Weights and Training Data for SSTR2 Radioligand Peptide Screening (KAERI, Republic of Korea)

---

Dear Prof. Dong,

I hope this message finds you well. My name is **[YOUR NAME]**, **[YOUR TITLE]** in the **[YOUR DEPARTMENT]** at the **Korea Atomic Energy Research Institute (KAERI)**, a government-funded non-profit research institute under the Ministry of Science and ICT of the Republic of Korea, located in Daejeon.

I am writing on behalf of our **AI Research Laboratory (AIRL)** team, which is developing an AI-driven computational screening pipeline for **SSTR2-targeted radioligand theranostic peptide candidates** labeled with ¹⁷⁷Lu. Our lead scaffold is cyclic somatostatin-14 analogs (14 residues, Cys3–Cys14 disulfide bond, FWKT pharmacophore), and we are currently preparing four candidates (PRST-001 through PRST-004) for entry into experimental validation (Gate-2). A key team review meeting is scheduled for **28 May 2026**, at which ADMET predictions will directly inform the go/no-go decision for wet-lab synthesis.

We have been closely following your group's work. In particular, we have studied and integrated two publications:

1. **Tan X. et al.** "pepADMET: A Novel Computational Platform for Systematic ADMET Evaluation of Peptides." *J. Chem. Inf. Model.*, 2026. DOI: [10.1021/acs.jcim.5c02518](https://doi.org/10.1021/acs.jcim.5c02518)

2. **Tan X. et al.** "Introducing enzymatic cleavage features and transfer learning realizes accurate peptide half-life prediction across species and organs." *Briefings in Bioinformatics*, 2024, **25**(4), bbae350. DOI: [10.1093/bib/bbae350](https://doi.org/10.1093/bib/bbae350)

We successfully installed the pepADMET GitHub repository (GPL-3.0, https://github.com/ifyoungnet/pepADMET) locally on our GPU servers and ran toxicity inference on our four SSTR2 peptide candidates using their SMILES representations. After patching a PyBioMed compatibility issue (`estate.py`), the four-task toxicity model produced results. We are genuinely impressed by the platform's architecture and comprehensive coverage of peptide ADMET space.

**The primary bottleneck we now face** is accurate half-life prediction. Serum stability is among the most critical ADMET criteria for our radiolabeled peptides, yet the GitHub repository currently exposes only four toxicity-related endpoints. The 25 additional endpoints described in your JCIM paper — including blood half-life in human and mouse — are not publicly available.

We attempted to reproduce a half-life regression model independently: we trained a GAT (Graph Attention Network)-based regressor using publicly available peptide half-life datasets, applying your PeptideCutter 39-enzyme descriptor strategy described in your Briefings in Bioinformatics paper. Unfortunately, our independent effort yielded a validation R² of **−0.028**, which is clearly non-functional and well below the R² ≈ 0.90 benchmark your team reported. This result honestly reflects the limitations of our local data and training strategy, and underscores our strong motivation to request access to your validated model or training data.

We would therefore like to respectfully request the following:

---

**Request 1 — Half-Life Endpoint Model Weights (Highest Priority)**

Could you share the pretrained model weights for the blood half-life endpoints (human and mouse) from your pepADMET framework? Even a minimal inference-ready checkpoint would be transformative for our pipeline. We are committed to using the weights solely for non-commercial academic research and will provide full attribution in any publications.

**Request 2 — Half-Life Training Dataset**

If sharing the model weights is not feasible, we would greatly appreciate access to the curated training dataset (peptide sequences, SMILES, and measured half-life values in human/mouse blood) used to train the half-life model in your Briefings in Bioinformatics 2024 paper (bbae350). A dataset with documented provenance would allow us to retrain under your methodology and validate against your reported R² of ~0.90.

**Request 3 — Environment and AlphaPeptDeep Pretrained Weights**

We noted that your half-life model employs AlphaPeptDeep-based transfer learning (Mann group, Nature Communications 2022). Could you clarify (a) which AlphaPeptDeep checkpoint you used for pretraining, and (b) provide or point to the frozen dependency specification (`environment.yml` or `requirements.txt`) that reproduces your training environment, including the compatible RDKit version?

**Request 4 — Broader Endpoint Weights (Optional)**

If feasible, access to weights for other endpoints (membrane permeability, bioavailability, BBB) would further strengthen our screening pipeline, as these are also listed in your paper but are not publicly released. We list this as secondary to Requests 1–3 and fully understand if resource constraints make this difficult.

---

Regarding intellectual property and licensing: our use is strictly **non-commercial academic research** within a government-funded institute. We will cite your work precisely (full bibliographic references and DOIs) in all presentations, reports, and publications arising from our project. We are also open to a formal academic data-sharing agreement or even a collaborative contribution to your benchmark dataset with our cyclic disulfide-bridged peptide validation results, should this be of interest to your group.

We recognize that responding to external requests takes time, and we are deeply grateful for any assistance you can provide. If possible, we would greatly appreciate an initial reply by **25 May 2026** (three days before our key review meeting), even if a complete data package follows later. Of course, we fully respect your timeline and will work with whatever schedule is convenient for you.

Please feel free to contact me at **[YOUR EMAIL]**. I would also be happy to arrange a brief video call at your convenience if that would be more efficient.

Thank you sincerely for your pioneering work on pepADMET and for your continued contributions to the computational peptide drug discovery community.

Yours sincerely,

**[YOUR NAME]**
[YOUR TITLE]
[YOUR DEPARTMENT]
Korea Atomic Energy Research Institute (KAERI)
989-111 Daedeok-daero, Yuseong-gu, Daejeon 34057, Republic of Korea
Email: **[YOUR EMAIL]**
Tel: [YOUR PHONE]
ORCID: [YOUR ORCID — optional]

---

## 2. 한국어 본문 (KAERI 행정 내부 전달용)

> **행정 참고사항**: 아래 본문은 위 영문 이메일(jiedong@csu.edu.cn 발송용)의 한국어 번역본입니다. KAERI 외부 발송 절차 확인 및 행정 담당자 검토용으로 작성되었습니다.

---

**제목**: 학술 데이터 협력 요청 — pepADMET 반감기 모델 가중치 및 학습 데이터 (SSTR2 방사성의약품 펩타이드 스크리닝, 한국원자력연구원)

---

안녕하세요, 董杰 교수님.

저는 대한민국 과학기술정보통신부 산하 정부출연연구기관인 한국원자력연구원(KAERI, Korea Atomic Energy Research Institute, 대전 소재)의 **[YOUR DEPARTMENT]** 소속 **[YOUR NAME] [YOUR TITLE]**입니다.

저희 **인공지능연구실(AIRL)** 팀은 ¹⁷⁷Lu 표지 **SSTR2(소마토스타틴 수용체 2형) 표적 방사성의약품 테라노스틱 펩타이드 후보 스크리닝** AI 파이프라인을 구축하고 있습니다. 저희 주요 스캐폴드는 환형 소마토스타틴-14 유사체(14 잔기, Cys3–Cys14 이황화결합, FWKT 약효단)이며, 현재 4개 후보(PRST-001~004)의 실험적 검증(Gate-2) 진입을 준비하고 있습니다. **2026년 5월 28일**에 핵심 팀 검토 회의가 예정되어 있으며, 해당 회의에서 ADMET 예측 결과가 습식 실험 합성의 진행 여부 결정에 직접 활용됩니다.

저희 팀은 교수님 연구 그룹의 다음 두 편의 논문을 면밀히 검토하고 연구에 통합해 왔습니다.

1. **Tan X. 외** "pepADMET: A Novel Computational Platform for Systematic ADMET Evaluation of Peptides." *J. Chem. Inf. Model.*, 2026. DOI: 10.1021/acs.jcim.5c02518

2. **Tan X. 외** "Introducing enzymatic cleavage features and transfer learning realizes accurate peptide half-life prediction across species and organs." *Briefings in Bioinformatics*, 2024, **25**(4), bbae350. DOI: 10.1093/bib/bbae350

저희는 pepADMET GitHub 저장소(GPL-3.0, https://github.com/ifyoungnet/pepADMET)를 자체 GPU 서버에 로컬로 설치하고, 4개의 SSTR2 펩타이드 후보에 대해 SMILES 기반 독성 추론을 수행했습니다. PyBioMed 호환성 문제(`estate.py` 패치) 해결 후 4-task 독성 모델이 정상 작동하였으며, 플랫폼의 설계와 포괄적인 펩타이드 ADMET 적용 범위에 깊은 인상을 받았습니다.

**현재 저희가 직면한 가장 큰 장벽**은 정확한 반감기(half-life) 예측입니다. 혈중 안정성은 방사성 표지 펩타이드에 있어 가장 중요한 ADMET 기준 중 하나입니다. 그러나 GitHub 저장소에는 현재 4개의 독성 관련 endpoint만 공개되어 있으며, JCIM 논문에 기술된 혈중 반감기(인간/마우스) 포함 25개의 추가 endpoint 모델은 공개되어 있지 않습니다.

저희 팀은 반감기 회귀 모델의 자체 재현을 시도했습니다. 공개된 펩타이드 반감기 데이터셋을 활용하여 GAT(Graph Attention Network) 기반 회귀 모델을 학습하고, 교수님의 Briefings in Bioinformatics 2024 논문에 기술된 PeptideCutter 39-효소 descriptor 전략을 적용하였습니다. 그러나 자체 학습 결과 검증 R²가 **−0.028**에 그쳐, 교수님 연구팀이 보고하신 R² ≈ 0.90 벤치마크에 크게 못 미쳤습니다. 이 결과는 저희 자체 데이터와 학습 전략의 한계를 솔직히 반영하는 것이며, 교수님의 검증된 모델 또는 학습 데이터 접근 요청의 강력한 동기가 되었습니다.

이에 따라 아래와 같이 정중하게 요청드립니다.

---

**요청 1 — 반감기 endpoint 사전학습 모델 가중치 (최우선 항목)**

pepADMET 프레임워크의 혈중 반감기(인간/마우스) endpoint에 대한 사전학습 모델 가중치를 공유해 주실 수 있을까요? 추론 가능한 최소 체크포인트만으로도 저희 파이프라인에 큰 도움이 됩니다. 해당 가중치는 비상업적 학술 연구 목적으로만 사용하며, 모든 발표 및 논문에서 교수님 논문을 정확히 인용할 것을 약속드립니다.

**요청 2 — 반감기 학습 데이터셋**

모델 가중치 공유가 어려우신 경우, Briefings in Bioinformatics 2024 논문(bbae350)의 반감기 모델 학습에 사용된 큐레이션 데이터셋(펩타이드 서열, SMILES, 인간/마우스 혈중 반감기 측정값)을 제공해 주실 수 있을까요? 출처가 명확한 데이터셋이 있다면, 교수님의 방법론대로 재학습하여 보고하신 R² ≈ 0.90을 검증할 수 있을 것입니다.

**요청 3 — 실행 환경 및 AlphaPeptDeep 사전학습 가중치**

교수님의 반감기 모델이 AlphaPeptDeep 기반 전이 학습을 활용하고 있음을 파악하였습니다. (a) 사전학습에 사용하신 AlphaPeptDeep 체크포인트 버전, (b) 학습 환경을 재현하기 위한 동결 의존성 사양(`environment.yml` 또는 `requirements.txt`, 호환 RDKit 버전 포함)을 공유해 주실 수 있을까요?

**요청 4 — 추가 endpoint 가중치 (선택 항목)**

가능하시다면, 막 투과성(PAMPA, Caco-2), 생체이용률(F), BBB 투과성 등 추가 endpoint 모델 가중치도 제공해 주시면 스크리닝 파이프라인을 더욱 강화할 수 있습니다. 다만 이 항목은 요청 1~3에 비해 우선순위가 낮으며, 자원 제약으로 어려우신 경우 충분히 이해합니다.

---

지식재산권 및 라이선스 관련하여: 저희의 사용 목적은 정부출연연구기관 내에서의 **순수 비상업적 학술 연구**입니다. 본 프로젝트에서 발생하는 모든 발표, 보고서, 논문에 교수님 연구팀의 논문을 정확한 참고문헌(DOI 포함)으로 인용하겠습니다. 또한 공식적인 학술 데이터 공유 협약 체결도 가능하며, 저희 환형 이황화결합 펩타이드 검증 결과를 교수님의 벤치마크 데이터셋에 기여하는 형태의 협력도 관심 있으시면 기꺼이 논의하겠습니다.

외부 요청 대응에 시간이 소요되는 것을 충분히 이해합니다. 가능하시다면 **2026년 5월 25일**(검토 회의 D-3)까지 초기 답변을 주시면 대단히 감사하겠습니다. 완전한 데이터 패키지는 이후에 전달해 주셔도 무방합니다. 물론 교수님의 일정을 최우선으로 존중합니다.

연락처는 **[YOUR EMAIL]**입니다. 영상통화가 더 편하시다면 기꺼이 일정을 조율하겠습니다.

pepADMET 개발 및 펩타이드 계산약학 발전에 기여해 주신 교수님과 연구팀에 깊이 감사드립니다.

감사합니다.

**[YOUR NAME]**
[직함/직위]
[소속 부서]
한국원자력연구원 (KAERI)
대전광역시 유성구 덕진동 989-111
이메일: **[YOUR EMAIL]**
전화: [YOUR PHONE]

---

## 3. 발송 전 체크리스트

### 필수 수정 항목 (플레이스홀더 교체)
- [ ] `[YOUR NAME]` — 실제 영문 성명 (예: Dong-Ju Kim)
- [ ] `[YOUR TITLE]` — 직함 영문 (예: Senior Researcher / Research Scientist / Principal Investigator)
- [ ] `[YOUR DEPARTMENT]` — 소속 부서 영문 (예: AI Research Laboratory / Nuclear Medicine Technology Division)
- [ ] `[YOUR EMAIL]` — 기관 이메일 (dongjukim@kaeri.re.kr 또는 담당자 실제 이메일)
- [ ] `[YOUR PHONE]` — 국제전화 형식 (예: +82-42-XXX-XXXX)
- [ ] `[YOUR ORCID]` — ORCID ID (선택, 있으면 신뢰도 향상)
- [ ] CC 수신자 — RI팀 담당자 / co-PI / KAERI 행정 담당자 주소

### 내용 검토 항목
- [ ] **V-03 toxicity 결과 (PRST-001~004 전원 binary_toxicity=1.0) 미포함 확인** — 협력 타진 단계에서 의도적으로 제외. 관계 구축 후 별도 논의 권장
- [ ] **R²=-0.028 정직 보고 재확인** — 본 이메일의 핵심 차별점 (투명성이 신뢰도 높임)
- [ ] 논문 DOI 정확성 재확인:
  - pepADMET JCIM: `10.1021/acs.jcim.5c02518` ✅
  - 반감기 BIB: `10.1093/bib/bbae350` ✅
- [ ] GitHub URL 재확인: `https://github.com/ifyoungnet/pepADMET` ✅

### 행정 절차 항목
- [ ] KAERI 외부 발송 사전 승인 (기관 정책에 따라 필요 여부 확인)
- [ ] 데이터 수신 시 적용 협약 서식 확인 (연구 데이터 공유 협약 필요 여부)
- [ ] GPL-3.0 라이선스 준수 확인 (로컬 설치 사용 — 이미 적법)
- [ ] 발송 후 답변 수신 시 A-03 액션 아이템 상태 업데이트 필요

### 발송 시한
- **권장 발송일**: 2026-05-21 (오늘) ~ 5/23
- **응답 요청일**: 2026-05-25 (회의 D-3)
- **회의일**: 2026-05-28

---

## 4. 배경 정보 요약 (행정 담당자용)

### 왜 이 이메일이 필요한가?

저희 AI 파이프라인은 SSTR2 표적 방사성의약품 후보 4개(PRST-001~004)를 평가하는 단계에 있습니다. ADMET 예측 중 **혈중 반감기**(얼마나 오래 체내에서 유효 농도를 유지하는가)는 방사성의약품 설계의 핵심 기준이나, 현재 공개된 pepADMET 모델에는 이 기능이 포함되어 있지 않습니다. 저희가 직접 모델을 학습해 보았으나 실패(R²=-0.028)하였고, 개발 논문 저자에게 협력을 요청하는 것이 현 시점에서 가장 효율적인 해결책입니다.

### 비용 발생 여부

없음. 학술 데이터 공유 협력 요청이며, 비용 계약은 현 단계에서 고려하지 않습니다.

### 기관 분류

pepADMET 개발 기관: 중국 중남대학교(Central South University) 상야약학부 — 학술 기관. 본 요청은 정부 간 학술 협력 범위에 해당합니다.
