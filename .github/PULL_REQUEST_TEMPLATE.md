<!--
PR 템플릿 — PRST_N_FM
harness Stage 4 의무화 (tools/harness-adaptation/INTEGRATION_PLAN.md)
-->

## 변경 요약

<!-- 한 줄로 이 PR의 목적 -->

## 변경 유형

- [ ] 코드 수정 (`fix`, `refactor`)
- [ ] 새 기능 추가 (`feat`)
- [ ] 문서·설정 (`docs`, `chore`)
- [ ] **신규 에이전트/스킬 도입** (`feat(agent)` / `feat(skill)`)  ← 해당 시 아래 §"신규 에이전트/스킬 의무 검증" 작성 필수
- [ ] **약리학·물리화학 lookup table 변경**  ← 해당 시 §"lookup table 변경 검증" 작성 필수
- [ ] **harness 어댑테이션 변경** (`tools/harness-adaptation/`, `CLAUDE.md §"Harness Pointer"`, `pipeline_local/scripts/pharmacology_guards.py`)  ← 해당 시 §"harness 어댑테이션 변경" 작성 필수

## 테스트

- [ ] `pytest pipeline_local/tests/` 통과
- [ ] (해당 시) 새 테스트 추가 — 어떤 회귀를 차단하는지 PR 본문에 명시
- [ ] (UI 변경 시) 브라우저에서 골든 패스 + 1개 엣지 케이스 수동 확인

---

## 🆕 신규 에이전트/스킬 의무 검증 (Stage 4 — 해당 PR만 작성)

> harness `tools/harness-adaptation/checklist.md §"새 에이전트/스킬 도입 시"` 기반.
> 본 섹션을 채우지 않은 채 신규 에이전트/스킬 PR을 머지하면 안 됨.

### 1. 패턴 선언

- **6개 패턴 중 어느 것인가**: <Pipeline | Fan-out/Fan-in | Expert Pool | Producer-Reviewer | Supervisor | Hierarchical Delegation>
- **선택 이유** (1~3 문장):
- **CLAUDE.md 위임 트리 어느 순위에 속하는가**: <1 tmux | 2 외부 | 3 Agent tool | 4 직접>

### 2. should-trigger 쿼리 (≥8개)

1. ...
2. ...
3. ...
4. ...
5. ...
6. ...
7. ...
8. ...
<!-- 9, 10도 가능. 트리거 커버리지 ≥80% 목표 -->

### 3. should-NOT-trigger 쿼리 (≥8개, near-miss 포함)

1. ...  ← 이 쿼리는 [다른 에이전트/스킬]로 라우팅되어야 함
2. ...
3. ...
4. ...
5. ...
6. ...
7. ...
8. ...

### 4. A/B 비교 결과

- with-skill 산출물 경로: `_workspace/release/<name>-validation-YYYY-MM-DD-with.md`
- without-skill 산출물 경로: `_workspace/release/<name>-validation-YYYY-MM-DD-without.md`
- 측정 기준 (객관 또는 정성): ...
- 결과 요약 (한 줄): ...

### 5. CLAUDE.md 갱신 (해당 시)

- [ ] 자동 트리거 키워드 표에 새 항목 추가
- [ ] §"팀원 목록"에 새 에이전트 추가
- [ ] §"Harness Pointer / Stage 적용 이력"에 항목 추가

---

## 🔁 harness 어댑테이션 변경 (Stage 6 — 해당 PR만 작성)

> `tools/harness-adaptation/`, CLAUDE.md `§Harness Pointer`, `pharmacology_guards.py` 변경 시.

- [ ] `tools/harness-adaptation/CHANGELOG.md`의 `[Unreleased]` 또는 새 minor entry에 본 PR 항목 추가
- [ ] (Stage 도입·변경 시) `CLAUDE.md §"Harness Pointer / Stage 적용 이력"`에 행 추가
- [ ] (산출물 추가 시) `tools/harness-adaptation/README.md` 파일 안내 표 갱신
- 변경 사유 — 1~2 문장으로:

---

## 🧪 lookup table 변경 검증 (Stage 5 — 해당 PR만 작성)

> 약리학·물리화학 lookup table(`KD_HYDROPATHY`, `RW_TRANSFER`, `NEND_HALFLIFE`, `PKA_SIDECHAIN`, `DIWV` 등) 변경 시.

- [ ] `pytest pipeline_local/tests/test_pharmacology_guards.py` 33/33 통과
- [ ] 변경된 키마다 새 정답을 `pipeline_local/scripts/pharmacology_guards.py:LITERATURE_VALUES`에 등록 (출처 인용 포함)
- [ ] 부호 규약(`SIGN_CONVENTIONS`) 영향 검토
- [ ] 변경 사유 — 문헌 갱신? 부호 규약 변경? 버그 수정?

---

## 메모

<!-- 리뷰어가 알아야 할 추가 컨텍스트 -->
