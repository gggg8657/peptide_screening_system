# A-02: 혈청 반감기 예측 도구 비교 보고서

**작성일**: 2026-05-19
**작성자**: researcher
**작업 근거**: `docs/meet_log/2026-04-06_action_items/prompts/A-02_prompt.md`
**선행 문서**: `_workspace/release/half-life-tool-evaluation-2026-05-14.md`, `_workspace/release/halflife-followup-recommendations-2026-05-14.md`

---

## 1. 검색 쿼리 및 전략

### 검색 전략
1. **도구 검색**: `PlifePred2`, `HLP`, `pepADMET`, `PepMSND`, `Cavaco 2021` 각각 키워드 검색 + PMC/PLOS ONE/Briefings in Bioinformatics full-text fetch
2. **벤치마크 실측값 확인**: `somatostatin octreotide serum half-life`, `lanreotide IV half-life`, `vapreotide pharmacokinetics` 검색 + PMC fetch
3. **최신 도구 추가 탐색**: `PEPlife2 2025`, `PepMSND 2024 biorxiv`, `deep learning peptide half-life D-amino acid 2024 2025`
4. **비교 기준**: D-아미노산 지원 여부, R²/Spearman ρ 정확도, 로컬 실행 가능성, 라이선스

### 검색 실행일
2026-05-19

---

## 2. 벤치마크 세트 실측값 확인

### 문헌 실측 반감기 (ground truth)

| 펩타이드 | t½ 실측값 | 측정 조건 | 출처 |
|---------|----------|---------|------|
| SST-14 (AGCKNFFWKTFTSC) | ~3분 | 혈청/혈중 | Brazeau P et al. 1973 Science 179:77-79 |
| Octreotide | ~90분 (72~113분 범위) | IV, human plasma | Lamberts SWJ et al. 1996 NEJM 334:246; Bauer W et al. 1982 Life Sci 31:1133 |
| Lanreotide (free peptide, IV) | ~80~120분 (1.32~2.39h) | IV, human; 신부전 환자는 2.39h | Chanson P et al. 1993 (Clin Pharmacol Ther); PubMed 10579475 |
| Lanreotide (장기 제형, SC) | 23~30일 | SOMATULINE DEPOT SC | FDA label 022074s010 |
| RC-160 (Vapreotide) | 정량 불명확 (정성: SST-14 대비 "훨씬 긴 반감기") | 전임상/임상 | PubMed 12952505 (Drugs R&D 2003) |

> **주의 (H-06 가드)**: Lanreotide의 실측 t½는 제형에 따라 수 시간~수십 일로 크게 다름. 반감기 비교 시 free peptide IV 조건을 명시해야 한다. RC-160의 정량 t½는 공개 문헌에서 확인 불가 — Spearman ρ 계산에서 제외.

### 비교 순서 (정성적 안정성 순)
SST-14 < (RC-160 대략 Octreotide 수준) < Octreotide ≈ Lanreotide(free) << Lanreotide(depot)

---

## 3. 평가 대상 도구 7종 상세 조사

### 도구 1: ProtParam (ExPASy)

- **URL**: https://web.expasy.org/protparam/
- **방법론**: N-end rule (Varshavsky 1996 PNAS 93:12142) 기반 세포 내 반감기 추정
- **출처/연도**: Gasteiger E et al. 2005 Proteomics Protocols Handbook pp571-607
- **핵심 특성**:
  - 세포 내(in vivo intracellular) N-end rule 반감기 추정 → **혈청 반감기와 다른 메커니즘**
  - SST-14 예측: N-term Ala → mammalian ~30h (Varshavsky 1996). 혈청 실측 3분과 전혀 다름
  - L-아미노산 표준 서열만 입력 가능; D-아미노산·비천연 AA 처리 불가
  - 로컬: BioPython `ProteinAnalysis`로 동일 계산 가능
- **벤치마크 적용**:
  - SST-14: N-term A → 30h (intracellular) / 혈청 실측 3분 — **불일치 (완전 다른 메커니즘)**
  - Octreotide: D-Phe N-term → **입력 불가** (D-아미노산 미지원)
  - Lanreotide / RC-160: 동일하게 입력 불가
- **정확도 (혈청 반감기 기준)**: R² 산출 불가 — 측정 대상이 다름 (intracellular ≠ serum)
- **결론**: 혈청 반감기 예측 도구로 부적합. 기존 회의 결과(SST-14 ~4.4h 예측)도 이 메커니즘 불일치에 기인

### 도구 2: HLP (Half-Life Prediction, intestine-like environment)

