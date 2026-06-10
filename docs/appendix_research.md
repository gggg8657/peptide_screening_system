# Appendix: 약리학 메트릭 원논문 출처 및 최근 활용 사례

> 본 문서는 펩타이드 치료제, 항균 펩타이드(AMP), 방사성의약품, 단백질 공학 분야에서 활용되는
> 13가지 약리학 메트릭/방법론의 원논문 구체적 출처(Table/Figure/Section)와
> 최근(2020-2026) 논문 활용 사례를 정리한 것이다.

---

## 1. 원논문 구체적 출처

### [5] Kyte & Doolittle 1982 -- Hydropathy Scale

- **논문**: Kyte J, Doolittle RF. "A simple method for displaying the hydropathic character of a protein." *J Mol Biol* 157(1):105-132, 1982.
- **Table II**: 20개 아미노산의 hydropathy 값이 수록된 핵심 테이블. Ile (+4.5, 최대 소수성)부터 Arg (-4.5, 최대 친수성)까지의 스케일을 정의한다. 값은 수상(水相) vs 증기상 전이 자유에너지, 아미노산의 내부/외부 분포 빈도 등 복수 기준의 합의(consensus)로 도출되었다.
- **Figure 4-6**: Sliding window 방식의 hydropathy plot 예시 (알려진 막단백질 구조 검증).

### [6] Boman 2003 -- Boman Index (Protein-Binding Potential Index)

- **논문**: Boman HG. "Antibacterial peptides: basic facts and emerging concepts." *J Intern Med* 254(3):197-215, 2003.
- **Section "Binding potential"**: 인덱스 정의와 임계값 2.48 kcal/mol이 기술된 섹션. Boman Index는 Radzicka & Wolfenden의 cyclohexane-to-water 전이 자유에너지 값을 각 잔기에 대해 합산한 뒤 전체 잔기 수(N)로 나눈 평균값이다. LL-37, PR-39, VIP 세 펩타이드가 2.48 이상의 값을 보이며, 이를 높은 단백질 결합 잠재력(high binding potential)의 임계값으로 제시하였다.

### [7] Guruprasad et al. 1990 -- Instability Index (II)

- **논문**: Guruprasad K, Reddy BVB, Pandit MW. "Correlation between stability of a protein and its dipeptide composition: a novel approach for predicting in vivo stability of a protein from its primary sequence." *Protein Eng* 4(2):155-161, 1990.
- **Table III**: 20x20 DIWV (Dipeptide Instability Weight Value) 매트릭스. 12개 불안정 단백질과 32개 안정 단백질의 디펩타이드 빈도 차이에서 도출된 400개 가중치 값을 수록한다.
- **Equation (수식)**: II = (10/L) x SUM[DIWV(x_i, x_{i+1})] (i = 1 to L-1). L은 서열 길이이며, II < 40이면 안정, II >= 40이면 불안정으로 예측한다.

### [8] Ikai 1980 -- Aliphatic Index

- **논문**: Ikai A. "Thermostability and aliphatic index of globular proteins." *J Biochem* 88(6):1895-1898, 1980.
- **Equation (본문 내 수식)**: Aliphatic Index = X(Ala) + a x X(Val) + b x [X(Ile) + X(Leu)]. 여기서 X(aa)는 각 아미노산의 mole percent (100 x mole fraction)이고, a = 2.9 (Val 측쇄의 Ala 대비 상대 부피), b = 3.9 (Leu/Ile 측쇄의 Ala 대비 상대 부피)이다.
- 높은 aliphatic index는 열안정성(thermostability)의 양의 인자로 해석된다. 호열성 세균(thermophilic bacteria)의 단백질이 일반 단백질보다 유의미하게 높은 aliphatic index를 보인다.

### [9] Bjellqvist et al. 1993 -- Isoelectric Point (pI) pKa Values

