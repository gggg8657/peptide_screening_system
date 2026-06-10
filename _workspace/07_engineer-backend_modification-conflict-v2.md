# Phase 5 — Engineer-Backend 작업 결과 (modification-conflict v2)

작성: 2026-05-11  
작성자: engineer-backend  
대상: `pipeline_local/scripts/modification_conflict.py`, `test_modification_conflict.py`,  
      `scripts/auto_dispatch.sh`, `pipeline_local/scripts/pharmacology_guards.py`

---

## 1. 적용 액션 체크리스트

| ID | 내용 | 상태 | 비고 |
|----|------|------|------|
| **A-1** | silent except → C-99 Conflict 승격 + C-06 선행 차단 후 filtered_mods로 다른 규칙 실행 | **PASS** | 비-int position이 다른 규칙에서 TypeError 유발하지 않음 |
| **A-2** | 누락 테스트 6건 추가 (비-int pos, None pos, mod_type 누락, 빈 서열, C-01+C-02 동시, bool position) | **PASS** | 6건 전수 PASS |
| **A-3** | C-04 severity WARNING → ERROR 격상 + 테스트 변경 | **PASS** | Veber 1978 + Pellegrini 1999 출처 보강 |
| **A-4** | auto_dispatch 외부 CLI 키워드를 도메인 키워드보다 먼저 매칭 | **PASS** | "코드 리뷰해줘" → codex:review, "약리학 Boman Index 확인" → internal:reviewer-pharma |
| **A-5** | `_SST14_CYS_SS_POSITIONS` dead const 제거 | **PASS** | L36 삭제 완료 |
| **A-6** | `_RULES`에서 C-06을 첫 번째로 이동 | **PASS** | `check_conflicts`에서 C-06 선행 실행 + filtered_mods 패턴 구현 |
| **A-7** | C-08~C-10 규칙 추가 (C-07 DOTA는 §검증 필요) | **PASS (C-07 SKIP)** | 8건 테스트 추가 전수 PASS |
| **A-8** | `pharmacology_guards.py` LITERATURE_VALUES에 `modification_conflict_rules` 카테고리 등록 | **PASS** | C-01~C-10, C-99 전체 출처 추적 등록 |

---

## 2. pytest 최종 결과

### test_modification_conflict.py

```
38 passed in 0.08s
```

기존 20개 → 38개 (+18개):
- Phase 5 A-2 edge case 6건 (TestEdgeCasesPhase5)
- C-08 3건, C-09 4건, C-10 2건, _find_cys_pairs 3건 (A-7)

### test_pharmacology_guards.py

```
33 passed in 0.13s  (기존 33/33 유지)
```

---

## 3. auto_dispatch 라우팅 검증 결과

| 입력 | 기대 라우팅 | 실측 라우팅 | 판정 |
|------|-----------|-----------|------|
| `"pipeline_local/scripts/foo.py 코드 리뷰해줘"` | `codex:review` | `codex:review` | PASS |
| `"약리학 Boman Index 확인"` | `internal:reviewer-pharma` | `internal:reviewer-pharma` | PASS |

A-4 휴리스틱: "리뷰해" 동사구가 명시적으로 등장하면 외부 CLI 우선, 도메인 단어만 있으면 내부 에이전트 fallback.

---

## 4. 의도 vs v2 갭 셀프-체크

| 목표 (의도) | v2 상태 | 판정 |
|-----------|---------|------|
| G-1: 모든 충돌 차단 | C-01~C-10 (C-07 제외) — 10/11 규칙 구현 | 조건부 PASS |
| G-2: step08 정합성 | C-09 cyclization+Nterm 추가로 일부 개선; PEG 위치 가드·반감기 cap은 후속 iteration | 부분 |
| G-3: 규칙 6개+충분한 테스트 | 규칙 10개, 테스트 38개 | PASS |
| G-4: 1차 문헌 출처 부착 | C-08~C-10 모두 출처 docstring 포함, pharmacology_guards 등록 | PASS |
| G-5: harness 사이클 검증 | Phase 5 PR 번들 완료 | PASS |

---

## 5. 구현 세부사항

### A-1 + A-6 통합 구현 (check_conflicts 변경)

단순 `_RULES` 순서 변경만으로는 비-int position 문제 해결 불가.
C-06 실행 후 ERROR가 발생한 mod 인덱스를 `invalid_mod_indices`로 수집하고,
`filtered_mods`(유효한 modification만)를 이후 규칙에 전달하는 패턴으로 해결.
filtered_mods 인덱스 → 원래 modifications 인덱스 재매핑(remapping) 로직 포함.

### mods_involved 타입 변경

`List[int]` → `Tuple[int, ...]` 로 변경. `Conflict` dataclass의 `mods_involved` 필드 타입 힌팅 업데이트.
기존 테스트는 `set(c.mods_involved) == {0, 1}` 패턴을 사용하고 있어 tuple/list 모두 통과.

### C-04 severity 격상 영향

기존 테스트 `TestC04DAminoOnCysSS::test_c04_triggers_on_cys3/14` 두 건의
`assert severity == "WARNING"` → `"ERROR"` 로 변경.

---

## §검증 필요 (후속 iteration 항목)

1. **C-07 DOTA chelator 이중 결합 금지** — 현재 `mod_type` 어휘에 `"dota_conjugation"` 부재.
   step08_stability.py 어휘 확장 RFC 완료 후 도입. (reviewer-chemistry §검증 필요 2 연동)

2. **PEG 위치 가드 (A-5 reviewer-science)** — step08의 `_MODIFICATION_BONUS[pegylation]`과
   연동되는 위치 제약 규칙 미추가. 후속 iteration.

3. **반감기 상한 cap ~240h** — `predict_half_life`에 cap 도입은 reviewer-pharma + PI 결정 필요.

4. **Baker & Squire 2005 Chem Biol 12:103** 인용 실재성 — researcher 라우팅으로 검증 필요.

5. **C-08 severity** — 현재 ERROR. reviewer-chemistry는 "WARNING" 제안 (D,D-cystine이 형성 가능하나 topology 비호환). Phase 5에서는 reviewer-chemistry·reviewer-pharma 교차 검증이 ERROR를 지지하는 방향이 명확하지 않아 §검증 필요로 분리. 현재 ERROR 유지.
