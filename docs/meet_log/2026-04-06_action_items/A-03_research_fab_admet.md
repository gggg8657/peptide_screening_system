# A-03 Fab-ADMET 조사 보고 (researcher)

## 조사일: 2026-05-20
## 조사자: researcher subagent (claude-sonnet-4-6)

> **상위 문서**: `docs/meet_log/2026-04-06_action_items/A-03_Fab-ADMET_validation.md` (기존 액션 아이템 정의)
> **이전 조사**: `_workspace/release/sod-2026-05-19-A03-fab-admet-validation.md` (2026-05-19 1차 조사)
> **본 문서**: 2차 심층 조사 — 1차에서 미확인된 항목 보완 + 대안 도구 공식 정보 확인

---

## 핵심 전제 (V-01 RESOLVED)

회의록(KAERI-AIRL-MOM-2026-003, 2026-04-06)의 **"Fab-ADMET" 표기는 오기재**이다.
**실제 평가 대상 도구: pepADMET** (2026 JCIM, 펩타이드 전용 ADMET 플랫폼)
이 사실은 2026-05-19 researcher 1차 조사 + 사용자 직접 확인으로 확정되었다.

> 근거: 학술 DB (PubMed, Google Scholar), GitHub 전체 검색에서 "Fab-ADMET"이라는 도구가 존재하지 않음. FP-ADMET (소분자 전용)과 혼동된 것으로 추정.

---

## 1. 공식 정보

### 1-A. pepADMET (주 평가 대상)

- **GitHub URL**: https://github.com/ifyoungnet/pepADMET
- **웹 플랫폼**: https://pepadmet.ddai.tech
- **라이선스**: GPL-3.0 (GitHub 저장소); 웹 플랫폼은 CC BY-NC-SA 4.0 (비상업 한정)
- **Organization**: Central South University (중남대학교), Jie Dong 연구실
- **리드 연락처**: Prof. Jie Dong (jiedong@csu.edu.cn)
- **저자**: Xiaorong Tan, Qianhui Liu, Yanpeng Fang, Mengting Zhou, Defang Ouyang, Wenbin Zeng, Jie Dong

### 1-B. FP-ADMET (참고 — 소분자 전용, 회의록 혼동 원인 추정)

- **GitLab URL**: https://gitlab.com/vishsoft/fpadmet
- **GitHub 미러**: https://github.com/jcheminform/fpadmet
- **라이선스**: GNU GPL v3.0
- **Organization**: Vishwesh Venkatraman (개인 연구자)

---

## 2. 원 논문

### pepADMET (주 평가 대상)

- **제목**: "pepADMET: A Novel Computational Platform For Systematic ADMET Evaluation of Peptides"
- **저널**: Journal of Chemical Information and Modeling (JCIM, ACS Publications)
- **DOI**: 10.1021/acs.jcim.5c02518
- **출판**: 2026년 1월 9일 (온라인 게재)
- **1저자**: Xiaorong Tan (공동 1저자 가능성 있음)

#### 보고 성능 지표

| Endpoint | AUC | 비고 |
|----------|-----|------|
| 독성 (toxicity) | 0.949 | 최고 성능 endpoint |
| 생체이용률 (F) | 0.90 | 5-CV 기준 |
| BBB 투과성 | 0.889 | |
| 막 투과성 (cyclic) | 0.901 | 환형 펩타이드 전용 모델 |

> **주의**: ACS 논문 paywall로 전문 미확인. 위 수치는 웹 플랫폼 문서 및 검색 결과 종합. 정확한 값은 V-02 (전문 접근) 완료 후 확인 필요.

#### 학습 데이터셋

- **총 규모**: 36,643개 고품질 항목 통합
- **환형 펩타이드**: CycPeptMPDB + 공개 문헌에서 7,765개 포함 확인
- **펩타이드 유형**: "linear, cyclic, modified, and natural peptides" 지원 명시

### FP-ADMET (참고)

- **제목**: "FP-ADMET: a compendium of fingerprint-based ADMET prediction models"
- **저널**: Journal of Cheminformatics
- **DOI**: 10.1186/s13321-021-00557-5
- **출판**: 2021
- **1저자**: Vishwesh Venkatraman
- **보고 성능**: BBB AUC=0.92, hERG AUC=0.88, 독성 AUC=0.65~0.96 (endpoint별 상이)
- **학습 데이터**: endpoint당 88~59,047개 소분자. **펩타이드 포함 안 됨.**

---

## 3. 펩타이드/SSTR2 적용 가능성

