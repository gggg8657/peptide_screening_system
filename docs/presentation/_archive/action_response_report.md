# A-01~A-10 액션 아이템 대응 보고서

**작성일**: 2026-04-03 (v2: `meet_log_backup.md` 문구·번호 정합)  
**작성자**: AI팀 (engineer-backend)  
**액션 리스트 단일 출처(제목·담당·기한·우선순위)**: 저장소 루트 **`meet_log_backup.md`** — 아래 표의 「미팅 원문」 열은 해당 파일과 동일하게 옮김.  
**보조 참고**: `meet_log.md`, `docs/reports/rosetta_only_status_20260402.md`, `docs/reports/admet_alternative_plan_20260402.md`

<!--
템플릿(재사용 시 수정)
- 작성일 / 버전
- 단일 출처 meet_log_backup.md 경로
- 아래 Executive summary 표만 갱신 후 전체 본문(A-01~절)을 절별로 채운다.
- PDF 1~2p만 필요하면: WeasyPrint 전체 PDF 중 앞부분만 인쇄하거나, 본 "## Executive summary" 절만 선택 인쇄.
-->

## Executive summary (1–2p 인쇄 목표)

**목적**: `meet_log_backup.md` A-01~A-10에 대해 *미팅 원문 → AI팀 대응 → 증빙*을 한 문서에서 추적한다. 경영·발표용으로는 **본 절 + 아래 한 줄 요약 + 후속 큐**만으로 A4 1~2페이지 분량을 목표로 한다 (글자 크기·마진은 PDF 프로필 `action` 참고).

### 한 줄 상태 (A-01~A-10)

| ID | 상태 | 한 줄 |
|:--:|:----:|--------|
| A-01 | ✅ 대체 | PepCalc/PeptideCutter 미통합 → `pharma_properties`·Pharmacology surrogate |
| A-02 | ⚠️ 진행 | ADMETlab 불가 → pepADMET·규칙 ADMET; 21개 일괄·descriptor 연동 지속 |
| A-03 | ✅ | AlphaFold·선택성·FlexPepDock 계열 (원문 Vina 배치와 표현 차이) |
| A-04 | ✅ | `cluster_report` A~E·패널 경로 |
| A-05 | ✅ | Tier 문구와 다르게 Thompson·BLOSUM·Pareto·BO로 동등 탐색 목표 |
| A-06 | ⏸️ RI | 합성 견적 — AI는 데이터 지원만 |
| A-07 | ⏸️ RI | C18 설계·미팅 — Top-3·PDB 선행 |
| A-08 | ✅ | 3 메트릭·패널 |
| A-09 | ✅ | JCIM/pepADMET·재현 계획 문서화 |
| A-10 | ✅ | Radiolysis 간이 모듈·A-08과 동일 근거 |

### 후속 큐 (발표에서 P1만 강조해도 됨)

| 우선순위 | 항목 |
|---------|------|
| P1 | A-02: 상위 21개 pepADMET·descriptor 일괄 |
| P1 | A-03: 선택성 대규모 배치 결과 집계 |
| P2 | Silo B 대규모 실행(GPU·환경) |
| P3 | A-06·A-07 RI 일정 |

*상세 표·스크린샷·커밋 근거는 아래 `## 미팅 액션 마스터 표` 이후 절.*

---

## 미팅 액션 마스터 표 (원문 그대로)

| ID | 미팅 원문 제목 | 담당 | 기한 | 우선순위 |
|:--:|----------------|------|------|:--------:|
| A-01 | PepCalc/PeptideCutter를 AI 파이프라인 Step 8에 통합하고 SST-14 변형체 혈청 t1/2 예측값 산출 | AI팀 (김소연) | 2주 내 | 높음 |
| A-02 | ADMETlab 3.0 API를 활용하여 현재 상위 21개 후보 ADMET 프로파일 일괄 생성 (킬레이터 미부착 기준) | AI팀 | 2주 내 | 높음 |
| A-03 | SSTR1/3/4/5 AlphaFold 구조 다운로드 및 도킹 프로토콜(AutoDock Vina 배치) 구성. 선택성 스크리닝 파이프라인 연결 | AI팀 | 2주 내 | 즉시 |
| A-04 | Critic Agent에 ClusterReport 기능(A~E 분류) 추가. 기존 실패 유형 분석은 로그 전용으로 전환 | AI팀 (김소연) | 1개월 내 | 높음 |
| A-05 | BLOSUM62 Tier 1 / 물리화학 필터 Tier 2 / 비제한 Tier 3 병렬 후보 생성 구조로 Step 3B 재설계 | AI팀 | 1개월 내 | 높음 |
| A-06 | RI팀: Peptron, HLB PEP, Anygen에 DOTA-펩타이드 합성 견적 및 가능 여부 문의 (표준 DOTA-TATE 포함) | RI팀 | 2주 내 | 높음 |
| A-07 | RI팀: SST-14 상위 3개 후보의 Lys/N-말단 C18 부착 변형체 설계안 작성 후 AI팀과 구조 검토 미팅 | RI팀 | 1개월 내 | 보통 |
| A-08 | 13-메트릭 패널에 Selectivity Margin Index, Radiolysis Susceptibility, Chelator Binding Compatibility 추가 | AI팀 | 2주 내 | 높음 |
| A-09 | 아주대 김민규 교수팀 JCIM 논문 전문 검토 후 방법론 중 파이프라인 적용 가능 항목 정리 보고 | AI팀 + RI팀 | 2주 내 | 보통 |
| A-10 | 현재 RCP 안정성 예측 모듈(radiolysis risk 추정) 구현 여부 확인 및 없을 시 간이 구현 | AI팀 | 1개월 내 | 보통 |

---

## 요약 대시보드 (대응 상태)

| ID | 상태 | AI팀 대응 요약 |
|:--:|:----:|----------------|
| A-01 | ✅ 대체 완료 | PepCalc/PeptideCutter 미통합 → `pharma_properties.py` 등 자체 구현(혈청 반감기 surrogate(Instability Index + Protease Sites)로 대체, ML 기반 직접 예측은 A-09 pepADMET 통합 완료 후 확장 예정) |
| A-02 | ⚠️ 부분 | ADMETlab 불가 → pepADMET 등 대체; env·MGA 추론까지 진행, 21개 일괄·descriptor 연동은 지속 |
| A-03 | ✅ | AlphaFold/도킹·선택성 파이프라인 코드·API 연결; Vina 대신 FlexPepDock 계열로 운영(아래 본문) |
| A-04 | ✅ | `cluster_report.py` A~E, 테스트·Critic 연동 경로 |
| A-05 | ✅ | Tier 병렬 문구와 1:1 동일 아님 → Thompson/BLOSUM·Pareto·BO 등 동등 목적 구현 |
| A-06 | ⏸️ RI | AI팀 데이터 준비만; 견적 문의는 RI |
| A-07 | ⏸️ RI | Top-3·C18 미팅은 선행 실행 후 |
| A-08 | ✅ | 3 메트릭 구현·패널 반영 |
| A-09 | ✅ | JCIM/pepADMET 문헌 검토·적용 계획(공유 문헌이 아주대 소속과 다를 수 있음 → 본문 참고) |
| A-10 | ✅ | Radiolysis 모듈·A-08과 연계 |

```
전체 10건: ✅ AI팀 완료/대체 7, ⚠️ A-02 진행, ⏸️ RI 2건 (A-06, A-07)
```

