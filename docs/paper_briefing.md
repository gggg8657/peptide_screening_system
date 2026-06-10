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
  .columns { display: flex; gap: 1.2em; align-items: flex-start; }
  .col { flex: 1; }
  blockquote { border-left: 3px solid #38bdf8; background: #1e293b; padding: 8px 14px; font-size: 0.80em; border-radius: 4px; }
  small { font-size: 0.6em; color: #94a3b8; }
  strong { color: #fbbf24; }
  code { font-size: 0.75em; background: #1e293b; padding: 1px 6px; border-radius: 3px; }
  a { color: #38bdf8; }
  .tag { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.7em; font-weight: 600; }
  .t-bio { background: #065f46; color: #6ee7b7; }
  .t-ai { background: #1e3a5f; color: #7dd3fc; }
  .t-rule { background: #78350f; color: #fbbf24; }
  section.compact { font-size: 26px; }
  section.compact h1 { font-size: 1.4em; }
  .box { border-radius: 8px; padding: 8px 14px; text-align: center; font-size: 0.78em; }
  .box-llm { background: #1e3a5f; border: 2px solid #38bdf8; }
  .box-rule { background: #78350f; border: 2px solid #fbbf24; }
  .box-proc { background: #064e3b; border: 2px solid #34d399; }
  .arrow { color: #64748b; font-size: 1.4em; line-height: 1; }
  .flow-row { display: flex; align-items: center; justify-content: center; gap: 6px; margin: 6px 0; flex-wrap: nowrap; }
  .flow-box { border-radius: 6px; padding: 6px 10px; text-align: center; font-size: 0.68em; line-height: 1.3; min-width: 100px; }
  .fb-llm { background: #1e3a5f; border: 2px solid #38bdf8; color: #7dd3fc; }
  .fb-rule { background: #451a03; border: 2px solid #f59e0b; color: #fbbf24; }
  .fb-sim { background: #064e3b; border: 2px solid #34d399; color: #6ee7b7; }
  .fb-data { background: #1e293b; border: 1px dashed #64748b; color: #94a3b8; font-size: 0.62em; }
  .legend { display: flex; gap: 16px; justify-content: center; font-size: 0.6em; margin-top: 8px; }
  .legend-item { display: flex; align-items: center; gap: 4px; }
  .legend-dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
---

# Paper Briefing
## Design and Operational Verification of an Agentic AI System for SSTR2-Binding Peptide Candidate Screening

<small>Transactions of the Korean Nuclear Society Spring Meeting
Jeju, Korea, May 7-8, 2026</small>

**저자**: 김동주ᵃ, 김소연ᵃᵇ, 유용균ᵃᵇ, 김민규ᶜ, 안기범ᶜ, 서호성ᶜᵇ*, 김유종ᵃᵇ*

<small>ᵃ KAERI 응용인공지능연구실 · ᵇ UST · ᶜ 사이클로트론응용연구실
\* Corresponding: hoseongseo@kaeri.re.kr, yjkim@kaeri.re.kr</small>

**키워드**: Agentic AI, Multi-agent, AI Scientist, Peptide Screening, SSTR2, SST14

---

# 연구 배경 & 목적

<div class="columns">
<div class="col">

### 배경

- **SSTR2**: 신경내분비종양(NET) 핵심 표적
- ¹⁷⁷Lu-DOTATATE (Lutathera®) — PRRT 표준치료
- 기존 한계: 제한적 침투, off-target 결합

### 문제: 기존 후보 탐색 = **수동 시행착오**

- 화학적 공간 극히 일부만 탐색
- 예측→도킹→평가 수동 조율 + 전문 인력 개입

</div>
<div class="col">

### 목적

SST-14 기반 SSTR2 결합 펩타이드 후보를
**자동으로** 설계·스크리닝·평가하는
멀티에이전트 시스템의 **설계 및 운용 검증**

### 논문의 범위

> 절대적 결합 에너지 예측이 **아닌**
> 후보 우선순위 결정을 위한
> **자동화 워크플로우의 설계와 검증**

</div>
</div>

---

<!-- _class: compact -->

# 시스템 아키텍처 — 5-Agent 폐루프 (Fig. 1)

<div class="flow-row" style="margin-top:16px;">
  <div class="flow-box fb-llm" style="min-width:120px;"><strong style="color:#38bdf8;">Planner</strong><br>돌연변이 전략<br>Prior-iteration 피드백</div>
  <span class="arrow">→</span>
  <div class="flow-box fb-sim" style="min-width:130px;"><strong style="color:#34d399;">Candidate Gen</strong><br>SST14 기반<br>변이 제안</div>
  <span class="arrow">→</span>
  <div class="flow-box fb-sim" style="min-width:130px;"><strong style="color:#34d399;">Simulation</strong><br>PyRosetta<br>FlexPepDock</div>
  <span class="arrow">→</span>
  <div class="flow-box fb-rule" style="min-width:110px;"><strong style="color:#f59e0b;">QCRanker</strong><br>ΔG/Clash<br>필터+랭킹</div>
</div>

<div class="flow-row">
  <div class="flow-box fb-llm" style="min-width:120px;"><strong style="color:#38bdf8;">Reporter</strong><br>구조화 로그<br>Top 후보+근거</div>
  <span class="arrow">←</span>
  <div class="flow-box fb-llm" style="min-width:130px;"><strong style="color:#38bdf8;">Critic</strong><br>실패 패턴 분석<br>개선 제안</div>
  <span class="arrow">←</span>
  <div class="flow-box fb-rule" style="min-width:130px;"><strong style="color:#f59e0b;">DiversityMgr</strong><br>중복 억제<br>위치 편향 제거</div>
  <span class="arrow">←───────</span>
</div>

<div style="text-align:center; margin:6px 0;">
  <span style="font-size:0.8em; color:#f87171;">↑ Feedback & Iteration Context ─── Critic → Planner (자기 개선 루프) ↩</span>
</div>

<div class="legend">
  <div class="legend-item"><span class="legend-dot" style="background:#1e3a5f; border:1px solid #38bdf8;"></span> LLM Agent (3개)</div>
  <div class="legend-item"><span class="legend-dot" style="background:#451a03; border:1px solid #f59e0b;"></span> Rule Agent (2개)</div>
  <div class="legend-item"><span class="legend-dot" style="background:#064e3b; border:1px solid #34d399;"></span> Process Step</div>
</div>

> **mutate → dock → QC → critique → report** 루프를 자동 반복
> 반복당 Critic 피드백 → Planner 전략 수정 (수렴 시 종료)

---

# 에이전트 역할 분담 — LLM + Rule 하이브리드

<div class="columns">
<div class="col">

| Agent | 유형 | 역할 | LLM 필요성 |
|-------|------|------|:---:|
| **Planner** | <span class="tag t-ai">LLM</span> | 돌연변이 전략 수립 | 4.2/5 |
| **QCRanker** | <span class="tag t-rule">Rule</span> | ΔG/Clash 필터+랭킹 | 1.2/5 |
| **DiversityMgr** | <span class="tag t-rule">Rule</span> | 중복/편향 억제 | 1.0/5 |
| **Critic** | <span class="tag t-ai">LLM</span> | 실패 분석+개선 제안 | 4.5/5 |
| **Reporter** | <span class="tag t-ai">LLM</span> | 구조화 로그 생성 | 3.8/5 |

</div>
<div class="col">

### 설계 원칙

> LLM 필요성 **≥ 2.0**인 에이전트만 LLM 사용
> 나머지는 **결정론적 코드**로 실행

### 효과

- LLM 호출 **50% 절감** (6회 → 3회/반복)
- **비결정성 위험 원천 제거** + SoC 유지
- 수렴: ddG 개선 < 0.5 **2연속** or 최대 5회

</div>
</div>

---

# 데이터 플로우 — 반복(Iteration) 상세

<div style="display:flex; gap:8px; align-items:stretch; margin-top:10px; font-size:0.72em;">
  <div style="flex:1; background:#1e293b; border-radius:8px; padding:10px; border-left:3px solid #38bdf8;">
    <strong style="color:#38bdf8;">① Planner (LLM)</strong><br><br>
    • 돌연변이 위치·종류 결정<br>
    • Critic 피드백 반영<br>
    • 최대 2개 파라미터 변경/iter<br>
    <div class="fb-data" style="margin-top:6px;">출력: mutation_strategy.json</div>
  </div>
  <div style="flex:1; background:#1e293b; border-radius:8px; padding:10px; border-left:3px solid #34d399;">
    <strong style="color:#34d399;">② Simulation</strong><br><br>
    • SST-14 변이체 생성<br>
    • PyRosetta FlexPepDock<br>
    • 후보당 <strong>10회 독립 도킹</strong><br>
    <div class="fb-data" style="margin-top:6px;">출력: docking_results.json</div>
  </div>
  <div style="flex:1; background:#1e293b; border-radius:8px; padding:10px; border-left:3px solid #f59e0b;">
    <strong style="color:#f59e0b;">③ QC + Diversity</strong><br><br>
    • Top-3 mean ΔG 산출<br>
    • ddG ≤ −5.0 / Clash ≤ 10<br>
    • 서열 유사도 클러스터링<br>
    <div class="fb-data" style="margin-top:6px;">출력: ranked_candidates.json</div>
  </div>
  <div style="flex:1; background:#1e293b; border-radius:8px; padding:10px; border-left:3px solid #f87171;">
    <strong style="color:#f87171;">④ Critic → Reporter</strong><br><br>
    • 실패 유형 6종 분류<br>
    • 교정 액션 매핑<br>
    • 구조화 로그 생성<br>
    <div class="fb-data" style="margin-top:6px;">출력: iteration_report.json</div>
  </div>
</div>

<div style="text-align:center; margin-top:14px;">
  <span style="background:#1e293b; border:1px solid #475569; border-radius:20px; padding:6px 20px; font-size:0.75em;">
    🔄 Reporter 출력 → <strong style="color:#38bdf8;">Planner 입력</strong>으로 피드백 (자기 개선 루프)
  </span>
</div>

<div style="display:flex; justify-content:center; gap:24px; margin-top:12px; font-size:0.68em; color:#94a3b8;">
  <span>ΔG > 0 시행 제외</span>
  <span>|</span>
  <span>파라미터 화이트리스트 검증 (환각 차단)</span>
  <span>|</span>
  <span>반복당 최대 2개 파라미터 변경</span>
</div>

---

<!-- _class: compact -->

# 평가 파이프라인 — QC Gate & 설계 원칙

<div class="columns">
<div class="col">

### PyRosetta FlexPepDock

<div style="background:#1e293b; border-radius:8px; padding:10px; font-size:0.85em; margin:6px 0;">
  <strong style="color:#34d399;">입력</strong>: SSTR2–SST14 Cryo-EM 복합체 [1,2]<br>
  <strong style="color:#34d399;">도킹</strong>: 후보당 10회 독립 시행<br>
  <strong style="color:#34d399;">지표</strong>: Top-3 mean ΔG (변동 완화)<br>
  <strong style="color:#f87171;">제외</strong>: ΔG > 0 시행
</div>

### QC Gate 기준

| 기준 | 임계값 | 역할 |
|------|--------|------|
| Rosetta ddG | ≤ −5.0 kcal/mol | 결합력 필터 |
| Clash score | ≤ 10 REU | 구조 충돌 필터 |

</div>
<div class="col">

### 핵심 설계 원칙

> ΔG 값은 **후보 간 상대 비교** 용도
> 동일 조건 하 **구조적으로 유리한 후보**를 식별

<div style="background:#1e293b; border-radius:8px; padding:10px; font-size:0.85em; margin:8px 0;">
  ✅ 동일 수용체 · 동일 프로토콜 · 동일 시행 수<br>
  ✅ <strong>directional consistency</strong> 검증<br>
  ❌ 절대값 ≠ 실험적 결합 에너지
</div>

### DiversityManager

- 서열 유사도 기반 클러스터링
- 중복 후보 제거 + 위치 편향 억제

</div>
</div>

---

# 검증 결과 — Table I: Directional-Consistency Check

| ID | Class | 설명 | Mean ΔG | Δ vs WT | Match |
|----|-------|------|:---:|:---:|:---:|
| **LIT-01** | WT SST-14 | 내재 리간드 (기준) | **−43.78** | — | — |
| LIT-02 | Octreotide | 임상 약물 유도체 | −42.11 | +1.67 | **Y** |
| LIT-03 | CST-14 | Lanreotide (나노몰) | −37.30 | +6.47 | **N*** |
| SAN-01 | **W8A** | Trp8 핫스팟 파괴 | −38.22 | +5.56 | **Y** |
| SAN-02 | **K9A** | Lys9 핫스팟 파괴 | −39.53 | +4.25 | **Y** |
| NOV-01 | AI 설계 | A1Y, G2S, S13N | **−43.92** | −0.15 | **WT급** |
| NOV-02 | AI 설계 | σ = 3.53 (최저) | −41.47 | +2.31 | 재현성 |

<div style="display:flex; gap:12px; margin-top:8px; font-size:0.72em;">
  <div style="flex:1; background:#064e3b; border-radius:6px; padding:6px 10px;">
    <strong style="color:#6ee7b7;">✅ 양성 대조군</strong>: WT, Octreotide → 상위권 정렬
  </div>
  <div style="flex:1; background:#7f1d1d; border-radius:6px; padding:6px 10px;">
    <strong style="color:#fca5a5;">✅ 음성 대조군</strong>: W8A, K9A → WT보다 낮은 순위
  </div>
  <div style="flex:1; background:#78350f; border-radius:6px; padding:6px 10px;">
    <strong style="color:#fbbf24;">⚠️ CST-14</strong>: G2→P proline 강직성 → 알려진 한계
  </div>
</div>

---

<!-- _class: compact -->

# 핵심 결과 해석

<div class="columns">
<div class="col">

### 시스템이 올바르게 판별

- **W8A, K9A** (핫스팟 파괴) → WT보다 낮은 순위
- **Octreotide** (임상 약물) → WT 유사 상위권
- 순서: WT ≈ NOV-01 > LIT-02 > SAN-02 > SAN-01

### AI 설계 후보

- **NOV-01**: ΔΔG −0.15, 비핫스팟 3곳 변이 → WT급
- **NOV-02**: σ 3.53 (최저) → 재현성 우수

</div>
<div class="col">

### CST-14 예외의 교훈

CST-14: 실험적 나노몰 친화도 but ΔG = +6.47

**원인**: G2→P → backbone 강직성 → FlexPepDock flexible-backbone 정제 불이익

**시사점**: Proline 펩타이드 QC 게이트 보정 필요

> *"a known simulator limitation, not a failure of the system's ranking logic"*

</div>
</div>

---

# 3대 기여 & 한계

<div class="columns">
<div class="col">

### 기여

<div style="background:#1e293b; border-left:3px solid #38bdf8; border-radius:6px; padding:8px 12px; font-size:0.85em; margin:6px 0;">
<strong style="color:#38bdf8;">1. 5-Agent 폐루프 아키텍처</strong><br>
candidate gen–sim–QC–critique–report 자동 반복하는 추적 가능한 워크플로우
</div>

<div style="background:#1e293b; border-left:3px solid #34d399; border-radius:6px; padding:8px 12px; font-size:0.85em; margin:6px 0;">
<strong style="color:#34d399;">2. 방향적 일관성 검증</strong><br>
문헌 기반 양성/음성 대조군으로 시스템의 판별력 정량 확인
</div>

<div style="background:#1e293b; border-left:3px solid #f59e0b; border-radius:6px; padding:8px 12px; font-size:0.85em; margin:6px 0;">
<strong style="color:#f59e0b;">3. LLM + Rule 하이브리드</strong><br>
과학적 추론에만 LLM, QC/Ranking은 결정론적 코드 → 재현성
</div>

</div>
<div class="col">

### 알려진 한계

| 한계 | 대응 방안 |
|------|---------|
| 웨트랩 검증 부재 | SPR / ⁶⁸Ga 표지 실험 |
| Proline 과소평가 | QC 게이트 보정 로직 |
| 절대 ΔG ≠ 실험값 | 상대 비교 용도로만 해석 |

### 향후 계획

- wet-lab 결과 → Planner 피드백 루프
- Silo A (de novo) 파이프라인 통합
- ADMET / 13-메트릭 약리학 자동화

</div>
</div>

---

# Q&A

<br>

## 감사합니다

<br>

**Korea Atomic Energy Research Institute**
Applied Artificial Intelligence Section

<small>Contact: yjkim@kaeri.re.kr | hoseongseo@kaeri.re.kr</small>

<br>

> *"The objective is not to improve a specific binding-affinity prediction accuracy but to present the design, implementation, and operational verification of a system that supports candidate prioritization."*
