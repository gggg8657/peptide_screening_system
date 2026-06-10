# Serum Stability & ADMET 예측 도구 종합 보고서

**작성일**: 2026-03-13
**목적**: SST-14 유사체 (14aa 사이클릭 펩타이드, Cys3-Cys14 SS bond, MW ~1600) 파이프라인 적용 가능성 평가

---

## Executive Summary

11개 도구를 5개 기준(사용 가능성, 용이성, 시스템 적합성, 온프레미스 가능성, 파이프라인 적용 가능성)으로 평가한 결과:

- **즉시 적용 가능**: `peptides` (pip), `modlAMP` (pip) — 서열 기반 physicochemical surrogate
- **조건부 적용**: `admet-ai` (pip, SMILES 변환 필요), `PRODIGY` (pip, 구조 기반 ΔG 검증)
- **참조 DB 활용**: PEPlife2 REST API (실험 반감기 데이터 조회)
- **부적합/통합 불가**: 나머지 전부 (소분자 전용, 웹 전용, API 미제공 등)

**핵심 결론**: 6개 ADMET 도구 모두 소분자(MW < 500) 훈련 데이터 기반이며, MW ~1600 사이클릭 펩타이드는 Applicability Domain 밖. 현재 `pharma_properties.py`의 문헌 기반 물리화학 계산이 SST-14 유사체에 훨씬 적합.

---

## Part 1. Serum Stability / Peptide Property 도구 (5개)

### 1.1 PepCalc / Peptide2.0

| 항목 | 내용 |
|------|------|
| **개발** | Innovagen AB (스웨덴) |
| **기능** | MW, pI, ε280, net charge, 용해도 추정, pH 적정 곡선 |
| **알고리즘** | pKa 기반 Henderson-Hasselbalch, Kyte-Doolittle 소수성 스케일 |
| **입력/출력** | 아미노산 서열 → 물리화학적 수치 |
| **접근 방식** | 웹 전용 (pepcalc.com). peptide2.0.com은 ECONNREFUSED |
| **온프레미스** | 불가 (소스 비공개, 상용) |
| **Serum stability** | **없음** — property 계산만 |
| **사이클릭 지원** | 없음 (선형 전용, disulfide 미반영) |
| **논문** | 독립 논문 없음 |

**평가**: 우리 `pharma_properties.py`가 이미 동일 기능을 문헌 기반으로 구현. 추가 가치 없음.

---

### 1.2 PEPlife2 / PlifePred (IIITD Raghava 그룹)

| 항목 | 내용 |
|------|------|
| **개발** | IIITD, Raghava 연구실 |
| **PEPlife2** | 치료용 펩타이드 반감기 실험 데이터 **DB** (혈청/혈장/혈액) |
| **PlifePred** | 반감기 **regression 예측** 웹서버 |
| **알고리즘** | PaDEL descriptor + ML (r = 0.743, 163개 자연 펩타이드) |
| **입력/출력** | 서열 → 반감기 (시간 단위) |
| **REST API** | PEPlife2 DB 조회용 API 있음 (`api.php?dataType=X&dataValue=Y`) |
| **온프레미스** | 불가 (GitHub 레포 404, 소스 비공개) |
| **Serum stability** | **있음 (유일한 regression 도구)** |
| **사이클릭 지원** | DB에 일부 cyclic 데이터 있으나, 예측 모델은 사이클릭 미지원 |
| **논문** | Mathur et al., *Sci. Rep.* 2016; *PLoS One* 2018 |

**평가**: **유일하게 혈청 반감기 regression을 제공**하지만 훈련 데이터 261개로 극소규모. 사이클릭 펩타이드 외삽 위험. DB 조회는 best-effort로 활용 가능.

---

### 1.3 Protein-sol (Manchester 대학)

| 항목 | 내용 |
|------|------|
| **개발** | Warwicker 그룹, Manchester 대학 |
| **기능** | 용해도(solubility) 예측, 표면 전하/소수성 패치 계산 |
| **알고리즘** | AA 조성 기반 회귀 (Sequence), FDPB 전기정역학 (Patches) |
| **입력/출력** | FASTA 서열 or PDB → 용해도 점수 (0-1) |
| **온프레미스** | 부분 (배치용 로컬 스크립트 다운로드 가능) |
| **Serum stability** | **없음** — 용해도 전용 |
| **사이클릭 지원** | 없음 (선형 가정) |
| **논문** | Hebditch et al., *Bioinformatics* 2017 (~200 citations) |

