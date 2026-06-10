# SSTR1-5 GPCR / MSA 적합성 생물학 검증 보고서

**작성**: reviewer-biology  
**날짜**: 2026-05-12  
**태스크**: T4 — SSTR1-5 GPCR docking precedent + AlphaFoldDB MSA 적합성  
**대상**: PR #14 Boltz-2 cross-validation (alphafold.ebi.ac.uk MSA, SST-14 × SSTR1-5)

---

## §1 GPCR-Peptide Docking에서 MSA Source 권장 (문헌 기반)

### 1.1 AlphaFold2 표준 MSA 파이프라인

AlphaFold2 (Jumper et al. 2021, DOI: 10.1038/s41586-021-03819-2) 기준 4-DB 파이프라인:

| 도구 | 데이터베이스 | 상한 |
|------|------------|------|
| JackHMMER | UniRef90 v2020_01 | 10,000 seq |
| JackHMMER | MGnify v2018_12 | 5,000 seq |
| HHBlits | BFD (2.2B seq) | unlimited |
| HHBlits | UniClust30 v2018_08 | unlimited |

**GPCR 특별 처리 없음.** 표준 4-DB 파이프라인을 class A GPCR에 동일 적용. 신뢰 등급: **HIGH**

### 1.2 ColabFold (MMseqs2) vs AlphaFoldDB Pre-computed MSA

Mirdita et al. 2022 (DOI: 10.1038/s41592-022-01488-1) 벤치마크:

- ColabFoldDB = BFD + MGnify 합성 (7억+ seq), MMseqs2 2-단계 검색
- CASP14 free-modeling TM-score: ColabFold 0.826 vs AF2 표준 0.79 — **동등 이상**
- 속도: AF2 표준 대비 5배 이상

**결론**: ColabFold MSA ≈ AlphaFoldDB MSA (품질 동등). 신뢰 등급: **HIGH**

> **주의**: GPCR 특화 비교 데이터는 문헌상 부재. 위는 범용 벤치마크 결과. 신뢰 등급: **MED** (GPCR 특화 외삽)

### 1.3 GPCR 구조 예측에서 MSA Depth의 결정적 역할

Perez-Benito et al. 2023 (DOI: 10.3389/fmolb.2023.1121962) + AlphaFold-MultiState (PMID: 35510704):

> **MSA source보다 MSA depth 제어가 GPCR 예측 품질에 더 결정적.**

- AlphaFold2 훈련 데이터에 비활성(inactive) GPCR 구조 과대표현 → **Deep MSA 사용 시 비활성 상태로 편향**
- 해결책: **Shallow MSA (sMSA) + GPCRdb 활성 상태 템플릿** 조합
  
| 프로토콜 | MSA | 템플릿 | 활성 상태 정확도 |
|---------|-----|--------|----------------|
| 표준 AF2 | Deep | PDB70 | 비활성 편향 |
| sMSA only | Shallow | 없음 | 불안정 |
| **ActTemp+sMSA** | **Shallow** | **GPCRdb 활성 4개** | **TM helix sub-Å** |

**본 프로젝트 적용**: alphafold.ebi.ac.uk deep MSA를 그대로 사용하면 **SSTR2 활성 상태 (G단백질 결합 형태) 예측 정확도 저하 위험**이 있음.  
신뢰 등급: **HIGH**

### 1.4 Boltz-2 MSA 권장 사항

Wohlwend et al. 2025 (bioRxiv, DOI: 10.1101/2025.06.14.659707):

- Boltz-1/2 공식 기본값: **ColabFold + MMseqs2** (Mirdita et al. 2022 인용)
- GPCR 특별 처리 없음
- §검증 필요: Boltz-2 `prediction.md` 전문 확인 — PDF 파싱 제한으로 MSA 세부 파라미터 미확인

---

## §2 SST-14 × SSTR2 iPTM 0.946 정상 범위 판정

### 2.1 iPTM 공식 기준

