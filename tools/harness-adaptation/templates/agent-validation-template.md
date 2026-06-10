# Agent Validation Report — `{{AGENT_NAME}}`

> harness Stage 4 산출물. 신규/변경된 에이전트의 should-trigger / should-NOT-trigger 세트와 A/B 비교 결과를 보존한다.
> 파일명 규칙: `_workspace/release/agent-{{AGENT_NAME}}-validation-{{YYYY-MM-DD}}.md`

## 0. 메타

| 항목 | 값 |
|------|---|
| Agent name | `{{AGENT_NAME}}` |
| 도입 PR | `#{{PR_NUMBER}}` 또는 커밋 `{{COMMIT_SHA}}` |
| 작성일 | `{{YYYY-MM-DD}}` |
| 작성자 | `{{AUTHOR}}` |
| harness 패턴 | `<Pipeline | Fan-out/Fan-in | Expert Pool | Producer-Reviewer | Supervisor | Hierarchical Delegation>` |
| CLAUDE.md 트리 위치 | `<1순위 | 2순위 | 3순위 | 4순위>` |

## 1. 에이전트 정의 요약

- **핵심 역할** (1문장):
- **입력 프로토콜**:
- **출력 프로토콜**:
- **협업 인터페이스** (어떤 다른 에이전트와 통신하는지):
- **에러 핸들링**:

## 2. 패턴 선택 정당화 (Phase 2)

- **왜 이 패턴인가** (1~3 문장):
- **대안 패턴 검토**:
  - <대안 1>: 기각 이유
  - <대안 2>: 기각 이유

## 3. should-trigger 쿼리 (≥8)

| # | 쿼리 | 라우팅 기대 | 실측 라우팅 | PASS? |
|---|------|----------|----------|------|
| 1 | | `{{AGENT_NAME}}` | | |
| 2 | | `{{AGENT_NAME}}` | | |
| 3 | | `{{AGENT_NAME}}` | | |
| 4 | | `{{AGENT_NAME}}` | | |
| 5 | | `{{AGENT_NAME}}` | | |
| 6 | | `{{AGENT_NAME}}` | | |
| 7 | | `{{AGENT_NAME}}` | | |
| 8 | | `{{AGENT_NAME}}` | | |

**Coverage**: __/8 (≥80% 목표)

## 4. should-NOT-trigger 쿼리 (≥8, near-miss 포함)

| # | 쿼리 | 라우팅 기대 | 실측 라우팅 | PASS? |
|---|------|----------|----------|------|
| 1 | | <다른 에이전트> | | |
| 2 | | <다른 에이전트> | | |
| 3 | | <다른 에이전트> | | |
| 4 | | <다른 에이전트> | | |
| 5 | | <다른 에이전트> | | |
| 6 | | <다른 에이전트> | | |
| 7 | | <다른 에이전트> | | |
| 8 | | <다른 에이전트> | | |

**False-positive rate**: __/8

## 5. A/B 비교 (Phase 6)

### 입력
- 시드 입력: <간단한 설명 또는 파일 경로>
- 입력 파일: `_workspace/{{NN}}_{{seed_agent}}_{{seed_artifact}}.json`

### 결과 산출물
- **with-`{{AGENT_NAME}}`**: `_workspace/release/agent-{{AGENT_NAME}}-validation-{{YYYY-MM-DD}}-with.md`
- **without-`{{AGENT_NAME}}`**: `_workspace/release/agent-{{AGENT_NAME}}-validation-{{YYYY-MM-DD}}-without.md`

### 측정 기준

| 메트릭 | with | without | Δ | 평가 |
|--------|------|---------|---|------|
| <메트릭 1> | | | | |
| <메트릭 2> | | | | |

### 정성 평가

<리뷰어 코멘트>

## 6. CLAUDE.md 갱신 항목

- [ ] 자동 트리거 키워드 표
- [ ] §"팀원 목록"
- [ ] §"Harness Pointer / Stage 적용 이력"

## 7. §검증 필요

| ID | 항목 |
|----|------|
| VR-{{AGENT_NAME}}-01 | |
| VR-{{AGENT_NAME}}-02 | |

---

**End of Validation Report.**