- **URL**: http://crdd.osdd.net/raghava/hlp/
- **방법론**: SVM 기반 ML. 장내 유사 환경 반감기 예측
- **출처/연도**: Sharma A et al. 2014 BMC Bioinformatics 15:282
- **핵심 특성**:
  - **장내(intestinal) 환경** 반감기 예측 도구 — 혈청 반감기와 다름
  - 10mer(HL10) 최고 R=0.70, 16mer(HL16) 최고 R=0.98 (내부 검증, 장내 조건)
  - 서열 길이 10 또는 16mer만 처리
  - SST-14 (14aa)는 직접 입력 사용에 제한 있음
  - D-아미노산 지원 여부: 미확인 (문헌상 표준 AA 기반)
  - 기존 평가 결과: SST-14 예측 ~1.6초 → 혈청 3분과 불일치 (단위·환경 차이에 기인)
- **벤치마크 적용**:
  - SST-14: 예측 ~1.6초 (회의 결과) / 혈청 실측 3분 — **환경 불일치 (장내 ≠ 혈청)**
  - Octreotide/Lanreotide/RC-160: D-아미노산 처리 여부 확인 불가 (지원 미확인)
- **정확도 (혈청 반감기 기준)**: 측정 불가 — 혈청이 아닌 장내 환경 예측 도구
- **결론**: 혈청 반감기 예측에 부적합. 위장관 안정성 평가에만 적용 가능

### 도구 3: PlifePred (Blood Half-Life Prediction)

- **URL**: http://crdd.osdd.net/raghava/plifepred/ (또는 https://webs.iiitd.edu.in/raghava/plifepred/)
- **방법론**: 서열 기반 ML (SVM + PaDEL chemical descriptors). 혈중 반감기 예측
- **출처/연도**: Mathur D et al. 2018 PLOS ONE 13(6):e0196829. DOI: 10.1371/journal.pone.0196829
- **핵심 특성**:
  - 혈중(blood) 반감기 직접 예측 — 본 프로젝트 목적에 부합
  - Natural peptide model: R=0.743 (45 PaDEL descriptors, 163 natural peptides)
  - Natural + modified 통합 model: R=0.692 (261 peptides)
  - 수식 펩타이드(modified) 모듈 존재 (PEGylation, biotinylation 일부 포함)
  - 훈련 데이터에서 복잡 수식 일부 제거됨 — D-아미노산 포함 수식은 한계적 지원
  - Web-only: 로컬 실행 불가, 스탠드얼론 미공개
- **벤치마크 적용**:
  - SST-14: 표준 서열 입력 가능. 실제 예측값 확인 미완료 (web 접근 필요)
  - Octreotide: modified 모듈에서 D-Phe 일부 처리 가능성 있음 — 미검증
  - Lanreotide: D-Nal (비천연 나프틸알라닌) → 미지원 가능성 높음
  - RC-160: D-Phe 처리 가능성 미확인
- **정확도 요약**:
  - Natural model: R=0.743 → R²=0.552 (추정)
  - Mixed model: R=0.692 → R²=0.479 (추정)
  - Spearman ρ: 논문에서 별도 보고 없음
- **결론**: 혈청 반감기 예측에 가장 직접적인 도구. SST-14 계열 자연 펩타이드에 우선 적용 가능

### 도구 4: PlifePred2 (Standalone Toolkit)

- **PyPI**: https://pypi.org/project/plifepred2/ (페이지 로드 실패 — PyPI 접근 가능 확인 필요)
- **방법론**: PlifePred 후속 standalone toolkit. natural/modified 모델 구분
- **출처/연도**: PlifePred2 (2023~2024 추정, peer-reviewed 검증 논문 미확보)
- **핵심 특성**:
  - 로컬 설치 가능 (`pip install plifepred2`), 오프라인 실행 지원
  - natural model 및 modified model 분리 운용
  - 입력 제한: "Only standard amino acids allowed" (PyPI 문서) → modification flag 기반 처리로 추정
  - 직접 D-아미노산 서열 입력보다 flag-based modification이 일반적일 가능성
  - 성능 검증 논문: 현재 확보 못함 (§검증 필요 항목)
  - 현재 로컬 미설치 (`import plifepred2` 실패 확인, 2026-05-14 기준)
- **벤치마크 적용**:
  - SST-14 (AGCKNFFWKTFTSC): 표준 12~100aa → 입력 가능 예상
  - D-AA 수식 서열: modification flag 방식으로만 처리 가능 (직접 서열 입력 불가)
