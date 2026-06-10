# pipeline_local 코드 분석 보고서
> T4 — 구조·품질·개선점 식별  
> 작성일: 2026-05-12  
> 담당: reviewer-code  
> 판정: **CONDITIONAL** (Critical 이슈 3건 + High 9건 존재)

---

## §1 모듈 인벤토리

### 1-1. 핵심 파일 (라인 수 + 주요 책임)

| 파일 | 라인 | 함수 수 | 주요 책임 |
|------|------|---------|---------|
| `orchestrator.py` | **2,226** | **33** | 파이프라인 전체 흐름, 에이전트 호출, 상태 파일 기록, UI live progress |
| `steps/step06_rosetta.py` | **916** | **29** | PyRosetta 정제, 결과 캐시, mmCIF 변환, 복합체 조립 |
| `steps/step07_analysis.py` | **613** | **10** | FoldMason 정렬, PyMOL 렌더, 인터페이스 분석, 보고서 |
| `steps/step04_qc.py` | **675** | **8** | ESMFold QC, pLDDT 게이트, 이황화결합 게이트 |
| `steps/step05c_boltz_cross.py` | **706** | **12** | Boltz 교차 도킹 |
| `steps/step08_stability.py` | **636** | **6** | 안정성 휴리스틱 ranking (H-06 disclaimer 포함) |
| `steps/step05_docking.py` | **537** | **10** | DiffDock/Boltz 도킹 |
| `steps/step01_receptor.py` | **513** | **10** | 수용체 준비, 포켓 잔기 추출 |
| `steps/step03b_blosum_mutation.py` | **477** | **10** | BLOSUM62 변이체 생성 |
| `steps/step05b_selectivity.py` | **473** | **10** | 오프타겟 선택성 평가 |
| `steps/step03_sequence.py` | **389** | **6** | ProteinMPNN 서열 설계 |
| `steps/step02_backbone.py` | **321** | **5** | RFdiffusion 백본 생성 |
| `scripts/modification_conflict.py` | **706** | **13** | 변형 충돌 검사 |
| `scripts/offtarget_dock.py` | **759** | **12** | 오프타겟 도킹 |
| `scripts/pharmacology_guards.py` | **435** | **5** | 약리학 환각 방지 가드 |
| `schemas/io_schemas.py` | **535** | N/A | 단계 간 I/O 스키마 (dataclass) |
| `core/local_runner.py` | **363** | **11** | conda subprocess 실행, JSON 파싱 |
| `core/config_loader.py` | **111** | **3** | model_paths.yaml 로드 |
| `core/selectivity_runner.py` | **327** | **5** | 선택성 평가 runner |
| `backend/state.py` | **189** | N/A | 백엔드 싱글톤 상태 |

**총계**: 소스 파이썬 20,185 줄 / 테스트 2,287 줄

### 1-2. 테스트 파일 (라인 수 + 테스트 함수 수)

| 파일 | 라인 | `def test_` 수 |
|------|------|--------------|
| `test_modification_conflict.py` | 514 | 42 |
| `test_pharmacology_guards.py` | 352 | 39 |
| `test_step05c_boltz_cross.py` | 523 | N/A* |
| `test_offtarget_dock_boltz.py` | 362 | N/A* |
| `test_tier1_rosetta_fixes.py` | 163 | 9 |
| `test_step07_foldmason_n_check.py` | 210 | 6 |
| `test_tier2_ui_integration.py` | 91 | 5 |
| `test_tier3_reference_complex_fix.py` | 202 | N/A* |
| `test_cycle_consistency.py` | 80 | 3 |

*파일 read 제한으로 추정. 총 확인된 테스트 함수: **104개**

---

## §2 구조 분석

### 2-1. 단일 책임 원칙 (SRP) 위반

**[CRITICAL] `orchestrator.py` — 6개 책임이 1파일에 혼재 (신뢰: HIGH)**

