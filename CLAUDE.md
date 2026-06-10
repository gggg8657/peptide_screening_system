# CLAUDE.md — PRST_N_FM 프로젝트 행동 규칙

## 작업 위임 의사결정 트리

모든 작업 요청 시 아래 순서로 실행 방식을 판단한다.

### 1순위: tmux team-mate 모드 (`/team`)

**패턴**: **Fan-out/Fan-in** (동일 입력에 대해 여러 관점 병렬 분석 → 통합) 또는 **Supervisor** (orchestrator가 동적으로 팀원에 작업 분배)
— 근거: `tools/harness-adaptation/ANALYSIS.md §5.2, §5.5`

**조건**: 아래 중 하나 이상 해당 시
- 팀 토론/검토가 필요한 작업 (설계 결정, 아키텍처 논의)
- 여러 관점의 리뷰가 동시에 필요한 작업
- 사용자가 "팀", "토론", "리뷰", "검토" 키워드를 사용한 경우
- 복잡한 작업에서 사용자가 실시간 모니터링을 원하는 경우

**실행**: tmux 세션 확인 → 있으면 attach 안내, 없으면 `./scripts/launch_agent_team.sh` 실행 안내

### 2순위: 외부 에이전트 (codex / cursor-agent)

**패턴**: **Expert Pool** (입력 유형에 따라 다른 전문가 호출 — codex=코드, cursor-agent=분석)
— 근거: `tools/harness-adaptation/ANALYSIS.md §5.3`

**codex** — 코드 수정/생성에 특화:
- 단일 파일 또는 명확한 스펙의 코드 구현
- 코드 리뷰 (`codex review`)
- 테스트 생성
- 반복적 수정 (lint fix, 리팩토링)

**cursor-agent** — 분석/일정에 특화:
- EOD 보고 + 일정 관리
- 코드 분석, 구조 파악
- 문서 작성/갱신

**실행**: `./scripts/agent-wrapper.sh <agent> <args>` — 요청/결과가 CLI에 표시되고 로그 기록됨.
  - 분석을 **파일 기반 Pipeline** 으로 단계별 실행할 때: [`tools/harness-adaptation/cursor-cli/`](tools/harness-adaptation/cursor-cli/) 프롬프트 + [`./scripts/cursor/harness_invoke.sh`](scripts/cursor/harness_invoke.sh) (`list` / `run` / `chain`; 기본 dry-run, 실호출 `--execute`).

### 3순위: 내장 서브에이전트 (Agent tool)

**패턴 (작업 형태별)**:
- **Pipeline** — 순차 의존 작업 (예: 시퀀스 검증 → 변이 적용 → 도킹 → 채점)
- **Producer-Reviewer** — engineer-backend 생성 ↔ reviewer-science/code 검증 루프 (재시도 ≤3)
- **Fan-out/Fan-in** — 여러 파일의 병렬 독립 작업 (`/subagent-dev`)

근거: `tools/harness-adaptation/ANALYSIS.md §5.1, §5.4, §5.2`

**조건**: 위 1-2순위로 처리 불가할 때
- 여러 파일에 걸친 복잡한 구현 (engineer-backend)
- 과학적 방법론 검증 (reviewer-science)
- 인프라/환경 구축 (engineer-infra)
- 병렬 독립 작업 (`/subagent-dev`)

### 4순위: 직접 구현

**패턴**: 없음 — 단일 작업, 위임 오버헤드보다 직접 처리가 효율적인 경우.
**경계 조건**: Hierarchical Delegation 평탄화의 결과로도 사용 (계층 분해가 1단계로 충분할 때 — `ANALYSIS.md §5.6`)

**조건**: 간단한 수정, 빠른 확인, 파일 1-2개 수정으로 끝나는 작업

---

## 위임 시 필수 행동

