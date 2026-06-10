# Code Review Report — modification_conflict

작성자: reviewer-code  
날짜: 2026-05-11  
Phase: Harness End-to-End 사이클 Phase 2a (코드 리뷰)

---

## 요약

- 판정: **CONDITIONAL PASS**
- 신뢰 등급: **HIGH** (모든 항목 코드/실행 직접 확인)

20개 테스트 전체 통과, 구조 설계는 명확하다. 다만 Silent exception swallowing, dead code, dataclass 가변성, 타입 힌팅 비일관성 4가지를 조건부 수정 후 통과 권장.

---

## Critical 이슈

### CR-1 — Silent exception swallowing (HIGH)

`pipeline_local/scripts/modification_conflict.py` L434–435:

```python
except Exception as exc:  # noqa: BLE001
    logger.error("규칙 %s 실행 중 예외 발생: %s", rule_id, exc)
```

`position`이 비-int 문자열일 때 C-06은 ERROR를 반환하지만, C-02는 그보다 먼저 실행되어 `'four' - 1` 연산에서 `TypeError`를 발생시킨다. 이 예외가 `check_conflicts`의 broad except로 삼켜지면서 C-02 규칙이 완전히 건너뛰어진다(실행 확인). 호출자는 C-06 ERROR 하나만 받아 C-02 로직이 정상 동작한 것처럼 오해할 수 있다.

**권고**: 각 규칙 함수 내부에서 `position`을 int로 조기 검증하거나, `check_conflicts`의 except를 `Exception`이 아닌 좁은 타입으로 제한하고 ValueError/TypeError는 재발생(re-raise)한다. 또는 C-06을 _RULES 리스트 첫 번째로 이동해 범위 검증을 선행한다.

---

### CR-2 — Dead code: `_SST14_CYS_SS_POSITIONS` (HIGH)

`pipeline_local/scripts/modification_conflict.py` L36:

```python
_SST14_CYS_SS_POSITIONS: Tuple[int, ...] = (2, 13)
```

모듈 전체에서 이 상수를 참조하는 코드가 없다(grep 확인). C-04는 `_find_cys_pairs()`로 동적 탐지하므로 이 상수가 쓰이지 않는다. 읽는 사람이 이 상수가 어딘가에 쓰이는 줄 오해하게 만든다.

**권고**: 제거하거나, C-04 fallback 상수로 실제 사용하도록 연결한다.

---

## 권장 리팩토링 (Impact ÷ Effort 우선순위)

| Priority | 항목 | 위치 | Impact | Effort |
|----------|------|------|--------|--------|
| 1 | C-06을 _RULES 첫 번째로 이동해 선행 검증 | L381–388 | H | 낮음 (순서 변경만) |
| 2 | Conflict dataclass `frozen=True` 적용 | L39 | M | 낮음 (한 줄) |
| 3 | 타입 힌팅 일관성 통일 (아래 참고) | 전체 | L | 낮음 |
| 4 | 함수 길이 — `check_conflicts` 분리 | L395–450 | L | 중간 |

### 상세

**P2 — `frozen=True`**: `Conflict.mods_involved`는 `List[int]`(가변 리스트)이고 `frozen=False`(실행 확인)이므로 반환된 Conflict 객체가 외부에서 변경 가능하다. `frozen=True`를 적용하면 `mods_involved`를 `Tuple[int, ...]`로 바꿔야 하나, 의도치 않은 변이를 방지하는 효과가 크다.

**P3 — 타입 힌팅 비일관성**: 소스 파일은 `from __future__ import annotations`가 있어 런타임 영향은 없다. 그러나 같은 파일 안에서:
- 대부분의 함수 시그니처: `List[dict]`, `List[Conflict]`, `Tuple[int, ...]` (typing 모듈 형식)
- 모듈 docstring 예시(L20): `list[Conflict]` (3.9+ 소문자 형식)
- `_RULES` 주석(L378): `list[Conflict]` 소문자

테스트 파일(`test_modification_conflict.py`) L34–38은 `list[Conflict]`, `list[str]`을 사용해 소스와 스타일이 엇갈린다. 프로젝트가 Python 3.9 호환을 명시했으므로 소스 전체를 `typing` 모듈 형식으로 통일하거나, 3.10+ 소문자 형식으로 일관되게 바꾼다(후자는 `__future__` import가 이미 있어 런타임 안전).

**P4 — 함수 길이**: 6개 규칙 함수 모두 30줄 초과(35–45줄), `check_conflicts`는 56줄. 단, 초과분의 대부분이 docstring과 f-string 메시지 구성이어서 로직 복잡도(CC=3–6)는 기준(10) 이내다. 순환복잡도 위반은 없음.

---

## 누락된 테스트 케이스

1. **비-int position 문자열 입력**: `position="four"` 케이스가 없다. 현재 C-02가 silent 예외로 건너뛰어지는 버그가 테스트에 드러나지 않는다.

2. **`position=None` 명시 입력**: `{"mod_type": "fatty_acid", "position": None}` — 현재 모든 규칙에서 `if pos is None: continue`로 무시된다. 이 동작이 의도인지 아닌지 테스트로 명세화되어 있지 않다.

3. **`mod_type` 키 누락**: `{"position": 4}` — 현재 조용히 무시된다(실행 확인). 테스트 없음.

4. **빈 서열(`""`)**에 modifications 입력: C-06이 `허용 범위=[1, 0]`이라는 어색한 메시지를 생성한다. 경계 케이스 테스트 없음.

5. **C-01 + C-02 동시 발생**: K4가 아닌 W8에 fatty_acid + pegylation 동시 지정 시 C-01과 C-02 둘 다 발생하는지 검증하는 케이스 없음.

6. **`_find_cys_pairs` 단위 테스트**: 내부 헬퍼이나 복잡도 있는 로직(이중 루프 + 간격 조건). 직접 단위 테스트가 없고 C-04/C-05를 통해서만 간접 검증.

---

## 기타 소견

- **docstring 품질**: 6개 규칙 모두 한국어 설명 + 출처 인용을 갖추어 기준 충족. `check_conflicts` docstring의 Args/Returns/Example 구성도 적절하다.
- **출처 인용 일관성**: Knudsen 2019, Reubi 2000, Merrifield 1963, Veber 1978 모두 DOI/저널 정보 포함. 단 `_find_cys_pairs` L85의 "Baker & Squire 2005 Chem Biol 12:103" 인용은 다른 규칙 함수들과 달리 연도·저자 외 검증 수단이 없어 출처 신뢰도가 상대적으로 낮다.
- **규칙 레지스트리 패턴**: `_RULES` 리스트로 규칙을 플러그인처럼 관리하는 설계는 OCP(개방-폐쇄 원칙) 관점에서 우수하다. 규칙 추가 시 `check_conflicts` 본체 수정 불필요.
- **SRP**: 각 규칙 함수가 단일 규칙만 담당하고, `check_conflicts`는 오케스트레이션만 담당해 SRP 준수.

---

## §검증 필요

- `_find_cys_pairs` L85 "Baker & Squire 2005 Chem Biol 12:103" 인용이 실제 존재하는 문헌인지, 그리고 "최소 4잔기 간격" 기준이 step08_stability.py와 실제로 일치하는지 — reviewer-science 또는 engineer-backend 확인 요청.
- C-06에서 `position=None`을 조용히 건너뛰는 동작이 upstream(step08_stability.py)의 명세된 계약인지, 아니면 방어적으로 WARNING이라도 발행해야 하는지.
