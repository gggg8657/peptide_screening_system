# /goal 프롬프트 v3 — SST14-M_scr 액션 아이템 완전 해소

> 사용처: `/goal` 명령 또는 자동 진행 trajectory 의 입력.
> 작성일: 2026-05-21, 작성: orchestrator (Claude Opus 4.7).
> v1 → v2 변경: 사용자 정책 결정 (A1·B2·C2·D1·E1·F1·G2·H1·I1·J1) 반영.
> v2 → v3 변경: A5 재훈련 분해 (pepADMET 재훈련 vs 자체 모델 분기) + sanity abort + GPU 양보 정책.

---

```
# 목표

`/home/dongjukim/Documents/workspace/repos/SST14-M_scr` 의 모든 미해결 액션 아이템을 다른 세션 충돌 없이 해소. 본 세션 역할 = orchestrator (위임·종합·머지 결정·EOD 정리).

# 철칙 (절대 위반 금지)

1. **외부 연락·메일·API 신청 절대 금지** (A1) — NIM API key, pepADMET 저자 contact (V-07), 외주 발주, 임의 외부 메일 전부 미관여
2. **wet-lab assay 발주 미관여** (D1) — in vitro RBC hemolysis 등 사용자 외주 결정. 본 세션은 문서·plan 만
3. **다른 세션 worktree 18개 영역 절대 회피** (E1) — `.worktrees/{daa-smiles-v2, fe-cd-pages, fe-jobs-status-v2, fe-llm-ux, fe-stub-badge, fe-warning-banner, feat-fe-about-migration, feat-fe-data-integration, flexpep-timeout, llm-vllm-upgrade, molstar-fix, orphan-cleanup, planner-prompt, pr85-rebase, silo-a-v2, worker-pool}` 변경·머지·삭제 금지
4. **다른 세션 미해결 task 3건 미관여**: V3-A pepMSND D-AA SMILES, V3-B Silo A 라우터, V4-C FE jobs status 색상
5. **합성 실 발주 안 함** (I1) — PRST-001~004 의뢰서 리스트만 유지. 실 외주 X
6. **회의·일정·조직 결정 미관여** (J1) — 5월 회의 일자, NIM API key, RI팀 협의 사용자만
7. **main 직접 push 금지** — 모든 변경은 PR
8. **시작 전 `git fetch origin`** + `git log origin/main..` 로 main 진화 확인 의무
9. **worktree base = `origin/main` 명시** (local main 의 다른 세션 commit 포함 위험)

# 사용 가능 도구 (작업 분담 가이드, C2)

| 도구 | 강점 | 적합 작업 |
|---|---|---|
| Claude orchestrator (본 세션) | 종합·의사결정·EOD | Group 전환·머지 결정·사용자 confirm |
| Claude 내장 서브에이전트 (Agent tool) | engineer-backend, reviewer-code, researcher, reviewer-pharma, reviewer-biology | 복잡 구현·과학 검증·병렬 독립 작업 |
| `/codex` (`./scripts/agent-wrapper.sh codex`) | 단일 파일 명확 스펙·테스트 생성·lint fix·반복 코드 수정 | Group A.A1, Group C 단순 fix, 테스트 자동 작성 |
| `/cursor-agent` (`./scripts/agent-wrapper.sh cursor-agent`) | EOD/SOD·코드 분석·문서 작성·일정 | research SOD, GPL 문서, 보고서 정리 |

**위임 패턴 (CLAUDE.md 의 6 패턴)**:
- Producer-Reviewer: backend(생성) ↔ tester(검증) — PR #82 패턴 그대로
- Pipeline: research(진단) → backend/codex(PR) → tester(리뷰) → 머지
- Fan-out/Fan-in: 독립 작업은 단일 PR 로 묶음 (변경 영역 분리 시)
- Expert Pool: 코드 fix=codex, 분석·EOD=cursor-agent, 종합=Claude

# 컨텍스트 파일 (먼저 읽기)

- `_workspace/release/eod-2026-05-20-selectivity-validation.md` — 본 세션 어제 EOD
- `_workspace/release/sod-2026-05-21-residual-tracks-collection.md` — 본 세션 오늘 SOD
- `_workspace/55_reviewer-pharma_prst-admet-ood-analysis.md` — PRST ADMET OOD 결론
- `_workspace/55_reviewer-biology_PRST-toxicity-pepadmet-bio-eval.md` — 생물학 평가
- `_workspace/pepadmet_local/PRST-candidates_revalidation_2026-05-20.md` — V-03 재검증
- `CLAUDE.md` — 위임 의사결정 트리

# 액션 아이템 — Group A~E

## Group A — 어제 위임 마무리 + pepADMET 재훈련 실 실행 (P0)

| ID | 작업 | 추천 도구 | 산출 |
|---|---|---|---|
| A1 | AG_src `gate_thresholds.yaml::rosetta_ddg_max` (-5.0 kcal/mol) → pipeline_local 정본 (498.4713 REU) 통일 + AG_src `orchestrator.py:1211/1266/1524`, `step06_rosetta.py:190/910` 폴백 5곳 갱신 | research(Claude) 진단 → codex (단일 파일 fix) → tester 리뷰 | PR 머지 |
| A2 | 보완 PR (`pharmacology_guards` SS-bond + `composite_scorer` fallback WARN + `ensemble_router/layer1_ensemble` 통합) | backend(Claude) → tester | PR 머지 |
| A3 | pepADMET 재훈련 plan SOD 작성 | research(Claude) 또는 cursor-agent | `sod-2026-05-21-pepadmet-retrain-plan.md` |
| A4 | PRST 변이 도킹 진단 (mutdock pipeline 가용성·예상 시간·GPU 자원) | dock(Claude) | plan 보고 |
| **A5** | **모델 학습 트랙** (B2) — A5-0 진단 분기. **단순 재실행 금지** (데이터·OOD detection 없으면 무의미). 세부 A5-0~A5e 참고 | 분기별 다름 | 학습된 모델 + sanity 통과 + PR |

### Group A.A5 세부 분해 (단순 재실행 방지)

**A5-0: pepADMET 재훈련 가용성 진단** (Pipeline 시작점)
- `_workspace/pepadmet_local/pepADMET/` 안에 학습 코드 (train.py, model.py, dataloader 등) 가용 여부
- 학습 데이터 (`Toxicity.csv` + 그 외 task csv) 라이센스·재현 가능성
- 의존성 (PyTorch, RDKit, PyG 등) 환경 점검
- 추정 학습 시간·GPU 메모리·체크포인트 크기
- → 가용 시 **분기 P (pepADMET 재훈련)**, 불가 시 **분기 Q (자체 모델 신규 학습)**

#### 분기 P — pepADMET 재훈련 (A5-0 가용 시)

| ID | 작업 | abort 조건 |
|---|---|---|
| A5Pa | 학습 데이터 큐레이션 — 외부 DB (DBAASP/APD3/HemoPI, H1) + FDA 승인 cyclic peptide 의약품 안전 라벨 (Octreotide/Lanreotide/Pasireotide/Vasopressin/Oxytocin/Atosiban/Desmopressin) + SST family 안전 라벨. **최소 cyclic SS-bond 30 안전 + 30 toxic 추가** | 큐레이션 < 50 row → abort, 사용자 보고 |
| A5Pb | OOD detection 메커니즘 추가 — confidence calibration (label smoothing, focal loss) + Mahalanobis distance 또는 MC dropout 으로 OOD 입력 차단 | 구현 막힘 → abort, 옵션 P fallback (Group A.A2 OOD 가드만) |
| A5Pc | 재훈련 (A5Pa 데이터 + A5Pb 통합) | 학습 발산 / NaN → abort |
| A5Pd | **Sanity check 의무 (즉시 abort 정책)**: (1) Octreotide → binary_toxicity < 0.5, (2) SST-14 native → < 0.5, (3) PRST-001~004 4 score 의 max-min ≥ 0.2 (변이 구별력) | sanity fail → 즉시 abort + 이전 모델 유지 + 사용자 보고 |
| A5Pe | 재훈련 모델 + Group A.A2 SS-bond 가드 통합 PR | tester 리뷰 통과 후 머지 |

#### 분기 Q — 자체 cyclic peptide hemolysis 모델 신규 학습 (A5-0 불가 시)

pepADMET 재훈련 불가능 시 fallback. 사용자 의향: "자체 모델 탐나네".

| ID | 작업 | abort 조건 |
|---|---|---|
| A5Qa | 데이터 큐레이션 — DBAASP cyclic disulfide peptide + APD3 + HemoPI hemolysis dataset + FDA 승인 cyclic 의약품 안전 라벨 + SST family. 양성/음성 균형 ≥1:1 | 큐레이션 < 100 row → abort, 옵션 P fallback |
| A5Qb | 모델 architecture 결정 — GNN (PyG GraphSAGE/GAT) 또는 ESM-2 임베딩 + MLP. cyclic SS-bond feature 명시 (atom-level + SS-bond edge) | 구현 막힘 → abort |
| A5Qc | OOD detection 내장 (분기 P 의 A5Pb 와 동일 메커니즘) | — |
| A5Qd | 학습 + 5-fold CV. 추정 ~수 시간 GPU | 5-fold AUC < 0.7 → abort, plan 복귀 |
| A5Qe | **Sanity check 의무 (즉시 abort 정책)**: 분기 P 의 A5Pd 와 동일 | sanity fail → 즉시 abort + 모델 폐기 + 사용자 보고 |
| A5Qf | 신규 wrapper (`pipeline_local/scripts/predict_hemolysis_custom.py`) + `composite_scorer` 가 ensemble (pepADMET applicable=true 일 때 pepADMET, false 일 때 자체 모델) + PR | tester 리뷰 통과 후 머지 |

### A5 자원 정책 (사용자 결정)

- **GPU 한도 없음** — H100 NVL ×4 자유 사용. 큐레이션·학습·평가 자원 제한 X
- **다른 세션 충돌 시 양보** — `nvidia-smi` 로 다른 프로세스 GPU 사용 감지 시 학습 일시 정지·재시도 (~5분 polling). 30분 이상 대기 시 사용자 보고
- **CUDA_VISIBLE_DEVICES**: 기본 2번 (사용자 메모리), 다른 GPU 도 가용 시 사용

### A5 sanity check 실패 시 무한 재훈련 방지

- **즉시 abort + 사용자 보고** (사용자 명시 결정)
- 자동 hyperparameter 재시도 / 데이터 재큐레이션 재시도 안 함 (사용자 결정 후)
- 이전 모델 (= 현 pepADMET 또는 직전 안정 weights) 유지
- 실패 보고서: `_workspace/release/a5-retrain-abort-2026-05-21.md` (분기/단계/메트릭/추정 원인)

## Group B — be-fe-trace G-4~G-8 잔여 (P1, FE 페이지 회피)

| ID | 작업 | 추천 도구 | 회피 근거 |
|---|---|---|---|
| B1 | G-4 `useSelectivity.stopAnalysis()` 에 `POST /api/selectivity/cancel/{job_id}` 호출 추가 | codex (hook 한 함수) | hook 1 함수만, FE 페이지 무관 |
| B2 | G-5 `hooks/useSelectivity.ts::useSelectivity()` vs `hooks/dashboard.ts::useSelectivity(runId)` 동명 훅 → 한 쪽 rename | codex | hooks 영역만 |
| B3 | G-6 BE 엔드포인트 수 문서 정정 (8 vs 9 명세) | cursor-agent | docs only |
| B4 | G-8 mount 시 completed 잡 N 개 일괄 fetch retention 정책 | backend(Claude) | hook + BE |

G-7 `/selectivity` Nav 누락은 FE 페이지 변경 → 다른 세션 영역, 회피.

## Group C — 기술 부채 (P2)

| ID | 작업 | 추천 도구 |
|---|---|---|
| C1 | `AG_src/agents/qc_ranker.py:80` `datetime.utcnow()` → `datetime.now(timezone.utc)` (DeprecationWarning) | codex |
| C2 | `gate_thresholds.yaml` AG_src vs pipeline_local 잔여 정합 (`esmfold_plddt_min` 60↔50, `gates_enabled.disulfide` false↔true) | research 진단 → codex |
| C3 | 깨진 `.worktrees/` 식별 (`fe-cd-pages` 등 `helloworld` 심링크 잔존 여부 확인, **본 세션 삭제 X**, 사용자 권고만) | infra(Claude) |

## Group D — 4/6 회의 잔여 (본 세션 안전 영역만)

| ID | 작업 | 추천 도구 |
|---|---|---|
| D1 | A-05 코드 폴백 5곳 (Group A.A1 에 흡수) | — |
| D2 | A-03 V-04 GPL-3.0 라이센스 법무 검토 문서 (`_workspace/release/v04-gpl3-legal-review-2026-05-21.md`, 실 법무 결정은 사용자) | cursor-agent |

A-02 D-AA tools (`daa-smiles-v2` worktree), A-07 GPU 견적 (사용자 외부 책임), A-09 합성 발주 (I1 Hold) → 본 세션 미관여.

## Group E — plan 만 (D1·I1 정책)

| ID | 작업 | 산출 |
|---|---|---|
| E1 | In vitro RBC hemolysis assay 발주 절차 **plan** (외주·내부 lab 비교, SST-14 동시 측정 권고, 비용·일정 견적) | `_workspace/release/in-vitro-hemolysis-assay-plan-2026-05-21.md`. 실 발주는 사용자 |
| E2 | Boltz complex (PR #67 `c5c70e4`) 로 PRST-001 ΔG 재산출 **plan**. 실 실행은 사용자 confirm 후 | plan 문서. 실 실행 시 별도 PR |

# 작업 사이클

1. 새 worktree: `git worktree add .worktrees/<name>-20260521 -b chore/<name>-20260521 origin/main` (반드시 `origin/main`)
2. 변경 + 테스트 (영향 분석 의무 — PR #82 의 3 라운드 self-discovery 패턴)
3. `git push -u origin chore/<name>-20260521`
4. `gh pr create` (description 에 영향 분석 + 다른 세션 회피 확인 포함)
5. tester 리뷰 (Producer-Reviewer)
6. APPROVE → 머지 (Group 전환 시점에만 사용자 confirm, G2)
7. 다음 작업

# 사용자 confirm 시점 (G2 — 빠른 진행)

- **Group 전환 시점만** (A→B→C→D→E)
- Group 내 개별 PR 머지는 본 세션 판단 (tester APPROVE 받으면 진행)
- **예외**: 큰 결함 발견·다른 세션 충돌 우려·외부 영향 (binary 추가 등) 시 즉시 사용자 보고

# 종료 조건 (F1 — 시간 무제한)

- Group A, B, C, D, E 의 모든 항목 closure (PR 머지 또는 plan 도출)
- 최종 EOD `_workspace/release/eod-2026-05-21-action-items-closure.md`:
  - 머지된 PR 리스트
  - Group 별 closure 상태표
  - A5 재훈련 결과 (성공/실패, 메트릭, 다음 세션 인계)
  - 다음 세션 인계 사항 (Group E 실 실행 trigger 조건)
  - 본 세션 역할 자평
- Group A.A5 재훈련은 시간 큼 (수 시간 ~ 수일 GPU). 진행 도중 sanity check 실패 시 즉시 abort + 사용자 보고

# 운영 노트

- **신중하게**: 각 PR 영향 분석 의무. caller 매트릭스·테스트·문서 변경 포함
- **빠르게**: PR #82 의 3 라운드 self-discovery 패턴 유지
- **다른 세션 보호**: 충돌 발견 시 즉시 abort + 사용자 보고. 다른 세션 commit/worktree 절대 손대지 않음
- **메시지 누락 회피**: idle 노티 후 결과 메시지 안 오면 ping (어제 dock 사례 학습)
- **외부 DB (H1)**: DBAASP, APD3, HemoPI 등 cyclic SS-bond peptide 데이터 다운로드 허용. 단 외부 API 호출 (메일·인증·신청) X
- **외부 CLI 호출**: `./scripts/agent-wrapper.sh codex|cursor-agent` 또는 `./scripts/cursor/harness_invoke.sh`. 호출·결과는 `logs/external_agents/` 에 자동 기록됨
- **재훈련 자원**: GPU H100 NVL ×4 (CUDA_VISIBLE_DEVICES=2 설정, 다른 GPU 자유 사용 가능). 재훈련 중 다른 세션 작업과 GPU 충돌 모니터
```

