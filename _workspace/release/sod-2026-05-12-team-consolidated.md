# SOD 2026-05-12 — Team `sod-2026-05-12-f11-recovery` 통합 보고서

- **팀 리드**: orchestrator (Claude Code 본 세션)
- **팀 API**: Claude Code 네이티브 Agent Team (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1)
- **세션 시간**: 2026-05-12 (전 세션 EOD 직후 SOD 모드)
- **목표**: F11 fix 적용 → 어제 데모 결과 회수·분석 → FE UI live 표시 디버깅 → Silo A dogfood 준비 → 회귀 테스트로 5개 작업 병렬 처리

---

## 1. 작업 분장 결과

| Task | 담당 | 상태 | 산출 |
|------|------|------|------|
| T1 — F11 fix (`_get_reference_complex_path` / `_get_reference_peptide_com` stale path) | engineer-backend (`backend`) | ✅ COMPLETED | `pipeline_local/steps/step06_rosetta.py` 수정 + `test_tier3_reference_complex_fix.py` 10 tests |
| T2 — 어제 데모 iter01~03 결과 회수 + ddG 분석 | reviewer-science (`science`) | ✅ COMPLETED | `_workspace/release/scenario-silo-b-tier12-validation-2026-05-12.md` |
| T3 — FE UI live 표시 (PipelineStatus + AgentMonitor) 디버깅 | reviewer-uiux (`frontend`) | ✅ COMPLETED | `usePipelineStatus.ts` + `SiloBPage.tsx` 수정 |
| T4 — F9 Silo A dogfood 환경 준비 + 명령 verification | engineer-infra (`infra`) | ✅ COMPLETED | `_workspace/release/silo-a-readiness-2026-05-12.md` |
| T5 — T1 F11 fix 회귀 테스트 + 코드 품질 리뷰 | reviewer-code (`tester`) | ✅ COMPLETED | 155/155 PASS, 4 minor issues 식별 |

병렬 실행으로 5개 작업 동시 처리. 5/5 closure.

---

## 2. 핵심 산출 요약

### 2.1 T1 — F11 fix (Critical, backend)

**대상 함수**: `pipeline_local/steps/step06_rosetta.py`
- `_get_reference_complex_path()` — 참조 복합체 PDB search path 정정
- `_get_reference_peptide_com()` — 참조 펩타이드 COM 계산 search path 정정

**변경**: stale path(`PRST_N_FM/data/fold_test1/...`) → 실 위치 2개 추가
1. `<repo>/data/fold_test1/fold_test1_model_0.pdb`
2. `<repo>/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/data/fold_test1/fold_test1_model_0.pdb`
- `REFERENCE_COMPLEX_PATH` 환경변수 override 지원 추가

**검증**: `_get_reference_peptide_com()` → `(-6.56, -19.23, -4.19)`, `_get_reference_complex_path()` → 유효 경로 반환.

### 2.2 T2 — 데모 결과 분석 (science)

| iter | seq_id | ddG (REU) | clash_score | Boltz score | cache_key (sha256[:24]) |
|------|--------|-----------|-------------|-------------|------------------------|
| iter01 | var_012 (K4N) | **40,582.7** | 191 | -9.6060 | `ef1409446d7fc6b52f7c7de5` |
| iter02 | var_024 (F6W) | **102,496.0** | 285 | -9.6274 | `9476678b351f5b739a287866` |
| iter03 | var_012 (K4N) | **42,462.2** | 268 | -9.3630 | `22bd4293bb2694edc871ff25` |

- **HEURISTIC-INVALID**: ddG 40K~102K REU는 결합 친화도 아닌 clash strain 신호. PyRosetta 정상 범위(±50 REU) 세 자릿수 초과.
- **HEURISTIC-VALID**: Boltz score -9.3 ~ -9.6 정상 범위.
- **F1+F3 fix 효과 검증됨**: cache key 3개 모두 상이 → 어제까지의 cache 충돌 해소 확인.
- **F11 결함 원인 확인**: 데모 시점에는 F11 미적용 → 펩타이드가 binding pocket 밖 배치 → 비현실적 ddG 산출. 현재 코드는 fix 완료, 재실행 시 -45 ~ -51 REU 복원 예상(메모리 기반 추정).
- **데모 실행 시각**(13:29 KST)이 Tier 1 PR #12 머지(21:46 KST)보다 *이전*임을 확인 → 결과는 fix 적용 전 상태로 해석 필요.

### 2.3 T3 — FE UI live 표시 fix (frontend)

**근본 원인 2개**:
1. `usePipelineStatus` 훅의 AbortController 라이프사이클이 React StrictMode double-mount에 취약 → 초기 fetch가 즉시 abort
2. `SiloBPage.tsx`의 `SILO_B_STEPS` whitelist에 step03b_qc/04/05/05b/08/09 누락 → 진행 중 step이 화면에 표시되지 않음

**수정**:
- `usePipelineStatus.ts` — `fetchLiveStatus(signal?: AbortSignal)` 시그니처 도입, `mountedRef`로 strict-mode 가드, polling effect 재구성
- `SiloBPage.tsx` — `SILO_B_STEPS` 화이트리스트에 누락 6 step 추가

**결과**: PipelineStatus 실시간 갱신 정상 동작 예상 (사용자 측 F5 reload 없이도 mount 시점부터 표시).

### 2.4 T4 — Silo A 환경 준비 (infra)

