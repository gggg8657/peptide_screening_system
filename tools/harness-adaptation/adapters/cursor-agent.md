# Cursor Agent Adapter — Harness Universal Prompt

> `PROMPT_TEMPLATE.md`의 추상 명령을 **Cursor Agent CLI 환경**으로 변환하는 어댑터.
> 우리 프로젝트는 `scripts/agent-wrapper.sh cursor-agent ...` 래퍼를 거쳐 호출 (`CLAUDE.md`).

---

## 1. 파일 위치 매핑

| 추상 (PROMPT_TEMPLATE) | Cursor Agent 실제 | 비고 |
|----------------------|----------------|------|
| 에이전트 정의 | `.cursor/rules/agents/{name}.mdc` | Cursor Rule 시스템 |
| 스킬 정의 | `.cursor/rules/skills/{name}.mdc` | 단일 rule 파일 |
| references | `.cursor/rules/refs/*.mdc` 또는 `@file` 참조 | 조건부 첨부 |
| 워크스페이스 | `_workspace/{phase}_{agent}_{artifact}.{ext}` | 동일 컨벤션 |
| 포인터 | `CLAUDE.md` 또는 `.cursorrules` | 우리는 `CLAUDE.md` 사용 |

### Cursor Rule frontmatter 예

```yaml
---
description: "<pushy한 트리거 설명>"
alwaysApply: false      # 자동 매칭만 필요 시 false
globs:                  # 특정 파일 패턴에서만 활성화
  - "src/**/*.py"
---
```

`.cursor/rules/`의 `.mdc` 파일은 `description`이나 `globs`로 트리거됨. `alwaysApply: true`는 모든 컨텍스트에 무조건 주입.

---

## 2. 에이전트 호출

우리 래퍼:

```bash
./scripts/agent-wrapper.sh cursor-agent -p "<프롬프트>"
```

또는 직접:

```bash
cursor-agent -p "<prompt>"
```

### 표준 실행형 하네스 (선택)

단계별 프롬프트를 레포에 두고 `_workspace/` 로 핸드오프할 때는 [`cursor-cli/README.md`](../cursor-cli/README.md) 의 stage 파일과 레포 [`scripts/cursor/harness_invoke.sh`](../../../scripts/cursor/harness_invoke.sh) 을 사용한다 (래퍼 경유 호출 동일).

```bash
./scripts/cursor/harness_invoke.sh list
./scripts/cursor/harness_invoke.sh chain explore,synthesize --topic myfeat --dry-run --task "브리프"
./scripts/cursor/harness_invoke.sh run explore --topic myfeat --execute --task "실호출"
```

**규칙**:
- ❌ 프롬프트 인라인에 긴 역할 정의 금지
- ✅ `.cursor/rules/agents/{name}.mdc`로 역할 정의 → 프롬프트는 태스크만

---

## 3. 팀 모드 — 폴백 전략

Cursor Agent도 `TeamCreate` / `SendMessage` 같은 팀 API가 (확인된 한) 없음 → **파일 기반 데이터 전달** + **다중 호출 + 집계** 패턴.

### 패턴별 변환

**Pipeline**:
```bash
./scripts/agent-wrapper.sh cursor-agent -p "$(cat <<EOF
역할: .cursor/rules/agents/auditor.mdc
태스크: ...
출력: _workspace/01_auditor_audit.md
EOF
)"

./scripts/agent-wrapper.sh cursor-agent -p "$(cat <<EOF
역할: .cursor/rules/agents/scorer.mdc
입력: @_workspace/01_auditor_audit.md
출력: _workspace/02_scorer_score.md
EOF
)"
```

**Fan-out/Fan-in**:
```bash
./scripts/agent-wrapper.sh cursor-agent -p "분석A" &
./scripts/agent-wrapper.sh cursor-agent -p "분석B" &
./scripts/agent-wrapper.sh cursor-agent -p "분석C" &
wait

./scripts/agent-wrapper.sh cursor-agent -p "통합: @_workspace/01_*.md @_workspace/02_*.md @_workspace/03_*.md"
```

**Producer-Reviewer**: Codex 패턴 동일 — 최대 2~3회 재시도 루프.

**Supervisor**: 공유 큐 파일 (`_workspace/queue.md`) 폴링.

**Expert Pool**: 라우터 1회 호출 → 결과로 전문가 1개 선택.

---

## 4. Cursor의 강점 활용

Cursor Agent는 다음 영역에서 효율이 높음 (우리 CLAUDE.md 분류):
- **분석/조사**: 코드 구조 파악
- **일정 관리**: EOD 보고, 상태 보고
- **문서 작성/갱신**: 한국어/영문 문서

→ Harness 6패턴 중 **Expert Pool**의 "문서·분석" 전문가로 자연스럽게 매핑됨.

---

## 5. 트리거 메커니즘

Cursor의 `.cursor/rules/*.mdc`는:
- `alwaysApply: true` → 모든 컨텍스트에 주입
- `description` 기반 자동 매칭 → 트리거 키워드 매칭 (확인 필요)
- `globs` → 특정 파일 패턴에서만 활성화

**pushy description** 원칙 (`SKILL.md:118-125`) 동일 적용.

---

## 6. 로그·감사

`./scripts/agent-wrapper.sh`가 `logs/external_agents/`에 cursor-agent 호출 기록 (`CLAUDE.md` 필수 행동).

---

## 7. 환경 검증 체크리스트

- [ ] `cursor-agent --version` 정상
- [ ] `./scripts/agent-wrapper.sh cursor-agent --help` 정상
- [ ] `.cursor/rules/` 디렉토리 존재 (없으면 생성)
- [ ] (해당 시) `.cursor/rules/agents/`, `.cursor/rules/skills/` 하위 디렉토리
- [ ] `logs/external_agents/` 쓰기 권한

---

## 8. 3개 CLI 비교 요약

| 항목 | Claude Code | Codex CLI | Cursor Agent |
|------|-----------|----------|------------|
| 정의 파일 | `.claude/agents/*.md` | `~/.codex/agents/*.md` | `.cursor/rules/agents/*.mdc` |
| 팀 메시지 | `SendMessage` 도구 | 파일 폴백 | 파일 폴백 |
| 작업 큐 | `TaskCreate` 도구 | 파일 폴백 | 파일 폴백 |
| 자동 트리거 | description 매칭 | 외부 라우터 | `.mdc` 매칭(설정 의존) |
| Plugin | `/plugin install` | 미확인 | 미확인 |
| 환경 플래그 | `EXPERIMENTAL_AGENT_TEAMS=1` | 없음 | 없음 |
| 강점 영역 | 메인 오케스트레이션, 팀 통신 | 코드 수정·리뷰·테스트 | 분석·문서·일정 |

---

## 9. 우리 프로젝트(PRST_N_FM)에서의 역할 분담

`CLAUDE.md`의 자동 트리거 표를 그대로 활용:

| 트리거 키워드 | 적절한 CLI |
|------------|----------|
| "구현해", "수정해" (단순) | Codex |
| "리뷰해" (코드) | Codex review |
| "EOD", "일정", "상태 보고" | Cursor Agent |
| "분석해", "조사해" (코드 구조) | Cursor Agent |
| "구현해" (복잡, 여러 파일) | Claude Code 서브에이전트 |
| "팀", "토론", "검토회의" | Claude Code tmux 팀 |

본 어댑터는 Cursor Agent 호출을 표준화하여, 위 트리거가 발동했을 때 **harness 6패턴의 어느 패턴인지 명시적으로 선택**되도록 함.

---

**End of Cursor Agent Adapter.**