- **논문**: Bjellqvist B, Hughes GJ, Pasquali C, Paquet N, Ravier F, Sanchez JC, Frutiger S, Hochstrasser DF. "The focusing positions of polypeptides in immobilized pH gradients can be predicted from their amino acid sequences." *Electrophoresis* 14:1023-1031, 1993.
- **Table 1**: 이온화 가능한 아미노산 측쇄(Asp, Glu, Cys, Tyr, His, Lys, Arg)와 N-말단/C-말단의 pKa 값을 수록. 이 pKa 값은 immobilized pH gradient (IPG) 겔에서의 초점 위치 실험 데이터로부터 결정되었으며, 관련 아미노산(immobiline) 간 차이를 이용하여 도출하였다.
- 29개 폴리펩타이드의 아미노산 서열 기반 계산 pI와 실험 pI의 일치를 검증하였다.

### [10] Eisenberg et al. 1982 -- Hydrophobic Moment

- **논문**: Eisenberg D, Weiss RM, Terwilliger TC. "The helical hydrophobic moment: a measure of the amphiphilicity of a helix." *Nature* 299:371-374, 1982.
- **Equation 1 (본문 수식)**: <mu_H> = |SUM(H_i * e^{i*delta*n})| / N. 여기서 H_i는 i번째 잔기의 소수성 값, delta는 나선 회전 각도 (alpha-helix의 경우 100도), n은 잔기 번호, N은 총 잔기 수이다. 벡터 합의 절대값을 잔기 수로 나누어 평균 소수성 모멘트를 구한다.
- **Figure 2**: Hydrophobic moment plot -- 평균 소수성(<H>) vs 평균 소수성 모멘트(<mu_H>)의 2D plot. 막관통 나선, 구상단백질 나선, 표면활성 나선이 서로 다른 영역에 클러스터링된다.

### [11] Wimley & White 1996 -- Interfacial Hydrophobicity Scale

- **논문**: Wimley WC, White SH. "Experimentally determined hydrophobicity scale for proteins at membrane interfaces." *Nat Struct Biol* 3(10):842-848, 1996.
- **Table 1**: 20개 아미노산 + 펩타이드 결합에 대한 deltaG 전이 자유에너지(수상 -> POPC 이중층 계면, kcal/mol). Trp (-1.85)가 가장 강한 계면 선호를 보이며, 방향족 잔기들이 계면에서 특히 유리하다. 하전된 잔기와 펩타이드 결합은 거의 동등하게 불리하다.
- Ace-WL-X-LL 펜타펩타이드 시리즈의 POPC 소낭(vesicle) 분배 실험에서 직접 측정한 값이다.

### [12] Pace et al. 1995 -- Extinction Coefficient (epsilon_280)

- **논문**: Pace CN, Vajdos F, Fee L, Grimsley G, Gray T. "How to measure and predict the molar absorption coefficient of a protein." *Protein Sci* 4(11):2411-2423, 1995.
- **Equation (핵심 수식)**: epsilon_280 (M^-1 cm^-1) = n_Trp x 5500 + n_Tyr x 1490 + n_SS x 125. 여기서 n_Trp은 Trp 잔기 수, n_Tyr은 Tyr 잔기 수, n_SS는 이황화결합(cystine) 수이다.
- **Table 2**: Trp, Tyr, cystine 모델 화합물의 물과 8 M guanidinium hydrochloride 조건에서의 흡광계수. 변성 조건(6.0 M GdnHCl)에서는 Trp = 5690, Tyr = 1280, Cys = 120의 대안적 값도 제시된다.
- Trp을 포함하는 단백질에 대해 신뢰도가 높으며, Trp이 없는 단백질은 편차가 10% 이상으로 커질 수 있다.

### [13] Henikoff & Henikoff 1992 -- BLOSUM62 Matrix

