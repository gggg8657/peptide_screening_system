# 변이 생성 Strategy 선행 연구 조사 보고서

**날짜**: 2026-05-15  
**에이전트**: researcher  
**산출물 번호**: sod-2026-05-15  
**대상 스텝**: `pipeline_local/steps/step03b_blosum_mutation.py` 대체 후보 검토

---

## 1. 검색 쿼리 및 전략

| # | 쿼리 키워드 | 검색 엔진 | 목적 |
|---|------------|----------|------|
| Q1 | `GPCR peptide ligand design mutation strategy ProteinMPNN ESM-IF1 SSTR somatostatin 2024 2025` | WebSearch | LLM-only 생성 문헌 수집 |
| Q2 | `somatostatin receptor SSTR2 peptide variant mutagenesis pharmacophore FWKT binding affinity 2023 2025` | WebSearch | SSTR2 특이 변이 전략 문헌 |
| Q3 | `position-specific scoring matrix PSSM peptide mutation generation receptor binder design 2024` | WebSearch | PSSM/알고리즘 치환 문헌 |
| Q4 | `saturation mutagenesis peptide pharmacophore conservation motif constrained mutation GPCR ligand optimization` | WebSearch | Motif/pharmacophore 기반 문헌 |
| Q5 | `RFdiffusion hallucination peptide binder GPCR receptor design 2024 2025 Nature Science` | WebSearch | RFdiffusion 최신 동향 |
| Q6 | `ESM-scan in silico deep mutational scanning zero-shot protein language model 2024 Protein Science` | WebSearch | ESM 기반 변이 스캔 |
| Q7 | `cyclic peptide variant generation SSTR2 theranostics DOTA constrained mutation computational 2024` | WebSearch | Theranostic 특화 설계 |
| Q8 | `hybrid LLM pharmacophore filter peptide variant generation diversity SST somatostatin analogue 2024` | WebSearch | Hybrid approach 탐색 |
| F1 | Bryant & Elofsson 2023 (PMC 37880344) | WebFetch | ESM-IF1 세부 방법론 |
| F2 | Longwell et al. 2020 (PMC 8068314) | WebFetch | Saturation mutagenesis 세부 |
| F3 | Mazzocato et al. 2024 (PMC 11672547) | WebFetch | 공진화+ML 조합 방법론 |
| F4 | Totaro et al. 2024 (PMC 11577456) | WebFetch | ESM-Scan 세부 방법론 |
| F5 | Robertson et al. 2022 (PMC 11073612) | WebFetch | SSTR2 ligand plasticity (FWKT 위치별 tolerance) |

---

## 2. 발견 자료 목록

| # | 저자 (연도) | 저널/플랫폼 | 방법론 분류 |
|---|-----------|------------|-----------|
| R1 | Bryant & Elofsson (2023) | *Communications Chemistry* DOI:10.1038/s42004-023-01029-7 | LLM (ESM-IF1 inverse folding) |
| R2 | Dauparas et al. (2022) | *Science* DOI:10.1126/science.add2187 | LLM (ProteinMPNN) |
| R3 | Longwell et al. (2021) | *ACS Chemical Biology* DOI:10.1021/acschembio.0c00722 PMC:8068314 | Motif/pharmacophore + saturation mutagenesis |
| R4 | Mazzocato et al. (2024) | *ACS Central Science* PMC:11672547 | Hybrid (coevolution DCA + ML 예측) |
| R5 | Totaro et al. (2024) | *Protein Science* PMC:11577456 | 알고리즘 (ESM-Scan zero-shot DMS) |
| R6 | Robertson et al. (2022) | *Nature Structural & Molecular Biology* PMC:11073612 | SSTR2 FWKT pharmacophore 구조 기반 |
| R7 | Madani et al. (2023) | *Cell Systems* DOI:10.1016/j.cels.2023.10.002 | LLM (ProGen2 sequence generation) |
| R8 | Bhardwaj et al. (2025) | *Nature Chemical Biology* DOI:10.1038/s41589-025-01929-w | LLM+diffusion (RFpeptides 매크로사이클) |
| R9 | Savytskyi & Bhatt (2024) | *bioRxiv* 10.1101/2024.11.27.625792 | State-specific GPCR-peptide (AlphaFold-Multistate + MPNN) |

---

## 3. 핵심 추출

