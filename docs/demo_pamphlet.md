---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
style: |
  section { font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif; }
  h1 { color: #1a365d; font-size: 1.6em; }
  h2 { color: #2d3748; font-size: 1.3em; }
  h3 { color: #4a5568; }
  table { font-size: 0.75em; }
  code { font-size: 0.8em; }
  .columns { display: flex; gap: 1.5em; }
  .col { flex: 1; }
  small { font-size: 0.65em; color: #718096; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; font-weight: bold; }
  .tag-bio { background: #c6f6d5; color: #22543d; }
  .tag-ai { background: #bee3f8; color: #2a4365; }
  .tag-ui { background: #fefcbf; color: #744210; }
  .tag-qc { background: #fed7e2; color: #702459; }
  .metric-card { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center; }
  .highlight { background: linear-gradient(135deg, #ebf8ff 0%, #e9d8fd 100%); border-radius: 8px; padding: 16px; }
  blockquote { border-left: 4px solid #4299e1; background: #ebf8ff; padding: 8px 16px; font-size: 0.85em; }
---

# 🧬 SSTR2 AI Co-Scientist
## 시스템 데모 가이드 & 생명공학 도구 해설

**PRST_N_FM** — Agentic AI for Radiopharmaceutical Peptide Screening

Korea Atomic Energy Research Institute (KAERI)
Applied Artificial Intelligence Section

<small>2026-03-09 | Internal Demo & Progress Briefing</small>

---

# 📋 데모 구성

<div class="columns">
<div class="col">

### Part 1 — 시스템 개요
1. 왜 AI Co-Scientist인가
2. 5-Agent 아키텍처
3. Silo B 파이프라인 흐름

### Part 2 — 생명공학 도구
4. PyRosetta FlexPepDock
5. FoldMason 구조 정렬
6. 약리학 13-메트릭 계산기
7. NVIDIA NIM API 도구들

</div>
<div class="col">

### Part 3 — 대시보드 UI
8. 실험 제어 패널
9. 후보 물질 테이블
10. 수렴 그래프 & ΔΔG 분포
11. SAR 히트맵 & 시퀀스 로고
12. 약리학 & 검증 패널
13. 3D 분자 뷰어

### Part 4 — 검증 결과
14. 논문 검증 테이블 (Table I)
15. 향후 계획

</div>
</div>

---

# Part 1 — 시스템 개요

---

# 왜 AI Co-Scientist인가

<div class="highlight">

**문제**: 펩타이드 후보 스크리닝은 단일 계산이 아닌 **반복 탐색 워크플로우**
생성 → 시뮬레이션 → QC → 비평 → 보고 → 다음 반복 계획

</div>

<div class="columns">
<div class="col">

### 기존 한계
- 도구 간 단절 (수동 연결)
- 반복 간 추적성 부재
- 결과 해석 → 다음 실험 설계 병목
- 후보 수 증가 시 수동 부담 폭증

</div>
<div class="col">

### AI Co-Scientist 접근
- **5-Agent 자동 루프** 구현
- 반복 간 피드백 자동 전달
- 구조화된 로그 → 완전한 추적성
- **~240 후보/시간** 스크리닝 처리량

</div>
</div>

> **핵심**: 개별 결합 에너지 정확도가 아닌, 반복 워크플로우의 **자동화·추적성·재현성**

---

# 5-Agent 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Iteration Loop                        │
│                                                          │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Planner  │───▶│  Candidate   │───▶│  Simulation  │   │
│  │ (Qwen3)  │    │  Generation  │    │ (FlexPepDock)│   │
│  └────▲─────┘    └──────────────┘    └──────┬───────┘   │
│       │                                      │           │
│       │  Feedback                    ΔG & clash          │
│       │                                      ▼           │
│  ┌────┴─────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Reporter │◀───│    Critic    │◀───│  QCRanker    │   │
│  │(PyMOL+MD)│    │  (Qwen3)    │    │ (PyRosetta)  │   │
│  └──────────┘    └──────────────┘    └──────────────┘   │
│                         ▲                                │
│                  ┌──────┴───────┐                        │
│                  │ Diversity    │                        │
│                  │ Manager     │                        │
│                  │ (FoldMason) │                        │
│                  └──────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

| Agent | 역할 | 핵심 도구 |
|-------|------|----------|
| **Planner** | 돌연변이 전략 수립, 피드백 반영 | Qwen3:8b LLM |
| **QCRanker** | 규칙 기반 QC 게이트 + 순위 매김 | PyRosetta InterfaceAnalyzer |
| **DiversityManager** | 중복 억제, 편향 완화 | FoldMason 구조 정렬 |
| **Critic** | 실패 패턴 분석, 개선점 도출 | Qwen3:8b LLM |
| **Reporter** | 구조화 로그, 시각화 생성 | PyMOL + CSV + Markdown |

---

# Silo B 파이프라인 흐름

```
SST-14 참조 서열: A G C K N F F W K T F T S C
                      ↑       ↑─────↑ ↑
                     Cys3     핵심 모티프  Cys14
                      └─── 이황화 결합 ───┘

[Config] → Baseline Refinement (best-of-N)
  └── Iteration Loop (max_iterations):
      ├── 1. Planner Agent → 가설 + 초점 위치 (Thompson Sampling)
      ├── 2. Mutation → SST-14 기반 변이체 생성 (8~32개)
      ├── 3. FlexPepDock → 병렬 도킹 (ThreadPoolExecutor)
      ├── 4. QC & Ranker → ΔΔG 게이트 + 순위 매김
      ├── 5. Convergence → Mann-Whitney U 검정
      ├── 6. Critic Agent → 파라미터 조정 제안
      └── 7. Reporter Agent → JSON 아티팩트 생성
```

---
<div class="columns">
<div class="col">

**핵심 파라미터**
- `n_candidates`: 반복당 8~32개
- `validation_n_trials`: 1(스크리닝)→10(논문)
- `rosetta_ddg_max`: ≤ −5.0 kcal/mol
- `rosetta_clash_max`: ≤ 10 REU

</div>
<div class="col">

**수렴 기준**
- Mann-Whitney U p-value > 0.05
- CV(변동계수) < 0.15
- 연속 3 윈도우 기준
- 조기 종료 지원

</div>
</div>

---

# Part 2 — 생명공학 도구 해설

---

# PyRosetta FlexPepDock
<span class="tag tag-bio">구조생물학</span> <span class="tag tag-qc">핵심 스코어링</span>

<div class="columns">
<div class="col">

### 무엇을 하는가
유연한 펩타이드-단백질 복합체의 **고해상도 도킹 정제**
- 측쇄 로타머 최적화
- 백본 유연성 반영
- **결합 자유 에너지 (ΔG)** 정량 계산

### 파이프라인 내 역할
- 후보 변이체의 **유일한 정량적 순위** 기준
- 10회 독립 도킹 → top-3 평균 ΔG
- ΔG > 0 제외 (정제 실패)

</div>
<div class="col">

### 핵심 출력값

| 메트릭 | 단위 | 의미 |
|--------|------|------|
| **ΔG** | kcal/mol | 결합 에너지 (−가 유리) |
| **total_score** | REU | 전체 에너지 |
| **clash_score** | REU | 입체 충돌 (fa_rep) |
| **sg_sg_distance** | Å | Cys3-Cys14 거리 |

### 생명공학적 의의
- GPCR-펩타이드 상호작용 모델링의 **표준 도구**
- 이황화 결합 제약조건 강제 (DOTATATE 토폴로지 유지)
- wet-lab 실험 전 후보 우선순위 결정

</div>
</div>

<small>Chaudhury et al., Bioinformatics 2010 / Raveh et al., PLoS ONE 2011</small>

---

# FoldMason 구조 정렬
<span class="tag tag-bio">구조생물학</span> <span class="tag tag-qc">다양성 관리</span>

<div class="columns">
<div class="col">

### 무엇을 하는가
**3D 기하학 기반** 다중 단백질 구조 정렬
- 서열이 아닌 **구조** 유사성으로 비교
- lDDT (local Distance Difference Test) 점수 산출
- **3Di 알파벳**: 20자 구조 인코딩

### 핵심 메트릭

| lDDT | 품질 |
|------|------|
| > 0.8 | 높은 구조적 일관성 |
| 0.5–0.8 | 중간 |
| < 0.5 | 낮음 (비신뢰 영역) |

</div>
<div class="col">

### 파이프라인 내 역할
1. **DiversityManager**: 유사 구조 후보 그룹핑 → 중복 억제
2. **수용체 패밀리 비교**: SSTR1-5 선택성 결정 잔기 식별
3. **모델 QC**: AlphaFold 예측 일관성 평가

### 생명공학적 의의
- GPCR 패밀리 수준 비교에서 서열보다 **구조가 본질적**
- SSTR2 특이적 결합 포켓 결정인자 발견
- 후보 풀의 **구조적 다양성 보장** → 편향 완화

</div>
</div>

<small>Gilchrist, Mirdita & Steinegger, Science 2026</small>

---

# 약리학 13-메트릭 계산기
<span class="tag tag-bio">약리학</span> <span class="tag tag-qc">방사성의약품</span>

서열만으로 **13가지 문헌 기반 생화학 특성**을 즉시 계산

<div class="columns">
<div class="col">

### 물리적 특성 (4개)
| 메트릭 | 출처 | 의미 |
|--------|------|------|
| GRAVY | Kyte 1982 | 소수성 (막 친화도) |
| Boman Index | Boman 2003 | 단백질 결합 잠재력 |
| 불안정성 지수 | Guruprasad 1990 | < 40 = 안정 |
| 지방족 지수 | Ikai 1980 | 열안정성 대리지표 |

### 전기화학 (4개)
| 메트릭 | 의미 |
|--------|------|
| 등전점 (pI) | 순전하 0인 pH |
| 흡광계수 (280nm) | 단백질 정량 |
| N-말단 규칙 | 세포 내 반감기 예측 |
| 소수성 모멘트 | 양친매성 |

</div>
<div class="col">

### 막 & 안정성 (4개)
| 메트릭 | 의미 |
|--------|------|
| Wimley-White | 막 이동 에너지 |
| pH별 전하 | **종양 선택성** (pH 6.5 vs 7.4) |
| 프로테아제 절단 | 트립신/NEP 취약점 |
| 금속 배위 | ⁶⁸Ga/⁶⁴Cu 킬레이트 호환성 |

### BLOSUM62 보존성 (1개)
- 돌연변이의 진화적 보존성 점수
- 보존적/반보존적/비보존적 분류

### 방사성의약품 활용
> **pH별 전하**: 산성 종양 미세환경 (pH 6.5) 에서의 SSTR2 선택성 설명
> **금속 배위**: 방사성금속 표지 호환성 평가
> **프로테아제**: D-아미노산 치환 가이드

</div>
</div>

---

# NVIDIA NIM API 도구들 (Silo A)
<span class="tag tag-ai">클라우드 API</span> <span class="tag tag-bio">구조생물학</span>

<div class="columns">
<div class="col">

### De Novo 설계 파이프라인

| 단계 | 도구 | 역할 |
|------|------|------|
| Step 02 | **RFdiffusion** | 신규 백본 3D 구조 생성 |
| Step 03 | **ProteinMPNN** | 백본 → 최적 서열 역설계 |
| Step 04 | **ESMFold** | 빠른 구조 예측 + pLDDT QC |
| Step 05 | **DiffDock** | 블라인드 분자 도킹 |
| Step 05b | **Boltz-2** | 복합체 구조 + 친화도 예측 |

### 생성 규모
```
RFdiffusion: 10 백본/반복
  × ProteinMPNN: 8 서열/백본
  = 80 후보 서열
  → ESMFold QC: ~25개 통과
  → DiffDock: ~250 포즈
  → PyRosetta: Top 10 정제
```

</div>
<div class="col">

### 각 도구의 생명공학적 의의

**RFdiffusion** (확산 모델)
- 템플릿/단편 라이브러리 불필요
- 핫스팟 가이드 설계 → SSTR2 핵심 잔기 접촉 보장

**ProteinMPNN** (역접힘)
- 구조 공간 → 서열 공간 변환
- 온도 제어로 안정성/다양성 균형

**ESMFold** (MSA-free 예측)
- MSA 없이 **10배 빠른** 구조 예측
- pLDDT로 불안정 후보 조기 필터링

**DiffDock** (확산 기반 도킹)
- 결합 부위 사전 지식 불필요
- 격자 기반 방법 대비 높은 정확도

</div>
</div>

---

# Part 3 — 대시보드 UI 해설

---

# 실험 제어 패널 (ExperimentControl)
<span class="tag tag-ui">실시간 제어</span>

<div class="columns">
<div class="col">

### 주요 제어 항목

| 파라미터 | 범위 | 의미 |
|---------|------|------|
| **Iterations** | 1–999 | mutate-dock-score 루프 횟수 |
| **Candidates** | 2–32 | 반복당 생성 변이체 수 |
| **Top-K** | 1–20 | Critic에 전달할 상위 후보 |
| **LLM Model** | 드롭다운 | Ollama 모델 선택 |
| **Objective** | Auto/ΔΔG/+제약 | 최적화 모드 |
| **Validation** | Off/3/5/10 | 검증 시행 횟수 |

</div>
<div class="col">

### 부가 기능 토글 (6개)

| 기능 | 태그 | 설명 |
|------|------|------|
| Cross-Run Dedup | 효율 | 실행 간 중복 제거 |
| Bandit Guidance | 최적화 | Thompson Sampling 위치 선택 |
| Convergence | 통계 | Mann-Whitney U 조기종료 |
| Disulfide | 구조 | Cys3-Cys14 결합 강제 |
| ADMET Gate | 약리 | 약물 유사성 + 신독성 |
| SAR Analysis | 분석 | 위치별 변이 히트맵 |

### 데모 포인트
> "Start Experiment" 클릭 → 실시간으로 모든 패널 업데이트

</div>
</div>

---

# 후보 물질 테이블 (CandidateTable)
<span class="tag tag-ui">순위 매김</span> <span class="tag tag-qc">다차원 평가</span>

**13개 컬럼**으로 후보 물질을 다차원 평가

| 컬럼 | 단위/형식 | 의미 | 색상 기준 |
|------|----------|------|----------|
| **Rank** | 1,2,3... | ΔΔG 기준 종합 순위 | 🥇🥈🥉 메달 |
| **ΔΔG** | kcal/mol | 결합 에너지 | 녹→적 (낮을수록 좋음) |
| **Total Score** | REU | PyRosetta 전체 에너지 | - |
| **Clash** | REU | 입체 충돌 | >5 주의, >10 위험 |
| **Sequence** | 14자 | 아미노산 서열 | - |
| **Result** | PASS/FAIL | QC 게이트 통과 여부 | 녹/적 배지 |
| **Repro.** | ΔΔG 범위 | 재현성 (시행 횟수 표시) | <20 녹, >50 적 |
| **Validation** | PASS/FAIL | 통합 검증 결과 | 방패 아이콘 |
| **Drug-like** | 0–100 | 약물 유사성 점수 | ≥75 녹, <50 적 |
| **Nephrotox** | Low/Mid/High | PRRT 신장 잔류 위험 | 신장 아이콘 |
| **3D** | 버튼 | Mol* 3D 구조 뷰어 실행 | - |

> **데모 포인트**: 행 클릭 → 선택 → "Validate" → 통합 검증 실행

---

# 수렴 그래프 & ΔΔG 분포
<span class="tag tag-ui">실시간 모니터링</span> <span class="tag tag-bio">통계</span>

<div class="columns">
<div class="col">

### ConvergenceGraph

**이중 Y축 복합 차트**
- **좌축 (노란선)**: Best ΔΔG 추이
  - 낮을수록 강한 결합
  - 수렴 임계값: Δ < 0.5 kcal/mol
- **우축 (보라막대)**: QC 통과 후보 수
- **참조선**: 수렴 임계값 (−8.1)

**의미**: 반복이 진행될수록
→ ΔΔG가 안정화되면 **수렴 달성**
→ 조기종료로 계산 자원 절약

</div>
<div class="col">

### DdGDistribution

**ΔΔG 히스토그램** (20 bin)
- X축: −50 ~ 0 kcal/mol
- Y축: 후보 수
- **적색 점선**: QC 게이트 (−5.0)

**통계 요약 표시**
- 평균, 중앙값, 표준편차
- **통과율**: ΔΔG ≤ −5.0 비율 (%)

**의미**: 전체 후보 풀의 에너지 분포
→ 왼쪽으로 치우칠수록 좋은 후보 많음
→ 게이트 통과율로 반복 품질 판단

</div>
</div>

---

# SAR 히트맵 & 시퀀스 로고
<span class="tag tag-ui">구조-활성 관계</span> <span class="tag tag-bio">진화 분석</span>

<div class="columns">
<div class="col">

### SARHeatmap (19×14 매트릭스)

**아미노산 (19행) × 위치 (14열)**
- 색상: 빈도 (어두운→노랑→시안)
- 대각선 점선: 참조 잔기 (ref)
- **금색 배경**: FWKT 파마코포어 (7-10번)

**의미**: 어떤 위치에 어떤 아미노산이
자주 생성되는지 한눈에 파악
→ **핫스팟 보존** 여부 즉시 확인
→ Thompson Sampling 가이드와 연동

</div>
<div class="col">

### SequenceLogo (정보 엔트로피)

**위치별 아미노산 분포 시각화**
- 글자 높이 = 정보량 × 빈도
- 정보 엔트로피: 0–4.32 bits
- **색상 분류**:
  - 회색: 소수성 (A,G,V,L,I,P,F,M,W)
  - 녹색: 극성 (S,T,C,Y,N,Q)
  - 청색: 양전하 (K,R,H)
  - 적색: 음전하 (D,E)

**의미**: 보존된 위치(높은 글자)
= 기능적으로 중요한 잔기
→ Trp8, Lys9 위치가 항상 높아야 정상

</div>
</div>

---

# 약리학 & 검증 패널
<span class="tag tag-qc">방사성의약품</span> <span class="tag tag-bio">약리학</span>

<div class="columns">
<div class="col">

### PharmacologyPanel (13 메트릭)

**4행 구성**:
1. **물리 특성**: GRAVY, Boman, 불안정성, 지방족
2. **전기화학**: pI, 흡광계수, N-말단 반감기, μH
3. **막/안정성**: Wimley-White, pH별 전하, 프로테아제, 금속배위
4. **BLOSUM62**: 돌연변이 보존성 테이블

**후보 선택 드롭다운** → 즉시 계산 결과 표시

</div>
<div class="col">

### ValidationPanel (통합 검증)

**3그룹 검증 기준**:
- 약리학적 (pharmacological)
- 방사성의약품 (radiopharmaceutical)
- 통계적 (statistical)

**프리셋 지원**:
- `prrt_radiopharmaceutical` 등

**결과 표시**:
- **PASS** / **CAUTION** / **FAIL** 판정
- 기준별 도트 매트릭스 (녹/적)
- 상세 모달 → 개별 임계값 확인

</div>
</div>

> **데모 포인트**: 후보 체크 → "Run Validation" → PRRT 방사성의약품 기준으로 통합 판정

---

# 3D 분자 뷰어 & 추가 패널
<span class="tag tag-ui">시각화</span>

<div class="columns">
<div class="col">

### MoleculeViewer (Mol* 라이브러리)

**뷰 모드 4종**:
| 모드 | 표현 |
|------|------|
| Complex | 리본 + 리간드/물/이온 |
| Cartoon | 백본만 |
| Ball & Stick | 전 원자 |
| Surface | 표면 |

**인터랙션**: 드래그 회전, 스크롤 줌, Shift+드래그 이동

### MutationAnalysis
- **FWKT 보존율**: ≥90% 녹, 70-89% 주의, <70% 위험
- **보존적/비보존적** 돌연변이 분류 (BLOSUM62)
- **ΔΔG vs 돌연변이 수** 산점도

</div>
<div class="col">

### PositionEnrichment (위치별 상위 변이체)

14개 위치 × Top-3 변이체 테이블
- 빈도 (%) + 평균 ΔΔG
- 색상: 녹(유리) → 적(불리)
- FWKT 위치 주황 강조

### QCGateChart
- 게이트별 통과/탈락 **적층 막대**
- 각 게이트 기준 표시 (예: "ΔΔG ≤ −5.0")

### RunComparisonPanel
- 과거 실행 이력 테이블
- 미니 **스파크라인** (ΔΔG 추이)
- 현재 실행 시안 강조

### RiskMatrix
- **3×3 확률×영향** 리스크 평가
- P0(적)→P3(녹) 우선순위 배지

</div>
</div>

---

# Part 4 — 검증 결과

---

# 논문 검증 결과 (Table I)
<span class="tag tag-bio">방향적 일관성 검증</span>

| ID | 분류 | 핵심 변이 | 예상 방향 | 시스템 판정 | Mean ΔG | dΔG vs WT | 일치 |
|------|------|---------|----------|-----------|---------|-----------|------|
| **LIT-01** | WT SST14 | 내재적 SSTR2 리간드 | 유리 | Upper Tier | **−43.78** | — | — |
| **LIT-02** | Octreotide | 임상 약물 | 유리 | Upper Tier | −42.11 | +1.67 | **Y** |
| **LIT-03** | CST-14 | nM 작용제 | 유리 | Upper Tier | −37.30 | +6.47 | **N*** |
| **SAN-01** | W8A | Trp8 파괴 | 불리 | Lower Tier | −38.22 | +5.56 | **Y** |
| **SAN-02** | K9A | Lys9 파괴 | 불리 | Lower Tier | −39.53 | +4.25 | **Y** |
| **NOV-01** | 파이프라인 설계 | A1Y,G2S,S13N | — | Upper Tier | **−43.92** | −0.15 | — |
| **NOV-02** | 파이프라인 설계 | — | — | Upper Tier | −41.47 | +2.31 | — |

\* LIT-03: G2→P 프롤린 치환 → **FlexPepDock 백본 강직성 페널티** (시뮬레이터 알려진 한계)

<div class="columns">
<div class="col">

**NOV-01 성과**: 3개 비핵심 위치 돌연변이로 **WT 수준 결합 에너지** 달성
→ Planner가 Trp8-Lys9 모티프 보존하면서 변이 허용 위치 올바르게 식별

</div>
<div class="col">

**NOV-02 성과**: **최저 σ = 3.53** (전 후보 중 가장 재현성 높은 결합 포즈)
→ 하류 실험 우선순위 결정에 유리한 특성

</div>
</div>

---

# 향후 계획 & Q&A

<div class="columns">
<div class="col">

### 단기 (1–2개월)
- **Silo A 구현**: NVIDIA NIM 8-step 파이프라인
- **Orchestrator**: Silo A+B 통합 오케스트레이션
  - `state_machine.py` strict/fast 모드 완성
  - `wait_timeout_sec` 실적용
- **Wet-lab 연계**: 실험 결과 → Planner 피드백 루프

### 중기 (3–6개월)
- **QC 게이트 고도화**: 프롤린 백본 제약 반영
- **ADMET 파이프라인**: 전임상 약리학 자동 평가
- **선택성 스크리닝**: SSTR1-5 off-target 차별화

</div>
<div class="col">

### 핵심 메시지

> 이 시스템의 의의는 개별 예측 정확도가 아닌,
> **후보 우선순위 결정과 실험 설계 지원을 위한
> 자동화 워크플로우의 설계·구현·운영 검증**에 있습니다.

### 데모 환경

| 서비스 | 포트 | 상태 |
|--------|------|------|
| Frontend | :5173 | React 19 + Vite |
| Backend | :8787 | FastAPI |
| Ollama | :11434 | Qwen3:8b |
| Pipeline | - | PyRosetta (conda) |

</div>
</div>

---

# Thank You

**PRST_N_FM** — Agentic AI Co-Scientist for SSTR2 Radiopharmaceutical Peptide Design

Korea Atomic Energy Research Institute (KAERI)


<small>Contact: dongjukim@kaeri.re.kr | yjkim@kaeri.re.kr | hoseongseo@kaeri.re.kr</small>
