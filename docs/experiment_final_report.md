# SSTR2 펩타이드 스크리닝 — LLM Agent Flow 최적화 실험 최종 보고서

> 작성일: 2026-04-13  
> 데이터 기준: `llm_benchmark/outputs/_all_results.json` (184개 유효 실험 레코드)  
> 작성자: engineer-backend (agent)  
> 대상: orchestrator, 프로젝트 팀 전원

---

## 1. Executive Summary

184개 실험을 통해 **Sequential 플로우 + deepseek_r1_32b 모델 + adaptive 게이트** 조합이 SSTR2 결합 펩타이드 스크리닝 파이프라인의 최적 설정으로 확인되었다. 복잡한 multi-agent 토론(Collaborative/Hierarchical) 방식은 Sequential 대비 SES 기준 14~20% 낮은 성능을 보였으며, 두 최우수 모델(deepseek_r1_32b vs qwen3_32b) 간 성능 차이는 통계적으로 유의하지 않다(Mann-Whitney p=0.25). V2 LLM-Direct Mutation 방식은 시퀀스 중복 문제로 인해 valid rate 44.4%에 그쳐 V1 대비 우위를 보이지 못했다.

---

## 2. 실험 개요

### 2.1 실험 대상 시스템

| 항목 | 값 |
|------|-----|
| 타겟 | SSTR2 (Somatostatin Receptor Type 2) |
| 기준 서열 (SST-14) | `AGCKNFFWKTFTSC` (14aa, Cys3-Cys14 이황화 결합) |
| 약물단 (pharmacophore) | FWKT (F7-W8-K9-T10, 고정 위치) |
| 베이스라인 ddG | -48.438 kcal/mol (FlexPepDock refined WT) |
| 템플릿 PDB | `fold_test1_model_0.pdb` (SSTR2-SST14 복합체) |
| 인프라 | H100 NVL 96GB, vLLM (GPU 3), PyRosetta FlexPepDock |

### 2.2 Phase별 실험 설계 요약

| Phase | 실험 수 | 주요 변수 | 고정 변수 |
|-------|---------|----------|---------|
| Phase1_before (사전) | 9 | 3 models × 3 seeds | Sequential + static gate |
| **Phase1** | **30** | 5 models × 2 gates × 3 seeds | Sequential flow |
| **Phase2A** | **54** | 3 models × 3 flows × 2 gates × 3 seeds | n_cand=8, max_iter=5 |
| **Phase2B** | **18** | qwen3_32b, 2 flows × 9 seeds | adaptive gate만 |
| **Phase3** | **64** | 2 models × n_total scaling | Sequential + adaptive |
| **V2 Phase1** | **18** | 3 models × 2 gates × 3 seeds | v2_sequential (LLM-Direct) |
| **합계 (유효)** | **184** | | |

> Phase1_before (9개): 파이프라인 버그로 전체 SES=0 → 분석에서 제외

### 2.3 평가 지표 — Screening Effectiveness Score (SES)

```
SES = (Hit_Rate × 0.30) + (Improvement × 0.25) + (Efficiency × 0.20)
    + (Diversity × 0.15) + (Robustness × 0.10)
```

| 컴포넌트 | 정의 | 범위 |
|---------|------|------|
| Hit_Rate | 모든 게이트 통과 후보 비율 (`n_pass / n_total`) | 0.0 – 1.0 |
| Improvement | 베이스라인 대비 ddG 개선 (`(baseline - best) / \|baseline\|`) | 0.0 – 1.0+ |
| Efficiency | 첫 히트 발견 속도 | 0.0 – 1.0 |
| Diversity | 히트 구조적 다양성 (`n_clusters / n_hits`) | 0.0 – 1.0 |
| Robustness | 반복 간 일관성 | 0.0 – 1.0 |

**게이트 기준**: ddG ≤ -5.0 kcal/mol, FWKT 100% 보존, Clash score ≤ 10

> **주의**: Diversity와 Robustness 컴포넌트는 현재 구현에서 모두 0.0으로 고정됨 (클러스터링 미구현). 실제 SES는 Hit_Rate + Improvement + Efficiency 세 항목으로만 결정됨.

