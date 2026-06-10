# Papers — 검증 통과 논문 목록

접근 확인일: 2026-06-01

| ID | 제목 (축약) | 저자 | 연도 | 저널 | DOI / arXiv | 상태 |
|----|-----------|------|------|------|-------------|------|
| P01 | Interaction of Radiopharmaceuticals with SSTR2 Revealed by MD Simulations | Gervasoni S et al. | 2023 | J Chem Inf Model | 10.1021/acs.jcim.3c00712 | 통과 (PMC10428218) |
| P02 | Exploring key features of selectivity in SSTRs through MD simulations | Gervasoni S et al. | 2024 | Comput Struct Biotechnol J | 10.1016/j.csbj.2024.03.005 | 통과 (PMC11630666) |
| P03 | DiffDock: Diffusion Steps, Twists, and Turns for Molecular Docking | Corso G et al. | 2023 | ICLR 2023 | arXiv:2210.01776 | 통과 |
| P04 | Accurate structure prediction of biomolecular interactions with AlphaFold 3 | Abramson J et al. | 2024 | Nature | 10.1038/s41586-024-07487-w | 통과 |
| P05 | Boltz-2: Towards Accurate and Efficient Binding Affinity Prediction | Wohlwend J et al. | 2025 | bioRxiv (preprint) | 10.1101/2025.06.14.659707 | 통과 (PMC12262699) |
| P06 | gmx_MMPBSA: A New Tool to Perform End-State Free Energy Calculations | Valdés-Tresanco MS et al. | 2021 | J Chem Theory Comput | 10.1021/acs.jctc.1c00645 | 통과 |
| P07 | In silico approaches for predicting the half-life of peptides in blood | Mathur D et al. | 2018 | PLoS ONE | 10.1371/journal.pone.0196829 | 통과 (PMID 29856745) |
| P08 | Designing of peptides with desired half-life in intestine-like environment | Sharma A et al. | 2014 | BMC Bioinformatics | 10.1186/1471-2105-15-282 | 통과 (PMID 25141912) |
| P09 | In vivo half-life of a protein is a function of its amino-terminal residue | Bachmair A, Finley D, Varshavsky A | 1986 | Science | 10.1126/science.3018930 | 통과 (PMID 3018930) |
| P10 | Towards the improved discovery and design of functional peptides (PeptideRanker) | Mooney C et al. | 2012 | PLoS ONE | PMID 23056189 | 통과 |
| P11 | ADMET-AI: a machine learning ADMET platform | Swanson K et al. | 2024 | Bioinformatics | 10.1093/bioinformatics/btae416 | 통과 (PMC11226862) |
| P12 | pepADMET: a novel computational platform for systematic ADMET evaluation of peptides | Tan X et al. | 2025/2026 | J Chem Inf Model | 10.1021/acs.jcim.5c02518 | 통과 |
| P13 | pymoo: Multi-objective Optimization in Python | Blank J, Deb K | 2020 | IEEE Access | arXiv:2002.04504 | 통과 |

## 도메인별 분류

### SSTR2 / 방사성의약품 (본 프로젝트 핵심)
- P01: SSTR2 + 방사성의약품 + MD — 직접 전례. DOTATATE 계열 킬레이터별 결합 분석
- P02: SSTR 아형 선택성 — SST14 유도체 SSTR2 선택성 향상 설계 가이드라인

### 도킹 / 구조 예측
- P03: DiffDock — 디퓨전 기반 소분자 도킹 (펩타이드 적용 검토 필요)
- P04: AlphaFold3 — 복합체 구조 예측 (펩타이드+GPCR 포함)
- P05: Boltz-2 — 구조 + binding affinity 통합 (FEP 수준 정확도)

### 자유에너지 / MD
- P06: gmx_MMPBSA — MM-GBSA 계산 표준 도구

### 반감기 / ADMET
- P07: PlifePred 원전 (혈중 반감기)
- P08: HLP 원전 (장내 반감기)
- P09: N-end rule 원전 (Bachmair 1986) — N말단 잔기 설계 근거
- P10: PeptideRanker 원전
- P11: ADMET-AI 원전
- P12: pepADMET 원전

### 최적화
- P13: pymoo 원전 (NSGA-II 포함)
