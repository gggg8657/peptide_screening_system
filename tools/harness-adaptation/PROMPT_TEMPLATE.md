# Harness Universal Prompt — CLI-Agnostic Template

> **목적**: harness(revfactory/harness)의 핵심 IP(L2 레이어)를 CLI 비종속 형태로 추출하여, **Claude Code / Codex CLI / Cursor Agent** 어디에서도 동일 워크플로우를 재현 가능하게 한 **메타-프롬프트 템플릿**.
>
> **사용 방법**: `{{...}}` 플레이스홀더를 채워 사용. 그대로 LLM 세션 시작에 붙여 넣음. CLI별 어댑터는 `adapters/{cli}.md` 참조. Cursor Agent를 **단계별 CLI 프로세스**로 돌릴 때는 `cursor-cli/` + `scripts/cursor/harness_invoke.sh`.
>
> **근거**: `ANALYSIS.md` (모든 규칙에 `파일경로:라인번호` 추적 가능)

---

## 0. 변수 사전 정의 (Variable Glossary)

| 변수 | 의미 | 예 |
|------|------|---|
| `{{DOMAIN}}` | 프로젝트가 다루는 도메인 한 문장 | "방사성의약품 펩타이드 후보 스크리닝" |
| `{{PROJECT_ROOT}}` | 절대경로 또는 작업 디렉토리 | `/home/user/repo` |
| `{{CLI}}` | 실행 환경 — `claude-code` / `codex` / `cursor-agent` 중 하나 | `claude-code` |
| `{{TEAM_SIZE}}` | 권장 팀원 수 (소 2~3, 중 3~5, 대 5~7) | `5` |
| `{{EXISTING_AGENTS}}` | 이미 정의된 에이전트 파일 경로 목록 | `CLAUDE.md, .claude/agents/` |
| `{{WORKSPACE_DIR}}` | 중간 산출물 디렉토리 | `_workspace/` 또는 `logs/external_agents/` |
| `{{DOMAIN_GUARDS}}` | 도메인 특수 환각 가드 (선택) | "약리학 수치는 문헌 라인 인용 필수" |

---

## 1. 진입 규칙 (★ 항상 적용 — Anti-Hallucination Pre-Guards)

다음 규칙은 **모든 Phase에서 항상 유효**하다.

**G-PRE-01: 출처 없는 수치 금지** — 물리화학·약리학·통계 수치는 `(출처: 저자YYYY, 표번호)` 또는 `(파일경로:라인)` 형태 주석 의무. 출처 없으면 결과에 포함 금지, "검증 필요" 섹션으로 분리.

**G-PRE-02: 도메인 어휘 사전 정의** — 사용할 척도/지표/단위를 첫 응답 블록에 표로 선언. 부호 규약·논문 연도·범위 명시. 이후 단계는 이 사전을 참조해야 함.

**G-PRE-03: 단계 건너뛰기 금지** — Phase 진입 시 실행 계획을 출력. 건너뛰는 Phase는 `SKIP: [이유]`로 명시.

**G-PRE-04: 불확실성 등급** — 산출물 각 항목에 `HIGH(문헌 직접 인용)` / `MED(계산 기반)` / `LOW(추론/추정)` 중 하나 부여. `LOW`는 "검증 필요" 플래그 의무.

**G-PRE-05: 이전 단계 참조 의무** — 각 Phase 시작 시 "이전 Phase에서 사용한 값: [파일:라인]" 명시.

**G-PRE-06: READ-ONLY / WRITE-ALLOWED 선언** — 작업 시작 시 수정 금지 파일·수정 허용 파일 목록 명시. 변경 필요 시 사용자 확인 요구.

**G-PRE-07: 단일 책임 범위** — 각 추론 세션이 책임지는 파라미터/계산/결정 목록을 선언.

---

## 2. 메인 워크플로우 (Phase 0~7 — CLI 비종속)

> harness `SKILL.md:18-415`의 8단계 워크플로우를 CLI 비종속으로 재구성. 원본 라인 인용은 `ANALYSIS.md §4.2` 표 참조.

### Phase 0 — 현황 감사

**입력**: `{{PROJECT_ROOT}}`

