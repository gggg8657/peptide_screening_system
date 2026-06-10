---
marp: true
theme: default
paginate: true
backgroundColor: #0f172a
color: #e2e8f0
style: |
  section { font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif; }
  h1 { color: #38bdf8; font-size: 1.6em; border-bottom: 2px solid #1e3a5f; padding-bottom: 6px; margin-bottom: 0.3em; }
  h2 { color: #7dd3fc; font-size: 1.3em; }
  h3 { color: #cbd5e1; font-size: 1.0em; }
  table { font-size: 0.82em; border-collapse: collapse; line-height: 1.3; }
  th { background: #1e3a5f; color: #e2e8f0; font-weight: 600; }
  td { color: #f1f5f9; background: #162032; }
  td, th { border: 1px solid #475569; padding: 5px 8px; }
  tr:nth-child(even) td { background: #1e293b; }
  section img { border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); max-height: 270px; object-fit: contain; }
  .caption { font-size: 0.60em; color: #94a3b8; text-align: center; margin-top: 2px; }
  .tag { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.7em; font-weight: 600; }
  .t-bio { background: #065f46; color: #6ee7b7; }
  .t-ai { background: #1e3a5f; color: #7dd3fc; }
  .t-ui { background: #713f12; color: #fde047; }
  .columns { display: flex; gap: 1.2em; align-items: flex-start; }
  .col { flex: 1; }
  blockquote { border-left: 3px solid #38bdf8; background: #1e293b; padding: 8px 14px; font-size: 0.80em; border-radius: 4px; }
  small { font-size: 0.6em; color: #94a3b8; }
  strong { color: #fbbf24; }
  code { font-size: 0.75em; background: #1e293b; padding: 1px 6px; border-radius: 3px; }
  a { color: #38bdf8; }
  section.compact { font-size: 24px; }
  section.compact h1 { font-size: 1.4em; }
  section.compact h3 { font-size: 0.9em; }
---

# SSTR2 AI Co-Scientist
## System Guide for Biotechnology Researchers

![bg right:35% w:400](screenshots/01_silo_b_full.png)

**PRST_N_FM** — Agentic AI 기반
SSTR2 결합 펩타이드 후보 스크리닝 시스템

한국원자력연구원 (KAERI)
응용인공지능연구실

<small>KNS 2026 Spring Conference | Jeju, 2026-05-07~08</small>

---

# 이 시스템이 하는 일

![w:1100](screenshots/03_experiment_control.png)
<div class="caption">실험 제어 패널 — 반복 횟수, 후보 수, LLM 모델, 검증 강도를 설정하고 Run 클릭</div>

> SST-14 서열에서 출발하여, **AI 에이전트가 자동으로**
> 돌연변이 생성 → 분자 도킹 → 품질 검증 → 비평 → 다음 반복 계획을
> 수행하는 **폐루프(closed-loop) 펩타이드 스크리닝 시스템**입니다.

---

# 5-Agent 구조 한눈에 보기

![w:480](screenshots/04_agent_and_candidates.png)

<div class="columns">
<div class="col">

| Agent | 하는 일 |
|-------|--------|
| **Planner** | LLM이 돌연변이 전략 수립 |
| **QC & Ranker** | 결합 에너지·충돌 기반 필터링 |
| **DiversityMgr** | 유사 후보 제거, 다양성 확보 |
| **Critic** | 실패 분석, 파라미터 조정 제안 |
| **Reporter** | 구조화 로그·시각화 생성 |

</div>
<div class="col">

좌측 **Agent Monitor**에서
각 에이전트의 실시간 상태를 확인:

- `Planner`: "positions 7-10 집중"
- `QC & Ranker`: "ddG gate 6/8 통과"
- 모든 판단 근거가 **로그로 기록**

</div>
</div>

---

# 후보 물질 순위 테이블

![w:1100](screenshots/05_candidate_table.png)
<div class="caption">Candidate Ranking — 50개 후보를 ΔG, Clash, 서열, PASS/FAIL 등 13개 기준으로 정렬</div>

<div class="columns">
<div class="col">

| 컬럼 | 의미 |
|------|------|
| **ddG** (kcal/mol) | 결합 에너지. **음수일수록 강한 결합** [1] |
| **Clash** (REU) | 원자 충돌. >10이면 FAIL [1] |
| **Result** | QC 게이트 종합 판정 |

</div>
<div class="col">

- 기존: 수동 엑셀 정리
- 본 시스템: **자동 순위 + 색상 코딩**
- PASS만 필터 → 실험 후보 즉시 도출

</div>
</div>

---

# 결합 에너지 분포 (ddG Distribution)

![w:1100](screenshots/06_ddg_distribution.png)
<div class="caption">ΔG 히스토그램 — Mean, Median, Std Dev, Pass Gate(%) 자동 계산</div>

<div class="columns">
<div class="col">

- X축: 결합 에너지 (kcal/mol), **왼쪽일수록 강함**
- 빨간 점선: QC 통과 기준 (≤ −5.0)
- **Pass Gate 100%** = 전 후보 기준 통과

</div>
<div class="col">

<span class="tag t-bio">약리학</span> FlexPepDock ΔG는 **후보 간 상대 비교** 기준 [1,2] — 동일 조건 하 **구조적으로 유리한 후보 우선순위**를 결정

</div>
</div>

---

# SAR 히트맵 — 구조-활성 관계

![w:900](screenshots/09_sar_heatmap.png)
<div class="caption">SAR Heatmap — 14개 위치 × 20개 아미노산 빈도 매트릭스</div>

- 금색 열: **FWKT 파마코포어** (7-10번 위치)
- 시안 셀: 해당 위치 돌연변이 빈도 / 노란 셀: 고빈도 (AI가 반복 선택)
- 점선 테두리: SST-14 원래 잔기

> **핵심**: 비핵심 위치(1,2,5,13)에서 다양한 변이가 관찰되면서 FWKT 모티프는 보존 → 시스템이 올바르게 작동하는 증거

---

# 시퀀스 로고 — 위치별 보존도

![w:900](screenshots/10_sequence_logo.png)
<div class="caption">Sequence Logo — 각 위치의 정보 엔트로피 (글자 높이 = 보존도)</div>

- **W8, K9**: 항상 높음 → SSTR2 결합 필수 잔기
- 회색 음영: FWKT 파마코포어 영역 (7-10번)
- 색상: 소수성(회) / 극성(녹) / +전하(청)

> Trp8-Lys9 모티프의 **절대적 보존**은 FlexPepDock 에너지 함수가 실험적으로 알려진 핫스팟을 정확히 포착하고 있음을 보여줍니다.

---

# 위치별 상위 변이체 (Position Enrichment)

![w:1100](screenshots/12_position_enrichment.png)
<div class="caption">14개 위치 × Top-3 변이체 — 빈도(%), 평균 ΔG, 색상으로 유리/불리 구분</div>

<div class="columns">
<div class="col">

- **녹색**: 유리한 ΔG / **적/주황**: 불리한 ΔG
- 노란 행 (7-10): FWKT 파마코포어
- Avg ddG: 해당 위치 전체 평균

</div>
<div class="col">

<span class="tag t-bio">실험 설계</span> 녹색 Top-1 변이체 = **우선 합성 대상**
- 반복 패턴 → **Thompson Sampling 학습** 결과 [3]
- wet-lab alanine scanning 대체 가능

</div>
</div>

---

# QC 게이트 + 수렴 그래프

![w:1100](screenshots/13_qc_convergence.png)
<div class="caption">좌: QC Gate Funnel (통과율) / 우: Convergence Graph (반복별 최적 ΔG 추이)</div>

<div class="columns">
<div class="col">

- **Rosetta ddG**: 64% 통과 (32/50)
- **Rosetta Clash**: 88% 통과 (28/32)
- 기준: `ddG ≤ −5.0` / `Clash ≤ 10`

</div>
<div class="col">

- 시안선: Best ΔG (반복마다 개선)
- **Converged** 배지 = 수렴 달성 [4]
- Last ΔddG: **0.20** → 조기 종료 가능

</div>
</div>

---

# 약리학 패널 — 서열 기반 예측

![w:1000](screenshots/08_pharmacology.png)
<div class="caption">Pharmacology Panel — 후보 서열 입력만으로 13가지 생화학 특성 즉시 산출</div>

<span class="tag t-bio">방사성의약품</span> 기존: 합성 후 in vitro 측정 → 본 시스템: **합성 전 in silico 예측**

> 특히 **pH별 전하 차이**(pH 7.4 vs 6.5)는 종양 미세환경에서의 SSTR2 선택적 결합을 예측하는 핵심 지표입니다.

---

# 약리학 13-메트릭 해설

<div class="columns">
<div class="col">

| # | 메트릭 | 의미 |
|:-:|--------|------|
| 1 | **GRAVY** [5] | 소수성 지수 — 막 투과성 |
| 2 | **Boman** [6] | 결합 잠재력 — GPCR 결합 |
| 3 | **불안정성 지수** [7] | <40 안정 — 혈중 안정성 |
| 4 | **Aliphatic Index** [8] | 지방족 — 열안정성 |
| 5 | **pI** [9] | 등전점 — 용해도·정제 |
| 6 | **ε₂₈₀** [12] | 흡광계수 — 정량 분석 |
| 7 | **N-end Rule** [22] | N-말단 반감기 예측 |

</div>
<div class="col">

| # | 메트릭 | 의미 |
|:-:|--------|------|
| 8 | **Hydrophobic Moment** [10] | 양친매성·막 결합 |
| 9 | **Wimley-White** [11] | 막 삽입 에너지 |
| 10 | **pH별 전하** [9] | **종양 선택성** |
| 11 | **프로테아제 절단** [14] | D-AA 치환 가이드 |
| 12 | **BLOSUM62** [13] | 보존적 치환 평가 |
| 13 | **금속 배위** [15] | **⁶⁸Ga 호환성** |

</div>
</div>

<small>13개 중 **6개**(pH별 전하, 금속 배위, 프로테아제, GRAVY, Boman, Wimley-White)가 **방사성의약품 개발**에 직접 활용 · 상세 해설 → Appendix A·B</small>

---

# Silo A: 3-Arm Virtual Screening 파이프라인

<div class="columns">
<div class="col">

### 3가지 병렬 접근법

세 가지 상이한 방법론을 **병렬 실행**하여
다양한 유형의 후보를 동시에 탐색합니다.

| Arm | 접근법 | 주요 도구 | 후보 |
|:---:|--------|---------|:---:|
| **1** | 소분자 생성+도킹 | MolMIM → DiffDock | 40 |
| **2** | 펩타이드 변이체 분석 | Ala scan + 강화 변이 | 13 |
| **3** | De Novo 바인더 설계 | RFdiff → MPNN → ESMFold | 16 |

> 모든 계산은 **NVIDIA NIM 클라우드 API** 기반
> 로컬 GPU 불필요

</div>
<div class="col">

![w:520](screenshots/16_nim_api_services.png)
<div class="caption">8개 NIM API 서비스 상태 모니터</div>

</div>
</div>

---

<!-- _class: compact -->

# Silo A: Arm별 상세

<div class="columns">
<div class="col">

### Arm 1 — 소분자

**MolMIM** 소분자 생성 (QED=0.94) → **DiffDock 블라인드 도킹** → 40후보 중 15개 도킹

### Arm 2 — 펩타이드 변이체

**Ala scan**: F6~F11→Ala (결합 기여도 측정)
**강화 변이체**: `A1S` `K4R` `F6Y` `K9R` `F11Y` → **13후보**

### Arm 3 — De Novo

**RFdiffusion**→**ProteinMPNN**→**ESMFold** (pLDDT=81.4) → **16후보**

</div>
<div class="col">

### 용어 정리

| 용어 | 의미 |
|------|------|
| **블라인드 도킹** | 결합 부위 미지정, 전체 표면 탐색 |
| **Ala scanning** | 잔기→Ala 치환으로 기여도 측정 |
| **강화 변이체** | 보존적 치환으로 결합력 개선 |
| **pLDDT** | 구조 예측 신뢰도 (0~100) |
| **QED** | 약물 유사성 정량 지표 (0~1) |

### 강화 변이체 5종

`A1S`(친수성↑) `K4R`(전하유지) `F6Y`(H-bond↑)
`K9R`(전하유지) `F11Y`(H-bond↑)

</div>
</div>

---

<!-- _class: compact -->

# Silo A: 7-Step 통합 파이프라인 — Arm별 병렬 흐름

| Step | Arm 1 (소분자) | Arm 2 (펩타이드 변이) | Arm 3 (De Novo) | 공통 도구 |
|:---:|------|------|------|------|
| 01 | — | — | 바인딩 포켓 추출 (35잔기) | AlphaFold3 |
| 02 | **MolMIM** 소분자 생성 (40개) | SST-14 Ala scan (6개) | **RFdiffusion** 백본 생성 | NIM API |
| 03 | QED 필터 → 상위 15개 선정 | 강화 변이체 생성 (5개) | **ProteinMPNN** 서열 역설계 | — |
| 04 | — | — | **ESMFold** 3D 예측 (pLDDT) | NIM API |
| 05 | **DiffDock** 블라인드 도킹 | **DiffDock** 펩타이드 도킹 | **DiffDock** 바인더 도킹 | NIM API |
| 06 | **PyRosetta** ddG 산출 | **PyRosetta** ddG 산출 | **PyRosetta** ddG 산출 | 로컬 |
| 07 | **FoldMason** 구조 정렬 | **FoldMason** 구조 정렬 | **FoldMason** 구조 정렬 | NIM API |

> Step 01(포켓 추출)은 **공유**, Step 02~04는 **Arm별 병렬**, Step 05~07은 **동일 QC 파이프라인** 통과
> 최종 **20후보** 가중합 통합 랭킹

---

# Silo A vs Silo B — 비교 & Unified Scoring

<div class="columns">
<div class="col">

| | Silo A (De Novo) | Silo B (SST-14 변이) |
|--|--------|--------|
| **접근** | 3-Arm 병렬 (69+후보) | 제약 기반 돌연변이 |
| **도구** | 8개 NIM 클라우드 API | PyRosetta 로컬 |
| **후보** | 완전 신규 서열 | SST-14 유사체 |
| **QC** | pLDDT ≥ 75 + ddG | ddG ≤ −5.0 + Clash ≤ 10 |
| **상태** | 설계 완료 | **운용 중** ✅ |

> **전략**: Silo B(보수적) + Silo A(혁신적)
> 양면 접근으로 화학 공간 극대화

</div>
<div class="col">

### Unified Scoring — `S = Σ wᵢ · norm(xᵢ)`

**Silo A** (MinMax [0,1]):

| 지표 | wᵢ | 지표 | wᵢ |
|------|:---:|------|:---:|
| Dock conf. | **0.35** | pLDDT | 0.15 |
| ΔEnergy | 0.25 | Diversity | 0.10 |
| QED | 0.15 | | |

**Silo B**: `0.45·dG + 0.20·stab + 0.15·drug + 0.10·div + 0.10·HIL − pen`
<small>Hard violation: −8.0/건, Soft: −0.4/규칙</small>

</div>
</div>

</div>
</div>

---

# 핵심 도구 요약

<div class="columns">
<div class="col">

### 구조 예측·도킹 <span class="tag t-bio">구조생물학</span>

| 도구 | 한 줄 설명 |
|------|-----------|
| **PyRosetta** | 펩타이드-GPCR 도킹 + ΔG [1] |
| **FlexPepDock** | 유연 백본 펩타이드 정제 [2] |
| **RFdiffusion** | 확산 모델 신규 백본 [16] |
| **ProteinMPNN** | 구조 → 서열 역설계 [17] |
| **ESMFold** | MSA 없는 빠른 구조 예측 [18] |
| **DiffDock** | 확산 기반 블라인드 도킹 [19] |

</div>
<div class="col">

### 분석·최적화 <span class="tag t-ai">AI/통계</span>

| 도구 | 한 줄 설명 |
|------|-----------|
| **FoldMason** | 3D 구조 다중 정렬 (lDDT) [20,21] |
| **Thompson Sampling** | 유망 위치 학습 (밴딧) [3] |
| **Mann-Whitney U** | 비모수 수렴 검정 [4] |
| **Qwen3:8b** | Planner·Critic LLM |
| **13-메트릭 계산기** | 서열 기반 약리학 예측 |
| **Mol\*** | 브라우저 3D 구조 뷰어 |

</div>
</div>

---

# 검증 결과 — 방향적 일관성

| ID | 설명 | Mean ΔG | vs WT | 판정 |
|------|------|---------|-------|------|
| LIT-01 | **WT SST-14** (내재 리간드) | **−43.78** | — | 기준 |
| LIT-02 | Octreotide (임상 약물) | −42.11 | +1.67 | **일치** |
| SAN-01 | **W8A** (Trp8 파괴) | −38.22 | +5.56 | **일치** |
| SAN-02 | **K9A** (Lys9 파괴) | −39.53 | +4.25 | **일치** |
| NOV-01 | AI 설계 (A1Y,G2S,S13N) | **−43.92** | −0.15 | WT급 |
| NOV-02 | AI 설계 (σ=3.53 최고 안정) | −41.47 | +2.31 | 재현 |

> - 핫스팟 파괴(W8A, K9A) → 확실히 낮은 순위 → **시스템이 올바르게 판별**
> - AI 설계 NOV-01이 WT 수준 달성 — CST-14 불일치는 proline 강직성 (알려진 한계)

---

# 데모 실행 방법

<div class="columns">
<div class="col">

### 3개 터미널, 1분 기동

```bash
# T1: LLM        | ollama serve
# T2: Backend    | conda activate bio-tools && uvicorn backend.main:app --port 8787
# T3: Frontend   | cd frontend && npm run dev
```

**브라우저**: `localhost:5173/silo-b`

</div>
<div class="col">

### 데모 시나리오

**1단계** — Iterations: 3, Candidates: 8, Run

**2단계** — Agent Monitor, Table 실시간 갱신

**3단계** — SAR Heatmap, Sequence Logo
→ FWKT 보존 여부 판단

**4단계** — 후보 선택 → Validate 클릭
→ 13-메트릭 + 통합 판정

</div>
</div>

---

# 정리

<div class="columns">
<div class="col">

### 이 시스템의 가치

기존의 **도구 간 단절된 워크플로우**를
5-Agent가 **자동 반복하는 폐루프**로 전환

- 반복당 ~240 후보 스크리닝
- 전 과정 **추적 가능한 구조화 로그**
- wet-lab 전 **in silico 우선순위 결정**
- 13가지 약리학 메트릭 자동 계산

</div>
<div class="col">

### 향후 계획

- Silo A (de novo) 파이프라인 구현
- Silo A+B **통합 오케스트레이션**
- wet-lab 결과 → Planner 피드백 루프
- QC 게이트: proline 백본 제약 반영
- ADMET 전임상 약리학 자동화

</div>
</div>

<br>

**Korea Atomic Energy Research Institute** | Applied Artificial Intelligence Section
<small>Contact: yjkim@kaeri.re.kr | hoseongseo@kaeri.re.kr</small>

---

<!-- _class: references -->

# References (1/2)

<small>

**[1]** Raveh B et al. "Sub-angstrom modeling of complexes between flexible peptides and globular proteins." *Proteins* 78:2029-2040 (2010)
**[2]** Raveh B et al. "Rosetta FlexPepDock ab-initio." *PLoS ONE* 6(4):e18934 (2011)
**[3]** Thompson WR. "On the likelihood that one unknown probability exceeds another." *Biometrika* 25(3-4):285-294 (1933)
**[4]** Mann HB, Whitney DR. "On a test of whether one of two random variables is stochastically larger." *Ann. Math. Statist.* 18(1):50-60 (1947)
**[5]** Kyte J, Doolittle RF. "A simple method for displaying the hydropathic character of a protein." *J. Mol. Biol.* 157:105-132 (1982)
**[6]** Boman HG. "Antibacterial peptides: basic facts and emerging concepts." *J. Intern. Med.* 254(3):197-215 (2003)
**[7]** Guruprasad K et al. "Correlation between stability of a protein and its dipeptide composition." *Protein Eng.* 4(2):155-161 (1990)
**[8]** Ikai A. "Thermostability and aliphatic index of globular proteins." *J. Biochem.* 88(6):1895-1898 (1980)
**[9]** Bjellqvist B et al. "Focusing positions of polypeptides in immobilized pH gradients." *Electrophoresis* 14:1023-1031 (1993)
**[10]** Eisenberg D et al. "The helical hydrophobic moment." *Nature* 299:371-374 (1982)

</small>

---

# References (2/2)

<small>

**[11]** Wimley WC, White SH. "Experimentally determined hydrophobicity scale for proteins at membrane interfaces." *Nat. Struct. Biol.* 3(10):842-848 (1996)
**[12]** Pace CN et al. "How to measure and predict the molar absorption coefficient of a protein." *Protein Sci.* 4:2411-2423 (1995)
**[13]** Henikoff S, Henikoff JG. "Amino acid substitution matrices from protein blocks." *PNAS* 89(22):10915-10919 (1992)
**[14]** Gasteiger E et al. "Protein identification and analysis tools on the ExPASy server." In *The Proteomics Protocols Handbook*, Humana Press (2005)
**[15]** Rulísek L, Vondrásek J. "Coordination geometries of selected transition metal ions." *J. Inorg. Biochem.* 71:115-127 (1998)
**[16]** Watson JL et al. "De novo design of protein structure and function with RFdiffusion." *Nature* 620:1089-1100 (2023)
**[17]** Dauparas J et al. "Robust deep learning–based protein sequence design using ProteinMPNN." *Science* 378:49-56 (2022)
**[18]** Lin Z et al. "Evolutionary-scale prediction of atomic-level protein structure with a language model." *Science* 379:1123-1130 (2023)
**[19]** Corso G et al. "DiffDock: Diffusion Steps, Twists, and Turns for Molecular Docking." *ICLR* (2023)
**[20]** Gilchrist CLM et al. "Multiple protein structure alignment at scale with FoldMason." *Science* (2024)
**[21]** Mariani V et al. "lDDT: a local superposition-free score." *Bioinformatics* 29(21):2722-2728 (2013)
**[22]** Varshavsky A. "The N-end rule." *PNAS* 93:12142-12149 (1996)

</small>

---

# Appendix A-1: GRAVY [5]

### Kyte-Doolittle 소수성 지수

`GRAVY = (1/N) × Σ H(i)`, H(i) = 아미노산별 소수성 값
<small>**[5] Table II, p.111** — *"A simple method for displaying the hydropathic character of a protein"*</small>

| AA | H | AA | H | AA | H | AA | H |
|----|----|----|----|----|----|----|----|
| I | **4.5** | A | 1.8 | P | -1.6 | N | -3.5 |
| V | **4.2** | M | 1.9 | S | -0.8 | D | -3.5 |
| L | **3.8** | G | -0.4 | W | -0.9 | Q | -3.5 |
| F | **2.8** | T | -0.7 | Y | -1.3 | K | -3.9 |
| C | 2.5 | H | -3.2 | E | -3.5 | R | **-4.5** |

> GRAVY > 0: 소수성 (막 투과 가능) / < 0: 친수성 (수용성)

---
<!-- _class: compact -->

# Appendix A-2: Boman & Instability & AI

### Boman Index [6] — 단백질 결합 잠재력

`BI = −(1/N) × Σ ΔG_transfer(i)` (Radzicka-Wolfenden, kcal/mol)
<small>**[6] p.204, "A simple index"** — *"hormones and neuropeptides have high indices"*</small>
BI **> 2.48** → 호르몬/수용체 리간드형

### Instability Index [7] — Guruprasad et al.

`II = (10/L) × Σ DIWV(x_i, x_{i+1})`, DIWV = 20×20 가중치
<small>**[7] Eq.1, p.156; Table I, p.157** — *"a protein whose index is less than 40 is predicted as stable"*</small>
**II < 40** → 안정 (in vivo) / ≥ 40 → 불안정

### Aliphatic Index [8] — 열안정성

`AI = X(A) + 2.9·X(V) + 3.9·[X(I)+X(L)]` <small>**[8] Eq.1, p.1896** — *"positively correlated with thermostability"*</small>

---
<!-- _class: compact -->

# Appendix A-3: ε₂₈₀ & pI

### Extinction Coefficient [12] — ε₂₈₀

`ε₂₈₀ = n_Trp × 5500 + n_Tyr × 1490 + n_SS × 125` (M⁻¹cm⁻¹)
<small>**[12] Eq.1, p.2413** — *"ε(280) = nTrp × 5500 + nTyr × 1490 + nCystine × 125"*</small>

### Isoelectric Point (pI) [9] — Bjellqvist et al.

Bisection 알고리즘 (pH 0-14), Henderson-Hasselbalch 기반
<small>**[9] Table 1, p.1025** — *"The pK values for amino acid residues in polypeptides"*</small>
Net charge = 0이 되는 pH → pI

### Hydrophobic Moment [10] — Eisenberg

`μH = (1/N) √[ (Σ H_i·sin(iδ))² + (Σ H_i·cos(iδ))² ]`
<small>**[10] Eq.1, Fig.1, p.372** — *"a measure of the amphiphilicity of a helix"*</small>
δ = 100° (α-helix), window = 11, μH **> 0.35** → 강한 양친매성 (막 결합/AMP)

---
<!-- _class: compact -->

# Appendix A-4: Wimley-White & pH 전하

### Wimley-White [11] — 막 삽입 자유 에너지

`ΔG = Σ ΔG_WW(i)` (water → POPC interface, kcal/mol)
<small>**[11] Table 1, p.843** — *"Experimentally determined free energies of transfer from water to POPC interfaces"*</small>
ΔG < −5.0: 강한 막 삽입 / 0~−5.0: 중간 / > 0: 수용성

### pH별 전하 — Henderson-Hasselbalch

`Q(pH) = Σ[n/(1+10^(pH−pKa))] − Σ[n/(1+10^(pKa−pH))]`
<small>pKa 값: **[9] Table 1, p.1025** (Bjellqvist)</small>

| 잔기 | pKa | 역할 | 잔기 | pKa | 역할 |
|------|------|------|------|------|------|
| N-term | 9.69 | + | **His** | **6.00** | **pH 스위치** |
| C-term | 2.34 | − | Lys | 10.53 | + |
| Asp | 3.65 | − | Arg | 12.48 | + |

---

# Appendix B-1: N-end Rule & BLOSUM62

### N-end Rule [22] — 반감기 예측

<small>**[22] Table 1, p.12143** — *"The N-end rule relates the in vivo half-life of a protein to the identity of its N-terminal residue"*</small>

| N-말단 잔기 | 반감기 | 분류 | N-말단 잔기 | 반감기 | 분류 |
|-----------|------|------|-----------|------|------|
| M,S,A,T,V,G | >30h | 안정 | F, D | 1.1h | 매우 불안정 |
| Y, W | 2.8h | 불안정 | R | 1.0h | 매우 불안정 |

### BLOSUM62 보존 점수 [13]

<small>**[13] Fig.3, p.10917** — *"Blocks substitution matrix… sequences clustered at 62% identity"*</small>
≥ +2: 보존적 치환 / 0~+1: 반보존적 / < 0: 비보존적
비교 기준: WT SST-14 `AGCKNFFWKTFTSC`

---

# Appendix B-2: 프로테아제 & 금속 배위

### 프로테아제 절단 부위 [14]

<small>**[14] Section "PeptideCutter", pp.571-607** — *"predicts potential cleavage sites cleaved by proteases or chemicals"*</small>

| 효소 | 절단 위치 | 저해 |
|------|--------|------|
| **Trypsin** | K, R 뒤 | P→P1' 차단 |
| **Chymotrypsin** | F,W,Y,L,M 뒤 | P→P1' 차단 |
| **Pepsin** | F,Y,L 앞 | — |

절단 부위 수 ↑ → 혈중 반감기 ↓ → **D-AA 치환** 또는 **cyclization**

### 금속 배위 [15] — ⁶⁸Ga 호환성 <small>**[15] Table 1, p.117** — *"coordination geometries of metal ions in metalloproteins"*</small>

His (imidazole N, 강: Zn²⁺/Cu²⁺/**Ga³⁺**) · Cys (thiolate S, 강: Cu⁺/Zn²⁺) · Asp/Glu (carboxylate O, 중: Ca²⁺)

---

<!-- _class: compact -->

# Appendix C-1: Unified Scoring — Silo A & B 공식

<div class="columns">
<div class="col">

### Silo B (PyRosetta Only)

`S_B = 0.70·ddG + 0.20·total + 0.10·clash`

| 지표 | 가중치 | 방향 | 정규화 |
|------|:------:|:----:|--------|
| **ddG** | 0.70 | 낮을수록 ↑ | 1 − MinMax |
| **total_score** | 0.20 | 낮을수록 ↑ | 1 − MinMax |
| **clash** | 0.10 | 낮을수록 ↑ | 1 − MinMax |

**Hard violation**: −8.0/건 (ddG>0, clash>20)
**Soft violation**: −0.4/규칙 (ddG>−3, clash>10)

> **ddG 지배적** (70%) — Rosetta FlexPepDock 결합 에너지가 순위 결정의 핵심

</div>
<div class="col">

### Silo A (NIM 통합)

`S_A = 0.15·pLDDT + 0.25·dock + 0.25·ddG + 0.15·lDDT + 0.20·sel`

| 지표 | 가중치 | 방향 | 의미 |
|------|:------:|:----:|------|
| **pLDDT** | 0.15 | 높을수록 ↑ | 구조 신뢰도 |
| **dock_score** | 0.25 | 낮을수록 ↑ | 도킹 품질 |
| **ddG** | 0.25 | 낮을수록 ↑ | 결합 에너지 |
| **lDDT** | 0.15 | 높을수록 ↑ | 구조 보존 |
| **selectivity** | 0.20 | 낮을수록 ↑ | SSTR2 특이성 |

모든 지표 **MinMax [0,1]** 정규화 후 가중합
<small>"낮을수록 좋은" 지표는 `1 − norm(x)` 반전 적용</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix C-2: QC Gate — 4단계 순차 필터

<div class="columns">
<div class="col">

### Gate 흐름 (AND 조건, 순차 적용)

| Gate | 대상 | 조건 | 기본 임계값 |
|:----:|------|------|-----------|
| **1** | ESMFold pLDDT | mean ≥ T₁ **AND** interface ≥ T₂ | T₁=50, T₂=45 |
| **2** | Docking Score | 상위 P% 이내 | P=20% |
| **3** | Rosetta | ddG ≤ T₃ **AND** clash ≤ T₄ **AND** violations=0 | T₃=−5.0, T₄=10 |
| **4** | Selectivity | margin ≤ T₅ **AND** offtarget ≤ T₆ | T₅=−10, T₆=−15 |

### 판정 결과

- **PASS**: Gate 1~3 전부 통과 (Gate 4는 선택적)
- **FAIL**: 실패 사유 기록 (`plddt_mean`, `clash`, `ddg` 등)
- **pass_rate**: 반복별 통과율 추적 → QC Funnel 시각화

</div>
<div class="col">

### Gate 활성화 설정

```yaml
# gate_thresholds.yaml
gates_enabled:
  esmfold_plddt: true    # Silo A only
  docking_score: true    # Silo A only
  rosetta_ddg: true      # 양 Silo 공통
  selectivity: false     # 후기 단계 활성화
```

### Silo B 전용 (PyRosetta 모드)

Gate 1·2 **비활성화** (ESMFold/DiffDock 미사용)
Gate 3만 활성: `ddG ≤ −5.0` AND `clash ≤ 10`

<small>추가 Gate: 이황화 SG-SG ≤ 2.5Å · 안정성 반감기 ≥ 50h</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix C-3: Thompson Sampling — 위치 최적화 밴딧

<div class="columns">
<div class="col">

### Beta 분포 다중 팔 밴딧

각 가변 위치에 Beta(α, β) 사후분포를 유지하여 **탐색-활용 균형**을 자동 조절합니다.

**기준 서열**: `AGCKNFFWKTFTSC` (SST-14)
**가변 위치** (1-indexed): **1, 2, 4, 5, 6, 11, 12, 13** (8개)
<small>불변 위치: C3, F7, W8, K9, T10, C14 (파마코포어+이황화)</small>

### 사전분포 & 갱신 규칙

**Prior**: α=1, β=1 (Uniform)

| 조건 | 갱신 |
|------|------|
| ddG < baseline (WT 평균) | **α += 1** (성공) |
| ddG ≥ baseline | **β += 1** (실패) |

baseline = WT 관찰 평균 ddG, 없으면 전체 중앙값

</div>
<div class="col">

### 샘플링 & 위치 선정

매 반복마다:
1. 각 위치 i에서 `θᵢ ~ Beta(αᵢ, βᵢ)` 샘플링
2. θ 값 내림차순 정렬
3. **상위 N개 위치** 반환 → Planner에게 전달

### 기대값 & 수렴

`E[θᵢ] = αᵢ / (αᵢ + βᵢ)`

- E[θ] → 1: 해당 위치 **반복 개선** / → 0: **불리** → 자동 회피
- 분산 감소: 관찰↑ → 불확실성↓

<small>유효 범위: ddG ∈ [−60.0, 200.0], 범위 밖 이상치는 갱신 제외</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix C-4: Mann-Whitney U 수렴 검정

<div class="columns">
<div class="col">

### 수렴 판정 조건 (두 가지 동시 충족)

**조건 1**: Mann-Whitney U 검정 p > 0.05
→ 이전 윈도우와 현재 윈도우 사이 **유의차 없음**

**조건 2**: 변동계수 CV < 0.15
→ 현재 윈도우의 top-k ddG 값이 **안정적**

`CV = σ / |μ|` (현재 윈도우 top-k ddG)

### 파라미터

| 항목 | 기본값 | 의미 |
|------|:------:|------|
| window_size | **3** | 비교 윈도우 크기 (반복 수) |
| α (유의수준) | **0.05** | U 검정 임계 |
| CV 임계 | **0.15** | 변동계수 상한 |
| 최소 반복 | **6** | 2×window 이후 검정 시작 |

</div>
<div class="col">

### Mann-Whitney U 통계량

**U = min(U₁, U₂)**

`U₁ = n₁n₂ + n₁(n₁+1)/2 − R₁`

R₁ = 이전 윈도우 순위합

### 정규 근사 (n ≥ 8)

`z = (U − μ_U) / σ_U`

μ_U = n₁n₂/2
σ_U = √[n₁n₂(n₁+n₂+1)/12]

연속성 보정: `z = (|U − μ_U| − 0.5) / σ_U`

<small>**흐름**: 6+반복 수집 → 이전3 vs 현재3 분할 → p>0.05 + CV<0.15 → **Converged**</small>

</div>
</div>

---

# Appendix D-1: 최근 논문 활용 — AMP 설계

<small>13-메트릭이 2020-2026년 최근 논문에서 어떻게 활용되고 있는지</small>

| 메트릭 | 최근 논문 | 활용 방식 |
|--------|---------|---------|
| **GRAVY** | Li C et al. *Nat Commun* 15:7390, 2024 | deepAMP 프레임워크에서 AMP 막 투과성 평가 |
| **Boman** | Bobde SS et al. *Front Microbiol* 12:715246, 2021 | PHNX 시리즈 AMP의 단백질 결합 잠재력 정량 |
| **μH** | Sugihara T et al. *Sci Rep* 12:4959, 2022 | CPP의 양친매성과 세포 투과 효율 상관 검증 |
| **WW** | Falanga A et al. *J Pept Sci* 30:e3558, 2024 | 약물 전달 펩타이드의 막 계면 분배 에너지 평가 |
| **BLOSUM62** | Szymczak P et al. *Nat Commun* 14:1453, 2023 | HydrAMP 생성 AMP의 신규성 평가 |

> *"HydrAMP is the first model directly optimized for diverse AMP generation tasks"* — Szymczak et al. 2023 [23]

---

# Appendix D-2: 최근 논문 활용 — 백신·방사성의약품

| 메트릭 | 최근 논문 | 활용 방식 |
|--------|---------|---------|
| **II** | Waqas M et al. *Sci Rep* 14:10297, 2024 | SARS-CoV-2 백신 구조체 II<40 안정성 검증 |
| **AI** | Khan S et al. *Front Microbiol* 14:1251716, 2023 | 다중 에피토프 백신 열안정성 예측 |
| **ε₂₈₀** | Waqas M et al. *Sci Rep* 14:10297, 2024 | 백신 구조체 UV 정량 조건 설정 |
| **Protease** | Tan X et al. *Brief Bioinform* 25:bbae350, 2024 | 효소 절단 기술자 → 반감기 예측 모델 |
| **N-end** | Seo J et al. *Biomedicines* 10:2100, 2022 | PROTAC 분자의 표적 단백질 분해 설계 |
| **pH 전하** | Deri MA et al. *Molecules* 28:203, 2023 | ⁶⁸Ga-DOTA 최적 표지 pH 설정 |
| **금속 배위** | Sawicka D et al. *Molecules* 27:3062, 2022 | 방사성의약품 킬레이터 설계 최적화 |

> *"pH-dependent speciation directly affects labeling efficiency and in vivo stability"* — Deri et al. 2023

---

# Appendix D-3: 논문 × 메트릭 크로스-레퍼런스

<small>최근 주요 논문들이 13개 메트릭 중 어떤 것을 사용했는지 한눈에 보기</small>

| 논문 (연도) | 분야 | GR | BI | II | AI | pI | μH | WW | ε | BL | Pr | Mt | Ne | pH |
|-----------|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:-:|:--:|:--:|:--:|:--:|:--:|
| Li *Nat Commun* '24 | AMP | ● | ● | | | | ● | | | ● | | | | |
| Szymczak *Nat Commun* '23 | AMP | ● | | | | | ● | | | ● | | | | |
| Bobde *Front Micro* '21 | AMP | ● | ● | ● | | | ● | | | | | | | |
| Waqas *Sci Rep* '24 | 백신 | ● | | ● | ● | ● | | | ● | | | | | |
| Khan *Front Micro* '23 | 백신 | | | ● | ● | ● | | | | | | | | |
| Tan *Brief Bioinfo* '24 | 반감기 | | | | | | | | | | ● | | ● | |
| Deri *Molecules* '23 | ⁶⁸Ga | | | | | | | | | | | ● | | ● |
| Sawicka *Molecules* '22 | 방사성 | | | | | | | | | | | ● | | ● |

<small>GR=GRAVY, BI=Boman, II=불안정성, AI=지방족, μH=소수성모멘트, WW=Wimley-White, ε=흡광계수, BL=BLOSUM62, Pr=프로테아제, Mt=금속배위, Ne=N-end, pH=pH전하</small>

---

<!-- _class: compact -->

# Appendix E-1: AI 모델 — MolMIM & DiffDock

<div class="columns">
<div class="col">

### MolMIM (NVIDIA)

**유형**: 소분자 생성 모델 (Generative)
**방법**: Mutual Information Machine — 잠재 공간(latent space)에서 분자를 생성하고 QED/logP 등 약물성 지표를 최적화
**입력**: 표적 단백질 포켓 구조 또는 시드 분자
**출력**: SMILES 형식의 소분자 후보 + QED 점수

| 항목 | 내용 |
|------|------|
| 학습 데이터 | ZINC, ChEMBL 소분자 DB |
| 핵심 지표 | **QED** (0~1), 약물 유사성 정량화 |
| 본 시스템 활용 | Arm 1: 40개 소분자 생성 (QED=0.94) |

<small>NVIDIA NIM API Documentation, 2024</small>

</div>
<div class="col">

### DiffDock [19]

**유형**: 분자 도킹 모델 (Diffusion-based)
**방법**: 확산 모델로 리간드의 회전·이동·비틀림을 동시 샘플링하여 결합 포즈 예측
**특징**: **블라인드 도킹** — 결합 부위 사전 지정 불필요

| 항목 | 내용 |
|------|------|
| 기반 | Score-based diffusion (SE(3)) |
| 입력 | 리간드 + 수용체 전체 구조 |
| 출력 | 랭킹된 결합 포즈 + confidence score |
| 장점 | 전체 표면 탐색, 기존 도킹 대비 높은 성공률 |
| 본 시스템 | Arm 1/2/3 공통 도킹 단계 (Step 05) |

<small>Corso G et al. *ICLR* (2023)</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix E-2: AI 모델 — RFdiffusion, ProteinMPNN, ESMFold

<div class="columns">
<div class="col">

### RFdiffusion [16]

**유형**: 단백질 구조 생성 (Diffusion)
**방법**: Denoising diffusion → **de novo 펩타이드 백본** 설계
**입출력**: 포켓 구조 + contigs → 3D 백본 좌표 (Cα trace)
<small>RoseTTAFold 기반 · *Nature* 620:1089 (2023)</small>

### ProteinMPNN [17]

**유형**: 서열 설계 (Inverse Folding)
**방법**: 3D 백본 → **최적 아미노산 서열** 할당
**입출력**: 백본 구조 → 서열 + per-residue 확률
<small>*Science* 378:49 (2022)</small>

</div>
<div class="col">

### ESMFold [18]

**유형**: 구조 예측 (Language Model)
**방법**: ESM-2 (15B) 서열→3D 구조, MSA **불필요**

| 항목 | 내용 |
|------|------|
| 입력 | 아미노산 서열 |
| 출력 | 3D 구조 + **pLDDT** 신뢰도 |
| 속도 | AlphaFold2 대비 ~60배 빠름 |
| 본 시스템 | Arm 3 Step 04 (pLDDT=81.4) |

<small>*Science* 379:1123 (2023)</small>

**Arm 3 흐름**: RFdiffusion(백본) → ProteinMPNN(서열) → ESMFold(검증) → DiffDock(도킹)

</div>
</div>

---

<!-- _class: compact -->

# Appendix F-1: AI 모델 — 최근 논문 활용 사례

### 분자 생성 & 도킹 (MolMIM · DiffDock)

| 저자 (연도) | 저널 | 모델 | 주요 결과 |
|---|---|---|---|
| Reidenbach et al. '23 | ICLR (MLDD) | MolMIM | 잠재 공간 보간 → 약물 유사 분자 최적화 |
| Deloitte/NVIDIA '24 | Industry | MolMIM+DiffDock | DGX Cloud 학습 4주→8일, 대규모 추론 |
| Innoplexus '24 | Industry | MolMIM+DiffDock | 580만 분자 5-8h 스크리닝, 90% 정확도 |
| Corso et al. '23 | ICLR | DiffDock | Top-1 38.2% (2Å), 기존 대비 ~2배 |

### 단백질 설계 (RFdiffusion · ProteinMPNN · ESMFold)

| 저자 (연도) | 저널 | 모델 | 주요 결과 |
|---|---|---|---|
| Watson et al. '23 | *Nature* | RFdiff+MPNN | de novo 단량체·결합체·올리고머·효소 실험 검증 |
| Dauparas et al. '22 | *Science* | ProteinMPNN | 서열 복구율 52.4% (Rosetta 32.9%) |
| Lin et al. '23 | *Science* | ESMFold | 6억+ 메타게놈 구조, AF2 대비 60배 빠름 |
| Bennett et al. '25 | *Nature* | RFdiff+MPNN | VHH·scFv·전장 항체 에피토프 특이적 설계 |

<small>+ Pacesa '25 *Nature* BindCraft 원샷 결합체 10-100% 성공률 · Hossack '26 *Nat Commun* β-시트 결합체 KIT·PDGFR-α</small>

---

<!-- _class: compact -->

# Appendix F-2: MolMIM — 소분자 생성 모델

<div class="columns">
<div class="col">

### 모델 개요

NVIDIA의 **Mutual Information Machine** 기반 생성 모델.
시드 분자의 **잠재 공간**(latent space)을 탐색하여 약물성이 높은 신규 분자를 자동 생성한다.

**작동 원리**
1. SMILES 문자열을 Perceiver 인코더로 고정 크기 잠재 벡터에 매핑
2. CMA-ES 최적화로 QED·logP 등 원하는 속성 방향으로 탐색
3. 디코더가 새로운 SMILES 문자열 출력

**학습 데이터**: ZINC15 **17억 분자**
(MW≤500, LogP≤5, QED≥0.5 약물 유사 화합물)

</div>
<div class="col">

### 성능 벤치마크

| 지표 | 수치 | 의미 |
|---|---|---|
| 유효성 | **~100%** | 생성 분자 전부 화학적으로 유효 |
| QED 최적화 | SOTA **+5%p** | 약물 유사성 점수 업계 최고 |
| 유효 신규성 | 경쟁 모델 **+12%p** | 새롭고 유효한 분자 비율 |
| 다양성 | 상위권 | 중복 없이 다양한 구조 생성 |

### 기존 방법 대비 차별점

| 기존 (VAE 기반) | MolMIM |
|---|---|
| 유효성↑ 이면 신규성↓ | **둘 다 동시 달성** |
| 잠재 공간 불안정 | MI 학습으로 **안정적 잠재 공간** |
| 속성 최적화 어려움 | CMA-ES로 **직접 최적화** |

</div>
</div>

**핵심**: "화학적으로 유효 + 기존에 없던 + 약물처럼 보이는" 세 조건을 동시 충족 · 본 시스템 Silo A Arm 1에서 **40종 소분자 후보** 생성 (평균 QED=**0.94**)

---

<!-- _class: compact -->

# Appendix F-3: DiffDock — 블라인드 분자 도킹

<div class="columns">
<div class="col">

### 모델 개요

확산 모델(Score-based diffusion on SE(3))로 리간드의 **회전·이동·비틀림**을 동시 샘플링. 결합 부위를 **사전 지정하지 않고도**(블라인드) 정확한 결합 포즈를 예측한다.

**작동 원리**
1. 단백질 전체 표면에 리간드를 무작위 배치
2. 확산 과정을 역으로 진행하며 최적 포즈로 수렴
3. confidence score로 예측 신뢰도 출력

### 성능 벤치마크 (PDBBind)

| 지표 | DiffDock | 기존 최선 | 향상 |
|---|---|---|---|
| Top-1 (2Å 이내) | **38.2%** | 20.4% | **~2배** |
| Top-5 (2Å 이내) | **44.7%** | — | 절반이 정답 |
| 고신뢰 정확도 | **83%** | — | 상위 1/3 |

</div>
<div class="col">

### 기존 방법 대비 차별점

| 기존 도킹 (Vina, GLIDE) | DiffDock |
|---|---|
| 결합 부위를 **미리 알아야** 함 | **블라인드** — 부위 지정 불필요 |
| 물리 기반 scoring → 느림 | 학습 기반 → **3-12배 빠름** |
| 정확도 ~20% (블라인드) | **38%** (블라인드) |
| 신뢰도 지표 없음 | confidence score 제공 |

### 지표가 의미하는 것

- **Top-1 38.2%**: 1순위 예측이 실제 포즈와 2Å 이내. 기존 ~20%에서 **2배 향상**
- **고신뢰 83%**: 상위 1/3 선별 시 83% → **자동 필터링으로 고품질 결과**
- **속도**: GPU로 수백만 분자 시간 내 스크리닝 (3-12×)

<small>본 시스템: Silo A 전 Arm Step 05 · NIM API 배치</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix F-4: RFdiffusion — de novo 단백질 백본 설계

<div class="columns">
<div class="col">

### 모델 개요

노이즈 제거 확산(denoising diffusion)으로 표적에 결합하는 **단백질 백본을 처음부터 새로** 설계. RoseTTAFold 아키텍처 기반.

**작동 원리**
1. 무작위 노이즈에서 시작 (3D 좌표)
2. 단계적으로 노이즈를 제거하며 구조 정제
3. 표적 포켓 정보를 조건으로 주어 결합체 생성
4. contigs로 길이·위치 제약 제어

### 성능 벤치마크

| 지표 | 수치 | 해석 |
|---|---|---|
| 실험 성공률 | **19%** | 설계 5개 중 1개 실제 결합 |
| vs Rosetta | **~100배** | 기존 0.1-0.2% → 19% |
| 적용 범위 | 50-400 AA | 대부분 단일 도메인 커버 |

</div>
<div class="col">

### 지표가 의미하는 것

**"5개 설계하면 1개가 실험에서 작동한다"**

이전 Rosetta 기반 방법은 **수천 개를 설계해야 1개가 성공**했다. RFdiffusion은 이를 100배 개선하여, 소수의 설계만으로도 실험적 검증이 가능해졌다.

**실험 비용 관점**: 단백질 1개의 실험 검증에 수십만 원이 드므로, 성공률 100배 향상은 **연구비 100분의 1 절감**과 동일.

### 적용 범위

- 단량체 (monomer) 설계
- 결합체 (binder) 설계 — **본 시스템 핵심**
- 대칭 올리고머 · 효소 스캐폴딩 · 금속 결합 단백질
- **본 시스템**: Arm 3 Step 02 — SSTR2 포켓 결합 백본 생성

</div>
</div>

---

<!-- _class: compact -->

# Appendix F-5: ProteinMPNN — 서열 설계 (역접힘)

<div class="columns">
<div class="col">

### 모델 개요

3D 백본 구조가 주어지면, 그 구조로 접힐 수 있는 **최적 아미노산 서열**을 할당하는 역접힘(inverse folding) 모델.

**작동 원리**
1. 백본의 3D 좌표를 그래프로 인코딩
2. Message-passing 신경망이 각 위치의 아미노산 확률 예측
3. 자기회귀적으로 서열 생성 (per-residue 확률 출력)

### 성능 벤치마크

| 지표 | MPNN | Rosetta | 향상 |
|---|---|---|---|
| 서열 복구율 | **52.4%** | 32.9% | +19.5pp |
| 용해도 | **88%** | 40% | **2.2배** |
| 단백질 수율 | **247 mg/L** | 9 mg/L | **27배** |

</div>
<div class="col">

### 지표가 의미하는 것

- **서열 복구율 52.4%**: 자연 서열의 **절반 이상을 정확히 복원**. 나머지 48%도 대부분 보존적 치환(예: Leu→Ile)이라 구조와 기능이 유지됨

- **용해도 88%**: 설계 단백질 **10개 중 9개**가 대장균에서 발현·용해. Rosetta는 10개 중 4개만 성공 → 실험 실패율 대폭 감소

- **수율 27배**: 같은 발현 조건에서 **27배 많은 단백질** 확보. 후속 실험(결합 측정, 구조 분석)에 충분한 양을 쉽게 확보

- **속도 1000×**: 백본 1개당 **~1초**. Rosetta 수분~수시간 대비

<small>본 시스템: Arm 3 Step 03 — RFdiffusion 백본에 서열 할당</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix F-6: ESMFold — 구조 예측

<div class="columns">
<div class="col">

### 모델 개요

**15B 파라미터** 단백질 언어 모델(ESM-2). 다중 서열 정렬(MSA) 없이 **서열만으로** 3D 구조를 예측한다.

**작동 원리**
1. 아미노산 서열을 ESM-2 언어 모델에 입력
2. 트랜스포머가 잔기 간 관계를 학습
3. Structure module이 3D 좌표 + pLDDT 신뢰도 출력

### 성능 벤치마크

| 지표 | ESMFold | AlphaFold2 | 해석 |
|---|---|---|---|
| TM (no MSA) | **0.68** | 0.37 | **1.8배** |
| 고신뢰 RMSD | **1.33Å** | 유사 | 실험급 정확도 |
| 속도 (<200 AA) | **>60배** | 기준 | 초 단위 예측 |
| pLDDT 중앙값 | 87.4 | 92.7 | 약간 낮지만 실용적 |

</div>
<div class="col">

### 지표가 의미하는 것

- **TM-score 0.68 vs 0.37**: MSA 없이 단일 서열만 줄 때, AlphaFold2는 0.37로 급락하지만 ESMFold은 **0.68 유지** → 상동 서열이 없는 **설계 단백질에 최적**

- **>60배 속도**: AlphaFold2는 MSA 검색에 ~30분 필요. ESMFold은 MSA 불필요 → **초 단위 예측**. 대량 후보 검증에 필수적

- **pLDDT 87.4**: 신뢰도(0-100). **70+면 실용적**, 90+면 매우 높음. 6억+ 메타게놈 구조 예측 실적

**본 시스템**: Silo A Arm 3 Step 04 — ProteinMPNN 서열 → ESMFold 구조 예측 (pLDDT=**81.4**)

</div>
</div>

---

<!-- _class: compact -->

# Appendix F-7: 5개 AI 모델 — 시스템 통합 & 성능 비교 요약

<div class="columns">
<div class="col">

### 모델별 파이프라인 위치

| 모델 | Silo·Arm | Step | 핵심 기여 |
|---|---|---|---|
| MolMIM | A · Arm 1 | 01 | 소분자 40종 생성 (QED=0.94) |
| DiffDock | A · 전 Arm | 05 | 블라인드 도킹 |
| RFdiffusion | A · Arm 3 | 02 | de novo 백본 설계 |
| ProteinMPNN | A · Arm 3 | 03 | 백본→서열 변환 |
| ESMFold | A · Arm 3 | 04 | 구조 검증 (pLDDT) |

### Arm 3 파이프라인 흐름

**RFdiffusion** (백본 생성)
→ **ProteinMPNN** (서열 할당)
→ **ESMFold** (구조 검증, pLDDT 필터)
→ **DiffDock** (블라인드 도킹)

"**서열만으로 de novo 펩타이드 설계→도킹 완료**" 완전 자동화

</div>
<div class="col">

### 모델 간 성능 비교

| 모델 | 핵심 지표 | 향상 |
|---|---|---|
| MolMIM | QED +5%p | 동시 달성 |
| DiffDock | Top-1 **38.2%** | ×2 |
| RFdiffusion | 성공률 **19%** | ×100 |
| ProteinMPNN | 복구 **52.4%** | +19pp |
| ESMFold | TM **0.68** | ×1.8 |

### 통합 시스템의 의미

기존: 각 단계를 **수동 연결**, 전문가가 중간 결과를 검토하며 다음 단계로 넘김

본 시스템: 5개 모델을 **NIM API**로 통합
- 구조 예측→생성→도킹→검증 **자동화**
- 전문가 개입 없이 **수시간 내** 후보 도출

</div>
</div>

---

<!-- _class: compact -->

# Appendix G-1: Unified Validation 17 기준 — 전체 구조

<div class="columns">
<div class="col">

### 약리학 기준 (12개)

| # | 기준 | Gate 조건 |
|:-:|------|----------|
| 1 | GRAVY | −2.0 ~ +2.0 |
| 2 | Boman Index | 0 ~ 4.0 kcal/mol |
| 3 | 불안정성 지수 | < 40 |
| 4 | Aliphatic Index | 30 ~ 200 |
| 5 | pI | 3.0 ~ 11.0 |
| 6 | ε₂₈₀ | > 0 M⁻¹cm⁻¹ |
| 7 | N-end Rule | 안정 잔기 (M,S,A,T,V,G) |
| 8 | Hydrophobic Moment | 0 ~ 3.0 |
| 9 | Wimley-White | −20 ~ +5 kcal/mol |
| 10 | pH별 전하 차이 | 0 ~ 5.0 |
| 11 | 프로테아제 절단 | 0 ~ 15 sites |
| 12 | BLOSUM62 보존 | −4 ~ +4 |

</div>
<div class="col">

### 방사성의약품 기준 (2개)

| # | 기준 | Gate 조건 |
|:-:|------|----------|
| 13 | **금속 배위** | His+Cys ≥ 2 (⁶⁸Ga 호환) |
| 14 | **신장독성** | Risk score < threshold |

### 통계적 기준 (3개)

| # | 기준 | Gate 조건 |
|:-:|------|----------|
| 15 | **Rank Stability** | 상위 후보 순위 변동 < σ |
| 16 | **Score Consistency** | Run 간 점수 CV < 15% |
| 17 | **No Dominance** | 단일 후보 점유율 < 50% |

<small>

**PASS**: 17개 중 ≥ 14개 통과
**CAUTION**: 11~13개 통과
**FAIL**: ≤ 10개 통과

통계적 3기준은 **교차 검증**(cross-run variance) 기반으로 단일 실험의 편향을 탐지합니다.

</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix G-2: Unified Validation — 범주별 해설

<div class="columns">
<div class="col">

### 약리학 12기준 — 역할

약리학 기준은 13-메트릭에서 **금속 배위**를 방사성의약품 범주로 분리한 12개입니다.

- **물리화학** (1~6): 용해도·안정성·정량 가능성 등 기본 druglikeness
- **구조·동역학** (7~9): 반감기·막 상호작용·양친매성
- **기능** (10~12): 종양 선택성(pH)·대사 안정성(프로테아제)·진화 보존(BLOSUM)

### 방사성의약품 2기준 — 역할

| 기준 | 설명 |
|------|------|
| **금속 배위** | His/Cys 잔기가 ⁶⁸Ga³⁺ 킬레이트 형성에 충분한지 |
| **신장독성** | ADMET 기반 신장 부담 위험 점수 — 방사성의약품은 신장 배출이 주경로 |

</div>
<div class="col">

### 통계적 3기준 — 역할

다중 실행(multi-run) **재현성·공정성** 보장

| 기준 | 의미 |
|------|------|
| **Rank Stability** | 순위가 실행마다 안정적인지 |
| **Score Consistency** | ddG 점수 실행 간 일관 (CV<15%) |
| **No Dominance** | 단일 후보 지배 여부 (편향 탐지) |

### PASS / CAUTION / FAIL 판정

1. 각 기준 Gate 조건 **통과/미통과** 판정
2. 통과 수 합산 → 3단계 판정
3. **CAUTION** 이상 → 후보 유지, **FAIL** → 제외
4. 통계 기준 미통과 시 → 추가 실행 권고

</div>
</div>

---

<!-- _class: compact -->

# Appendix G-3: Validation Checklist — 살린다 / 죽인다

<div class="columns">
<div class="col">

| # | 항목 | 설명 | ✓ |
|:-:|------|------|:--:|
| 1 | GRAVY | 소수성 범위 이내 | ☐살/☐죽 |
| 2 | Boman | 결합 잠재력 적정 | ☐살/☐죽 |
| 3 | 불안정성 지수 | II < 40 안정 | ☐살/☐죽 |
| 4 | Aliphatic Index | 열안정성 확보 | ☐살/☐죽 |
| 5 | pI | 등전점 범위 적정 | ☐살/☐죽 |
| 6 | ε₂₈₀ | UV 정량 가능 | ☐살/☐죽 |
| 7 | N-end Rule | N-말단 안정 잔기 | ☐살/☐죽 |
| 8 | Hydrophobic Moment | 양친매성 적정 | ☐살/☐죽 |
| 9 | Wimley-White | 막 삽입 에너지 | ☐살/☐죽 |

</div>
<div class="col">

| # | 항목 | 설명 | ✓ |
|:-:|------|------|:--:|
| 10 | pH별 전하 | 종양 선택성 | ☐살/☐죽 |
| 11 | 프로테아제 절단 | 절단 부위 허용 | ☐살/☐죽 |
| 12 | BLOSUM62 | 보존적 치환 | ☐살/☐죽 |
| 13 | **금속 배위** | ⁶⁸Ga 킬레이트 | ☐살/☐죽 |
| 14 | **신장독성** | 신장 배출 위험 | ☐살/☐죽 |
| 15 | **Rank Stability** | 순위 변동 허용 | ☐살/☐죽 |
| 16 | **Score Consistency** | 점수 CV<15% | ☐살/☐죽 |
| 17 | **No Dominance** | 단일 후보 비지배 | ☐살/☐죽 |

<small>**살**=Gate 적용(살린다) · **죽**=Gate 비활성화(죽인다) · 최소 14개 이상 활성화 권장</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix H-1: ADMET & 신장독성 — 계산식 & 모델

<div class="columns">
<div class="col">

### 신장독성 위험 점수 (Renal Retention Risk)

PRRT 방사성의약품은 **신장 배출이 주경로**이며, 양이온성 잔기가 세뇨관 재흡수를 증가시킵니다.

**공식**:

`Risk = min(100, (n_K + n_R) × 20 + max(0, Q_net) × 15)`

| 변수 | 정의 |
|------|------|
| n_K | Lys 잔기 수 (강양이온, +1.0) |
| n_R | Arg 잔기 수 (강양이온, +1.0) |
| Q_net | pH 7.4 순전하 (His +0.1 기여) |

**등급**: Low(<30, 허용) · Moderate(30~60, 아미노산 병용) · High(>60, Gelofusine)

</div>
<div class="col">

### 기준선: 임상 방사성의약품

| 약물 | n_K | n_R | Q_net | Risk |
|------|:---:|:---:|:-----:|:----:|
| **DOTATATE** | 1 | 0 | ~+1 | **~35** |
| SST-14 (WT) | 2 | 0 | ~+1 | **~55** |
| Octreotide | 1 | 0 | ~+1 | **~35** |

<small>DOTATATE Moderate → 임상에서 아미노산 병용주입으로 관리 [24]</small>

### Druglikeness (0~100)

MW 1200~2000(+25) · |Q_net|≤3(+25) · GRAVY[−2,+1](+25) · 동일잔기연속<3(+25)

<small>예측 모델 참조: ProTox 3.0 AUC=**0.86–0.89** [25] · pkCSM OCT2 기질 AUC=**0.810** [25] · ADMETlab AUC=**0.780** [26] · 본 시스템은 rule-based scoring 사용</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix H-2: FlexPepDock — 도킹 프로토콜 상세

<div class="columns">
<div class="col">

### 프로토콜 개요

PyRosetta FlexPepDock [1,2]은 수용체-펩타이드 복합체의 **유연 백본 정제**(flexible backbone refinement)를 수행합니다.

**초기화 플래그**:
```
-mute all
-ex1 -ex2aro
-ignore_unrecognized_res
-flexPepDocking:pep_refine
-constraints:cst_fa_weight 1.0
```

### 3단계 정제

| Step | 동작 |
|:----:|------|
| 1 | MutateResidue (백본 보존) |
| 2 | 곁사슬 chi각 최적화 |
| 3 | 백본 유연 최소화 (수용체 고정) |

</div>
<div class="col">

### 추출 에너지 지표

| 지표 | 계산 방법 | 의미 |
|------|---------|------|
| **ddG** | InterfaceAnalyzer(jump=1) | 결합 자유 에너지 변화 |
| **total_score** | REF2015 full-atom | 전체 에너지 |
| **clash_count** | fa_rep > 10.0 REU 잔기 수 | 원자 충돌 |
| **H-bonds** | Interface H-bond 수 | 수소 결합 |

### 이황화 결합 (Cys3-Cys14)

1. `detect_disulfides()` 자동 탐지
2. 실패 → **AtomPairConstraint** (2.05Å, σ=0.3)
3. 정제 후 SG-SG < 3.0Å → intact

<small>ddG는 **동일 조건 내 상대 비교**에 최적화 — 후보 간 순위가 절대값보다 신뢰 [1,2]</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix I-1: SST-14 기준 서열 & SSTR2 구조

<div class="columns">
<div class="col">

### SST-14 (Somatostatin-14)

**서열**: `AGCKNFFWKTFTSC` (14 AA, cyclic)
**이황화**: Cys3-Cys14 (β-hairpin 안정화)
**MW**: 1,638.8 Da · **pI**: ~9.2

### FWKT 파마코포어 (위치 7-10)

| 잔기 | 역할 |
|------|------|
| **Phe7** | 상부 소수성 포켓 방향족 스태킹 |
| **Trp8** | Ile177/Phe208/Phe272 **깊은 소수성 포켓** 삽입 |
| **Lys9** | **Asp122와 2.7Å 염다리** (필수) |
| **Thr10** | β-turn 안정화, W·K 배치 유지 |

> D122A 돌연변이 → 결합 소실 (<20% cAMP 저해) [23]
> **Trp-Lys 이합체**가 최소 필수 파마코포어

</div>
<div class="col">

### SSTR2 구조 (7-TM GPCR)

**Cryo-EM 구조**: PDB **7WJ5** (3.1Å, 2022)
<small>Robertson et al. *eLife* 11:e76823 (2022) [23]</small>

### 결합 포켓 주요 잔기

| 잔기 | TM | 상호작용 |
|------|:--:|---------|
| **Asp122** | 3 | Lys9 염다리 (2.7Å) |
| Gln126 | 3 | Lys9 H-bond |
| Ile177 | 4 | Trp8 소수성 포켓 |
| Phe208 | 5 | Trp8 소수성 포켓 |
| Thr212 | 5 | Trp8 소수성 포켓 |
| Phe272 | 6 | Trp8 소수성 포켓 |
| Asn276 | 6 | 펩타이드 결합 H-bond |

<small>추가 PDB: 7T10(SST-14), 7XAU(Octreotide), 7XNA(antagonist X-ray)</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix I-2: 임상 SSTR2 방사성의약품

<div class="columns">
<div class="col">

### 승인 약물 & 서열

| 약물 | 펩타이드 서열 | 승인 |
|------|-----------|------|
| **⁶⁸Ga-DOTATATE** (Netspot) | DOTA-DPhe-Cys-**Tyr**-**DTrp-Lys**-Thr-Cys-Thr | FDA 2016 |
| **⁶⁸Ga-DOTATOC** (Detectnet) | DOTA-DPhe-Cys-**Tyr**-**DTrp-Lys**-Thr-Cys-Thr(ol) | FDA 2019 |
| **¹⁷⁷Lu-DOTATATE** (Lutathera) | 동일 (치료용 동위원소) | FDA 2018 |

모든 임상 약물이 **DTrp-Lys** (SST-14의 W8-K9 대응) 보존

### NETTER-1 임상시험 (¹⁷⁷Lu-DOTATATE)

| 지표 | Lutathera | Octreotide |
|------|:---------:|:----------:|
| 20개월 PFS | **65.2%** | 10.8% |
| ORR | **18%** | 3% |
| n | 116 | 113 |

<small>NCT01578239, Strosberg et al. *NEJM* 376:125 (2017) [27]</small>

</div>
<div class="col">

### ⁶⁸Ga 킬레이션

| 특성 | DOTA | NOTA |
|------|------|------|
| 배위 | N₄O₂ | N₃O₃ |
| log K | **21~26** | **>30** |
| 표지 | 85°C 15분 | RT <5분 |
| ¹⁷⁷Lu | ✅ | ✗ |

**DOTA**: ⁶⁸Ga+¹⁷⁷Lu → **테라노스틱**
<small>His/Cys 도전 분석(37°C): transchelation 없음</small>

</div>
</div>

---

<!-- _class: compact -->

# Appendix I-3: AI × 방사성의약품 — 최신 동향 & 본 시스템 위치

<div class="columns">
<div class="col">

### AI 기반 방사성의약품 설계 동향

| 연도 | 저자/도구 | 내용 |
|:----:|---------|------|
| 2024 | Tao et al. [28] | AI 설계 방사성의약품 리뷰 (iRADIOLOGY) |
| 2025 | RFpeptides | 고리형 펩타이드 전용 RFdiffusion 변형 |
| 2025 | PepTune | 다목적 펩타이드 최적화 (친화도+용해도+투과성) |
| 2024 | AlphaFold 3 | 펩타이드-단백질 복합체 구조 예측 |

### 문헌 갭 — 본 시스템의 독자성

> **2026년 3월 기준**, 생성형 AI (RFdiffusion, diffusion model 등)를 **SSTR2 표적 방사성의약품 펩타이드 설계**에 적용한 논문은 **발견되지 않음**

</div>
<div class="col">

### 본 시스템(PRST_N_FM)의 차별점

| 기존 방법 | 본 시스템 |
|---------|---------|
| 수동 SAR 분석 | **5-Agent 자동 폐루프** |
| 단일 도구 (Rosetta) | **8개 NIM API 통합** |
| 약리학 미평가 | **13메트릭 + 17검증** 자동 |
| 신장독성 미고려 | **PRRT 특화** risk score |
| 재현성 미검증 | **통계적 3기준** (교차검증) |

### 학술적 기여

1. **Agentic AI** + 방사성의약품 = **최초 통합**
2. 13 약리학 메트릭의 **자동화된 in silico 평가**
3. PRRT 특화 **신장독성 사전 예측**
4. Thompson Sampling 기반 **적응적 탐색**
5. 통계적 검증으로 **재현성 보장**

</div>
</div>

---

<!-- _class: compact -->

# References (3/3)

<small>

**[23]** Robertson MJ et al. "Structure determination of the somatostatin receptor 2 complex with its agonist somatostatin delineates the ligand-binding specificity." *eLife* 11:e76823 (2022)
**[24]** Bodei L et al. "Long-term tolerability of PRRT in 807 patients with neuroendocrine tumours: the value and limitations of clinical factors." *Eur J Nucl Med Mol Imaging* 42:5-18 (2015)
**[25]** Pires DEV et al. "pkCSM: Predicting small-molecule pharmacokinetic and toxicity properties using graph-based signatures." *J Med Chem* 58:4066-4072 (2015)
**[26]** Xiong G et al. "ADMETlab 2.0: an integrated online platform for accurate and comprehensive predictions of ADMET properties." *Nucleic Acids Res* 49:W5-W14 (2021)
**[27]** Strosberg J et al. "Phase 3 trial of ¹⁷⁷Lu-DOTATATE for midgut neuroendocrine tumours." *NEJM* 376:125-135 (2017)
**[28]** Tao L et al. "Embracing artificial intelligence design for better radiopharmaceuticals." *iRADIOLOGY* 2:429-439 (2024)

</small>

---
<!-- _class: compact -->

# Appendix J-1: 통합 수식 레퍼런스 — 약리학·에너지

> 전 부록에 분산된 수식을 한눈에 참조할 수 있도록 정리. 상세 해설은 각 원본 부록 참조.

<div class="columns">
<div class="col">

### 생화학 13-메트릭 (A-1 ~ B-2)

| # | 수식 | 출처 |
|---|------|------|
| 1 | `GRAVY = (1/N) Σ H(i)` | [5] A-1 |
| 2 | `BI = −(1/N) Σ ΔG_tr(i)` | [6] A-2 |
| 3 | `II = (10/L) Σ DIWV(xᵢ,xᵢ₊₁)` | [7] A-2 |
| 4 | `AI = X(A)+2.9·X(V)+3.9·[X(I)+X(L)]` | [8] A-2 |
| 5 | `ε₂₈₀ = nW×5500+nY×1490+nSS×125` | [12] A-3 |
| 6 | `μH = (1/N)√[(ΣHᵢsinδi)²+(ΣHᵢcosδi)²]` | [10] A-3 |
| 7 | `ΔG_WW = Σ ΔG_WW(i)` | [11] A-4 |
| 8 | `Q(pH) = Σ n/(1+10^(pH−pKa)) − Σ n/(1+10^(pKa−pH))` | [9] A-4 |

</div>
<div class="col">

### Rosetta 에너지 (H-2)

| 항목 | 정의 |
|------|------|
| **ddG** | InterfaceAnalyzer(jump=1) 상대 ΔG |
| **total** | REF2015 full-atom score |
| **clash** | fa_rep > 10.0 REU 잔기 수 |
| **SS 구속** | SG-SG 2.05Å (σ=0.3) |

### 신장독성 (H-1)

| 수식 | 기준 |
|------|------|
| `Risk = min(100, (nK+nR)×20 + max(0,Qnet)×15)` | <30 Low · 30-60 Mod · >60 High |

### Druglikeness (H-1)

`DL = Σ(MW∈[1200,2000]→25, |Qnet|≤3→25, GRAVY∈[−2,+1]→25, repeat<3→25)`

</div>
</div>

---
<!-- _class: compact -->

# Appendix J-2: 통합 수식 레퍼런스 — 스코어링·통계·검증

<div class="columns">
<div class="col">

### Silo 스코어링 (C-1)

| Silo | 수식 |
|------|------|
| **B** | `S = 0.70·ddG + 0.20·total + 0.10·clash` |
| **A** | `S = 0.15·pLDDT + 0.25·dock + 0.25·ddG + 0.15·lDDT + 0.20·sel` |

<small>전 메트릭 MinMax [0,1] 정규화 · lower-is-better → 1−norm(x) · 경위반: −8.0/−0.4</small>

### QC Gate 4단계 (C-2)

| Gate | 조건 | 기본값 |
|------|------|--------|
| G1 | pLDDT ≥ T₁, interface ≥ T₂ | 50, 45 |
| G2 | dock top P% | 20% |
| G3 | ddG ≤ T₃ ∧ clash ≤ T₄ | −5.0, 10 |
| G4 | margin ≤ T₅ ∧ offtarget ≤ T₆ | −10, −15 |

### Unified Validation (G-1)

`PASS ≥ 14/17 · CAUTION 11-13 · FAIL ≤ 10`

</div>
<div class="col">

### Thompson Sampling (C-3)

| 단계 | 수식 |
|------|------|
| **사전분포** | `Beta(α=1, β=1)` |
| **갱신** | ddG < baseline → α++ · else β++ |
| **샘플링** | `θᵢ ~ Beta(αᵢ, βᵢ)` → top-N 선택 |
| **기댓값** | `E[θ] = α/(α+β)` |

### Mann-Whitney 수렴 (C-4)

| 항목 | 수식 |
|------|------|
| **U통계량** | `U₁ = n₁n₂ + n₁(n₁+1)/2 − R₁` |
| **정규근사** | `z = (U − n₁n₂/2) / √[n₁n₂(n₁+n₂+1)/12]` |
| **CV** | `σ / |μ|` |
| **수렴조건** | p > 0.05 **AND** CV < 0.15 |

<small>window=3 · α=0.05 · min_iter=6 · ddG ∈ [−60, 200]</small>

### 통계적 3기준 (G-1)

| 기준 | 조건 | 가중치 |
|------|------|--------|
| Rank Stability | confidence ≥ 0.7 | 0.4 |
| Score Consistency | max_cv ≤ 0.5 | 0.4 |
| No Dominance | gap_ratio > 2.0 이상 | 0.2 |

</div>
</div>
