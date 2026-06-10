# 적용 체크리스트 — Anti-Hallucination + 운영 가드

> `PROMPT_TEMPLATE.md`를 LLM 세션에서 사용할 때 **체크리스트로 활용**할 한 페이지.
> 매 작업 사이클의 시작 / 진행 중 / 종료 각 시점에 확인.

---

## 🟢 작업 시작 전 (Pre-Session Checklist)

### 변수 충족
- [ ] `{{DOMAIN}}` 한 문장으로 정의됨
- [ ] `{{PROJECT_ROOT}}` 절대경로 확정
- [ ] `{{CLI}}` 결정 (claude-code / codex / cursor-agent / hybrid)
- [ ] `{{TEAM_SIZE}}` 결정 (소 2-3 / 중 3-5 / 대 5-7)
- [ ] `{{WORKSPACE_DIR}}` 디렉토리 존재 확인 또는 생성

### 도메인 어휘
- [ ] 사용할 척도/지표/단위 사전 작성 (`PROMPT_PRST_N_FM_EXAMPLE.md §1` 참조)
- [ ] 부호 규약 명시 (특히 Boman Index 같은 혼동 주의 척도)
- [ ] 논문 출처(저자, 연도, 저널, 쪽수) 사전 정의

### 환경
- [ ] (Claude Code 팀 모드 시) `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 환경변수
- [ ] (Codex 사용 시) `./scripts/agent-wrapper.sh codex --help` 정상
- [ ] (Cursor 사용 시) `./scripts/agent-wrapper.sh cursor-agent --help` 정상
- [ ] (Cursor Pipeline 사용 시) `./scripts/cursor/harness_invoke.sh list` 로 stage 확인 후 `--dry-run` 으로 프롬프트 검토 → 필요 시 `--execute`
- [ ] `logs/external_agents/` 쓰기 가능
- [ ] READ-ONLY / WRITE-ALLOWED 파일 목록 선언

---

## 🟡 작업 진행 중 (Per-Phase Gates)

### 각 Phase 시작 시
- [ ] "이전 Phase 사용 값: [파일:라인]" 명시 (G-PRE-05)
- [ ] 이 Phase의 책임 범위 선언 (G-PRE-07)
- [ ] 허용 도구/데이터 소스 목록 선언 (GATE-B 사전)

### 각 Phase 종료 시
- [ ] **GATE-A** 입력값 동일성: 직전 단계 핵심 수치 vs 현재 입력 일치
- [ ] **GATE-B** 범위 이탈 감지: 선언된 소스 외 접근 발생 없음
- [ ] **GATE-C** 수치 경계 검사: 모든 수치가 도메인 합리 범위 내
- [ ] **GATE-D** 상호 참조 일관성: 동일 변수의 단계 간 일관성
- [ ] **GATE-E** 최소 출처 카운트: 수치의 80% 이상에 출처 부착

### Phase별 추가 게이트

#### Phase 0 (현황 감사) 종료 시
- [ ] 분기 결정문 명시 (신규 / 확장 / 유지보수)
- [ ] 사용자가 분기 결정에 **동의** (GATE-00)

#### Phase 2 (아키텍처 설계) 종료 시
- [ ] 6개 패턴 중 선택한 패턴 명칭 명시
- [ ] **선택 이유** 1~3 문장 명시 (GATE-02)
- [ ] 팀 크기 가이드 준수 확인

#### Phase 3 (에이전트 정의) 종료 시
- [ ] 모든 에이전트가 정의 파일로 존재 (인라인 X)
- [ ] 6개 필수 섹션 모두 채워짐 (핵심 역할 / 작업 원칙 / 입력 / 출력 / 에러 / 협업)

#### Phase 4 (스킬 생성) 종료 시
- [ ] 본문 ≤500줄 (초과 시 references/ 분리)
- [ ] description "pushy하게" 작성 (트리거 상황 구체적)

#### Phase 5 (통합) 종료 시
- [ ] `{{WORKSPACE_DIR}}/{NN}_{agent}_{artifact}` 컨벤션 준수
- [ ] 후속 산출물이 선행 산출물 라인/번호 인용

#### Phase 6 (검증) 종료 시
- [ ] should-trigger 8~10개 작성
- [ ] should-NOT-trigger 8~10개 (near-miss 포함) 작성
- [ ] A/B 비교 1회 이상 실행
- [ ] 트리거 커버리지 ≥ 80%

---

## 🔴 작업 종료 직전 (Post-Delivery Checklist)

산출물 인도 전 **모두** 확인:

### 검증 가능성
- [ ] **C-01** 핵심 수치를 독립 스크립트로 재계산하여 일치 확인
- [ ] **C-02** 각 척도에 "논문 표 직접 확인" 이진 플래그
- [ ] **C-03** 부호 규약 일관성 (사전 vs 계산 함수)
- [ ] **C-04** NULL / 0 / "계산 불가" 세 가지 명시 분리
- [ ] **C-05** 각 수치 옆에 `(생성 단계: Phase-X, 파일:라인)` 표기
- [ ] **C-06** 범위 외 값 최종 스캔 (GATE-C 일괄 재적용)
- [ ] **C-07** 교차 파이프라인 일관성 (Silo A ↔ Silo B 등)

### 메타데이터
- [ ] 산출물에 작성일 / 작성자 / 데이터 소스 메타 헤더
- [ ] 변경 이력 테이블 갱신 (Phase 7)
- [ ] §검증 필요 절 작성 (확정 못한 항목 모두)

### 출처·라이선스
- [ ] 외부 자료 인용 모두 출처 표기
- [ ] (해당 시) revfactory/harness Apache-2.0 명시
- [ ] (해당 시) 논문 인용 형식 (저자 YYYY 저널 vol:page)

---

## 🆕 새 에이전트/스킬 도입 시 (Stage 4 운영)

- [ ] 도입 PR에 should-trigger 10개 + should-NOT-trigger 10개 포함
- [ ] 패턴 명칭 (6개 중 어느 것인지) 명시
- [ ] A/B 비교 결과 첨부 (전/후 산출물 1쌍)
- [ ] CLAUDE.md 트리거 표 갱신 (필요 시)
- [ ] `_workspace/release/agent-XXX-validation-YYYY-MM-DD.md` 작성

---

## ⚠️ 위험 신호 (즉시 작업 중단)

다음 발생 시 즉시 중단하고 사용자 보고:

1. **READ-ONLY 파일 수정 시도** — `data/`, `local_models/`, `paper/`, `_backup/`, `pipeline_local/data/`, `bionemo/`, `tools/harness-adaptation/reference/` (submodule)
2. **GATE-E 출처 미달 30% 이상** — 보고서 신뢰도 자체가 무너짐
3. **GATE-C 범위 외 수치가 단순 오타가 아닌 계산 함수 버그로 추정** — 함수 점검 우선
4. **부호 규약 위반 후 NSGA-II 순위가 뒤집힌 흔적** — H-02 발생 가능성
5. **재시도 루프가 3회 초과** (Producer-Reviewer) — 패턴 선택 오류 가능

---

## 한 줄 운영 격언

> "수치는 어디서 왔는가? 부호는 어느 방향인가? 누가 만들었는가?" — 매 산출물에 답할 수 있어야 함.

---

**End of Checklist.**