**평가**: 용해도 검증 보조 도구로 참고 가능하나 핵심 니즈(serum stability)와 무관.

---

### 1.4 DPPred / PepAnalyzer

| 항목 | 내용 |
|------|------|
| **DPPred** | 독립 도구로 확인 불가. peptide.tools 사이트 timeout |
| **PepAnalyzer** | PubMed/Google Scholar 검색 결과 없음. 공개 도구로 존재하지 않음 |
| **대안 발견** | **modlAMP** — `pip install modlamp`, MIT 라이선스 |

**modlAMP 상세**:

| 항목 | 내용 |
|------|------|
| **기능** | AA descriptor 계산, 소수성 모멘트, 서열 생성, AMP 분류, 시각화 |
| **설치** | `pip install modlamp` (순수 Python, 의존성 최소) |
| **온프레미스** | **완전 가능** |
| **Serum stability** | 없음 (descriptor surrogate만) |
| **논문** | Müller et al., *Bioinformatics* 2017 |

---

### 1.5 HADDOCK Stability (github.com/haddocking)

| 항목 | 내용 |
|------|------|
| **확인 결과** | Serum stability 전용 도구 없음 |
| **가장 관련 도구** | **PRODIGY** — 단백질-단백질/리간드 결합 친화도 예측 |
| **PRODIGY 기능** | PDB 복합체 → ΔG (kcal/mol), Kd (M) |
| **설치** | `pip install prodigy-prot` |
| **온프레미스** | **완전 가능** |
| **펩타이드 적용** | 복합체 PDB 필요. FlexPepDock 결과로 ΔG 독립 검증 가능 |
| **Serum stability** | **없음** — 결합 친화도만 |
| **논문** | Vangone & Bonvin, *eLife* 2015 (3000+ citations) |

---

## Part 2. ADMET 도구 (6개)

### 종합 비교표

| 도구 | 알고리즘 | 엔드포인트 | API | 온프레미스 | 배치 | Half-life | 펩타이드 적합 |
|------|----------|-----------|-----|-----------|------|-----------|-------------|
| **ADMETlab 3.0** | DMPNN-Des (DL) | 119개 | REST | 불가 | 가능 | 있음(추정) | **낮음** |
| **Deep-PK** | D-MPNN (DL) | 73개 | REST | 불가 | 가능 | 있음 | **낮음** |
| **pkCSM** | Graph signature (ML) | ~30개 | 없음 | 불가 | 가능 | 없음 | **낮음** |
| **admetSAR 2.0** | QSAR/ML | ~50개 | 없음 | 불가 | 20개 | 있음 | **낮음** |
| **ProTox-3.0** | Similarity+ML | 61개 | 없음 | 불가 | 불명확 | 없음 | 조건부 |
| **SwissADME** | Rule-based+ML | ~40개 | 없음 | 불가 | 가능 | 없음 | **없음** |

### 공통 제한사항 (전 도구)

1. **훈련 데이터 편향**: 전부 소분자 (MW < 500) 데이터셋으로 훈련. MW ~1600 사이클릭 펩타이드는 AD 밖
2. **메커니즘 불일치**: 소분자 half-life (대사/배설) ≠ 펩타이드 serum stability (프로테아제 분해). 개념 자체가 다름
3. **Cys-Cys SS bond**: SMILES로 표현은 가능하지만 훈련 예시 부재
4. **온프레미스 전멸**: 6개 모두 로컬 설치 불가 (소스 미공개)

### 개별 주요 이슈

- **ADMETlab 3.0**: TLS 인증서 만료로 서버 접속 불가 (2026-03 기준)
- **Deep-PK**: REST API 있어 자동화 가능하나 소분자 명시
- **pkCSM**: API 미공개, 2015년 모델로 사실상 Deep-PK에 대체됨
- **admetSAR**: 배치 20개 제한, API 없음
- **ProTox-3.0**: 독성(T)에 편중, ADME 예측 약함
- **SwissADME**: MW 150-500 명시, 펩타이드 입력 시 전 rule violation

---

## Part 3. 추가 발굴 도구