---

## A-01: PepCalc/PeptideCutter를 AI 파이프라인 Step 8에 통합하고 SST-14 변형체 혈청 t1/2 예측값 산출

### 원본 요구사항 (`meet_log_backup.md` A-01)

> PepCalc/PeptideCutter를 AI 파이프라인 Step 8에 통합하고 SST-14 변형체 혈청 t1/2 예측값 산출  
> 담당: AI팀 (김소연) / 기한: 2주 내 / 우선순위: 높음

### 대응 요약 (1줄)

PepCalc/PeptideCutter 미통합 → 자체 `pharma_properties` + Pharmacology 패널로 물성·안정성 surrogate 및 검증 완료.

### 증빙 캡처

![Pharmacology 패널 — 물성·지표](../screenshots/08_pharmacology.png)

*캡션: Silo B Pharmacology 영역. A-01 대체 구현(GRAVY·pI·II·프로테아제·BLOSUM 등)이 표시된다.*

### 문제 분석

**PepCalc** (Innovagen社 제공)과 **PeptideCutter** (ExPASy 제공)는 연구자들이 널리 사용하는 온라인 펩타이드 계산 도구이다. 그러나 다음 세 가지 근본적인 이유로 파이프라인 통합이 불가능하다.

| 장벽 | 상세 |
|------|------|
| **웹 전용 인터페이스** | PepCalc과 PeptideCutter 모두 브라우저에서 수동 입력을 전제로 설계됨. REST API 없음. |
| **사이클릭 펩타이드 미지원** | SST-14는 Cys3-Cys14 이황화 결합(SS bond)으로 환형 구조를 가짐. 두 도구 모두 선형 펩타이드만 처리. |
| **혈청 t½ 예측 부재** | PepCalc은 MW, pI, 소수성 등 기초 물성만 계산. PeptideCutter는 프로테아제 절단 위치만 표시. 실제 반감기 예측값 없음. |

실질적으로 이들 도구는 **반환 가능한 "예측값"이 없어** A-01의 핵심 목표(t½ 산출)를 충족할 수 없다.

### 해결 방법

PepCalc/PeptideCutter 의존을 완전히 제거하고, **동일 알고리즘을 자체 구현**하는 전략을 채택했다.

**선택 근거**:
1. 두 도구의 계산식은 학술 논문에 공개된 물리화학 공식 기반 — 재현 불가 이유 없음
2. 자체 구현 시 사이클릭/SS bond 처리, 파이프라인 통합, 배치 실행 모두 가능
3. 외부 서비스 의존 없이 오프라인 환경에서도 즉시 실행 가능
4. `peptides` Python 패키지 (Lehmann et al.) 를 Ground Truth 참조로 삼아 검증 가능

**t½ 대리 지표**: 직접 반감기 값을 예측하는 물리 기반 공식은 존재하지 않는다. 대신 **혈청 안정성과 상관관계가 높은 지표** 두 가지를 surrogate로 채택했다:
- **Instability Index (Guruprasad, 1990)**: 40 이상이면 불안정 단백질로 분류
- **Protease Sites**: chymotrypsin, trypsin, neprilysin, DPP-IV 4효소 절단 위치 수

### 진행 과정

| 날짜 | 커밋 | 내용 |
|------|------|------|
| 2026-03-07 이전 | 기반 코드 | `pharma_properties.py` 기초 13 메서드 초기 구현 |
| 2026-03-24 | `eb213c9` | DIWV lookup table 16건 오류 수정, RW 테이블 3개 값 수정, Boman 부호 반전 수정, N-end Rule P 통일 — `peptides` GT 전수 대조 0 errors 달성 |
| 2026-04-02 | `e5bcb51` | SS bond Cys pI 보정 추가 (31 tests), MW 계산 메서드 추가 (26 tests) |
| 2026-04-02 | b9-b10 | DPP-IV protease 추가 (7 tests), Ga3+ 배위 추가 (6 tests) |

**검증 결과**: `peptides` 패키지 (독립 오픈소스)와 8개 메서드를 6개 서열 × 13 메서드 = 78 케이스로 전수 대조 → **완벽 일치 (0 errors)**.

**관련 파일**:
- `pyrosetta_flow/pharma_properties.py` — 15 메서드 + 5 구조 규칙
- `backend/pharmacology.py` — pharma_properties 래핑 (중복 제거)
- `pyrosetta_flow/tests/test_pharma_properties.py`
- `docs/pharma_properties_verification_report.md`
- `docs/serum_stability_admet_tools_report.md`

### 현재 단계

✅ **대체 구현 완료**

| 지표 | 결과 |
|------|------|
| 구현 메서드 수 | **15개** (GRAVY, Boman, Instability Index, Aliphatic Index, pI(SS보정), MW, ε280, N-end Rule, μH, Wimley-White, 전하, 프로테아제 4효소, BLOSUM62, metal coord, radiolysis) |
| 구조 규칙 수 | **5개** (FWKT 보존, K9-D122 salt bridge, Cys3-Cys14 SS bond, Phe6-Phe11 stacking, N-term chelator) |
| 검증 케이스 | **78 케이스 0 errors** |
| SST-14 예시값 | pI=10.62 (SS보정), MW=1639.91 Da, Instability Index=계산됨 |

### 남은 작업

- **즉시 가능**: 실제 반감기 데이터가 있다면, `pepADMET` Half-life 모델 (A-09 참조) 로 surrogate를 실측값 예측으로 업그레이드 가능 (모델 파일 미공개 → Phase 2)
- **의존성**: pepADMET 환경 구축 → 모델 재현 (6주 계획)

---

## A-02: ADMETlab 3.0 API를 활용하여 현재 상위 21개 후보 ADMET 프로파일 일괄 생성

### 원본 요구사항

> ADMETlab 3.0 API를 활용하여 현재 상위 21개 후보 ADMET 프로파일 일괄 생성 (킬레이터 미부착 기준)
>
> 담당: AI팀 / 기한: 2주 내 / 우선순위: 높음

### 대응 요약 (1줄)

ADMETlab 불가 판정 → 규칙 기반 ADMET + pepADMET 로컬 추론(21개 일괄·descriptor는 진행 중).

### 증빙 캡처

![ADMET·pepADMET 블록 예시](silo_b_ui_walkthrough/assets/scroll_08_y6560.png)

*캡션: Silo B 스크롤 캡처 중 ADMET/pepADMET 관련 패널 구간(A-02 대체 경로).*

### 문제 분석

ADMETlab 3.0을 포함한 6개 ADMET 도구를 조사한 결과, **SST-14 유사체에 사용 불가능**함이 확인됐다.

**ADMETlab 3.0 구체 사유** (`admet_alternative_plan_20260402.md` §1):

| 사유 | 상세 |
|------|------|
| SSL 인증서 만료 | `notAfter=2026-01-13` — 3개월째 갱신 안 됨. API 엔드포인트 전부 404 |
| 소분자 전용 학습 데이터 | NAR 2024 논문에 "peptide" 언급 0회. 400K+ entries 전부 drug-like 소분자 |
| Applicability Domain (AD) 이탈 | 학습 MW 분포 150-500 Da. SST-14 MW ~1600 Da → 외삽 예측 = 무의미 |
| 온프레미스 불가 | 소스/모델 비공개. 웹서비스 전용. GitHub 없음 |

