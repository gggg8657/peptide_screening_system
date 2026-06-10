# EOD 2026-05-20 — Selectivity Validation Session (orchestrator)

> **세션 유형**: Claude Code orchestrator (Opus 4.7) + 8 명 위임 팀 (`selectivity-validation-20260520`)
> **세션 시간**: ~06:30–07:10 UTC (실 진행 ~6 시간 + 위임 병렬)

---

## 0. 본 세션의 역할 (Session Identity)

본 세션은 **selectivity 종단 검증 + ADMET 신뢰성 위기 대응**을 맡은 orchestrator 세션이었다. 시작 trigger 는 사용자의 한 줄 보고: *"셀렉티비티 지금 다른 세션에서 돌리고 있는 UI BE/FE 에서 돌리는데, 이거 제대로 안 돌거든? 무슨일인지 확인해라."*

본 세션은 직접 코드를 작성하기보다 — 위임·종합·의사결정 입력 정리·사용자 결정 받기 — 4가지를 반복 사이클로 수행했다. 본 세션의 1차 산출물은 **머지된 PR 4건**, 2차 산출물은 **PRST-001~004 ADMET 신뢰도 평가 결과**, 3차 산출물은 본 EOD 이다.

### 본 세션이 한 일 (요약)
1. selectivity가 estimation 난수 모드로만 도는 진짜 원인 추적 → **git index 의 mode 120000 helloworld 심볼릭 링크가 모든 worktree 에서 receptor 디렉토리를 깨뜨리고 있었음** 발견
2. silent fallback 가드 + env 기반 경로 추가
3. FE↔BE candidate_id 포맷 불일치(G-1)·margin 부호 컨벤션 불일치(G-2) 발견·fix
4. codex 가 추진한 PRST ADMET 재검증을 받아 reviewer-pharma + reviewer-biology 평가로 OOD 외삽 결론 도출
5. Gate-2 합성 발주 운영 결정 (외주 안 함, 리스트만 보존, pepADMET 재훈련 별도 트랙) 받음
6. 본 EOD 작성 + 잔여 위임 추적

