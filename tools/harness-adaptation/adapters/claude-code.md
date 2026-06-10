# Claude Code Adapter — Harness Universal Prompt

> `PROMPT_TEMPLATE.md`의 추상 명령을 **Claude Code CLI 환경**으로 변환하는 어댑터.
> 원본 harness가 사실상 Claude Code 네이티브이므로 가장 직접적 매핑.

---

## 1. 파일 위치 매핑

| 추상 | Claude Code 실제 | 출처 |
|------|----------------|------|
| 에이전트 정의 | `.claude/agents/{name}.md` | `SKILL.md:80-93` |
| 스킬 정의 | `.claude/skills/{name}/SKILL.md` | `SKILL.md:103` |
| 스킬 references | `.claude/skills/{name}/references/*.md` | `SKILL.md:138-158` |
| 전역 스킬 | `~/.claude/skills/{name}/` | `README.md:107-111` |
| 워크스페이스 | `_workspace/{phase}_{agent}_{artifact}.{ext}` | `SKILL.md:226-229` |
| 포인터 | `CLAUDE.md` (목록 X, 변경 이력 O) | `SKILL.md:264-265` |

---

## 2. 에이전트 호출

```text
# 본 세션 내 서브에이전트 (CLI에 노출되는 Agent tool 사용)
Agent({
  description: "...",
  subagent_type: "<built-in or custom>",
  prompt: "<에이전트 정의 파일을 읽고 그 역할로 작업하세요. 파일: .claude/agents/{name}.md>"
})
```

**규칙** (`SKILL.md:80`):
- ❌ Agent tool prompt에 역할을 인라인으로 작성 금지
- ✅ 반드시 `.claude/agents/{name}.md` 파일을 정의하고 prompt에 그 파일을 참조하라고 지시

---

## 3. 팀 모드 vs 서브에이전트 모드

### 팀 모드 (Fan-out/Fan-in, Producer-Reviewer, Supervisor 권장)

`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 필요 (`experimental-dependency.md:12`).

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

사용 가능한 도구 (loaded via ToolSearch in current session):
- `TeamCreate` — 팀 생성
- `SendMessage` — 팀원 간 메시지
- `TaskCreate` / `TaskUpdate` / `TaskList` — 공유 작업 큐

**제약** (`SKILL.md:89`, `agent-design-patterns.md:31`):
- 세션당 한 팀만 활성화
- 팀원이 팀 생성 불가 (Hierarchical Delegation 깊이 ≤ 2)

### 서브에이전트 모드 (Pipeline, Expert Pool 권장)

플래그 무관, `Agent` 도구만 사용:
```text
Agent({ description, subagent_type, prompt, run_in_background? })
```

---

## 4. 우리 프로젝트(PRST_N_FM)에 매핑

| 추상 | PRST_N_FM 실제 |
|------|--------------|
| 에이전트 정의 | `CLAUDE.md` 팀원 목록 + (필요 시) `.claude/agents/` 신설 |
| 스킬 정의 | 본 디렉토리 또는 `.claude/skills/` |
| 워크스페이스 | `_workspace/` 신설 또는 `logs/external_agents/` 재활용 |
| tmux 풀팀 모드 | `./scripts/launch_agent_team.sh` (6명 분산 tmux) |
| 본 세션 팀 모드 | `TeamCreate` + Agent tool 병렬 |

---

## 5. 트리거 메커니즘

Claude Code는 SKILL.md의 `description:` 필드를 기반으로 자동 매칭. **pushy하게 작성** (`SKILL.md:118-125`):

✅ 좋음: `"하네스를 구성합니다. (1) '하네스 구성해줘' 요청 시, (2) '하네스 설계' 요청 시, (3) ..."`

❌ 나쁨: `"Builds team configurations"`

---

## 6. 모델 지정

원본 규칙: 모든 에이전트 `model: "opus"` 강제 (`SKILL.md:87`).

우리 환경:
- 본 세션: 자동으로 Opus 4.7 (1M context)
- 서브에이전트: `Agent` 호출 시 `model` 파라미터로 명시 가능

비용 트레이드오프는 §검증 필요(`ANALYSIS.md VR-07`) — 우리 vLLM 로컬 모델 대비 효율 미확인.

---

## 7. 산출물 검증 (Phase 6)

A/B 비교:
```text
# 같은 입력을 두 모드로
Agent({ subagent_type: "general-purpose", prompt: "<with skill loaded>" })
Agent({ subagent_type: "general-purpose", prompt: "<without skill>" })
```

QA 에이전트는 **`general-purpose` 타입 의무** (`SKILL.md:96`): `Explore`는 읽기 전용이라 검증 스크립트 실행 불가.

---

## 8. 환경 검증 체크리스트

작업 시작 전:

- [ ] Claude Code v2.x 이상 (`quickstart.md:12`)
- [ ] (팀 모드 시) `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 환경변수
- [ ] (해당 시) `~/.claude/skills/harness/` 또는 프로젝트 `.claude/skills/` 존재
- [ ] `CLAUDE.md`에 포인터 블록 자리 확보

---

**End of Claude Code Adapter.**
