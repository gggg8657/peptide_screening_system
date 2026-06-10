# pepADMET Author Inquiry — English Email Draft

**Draft date**: 2026-05-20  
**To**: Prof. Jie Dong \<jiedong@csu.edu.cn\>  
**CC**: [co-PI / RI team lead — fill in before sending]  
**Subject**: Academic Collaboration Inquiry — pepADMET Full Paper, Extended Endpoint Models, and License Clarification (KAERI, Korea)

> ⚠ **발송 전 필수 수정**: `[YOUR NAME]`, `[YOUR TITLE]`, `[YOUR DEPARTMENT]` 플레이스홀더를 실제 정보로 교체할 것.

---

## Draft Email

---

Dear Prof. Jie Dong,

I hope this message finds you well. My name is **[YOUR NAME]**, **[YOUR TITLE]** at the **Korea Atomic Energy Research Institute (KAERI)**, a government-funded non-profit research institute in Daejeon, Republic of Korea.

I am writing on behalf of our AI Research Laboratory, where we are developing a computational screening pipeline for **SSTR2-targeted radioligand theranostic peptide candidates** (¹⁷⁷Lu-based). Our project focuses on cyclic somatostatin-14 analogs (14-residue, Cys3–Cys14 disulfide bond) as lead scaffolds for targeted radionuclide therapy and diagnostics.

We recently integrated **pepADMET** (Tan et al., 2026, *JCIM*, DOI: 10.1021/acs.jcim.5c02518) into our screening pipeline as the primary ADMET evaluation tool. We successfully installed the GPL-3.0 GitHub version locally and ran inference on our four lead candidates (PRST-001 through PRST-004). The toxicity task results have been informative, and we are highly impressed by the platform's design and scope.

We are reaching out with **three specific requests** for academic collaboration:

---

### Request 1 — Full Paper PDF (Preprint or Author Copy)

Access to the full text of your paper is unfortunately restricted by the ACS paywall at our institution at this time. We would greatly appreciate it if you could share an author's accepted manuscript or preprint version of:

> Tan X. et al., "pepADMET: A Novel Computational Platform For Systematic ADMET Evaluation of Peptides," *J. Chem. Inf. Model.*, 2026, DOI: 10.1021/acs.jcim.5c02518

We are particularly interested in the detailed descriptions of model architecture, training datasets, and performance metrics for each endpoint, as well as any documentation regarding support for **D-amino acid residues** (relevant to our Octreotide-class analogs).

---

### Request 2 — Extended Endpoint Models (Code and Pretrained Weights)

The public GitHub repository (https://github.com/ifyoungnet/pepADMET) currently provides models for four toxicity-related tasks. However, your paper describes a comprehensive platform covering **29 endpoints** across absorption, distribution, metabolism, and toxicity.

For our SSTR2 theranostic peptide pipeline, we have a particular need for the following endpoints that are described in the paper but not yet available on GitHub:

| Priority | Endpoint | Relevance to our pipeline |
|----------|----------|--------------------------|
| HIGH | Half-life (human/mouse blood) | Serum stability screening (TPP: ≥ 24 h) |
| HIGH | Membrane permeability (PAMPA, Caco-2) | Especially cyclic peptide-specific model |
| HIGH | Bioavailability (F) | Oral/IV PK profiling |
| MED | BBB permeability | CNS-off-target exclusion |

We would be grateful if you could share the code and pretrained weights for these additional endpoints, or advise us on how to access them. We are committed to using the models strictly for non-commercial, academic research purposes.

---

### Request 3 — License Clarification for KAERI (Non-Profit Government Institute)

Regarding the use of pepADMET in our research:

- **GitHub repository (GPL-3.0)**: We have installed this version locally and are using it for internal research computations.
- **Web platform (CC BY-NC-SA 4.0)**: The non-commercial restriction raises a question for our use case.

**KAERI** is a government-funded, non-profit research institution operating under the Ministry of Science and ICT of the Republic of Korea. Our intended use is:
1. Internal research computation (non-commercial)
2. Publication of scientific results in peer-reviewed journals (with appropriate citation of pepADMET)
3. No commercial product development or licensing

We believe our use is compatible with the CC BY-NC-SA 4.0 terms, but we would appreciate your formal confirmation. If a separate academic collaboration agreement (e.g., MOU or data sharing agreement) would be more appropriate, we are open to that as well.

---

We believe that a collaboration between our groups could be mutually beneficial. Our application domain — cyclic disulfide-bridged peptides for nuclear medicine — represents an underexplored area for ADMET tools, and our validation results on SSTR2-targeting candidates could contribute to the pepADMET benchmark dataset.

Please feel free to contact me at **[YOUR EMAIL]** or my supervisor at **[SUPERVISOR EMAIL]**. We look forward to hearing from you at your earliest convenience.

Thank you sincerely for your time and for developing such a valuable tool for the peptide research community.

Yours sincerely,

**[YOUR NAME]**  
[YOUR TITLE]  
[YOUR DEPARTMENT]  
Korea Atomic Energy Research Institute (KAERI)  
989-111 Daedeok-daero, Yuseong-gu, Daejeon 34057, Republic of Korea  
Tel: [YOUR PHONE]  
Email: [YOUR EMAIL]

---

## 작성 메모 (한국어)

### 톤 및 전략
- **정중·간결·학술적** — 협력 타진이므로 요구보다 제안 톤 유지
- Request 2에서 전체 25 endpoint 나열 대신 **우리 파이프라인에 직접 필요한 4개 우선순위** 제시 → 응답 가능성 높임
- V-03 결과 (4건 모두 toxic)는 편지 본문에 포함하지 않음 — 협력 관계 구축 후 별도 논의가 적절

### V-05 라이선스 전략
- KAERI = 정부출연연, 비영리 → CC BY-NC-SA NC 조건 충족 가능성 HIGH
- GPL-3.0 GitHub 버전은 이미 자유롭게 사용 가능 (로컬, 비영리)
- 웹 플랫폼 CC BY-NC-SA는 웹 API 접근 시 적용 — 로컬 설치에는 GPL-3.0 적용
- Request 3은 "확인" 요청이지 "허가 요청"이 아님 → 협력 관계 출발점으로 활용

### 발송 전 최종 확인 사항
- [ ] `[YOUR NAME]` → 실제 성명 (영문)
- [ ] `[YOUR TITLE]` → 직함 (예: Senior Researcher, Research Scientist)
- [ ] `[YOUR DEPARTMENT]` → 소속 부서 (예: AI Research Division, Nuclear Medicine Technology Division)
- [ ] `[YOUR EMAIL]` → 기관 이메일
- [ ] `[SUPERVISOR EMAIL]` → 필요 시 지도교수/팀장 CC
- [ ] CC 수신자 확인 (RI팀 담당자, co-PI 등)
- [ ] 논문 DOI 링크 정확성 재확인: 10.1021/acs.jcim.5c02518 ✅
- [ ] pepADMET GitHub URL 재확인: https://github.com/ifyoungnet/pepADMET ✅
