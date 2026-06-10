# A-04 복합 스코어링 모듈 구현 보고서

**작성일**: 2026-05-19
**작성자**: engineer-backend
**PR**: https://github.com/AI-scientist4BIO/SST14-M_scr/pull/62
**브랜치**: feat/a04-composite-scoring

---

## 1. 작업 요약

A-04 액션 아이템(KAERI-AIRL-MOM-2026-003 §Step 3~4)에 따라 복합 스코어링 모듈을 신규 구현했다.

### 신규 파일

| 파일 | 역할 |
|------|------|
| `pipeline_local/scoring/composite_scorer.py` | WSS + Pareto front + Tier 분류 엔진 |
| `pipeline_local/scoring/radiolysis_scorer.py` | ¹⁷⁷Lu Radiolysis 민감도 점수 |
| `pipeline_local/scoring/__init__.py` | scoring 패키지 Public API |
| `pipeline_local/scripts/composite_scorer.py` | CompositeScorer 클래스 (scripts 진입점) |
| `pipeline_local/scripts/composite_scorer_cli.py` | CLI 진입점 (smoke test 내장) |
| `pipeline_local/tests/test_composite_scorer.py` | 34개 단위 테스트 |

### 변경 파일

| 파일 | 변경 내용 |
|------|---------|
| `pipeline_local/scripts/pharmacology_guards.py` | `SST14_SSTR2_ref_ddg_boltz2` LITERATURE_VALUES 등록 (Stage 5 의무) |

---

## 2. Hard Cutoff 5게이트 (A-04 §Step 2)

| 게이트 | 지표 | 기준 | 필드 |
|-------|------|------|-----|
| Gate 1 | ΔG SSTR2 | ≤ -95.024 REU | `dg_max` (pharmacology_guards 자동 조회) |
| Gate 2 | 셀렉티비티 | ≥ 100× | `selectivity_min` |
| Gate 3 | Radiolysis 민감 잔기 수 | ≤ 3개 | `radiolysis_max` |
| Gate 4 | ADMET 독성 확률 | ≤ 0.3 | `admet_tox_max` |
| Gate 5 | Instability Index | < 40 | `instability_max` |

SST-14 레퍼런스 ΔG(-95.024 REU)는 pharmacology_guards.py LITERATURE_VALUES에서 자동 조회한다. A-05 미완료 시 `dg_max=None` soft mode로 스킵 가능하다.

---

## 3. WSS 가중치 (합 = 1.0, A-04 §Step 3 방식 A)

| 지표 | 가중치 | 정규화 방향 |
|------|--------|-----------|
| dg | 0.35 | invert (낮을수록 좋음) |
| selectivity | 0.25 | 높을수록 좋음 |
| half_life | 0.20 | 높을수록 좋음 |
| admet_safety (= 1 - admet_tox) | 0.10 | invert |
| radiolysis_safety | 0.10 | invert |

가중치는 생성자 파라미터 또는 CLI `--weights` JSON으로 외부 주입 가능하다.

---

## 4. Pareto Front (A-04 §Step 3 방식 B)

pymoo 미설치 환경을 위한 독립 구현:
- `pareto_nondominated_sort()`: O(n²M) 비지배 정렬
- 목적 함수(최소화): `[dg, -selectivity, -half_life, admet_tox, radiolysis_count]`
- 후보 수 ≥ 2 시 계산, < 10 시 경고 출력

---

## 5. Tier 분류 (A-04 §Step 3 최종 순위 결정)

| Tier | 조건 |
|------|------|
| S | WSS 상위 20% AND Pareto rank=1 |
| A | WSS 상위 20% XOR Pareto rank=1 |
| B | 나머지 Hard Cutoff 통과 후보 |
| FAIL | Hard Cutoff 미통과 |

---

## 6. Radiolysis 민감도 (서호성 박사 제안, A-04)

