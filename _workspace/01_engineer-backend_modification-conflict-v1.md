# 산출물: modification_conflict — Phase 1 구현 완료

작성자: engineer-backend  
날짜: 2026-05-11  
Phase: Harness End-to-End 사이클 Phase 1 (구현)

---

## 구현 규칙 6개 요약 + 출처

| rule_id | 요약 | 출처 |
|---------|------|------|
| C-01 | 동일 position에 fatty_acid + pegylation 동시 결합 불가 — Lys ε-NH2 단일 부위 | Knudsen & Lau 2019 Front Endocrinol 10:155 |
| C-02 | fatty_acid를 Lys(K) 또는 N-terminal 외 위치에 적용 불가 — NHS-ester 아실화 선택성 | Knudsen & Lau 2019 |
| C-03 | d_amino_acid를 Gly 위치에 적용 → no-op WARNING — Gly은 키랄 중심 없음 | Merrifield 1963 J Am Chem Soc 85:2149 |
| C-04 | d_amino_acid를 Cys-Cys SS bond 위치에 적용 → β-turn 손상 위험 WARNING | Reubi 2000 Eur J Nucl Med 28:836; Veber 1978 PNAS 75:2636 |
| C-05 | 자연 Cys-Cys SS bond가 존재하는데 cyclization modification 추가 → 중복 WARNING | Reubi 2000 DOTATATE SS topology |
| C-06 | position이 [1, len(sequence)] 범위 밖 → INDEX_ERROR | 기본 배열 인덱스 유효성 |

---

## 테스트 결과

- 테스트 파일: `pipeline_local/tests/test_modification_conflict.py`
- 테스트 수: **20개** (클래스 6개 + 통합 4개)
- pytest 결과: **20 passed in 0.09s**

```
============================= test session starts ==============================
collected 20 items

TestC01SamePositionFattyPeg::test_c01_triggers_on_same_position       PASSED
TestC01SamePositionFattyPeg::test_c01_no_conflict_different_positions  PASSED
TestC01SamePositionFattyPeg::test_c01_mods_involved_indices_correct    PASSED
TestC02FattyAcidNonLys::test_c02_triggers_on_trp_position              PASSED
TestC02FattyAcidNonLys::test_c02_no_conflict_on_lys                    PASSED
TestC02FattyAcidNonLys::test_c02_allows_n_terminal                     PASSED
TestC03DAminoOnGly::test_c03_triggers_on_gly2                          PASSED
TestC03DAminoOnGly::test_c03_no_conflict_on_non_gly                    PASSED
TestC04DAminoOnCysSS::test_c04_triggers_on_cys3                        PASSED
TestC04DAminoOnCysSS::test_c04_triggers_on_cys14                       PASSED
TestC04DAminoOnCysSS::test_c04_no_conflict_non_ss_cys                  PASSED
TestC05DuplicateCyclization::test_c05_triggers_on_sst14_with_cyclization PASSED
TestC05DuplicateCyclization::test_c05_no_conflict_without_natural_ss   PASSED
TestC06OutOfRangePosition::test_c06_triggers_on_position_zero          PASSED
TestC06OutOfRangePosition::test_c06_triggers_on_position_exceeding_length PASSED
TestC06OutOfRangePosition::test_c06_no_conflict_on_valid_boundary      PASSED
TestIntegration::test_clean_fatty_acid_on_k4                           PASSED
TestIntegration::test_multiple_conflicts_in_one_call                   PASSED
TestIntegration::test_return_type_is_list_of_conflict                  PASSED
TestIntegration::test_lowercase_sequence_auto_normalized               PASSED

20 passed in 0.09s
```

---

## 의도 vs 구현 갭 셀프-체크

명세에서 C-03은 "WARNING (no-op)"로만 정의되었으나, D-Gly이 실제로 no-op임을 테스트로 명시적으로 검증하는 케이스는 포함하지 않았다 — severity=WARNING 탐지까지만 검증. 생물학적 효과 부재를 단위 테스트로 증명하려면 반감기 계산 모의(mock)가 필요해 별도 Phase로 분리가 적절하다.

---

## §검증 필요

없음 — 모든 규칙이 공개 문헌 출처를 가지며 SST-14 서열 기반으로 테스트 통과 확인.