- **논문**: Henikoff S, Henikoff JG. "Amino acid substitution matrices from protein blocks." *Proc Natl Acad Sci USA* 89(22):10915-10919, 1992.
- **도출 방법 (Figure 1-3)**: BLOCKS 데이터베이스의 약 2000개 ungapped alignment block에서 아미노산 치환 빈도를 관찰하고, 62% 이상 동일한 서열을 하나의 클러스터로 병합(clustering)하여 근연 서열 편향을 감소시킨 뒤, 관찰된 치환 빈도와 배경 빈도의 log-odds ratio를 계산하여 20x20 대칭 행렬(210개 고유 쌍)을 생성하였다.
- **Figure 2**: BLOSUM62 치환 행렬 자체를 보여주는 주요 figure. 500개 이상의 단백질 family를 대표하는 블록으로부터 도출되었다.

### [14] Gasteiger et al. 2005 -- PeptideCutter (ExPASy)

- **논문**: Gasteiger E, Hoogland C, Gattiker A, Duvaud S, Wilkins MR, Appel RD, Bairoch A. "Protein Identification and Analysis Tools on the ExPASy Server." In: Walker JM (ed) *The Proteomics Protocols Handbook*, Humana Press, pp. 571-607, 2005.
- **Section 8 (PeptideCutter)**: 이 장(chapter)의 Section 8에서 PeptideCutter 도구를 기술한다. 주어진 단백질 서열에 대해 프로테아제 또는 화학시약에 의한 잠재적 절단 부위를 예측하는 도구이며, 37종의 효소/시약에 대한 절단 규칙을 포함한다.
- 절단 특이성은 MEROPS 데이터베이스와 문헌의 실험 데이터에 기반한다.

### [15] Rulisek & Vondrasek 1998 -- Metal Coordination Geometries

- **논문**: Rulisek L, Vondrasek J. "Coordination geometries of selected transition metal ions (Co2+, Ni2+, Cu2+, Zn2+, Cd2+, and Hg2+) in metalloproteins." *J Inorg Biochem* 71(3-4):115-127, 1998.
- **Table 1-3**: 각 금속 이온별 배위수(coordination number) 분포와 배위 기하(tetrahedral, octahedral, square-planar 등)를 PDB 구조에서 통계적으로 분석하여 수록. Zn2+는 4-배위 사면체(tetrahedral)가 82%로 지배적이며, His와 Cys가 가장 빈번한 리간드이다.
- **Table 2**: 각 금속 이온에 대한 아미노산 리간드(His, Cys, Asp, Glu 등) 선호도 분포.

### [22] Varshavsky 1996 -- N-end Rule Half-life

- **논문**: Varshavsky A. "The N-end rule: functions, mysteries, uses." *Proc Natl Acad Sci USA* 93(22):12142-12149, 1996.
- **Table 1**: 포유류(mammalian reticulocyte) 시스템에서 N-말단 아미노산에 따른 단백질 반감기. 대표적 값: Met (30 h), Val (100 h), Gly (30 h), Ile (20 h), Pro (>20 h)는 안정화 잔기이고, Arg (1 h), Glu (1 h), Gln (0.8 h), Asp (1.1 h), Phe (1.1 h), Lys (1.3 h)는 불안정화(destabilizing) 잔기이다.
- N-end rule pathway는 유비퀴틴-프로테아좀 시스템(UPS)의 일부로, 최근 N-degron pathway로 재명명되었다.

---

## 2. 최근 논문 활용 사례 (2020-2026)

### 2.1 GRAVY (Kyte-Doolittle Hydropathy)

| 항목 | 내용 |
|------|------|
| **논문 1** | Li C, Ren Q, Luo M, Wang H, et al. "A Foundation Model Identifies Broad-Spectrum Antimicrobial Peptides against Drug-Resistant Bacterial Infection." *Nature Communications* 15:7390, 2024. |
| **활용** | deepAMP 프레임워크로 설계한 항균 펩타이드 후보의 물리화학적 특성 평가에 GRAVY를 사용하여 소수성/친수성 경향을 분석하고, 막 투과성과의 상관관계를 검토하였다. |
| **맥락** | 항균 펩타이드 (AMP) 설계 |
| **논문 2** | Bobde SS, Alsaab FM, Wang G, Van Hoek ML. "Ab initio Designed Antimicrobial Peptides Against Gram-Negative Bacteria." *Front Microbiol* 12:715246, 2021. |
| **활용** | APD3 도구를 사용하여 ab initio 설계 AMP (PHNX 시리즈)의 GRAVY를 계산하고, 그람 음성균 외막과의 상호작용에 적합한 소수성 범위를 결정하였다. |
| **맥락** | 항균 펩타이드 합리적 설계 |

