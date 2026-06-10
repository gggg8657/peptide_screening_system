# 세션 분리 컨벤션 (EOD/SOD 명시)

> **수립**: 2026-05-13 SOD
> **계기**: 2026-05-12에 두 세션이 같은 파일을 병행 수정하여 commit 흐름이 섞임 (PR #20 머지에서 발견)
> **수단**: CLAUDE.md 미변경, EOD/SOD 보고서 컨벤션으로만 운영 (사용자 선택)

---

## 1. 두 세션 식별

| 항목 | 본 세션 (orchestrator) | 별도 세션 (cand03-tomorrow-priorities) |
|------|----------------------|--------------------------------------|
| 유형 | Claude Code Native Agent Team API | tmux team-mate 모드 (6 팀원) |
| LLM | Claude Opus 4.7 (1M context) | Claude Sonnet 4.6 (Opus 일부) |
| 시작 시점 | 어제 EOD 직후 또는 사용자 `/team` 호출 시 | 사용자 별도 터미널 SOD 호출 |
| 역할 | Meta — 검증·통합·머지·dogfood | Implementation — 신규 구현·실험 |
| EOD 파일명 | `eod-{date}-orchestrator-session.md` | `eod-{date}-team-session.md` |
| SOD 파일명 | `sod-{date}-orchestrator-*-consolidated.md` (팀별) | `sod-{date}-cand03-*` 또는 자체 명명 |

---

## 2. 충돌 회피 권고 (자율)

### Branch 명명 (강제 아님, 권고)
- 본 세션: `fix/*`, `docs/*`, `chore/*`
- 별도 세션: `feat/*`, `refactor/*`, `wip/*`

### Commit 메시지 type (자연 분리)
- 본 세션 위주: `fix:` `docs:` `test:`
- 별도 세션 위주: `feat:` `refactor:`

→ Conventional Commit 컨벤션이 자연스럽게 역할 분리에 맞물림. *강제 룰 아님*.

### 운영 룰 (최소)
1. **PR로만 main 진입** — 두 세션 모두 `gh pr create` 의무, `git push origin main` 직접 금지
2. **다른 세션의 미커밋 변경에 손대지 않음** — fetch 후 *읽기*만, stash·rebase로 옮기지 않음
3. **EOD/SOD 명명에 세션 식별자 포함** — 위 §1 표 형식 준수

---

## 3. 사고 회복 패턴

| 상황 | 본 세션 행동 |
|------|-------------|
| `git fetch` 결과 별도 세션 commit이 main에 추가됨 | 자기 변경 중단 → 그 commit을 dogfood로 *검증* → 결함 발견 시 *후속 PR* (절대 amend·rebase 금지) |
| 두 세션이 동일 파일 수정 중 (동시) | 본 세션이 양보, 별도 세션이 commit 후 후속 fix PR로 진입 |
| working tree에 다른 세션의 untracked/M 변경 발견 | 알림만, 손대지 않음. *명시적으로 사용자가 통합 요청* 시에만 처리 |

---

## 4. 본 컨벤션의 한계

- **소유권 없음**: 같은 파일을 동시 수정하면 여전히 conflict 가능 (`.gitattributes` 미사용)
- **자율 룰**: 강제 enforcement 없음. 사용자가 각 세션에 명시적으로 따르도록 지시 필요
- **CLAUDE.md 미변경**: 새 세션이 자동으로 이 룰을 알지 못함. EOD/SOD에서 *참조*해야 발견됨

향후 강화 필요 시:
- `.gitattributes`에 owner 명시
- CLAUDE.md `§세션 분리` 신설
- pre-commit hook으로 branch naming 강제

---

## 5. 적용 시작

본 컨벤션은 **2026-05-13 본 SOD 이후 작성되는 모든 EOD/SOD 보고서**에 적용.

기존 보고서 (2026-05-12)는 *후술적으로* 이 컨벤션과 정합 (이미 `orchestrator-session` / `team-session` 분리 명명 사용).