조사 과정에서 리스트에 없던 유용한 도구 2개 발견:

### 3.1 admet-ai (swansonk14)

| 항목 | 내용 |
|------|------|
| **GitHub** | https://github.com/swansonk14/admet_ai |
| **설치** | `pip install admet-ai` |
| **Python API** | `from admet_ai import ADMETModel` — 직접 import |
| **오프라인** | **가능** (설치 후 인터넷 불필요) |
| **모델** | Chemprop v2 GNN, TDC 데이터셋 41개 ADMET 속성 |
| **입력** | SMILES (1,000개 배치 처리) |
| **Python** | 3.11+ 필요 |
| **펩타이드** | SMILES 변환 필요, AD 밖이지만 상대 비교 참고 가능 |

### 3.2 peptides (PyPI)

| 항목 | 내용 |
|------|------|
| **설치** | `pip install peptides` |
| **Python API** | 직접 import, 순수 Python |
| **오프라인** | **완전 오프라인** (의존성 0) |
| **계산** | instability index, aliphatic index, pI, hydrophobicity, charge, Boman index 등 |
| **펩타이드** | **서열 직접 입력** — 유일하게 SMILES 불필요 |

---

## Part 4. 통합 평가 매트릭스

### 5대 평가 기준 (각 5점 만점)

| 도구 | 사용 가능성 | 용이성 | 시스템 적합성 | 온프레미스 | 파이프라인 통합 | **총점** |
|------|-----------|--------|-------------|-----------|--------------|---------|
| **peptides** (PyPI) | 5 | 5 | 4 | 5 | 5 | **24** |
| **modlAMP** | 5 | 4 | 3 | 5 | 4 | **21** |
| **PRODIGY** | 4 | 3 | 4 | 5 | 3 | **19** |
| **admet-ai** | 4 | 3 | 2 | 5 | 3 | **17** |
| **PEPlife2 DB** | 3 | 3 | 4 | 1 | 2 | **13** |
| **Deep-PK** | 3 | 3 | 1 | 1 | 2 | **10** |
| **ADMETlab 3.0** | 1 | 2 | 1 | 1 | 1 | **6** |
| **Protein-sol** | 3 | 2 | 2 | 2 | 1 | **10** |
| **PepCalc** | 2 | 3 | 2 | 1 | 1 | **9** |
| **pkCSM** | 2 | 2 | 1 | 1 | 1 | **7** |
| **admetSAR** | 2 | 2 | 1 | 1 | 1 | **7** |
| **ProTox-3.0** | 2 | 2 | 1 | 1 | 1 | **7** |
| **SwissADME** | 2 | 3 | 0 | 1 | 1 | **7** |

### 평가 기준 설명

- **사용 가능성**: 현재 접속/설치 가능한가 (서버 다운, 레포 404 등)
- **용이성**: 설치/사용 난이도 (pip 한줄 vs 복잡한 세팅)
- **시스템 적합성**: 14aa 사이클릭 펩타이드 (MW ~1600)에 적용 가능한가
- **온프레미스**: 오프라인/로컬 실행 가능한가 (테더링 환경 고려)
- **파이프라인 통합**: runner.py iteration loop 안에서 Python import로 호출 가능한가

---

## Part 5. 통합 비교표 — 전 도구 + 현재 구현 정확도

### 5.1 전체 도구 종합 판정