### 2.2 Boman Index

| 항목 | 내용 |
|------|------|
| **논문 1** | Li C, Ren Q, et al. "A Foundation Model Identifies Broad-Spectrum Antimicrobial Peptides against Drug-Resistant Bacterial Infection." *Nature Communications* 15:7390, 2024. |
| **활용** | deepAMP으로 예측한 AMP 후보의 Boman Index가 2.48 이상인 것을 확인하여, 설계된 펩타이드가 높은 단백질 결합 잠재력을 가짐을 입증하였다. |
| **맥락** | AI 기반 항균 펩타이드 발견 |
| **논문 2** | Bobde SS, Alsaab FM, Wang G, Van Hoek ML. "Ab initio Designed Antimicrobial Peptides Against Gram-Negative Bacteria." *Front Microbiol* 12:715246, 2021. |
| **활용** | APD3 도구로 설계 AMP의 Boman Index를 계산하여 단백질 결합 잠재력을 평가하고, 항균 활성 예측의 보조 지표로 활용하였다. |
| **맥락** | 항균 펩타이드 ab initio 설계 |

### 2.3 Instability Index (Guruprasad)

| 항목 | 내용 |
|------|------|
| **논문 1** | Jafari Najaf Abadi MH, et al. "Vaccinomic approach for novel multi epitopes vaccine against severe acute respiratory syndrome coronavirus-2 (SARS-CoV-2)." *BMC Immunol* 22:21, 2021. |
| **활용** | ExPASy ProtParam으로 다중 에피토프 백신 구조체의 instability index를 계산하여 40 미만의 안정 범위에 있음을 확인하고, in vivo 안정성을 예측하였다. |
| **맥락** | 펩타이드 백신 설계 |
| **논문 2** | Waqas M, et al. "Immunoinformatics design of a structural proteins driven multi-epitope candidate vaccine against different SARS-CoV-2 variants based on fynomer." *Sci Rep* 14:10297, 2024. |
| **활용** | ProtParam으로 백신 구조체의 instability index (II < 40)를 검증하여 열역학적 안정성을 확인하고, aliphatic index, GRAVY와 함께 종합적 물리화학적 프로파일링에 활용하였다. |
| **맥락** | 면역정보학 기반 백신 설계 |

### 2.4 Aliphatic Index (Ikai)

| 항목 | 내용 |
|------|------|
| **논문 1** | Waqas M, et al. "Immunoinformatics design of a structural proteins driven multi-epitope candidate vaccine against different SARS-CoV-2 variants based on fynomer." *Sci Rep* 14:10297, 2024. |
| **활용** | 백신 구조체의 aliphatic index = 84.39로 계산하여 광범위한 온도 범위에서의 안정성(thermostability)을 예측하였다. |
| **맥락** | 펩타이드 백신 열안정성 평가 |
| **논문 2** | Khan S, et al. "Immunoinformatics exploration of a multi-epitope-based peptide vaccine candidate targeting emerging variants of SARS-CoV-2." *Front Microbiol* 14:1251716, 2023. |
| **활용** | ExPASy ProtParam으로 다중 에피토프 백신의 aliphatic index를 계산하여 열안정성이 높은 구조체임을 확인하였다. |
| **맥락** | 면역정보학 기반 백신 설계 |

### 2.5 Isoelectric Point (pI) -- Bjellqvist