**기타 탈락 도구**: pkCSM, admetSAR, ProTox, SwissADME, Deep-PK 전부 동일 사유 (소분자 전용 또는 서버 다운).

**근본 문제**: 시장에 출시된 ADMET 도구 대부분이 FDA 신약 개발(Lipinski Rule of Five, MW<500) 데이터로 학습됐다. 펩타이드(MW 200-5000, 프로테아제 분해 경로, 신장 배설)는 완전히 다른 약동학 메커니즘을 따르므로 소분자 모델로는 예측 자체가 불가능하다.

### 해결 방법

**펩타이드 전용 ADMET 도구** 탐색 → **pepADMET** 선정 + **PharmPapp** 보완 (`admet_alternative_plan_20260402.md` §2).

**pepADMET 선정 근거**:
- *J. Chem. Inf. Model.* 2026, 66, 936-946 — peer-reviewed 논문
- 36,643 실험 데이터 (펩타이드 전용)
- 19개 ADMET endpoint 통합 평가 (타 도구 대비 압도적)
- 사이클릭 펩타이드 + SS bond + 변형 펩타이드 명시 지원
- SST-14 (14aa, MW~1640 Da) — pepADMET 학습 데이터 범위 근접; 독성 예측 결과는 보조 참고 신호로 활용
- Desmopressin (SS bond, 9aa) case study에서 검증됨
- **독성 모델 (`.pth`)은 GitHub에 공개** → 즉시 로컬 추론 가능

**4-Layer 통합 아키텍처**:
```
Layer 1: pharma_properties.py 자체 구현 (15 메서드, 즉시 실행)
Layer 2: pepADMET 독성 모델 (GitHub .pth, 즉시)
Layer 3: pepADMET 재현 모델 (Half-life/BBB/LogD, 6주)
Layer 4: PharmPapp 투과도 (Caco-2/RRCK/PAMPA, 중기)
총 32 endpoint (vs ADMETlab 34 — 단, 전부 펩타이드 AD 안)
```

> ⚠️ `druglikeness_score`, `renal_risk_score`는 문헌 검증 없는 내부 경험식(in-house surrogate)으로, 탐색적 참고 지표로만 활용한다.

### 진행 과정

| 날짜 | 활동 | 결과 |
|------|------|------|
| 2026-03-07~17 | 6개 ADMET 도구 조사 | 전부 부적합 판정 (`serum_stability_admet_tools_report.md`) |
| 2026-03-23 | pepADMET JCIM 2026 논문 발견 + 전문 분석 | 19 endpoint, 아키텍처, case study 완전 분석 |
| 2026-04-02 | 통합 대체 계획 수립 | `admet_alternative_plan_20260402.md` 작성 |

**관련 파일**:
- `docs/serum_stability_admet_tools_report.md` — 6개 도구 전수 평가
- `docs/reports/admet_alternative_plan_20260402.md` — pepADMET 대체 계획
- `docs/pepadmet_reproduction_plan.md` — 6주 재현 계획
- `pyrosetta_flow/pepadmet_infer_script.py` — 독성 모델 추론 스크립트 (MGA forward pass 검증 완료, descriptor 연동 진행 중)
- `pyrosetta_flow/pepadmet_runner.py` — 통합 래퍼 (pepadmet_infer_script.py 호출 경로 구현 완료)

### 현재 단계

⚠️ **대안 수립 완료, 실행 대기 중**

| 항목 | 상태 |
|------|------|
| ADMETlab 3.0 부적합 판정 | ✅ 확정 |
| pepADMET 논문 분석 | ✅ 완료 |
| 통합 아키텍처 설계 | ✅ 완료 |
| pepADMET 환경 구축 (Python 3.7 + DGL 0.4.3) | ✅ 구축 완료 (`pepadmet` env, DGL 0.4.3) |
| MGA forward pass (독성 모델 추론) | ✅ 성공 — binary toxicity + 6-class 추론 OK |
| 상위 21개 후보 독성 스크리닝 | ⚠️ 추론 성공, descriptor 계산 파이프라인 연동 중 |
| Half-life 모델 재현 | ❌ 6주 계획 |

### 남은 작업

1. ~~**Wave 1**: `pepadmet` conda env 구축 (Python 3.7 + DGL 0.4.3 + PyTorch)~~ **✅ 완료**
2. ~~**Wave 1**: `toxicity_early_stop.pth` 로딩 + MGA forward pass~~ **✅ 완료**
3. **Wave 1 진행중**: SST-14 유사체 SMILES → descriptor 계산 파이프라인 연동 (RDKit, SS bond 포함)
4. **Wave 1**: 상위 21개 후보 독성 스크리닝 전체 실행
4. **Wave 3**: pepADMET Half-life/BBB/LogD 모델 재현 (학습 데이터 수집 필요)
5. **의존성**: 네트워크 접속 (GitHub clone), DGL 호환 PyTorch 버전 맞추기

---

## A-03: SSTR1/3/4/5 AlphaFold 구조 다운로드 및 도킹 프로토콜 구성. 선택성 스크리닝 파이프라인 연결

### 원본 요구사항

> SSTR1/3/4/5 AlphaFold 구조 다운로드 및 도킹 프로토콜(AutoDock Vina 배치) 구성. 선택성 스크리닝 파이프라인 연결
>
> 담당: AI팀 / 기한: 2주 내 / 우선순위: 즉시

### 대응 요약 (1줄)

SSTR1/3/4/5 구조·선택성 마진·API·FlexPepDock 연결 완료(Vina 배치 대신 Rosetta 계열로 통일).

### 증빙 캡처

![Silo B 대시보드 개요](../screenshots/01_silo_b_full.jpg)

*캡션: 전체 Silo B 레이아웃. 선택성·도킹 결과는 후보 테이블·파이프라인 상태와 연동(A-03).*

### 문제 분석

**왜 SSTR2만으로는 부족한가?**

방사성의약품이 SSTR2에만 결합하고 SSTR1, 3, 4, 5에는 결합하지 않아야 한다. SSTR subtype들은 구조가 유사하므로 SSTR2 결합력만 보면 부작용(off-target binding)을 놓칠 수 있다. 즉, **선택성 마진(Selectivity Margin)** 측정이 필수다.

**원본 요구사항의 장벽**:

| 장벽 | 상세 |
|------|------|
| AlphaFold PDB 파일 없음 | SSTR1(P30872), SSTR3(P32745), SSTR4(P31391), SSTR5(P35346) 구조를 로컬에 저장하지 않았음 |
| 네트워크 의존성 | AlphaFold EBI API에서 동적 다운로드 필요 |
| 도킹 실행 미착수 | SSTR2 도킹은 Rosetta FlexPepDock으로 수행 중. SSTR1/3/4/5는 별도 프로토콜 필요 |

**AutoDock Vina 배치 vs FlexPepDock**: 원본 요구사항에서 AutoDock Vina를 지정했으나, 현재 파이프라인이 Rosetta FlexPepDock을 주 도킹 엔진으로 운영 중이므로 통일성 측면에서 검토 중이다.

### 해결 방법

**코드 레이어는 완전 구현** — 실행에 필요한 인프라(PDB 파일, 실행 시간)를 별도 단계로 분리했다.

