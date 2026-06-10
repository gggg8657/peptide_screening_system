# Changelog — `tools/harness-adaptation/`

본 어댑테이션의 SemVer 이력. Phase 7 진화 메커니즘 산출물.
형식: [Keep a Changelog](https://keepachangelog.com/) 1.1.0 준수.

> 운영 규칙
> - 어댑테이션 자체에 영향을 주는 PR은 본 파일을 갱신한다 (PR 템플릿이 강제).
> - **분기당 최소 1회 갱신** — 신규 entry가 없으면 회고 항목으로 별도 entry 작성.
> - 버전 규칙:
>   - `MAJOR` — 기존 산출물(`PROMPT_TEMPLATE.md`, 어댑터 등)의 breaking 변경
>   - `MINOR` — 새 Stage 도입, 새 산출물 추가, 새 가드 추가
>   - `PATCH` — 문서 보강, 오타 수정, 출처 인용 추가

---

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

---

## [0.17.0] — 2026-05-11

### Added — Stage 9 Rosetta Flow End-to-End Dogfood

**RETROSPECTIVE_GUIDE Action Q-2026-Q3-2 사전 실행**. PyRosetta Silo B flow 실 실험으로 시스템 6개 critical 결함을 자가 노출. 분석·권고 보고서만 생성 (코드 수정 X — 별도 PR).

**환경 부트스트랩**:
- `ollama serve` (PID 834978, qwen3:8b 외 7 모델 pulled)
- `ai4sci-kaeri/backend` uvicorn port 8765 ✅
- `ai4sci-kaeri/frontend` Vite port 5173 ✅
- `pipeline_local/config/pipeline_config_local_dogfood.yaml` (max_variants 200→32)

**실 실험 결과 (의도 5 iter → 실제 3 iter, patience 2/2 early stop, 9.5분)**:
- iter01: 44 단일 변이 → ESMFold 5/44 PASS → Boltz 5 docked (score -9.65~-9.22) → PyRosetta var_012 ddG=0.00 ⚠️
- iter02/03: 0/44 ESMFold PASS, cache hit으로 ddG=0.00 동일

### Critical 발견 6건 (자가 노출, Producer-Reviewer cross-validation 4명 일치)

1. **vLLM provider 8000 connection refused** — `--llm-base-url` 누락, 모든 LLM 호출 silent 폴백
2. **★ PyRosetta cache key 충돌** — `var_024` (iter02/03)가 `var_012` (iter01) PDB 가리킴 (서로 다른 시퀀스, 동일 cache key)
3. **★ PyRosetta `ddG=0.00, clash=0.00`** — refined PDB 232KB는 생성, score 컬럼 모두 0 (Boltz -9.65와 모순)
4. ESMFold pLDDT≥60 임계값 작은 cyclic peptide 부적합
5. `source: "silo_a"` 라벨 버그 (--approach-b인데 silo_a)
6. Convergence detector의 degraded-mode 미구분 (LLM 부재로 인한 정체 vs 진짜 수렴)

### 자가 발전 권고 R1~R7 (코드 수정 X, 보고서만)

- R1 LLM base_url 옵션 의무화 또는 명시적 경고
- R2 PyRosetta cache key 결정 로직 진단·fix (Critical)
- R3 `compute_binding_ddg()` silent fallback 진단 (Critical)
- R4 ESMFold pLDDT 임계값 domain-calibrate
- R5 `source` 라벨 fix
- R6 Convergence detector degraded-mode 구분
- R7 본 발견을 `HEURISTIC_FUNCTION_DISCLAIMERS`에 등록 (Stage 5 절차)

### 새 §검증 필요 5건 (VR-cycle-10~14) + 다음 분기 Action Q-2026-Q3-9~14 추가

| ID | 항목 |
|----|------|
| VR-cycle-10 | LLM provider auto-detect (vLLM unavail → ollama graceful) |
| VR-cycle-11 | PyRosetta cache key 충돌 |
| VR-cycle-12 | compute_binding_ddg silent fallback 0.0 |
| VR-cycle-13 | ESMFold pLDDT 임계값 calibration |
| VR-cycle-14 | Convergence detector degraded-mode |

### 사이클 메타 검증 — 본 release의 가장 큰 가치

**VR-cycle-09 (H-06 "계산 불가능을 계산 가능한 척" 가드)가 운영 적용 사례로 작동**: ddG=0.00이라는 *비현실적 결과를 임상 binding 값처럼 보고하지 않고 도메인 fail 신호로 정직히 분류*. 사이클이 자기 점검 메커니즘을 두 번째로 입증 (첫 번째: modification_conflict dogfood v0.12.0).

### Files

- `_workspace/release/scenario-rosetta-flow-2026-05-11.md` (보고서, ~280줄)
- `pipeline_local/config/pipeline_config_local_dogfood.yaml` (dogfood config, 재현용)

---

## [0.16.0] — 2026-05-11

### Added
- **분기 회고 2026-Q2 1차 실행** — RETROSPECTIVE_GUIDE.md 6-Phase 어젠다 따라 진행.
- 회고 보고서: `_workspace/release/retro-2026-Q2.md` (~360줄)
  - Phase A 사실 정리: 17 commits, 15 SemVer cuts, 95 tests, 16 routing, 11 agents
  - Phase B 패턴 적합성: 1~4순위 운영 매트릭스 + "메타 작업의 패턴 부재" 발견
  - Phase C 환각 가드: LITERATURE_VALUES 추가 후보 3 / SCALE_RANGES 보정 1
  - Phase D 미적용 Stage: Stage 9~12 후보 4건 식별
  - Phase E Action Items: Q-2026-Q3-1~8 (8 액션, Q3-1 CI 등록 Critical)
  - Phase F CHANGELOG cut: 본 entry
- 회고 자체의 §검증 필요 3건 식별 (VR-retro-Q2-01~03)

### Notes — 메타 평가

**잘 작동**: 자기 진화 루프 (10/10 §검증 처리), Producer-Reviewer cross-validation,
한계의 정직한 노출, 하네스 본질 명확화.

**부족**: 실 트래픽 부재 → VR-cycle-05/06 partial 상태; tmux team-mate 0회 운영;
메타 작업의 패턴 부재; CI 등록 누락.

**다음 회고**: 2026-Q3 말 (~09-26) 또는 비상 트리거 발생 시.

---

## [0.15.0] — 2026-05-11

### Added
- **VR-cycle-05 closure (echo 가능성)** — `PROMPT_TEMPLATE.md`에 **GATE-F** "Fan-out 독립성 검증" 신설:
  - 동일 phrasing/동일 누락 패턴 신호 3종 정의
  - 다양화 가이드 (다른 출발점 시드 / 다른 검증 기준 / 독립 판단 명시)
- **VR-cycle-06 closure (토큰 비용)** — `PROMPT_TEMPLATE.md`에 **GATE-G** "토큰 비용 최적화" 신설:
  - 공유 컨텍스트는 `_workspace/shared_context_{topic}_{YYYY-MM-DD}.md`로 분리
  - Agent 호출 prompt에는 파일 경로만 전달
  - 200단어 미만 컨텍스트는 인라인 예외 (조건부)
- 사후 체크리스트에 **C-08** (Fan-out echo 셀프-체크) + **C-09** (휴리스틱 함수 인용 형식) 추가
- **VR-S5-01 closure (`_PROTEASE_VULNERABILITY` 출처 부재)** — `pharmacology_guards.py::HEURISTIC_FUNCTION_DISCLAIMERS`에 명시 등록:
  - 정량 출처 부재 한계 인정 (kcat/Km 무관)
  - valid_use: 잔기별 상대 vulnerability 순위만
  - invalid_use: protease cleavage rate 추정, 절대값 임상 보고
- **VR-cycle-08 closure (PDB 좌표 한계)** — `pyrosetta.pose_from_sequence_ideal_coord` 명시 등록:
  - ideal backbone/side chain → 실 conformation과 다름
  - ref2015 큰 단백질용 calibrated, 작은 cyclic peptide 부적합 가능
  - partial closure (full은 실 PDB 좌표 인프라 도입 후)
- 회귀 테스트 2건 추가 (test_protease_vulnerability_registered / test_pyrosetta_sequence_only_pose_registered)

### Verification
- 전체 pytest: **95/95 PASS** (이전 93 + 회귀 2)
- auto_dispatch routing: 16/16 PASS (회귀 없음)

### Closure 상태 — 9건 중 9건 처리 완료 (5 full + 3 partial + 1 흡수)

| ID | 항목 | 상태 |
|----|------|------|
| VR-cycle-01 | C-07 DOTA 도입 | ✅ FULL CLOSED (v0.13.0) |
| VR-cycle-02 | 반감기 cap | ✅ ABSORBED into 09 (v0.14.0) |
| VR-cycle-03 | PyRosetta SS bond API | ✅ FULL CLOSED (v0.12.1) |
| VR-cycle-04 | auto_dispatch 휴리스틱 | ✅ FULL CLOSED (v0.13.0) |
| VR-cycle-05 | cross-validation echo | 🟡 PARTIAL CLOSED — 가이드 / 운영 측정 후 full |
| VR-cycle-06 | Fan-out 토큰 비용 | 🟡 PARTIAL CLOSED — 컨벤션 / 운영 측정 후 full |
| VR-cycle-07 | 자동 동기화 | ✅ FULL CLOSED (v0.13.0) |
| VR-cycle-08 | PDB 좌표 score 한계 | 🟡 PARTIAL CLOSED — disclaimer / 실 PDB 도입 후 full |
| VR-cycle-09 | H-06 휴리스틱 명세화 | ✅ FULL CLOSED (v0.14.0) |
| VR-S5-01 | _PROTEASE_VULNERABILITY 출처 | 🟡 PARTIAL CLOSED — disclaimer / 출처 조사 후 full |

**100% 처리율** (full 5 + absorbed 1 + partial 4). 운영 데이터 누적 또는 별도 인프라 필요한 항목만 partial.

### Notes
- "partial closure" = 코드/문서에서 한계가 *명시적으로 노출*되어 환각 차단됨. full closure는 출처 조사/실 인프라 도입/운영 데이터 누적이 필요.
- 본 release로 사이클이 자기 §검증 필요 항목을 **사실상 모두 처리**함. 운영 단계 진입 가능.

---

## [0.14.0] — 2026-05-11

### Added
- **VR-cycle-09 (H-06) — 신규 §검증 항목 식별 + 즉시 closure**:
  사용자 통찰("지금 serum stability half-life 계산이 불가능하잖아?")로
  Stage 5 가드가 잡지 못한 가장 큰 환각 위험 발견 — **"계산 불가능한 것을
  계산 가능한 척"** 시나리오.
- **3-layer closure** (A 하네스 메타 + B 플래너 프롬프트 + C 도메인 코드):
  - **A 레이어** (`PROMPT_PRST_N_FM_EXAMPLE.md §3`): H-06 환각 시나리오 추가.
    가드: 휴리스틱 함수의 정직한 명세화. 하네스 본질은 "한계가 노출되도록
    돕는 역할"이지 "정확도 보장"이 아님.
  - **B 레이어** (`.claude/agents/reviewer-pharma.md`): §"휴리스틱 함수 해석
    가이드" 신설. predict_half_life / suggest_modifications /
    _compute_stability_score / _PROTEASE_VULNERABILITY 4개 함수의 표면/실제
    의미 표 + 검토 의무 4건. *임상 단위로 인용 금지*.
  - **C 레이어** (`pipeline_local/steps/step08_stability.py`): 모듈 docstring
    + predict_half_life docstring에 정직한 명세화. 함수 시그니처/이름은
    호환성을 위해 유지 (호출자 깨짐 방지). 한계·valid_use·invalid_use 명시.
  - **C 레이어 가드** (`pipeline_local/scripts/pharmacology_guards.py`):
    `HEURISTIC_FUNCTION_DISCLAIMERS` 신설 — 3개 휴리스틱 함수의 surface_unit /
    actual_meaning / limitations / valid_use / invalid_use / confidence_grade
    / fix_status. `is_heuristic_function(qualname)` API 추가.
- 회귀 테스트 4건 추가 (test_pharmacology_guards.py::TestHeuristicFunctionDisclaimers)

### Changed
- `pharmacology_guards.py` Public API에 `HEURISTIC_FUNCTION_DISCLAIMERS`,
  `is_heuristic_function` 추가.

### Notes — 본 closure의 메타 의의

사용자 통찰로 발견된 **하네스 본질의 명확화**:

> "이 하네스는 pre-wet-lab screening Agentic AI system을 *잘 구현하기 위한*
> 메타 인프라이지, screening을 *직접 수행*하는 도구가 아니다."

VR-cycle-02 (반감기 cap 정책)는 *틀린 frame*에 갇혀 있었음. cap을 어디 두든
`predict_half_life()` 함수 자체가 휴리스틱이라 임상 의미가 없음. 진짜 closure는
"정직한 명세화 — 함수의 한계가 노출되도록 가드 + 해석 가이드 + 환각 시나리오
등록". 이는 도메인 정확도 향상이 아니라 *도메인 한계의 시스템적 노출*이고,
**그것이 하네스가 할 일이다.**

VR-cycle-02도 본 cycle 09의 부분 closure로 흡수 — cap은 불필요 (절대값 의미
없음). 단 운영 데이터 누적 후 분기 회고에서 R2 (deprecate + 대체 도구 도입)
검토 가능.

### Verification
- 전체 pytest: **93/93 PASS** (이전 89 + H-06 가드 4)
- auto_dispatch routing 16/16 PASS (회귀 없음)

### Closure 상태 (8건 중 5건 closed)

| ID | 항목 | 상태 |
|----|------|------|
| VR-cycle-01 | C-07 DOTA 도입 | ✅ CLOSED (v0.13.0) |
| VR-cycle-02 | 반감기 상한 cap | ✅ CLOSED — frame 재정의로 VR-cycle-09에 흡수 |
| VR-cycle-03 | PyRosetta SS bond API | ✅ CLOSED (v0.12.1) |
| VR-cycle-04 | auto_dispatch 휴리스틱 | ✅ CLOSED (v0.13.0) |
| VR-cycle-05 | cross-validation echo | ⏸ 운영 데이터 누적 후 |
| VR-cycle-06 | Fan-out 토큰 비용 | ⏸ 운영 데이터 누적 후 |
| VR-cycle-07 | 자동 동기화 | ✅ CLOSED (v0.13.0) |
| VR-cycle-08 | PDB 좌표 score 한계 | ⏸ 별도 인프라 |
| **VR-cycle-09** | **H-06 계산 불가능을 계산 가능한 척** | ✅ **CLOSED — 본 release** |

---

## [0.13.0] — 2026-05-11

### Added
- **Stage 8e (VR-cycle-04 closure)**: auto_dispatch 라우팅 회귀 테스트 신설.
  - `scripts/test_auto_dispatch_routing.sh` (110줄, 실행 가능)
  - 16개 표준 케이스 (외부 동사구 6 + 내부 도메인 6 + 동사구+도메인 혼합 2 + unmatched 1 + 외부 영문 1)
  - 결과: **16/16 PASS**. 외부 CLI 동사구 + 도메인 단어 동시 입력 시 외부 우선 매칭 검증.
- **Stage 8f (VR-cycle-07 closure)**: 사이클 자기 일관성 pytest 신설.
  - `pipeline_local/tests/test_cycle_consistency.py` (90줄)
  - `_workspace/phase3_experiment.py`의 TEST_CASES 12개를 parametrize로 production code와 자동 비교
  - 추가 SST14 상수 + 케이스 카운트 회귀 가드 (총 14 tests)
  - Phase 5 같은 production code 변경이 phase3 expected와 어긋나면 CI/로컬에서 즉시 catch.
- **Stage 8g (VR-cycle-01 closure)**: C-07 DOTA chelator stoichiometry 규칙 도입.
  - `_rule_c07_dota_double_conjugation` — 펩타이드당 DOTA 1개 제한 (theranostic 라벨링)
  - 출처: Reubi 2000 Eur J Nucl Med 28:836; Wadas 2010 Chem Rev 110:2858
  - 4 tests (single/double/case-insensitive/triple) → 모두 PASS
  - `pharmacology_guards.py::LITERATURE_VALUES["modification_conflict_rules"]["C-07"]` 등록

### Verification
- 전체 pytest: **89/89 PASS** (이전 71 + C-07 테스트 4 + cycle_consistency 14)
- auto_dispatch routing 테스트: 16/16 PASS

### Closure 상태

| ID | 항목 | 상태 |
|----|------|------|
| VR-cycle-01 | C-07 DOTA 도입 | ✅ CLOSED |
| VR-cycle-02 | 반감기 상한 cap | ⏸ 정책 결정 대기 |
| VR-cycle-03 | PyRosetta SS bond API | ✅ CLOSED (v0.12.1) |
| VR-cycle-04 | auto_dispatch 휴리스틱 | ✅ CLOSED |
| VR-cycle-05 | cross-validation echo | ⏸ 운영 데이터 누적 후 |
| VR-cycle-06 | Fan-out 토큰 비용 | ⏸ 운영 데이터 누적 후 |
| VR-cycle-07 | 자동 동기화 | ✅ CLOSED |
| VR-cycle-08 | PDB 좌표 score 한계 | ⏸ 별도 인프라 필요 |

**8건 중 4건 closed** — 사이클이 자기 §검증 항목을 50% 닫음.

---

## [0.12.1] — 2026-05-11

### Fixed
- **VR-cycle-03 closure**: PyRosetta SS bond API 정정.
  - 원인: `DisulfideInsertionMover().set_residue_ids(3, 14)` — 존재하지 않는 메서드 호출
  - 수정: `core.conformation.form_disulfide(pose.conformation(), 3, 14)` 사용
  - 재실험 결과: linear 3009.20 → +SS bond 17467.58 → MinMover 12786.89 (strain 단계적 해소 확인)
- `_workspace/phase3_experiment.py` `expected` 값 갱신 (Phase 5 C-04 격상 반영) → 12/12 PASS 회복.

### Added
- **VR-cycle-07** 식별: Phase 5 production code 변경이 phase3_experiment.py의 expected와 자동 동기화 안 됨 — 다음 분기 회고에서 자동 일관성 메커니즘 검토.

### Notes
- `_workspace/release/scenario-modification-conflict-2026-05-11.md` §7 "후속 정정"으로 결과 보존.
- `_workspace/phase3_experiment.py`는 .gitignore 정책상 force-add로 영구 추적 (재현 보장).

---

## [0.12.0] — 2026-05-11

### Added
- **Stage 8d** (End-to-End Cycle Dogfooding): modification_conflict checker 도입을 통한 사이클 1회 전체 운영 — `구현 → 검증 → 실험 → 갭 피드백 → 수정 → 완성`.
- `pipeline_local/scripts/modification_conflict.py` (신설, ~480줄, 9 conflict rules + INTERNAL_ERROR)
- `pipeline_local/tests/test_modification_conflict.py` (38 tests)
- `_workspace/01~07_*.md` + `_workspace/phase3_experiment.py` + `_workspace/06_experiment_raw.json`
- 종합 보고서: `_workspace/release/scenario-modification-conflict-2026-05-11.md`
- `pharmacology_guards.py::LITERATURE_VALUES["modification_conflict_rules"]` — C-01~C-10 + C-99 출처 추적 등록 (Stage 5 절차 dogfooding)

### Changed
- `scripts/auto_dispatch.sh::detect_route()` — 외부 CLI 동사구를 도메인 키워드보다 우선 매칭 (Phase 4에서 발견된 라우팅 버그 A-4 수정)

### Fixed
- **Critical (Phase 4 갭에서 발견·Phase 5 수정)**:
  - A-1: silent exception swallowing → C-99 `INTERNAL_ERROR` Conflict 승격
  - A-4: auto_dispatch가 "modification" 같은 도메인 키워드를 외부 CLI 동사구보다 우선 매칭하던 버그
  - C-04 severity WARNING → ERROR 격상 (Veber 1978, Pellegrini 1999 출처)
- A-5 dead code `_SST14_CYS_SS_POSITIONS` 제거
- A-6 `_RULES` 레지스트리 순서 — C-06 (range check) 최우선
- A-7 누락 규칙 3건 추가: C-08 SS pair 양쪽 D-Cys / C-09 lactam + N-term mod / C-10 substitution + d_amino_acid

### Verification
- pytest **71/71 PASS** (33 pharmacology_guards + 38 modification_conflict)
- conflict matrix **12/12 PASS** (Phase 3 실 실험)
- auto_dispatch 라우팅 **3/3 재검증** (외부 동사구 / 도메인 단어 / EOD 모두 의도대로)
- codex 실 호출 1회 (23초, reviewer-code와 독립 일치)
- PyRosetta SST-14 score 1회 (3009 → 19, SS bond API는 §검증 필요 VR-cycle-03)

### Notes
- **사이클 1회 종료 판정**: PASS (조건부) — 6 §검증 필요 항목(VR-cycle-01~06)을 다음 분기 회고로 분리.
- 본 Stage 8d로 사용자가 정의한 사이클(`구현→검증→실험→갭→수정→완성`)이 13명 팀 + 가드 + auto_dispatch 인프라로 1회 완주됨을 입증.

---

## [0.11.0] — 2026-05-11

### Added
- **Stage 8c**: 외부 CLI 자동 dispatch 파이프라인.
  - `scripts/auto_dispatch.sh` (신설, 208줄) — CLAUDE.md 트리거 키워드 표 기반 라우팅
  - 자동 호출: `codex review` / `codex exec` / `cursor-agent -p`
  - 자동 보존: `_workspace/{NN}_{cli}_<slug>.md` (Stage 1 컨벤션)
  - 내부 에이전트 입력은 안내 메시지로 가드 (자동 호출 X, 본 세션 Agent tool 의무)
  - unmatched 입력은 명시적 거부 (자동 추측 차단)
- `.claude/agents/orchestrator.md`에 §"외부 CLI 자동 dispatch" 추가.
- 검증 보고서: `_workspace/release/auto-dispatch-validation-2026-05-11.md` — 5/5 dry-run PASS.

### Notes
- 본 Stage로 "Codex/Cursor도 다 호출해서 쓰는가" 질문에 부분 자동화 답변 (Claude Code 내부는 본 세션 의무, 외부 CLI는 자동).
- `codex exec --dangerously-bypass-approvals-and-sandbox` 사용의 안전성 검토는 별도 §검증 필요 (VR-autodispatch-02).

---

## [0.10.0] — 2026-05-11

### Added
- **Stage 8b**: `reviewer-science` 도메인별 4분리.
  - `reviewer-pharma` (약리학·ADMET·PK/PD) — Stage 5 `pharmacology_guards.py` 직결
  - `reviewer-biology` (펩타이드 구조·SS bond·GPCR 결합)
  - `reviewer-chemistry` (합성·modification·DOTA 라벨링)
  - `reviewer-math` (NSGA-II·BO·통계·수렴)
- 검증 보고서: `_workspace/release/agent-reviewer-domain-split-validation-2026-05-11.md`
- CLAUDE.md 트리거 키워드 표 +5 행, 팀원 목록 +4 명 (총 13명).

### Changed
- `reviewer-science` 재정의: 직접 검증자 → **라우터·통합 판정자** (Expert Pool 패턴).
  - 기존 호출 호환: 단일 도메인 호출은 라우터가 자동 위임, 오버헤드 최소.
- `reviewer-pharma` 도입으로 Stage 5 환각 가드 → 약리학 리뷰어 직결 (이전: 통합 reviewer-science가 호출).

### Notes
- 도메인 경계 모호한 입력은 `reviewer-science` 라우터가 통합 판정.
- A/B 정량 측정은 실 트래픽 후 다음 분기 회고에서.

---

## [0.9.0] — 2026-05-11

### Added
- **Stage 8a**: 전용 `researcher` 에이전트 신설.
  - `.claude/agents/researcher.md` — Expert Pool 패턴, sonnet 모델
  - 검증 보고서: `_workspace/release/agent-researcher-validation-2026-05-11.md`
  - should-trigger 8개 + should-NOT-trigger 8개 + reviewer-science와 역할 경계 명시
- `CLAUDE.md`: 자동 트리거 키워드 표에 "논문 조사·문헌 비교·선행 연구·research·literature review" 행 추가.
- `CLAUDE.md`: 팀원 목록에 researcher 추가 (총 9명).

### Changed
- `reviewer-science`의 역할 범위 표기 명료화: "수집은 researcher가" 주석 추가 (CLAUDE.md 팀원 목록).

### Notes
- Stage 8b (reviewer-science를 도메인별 분리) / 8c (Codex·Cursor 자동 호출 파이프라인)는 별도 minor 버전으로 분할 예정.

---

## [0.8.0] — 2026-05-11

### Added
- **Stage 7**: `.claude/agents/` 6개 에이전트 정의에 harness 표준 3섹션(입력 프로토콜 / 출력 프로토콜 / 에러 핸들링) 보강.
  - `orchestrator.md` / `reviewer-code.md` / `reviewer-science.md` / `engineer-backend.md` / `engineer-infra.md` / `reviewer-uiux.md`
  - 평균 +24줄 per file, 기존 내용 무손상 (append-only)
- `reviewer-science.md`: §"알려진 historical defect" 신설 — Stage 5 회귀 테스트와 연동된 기록 보존.

### Changed
- INTEGRATION_PLAN.md Stage 7의 가정 (".claude/agents/ 부재") 정정: 실제로는 이미 6개 정의 파일 존재 → 신설이 아닌 표준 섹션 보강으로 작업 재정의.

### Notes
- 본 Stage 적용으로 모든 INTEGRATION_PLAN Stage(0~7) 완료.
- 다음 Stage 후보는 분기 회고(`RETROSPECTIVE_GUIDE.md`)에서 발굴 예정.

---

## [0.7.0] — 2026-05-11

### Added
- **Stage 6**: 본 `CHANGELOG.md` 신설 (Phase 7 진화 메커니즘 운영화).
- PR 템플릿(`.github/PULL_REQUEST_TEMPLATE.md`)에 "harness 어댑테이션 변경 사항" 체크 항목 추가.
- `tools/harness-adaptation/RETROSPECTIVE_GUIDE.md` — 분기 회고 진행 가이드.

### Changed
- `CLAUDE.md` §"Harness Pointer / Stage 적용 이력"에 Stage 6 entry 추가.
- 미적용 Stage 목록에서 Stage 6 제거.

---

## [0.6.0] — 2026-05-11

### Added
- **Stage 4**: 신규 에이전트/스킬 PR 의무 검증 템플릿 도입.
  - `.github/PULL_REQUEST_TEMPLATE.md` (84줄) — GitHub PR 시 자동 노출
  - `tools/harness-adaptation/templates/agent-validation-template.md` (95줄)
  - `tools/harness-adaptation/templates/skill-validation-template.md` (80줄)
- PR 템플릿에 §"신규 에이전트/스킬 의무 검증" + §"lookup table 변경 검증" 2개 섹션.
- 검증 보고서는 `_workspace/release/{agent|skill}-<name>-validation-YYYY-MM-DD.md`로 보존.

### Changed
- `CLAUDE.md` §"Harness Pointer" 미적용 Stage에서 Stage 4 제거.
- `tools/harness-adaptation/README.md`에 templates 항목 추가.

### 커밋
- `81f2141`

---

## [0.5.0] — 2026-05-11

### Added
- **Stage 3**: 작업 위임 의사결정 트리 1~4순위 각각에 harness 6패턴 명칭 매핑.
- 각 순위에 `ANALYSIS.md §5.X` 인용 추가하여 사후 감사 가능.

### 매핑 표
| 순위 | 패턴 |
|------|------|
| 1 tmux team-mate | Fan-out/Fan-in 또는 Supervisor |
| 2 codex/cursor-agent | Expert Pool |
| 3 Agent tool | Pipeline / Producer-Reviewer / Fan-out/Fan-in |
| 4 직접 구현 | 없음 (+ Hierarchical Delegation 평탄화) |

### 커밋
- `3a3a54b`

---

## [0.4.0] — 2026-05-11

### Added
- **Stage 2**: `CLAUDE.md`에 §"Harness Pointer" 블록 신설.
  - 8개 산출물 경로 + Stage 적용 이력 테이블 + 미적용 Stage 안내.
- 자동 트리거 키워드 표에 1행 추가: "하네스/팀 아키텍처/패턴 선택/Stage N 진행".

### Notes
- `SKILL.md:264-265` 원칙 준수: Pointer 블록에는 에이전트·스킬 목록 직접 기재 금지. 목록은 §"팀원 목록"이 담당.

### 커밋
- `a3b3bb8`

---

## [0.3.0] — 2026-05-11

### Added
- **Stage 5 (Critical)**: 약리학 환각 가드 모듈 + 33개 회귀 테스트.
  - `pipeline_local/scripts/pharmacology_guards.py` (245줄)
    - `LITERATURE_VALUES` — 알려진 정답 4개 테이블 (KD, RW Boman convention, NEND mammalian, Lehninger pKa)
    - `SCALE_RANGES` — 10개 척도의 합리 범위
    - `SIGN_CONVENTIONS` — 부호 규약 invariant
    - `assert_literature_value` / `audit_table` / `assert_in_range` / `check_sign_convention`
  - `pipeline_local/tests/test_pharmacology_guards.py` (271줄, 33 tests, all passing)
- 검증 보고서: `_workspace/release/stage5-pharmacology-guards-2026-05-11.md`.

### Fixed
- 가드 자체 결함 1건 (코드 작성 중 발견·수정): `boman_index_kcal_per_mol` 범위가 `[-5, +5]`로 너무 좁음 → `[-5, +15]`로 보정 (all-K = 5.55, 이론 max all-R = 14.92).

### Notes (회귀 차단 대상)
- `RW_TRANSFER[P]=0.0` (truth -2.54, Boman convention)
- `RW_TRANSFER[S]=1.15` (truth 3.40, Boman convention)
- `NEND_HALFLIFE[P]=20.0` (truth 30.0; species confusion yeast vs mammalian)

### 커밋
- `de5fabb`

---

## [0.2.0] — 2026-05-11

### Added
- **Stage 1**: `_workspace/` 디렉토리 + 파일명 컨벤션 (`{NN}_{agent}_{artifact}.{ext}`).
- `_workspace/README.md` — 컨벤션 + git 추적 정책 (README + release/*.md 추적, raw 산출물 ignore).
- `.gitignore`에 4줄 패턴 추가.

### Changed
- 책임 분리: `logs/external_agents/` (호출 메타) vs `_workspace/` (산출물 자체).

### 커밋
- `5805109`

---

## [0.1.0] — 2026-05-11

### Added
- **Stage 0**: 어댑테이션 디렉토리 신설.
- revfactory/harness v1.2.0을 Git submodule로 추가 (Apache-2.0 LICENSE 보존).
- 산출물 9개:
  - `README.md`, `ANALYSIS.md` (모든 주장 파일:라인 인용)
  - `PROMPT_TEMPLATE.md` (CLI-agnostic 범용 프롬프트)
  - `PROMPT_PRST_N_FM_EXAMPLE.md` (SST-14 / SSTR2 도메인 적용 예시)
  - `adapters/{claude-code,codex-cli,cursor-agent}.md`
  - `INTEGRATION_PLAN.md` (Stage 0~7 로드맵)
  - `checklist.md`
- `.gitignore`에 `/tools/*` + `!/tools/harness-adaptation/` 예외처리.
- 3개 서브에이전트 병렬 분석 결과(engineer-backend / reviewer-code / reviewer-science) 통합.

### Design decisions
- L1 (`.claude-plugin/`, `EXPERIMENTAL_AGENT_TEAMS=1` 등 Claude Code 종속) 미채택.
- L2 (6패턴, Phase 0~7 워크플로우, `_workspace/` 컨벤션, 검증 게이트) 추출.
- L3 (우리 기존 자산과 중복) 통합.
- 도메인 환각 가드 H-01~05 (약리학 수치) 추가.

### 커밋
- `2637b1c`

---

[Unreleased]: https://github.com/<owner>/<repo>/compare/harness-v0.17.0...HEAD
[0.17.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.17.0
[0.16.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.16.0
[0.15.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.15.0
[0.14.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.14.0
[0.13.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.13.0
[0.12.1]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.12.1
[0.12.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.12.0
[0.11.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.11.0
[0.10.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.10.0
[0.9.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.9.0
[0.8.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.8.0
[0.7.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.7.0
[0.6.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.6.0
[0.5.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.5.0
[0.4.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.4.0
[0.3.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.3.0
[0.2.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.2.0
[0.1.0]: https://github.com/<owner>/<repo>/releases/tag/harness-v0.1.0