| # | 도구 | 유형 | 판정 | 부적합 사유 / 활용 방식 | 대체안 | 비고 |
|---|------|------|------|----------------------|--------|------|
| 1 | **PepCalc / Peptide2.0** | 펩타이드 property | **부적합** | 웹 전용 (API 없음), 소스 비공개, 사이클릭 미지원 | `pharma_properties.py`가 동일 기능 구현 완료 | peptide2.0.com ECONNREFUSED |
| 2 | **PEPlife2 DB** | 혈청 반감기 DB | **참조용** | 온프레미스 불가, GitHub 404 | REST API로 best-effort 조회 가능 | 유일한 펩타이드 반감기 DB |
| 3 | **PlifePred** | 혈청 반감기 예측 | **부적합** | 훈련 261개 극소, 사이클릭 미지원, 웹 전용 | 대안 없음 (serum stability regression 자체가 미성숙 분야) | r = 0.743 (선형 펩타이드) |
| 4 | **Protein-sol** | 용해도 | **부적합** | serum stability와 무관, 선형 가정 | pharma WW 스케일로 membrane interaction 대리 | — |
| 5 | **DPPred** | 불명 | **부적합** | peptide.tools 사이트 timeout, 도구 존재 미확인 | — | — |
| 6 | **PepAnalyzer** | 불명 | **부적합** | PubMed/Scholar 검색 결과 없음, 존재 자체 미확인 | — | — |
| 7 | **ADMETlab 3.0** | 소분자 ADMET | **부적합** | TLS 인증서 만료 서버 다운, 온프레미스 불가, MW<500 전용 | — | 119 endpoints, 전부 소분자 |
| 8 | **Deep-PK** | 소분자 ADMET | **부적합** | 온프레미스 불가, MW<500 전용 | REST API 존재하나 AD 밖 결과 신뢰 불가 | D-MPNN 모델 |
| 9 | **pkCSM** | 소분자 ADMET | **부적합** | API 없음, 2015년 모델 (Deep-PK에 대체됨), MW<500 전용 | — | Graph signature |
| 10 | **admetSAR 2.0** | 소분자 ADMET | **부적합** | API 없음, 배치 20개 제한, MW<500 전용 | — | QSAR/ML |
| 11 | **ProTox-3.0** | 소분자 독성 | **부적합** | 독성(T) 편중, ADME 약함, MW<500 전용 | — | API 없음 |
| 12 | **SwissADME** | 소분자 ADME | **부적합** | MW 150-500 명시, 펩타이드 입력 시 전 rule violation, API 없음 | — | rule-based |
| 13 | **peptides** (PyPI) | 펩타이드 property | **활용 중** | `pip install`, 오프라인, 서열 직접 입력 | — | **검증 ground truth로 채택** |
| 14 | **modlAMP** | AMP descriptor | **Tier 1 적용 가능** | `pip install`, 오프라인, MIT | Eisenberg μH 등 추가 feature 제공 | 소수성 모멘트 등 |
| 15 | **admet-ai** | 소분자 ADMET | **Tier 2 조건부** | `pip install`, 오프라인 가능, 단 SMILES 변환 필요 | 41개 ADMET 속성, AD 밖이지만 상대 비교 참고 | Python 3.11+ 필요 |
| 16 | **PRODIGY** | 결합 친화도 | **Tier 3 구조 검증** | `pip install prodigy-prot`, PDB 복합체 필요 | FlexPepDock ΔG 독립 검증 | eLife 2015, 3000+ citations |
| 17 | **pepADMET** | 펩타이드 전용 ADMET | **Tier 1.5 (독성 즉시, 나머지 중기)** | 36,643 데이터, 19 ADMET endpoints, 17 모델. 사이클릭/SS bond/변형 펩타이드 지원. 2-50aa (MW ~200-5000) | GitHub 독성 모델 (.pth) 즉시 활용, permeability/half-life/BBB/LogD는 웹 API 또는 모델 재현 | JCIM 2026, 66, 936-946. Tan et al. (Central South Univ.) GitHub: ifyoungnet/pepADMET |

### 5.2 ADMET 도구 공통 부적합 사유