| 항목 | 내용 |
|------|------|
| **논문 1** | Jafari Najaf Abadi MH, et al. "Vaccinomic approach for novel multi epitopes vaccine against SARS-CoV-2." *BMC Immunol* 22:21, 2021. |
| **활용** | ProtParam으로 백신 구조체의 이론적 pI = 10.19를 계산하여, 양전하를 띠는 특성이 세포 표면 상호작용에 유리함을 예측하였다. |
| **맥락** | 면역정보학 기반 백신 설계 |
| **논문 2** | Ali A, et al. "Multi-epitope vaccine against SARS-CoV-2 targeting the spike RBD: an immunoinformatics approach." *Future Sci OA* 10:FSO981, 2024. |
| **활용** | ProtParam으로 다중 에피토프 백신의 pI를 계산하고, 전하 특성에 따른 용해도와 면역원성을 예측하였다. |
| **맥락** | 펩타이드 백신 물리화학적 특성 분석 |

### 2.6 Hydrophobic Moment (Eisenberg)

| 항목 | 내용 |
|------|------|
| **논문 1** | Sugihara T, et al. "Effect of hydrophobic moment on membrane interaction and cell penetration of apolipoprotein E-derived arginine-rich amphipathic alpha-helical peptides." *Sci Rep* 12:4959, 2022. |
| **활용** | ApoE 유래 아르기닌 풍부 양친매성 펩타이드의 구조 이성질체 3종에 대해 소수성 모멘트를 계산하여, 모멘트 값이 높을수록 세포 투과 효율이 증가하는 경향을 실험적으로 검증하였다. |
| **맥락** | 세포 투과 펩타이드 (CPP) 설계 |
| **논문 2** | Kosar F, et al. "Interaction of designed cationic antimicrobial peptides with the outer membrane of gram-negative bacteria." *Sci Rep* 14:4318, 2024. |
| **활용** | 설계 양이온성 AMP의 소수성 모멘트를 계산하여 양친매성 정도를 정량화하고, 그람 음성균 외막과의 상호작용 모드를 분류하였다. |
| **맥락** | 항균 펩타이드 막 상호작용 분석 |

### 2.7 Wimley-White Hydrophobicity Scale

| 항목 | 내용 |
|------|------|
| **논문 1** | Falanga A, et al. "Hydrophobicity: The door to drug delivery." *J Pept Sci* 30:e3558, 2024. |
| **활용** | Wimley-White 계면 소수성 스케일을 사용하여 약물 전달 펩타이드의 막 계면 분배 에너지를 평가하고, 세포 투과 펩타이드의 작용 메커니즘을 분류하였다. |
| **맥락** | 펩타이드 약물 전달 시스템 |
| **논문 2** | Gonzalez-Ortega O, et al. "Investigating molecular descriptors in cell-penetrating peptides prediction with deep learning: Employing N, O, and hydrophobicity according to the Eisenberg scale." *PLoS One* 19:e0305253, 2024. |
| **활용** | Wimley-White와 Eisenberg 소수성 스케일을 분자 기술자(molecular descriptor)로 사용하여 딥러닝 기반 CPP 예측 모델의 성능을 비교 평가하였다. |
| **맥락** | 세포 투과 펩타이드 예측 모델 |

### 2.8 Extinction Coefficient (epsilon_280) -- Pace

| 항목 | 내용 |
|------|------|
| **논문 1** | Waqas M, et al. "Immunoinformatics design of a structural proteins driven multi-epitope candidate vaccine against different SARS-CoV-2 variants based on fynomer." *Sci Rep* 14:10297, 2024. |
| **활용** | ProtParam으로 백신 구조체의 흡광계수 71,740 M^-1 cm^-1를 계산하고, 0.1% (g/L) 흡광도 1.185를 도출하여 UV 분광법 기반 농도 정량 조건을 설정하였다. |
| **맥락** | 펩타이드 백신 정량 분석 |
| **논문 2** | Ali A, et al. "Multi-epitope vaccine against SARS-CoV-2 targeting the spike RBD." *Future Sci OA* 10:FSO981, 2024. |
| **활용** | 백신 구조체의 흡광계수 55,305 M^-1 cm^-1 (280 nm, 수용액)을 계산하여 정제 및 정량 프로토콜 수립에 활용하였다. |
| **맥락** | 면역정보학 기반 백신 설계 |

