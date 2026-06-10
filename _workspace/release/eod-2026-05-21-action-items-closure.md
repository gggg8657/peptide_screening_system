# EOD 2026-05-21 — Action Items Closure (orchestrator)

> **세션 유형**: Claude Code orchestrator (Opus 4.7) + 6 명 위임 팀 (`action-items-closure-20260521`)
> **세션 진행**: ~04:00–08:00 UTC (실 진행 ~4 시간)
> **선행**: 어제 EOD `eod-2026-05-20-selectivity-validation.md`, 오늘 SOD `sod-2026-05-21-residual-tracks-collection.md`, /goal 프롬프트 v3 `goal-prompt-2026-05-21.md`

---

## 0. 본 세션의 역할 (Session Identity)

본 세션은 **v3 /goal 프롬프트의 Group A 실행자** + **PRST-001 selectivity production 검증자** + **pepADMET 재훈련 trajectory 운영자**. 어제 selectivity-validation 팀이 자동 종료된 상태에서 신규 팀 `action-items-closure-20260521` 기동 후 Group A 의 4 트랙 (rosetta_ddg_max 통일, 보완 PR, retrain plan SOD, 변이 도킹 진단) + A.A5 분기 P 시작.

본 세션이 한 일:
1. v3 /goal 프롬프트 작성 (v1→v2→v3) — 사용자 정책 결정 10개 반영 + A5 재훈련 의미 있게 만들기 위한 분기 P/Q + sanity abort 구조
2. 잃은 위임 (어제 backend/research/dock unreachable) 식별 + 신규 팀 기동
3. PR #108 (보완 PR — pharmacology_guards SS-bond + composite_scorer WARN) 머지
4. PRST-001 nstruct=50 시범 도킹 운영 (BROKEN 7 → MutateResidue 모드 전환 → 50 완주, 최선 ddg=-42.31)
5. Selectivity production 검증 시 K-1/K-2 새 결함 발견 (의미 있는 negative finding)
6. A.A5 분기 P 실 실행 시작 — A5Pa·A5Pb-env 완료, A5Pb-data 이후 backend 무응답으로 일시 중단
7. 본 EOD + 다음 세션 인계

본 세션이 안 한 일:
- 다른 세션 worktree 18개 영역 미관여 (daa-smiles-v2, fe-*, llm-vllm-upgrade, flexpep-timeout, worker-pool, planner-prompt, orphan-cleanup 등)
- 외부 메일·API 신청·외주 발주 (철칙 A1)
- main 직접 push (전부 PR)
- 사용자 결정 사항 (재훈련 plan→실 실행 결정, in vitro 발주, NIM API key 등)

---

## 1. 본 세션 머지 PR

| PR | merge commit | 내용 | 라운드 |
|---|---|---|---|
| **#108** | (early 5/21) | 보완 PR — pharmacology_guards cyclic SS-bond OOD 분기 + composite_scorer fallback WARN 회귀 테스트 (122/122 PASS) | tester APPROVE 1라운드 + LOW 권고 1건 반영 |
| **#113** | `f72c48e` | feat(pepadmet): retrained model + OOD detection — PRST OOD artifact mitigated (sanity PASS). 9 파일, +1930/-4, disclaimer 전문 포함 (PRST-001=PRST-004 동일, max-min 0.217 간신히, val=0.25 약함, ranking 만, in vitro 교차 검증) | tester 2 라운드 (REQUEST_CHANGES → APPROVE, test_ood_detection.py git 누락 fix) |