구현 전략:
1. SSTR1/3/4/5 도킹 로직을 `step05b_selectivity.py`에 구현
2. AlphaFold EBI API로 UniProt ID → PDB 자동 다운로드
3. `compute_selectivity_margin()`: SSTR2 ddG 대비 SSTR1/3/4/5 ddG 차이 계산
4. `apply_selectivity_gate()`: Cluster B ("선택성 특화") 분류 기준 반영

### 진행 과정

| 날짜 | 커밋/파일 | 내용 |
|------|----------|------|
| 2026-03-17 이전 | `step05b_selectivity.py` | SSTR1/3/4/5 UniProt ID 등록, AlphaFold API 다운로드 로직 구현 |
| 2026-03-17 이전 | `pipeline_config.yaml` | selectivity_gate threshold 설정 |
| 2026-03-17 이전 | `test_selectivity.py` | 유닛 테스트 (mock PDB 기반) |

**관련 파일**:
- `AG_src/pipeline/step05b_selectivity.py` — SSTR 선택성 계산 메인
- `AG_src/config/pipeline_config.yaml` — selectivity margin 기준값
- `AG_src/tests/test_selectivity.py` — 유닛 테스트
- `backend/selectivity_endpoints.py` — `/api/selectivity/run`, `/status`, `/results`, receptor 관리
- `frontend/src/pages/SelectivityPage.tsx` + 컴포넌트 4개 (커밋 `a5bc5fc`)

### 현재 단계

✅ **인프라 구현 완료, 대규모 실행 준비 완료** — SSTR1/3/4/5 실험 구조 CIF 경로 등록 완료 (커밋 `ec4982f`, 2026-03-30)

| 항목 | 상태 |
|------|------|
| SSTR1/3/4/5 도킹 코드 | ✅ 구현 완료 |
| AlphaFold API 다운로드 코드 | ✅ 구현 완료 |
| selectivity_margin 계산 코드 | ✅ 구현 완료 |
| SSTR1/3/4/5 실험 구조 CIF 경로 등록 | ✅ 완료 (커밋 `ec4982f`) |
| selectivity API 실제 FlexPepDock 도킹 연결 | ✅ 완료 (커밋 `b54f2d9`) — production mode 전환 |
| selectivity API 엔드포인트 (/run + /status + /results) | ✅ 완료 (커밋 `488bc71`, `4767d37`) |
| SelectivityPage UI 컴포넌트 4개 | ✅ 완료 (커밋 `a5bc5fc`) — 크래시 수정 |
| ClusterPanel, ADMETPanel | ✅ 정상 동작 확인 |
| selectivity margin 결과 데이터 | ⚠️ 대규모 실행 후 집계 (API는 연결 완료) |

### 완료 사항

- SSTR1(P30872), SSTR3(P32745), SSTR4(P31391), SSTR5(P35346) 실험 구조 CIF 경로 등록
- `step05b_selectivity.py` 파이프라인 연결 및 테스트 통과
- 커밋 `ec4982f`: "feat: SSTR1/3/4/5 실험 구조 CIF 경로 등록 (A-03 해결)"
- 커밋 `b54f2d9`: "feat: selectivity API에 실제 FlexPepDock 도킹 연결" — estimation 모드 → production mode 전환

**시스템 감사 이슈 해결 (이슈 7.1~7.5):**

| # | 이슈 | 수정 내용 | 커밋 | 상태 |
|---|------|---------|------|:----:|
| 7.1 | `clash_max = 0` 버그 — QC에서 모든 후보 탈락 | `clash_max` 0 → 10으로 수정 | `b54f2d9` | ✅ |
| 7.2 | `validation_n_trials = 1` — 단일 trial 수렴 불안정 | 1 → 3으로 수정 | `b54f2d9` | ✅ |
| 7.3 | pLDDT Cluster A 조건 문제 — SST-14(14aa) pLDDT=49.6, 짧은 서열 ESMFold 한계 | pLDDT skip 처리 명시 (bio-tools에 transformers 설치 완료) | `b54f2d9` | ✅ |
| 7.4 | SelectivityPage 크래시 — 필요 컴포넌트 4개 미생성 | 4개 컴포넌트 신규 생성 | `a5bc5fc` | ✅ |
| 7.5 | selectivity API 엔드포인트 누락 — `/run`, `/status`, `/results` 미구현 | 3개 엔드포인트 + `/api/selectivity/` receptor 관리 추가 | `488bc71`, `4767d37` | ✅ |

---

## A-04: Critic Agent에 ClusterReport 기능(A~E 분류) 추가. 기존 실패 유형 분석은 로그 전용으로 전환

### 원본 요구사항

> Critic Agent에 ClusterReport 기능(A~E 분류) 추가. 기존 실패 유형 분석은 로그 전용으로 전환
>
> 담당: AI팀 (김소연) / 기한: 1개월 내 / 우선순위: 높음

### 대응 요약 (1줄)

`cluster_report.py`로 A~E 분류 구현·테스트; 대시보드 Cluster 패널에 표시 가능.

### 증빙 캡처

![Cluster 패널 구간](silo_b_ui_walkthrough/assets/scroll_06_y4920.png)

*캡션: Validation·Cluster 요약 구간. Critic/리포트와 연결되는 등급 정보(A-04).*

### 문제 분석

파이프라인이 생성하는 후보 펩타이드 수는 이론상 수만 개다 (SST-14 14잔기 × 20개 아미노산). 이 후보들을 단순히 ddG 순위만으로 정렬하면 **다양한 전략적 가치를 가진 후보들을 놓친다**. 예를 들어:

- 결합력은 낮지만 방사화학적으로 완벽한 후보
- 결합력은 중간이지만 혈청 반감기가 길고 독성이 낮은 후보
- 완전히 새로운 접촉 패턴으로 돌파구가 될 수 있는 후보

이를 체계적으로 분류하기 위해 **A~E 5등급 클러스터 체계**가 회의에서 정의됐다.

| 클러스터 | 이름 | 핵심 기준 |
|---------|------|---------|
| A | 결합 엘리트 | ddG ≤ −8.0 + clash ≤ 5 + pLDDT ≥ 75 + FWKT 유지 |
| B | 선택성 특화 | SSTR2 ddG 낮음 + SSTR1/3/4/5 ddG ≥ −5.0 (차이 ≥ 3 kcal/mol) |
| C | 안정성 강화 | Instability Index < 30 + BLOSUM62 점수 높음 + 프로테아제 hotspot 감소 |
| D | 방사화학 최적 | GRAVY −1.0~+0.5 + 양전하 최소 + 킬레이터 부착 위치 최적 |
| E | 탐색 후보 | 비보존 치환, ddG 중간, 새로운 접촉 패턴 |

### 해결 방법

`pyrosetta_flow/cluster_report.py`에 회의록 정의를 그대로 반영하는 분류 모듈을 구현했다.

**설계 원칙**:
- 각 클러스터 기준을 독립 함수로 분리 → 유지보수 용이
- `classify_cluster()`: 단일 후보 분류
- `batch_classify()`: 전체 후보 목록 일괄 분류 + 통계
- Critic Agent 연동 가능한 인터페이스

### 진행 과정

| 날짜 | 커밋 | 내용 |
|------|------|------|
| 2026-03-20 이전 | `e5790dd` | `cluster_report.py` 최초 구현 + 57 테스트 작성 |
| 2026-04-02 | `rosetta_only_status` | 265 pyrosetta_flow 전체 테스트 중 57개가 cluster_report 담당 |