### 2.9 BLOSUM62 Conservation Score -- Henikoff

| 항목 | 내용 |
|------|------|
| **논문 1** | Jiang L, et al. "Zero-shot prediction of mutation effects with multimodal deep representation learning guides protein engineering." *Cell Rep Methods* 4:100862, 2024. |
| **활용** | BLOSUM62 치환 점수를 단백질 언어모델의 돌연변이 효과 예측 벤치마크 기준선(baseline)으로 사용하고, 단백질 공학에서의 적합도(fitness) 예측에 BLOSUM62 기반 보존 점수를 feature로 통합하였다. |
| **맥락** | 단백질 공학 / 딥러닝 돌연변이 예측 |
| **논문 2** | Szymczak P, et al. "Discovering highly potent antimicrobial peptides with deep generative model HydrAMP." *Nature Communications* 14:1453, 2023. |
| **활용** | 생성된 AMP 서열의 기존 AMP 데이터베이스 대비 서열 유사성을 BLOSUM62 기반 alignment scoring으로 평가하여 신규성(novelty)과 활성 간의 관계를 분석하였다. |
| **맥락** | AI 기반 항균 펩타이드 생성 모델 |

### 2.10 Protease Cleavage Site Prediction -- PeptideCutter

| 항목 | 내용 |
|------|------|
| **논문 1** | Tan X, Liu Y, Fang Y, Yang X, Chen X, Wang P, Ouyang L, Dong G, Zeng J. "Introducing enzymatic cleavage features and transfer learning realizes accurate peptide half-life prediction across species and organs." *Brief Bioinform* 25(4):bbae350, 2024. |
| **활용** | PeptideCutter로 37종 효소에 대한 절단 부위를 예측하여 39개의 효소 절단 기술자(descriptor)를 정의하고, 이를 전이학습 기반 펩타이드 반감기 예측 모델의 핵심 feature로 활용하였다. 총 절단 부위 수, 최근접 절단 부위 거리, 효소별 절단 가중치를 포함한다. |
| **맥락** | 펩타이드 약물 반감기 예측 |
| **논문 2** | Duffy C, et al. "Protein cleaver: an interactive web interface for in silico prediction and systematic annotation of protein digestion-derived peptides." *Front Bioinform* 5:1576317, 2025. |
| **활용** | PeptideCutter의 절단 규칙을 참조하여 개선된 단백질 분해 예측 웹 인터페이스를 개발하고, 프로테오믹스 실험 설계에 활용하였다. |
| **맥락** | 프로테오믹스 / 펩타이드 약물 안정성 |

### 2.11 Metal Coordination (His/Cys) -- Rulisek

| 항목 | 내용 |
|------|------|
| **논문 1** | Szekeres GP, et al. "Studying Peptide-Metal Ion Complex Structures by Solution-State NMR." *Int J Mol Sci* 23(24):15957, 2022. |
| **활용** | His, Cys 잔기의 금속 배위 특성을 NMR로 규명하면서, Rulisek & Vondrasek의 배위 기하 데이터를 참조하여 Zn2+, Cu2+ 등 필수 금속 이온과 펩타이드 리간드의 결합 모드를 분류하였다. |
| **맥락** | 펩타이드-금속 복합체 구조 분석 |
| **논문 2** | Sawicka D, et al. "The Chemical Scaffold of Theranostic Radiopharmaceuticals: Radionuclide, Bifunctional Chelator, and Pharmacokinetics Modifying Linker." *Molecules* 27:3062, 2022. |
| **활용** | 방사성의약품의 이기능성 킬레이터(BFCA) 설계에서 His, Cys 잔기를 포함한 펩타이드 링커의 금속 배위 특성을 활용하여, 방사성핵종(68Ga, 99mTc, 177Lu)의 안정적 표지 조건을 최적화하였다. |
| **맥락** | 방사성의약품 (치료진단학) |

### 2.12 N-end Rule Half-life -- Varshavsky