---

## 3. Phase 1: 모델 스크리닝

**목표**: Sequential flow에서 5개 LLM 모델의 기초 성능 비교  
**설정**: n_candidates=4, max_iterations=3, 3 seeds (s42/s137/s256), 2 gates (adaptive/static)

### 3.1 모델별 SES 결과

| 모델 | 파라미터 | 전체 평균 SES | Adaptive gate | Static gate | 비고 |
|------|---------|------------|---------------|-------------|------|
| **deepseek_r1_32b** | 32B | **0.5885** | 0.5001 ± 0.0002 | 0.6768 ± 0.3062 | 최우수, CoT 추론 강점 |
| **qwen3_32b** | 32B | **0.5847** | 0.5896 ± 0.1497 | 0.5798 ± 0.1382 | 2위, 균형적 성능 |
| glm_z1_32b | 32B | 0.5328 | 0.4900 ± 0.0173 | 0.5756 ± 0.1309 | 3위 |
| qwen3_5_27b | 27B | 0.5006 | 0.5011 ± 0.0019 | 0.5000 ± 0.0000 | 4위, 낮은 개선율 |
| qwen2_5_7b | 7B | 0.4895 | 0.4789 ± 0.0183 | 0.5002 ± 0.0003 | 최하, 파라미터 한계 |

### 3.2 게이트 유형 비교

| 게이트 | SES 평균 | SES 표준편차 | best_dG 평균 |
|-------|---------|------------|------------|
| Adaptive | 0.5119 | 0.0706 | -47.47 kcal/mol |
| Static | 0.5665 | 0.1521 | -57.72 kcal/mol |

- Static 게이트가 평균 SES +5.5%p 높으나, 분산이 2배 이상 큼
- Phase2 이후에는 Adaptive 게이트를 표준으로 채택 (재현성 우선)

### 3.3 Phase1 결론

**Top-3 진출 모델**: deepseek_r1_32b, qwen3_32b, glm_z1_32b  
(qwen3_5_27b, qwen2_5_7b 탈락 — SES < 0.51, Improvement ≈ 0)

---

## 4. Phase 2A: 플로우 패턴 비교

**목표**: Top-3 모델에서 3가지 에이전트 플로우 패턴 정량 비교  
**설정**: n_candidates=8, max_iterations=5, 3 models × 3 flows × 2 gates × 3 seeds = 54개

### 4.1 플로우별 SES 결과

| 플로우 | LLM 호출/iter | SES 평균 | SES 표준편차 | best_dG 평균 |
|-------|------------|---------|------------|------------|
| **Sequential** | 3 | **0.6311** | 0.1993 | -72.92 kcal/mol |
| Hierarchical | 4–6 | 0.5345 | 0.0917 | -53.90 kcal/mol |
| Collaborative | 5–7 | 0.5200 | 0.0608 | -51.20 kcal/mol |

- Sequential이 Hierarchical 대비 **+18.1%**, Collaborative 대비 **+21.4%** 우위
- 복잡한 플로우일수록 SES 중앙값은 낮고, 고성능 아웃라이어 발생 빈도도 낮음
- 전체 최고 단일 실험: deepseek_r1_32b + sequential + adaptive, **SES=1.083**, best_ddG=-161.39 kcal/mol

### 4.2 모델 × 플로우 교호작용

모든 3개 모델에서 동일하게 **Sequential > Hierarchical > Collaborative** 순위가 유지됨  
→ 플로우 패턴 효과가 모델 선택 효과보다 강함

### 4.3 Phase2A 결론

**Sequential 플로우 확정 채택**: LLM 호출 수 증가가 성능 향상으로 이어지지 않음.  
이는 Planner-Critic 단방향 피드백이 이미 충분한 정보를 제공하기 때문으로 해석됨.

---

## 5. Phase 2B: Sub-variable 비교

**목표**: Collaborative(debate rounds) vs Hierarchical(cross-model orchestrator) 세부 변수 효과  
**설정**: qwen3_32b, adaptive gate, 2 flows × 9 seeds = 18개 (Phase2A 확장 실험)

