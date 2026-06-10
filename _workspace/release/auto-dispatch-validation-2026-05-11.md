# Auto-Dispatch Validation Report — Stage 8c

> harness Stage 8c 산출물. `scripts/auto_dispatch.sh` 자동 라우팅·호출 파이프라인 검증.

## 0. 메타

| 항목 | 값 |
|------|---|
| Stage | 8c |
| 신설 스크립트 | `scripts/auto_dispatch.sh` (208줄) |
| 확장 에이전트 | `orchestrator` — §"외부 CLI 자동 dispatch" 추가 |
| 패턴 | **Expert Pool** (입력 키워드 → CLI 라우팅) — `ANALYSIS.md §5.3` |
| 작성일 | 2026-05-11 |

## 1. 자동화 범위·한계

| 항목 | 자동화 |
|------|------|
| Codex 호출 | ✅ 자동 (`codex review`, `codex exec`) |
| Cursor Agent 호출 | ✅ 자동 (`cursor-agent -p`) |
| 결과 보존 (`_workspace/{NN}_*.md`) | ✅ 자동 |
| 호출 로깅 (`logs/external_agents/`) | ✅ 자동 (기존 `agent-wrapper.sh` 활용) |
| Claude Code 내부 에이전트 (researcher, reviewer-*) | ❌ 안내만 출력 — 본 Claude Code 세션 Agent tool 의무 |
| unmatched 입력 자동 추측 | ❌ 명시적 거부 (할루시네이션 차단) |
| Codex/Cursor 응답 품질 보장 | ❌ orchestrator가 후속 검증 |

## 2. 라우팅 규칙 (CLAUDE.md 트리거 표와 일치)

```
입력 키워드           → 라우팅
─────────────────────────────────────────
"리뷰해" (코드)        → codex:review
"구현해", "수정해"     → codex:exec
"테스트 생성"          → codex:exec
"EOD", "일정", "보고"  → cursor:prompt
"분석해", "조사해"     → cursor:prompt

(아래는 internal: prefix로 안내만)
약리학·ADMET·반감기 등 → reviewer-pharma
구조·SS bond·GPCR     → reviewer-biology
합성·modification·DOTA → reviewer-chemistry
NSGA·BO·통계          → reviewer-math
UI/UX                 → reviewer-uiux
conda·GPU·CI          → engineer-infra
팀·토론·검토회의       → tmux-team
리서치·문헌·논문       → researcher

매칭 실패              → unmatched (사용자에게 prefix 요청)
```

## 3. should-trigger / should-NOT-trigger 검증

### 실측 dry-run 결과

| 입력 | 기대 | 실측 | PASS? |
|------|------|------|------|
| "이 backend/foo.py 코드 리뷰해줘" | codex:review | codex:review | ✅ |
| "오늘 EOD 보고서 작성" | cursor:prompt | cursor:prompt | ✅ |
| "Boman Index 부호 확인" | internal:reviewer-pharma | internal:reviewer-pharma | ✅ |
| "NSGA-II 수렴 진단" | internal:reviewer-math | internal:reviewer-math | ✅ |
| "오늘 날씨 알려줘" | unmatched | unmatched | ✅ |

**5/5 PASS**. 추가 should-NOT-trigger 검증은 분기 회고에서 실 트래픽으로.

## 4. A/B 비교

### 비교 시드
- 시드 작업: "이 PR 코드 리뷰 + EOD 보고서 작성" (2단계 작업)

### 비교

| 항목 | with auto_dispatch | without (수동) |
|------|------------------|--------------|
| orchestrator 라우팅 단계 수 | 1 (`auto_dispatch.sh "..."`) | 3 (라우팅 판단 + agent-wrapper 호출 + 결과 보존 수동) |
| 결과 파일 컨벤션 일관성 | 보장 (`_workspace/{NN}_*.md` 자동) | 사람 의존 |
| 호출 로깅 | 보장 (기존 wrapper 통합) | 보장 (기존 wrapper) |
| 미스매치 처리 | 명시적 거부 + 가이드 | 즉흥적 추측 위험 |

### 정량 (실 트래픽 후 측정)

| 메트릭 | 목표 |
|--------|------|
| 라우팅 정확도 | ≥ 90% |
| unmatched 비율 | ≤ 20% (모호 입력 자연 발생률) |
| 결과 파일 자동 보존율 | 100% |

## 5. 보안·안전성

- `codex exec --dangerously-bypass-approvals-and-sandbox` 사용 (기존 wrapper L57) — sandbox 우회. 실 운영 시 신중.
- `tee -a` 로 stdout/stderr 모두 캡처 — secret leak 가능성. `.gitignore`의 `_workspace/*` 패턴으로 raw 결과는 ignore.
- `set -euo pipefail` — 실패 시 즉시 정지.

## 6. CLAUDE.md 갱신 항목

- [x] §"외부 CLI 자동 dispatch" 추가 (orchestrator.md)
- [x] Stage 8c 이력 entry
- [ ] (선택) 자동 트리거 표 상단에 "자동 dispatch 사용 가능" 표기

## 7. §검증 필요

| ID | 항목 |
|----|------|
| VR-autodispatch-01 | 실 트래픽 라우팅 정확도 측정은 분기 회고에서 |
| VR-autodispatch-02 | `codex exec --dangerously-bypass-approvals-and-sandbox` 사용의 적절성 (security review 필요) |
| VR-autodispatch-03 | 한글 prompt를 그대로 codex/cursor에 전달 — 두 CLI의 한국어 응답 품질 모니터링 |
| VR-autodispatch-04 | 키워드 매칭의 false-positive — 분기 회고에서 unmatched 외 잘못 라우팅된 사례 수집 |

---

**End of Auto-Dispatch Validation Report.**
