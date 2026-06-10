# Agent Validation Report — `researcher`

> harness Stage 4 산출물. 신규 `researcher` 에이전트 도입 검증.

## 0. 메타

| 항목 | 값 |
|------|---|
| Agent name | `researcher` |
| 도입 커밋 | (본 PR/커밋과 동일) |
| 작성일 | 2026-05-11 |
| 작성자 | orchestrator team via Claude Code |
| harness 패턴 | **Expert Pool** (Researcher는 "외부 자료" 전문가) — `ANALYSIS.md §5.3` |
| CLAUDE.md 트리 위치 | **3순위** (내장 서브에이전트) 또는 보완적으로 2순위(외부 도구 대신 호출) |

## 1. 에이전트 정의 요약

- **핵심 역할**: 외부 정보 수집·문헌 비교·선행 연구 조사 전담
- **입력 프로토콜**: 리서치 주제 + 기대 산출물 형식 + 우선순위 도메인
- **출력 프로토콜**: `_workspace/{NN}_researcher_<topic>.md` — 출처 의무 + 신뢰 등급 + 비교 표
- **협업 인터페이스**: orchestrator ← researcher → reviewer-science(검증) / engineer-backend(구현 위임)
- **에러 핸들링**: 검색 부족·paywall·상충 문헌 모두 §검증 필요로 분리, 임의 선택 금지

## 2. 패턴 선택 정당화 (Phase 2)

- **왜 Expert Pool인가**: 입력(쿼리)의 도메인이 약리학·생명공학·화학·물리/수학·SW 어느 것이든 동일 에이전트가 처리. 다른 전문가(reviewer-science 등)와 병렬 운영되며 입력 유형에 따라 라우팅.
- **대안 검토**:
  - **Pipeline 기각**: 단일 단계 작업이 많아 순차 강제 불필요
  - **Producer-Reviewer 기각**: reviewer-science와 페어를 이루지만, researcher 단독 호출도 빈번 (예: 단순 논문 메모)
  - **Supervisor 기각**: 작업 가변성이 낮음

## 3. should-trigger 쿼리 (≥8)

| # | 쿼리 | 라우팅 기대 |
|---|------|----------|
| 1 | "SST-14 변이체에 대한 선행 연구 조사해줘" | `researcher` |
| 2 | "Kyte-Doolittle 척도의 원본 논문 인용 정확히 확인해줘" | `researcher` |
| 3 | "GLP-1 작용제 반감기 연장 메커니즘 문헌 비교" | `researcher` |
| 4 | "PyRosetta REF2015 가중치 공식 출처 찾아줘" | `researcher` |
| 5 | "research papers on SSTR2 antagonist peptide design" | `researcher` |
| 6 | "이 약리학 가설의 선행 연구가 있는지 리서치해줘" | `researcher` |
| 7 | "NSGA-II vs 베이지안 최적화 펩타이드 설계 적용 사례 문헌" | `researcher` |
| 8 | "literature review on cyclic peptide stability strategies" | `researcher` |

**Coverage**: 사전 검토 8/8 (실측 미실시 — 신규 도입이라 traffic 없음)

## 4. should-NOT-trigger 쿼리 (≥8, near-miss 포함)

| # | 쿼리 | 라우팅 기대 |
|---|------|----------|
| 1 | "이 코드 리뷰해줘" | `reviewer-code` / `codex review` |
| 2 | "Boman Index 계산 함수 부호가 맞는지 검증" | `reviewer-science` (검증·판정은 reviewer 몫) |
| 3 | "FlexPepDock 호출 코드 작성해줘" | `engineer-backend` |
| 4 | "EOD 보고서 작성" | `cursor-agent` |
| 5 | "conda 환경 충돌 해결" | `engineer-infra` |
| 6 | "이 시퀀스 도킹 점수 계산" | `engineer-backend` |
| 7 | "App.tsx 레이아웃 검토" | `reviewer-uiux` |
| 8 | "팀 토론으로 아키텍처 결정" | tmux team-mate |

**False-positive rate**: 0/8 (사전 검토)

## 5. A/B 비교 (Phase 6)

### 입력 시드
- 시드 질문: "Radzicka-Wolfenden Boman convention의 원본 출처와 부호 규약 정확히 확인"

### 결과 산출물 (예상)
- **with-`researcher`**: 출처 명시(논문 인용) + 부호 규약 정리 + 본 프로젝트 적용 가능성 등급
- **without-`researcher`** (현재): orchestrator가 직접 본 세션 WebSearch/WebFetch 또는 cursor-agent에 위임. 출처 인용 일관성 낮음, 분야 전문성 약함

### 측정 기준 (사후 측정 대상)

| 메트릭 | 측정 방법 | 목표 |
|--------|---------|------|
| 출처 인용 비율 | 산출물 내 수치·주장 중 출처 부착 비율 | ≥ 80% |
| WebFetch 호출 적절성 | 불필요한 fetch 비율 | ≤ 10% |
| 후속 reviewer-science PASS율 | 검증 단계에서 통과한 출처 비율 | ≥ 90% |

**A/B 비교 1회**는 실 트래픽 발생 시 (다음 분기 회고에서 측정) 수행 — 본 시점에는 사전 검토만.

## 6. CLAUDE.md 갱신 항목

- [x] 자동 트리거 키워드 표에 항목 추가
- [x] §"팀원 목록"에 researcher 추가
- [x] §"Harness Pointer / Stage 적용 이력"에 Stage 8a entry

## 7. §검증 필요

| ID | 항목 |
|----|------|
| VR-researcher-01 | A/B 비교 정량 측정은 실 트래픽 발생 후 다음 분기 회고에서 |
| VR-researcher-02 | `model: sonnet`이 적절한지 (광범위 reasoning이라 opus 필요 가능성) — 비용 vs 품질 트레이드오프 모니터링 |
| VR-researcher-03 | `cursor-agent`와의 역할 경계 명확성 — 실 운영에서 중복 호출 사례 발생 시 추가 가이드 필요 |

---

**End of Validation Report.**