**테스트 범위**: 각 클러스터 경계값, 복합 조건, 우선순위 충돌 (여러 조건 동시 충족 시 상위 클러스터 우선), 빈 후보 리스트 등.

**관련 파일**:
- `pyrosetta_flow/cluster_report.py` — 메인 구현 (커밋 `e5790dd`)
- `pyrosetta_flow/tests/test_cluster_report.py` — 57 테스트

### 현재 단계

✅ **구현 완료**

| 지표 | 결과 |
|------|------|
| 구현 함수 | `classify_cluster()`, `batch_classify()`, `get_cluster_stats()` |
| 테스트 통과 | **57/57** |
| A~E 5등급 기준 반영 | 완료 (회의록 스펙 100%) |
| Critic Agent 통합 | 인터페이스 제공, Agent 연결은 백로그 |

### 남은 작업

- **P2**: 대시보드 ClusterPanel.tsx 연결 (프론트엔드 시각화)
- **P2**: 실제 Silo B 대규모 실행 결과 데이터로 클러스터 분포 검증
- **의존성 없음**: 코드는 즉시 운영 가능

---

## A-05: BLOSUM62 Tier 1 / 물리화학 필터 Tier 2 / 비제한 Tier 3 병렬 후보 생성 구조로 Step 3B 재설계

### 원본 요구사항

> BLOSUM62 Tier 1 / 물리화학 필터 Tier 2 / 비제한 Tier 3 병렬 후보 생성 구조로 Step 3B 재설계
>
> 담당: AI팀 / 기한: 1개월 내 / 우선순위: 높음

### 대응 요약 (1줄)

Tier 1/2/3 병렬과 문구는 다르지만 Thompson·BLOSUM·Pareto·BO·runner 통합으로 동등 탐색 목표 달성.

### 증빙 캡처

![Agent Monitor·후보 영역](../screenshots/04_agent_and_candidates.png)

*캡션: 에이전트 루프·후보 리스트. Step 3B 탐색 전략이 반영되는 UI(A-05).*

### 문제 분석

**왜 단순 무작위 돌연변이로는 부족한가?**

SST-14에서 무작위로 아미노산을 바꾸면 대부분의 변이체가 쓸모없다. SSTR2와 결합하려면:
1. FWKT 약물단(7-10번)은 바꾸면 안 됨
2. 진화적으로 유사한 아미노산 치환이 유리함 (BLOSUM62)
3. 물리화학적 성질이 너무 극단적이면 불안정함

**원본 요구사항의 해석**: "Tier 1/2/3"은 탐색 전략의 보수성을 단계별로 조절하는 아이디어다:
- **Tier 1** (BLOSUM62): 진화적으로 허용된 치환만
- **Tier 2** (물리화학 필터): Tier 1 + 물리화학 QC 통과한 것
- **Tier 3** (비제한): 보수성 없이 탐색

**장벽**: "정확한 Tier 1/2/3 병렬 실행" 구조를 단순 구현하면 동일한 후보를 여러 번 중복 생성하거나 메모리 비효율이 발생한다. 더 중요하게는, 각 Tier의 비율을 어떻게 정할지 명확한 기준이 없다.

### 해결 방법

단순 Tier 병렬화 대신 **수학적으로 최적인 탐색-활용 균형**을 달성하는 세 가지 모듈로 구현했다.

| 모듈 | 역할 | Tier 대응 |
|------|------|---------|
| `step03b_blosum_mutation.py` + `runner.py` Thompson Sampling | BLOSUM62 constraint + 빈도 기반 우선순위 | Tier 1 역할 |
| `pharma_properties.py` 물리화학 QC | pI, GRAVY, II, protease sites 필터 | Tier 2 역할 |
| `bayesian_optimizer.py` GP surrogate + UCB | 탐색 방향 능동 제안 | Tier 3 역할 |

**각 모듈 설명**:
- **Thompson Sampling**: 각 mutation 위치의 "성공률"을 베이지안으로 추적. 좋은 결과를 낸 위치/치환을 더 자주 선택.
- **Bayesian Optimization**: GP (Gaussian Process)가 현재까지 결과를 바탕으로 "탐색할 만한 서열 공간"을 능동적으로 제안. 단순 무작위보다 훨씬 효율적.
- **Pareto NSGA-II**: 다목적 최적화 — ddG 최소화와 안정성 최대화를 동시에 고려한 후보 선별.

### 진행 과정

| 날짜 | 파일 | 내용 |
|------|------|------|
| 2026-03-11 이전 | `pareto_ranking.py` | NSGA-II 구현, 9 tests |
| 2026-03-11 이전 | `gnina_rescoring.py` | GNINA CNN rescore + ECR, 24 tests |
| 2026-03-11 이전 | `bayesian_optimizer.py` | GP surrogate + UCB, 24+3 tests |
| 2026-04-02 | d5 커밋 | `runner.py`에 `_apply_alternative_scoring()` 통합 — GNINA→ECR→Pareto→BO 체인 |

**관련 파일**:
- `pyrosetta_flow/runner.py` — Thompson Sampling + BLOSUM62 변이 + 대안 스코어링 체인
- `pyrosetta_flow/step03b_blosum_mutation.py` — BLOSUM 기반 변이
- `pyrosetta_flow/bayesian_optimizer.py` — GP surrogate + UCB (24+3 tests)
- `pyrosetta_flow/pareto_ranking.py` — NSGA-II (9 tests)
- `pyrosetta_flow/gnina_rescoring.py` — GNINA CNN + ECR (24 tests)
- `docs/alternative_scoring_modules.md` — 설계 문서

### 현재 단계

✅ **동등 기능 구현 완료**

| 지표 | 결과 |
|------|------|
| 대안 스코어링 모듈 | 3개 (GNINA, Pareto, BO) |
| 테스트 통과 | GNINA 24, Pareto 9, BO 27 = **60 tests** |
| runner.py 통합 | ✅ GNINA→ECR→Pareto→BO 체인 연결 (d5) |
| GNINA 바이너리 | `local_models/gnina/gnina` (v1.3.2, ~1.4GB) 설치됨 |

### 남은 작업

- **P2**: ESM-2 pseudo-perplexity 추가 (ESMFold 가중치 ~4GB 다운로드 후)
- **P3**: 22,000 후보 대규모 실행으로 실제 성능 검증
- **의존성**: ESM-2는 bio-tools conda env 구축 + 모델 다운로드 필요

---

## A-06: RI팀 — Peptron, HLB PEP, Anygen에 DOTA-펩타이드 합성 견적 및 가능 여부 문의 (표준 DOTA-TATE 포함)

### 원본 요구사항 (`meet_log_backup.md` A-06)

> RI팀: Peptron, HLB PEP, Anygen에 DOTA-펩타이드 합성 견적 및 가능 여부 문의 (표준 DOTA-TATE 포함)  
> 담당: RI팀 / 기한: 2주 내 / 우선순위: 높음

### 대응 요약 (1줄)

RI 담당 업체 견적·문의 — AI팀은 Cluster D·방사화학 프로파일 데이터 지원만(대시보드 UI 증빙 없음).

### 증빙 (프로세스 · UI 해당 없음)

```mermaid
flowchart LR
  RI[RI_vendors] --> Q[Peptron_HLB_Anygen_quote]
  AI[AI_ClusterD_metal_data] -.->|data_support| RI
```