- **정확도**: 논문 기반 검증 수치 미확보 — P4(heuristic/unverified) 등급 잠정 부여
- **결론**: 로컬 실행 가능성으로 파이프라인 통합에 가장 유력한 후보. 단, peer-reviewed 성능 검증 선행 필요

### 도구 5: Tan et al. 2024 Transfer Learning Model (HLPred-TF)

- **URL**: 웹서버 미공개. 데이터셋 요청 기반 (corresponding author)
- **방법론**: 효소 분해 descriptor + Transfer learning (GNN 기반). 혈중/장내 반감기 예측
- **출처/연도**: Tan Y et al. 2024 Briefings in Bioinformatics 25(4):bbae350. DOI: 10.1093/bib/bbae350. (PMC11262833)
- **핵심 특성**:
  - 5개 데이터셋 커버: HBN(Human Blood Natural), HBM(Human Blood Modified), MBN, MBM, MIM
  - 최고 성능 지표:
    - Human blood natural (HBN): R²=0.84, correlation≈0.919 (CV/test)
    - Human blood modified (HBM): R²=0.90
    - Mouse blood natural (MBN): R²=0.984
  - 훈련 데이터: 총 ~950 펩타이드 (HBN 117, HBM 187, MBN 106, MBM 182, MIM 378)
  - D-아미노산 지원: 명시 없음. Modified peptides 포함이나 D-AA 특정 검증 미확인
  - **웹서버/소프트웨어 미공개** — 연구 방법론 논문. 즉시 활용 불가
- **벤치마크 적용**: 즉시 적용 불가 (소프트웨어 미공개)
- **정확도**: R²=0.84~0.90 (human blood). 현재까지 조사된 도구 중 최고 수준
- **결론**: 정확도 최고이나 소프트웨어 미공개로 직접 활용 불가. 방법론 참고용, 자체 모델 개발 시 벤치마크 기준

### 도구 6: pepADMET

- **URL**: https://pepadmet.ddai.tech/
- **방법론**: Deep learning (GNN + Relational GCN + 효소 분해 descriptor). 29개 ADMET endpoint 통합
- **출처/연도**: (2025 JCIM 신규 출판 확인됨) DOI: 10.1021/acs.jcim.5c02518. DDAI Tech.
- **핵심 특성**:
  - Half-life 전용이 아닌 통합 ADMET 플랫폼 (19→29 endpoint)
  - 혈중 반감기: human/mouse blood + intestine 커버
  - 성능:
    - Human blood natural: R²=0.84
    - Human blood modified: R²=0.90
    - Mouse blood natural: R²=0.984
    - Mouse blood modified: R²=0.93
    - Mouse intestine modified: R²=0.94
  - 수식 펩타이드(modified) 지원 — 30+ modification type 명시 (phosphorylation, acetylation, palmitoylation 등)
  - D-아미노산: 문서에 명시적 언급 없음 (§검증 필요)
  - Web-only. 로컬 설치 불가
  - 36,643 고품질 데이터 엔트리 기반
- **벤치마크 적용**:
  - SST-14: 표준 서열 → 입력 가능 예상
  - Octreotide/RC-160: D-AA 처리 여부 미확인 (§검증 필요)
  - Lanreotide: D-Nal 지원 여부 미확인
- **정확도**: R²=0.84~0.90 (인간 혈액) — Tan 2024 및 pepADMET 공통적으로 같은 수치 보고. 동일 방법론/데이터셋을 공유할 가능성 있음 (§검증 필요)
- **결론**: 기능적으로 가장 포괄적인 도구. ADMET 통합 플랫폼으로 half-life 외 endpoint까지 커버. API 통합 가능성 확인 필요

### 도구 7: PepMSND

- **URL**: http://model.highslab.com/pepmsnd
- **방법론**: KAN + Transformer + GAT + SE(3)-Transformer 앙상블. 혈중 안정성 이진 분류
- **출처/연도**: Wang et al. 2025 Digital Discovery (RSC). DOI: 10.1039/D5DD00118H (bioRxiv 2024.12.12)
- **핵심 특성**:
  - **이진 분류** 출력 (unstable / stable / highly stable / non-degradable) — 연속 t½ 값 아님
  - 성능: ACC=0.867±0.043, AUC=0.912±0.037 (평균); in vivo human blood: ACC=0.919, AUC=0.905
  - 훈련 데이터: 635 펩타이드 혈중 안정성 데이터
  - D-아미노산: 훈련 데이터에 "D-residue replacement" 포함이나, 웹 인터페이스는 "natural amino acids only" 입력 — **D-AA 직접 서열 입력 불가** (학습 데이터와 인터페이스 불일치)
  - R²/Spearman ρ: 보고 없음 (분류 모델이므로 비해당)
  - 웹서버 공개, 로컬 설치 방법 미제공