**R1 — Bryant & Elofsson 2023 (ESM-IF1 + Foldseek)**  
Foldseek로 구조적 backbone seed를 생성하고 ESM-IF1로 시퀀스를 디자인한 후 AlphaFold2로 평가. heteromeric 인터페이스에서 6.5% 성공률(ProteinMPNN 대비 ~4배). GPCR 적용 사례는 없으나 비환형 펩타이드 인터페이스 설계에 강점.

**R2 — Dauparas et al. 2022 (ProteinMPNN)**  
구조 기반 message-passing network으로 아미노산 시퀀스를 역설계. GPU에서 100잔기 단백질을 ~1.2초 내 처리. 다수 연구에서 benchmark 선두. 고정 잔기 (fixed_positions) 지원으로 pharmacophore 보존에 직접 적용 가능.

**R3 — Longwell et al. 2021 (GLP-1R saturation mutagenesis)**  
GLP-1 N-말단 5잔기에 트리머 포스포라미다이트로 전체 변이를 탐색, ~1,700개 효모 분비 변이체 스크리닝. 위치3 음전하 잔기가 >80% 활성 hit에서 필수 — pharmacophore의 화학적 특성(charge, polarity) 보존이 saturation mutagenesis에서도 핵심임을 입증.

**R4 — Mazzocato et al. 2024 (DCA + Random Forest)**  
plmDCA (psuedolikelihood maximization Direct Coupling Analysis) + Monte Carlo로 ~23,600 시퀀스를 소규모 데이터셋(37~50 펩타이드)으로부터 생성. Random Forest Ki 예측으로 우선 순위 결정. parental clone 대비 Ki를 53 nM → 4.3 nM으로 10배 개선. 공진화 정보로 구조적 맥락을 보존.

**R5 — Totaro et al. 2024 (ESM-Scan)**  
ESM zero-shot masked token inference로 시퀀스 전체를 in silico deep mutational scanning. 양성값 = 유리한 치환, 음성값 = 불리한 치환. 빠른 추론 + 웹 인터페이스. 현재까지 14aa 이하 소형 peptide 적용 사례 없음(403aa 효소에 적용).

**R6 — Robertson et al. 2022 (SSTR2 ligand plasticity)**  
cryo-EM으로 SSTR2에 SST14 및 octreotide 결합 구조 결정. FWKT (F7-W8-K9-T10) pharmacophore의 W8이 소수성 포켓에 매몰되고, K9가 D122 염교(salt bridge) 형성. 비-pharmacophore 위치는 리간드 정체에 따라 differential tolerance — 설계 시 이 위치별 허용도를 이용해 변이 공간을 제한 가능.

**R7 — Madani et al. 2023 (ProGen2)**  
최대 6.4B 파라미터 단백질 언어 모델, zero-shot 피트니스 예측 + sequence generation. narrow/wide fitness landscape 모두에서 competitive performance. GPCR peptide 특화 fine-tuning 데이터 없음.

**R8 — Bhardwaj et al. 2025 (RFpeptides)**  
RoseTTAFold2 + RFdiffusion 기반 매크로사이클 binder 설계 파이프라인. 20개 이하 설계에서 4개 다양한 단백질 모두 중-고친화도 binder 획득. Kd <10 nM 사례 보고. SS bond 포함 환형 구조 설계 지원.

**R9 — Savytskyi & Bhatt 2024 (State-specific GPCR-peptide)**  
AlphaFold-Multistate + HelixFold-Multimer로 GPCR 활성/비활성 상태별 펩타이드 설계. GLP-1R, GHSR 등 검증. ProteinMPNN으로 시퀀스 다각화. SSTR2 직접 검증 미확인(bioRxiv 단계).

---

## 4. 비교 표 — 변이 생성 전략 옵션별

