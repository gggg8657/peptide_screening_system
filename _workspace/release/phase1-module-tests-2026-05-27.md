# Phase 1 — 모듈 단위 테스트 (회귀 baseline)

> **점검일**: 2026-05-27 (D-1) — **재실행 갱신 12:14 KST** (SSTR2 symlink 적용 + vLLM 가동 후)
> **대상**: `pipeline_local/tests/`, `pipelines/silo_a/tests/`, `pipelines/silo_b/tests/`
> **범위**: 단위 + 모듈 통합 + 일부 Boltz 실 호출 (SSTR2 PDB 활성화 후)
> **GPU 정책**: `CUDA_VISIBLE_DEVICES=2,3` (본인 가용). GPU 0/1은 타인 점유로 손대지 않음
> **부수 서비스**: vLLM `deepseek-r1-distill-32b` GPU 3 / port 8002 가동
> **컨텍스트**: 시스템 전체 점검 Phase 0~5 중 Phase 1 단계

---

## 1. 환경

| 항목 | 값 |
|------|------|
| 호스트 | dongjukim (Linux 6.8.0-58-generic) |
| Python | 3.11.15 |
| conda env | `bio-tools` (테스트), `vllm-server` (별도 부수 서비스) |
| PyRosetta | ✓ |
| Biopython | 1.79 |
| rdkit | 2025.03.6 |
| torch | 2.10.0+cu128 |
| transformers | 4.57.6 |
| FastAPI | 0.135.2 |
| pytest | 9.0.2 |
| PyMOL | `/home/dongjukim/miniforge3/envs/bio-tools/bin/pymol` |
| GPU 가시 | H100 NVL ×4 (본인 가용 GPU 2, 3) |

**활성화 명령** (회귀 검증 시):
```bash
source /home/dongjukim/miniforge3/etc/profile.d/conda.sh && conda activate bio-tools
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
export CUDA_VISIBLE_DEVICES=2,3
```

---

## 2. 종합 결과

| 컴포넌트 | 결과 | 시간 | 이전 (5/27 09:30) 대비 |
|---------|------|------|------|
| `pipeline_local` | **740 PASS / 1 skip / 2 xfail / 0 fail** | 199.3 s | **+4 PASS, -4 skip** (SSTR2 symlink로 4건 해제, Boltz 실 호출 발생) |
| `pipelines/silo_a` | **9 PASS** / 0 | 0.20 s | 동일 |
| `pipelines/silo_b` | **32 PASS** / 0 (Pydantic 경고 82건) | 0.61 s | 동일 |
| **총합** | **781 PASS / 0 fail / 0 error** | ~200 s | **+4 PASS (777 → 781)** |

**5/20 STATUS → 5/27 변화**: 그때 "589 PASS / 8 FAIL / 12 ERROR / 15 skip" → 본 시점 **781 PASS / 0 fail / 0 error / 1 skip**. fail/error 20건 + skip 14건 정리.

**시간 199 s로 늘어남**: SSTR2 PDB 활성화로 `test_offtarget_dock_boltz.py`의 Boltz 실 호출 4건이 실행됨 (단순 모듈 단위가 아니라 일부 GPU 호출 포함). 본 phase1은 이제 "모듈 단위 + 일부 외부 도구 통합" 수준이다.

---

## 3. 남은 1 skip + 2 xfail — 사유 명시 (모두 정당)

### 3.1 SKIPPED 1건

**`pipeline_local/tests/test_flexpep_dock_wrapper.py:242`**
> "SSTR2.pdb가 이미 생성되어 있음 — 변환 테스트 불필요"

→ **의도적 skip**. 변환 입력 fixture가 이미 결과물로 존재할 때 변환을 다시 시도하지 않는다. 코드 정합.

### 3.2 XFAIL 2건 (알려진 결함, 향후 작업으로 등록됨)

**`test_stability_predictor.py::TestModificationConflict::test_daa_dota_conflict_detected`**
> "D-AA + DOTA 충돌 미탐지 (High 결함). modification_conflict.py 통합 필요."