### pepADMET 적용 가능성 평가

| 항목 | 확인 결과 | 신뢰 등급 | 비고 |
|------|----------|-----------|------|
| 입력 형식 | 펩타이드 서열 + SMILES 병용 추정 | LOW | 공식 문서 명시 부족, 직접 테스트 필요 |
| 환형 펩타이드 (SS bond) | **지원 가능** | MED | "cyclic peptides" 명시적 지원 표명 |
| 표준 L-아미노산 (SST14) | 지원 | HIGH | 36,643 데이터 중 포함 |
| D-아미노산 (D-Phe, D-Trp) | **미명시 — 불명확** | LOW | 공식 문서 어디에도 언급 없음 |
| 비천연 아미노산 (D-Nal) | **미명시** | LOW | 지원 여부 불명확 |
| DOTA 킬레이터 결합 | **미지원 추정** | MED | 펩타이드 범위 초과, SMILES 기반 시도 필요 |
| 로컬 실행 | **가능** (GitHub GPL-3.0) | HIGH | 코드 공개, 학습 코드 포함 |
| 상업적 활용 | **제한** | HIGH | CC BY-NC-SA 4.0 (비상업 한정) |
| 자체 fine-tuning | **가능** | MED | GPL-3.0 코드 + 학습 스크립트 포함 |

#### ADMET Endpoint 커버리지 (29개)

- **흡수**: LogD7.4, 생체이용률(F), 막 투과성(Caco-2, PAMPA, RRCK)
- **분포**: BBB 투과성
- **대사**: 반감기 (human/mouse blood, intestine — natural 및 modified 구분)
- **독성**: 세포 독성(cytolysis), 용혈성(hemolysis), 신경독성(neurotoxicity), HC50

#### 결론

**SSTR2 theranostic 후보 적용 가능성: 부분 가능**

- SST14 원형 서열 (표준 L-AA): **적용 가능** (HIGH 신뢰)
- 환형 구조 (Cys-Cys SS bond): **조건부 가능** (MED 신뢰 — 직접 테스트 필요)
- D-아미노산 포함 후보 (Octreotide 계열): **불명확** — 공식 지원 미명시
- DOTA 결합 후보: **적용 불가** — 전용 도구 없음
- 로컬 실행 및 학습 코드: **가능** (GPL-3.0)

---

## 4. 대안 도구 비교

### 4-A. 펩타이드 독성 전용 도구

#### ToxTeller (2024, ACS Omega)

- **GitHub**: https://github.com/comics-asiis/ToxicPeptidePrediction
- **라이선스**: CC BY 4.0 (상업적 활용 가능)
- **논문**: PMC11270677, DOI: 10.1021/acsomega.4c04246
- **성능**: XGBoost 기준 AUC=0.930, Accuracy=0.855, F1=0.842
- **학습 데이터**: 4,129 펩타이드 (SwissProt + ConoServer, 90% 유사도 필터링)
- **입력 형식**: 아미노산 서열 (10~50 AA)
- **D-아미노산**: **미지원** — "unusual amino acids removed" (학습 시 비표준 AA 제거)
- **환형 펩타이드**: **미지원** (서열 기반, 구조 정보 없음)
- **로컬 실행**: 가능

#### CAPTP (2024, Bioinformatics Oxford)

- **GitHub**: https://github.com/jiaoshihu/CAPTP
- **라이선스**: CC BY 4.0
- **기술**: CNN + Transformer (convolution + self-attention)
- **입력**: 아미노산 서열
- **D-아미노산/환형**: **미지원** (서열 기반)
- **로컬 실행**: 가능

### 4-B. 소분자 ADMET — 참고용 (펩타이드 부적합)

#### ADMET-AI (2024, Bioinformatics)

- **GitHub**: https://github.com/swansonk14/admet_ai
- **라이선스**: MIT (상업적 활용 가능)
- **논문**: PMC11226862, DOI: 10.1093/bioinformatics/btae416
- **기술**: Chemprop-RDKit (그래프 신경망) — TDC 41개 데이터셋 학습
- **입력**: SMILES 전용
- **성능**: 41개 endpoint 중 20/31개 AUROC > 0.85
- **D-아미노산/환형**: **공식 미지원** — SMILES 기반이라 이론적 표현 가능하나 학습 도메인 외
- **로컬 실행**: 가능 (pip 설치)
- **PRST_N_FM 적합성**: 저분자 약물 기반 — SSTR2 환형 펩타이드에 **미권고**

#### FP-ADMET (2021, J Cheminform)