**행동**:
1. `{{EXISTING_AGENTS}}` 경로 전수 읽기
2. 다음 3분기로 라우팅:
   - **신규**: 에이전트·스킬 정의가 없거나 빈 경우 → Phase 1~6 전수 실행
   - **확장**: 일부 존재, 새 에이전트/스킬 추가 → Phase 2/3 또는 4 선택 실행
   - **유지보수**: 기존 구조 감사·수정·동기화 → Phase 7-5만 실행
3. 분기 결정과 이유를 사용자에게 보고하고 **확인 받음**

**산출물 (검증 가능)**: 파일 시스템 읽기 목록 + 분기 결정문

**GATE-00**: 분기 결정의 정당성을 사용자가 확인할 때까지 다음 Phase 진입 금지.

---

### Phase 1 — 도메인 분석

**입력**: `{{DOMAIN}}` 한 문장 + 코드베이스

**행동**:
1. 도메인 핵심 작업 유형 식별 (최대 5개, 각각 한 줄)
2. 기술 스택·데이터 모델·주요 모듈 인벤토리 (파일경로 인용)
3. 기존 에이전트/스킬과의 충돌·중복 분석 표
4. `{{DOMAIN_GUARDS}}`가 있으면 도메인 특수 환각 위험 5개 식별

**산출물 (검증 가능 형식 강제)**:
```markdown
## Domain Analysis
- Core Tasks: 1. ... 2. ... (각 한 줄)
- Tech Stack: { ... } (파일경로 인용)
- Conflicts: | 기존 | 신규 | 중복도 | 권고 |
- Hallucination Risks: H-01: ... H-05: ...
```

**GATE-01**: 위 마크다운 섹션이 누락 없이 완성되어야 Phase 2 진입.

---

### Phase 2 — 팀 아키텍처 설계

**입력**: Phase 1 산출물

**행동**:
1. **실행 모드 선택** (CLI별 어댑터 참조):
   - 에이전트 팀 모드 (병렬 통신 필요)
   - 서브에이전트 모드 (병렬 통신 불필요)
   - 하이브리드
2. **6개 패턴 중 선택** + **선택 이유 명시 의무**:

| 패턴 | 적용 신호 | 팀 권장 | CLI 매핑 |
|------|---------|--------|---------|
| **Pipeline** | 순차 의존, 단계가 이전 산출물에 강하게 의존 | 제한적 (병렬 구간 있으면 유용) | Claude: 메시지 체인 / Codex: `codex exec` 시퀀스 / Cursor: `.cursor/rules` 순차 |
| **Fan-out/Fan-in** | 동일 입력 → 다른 관점 분석 | **필수: 에이전트 팀** | Claude: TeamCreate / Codex+Cursor: `agent-wrapper.sh` 다중 호출 + 집계 |
| **Expert Pool** | 입력 유형별 다른 처리 | 서브에이전트 적합 (라우터) | 라우터가 1개 전문가 선택 호출 |
| **Producer-Reviewer** | 품질 보장 + 객관 검증 기준 존재 | 팀 (재시도 2~3회 필수) | 검증 실패 시 재생성 루프 |
| **Supervisor** | 작업량 가변 / 런타임 동적 분배 | 팀 (공유 작업 목록) | TaskCreate 또는 공유 큐 |
| **Hierarchical Delegation** | 자연스러운 계층 분해 (깊이 ≤2) | 1단계 팀, 2단계 서브에이전트 (중첩 불가) | 평탄화 권장 |

3. **에이전트 분리 4축 판단**: 전문성 / 병렬성 / 컨텍스트 / 재사용성
4. **팀 크기 결정**: `{{TEAM_SIZE}}` 가이드 (소 2~3 / 중 3~5 / 대 5~7)

**산출물**:
```markdown
## Architecture Decision
- Execution Mode: <team|subagent|hybrid> — Reason: ...
- Pattern: <Pipeline|Fan-out/Fan-in|...> — Reason: ...
- Separation Axes: ...
- Team Size: {{TEAM_SIZE}}
```

**GATE-02**: 패턴 선택 이유가 명시되지 않으면 Phase 3 진입 금지.

---

### Phase 3 — 에이전트 정의 생성

