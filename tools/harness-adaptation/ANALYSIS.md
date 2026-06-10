# Harness 레포 팩트 기반 분석 보고서

> 출처: `tools/harness-adaptation/reference/harness/` (revfactory/harness @ v1.2.0, Apache-2.0)
> 작성: 2026-05-11 — engineer-backend / reviewer-code / reviewer-science 3개 서브에이전트 병렬 분석 결과 통합
> **규칙**: 모든 사실 주장에 `파일경로:라인번호` 또는 직접 인용 첨부. 추측은 §검증 필요 절에만 기록.

---

## 1. 한 줄 요약

Harness는 **"도메인 설명 한 문장"을 입력받아 `.claude/agents/` + `.claude/skills/` + `_workspace/` 트리플로 변환하는 Claude Code 메타-스킬**이다 (`plugin.json:3`). 6개 사전 정의 아키텍처 패턴(Pipeline / Fan-out·Fan-in / Expert Pool / Producer-Reviewer / Supervisor / Hierarchical Delegation) 중 LLM이 도메인에 맞춰 선택한다.

---

## 2. 파일 인벤토리

```
harness/
├── .claude-plugin/
│   ├── plugin.json          ─ 매니페스트 (name=harness, version=1.2.0, Apache-2.0)
│   └── marketplace.json     ─ marketplace 등록 메타 (source="./", owner=revfactory)
├── skills/harness/
│   ├── SKILL.md             ─ ★ Phase 0~7 워크플로우 본체 (444줄)
│   └── references/
│       ├── agent-design-patterns.md    ─ 6개 패턴 상세 정의
│       ├── orchestrator-template.md
│       ├── qa-agent-guide.md
│       ├── skill-testing-guide.md
│       ├── skill-writing-guide.md
│       └── team-examples.md
├── docs/
│   ├── quickstart.md
│   └── experimental-dependency.md     ─ CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 의존성
├── _workspace/
│   ├── 01_auditor_repo_audit.md       ─ repo-auditor 실제 산출물
│   ├── 02_content_launch_contents.md  ─ content-creator 산출물
│   ├── 03_scout_outreach_map.md       ─ community-scout 산출물
│   ├── 04_strategist_launch_plan.md   ─ launch-strategist 산출물
│   └── release/
│       ├── audit-2026-04-18.md
│       └── post-m0-audit-2026-04-18.md
├── README.md / README_KO.md / README_JA.md    ─ 3개국어
├── CONTRIBUTING.md / CHANGELOG.md / LICENSE
└── index.html / privacy.html                  ─ 랜딩 페이지
```

---

## 3. plugin.json / marketplace.json 핵심 필드

`plugin.json:1-31`

| 필드 | 값 | 라인 |
|------|---|------|
| `name` | `"harness"` | L2 |
| `version` | `"1.2.0"` | L4 |
| `description` | `"The team-architecture factory for Claude Code — a meta-skill that turns a domain description into an agent team and the skills they use, with six pre-defined team-architecture patterns..."` | L3 |
| `license` | `"Apache-2.0"` | L11 |
| `keywords` | `harness, team-architecture-factory, claude-code-plugin, multi-agent, pipeline, fan-out-fan-in, expert-pool, producer-reviewer, supervisor, hierarchical-delegation` 등 17개 | L12-30 |