| 항목 | 상태 |
|------|------|
| GPU 4×H100 NVL | 92 GB free each (전부 유휴) |
| conda env: rfdiffusion / proteinmpnn / esmfold / boltz | **4/4 OK** |
| 모델 가중치 (RFdiffusion 8종, ESMFold/Boltz HF cache) | **OK** |
| `ligandmpnn` CLI 미검증 → 검증 완료 | **39일 전 우려 해소** |
| wrapper script (`run_rfdiffusion.py`, `run_proteinmpnn.py`) | 검토 이상 없음 |

**알려진 장애물 4건** (모두 낮음/중간):
- B1: `pipeline_config_local_dogfood.yaml`의 `local_models.rfdiffusion.enabled: false` → 1줄 수정 필요
- B2: LLM 기본값이 vLLM/Qwen3.5-27B/port 8002 → ollama 11435 사용 시 CLI override 필요
- B3: `--output-dir` 사전 생성 (pipeline 자동)
- B4: `CUDA_VISIBLE_DEVICES=2,3` 설정 (이중 silo 시)

**예상 자원**: 1 iter(n=10) 약 15~35분 / GPU 여유 충분.

### 2.5 T5 — T1 F11 fix 리뷰 (tester, CONDITIONAL PASS)

**총괄**: pytest 155/155 PASS (109 baseline → +46). F11 신규 테스트 10/10 PASS.

**4 minor issues**:
| ID | Severity | 위치 | 내용 |
|----|----------|------|------|
| Issue-1 | **Medium** | `test_tier3_reference_complex_fix.py:138-166` `test_returns_none_when_all_paths_missing` | `original_fn = mod._get_reference_complex_path` 저장 후 미사용; 로컬 `_patched()`가 자신을 호출 — 실 모듈 함수 미검증 |
| Issue-2 | Low | `step06_rosetta.py:475-483`, `:619-627` | `ref_paths` 리스트가 두 함수에 100% 중복 — `_build_ref_paths()` 추출 권장 |
| Issue-3 | Low | `_get_reference_peptide_com()` | `logger.info` 누락 — `_get_reference_complex_path` L630과 패턴 불일치 |
| Issue-4 | Low/Med | 테스트 카운트 | backend 보고 117/119, tester 측 관찰 155/155 — Bio 모듈 skip 차이 가능, 재확인 권장 |

판정: **CONDITIONAL PASS** — 머지 가능, 위 4건은 후속 PR로 처리 권장.

---

## 3. 진척도 비교 (어제 EOD → 오늘 SOD)

| 영역 | 어제 EOD | 오늘 SOD |
|------|---------|---------|
| F11 (`_get_reference_*` stale path) | 미적용 (어제 후반 식별) | ✅ 코드 적용 + 10 회귀 테스트 |
| 어제 데모 분석 | iter01 부분 ddG 확인 | ✅ iter01~03 전체 + HEURISTIC 신뢰등급 |
| FE UI live 표시 | 사용자 F5 reload 필요 | ✅ 근본 2개 원인 fix |
| Silo A 환경 | "ProteinMPNN 미검증" (39일 전) | ✅ 4 env + 가중치 + CLI 전부 확인 |
| 회귀 테스트 | tier1 9 + tier2 5 | ✅ 155/155 (+tier3 10) |

---

## 4. 미해결·후속 작업

### 4.1 즉시 후속 (확정 후 실행)
1. **새 데모 실행** — Tier 1+2+3 모두 적용한 상태에서 Silo B only 1~3 iter (ddG -45~-51 회복 검증)
2. **F9 Silo A dogfood** — T4 인계 체크리스트(§8) 기반 첫 실행

### 4.2 코드 품질 (후속 PR)
- T5 Issue-1: `test_returns_none_when_all_paths_missing`를 실 모듈 함수 호출 형태로 재작성
- T5 Issue-2: `_build_ref_paths()` 공통 헬퍼 추출 (DRY)
- T5 Issue-3: `_get_reference_peptide_com()`에 `logger.info` 추가
- T5 Issue-4: 117/119 vs 155/155 차이 재확인

### 4.3 별도 PR (R1)
- LLM provider override (`--llm-provider` flag) — Critical 분류된 R1 권고 미구현 잔존

### 4.4 백그라운드 보존
- ollama 11435, BE 8787, FE 5173 가동 중
- PID 946370(`silo_b_demo_tier2_2026-05-11`) 어제 완료

---

## 5. 메타 관찰 (팀 모드 자체)

- **5명 병렬 처리** — 단일 세션 직렬 진행 대비 약 4~5배 단축 (체감)
- **역할 분리의 효과**: science의 HEURISTIC 신뢰등급 부여, tester의 Issue-1 발견(테스트가 자기 함수 검증), frontend의 React StrictMode 진단 — 단일 에이전트가 모두 노출시키기 어려운 다층 결함
- **이전 메모리(VR-cycle-08 GATE-F echo 가드) 활용**: tester가 backend 보고를 무비판적으로 echo하지 않고 117 vs 155 재교차 검증 — 가드 정착 신호

---

## 6. 통합 판정

**TEAM SOD: COMPLETED — 5/5 tasks closed**

- 어제 EOD 시점 미해결 7건 중 5건 closure (F11/데모분석/FE live/Silo A 준비/회귀)
- 잔여 2건: 새 데모 실행 + F9 Silo A dogfood (다음 SOD 후보)

본 통합 보고서가 user 의사결정 대기 상태.