1. **작업 할당 시**: CLI에 대상, 내용, 예상 결과를 명시적으로 출력
2. **결과 수신 시**: CLI에 결과 요약, 변경 파일, 테스트 결과를 출력
3. **로그 기록**: `logs/external_agents/` 에 모든 외부 에이전트 호출 기록
4. **실패 시**: 에러 내용을 사용자에게 보고하고 대안 제시

---

## 자동 트리거 키워드

| 사용자 입력 패턴 | 자동 선택 |
|----------------|---------|
| "팀", "토론", "검토회의", "/team" | tmux team-mate |
| "구현해", "코드 작성", "수정해" (단순) | codex exec |
| "리뷰해" (코드) | codex review |
| "EOD", "일정", "상태 보고" | cursor-agent |
| "분석해", "조사해" (코드 구조) | cursor-agent |
| "구현해" (복잡, 여러 파일) | 서브에이전트 |
| "테스트 수정" | /test-fix 스킬 |
| "디버깅" | /root-cause 스킬 |
| "하네스", "팀 아키텍처", "패턴 선택", "Stage N 진행" | `tools/harness-adaptation/` 참조 |
| "cursor 하네스", `harness_invoke`, 파일 기반 Pipeline(cursor-agent 단계 실행) | `tools/harness-adaptation/cursor-cli/` + `./scripts/cursor/harness_invoke.sh` |
| "논문 조사", "문헌 비교", "선행 연구", "리서치", "research", "literature review" | researcher |
| "약리학", "ADMET", "PK", "PD", "반감기", "친화도", "Boman", "GRAVY", "Instability" | reviewer-pharma |
| "구조", "SS bond", "이황화결합", "GPCR", "수용체", "binding pocket", "생물활성" | reviewer-biology |
| "합성", "modification", "D-amino", "PEG화", "아실화", "킬레이션", "DOTA", "라벨링" | reviewer-chemistry |
| "NSGA", "베이지안", "BO", "GP", "Gaussian Process", "최적화 알고리즘", "통계", "p-value", "수렴" | reviewer-math |
| (다도메인 통합 또는 도메인 모호) | reviewer-science (라우터) |

---

## 프로젝트 컨텍스트

