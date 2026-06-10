# MASTER EOD 2026-05-21 — Integrated (All Sessions)

> **작성**: orchestrator (action-items-closure-20260521 team-lead, Claude Opus 4.7)
> **통합 범위**: 본 세션(action-items-closure) + 추적 가능한 다른 세션 7개 흔적
> **자료 출처**: `_workspace/release/` 의 5/21 mtime 보고서 + `git log origin/main` 13 PR + tester 보고서
> **한계**: 다른 세션 내부 의사결정·맥락은 디스크/PR 본문 범위로 재구성. 실시간 자율 결정은 누락 가능

---

## 0. 한 줄 결론

오늘 **13 PR 머지** (본 세션 2 + 다른 세션 11). 3-Layer Ensemble framework 가동 (PR #85) + pepADMET 재훈련 OOD 모델 (PR #113) + FE 2-level 셀렉터 (PR #107) + Silo A 라우터 (PR #102) + D-AA SMILES (PR #103) + selectivity silent fallback 제거 (PR #109). PRST-001~004 binary_toxicity=1.0 OOD 아티팩트 완화 + Gate-2 합성 발주 안 함 결정 유지 + 핵심 selectivity 결함 K-1/K-2 본 세션 발견 + 부분 fix (PR #109).

---

## 1. 오늘 머지 PR 13건 (시간순)

| # | 시각 UTC | 분류 | 세션 추정 | PR 제목 |
|---|---|---|---|---|
| #85 | 01:17 | feat | layer-ensemble | 3-Layer Ensemble framework (Layer 1 PlifePred + Layer 2 pepMSND-local + Layer 3 ADMET-AI) |
| #101 | 01:30 | feat(fe) | fe-jobs-status | Manual Selectivity job status chips (colors + icons) |
| #102 | 01:30 | feat(be) | silo-a-router | Silo A 로컬 라우터 Phase 1 (V3-B) |
| #103 | 01:30 | feat(scoring) | daa-smiles | D-AA SMILES 생성 utility (V3-A) |
| #104 | 01:30 | feat(flexpep) | worker-pool | expand worker pool to 4 |
| #105 | 01:30 | feat(wetlab) | wetlab-prst | PRST synthesis orders |
| #106 | 01:30 | feat(fe) | fe-candidate-selector | candidate selector to CandidatePage |
| #84 | 02:13 | docs | meeting-prep | 5월 회의 D-8 준비 + audit 사후 갱신 (rebase) |
| **#108** | 02:46 | fix(pharma) | **본 세션** | cyclic SS-bond OOD guard + composite_scorer fallback WARN |
| #109 | 02:49 | fix(flexpep) | flexpep-silent-fallback | silent 0.0 fallback 제거 — mock 금지 (selectivity 살리기) |
| #110 | 04:19 | feat(scoring) | hle-regression | HLE regression callable wrapper — Layer 1 보강 |
| #107 | 06:16 | feat(fe) | fe-2level-selector | 2-level 셀렉터 — Run + Candidate (사용자 직관 UI) |
| **#113** | 08:49 | feat(pepadmet) | **본 세션** | retrained model + OOD detection — PRST OOD artifact mitigated (sanity PASS) |

**본 세션 머지**: 2건 (#108, #113)
**다른 세션 머지**: 11건

> **📌 정정 메모 (orchestrator-2026-05-20→21 추가)**: 본 통합 EOD가 작성된 시점 기준으로는 PR #84/#85/#90/#91/#110 + 신규 #111/#112가 "다른 세션 머지"로 분류되었으나, 실제로 이 7건은 **`orchestrator-2026-05-20→21` 세션 (어제 세션 연장)** 산출물.
> 본 세션 별도 EOD: [`eod-2026-05-21-orchestrator-3layer-and-followup.md`](eod-2026-05-21-orchestrator-3layer-and-followup.md)
> SOD 시 두 EOD를 함께 읽으면 같은 날 두 orchestrator 세션의 산출이 명확히 구분됨.

---

## 2. 본 세션 (action-items-closure-20260521) 결과

### 2.1 정체
- 역할: orchestrator (Opus 4.7) + 6 명 위임 팀 (backend, research, dock, tester, infra, + 보너스)
- 시작: 어제 selectivity-validation 팀 종료 후 신규 팀 기동
- /goal 프롬프트 v3 작성 후 Group A 실행
- 진행 시간: ~04:00–09:00 UTC

### 2.2 Group A 완전 closure (13/13)
| Task | 결과 |
|---|---|
| A.A1 rosetta_ddg_max | closure (pipeline_local PR #79 완료, AG_src 단위 다름) |
| A.A2 보완 PR #108 | MERGED — 122/122 PASS |
| A.A3 retrain plan SOD | `sod-2026-05-21-pepadmet-retrain-plan.md` |
| A.A4 변이 도킹 진단 | dock 분석 + 실행 명령 + 위험 6건 |
| A.A4-EXEC PRST-001 시범 | FlexPepDock nstruct=50 완주 (BROKEN 7→재시작 후 MutateResidue 모드, SS INTACT 50/50). 최선 ddg **-42.31 kcal/mol** |
| A.A5-0 가용성 진단 | Train.ipynb + model + data + GPL v3 |
| A.A5Pa 데이터 큐레이션 | `Toxicity_extended.csv` 359 row (+224 신규, FDA 10 + Cyclotides 5 + Hemolytik2 209) |
| A.A5Pb-env env 업그레이드 | `pepadmet-upgrade` env (python 3.10 / dgl 2.4 / torch 2.4) + MY_GNN.py 3곳 + build_dataset 1곳 수정 |
| A.A5Pb-data 정제·분할 | `Toxicity_extended_clean.csv` (294, 2139), SS-bond 51 (train 47/val 4/test 0) |
| A.A5Pb-OOD | `pipeline_local/pepadmet_ood/ood_detection.py` Mahalanobis + MC Dropout (10/10 pytest) |
| A.A5Pc 재훈련 | 5 seed CV, early stop epoch 117/300, ~13분, weights 60MB |
| A.A5Pd Sanity | **PASS** — Octreotide 0.132 / SST-14 0.402 / PRST max-min 0.217 |
| A.A5Pe 통합 PR #113 | MERGED — disclaimer 전문 포함 (PRST-001=PRST-004 동일, max-min 간신히, val=0.25 약함, ranking 만, in vitro 교차검증 필수) |

### 2.3 신규 발견 결함 (K-1/K-2)
PRST-001 selectivity production 검증 중 BE 로그 추적으로 발견:
- **K-1**: `_build_pdb_index` 가 `sorted(..., reverse=True)` 알파벳 정렬 — `test_full_pipeline_20260402` ('t' > 'p') 가 본 세션의 `prst_mutdock_20260521` 보다 먼저 매칭 → 본 세션 cand_001 무시
- **K-2**: `_run_offtarget_pyrosetta(sstr2_complex_pdb, receptor_pdb, ...)` 시그니처에 candidate_pdb 인자 없음 → off-target dock 가 baseline (SST-14) 만 사용, 변이 무관 → **모든 후보 동일 결과 = 의미 없음**
- **의미**: PR #82 G-2 머지 후에도 selectivity production 평가는 사실상 baseline 만 평가 — 종단 검증 가치 무력화
- **사용자 결정**: EOD 기록만, 다음 세션. Task #14 pending

### 2.4 PR #109 와의 직결성
**다른 세션 PR #109** (`fix(flexpep): silent 0.0 fallback 제거`) 가 본 세션 K-1/K-2 와 같은 영역의 부분 fix:
- PR #109 fix: `aggregate_scores([], [])` → `(0.0, 0.0)` silent return 제거. 빈 ddg_values 시 `RuntimeError` + `stub_reason='interface_analyzer_failed_all_nstruct'`
- 본 세션 K-1/K-2 와의 관계: PR #109 가 **silent fallback** 표면화 (mock 금지 정책) — 본 세션 K-2 의 일부 (결과 처리 실패 시 0.0 침묵) 를 부분 fix. 다만 **K-1 (run 선택) + K-2 (candidate_pdb 미사용)** 본체 결함은 잔존
- 두 세션이 동시 같은 영역 작업했지만 충돌 없음 — 본 세션은 `pharmacology_guards.py`, 다른 세션은 `flexpep_dock.py`

---

## 3. 다른 세션 활동 (PR + 보고서 흔적)

### 3.1 3-Layer Ensemble framework + HLE 보강 (PR #85, #110)
- **PR #85** `feat/layer1-ensemble-framework-20260520`: Layer 1 PlifePred + Layer 2 pepMSND-local + Layer 3 ADMET-AI. 5 commits rebase 후 머지 (`pr85-rebase-resolve-2026-05-21.md` 참고)
- **PR #110** `feat/hle-regression-callable-wrapper`: `predict_halflife_pepmsnd.predict_halflife_hle_regression` callable + `_predict_hle_regression` adapter. HLE 모델 가중치/실행파일 없어 `unavailable` 반환 (가짜 값 만들지 않음)
- 보고서: `hle_wrapper_2026-05-21.md`

### 3.2 FE 개편 (PR #101, #106, #107)
- **#101**: Manual Selectivity job status chips (색상/아이콘 구분)
- **#106**: CandidatePage 에 candidate selector 추가
- **#107**: 2-level 셀렉터 (Run header + Candidate Mol* 근처) — 사용자 직관 UI

### 3.3 Silo A 인프라 (PR #102, #104)
- **#102**: Silo A 로컬 라우터 Phase 1 (V3-B) — health + dry-run
- **#104**: FlexPepDock worker pool 2→4 (`sod-2026-05-21-worker-pool-4.md` 참고)

### 3.4 D-AA SMILES (PR #103)
- **#103**: D-AA SMILES 생성 utility (V3-A) — pepMSND 학습 D-AA 0건 fix
- A-02 (4/6 회의 액션 아이템) 후속 D-AA HIGH-BLOCKER 의 일부 해소

### 3.5 PRST synthesis orders + 매트릭스 (PR #105 + 보고서)
- **#105**: `wetlab/PRST-001~004 합성 의뢰서` 통합 — 사용자 결정 "리스트만 보존" 정책 반영
- 보고서: `prst-matrix-2026-05-21.md` (Layer 3 ADMET-AI 시각 묶음, **commit 없음** 작성 트리만)

### 3.6 selectivity silent fallback 제거 (PR #109) — 본 세션 K-1/K-2 직결
- 위 §2.4 참조. 본 세션과 같은 도메인이지만 변경 파일 다름 (충돌 없음)

### 3.7 docs/회의 (PR #84)
- 5월 28일 회의 D-7 prep + audit 사후 갱신. rebase 작업 (`pr84-rebase-resolve-2026-05-21.md`)

### 3.8 architecture 문서 (commit 없음)
- `architecture-silo-ab-2026-05-21.md` — team-lead orchestrator 작성. 듀얼 파이프라인 Silo A 3-Arm NIM vs Silo B PyRosetta 구현/미구현 명확화. **본 세션 외 다른 orchestrator** 세션 산출물

---

## 4. 통합 통계

| 항목 | 본 세션 | 다른 세션 합계 | 전체 |
|---|---|---|---|
| 머지 PR | 2 | 11 | **13** |
| 신규 SOD 파일 | 1 (residual-tracks-collection) | 2 (worker-pool-4, retrain-plan*) | 3 |
| EOD/보고서 파일 | 1 (action-items-closure) | 7 (architecture, hle_wrapper, prst-matrix, pr84/85-rebase 등) | 8 |
| 신규 발견 결함 | K-1, K-2 | (PR #109 silent fallback) | 3 |
| 결함 fix PR | 1 (#108) | 2 (#109, #103 V3-A) | 3 |

* retrain-plan 은 본 세션 research 위임 산출이지만 다른 세션에서도 참조됨

---

## 5. 누적 5월 진행 (5/19~5/21 본 세션 기여 한정)

| PR | 날짜 | 내용 |
|---|---|---|
| #69 | 5/20 | git index symlink fix (helloworld 깨진 링크) |
| #70 | 5/20 | D+B 가드 (silent estimation + SST_DATA_DIR env) |
| #71 | 5/20 | G-1 candidate_id format fix |
| #82 | 5/20 | G-2 margin sign convention (yaml SSOT 양수 단방향 정렬) |
| #108 | 5/21 | 보완 PR — cyclic SS-bond OOD guard |
| #113 | 5/21 | pepADMET retrained model + OOD detection |

**누적 6건** (선택성·약리학 신뢰성·가드 강화 트랙)

---

## 6. 잔여 / 다음 세션 P0~P2 인계

### P0 — selectivity 종단 가치 회복 (Task #14 K-1/K-2)
- **K-1**: `_build_pdb_index` 정렬 mtime 기준으로 변경 또는 explicit run_id 선택
- **K-2**: `_run_offtarget_pyrosetta` 에 candidate_pdb 인자 추가 + sstr2_complex peptide chain 을 candidate 변이체로 replace 후 도킹
- 도메인 영역이라 reviewer-science (생물학적 정합성) 사전 검토 권고
- 결합: PR #109 가 silent fallback 표면화 까지 했으니 K-1/K-2 fix 후 진짜 selectivity production 평가 가능

### P0 — 60MB 재훈련 모델 git LFS 통합
- 현 상태: `_workspace/pepadmet_local/pepADMET/model/toxicity_retrained_2026-05-21.pth` 로컬 전용 (.gitignore)
- 결정 필요: git LFS 설치 + 추적 vs 외부 release artifact

### P1 — Group B (G-4~G-8 hook 잔여)
- B1 useSelectivity.stopAnalysis 의 cancel API 호출
- B2 useSelectivity 동명 훅 충돌 rename
- B3 BE 엔드포인트 수 문서 정정
- B4 mount 시 N fetch retention

### P1 — Group C 기술 부채
- C1 qc_ranker.py datetime.utcnow → datetime.now(UTC)
- C2 yaml 잔여 정합 (esmfold_plddt_min, gates_enabled.disulfide)
- C3 깨진 .worktrees 식별

### P2 — Group D
- D2 GPL-3.0 V-04 법무 검토 문서

### Group E — plan 만 (사용자 결정 보류)
- E1 in vitro RBC hemolysis assay 발주 절차 plan
- E2 Boltz complex 로 PRST-001 ΔG 재산출 plan

### 다른 세션 후속 추정 (본 세션 미관여)
- PR #110 HLE wrapper — 실 HLE 모델 가중치 확보 후 `unavailable` → 실 예측 (사용자 V-05 결정 + 학습 작업)
- PR #102 Silo A 라우터 — Phase 2 (실 wiring)
- A-02 D-AA tools — PR #103 후 pepMSND D-AA 학습 (어제 V-A02 권고)
- 5월 28일 회의 PPTX 갱신 (D-7 prep 후 D-1 prep)

---

## 7. v3 /goal 프롬프트 평가

본 세션의 v3 적용 결과:
- ✅ 철칙 9 조항 (A1·D1·E1·I1·J1) 완전 준수 — 외부 메일/API/외주 0, 다른 세션 영역 0 침범
- ✅ Group A 13/13 closure — Group 단위 사용자 confirm G2 정책으로 빠른 진행
- ✅ A5 분기 P/Q + sanity abort 구조 — sanity PASS 케이스에서 자동 진행, fail 시 분기 Q 결정 받을 trigger 명확
- ✅ Producer-Reviewer self-discovery — PR #82 (3 라운드), PR #108 (1 라운드 + LOW), PR #113 (2 라운드 REQUEST_CHANGES → APPROVE) 모두 critical 발견. 신뢰성 입증
- ⚠ backend 4시간 "무응답" 오추정 — 실제로는 RDKit 2026 / NumPy 2.x 호환성 패치 작업. agent 의 silence ≠ stuck
- ⚠ backend 가 PR # 잘못 보고 (PR #112 다른 세션 vs #113 본 세션) — 본 세션이 즉시 검증 안 했으면 잘못된 머지 위험. **검증 의무 강화 필요**

---

## 8. 한 줄 자평 (전체 통합)

오늘 레포지토리는 **13 PR 누적 머지** 와 함께 **3 영역에서 의미 있는 신뢰성 강화**를 달성:
- (1) **약리학 OOD 가드** (PR #108 + #113): PRST binary_toxicity=1.0 외삽 아티팩트 완화 + 명시 disclaimer 가 운영 진입
- (2) **Selectivity silent fallback 차단** (PR #109): mock 금지 정책 적용 + K-1/K-2 잔존 결함 발견까지
- (3) **3-Layer Ensemble framework + Silo A 라우터 + FE 2-level 셀렉터**: 다음 단계 ops 인프라 가동

본 세션은 **Group A 13/13 closure + 통합 master EOD** 까지 마무리. 다음 세션은 **K-1/K-2 fix + git LFS + Group B/C** 로 진짜 production 가치 회복 + 부채 청산.

---

## 9. 본 EOD 작성 한계 명시

- 본 EOD 는 디스크의 5/21 보고서 + `gh pr` 메타데이터 + git log 만으로 재구성
- 다른 세션의 **실시간 자율 결정** (예: PR #109 가 어떤 진단으로 silent fallback 발견했는지) 는 본문 인용 범위로만 추정
- 다른 세션 orchestrator (예: `architecture-silo-ab-2026-05-21.md` 작성자) 의 own EOD 가 있다면 본 통합본은 부분적
- 다른 세션이 작성 의무인 EOD 가 누락된 경우, 그 세션의 작업은 PR 본문 + 보고서 흔적으로만 표현됨

다음 세션 (다른 세션 또는 본 후속) 에서 이 master EOD 를 입력으로 받아 누락분 보강 권고.