**총 머지 2건** (어제 4건 + 오늘 2건 = 누적 **6건**: #69·#70·#71·#82·#108·#113)

---

## 2. Group A 진행 결과

| Task | 상태 | 결과 |
|---|---|---|
| A.A1 rosetta_ddg_max | ✅ closure | pipeline_local 5곳 PR #79 완료. AG_src 는 단위 자체가 kcal/mol 라 변경 불가 (의미 다름). AG_src 운영 시 별도 SST-14 ΔΔG kcal/mol 측정 후 갱신은 별도 트랙 |
| A.A2 보완 PR #108 | ✅ MERGED | 묶음 A SS-bond OOD 가드 + 묶음 B 회귀 테스트 (묶음 B 본체는 다른 세션이 이미 main 머지). 122/122 PASS |
| A.A3 retrain plan SOD | ✅ closure | `_workspace/release/sod-2026-05-21-pepadmet-retrain-plan.md` (research). 분기 P 가능, conda env 위험, DBAASP 1위, Mahalanobis+MCDropout, sanity 3종, 12-24h |
| A.A4 도킹 진단 | ✅ closure | PRST PDB 전무, 방법 A flexpep_dock.py CLI (`_build_pdb_index` 매칭), 나중에 발견된 Critical B-2 (worker pool 경로 불일치) |
| A.A5-0 가용성 | ✅ closure | 분기 P 가능 확정 (Train.ipynb + model + data + requirements 가용) |
| **A.A4-EXEC** | ✅ closure (PR 미생성) | PRST-001 FlexPepDock nstruct=50 완주: 최선 ddg=-42.31 kcal/mol, SS bond INTACT 50/50, 106분 |

### Group A 첫 번째 큰 사건 — FlexPepDock SS bond BROKEN → MutateResidue 모드 전환
- 초기 fallback 모드 (extended peptide) 강제 → SG-SG 37.1 Å BROKEN, ddg +555~+591 (의미 없는 결과)
- 근본 원인: `flexpep_dock.py::_find_reference_complex()` 가 찾는 3 경로 모두 없음
- 해법: `ln -sf SSTR2_SST14_complex_boltz_1.pdb SSTR2_7XNA_complex.pdb` 심링크 1개 → MutateResidue 모드 진입
- 재시작 후 SG-SG 2.0~2.06 Å INTACT 50/50, 최선 ddg -42.31

---

## 3. A.A5 분기 P 진행 결과 (재훈련 trajectory)

| Task | 상태 | 결과 |
|---|---|---|
| A.A5Pa 데이터 큐레이션 | ✅ closure | `Toxicity_extended.csv` 359 row (+224 신규: FDA 10 + Cyclotides 5 + Hemolytik2 209). non-toxic 145, toxic 109, NaN 105 |
| A.A5Pb-env env 업그레이드 | ✅ closure | `pepadmet-upgrade` env: python 3.10 / dgl 2.4.0+cu121 / torch 2.4.1+cu121 / rdkit 2026.3.2. MY_GNN.py 3곳 + build_dataset.py 1곳 수정. smoke test 통과 |
| A.A5Pb-data 정제·분할 | ✅ closure | `Toxicity_extended_clean.csv` (294×2139), NaN 26 행, SS-bond 51 (train 47/val 4/test 0) |
| A.A5Pb-OOD detection | ✅ closure | `pipeline_local/pepadmet_ood/ood_detection.py` — Mahalanobis distance + MC Dropout (10/10 pytest PASS) |
| A.A5Pc 재훈련 5-fold CV | ✅ closure | `toxicity_retrained_2026-05-21.pth` (60MB, 로컬 전용, .gitignore). 5 seed early stop, task_0 val AUC ~0.95, 복합 val=0.25. 13분 소요 |
| A.A5Pd Sanity check | ✅ PASS | Octreotide=0.1322, SST-14=0.4022, PRST max-min=0.2174 (전 3 기준 통과) |
| A.A5Pe 통합 PR | ✅ MERGED (PR #113, `f72c48e`) | disclaimer 전문 포함. tester 2 라운드 (REQUEST_CHANGES → APPROVE) |

### Sanity check 실제 결과 (PASS)
- 우려와 달리 sanity 통과: Octreotide 0.132 (안전 명확), SST-14 0.402 (간신히), PRST max-min 0.217 (간신히)
- 다만 PRST-001 = PRST-004 = 0.402 (정확 동일, 변이 구별력 매우 약함)
- val score 0.25 (best, 복합) — 절대 신뢰도 낮음, task_0 단독 val AUC ~0.95
- PR #113 disclaimer 에 "ranking 만 사용, in vitro 교차 검증 필수, 합성 단독 근거 금지" 명시

### 운영 결정 (사용자)
- PR #113 disclaimer 포함 머지 결정 — 즉시 squash 머지 (Recommended 채택)
- 60MB .pth 는 로컬 전용 (.gitignore), git LFS 결정은 다음 세션

---

## 4. 🔴 새로운 결함 K-1·K-2 (PRST-001 검증 중 발견)

selectivity production mode 진입은 됐지만 **off-target 4 receptor 다 0.0** 잔존 → BE 로그 추적 결과:

### K-1: `_build_pdb_index` 알파벳 reverse 정렬
- 현 코드: `sorted(runs_dir.glob("*/sst14_agentic_mutdock"), reverse=True)` → ASCII reverse
- `test_full_pipeline_20260402` ('t'=116) > `prst_mutdock_20260521` ('p'=112) → test_ 가 먼저 매칭
- 결과: 본 세션이 만든 `prst_mutdock_20260521` 디렉토리 무시, baseline 으로 `test_full_pipeline_20260402` 사용
- **수정 방향**: mtime 기준 정렬 또는 explicit run 선택

### K-2: `_run_offtarget_pyrosetta` 시그니처에 candidate_pdb 인자 없음
- `_run_offtarget_pyrosetta(sstr2_complex_pdb, receptor_pdb, ...)` — 변이 candidate 무관
- off-target dock 가 SSTR2-SST14 baseline complex 의 peptide 를 다른 receptor 에 도킹 → 모든 후보가 동일 결과 (= 0.0 또는 동일 값)
- **수정 방향**: candidate_pdb 인자 추가, sstr2_complex 의 peptide chain 을 candidate 변이체로 replace 후 도킹

→ **PR #82 머지 (G-2 margin sign convention) 이후에도 selectivity production 평가는 사실상 모든 후보에 baseline 만 평가**. **selectivity 종단 검증의 가치를 무력화**. 본 세션 발견의 가장 큰 의미 있는 negative finding.

---

## 5. 운영 사건 (Operational Events)

| 시각 | 사건 | 처치 |
|---|---|---|
| 02:30~ | 어제 위임한 backend/research/dock 모두 unreachable | 신규 팀 기동, 잃은 작업 재위임 |
| 03:00 | PRST-001 FlexPepDock 시작 (fallback 모드) | nstruct 4/4 BROKEN 확인 |
| 03:16 | abort + 심링크 + 재시작 (본 세션 판단) | MutateResidue 모드 진입, SS INTACT 50/50 |
| 03:31 | A5Pa (research) + A5Pb-env (infra) 동시 완료 | A.A5 chain 다음 단계 위임 |
| 03:40 | backend 에 A.A5 chain 위임 | Task #9 시작 명령 |
| 07:53 | backend ~4시간 idle 만 보고, 본 세션 무응답 추정 | 사용자에게 보고, A.A5 chain 중단 추정 |
| 08:00 | 본 세션이 직접 selectivity /run 호출 | production 진입 확인 + K-1/K-2 발견 |
| 08:02 | EOD 작성 완료 후 backend 실제 응답 — 실은 context 전환 + RDKit 2026/NumPy 2.x 호환성 패치 작업으로 03:40→07:40 지연된 것 (무응답 아님) | EOD §3·§5·§7 부분 정정 필요 (아래 §11 부록) |

---

## 6. 다른 세션 활동 좌표 (5/20 이후)

본 세션 외 진행:
- main: PR #84/#100/#105/#106 (대규모 머지: D-7 prep, EOD 통합, PRST synthesis orders FE, candidate selector FE)
- `.worktrees/`: 18개 (daa-smiles-v2, fe-jobs-status-v2, fe-llm-ux, fe-stub-badge, fe-warning-banner, feat-fe-about-migration, feat-fe-data-integration, fe-cd-pages, flexpep-timeout, llm-vllm-upgrade, molstar-fix, orphan-cleanup, planner-prompt, pr85-rebase, silo-a-v2, worker-pool, g2-margin-convention-20260520, selectivity-cid-fix-20260520, selectivity-guard-20260520, pepadmet-guards-20260520)
- session 13 (Cursor Composer 동일 브랜치) — PR 머지 후 자동 처리

본 세션 머지 PR (#108) 와 main 진화 8 PR 사이 충돌 없음 확인.

---

## 7. 다음 세션 인계 (Critical) — 우선순위 P0 ~ P2

### P0 — A.A5 chain 모니터 (backend 자율 진행 중)
- backend 가 EOD 작성 직후 응답 — 실제로는 RDKit 2026/NumPy 2.x 호환성 패치로 03:40→07:40 지연됐을 뿐 작업 진행 중
- Task #9 (descriptor 81/160 → 08:11 완료) → #10 (OOD) → #11 (재훈련) → #12 (sanity) → #13 (통합 PR) 자율 chain
- 다음 세션은 progress 모니터 + 단계별 결과 확인 + 사용자 confirm (sanity fail 시)
- 만약 backend 가 다시 응답 안 하면 codex 폴백 (C2 정책)

### P0 — K-1/K-2 결함 fix
- `step05b._run_offtarget_pyrosetta` 에 candidate_pdb 인자 추가 + sstr2_complex peptide chain 을 candidate 로 replace 후 도킹
- `_build_pdb_index` 정렬 mtime 기준으로 변경 (또는 명시적 run_id 선택)
- 도메인 영역이라 reviewer-science (생물학적 정합성) 사전 검토 권고

### P1 — Group B (G-4~G-8 jvavid 잔여) 시작
- B1 useSelectivity.stopAnalysis() 가 cancel API 호출 (hook 1 함수)
- B2 useSelectivity 동명 훅 충돌 rename
- B3 BE 엔드포인트 수 문서 정정
- B4 mount 시 N fetch retention 정책

### P1 — Group C 기술 부채
- C1 qc_ranker.py datetime.utcnow → datetime.now(UTC)
- C2 yaml 잔여 정합 (esmfold_plddt_min 60↔50, gates_enabled.disulfide false↔true)
- C3 깨진 .worktrees 식별 (helloworld 심링크 잔존 여부, 본 세션 삭제 X)

### P2 — Group D
- D2 A-03 V-04 GPL-3.0 라이센스 법무 검토 문서

### Group E — plan 만 (사용자 결정 보류)
- E1 in vitro RBC hemolysis assay 발주 절차 plan
- E2 Boltz complex 로 PRST-001 ΔG 재산출 plan

### 본 세션 worktree 정리 권고
- 머지 완료된 4 worktree (`selectivity-guard-20260520`, `selectivity-cid-fix-20260520`, `g2-margin-convention-20260520`, `pepadmet-guards-20260520`) 는 사용자가 `git worktree remove` 가능. 본 세션이 자동 삭제하지 않음

---

## 8. v3 /goal 프롬프트 자가 평가

v3 가 본 세션에 미친 영향:
- ✅ 철칙 9 조항 (A1·D1·E1·I1·J1) — 외부 메일·API·외주 0 유지, 다른 세션 영역 0 침범
- ✅ A5 분기 P/Q + sanity abort — 실 실행 진입 시 무한 재훈련 루프 차단 구조 명확
- ✅ Group 전환 시점만 사용자 confirm (G2) — 빠른 진행 (PR #108 머지·dock abort 본 세션 판단)
- ⚠ A5 chain 직렬 5단계 — backend 무응답 1단계에서 중단. 다음 세션이 재기동 필요
- ⚠ 외부 CLI 활용 (C2) — 본 세션은 backend 위임만 사용, codex/cursor-agent 활용 미시도. 다음 세션이 backend 안 움직일 때 codex 폴백 권고

---

## 9. 본 세션 머지 통계 (오늘만)

- 머지 PR: **2건** (#108, #113)
- 완료 Task: **13건** (A1·A2·A3·A4·A5-0·A4-EXEC·A5Pa·A5Pb-env·A5Pb-data·A5Pb-OOD·A5Pc·A5Pd·A5Pe — Group A 전부)
- 미완 Task: 1건 (#14 K-1/K-2 — 사용자 결정 EOD 기록만)
- 신규 발견 결함: 2건 (K-1·K-2)
- 사용자 결정 받은 횟수: 7회 (Group A 트랙 선택·재훈련 진행·SS bond 부족 처리·nstruct 전략·K-1/K-2 처리·Task #13 PR 진행·PR #113 머지)

---

## 11. EOD 작성 후 정정 사항 (부록)

### 11.1 backend 응답 지연 사유 (1차 부록)
EOD 작성 시점 (08:02) 에 backend 무응답으로 추정했으나 직후 backend 응답 — 실제로는:
- A.A5 chain 위임 받은 후 context 전환 + RDKit 2026/NumPy 2.x 호환성 패치 작업 (estate.py, scipy.sum, numpy.float, GetSSSR len 등) 으로 03:40→07:40 까지 약 4시간 진단·패치
- 07:40 descriptor 계산 본격 시작, 08:06 완료
- backend 가 pepadmet (Python 3.7, RDKit 2022) 환경으로 descriptor 계산, pepadmet-upgrade (RDKit 2026) 는 GNN 학습 전용 — 의미 있는 자율 판단

### 11.2 A.A5 chain 자율 완주 (2차 부록)
- 08:13 Task #11 첫 실행 fail (`Parent directory model does not exist`) → 본 세션 `mkdir -p _workspace/pepadmet_local/model` + backend EarlyStopping filename 절대경로 fix
- 08:30 5 seed CV 완료 (13분), sanity PASS
- 08:38 backend 가 PR #112 로 잘못 보고 (다른 세션 pepMSND PR 과 혼동, 잘못된 브랜치 체크아웃 상태에서 commit)
- 08:44 본 세션 잘못 보고 발견 → backend 정정 요청 + backend 가 PR #113 자체 생성
- 08:49 tester REQUEST_CHANGES (test_ood_detection.py git 누락) → 08:51 backend fix
- 08:54 tester APPROVE → 즉시 squash 머지 (`f72c48e`)

### 11.3 교훈 (다음 세션 입력)
- agent 의 idle notification ≠ "작업 안 함" — env 의존성 진단/패치 단계가 길어질 수 있음. 4시간 무응답 보다 일찍 (1-2시간 시점) ping + progress 요청이 효율적
- agent 가 "PR # 보고" 받으면 본 세션이 즉시 PR URL/제목 검증 의무 — backend 가 잘못된 브랜치에서 commit 한 사실 발견 못 했으면 EOD 에 잘못된 PR 들어갔을 위험
- v3 의 sanity abort 정책 (즉시 abort + 사용자 보고) 이 무한 재훈련 루프 차단했으면서도 sanity PASS 케이스에서는 자동 진행 — 정상 작동
- tester self-discovery 패턴 (PR #82 3 라운드, PR #108 1 라운드 + LOW, PR #113 2 라운드) 모두 critical 발견 — Producer-Reviewer 신뢰성 입증

---

## 10. 한 줄 자평

본 세션은 "잃은 4 트랙 재기동 + PRST-001 시범 도킹 + pepADMET 재훈련 trajectory" 으로 출발해 **Group A 의 13/13 완전 closure** (PR #108 보완 가드 + PR #113 재훈련 모델 + OOD detection), PRST-001 의 의미 있는 ddg=-42.31 산출, selectivity production 의 미보고된 K-1/K-2 결함 발견, pepADMET sanity PASS (Octreotide 0.132, SST-14 0.402, PRST max-min 0.217) 까지 도달. 4시간 backend "무응답" 으로 보였던 시간은 RDKit 2026/NumPy 2.x 호환성 패치 작업 — 잘못된 추측. 다음 세션은 K-1/K-2 fix + Group B/C/D + (선택) git LFS 60MB 모델 통합.