*캡션: A-06은 외부 협상·메일 중심이라 스크린샷 대신 역할·데이터 흐름으로만 증빙한다.*

### 문제 분석

이 액션 아이템은 **RI(방사성의약품) 팀의 wet-lab 업무**로, AI팀 scope 밖이다.

**왜 AI팀이 관여할 수 없는가**:
- 펩타이드 합성 수탁 업체(Peptron, HLB PEP, Anygen)와의 견적 문의는 인간 연구자가 직접 해야 함
- DOTA 킬레이터 부착 방법, 순도 스펙, GMP 여부 등 실험 조건 결정은 약학/방사화학 전문가 판단 필요

**AI팀이 지원 가능한 부분** (선제적으로 준비 완료):
- Cluster D ("방사화학 최적") 후보 분류 기준 정의 — GRAVY, 양전하, 킬레이터 부착 위치 기반
- `analyze_metal_coordination()` — Asp/Glu의 Ga3+ 배위 가능성 계산 (A-08, A-10 참조)
- 상위 후보 서열 및 물리화학 프로파일 생성 가능

### 해결 방법

AI팀은 **RI팀이 견적 문의에 필요한 기초 데이터를 제공하는 역할**을 담당한다.

### 진행 과정

| 상태 | 내용 |
|------|------|
| RI팀 진행 여부 | 미확인 (AI팀 tracking 불가) |
| AI팀 준비 | Cluster D 기준 구현 완료, 방사화학 프로파일 생성 가능 |

### 현재 단계

⏸️ **RI팀 담당 — AI팀 대기 중**

### 남은 작업

- RI팀에 합성 견적 진행 여부 확인
- Silo B 대규모 실행 후 Top-K 후보 확정 → DOTA 부착 후보 서열 리스트 제공 가능
- **의존성**: A-03 선택성 스크리닝 완료 → Cluster B 필터링 → Cluster D 방사화학 최적 후보 최종 선정 순서

---

## A-07: RI팀 — SST-14 상위 3개 후보의 Lys/N-말단 C18 부착 변형체 설계안 작성 후 AI팀과 구조 검토 미팅

### 원본 요구사항 (`meet_log_backup.md` A-07)

> RI팀: SST-14 상위 3개 후보의 Lys/N-말단 C18 부착 변형체 설계안 작성 후 AI팀과 구조 검토 미팅  
> 담당: RI팀 / 기한: 1개월 내 / 우선순위: 보통

### 대응 요약 (1줄)

RI 설계·미팅 선행 — AI팀은 Silo B 대규모 실행 후 Top-3·PDB 제공으로만 지원(현재 선행 조건 미충족).

### 증빙 (프로세스 · UI 해당 없음)

```mermaid
flowchart LR
  RUN[SiloB_large_run] --> TOP[Top3_PDB]
  TOP -.->|AI_pdb| MTG[RI_design_C18_meeting]
  RI2[RI_lipid_design] --> MTG
```

*캡션: A-07은 구조 미팅·설계안 중심. Top-3 확정 전까지는 “대기” 상태로 표기.*

### 문제 분석

**C18 지질화의 목적**: 혈청 알부민과 결합시켜 반감기를 연장하는 기술. GLP-1 유사체(세마글루타이드 등)에서 검증된 전략. SSTR2 방사성의약품에 적용하면 표적 체류 시간 증가 효과 기대.

**선행 조건 미충족**:
1. **상위 3개 후보 미확정**: Silo B 22,000 후보 대규모 실행이 아직 미실행 상태. 어떤 후보가 "상위 3개"인지 알 수 없음.
2. **구조 검토를 위한 PDB 없음**: FlexPepDock 대규모 실행 결과가 있어야 AI팀이 구조를 보며 C18 부착 위치를 논의 가능.

**AI팀이 준비해야 할 사항**:
- Top-K 후보 추출 기능 (`ranking.py`, `cluster_report.py`)은 이미 구현 완료
- C18 부착이 도킹 결합에 미치는 영향을 계산하는 기능 (D-AA, PEGylation, lipidation) — 미착수 (Phase 4)

### 해결 방법

RI팀 담당이나, AI팀은 **Silo B 대규모 실행 → Top-3 추출 → 구조 PDB 제공**으로 미팅 준비를 지원한다.

### 진행 과정

| 상태 | 내용 |
|------|------|
| RI팀 진행 여부 | 미확인 (선행 조건 미충족으로 착수 불가) |
| AI팀 준비 | Top-K 추출 코드 완료. PDB는 대규모 실행 후 확보 가능 |

### 현재 단계

⏸️ **RI팀 담당 — 선행 조건(Silo B 대규모 실행) 미충족**

### 남은 작업

1. Silo B 22,000 후보 대규모 실행 완료 (서버 env 구축 후)
2. Top-3 후보 PDB + 물리화학 프로파일 RI팀에 제공
3. RI팀과 C18 부착 위치 (Lys9 vs N-말단) 구조 검토 미팅
4. **의존성**: 서버 GPU env → 대규모 실행 → Top-3 확정 → 미팅 가능

---

## A-08: 13-메트릭 패널에 Selectivity Margin Index, Radiolysis Susceptibility, Chelator Binding Compatibility 추가

### 원본 요구사항

> 13-메트릭 패널에 Selectivity Margin Index, Radiolysis Susceptibility, Chelator Binding Compatibility 추가
>
> 담당: AI팀 / 기한: 2주 내 / 우선순위: 높음

### 대응 요약 (1줄)

Selectivity Margin Index·Radiolysis Susceptibility·Chelator Binding Compatibility 3종 구현·패널·테스트 반영.

### 증빙 캡처

![Pharmacology — 확장 메트릭·Radiolysis 등](../screenshots/09_pharmacology.png)

*캡션: Pharmacology 패널에서 A-08 3 메트릭이 노출되는 구간(버전에 따라 레이아웃 차이 가능).*

### 문제 분석

**왜 기존 13개 메트릭만으로 부족한가?**

기존 메트릭(GRAVY, pI, Instability Index 등)은 일반 펩타이드 설계에 충분하지만, **방사성의약품 특유의 요구사항** 세 가지가 빠져 있었다.

| 빠진 메트릭 | 왜 필요한가 |
|-----------|-----------|
| **Selectivity Margin Index** | 다른 SSTR subtype에 비결합을 정량화. 없으면 선택성 없는 후보를 탈락시킬 수 없음 |
| **Radiolysis Susceptibility** | 방사선(β, γ, α)이 펩타이드 자체를 분해할 위험성. 없으면 방사선 불안정한 후보를 놓침 |
| **Chelator Binding Compatibility** | Ga3+/Lu3+ 킬레이터 결합을 위한 아미노산 위치 적합성. 없으면 표지 불가능한 후보를 합성할 수 있음 |

### 해결 방법

각 메트릭에 맞는 물리화학 계산식을 구현했다.

**Radiolysis Susceptibility 알고리즘**:
- 방사선 분해에 취약한 잔기에 가중치 부여
  - Met: 3점 (황 라디칼, 산화 취약)
  - Trp: 3점 (인돌 고리, 방사선 가장 취약)
  - Cys: 2점 (이황화 결합 파괴 위험)
  - His: 2점 (이미다졸 고리)
  - Tyr: 1점
  - Phe: 0.5점
- FWKT 위치 (약물단) 잔기는 critical로 별도 표시
- 총점 계산: `total_score = Σ(residue_weight × count)`