- **GitLab**: https://gitlab.com/vishsoft/fpadmet
- **라이선스**: GNU GPL v3.0
- **입력**: SMILES
- **성능**: BBB AUC=0.92, hERG AUC=0.88
- **펩타이드 적합성**: **없음** — 소분자 전용

### 4-C. 환형 펩타이드 특화 도구

#### CycPeptMP (막 투과성 전용)

- **논문**: PMC11361855
- **특화**: 환형 펩타이드 막 투과성 예측 (R=0.87)
- **입력**: 구조 정보 포함
- **D-아미노산**: 부분 가능 (연구에 따라 다름)
- **ADMET 범위**: 막 투과성 단일 endpoint — 독성 예측 불가

---

## 5. PRST_N_FM 통합 권장사항

### pharmacology_guards.py 등록 권장 등급

| 도구 | ENDPOINT_CONFIDENCE 등급 | 권장 등록 이유 |
|------|------------------------|--------------|
| pepADMET | **P2** (MED) | 펩타이드 전용, 환형 지원, 29 endpoints — D-AA 불명확으로 P1 미달 |
| ToxTeller | **P3** (LOW) | L-AA 서열 기반 독성 — D-AA/환형 미지원 한계 |
| ADMET-AI | **P4** (매우 낮음) | 소분자 기반 — 펩타이드 OOD |
| FP-ADMET | **P4** (매우 낮음) | 소분자 전용 |

> 등급 정의: P1=검증됨, P2=조건부, P3=참고용, P4=미권고

### 통합 방식 권고

```
pepADMET:
  방식: 로컬 실행 (GitHub GPL-3.0 코드 클론)
  단계: 7단계 선별 체계 Step (3) — Toxicity 필터
  적용 범위: SST14 유사 L-AA 후보만 (D-AA 제외)
  한계 명시: H-06 가드 필수 (D-AA/DOTA 후보는 OOD 경고)

ToxTeller/CAPTP:
  방식: 로컬 실행 (CC-BY, pip 가능)
  단계: pepADMET 보조 또는 대체
  적용 범위: L-AA 서열 기반 후보만
```

### pharmacology_guards.py 추가 코드 블록 (권고)

```python
ENDPOINT_CONFIDENCE["pepadmet_toxicity"] = {
    "tool": "pepADMET (Tan et al. 2026 JCIM DOI:10.1021/acs.jcim.5c02518)",
    "grade": "P2",
    "d_amino_acid_support": None,          # 공식 미명시 — 직접 테스트 필요
    "cyclic_peptide_support": True,        # 명시적 지원 표명
    "dota_support": False,                 # 펩타이드 범위 초과
    "local_executable": True,             # GPL-3.0
    "reported_auc": 0.949,                # toxicity endpoint
    "disclaimer": (
        "SST14 환형 L-AA 후보에 한해 참고 활용. "
        "D-Phe/D-Trp/D-Nal 등 비천연 아미노산 후보는 학습 도메인 외(OOD). "
        "DOTA 결합 구조는 처리 불가. wet-lab ADMET 실측 병행 필수."
    ),
    "source": "DOI:10.1021/acs.jcim.5c02518",
}

ENDPOINT_CONFIDENCE["toxteller_toxicity"] = {
    "tool": "ToxTeller (PMC11270677 DOI:10.1021/acsomega.4c04246)",
    "grade": "P3",
    "d_amino_acid_support": False,         # 학습 시 비표준 AA 제거 명시
    "cyclic_peptide_support": False,
    "dota_support": False,
    "local_executable": True,
    "reported_auc": 0.930,
    "disclaimer": (
        "L-AA 선형 서열 기반 독성 예측. D-AA/환형/DOTA 미지원. "
        "참고용으로만 활용 — 단독 판단 기준 금지."
    ),
    "source": "DOI:10.1021/acsomega.4c04246",
}
```

---

## 6. 검색 쿼리 및 전략

### 사용한 검색 쿼리

1. `"Fab-ADMET" GitHub repository ADMET prediction deep learning`
2. `"FAB-ADMET" OR "FAb-ADMET" ADMET antibody fragment prediction tool`
3. `"FabADMET" peptide ADMET prediction open source`
4. `pepADMET "ifyoungnet" cyclic peptide D-amino acid toxicity prediction GitHub 2025`
5. `"FP-ADMET" "Venkatraman" 2021 "J Cheminform" GitHub peptide toxicity GPL license`
6. `"ToxTeller" CAPTP peptide toxicity prediction D-amino acid cyclic 2023 2024 GitHub CC-BY`
7. `pepADMET 2025 JCIM "36643" D-amino acid cyclic modified peptide endpoints`

