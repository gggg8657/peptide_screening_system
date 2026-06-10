# 통합 가이드 — Harness Adapter를 PRST_N_FM에 단계적으로 도입

> `PROMPT_TEMPLATE.md` + `PROMPT_PRST_N_FM_EXAMPLE.md`를 실제 운영에 통합하는 **단계별 로드맵**.
> 각 단계는 독립 가능 — 하나 끝낼 때마다 가치 발생.

---

## Stage 0 — 본 디렉토리 커밋 (완료 시점)

✅ 이 커밋 자체가 Stage 0. 이후 단계는 별도 PR/커밋으로 진행.

**산출물 (이미 존재)**:
- `tools/harness-adaptation/` 전체
- `.gitmodules` (revfactory/harness submodule 등록)
- `.gitignore` 갱신 (`/tools/*` + `!/tools/harness-adaptation/`)

---

## Stage 1 — `_workspace/` 디렉토리 신설 + 파일명 컨벤션 채택

**목표**: 다단계 작업의 중간 산출물 추적 가능화.

**행동**:
1. 프로젝트 루트에 `_workspace/` 생성
2. `.gitignore`에 `/_workspace/` 추가 (산출물은 일반적으로 ignore)
3. `_workspace/README.md` 작성 — 파일명 컨벤션 `{NN}_{agent}_{artifact}.{ext}` 명시
4. 사용 예: 다음 다단계 작업부터 즉시 적용

**검증**:
- 다음 multi-phase 작업의 산출물이 `_workspace/01_*.md` 등으로 저장되는가?

**리스크**: 기존 `logs/external_agents/`와 혼동. → 명확히 구분: `logs/`는 호출 추적(when, who, what command), `_workspace/`는 산출물(content of artifacts).

---

## Stage 2 — `CLAUDE.md`에 Harness Pointer 블록 추가

**목표**: 본 디렉토리의 존재를 CLAUDE.md를 통해 알리고, 트리거 키워드 표에 harness 관련 키워드 추가.

**행동**:
1. `CLAUDE.md`에 다음 추가:
   ```markdown
   ## Harness Pointer
   - 본 프로젝트 harness 어댑테이션: `tools/harness-adaptation/`
   - 범용 프롬프트: `tools/harness-adaptation/PROMPT_TEMPLATE.md`
   - 변경 이력: 본 블록의 아래 표

   | 날짜 | 변경 | 대상 | 사유 |
   ```
2. CLAUDE.md 자동 트리거 키워드 표에 다음 추가:
   | "하네스", "패턴 선택", "팀 아키텍처" | tools/harness-adaptation/ 참조 |

**금지** (`SKILL.md:264-265`): 이 블록에 에이전트·스킬 목록을 직접 기재하지 않음 (목록은 `CLAUDE.md` 별 §"팀원 목록"이 이미 담당).

---

## Stage 3 — 6개 패턴 명칭을 `CLAUDE.md` 의사결정 트리에 매핑

**목표**: 우리 5단계 트리의 각 분기에 harness 6패턴 중 어느 것인지 명시 → 사후 감사 가능.

**행동**: `CLAUDE.md`의 "작업 위임 의사결정 트리" 섹션에 각 분기 옆에 패턴 명칭 추가. 예:

```markdown
### 1순위: tmux team-mate (`/team`)
**패턴**: Fan-out/Fan-in (병렬 토론) 또는 Supervisor (동적 작업 분배)
**조건**: ...

### 2순위: 외부 에이전트 (codex / cursor-agent)
**패턴**: Pipeline (단순 위임) 또는 Expert Pool (codex=코드, cursor-agent=분석)
...
```

**검증**: 다음 위임 결정 시 패턴 명칭을 명시적으로 기록할 수 있는가?

---

## Stage 4 — Phase 6 검증 메커니즘 도입

**목표**: 새 에이전트/스킬 도입 시 should-trigger / should-NOT-trigger 세트 필수화.

**행동**:
1. `tools/harness-adaptation/checklist.md`의 §"새 에이전트 도입" 항목 활용
2. 다음 에이전트 신설 시: trigger query 10+10 세트 작성, A/B 비교 1회 실행
3. 결과를 `_workspace/release/agent-XXX-validation-YYYY-MM-DD.md`에 보존