**외부 의존성 (`docs/experimental-dependency.md:12-28`)**:
- `TeamCreate`, `SendMessage`, `TaskCreate` 도구 → `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 환경 변수 필요
- `Agent` 도구는 GA(플래그 무관)

**명령어 등록**: 없음. `SKILL.md:299`에 `".claude/commands/" — 아무것도 생성하지 않음` 명시.

---

## 4. SKILL.md 워크플로우 (★ 핵심)

### 4.1 Frontmatter (`SKILL.md:1-4`)

```yaml
name: harness
description: "하네스를 구성합니다. ... (1) '하네스 구성해줘' 요청 시, (2) '하네스 설계' 요청 시, (3) 새로운 도메인/프로젝트에 대한 하네스 기반 자동화 체계를 구축할 때 ..."
```

### 4.2 Phase 0~7 (워크플로우 전체)

| Phase | 라인 | 책임 | 검증 가능 산출물 |
|-------|------|------|----------------|
| **0. 현황 감사** | L19-35 | `.claude/agents/`, `.claude/skills/`, `CLAUDE.md` 읽고 신규/확장/유지보수 분기 | 파일 시스템 읽기 결과 |
| **1. 도메인 분석** | L37-43 | 코드베이스 탐색, 사용자 숙련도 감지 | 없음 (LLM 내부 판단) |
| **2. 팀 아키텍처 설계** | L44-76 | 실행 모드(팀/서브에이전트/하이브리드) + 6개 패턴 중 선택 | 패턴 선택 명시 |
| **3. 에이전트 정의 생성** | L78-99 | `.claude/agents/{name}.md` 작성. **모든 에이전트는 `model: "opus"`**(L87) | 파일 존재, frontmatter |
| **4. 스킬 생성** | L101-167 | `.claude/skills/{name}/SKILL.md` (Progressive Disclosure 3단계, 본문 ≤500줄) | 파일 존재, references/ 분리 |
| **5. 통합·오케스트레이션** | L169-288 | `_workspace/{phase}_{agent}_{artifact}.{ext}` 컨벤션(L227-228). 데이터 전달 4전략(메시지/태스크/파일/반환값) | `_workspace/` 파일 |
| **6. 검증·테스트** | L290-343 | should-trigger 8~10개 + should-NOT-trigger 8~10개(L329-335), with-skill vs without-skill A/B(L313-317) | 트리거 쿼리 목록, A/B 결과 |
| **7. 하네스 진화** | L349-415 | 피드백 수집 → 수정 매핑(L364-372) → CLAUDE.md 변경 이력 테이블 | 변경 이력 테이블 |

### 4.3 강제 규칙

| 규칙 | 출처 |
|------|------|
| 에이전트 정의 파일 없이 Agent 도구 prompt에 역할 직접 넣는 것 금지 | `SKILL.md:80` |
| 모든 에이전트는 `model: "opus"` | `SKILL.md:87` |
| SKILL.md 본문 ≤500줄, 초과 시 `references/` 분리 | `SKILL.md:147` |
| QA 에이전트는 `general-purpose` 타입 (Explore는 읽기 전용이라 검증 스크립트 실행 불가) | `SKILL.md:96` |
| `.claude/commands/`는 아무것도 생성하지 않음 | `SKILL.md:299, 426` |
| CLAUDE.md에는 포인터만 등록, 에이전트·스킬 목록 기입 금지 | `SKILL.md:264-265` |
| 에이전트 팀은 세션당 한 팀만 활성화 | `SKILL.md:89`, `agent-design-patterns.md:31` |

### 4.4 사용자 입력

전 워크플로우에서 사용자가 제공해야 하는 입력은 **도메인 설명 한 문장**뿐 (`"build a harness for <domain>"` 또는 `"하네스 구성해줘"`). 나머지는 LLM이 자율 판단.

---

## 5. 6개 아키텍처 패턴 정확 추출

권위 있는 명칭 출처: `plugin.json:3` 영문 열거. 상세 정의: `agent-design-patterns.md:83-161`.

### 5.1 Pipeline (`agent-design-patterns.md:88-95`)
- 적용: 순차 의존 작업, 각 단계가 이전 단계 산출물에 강하게 의존
- 팀 구성: "순차 의존이 강해 팀 모드의 이점이 제한적. 단, 파이프라인 내 병렬 구간이 있으면 팀 모드 유용" (L93)
- 산출: `_workspace/{phase}_{agent}_{artifact}.{ext}` 단계별 파일

### 5.2 Fan-out/Fan-in (`agent-design-patterns.md:99-108`)
- 적용: 동일 입력에 대해 서로 다른 관점/영역 분석
- 팀 구성: "**반드시 에이전트 팀으로 구성해야 한다**" (L107)
- 산출: 통합 에이전트가 최종 보고서, 중간 결과는 `_workspace/`

### 5.3 Expert Pool (`agent-design-patterns.md:111-119`)
- 적용: 입력 유형에 따라 다른 처리
- 팀 구성: "서브 에이전트가 더 적합. 필요한 전문가만 호출하므로 상시 팀이 불필요" (L119)
- 산출: 라우터가 선택한 전문가 1개의 반환값

### 5.4 Producer-Reviewer (`agent-design-patterns.md:121-131`)
- 적용: 산출물 품질 보장 필요 + 객관적 검증 기준 존재
- 팀 구성: "SendMessage로 생성자↔검증자 실시간 피드백 교환. 최대 재시도 2~3회 설정 필수" (L130-131)
- 산출: 검증 통과 후 최종, 실패 시 재생성 루프

### 5.5 Supervisor (`agent-design-patterns.md:135-146`)
- 적용: 작업량 가변 / 런타임 동적 분배 필요
- 팀 구성: "팬아웃은 사전 고정 분배, 감독자는 진행 보며 동적 조정" (L144)
- 산출: 동적 분배 결과의 통합

### 5.6 Hierarchical Delegation (`agent-design-patterns.md:149-161`)
- 적용: 문제가 자연스럽게 계층적 분해
- 팀 구성: "에이전트 팀은 중첩 불가. 1단계는 팀, 2단계는 서브에이전트로 구현하거나 평탄화" (L160). 깊이 3단계 이상 금지 (L159)
- 산출: 총괄-팀장-실무자 트리에서 최종 취합

---

## 6. L1 / L2 / L3 레이어 분리 (CLI 추상화 핵심)

### L1 — Claude Code 종속

| 요소 | 출처 |
|------|------|
| `.claude-plugin/plugin.json` 매니페스트 (`/plugin install`) | `plugin.json:1-31` |
| `.claude-plugin/marketplace.json` | 파일 존재 |
| `TeamCreate` / `SendMessage` / `TaskCreate` 도구 호출 | `SKILL.md:47-53`, `experimental-dependency.md:12-19` |
| `.claude/agents/` / `.claude/skills/` 디렉토리 규약 | `SKILL.md:80-93, 103` |
| `~/.claude/skills/harness/` 전역 설치 경로 | `README.md:107-111` |
| `subagent_type` / `model: "opus"` Agent 파라미터 | `SKILL.md:87` |
| YAML frontmatter `name:` / `description:` 트리거 메커니즘 | `SKILL.md:1-4` |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | `experimental-dependency.md:12-28` |

### L2 — CLI-agnostic 핵심 IP (★ 우리가 추출할 자산)

| 요소 | 출처 |
|------|------|
| 6개 패턴 정의 전체 | `agent-design-patterns.md:83-161` |
| 모드 선택 의사결정 트리 (에이전트 2개 이상? 통신 필요?) | `agent-design-patterns.md:62-77` |
| Phase 0~7 메타-프롬프트 워크플로우 | `SKILL.md:18-415` |
| Progressive Disclosure 3단계 로딩 | `SKILL.md:138-158` |
| 에이전트 분리 기준 4축 (전문성·병렬성·컨텍스트·재사용성) | `agent-design-patterns.md:253-260` |
| 스킬 description "pushy" 작성 원칙 | `SKILL.md:118-125` |
| `_workspace/{phase}_{agent}_{artifact}` 파일 컨벤션 | `SKILL.md:226-229` |
| Harness Evolution (델타 피드백 루프) | `README.md:62-74` |
| 팀 크기 가이드라인 (소 2-3 / 중 3-5 / 대 5-7) | `SKILL.md:237-244` |

### L3 — PRST_N_FM 기존 자산과 중복

| Harness | 우리 자산 | 중복도 |
|---------|---------|--------|
| orchestrator + 팀원 정의 | `CLAUDE.md` 팀원 목록 7개 | 높음 — 이미 분리 완료 |
| CLAUDE.md 트리거 키워드 표 | `CLAUDE.md` 자동 트리거 키워드 표 | 완전 — 우리가 더 세분화 |
| 의사결정 트리 (팀 vs 서브에이전트 2갈래) | `CLAUDE.md` 5단계 트리 (tmux/codex/cursor-agent/서브에이전트/직접) | 우리가 더 구체적 |
| `_workspace/` 중간 파일 컨벤션 | `logs/external_agents/` | 부분 — 경로·형식 다름 |
| Phase 7 진화 메커니즘 | 없음 | 우리 부재 — 도입 가치 |
| Phase 6 should-trigger/should-NOT-trigger | 없음 | 우리 부재 — 도입 가치 |

---

## 7. CLI 추상화 매핑 (보존/변환)

| L1 (Claude Code) | Codex CLI | Cursor Agent |
|---|---|---|
| `.claude-plugin/plugin.json` | `~/.codex/agents/` (SaehwanPark/meta-harness 규약, `README.md:250`) | `.cursor/rules/*.mdc` |
| `skills/SKILL.md` frontmatter | `codex exec --instructions <file>` | `.cursor/rules/` `alwaysApply` 또는 `description` |
| `TeamCreate` + `SendMessage` | `codex exec` 병렬 프로세스 spawning | `cursor-agent -p` 다중 호출 + `agent-wrapper.sh` 집계 |
| `.claude/agents/{name}.md` | `~/.codex/agents/{name}.md` | `.cursor/rules/agents/{name}.mdc` |
| `EXPERIMENTAL_AGENT_TEAMS=1` | 불필요 | 불필요 |
| `model: "opus"` | `--model claude-opus-4-7` | 설정 파일 모델 지정 |

우리 `scripts/agent-wrapper.sh`가 이 매핑의 접합점.

---

## 8. _workspace/ 산출물 품질 패턴 (차용 가치 있음)

`_workspace/` 4개 실예시 + `release/` 2개 분석:

| 양식 | 출처 | 차용 가치 |
|------|------|---------|
| 점수 + PASS/FAIL 매트릭스 | `01_auditor_repo_audit.md` 카테고리 점수 8/10·4/10·3/10·7/10 | 약리학 스코어 카테고리 평가 |
| 수치 기반 KPI (시간대별 목표) | `04_strategist_launch_plan.md` `D-Day +6h: 100+`, `D+7: 800+` | 파이프라인 단계별 메트릭 목표 |
| Impact ÷ Effort 우선순위 | `01_auditor:129-143` 10개 권장사항 정렬 | 후보 펩타이드 우선순위 |
| 에이전트 귀속 테이블 | `post-m0-audit:113-130` 파일별·에이전트별 편집 추적 | 다단계 파이프라인 책임 추적 |
| 라인 번호 인용 (`EN(L20)`, `KO(L24)`) | `post-m0-audit` 영역 PASS 표시 | 검증자 재현 가능한 인용 |
| 에이전트 간 명시적 의존 | `04_strategist`가 `Audit R4`, `R9` 등으로 `01_auditor` 권고 번호 참조 | 단계 간 데이터 흐름 추적 |

---

## 9. 환각 위험 지점 식별 (reviewer-science)

| 단계 | 위험 | 근거 |
|------|------|------|
| Phase 1 도메인 분석 | "핵심 작업 유형 식별"의 출력 형식 미지정 → LLM 자유 기술 | `SKILL.md:39-40` |
| Phase 2 패턴 선택 | 선택 이유가 파일에 기록 안 됨 → 사후 감사 불가 | `SKILL.md:44-76` |
| Phase 0 분기 | "기존 확장" vs "유지보수" 경계 모호 | `SKILL.md:24-26` |
| Phase 2 모드 선택 | "팀 통신이 구조적으로 불필요"의 기준 부재 | `README.md:57-58` |
| Phase 6 A/B 평가 | assertion 정의는 "객관적 검증 가능" 시에만 → 그 외엔 주관 | `SKILL.md:317` |

**실제 발생 사례**: `post-m0-audit:64` — content-creator 에이전트가 READ-ONLY인 `plugin.json`을 무단 편집한 Critical 결함. 패턴 정의·범위 선언 부재에서 비롯.

---

## 10. PRST_N_FM 도메인 적합성 사전 검토

### 적합한 패턴
- **Producer-Reviewer**: 후보 펩타이드 생성 ↔ `reviewer-science` 검증 구조에 자연 매핑
- **Fan-out/Fan-in**: Silo A(3-Arm NIM) ↔ Silo B(PyRosetta) 듀얼 파이프라인 통합 보고
- **`_workspace/` + 에이전트 귀속 테이블**: 약리학 파라미터 수치 오류 발생 지점 추적

### 부적합·주의 패턴
- **Phase 1 "사용자 숙련도 감지 → 톤 조절"**: 우리 도메인은 톤보다 수치 정확성 — 불필요 단계
- **Phase 7 "에이전트 반복 실패 패턴 인식"**: 약리학 파라미터 오류는 매번 다른 값으로 나타나 패턴 인식 어려움 (`SKILL.md:392`)
- **"+60% 품질 개선" 일반화 불가**: README:264-273의 n=15 측정은 소프트웨어 태스크. 약리학 정확도 일반화 근거 없음

### 도메인 환각 시나리오
| 시나리오 | 사례 |
|---------|------|
| H-01: 파라미터 테이블 오기재 | Radzicka-Wolfenden S=1.15 (정답 1.83) |
| H-02: 부호·방향 역전 | Boman Index 부호 오류 → NSGA-II 순위 역전 |
| H-03: 척도 혼용 | Kyte-Doolittle/Wimley-White/Eisenberg 섞임 → 상대 비교 무의미 |
| H-04: PyRosetta 채점 함수 환각 | ref2015 가중치 기억 재생 |
| H-05: 반감기 참조 종 혼동 | DIWV Pro half-life=20 (정답 30) — 효모 vs 포유류 |

---

## 11. 코드 품질 관찰

- Phase 0 God-Method 성격: 신규/확장/유지보수 3분기 모두 수용 (`SKILL.md:18-35`)
- Phase 7-5 (운영/유지보수, `SKILL.md:395-415`)는 별도 SKILL.md로 분리 가능
- SKILL.md 자체가 444줄 — 500줄 상한(`SKILL.md:147`)에 근접
- 패턴 간 부분 겹침: Pipeline↔Supervisor, Fan-out/Fan-in↔Producer-Reviewer
- description 작성 원칙이 "Why가 아닌 What" 위주 — 자기 모순 (`SKILL.md:118-131`)
- Hierarchical Delegation의 "팀 중첩 불가" 제약 (`agent-design-patterns.md:160`) → 패턴 정의와 구현 현실의 괴리

---

## 12. §검증 필요

본문만으로 확정 불가, 추측 표시:

| ID | 항목 | 비고 |
|----|------|------|
| VR-01 | `/harness:evolve` 실제 구현 여부 | `README.md:63` 언급, `skills/` 디렉토리에 파일 없음 |
| VR-02 | "+60% 품질 향상" 수치 (n=15, author-measured) | `README.md:264-273` 자체 시인. 동료 심사 없음. 우리 도메인 일반화 불가 |
| VR-03 | "에이전트 팀이 서브에이전트보다 품질 높다" 주장 | `SKILL.md:48` 정량 데이터 없음 |
| VR-04 | "에이전트 팀 세션당 한 팀" 제약의 v2.x 현재 상태 | `SKILL.md:89` 명시이나 릴리스 노트 미확인 |
| VR-05 | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 현 상태 | 문서 last updated 2026-04-18, 현재 2026-05-11 — GA 승격 가능성 |
| VR-06 | `/plugin install harness@harness`의 멀티-CLI 동작 | Codex CLI / Cursor Agent에서 동일 작동 여부 미확인 |
| VR-07 | `model: "opus"` 강제의 비용 정당성 | 우리 vLLM 로컬 모델 대비 트레이드오프 본문 미확인 |
| VR-08 | `SaehwanPark/meta-harness`와 우리 `scripts/agent-wrapper.sh` 호환 범위 | `README.md:250` 언급 외 미확인 |
| VR-09 | 500줄 상한의 컨텍스트 품질 영향 근거 | 구체 수치 근거 본문 없음 |

---

## 13. 결론 — 채택 전략

**최소 비용 최대 효과 경로**:
1. **L2(핵심 IP)만 추출**: 6개 패턴 정의 + Phase 워크플로우 + `_workspace/` 컨벤션 + 검증 게이트
2. **L1(Claude Code 의존) 폐기**: `.claude-plugin/`, `/plugin install`, `EXPERIMENTAL_*` 플래그
3. **L3(우리 자산과 중복) 통합**: 기존 `CLAUDE.md` 의사결정 트리에 6개 패턴 명칭만 명시적 매핑. 우리 orchestrator + 5 teammate는 사실상 Supervisor 또는 Fan-out/Fan-in의 실구현
4. **CLI 추상화**: `scripts/agent-wrapper.sh`를 추가 어댑터로 활용해 Codex / Cursor 변환
5. **도메인 환각 가드 추가**: §9의 위험 + §10의 H-01~05를 우리 PROMPT_TEMPLATE에 강제 규칙으로

→ `PROMPT_TEMPLATE.md`, `INTEGRATION_PLAN.md`, `checklist.md`로 이어짐.
