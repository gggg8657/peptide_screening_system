# Session Tracker 2026-05-20 (T2 by tracker)

> **작성**: tracker (engineer-infra, read-only 정찰)  
> **일시**: 2026-05-20 오후  
> **정찰 방법**: git log/diff/status + file read 전용. 코드 변경 없음.  
> **컨텍스트**: 어제(2026-05-19) 다른 세션들이 24 PR 머지 + Action Items 9/9 완료 + Gate-2 진입.

---

## 1. 활성 브랜치 매트릭스

### 오늘(2026-05-20) 핫픽스 브랜치

| 브랜치 | HEAD | 변경 파일 | 주요 파일 | Action Item 매핑 |
|--------|------|----------|----------|----------------|
| `chore/selectivity-guard-20260520` | `f125e61` | 3개, +434/-3 | `backend/routers/selectivity.py`, `backend/state.py`, `tests/test_selectivity_guard.py` | hotfix D+B (silent estimation 차단 + SST_DATA_DIR env) |

#### 최근 커밋 (5개)
```
f125e61 fix(selectivity): 정공 조치 D+B — silent estimation 차단 + SST_DATA_DIR env 경로
4d3583c feat(scoring): P1/P2 sprint 손실 복구 — ENDPOINT_CONFIDENCE 11개 + HEURISTIC 4개 + attach_confidence 단수키 패치
8e9ed23 docs(eod): 2026-05-19 EOD — 24 PR 머지 + Action Items 9/9 + Gate-2 진입
e83fda9 fix(be): box_size Pydantic validation (reviewer H-2)
eeae158 feat(fe): BindingPocketEditor + /binding-pocket 라우트 + useBindingPocket 훅
```

---

### 어제(2026-05-19) feat/* 브랜치 6개