### WebFetch 접근 URL

| URL | 결과 |
|-----|------|
| https://github.com/ifyoungnet/pepADMET | 접근 성공 — 저자, 라이선스 확인 |
| https://pepadmet.ddai.tech/documentation/ | 접근 성공 — 29 endpoints, CC BY-NC-SA 확인 |
| https://pubs.acs.org/doi/10.1021/acs.jcim.5c02518 | **403 Forbidden (paywall)** |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC11270677/ | 접근 성공 — ToxTeller 성능 확인 |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC8479898/ | 접근 성공 — FP-ADMET 소분자 전용 확인 |
| https://github.com/swansonk14/admet_ai | 접근 성공 — MIT 라이선스, SMILES 전용 확인 |

---

## 7. 검증 필요 항목

| # | 사항 | 우선순위 | 방법 |
|---|------|---------|------|
| V-01 | ~~"Fab-ADMET" = pepADMET 오기재 확정~~ | **DONE** | 사용자 확인 (2026-05-19) |
| V-02 | pepADMET 논문 전문 (AUC 정확한 값) — paywall | HIGH | KAERI 도서관 또는 저자 preprint 요청 |
| V-03 | pepADMET D-아미노산 처리 실제 테스트 | HIGH | Octreotide SMILES/서열 입력 → 에러 여부 |
| V-04 | pepADMET GitHub 로컬 설치 성공 여부 | HIGH | engineer-infra: `git clone` + `pip install` |
| V-05 | pepADMET 상업적 라이선스 (KAERI 적용 가능 여부) | MED | CC BY-NC-SA → 비상업 한정. KAERI 법무 확인 |
| V-06 | ToxTeller D-AA 훈련 데이터 원본 확인 | MED | SwissProt + ConoServer D-AA 항목 수 |
| V-07 | CycPeptMP D-AA monomer 입력 처리 여부 | LOW | 코드 직접 확인 |
| V-08 | pepADMET 반감기 endpoint (half-life in blood) A-02와 연동 | HIGH | A-02 벤치마크 세트에 pepADMET 반감기 예측 포함 |

---

## 비교 표 — 도구 종합

| 특성 | pepADMET | ToxTeller | CAPTP | ADMET-AI | FP-ADMET |
|------|----------|-----------|-------|----------|----------|
| 펩타이드 특화 | **YES** | YES | YES | NO | NO |
| 환형 지원 | **YES** | NO | NO | 미확인 | NO |
| D-AA 지원 | **미명시** | NO | NO | 미확인 | NO |
| DOTA 결합 | NO | NO | NO | NO | NO |
| 입력 | 서열/SMILES | 서열 | 서열 | SMILES | SMILES |
| 로컬 실행 | YES (GPL) | YES (CC-BY) | YES (CC-BY) | YES (MIT) | YES (GPL) |
| 상업 활용 | **NO** (NC-SA) | YES | YES | YES | YES |
| endpoint 수 | 29 | 1 (독성) | 1 (독성) | 41 | 50+ |
| 최고 AUC | 0.949 | 0.930 | 0.959 | 0.85+ | 0.92 |
| 자체 학습 | YES (GPL) | YES | YES | YES (MIT) | YES (GPL) |
| 논문 연도 | 2026 | 2024 | 2024 | 2024 | 2021 |

---

## 본 프로젝트 적용 가능성 — 최종 등급

| 시나리오 | 도구 | 신뢰 등급 | 권고 |
|---------|------|----------|------|
| SST14 (L-AA) 독성 사전 스크리닝 | pepADMET | HIGH | **권고** |
| 환형 변형 후보 독성 | pepADMET | MED | 조건부 (D-AA 미포함 한정) |
| D-AA 후보 독성 (Octreotide 계열) | **없음** | - | wet-lab 필수 |
| DOTA 결합 후보 독성 | **없음** | - | wet-lab 필수 |
| 반감기 예측 (pepADMET 내) | pepADMET | MED | A-02와 연동 검토 |

> 핵심 결론: **SSTR2 theranostic 후보의 D-아미노산·DOTA 킬레이터 결합 구조에 대한 신뢰할 수 있는 ADMET 예측 도구는 현재 존재하지 않는다.** pepADMET이 현재 최선의 선택이나 D-AA 미명시 한계가 있으며, 자체 fine-tuning을 위한 D-AA 환형 ADMET 레이블 데이터 확보가 중장기 과제이다.