| 항목 | 옵션 1: LLM-only (ProteinMPNN / ESM-IF1) | 옵션 2: 알고리즘 치환 (PSSM / ESM-Scan) | 옵션 3: Motif/pharmacophore 기반 | 옵션 4: Hybrid (LLM + pharmacophore filter) |
|------|------------------------------------------|----------------------------------------|--------------------------------|---------------------------------------------|
| **대표 논문** | Dauparas 2022 *Science*; Bryant 2023 *Commun. Chem.* | Totaro 2024 *Protein Sci*; Mazzocato 2024 *ACS Cent. Sci.* | Longwell 2021 *ACS Chem. Bio.*; Robertson 2022 *Nat. Struct. Mol. Biol.* | Bhardwaj 2025 *Nat. Chem. Bio.*; Savytskyi 2024 *bioRxiv* |
| **(a) 대표 논문 2건** | Dauparas et al. 2022; Bryant & Elofsson 2023 | Totaro et al. 2024; Mazzocato et al. 2024 | Longwell et al. 2021; Robertson et al. 2022 | Bhardwaj et al. 2025; Savytskyi & Bhatt 2024 |
| **(b) 장점 (우리 컨텍스트)** | 구조 정보 활용, 고정 잔기 지원(FWKT 보존 직접 설정), 대량 생성 가능 (~3,600 seq/hr) | 적은 데이터로 시작 가능, BLOSUM 대체 가능(더 나은 scoring), 해석 가능성 높음 | FWKT pharmacophore 보존이 설계 원칙에 내재, 화학적 직관 반영, 탐색 공간 명확히 제한 | 다양성 + pharmacophore 보존 동시 달성, LLM의 서열 다양성 + 규칙 기반 필터 결합 |
| **(c) 단점/risk** | 구조 파일(PDB) 의존, SSTR2-SST14 complex 구조 필요, black-box, FWKT 해석 어려움 | ESM-Scan은 14aa 소형 펩타이드 검증 미흡, DCA는 공진화 alignment 데이터 필요 | 탐색 공간 제한으로 신규 스캐폴드 발견 어려움, 현재 BLOSUM 방식과 차이 작음 | 구현 복잡도 증가, 두 단계 LLM + 필터 파이프라인 연결 필요 |
| **(d) GPCR/SSTR 적용 사례** | GHSR, GLP-1R (R9); SSTR 직접 사례 미확인 | DCA: urokinase 펩타이드 억제제 (SSTR 아님); ESM-Scan: 효소 단백질 | GLP-1R saturation (R3); SSTR2 pharmacophore 구조 (R6) | 매크로사이클(R8) SSTR 미확인; GPCR-state specific(R9) |
| **(e) 연산 비용** | ProteinMPNN: GPU ~1초/시퀀스; ESM-IF1: 더 큰 모델, 2-3배 느림 | ESM-Scan: CPU 기반 가능, 빠름; DCA: CPU ~수분 (23K seq 생성) | CPU 전용, 규칙 기반 (<1초/시퀀스), 현재 step03b 수준 | ProteinMPNN + 후처리 필터: GPU 1대 기준 ~5,000 seq/시간 |

---

## 5. 본 프로젝트 적용 가능성

| 옵션 | 신뢰 등급 | 근거 |
|------|----------|------|
| 옵션 1: LLM-only (ProteinMPNN) | **HIGH** | 고정 잔기 직접 지원, GPCR 적용 사례 확인(R9), 대량 생성 능력, H100×4 보유로 비용 문제 없음 |
| 옵션 2: ESM-Scan (알고리즘 치환) | **MED** | 빠른 scoring 보완 도구로 유효하나, 14aa 소형 펩타이드 단독 생성 전략으로 검증 미흡 |
| 옵션 3: Motif/pharmacophore 기반 | **HIGH** | 기존 step03b와 설계 원칙 호환, FWKT 보존 명시적, R6 구조 데이터로 위치별 tolerance 설정 가능 |
| 옵션 4: Hybrid | **HIGH** | 다양성과 약리학적 제약 동시 달성, 단 구현 복잡도 MED-HIGH |

---

## 6. 최종 권고

### 추천 1순위: Hybrid (옵션 4) — ProteinMPNN + Pharmacophore Hard-Filter

**구현 요약**: ProteinMPNN (fixed_positions=[3, 7, 8, 9, 10, 14])으로 후보 풀 생성 → FWKT 보존 + Cys3-Cys14 고정 hard-filter → Kyte-Doolittle 소수성 범위 필터 → 다양성 클러스터링 (예: BLOSUM 거리 기반 dedup).

**추천 근거 3가지**:
1. **FWKT pharmacophore 보존이 설계에 내재**: ProteinMPNN fixed_positions 인자로 F7, W8, K9, T10, C3, C14를 직접 고정하므로 별도 post-hoc 필터 없이 pharmacophore가 보장됨 (Robertson 2022 SSTR2 구조와 직결).
2. **다양성 극대화**: 알고리즘 치환(BLOSUM) 대비 LLM 기반 생성은 서열 공간을 넓게 탐색 — 진화적으로 불가능한 치환도 structural context에서 허용하여 신규 스캐폴드 발견 가능. Mazzocato 2024는 소규모 데이터로도 10배 친화도 개선을 달성.
3. **H100×4 GPU 활용 효율**: ProteinMPNN은 GPU ~1초/시퀀스, 1시간에 ~3,600개 생성 가능 → step03b 현재 max_variants=200을 손쉽게 대규모화(2,000~10,000개) 가능.

