# A-09: 최종 후보 3-4개 도출 및 합성 의뢰 준비 (파이프라인 1차 완전 실행)

## 메타
- 회의: KAERI-AIRL-MOM-2026-003 (2026-04-06)
- 담당: AI팀 + RI팀 (합성 가능성 협의)
- 기한: 5월 회의 전
- 상태: **✅ 완료** (PR #63 머지, "최종 후보 4개 도출 + 합성 의뢰서 작성, Gate-2 진입 준비" — 2026-05-19)
- 비고: **A-04 복합 스코어링 체계 확립 후 착수**. MOM-002 A-10(킬레이터 벤더 선정)과 연동

### 실제 산출물 (2026-05-19 산출)
**합성 의뢰서 위치**: `runs_local/final_candidates/synthesis_orders/PRST-001~004.md` (후보별 개별 파일)

| 후보 ID | 서열 | Tier | WSS | ΔG (SSTR2, Boltz2) | ΔΔG vs SST-14 | Selectivity | II |
|--------|-----|------|-----|------------------|---------------|------------|-----|
| **PRST-001** | AGCKNIIWKTITSC | **S** | 1.000 | -105.5 REU | -10.5 (개선) | 250× (HEURISTIC) | 28.5 |
| **PRST-002** | (변형) | B | — | — | — | — | — |
| **PRST-003** | (변형) | B | — | — | — | — | — |
| **PRST-004** | (변형) | B | — | — | — | — | — |

> ⚠ **다양성 WARN**: 후보 4개 간 sequence identity 86~93%로 기준 80% **미달**. 14aa SS bond 제약(Cys3-Cys14) + 핵심 잔기(FWKT) 보존 요건으로 인해 불가피한 수렴. WARN으로 기록되었고, 다양성 강제 적용 시 후보 부족 발생.

> **신뢰도 한계 (각 의뢰서에 명시)**:
> - Selectivity 250×: dock score 차이 기반 HEURISTIC, 실측 Ki 상관 미검증
> - Stability half-life 4.5: HEURISTIC ranking score (`predict_half_life`), 실측 serum t½ 아님
> - ADMET 독성 0.10: pepADMET L-AA 기반, D-AA 미포함 시 적용 (절대값 신뢰도 LOW)

---

## 배경

회의에서 **최종 후보 3-4개를 빠르게 도출하여 합성 및 실험 진행** 필요성이 강조되었다.
전략 보고서 Gate-1(계산 스크리닝) 완료 → Gate-2(표지/제조 검증) 진입을 위한 핵심 마일스톤이다.

현재까지 파이프라인이 생성한 후보 라이브러리에 A-04 복합 스코어링을 적용하여
**Tier-S 후보 3-4개**를 확정하고, 합성 의뢰서를 작성해야 한다.

### Gate 구조 (전략 보고서)
```
Gate-1 (계산)
  └── A-04 복합 스코어링 → A-09 최종 후보 3-4개 확정
        ↓
Gate-2 (표지/제조)
  └── ¹⁷⁷Lu 표지 → RCP 측정 → 동물 실험
```

---

## 수행 방법 (단계별)

### Step 1 — 전체 후보 라이브러리에 복합 스코어링 적용
1. A-04의 `composite_scorer.py` 모듈 실행하여 현재까지 생성된 전체 후보에 WSS + Pareto front 적용.
2. Hard Cutoff 통과 후보 목록 추출 → `runs_local/final_candidates/hard_cutoff_pass.csv`.
3. Tier-S (WSS 상위 20% ∩ Pareto front) 후보 리스트업 → `runs_local/final_candidates/tier_s_candidates.csv`.

### Step 2 — 합성 가능성 평가 (RI팀 협의)
RI팀과 협의할 항목:

| 평가 항목 | 내용 | 담당 |
|----------|------|------|
| 비천연 아미노산 조달 | Nle, 5-F-Trp, Abu, Orn 등 국내 조달 가능성 | RI팀 |
| 고리화 전략 | Cys-Cys SS bond vs. Thioether/Lactam/Dicarba bridge | AI팀+RI팀 |
| 예상 합성 수율 | SPPS 수율 ≥ 20% 목표 | RI팀 |
| DOTA/DFO 킬레이터 접합 | N-말단 또는 Lys 측쇄 접합 위치 | RI팀 + A-10 연동 |

협의 결과를 `runs_local/final_candidates/synthesis_feasibility.md`에 기록.

### Step 3 — 최종 3-4개 확정 및 합성 의뢰서 작성

#### 최종 후보 선정 기준 (우선순위 순)
1. Tier-S 중 합성 가능성 평가 통과 후보 우선
2. Tier-A 중 합성 가능성 우수하고 Tier-S와 서열 다양성이 충분한 후보 보완
3. 최종 3-4개는 **서열 유사도 ≤ 80%** (다양성 보장)

#### 합성 의뢰서 항목 (누락 없음 — 수용 기준)
```
합성 의뢰서 필수 항목:
  1. 후보 ID (예: PRST-001 ~ PRST-004)
  2. 아미노산 서열 (single-letter code)
  3. 수식(modification) 위치 및 종류
     - N-말단: Ac (아세틸화) / H (자유 아민)
     - C-말단: NH2 (아미드화) / OH (자유 카복실)
     - 고리화: 위치(i, j) 및 결합 유형 (SS/thioether/lactam/dicarba)
     - DOTA/DFO 킬레이터: 접합 위치 (N-말단 vs Lys 측쇄)
     - 비천연 아미노산: 위치 및 코드 (예: Nle, Abu, Orn)
  4. 합성 순도 기준: ≥ 95% (HPLC)
  5. 납기: 협의 예정 (목표: 5월 회의 후 6주)
  6. 수량: 각 5–10 mg (in vitro 테스트 + 표지 실험 고려)
  7. 특이사항: 고리화 보호기 전략, 키랄 순도 요구사항
```

합성 의뢰서 출력 파일: `runs_local/final_candidates/synthesis_orders/PRST-001.md` ~ `runs_local/final_candidates/synthesis_orders/PRST-004.md`

> 이전 기획의 `runs_local/final_candidates/synthesis_request_<YYYYMMDD>.md` 단일 통합 파일은 생성되지 않았고, 후보별 개별 의뢰서 4개로 대체되었다.

---

## 판단 기준 / KPI

| 구분 | 지표 | 기준 |
|------|------|------|
| 최종 후보 수 | Gate-2 진입 후보 | 3-4개 |
| 서열 다양성 | 후보 간 유사도 | ≤ 80% |
| 합성 의뢰서 완성도 | 누락 항목 | 0개 |
| 합성 가능성 | RI팀 협의 완료 | 전원 통과 |
| 후속 RCP 기준 | 72시간 HPLC RCP | ≥ 90% (실험 검증) |

### 7단계 다단계 선별 체계 매핑

| A-09 단계 | 7단계 선별 체계 단계 |
|----------|------------------|
| Step 1 (복합 스코어링 적용) | (1)~(3): Specificity + Stability + Toxicity 통과 후보 취합 |
| Step 1 (Tier-S 선정) | (4) Lead Compound 확정 |
| Step 2 (수식/고리화 전략) | (5) Amino Acid Modification 입력 준비 |
| Step 3 (합성 의뢰서) | Gate-2 → (6) RI 표지 후 MD Simulation 준비 |

---

## 활용 도구 / 알고리즘

| 도구 | 용도 |
|------|------|
| `pipeline_local/scoring/composite_scorer.py` (A-04 구현) | WSS + Pareto front 적용 |
| `pharmacology_guards.py` | 최종 약리학 KPI 재확인 |
| 합성 의뢰서 Markdown 템플릿 | 표준 의뢰 양식 출력 |
| MOM-002 A-10 킬레이터 벤더 리스트 | DOTA/DFO 조달 연동 |

---

## 서호성 박사 의견

- 최종 후보는 **합성 가능성**이 계산 점수만큼 중요 — RI팀과 사전 협의 없이 합성 의뢰서 발송 금지.
- **Radiolysis 72시간 기준**: 계산 단계에서 `radiolysis_score` ≤ 3이 통과 기준이나,
  실험에서 72시간 RCP ≥ 90% 미달 시 Step 5(Amino Acid Modification) 재진입.
- **Quencher 전략** (QC-1~QC-4)을 합성 의뢰서에 함께 기재하여 표지 실험 시 즉시 적용 가능하도록 준비.
- DOTA vs DFO 선택: ¹⁷⁷Lu 표지에는 **DOTA 우선**, ⁶⁸Ga PET는 DOTA/DFO 모두 가능.

---

## 본 프로젝트 매핑

- **실제 산출물 (2026-05-19 확인)**:
  - `runs_local/final_candidates/synthesis_orders/PRST-001.md` (8.7KB) — Tier-S 합성 의뢰서
  - `runs_local/final_candidates/synthesis_orders/PRST-002.md` (6.2KB) — Tier-B 합성 의뢰서
  - `runs_local/final_candidates/synthesis_orders/PRST-003.md` (6.6KB) — Tier-B 합성 의뢰서
  - `runs_local/final_candidates/synthesis_orders/PRST-004.md` (6.1KB) — Tier-B 합성 의뢰서
  - `runs_local/final_candidates/tier_s_candidates.csv` — Tier-S 후보 표 ✅
  - `runs_local/final_candidates/tier_b_candidates.csv` — Tier-B 후보 표 ✅
  - `runs_local/final_candidates/hard_cutoff_pass.csv` — Hard Cutoff 통과 목록 ✅
  > ⚠ 이전 기획의 `synthesis_request_YYYYMMDD.md` 단일 통합 파일은 생성되지 않음 — 후보별 개별 파일로 대체됨
- **기존 연동**:
  - `pipeline_local/scripts/composite_scorer.py` (A-04 구현 결과)
  - `pipeline_local/scripts/pharmacology_guards.py` — 최종 약리학 가드 재검증
  - `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/pipeline/` — Critic/Planner Agent

---

## 의존성 / 연관 액션 아이템

| 관계 | 액션 아이템 | 내용 |
|------|-----------|------|
| **선행 필수** | **A-04** | 복합 스코어링 체계 확립 |
| 연동 필수 | **MOM-002 A-10** | DOTA/DFO 킬레이터 벤더 선정 |
| 참고 | **A-02** | 반감기 예측 (합성 의뢰서 기재) |
| 참고 | **A-03** | ADMET 독성 (합성 의뢰서 기재) |
| 참고 | **A-05** | SST14 ΔG 기준선 (Hard Cutoff) |
| 후행 | Gate-2 실험 | ¹⁷⁷Lu 표지 → HPLC RCP 72h 측정 |
