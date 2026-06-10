# Claude Code 실행 프롬프트 — A-04: 복합 스코어링 체계 설계·구현

## 사용 방법

Claude Code CLI에서 아래 **컨텍스트 섹션을 포함하여** 대화를 시작한다:

```
# 아래 파일들을 먼저 읽어라
@CLAUDE.md
@docs/meet_log/2026-04-06_action_items/A-04_composite_scoring.md
@pipeline_local/scripts/pharmacology_guards.py
@pipeline_local/strategies/blosum.py
@pipeline_local/steps/step05b_selectivity.py

# 그 다음 아래 작업 정의를 실행하라
```

---

## 컨텍스트

| 파일 | 역할 |
|------|------|
| `@CLAUDE.md` | 프로젝트 행동 규칙, 위임 의사결정 트리 |
| `@docs/meet_log/2026-04-06_action_items/A-04_composite_scoring.md` | A-04 액션 아이템 상세 — Hard Cutoff·가중치·Radiolysis 기준 |
| `회의록: docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf` | 원문 (§2.5 7단계 선별 체계, Radiolysis 전략) |
| `@pipeline_local/scripts/pharmacology_guards.py` | Stage 5 약리학 가드 — Instability/GRAVY/Boman 기존 구현 |
| `@pipeline_local/steps/step05b_selectivity.py` | 셀렉티비티 입력 데이터 형식 참조 |
| `@pipeline_local/strategies/blosum.py` | BLOSUM 변이 전략 (Radiolysis 수정과 연동 예정) |
| `7단계 선별 체계` | A-04 정리 파일 §"7단계 다단계 선별 체계 매핑" 참조 |

---

## 작업 정의

### 목표
`pipeline_local/scripts/` 내에 **복합 스코어링 모듈 2개**를 신규 구현한다:
1. `composite_scorer.py` — WSS(Weighted Sum Score) + Pareto front 스코어링 엔진
2. `radiolysis_scorer.py` — Radiolysis 민감도 점수 산출기

### 세부 구현 요구사항

#### composite_scorer.py
```python
# 필수 public API
class CompositeScorer:
    def __init__(self, weights: dict | None = None, hard_cutoffs: dict | None = None): ...
    
    def score(self, candidates: list[dict]) -> pd.DataFrame:
        """
        입력: 후보 list[dict] — 각 dict에 dg, selectivity, half_life, admet_tox, radiolysis_count 포함
        출력: DataFrame with columns [candidate_id, wss, pareto_rank, tier]
              tier: "S" | "A" | "B" | "FAIL" (Hard Cutoff 미통과)
        """
    
    def pareto_front(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """NSGA-II 기반 비지배 해집합 반환 (pymoo 사용)"""
    
    def explain(self, candidate_id: str) -> dict:
        """스코어 기여도 분해 — 각 지표별 가중치 기여 반환"""
```

기본 Hard Cutoff 값:
```python
DEFAULT_HARD_CUTOFFS = {
    "dg_max": None,          # A-05 결과 주입 (기본값: SST14 ref ΔG)
    "selectivity_min": 100.0, # 100× 이상
    "radiolysis_max": 3,      # 민감 잔기 ≤ 3개
    "admet_tox_max": 0.3,     # 독성 확률 ≤ 0.3
    "instability_max": 40.0,  # Guruprasad 기준
}

DEFAULT_WEIGHTS = {
    "dg": 0.35,
    "selectivity": 0.25,
    "half_life": 0.20,
    "admet_safety": 0.10,  # 1 - admet_tox
    "radiolysis_safety": 0.10,  # 1 - normalized(radiolysis_count)
}
```

#### radiolysis_scorer.py
```python
# 필수 public API
RADIOLYSIS_SCORES = {
    "C": 3, "M": 3,          # Cys, Met — 최고 민감도
    "F": 2, "Y": 2, "W": 2,  # Phe, Tyr, Trp — 높음
    "P": 1, "H": 1, "L": 1,  # Pro, His, Leu — 중간
}

class RadiolysisScorer:
    def score_sequence(self, sequence: str, ss_bond_positions: tuple[int,int] | None = None) -> dict:
        """
        입력: 아미노산 서열 (single-letter), SS bond 위치 (0-indexed, 선택)
        출력: {
            "sensitive_count": int,       # 민감 잔기 개수 (SS bond 제외)
            "total_score": float,         # 가중 점수 합계
            "sensitive_residues": list,   # [(위치, 잔기, 점수)] 리스트
            "ss_bond_intact": bool,       # SS bond 위치 명시 시 True/False
            "pass_cutoff": bool,          # sensitive_count ≤ 3
        }
        """
```