**검증**: 새 에이전트의 트리거 커버리지가 80% 이상인가?

---

## Stage 5 — 약리학 환각 가드 적용 (도메인 특화)

**목표**: `PROMPT_PRST_N_FM_EXAMPLE.md §3`의 H-01~05 가드를 기존 약리학 평가 코드에 통합.

**행동**:
1. `pipeline_local/scripts/`의 약리학 평가 함수 전수 점검
2. 각 함수의 docstring에 출처(논문, 년도, 표) 명시
3. 부호 규약 주석 추가 (특히 Boman Index)
4. GATE-C 범위 검사를 함수에 코드 레벨로 삽입 (예: `assert -5 <= boman <= 5, "Out of range"`)

**검증**: `pytest -k pharmacology` 통과 + 알려진 오류 케이스(Radzicka-Wolfenden S=1.15, Pro half-life=20) 재발생 안 함.

---

## Stage 6 — Phase 7 진화 메커니즘 운영화

**목표**: 매 PR 또는 매 sprint 종료 시 harness 자체의 변경 이력을 기록.

**행동**:
1. `tools/harness-adaptation/CHANGELOG.md` 신설 (semver 형식)
2. PR 템플릿에 "harness 어댑테이션 변경 사항 (해당 시)" 항목 추가
3. 매 분기 회고 때 PROMPT_TEMPLATE.md 개선점 토론

**검증**: 분기당 최소 1회 CHANGELOG.md 갱신.

---

## Stage 7 — (선택) `.claude/agents/`로 점진적 분리

**목표**: CLAUDE.md의 팀원 목록이 너무 비대해지면 harness 표준 6섹션 형식으로 분리.

**행동** (필요 시점에):
1. `.claude/agents/{name}.md` 디렉토리 신설
2. 각 팀원당 6섹션(핵심 역할/작업 원칙/입력/출력/에러/협업) 채워서 분리
3. CLAUDE.md는 포인터만 유지

**현재 권장**: 미실행. CLAUDE.md가 아직 관리 가능한 크기 → 분리 비용 > 이득.

---

## 리스크·완화

| 리스크 | 완화 |
|--------|------|
| Harness 원본 라이선스(Apache-2.0) 미준수 | `reference/harness/LICENSE` 보존(submodule), 본 디렉토리에 출처 명시 |
| Submodule 사용성 부담 (`git submodule update --init`) | `tools/harness-adaptation/README.md`에 init 명령 안내 |
| 신규 `_workspace/` 디렉토리가 기존 `logs/`와 혼동 | Stage 1 단계에서 README로 역할 분리 명시 |
| 6패턴 매핑이 우리 트리(5단계)와 1:1 안 됨 | 매핑은 "어느 패턴의 실제 구현인지" 표기 정도로 시작 (강제 X) |
| CLAUDE.md 비대화 | Stage 7로 분리 가능 |
| Harness 원본 업데이트 추적 | 분기당 1회 `git submodule update --remote` + CHANGELOG 비교 |

---

## 도입 우선순위 요약

| Stage | 우선순위 | 비용 | 효과 |
|-------|--------|------|------|
| 0 | 완료 | — | — |
| 1 (_workspace/) | High | 낮음 | 다단계 추적성 ↑ |
| 2 (CLAUDE.md 포인터) | High | 낮음 | 발견 가능성 ↑ |
| 5 (약리학 가드) | **Critical** | 중간 | 환각 사고 예방 |
| 4 (Phase 6 검증) | Medium | 중간 | 신규 에이전트 품질 ↑ |
| 3 (패턴 매핑) | Medium | 낮음 | 사후 감사 가능 |
| 6 (진화 메커니즘) | Medium | 낮음 | 장기 유지보수 |
| 7 (.claude/agents/) | Low | 높음 | 현재 불필요 |

**권고 순서**: 0(완료) → 1 → 2 → 5 → 3 → 4 → 6 → (Stage 7은 보류).

---

**End of Integration Plan.**