| 항목 | 내용 |
|------|------|
| **논문 1** | Seo J, et al. "Targeted Protein Degradation to Overcome Resistance in Cancer Therapies: PROTAC and N-Degron Pathway." *Biomedicines* 10(9):2100, 2022. |
| **활용** | N-end rule (N-degron pathway)에 기반하여 PROTAC 분자의 표적 단백질 분해 메커니즘을 설명하고, N-말단 아미노산에 따른 반감기 차이를 약물 설계의 핵심 파라미터로 활용하였다. Arg, Lys 등 불안정화 잔기를 인식하는 Ubr1/Ubr2 E3 리가제 기반의 분해 전략을 제시하였다. |
| **맥락** | 표적 단백질 분해 (PROTAC) 항암 치료 |
| **논문 2** | Zheng N, et al. "N/C-degron pathways and inhibitor development for PROTAC applications." *Biochimie* 213:13-25, 2023. |
| **활용** | N-degron (구 N-end rule) pathway의 포유류 반감기 테이블을 참조하여 PROTAC의 E3 리가제 선택과 degron 설계에 적용하고, poly-Arg degron 기반의 새로운 PROTAC 전략을 개발하였다. |
| **맥락** | 표적 단백질 분해 약물 설계 |

### 2.13 pH-dependent Charge (Henderson-Hasselbalch)

| 항목 | 내용 |
|------|------|
| **논문 1** | Deri MA, et al. "Modern Developments in Bifunctional Chelator Design for Gallium Radiopharmaceuticals." *Molecules* 28(1):203, 2023. |
| **활용** | 68Ga 방사성의약품의 표지(labeling) 과정에서 pH에 따른 펩타이드-킬레이터 복합체의 전하 변화를 Henderson-Hasselbalch 원리로 설명하고, 최적 표지 pH (pH 3-4 for DOTA, pH 5-7 for NOTA 유도체)를 설정하였다. pH 의존적 종분화(speciation)가 표지 효율과 생체 안정성에 직접 영향을 미친다. |
| **맥락** | 방사성의약품 (68Ga-PET) |
| **논문 2** | Ahn SH, et al. "Bn2DT3A, a Chelator for 68Ga Positron Emission Tomography: Hydroxide Coordination Increases Biological Stability of [68Ga][Ga(Bn2DT3A)(OH)]^-." *Inorg Chem* 62:2838-2847, 2023. |
| **활용** | pH 5 이상에서 68Ga-Bn2DT3A 복합체의 hydroxide 배위에 의한 음전하 종(species) 형성을 확인하고, Henderson-Hasselbalch 기반의 pH-전하 관계를 이용하여 생리학적 pH에서의 복합체 안정성 향상 메커니즘을 규명하였다. |
| **맥락** | 방사성의약품 킬레이터 화학 |

---

## 참고문헌 (원논문)

1. Kyte J, Doolittle RF. *J Mol Biol* 157:105-132, 1982.
2. Boman HG. *J Intern Med* 254:197-215, 2003.
3. Guruprasad K, Reddy BVB, Pandit MW. *Protein Eng* 4:155-161, 1990.
4. Ikai A. *J Biochem* 88:1895-1898, 1980.
5. Bjellqvist B, et al. *Electrophoresis* 14:1023-1031, 1993.
6. Eisenberg D, Weiss RM, Terwilliger TC. *Nature* 299:371-374, 1982.
7. Wimley WC, White SH. *Nat Struct Biol* 3:842-848, 1996.
8. Pace CN, et al. *Protein Sci* 4:2411-2423, 1995.
9. Henikoff S, Henikoff JG. *Proc Natl Acad Sci USA* 89:10915-10919, 1992.
10. Gasteiger E, et al. In: Walker JM (ed) *The Proteomics Protocols Handbook*, Humana Press, pp. 571-607, 2005.
11. Rulisek L, Vondrasek J. *J Inorg Biochem* 71:115-127, 1998.
12. Varshavsky A. *Proc Natl Acad Sci USA* 93:12142-12149, 1996.