→ **알려진 결함**. D-AA(분해 저항)와 DOTA(킬레이터) 동시 적용 시 화학적 호환성 충돌을 현재 stability_predictor가 탐지하지 못한다. `pipeline_local/scoring/modification_conflict.py`가 별도 모듈로 존재하지만 stability_predictor에서 호출 미통합. **Phase 5 P0 또는 P1 항목.**

**`test_stability_predictor.py::TestBatchMode::test_batch_compute_exists`**
> "batch_compute_stability 함수 없음 — 10 후보 루프에서 compute_stability를 개별 호출하는 방식도 허용"

→ **알려진 부재**. 배치 모드 API가 없으나, 개별 호출이 정상 작동하므로 의도된 xfail. 성능 최적화 항목이며 정확성 영향 없음. **Phase 5 P3 항목.**

---

## 4. 이번 갱신에서 적용한 변경 — 코드 수정 없이 데이터만

### 4.1 SSTR2 PDB symlink (Phase 1 직접 실행 시 4 skip 해제 목적)

`pipeline_local/tests/test_offtarget_dock_boltz.py:49`가 다음 세 경로 중 하나에 SSTR2 구조 PDB를 요구:
1. `runs_local/selectivity_demo_20260511/alphafold_receptors/SSTR2.pdb`
2. `runs_local/selectivity_demo_20260511/alphafold_receptors/AF-P30874-F1-model_v4.pdb`
3. `runs_local/selectivity_demo_20260511/alphafold_receptors/sstr2.pdb`

해당 디렉토리에는 **`AF-P30874-F1-model.pdb`** 만 존재 (`_v4` suffix 없음). AF-P30874는 SSTR2의 UniProt ID이므로 같은 파일에 alias 추가:

```bash
cd runs_local/selectivity_demo_20260511/alphafold_receptors
ln -sf AF-P30874-F1-model.pdb SSTR2.pdb
ln -sf AF-P30874-F1-model.pdb AF-P30874-F1-model_v4.pdb
ln -sf AF-P30874-F1-model.pdb sstr2.pdb
```

**효과**: 4 skip → 4 PASS (Boltz 단건 실 호출 포함). 코드 수정 0 라인.

### 4.2 vLLM 가동 (GPU 3, port 8002)

`pipeline_local`의 Planner agent가 LLM 호출 시 `http://localhost:8002`를 찾는다 (이전에 Phase 2 dual silo smoke에서 `Connection refused` 발생). 5/28 시연 + 향후 pipeline 실행을 위해 가동:

```bash
MODEL_PATH="$HOME/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-32B/snapshots/711ad2ea6aa40cfca18895e8aca02ab92df1a746"
CUDA_VISIBLE_DEVICES=3 conda run --no-capture-output -n vllm-server \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "deepseek-r1-distill-32b" \
    --host 127.0.0.1 --port 8002 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.85 \
    --dtype bfloat16 \
  > /tmp/vllm_8002.log 2>&1 &
```

**상태 검증**:
- `/health` → HTTP 200 (응답 6 ms)
- `/v1/models` → `{"id": "deepseek-r1-distill-32b", "owned_by": "vllm"}`
- GPU 3 점유 83467 MiB / 95830 MiB
- 모델 로드 시간 약 3분 (32B bfloat16)

**pytest 영향**: 본 phase1 단위 테스트는 vLLM 호출 안 함. 영향 0. 그러나 Phase 2 dual silo smoke 또는 5/28 시연 시 Planner agent가 정상 동작하도록 사전 가동.

---

## 5. 컴포넌트별 상세

### 5.1 `pipeline_local/tests/` — 통합 BE (38 test 파일)

**명령**
```bash
python3 -m pytest pipeline_local/tests/ --tb=line -rsxX -q --no-header
```

**결과**
```
740 passed, 1 skipped, 2 xfailed, 15 warnings in 199.31s (0:03:19)
```

**시간 증가 원인**: SSTR2 PDB 활성화 후 `test_offtarget_dock_boltz.py`의 Boltz 실 호출 4건 (각 약 30-40초). 이제 본 phase1은 단위 + 일부 GPU 통합 테스트의 hybrid.

### 5.2 `pipelines/silo_a/tests/` — 3-Arm SSTR2 virtual screening

