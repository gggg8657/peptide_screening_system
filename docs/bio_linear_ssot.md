# 바이오 AI(방사성 펩타이드) — Linear × Git 단일 진입점

**목적**: 미팅 로그(`meet_log.md`), 산재한 `docs/*`, 레포 코드 변경을 **한 흐름**으로 묶기.  
**원칙**: 실행 가능한 작업·우선순위·상태는 **Linear**가 우선(SSOT). Git은 **근거·재현·장문 보고**를 보관한다.

---

## 1. Linear에서 무엇을 보면 되나

| 구분 | Linear | URL |
|------|--------|-----|
| **바이오 / 방사성의약품 (회의 액션·파이프라인 통합)** | Project **AI Co-Scientist for 방사선의약품** | [열기](https://linear.app/chadkim/project/ai-co-scientist-for-방사선의약품-ff552425a30d) |
| **Epic (회의 A-01~A-10 허브)** | Issue **CHA-116** | [열기](https://linear.app/chadkim/issue/CHA-116/epic-meet-log-a-01a-10-git-연동-허브) — 자식 CHA-117~123, 라벨 `MeetAction` |
| **에이전트/MCP 인프라** | Project **Multi-Agent MCP System** | [열기](https://linear.app/chadkim/project/multi-agent-mcp-system-46b7df6a24c8) |
| **SSTR2 논문 트랙** | Project **SSTR2 AI Agent Paper** | [열기](https://linear.app/chadkim/project/sstr2-ai-agent-paper-2f8dd550157c) |
| 팀 | **CHADKIM** (`CHA`) | Cycle **9** = 현재 주차 파이프라인 묶음, **10** = 다음 주 RI·후속 |

회의 액션 이슈에는 라벨 **`MeetAction`**이 붙어 있다. **Parent = CHA-116** 은 Linear UI에서 자식 이슈에 수동 지정 (MCP `parentId` 제약).

---

## 2. Git에서 무엇이 SSOT인가

| 역할 | 경로 |
|------|------|
| 회의 액션 A-01~A-10 상세·pepADMET 분석 | [`meet_log.md`](../meet_log.md) |
| 통합 추적표(미팅 M2-xx 등) | [`action_items_tracker.md`](action_items_tracker.md) |
| 일자별 진행 스냅샷 | [`progress_report_20260323.md`](progress_report_20260323.md) |
| pepADMET 재현 로드맵 | [`presentation/01_appendix/pepadmet_reproduction_plan.md`](presentation/01_appendix/pepadmet_reproduction_plan.md) |

**규칙**: Linear 이슈 본문 상단에 `Git: meet_log.md#…` 또는 `docs/…` 링크를 한 줄 넣으면 양쪽이 서로 찾기 쉽다.

---

## 3. 회의 액션(A-01~A-10) ↔ Linear 매핑 (등록됨)

프로젝트 **[AI Co-Scientist for 방사선의약품](https://linear.app/chadkim/project/ai-co-scientist-for-방사선의약품-ff552425a30d)** 소속, Epic **[CHA-116](https://linear.app/chadkim/issue/CHA-116)** 기준.

| Meet ID | Linear 이슈 | Cycle | 비고 |
|---------|-------------|-------|------|
| **A-02** | [CHA-117](https://linear.app/chadkim/issue/CHA-117) | 9 | pepADMET/ADMET 일괄 |
| **A-03** | [CHA-118](https://linear.app/chadkim/issue/CHA-118) | 9 | SSTR PDB + 선택성 도킹 |
| **A-04** | [CHA-120](https://linear.app/chadkim/issue/CHA-120) | 9 | 대시보드 연결 |
| **A-05** | [CHA-119](https://linear.app/chadkim/issue/CHA-119) | 9 | Step 3B Tier 병렬 |
| **A-06** | [CHA-121](https://linear.app/chadkim/issue/CHA-121) | 10 | RI 합성 견적 |
| **A-07** | [CHA-122](https://linear.app/chadkim/issue/CHA-122) | 10 | RI C18 설계·검토 |
| **A-09** 후속 | [CHA-123](https://linear.app/chadkim/issue/CHA-123) | 10 | pepADMET 재현 Phase |
| **A-01** | — | — | 코드 반영 완료; 필요 시 **CHA-66**과 링크 |
| **A-08 / A-10** | — | — | 구현 완료; 추가 UX만 필요 시 **CHA-120** 등과 통합 |

---

## 4. Git 커밋 / 브랜치 규칙 (제안)

- 브랜치: `feature/cha-XX-short-topic` (Linear **Issue ID**와 동일 접두)
- 커밋: `feat: 한 줄 요약 [CHA-XX]` 또는 `docs: … [CHA-XX]`
- PR 본문에 **Linear 이슈 링크** 1줄 + **관련 `docs/` 또는 `meet_log` 구간** 1줄

---

## 5. 다음에 할 일 (정리)

1. Linear UI에서 **CHA-117 ~ CHA-123** 각각 **Parent → CHA-116** 설정 (서브이슈 트리).  
2. 진행에 맞춰 Cycle 9 이슈가 끝나면 **Done** 처리; 미완은 Cycle 10으로 드래그.  
3. 이전에 실험용으로 만든 빈 프로젝트 **PRST 방사선의약품 — 회의 액션**은 이슈가 없으면 Linear에서 **아카이브/삭제**해도 됨.  
4. 이 파일은 **온보딩 목차**로 유지; 수치·근거는 `meet_log` / `progress_report`가 SSOT.
