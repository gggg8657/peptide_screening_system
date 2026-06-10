# Codex CLI Adapter — Harness Universal Prompt

> `PROMPT_TEMPLATE.md`의 추상 명령을 **OpenAI Codex CLI 환경**으로 변환하는 어댑터.
> 우리 프로젝트는 `scripts/agent-wrapper.sh codex ...` 래퍼를 거쳐 호출함 (`CLAUDE.md` 팀원 목록).

---

## 1. 파일 위치 매핑

| 추상 (PROMPT_TEMPLATE) | Codex CLI 실제 | 비고 |
|----------------------|--------------|------|
| 에이전트 정의 | `~/.codex/agents/{name}.md` 또는 `instructions/{name}.md` | meta-harness 규약 (`README.md:250`) |
| 스킬 정의 | `~/.codex/skills/{name}/` 또는 `instructions/{name}.md` | Codex는 단일 instructions 파일 모델 |
| references | `instructions/{name}/refs/*.md` | 조건부 `--context-file`로 주입 |
| 워크스페이스 | `_workspace/{phase}_{agent}_{artifact}.{ext}` | 동일 컨벤션 유지 |
| 포인터 | `CLAUDE.md` 또는 `AGENTS.md` (프로젝트 컨벤션) | 우리는 `CLAUDE.md` 그대로 사용 |

> §검증 필요: Codex CLI의 plugin 시스템(공식 marketplace)이 있는지는 `ANALYSIS.md VR-06`에서 미확인. 안전한 가정은 "단일 instructions 파일 + `--context-file` 주입" 모델.

---

## 2. 에이전트 호출

우리 래퍼 사용:

```bash
./scripts/agent-wrapper.sh codex exec \
  --instructions ~/.codex/agents/{name}.md \
  "<태스크 설명>"
```

또는 직접:

```bash
codex exec --instructions <path> --model claude-opus-4-7 "<prompt>"
```

**규칙**:
- ❌ 인라인 프롬프트에 긴 역할 정의 직접 작성 금지 (재사용성 ↓)
- ✅ `--instructions` 파일로 역할 정의, 태스크만 인자로

---

## 3. 팀 모드 — 폴백 전략

Codex CLI는 `TeamCreate` / `SendMessage` 등 메시지 기반 팀 API가 (확인된 한) 없음 → **파일 기반 데이터 전달** 폴백 (Phase 5의 `_workspace/` 컨벤션).

### 패턴별 변환

**Pipeline**:
```bash
# 순차 실행
./scripts/agent-wrapper.sh codex exec --instructions ~/.codex/agents/auditor.md \
  "출력 → _workspace/01_auditor_audit.md"

./scripts/agent-wrapper.sh codex exec --instructions ~/.codex/agents/scorer.md \
  --context-file _workspace/01_auditor_audit.md \
  "출력 → _workspace/02_scorer_score.md"
```

**Fan-out/Fan-in**:
```bash
# 병렬 실행 (백그라운드)
./scripts/agent-wrapper.sh codex exec ... &
./scripts/agent-wrapper.sh codex exec ... &
./scripts/agent-wrapper.sh codex exec ... &
wait

# 통합
./scripts/agent-wrapper.sh codex exec --instructions ~/.codex/agents/integrator.md \
  --context-file _workspace/*.md \
  "출력 → _workspace/05_integrator_report.md"
```

**Producer-Reviewer**:
```bash
# 재시도 루프 (최대 2~3회 — agent-design-patterns.md:131)
for i in 1 2 3; do
  ./scripts/agent-wrapper.sh codex exec --instructions ~/.codex/agents/producer.md ...
  ./scripts/agent-wrapper.sh codex exec --instructions ~/.codex/agents/reviewer.md ...
  # reviewer 결과에 PASS 마커 있으면 break
done
```

**Supervisor**: 공유 작업 큐를 단순 파일로 (`_workspace/queue.md`). supervisor가 큐 갱신, 워커가 폴링.

**Expert Pool**: 라우터 에이전트 1회 호출 → 그 결과로 어느 전문가를 호출할지 결정.

**Hierarchical Delegation**: 평탄화 권장 (`agent-design-patterns.md:160`).

---

## 4. 모델 지정

```bash
codex exec --model claude-opus-4-7 ...   # 또는
codex exec --model gpt-4o ...
```

원본 harness는 `opus` 강제이나 (`SKILL.md:87`), Codex의 모델 선택은 우리 비용/성능 트레이드오프 실험에 따름 (`project_agent_flow_benchmark.md` 참조).

---

## 5. 트리거 메커니즘

Codex는 자동 description 매칭이 (확인된 한) 없음. → **명시적 호출** 또는 **CLAUDE.md 트리거 표 + 인간 운영자 라우팅**.

우리 CLAUDE.md의 자동 트리거 키워드 표는 인간 또는 본 Claude Code 세션이 라우터 역할 → 적절한 Codex 호출로 변환.

```text
사용자: "코드 리뷰해줘 backend/foo.py"
       ↓
Claude Code (라우터): CLAUDE.md 트리거 표 매칭 → codex review
       ↓
./scripts/agent-wrapper.sh codex review backend/foo.py
```

---

## 6. 로그·감사

`./scripts/agent-wrapper.sh`가 `logs/external_agents/`에 모든 codex 호출 기록 (`CLAUDE.md` 필수 행동 §3).

산출물 검증 시 이 로그 + `_workspace/` 파일로 추적.

---

## 7. 환경 검증 체크리스트

작업 시작 전:

- [ ] `codex --version` 정상 응답
- [ ] `./scripts/agent-wrapper.sh codex --help` 정상 출력
- [ ] `~/.codex/agents/` 디렉토리 존재 (또는 프로젝트 `instructions/`)
- [ ] `logs/external_agents/` 쓰기 권한
- [ ] (선택) Codex 모델 API 키 환경변수

---

## 8. Claude Code 어댑터와의 차이 요약

| 항목 | Claude Code | Codex CLI |
|------|-----------|----------|
| 팀 메시지 | `SendMessage` 도구 | 파일 기반 폴백 (`_workspace/`) |
| 동적 작업 큐 | `TaskCreate` 도구 | `_workspace/queue.md` 폴링 |
| 트리거 매칭 | description 자동 매칭 | 인간 또는 외부 라우터 |
| Plugin marketplace | `/plugin install` | 미확인 (§검증 필요 VR-06) |
| 환경 플래그 | `EXPERIMENTAL_AGENT_TEAMS=1` | 불필요 |

---

**End of Codex CLI Adapter.**