6개 소분자 ADMET 도구(#7-12)가 모두 부적합한 근본 이유:

> **주의**: 아래 부적합 사유는 **소분자 ADMET 도구(#7-12)에만 해당**. #17 pepADMET은 펩타이드 전용 플랫폼으로 이 사유들이 대부분 해소됨 (36,643 펩타이드 데이터, 사이클릭/SS bond 지원, 2-50aa MW 범위, 독성 모델 GitHub 공개).

| 문제 | 설명 |
|------|------|
| **Applicability Domain** | 전부 소분자 (MW < 500) 데이터셋으로 훈련. SST-14 MW ~1600은 AD 밖 |
| **메커니즘 불일치** | 소분자 half-life = 간 대사 + 신장 배설. 펩타이드 serum stability = 프로테아제 분해. 개념 자체가 다름 |
| **SS bond 표현** | SMILES로 Cys-Cys SS bond 표현은 가능하나 훈련 예시 부재 |
| **온프레미스 전멸** | 6개 전부 소스 비공개, 로컬 설치 불가 |

---

## Part 6. 현재 구현 (`pharma_properties.py`) 정확도 검증 결과

### 6.1 peptides 패키지 대비 수치 정확도 (수정 후)

검증 서열 6종: SST-14, All-A(AAAAAAAAAA), Charged(KKKKDDDDEE), Hydrophobic(ILLLVVFFWW), M-rich(MMFMMTMMRR), Short(ACDEF)

| # | Method | 원본 연도 | 검증 결과 (6서열) | peptides 대비 오차 | 현행성 (2026) |
|---|--------|---------|-----------------|------------------|-------------|
| 1 | GRAVY (Kyte-Doolittle) | 1982 | **6/6 완벽 일치** | 0.00% | gold standard (44년 표준) |
| 2 | Boman Index (RW) | 1988/2003 | **6/6 완벽 일치** | 0.00% | 유일한 단일 지표, 대안 없음 |
| 3 | Instability Index (DIWV) | 1990 | **6/6 완벽 일치** | 0.00% | ExPASy ProtParam 표준 |
| 4 | Aliphatic Index | 1980 | **6/6 완벽 일치** | 0.00% | 열안정성 surrogate |
| 5 | pI (Lehninger bisection) | 1993 | **6/6 완벽 일치** | <0.05 pH | IPC 2.0 (2021) 업데이트 고려 |
| 6 | ε280 (Pace) | 1995 | 내부 일치 | GT 없음 | 변경 불필요 |
| 7 | N-end Rule (Varshavsky) | 1996 | 내부 일치 | GT 없음 | 참고용 (cyclic 펩타이드 N-말단 미노출) |
| 8 | Hydrophobic Moment (Eisenberg) | 1982 | **6/6 완벽 일치** | 0.00% | 막 투과 예측 표준 |
| 9 | Wimley-White | 1996 | 내부 일치 | 스케일 상이 | POPC 인터페이스 표준 |
| 10 | Net Charge (H-H) | — | **6/6 완벽 일치** | <0.01% | **SS bond Cys 보정 필요** |
| 11 | Protease Sites | — | 내부 일치 (3효소) | GT 없음 | DPP-IV 추가 고려 |
| 12 | BLOSUM62 | 1992 | 설계 차이 (양 파일) | GT 없음 | 표준 치환 행렬 |
| 13 | Metal Coordination | 1998 | 내부 일치 | GT 없음 | Ga3+ D/E 배위 추가 고려 |

### 6.2 수정 전후 비교 (발견·수정한 버그)

| 위치 | 버그 유형 | 건수 | 최대 오차 | 수정 상태 |
|------|----------|------|----------|----------|
| pharma DIWV 테이블 | copy-paste 전사 오류 | 12 | RR: 64.82 (II 단위) | ✅ 수정 완료 |
| pharmacology DIWV 테이블 | 값 오류 | 4 | YT: 41.09 | ✅ 수정 완료 |
| 양쪽 RW H/S/W 값 | 문헌값 불일치 | 3+4 | H: 2.60 kcal/mol | ✅ 수정 완료 |
| pharmacology Boman 부호 | `-sum/n` → `+sum/n` | 1 | 방향 반전 | ✅ 수정 완료 |
| N-end Rule P 불일치 | 양 파일 값 다름 | 1 | — | ✅ 통일 완료 |
| **SS bond Cys pI 미보정** | 기능 미구현 | — | pI ~0.2-1.1 pH | ❌ 미수정 (P0) |
| **MW 미구현** | 기능 없음 | — | — | ❌ 미수정 (P1) |

### 6.3 기능 커버리지 비교 (pharma_properties.py vs 외부 도구)

| 기능 | pharma_prop | pharmacology | peptides | PepCalc | 비고 |
|------|:-----------:|:------------:|:--------:|:-------:|------|
| GRAVY | ✓ | ✓ | ✓ | ✓ | 4자 동일 결과 |
| Boman Index | ✓ | ✓ | ✓ | — | 3자 동일 결과 |
| Instability Index | ✓ | ✓ | ✓ | — | 3자 동일 결과 |
| Aliphatic Index | ✓ | ✓ | ✓ | — | 3자 동일 결과 |
| pI | ✓ | ✓ | ✓ | ✓ | Lehninger scale 기준 일치 |
| ε280 | ✓ | ✓ | — | ✓ | SS bond 반영 |
| N-end Rule | ✓ | ✓ | — | — | 도메인 특화 |
| Hydrophobic Moment | ✓ | ✓ | ✓ | — | 3자 동일 결과 |
| Wimley-White | ✓ | ✓ | 스케일 다름 | — | POPC vs pH8 |
| Net Charge | ✓ | ✓ | ✓ | ✓ | 3자 동일 결과 |
| Protease Sites | 3효소 | 4효소 | — | — | pepsin: pharmacology만 |
| BLOSUM62 | ✓ | ✓ | — | — | 설계 차이 있음 |
| Metal Coordination | ✓ | ✓ | — | — | 방사성의약품 특화 |
| MW | **—** | **—** | ✓ | ✓ | **미구현** |
| SS bond pI 보정 | **—** | **—** | **—** | **—** | **전부 미지원** |
| 5대 구조 규칙 | ✓ | — | — | — | FWKT, K9-D122 등 |
| pH profile (다중 pH) | — | ✓ | — | ✓ | |
| Batch analyze | ✓ | — | — | — | 파이프라인 전용 |
| Input validation | ✓ | — | — | — | 빈 서열/비표준 잔기 방어 |
| Sequence entropy | — | — | ✓ | — | |
| ESI m/z | — | — | ✓ | — | 방사성의약품 설계 시 유용 |

---

## Part 7. 결론

### 핵심 판정

1. **외부 ADMET 도구 (6개)**: MW ~1600 사이클릭 펩타이드에 **전부 부적합**. Applicability Domain 밖이며 메커니즘 자체가 다름 (간 대사 vs 프로테아제 분해).

2. **외부 펩타이드 도구 (5개)**: PepCalc은 자체 구현 완료로 불필요. PEPlife2 DB만 참조용 가치. DPPred/PepAnalyzer는 존재 미확인.

3. **현재 구현 정확도**: lookup table 버그 16건 수정 후 **peptides ground truth 대비 8개 메서드 완벽 일치**. 문헌 기반 방법론 자체는 2026년 기준으로도 gold standard (10/13).

4. **방법론 현행성**: "올드한 방식"이 아니라 "검증된(established) 표준". 문제는 메서드가 아니라 전사 오류였음.

### 남은 작업

| 우선순위 | 항목 | 이유 |
|---------|------|------|
| **P0** | SS bond Cys pI/charge 보정 | pI ~0.2-1.1 pH 오차. 신장 클리어런스 판단 직결 |
| **P1** | MW 구현 | 방사성의약품 MW 검증 필수 |
| **P1** | BLOSUM62 설계 통일 | 양쪽 결과 해석 불일치 |
| **P2** | pharmacology → pharma_properties 래핑 | 중복 제거, 재발 방지 |
| **P3** | DPP-IV protease 추가 | 혈청 안정성 커버리지 확장 |
| **P3** | Ga3+ Metal coord D/E 추가 | 68Ga 킬레이션 정확도 |

### Tier별 적용 계획

| Tier | 도구 | 설치 | 역할 |
|------|------|------|------|
| **Tier 1 (즉시)** | `peptides` | `pip install peptides` | cross-validation GT, MW/m_z 보완 |
| **Tier 1 (즉시)** | `modlAMP` | `pip install modlamp` | AA descriptor 추가 feature |
| **Tier 1.5 (독성 즉시)** | `pepADMET` (독성) | GitHub clone + DGL 0.4.3 + PyTorch | binary/6-class toxicity, neurotoxicity, HC_50 — **펩타이드 전용, SS bond 지원** |
| **Tier 2 (중기)** | `pepADMET` (ADME) | 웹 API 자동화 또는 모델 재현 | permeability (5 cell lines), half-life (5 tissues), BBB, LogD_7.4, F |
| **Tier 2 (중기)** | `admet-ai` | `pip install admet-ai` (Python 3.11, 별도 env) | SMILES 변환 후 ADMET 상대 비교 |
| **Tier 3 (구조)** | `PRODIGY` | `pip install prodigy-prot` | FlexPepDock ΔG 독립 검증 |
| **Tier 4 (참조)** | PEPlife2 | REST API (네트워크) | 실험 반감기 best-effort 조회 |