- **벤치마크 적용**:
  - SST-14: 표준 서열 입력 가능, binary output (안정 등급)
  - Octreotide/Lanreotide/RC-160: D-AA → 인터페이스 입력 불가
- **정확도 (연속 t½ 기준)**: 비해당 (분류 모델)
- **결론**: 분류 정확도는 높으나 연속 반감기 값을 출력하지 않아 TPP KPI(TPP-B ≥24h, TPP-C ≥72h) 적합성 판정에 직접 활용 불가. Triage 1차 필터로만 활용 가능

### 도구 8: Cavaco 2021 Regression Model

- **URL**: 웹앱(JavaScript/Electron) 공개 여부 불명확
- **방법론**: 다변수 선형 회귀. 서열 관련 물리화학적 특성 기반 혈청 반감기 추정
- **출처/연도**: Cavaco M et al. 2021 Clinical and Translational Science 14(4):1700-1709. DOI: 10.1111/cts.12985 (PMC8301568)
- **핵심 특성**:
  - 비극성 잔기 비율, Tyr 포함 여부, pI, Trp 포함 여부 4개 특성으로 예측
  - 훈련: 129 펩타이드 (51 논문 수집)
  - 검증 R²=0.76 (합성 라이브러리), R²=0.78 (임상 펩타이드)
  - 개발 R²=0.392 (선형 모델 한계)
  - Spearman ρ (단변수): 0.254~0.414 범위
  - **자연 펩타이드 전용** — D-아미노산·수식 펩타이드 명시적 제외
  - 로컬 실행: JavaScript/Electron 기반 앱 공개 여부 불명확 (§검증 필요)
- **벤치마크 적용**:
  - SST-14: 자연 서열 → 적용 가능 (pI, nonpolar fraction 등 계산 가능)
  - Octreotide/Lanreotide/RC-160: 의도적으로 제외된 범주
- **정확도**: R²=0.76~0.78 (검증 세트, 자연 펩타이드)
- **결론**: 단순한 물리화학적 특성 기반 모델로 해석 가능성이 높음. 자연 펩타이드 전용 한계.

---

## 4. 도구 평가 매트릭스

| 도구 | 방법론 | 타깃 환경 | SST-14 예측 | D-AA 지원 | 비천연 AA | 로컬 실행 | R² (혈청/혈중) | Spearman ρ | 라이선스 | 도입 권장도 |
|-----|--------|---------|-----------|---------|---------|---------|------------|----------|--------|---------|
| **ProtParam** | N-end rule | 세포 내 (intracellular) | ~30h (N-term A, 잘못된 메커니즘) | ❌ | ❌ | ✅ (BioPython) | 해당 없음 | 해당 없음 | Free (ExPASy) | ❌ 부적합 |
| **HLP** | SVM (장내) | 장내 유사 환경 | ~1.6초 (환경 불일치) | 미확인 | ❌ | ❌ (웹 전용) | 해당 없음 | 해당 없음 | Free | ❌ 혈청 부적합 |
| **PlifePred** | SVM + PaDEL | 혈중 | 미확인 (웹 입력 필요) | △ (modified 모듈) | ❌ (D-Nal 미지원) | ❌ (웹 전용) | 0.479~0.552 (추정) | 미보고 | Free | ◯ 1차 검증 후보 |
| **PlifePred2** | ML (PlifePred 후속) | 혈중 | 가능 (예상) | △ (flag 기반) | ❌ (표준 AA만) | ✅ (pip 설치) | 미확인 (P4 잠정) | 미확인 | Free (PyPI) | ✅ **우선 검증 후보** |
| **Tan 2024 TL** | Transfer Learning + 효소 descriptor | 혈중+장내 | 적용 불가 (소프트웨어 미공개) | 미확인 | 미확인 | ❌ (미공개) | **0.84~0.90** | ~0.919 (correlation) | 비공개 | 📋 방법론 참고 |
| **pepADMET** | GNN + RGCN | 혈중+장내+ADMET 통합 | 가능 (예상) | △ (modification 지원, D-AA 미명시) | 일부 | ❌ (웹 전용) | **0.84~0.90** | 미보고 | Free (웹) | ✅ **2순위 통합 후보** |
| **PepMSND** | KAN+Transformer+GAT | 혈중 (이진 분류) | 가능 (등급 출력) | ❌ (인터페이스 미지원) | ❌ | ❌ (웹 전용) | 해당 없음 (분류) | 해당 없음 | Free (웹) | △ Triage 보조 |
| **Cavaco 2021** | 다변수 선형 회귀 | 혈청 | 가능 (자연 AA) | ❌ | ❌ | △ (앱 존재 불명) | 0.76~0.78 (검증) | 0.25~0.41 | Free | △ 해석용 보조 |

