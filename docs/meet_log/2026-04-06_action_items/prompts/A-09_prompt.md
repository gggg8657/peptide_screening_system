# Claude Code 실행 프롬프트 — A-09: 최종 후보 3-4개 도출 및 합성 의뢰서 작성

## 사용 방법

Claude Code CLI에서 아래 **컨텍스트 섹션을 포함하여** 대화를 시작한다:

```
# 아래 파일들을 먼저 읽어라 (A-04 완료 후 실행)
@CLAUDE.md
@docs/meet_log/2026-04-06_action_items/A-09_final_candidates_synthesis.md
@docs/meet_log/2026-04-06_action_items/A-04_composite_scoring.md
@pipeline_local/scripts/composite_scorer.py    ← A-04 구현 결과
@pipeline_local/scripts/pharmacology_guards.py
@runs_local/final_candidates/tier_s_candidates.csv  ← A-04 산출물

# 그 다음 아래 작업 정의를 실행하라
```

> **선행 조건**: `A-04_prompt.md` 작업 완료 후 `tier_s_candidates.csv`가 생성된 상태에서 실행.

---

## 컨텍스트

| 파일 | 역할 |
|------|------|
| `@CLAUDE.md` | 프로젝트 행동 규칙 |
| `@A-09_final_candidates_synthesis.md` | A-09 액션 아이템 상세 |
| `@A-04_composite_scoring.md` | Hard Cutoff·가중치·Tier 정의 참조 |
| `@composite_scorer.py` | A-04 구현 결과 — 스코어링 API |
| `@tier_s_candidates.csv` | A-04 산출물 — Tier-S 후보 목록 |
| `회의록: docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf` | §2.5 7단계 선별 체계, Gate-1/Gate-2 정의 |
| `7단계 선별 체계` | A-09 정리 파일 §"7단계 다단계 선별 체계 매핑" 참조 |

---

## 작업 정의

### 목표
1. A-04 복합 스코어링 결과에서 **최종 후보 3-4개** 선정
2. 합성 가능성 평가 체크리스트 자동 생성
3. **표준화된 합성 의뢰서** (Markdown) 3-4개 자동 작성

### 세부 구현 요구사항

#### Step 1 — 최종 후보 선정 스크립트

`pipeline_local/scripts/select_final_candidates.py` 구현:

```python
class FinalCandidateSelector:
    def select(
        self,
        tier_s_csv: str,          # A-04 Tier-S 후보 CSV 경로
        n_candidates: int = 4,    # 목표 후보 수 (기본 4)
        diversity_threshold: float = 0.80,  # 서열 유사도 상한
    ) -> list[dict]:
        """
        선정 기준 (순서대로 적용):
        1. Tier-S 후보 전원 포함 우선
        2. 서열 유사도 ≤ 80% (Levenshtein/sequence identity 기준)
        3. 목표 수 미달 시 Tier-A에서 보완 (합성 가능성 높은 순)
        4. 최종 n_candidates개 반환
        """
    
    def sequence_diversity_check(
        self, sequences: list[str], threshold: float = 0.80
    ) -> bool:
        """모든 후보 쌍의 서열 유사도 ≤ threshold 확인"""
```

#### Step 2 — 합성 가능성 체크리스트 생성

`pipeline_local/scripts/synthesis_checker.py` 구현:

```python
class SynthesisChecker:
    # 비천연 아미노산 목록 (국내 조달 가능성 표시)
    NON_NATURAL_AA = {
        "Nle": {"code": "Nle", "vendor_available": True,  "note": "norleucine, Met 대체"},
        "Abu": {"code": "Abu", "vendor_available": True,  "note": "α-aminobutyric acid, Cys 대체"},
        "Orn": {"code": "Orn", "vendor_available": True,  "note": "ornithine, Lys 대체"},
        "Dab": {"code": "Dab", "vendor_available": None,  "note": "확인 필요"},
        "5F-Trp": {"code": "5F-Trp", "vendor_available": None, "note": "합성 특주 가능성"},
        # ... 추가
    }
    
    def check(self, candidate: dict) -> dict:
        """
        반환:
        {
          "candidate_id": str,
          "modifications": list[dict],   # 각 수식 위치·종류
          "non_natural_aa": list[dict],  # 비천연 아미노산 조달 정보
          "cyclization_strategy": str,   # SS/thioether/lactam/dicarba
          "dota_attachment": str,        # N-term / Lys_sidechain / N/A
          "synthesis_feasibility": str,  # "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
          "ri_team_review_required": bool,
        }
        """
```

#### Step 3 — 합성 의뢰서 자동 작성

`pipeline_local/scripts/generate_synthesis_request.py` 구현:

```python
def generate_synthesis_request(
    candidates: list[dict],
    output_dir: str = "runs_local/final_candidates/",
    date_str: str | None = None,  # None이면 오늘 날짜 사용
) -> str:
    """
    출력: runs_local/final_candidates/synthesis_request_<YYYYMMDD>.md
    
    각 후보에 대해 아래 섹션 포함:
    - 후보 ID (PRST-001 형식)
    - 아미노산 서열
    - 수식 위치 및 종류 (N-말단, C-말단, 고리화, DOTA, 비천연 AA)
    - 합성 순도 기준 (≥ 95% HPLC)
    - 납기 및 수량
    - Quencher 조합 (QC-1~QC-4) 참고 기재
    - RI팀 협의 메모 필드 (빈칸)
    """
```

