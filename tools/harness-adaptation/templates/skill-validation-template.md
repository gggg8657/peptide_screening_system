# Skill Validation Report — `{{SKILL_NAME}}`

> harness Stage 4 산출물. 신규/변경된 스킬의 트리거 매칭과 Progressive Disclosure 적합성을 검증한다.
> 파일명 규칙: `_workspace/release/skill-{{SKILL_NAME}}-validation-{{YYYY-MM-DD}}.md`

## 0. 메타

| 항목 | 값 |
|------|---|
| Skill name | `{{SKILL_NAME}}` |
| 도입 PR | `#{{PR_NUMBER}}` 또는 커밋 `{{COMMIT_SHA}}` |
| 작성일 | `{{YYYY-MM-DD}}` |
| 작성자 | `{{AUTHOR}}` |
| 사용 CLI | `<claude-code | codex-cli | cursor-agent | 다중>` |

## 1. 스킬 메타데이터

- **`description`** (pushy하게 작성됨? trigger 상황 구체적?):
  ```
  <description 텍스트 그대로>
  ```
- **본문 라인 수**: __줄 (≤500 권장, 초과 시 references/ 분리)
- **references/ 파일 목록** (있다면):

## 2. Progressive Disclosure 검증

- [ ] 메타데이터(~100단어) 명확
- [ ] 본문 ≤500줄, 초과 시 references/ 분리
- [ ] references/ 파일이 본문에 명시적 포인터로 인용됨

## 3. should-trigger 쿼리 (≥8)

| # | 쿼리 | 매칭 기대 | 실측 | PASS? |
|---|------|---------|------|------|
| 1 | | `{{SKILL_NAME}}` | | |
| ... | | | | |
| 8 | | `{{SKILL_NAME}}` | | |

**Coverage**: __/8

## 4. should-NOT-trigger 쿼리 (≥8, near-miss 포함)

| # | 쿼리 | 매칭 기대 | 실측 | PASS? |
|---|------|---------|------|------|
| 1 | | <다른 스킬 또는 미매칭> | | |
| ... | | | | |
| 8 | | <다른 스킬 또는 미매칭> | | |

**False-positive rate**: __/8

## 5. A/B 비교 (with-skill vs without-skill)

### 입력
- 시드 입력: ...

### 결과
- **with-skill**: `_workspace/release/skill-{{SKILL_NAME}}-validation-{{YYYY-MM-DD}}-with.md`
- **without-skill**: `_workspace/release/skill-{{SKILL_NAME}}-validation-{{YYYY-MM-DD}}-without.md`

### 측정

| 메트릭 | with-skill | without-skill | Δ |
|--------|-----------|-------------|---|
| | | | |

## 6. CLI 적용 검증

| CLI | 적용 여부 | 경로 | 동작 확인 |
|-----|---------|-----|--------|
| Claude Code | | `.claude/skills/{{SKILL_NAME}}/SKILL.md` | |
| Codex CLI | | `~/.codex/skills/{{SKILL_NAME}}/` 또는 `instructions/{{SKILL_NAME}}.md` | |
| Cursor Agent | | `.cursor/rules/skills/{{SKILL_NAME}}.mdc` | |

## 7. §검증 필요

| ID | 항목 |
|----|------|

---

**End of Skill Validation Report.**