`LocalPipelineOrchestrator` 클래스가 다음을 모두 담당:
1. 파이프라인 Step 실행 (`run_single_iteration`, `_execute_step`)
2. 에이전트 호출 및 fallback stub (`_invoke_agent`, `_invoke_agent_stub`)
3. 컨텍스트 변환 (`_adapt_agent_context`, `_map_agent_result`)
4. 상태 파일 기록/UI live progress (`_write_status`)
5. 수렴 판단 (`_check_convergence`)
6. 체크포인트 저장/로드 (`_save_state`, `_load_state`)

→ 분리 필요 (`StepExecutor`, `AgentRegistry`, `StatusReporter`, `ConvergenceChecker`, `CheckpointManager`)

**`run_single_iteration()` — 561줄 God Function** (`orchestrator.py:533~1093`)
- Approach A / Approach B / 듀얼 사일로 3분기 로직이 모두 인라인
- pLDDT 통계 캡처, 도킹 게이트, Rosetta 게이트, 다양성 선택, 에이전트 호출이 1함수에서 처리
- 30줄 이하 함수 기준 대비 **19배** 초과

### 2-2. 결합도 분석

- `orchestrator.py`는 `AG_src.*` (PlannerAgent, ScientistCriticAgent, DiversityManagerAgent, QCRankerAgent, ReporterAgent, BaseAgent, create_provider) 7개 모듈에 직접 의존 → 테스트 격리 불가
- `sys.path` 뮤테이션이 **8개 파일**에 분산 (orchestrator.py:65, run_pipeline_local.py:45, backend/state.py:36, tests/*.py 4개 등) — 로드 순서에 따라 다른 결과 가능
- `step05b_selectivity.py:75~103`에서 `SelectivityResult`, `OffTargetDockingResult`, `Step05bOutput` 클래스를 **try/except fallback 내부에 재정의** — io_schemas.py와 이중 정의

### 2-3. 패턴 일관성

- `steps/*.py`는 모두 모듈 레벨 함수 패턴 (클래스 없음) — 일관됨 ✅
- `step06_rosetta.py`만 `_ResultCache` 클래스 보유 (내부 캐시 목적, 합리적) ✅
- `core/local_runner.py`는 `LocalModelRunner` 클래스 패턴 ✅
- `schemas/io_schemas.py`는 `@dataclass` + `to_dict/from_dict` 패턴 일관 ✅

---

## §3 품질 메트릭

### 3-1. 타입 힌트

| 항목 | 수치 | 신뢰 |
|------|------|------|
| `Optional[...]` 사용 (steps/*.py) | 36건 | HIGH |
| `# type: ignore` (orchestrator.py) | 4건 | HIGH |
| `Any` 파라미터 (`_run_silo_a`, `_run_silo_b`) | 2건 | HIGH |

`_run_silo_a(step01_out: Any, ...)` — `Step01Output`으로 구체화 가능 (`orchestrator.py:1096`)  
`_run_silo_b(step01_out: Any, ...)` — 동일 (`orchestrator.py:1158`)

### 3-2. 에러 핸들링

| 위치 | 패턴 | 평가 |
|------|------|------|
| `_execute_step()` | try/except → StepResult(success=False) | ✅ 적절 |
| `run_foldmason_alignment()` | except Exception → 플레이스홀더 반환 | ⚠️ 과도하게 silent |
| `run_interface_analysis()` | except ImportError → stub; except Exception → continue | ✅ 합리적 |
| `_invoke_agent()` | except Exception → stub fallback | ✅ 합리적 |
| `_run_silo_b()` | `except Exception: # noqa: BLE001` | ⚠️ BLE001 suppress는 의도적이나 문서화 필요 |

전체적으로 **fail-soft 전략** 채택 — 파이프라인 중단 최소화 목적. 단, 일부 `except Exception` 범위가 너무 넓음.

### 3-3. DRY 위반

| 위반 위치 | 내용 | 신뢰 |
|-----------|------|------|
| `step06_rosetta.py:467`, `step06_rosetta.py:598` | `_get_reference_peptide_com()` vs `_get_reference_complex_path()`: 동일한 ref_paths 목록을 각각 로컬 변수로 구성 | HIGH |
| `orchestrator.py:65`, `run_pipeline_local.py:45`, `backend/state.py:36`, 테스트 4개 | `sys.path` AG_src 삽입 로직 8회 중복 | HIGH |
| `step04_qc.py:126~156` (배치 fallback) vs `step04_qc.py:236~330` (단독 predict_and_evaluate) | pLDDT 게이트 판정·이황화결합 게이트 로직 부분 중복 | MED |
| `orchestrator.py:1797` | `_STEP_PROGRESS` dict가 `_write_status()` 메서드 내부에서 매 호출마다 재생성 | MED |

### 3-4. Anti-Pattern

| 위치 | 패턴 | 이유 |
|------|------|------|
| `orchestrator.py:910` | `locals().get("step03b_out")` | 동적 스택 프레임 조회 — 리팩토링 시 silent bug 유발 |
| `orchestrator.py:933` | `type('R', (), {'success': True, 'output': ...})()` | 익명 클래스 — `StepResult` dataclass 사용해야 |
| `step06_rosetta.py:255` | `import shutil` (for 루프 내부) | 함수 최상단으로 이동 필요 |
| `step06_rosetta.py:614` | 일본어 주석 ("conda run -n bio-tools で ...") | 코드베이스 언어 불일치 |
| `step06_rosetta.py:142~162` | `is_pyrosetta_available()` 함수 속성(`._cached`)으로 캐시 | 클래스/functools.lru_cache 사용 권장 |

### 3-5. 매직 상수

| 위치 | 값 | 의미 |
|------|-----|------|
| `orchestrator.py:1209` | `"AGCKNFFWKTFTSC"` 하드코딩 | config에서 읽어야 (SST-14 원본 서열) |
| `step07_analysis.py:305` | `cutoff = 5.0` (계면 분석 거리) | 상수 정의 필요 |
| `step07_analysis.py:325` | `float(len(contact_rec) * 25)` | BSA 추정 매직 넘버 |
| `orchestrator.py:659` | `approach_b_cfg.get("stability_prescreen_min_hours", 50.0)` | gate_thresholds.yaml과 중복 기본값 |

---

## §4 테스트 분석

### 4-1. 커버리지 추정

| 모듈 | 테스트 존재 | 커버리지 추정 | 비고 |
|------|-----------|------------|------|
| `orchestrator.py` | ❌ 없음 | ~0% | 가장 복잡한 파일 (2226줄) 미커버 |
| `steps/step01_receptor.py` | ❌ 없음 | ~0% | |
| `steps/step02_backbone.py` | ❌ 없음 | ~0% | |
| `steps/step03_sequence.py` | ❌ 없음 | ~0% | |
| `steps/step04_qc.py` | ❌ 없음 | ~0% | |
| `steps/step05_docking.py` | ❌ 없음 | ~0% | |
| `steps/step05b_selectivity.py` | 부분 (offtarget_dock) | ~20% | |
| `steps/step05c_boltz_cross.py` | ✅ test_step05c... | ~60% | |
| `steps/step06_rosetta.py` | ✅ test_tier1_rosetta_fixes | ~30% | F1/F2/F3 커버, 나머지 미커버 |
| `steps/step07_analysis.py` | ✅ test_step07_foldmason_n_check | ~40% | F-05 기대 동작 커버 (T1 fix 후) |
| `scripts/modification_conflict.py` | ✅ test_modification_conflict | ~80% | 42개 테스트 |
| `scripts/pharmacology_guards.py` | ✅ test_pharmacology_guards | ~90% | 39개 테스트 |
| `core/local_runner.py` | ❌ 없음 | ~0% | |
| `core/config_loader.py` | ❌ 없음 | ~0% | |
| `schemas/io_schemas.py` | ❌ 없음 | ~0% | |

**전체 추정 커버리지**: ~25% (가중 라인 기준)

### 4-2. Mock 패턴 분석

- `test_tier1_rosetta_fixes.py`: `pytest.fixture(scope="class")` + Stage 9 실 아티팩트 의존 → 아티팩트 없으면 `pytest.skip` — 적절한 전략 ✅
- `test_step07_foldmason_n_check.py`: `unittest.mock.patch` + `MagicMock` — subprocess를 격리하는 올바른 패턴 ✅
- `test_modification_conflict.py`: 42 테스트로 가장 충실 ✅
- `test_cycle_consistency.py`: `_PHASE3_AVAILABLE` 조건부 skip — 외부 실험 파일 의존 ⚠️

### 4-3. Skip/XFail 현황

- `test_cycle_consistency.py:39`: `@pytest.mark.skipif(not _PHASE3_AVAILABLE, ...)` — 환경 의존 skip
- F-05 fix 테스트(`test_step07_foldmason_n_check.py`)는 T1 미적용 시 실패 가능

---

## §5 결함 ↔ 코드 위치 매핑

### 5-1. F-05 — FoldMason "Need ≥ 2 structures" 처리

- **현재 코드** `step07_analysis.py:199~202`:
  ```python
  if len(pdb_paths) < 2:
      logger.info("[Step07] Fewer than 2 PDBs; skipping FoldMason alignment.")
      return FoldMasonResult(lddt_scores={}, html_report="", success=False,
                             error="Need >= 2 structures for alignment.")
  ```
- **문제**: `success=False`로 반환 → `run_analysis()`에서 파이프라인 에러처럼 처리될 수 있음
- **T1 fix가 기대하는 동작** (test_step07_foldmason_n_check.py:47~67): `success=True, skipped=True, error=None`
- **영향**: T1 fix가 적용되면 `FoldMasonResult`에 `skipped: bool` 필드 추가 필요 → `io_schemas.py` 또는 step07 내부 dataclass 수정 연동

- **T1과 본 분석의 충돌 가능성**: step07_analysis.py는 T1 수정 대상. 본 보고서의 §6 개선 제안 [MED-3]은 T1 merge 이후 적용 권장.

### 5-2. F-13/F-14/F-15 — UI Live Progress

- **현재 코드** `orchestrator.py:392~408`: `StatusEmitter` 초기화 + `orchestrator.py:1351~1419`: `_execute_step()` 내 `emitter.update_step()` 호출
- **상태**: Tier 2 fix로 구현 완료 ✅
- **잔여 위험**: `_STATUS_EMITTER_AVAILABLE` 플래그가 모듈 임포트 시 결정되어 런타임 토글 불가 → [LOW-7] 참조

### 5-3. §검증 4건

| ID | 위치 | 검증 필요 사항 |
|----|------|-------------|
| VR-cycle-10 | `step06_rosetta.py:467` `_get_reference_peptide_com()` | ref_paths 중 첫 번째만 존재 확인 — 추가 경로 필요 여부 |
| VR-cycle-11 | `orchestrator.py:933` anonymous class | StepResult 교체 후 하위 코드에서 `.success`, `.output` 접근 동작 확인 |
| VR-cycle-12 | `step07_analysis.py:325` BSA 추정 공식 | `float(len(contact_rec) * 25)` — 과학적 근거 검토 (reviewer-biology) |
| VR-cycle-13 | `orchestrator.py:1209` 하드코딩 서열 | `config`에서 읽도록 변경 후 테스트 영향 범위 |

### 5-4. R5 (ref_paths DRY) 현황

- 커밋 `680f19a`에서 `_build_ref_paths` 추출 언급됨
- **현재 코드 확인**: `step06_rosetta.py:469~471` (get_reference_peptide_com)과 `step06_rosetta.py:600~601` (get_reference_complex_path)에 동일한 경로 목록이 별도 존재 → **부분 적용** (MED 수준 잔여)

### 5-5. R1 — mmCIF 변환 (CRIT-1)

- `step06_rosetta.py:494~519` `_cif_to_pdb()` 구현 완료
- `step06_rosetta.py:544~550` `_assemble_complex()` 상단에 mmCIF 감지 후 변환 추가
- 회귀 테스트: `test_tier1_rosetta_fixes.py:30~89` ✅
- **잔여 이슈**: `_cif_to_pdb()` 실패 시 원본 텍스트 반환 (fail-soft) — 실패 시 후속 ATOM 파싱이 잘못된 결과 산출 가능 → [MED-6]

---

## §6 개선 후보 목록 (10~20건)

---

### [CRIT-1] `run_single_iteration()` 561줄 God Function 분해

- **위치**: `orchestrator.py:533~1093`
- **현재 상태**: Approach A / Approach B / 듀얼 사일로 분기 + 6개 에이전트 호출 + 게이트 통계 캡처 모두 1함수
- **제안**: 
  1. `_build_sequences(iteration, step01_out) -> Step03Output` 추출 (분기 로직)
  2. `_run_quality_gates(step03_out, step01_out) -> Tuple[List[QCResult], Step05Output]` 추출
  3. `_run_refinement(docking_top, step01_out, step03b_out) -> Tuple[Step06Output, List[RosettaResult]]` 추출
  4. `_run_analysis_and_agents(step06_out, ...)` 추출
- **추정 공수**: L (3~5일)
- **의존성**: [CRIT-3] locals() 제거 선행 필요

---

### [CRIT-2] `locals().get("step03b_out")` + 익명 클래스 Anti-Pattern 제거

- **위치**: `orchestrator.py:910`, `orchestrator.py:933`
- **현재 상태**:
  ```python
  # 910
  step03b_out_local = locals().get("step03b_out")
  # 933
  step06_result = type('R', (), {'success': True, 'output': Step06Output(rosetta_results=[])})()`
  ```
- **제안**:
  - `run_single_iteration`에서 `step03b_out`을 명시적 변수로 선언 및 전달
  - 익명 클래스를 `StepResult(step_name="step06_rosetta", success=True, output=Step06Output(rosetta_results=[]))` 로 교체
- **추정 공수**: S (1~2시간)
- **의존성**: 없음 (즉시 적용 가능)

---

### [CRIT-3] SST-14 원본 서열 하드코딩 제거

- **위치**: `orchestrator.py:1209`
  ```python
  original_sequence="AGCKNFFWKTFTSC",  # SST-14
  ```
- **현재 상태**: config에서 읽어야 하는 값이 코드에 직접 기재
- **제안**: `pipeline_config_local.yaml`에 `peptide.reference_sequence: "AGCKNFFWKTFTSC"` 추가 후 `self.config.get("peptide", {}).get("reference_sequence", "AGCKNFFWKTFTSC")` 로 변경
- **추정 공수**: S (1시간)
- **의존성**: config 파일 변경 → 관련 테스트 검토 필요

---

### [HIGH-1] `sys.path` 뮤테이션 중앙화

- **위치**: `orchestrator.py:65`, `run_pipeline_local.py:45`, `backend/state.py:36`, 테스트 4개 파일
- **현재 상태**: `sys.path.insert(0, ...)` 로직이 8개 파일에 분산 — 순서 의존 버그 위험
- **제안**: `pipeline_local/core/path_setup.py` 단일 모듈 생성
  ```python
  def ensure_ag_src_on_path() -> None:
      """AG_SRC_REPO를 sys.path에 1회만 삽입한다."""
  ```
  → 모든 진입점에서 `from pipeline_local.core.path_setup import ensure_ag_src_on_path; ensure_ag_src_on_path()` 호출
- **추정 공수**: S (2~3시간)
- **의존성**: 없음

---

### [HIGH-2] `_write_status()` 내 `_STEP_PROGRESS` 외부화

- **위치**: `orchestrator.py:1797~1821`
- **현재 상태**: `_STEP_PROGRESS` dict가 메서드 내부에 정의되어 **매 호출마다** 생성 (UI 폴링이 2초 간격이므로 반복 비용 있음)
- **제안**: 클래스 수준 상수 `_STEP_PROGRESS: ClassVar[Dict[str, float]]` 로 이동
- **추정 공수**: S (30분)
- **의존성**: 없음

---

### [HIGH-3] `_get_reference_peptide_com()` + `_get_reference_complex_path()` DRY 통합

- **위치**: `step06_rosetta.py:467~491`, `step06_rosetta.py:598~606`
- **현재 상태**: 동일한 `ref_paths` 목록(PRST_N_FM/data/fold_test1/...)이 두 함수에 각각 선언
- **제안**: 
  ```python
  _REF_COMPLEX_PATHS: List[Path] = [
      Path(__file__).parent.parent.parent / "PRST_N_FM" / "data" / "fold_test1" / "fold_test1_model_0.pdb",
  ]
  def _find_reference_complex() -> Optional[Path]: ...
  ```
  두 함수가 `_find_reference_complex()` 호출하도록 통합
- **추정 공수**: S (1~2시간)
- **의존성**: 기존 테스트(test_tier3_reference_complex_fix.py) 확인 필요

---

### [HIGH-4] `orchestrator.py` 에이전트 stub 분리

- **위치**: `orchestrator.py:1695~1771`
- **현재 상태**: `_invoke_agent_stub()` 내에 Planner/QCRanker/DiversityManager/Critic/Reporter 5개의 rule-based 로직이 elif 체인
- **제안**: `pipeline_local/agents/stubs.py` 모듈로 분리하여 dict-of-callables 또는 Strategy 패턴 적용
  ```python
  _STUBS: Dict[str, Callable] = {
      "planner": _stub_planner,
      "qc_ranker": _stub_qc_ranker,
      ...
  }
  ```
- **추정 공수**: M (반나절)
- **의존성**: [CRIT-1] 이후 작업 권장

---

### [HIGH-5] `step04_qc.py` 배치/개별 fallback 내 게이트 로직 중복 제거

- **위치**: `step04_qc.py:157~223` (배치 결과 후처리) vs `step04_qc.py:263~330` (`predict_and_evaluate`)
- **현재 상태**: pLDDT 게이트 + 이황화결합 게이트 판정이 두 코드 경로에 각각 구현
- **제안**: `_apply_gates_to_qc_result(pdb_text, entry, ...) -> QCResult` 헬퍼 추출 후 양쪽에서 호출
- **추정 공수**: M (2~3시간)
- **의존성**: step04 단독 테스트 없으므로 리팩토링 전 테스트 먼저 작성 권장

---

### [HIGH-6] `is_pyrosetta_available()` 함수 속성 캐시 → `functools.lru_cache` 전환

- **위치**: `step06_rosetta.py:142~162`
  ```python
  if hasattr(is_pyrosetta_available, "_cached"):
      return is_pyrosetta_available._cached
  ```
- **현재 상태**: 함수 속성 남용 — 표준 패턴 아님, mypy/pylint 경고 유발
- **제안**: `@functools.lru_cache(maxsize=None)` 데코레이터 적용
- **추정 공수**: S (15분)
- **의존성**: 없음

---

### [HIGH-7] `orchestrator.py` 에이전트 임포트 의존성 격리 (테스트 가능성)

- **위치**: `orchestrator.py:142~157`
- **현재 상태**: `from AG_src.agents.base_agent import BaseAgent` 등 7개 직접 임포트 → 단위 테스트 시 AG_src 전체 필요
- **제안**: `Protocol` 또는 `ABC` 기반 인터페이스 정의 → 테스트에서 mock 주입 가능
  ```python
  class IAgent(Protocol):
      def execute(self, context: Dict[str, Any]) -> Dict[str, Any]: ...
  ```
- **추정 공수**: M (1일)
- **의존성**: [CRIT-1] 이후

---

### [MED-1] `step05b_selectivity.py` 내 dataclass 재정의 제거

- **위치**: `step05b_selectivity.py:75~103`
  ```python
  except ImportError:
      class OffTargetDockingResult: ...
      class SelectivityResult: ...
  ```
- **현재 상태**: `io_schemas.py`와 동일 구조의 클래스가 fallback으로 재정의 — 두 정의가 다를 경우 타입 혼용
- **제안**: `io_schemas.py`를 항상 임포트되도록 의존성 정리, fallback 클래스 제거
- **추정 공수**: S (2시간)
- **의존성**: step05b 단위 테스트 필요

---

### [MED-2] `step06_rosetta.py` 내 `import shutil` 루프 외부 이동

- **위치**: `step06_rosetta.py:255`
  ```python
  import shutil
  shutil.copy(result.refined_pdb, refined_path)
  ```
- **제안**: 파일 최상단 import 블록에 `import shutil` 추가
- **추정 공수**: S (5분)
- **의존성**: 없음

---

### [MED-3] `step07_analysis.py` F-05 fix 후 `FoldMasonResult.skipped` 필드 추가 (T1 연동)

- **위치**: `step07_analysis.py:65~76`, T1 fix 이후
- **현재 상태**: `FoldMasonResult`에 `skipped` 필드 없음 → `test_step07_foldmason_n_check.py`의 `result.skipped`가 AttributeError 발생
- **제안**: T1 fix 적용 시 dataclass에 `skipped: bool = False` 추가
- **추정 공수**: S (30분)
- **의존성**: T1 fix 선행 필요

---

### [MED-4] `_write_status()` 함수 책임 분리

- **위치**: `orchestrator.py:1777~1913`
- **현재 상태**: 138줄, 진행률 계산 + payload 조립 + steps/agents/qc_gates 목록 빌딩 + 파일 쓰기를 모두 수행
- **제안**: 
  - `_build_status_payload(phase, iteration, ...) -> Dict` — 순수 함수
  - `_write_status(phase, ...)` — payload 조립 후 파일 쓰기만 담당
- **추정 공수**: M (2~3시간)
- **의존성**: [HIGH-2] 이후 권장

---

### [MED-5] 일본어 주석 제거

- **위치**: `step06_rosetta.py:614`
  ```python
  def _run_pyrosetta_subprocess(...):
      """conda run -n bio-tools で PyRosetta スクリプトを実行する."""
  ```
- **제안**: "conda bio-tools 환경에서 PyRosetta 스크립트를 실행한다." 로 변경
- **추정 공수**: S (5분)
- **의존성**: 없음

---

### [MED-6] `_cif_to_pdb()` fail-soft 처리 강화

- **위치**: `step06_rosetta.py:517~518`
  ```python
  except Exception as exc:
      logger.warning("[Step06] mmCIF→PDB 변환 실패 (%s), 원본 반환", exc)
      return cif_text
  ```
- **현재 상태**: 변환 실패 시 mmCIF 원본을 PDB로 반환 → 후속 ATOM 파싱에서 잘못된 결과
- **제안**: 변환 실패 시 `RosettaResult`의 fallback stub으로 직접 반환하거나 `raise` 후 상위에서 처리하도록 수정
- **추정 공수**: M (2시간)
- **의존성**: test_tier1_rosetta_fixes.py에 실패 케이스 추가 필요

---

### [LOW-1] `orchestrator.py` 내 `interface` pLDDT 기본값 중복

- **위치**: `orchestrator.py:659` (`stability_prescreen_min_hours: 50.0`) vs `gate_thresholds.yaml:49` 동일 값
- **제안**: config 파일 값을 단일 소스로 사용, 코드 내 기본값 제거
- **추정 공수**: S (30분)

---

### [LOW-2] `_invoke_agent_stub()` Critic 하드코딩 메시지 외부화

- **위치**: `orchestrator.py:1729~1741`
  ```python
  "Increase diffusion steps to 100 and hotspot weight to improve binding."
  ```
- **제안**: `pipeline_config_local.yaml`의 `critic_stub_messages` 섹션에서 로드
- **추정 공수**: S (1시간)

---

### [LOW-3] `test_tier1_rosetta_fixes.py` Stage 9 아티팩트 의존 해소

- **위치**: `test_tier1_rosetta_fixes.py:42~49`
- **현재 상태**: `runs_local/dogfood_2026-05-11/...` 실 아티팩트가 없으면 pytest.skip — CI에서 항상 skip
- **제안**: 최소한의 synthetic mmCIF fixture 생성하여 F1 회귀를 아티팩트 없이 검증 가능하도록
- **추정 공수**: M (반나절)

---

### [LOW-4] orchestrator.py 단위 테스트 추가 (최우선)

- **위치**: 신규 파일 `tests/test_orchestrator.py`
- **현재 상태**: 2226줄, 33 함수 중 **테스트 0개**
- **제안 테스트 케이스**:
  1. `_check_convergence()` — 수렴 조건 경계값 (patience=2, delta=0.5)
  2. `_aggregate_best_candidates()` — ddG 정렬, 최대 10개 제한
  3. `_get_step_id()` — step_name 매핑
  4. `_invoke_agent_stub()` — 에이전트별 반환값 검증
  5. `_apply_parameter_updates()` — config 변경 반영
- **추정 공수**: M (1일)

---

### [LOW-5] `core/local_runner.py` 단위 테스트 추가

- **위치**: 신규 파일 `tests/test_local_runner.py`
- **현재 상태**: `LocalModelRunner` 클래스 테스트 없음 — subprocess 실패 시 동작 미검증
- **추정 공수**: M (반나절)

---

## §7 로드맵

### 1-Week (즉시 적용 — 공수 S 위주)

| 우선순위 | 항목 | 공수 | 기대 효과 |
|---------|------|------|---------|
| 1 | [CRIT-2] `locals()` + 익명 클래스 제거 | S | 버그 잠재성 즉시 제거 |
| 2 | [HIGH-2] `_STEP_PROGRESS` 상수화 | S | 성능 + 가독성 |
| 3 | [MED-2] `import shutil` 이동 | S | PEP 8 준수 |
| 4 | [MED-5] 일본어 주석 한국어 교체 | S | 코드베이스 일관성 |
| 5 | [HIGH-6] `functools.lru_cache` 적용 | S | 표준 패턴 준수 |
| 6 | [CRIT-3] SST-14 서열 config 이동 | S | 하드코딩 제거 |
| 7 | T1 완료 후 [MED-3] `skipped` 필드 추가 | S | F-05 테스트 통과 |

### 1-Month (구조 개선 — 공수 M 위주)

| 우선순위 | 항목 | 공수 | 기대 효과 |
|---------|------|------|---------|
| 1 | [HIGH-1] sys.path 중앙화 | S | 로드 순서 버그 차단 |
| 2 | [HIGH-3] ref_paths DRY 통합 | S~M | 유지보수성 향상 |
| 3 | [MED-1] step05b 재정의 제거 | M | 타입 혼용 방지 |
| 4 | [HIGH-4] stub 분리 (`agents/stubs.py`) | M | 테스트 가능성 향상 |
| 5 | [LOW-4] `tests/test_orchestrator.py` 신설 | M | orchestrator 커버리지 0% → 30% |
| 6 | [MED-4] `_write_status()` 분리 | M | 단일 책임 준수 |
| 7 | [MED-6] `_cif_to_pdb()` 오류 처리 강화 | M | 무언의 실패 방지 |

### 1-Quarter (대규모 리팩토링 — 공수 L)

| 우선순위 | 항목 | 공수 | 기대 효과 |
|---------|------|------|---------|
| 1 | [CRIT-1] `run_single_iteration()` 561줄 분해 | L | 가독성, 테스트 가능성 극적 개선 |
| 2 | [HIGH-7] 에이전트 인터페이스 격리 (Protocol/ABC) | L | orchestrator 단위 테스트 가능 |
| 3 | [LOW-3] Stage 9 아티팩트 의존 테스트 synthetic fixture 전환 | M | CI에서 F1 회귀 테스트 가능 |
| 4 | [LOW-5] `core/local_runner.py` 테스트 신설 | M | 로컬 모델 실행 안정성 검증 |
| 5 | 전체 커버리지 25% → 60% 목표 | L | 다음 분기 기능 개발 안전망 |

---

## §A 신뢰 등급 요약

- **HIGH** (코드 직접 확인): §2, §3, §5 전체, §6 모든 항목
- **MED** (추론): 커버리지 추정(§4-1), [LOW-2] 외부화 효과
- **LOW** (가정): 없음

---

*본 보고서는 orchestrator.py T1 fix 브랜치(`fix/tier3-followup-cleanup`) 기준으로 작성됨.*  
*T1 fix(step07_analysis.py 변경) 완료 후 §5-1 및 [MED-3] 사항을 재검토 바람.*