---

## 합성 의뢰서 표준 템플릿

각 후보에 대해 아래 형식으로 출력:

```markdown
## 후보 [PRST-XXX]

### 기본 정보
| 항목 | 값 |
|------|---|
| 후보 ID | PRST-XXX |
| 서열 | XXXXXXXXXXXXXXXXX |
| 길이 | XX aa |
| Tier | S / A |
| WSS | 0.XX |
| ΔG (SSTR2) | -X.X kcal/mol |
| 셀렉티비티 | XXX× |

### 수식 (Modification) 상세
| 위치 | 잔기 | 원래 → 변형 | 종류 |
|------|------|-----------|------|
| N-말단 | — | H → Ac | 아세틸화 (선택) |
| C-말단 | — | OH → NH2 | 아미드화 |
| 고리화 | 3↔14 | Cys-Cys | [SS bond / Thioether / Lactam / Dicarba] |
| DOTA | N-말단 / Lys-X | — | DOTA-NHS 접합 |
| XX | [잔기] | → [대체] | 비천연 AA |

### 합성 사양
| 항목 | 기준 |
|------|------|
| 순도 | ≥ 95% (HPLC) |
| 수량 | 5–10 mg |
| 납기 | 협의 예정 (목표: 발주 후 6주) |
| 특이사항 | [키랄 순도, 보호기 전략 등] |

### Quencher 조합 참고
72시간 RCP ≥ 90% 검증 시 QC-1~QC-4 중 선택 (A-04 정리 파일 참조)

### RI팀 협의 메모
> (RI팀 검토 후 기재)
```

---

## 입력 (Input Spec)

1. **`tier_s_candidates.csv`** (A-04 산출물):
   ```
   candidate_id, sequence, dg, selectivity, half_life, admet_tox, radiolysis_count,
   wss, pareto_rank, tier, modifications_json
   ```

2. **`synthesis_feasibility.md`** (RI팀 협의 결과, 선택):
   - 있으면 synthesis_request에 반영
   - 없으면 "RI팀 협의 필요" 표시

---

## 출력 (Output Spec)

| 파일 | 내용 |
|------|------|
| `runs_local/final_candidates/final_4_candidates.csv` | 최종 3-4개 후보 표 |
| `runs_local/final_candidates/synthesis_request_<YYYYMMDD>.md` | 합성 의뢰서 (3-4개) |
| `runs_local/final_candidates/synthesis_checklist.md` | 합성 가능성 체크리스트 |
| `runs_local/final_candidates/diversity_matrix.csv` | 후보 간 서열 유사도 행렬 |

---

## 검증 기준 (Acceptance Criteria)

| 기준 | 내용 |
|------|------|
| 최종 후보 수 | 3-4개 (정확히) |
| 서열 다양성 | 모든 후보 쌍 유사도 ≤ 80% |
| 합성 의뢰서 완성도 | 7개 필수 항목 전원 포함 (서열·수식·순도·납기·수량·킬레이터·특이사항) |
| Quencher 참고 | QC-1~QC-4 중 해당 후보의 적용 우선순위 기재 |
| DOTA 접합 위치 | 각 후보별 명시 (N-말단 vs Lys 측쇄) |
| 단위 테스트 | `test_select_final_candidates.py` ≥ 5개 |
| 선정 이유 | 각 후보 선정 근거 1문장 이상 기재 |

---

## 추천 위임 경로

```
1. engineer-backend  → select_final_candidates.py + generate_synthesis_request.py 구현
2. reviewer-chemistry → 합성 가능성 (비천연 AA 조달, 고리화 전략) 검증
3. reviewer-pharma   → 합성 의뢰서 ADMET/반감기 수치 정확성 확인
4. reviewer-biology  → SS bond/고리화 전략 → SSTR2 결합 유지 여부 검증
5. reviewer-code     → 코드 품질, 의뢰서 템플릿 완성도
```

---

## 에러 처리

| 상황 | 처리 방법 |
|------|----------|
| Tier-S 후보 < 3개 | Tier-A에서 보완, 경고 출력 (`WARN: Tier-S insufficient`) |
| 서열 다양성 ≤ 80% 확보 불가 | 가장 다양한 조합으로 선정 + 경고 (`WARN: Diversity threshold not met`) |
| `tier_s_candidates.csv` 없음 | `FileNotFoundError` — A-04 먼저 실행하도록 안내 |
| 비천연 AA 조달 정보 없음 | `vendor_available: null` 표시 + "RI팀 확인 필요" 기재 |
| RI팀 협의 파일 없음 | 의뢰서에 "RI팀 협의 메모: (미작성)" 필드 유지 |

---

## 참고 자료

- A-09 정리 파일: `docs/meet_log/2026-04-06_action_items/A-09_final_candidates_synthesis.md`
- A-04 정리 파일: `docs/meet_log/2026-04-06_action_items/A-04_composite_scoring.md`
- 회의록 §2.5: 7단계 선별 체계, Gate-1/Gate-2 정의
- Quencher DOE 전략: A-04 §"Quencher DOE 조합"
- DOTA 킬레이터 벤더: MOM-002 A-10 선행 완료 후 연동
- 서열 유사도 산출: Biopython `pairwise2` 또는 scikit-bio `local_pairwise_align_ssw`
- Lutathera® Quencher 조합 참조 (QC-1): Bernhardt et al., Eur. J. Nucl. Med. 2011
