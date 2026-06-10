# harness-adaptation

> **CLI-agnostic 메타-스킬 어댑테이션** — [revfactory/harness](https://github.com/revfactory/harness)의 핵심 IP를 추출하여 **Claude Code · Codex CLI · Cursor Agent** 어디에서나 동일 워크플로우로 작동하게 한 어댑테이션. 환각 가드 + 검증 게이트 + 분기 회고 메커니즘 내장.

| Field | Value |
|---|---|
| **Location** | `tools/harness-adaptation/` |
| **Version** | `v0.8.0` (8 Stages applied) |
| **License (本)** | 프로젝트 라이선스 / **License (upstream)** Apache-2.0 |
| **Upstream** | `revfactory/harness@v1.2.0` (Git submodule, 원본 보존) |
| **Tests** | `pytest pipeline_local/tests/` — **33/33 passing** |
| **CLI support** | Claude Code · Codex CLI · Cursor Agent (어댑터 3종) |
| **Adopted by** | PRST_N_FM (SST-14 / SSTR2 방사성의약품 스크리닝 파이프라인) |

---

## 한 줄 요약

> **"도메인 한 문장"** 을 입력받아 **"검증 가능한 에이전트 팀 + 스킬 + 환각 가드"** 산출물 묶음으로 변환하는 메타-스킬.

upstream `harness`는 Claude Code 플러그인이지만, 본 어댑테이션은 그 핵심 IP만 추출하여 멀티-CLI 환경에서도 동일한 결과를 보장한다.

---

## 디렉토리 위치

본 어댑테이션의 **루트 경로**는 다음과 같다:

```
프로젝트루트(예: /home/dongjukim/Documents/workspace/repos/SST14-M_scr/)
└── tools/
    └── harness-adaptation/              ← ★ 본 어댑테이션 루트
        ├── README.md                    ← 본 파일
        ├── ANALYSIS.md                  ← 팩트 기반 분석 (파일:라인 인용)
        ├── PROMPT_TEMPLATE.md           ← ★ CLI-agnostic 범용 프롬프트
        ├── PROMPT_PRST_N_FM_EXAMPLE.md  ← 우리 도메인 적용 예시
        ├── INTEGRATION_PLAN.md          ← Stage 0~7 단계별 로드맵
        ├── CHANGELOG.md                 ← SemVer 이력 (v0.1.0 ~ v0.8.0)
        ├── RETROSPECTIVE_GUIDE.md       ← 분기 회고 진행 가이드
        ├── checklist.md                 ← 작업 시작/진행/종료 체크리스트
        ├── adapters/
        │   ├── claude-code.md
        │   ├── codex-cli.md
        │   └── cursor-agent.md
        ├── templates/
        │   ├── agent-validation-template.md
        │   └── skill-validation-template.md
        └── reference/
            └── harness/                 ← Git submodule (원본, 자동 클론 시 `git submodule update --init` 필요)
```

**연동 위치** (어댑테이션 결과로 영향 받는 외부 경로):

```
프로젝트루트/
├── CLAUDE.md                                       ← Stage 2/3: Pointer 블록 + 패턴 매핑
├── .claude/agents/{6명}.md                          ← Stage 7: 표준 3섹션 보강
├── .github/PULL_REQUEST_TEMPLATE.md                ← Stage 4: PR 의무 검증
├── .gitmodules                                     ← Stage 0: harness submodule 등록
├── _workspace/                                     ← Stage 1: 다단계 산출물
│   ├── README.md                                   ← 파일명 컨벤션 정의
│   └── release/*.md                                ← 검증·회고 보고서 (git 추적)
└── pipeline_local/
    ├── scripts/pharmacology_guards.py              ← Stage 5: 환각 가드
    └── tests/test_pharmacology_guards.py           ← Stage 5: 33 회귀 테스트
```

---

## 무엇을 추출했나 — L1 / L2 / L3 분리

[`ANALYSIS.md`](ANALYSIS.md)의 핵심 결정:

| Layer | 정체 | 본 어댑테이션에서 |
|---|---|---|
| **L1** | Claude Code 종속 (`.claude-plugin/`, `EXPERIMENTAL_AGENT_TEAMS=1`, `/plugin install`) | ❌ 채택하지 않음 — 멀티-CLI 호환성을 위해 의도적 제외 |
| **L2** | CLI-agnostic 핵심 IP (6 패턴, Phase 0~7 워크플로우, `_workspace/` 컨벤션, Progressive Disclosure) | ✅ **이게 핵심 추출 자산** |
| **L3** | PRST_N_FM 기존 자산과 중복 (CLAUDE.md 트리, `scripts/agent-wrapper.sh`) | ⚠️ 충돌 회피 통합 (Stage 3 매핑) |

---

## 6개 아키텍처 패턴

`reference/harness/.claude-plugin/plugin.json:3` 원문 그대로:

| # | 패턴 | 언제 쓰나 | PRST_N_FM 적용 사례 |
|---|---|---|---|
| 1 | **Pipeline** | 순차 의존 작업, 각 단계가 이전 산출물에 강 의존 | 시퀀스 검증 → 변이 적용 → 도킹 → 채점 |
| 2 | **Fan-out/Fan-in** | 동일 입력에 대한 다관점 병렬 분석 | Silo A (3-Arm NIM) + Silo B (PyRosetta) 듀얼 파이프라인 |
| 3 | **Expert Pool** | 입력 유형별 다른 전문가 라우팅 | codex(코드) ↔ cursor-agent(분석) — CLAUDE.md 2순위 |
| 4 | **Producer-Reviewer** | 객관적 검증 기준이 존재하는 품질 보장 | engineer-backend ↔ reviewer-science 검증 루프 |
| 5 | **Supervisor** | 작업량 가변 / 런타임 동적 분배 | tmux team-mate 모드 — orchestrator 동적 분장 |
| 6 | **Hierarchical Delegation** | 자연스러운 계층 분해 (깊이 ≤2) | 평탄화 권장 — 현재 미사용 |

---

## CLI 어댑터 — Claude Code · Codex · Cursor

같은 추상 명령을 3개 CLI에서 동일 의미로 작동시킨다:

| 추상 | Claude Code | Codex CLI | Cursor Agent |
|---|---|---|---|
| 에이전트 정의 | `.claude/agents/{name}.md` | `~/.codex/agents/{name}.md` | `.cursor/rules/agents/{name}.mdc` |
| 팀 메시지 | `SendMessage` 도구 | 파일 폴백 (`_workspace/`) | 파일 폴백 |
| 동적 작업 큐 | `TaskCreate` 도구 | `_workspace/queue.md` 폴링 | `_workspace/queue.md` 폴링 |
| 트리거 매칭 | description 자동 매칭 | 외부 라우터 (CLAUDE.md 표) | `.mdc` description |
| 환경 플래그 | `EXPERIMENTAL_AGENT_TEAMS=1` | 불필요 | 불필요 |

전체 매핑은 `adapters/{claude-code,codex-cli,cursor-agent}.md` 참조.

---

## 실제 적용 사례 — PRST_N_FM Case Study

> **프로젝트**: SST-14 (`AGCKNFFWKTFTSC`, Cys3-Cys14 SS bond, FWKT pharmacophore) 기반 SSTR2 타겟 방사성의약품 후보 in-silico 스크리닝 AI 파이프라인.
> **듀얼 파이프라인**: Silo A (3-Arm NIM) + Silo B (PyRosetta mutation+dock).
> **기존 자산**: orchestrator + 5 teammate (CLAUDE.md), `scripts/agent-wrapper.sh` (codex/cursor-agent 래퍼).

본 어댑테이션은 **PRST_N_FM에 8개 Stage를 모두 적용**해 동작을 입증했다.

### 적용 타임라인 — 8 Stages, 단일 분기 적용

| # | Stage | 커밋 | 산출물 | 우선순위 |
|---|-------|------|--------|--------|
| 1 | **0 Bootstrap** | [`2637b1c`](../../commit/2637b1c) | 어댑테이션 디렉토리 + submodule (9 docs, +1703 lines) | — |
| 2 | **1 Workspace** | [`5805109`](../../commit/5805109) | `_workspace/{NN}_{agent}_{artifact}` 컨벤션 | High |
| 3 | **5 Guard** ★ | [`de5fabb`](../../commit/de5fabb) | `pharmacology_guards.py` + **33 회귀 테스트** | **Critical** |
| 4 | **2 Pointer** | [`a3b3bb8`](../../commit/a3b3bb8) | `CLAUDE.md` Harness Pointer + 트리거 키워드 | High |
| 5 | **3 Mapping** | [`3a3a54b`](../../commit/3a3a54b) | 위임 트리 1~4순위에 6패턴 명칭 매핑 | Medium |
| 6 | **4 PR Check** | [`81f2141`](../../commit/81f2141) | PR 템플릿 + 검증 보고서 템플릿 2종 | Medium |
| 7 | **6 Evolution** | [`f4f2670`](../../commit/f4f2670) | `CHANGELOG.md` + `RETROSPECTIVE_GUIDE.md` | Medium |
| 8 | **7 Standardization** | [`4cc9af7`](../../commit/4cc9af7) | `.claude/agents/` 6명에 표준 3섹션 보강 | Low (재정의) |

**전체 변경 규모**: 8 commits, ~3000 라인 추가, 기존 운영 코드 무수정.

### 도메인 환각 가드 — 실 사례

`PROMPT_PRST_N_FM_EXAMPLE.md §3`의 H-01~05를 `pipeline_local/scripts/pharmacology_guards.py`로 코드화:

| ID | 위험 | 정답 (회귀 차단됨) | 검증 테스트 |
|----|------|---------|----------|
| **H-01** 파라미터 오기재 | Radzicka-Wolfenden `P=0.0` 사용 | `P=-2.54` (Boman convention) | `test_rw_transfer_boman_convention` |
| **H-01** 파라미터 오기재 | Radzicka-Wolfenden `S=1.15` 사용 | `S=3.40` (Boman convention) | `test_rw_transfer_boman_convention` |
| **H-02** 부호 역전 | Boman Index 부호 오류 → NSGA-II 순위 역전 | `RW[R] > RW[I]` invariant | `test_boman_convention_sign` |
| **H-05** 종 혼동 | N-end Pro half-life `20h` (yeast) | `30h` (mammalian, Varshavsky 1996) | `test_nend_half_life_pro_is_30_not_20` |

CI가 위 4건을 영구 차단한다.

### 자체 결함 자체 발견 — Stage 5의 메타-효과

가드 모듈 작성 중 **본 어댑테이션 자체의 가설 오류**를 1건 발견·수정:
- 초기 가설: `boman_index_kcal_per_mol` 범위 `[-5, +5]`
- 실측: all-K 14mer = `5.55` → 범위 위반
- 정정: 이론 max(all-R = `14.92`)에 맞춰 `[-5, +15]`로 보정
- **의의**: GATE-C 가드가 자체 가설의 부정확성을 검출 — 가드 메커니즘 자체가 작동함을 입증.

### CLAUDE.md 위임 트리 ↔ 패턴 매핑 (Stage 3 적용 후)

| 순위 | 우리 자산 | 매핑된 패턴 |
|------|---------|-----------|
| 1 | tmux team-mate (`/team`) | Fan-out/Fan-in 또는 Supervisor |
| 2 | codex / cursor-agent (외부) | Expert Pool |
| 3 | Agent tool (내장 서브) | Pipeline / Producer-Reviewer / Fan-out/Fan-in |
| 4 | 직접 구현 | (없음) + Hierarchical Delegation 평탄화 결과 |

이제 모든 위임 결정에 "어느 패턴인가 + 근거 §"를 표기 가능 → 사후 감사 가능.

---

## 빠른 시작

다른 프로젝트에 어댑테이션을 가져갈 때:

### 1. 분석 자료 확보

```bash
# upstream 원본 보존 (Apache-2.0 LICENSE 동반)
git submodule add https://github.com/revfactory/harness.git tools/harness-adaptation/reference/harness
```

### 2. 본 어댑테이션 산출물 복사

본 디렉토리(`tools/harness-adaptation/`) 통째로 복사하고, **3개 파일만 도메인에 맞게 교체**:
- `PROMPT_PRST_N_FM_EXAMPLE.md` → `PROMPT_<YOUR_DOMAIN>_EXAMPLE.md`
- `INTEGRATION_PLAN.md`의 Stage 5 (도메인 환각 가드) → 본인 도메인 위험으로 재작성
- `CHANGELOG.md` 초기화 (v0.1.0부터 시작)

### 3. Stage 단계적 도입

`INTEGRATION_PLAN.md`의 우선순위 표대로:

```
Stage 0 (bootstrap)
  → Stage 1 (_workspace/)
  → Stage 5 (★ 도메인 환각 가드, Critical)
  → Stage 2 (CLAUDE.md/AGENTS.md pointer)
  → Stage 3 (트리 ↔ 패턴 매핑)
  → Stage 4 (PR template)
  → Stage 6 (CHANGELOG + 회고)
  → Stage 7 (에이전트 정의 표준화)
```

### 4. PROMPT_TEMPLATE.md를 LLM 세션에 적용

`{{DOMAIN}}`, `{{PROJECT_ROOT}}`, `{{CLI}}`, `{{TEAM_SIZE}}`, `{{WORKSPACE_DIR}}`, `{{DOMAIN_GUARDS}}` 6개 플레이스홀더만 채우면 즉시 사용 가능.

---

## 산출물 안내

| 파일 | 역할 | 분량 |
|------|------|---|
| `README.md` | 본 파일 (쇼케이스 + 빠른 시작) | ~250 |
| [`ANALYSIS.md`](ANALYSIS.md) | 팩트 기반 분석 (모든 주장 파일:라인 인용) | ~400 |
| [`PROMPT_TEMPLATE.md`](PROMPT_TEMPLATE.md) | ★ CLI-agnostic 범용 프롬프트 | ~340 |
| [`PROMPT_PRST_N_FM_EXAMPLE.md`](PROMPT_PRST_N_FM_EXAMPLE.md) | SST-14 / SSTR2 도메인 적용 예시 | ~280 |
| [`INTEGRATION_PLAN.md`](INTEGRATION_PLAN.md) | Stage 0~7 로드맵 + 리스크·완화 | ~210 |
| [`CHANGELOG.md`](CHANGELOG.md) | SemVer 이력 (Keep a Changelog 1.1.0) | ~170 |
| [`RETROSPECTIVE_GUIDE.md`](RETROSPECTIVE_GUIDE.md) | 분기 회고 진행 가이드 | ~180 |
| [`checklist.md`](checklist.md) | 매 작업 시작/진행/종료 체크리스트 | ~160 |
| `adapters/claude-code.md` | Claude Code 어댑터 | ~140 |
| `adapters/codex-cli.md` | Codex CLI 어댑터 | ~170 |
| `adapters/cursor-agent.md` | Cursor Agent 어댑터 | ~150 |
| [`cursor-cli/README.md`](cursor-cli/README.md) | Cursor Agent **실행형** 하네스(stage 프롬프트 + `scripts/cursor/harness_invoke.sh`) | ~90 |
| `templates/agent-validation-template.md` | 신규 에이전트 검증 보고서 템플릿 | ~95 |
| `templates/skill-validation-template.md` | 신규 스킬 검증 보고서 템플릿 | ~80 |
| `reference/harness/` | revfactory/harness 원본 (submodule) | — |

---

## 핵심 컨셉 — 한 페이지 요약

### Phase 0~7 워크플로우 (`PROMPT_TEMPLATE.md §2`)

```
Phase 0 현황 감사 → 신규/확장/유지보수 분기
Phase 1 도메인 분석 (코드베이스 탐색)
Phase 2 팀 아키텍처 설계 (6패턴 중 선택, 이유 명시 의무)
Phase 3 에이전트 정의 생성 (인라인 금지)
Phase 4 스킬 생성 (Progressive Disclosure 3단계)
Phase 5 통합·오케스트레이션 (_workspace/ 파일 기반)
Phase 6 검증·테스트 (should-trigger/NOT-trigger 8+8, A/B)
Phase 7 진화 (피드백 → 매핑 표 → CHANGELOG)
```

### Anti-Hallucination Guards (`PROMPT_TEMPLATE.md §1, §3, §4`)

```
사전 (G-PRE-01~07)         : 출처 의무 / 어휘 정의 / 단계 명시 / 신뢰 등급 / 이전 단계 참조 / READ-ONLY 경계 / 단일 책임
단계별 게이트 (GATE-A~E)    : 입력 동일성 / 범위 이탈 / 수치 경계 / 상호 참조 / 출처 카운트
사후 체크리스트 (C-POST-1~7): 독립 재계산 / 논문 인용 / 부호 / NULL 구분 / 귀속 / 범위 / 교차 일관성
```

### 디렉토리 컨벤션 (`PROMPT_TEMPLATE.md §5`)

```
_workspace/{NN}_{agent}_{artifact}.{ext}   ← 중간 산출물
_workspace/release/<topic>-YYYY-MM-DD.md   ← 검증/회고 보고서 (git 추적)
```

---

## 결과 / 측정 지표

| 메트릭 | 측정값 |
|--------|------|
| 적용된 Stage | **8 / 8** (Stage 0, 1, 2, 3, 4, 5, 6, 7 전부) |
| 회귀 테스트 | **33 / 33** passing (`pytest pipeline_local/tests/test_pharmacology_guards.py`) |
| 차단된 historical defect | **4건** (Radzicka-Wolfenden P/S, Pro half-life, Boman 부호) |
| 자체 결함 자체 검출 | 1건 (Stage 5 작성 중 가드 가설 오류 발견·수정) |
| Critical 위험 영구 차단 | 약리학 lookup table 무단 변경 → CI/로컬에서 즉시 fail |
| CLI 어댑터 | 3종 (Claude Code · Codex CLI · Cursor Agent) |
| 도메인 환각 시나리오 식별 | H-01~05 (PRST_N_FM 도메인 특화) |

---

## 라이선스·출처

- **upstream**: revfactory/harness v1.2.0 — **Apache-2.0** (`reference/harness/LICENSE`)
- **본 어댑테이션**: 프로젝트 라이선스 준수
- 모든 분석 주장은 `ANALYSIS.md`에서 파일:라인 수준 추적 가능
- `ANALYSIS.md §12 §검증 필요` (VR-01~09)에 본문만으로 확정 못한 항목 9건 명시

---

## 변경 이력

전체 이력은 [`CHANGELOG.md`](CHANGELOG.md). 분기당 1회 회고 후 minor cut.

### 최근

- **v0.8.0** (2026-05-11) — Stage 7: `.claude/agents/` 표준 3섹션 보강
- **v0.7.0** (2026-05-11) — Stage 6: CHANGELOG + 회고 가이드 (Phase 7 운영화)
- **v0.6.0** (2026-05-11) — Stage 4: PR 의무 검증 템플릿
- **v0.5.0** (2026-05-11) — Stage 3: 위임 트리 ↔ 6패턴 매핑
- **v0.4.0** (2026-05-11) — Stage 2: CLAUDE.md Pointer 블록
- **v0.3.0** (2026-05-11) — Stage 5 (Critical): 약리학 환각 가드 + 33 회귀 테스트
- **v0.2.0** (2026-05-11) — Stage 1: `_workspace/` 컨벤션
- **v0.1.0** (2026-05-11) — Stage 0: 어댑테이션 디렉토리 + submodule

---

## 다음 단계

분기 회고(`RETROSPECTIVE_GUIDE.md`)에서 새 Stage 후보 발굴. 즉시 액션:

- [ ] 매 PR에 본 어댑테이션 변경 항목 점검 — `.github/PULL_REQUEST_TEMPLATE.md`가 자동화
- [ ] 매 분기 마지막 주에 `_workspace/release/retro-YYYY-Q.md` 작성
- [ ] 새 약리학 척도 도입 시 `LITERATURE_VALUES`에 등록 (Stage 5 절차)
- [ ] 새 에이전트/스킬 도입 시 should-trigger 10개 + A/B 비교 (Stage 4 절차)

---

**문의·기여**: 본 어댑테이션은 PRST_N_FM 프로젝트 내부 자원. 외부 공유 시 revfactory/harness 출처와 Apache-2.0 라이선스 함께 명시.
