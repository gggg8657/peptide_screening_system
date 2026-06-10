# A-04: Top-K 후보 선정 복합 스코어링 체계 설계

**회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) | **담당**: AI팀·RI팀 | **기한**: 5월 회의 전 | **상태**: ✅ PR #62 머지

---

## ① 원본 요청 및 해석/분석

### 원문 (PDF §3 Action Items 표, p.5)
> "Top-K 후보 선정 복합 스코어링 체계 설계 (⊿G + 반감기 + 셀렉티비티 + ADMET 통합)"

### 회의록 §2.3 배경 (p.4)
> "**핵심 이슈**: Top-K 후보 선정 기준이 아직 확정되지 않았으며, 현재 ⊿G 값에 과도하게 의존하는 경향이 있다. ⊿G 외에 반감기, 셀렉티비티 등 복합 파라미터를 종합 고려한 최종 스코어링 체계가 필요하다. SST14 도킹 스코어를 레퍼런스 값으로 활용하여 ⊿G 기준선을 가변적으로 설정하는 방안이 제안되었다."

### 회의록 §4 A-04 수행 가이드 (p.7)
1. 현재 파이프라인에서 산출 가능한 지표를 목록화: ⊿G(도킹), 셀렉티비티(⊿⊿G), Radiolysis score, ADMET 독성 예측값, 반감기 예측값.
2. 각 지표에 대해 최소 통과 임계값(hard cutoff) 설정. 예: ⊿G ≤ SST14 레퍼런스, 셀렉티비티 ≥100×, Radiolysis-sensitive 잔기 ≤3개.
3. Hard cutoff 통과 후보에 대해 **가중 합산 스코어(weighted sum)** 또는 **Pareto front 방식**으로 순위 결정.
4. Critic Agent가 스코어링 결과를 자동 검증하고, Planner Agent가 다음 세대 후보 생성 규칙에 반영하도록 파이프라인 구성.

### 의도·범위·성공 기준
- **의도**: ⊿G 단일 의존 탈피 + 7단계 §4 Lead Compound 확정(3-4개) 도구
- **성공 기준**: PRST-001~004 도출 + 합성 의뢰서 작성
- **요청 분류**: 기능 + 연구

---

## ② 대응 방법 (Computer Science Method)

### 선택한 접근
- **Tier 시스템** (S/A/B/FAIL) — hard cutoff + weighted sum 하이브리드
- **ensemble_router** — 도메인별(L-AA/D-AA/cyclic/DOTA) Layer 라우팅
- **Critic Agent 자동 검증** + Planner Agent 피드백 루프

### 알고리즘·파이프라인
1. `composite_scorer.py` 가 입력 후보의 ⊿G, 셀렉티비티, Radiolysis score, ADMET, 반감기를 종합
2. Hard cutoff 통과 여부로 FAIL 분류
3. 통과 후보에 가중 합산 점수 부여 → Tier S/A/B 분류
4. Critic Agent (`AG_src/agents/critic.py`)가 결과 검증
5. Planner Agent가 다음 generation 변이 규칙에 반영

### 대안 / Trade-off
- **Pareto front** (회의록 §4 권고): 다목적 최적화 정통, 단 시각화·해석 ↑
- **Weighted sum**: 단순, 가중치 의존성·합치 가중 trap
- **NSGA-II/MOEA** (`[추정]`): DEAP/pymoo 라이브러리 활용 가능 §5 검증

---

## ③ 현재 구현된 기능 (근거 필수)

### 동작 코드
- `pipeline_local/scoring/composite_scorer.py` ([확인] Tier 시스템)
- `pipeline_local/scoring/ensemble_router.py` (Layer 라우팅)
- `pipeline_local/scoring/layer{1,2}_ensemble.py`
- `AG_src/agents/critic.py` (Critic Agent)
- `AG_src/agents/planner.py` (Planner Agent)

### 라이브 검증
- PRST-001~004 후보 4종이 Tier S로 도출됨 ([확인] PR #63 머지, `runs_local/dual_final_03/`)
- 단위 테스트 `test_composite_scorer.py` PASS

### 한계 (정직 명시)
- 🔴 **enrichment 경로 분리 격차** (audit §1.1 ①): `enrich_candidates_from_wrappers`가 `run_routed_halflife`를 호출하지 않음 — 3 reviewer 공통 확인
- 🔴 **PR #117 미머지** (ADMET divergence guard): Layer 2 R²=0.022 재학습 합의 후 머지 가능
- 🟡 **Layer 3 STUB**으로 DOTA 후보 종합 점수 일부 공백
- 🔴 **K-1/K-2 selectivity 결함**이 입력 신뢰성 위협 (본 점검 신규 발견)

### 데모 가능 여부
- 🟢 PRST-001~004 후보 페이지 (`/candidate/:id`) 라이브 시연 가능
- 🟡 enrichment 정합·Layer 3 보강은 다음 cycle 필요

---

## ④ AI Scientist 관점 결과 · 향후 방향 · 단기 목표

### 연구 관점 의미
- 약리학적으로 **단일 지표 의존 탈피**는 방사성의약품 후보 선정의 표준 — 본 시스템은 이를 framework로 구현
- 3-Layer Ensemble + Tier 시스템은 narrative v3 §5의 "한계 노출 framework" 정신과 부합

### 향후 방향 (§5 웹 검증)
- **Pareto front 시각화** — DEAP·pymoo (NSGA-II) `[추정]` §5 검증
- **Critic Agent 강화** — 자동 검증 규칙 추가 (`[추정]` GPT 기반 비평이 신뢰 가능한지 §5 papers 검증)
- **PR #117 머지** — Layer 2 재학습 합의 시 즉시

### 단기 목표 (다음 회의까지)
1. **PR #117 머지 결정** (단기 P0)
2. **enrichment 경로 정합** — Option A(코드를 narrative에 맞춤) vs B(narrative를 코드에 맞춤) 6월 결정
3. K-1/K-2 selectivity 정정 후 PRST-001~004 ranking 재검증

### `[확인]` vs `[추정]` 분리
- `[확인]` Tier 시스템 동작, PRST-001~004 Tier S 도출
- `[확인]` enrichment 분리 (audit 3 reviewer 공통)
- `[추정]` Pareto front 도입 효과 — §5 검증
- `[추정]` Critic Agent 추가 규칙 효과 — `확인 필요`

---

## ⑤ 한 줄 보고 요약
> Tier S/A/B/FAIL 복합 스코어링이 PR #62로 머지되어 PRST-001~004 도출에 사용되었으나, **PR #117 미머지 + enrichment 경로 분리 + Layer 3 STUB + K-1/K-2 selectivity 결함**으로 종합 점수의 입력 신뢰성을 6월 회의 전 보정해야 한다.

---

## 추적성 매핑
- 머지 PR: **#62** (Tier S/A/B/FAIL)
- 핵심 파일: `pipeline_local/scoring/composite_scorer.py`, `ensemble_router.py`, `AG_src/agents/critic.py`
- 점검 증거: `inspect_evidence/silo_b_docking.md` §3-Layer, audit `phase4-integration-and-refactor-plan.md` §1.1
- 회의록 출처: PDF p.4 §2.3, p.7 §4 A-04
- 관련 Action Item: A-02 (반감기), A-03 (ADMET), A-05 (레퍼런스), A-09 (Lead 선정 = §4)