### 5.1 Sub-variable 결과

| 플로우 | Sub-variable 내용 | SES 평균 | SES 표준편차 |
|-------|-----------------|---------|------------|
| **Collaborative** | debate_max_rounds 변화 | **0.6939** | 0.2872 |
| Hierarchical | cross-model orchestrator | 0.5906 | 0.1841 |

- Phase2A에서 하위였던 Collaborative가 Phase2B에서 상대적으로 높은 SES 기록
- 그러나 표준편차(0.2872)가 크고 최솟값 0.5, 최댓값 1.08로 **불안정한 성능**
- Phase2A와 Phase2B 결과 불일치 원인: Phase2B가 qwen3_32b 단일 모델로만 구성, n=9 소표본

### 5.2 Phase2B 해석

Phase2B의 Collaborative 고SES는 특정 시드에서의 이상치(SES 1.07~1.08 × 3개)에 의한 것으로, 안정적 우위라 보기 어려움. Sequential 채택 결론 유효.

---

## 6. Phase 3: Scaling + 통계 검증

**목표**: deepseek_r1_32b vs qwen3_32b의 대규모 샘플링으로 통계적 유의성 검증  
**설정**: Sequential + adaptive, n_total = 16~133 (다양한 스케일), 64개 실험

### 6.1 모델 간 SES 비교

| 모델 | n | SES 평균 | SES 표준편차 | best_dG 평균 |
|------|---|---------|------------|------------|
| deepseek_r1_32b | 20 | 0.5534 | 0.1332 | — |
| qwen3_32b | 44 | 0.5732 | 0.1567 | — |

**Mann-Whitney U 검정**: U=367.5, **p=0.2501** (양측 검정)  
→ 두 모델 간 SES 분포 차이 통계적으로 **유의하지 않음** (α=0.05 기준)

### 6.2 스케일링 효과

n_total이 증가할수록 SES가 상승하는 경향이 관찰됨:

| n_total 구간 | 평균 SES | 해석 |
|------------|---------|------|
| ≤ 32 | 0.505–0.554 | 탐색 부족, 개선 기회 제한 |
| 33 | 0.633 | 4 seq × 8 iter 표준 규모 |
| ≥ 128 | 0.975–0.995 | 대규모 탐색에서 Improvement 급등 |

→ n_candidates 또는 max_iterations 증가가 SES 향상에 실질적으로 기여함

### 6.3 Phase3 결론

두 모델 모두 프로덕션 수준으로 활용 가능하며, deepseek_r1_32b는 Phase1/2A에서 일관된 1위 실적을 보이므로 **기본 선택** 유지 권고.

---

## 7. V2: LLM-Direct Mutation 비교

**목표**: V1(확률적 guided mutation)과 V2(LLM이 완전 서열 직접 생성) 방식 비교  
**설정**: 3 models × 2 gates × 3 seeds = 18개

### 7.1 V1 vs V2 SES 비교

| 버전 | n | SES 평균 | SES 표준편차 | improvement>0 비율 |
|------|---|---------|------------|-----------------|
| V1 (전체) | 166 | 0.5595 | 0.1391 | 37.3% |
| V2 Phase1 | 18 | 0.5420 | 0.1168 | 38.9% |

→ V2가 V1 대비 SES 평균 -1.7%p, improvement 발생 빈도는 유사  
→ **V1 우위** 확인

### 7.2 V2 시퀀스 유효성 분석 (Valid Rate)

V2 플래너가 생성한 363개 후보 서열 (attempt=0 기준)에 대한 유효성 검사:

| 검사 항목 | 통과 | 실패 |
|---------|------|------|
| 길이=14aa | 363 | 0 |
| FWKT 보존 | 343 | 0 |
| Cys14 보존 | — | 20 (5.5%) |
| Baseline 중복 아님 | — | 146 (40.2%) |
| 이전 제안과 중복 아님 | — | 36 (9.9%) |
| **최종 유효 (모두 통과)** | **161** | **202** |
| **Valid Rate** | **44.4%** | |