---

## 부속 — v1 대비 변경 요약

| 변경 항목 | 결정 | v1 → v2 |
|---|---|---|
| 철칙 섹션 | A1·D1·E1·I1·J1 | 신설 (9 조항) |
| Group A.A5 추가 | B2 | E1 (재훈련 실 실행) → Group A 로 승격 |
| 외부 CLI 활용 가이드 | C2 | 신설 — codex/cursor-agent 강점·작업 분담 표 |
| 사용자 confirm 빈도 | G2 | "모든 PR" → "Group 전환만" |
| 시간 제한 | F1 | "사용자 결정 필요" → "무제한" |
| 외부 DB 다운로드 | H1 | "별도 명시 없음" → "DBAASP/APD3 등 허용" |
| Group E 처리 | D1·I1 | "사용자 결정 보류" → "in vitro/Boltz plan 만" |
| 의뢰서 정책 | I1 | "현재 결정 유지 (Hold)" 명시 |
| 회의·일정 | J1 | "본 세션 미관여" 명시 |

## 추정 작업 시간

| Group | 추정 |
|---|---|
| A1~A4 | ~3-4 시간 |
| **A5-0 진단** | ~30분 |
| **A5 분기 P (pepADMET 재훈련)** | 6 시간 ~ 2일 (큐레이션·재훈련·sanity) |
| **A5 분기 Q (자체 모델)** | 1-3일 (데이터 큐레이션·architecture·CV·sanity) |
| B1~B4 | ~2 시간 |
| C1~C3 | ~1 시간 |
| D2 | ~30분 |
| E1~E2 (plan) | ~1 시간 |
| EOD | ~30분 |

**총 추정**: A5 제외 ~7-8 시간. A5 포함 ~15-72 시간 (분기·sanity·재시도 여부에 따라).

## v3 의 핵심 안전 장치

1. **단순 재실행 금지** — A5-0 진단으로 가용성 확인 + 분기 P/Q 분리
2. **데이터·OOD detection 없이 재훈련 무의미** 명시 — A5Pa/A5Pb + A5Qa/A5Qb/A5Qc 의무
3. **Sanity check 의무 (Octreotide + SST-14 + PRST 구별력)** — 통과 못 하면 모델 무효
4. **즉시 abort 정책** — sanity fail 시 무한 재훈련 루프 차단, 사용자 보고
5. **자원 양보** — 다른 세션 GPU 사용 시 polling 양보, 30분+ 대기 시 사용자 보고
6. **분기 Q (자체 모델) 도 허용** — pepADMET 외부 의존 막히면 자체 학습으로 전환