| 잔기 | 민감도 | 점수/개 |
|------|--------|--------|
| Cys, Met | 최고 | 3 |
| Phe, Tyr, Trp | 높음 | 2 |
| Pro, His, Leu | 낮음 | 1 |

**SST-14 실측**: AGCKNFFWKTFTSC → Cys3+Cys14(SS bond 제외) 후 F×3 + W×1 = 민감 잔기 4개

Hard Cutoff는 민감 잔기 개수 ≤ 3(점수 합 아님). SST-14 자체는 Gate 3 탈락(4개)이므로 수식 변형 후보 대상임.

---

## 7. Smoke Test 결과

```
후보: 11개 (mock 데이터, dg 단위 REU)
Tier S:    1개  (PRST-001: dg=-105.5, sel=250, hl=4.5)
Tier B:    5개
Tier FAIL: 5개  (각 FAIL-sel/FAIL-admet/FAIL-instab/FAIL-radiolysis/missing-admet)
```

저장 파일:
- `runs_local/final_candidates/tier_s_candidates.csv`
- `runs_local/final_candidates/hard_cutoff_pass.csv`
- `runs_local/final_candidates/summary.json`

---

## 8. 테스트 결과

```
pipeline_local/tests/test_composite_scorer.py: 34/34 통과
pipeline_local/tests/test_pharmacology_guards.py: 39/39 통과
합계: 73/73 통과
```

주요 테스트 케이스:
- TC-01~05: Hard Cutoff 5게이트 각각 통과/탈락 경계값 검증
- TC-06~07: WSS 가중치 합 = 1.0, min-max 정규화 검증
- TC-08~10: Tier S/B/FAIL 분류 검증
- TC-11: SST-14 Radiolysis 실측값(민감 잔기 4개) 확인
- TC-13: Critic Agent 플래그 (통과율 < 5% 경고)
- TC-15: pharmacology_guards SST14 ref_ddg 로드 검증

---

## 9. pharmacology_guards.py 등록 (Stage 5)

LITERATURE_VALUES에 신규 항목 등록:

```python
"SST14_SSTR2_ref_ddg_boltz2": {
    "ref_ddg_reu": (
        -95.024,
        "KAERI-AIRL P0 commit ed86fa0 (2026-03, SSTR2 PDB 7XMS)",
        "SST14 AGCKNFFWKTFTSC vs SSTR2 Boltz2 dock ΔG 레퍼런스. "
        "A-04 Hard Cutoff 기준선: candidate.ddg ≤ -95.024 REU 통과.",
    ),
},
```

---

## 10. HEURISTIC 주의 사항 (H-06 가드)

이 모듈의 WSS/Pareto 스코어는 **ranking 도구**이며 임상 판단을 대체하지 않는다:
- half_life: heuristic ranking score (실측 PK 아님)
- admet_tox: pepADMET P3 등급 (SSTR2 환형 펩타이드 OOD 예측)
- selectivity: dock_score 차이 기반 (실측 Ki 상관 미검증, M5-P4)

---

## 11. A-09 연동

출력 CSV가 A-09 최종 후보 선정 입력으로 사용된다:
- `runs_local/final_candidates/tier_s_candidates.csv` → A-09 합성 의뢰서 초안
- `runs_local/final_candidates/all_candidates.csv` → 전체 랭킹

---

## 12. 미완료/후속 작업

| 항목 | 상태 | 비고 |
|------|------|------|
| NSGA-II pymoo 활성화 | OPEN | pymoo 설치 후 후보 ≥ 50 시 자동 활성 |
| Tier C 분류 | OPEN | 현재 spec은 S/A/B/FAIL 4단계. orchestrator 요청 시 C 추가 |
| reviewer-math NSGA-II 수렴 검증 | OPEN | 실 후보 데이터로 검증 필요 |
| Pareto front 시각화 | OPEN | `pareto_front.png` 생성 CLI 옵션 추가 예정 |