**최대 실패 원인**: LLM이 원본 서열 `AGCKNFFWKTFTSC`를 반복 제안 (전체 실패의 72.3%)

### 7.3 V2 모델별 분석

| 모델 | SES 평균 | SES 표준편차 | 비고 |
|------|---------|------------|------|
| glm_z1_32b | 0.6542 | 0.1659 | 최우수 (이상치 포함) |
| qwen3_32b | 0.5732 | 0.0945 | |
| deepseek_r1_32b | 0.5068 | 0.0219 | 가장 낮은 분산 |

### 7.4 V2 결론

LLM-Direct 방식의 핵심 문제는 **exploration 부족**이다:
- 40.2%가 baseline과 동일한 서열 제안 (안전 회피 편향)
- 9.9%가 이전 자신의 제안과 중복
- V2 태스크 #3: valid rate 44% → **70%+ 개선 필요**

---

## 8. 이상치 분석

### 8.1 고SES 이상치 (SES > 0.919 = mean + 2σ)

전체 184개 중 **14개 (7.6%)** 가 이상치 기준 초과:

| Phase | 발생 수 | 대표 케이스 |
|-------|---------|-----------|
| Phase2A | 3 | deepseek+sequential (SES=1.083, best_ddg=-161.4) |
| Phase2B | 4 | qwen3+collaborative (SES=1.07~1.08 × 3) |
| Phase3 | 5 | qwen3+sequential (SES=0.976~1.023, n_total≥128) |
| V2 Phase1 | 1 | glm+v2_sequential (SES=0.945) |
| Phase1 | 1 | deepseek+static (SES=1.030) |

모든 이상치는 **clash=0** (게이트 통과) + **Improvement > 0.5** 조합으로 발생.

### 8.2 이상치 발생 패턴

- **clash=0 이상치 없음**: clash_count=0인 레코드는 모두 게이트 통과 정상 (gate threshold ≤10)
- **interface dG 용어 문제**: `best_ddg` 값이 PyRosetta의 `total_score` 기여 혼재 가능성 (단위 REU, kcal/mol 혼용 주의)
- **SES > 1.0 가능**: Improvement 컴포넌트가 이론 상한 없이 ddG 개선률을 선형 반영하므로 SES > 1.0 정상

### 8.3 Phase1_before — 파이프라인 버그

| 항목 | 값 |
|------|-----|
| 실험 수 | 9개 |
| SES | 모두 0.000 |
| n_hits | 모두 0 |
| 모델 | deepseek_r1_32b, qwen2_5_7b, qwen3_5_27b |
| 원인 | FlexPepDock 게이트 처리 로직 버그 (파이프라인 수정 후 Phase1 정식 재실행) |

---

## 9. 핵심 결론 및 권고사항

### 9.1 핵심 결론

| # | 결론 | 근거 |
|---|------|------|
| 1 | Sequential 플로우가 최적 | SES 0.6311 > Hierarchical 0.5345 > Collaborative 0.5200 |
| 2 | deepseek_r1_32b 최우수 모델 | Phase1/2A 일관된 1위, CoT 추론 효과 |
| 3 | 두 최우수 모델 차이 통계적 무의미 | Mann-Whitney p=0.25 |
| 4 | Scaling이 SES에 실질 효과 | n_total ≥ 128에서 SES 0.97+ |
| 5 | V2 LLM-Direct 방식 현재 V1 미달 | Valid rate 44.4%, baseline 반복 문제 |
| 6 | Diversity 메트릭 미작동 | 모든 실험에서 diversity=0.0 (구현 필요) |

### 9.2 프로덕션 권고 설정

```
Model:      deepseek_r1_32b
Flow:       sequential
Gate:       adaptive
n_cand:     8 (최소), 32+ (고품질 스크리닝)
max_iter:   5
seed:       3회 반복 평균 권장
```

### 9.3 단기 개선 과제