**행동**:
1. 각 에이전트마다 **정의 파일** 작성 (인라인 프롬프트 금지)
   - Claude Code: `.claude/agents/{name}.md`
   - Codex CLI: `~/.codex/agents/{name}.md` (또는 `instructions/{name}.md`)
   - Cursor Agent: `.cursor/rules/agents/{name}.mdc`
2. 필수 섹션:
   - **핵심 역할** (1 문장)
   - **작업 원칙** (3~7 항목)
   - **입력 프로토콜** (어떤 형식의 입력 받는지)
   - **출력 프로토콜** (어떤 형식 산출하는지 — 검증 가능 형식 강제)
   - **에러 핸들링**
   - **협업 인터페이스** (다른 에이전트와의 통신 약속)
3. **모델 지정**: 도메인이 고품질 추론을 요구하면 최상위 모델 (Claude Opus 4.7 등)

**GATE-03**: 모든 에이전트 정의 파일이 존재하고 6개 섹션을 갖춰야 Phase 4 진입.

---

### Phase 4 — 스킬 생성

**행동**:
1. 각 스킬마다 **3단계 Progressive Disclosure** 적용:
   - **메타데이터** (~100단어): name, description, trigger
   - **본문** (≤500줄): 트리거 시 로드
   - **references/** (선택): 본문이 500줄 초과 시 분리
2. `description`은 **pushy하게** — 무엇을 하는지 + 구체적 트리거 상황 + 경계 조건 모두 기술
3. CLI 어댑터별 위치:
   - Claude Code: `.claude/skills/{name}/SKILL.md`
   - Codex CLI: `~/.codex/skills/{name}/` 또는 `instructions/{name}.md`
   - Cursor Agent: `.cursor/rules/skills/{name}.mdc`

**GATE-04**: 본문 길이 검증. 500줄 초과 시 references/ 분리 의무.

---

### Phase 5 — 통합 및 오케스트레이션

**행동**:
1. **오케스트레이터 = 스킬의 특수 형태**로 정의
2. **데이터 전달 4전략** 중 선택:
   - 메시지 기반 (실시간, 양방향)
   - 태스크 기반 (공유 작업 목록)
   - **파일 기반 (★ 권장)**: `{{WORKSPACE_DIR}}/{phase}_{agent}_{artifact}.{ext}` 컨벤션
   - 반환값 기반 (단순 함수형)
3. **파일명 컨벤션 강제**: `01_auditor_repo_audit.md` 같이 `{2자리 단계번호}_{에이전트 역할}_{산출물 종류}.{확장자}`
4. **에이전트 간 명시적 의존 표기**: 후속 산출물에서 선행 권고 번호 인용 (`Audit R4`)

**GATE-05**: 한 단계의 출력이 다음 단계 입력의 형식과 호환되는지 사전 검증.

---

### Phase 6 — 검증 및 테스트

**행동**:
1. **트리거 쿼리 세트**:
   - should-trigger 8~10개
   - should-NOT-trigger 8~10개 (near-miss 포함)
2. **A/B 비교 실행** (with-skill vs without-skill):
   - 같은 입력을 두 모드로 병렬 처리
   - 정량(assertion) + 정성(사용자 리뷰) 평가
3. **드라이런**: 실제 실행 없이 워크플로우 트레이스만 출력

**검증 가능 형식**:
```markdown
## Verification Report
- Trigger Coverage: 9/10 should-trigger pass, 1/10 with caveat
- A/B Quality Delta: <측정 기준> +N% (with-skill)
- Dry-run Trace: Phase 0 → ... → Phase 5 [OK]
```

**GATE-06**: 트리거 커버리지 < 80% 또는 A/B 델타 < 0이면 Phase 7로 진화 루프 진입.

---

### Phase 7 — 진화

**행동**:
1. 매 실행 후 피드백 수집 (강요 X, 기회 O)
2. **피드백 유형별 매핑**:
   - 트리거 누락 → 스킬 description 보강
   - 출력 형식 불일치 → 에이전트 출력 프로토콜 수정
   - 단계 누락 → SKILL.md Phase 수정
   - 충돌 → CLAUDE.md 위임 트리 수정
3. **변경 이력 테이블**: `날짜 | 변경 내용 | 대상 파일 | 사유` 4컬럼 유지

**Phase 7-5 운영/유지보수** (독립 진입 가능):
1. 현황 감사
2. 점진적 추가/수정
3. CLAUDE.md 포인터 갱신 (목록은 기입 X, 변경 이력만)
4. 변경 검증

---

## 3. 단계별 게이트 (Anti-Hallucination Gates)

각 Phase 종료 시 적용:

**GATE-A 입력값 동일성** — 직전 단계 핵심 수치 vs 현재 입력 대조. 불일치 시 경고.

**GATE-B 범위 이탈 감지** — Phase별 "허용 도구/데이터 소스 목록"을 선언. 목록 외 접근 시 `범위 이탈: [소스]` 플래그.

**GATE-C 수치 경계 검사** — 도메인 척도의 "생물학적/공학적 합리 범위"를 사전 정의. 벗어나면 `RANGE-CHECK FAIL: [값] — 예상 범위: [min, max]`.

**GATE-D 상호 참조 일관성** — 동일 변수가 여러 단계에서 다른 값으로 나타나면 둘 다 보존 + 출처 병기.

**GATE-E 최소 출처 카운트** — 단계 산출물 수치 N개 중 출처가 달린 n개. `n/N < 0.8`이면 `출처 미달: {N-n}개` 경고.

**GATE-F Fan-out 독립성 검증** (VR-cycle-05 closure) — Fan-out/Fan-in 패턴으로 4명 이상 호출 시 각 에이전트 산출물의 독립성을 셀프-체크. 다음 신호 발견 시 echo 가능성으로 §검증 필요에 등록:
- 동일 phrasing이 2+ 산출물에 등장 (인용은 제외)
- 동일 출처를 동일 라인으로 인용하는 비율 ≥ 30% (정상 5~15%)
- 동일 누락 패턴 (예: 모두 C-04를 짚지 않음 — group think 의심)

다양화 가이드: 각 Fan-out 호출 prompt에 (a) 다른 출발점 시드(특정 함수/특정 라인) (b) 다른 검증 기준(코드 품질 vs 화학 정확성 vs PK 영향) (c) "다른 reviewer와 독립 판단" 명시 의무.

**GATE-G 토큰 비용 최적화** (VR-cycle-06 closure) — 같은 컨텍스트(파일 경로·이전 산출물·도메인 어휘 사전 등)를 2+ Fan-out 호출에 반복 임베드하면 토큰 비용이 N배 증가. 다음 컨벤션 의무:
- **공유 컨텍스트는 파일로 분리**: `_workspace/shared_context_{topic}_{YYYY-MM-DD}.md`
- 각 Agent 호출 prompt에는 파일 경로만 전달 (예: "컨텍스트는 `_workspace/shared_context_*.md` 참조")
- LLM이 파일을 직접 읽는 toolset (Read tool 등) 보유 시에만 적용
- 컨텍스트 부분이 < 200 단어면 인라인이 더 효율 — 조건부 적용

---

## 4. 사후 검증 체크리스트 (Post-Delivery)

산출물 인도 **직전** 적용:

- [ ] **C-01 독립 재계산 대조** — 핵심 수치를 별도 스크립트(예: `codex exec`)로 재계산하여 일치 확인
- [ ] **C-02 논문 테이블 직접 인용** — 각 척도에 "원본 논문 표에서 직접 확인" 이진 플래그
- [ ] **C-03 부호 규약 최종 확인** — 각 척도의 "고값이 의미하는 방향" 명시
- [ ] **C-04 NULL vs 계산 불가 구분** — NULL/NA, 0, "계산 불가(이유)" 세 가지 명시 분리
- [ ] **C-05 에이전트 귀속** — 각 수치 옆에 `(생성 단계: Phase-X, 파일:라인)`
- [ ] **C-06 범위 외 값 최종 스캔** — GATE-C 일괄 재적용
- [ ] **C-07 교차 파이프라인 일관성** — 병렬 파이프라인이 동일 파라미터를 동일 값으로 사용하는지 비교 테이블
- [ ] **C-08 Fan-out echo 셀프-체크** (VR-cycle-05) — N개 Fan-out 산출물 비교. 동일 phrasing·동일 누락 패턴 발견 시 §검증 필요로 분리. 30%+ 인용 중복은 group think 신호.
- [ ] **C-09 휴리스틱 함수 인용 형식** (VR-cycle-09 / H-06) — 본 산출물이 `predict_half_life()` 등 휴리스틱 함수의 출력을 인용한 경우, *임상 단위로 보고하지 않음*. "ranking score (heuristic)" 표기 + HEURISTIC 신뢰 등급 표시. `is_heuristic_function(qualname)` 가드로 자동 확인.

---

## 5. 출력 산출물 구조 (디렉토리 컨벤션)

```
{{PROJECT_ROOT}}/
├── (CLI별 에이전트 정의 경로 — adapters/{cli}.md 참조)
├── (CLI별 스킬 경로)
├── {{WORKSPACE_DIR}}/
│   ├── 01_<agent>_<artifact>.md
│   ├── 02_<agent>_<artifact>.md
│   └── release/                    # 검증 산출물
│       └── audit-YYYY-MM-DD.md
└── CLAUDE.md (또는 그 CLI 등가물)
    └── 포인터 블록 (목록 X, 변경 이력 O)
```

**CLAUDE.md (또는 등가물) 포인터 블록 템플릿**:
```markdown
## Harness Pointer
- 트리거 규칙: <키워드 → 스킬 매핑>
- 변경 이력:
  | 날짜 | 변경 | 대상 | 사유 |
  |------|------|------|------|
  | YYYY-MM-DD | ... | <file> | ... |
```

**금지**: CLAUDE.md(또는 등가물)에 에이전트·스킬 **목록**을 직접 기입하지 않음 (`SKILL.md:264-265` 원칙).

---

## 6. CLI 어댑터 참조

본 템플릿의 추상 명령을 실제 도구로 변환하는 어댑터:

- **Claude Code**: `adapters/claude-code.md`
- **Codex CLI**: `adapters/codex-cli.md`
- **Cursor Agent**: `adapters/cursor-agent.md`

각 어댑터는 다음 매핑을 제공:
- "에이전트 호출" → 어떤 CLI 명령
- "팀 메시지" → 어떤 CLI 메커니즘 (또는 폴백)
- "병렬 실행" → 어떤 CLI 패턴
- "스킬 등록" → 어떤 파일 위치·포맷

---

## 7. 도메인 환각 가드 (선택 — `{{DOMAIN_GUARDS}}`)

도메인별 추가 환각 가드. 우리 프로젝트(SST-14 펩타이드/PyRosetta) 예시는 `PROMPT_PRST_N_FM_EXAMPLE.md`의 §3 참조. 일반 도메인의 가이드는 아래.

```markdown
## Domain Hallucination Risks (Domain-Specific)
- H-01: <도메인 특수 수치 환각 위험>
- H-02: <부호/방향 역전 위험>
- H-03: <척도 혼용 위험>
- H-04: <기억 재생 위험>
- H-05: <참조 종/조건 혼동>
```

각 H-* 항목은 산출물의 해당 단계에서 GATE-C와 결합되어 적용된다.

---

## 8. 실행 체크리스트 (한 페이지 요약)

LLM이 본 템플릿을 사용할 때 응답에 다음을 **순서대로** 포함:

1. **변수 사전 정의** 출력 (`{{...}}` 채워진 값 + 도메인 어휘표)
2. **Phase 0 분기 결정** + 사용자 확인
3. **Phase 1~6 (또는 Phase 7-5) 순차 실행** — 각 단계 산출물을 검증 가능 형식으로
4. **모든 게이트 통과 보고** — GATE-A~E + C-01~07
5. **변경 이력 테이블** 갱신 (Phase 7)
6. **§검증 필요 절** — 본 작업으로 확정 못한 항목 명시

---

## 9. 라이선스·출처

- 원본: revfactory/harness @ v1.2.0 (Apache-2.0, `tools/harness-adaptation/reference/harness/LICENSE`)
- 본 템플릿은 원본의 L2(CLI-agnostic 핵심 IP) 추출 + 환각 가드 추가
- 모든 라인 인용은 `ANALYSIS.md`에서 추적 가능
- §검증 필요 (VR-01~09)는 `ANALYSIS.md §12` 참조

---

**End of Template.** CLI별 적용은 `adapters/`로, 우리 프로젝트 실제 적용은 `PROMPT_PRST_N_FM_EXAMPLE.md`로.