### 본 세션이 안 한 일 (다른 세션 영역)
- 다른 세션이 main 에 직접 push 한 8 PR (#68/#72/#73/#74/#78/#79/#81/#83) — 참조만, 수정 0
- session 13 (Cursor Composer) 의 동일 브랜치 18 files 편집 — 캡처 후 미관여
- A-02 D-AA tools / A-06 VRAM PoC SOD — 다른 세션 SOD, 본 세션 좌표만
- 실제 합성 외주, 실 in vitro hemolysis assay 발주 — 사용자 결정 사항

---

## 1. 본 세션 머지 PR 4건

| PR | merge commit | 내용 | 라운드 |
|---|---|---|---|
| **#69** | `fdf2769` | git index mode 120000 helloworld 심볼릭 링크 → 실 디렉토리 (13M, 22 파일) | 1 |
| **#70** | `e6dc7de` | D+B 가드 (silent estimation_fallback warning + `SST_DATA_DIR` env) | tester 1차 APPROVE, 155/155 PASS |
| **#71** | `45357aa` | G-1 candidate_id format fix (FE `iter04_cand004` ↔ BE 인덱스) | tester 1차 APPROVE, 162/162 PASS |
| **#82** | `a2139a3` | G-2 margin sign convention — yaml SSOT 양수 컨벤션으로 step05b/qc_ranker/orchestrator/live/demo 단방향 정렬 | tester 3 라운드 self-discovery (C-1~C-4, K-1~K-2, Medium 8건) → 최종 APPROVE 32/32 PASS |

**라운드 패턴**: PR #70/#71 은 1라운드 APPROVE, PR #82 는 3라운드 (Critical 6 + Medium 8 단계적 발견·해결). PR #82 의 patterned self-discovery 가 가장 가치 있었음 — `qc_ranker.py` 누락 (테스트 커버리지 0) 같은 critical 을 정상 검출.

---

## 2. 5 단계 진단 → 5 가지 fix

| 단계 | 진단 결과 | 처치 |
|---|---|---|
| 1 (어제 EOD) | BE 가 receptor 0/5 인식, estimation 난수 모드, 사용자에게는 `gate_pass=true` 만 보임 | hot fix: `cp -r data/somatostatin_receptor` (수동 복구) |
| 2 (오늘) | hot fix 직후 깨진 심링크 자동 복원 → **git index 의 mode 120000 심볼릭 링크가 범인** (infra 분석) | PR #69 — 실 디렉토리 commit |
| 3 | hot fix 가 깨지면 silent 하게 estimation 으로 떨어지는 UX 함정 | PR #70 — D+B 가드, `loaded==0` 로그·`estimation_fallback` warning 필드 |
| 4 | `mode=production` 으로 찍혀도 candidate_id 포맷 불일치로 candidate-level estimation fallback (FE `iter04_cand004` vs BE `004`) | PR #71 — `_build_pdb_index` 에 `iter*_cand*` 키 추가 |
| 5 | step05b margin 부호 (`sstr2 - worst_ot`, gate ≤ −2.0) 와 router/yaml (`worst_ot - sstr2`, gate ≥ 10.0) 가 같은 물리량의 반대 부호 — selectivity gate 신뢰성 위기 | PR #82 — yaml SSOT 양수 컨벤션으로 step05b/qc_ranker/orchestrator/live/demo 통일 |

---

## 3. 발견 — **PRST-001~004 ADMET 신뢰성 위기 (가장 큰 발견)**

### 사건 흐름
- codex(다른 세션)가 04:15 V-03 pepADMET 재검증 후 의뢰서 4건 ADMET=1.00 갱신
- 본 세션이 reviewer-pharma + reviewer-biology 평가 요청 → 둘 다 OOD 외삽 결론 일치

### 핵심 근거 — pharma + bio 합의

| 가설 | 결론 |
|---|---|
| `binary_toxicity=1.0` 신뢰성 | pepADMET Toxicity.csv 135 row 에 cyclic 14aa SS-bond 학습 데이터 **0건** (구조적 OOD) |
| **Octreotide 교차검증** | FDA 승인 안전 의약품 Sandostatin 도 동일 `binary_toxicity=1.0, hemostasis, Na_inhibitor` — 체계적 오분류 입증 |
| hemostasis 메커니즘 | **SST-14 의 치료 기전** (혈소판 응집 강화, 위장관 출혈 치료 PMID 598562 등). 독성 아님 |
| Na_inhibitor 메커니즘 | µ-Conotoxin 구조 요건 미충족 (14aa SS×1, ICK 없음, Trp8 ≠ pore-blocking Arg) — 위양성 가능성 높음 |
| hc50 (-38~-45) | 학습 범위 (+0.8~+2.6, 양수 log₁₀ μM 추정) 외 음수 — INVALID, 추론 스크립트 역정규화 없음 |
| confidence=1.0 | sigmoid saturation + softmax concentration — OOD 입력에서 raw output 폭주, 4 후보 모두 동일 = **변이 구별력 0** |
| 의뢰서 0.10~0.25 진위 | composite_scorer wrapper 실패 시 fallback 입력값 전파 — 실측 아님 |

### 운영 결정 (사용자)
- **Gate-2 합성 발주 안 함** (실 외주 안 함, `runs_local/final_candidates/synthesis_orders/PRST-00{1..4}.md` 리스트만 보존)
- **pepADMET 재훈련 + 재평가** 별도 트랙 시작 (plan 단계)
- 보완 PR (cyclic SS-bond guard + fallback WARN) 즉시 진행 (backend 위임 중)

---

## 4. 다른 세션 활동 좌표

본 세션 진행 중 다른 세션이 main 에 8 PR 추가 머지:

| PR | merged | 내용 | 영향 |
|---|---|---|---|
| #68 | 01:57 | P1 sprint wrapper × composite_scorer 자동 enrichment 통합 | ENDPOINT_CONFIDENCE/HEURISTIC 등록 — 본 세션 P0 으로 권고됐던 "P1/P2 sprint 4파일 복구" 가 이미 처리됨 발견 |
| #72 | 01:55 | SSTR4 VILRYAKMKTA 시그니처 충돌 제거 | be-fe-trace G-3 일부 자동 해결 |
| #73 | 01:56 | docs(action-items) STATUS §6 4파일 갱신 | research grounding 입력 |
| #74 | 02:29 | ENDPOINT_CONFIDENCE webmetabase + HLE regression (A-02 후속) | A-02 진행 |
| #78 | 02:10 | PPTX update (#68/#71/#72/#73 반영) | docs |
| #79 | 02:11 | A-05 Rosetta gate threshold align (498.4713 REU) | `pipeline_local/` 만 fix, **AG_src 의 `-5.0 kcal/mol` 잔존** — research 트랙 3 가치 |
| #81 | 02:14 | SSTR4 수정 후 PRST-001~004 재산정 (Tier/WSS 변동 없음) | 의뢰서 4건 갱신 + PPTX |
| #83 | 02:21 | FE 대시보드 라이브 데이터 훅 통합 + SelectivityExplorer 타입 정합성 | FE 통합 |

**충돌 회피**:
- 세션 13 (Cursor Composer, 동일 브랜치 18 files edited, Q&A 모드): PR #69 머지로 origin 브랜치 삭제, 미관여 그대로 둠
- 세션 23 pane1 (be-binding-api, cherry-pick 진행 중): main divergence 가능성 모니터, 미관여
- 본 세션의 local main 의 다른 세션 commit `4d3583c` (P1/P2 sprint 손실 복구): cherry-pick 시도 → 빈 commit 확인 (PR #68 에 이미 포함) → branch 정리

---

## 5. 진행 중 위임 4 트랙 (다음 세션 인계)

| Task | Owner | 상태 | 인계 |
|---|---|---|---|
| #3 `rosetta_ddg_max` AG_src 단위 혼재 조사 | research | 🟡 진행 | PR #79 가 `pipeline_local` 만 fix. AG_src 의 `-5.0 kcal/mol` 잔존. caller 매트릭스 + 통일 권고 |
| #4 PRST-001~004 변이 도킹 진단 | dock | 🟡 진행 | PR #81 가 PRST 재산정했으나 selectivity production 검증 0. mutdock pipeline 실행 가능성 + 예상 시간·GPU |
| #11 보완 PR — guards SS-bond + composite_scorer fallback WARN + ensemble/layer1 통합 | backend | 🟡 진행 | 새 worktree `pepadmet-guards-20260520`. tester 리뷰 → 머지 결정 |
| #12 pepADMET 재훈련 plan SOD | research | 🟡 진행 | `sod-2026-05-20-pepadmet-retrain-plan.md` 신규. 학습 데이터 큐레이션 + 재훈련 전략 비교 + 메트릭 + 일정 |

---

## 6. 잔여 / 다음 세션 SOD 후보

| 후보 | 출처 | 우선도 |
|---|---|---|
| pipeline_local · vLLM · UI 점검 v1.2~ (P1-2 vLLM 스모크, P1-3 자동 테스트, P2 UX) | 사용자 IDE 열린 `docs/pipeline_local_vllm_ui_inspection_plan.md` | 미정 |
| pepADMET 재훈련 실행 (Task #12 plan 검토 후 실 재훈련) | 본 세션 결정 | High (시간 큼) |
| In vitro RBC hemolysis assay 발주 (외부 외주 또는 내부 lab 결정) | pharma+bio 권고 | 사용자 결정 보류 |
| `pipeline_local/scoring/ensemble_router.py` / `layer1_ensemble.py` 정착 (현재 untracked) | codex 산출 추정, backend Task #11 에 흡수 시도 중 | Med |
| AG_src 의 `rosetta_ddg_max` 단위 (`-5.0 kcal/mol`) 통일 (research Task #3 결과 받고) | research Task #3 | Med |
| qc_ranker.py `datetime.utcnow()` DeprecationWarning | tester PR #82 리뷰 §부수 발견 | Low |
| 세션 13 Cursor Composer 동일 브랜치 18 files 상태 정리 | ext-tmux | Low (PR 머지 후 자체 수렴 가능) |
| Boltz complex로 PRST-001 ΔG 재산출 (어제 V-A09-06 부분 해소) | 어제 EOD orchestrator §12 #3 | Low |

---

## 7. 본 세션 위임 통계

**팀 이름**: `selectivity-validation-20260520`
**총 위임 인원**: 9 명 (infra, backend, dock, tester, research, ext-tmux, be-fe-trace, pharma, bio)
**총 Task**: 12 (1+2+3+4+5+6+7+8+9+10+11+12 — 일부 backend 동시 처리)
**자가 발견 라운드 수 (PR #82)**: 3
**다른 세션 commit 위에 cherry-pick 시도**: 1 회 (4d3583c — 빈 commit, 폐기)
**처음 발견 후 즉시 표면화한 결함**: 6 (helloworld 심링크, silent estimation, cid mismatch, margin 부호, qc_ranker 누락, ADMET=1.00 OOD)

---

## 8. 한 줄 자평

본 세션은 "selectivity 가 안 돈다" 한 줄에서 출발해 (1) BE↔FE↔config 의 5단 결함을 PR 4건으로 단방향 정렬했고, (2) Gate-2 후보의 ADMET 점수가 실측이 아니라 fallback 가짜 입력이었음을 외부 (codex) 발견 위에서 reviewer-pharma·biology 평가로 OOD 외삽 결론까지 끌어올렸다. 다음 세션은 본 세션의 잔여 4 트랙 (research × 2, dock, backend 보완 PR) 결과를 받아 pepADMET 재훈련 실행 또는 vLLM/UI 점검으로 이어간다.

---

## 변경 이력

| 시각 | 사건 |
|---|---|
| 어제 EOD | selectivity hot fix (수동 cp -r) |
| 오늘 06:32 | infra 범인 확정 (git index mode 120000) |
| 06:38 | PR #69 머지 (`fdf2769`) |
| 06:45 | PR #70 머지 (`e6dc7de`) |
| 06:55 | PR #71 머지 (`45357aa`) |
| 07:00 ~ 07:05 | be-fe-trace + research + ext-tmux grounding 도착 |
| 07:00+ | codex 04:15 PRST ADMET 재검증 작업 발견 |
| 08:45 | PR #82 머지 (`a2139a3`) |
| 09:07 | pharma OOD 결론 도착 |
| 09:08 | bio 메커니즘 결론 도착 (pharma 와 일치) |
| 09:10 | 사용자 결정: 합성 발주 안 함 + pepADMET 재훈련 |
| 09:15 | 보완 PR (backend) + retrain plan SOD (research) 위임 |
| 09:20 | 본 EOD 작성 |

(시각은 UTC 기준 본 세션 진행 시점, ±5min 추정)