SST-14 레퍼런스 처리:
- 서열: `AGCKNFFWKTFTSC` (Cys3-Cys14 SS bond, 0-indexed: (2, 13))
- Cys3, Cys14는 `ss_bond_positions=(2,13)` 전달 시 `sensitive_count`에서 제외
- FWKT pharmacophore (F7, W8, K9, T10) 보존 여부를 별도 필드로 표시

---

## 입력 (Input Spec)

```json
// 후보 1개 예시 (NDJSON 또는 list[dict])
{
  "candidate_id": "PRST-001",
  "sequence": "AGCKNFFWKTFTSC",
  "dg": -8.5,
  "selectivity": 150.0,
  "half_life": 2.5,
  "admet_tox": 0.15,
  "radiolysis_count": 2,
  "instability_index": 35.2
}
```

CSV 형식도 지원 — pandas DataFrame으로 입력 가능.

---

## 출력 (Output Spec)

```python
# composite_scorer.score() 반환 예시
# columns: candidate_id, dg, selectivity, half_life, admet_tox, radiolysis_count,
#          wss, pareto_rank, tier, hard_cutoff_pass, explain_json
```

추가 산출물:
- `runs_local/final_candidates/hard_cutoff_pass.csv` — Hard Cutoff 통과 후보
- `runs_local/final_candidates/tier_s_candidates.csv` — Tier-S 후보
- Pareto front 시각화: `runs_local/final_candidates/pareto_front.png` (matplotlib)

---

## 검증 기준 (Acceptance Criteria)

| 기준 | 내용 |
|------|------|
| WSS 구현 | 가중치 합 = 1.0, min-max 정규화 적용 |
| Pareto front 구현 | pymoo NSGA-II 또는 직접 비지배 정렬 알고리즘 |
| Hard Cutoff 격리 | tier="FAIL" 후보가 WSS에 영향 없음 |
| SST-14 SS bond 처리 | Cys3-Cys14는 radiolysis_count에서 제외 |
| 단위 테스트 | `pipeline_local/tests/test_composite_scorer.py` ≥ 10개 |
| `pharmacology_guards.py` 연동 | Instability Index 가드 통과 확인 테스트 포함 |
| 가중치 외부 주입 | YAML/JSON 파일 또는 생성자 파라미터로 오버라이드 가능 |

---

## 추천 위임 경로

```
1. engineer-backend → composite_scorer.py + radiolysis_scorer.py 구현
2. reviewer-math    → NSGA-II 수렴 검증, WSS 가중치 민감도 분석
3. reviewer-pharma  → Radiolysis 민감도 등급·점수 체계 검증
4. reviewer-chemistry → Radiolysis 대응 수식 전략 타당성 (Nle, Abu, Orn 등)
5. reviewer-code    → OOP 설계, 단위 테스트 품질
```

---

## 에러 처리

| 상황 | 처리 방법 |
|------|----------|
| `dg_max`가 None (A-05 미완료) | 경고 출력 + dg Hard Cutoff 스킵 (soft mode) |
| Hard Cutoff 통과율 < 5% | `CompositeScorer.WARN_LOW_PASSRATE` 예외 발생 + 임계값 재검토 요청 |
| 후보 수 < 10 | Pareto front 스킵 → WSS만 적용 (경고 출력) |
| `admet_tox` 필드 누락 | 기본값 0.5 (보수적) 적용 + 로그 기록 |
| SS bond 위치 불일치 | `ValueError` 발생 — 명확한 에러 메시지 포함 |

---

## 참고 자료

- A-04 정리 파일: `docs/meet_log/2026-04-06_action_items/A-04_composite_scoring.md`
- 회의록 §2.5: 7단계 다단계 선별 체계
- Radiolysis 민감도: Spinks & Wood (1990) — 아미노산별 방사선 손상 순서
- NSGA-II: Deb et al. (2002) — IEEE Trans. Evol. Comput. 6(2):182-197
- `pharmacology_guards.py` Stage 5 가드 — Instability/GRAVY/Boman 기존 구현 참조
- Weighted sum normalization: min-max scaling [0,1] 적용