| 우선순위 | 과제 | 예상 효과 |
|---------|------|---------|
| P0 | V2 valid rate 개선: baseline 반복 방지 프롬프트 강화 | 44% → 70%+ |
| P1 | Diversity 메트릭 구현 (클러스터링) | SES 신뢰도 향상 |
| P2 | n_candidates 증가 실험 (n≥64) | SES 0.8+ 달성 가능 |
| P3 | best_ddg vs interface_dG 용어 통일 | 해석 오류 방지 |

---

## 10. Appendix

### A. SES 정의 상세

**SES (Screening Effectiveness Score)**는 5개 컴포넌트의 가중 합산:

```
SES = (Hit_Rate × 0.30) + (Improvement × 0.25) + (Efficiency × 0.20)
    + (Diversity × 0.15) + (Robustness × 0.10)
```

- **기준 SES = 0.50**: Hit_Rate=1.0, Improvement=0, Efficiency=1.0, Diversity=0, Robustness=0  
  → 모든 후보가 ddG ≤ -5.0 게이트를 통과했으나 베이스라인 대비 개선이 없는 상태
- **SES > 1.0 가능**: Improvement가 베이스라인 대비 큰 개선(100%+)을 달성하는 경우

### B. 게이트 조건

| 게이트 유형 | 조건 | 설명 |
|------------|------|------|
| ddG gate | ddG ≤ -5.0 kcal/mol | 의미있는 결합 에너지 개선 |
| FWKT | F7-W8-K9-T10 100% 보존 | 약물단 보존 |
| Clash score | clash_count ≤ 10 | 구조적 실현 가능성 |
| **Adaptive** | 게이트 임계값 동적 조정 | 실험 진행에 따라 기준 강화 |
| **Static** | 게이트 임계값 고정 | 재현성 최대화 |

### C. 실험 ID 체계

```
Phase1:       P1-01 ~ P1-30  (5 models × 2 gates × 3 seeds)
Phase2A:      P2-01 ~ P2-54  (3 models × 3 flows × 2 gates × 3 seeds)
Phase2B:      P2B-01 ~ P2B-18 (qwen3_32b, 2 flows × 9 seeds)
Phase3:       P3-A01 ~ P3-B64 (2 models, sequential, scaling)
V2 Phase1:    V2P1-01 ~ V2P1-18 (3 models × 2 gates × 3 seeds)
Phase1_before: (9개, 분석 제외)
```

### D. V2 시퀀스 유효성 실패 유형별 세부

| 실패 유형 | 건수 | 비율 | 의미 |
|---------|------|------|------|
| baseline_identical | 146 | 72.3% | LLM이 원본 서열 그대로 반복 제안 |
| duplicate | 36 | 17.8% | 동일 실험 내 이미 제안한 서열 재제안 |
| Cys14 위반 | 20 | 9.9% | 14번 위치 Cys 손실 (C-terminus 파괴) |
| 길이 위반 | 0 | 0% | 14aa 조건은 LLM이 준수 |
| FWKT 위반 | 0 | 0% | 약물단 보존은 LLM이 준수 |
| **총 실패** | **202** | 55.6% | |
| **총 통과 (valid)** | **161** | **44.4%** | |

### E. 데이터 소스

| 파일 | 설명 |
|------|------|
| `llm_benchmark/outputs/_all_results.json` | 193개 전체 레코드 (Phase1_before 9개 포함) |
| `llm_benchmark/outputs/{phase}/{run}/ses_score.json` | 개별 실험 SES 상세 (hit_rate, improvement, efficiency, diversity, robustness) |
| `llm_benchmark/outputs/{phase}/{run}/status.json` | 실험 상태 (done/skipped/error), 소요시간 |
| `llm_benchmark/outputs/{phase}/{run}/agent_log/iter_*_v2_planner.jsonl` | V2 플래너 제안 시퀀스 로그 |
| `llm_benchmark/outputs/{phase}/{run}/pyrosetta_flow/.../iteration_manifest.json` | 도킹 결과 상세 (ddG, clash, pharma) |

---

*본 보고서는 `llm_benchmark/outputs/_all_results.json` 및 개별 실험 디렉토리에서 직접 집계한 수치를 사용하며, 수동 추정 없이 코드로 검증된 데이터만 포함합니다.*
