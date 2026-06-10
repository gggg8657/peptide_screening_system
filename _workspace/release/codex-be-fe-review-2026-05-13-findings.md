# Codex BE/FE 전체 리뷰 발견 사항 (raw 보존)

**작성**: orchestrator-session, 2026-05-13
**호출**: `./scripts/agent-wrapper.sh codex exec '지금 BE FE 코드를 전부 다 검토하고 디테일하게 분석하고 분석 보고를 해라.'`
**모델**: gpt-5.4 (research preview, Codex CLI 0.118.0)
**소요**: 218초, 156,134 tokens
**로그**: `logs/external_agents/codex_20260513_110724_365423.jsonl`

---

## 검증 환경
- workdir: `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri`
- approval: never, sandbox: danger-full-access
- frontend: `npm run build` ✓, `npm run lint` ✓, `npm test` 60 pass (act 경고 다수)
- backend: `pytest -q ...` → **74 passed / 4 skipped / 14 errors** (python-multipart 누락으로 selectivity router import 실패)

---

## P0 (Critical, 3건)

### C-P0-1 — Selectivity Stop이 서버 작업 안 멈춤
**증상**: FE polling만 중단, BE에 cancel endpoint 자체 없음
- `frontend/src/hooks/useSelectivity.ts:288-292` — `stoppedRef.current=true; stopPolling(); setIsRunning(false)`
- `backend/routers/selectivity.py:292-324` — `/selectivity/run`, `/status`, `/results`, `/jobs` 4개만, cancel 없음

**Codex 권장**: cancel endpoint 신규 추가

**정합성 검증 후 정정 (v2.1)**:
- soft cancel만 가능 (subprocess timeout 600s 대기)
- 즉시 cancel은 PID 노출 별도 sprint
- `_jobs` 변수명 (v2의 `_JOBS` 오기)

### C-P0-2 — Settings 화면이 실제 실행과 단절
**증상**: 저장은 runtime_settings 갱신만, 실험 실행은 하드코딩 default
- `backend/routers/settings.py:41-44` — `runtime_settings.update(updates)`
- `backend/routers/experiment.py:128-185` — DEFAULT_EXPERIMENT_CONFIG 사용, runtime_settings 미참조
- `backend/routers/experiment.py:177-186` — 실행 시 저장값 미참조

**정합성 검증 후 정정 (v2.1)**:
- `llm_provider/model/base_url`은 이미 폴백 구현됨 (line 263-291)
- **미구현은 `max_iterations/n_candidates/top_k` 3필드만**

### C-P0-3 — Silo A / Combined가 BE 미구현
**증상**: FE는 approach 보내지만 BE 무시
- `frontend/src/pages/SiloAPage.tsx:108-112` — `startExperiment({ approach: 'a', ... })`
- `frontend/src/pages/CombinedPage.tsx:176, 192-196` — `approach: 'dual'`
- `backend/routers/experiment.py:177-186` — `approach` 무시, `--planner-mode pyrosetta-only` 하드코딩

**정합성 검증 후 정정 (v2.1)**:
- **Silo A는 이미 구현됨** — `--no-approach-b` 플래그 분기
- **dual만 차단됨** — `ExperimentRunRequest.pattern=r"^[abAB]$"`
- 해결: regex 확장 (`r"^[abABdD]$"`) + `--dual` 매핑

---

## P1 (5건)

### C-P1-4 — Selectivity 진행률 BE/FE 가정 불일치
- `backend/routers/selectivity.py:310,280` — total_tasks = 후보수, completed_tasks += 1
- `frontend/src/hooks/useSelectivity.ts:175-180` — perReceptor = `Math.ceil(total / 4)` (후보 × 4 receptor 가정)

**해결**: 후보 단위 통일 또는 BE를 receptor 단위로 변경. UX 손실 검토 필요 (reviewer-uiux: BE가 receptor 단위 카운트 별도 제공이 근본 해법)

### C-P1-5 — off-target worst가 BE/FE 정반대
- BE `backend/routers/selectivity.py:255,266` — `min(scores)` (가장 음수 = 가장 강한 결합 = 가장 위험)
- FE `frontend/src/hooks/useSelectivity.ts:63-67` — `max` (가장 0에 가까운 = 가장 약한 결합)

**[가장 critical] 정합성 검증 발견**: BE는 이미 응답에 `offtarget_max_receptor`, `offtarget_max_score` 포함 (`selectivity.py:273-274`). FE가 이걸 무시하고 재계산. **1~2줄 수정으로 완결**.