Evans et al. 2022 AlphaFold-Multimer 원논문 (`ranking_confidence = 0.8×iPTM + 0.2×pTM`):

| iPTM 범위 | 해석 |
|-----------|------|
| **> 0.8** | **신뢰 가능한 고품질 예측** |
| 0.6 – 0.8 | 회색 지대 |
| < 0.6 | 예측 실패 가능성 높음 |

**판정: iPTM 0.946 → 최상위 신뢰 구간. 구조 geometry 예측 신뢰.**  
신뢰 등급: **HIGH**

### 2.2 iPTM와 결합 친화도 상관관계 — ⚠️ VR-cycle-09 가드 적용

> **⚠️ HEURISTIC-PARTIAL (H-06 적용)**  
> iPTM은 예측된 계면 구조의 좌표 정확도(geometry) 지표이며,  
> 결합 자유에너지(ΔG) 또는 Ki/Kd의 직접 대리 변수가 **아니다.**

- EBI 공식 문서 + Olzemann et al. 2025 (PMC11844409) 명시: iPTM ≠ 결합 강도
- "iPTM 높음 → 결합 세기 강함" 추론은 **근거 없음**
- Boltz-2는 binding affinity 예측 모듈이 별도 구현 (PMC12262699)

**본 프로젝트 적용**:
- SST-14 × SSTR2 iPTM 0.946 → "결합 포켓 geometry 신뢰" 판단 ✓
- iPTM 0.946 → "Ki=0.2 nM을 반영하거나 예측한다" 주장 ✗

신뢰 등급: **HIGH** (상관관계 없음 결론 자체가 HIGH 신뢰)

### 2.3 GPCR-Peptide 복합체에서 iPTM 과대 추정 경향

Frontiers in Bioinformatics 2022 (doi: 10.3389/fbinf.2022.959160):

- 짧은 선형 펩타이드에서 AlphaFold-Multimer iPTM 과대 추정 경향 보고
- "단순 iPTM 하나만으로 품질 판단 비권장"
- Boltz-2의 GPCR-peptide 특화 iPTM 거동: §검증 필요

신뢰 등급: **MED** (AlphaFold-Multimer 관찰 → Boltz 외삽)

---

## §3 SSTR1-5 Pan-receptor 패턴 재현 신뢰성 평가

### 3.1 실측 vs 예측 비교

| SSTR | 실측 Ki (nM) | Boltz iPTM | Ki 순위 | iPTM 순위 |
|------|------------|-----------|--------|----------|
| SSTR1 | 0.4 | 0.975 | 2위 | 1위 |
| SSTR2 | **0.2** | 0.946 | 1위(최강) | 4위 |
| SSTR3 | 0.8 | 0.958 | 3위 | 2위 |
| SSTR4 | 1.6 | 0.956 | 5위(최약) | 3위 |
| SSTR5 | 0.3 | 0.913 | 2~3위 | 5위(최저) |

Ki 출처: Reubi et al. 1994 / 2000 (SSTR1-5 pharmacology) — 신뢰 등급 HIGH  
Boltz iPTM: PR #14 보고값

### 3.2 Pan-receptor 패턴 재현 실패 분석

> **⚠️ HEURISTIC-PARTIAL — iPTM 분산 0.062로 Ki 8배 차이 구분 불가**

- **Ki 범위**: 0.2 nM ~ 1.6 nM = **8배 차이**
- **iPTM 범위**: 0.913 ~ 0.975 = **0.062 분산** (최고-최저 차이 6.2%)

**결정적 불일치**:
- SSTR2: Ki 최강(0.2 nM), iPTM 4위(0.946) → **역순위**
- SSTR4: Ki 최약(1.6 nM), iPTM 중간(0.956) → **과대 추정**
- SSTR5: Ki 강(0.3 nM), iPTM 최저(0.913) → **과소 추정**

