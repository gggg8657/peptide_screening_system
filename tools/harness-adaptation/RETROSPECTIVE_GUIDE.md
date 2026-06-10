# Quarterly Retrospective Guide — `tools/harness-adaptation/`

> harness Stage 6 산출물. 분기당 1회, harness 어댑테이션 운영을 점검·개선하는 회고 가이드.
> 본 문서가 회고 진행 절차를 정의하고, 회고 결과는 `_workspace/release/retro-{{YYYY-Q}}.md`로 보존.

---

## 회고 주기

- **분기 마지막 주 1회** (3월 / 6월 / 9월 / 12월 마지막 금요일 권장)
- 참여: 프로젝트 리드 + 활성 협업자
- 소요: 60~90분
- 산출물: `_workspace/release/retro-{{YYYY-Q}}.md` (예: `retro-2026-Q2.md`)

---

## 0. 회고 입력 데이터 수집 (사전 30분)

회고 전에 아래를 수집:

| 데이터 | 명령 또는 경로 |
|--------|-----------|
| 본 분기 CHANGELOG entries | `tools/harness-adaptation/CHANGELOG.md` |
| 본 분기 commit | `git log --since="{{Q_START}}" --until="{{Q_END}}" --oneline tools/harness-adaptation/ CLAUDE.md` |
| 본 분기 검증 보고서 | `ls _workspace/release/*-validation-*.md` |
| 본 분기 trigger query 통계 | (해당 시) `_workspace/release/` 보고서에서 PASS/FAIL 집계 |
| 알려진 §검증 필요 항목 | `ANALYSIS.md §12`, 각 검증 보고서 §검증 필요 |

---

## 1. 회고 어젠다 (90분)

### Phase A — 사실 정리 (15분)

- 본 분기에 적용된 Stage (CHANGELOG의 [unreleased] + 본 분기 minor entries)
- 본 분기에 차단된 회귀 사례 — `pytest pipeline_local/tests/test_pharmacology_guards.py` 실패 이력
- 본 분기에 추가된 검증 보고서 수

### Phase B — 패턴 적합성 검토 (20분)

각 위임 (CLAUDE.md 트리 1~4순위)에 대해:

- **선언된 패턴**(`CLAUDE.md §"작업 위임 의사결정 트리"`)이 실제 운영과 일치하는가?
- 예: 1순위 "Fan-out/Fan-in"으로 선언했으나 실제는 Pipeline으로 운영된 사례가 있는가?
- 불일치 시 — 트리 명세를 수정할 것인가, 운영 방식을 명세에 맞출 것인가?

### Phase C — 환각 가드 효과 (15분)

- `LITERATURE_VALUES`에 추가할 척도/키가 있는가?
- `SCALE_RANGES`의 어떤 범위가 너무 좁았거나/넓었는가?
- 본 분기에 추가된 lookup table은 모두 회귀 테스트에 등록되었는가?
- `_PROTEASE_VULNERABILITY`(step08_stability.py) 등 휴리스틱 값들의 정량화 진척은? (VR-S5-01)

### Phase D — Stage 미적용 항목 검토 (15분)

`tools/harness-adaptation/INTEGRATION_PLAN.md`의 미적용 Stage 검토:

- Stage 7 (`.claude/agents/` 분리) — CLAUDE.md가 비대해졌나? 분리 시점인가?
- 본 분기 새로 식별된 Stage 후보 — 어댑테이션에 추가할 가치?

### Phase E — Action Items (10분)

다음 분기에 진행할 액션:

| ID | 액션 | 책임 | 기한 |
|----|------|------|------|
| Q-{{YYYY-Q}}-1 | | | |
| Q-{{YYYY-Q}}-2 | | | |

### Phase F — CHANGELOG·문서 갱신 (15분)

- `CHANGELOG.md` `[Unreleased]` 섹션 정리 → 새 minor 버전으로 cut
- `CLAUDE.md §"Harness Pointer / Stage 적용 이력"` 갱신
- 본 회고 결과를 `_workspace/release/retro-{{YYYY-Q}}.md`로 저장

---

## 2. 회고 산출물 템플릿 (`retro-{{YYYY-Q}}.md`)

```markdown
# Quarterly Retrospective — {{YYYY-Q}}

## 0. 메타
- 일시: {{YYYY-MM-DD}}
- 참여: {{names}}
- 분기 범위: {{Q_START}} ~ {{Q_END}}

## A. 사실 정리
- 적용된 Stage / minor 버전:
- 차단된 회귀:
- 추가된 검증 보고서:

## B. 패턴 적합성 검토
| 순위 | 선언 패턴 | 실 운영 패턴 | 일치? | 액션 |
|------|---------|-----------|------|------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |

## C. 환각 가드 효과
- LITERATURE_VALUES 추가 후보:
- SCALE_RANGES 보정 사례:
- 휴리스틱 정량화 진척:

## D. 미적용 Stage 검토
- Stage 7: <도입/보류 결정 + 이유>
- 새 Stage 후보:

## E. Action Items
| ID | 액션 | 책임 | 기한 |

## F. CHANGELOG cut
- 신규 minor 버전: 0.X.0
- [Unreleased] 항목 이동 완료 여부:
```

---

## 3. 비상 회고 트리거 (분기 외)

다음 발생 시 분기 회고 일정과 무관하게 즉시 회고:

1. **회귀 테스트 실패가 main 브랜치에 머지됨** — 본 어댑테이션의 가드가 작동하지 못한 사례
2. **패턴 선언과 실 운영 불일치가 3건 이상** — 트리 명세 자체 결함 가능성
3. **lookup table 변경 PR이 LITERATURE_VALUES 등록 없이 머지됨** — Stage 4 절차 우회 사례

---

## 4. 회고 간소화 옵션 (분기 외 시점)

전체 어젠다가 부담스러울 때:

- **15분 lightning retro**: Phase A + F만 수행
- **30분 mid-quarter checkup**: Phase A + C + E

본 가이드는 강제가 아닌 권장. 어떤 형식이든 **CHANGELOG 갱신**만 분기당 1회 의무.

---

**End of Retrospective Guide.**
