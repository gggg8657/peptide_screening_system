# SOD 2026-05-21 — 잔여 트랙 수렴 + 필요 PR 머지

**세션**: 본 세션 (orchestrator) — 어제 EOD `eod-2026-05-20-selectivity-validation.md` 의 진행 중 4 트랙 마무리에 집중.

## 0. 한 줄 목표

어제 5/20 EOD §5 의 4 트랙 (research×2, dock, backend) 결과를 수렴해 머지 결정·문서화하고, 본 세션이 진짜로 마무리해야 닫을 수 있는 것만 닫는다. 새 트랙 (vLLM/UI 점검, pepADMET 재훈련 실 실행, in vitro 발주 절차) 은 본 SOD 범위 밖.

## 1. 이월 트랙 4건

| Task | Owner | 어제 상태 | 오늘 처리 |
|---|---|---|---|
| #3 `rosetta_ddg_max` AG_src 단위 혼재 조사 | research | 진행 (PR #79 가 pipeline_local 만 fix, AG_src 의 `-5.0 kcal/mol` 잔존) | 결과 도착 → caller 매트릭스·통일 권고 검토 → 별도 PR 진행 여부 결정 |
| #4 PRST 변이 도킹 진단 | dock | 진행 (mutdock pipeline 실행 가능성·예상 시간·GPU 진단 요청) | 결과 도착 → 실 실행 여부 사용자 confirm |
| #11 보완 PR — guards SS-bond + composite_scorer fallback WARN + ensemble/layer1 통합 | backend | 진행 (worktree `pepadmet-guards-20260520`) | PR 도착 → tester 리뷰 → 머지 결정 |
| #12 pepADMET 재훈련 plan SOD | research | 진행 (`sod-2026-05-20-pepadmet-retrain-plan.md` 신규 작성) | SOD 도착 → 검토 후 다음 세션 실행 입력으로 보관 (실 재훈련 X) |

## 2. 작업 순서

### Step 1 — 트랙 상태 확인 (5분)
- `TaskList` + `TaskGet` 으로 각 Task 의 최신 메시지·완료 여부
- 도착 안 한 트랙에는 ping (이전 메시지 mailbox 확인 + 진행 상황 요약 요청)

### Step 2 — backend #11 보완 PR 수렴 (가장 우선)
- tester 리뷰 결과 받기 → APPROVE 시 머지 결정 받기 → squash 머지
- REQUEST_CHANGES 시 backend 가 반영 후 재요청 (PR #82 패턴 재사용)
- 머지 후 본 EOD §3 ADMET OOD 결정의 코드 측면 closure

### Step 3 — research #3 (rosetta_ddg_max AG_src) 수렴
- caller 매트릭스 + 권고 받기
- AG_src 의 `-5.0 kcal/mol` 통일 PR 필요 여부 사용자 결정
- 필요 시 backend 위임 (영역 침범 위험 — PR #82 패턴 적용, 영향 분석 의무)

### Step 4 — research #12 retrain plan SOD 검토
- 신규 SOD 작성 완료 → plan 핵심만 본 세션 EOD 에 인용
- 실 재훈련은 다음 세션 (사용자 결정 후) — 본 SOD 범위 밖
- plan 의 4 섹션 (데이터 큐레이션, 재훈련 전략, 메트릭, 일정·자원) sanity check

### Step 5 — dock #4 변이 도킹 진단 수렴
- mutdock pipeline 가용성 + 예상 시간·GPU 보고 받기
- 실 실행 여부 사용자 confirm — production 시간 비용 큰 작업이라 holding 가능성 큼
- holding 시 다음 세션 입력으로만 (본 SOD 범위 밖)

### Step 6 — EOD 작성 + 본 세션 종료
- 4 트랙 수렴 결과 + 추가 머지 PR (있다면) + 잔여 SOD 후보 정리
- `eod-2026-05-21-residual-tracks-collection.md`

## 3. 결정 대기 (예상)

| 시점 | 대기 결정 |
|---|---|
| Step 2 | backend 보완 PR 머지 (예상: APPROVE 시 즉시 머지) |
| Step 3 | AG_src `rosetta_ddg_max` 통일 PR 진행 (예상: 권고 의존) |
| Step 5 | dock 실 변이 도킹 실행 (예상: holding) |

## 4. 다른 세션과의 경계

- 본 SOD 는 어제 본 세션 위임의 closure 만. 다른 세션 활동 (Codex, FE/BE 검증 세션) 은 좌표만, 미관여.
- 어제 EOD §4 의 다른 세션 8 PR (#68/#72/#73/#74/#78/#79/#81/#83) 은 이미 머지됨 — 추가 추적 불필요.
- 새 SOD 트랙 (vLLM/UI 점검, pepADMET 재훈련 실, in vitro 발주) 은 본 SOD 안 다룸.

## 5. 본 세션 범위 밖 (다음 SOD 후보)

| 후보 | 트리거 |
|---|---|
| pipeline_local · vLLM · UI 점검 v1.2~ | 사용자 IDE 열린 계획서, 본 SOD 끝난 뒤 결정 |
| pepADMET 재훈련 실 실행 | research #12 plan + 사용자 승인 |
| In vitro RBC hemolysis assay 발주 절차 | pharma+bio 권고, 외주·내부 lab 결정 |
| AG_src `rosetta_ddg_max` 단위 통일 PR | research #3 권고 + Step 3 사용자 결정 |
| Boltz complex 로 PRST-001 ΔG 재산출 | 어제 V-A09-06 잔여 |

## 6. 컨디션·메타

- 본 세션은 5/19 마라톤 + 5/20 selectivity sprint 직후. 본 SOD 는 의도적으로 "닫는 작업" 만 — 새 큰 트랙 시작 X.
- 위임 4 트랙 결과만 받고 정리해 깔끔히 EOD 마무리. 다음 세션이 새 트랙 시작.