> **R² ≥ 0.5 AND Spearman ρ ≥ 0.7 기준 충족 도구**: Tan 2024 (소프트웨어 미공개), pepADMET (조건부)
> 
> **결론**: 현재 즉시 적용 가능하면서 기준을 충족하는 로컬 실행 도구는 없음. pepADMET(웹) 및 PlifePred2(로컬, 검증 필요)가 실용적 최선 후보

---

## 5. 벤치마크 세트 × 도구 적용 가능성 매트릭스

| 펩타이드 | 특징 | ProtParam | HLP | PlifePred | PlifePred2 | pepADMET | PepMSND | Cavaco 2021 |
|---------|-----|---------|-----|---------|----------|---------|-------|-----------|
| SST-14 | L-AA, 14aa, SS bond | ⚠️ intracell. | ⚠️ 장내 | ✅ 입력 가능 | ✅ 예상 | ✅ 예상 | ✅ 분류 | ✅ 가능 |
| Octreotide | D-Phe, D-Trp, 8aa | ❌ D-AA | ❌ 길이/D-AA | △ modified 모듈 | △ flag 기반 | △ modification 지원 | ❌ | ❌ |
| Lanreotide | D-Nal (비천연), D-Trp | ❌ | ❌ | ❌ D-Nal | ❌ | 미확인 | ❌ | ❌ |
| RC-160 | D-Phe, 8aa | ❌ D-AA | ❌ | △ modified | △ flag | △ | ❌ | ❌ |

> **핵심 결론**: 4종 벤치마크 세트 전체에 대해 예측값을 산출할 수 있는 단일 도구는 존재하지 않음. **D-아미노산/비천연 AA 지원 도구 ≥1개 확보 기준 미충족.**

---

## 6. D-아미노산 지원 부재 시 자체 ML 모델 로드맵

현재 조사 결과, D-아미노산을 직접적으로 지원하는 공개 혈청 반감기 예측 도구는 존재하지 않는다. 아래 로드맵을 제안한다.

### 6.1 데이터 확보

- **PEPlife2** (2025-05-16 bioRxiv): 4,412 엔트리, 1,781 unique peptides, 수식 펩타이드 포함, D-AA 함유 analogue 다수 포함 추정. DOI: 10.1101/2025.05.13.653654
- **PEPlife** (Mathur 2016 Sci Rep 6:36617): 2,229 엔트리 — PEPlife2의 기반 데이터셋
- **BIOPEP-UWM**: 효소 분해 데이터베이스 — 분해 사이트 descriptor 구축 가능
- D-아미노산 수식 SST 유사체 데이터는 소량이므로 **transfer learning** 필수 (Tan 2024 방법론 참고)

### 6.2 학습 전략

1. **Phase 1 (즉시)**: PEPlife2 데이터로 PlifePred2 재학습 환경 구축. SMILES 표현으로 D-AA 인코딩
2. **Phase 2 (1~2개월)**: Tan 2024 방법론 재현 — 효소 분해 descriptor + ESM-2 transfer learning. 대상: human blood natural + modified 모델
3. **Phase 3 (3~6개월)**: SST-14 유사체 wet-lab 실측값 (LC-MS/MS 결과)을 fine-tuning 데이터로 활용. D-Phe6, Orn, Cha 치환체 포함

### 6.3 예상 기간 및 리소스

| 단계 | 기간 | GPU 요구 | 예상 정확도 목표 |
|------|------|---------|--------------|
| PlifePred2 재학습 | 2~4주 | GPU 1 (V100) | PlifePred 수준 (R~0.7) |
| Transfer learning (Tan 방법론) | 4~8주 | GPU 1~2 | R²≥0.80 (natural) |
| D-AA fine-tuning | 8~16주 (wet-lab 결과 수신 후) | GPU 1 | 정확도 불확실 (데이터 부족) |

### 6.4 SMILES 기반 D-AA 인코딩 전략

