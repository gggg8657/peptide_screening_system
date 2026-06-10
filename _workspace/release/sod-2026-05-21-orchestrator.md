# SOD 2026-05-21 — Orchestrator Start

> **작성 시각**: 2026-05-21 UTC  
> **현재 branch**: `docs/pptx-2026-05-28-3layer-ensemble`  
> **기준 입력**: 2026-05-20 EOD 3건 + 현재 git 상태  
> **운영 원칙**: 다른 세션 미커밋/미추적 산출물은 건드리지 않음

---

## 0. 한 줄 결론

오늘 SOD 1순위는 **어제 열린 3-Layer/회의 D-8/수동 selectivity 후속을 main 상태와 정렬하고, pepADMET/pepMSND 신뢰성 이슈를 정직하게 닫는 것**이다. 현재 로컬은 PR #89~#95 계열 commit 7개를 가진 상태지만 원격 branch 대비 `ahead 7, behind 1` 이므로, merge/rebase 결정 전에는 push/정리 작업을 보류한다.

---

## 1. 현재 상태 스냅샷

| 항목 | 상태 |
|---|---|
| branch | `docs/pptx-2026-05-28-3layer-ensemble` |
| remote divergence | `ahead 7, behind 1` |
| origin only | `2d43e95 docs(pptx): 5월 28일 회의 18 슬라이드 — 3-Layer Ensemble 결과 반영` |
| local only | PR #89, #90, #91, #92, #93, #94, #95 commit 7개 |
| staged | `_workspace/release/eod-2026-05-20-orchestrator-session.md` added |
| untracked | 다수의 `_workspace/release/*`, `.codex/`, `.worktrees/`, `runs_local/*`, FE smoke test 등 |
| working diff | tracked unstaged diff 없음 |

주의: 이 상태는 다른 세션 산출물이 섞여 있을 가능성이 높다. 특히 `runs_local/*`, `.worktrees/*`, FE smoke test, 2026-05-20 release report들은 작성 주체 확인 전 일괄 add/commit 금지.

---

## 2. 어제 EOD에서 이어받은 핵심 사실

### 2.1 Gate-2 / ADMET
- PRST-001~004 기존 ADMET 0.10~0.25는 실측이 아니라 fallback 전파값이었다.
- pepADMET 재검증은 4 후보 모두 `binary_toxicity=1.00` 으로 나왔지만, cyclic 14aa SS-bond/D-AA 입력은 학습 도메인 외 외삽 가능성이 크다.
- 운영 결정은 EOD 간 일부 표현 차이가 다르다.
  - `eod-2026-05-20-orchestrator-session.md`: 옵션 B, OOD 명시 후 의뢰 진행 문서화.
  - `eod-2026-05-20-selectivity-validation.md`: 실제 외주 발주는 하지 않고 리스트 보존 + pepADMET 재훈련 별도 트랙.
- 오늘은 이 차이를 먼저 정리해야 한다. 실 발주 여부를 문서/코드/회의자료에서 같은 표현으로 맞추는 것이 필요하다.

### 2.2 Selectivity / FlexPepDock
- 어제 selectivity 장애의 근본 원인은 receptor 디렉토리 심볼릭 링크, silent estimation fallback, candidate_id 포맷, margin 부호 컨벤션이 겹친 5단 결함이었다.
- PR #69/#70/#71/#82 로 핵심 경로는 정렬되었다.
- 이후 PR #94/#95 로 FlexPepDock per-receptor timeout 6h 및 worker pool 2개가 local commit 에 존재한다.
- 오늘은 실 job 상태와 UI/BE 반영 여부를 smoke test 해야 한다.

### 2.3 3-Layer Ensemble / 회의 D-7
- PR #85: 3-Layer Ensemble framework.
- PR #90: binding pocket 좌표 auth_seq_id 정합성.
- PR #91: 2026-05-28 회의용 18 슬라이드.
- Layer 2 pepMSND-local은 R²=-0.028로 screening 부적합(P4) 정직 보고.
- Layer 3 ADMET-AI는 CPU 추론 성공했지만 H-06 외삽 가드로 의사결정 비권장.
- 오늘은 PR 리뷰 대응 및 회의 Q&A 정교화가 우선이다.

---

## 3. 오늘 우선순위

| 우선 | 작업 | 완료 기준 |
|---|---|---|
| P0 | branch divergence 정리 방침 결정 | `origin` 의 `2d43e95` 와 local `7737650` 중 어느 PPTX commit 이 최종인지 확인 |
| P0 | ADMET/Gate-2 운영 표현 통일 | "발주 진행" vs "발주 안 함, 리스트 보존" 중 현재 결정이 모든 handoff 문서에 일관됨 |
| P1 | PR #89~#95 상태 확인 | main 포함 여부, open/merged 여부, 리뷰 코멘트 여부 정리 |
| P1 | FlexPepDock worker pool smoke | 8787 BE health, `/api/flexpepdock/jobs`, 실제 job progress/timeout/worker count 확인 |
| P1 | 3-Layer Ensemble 검증 | unit/smoke test 가능 범위 실행, Layer별 confidence/disclaimer 출력 확인 |
| P2 | 2026-05-28 회의 D-7 자료 | Q&A, risk slide, "불확실성" wording 정교화 |
| P2 | pepADMET 저자 이메일 | 발송 여부 결정 전 KAERI 행정용 초안만 정리 |

---

## 4. 즉시 실행 체크리스트

1. `git fetch` 후 branch divergence 최신화.
2. PR #84/#85/#90/#91/#94/#95 상태 확인.
3. `git status --short --branch` 재확인 후 소유 불명 파일 분리.
4. BE 8787/Vite 5173 가동 여부 확인.
5. FlexPepDock job endpoint smoke.
6. Ensemble/scoring tests 중 빠른 것부터 실행.
7. Gate-2 발주 상태 문구를 사용자 결정 기준으로 통일.

---

## 5. 손대지 말 것

- `.codex/`, `.worktrees/`
- 대량 `runs_local/*`
- 다른 세션이 만든 것으로 보이는 FE/BE 미추적 파일
- PR 소유자가 불명확한 release report 일괄 commit
- destructive git 명령 (`reset --hard`, checkout 되돌리기 등)

---

## 6. 오늘의 첫 의사결정

**Branch 정리 우선**: 현재 local branch 는 origin 대비 `ahead 7, behind 1` 이다. 원격의 `2d43e95` 와 local 의 `7737650` 이 모두 PPTX 갱신 commit 이므로, 파일 내용 차이를 확인한 뒤 하나로 수렴해야 한다. 이 결정을 하기 전에는 push/merge 작업을 시작하지 않는다.