**명령**
```bash
python3 -m pytest pipelines/silo_a/tests/ --tb=line -rsxX -q --no-header
```

**결과**
```
9 passed in 0.20s
```

**구성**: `unit/` + `integration/` 하위. 실 NIM API 호출은 미실시 (NGC API key 부재 — 향후 Phase 5 P2 항목: NIM mock client 도입).

### 5.3 `pipelines/silo_b/tests/` — HIL SST-14 mutant generation

**명령**
```bash
python3 -m pytest pipelines/silo_b/tests/ --tb=line -rsxX -q --no-header
```

**결과**
```
32 passed, 82 warnings in 0.61s
```

테스트 파일: `test_config.py`, `test_constraint_compiler.py`, `test_filters.py`, `test_generator.py`, `test_orchestrator.py`, `test_relax.py`, `test_scoring.py`

---

## 6. 경고 분석

### 6.1 Pydantic v2 deprecation — 82건 (Silo B)

**위치**:
- `pipelines/silo_b/src/config.py:460, 472` — class-based `config` deprecated
- `pipelines/silo_b/src/config.py:492` — `obj.dict()` deprecated → `model_dump()` 권장
- `pipelines/silo_b/src/constraint_compiler.py:60, 108` — `rule.dict()` deprecated (30회 호출)

**정책**: Pydantic V3.0에서 제거 예정. 현재 기능 영향 없음.
**처리 권고**: Phase 5 §5.2 P2 항목 — `class Config` → `ConfigDict`, `.dict()` → `.model_dump()` (추정 1시간).

### 6.2 NCAA(Non-Canonical Amino Acid) 치환 경고 — 7건 (pipeline_local)

**위치**: `pipeline_local/scripts/stability_predictor/__init__.py:547`

D-Threonine `[dT]`, Cyclohexylalanine `[Cha]`, 2-Naphthylalanine `[2Nal]`, unknown `[XYZ123]` 등 입력 시 canonical AA로 fallback함을 사용자에게 명시. **H-06 가드 정책의 정직성 장치**. 처리 불필요.

### 6.3 PyTorch deprecation — 3건

- `pynvml deprecated` (torch 2.10 자동 import, 본 리포 무관)
- `torch.jit.script deprecated` (외부 의존 — pepMSND 또는 ESMFold)

---

## 7. 회귀 baseline (다음 세션 검증 명령)

```bash
# 환경
source /home/dongjukim/miniforge3/etc/profile.d/conda.sh && conda activate bio-tools
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
export CUDA_VISIBLE_DEVICES=2,3

# 세 컴포넌트 한꺼번에
python3 -m pytest \
  pipeline_local/tests/ \
  pipelines/silo_a/tests/ \
  pipelines/silo_b/tests/ \
  --tb=no -rsxX -q --no-header

# 기대 출력
# 781 passed, 1 skipped, 2 xfailed, 99 warnings in ~200s
```

**검증 게이트**:
- 781 PASS 유지 (감소 시 회귀, 증가 시 신규 테스트 — 정상)
- 0 fail / 0 error
- skip 1 (의도적), xfail 2 (알려진 결함, 작업 등록됨)
- Pydantic 경고 ≤ 82 (감소 = 마이그레이션 진척)

---

## 8. BE P0 fix (PR #122 → main `fc5e15b`) 적용 후 회귀

본 phase1 baseline 작성 후 BE P0 fix가 PR #122로 main에 머지됨 (`fc5e15b`). 변경 후 pipeline_local pytest 재검증:

- **회귀 없음 확인** (`pipeline_local` 740 PASS 유지, BE 코드와 분리).
- BE 부팅 가능 상태 (`/api/health` 응답 `service: "ai4sci-kaeri-backend"`).

자세한 fix 내용: `_workspace/release/be-p0-fix-2026-05-27.md`

---

## 9. 한 줄 결론

`pipeline_local` 740 + Silo A 9 + Silo B 32 = **781 PASS / 0 fail / 0 error**. SSTR2 PDB symlink로 4 skip 해제 + vLLM 가동까지 5/28 시연 환경 준비 완료. 남은 1 skip은 의도적, 2 xfail은 알려진 결함으로 작업 등록됨.