- **프로젝트**: SSTR2 타겟 방사성의약품 후보 스크리닝 AI 파이프라인
- **SST-14**: AGCKNFFWKTFTSC (14aa, Cys3-Cys14 SS bond, FWKT pharmacophore)
- **듀얼 파이프라인**: Silo A (3-Arm NIM), Silo B (PyRosetta mutation+dock)
- **현재 브랜치**: `chore/bio-schedule-sync-20260324`
- **주요 디렉토리**: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/`

## 팀원 목록

| 에이전트 | 역할 | 호출 방식 |
|---------|------|---------|
| orchestrator | 업무 분장, 취합, 의사결정 | Agent (opus) |
| researcher | 논문 검색·문헌 비교·선행 연구 조사 | Agent (sonnet) |
| reviewer-code | OOP/클린코드/테스트 리뷰 | Agent (sonnet) |
| reviewer-science | **라우터·통합 판정** (4개 도메인 리뷰어 조율) | Agent (sonnet) |
| reviewer-pharma | 약리학·ADMET·PK/PD 검증 (Stage 5 가드 직결) | Agent (sonnet) |
| reviewer-biology | 구조·SS bond·GPCR 결합 메커니즘 검증 | Agent (sonnet) |
| reviewer-chemistry | 합성 가능성·modification·DOTA 라벨링 검증 | Agent (sonnet) |
| reviewer-math | NSGA-II·베이지안·통계·수렴 검증 | Agent (sonnet) |
| engineer-backend | 파이프라인/스코어링 구현 | Agent (sonnet) |
| engineer-infra | conda/GPU/CI-CD 인프라 | Agent (sonnet) |
| reviewer-uiux | UI/UX 디자인, 접근성 | Agent (sonnet) |
| codex | 코드 수정/리뷰/테스트 | `./scripts/agent-wrapper.sh codex` |
| cursor-agent | 분석/일정/EOD | `./scripts/agent-wrapper.sh cursor-agent`; 단계별 Pipeline 은 `./scripts/cursor/harness_invoke.sh` 참고 |

## 한국어 사용

- 사용자와의 대화: 한국어
- 코드 주석: 한국어 OK (기존 스타일 유지)
- 커밋 메시지: 한국어 제목 + 영문 상세
- 보고서/문서: 한국어

---

## Harness Pointer

본 프로젝트는 [revfactory/harness](https://github.com/revfactory/harness) (Apache-2.0)의 핵심 IP를 CLI 비종속(Claude Code / Codex CLI / Cursor Agent)으로 추출하여 운영한다.

- **어댑테이션 디렉토리**: `tools/harness-adaptation/`
- **범용 프롬프트**: `tools/harness-adaptation/PROMPT_TEMPLATE.md` — `{{...}}` 플레이스홀더 채워서 사용
- **우리 도메인 예시**: `tools/harness-adaptation/PROMPT_PRST_N_FM_EXAMPLE.md`
- **CLI 어댑터**: `tools/harness-adaptation/adapters/{claude-code,codex-cli,cursor-agent}.md`
- **Cursor CLI 하네스**(실행형): `tools/harness-adaptation/cursor-cli/` — stage 프롬프트 라이브러리 + [`scripts/cursor/harness_invoke.sh`](scripts/cursor/harness_invoke.sh)
- **단계별 로드맵**: `tools/harness-adaptation/INTEGRATION_PLAN.md` (Stage 0~7)
- **체크리스트**: `tools/harness-adaptation/checklist.md`
- **팩트 분석**: `tools/harness-adaptation/ANALYSIS.md`
- **상위 원본**: `tools/harness-adaptation/reference/harness/` (Git submodule, 자동 클론 시 `git submodule update --init` 필요)

**중간 산출물**: `_workspace/{NN}_{agent}_{artifact}.{ext}` 컨벤션 (Stage 1 채택, `_workspace/README.md` 참조)

### Stage 적용 이력

| 날짜 | Stage | 변경 | 사유 |
|------|-------|------|------|
| 2026-05-11 | Stage 0 | `tools/harness-adaptation/` 디렉토리 + submodule 신설 | 어댑테이션 골격 + 원본 보존 (커밋 `2637b1c`) |
| 2026-05-11 | Stage 1 | `_workspace/` 디렉토리 + 파일명 컨벤션 채택 | 다단계 산출물 추적성 (커밋 `5805109`) |
| 2026-05-11 | Stage 5 | `pipeline_local/scripts/pharmacology_guards.py` + 33 회귀 테스트 (2026-05-13 현재 39개) | 약리학 lookup table 환각 차단 (Critical, 커밋 `de5fabb`) |
| 2026-05-11 | Stage 2 | 본 Pointer 블록 + 트리거 키워드 추가 | 발견 가능성 향상 |
| 2026-05-11 | Stage 3 | 위임 트리 1~4순위에 6패턴 명칭 매핑 | 사후 감사 가능성 — 어느 위임이 어느 패턴인지 추적 |
| 2026-05-11 | Stage 4 | PR 템플릿 + 검증 보고서 템플릿 의무화 | 신규 에이전트·스킬 도입 시 should-trigger / NOT-trigger / A-B 비교 강제 |
| 2026-05-11 | Stage 6 | `CHANGELOG.md` + `RETROSPECTIVE_GUIDE.md` + PR 템플릿 보강 | Phase 7 진화 메커니즘 운영화 — 분기 회고 + SemVer 이력 관리 |
| 2026-05-11 | Stage 7 | `.claude/agents/*.md` 6개에 harness 표준 3섹션(입력/출력/에러) 보강 | 기존 에이전트 정의의 검증 가능 형식 정립 (이미 분리되어 있어 신설 불필요) |
| 2026-05-11 | Stage 8a | `researcher` 에이전트 신설 + Stage 4 검증 보고서 | 외부 자료 수집·문헌 비교 전담 — reviewer-science의 "수집" 부담 분리 |
| 2026-05-11 | Stage 8b | reviewer-science → 도메인별 4명(pharma/biology/chemistry/math) 분리, 기존 reviewer-science는 라우터로 재정의 | 도메인 경계 명확화 + 약리학 가드 직결 — 기존 호출 호환성 보장 |
| 2026-05-11 | Stage 8c | `scripts/auto_dispatch.sh` 신설 + orchestrator §"외부 CLI 자동 dispatch" | Codex/Cursor 자동 라우팅·호출·결과 보존 (Expert Pool 키워드 매칭) |
| 2026-05-11 | Stage 8d | End-to-End 사이클 dogfooding — modification_conflict checker 사이클 1회 운영 (71/71 tests, auto_dispatch A-4 결함 발견·수정) | 사이클이 구현→검증→실험→갭→수정→완성 6단계 모두 작동함을 입증. harness 어댑테이션 자체 결함 1건 자체 수정 |
| 2026-05-11 | Stage 8e/8f/8g | VR-cycle-04/07/01 closure — auto_dispatch 라우팅 회귀 테스트 + 사이클 자기 일관성 pytest + C-07 DOTA stoichiometry 규칙 (89/89 tests) | §검증 필요 8건 중 4건 자체 closure. 사이클이 자기 §검증 항목을 50% 닫음 |
| 2026-05-11 | Stage 8h | VR-cycle-09 (H-06 "계산 불가능을 계산 가능한 척") 식별 + 즉시 closure. VR-cycle-02 frame 재정의로 흡수 (93/93 tests) | 3-layer closure (A 하네스 + B 플래너 + C 도메인). 하네스 본질 = "도메인 한계의 정직한 노출", 정확도 보장 X. §검증 필요 9건 중 5건 closed |
| 2026-05-11 | Stage 8i | VR-cycle-05/06/08 + VR-S5-01 partial closure (95/95 tests) | GATE-F (echo)·GATE-G (토큰)·C-08/C-09 사후 체크 추가 + HEURISTIC_FUNCTION_DISCLAIMERS에 2 entry 추가. **10건 중 10건 처리 완료** (5 full + 1 흡수 + 4 partial). 운영 단계 진입 가능 |
| 2026-05-11 | Retro 2026-Q2 | 분기 회고 1차 실행 — `_workspace/release/retro-2026-Q2.md` | 6-Phase 어젠다 완료, 8 Action Items 식별 (다음 분기 Q3 작업), Stage 9~12 후보 식별, 메타 작업의 패턴 부재 발견 |
| 2026-05-11 | Stage 9 | Rosetta Flow End-to-End Dogfood (3 iter, 9.5분, patience early stop) — `_workspace/release/scenario-rosetta-flow-2026-05-11.md` | BE/FE/PyRosetta/Boltz 실 운영 + 6 critical 결함 자가 노출 + R1~R7 권고 + VR-cycle-10~14 등록. VR-cycle-09 (H-06) 가드의 운영 적용 사례 입증 |

### 미적용 Stage (`INTEGRATION_PLAN.md` 우선순위)

(전부 적용 완료. `INTEGRATION_PLAN.md`의 Stage 7은 "분리 신설"을 가정했으나 실제로는 이미 `.claude/agents/` 6개 파일이 존재하여 표준 3섹션 보강으로 대체됨.)

### 금지 (`SKILL.md:264-265` 원칙)

본 Pointer 블록에는 **에이전트·스킬 목록을 직접 기재하지 않는다.** 목록은 §"팀원 목록"이 담당. 본 블록은 포인터 + 변경 이력만 유지한다.