#### feat/a01-sstr-site-directed-docking
| 항목 | 내용 |
|------|------|
| HEAD | `bd0c568` |
| 변경 파일 수 | 10개, +43,295 ins / -5 del |
| 주요 파일 | `data/somatostatin_receptor/binding_pocket_SSTR2.json`, `pipeline_local/scripts/extract_binding_pocket.py`, `pipeline_local/scripts/align_subtypes.py` |
| Action Item | **A-01** SSTR site-directed docking (PR #61) |

**최근 5 커밋**:
```
bd0c568 feat(selectivity): A-01 SSTR 결합 포켓 좌표 + 5종 정렬 + selectivity_runner 인터페이스
5f5f7af fix(docking): handle SSTR3 8XIR chain selection (#60)
91eaef8 fix(ci): flexpep_dock.py F821 — TYPE_CHECKING 패턴으로 forward reference 해소
a1eee1f feat(strategies): default strategy를 dual_b1_b2로 — BLOSUM은 평가만 (#59)
cb3731f feat(strategies): BLOSUM Phase 5 — 4 strategy A/B 실험 + 비교 보고서 (#58)
```

#### feat/a04-composite-scoring
| 항목 | 내용 |
|------|------|
| HEAD | `8d98861` |
| 변경 파일 수 | 7개, +2,477 ins |
| 주요 파일 | `pipeline_local/scoring/composite_scorer.py`, `pipeline_local/scripts/composite_scorer_cli.py`, `pipeline_local/tests/test_composite_scorer.py` |
| Action Item | **A-04** 복합 스코어링 체계 (PR #62) |

**최근 5 커밋**:
```
8d98861 feat(scoring): A-04 복합 스코어링 모듈 (composite_scorer + Tier S/A/B/C 분류)
5f5f7af fix(docking): handle SSTR3 8XIR chain selection (#60)
91eaef8 fix(ci): flexpep_dock.py F821 — TYPE_CHECKING 패턴으로 forward reference 해소
a1eee1f feat(strategies): default strategy를 dual_b1_b2로 — BLOSUM은 평가만 (#59)
cb3731f feat(strategies): BLOSUM Phase 5 — 4 strategy A/B 실험 + 비교 보고서 (#58)
```

#### feat/a05-sst14-reference-dg
| 항목 | 내용 |
|------|------|
| HEAD | `5f5f7af` (main과 동일) |
| 변경 파일 수 | 0 (A-05는 main direct push `8e7e1cc`로 처리) |
| 주요 파일 | A-05 작업은 main 브랜치에 `8e7e1cc`로 직접 push |
| Action Item | **A-05** SST14 reference dG n=10 (mean=553.857 REU, σ=4.024) |

**최근 커밋**: A-10 fix까지만 포함 (`5f5f7af`), A-05 커밋은 main에 직접 기록됨.

#### feat/a09-final-candidates-synthesis
| 항목 | 내용 |
|------|------|
| HEAD | `eaaba95` |
| 변경 파일 수 | 5개, +1,005 ins |
| 주요 파일 | `runs_local/final_candidates/synthesis_orders/PRST-001.md`, `PRST-002.md`, `PRST-003.md`, `PRST-004.md` |
| Action Item | **A-09** 최종 후보 4개 + 합성 의뢰서 (PR #63) |

**최근 5 커밋**:
```
eaaba95 feat(a09): 최종 후보 4개 도출 + 합성 의뢰서 작성 (Gate-2 진입 준비)
39b6e39 feat(p1-action-items): A-02/A-03 도구 wrapper + A-01 네거티브 디자인 잔기 + P1 통합 보고
6054ea9 feat(docking): A-06 DiffPepDock PoC + PyRosetta/Boltz 비교 평가
f89e6fb feat(scoring): A-04 복합 스코어링 모듈 (#62)
55ce2c2 feat(selectivity): A-01 SSTR 결합 포켓 좌표 + 5종 정렬 (#61)
```

#### feat/boltz-sstr2-sst14-complex (Task #38)
| 항목 | 내용 |
|------|------|
| HEAD | `600bb60` |
| 변경 파일 수 | 7개, +12,805 ins |
| 주요 파일 | `data/somatostatin_receptor/SSTR2_SST14_complex_boltz_3.pdb`, `pipeline_local/scripts/generate_sstr2_sst14_complex.py`, `pipeline_local/tests/test_generate_sstr2_sst14_complex.py` |
| Action Item | Task #38 Boltz-2 SSTR2-SST14 complex 생성 (PR #67) |

**최근 5 커밋**:
```
600bb60 feat(docking): Boltz-2로 SSTR2-SST14 complex 생성 (Task #38)
5d1e79b docs(pptx): Action Items 9건 audit — 회의 요구 vs 실행 결과 비교 (12 슬라이드) (#65)
11ec533 docs(pptx): SOD 2026-05-19 종합 발표 자료 16 슬라이드 + 보고서 2건 (#64)
8e7e1cc feat(scoring): A-05 SST14 reference dG n=10 FlexPepDock 도킹 + 통계
7b53dca feat(a09): 최종 후보 4개 도출 + 합성 의뢰서 작성 (Gate-2 진입 준비) (#63)
```

#### feat/p1-sprint-integration (**P2 sprint 통합 브랜치, main 미머지**)
| 항목 | 내용 |
|------|------|
| HEAD | `ffc55b0` |
| 변경 파일 수 | 15개, +2,877 ins / -5 del |
| 주요 파일 | `backend/routers/binding_pocket.py`, `frontend/src/components/binding_pocket/BindingPocketEditor.tsx`, `frontend/src/pages/StrategyRunnerPage.tsx`, `pipeline_local/scoring/composite_scorer.py` |
| Action Item | **P2 sprint** (binding-pocket-pepadmet) 통합 — BE CRUD + FE + ENDPOINT_CONFIDENCE 통합 |
| ⚠ 상태 | **main 미머지** — E2E CONDITIONAL PASS (BE 152/152, FE 99/99, pipeline 592/597) |

**최근 5 커밋**:
```
ffc55b0 feat(scoring): integrate P1 sprint wrapper enrichment
da19fe2 Revert "feat(docking): Boltz-2로 SSTR2-SST14 complex 생성 (Task #38)"
fc2d89e feat(docking): Boltz-2로 SSTR2-SST14 complex 생성 (Task #38)
4c868a6 feat(fe): BindingPocketEditor + /binding-pocket 라우트 + useBindingPocket 훅
5035e1a feat: add strategy runner selection flow
```

#### feat/user-selection-system-pr (Task #39)
| 항목 | 내용 |
|------|------|
| HEAD | `7bbe36c` |
| 변경 파일 수 | 5개, +882 ins / -1 del |
| 주요 파일 | `backend/routers/strategies.py`, `frontend/src/pages/StrategyRunnerPage.tsx`, `backend/tests/test_strategies_router.py` |
| Action Item | Task #39 Strategy Runner 취사선택 시스템 (PR #66) |

**최근 5 커밋**:
```
7bbe36c feat: add strategy runner selection flow
5d1e79b docs(pptx): Action Items 9건 audit...
11ec533 docs(pptx): SOD 2026-05-19 종합 발표 자료...
8e7e1cc feat(scoring): A-05 SST14 reference dG...
7b53dca feat(a09): 최종 후보 4개 도출...
```

---

### main 브랜치 (최근 5 커밋)
```
4d3583c feat(scoring): P1/P2 sprint 손실 복구 — ENDPOINT_CONFIDENCE 11개 + HEURISTIC 4개 + attach_confidence 단수키 패치
8e9ed23 docs(eod): 2026-05-19 EOD — 24 PR 머지 + Action Items 9/9 + Gate-2 진입
e83fda9 fix(be): box_size Pydantic validation (reviewer H-2)
eeae158 feat(fe): BindingPocketEditor + /binding-pocket 라우트 + useBindingPocket 훅
9bc4dd2 feat: add strategy runner selection flow (#66)
```

---

## 2. Worktree 4개 현황 (`.worktrees/`)

### ① selectivity-guard-20260520 (오늘 핫픽스)

| 항목 | 내용 |
|------|------|
| 경로 | `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/.worktrees/selectivity-guard-20260520` |
| 브랜치 | `chore/selectivity-guard-20260520` |
| HEAD | `f125e61` |
| 마지막 커밋 | `fix(selectivity): 정공 조치 D+B — silent estimation 차단 + SST_DATA_DIR env 경로` |
| git status | `D AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/data/somatostatin_receptor` |
| 책임 작업 | selectivity silent estimation 차단 + SST_DATA_DIR env 경로 정공 조치 |
| ⚠ 주의 | `data/somatostatin_receptor` 삭제(D) 상태 — 심링크→디렉토리 전환 작업 진행 중. **본 세션 절대 수정 금지** |

### ② feat-fe-about-migration

| 항목 | 내용 |
|------|------|
| 경로 | `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/.worktrees/feat-fe-about-migration` |
| 브랜치 | `feat/fe-about-migration` |
| HEAD | `2f677cd` |
| 마지막 커밋 | `feat(fe): migrate about page to OKLCH handoff design` |
| git status | clean |
| 책임 작업 | About 페이지 OKLCH 색상 디자인 마이그레이션 |

### ③ feat-fe-data-integration

| 항목 | 내용 |
|------|------|
| 경로 | `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/.worktrees/feat-fe-data-integration` |
| 브랜치 | `feat/fe-data-integration` |
| HEAD | `eb69d90` |
| 마지막 커밋 | `feat(fe): connect new dashboard pages to live BE data` |
| git status | clean |
| 책임 작업 | Dashboard 페이지 → 실 BE 데이터 연결 |

### ④ fe-cd-pages

| 항목 | 내용 |
|------|------|
| 경로 | `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/.worktrees/fe-cd-pages` |
| 브랜치 | `feat/fe-cd-pages` |
| HEAD | `a31188c` |
| 마지막 커밋 | `feat(fe): C Candidate Review + D Run Launcher 화면 포팅 (마이그레이션 Phase 5.3+5.4)` |
| git status | clean |
| 책임 작업 | Candidate Review + Run Launcher FE 화면 마이그레이션 |

> **참고**: 그 외 `/tmp/` + `_workspace/` + 외부 경로에 11개 추가 worktree 존재 (SST14-M_scr__p2, SST14-M_scr_c1~c3, SST14-M_scr_fe_ab_pages, SST14-M_scr_p0, /tmp/SST14-M_scr-p1, /tmp/SST14-p1-sprint-integration-codex, /tmp/SST14-user-selection-pr, /tmp/fix-pipelines, /tmp/resolve-pr35, /tmp/resolve-pr37). 이들은 `.worktrees/` 외부에 위치하므로 별도 세션 소유 추정.

---

## 3. chore/selectivity-guard-20260520 상세 (오늘 핫픽스)

### 변경 파일 (3개)
```
AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/selectivity.py   +40/-3
AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/state.py                 +12
AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/tests/test_selectivity_guard.py  +385 (신규)
```

### 핫픽스 내용
- **정공 조치 D** (SST_DATA_DIR 환경변수): `backend/state.py`에 `OUTER_REPO_ROOT` + `SST_DATA_DIR` 환경변수 주입 경로 신설
- **정공 조치 B** (silent estimation 차단): `selectivity.py` — receptor 로딩 실패 시 `random.gauss()` fallback 대신 명시적 에러/경고
- **테스트**: `test_selectivity_guard.py` 385줄 신규 (guard 동작 검증)

### ⚠ 본 세션이 절대 손대지 말아야 할 파일
- `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/routers/selectivity.py`
- `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/state.py`
- `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/tests/test_selectivity_guard.py`
- **worktree** `.worktrees/selectivity-guard-20260520/` 전체

---

## 4. 어제 SOD/EOD 23개 파일 한 줄 요약

| 파일 | 분류 | 한 줄 요약 |
|------|------|-----------|
| `sod-2026-05-19-action-items-plan.md` | meta | 9건 Action Items 분류 + 의존성 그래프 + 3-Phase 실행 계획 |
| `sod-2026-05-19-A01-sstr-site-directed.md` | A-01 | SSTR2 결합 포켓 좌표(center=-5.6,-28.6,52.2) + 5종 RMSD 2.77~3.13Å |
| `sod-2026-05-19-A02-halflife-tools-comparison.md` | A-02 | 혈청 반감기 7종 비교 + D-AA HIGH-BLOCKER 확정 (pepMSND/PlifePred2 검토) |
| `sod-2026-05-19-A02-followup-pepadmet-daa-test.md` | A-02 | D-AA SMILES 실 테스트 + pepADMET 403 원인 분석 follow-up |
| `sod-2026-05-19-A03-fab-admet-validation.md` | A-03 | "Fab-ADMET"=pepADMET 오기재 사용자 확정 + V-01 RESOLVED |
| `sod-2026-05-19-A04-composite-scoring.md` | A-04 | composite_scorer + Tier S/A/B/FAIL + WSS + Pareto front 구현 보고 |
| `sod-2026-05-19-A05-sst14-reference-dg.md` | A-05 | SST14 FlexPepDock n=10: mean=553.857 REU, σ=4.024 (KPI σ<5 충족) |
| `sod-2026-05-19-A06-diffdock-poc.md` | A-06 | DiffPepDock PoC — NOT_RECOMMENDED (SS bond 처리 불가, 친화도 점수 미출력) |
| `sod-2026-05-19-A07-gpu-infra-quote.md` | A-07 | H100 NVL×4 현황: GPU 2/3 유휴(93GB 여유), GPU 0/1 점유(PID 좀비 추정) |
| `sod-2026-05-19-A08-meeting-recovery.md` | A-08 | 회의록 PDF p.5 취소선 확인 — A-08 정식 삭제 항목, prompts 미생성 정상 |
| `sod-2026-05-19-A09-final-candidates-synthesis.md` | A-09 | PRST-001(Tier S, WSS=1.000, AGCKNIIWKTITSC) 외 3개 합성 의뢰서 |
| `sod-2026-05-19-strategy-ab-experiment.md` | meta | BLOSUM 5-Phase A/B 실험 전략 + dual_b1_b2 default 선택 결정 |
| `sod-2026-05-19-task38-boltz-complex.md` | Task #38 | Boltz-2 SSTR2-SST14 complex PDB 3개 생성 + metadata (PR #67) |
| `sod-2026-05-19-comprehensive-plan.md` | meta | 5/19 후반 추가 작업(PPTX, Task #38, #39, P1 통합) 우선순위 계획 |
| `eod-2026-05-19-orchestrator-session.md` | EOD | 24 PR 머지 + A-01~A-10 완료 + PRST-001~004 Gate-2 진입 선언 |
| `eod-2026-05-19-p2-binding-pocket-pepadmet.md` | EOD/P2 | P2 sprint 24분 완료 (BE 152/152, FE 99/99) — feat/p1-sprint-integration 미머지 |
| `eod-2026-05-19-selectivity-hotfix.md` | EOD/hotfix | 깨진 심링크(helloworld 절대경로) 진단 + cp hotfix + 재발 위험 경고 |
| `p1-action-items-execution-2026-05-19.md` | P1 | p1-action-items 팀 55/55 PASS — ENDPOINT_CONFIDENCE 16개 등록 |
| `p2-binding-pocket-pepmsnd-pepadmet-execution-2026-05-19.md` | P2 | P2 infra 실행 — ENDPOINT_CONFIDENCE 11개 + HEURISTIC 4개 복구 + 62/62 |
| `p2-e2e-validation-2026-05-19.md` | P2 | E2E CONDITIONAL PASS — 신규 회귀 0건, pre-existing 5건 잔존 |
| `p2-fe-review-2026-05-19.md` | P2 | BindingPocketEditor PASS (23/23 vitest, 0 tsc errors) |
| `p2-partial-review-2026-05-19.md` | P2 | 부분 리뷰 — false positive 2건 포함(RETRACTED), uvicorn 재기동 전 상태 |
| `p2-pepmsnd-pepadmet-retry-2026-05-19.md` | P2 | PepMSND(MIT) + pepADMET(GPL-3.0) 재접근 — 올바른 URL + 라이선스 확인 |

---

## 5. 본 세션 손대지 말 것 — 미커밋 변경 목록

현재 브랜치(`chore/fix-receptor-symlink-20260520`)의 `git status` 기준:

### M (Staged/Modified) — 다른 세션 작업 추정
```
 M AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/test_full_pipeline_20260402/sst14_agentic_mutdock/ot_SSTR1_9IK8.pdb
 M AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/test_full_pipeline_20260402/sst14_agentic_mutdock/ot_SSTR3_8XIR.pdb
 M AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/test_full_pipeline_20260402/sst14_agentic_mutdock/ot_SSTR4_7XMT.pdb
 M AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/test_full_pipeline_20260402/sst14_agentic_mutdock/ot_SSTR5_8ZBJ.pdb
```
> ⚠ 이 4개 PDB는 본 브랜치 이름(`fix-receptor-symlink`)과 관련된 파일이지만, **현재 스테이징/비스테이징 상태**이므로 본 세션에서 git add/commit 하지 않음.

### ?? (Untracked) — 손대지 말 것 분류

| 분류 | 경로 | 소유 추정 |
|------|------|----------|
| **다른 세션 산출물** | `_workspace/release/p2-*.md`, `_workspace/release/eod-2026-05-19-*.md` | P2 sprint 세션 |
| **다른 세션 산출물** | `_workspace/release/sod-2026-05-19-*.md`, `sod-2026-05-20-*.md` | orchestrator 세션 |
| **다른 세션 데이터** | `runs_local/` (전체) | BE 실험 세션 |
| **다른 세션 코드** | `pipeline_local/tests/test_p1_critical_fixes.py` | P1 sprint 세션 |
| **다른 세션 코드** | `pipeline_local/scripts/status_updater.py` | 미상 세션 |
| **인프라** | `scripts/codex/`, `scripts/cursor/`, `scripts/run_with_status.sh` | engineer-infra 세션 |
| **하네스** | `tools/harness-adaptation/cursor-cli/` | orchestrator 세션 |
| **데이터** | `docs/meet_log/`, `eliminated_sequences.csv` | 다른 세션 |
| **데이터** | `runs_local/diffdock_poc/`, `runs_local/sstr2_sst14_complex/` 등 | BE 실험 세션 |
| **OS 디렉토리** | `.codex/`, `.worktrees/` | 시스템 |
| **테스트** | `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/tests/agents/` | 다른 세션 |

---

## 6. P1/P2 Sprint 정의 추출

### P1 Sprint

| 항목 | 내용 |
|------|------|
| **팀명** | `p1-action-items` |
| **팀원** | be-a04, be-a01-cif, infra, reviewer-pharma (4명) |
| **범위** | A-02/A-03 도구 wrapper 신설 + ENDPOINT_CONFIDENCE 등록 |
| **신규 파일** | `predict_halflife_pepmsnd.py`, `predict_admet_pepadmet.py`, `sequence_to_smiles.py` |
| **테스트** | 55/55 PASS (기존 39 + 신규 16 `TestEndpointConfidenceExternalTools`) |
| **ENDPOINT_CONFIDENCE** | 16건 신규 (halflife 7종 + admet 4종 + HEURISTIC 4종 + UNKNOWN 1종) |
| **브랜치 전략** | main에 직접 push (커밋 `39b6e39`) |
| **산출물** | `_workspace/release/p1-action-items-execution-2026-05-19.md` |
| **결론** | D-AA HIGH-BLOCKER 확정, pepADMET HTTP 403 = 인프라 문제 (등급 ≠ 상태) |

### P2 Sprint

| 항목 | 내용 |
|------|------|
| **팀명** | `binding-pocket-pepadmet` (lead session 80814a02) |
| **팀원** | be-binding-api, fe-binding-ui, researcher, infra, reviewer (5명) |
| **시간** | 2026-05-19 12:14~12:38 KST (~24분) |
| **범위** | BE binding_pocket CRUD API + FE BindingPocketEditor + researcher pepADMET/PepMSND 재시도 + infra ENDPOINT_CONFIDENCE 11개 통합 + E2E 검증 |
| **브랜치** | `feat/p1-sprint-integration` — **main 미머지** |
| **커밋** | `402e526` BE, `49db836` box_size fix, `4c868a6` FE, `ffc55b0` wrapper 통합 |
| **테스트** | BE 152/152, FE 99/99, pipeline 592/597 (5 pre-existing), CONDITIONAL PASS |
| **주요 차단** | researcher pepADMET/PepMSND URL 정정 대기로 Step 2/3/5 pending 상태로 EOD |
| **P1 손실 복구** | `4d3583c` (main에 별도 push) — ENDPOINT_CONFIDENCE 11개 + HEURISTIC 4개 |
| **산출물 5종** | `p2-e2e-validation`, `p2-fe-review`, `p2-partial-review`, `p2-pepmsnd-pepadmet-retry`, `p2-binding-pocket-pepmsnd-pepadmet-execution` |

### P1 vs P2 구분 요약

| | P1 Sprint | P2 Sprint |
|--|-----------|-----------|
| 팀 | p1-action-items | binding-pocket-pepadmet |
| 핵심 | 도구 wrapper + ENDPOINT_CONFIDENCE 등록 | binding_pocket CRUD + FE + E2E 검증 |
| 브랜치 | main direct push (`39b6e39`) | `feat/p1-sprint-integration` (미머지) |
| 상태 | ✅ 완료 머지 | ⏳ **main 미머지** (CONDITIONAL PASS) |

---

## 7. 추적 시 주의사항 (다음 작업자용)

### 🔴 CRITICAL — 즉시 주의

1. **`feat/p1-sprint-integration` 미머지**: P2 sprint 전체 작업(binding_pocket CRUD + FE + ENDPOINT_CONFIDENCE 통합)이 main에 미머지. 다음 세션이 PR을 생성하고 머지해야 Gate-2 공식 완성.

2. **`chore/selectivity-guard-20260520` 핫픽스 진행 중**: `.worktrees/selectivity-guard-20260520`에서 `data/somatostatin_receptor` D(deleted) 상태. 이 worktree 또는 해당 파일에 **절대 손대지 말 것**. 핫픽스 세션이 완료 후 PR 머지 예정.

3. **심링크 재발 위험 미해결**: `ai4sci-kaeri/data/somatostatin_receptor`가 `helloworld` 절대경로 심링크로 자동 복원되는 현상 관측됨(출처 미확인). `sod-2026-05-20-selectivity-followup.md`에서 오늘 추적 예정이나 미해결.

### 🟡 MEDIUM — 머지 전 확인 필요

4. **P2 sprint E2E pre-existing 5건**: `SSTR4 서명 4건 + PDB/CIF 좌표 1건` — 이번 스프린트 범위 외이나 주요 테스트 결과에 영향. 별도 추적 필요.

5. **`feat/p1-sprint-integration`의 Revert 커밋 주의**: `da19fe2 Revert "feat(docking): Boltz-2..."` — Boltz 관련 작업이 revert 후 `ffc55b0`에서 재통합됨. 충돌 가능성 확인 필요.

6. **pepADMET HTTP 403**: REST API 자동화 접근이 차단됨. `predict_admet_pepadmet.py`의 pepADMET 채널은 infra 미해결 상태. 실 사용 전 서버 측 인증 방식 확인 필요.

### 🟢 LOW — 배경 정보

7. **`feat/a05-sst14-reference-dg`는 사실상 main과 동일**: A-05 작업은 main에 직접 push(`8e7e1cc`)되어 이 브랜치는 A-10 fix까지만 포함. PR이 없이 닫힌 것으로 보임.

8. **GPU 0/1 좀비 프로세스**: A-07 보고서 기준 GPU 0/1에 ~87GB씩 점유하는 PID가 ps 목록에 없음. 컨테이너/네임스페이스 내부 프로세스로 추정. A-07 권고: 사용자 결정 필요.

9. **tmux 28개 세션 존재**: 어제 기준. 현재 attached 세션 #28. 다수 세션이 동시 작업 중이므로 `git pull` 전 충돌 확인 권장.

10. **가장 리스크 높은 브랜치**: `feat/p1-sprint-integration` (P2 sprint 미머지) + `chore/selectivity-guard-20260520` (핫픽스 진행 중) 두 브랜치가 오늘 기준 가장 주의 필요.

---

*작성 완료: 2026-05-20 오후 — tracker (read-only 정찰, 코드 변경 없음)*