**결론**: 현재 iPTM 분포는 실측 Ki 선택성 패턴을 재현하지 **못한다.**  
iPTM이 binding geometry 신뢰도 지표임을 고려할 때, 이는 예상된 결과이지 방법론적 실패가 아님.  
그러나 "Boltz iPTM으로 SSTR subtype 선택성 예측 가능" 주장은 현재 데이터로는 지지되지 않음.

신뢰 등급: **HIGH** (패턴 불일치 자체) / **HIGH** (원인 해석)

---

## §4 선행 cryo-EM 구조 대비 검증 가능성

### 4.1 주요 SSTR 구조 데이터베이스

| PDB ID | 수용체 | 리간드 | 해상도 | 출처 논문 |
|--------|--------|--------|--------|---------|
| **7T10** | SSTR2 | SST-14 + Gi3 | 2.50 Å | Robertson et al. 2022, doi: 10.1038/s41594-021-00720-z |
| **7T11** | SSTR2 | Octreotide + Gi3 | cryo-EM | Robertson et al. 2022 |
| **7WJ5** | SSTR2 | SST-14 + Gi3 | — | Zhao et al. 2022, doi: 10.7554/eLife.76823 |
| **7XNA** | SSTR2 | CYN 154806 (길항제) | 2.65 Å | Zhao W. et al. 2022, doi: 10.1038/s41422-022-00679-x |
| **7XNB** | SSTR3 | — | — | Zhao W. et al. 2022 |
| **7XMU** | SSTR4 | — | — | Zhao W. et al. 2022 |
| **7XMX** | SSTR5 | — | — | Zhao W. et al. 2022 |
| **7Y34** | SSTR5 | — | — | Cell Research 2022 |

### 4.2 SST-14 결합 핵심 잔기 (SSTR2 7T10/7WJ5 기준)

**결합 포켓 핵심 잔기 — chain A**:

| 잔기 | 위치 | 상호작용 | 리간드 파트너 |
|------|------|---------|------------|
| Asp122 | TM2 | salt bridge (~2.7 Å) | Lys9 (SST-14 FWKT 중 K) |
| Gln126 | TM2 | H-bond | Lys9 |
| Tyr205 | TM5 | aromatic stacking | Phe7 (SST-14 중 F) |
| Phe272 | TM6 | hydrophobic | Trp8 (SST-14 중 W) |
| Phe294 | TM7 | hydrophobic | Trp8 |
| Ile177, Phe208, Thr212 | TM4-5 | hydrophobic pocket | Trp8 |

**SST-14 이황화결합 (Cys3–Cys14)**: 세포외면 표면에 노출 — 결합 포켓 내부가 아님  
신뢰 등급: **HIGH** (cryo-EM 직접 관찰)

### 4.3 Subtype 선택성 구조 기반

Zhao W. et al. 2022 (Cell Research, paywall):

- **ECL2 (Extracellular Loop 2) 형태 차이**가 subtype 선택성의 주요 결정 인자
- Octreotide (SSTR2 편향) vs Pasireotide (SSTR5 편향): ECL2 구조 차이로 설명
- TM helices 내부 서열 유사도는 높으나, ECL2 loop 길이/형태가 크게 다름

**Boltz 예측 vs cryo-EM RMSD 비교 가능성**:  
7T10 (SST-14 × SSTR2 Gi3)와 Boltz 예측 구조를 PyMOL align으로 RMSD 계산 가능.  
7XNA는 길항제 결합 비활성 구조 — Boltz가 활성 상태 예측 시 직접 비교에 한계 있음.  
신뢰 등급: **MED** (비교 가능하나 상태 차이 보정 필요)

---

## §5 SSTR Paralog Contamination 위험 평가

### 5.1 AlphaFoldDB MSA 구성과 Paralog 포함 여부

AlphaFold2 파이프라인 (Jumper et al. 2021):

> **UniRef90 기반 JackHMMER는 sequence similarity ≥40% 수준의 모든 homolog 포함 — paralog 필터링 없음.**