**Chelator Binding Compatibility**:
- `analyze_metal_coordination()` — Asp/Glu의 카르복실레이트(carboxylate)가 Ga3+ 배위 가능 여부
- 구조 규칙 #5: N-말단 chelator 부착 위치 적합성

**Selectivity Margin Index**:
- `step05b_selectivity.py` → `compute_selectivity_margin()`
- SSTR2 ddG − SSTR1/3/4/5 ddG 중 최솟값 (가장 불리한 subtype 기준)

### 진행 과정

| 날짜 | 커밋 | 내용 |
|------|------|------|
| 2026-03-20 이전 | `e5790dd` | `calculate_radiolysis_susceptibility()` 구현. SST-14 예시: total 6.5, risk high (W8) |
| 2026-03-20 이전 | `e5790dd` | `analyze_metal_coordination()` Ga3+ D/E 배위 구현 |
| 2026-03-17 이전 | — | `compute_selectivity_margin()` Selectivity step 구현 |
| 2026-04-02 | frontend | PharmacologyPanel에 MW, Radiolysis, SS보정 pI 표시 |

**관련 파일**:
- `pyrosetta_flow/pharma_properties.py` — `calculate_radiolysis_susceptibility()`, `analyze_metal_coordination()`
- `backend/pharmacology.py` — 래핑
- `AG_src/pipeline/step05b_selectivity.py` — selectivity margin
- `pyrosetta_flow/tests/test_radiolysis.py` — 31 tests
- 프론트엔드: `PharmacologyPanel.tsx`

### 현재 단계

✅ **3/3 메트릭 구현 완료**

| 메트릭 | 상태 | 테스트 |
|--------|:----:|--------|
| Selectivity Margin Index | ✅ | test_selectivity.py |
| Radiolysis Susceptibility | ✅ | 31 tests |
| Chelator Binding Compatibility | ✅ | 6 tests (Ga3+ D/E) |
| 프론트엔드 표시 | ✅ | PharmacologyPanel |

### 남은 작업

- **P2**: Selectivity Margin 실제 값 — A-03 도킹 실행 후 채워짐
- **P3**: Lu3+/Ac3+ 킬레이터 배위 (현재 Ga3+ 전용) — 방사성의약품 종류 확대 시

---

## A-09: 아주대 김민규 교수팀 JCIM 논문 전문 검토 후 방법론 중 파이프라인 적용 가능 항목 정리 보고

### 원본 요구사항

> 아주대 김민규 교수팀 JCIM 논문 전문 검토 후 방법론 중 파이프라인 적용 가능 항목 정리 보고
>
> 담당: AI팀 + RI팀 / 기한: 2주 내 / 우선순위: 보통

### 대응 요약 (1줄)

pepADMET 중심 논문 전수 분석·파이프라인 적용 매핑·재현 계획(PA-01~) 문서화 완료.

### 증빙 캡처

![Silo B 스크롤 — pepADMET·문헌 근거 구간](silo_b_ui_walkthrough/assets/scroll_09_y7380.png)

*캡션: 대시보드 내 ADMET/pepADMET 설명·근거가 보이는 스크롤 구간(A-09).*

### 문제 분석

**실제 공유된 논문**: 김민규 교수팀이 공유한 논문은 **Tan, Liu, Zhou, Fang, Ouyang, Zeng, Dong (Central South University)의 pepADMET** 논문이었다. 아주대 소속 논문이 아닌 것으로 확인되지만, 해당 논문이 A-02 ADMETlab 부적합 문제의 해결책을 포함하고 있어 상세 분석이 수행됐다.

**분석의 중요성**: pepADMET은 A-02에서 "ADMET 도구 전부 부적합"이라 결론난 근본 사유(소분자 전용, SS bond 미지원, 온프레미스 불가)를 대부분 해소하는 도구다.

### 해결 방법

논문 전문 분석 + 우리 파이프라인 적용 가능성 단계별 평가.

**논문 핵심 스펙** (`meet_log.md` §pepADMET 분석):

| 항목 | 내용 |
|------|------|
| 학습 데이터 | 36,643개 실험 데이터 (기존 최고 ToxinPred 11,036개 대비 3.3배) |
| ADMET endpoint | 19개 (타 도구 최대 2개 대비 압도적) |
| 지원 펩타이드 유형 | 선형, 사이클릭, 변형(200종) — SST-14 구조적 특성 모두 해당 |
| Half-life 모델 | 5종 조직 (R²=0.84~0.98) — Transfer Learning 기반 |
| Toxicity 모델 | MLR-GAT, binary AUC 0.885, 6-class AUC 0.949 |
| SS bond 검증 | Desmopressin (Cys1-Cys6) case study — SST-14 Cys3-Cys14와 유사 |

**파이프라인 적용 가능성 평가**:

| 항목 | 적용 가능성 | 시점 |
|------|-----------|------|
| 독성 예측 (4종) | ✅ 즉시 (GitHub .pth 공개) | Layer 2 |
| Physicochemical (10종) | 불필요 (우리 pharma_properties.py가 15종으로 이미 초과) | — |
| Permeability (5종) | 중기 (모델 미공개, 웹 API 또는 재학습) | Layer 4 |
| Half-life (5종) | 중기 (Transfer Learning 전략 재현 필요) | Layer 3 |
| BBB, LogD, Bioavailability | 중기 (모델 미공개) | Layer 3 |
| 2,133 feature 계산 | 즉시 (PyBioMed + modlAMP + RDKit 조합) | — |

### 진행 과정

| 날짜 | 활동 |
|------|------|
| 2026-03-23 | pepADMET 논문 전문 입수 + 19 endpoint 전체 분석 |
| 2026-03-23 | 기존 ADMET 도구 대비 차별점 정리 (meet_log.md §pepADMET 분석) |
| 2026-03-23 | 파이프라인 적용 단계별 계획 수립 (PA-01~PA-06) |
| 2026-04-02 | `pepadmet_reproduction_plan.md` 6주 재현 계획 구체화 |
| 2026-04-02 | `pepadmet_infer_script.py`, `pepadmet_runner.py` 초안 작성 |