**백업 2순위: Motif/pharmacophore 기반 + ESM-Scan scoring (옵션 3+2 조합)**

현재 step03b에 가장 가까운 아키텍처. fixed_positions 유지, BLOSUM min_score 대신 ESM-Scan zero-shot score를 치환 우선순위 기준으로 교체. 구조 파일(SSTR2-SST14 complex PDB) 없이도 동작하므로 fallback 경로로 적합.

**구현 난이도 (step03b 대체 시)**:

| 전략 | 난이도 | 변경 범위 |
|------|--------|---------|
| 1순위 Hybrid (ProteinMPNN) | MED | step03b.py 전면 교체, ProteinMPNN conda 환경 + SSTR2-SST14 PDB 입력 추가. 기존 `fixed_positions`, `VariantEntry`, `validate_constraints` 재사용 가능. `run_approach_b` 인터페이스 유지 필요. |
| 2순위 ESM-Scan 치환 기준 교체 | LOW | `get_plausible_substitutions()` 내 min_blosum 필터를 ESM-Scan 점수 필터로 교체. BLOSUM matrix 유지하되 생성 우선순위만 PLM 점수로 재가중. 환경 변경 최소. |

---

## 7. §검증 필요

| 항목 | 상태 | 비고 |
|------|------|------|
| ProteinMPNN의 14aa 환형 펩타이드 fixed_positions 처리 검증 | **미검증** | 문헌에서 단백질 단위 적용이 주류. 14aa 소형 peptide + SS bond 동시 고정 시 backbone 생성 quality 확인 필요. RFpeptides (R8)는 환형 지원 확인됨. |
| ESM-Scan의 14aa 단기 펩타이드 적용 | **미검증** | Totaro 2024는 403aa 효소에만 적용. 소형 펩타이드에서 masked token inference의 context window 충분성 불명. |
| SSTR2-SST14 complex 구조 파일 (PDB) 접근 가능성 | **요확인** | 7YAE (octreotide-SSTR2-Gi) RCSB에 공개 확인. SST14-SSTR2 직결 complex 구조 별도 확인 필요 (Robertson 2022 구조 PDB ID 미확인). |
| DCA (Mazzocato 2024)의 SSTR2 적용 alignment 크기 | **미확인** | SST14 유사체 alignment 데이터셋 크기(37~50 예시)로도 작동하나, 실제 SSTR2 binder 실험 데이터 부재 시 cold-start 가능. |
| ProGen2 / RFpeptides SSTR2 직접 적용 사례 | **미발견** | R9 (state-specific GPCR)도 SSTR2 미확인. paywall/preprint 단계. |

---

## 출처 목록

- [Bryant & Elofsson (2023) - Peptide binder design with inverse folding, Commun. Chem.](https://www.nature.com/articles/s42004-023-01029-7)
- [Dauparas et al. (2022) - ProteinMPNN, Science](https://www.science.org/doi/10.1126/science.add2187)
- [Longwell et al. (2021) - N-terminal GLP-1R saturation mutagenesis, ACS Chem. Bio., PMC8068314](https://pmc.ncbi.nlm.nih.gov/articles/PMC8068314/)
- [Mazzocato et al. (2024) - DCA + ML cyclic peptide inhibitors, ACS Central Science, PMC11672547](https://pmc.ncbi.nlm.nih.gov/articles/PMC11672547/)
- [Totaro et al. (2024) - ESM-Scan, Protein Science, PMC11577456](https://pmc.ncbi.nlm.nih.gov/articles/PMC11577456/)
- [Robertson et al. (2022) - SSTR2 ligand plasticity, Nat. Struct. Mol. Biol., PMC11073612](https://pmc.ncbi.nlm.nih.gov/articles/PMC11073612/)
- [Madani et al. (2023) - ProGen2, Cell Systems](https://www.cell.com/cell-systems/fulltext/S2405-4712(23)00272-7)
- [Bhardwaj et al. (2025) - RFpeptides macrocycles, Nat. Chem. Bio.](https://www.nature.com/articles/s41589-025-01929-w)
- [Savytskyi & Bhatt (2024) - State-specific GPCR peptide, bioRxiv](https://www.biorxiv.org/content/10.1101/2024.11.27.625792v2.full)
- [RCSB PDB 7YAE - Octreotide-SSTR2-Gi complex](https://www.rcsb.org/structure/7YAE)