SSTR1-5는 같은 GPCR subfamily로 서로의 MSA에 **의도적으로** 포함됨. 신뢰 등급: **HIGH**

### 5.2 SSTR1-5 서열 유사도

| 비교 쌍 | Subfamily | 전체 identity | 비고 |
|---------|-----------|-------------|------|
| SSTR1 ↔ SSTR4 | SRIF2 | ~70% | 최고 유사도 |
| SSTR2 ↔ SSTR3 | SRIF1 | ~50–57% | 동일 subfamily |
| SSTR2 ↔ SSTR5 | SRIF1 | ~50–55% | 동일 subfamily |
| SSTR1 ↔ SSTR2 | 간 subfamily | ~39–47% | 최저 유사도 |

출처: Ma et al. 2020 ACS Omega (doi: 10.1021/acsomega.0c02847) + PMC11630666  
신뢰 등급: **HIGH**

> **TM domain 구조적 차이**: SSTR2 TM5 = 36 aa (타 subtype = 41 aa), SSTR4 TM6 = 4-5 aa 짧음.  
> MSA gap 처리가 co-evolutionary signal 해석을 복잡하게 함.

### 5.3 Paralog Contamination이 선택성 예측에 미치는 영향

핵심 메커니즘:

1. **공통 보존 잔기 신호 증폭**: TM1-7에 공유되는 GPCR 서명 잔기 (DRY motif, NPxxY 등)의 co-evolutionary signal이 SSTR-specific 신호를 희석
2. **ECL2 다양성 신호 감쇠**: subtype 선택성의 핵심 결정 요소인 ECL2 형태 차이가 paralog 중복 신호에 묻힘
3. **AlphaFold homolog-bias**: 가까운 homolog가 다른 구조를 취할 때 잘못된 구조 예측 경향 보고 (Current Opinion in Structural Biology 2024, doi: 10.1016/j.sbi.2024.102805)

**Perez-Benito et al. 2023 (doi: 10.3389/fmolb.2023.1121962)**: Shallow MSA + curated template 조합이 GPCR subtype-specific 예측 정확도 향상.

**위험 등급**: **MED-HIGH** — 메커니즘 HIGH 신뢰, SSTR 직접 실험 데이터 없어 MED  

### 5.4 Mitigation 전략

| 방법 | 효과 | 구현 |
|------|------|------|
| A3M paralog 직접 제거 | HIGH | SSTR1/3/4/5 UniProt ID row 필터링 |
| Shallow MSA (`--max-seq 512`) | HIGH | ColabFold 파라미터 |
| GPCRdb 활성 상태 템플릿 주입 | HIGH | sMSA + ActTemp 프로토콜 |
| AFProfile (사후 교정) | MED | gradient descent bias 보정 |

---

## §6 종합 판정 — alphafold.ebi.ac.uk MSA가 SSTR1-5 Cross-validation에 적합한가?

### 6.1 세부 항목별 판정

| 검증 항목 | 판정 | 신뢰 등급 | 근거 |
|---------|------|---------|------|
| AlphaFoldDB MSA 품질 (구조 예측) | ✅ 충분 | HIGH | ColabFold 동등 성능 |
| GPCR 활성 상태 편향 위험 | ⚠️ 위험 | HIGH | Deep MSA = 비활성 편향 |
| iPTM 0.946 구조 신뢰도 | ✅ 고품질 | HIGH | >0.8 최상위 구간 |
| iPTM → Ki 대리 변수 사용 | ❌ 불가 | HIGH | VR-cycle-09 / H-06 |
| SSTR2 Ki 선택성 재현 | ❌ 실패 | HIGH | 순위 역전 확인 |
| Paralog contamination 위험 | ⚠️ 존재 | MED-HIGH | 메커니즘 확인, 직접 실험 없음 |
| cryo-EM 검증 가능성 | ✅ 가능 | MED | 7T10/7WJ5 활용, 상태 보정 필요 |

### 6.2 종합 결론