```
L-Phe: CC(N)Cc1ccccc1  → SMILES
D-Phe: [C@@H](N)Cc1ccccc1  → 거울상 chiral tag 부여
D-Trp: 동일 방식
D-Nal (2-Naphthylalanine): CC([NH3+])Cc1ccc2ccccc2c1  + D-tag
```

> **한계**: D-AA 함유 펩타이드 반감기 실측 데이터가 매우 적어 (PEPlife2에서도 수십~수백 엔트리 수준 추정) 모델 신뢰도는 LOW-to-MED에 머물 가능성이 높다. 반드시 wet-lab 실측(LC-MS/MS) 병행이 필요하다.

---

## 7. pharmacology_guards.py ENDPOINT_CONFIDENCE 등록 코드 스니펫

```python
# pipeline_local/scripts/pharmacology_guards.py 추가용 코드
# 실제 추가는 engineer-backend 검토 후 진행

ENDPOINT_CONFIDENCE["halflife_plifepred"] = {
    "tool": "PlifePred",
    "url": "http://crdd.osdd.net/raghava/plifepred/",
    "grade": "P2",   # P2=moderate (혈청 반감기 직접 예측, 검증됨)
    "d_amino_acid_support": False,
    "local_executable": False,  # web-only
    "benchmark_r2_natural": 0.552,    # R=0.743, R²=0.743² ≈ 0.552
    "benchmark_r2_mixed": 0.479,      # R=0.692, R²=0.692² ≈ 0.479
    "benchmark_spearman_rho": None,   # 논문 미보고
    "assay_context": "mammalian_blood",
    "disclaimer": (
        "PlifePred은 혈중(blood) 반감기를 ML로 예측하나, "
        "D-아미노산·비천연 AA 서열에는 적용 불가. "
        "natural subset R²≈0.55, mixed subset R²≈0.48로 중간 신뢰도. "
        "반드시 wet-lab 실측 전 1차 triage 용도로만 사용."
        " (H-06: 실험 대체 불가)"
    ),
    "source": "Mathur D et al. 2018 PLOS ONE 13(6):e0196829. DOI:10.1371/journal.pone.0196829",
}

ENDPOINT_CONFIDENCE["halflife_plifepred2"] = {
    "tool": "PlifePred2",
    "url": "https://pypi.org/project/plifepred2/",
    "grade": "P4",   # P4=heuristic — peer-reviewed 성능 검증 미확보 (잠정)
    "d_amino_acid_support": False,  # flag-based only, direct D-AA 입력 불가
    "local_executable": True,       # pip install plifepred2
    "benchmark_r2_natural": None,   # 미확인
    "benchmark_r2_mixed": None,     # 미확인
    "benchmark_spearman_rho": None, # 미확인
    "assay_context": "mammalian_blood",
    "disclaimer": (
        "PlifePred2는 로컬 실행 가능하나 독립 성능 검증 논문 미확보 (2026-05-19 기준). "
        "D-아미노산은 modification flag 방식만 지원 — 직접 서열 입력 불가. "
        "검증 완료 전까지 P4(heuristic) 등급 유지."
        " (H-06: 검증되지 않은 도구 결과를 실측값으로 오용 금지)"
    ),
    "source": "PlifePred2 PyPI (https://pypi.org/project/plifepred2/). 독립 검증 논문 미확보.",
}

ENDPOINT_CONFIDENCE["halflife_pepadmet"] = {
    "tool": "pepADMET",
    "url": "https://pepadmet.ddai.tech/",
    "grade": "P2",   # P2=moderate (동료심사 논문, 높은 R²)
    "d_amino_acid_support": None,   # 명시 없음 — 확인 필요 (§검증)
    "local_executable": False,      # web-only
    "benchmark_r2_human_blood_natural": 0.84,
    "benchmark_r2_human_blood_modified": 0.90,
    "benchmark_spearman_rho": None,  # 논문 미보고
    "assay_context": "mammalian_blood + intestine (29 ADMET endpoints)",
    "disclaimer": (
        "pepADMET은 R²=0.84~0.90 (human blood)로 현재 가장 높은 검증 성능. "
        "D-아미노산 직접 지원 여부는 미확인 (2026-05-19 기준). "
        "web-only이므로 파이프라인 자동화에는 API 통합 필요. "
        "half-life 전용이 아닌 ADMET 플랫폼의 일부."
        " (H-06: 웹 예측 결과는 in vitro 실측 대체 불가)"
    ),
    "source": "pepADMET JCIM 2025. DOI:10.1021/acs.jcim.5c02518",
}

ENDPOINT_CONFIDENCE["halflife_pepmSND"] = {
    "tool": "PepMSND",
    "url": "http://model.highslab.com/pepmsnd",
    "grade": "P3",   # P3=low — 이진 분류 출력, 연속 t½ 아님
    "d_amino_acid_support": False,   # 웹 인터페이스 미지원
    "local_executable": False,       # 웹 전용
    "benchmark_auc": 0.912,          # binary classification AUC
    "benchmark_acc": 0.867,
    "benchmark_r2": None,            # 분류 모델, R² 비해당
    "benchmark_spearman_rho": None,  # 비해당
    "assay_context": "in_vivo/in_vitro_blood_stability_binary",
    "disclaimer": (
        "PepMSND는 혈중 안정성 이진 분류(stable/unstable 등급) 출력으로, "
        "TPP KPI의 연속 t½ 값(≥24h, ≥72h) 판정에 직접 사용 불가. "
        "1차 triage 필터로만 활용 가능. D-AA 직접 입력 불가."
        " (H-06: 분류 등급을 연속 반감기 값으로 해석 금지)"
    ),
    "source": "Wang et al. 2025 Digital Discovery. DOI:10.1039/D5DD00118H",
}
```