---

## 10. 다음 단계 권고

| 우선순위 | 항목 | 분담 | 산출 |
|---------|------|------|------|
| **P0** | `modification_conflict.py`를 stability_predictor에 통합 | engineer-backend | XFAIL → PASS (D-AA+DOTA 충돌 탐지) |
| P1 (4주) | Silo B Pydantic v2 마이그레이션 | codex | 경고 82 → 0 |
| P2 (8주) | `batch_compute_stability` 함수 신설 (또는 xfail 영구 등록) | engineer-backend | XFAIL → PASS 또는 deprecated 정리 |
| P2 (8주) | NCAA 처리 로직 별도 모듈 분리 | engineer-backend | §6.2 경고 의도 명확화 |
| P2 (8주) | Silo A NIM mock client 도입 (NGC API key 없이 E2E) | engineer-backend | Silo A 9 → 20+ |
| P3 (미정) | pytest suite 단일화 (CI 시간 단축) | engineer-infra | 통합 명령 |

Phase 4 `phase4-code-audit-refactor.md` §5 리팩토링 일정과 정합.

---

## 부록 A. SSTR2 symlink 영구성

본 phase1에서 만든 symlink 3개:
- `runs_local/selectivity_demo_20260511/alphafold_receptors/SSTR2.pdb` → `AF-P30874-F1-model.pdb`
- `runs_local/selectivity_demo_20260511/alphafold_receptors/AF-P30874-F1-model_v4.pdb` → 동일
- `runs_local/selectivity_demo_20260511/alphafold_receptors/sstr2.pdb` → 동일

**git 상태**: `.gitignore` 갱신(다른 세션, "Max-retention")으로 `runs_local/` 전체 track 정책이 되어, 이 symlink들은 다음 commit 시 git에 포함될 가능성 있음. 본 phase1 보고서가 그 부수효과를 기록.

**대안 (코드 수정 시)**: `test_offtarget_dock_boltz.py`의 `_SSTR2_PDB_CANDIDATES`에 `data/somatostatin_receptor/SSTR2_7XNA.pdb` 또는 `AF-P30874-F1-model.pdb` 추가. 본 phase1 범위 밖.

---

## 부록 B. vLLM 가동 명령 (재가동 필요 시)

```bash
MODEL_PATH="$HOME/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-32B/snapshots/711ad2ea6aa40cfca18895e8aca02ab92df1a746"
CUDA_VISIBLE_DEVICES=3 nohup conda run --no-capture-output -n vllm-server \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "deepseek-r1-distill-32b" \
    --host 127.0.0.1 --port 8002 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.85 \
    --dtype bfloat16 \
  > /tmp/vllm_8002.log 2>&1 &
disown
```

종료: `pkill -f "vllm.entrypoints.openai.api_server.*port 8002"`

---

## 부록 C. 실행 진행률 (pipeline_local)

```
SKIPPED [1] pipeline_local/tests/test_flexpep_dock_wrapper.py:242: SSTR2.pdb가 이미 생성되어 있음 — 변환 테스트 불필요
XFAIL pipeline_local/tests/test_stability_predictor.py::TestModificationConflict::test_daa_dota_conflict_detected
XFAIL pipeline_local/tests/test_stability_predictor.py::TestBatchMode::test_batch_compute_exists
740 passed, 1 skipped, 2 xfailed, 15 warnings in 199.31s (0:03:19)
```

---

## 부록 D. 참고 문서

- 본 phase1의 후속 Phase: `phase2-dual-silo-smoke-2026-05-27.md` / `phase3-ui-ux-2026-05-27.md`
- Phase 4 다관점 분석: `phase4-{pharma,code,uiux,integration-and-refactor-plan}.md`
- 5/20 STATUS 비교 기준: `docs/meet_log/2026-04-06_action_items/STATUS_2026-05-20.md`
- BE P0 fix: `be-p0-fix-2026-05-27.md` (main `fc5e15b`로 머지됨)
- 본 세션 SSOT: `eod-2026-05-27-orchestrator-d1-system-audit.md`