### C-P1-6 — .pdb 업로드 받지만 조회는 .cif 하드코딩
- `backend/routers/selectivity.py:69-82` — `suffix = Path(file.filename).suffix.lower() or ".cif"`, 확장자 그대로 저장
- `backend/routers/selectivity.py:121-137` `_get_receptor_pdb` — `_RECEPTORS[*]['file']`의 `.cif`만 참조

**정합성 검증 후 정정 (v2.1)**:
- **pipeline_local 버전엔 이미 `_resolve_receptor_paths()`로 구현됨** (`.pdb > .cif > .mmcif`)
- ai4sci-kaeri 옛 selectivity.py에만 해당

### C-P1-7 — requirements.txt 의존성 누락
- `requirements.txt:1-14` — fastapi/uvicorn/pydantic/requests/pytest 5개만
- 누락: `python-multipart` (UploadFile용), `Biopython` (Bio.PDB 사용)
- 실제 pytest에서 selectivity router import 시 **14건 error**

**정합성 검증 후 정정 (v2.1)**:
- **conda env `bio-tools`엔 이미 설치됨**: python-multipart 0.0.22, biopython 1.79
- requirements.txt 추가는 환경 재구성 문서화 목적

### C-P1-8 — Experiment subprocess PIPE 미소비
- `backend/routers/experiment.py:194` — `subprocess.Popen(stdout=PIPE, stderr=PIPE)`, drain 없음
- OS pipe buffer (보통 64KB) fill 시 subprocess write block → watchdog `proc.wait()` 무한정 block

**해결 (engineer-backend 권장)**: `stdout=DEVNULL, stderr=DEVNULL`이 가장 단순/안전. daemon thread drain은 asyncio 혼용 위험.

---

## P2 (2건)

### C-P2-9 — Unified Validation 통계 검증이 placeholder
- `backend/unified_validation.py:308-315` — `rank_stability`, `score_consistency`, `no_dominance` 모두 `value=None, passed=True, skipped=True`
- `backend/unified_validation.py:160` 프리셋에 활성 항목으로 포함
- `frontend/src/components/ValidationPanel.tsx:218-246` — placeholder 그대로 렌더링

**정합성 검증 후 정정 (v2.1)**:
- `ValidationPanel.tsx:41-42`에서 `check.skipped`에 `MinusCircle` 처리는 이미 구현됨
- 결과 행 dot 시각화에는 skipped 제외 → 회색 dot 추가 필요

### C-P2-10 — FE 테스트 `act()` 경고
- 60 tests passed but React `act(...)` warnings
- 특히 `CandidateTable.tsx`, `ArchivesTopKSlider` 테스트가 비동기 상태 업데이트 검증 약함

**판정**: green test ≠ 회귀 방지력. 별도 트랙으로 정리 필요.

---

## Codex 종합 의견 (원문 인용)

> 코드베이스는 "PyRosetta 중심 Silo B"는 어느 정도 돌아가는 형태지만, FE가 보여주는 멀티-파이프라인/설정/선택성 제어 범위가 실제 BE 능력보다 넓습니다. 지금 상태에서 가장 먼저 정리해야 할 것은 `selectivity cancel/progress`, `settings-실행 연결`, `Silo A/Combined 기능 정합성`, `requirements 보강`입니다.

---

## 통합 v2.1과의 매핑

| Codex 발견 | v2.1 패치 | 정정 사항 |
|---|---|---|
| C-P0-1 | P11 | soft cancel만 가능, 변수명 `_jobs` |
| C-P0-2 | P09 | llm_* 이미 구현, max_iter/n_cand/top_k만 |
| C-P0-3 | P10 + G-5 | Silo A 활성 유지, dual만 regex 확장 |
| C-P1-4 | P13 | BE-FE 합의 필요 |
| C-P1-5 | P14 | BE 응답값 사용, 1~2줄 |
| C-P1-6 | P12 | pipeline_local 이미 구현, ai4sci-kaeri만 |
| C-P1-7 | P08 | conda env 설치됨, 문서화 |
| C-P1-8 | P08 | DEVNULL 권장 |
| C-P2-9 | P15 | 기존 처리 활용, dot 추가 |
| C-P2-10 | 별도 트랙 | green test 정리 |

---

## 참고 파일

- raw 출력 (11,183줄): `/tmp/claude-1010/.../tasks/bv01hmhga.output` (휘발성)
- wrapper 로그: `logs/external_agents/codex_20260513_110724_365423.jsonl`
- 통합 분석: `liverun-integration-analysis-v2-2026-05-13.md`
- 정합성 검증: `v2-validation-cross-check-2026-05-13.md`