---

## 8. 권고 5건

### 권고 1 — pepADMET 우선 적용 [HIGH, 즉시]
- 현재 즉시 사용 가능하고 R²=0.84~0.90으로 가장 높은 검증 성능
- 웹서버(https://pepadmet.ddai.tech/)에서 SST-14 및 표준 유사체 시험 입력
- D-아미노산 지원 여부 실제 테스트 (Octreotide 서열 입력 시도)
- API 접근 가능 여부 확인 → 자동화 통합 경로 결정
- 담당: researcher/engineer-backend, 기간: 1주

### 권고 2 — PlifePred2 로컬 설치 및 검증 [HIGH, 2주]
- `pip install plifepred2` → conda 격리 환경 설치
- SST-14, AGCKNFFWKTFTSC 계열 smoke test 실행
- 출력 단위(분 vs log 변환 vs 점수) 확인 및 정규화 방식 결정
- 성능 검증: PlifePred 원논문 벤치마크 세트 (163 natural peptides) 재현 시도
- 검증 결과로 P4 → P2/P3 등급 상향 또는 유지 결정
- 담당: engineer-backend, 기간: 2주

### 권고 3 — D-AA 처리를 위한 자체 ML 모델 로드맵 착수 [MED, 1~3개월]
- PEPlife2 데이터셋 다운로드 및 D-아미노산 함유 엔트리 추출
- SMILES 인코딩으로 D-AA chiral tag 부여 → PlifePred2 재학습 환경 구축
- Tan 2024 (Briefings in Bioinformatics) 방법론 재현 — 효소 descriptor + ESM-2 transfer learning
- 단기 목표: R²≥0.7 @ human blood natural; 중기: D-AA modified ≥ R²=0.6
- 담당: engineer-backend (구현) + reviewer-math (모델 검증), 기간: 4~8주 (1단계)

### 권고 4 — 벤치마크 세트 wet-lab 실측 가속 [HIGH, 병렬]
- SST-14 및 합의 후보 3종 + Octreotide(대조) = 5종 LC-MS/MS serum stability assay 발주
- 목적: in-silico 도구 정확도 검증의 ground truth 확보 (SST-14 t½=3분만으론 n=1로 부족)
- 담당: RI팀 (wet-lab), 기간: 2~4주 (발주 후)
- 발주서 기존 템플릿: `docs/wetlab/halflife_methodology.md`

### 권고 5 — ENDPOINT_CONFIDENCE 테이블 업데이트 [MED, 즉시]
- 위 §7의 코드 스니펫 4건을 `pharmacology_guards.py`에 추가
- `HEURISTIC_FUNCTION_DISCLAIMERS`에 PlifePred2 (P4), pepADMET (P2) 도구 한계 명세 추가
- 기존 `predict_half_life()` 함수에 도구 출처 구분 필드 (`source`, `confidence_grade`) 추가 분리
- 담당: engineer-backend, 기간: 3일 (코드 스니펫 참고하여 직접 구현)

---

## 9. 비교 표: 전체 도구 × 평가 기준

| 도구 | 혈청/혈중 t½ 직접 예측 | D-AA 지원 | 비천연 AA | 로컬 실행 | R² (best) | 통합 난이도 | 권장도 |
|-----|-------------------|---------|---------|---------|---------|-----------|------|
| ProtParam | ❌ (세포 내) | ❌ | ❌ | ✅ | 해당 없음 | 쉬움 | ❌ |
| HLP | ❌ (장내) | 미확인 | ❌ | ❌ | 해당 없음 | 중간 | ❌ |
| PlifePred | ✅ | △ | ❌ | ❌ | ~0.55 | 어려움(웹) | ◯ |
| PlifePred2 | ✅ | △(flag) | ❌ | ✅ | 미확인 | 쉬움(pip) | **✅ 1순위** |
| Tan 2024 TF | ✅ | 미확인 | 미확인 | ❌(미공개) | 0.90 | 불가 | 📋 참고 |
| pepADMET | ✅ | 미확인 | 일부 | ❌ | 0.90 | 중간(API) | **✅ 2순위** |
| PepMSND | △(분류만) | ❌ | ❌ | ❌ | 해당없음(분류) | 중간 | △ Triage |
| Cavaco 2021 | ✅ | ❌ | ❌ | △ | 0.78 | 중간 | △ 보조 |
| 자체 ML 모델 | ✅ (구축 시) | ✅ (구축 후) | ✅ (구축 후) | ✅ | 목표 ≥0.8 | 높음(개발 필요) | 중장기 |

---

## 10. §검증 필요

1. **PlifePred2 성능 검증 논문**: peer-reviewed 독립 벤치마크 미확보. 로컬 설치 후 PlifePred 원논문(PLOS ONE 2018) 테스트 세트 재현으로 자체 검증 필요
2. **pepADMET D-아미노산 지원 여부**: 문서에 명시 없음. Octreotide (D-Phe, D-Trp) 직접 입력 테스트 필요
3. **Tan 2024 모델 코드 공개 여부**: "데이터셋은 corresponding author에 요청"으로만 기재. 코드/웹서버 공개 여부 저자 확인 필요
4. **RC-160 (Vapreotide) 정량 t½**: 공개 문헌에서 정량값 미확인. 비교 분석에서 Spearman ρ 계산 제외 처리
5. **Cavaco 2021 앱 공개 여부**: JavaScript/Electron 기반 데스크탑 앱이 공개 배포 중인지 미확인
6. **PEPlife2 D-AA 엔트리 비율**: 수식/D-AA 함유 엔트리가 전체 4,412개 중 몇 개인지 미확인 — 자체 ML 모델 로드맵의 데이터 충분성 판단에 필수
7. **pepADMET API 접근 가능성**: 파이프라인 자동화를 위한 REST API 제공 여부 미확인

---

## 11. 참고 문헌 목록

1. Brazeau P et al. 1973 Science 179:77-79 — SST-14 원본 발견 논문, t½≈3분
2. Lamberts SWJ et al. 1996 NEJM 334:246 — Octreotide pharmacology
3. Bauer W et al. 1982 Life Sci 31:1133-1140 — Octreotide t½≈90분 원본 기술
4. Chanson P et al. 1993 Clin Pharmacol Ther 53:288-298 — Lanreotide IV t½ ~80~120분
5. Varshavsky A 1996 PNAS 93:12142-12149 — N-end rule (mammalian reticulocyte)
6. Gasteiger E et al. 2005 Proteomics Protocols Handbook pp571-607 — ProtParam 도구 출처
7. Sharma A et al. 2014 BMC Bioinformatics 15:282 — HLP 도구 (장내 반감기)
8. Mathur D et al. 2018 PLOS ONE 13(6):e0196829 — PlifePred 도구 (혈중 반감기)
9. Cavaco M et al. 2021 Clinical and Translational Science 14:1700. DOI:10.1111/cts.12985 — 물리화학 특성 기반 serum t½ 회귀 모델 (PMC8301568)
10. Tan Y et al. 2024 Briefings in Bioinformatics 25(4):bbae350. DOI:10.1093/bib/bbae350 — 효소 descriptor + Transfer learning 혈중 반감기 예측 (PMC11262833)
11. pepADMET: DOI:10.1021/acs.jcim.5c02518 (JCIM 2025) — pepADMET ADMET 플랫폼
12. Wang et al. 2025 Digital Discovery DOI:10.1039/D5DD00118H — PepMSND 혈중 안정성 분류
13. Mathur D et al. 2016 Sci Rep 6:36617 — PEPlife 데이터베이스
14. Biorxiv 2025-05-16 DOI:10.1101/2025.05.13.653654 — PEPlife2 업데이트 데이터베이스
15. PubMed 12952505 (Drugs R&D 2003) — Vapreotide (RC-160) 약리 리뷰
16. PubMed 10579475 — Lanreotide PK in renal insufficiency (t½=1.32~2.39h)