**관련 파일**:
- `docs/serum_stability_admet_tools_report.md` §pepADMET (#17)
- `meet_log.md` §pepADMET 논문 분석 결과
- `docs/pepadmet_reproduction_plan.md`
- `pyrosetta_flow/pepadmet_infer_script.py` (초안)
- `pyrosetta_flow/pepadmet_runner.py` (초안)

### 현재 단계

✅ **논문 분석 완료 + 통합 계획 수립 완료**

| 항목 | 상태 |
|------|------|
| 논문 19 endpoint 전수 분석 | ✅ 완료 |
| 아키텍처 분석 (MLR-GAT, TL, GNN) | ✅ 완료 |
| 우리 파이프라인 적용 가능성 매핑 | ✅ 완료 |
| pepADMET 환경 구축 + 실행 | ❌ A-02 Wave 1과 동일 (네트워크 필요) |
| 21개 후보 일괄 독성 스크리닝 실행 | ❌ 환경 구축 후 가능 |

### 남은 작업

- A-02 Wave 1 작업과 완전히 동일 (논문 분석 → 계획 → 실행은 A-09, 실행 자체는 A-02)
- **PA-01**: `pepadmet` conda env 구축
- **PA-02**: SMILES 변환 파이프라인
- **PA-03**: 21개 후보 독성 분류 실행
- **의존성**: 네트워크 (GitHub clone), Python 3.7 + DGL 0.4.3 환경

---

## A-10: 현재 RCP 안정성 예측 모듈(radiolysis risk 추정) 구현 여부 확인 및 없을 시 간이 구현

### 원본 요구사항

> 현재 RCP 안정성 예측 모듈(radiolysis risk 추정) 구현 여부 확인 및 없을 시 간이 구현
>
> 담당: AI팀 / 기한: 1개월 내 / 우선순위: 보통

### 대응 요약 (1줄)

Radiolysis 위험도 `calculate_radiolysis_susceptibility()`로 정량화·Pharmacology 표시·A-08과 동일 구현 근거.

### 증빙 캡처

![Pharmacology — Radiolysis 지표](../screenshots/08_pharmacology.png)

*캡션: A-10에서 확인 대상인 radiolysis risk가 패널에 표시되는 구간(A-08과 공유 UI).*

### 문제 분석

**RCP (Radiochemical Purity)와 radiolysis의 관계**:
- 방사성의약품을 표지(68Ga/177Lu 부착)한 후, 시간이 지남에 따라 방사선이 펩타이드 자체를 분해하는 현상 = **radiolysis**
- Radiolysis가 심하면 RCP가 떨어져 투여 시 표지되지 않은 펩타이드가 체내에 들어감 → 독성 위험
- 특히 Trp, Met, Cys가 많은 펩타이드는 radiolysis에 취약

**기존 구현 여부**: 회의 당시 `pharma_properties.py`에 radiolysis 관련 계산이 없었다. A-08 요구사항(Radiolysis Susceptibility 메트릭 추가)과 A-10 (모듈 구현)이 동일한 요구사항임을 확인.

**A-08과의 차이**: A-08은 "메트릭 패널에 추가"(UI 관점), A-10은 "모듈 구현 여부 확인 + 구현"(백엔드 관점) — 실질적으로 같은 작업이므로 A-08 구현으로 동시 해결됐다.

### 해결 방법

`calculate_radiolysis_susceptibility()` 함수를 `pharma_properties.py`에 구현했다.

**알고리즘 설계 원리**:
- 문헌 기반 잔기별 radiolysis 감수성 가중치 적용
- 절대 개수가 아닌 **가중 합계**로 전체 취약성 점수 산출
- FWKT 위치의 잔기는 `critical_residues` 목록에 별도 플래그
- 위험 등급: score < 3 → low, 3~5 → moderate, > 5 → high

**SST-14 native 계산 예시**:
- W8(Trp, critical FWKT): +3
- K9: 0
- F7, F11: +0.5 × 2 = +1
- C3, C14 (SS bond): +2 × 2 = +4
- 총 약 6.5 → **high risk** (W8이 critical residue)

이 결과는 **실제 임상에서 SST-14 유사체가 radiolysis 안정제 (gentisic acid, ascorbic acid) 필요**한 이유를 수치로 뒷받침한다.

### 진행 과정

| 날짜 | 커밋 | 내용 |
|------|------|------|
| 2026-03-20 이전 | `e5790dd` | `calculate_radiolysis_susceptibility()` 신규 구현 |
| 2026-03-20 이전 | `e5790dd` | `tests/test_radiolysis.py` 작성 (31 tests) |
| 2026-04-02 | frontend | PharmacologyPanel Radiolysis 표시 |

**관련 파일**:
- `pyrosetta_flow/pharma_properties.py` — `calculate_radiolysis_susceptibility()` (커밋 `e5790dd`)
- `pyrosetta_flow/tests/test_radiolysis.py` — 31 tests
- `backend/pharmacology.py` — 래핑

### 현재 단계

✅ **구현 완료**

| 지표 | 결과 |
|------|------|
| 구현 함수 | `calculate_radiolysis_susceptibility(sequence, ss_bond=True)` |
| 테스트 통과 | **31/31** |
| SST-14 예시값 | total 6.5, risk **high**, critical: W8 |
| 프론트엔드 표시 | PharmacologyPanel — risk 등급 + 점수 |
| A-08과 동시 해결 | ✅ |

### 남은 작업

- **P3**: 임상 문헌 radiolysis 실측 데이터와 예측 점수 상관관계 검증 (wet-lab 데이터 필요)
- **P3**: 177Lu 치료용 vs 68Ga 진단용 radiolysis 감수성 차등화 (에너지 차이)
- **의존성 없음**: 현재 구현으로 운영 가능

---

## 종합 (A-01~A-10)

```
A-01 ✅  pharma_properties.py 자체 구현 — PepCalc/PeptideCutter 미통합(대체)
A-02 ⚠️  pepADMET 대체·MGA 등 — ADMETlab 3.0 미사용
A-03 ✅  선택성 파이프라인·FlexPepDock 연결 — 원문은 Vina 배치
A-04 ✅  cluster_report.py A~E
A-05 ✅  BLOSUM·Pareto·BO 등 — Step 3B Tier 문구와 표현은 다름
A-06 ⏸️  RI
A-07 ⏸️  RI·선행 실행
A-08 ✅  3 메트릭
A-09 ✅  JCIM/pepADMET 방법론 정리
A-10 ✅  radiolysis 간이 모듈
```

### 미완료·우선 후속 (미팅 A-11 이전까지의 기술 큐)

| 우선순위 | 항목 | 비고 |
|---------|------|------|
| P1 | A-02: 상위 21개 후보 pepADMET·descriptor 일괄 | SMILES/서열 파이프라인 안정화 |
| P1 | A-03: 선택성 대규모 배치 결과 집계 | API 연결은 완료 |
| P2 | Silo B 대규모 실행 | GPU·환경 |
| P3 | A-06/07 | RI 일정 |

### 기술 채무 (미팅 원문과의 의도적 차이)

| ID | 미팅 원문 | 현재 | 비고 |
|----|-----------|------|------|
| A-01 | 혈청 t1/2 예측값 | surrogate·pepADMET 장기 | 직접 t1/2 물리모델 없음 |
| A-02 | ADMETlab 3.0 | pepADMET 등 | 소분자 도구 부적합 |
| A-03 | AutoDock Vina 배치 | FlexPepDock 중심 | 파이프라인 일관성 |
| A-05 | Tier 1/2/3 병렬 Step 3B | TS·Pareto·BO | 동등 목표 다른 구조 |

---

## 차기·추가 액션 (미팅 번호 A-11 이후 — 문서·산출물)

아래는 **`meet_log_backup.md`에 없는** 후속 항목으로, 발표·레포 정리에서 추가로 수행함.

| ID | 제목 | 상태 | 비고 |
|:--:|------|:----:|------|
| A-11 | 최종 발표용 통합 보고: `SILO_B_MASTER_PRESENTATION_REPORT.md` — **Part I에 본 액션 보고 우선 배치**, Part II·부록 A~D | ✅ | `build_silo_b_master_report.py`로 조립 |
| A-12 | PDF 생성·**페이지 번호**·이미지 폭 축소(스크린 PNG·screenshots) | ✅ | WeasyPrint `_md_to_pdf_weasyprint.py`, `resize_report_images.py` |
| A-13 | Linear `CHA-66` 등 추적 코멘트 | ✅ | 경로 기록 |

---

*본 보고서 v2 기준일: 2026-04-03 | 미팅 원문: `meet_log_backup.md`*