> **alphafold.ebi.ac.uk MSA는 SSTR1-5 구조 geometry 예측에는 충분하나,  
> subtype 선택성 정량 평가(Ki 차이 구분)에는 부적합하다.**

**적합 (PASS)**: Boltz iPTM 값의 절대적 신뢰도 확인, 결합 포켓 형태 예측  
**부적합 (FAIL)**: iPTM으로 Ki 0.2~1.6 nM 범위의 SSTR subtype 선택성 구분  
**조건부 개선**: sMSA + GPCRdb 활성 템플릿 + paralog 제거 조합 시 재평가 필요

### 6.3 권고 사항

1. **iPTM 해석 제한 명시 의무**: PR #14 본문에 "iPTM = geometry confidence, not affinity proxy" 추가
2. **Selectivity 정량 평가**: 별도 FEP (Free Energy Perturbation) 또는 MM-GBSA 계산 필요
3. **sMSA 실험**: SSTR2 × SST-14 결합에서 depth=512 shallow MSA 재실행 비교 권장
4. **Paralog 제거 A/B 실험**: AlphaFoldDB MSA에서 SSTR1/3/4/5 row 제거 후 SSTR2 예측 품질 비교

---

## §검증 필요

| ID | 항목 | 방법 |
|----|------|------|
| VB-01 | Boltz-2 `prediction.md` 전문 MSA 파라미터 | GitHub/arXiv PDF 직접 확인 |
| VB-02 | SSTR2 특화 MSA depth 실험 문헌 | PubMed SSTR2 + AlphaFold + MSA 검색 |
| VB-03 | AlphaFoldDB SSTR2(P30874) MSA raw 파일 paralog 포함 확인 | EBI AlphaFold API 다운로드 |
| VB-04 | 7XNB/7XMU/7XMX 상세 결합 잔기 | Cell Research paywall full text 또는 PDB 직접 열람 |
| VB-05 | Boltz-2 GPCR 벤치마크 RMSD 데이터 | Boltz-2 paper supplementary |
| VB-06 | SSTR2 × SST-14 Boltz 예측 vs 7T10 RMSD 직접 계산 | PyMOL align 수행 |

---

## 참고 문헌

| DOI / ID | 제목 | 신뢰도 |
|---------|------|--------|
| 10.1038/s41586-021-03819-2 | Jumper et al. 2021 AlphaFold2 | HIGH |
| 10.1038/s41592-022-01488-1 | Mirdita et al. 2022 ColabFold | HIGH |
| 10.3389/fmolb.2023.1121962 | Perez-Benito et al. 2023 GPCR sMSA | HIGH |
| PMID: 35510704 | Heo & Feig 2022 AlphaFold-MultiState | HIGH |
| 10.1093/nar/gkac1013 | Pandy-Szekeres 2023 GPCRdb | HIGH |
| 10.1038/s41594-021-00720-z | Robertson et al. 2022 SSTR2 7T10/7T11 | HIGH |
| 10.7554/eLife.76823 | Zhao et al. 2022 SSTR2 7WJ5 | HIGH |
| 10.1038/s41422-022-00679-x | Zhao W. et al. 2022 SSTR1-5 7XNA 등 | MED (paywall) |
| 10.3389/fbinf.2022.959160 | Frontiers Bioinf 2022 peptide-GPCR | MED |
| PMC11844409 | Olzemann et al. 2025 iPTM 한계 | HIGH |
| 10.1016/j.sbi.2024.102805 | Curr Op Struct Biol 2024 homolog bias | MED |
| 10.1021/acsomega.0c02847 | Ma et al. 2020 SSTR identity | HIGH |
| 10.1101/2025.06.14.659707 | Wohlwend et al. 2025 Boltz-2 | MED |
| PDB 7T10 | SSTR2 + SST-14 + Gi3 cryo-EM | HIGH |
| PDB 7WJ5 | SSTR2 + SST-14 + Gi3 cryo-EM | HIGH |
| PDB 7XNA | SSTR2 + 길항제 | MED |
