# M3 인프라 검증 보고서 — Step06~08 + 환경 + STATUS_FILE 분석
**작성**: engineer-infra | **날짜**: 2026-05-13 | **세션**: module-verification-2026-05-13

---

## 목차
1. [Step06 — PyRosetta 정밀 정제](#1-step06--pyrosetta-정밀-정제)
2. [Step07 — 구조 정렬/시각화](#2-step07--구조-정렬시각화)
3. [Step08 — 안정성 휴리스틱 + U1.5 통합 여부](#3-step08--안정성-휴리스틱--u15-통합-여부)
4. [Conda 환경 Health Matrix (10 envs)](#4-conda-환경-health-matrix-10-envs)
5. [STATUS_FILE 메커니즘 분석](#5-statusfile-메커니즘-분석)
6. [ARCHIVE_DIR 확장 권장](#6-archive_dir-확장-권장)
7. [결함 목록](#7-결함-목록)
8. [신규 기능 제안](#8-신규-기능-제안)
9. [종합 판정](#9-종합-판정)

---

## 1. Step06 — PyRosetta 정밀 정제

### 1.1 파일 개요
| 항목 | 값 |
|------|----|
| 경로 | `pipeline_local/steps/step06_rosetta.py` |
| LOC | 915 |
| conda env | `bio-tools` |
| PyTorch | 2.10.0+cu128 |

### 1.2 입출력 명세

**입력**
```
candidates: List[DockingResult]   # Step05 상위 M개 도킹 후보
receptor_pdb: str                 # 수용체 PDB 경로 (RECEPTOR_PDB env var)
config: Dict[str, Any]            # 파이프라인 설정 (gate_thresholds, rosetta, iteration)
```

**출력**
```
Step06Output:
  ├── results: List[RosettaResult]
  │     ├── seq_id, ddg (kcal/mol), total_score, clash_score
  │     ├── constraint_violations, refined_pdb (경로), pre_score, score_delta
  └── out_dir: 06_rosetta/
        ├── refined_{seq_id}.pdb   # 정제된 복합체 구조
        └── .rosetta_cache.json    # 디스크 캐시 사이드카
```

### 1.3 의존성 체인
```
step06_rosetta.py
├── pipeline_local.schemas.io_schemas (RosettaResult, Step06Output, DockingResult)
├── conda run -n bio-tools → PyRosetta (subprocess)
│     ├── FastRelax (cartesian)
│     ├── FlexPepDock
│     └── ddG calculation
├── Bio.PDB (mmCIF↔PDB 변환)
└── hashlib, tempfile, subprocess
```

### 1.4 캐시 키 설계 (`_ResultCache`)
```python
key = sha256(pdb_content || "\x00" || sequence || "\x00" || protocol)[:24]
# 메모리 캐시 (_mem dict) + 디스크 (.rosetta_cache.json)
# 재시작 시 기존 계산 결과 자동 복원
```

**평가**: ✅ 캐시 키가 pdb_content + sequence + protocol 3-tuple로 구성되어 
동일 입력에 대한 중복 계산을 방지함. 디스크 플러시 시 OSError 처리 있음.

### 1.5 mmCIF fallback 처리
- Boltz-2가 `.cif` 형식으로 출력 → `_cif_to_pdb()` 자동 변환
- `Bio.PDB.MMCIFParser + PDBIO` 사용
- 실패 시 원본 텍스트 그대로 전달 (warn 로깅)

### 1.6 절대값 신뢰성 문제 (⚠️ 주의)
- 실제 실행 로그: `"1/1 통과 (ddG ≤ -1.0)"` — 게이트 기준이 YAML에서 `-1.0`으로 완화됨
- 코드 상 기본값: `_DEFAULT_DDG_MAX = -5.0`, YAML 오버라이드 우선
- **결함 D-06-01**: gate_thresholds.yaml 값이 코드 기본값보다 완화된 상태로 운영 중

```
실제 STATUS_FILE 기록 (2026-05-12):
  step06_rosetta: 1/1 통과 (ddG ≤ -1.0)   ← 완화된 임계값
  top_ddg: -31.4863                         ← 실제 계산값 (신뢰 가능)
```

### 1.7 Stub 모드
```python
pyrosetta_ok = is_pyrosetta_available()  # subprocess probe (30s timeout, cached)
# 미설치 시 placeholder 점수 반환 (CI/dry-run용)
```

**검증 명령**
```bash
conda run -n bio-tools python -c "import pyrosetta; print('OK')"
```

---

## 2. Step07 — 구조 정렬/시각화

### 2.1 파일 개요
| 항목 | 값 |
|------|----|
| 경로 | `pipeline_local/steps/step07_analysis.py` |
| LOC | 625 |
| conda env | `bio-tools` |
| 외부 도구 | FoldMason (`foldmason`), PyMOL (`pymol`) |

### 2.2 입출력 명세

**입력**
```
candidates: List[RosettaResult]   # Step06 정제 결과
receptor_pdb: str                 # 수용체 PDB
config: Dict[str, Any]
```

**출력**
```
Step07Output:
  └── out_dir: 07_viz/
        ├── foldmason_report.html     # FoldMason 다중 구조 정렬 HTML
        ├── lddt_table.json           # lDDT 점수 dict (seq_id → float)
        ├── rank_table.csv            # ddG/clash/lDDT 종합 랭킹
        ├── summary.md                # 상위 3 후보 요약
        └── {overview,closeup,interface,electrostatics}.png
```

### 2.3 lDDT Gate 처리
```python
@dataclass
class FoldMasonResult:
    lddt_scores: Dict[str, float]  # seq_id → lDDT (0.0~1.0)
    skipped: bool = False          # n<2 일 때 True (정렬 불필요)
    success: bool
```

- FoldMason 실행 실패 → `skipped=True, success=False` (파이프라인 중단 없음)
- lDDT < 0.7 후보는 rank_table에 경고 표시 (게이트 차단 아님 — 리뷰 권장)

### 2.4 실제 실행 결과
```json
{"id": "step07", "status": "completed", "duration": "4.4s"}
```
**평가**: ✅ FoldMason 4.4초 완료. 단일 후보(n=1)로 정렬 스킵됨 (정상 동작).

### 2.5 PyMOL 렌더링 상태
- `pymol` 패키지: bio-tools 환경에 설치됨 (버전 확인: `from pymol import cmd`)
- 4개 뷰 (`overview, closeup, interface, electrostatics`) PNG 생성
- 렌더링 실패 시 skip 로그 후 계속 (CI에서 GUI 없을 때 graceful)

---

## 3. Step08 — 안정성 휴리스틱 + U1.5 통합 여부

### 3.1 파일 개요
| 항목 | 값 |
|------|----|
| 경로 | `pipeline_local/steps/step08_stability.py` |
| LOC | 636 |
| 의존성 | stdlib only (logging, math, dataclasses) |

### 3.2 입출력 명세

**입력**
```
candidates: List[DockingResult | RosettaResult]
config: Dict[str, Any]
  └── stability.min_half_life_hours: float (default: 144.0)
```

**출력**
```
List[StabilityResult]:
  ├── candidate_id: str
  ├── sequence: str
  ├── base_hl_hours: float        # 수정 전 휴리스틱 점수
  ├── modified_hl_hours: float    # 수정 후 점수
  ├── modifications: List[ModificationSuggestion]
  ├── target_met: bool            # modified_hl ≥ min_hl
  └── score: float (0.0~1.0)     # NSGA-II 입력용 정규화 점수
```

### 3.3 ⚠️ 정직한 명세 (VR-cycle-09 / H-06)

```
본 모듈은 휴리스틱 ranking score 전용.
임상 반감기 절대값 예측 ≠ 본 모듈 출력.
```

**허용 용도**
- ✅ 후보 펩타이드 상대 순위 부여 (NSGA-II 목적함수 입력)
- ✅ modification 제안의 우선순위 결정

**금지 용도**
- ❌ 임상 반감기 절대값 보고
- ❌ wet-lab 결과 대체

### 3.4 휴리스틱 계산 흐름

```
1. base_hl = 3.0h (선형 펩타이드 기준)
2. avg_vulnerability = Σ(_PROTEASE_VULNERABILITY[aa]) / len(seq)
3. vulnerability_factor = exp(-0.5 × (avg_vulnerability - 1.0))
4. intrinsic_hl = base_hl × vulnerability_factor
5. Cys 쌍 검출 (≥2개, 간격≥4) → cyclization 감지
6. penalty_factor = max(0.2, 1.0 - 0.10×(R+K) - 0.08×Met - ...)
7. adjusted_hl = intrinsic_hl × penalty_factor
8. ext_mod_bonus = 수정 유형별 가산 (fatty_acid:+120h, peg:+96h, d_aa:+48h, ...)
9. final_hl = max(0.0, adjusted_hl + ext_mod_bonus)
```

### 3.5 stability_predictor U1.5 통합 여부

**현황**: **미통합** (독립 구현)

```python
# step08_stability.py는 stdlib만 사용
# stability_predictor 패키지 참조 없음
# _compute_stability_score는 step08 내부 함수로 자체 구현
```

**결론**: step08과 stability_predictor(U1.5)는 **병렬 존재**하는 두 구현체.

| 항목 | step08_stability.py | stability_predictor (U1.5) |
|------|---------------------|---------------------------|
| 위치 | `pipeline_local/steps/` | `pipeline_local/scripts/stability_predictor/` |
| 의존성 | stdlib only | biopython + peptides.py 선택적 |
| Silo 지원 | 없음 (공통) | Silo A / Silo B 분리 |
| NCAA 지원 | 없음 | ✅ ([dT]→T, [Cha]→L, ...) |
| is_unstable 필드 | ✅ | ✅ |
| 테스트 | 없음 (step08 단독) | 42개 (28 pass, 10 skip) |
| 파이프라인 호출 | orchestrator.py에서 직접 호출 | 아직 미통합 |

**권장**: step08을 stability_predictor U1.5의 `core.hl_score_heuristic()`으로 교체하면
NCAA 지원 + Silo 분리 + 테스트 커버리지 획득 가능. 단, 결과 수치 동등성 검증 필요.

---

## 4. Conda 환경 Health Matrix (10 envs)

### 4.1 Python 버전 + GPU 상태

| 환경 | Python | PyTorch | CUDA | GPU (RTX 4090×2) | 역할 |
|------|--------|---------|------|-------------------|------|
| **bio-tools** | 3.11.1 | 2.10.0+cu128 | 12.8 | ✅ True / 2 GPU | ESMFold·PyRosetta·ProteinMPNN·FoldMason |
| **boltz** | 3.11.0 | 2.5.1+cu121 | 12.1 | ✅ True / 2 GPU | Boltz-2 도킹 |
| **rfdiffusion** | 3.9.19 | 2.1.0+cu121 | 12.1 | ✅ True / 2 GPU | RFdiffusion de novo |
| **diffpepbuilder** | 3.9.16 | 2.1.0 (CPU only) | — | ❌ False | DiffPepBuilder |
| **esmfold** | 3.10.2 | 2.6.0+cu124 | 12.4 | ✅ True / 2 GPU | ESMFold 독립 env |
| **genmol** | 3.11.1 | 2.6.0+cu124 | 12.4 | ✅ True / 2 GPU | MolMIM / GenMol |
| **openfold3** | 3.11.1 | 2.10.0+cu128 | 12.8 | ✅ True / 2 GPU | OpenFold3 |
| **pepadmet** | 3.7.16 | 1.13.1+cu117 | 11.7 | ✅ True / 2 GPU | PepADMET |
| **proteinmpnn** | 3.11.1 | 2.2.1+cu121 | 12.1 | ✅ True / 2 GPU | ProteinMPNN |
| **vllm-server** | 3.11.1 | 2.10.0+cu128 | 12.8 | ✅ True / 2 GPU | LLM 추론 서버 |

### 4.2 bio-tools 핵심 패키지 상태

| 패키지 | 버전 | 상태 | 비고 |
|--------|------|------|------|
| pyrosetta | (비공개) | ✅ import OK | `__version__` 없음 |
| biopython | 1.79 | ✅ | Bio.PDB, ProteinAnalysis |
| peptides | **0.5.0** | ✅ | Boman, aliphatic_index (신규 2026-05-12) |
| pymol | (비공개) | ✅ | `from pymol import cmd` 필요 |
| numpy | 1.26.4 | ✅ | |
| scipy | 1.12.0 | ✅ | |
| torch | 2.10.0+cu128 | ✅ | CUDA 12.8, 2 GPU |

### 4.3 주의 사항

**diffpepbuilder**: GPU 없음 (CPU-only PyTorch)
```bash
conda run -n diffpepbuilder python -c "import torch; print(torch.cuda.is_available())"
# → False
```
→ DiffPepBuilder가 GPU 필요할 경우 `cu121` 또는 `cu118` 빌드로 교체 필요.

**pepadmet**: CUDA 11.7 (구버전)
```
pepadmet: PyTorch 1.13.1+cu117
```
→ RTX 4090 (compute capability 8.9)에서 동작하나 sm_89 최적 지원 없음.
→ 성능 제약 있을 수 있음 (PepADMET 추론 속도).

**peptides 0.5.0 + GRAVY 주의**
```python
import peptides
# peptides.Peptide('AGCKNFFWKTFTSC').gravy() → AttributeError (0.5.0에 없음)
# 대신 Bio.SeqUtils.ProtParam.ProteinAnalysis.gravy() 사용 필요
```

### 4.4 검증 명령

```bash
# bio-tools 전체 import 검증
conda run -n bio-tools python -c "
from pipeline_local.scripts.stability_predictor import compute_stability
r = compute_stability('AGCKNFFWKTFTSC', 'test')
print('score:', r.score, 'hl:', r.modified_hl_hours)
"

# GPU 유효성 (전체 환경)
for env in bio-tools boltz rfdiffusion esmfold genmol openfold3 pepadmet proteinmpnn vllm-server; do
    conda run -n $env python -c "import torch; print(f'$env: {torch.cuda.is_available()}, {torch.__version__}')"
done
```

---

## 5. STATUS_FILE 메커니즘 분석

### 5.1 STATUS_FILE 경로

```python
# pipeline_local/backend/state.py (line 40-43)
STATUS_FILE = Path(os.environ.get(
    "PIPELINE_STATUS_FILE",
    "/tmp/pipeline_local_status.json",
))
```

```bash
# 실제 존재 확인
/tmp/pipeline_local_status.json   ← pipeline_local orchestrator 사용
/tmp/ag_pipeline_status.json      ← 레거시 (AG_src 오케스트레이터)
```

### 5.2 STATUS_FILE 쓰기 경로 (현재)

```
┌─────────────────────────────────────────────────────────────────┐
│  경로 1: orchestrator.py (정식 파이프라인)                       │
│                                                                   │
│  orchestrator.py → _write_status_file() [line 1978]             │
│    _STATUS_FILE.write_text(json.dumps(payload), ...)            │
│    호출 시점: 매 step 완료, iteration 완료, 파이프라인 완료      │
│                                                                   │
│  경로 2: POST /api/status (FastAPI 엔드포인트)                   │
│                                                                   │
│  status.py → post_status() [line 47-57]                         │
│    STATUS_FILE.write_text(json.dumps(data.model_dump()), ...)   │
│    호출 시점: 외부 프로세스가 HTTP POST로 상태 push              │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 문제 핵심: CLI ad-hoc 실행 시 STATUS_FILE 미갱신

```
┌─────────────────────────────────────────────────────────────────┐
│  CLI ad-hoc 실행 예시:                                           │
│                                                                   │
│  python pipeline_local/steps/step06_rosetta.py --seq-id cand01  │
│  python -m pipeline_local.scripts.stability_predictor ...       │
│                                                                   │
│  ❌ 이 경우 STATUS_FILE 갱신 없음                                │
│  ❌ runs_local/ 하위 결과 폴더 생성 → archives/ 미포함          │
│  ❌ GET /api/runs → 해당 실행 결과 노출 안 됨                   │
│  ❌ 프론트엔드 대시보드에서 보이지 않음                          │
└─────────────────────────────────────────────────────────────────┘
```

**현재 runs_local/ 내 ad-hoc 결과 (archives/ 미포함)**:
```
runs_local/
├── dogfood_2026-05-11/    # ad-hoc → 대시보드 미노출
├── dual_final_01/         # ad-hoc → 대시보드 미노출
├── dual_final_02/         # ad-hoc → 대시보드 미노출
├── dual_final_03/         # ad-hoc → 대시보드 미노출
├── dual_full_01/          # ...
├── cand03_variants/
├── local_20260326_1153_iter01/
└── local_20260326_1154_iter01/
```

### 5.4 해결 방법 제안

#### Option A: SSE (Server-Sent Events) 스트리밍 [중기]
```python
# backend/routers/status.py에 추가
@router.get("/status/stream")
async def status_stream():
    """STATUS_FILE을 tail하며 변경 시 SSE로 push."""
    async def event_gen():
        last_mtime = 0.0
        while True:
            mtime = STATUS_FILE.stat().st_mtime if STATUS_FILE.exists() else 0.0
            if mtime != last_mtime:
                data = STATUS_FILE.read_text()
                yield f"data: {data}\n\n"
                last_mtime = mtime
            await asyncio.sleep(1.0)
    return StreamingResponse(event_gen(), media_type="text/event-stream")
```
**장점**: 실시간 갱신, 폴링 없음 | **단점**: FastAPI 실행 중에만 동작

#### Option B: JSONL tail + 공유 로그 [단기, 권장]
```python
# orchestrator.py 내 _write_status_file() 하단에 추가
EXP_JSONL = REPO_ROOT / "runs_local" / "experiment_log.jsonl"
with EXP_JSONL.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"ts": ..., "run_id": ..., **payload}) + "\n")
```
```bash
# CLI에서 tail로 실시간 모니터링
tail -f runs_local/experiment_log.jsonl | python -m json.tool
```
**장점**: 구현 간단, ad-hoc 실행도 append 가능 | **단점**: UI 미연동

#### Option C: ad-hoc 결과 자동 STATUS_FILE 기록 스크립트 [즉시 적용]
```bash
# scripts/adhoc_status_update.sh
#!/bin/bash
# ad-hoc step 완료 후 STATUS_FILE에 간략 상태 기록
RUN_ID="${1:-adhoc_$(date +%Y%m%d_%H%M)}"
STEP="${2:-unknown}"
python3 -c "
import json, os, time
from pathlib import Path
sf = Path(os.environ.get('PIPELINE_STATUS_FILE', '/tmp/pipeline_local_status.json'))
data = json.loads(sf.read_text()) if sf.exists() else {}
data['last_adhoc'] = {'run_id': '$RUN_ID', 'step': '$STEP', 'ts': time.time()}
sf.write_text(json.dumps(data, indent=2))
print('STATUS_FILE 갱신:', sf)
"
```

#### Option D: 폴링 확장 (GET /api/status의 갱신 주기 단축)
```javascript
// 프론트엔드 StatusPoller 갱신 주기를 2s → 500ms로 단축
// 단기 workaround (CPU 비용 주의)
```

**권장 실행 순서**:
1. **즉시**: Option B (JSONL append) — orchestrator.py에 3줄 추가
2. **단기**: Option C (ad-hoc 스크립트) — CI 작업 후 자동 기록
3. **중기**: Option A (SSE 스트리밍) — 대시보드 실시간 갱신

---

## 6. ARCHIVE_DIR 확장 권장

### 6.1 현재 ARCHIVE_DIRS 구성

```python
# pipeline_local/backend/state.py (line 48-53)
def _default_archive_dirs() -> list[Path]:
    return [
        REPO_ROOT / "runs" / "pyrosetta_flow" / "archives",      # ① 레거시
        REPO_ROOT / "runs_local" / "archives",                     # ② 현재 메인
        AG_SRC_REPO / "runs" / "pyrosetta_flow" / "archives",     # ③ 원본 리포
    ]
```

**`runs_local/archives/`에 실제 등록된 실험**:
```
sst14_mutdock_100, sst14_mutdock_137, sst14_mutdock_256, ...
sst14_mutdock_1024, sst14_mutdock_1337, sst14_mutdock_2048
sst14_mutdock_4096, sst14_mutdock_512, sst14_mutdock_42, sst14_mutdock_777
(총 10개 _dashboard.json)
```

### 6.2 문제: ad-hoc 실행 결과 미노출

**`runs_local/` 하위 비-archive 폴더** (대시보드 미노출):
```
dogfood_2026-05-11/        # May 11 dogfood
dual_final_01~03/          # dual silo 최종 실험
dual_full_01/              # 전체 파이프라인 실험
dual_test_01/, dual_ui_test/
dual_verify_01~04/         # 검증 실험
cand03_variants/           # 후보 변이 실험
local_20260326_*/          # 3월 실험
silo_b_pr14_dogfood_2026-05-12/  # 최신 dogfood (STATUS_FILE 상의 실험)
```

### 6.3 ARCHIVE_DIRS 확장 방안

#### 방안 A: runs_local/ 전체를 탐색 범위에 추가 [권장]
```python
# state.py _default_archive_dirs() 수정
def _default_archive_dirs() -> list[Path]:
    return [
        REPO_ROOT / "runs" / "pyrosetta_flow" / "archives",
        REPO_ROOT / "runs_local" / "archives",
        REPO_ROOT / "runs_local",                              # ← 신규 추가
        AG_SRC_REPO / "runs" / "pyrosetta_flow" / "archives",
    ]
```
`list_archive_dashboard_files()`는 `*_dashboard.json` glob이므로
archives 폴더에 없는 ad-hoc 결과도 `{run_id}_dashboard.json`만 있으면 노출됨.

#### 방안 B: 신규 `ADHOC_RESULT_DIR` 경로 추가
```python
ADHOC_RESULT_DIRS = [
    REPO_ROOT / "runs_local",
    REPO_ROOT / "runs_local" / "dogfood_*",   # glob은 직접 지원 안 되므로 코드 변경 필요
]
```

#### 방안 C: orchestrator 완료 시 archives/ 자동 링크
```python
# orchestrator.py _save_archive() 추가
archive_src = output_base / run_id
archive_dst = ARCHIVE_DIRS[1] / f"{run_id}_dashboard.json"
shutil.copy(dashboard_json, archive_dst)  # 완료 시 archives에 dashboard 복사
```

**권장**: 방안 A를 즉시 적용 (2줄 추가), 방안 C는 중기 적용.

### 6.4 코드 수정 (방안 A)

```python
# pipeline_local/backend/state.py 수정 대상
def _default_archive_dirs() -> list[Path]:
    return [
        REPO_ROOT / "runs" / "pyrosetta_flow" / "archives",
        REPO_ROOT / "runs_local" / "archives",
        REPO_ROOT / "runs_local",                              # ← 신규: ad-hoc 결과 노출
        AG_SRC_REPO / "runs" / "pyrosetta_flow" / "archives",
    ]
```

**영향 범위**: `list_archive_dashboard_files()`, `find_dashboard_archive()` — 
모두 `_default_archive_dirs()` 사용 → 자동 반영.

---

## 7. 결함 목록

### Critical (즉시 수정)
없음 (현재 운영 중)

### High

| ID | 파일 | 설명 | 수정 방법 |
|----|------|------|---------|
| D-06-01 | `step06_rosetta.py` | gate_thresholds.yaml의 `rosetta_ddg_max: -1.0`이 코드 기본값 `-5.0`보다 완화 | gate_thresholds.yaml 검토 및 `-5.0` 복원 또는 명시적 문서화 |
| D-08-01 | `step08_stability.py` | `_PROTEASE_VULNERABILITY` 점수의 정량 문헌 출처 부재 (VR-S5-01) | HEURISTIC_FUNCTION_DISCLAIMERS에 등록 완료; pharmacology_guards에 출처 주석 추가 |
| D-ST-01 | `state.py` | ad-hoc 실행 결과 STATUS_FILE 미갱신 → 대시보드 미노출 | §5.4 Option B 즉시 적용 |

### Medium

| ID | 파일 | 설명 | 수정 방법 |
|----|------|------|---------|
| D-06-02 | `step06_rosetta.py` | cache flush 실패 시 warning만 (결과 손실 가능) | 재시도 로직 또는 sqlite 기반 캐시로 전환 |
| D-07-01 | `step07_analysis.py` | lDDT threshold 미정의 (rank_table 경고 기준 없음) | `gate_thresholds.yaml`에 `foldmason_lddt_min: 0.7` 추가 |
| D-08-02 | `step08_stability.py` | modification 보너스 단순 가산 (saturation 비선형성 무시) | 장기: sigmoid saturation 모델 도입 (VR-S5-01 partial) |
| D-ENV-01 | `diffpepbuilder` env | GPU 없음 (CPU-only) → DiffPepBuilder 실행 시 성능 저하 | `cu121` build로 재설치 |
| D-ENV-02 | `pepadmet` env | PyTorch 1.13.1+cu117 (구버전, sm_89 최적 없음) | PepADMET 모델과 신버전 호환성 확인 후 업그레이드 |

### Low

| ID | 파일 | 설명 |
|----|------|------|
| D-ST-02 | `state.py` | `ARCHIVE_DIR` 레거시 변수 (첫 번째 경로만) — 신규 코드에서 미사용이나 혼동 가능 |
| D-06-03 | `step06_rosetta.py` | `import shutil` 루프 내부 지연 import (성능 무관하나 스타일) |

---

## 8. 신규 기능 제안

### 8.1 GPU 모니터링 대시보드 (권장 우선순위: High)

```python
# scripts/gpu_monitor.py (신규)
import subprocess, json, time
from pathlib import Path

def get_gpu_stats() -> dict:
    """nvidia-smi --query-gpu 기반 GPU 통계."""
    proc = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True
    )
    rows = []
    for i, line in enumerate(proc.stdout.strip().split("\n")):
        name, mem_used, mem_total, util, temp = line.split(",")
        rows.append({
            "gpu_id": i, "name": name.strip(),
            "mem_used_mb": int(mem_used), "mem_total_mb": int(mem_total),
            "util_pct": int(util), "temp_c": int(temp),
        })
    return {"gpus": rows, "ts": time.time()}
```

```bash
# FastAPI 엔드포인트 추가
GET /api/gpu-stats   → {"gpus": [...], "ts": 1715xxx}
```

**활용**: 대시보드 사이드바에 GPU 사용률 실시간 표시
**우선순위**: M4 팀원과 협의 후 프론트 연동

### 8.2 모델 Warm-up 스크립트 (권장 우선순위: Medium)

```bash
# scripts/warmup_models.sh (신규)
#!/bin/bash
# 파이프라인 실행 전 각 모델 환경 사전 초기화

echo "[Warm-up] bio-tools / PyRosetta..."
conda run -n bio-tools python -c "import pyrosetta; pyrosetta.init()" &

echo "[Warm-up] boltz..."
conda run -n boltz python -c "import boltz; print('ready')" &

echo "[Warm-up] esmfold..."
conda run -n esmfold python -c "import esm; print('ready')" &

wait
echo "[Warm-up] 완료"
```

**효과**: step01~05 실행 전 conda env 활성화 지연 제거 (cold start ~30s → ~5s)

### 8.3 Step08 → stability_predictor U1.5 교체 로드맵

```
Phase 1 (1일): 수치 동등성 검증
  - step08.predict_half_life('AGCKNFFWKTFTSC') vs
    stability_predictor.core.hl_score_heuristic('AGCKNFFWKTFTSC')
  - 결과 비교 테스트 추가

Phase 2 (2일): step08에서 stability_predictor 임포트
  from pipeline_local.scripts.stability_predictor.core import hl_score_heuristic
  # step08.predict_half_life()를 래퍼로 전환

Phase 3 (1일): Silo A/B 분기 적용
  - SiloAEvaluator / SiloBEvaluator로 후보별 평가 분기
  - combined_report.py 출력 검증
```

### 8.4 JSONL 실험 로그 tail UI

```bash
# 대시보드 사이드 패널에 실시간 JSONL tail 추가
GET /api/log/stream   → SSE (tail experiment_log.jsonl)

# 프론트엔드: EventSource('/api/log/stream') → 콘솔 패널 출력
```

---

## 9. 종합 판정

### 9.1 step06~08 완성도

| Step | 구현 상태 | 테스트 | 실제 실행 | 판정 |
|------|---------|--------|---------|------|
| step06 (Rosetta) | ✅ 완성 | 기능 테스트 없음 | ✅ 완료 (104.4s) | **PASS** |
| step07 (Analysis) | ✅ 완성 | 기능 테스트 없음 | ✅ 완료 (4.4s) | **PASS** |
| step08 (Stability) | ✅ 완성 | 없음 | ⏳ pending | **CONDITIONAL** |

### 9.2 환경 Health

| 환경 | Python | GPU | 핵심 패키지 | 판정 |
|------|--------|-----|-----------|------|
| bio-tools | 3.11.1 | ✅ | pyrosetta+biopython+peptides | ✅ **HEALTHY** |
| boltz | 3.11.0 | ✅ | boltz | ✅ **HEALTHY** |
| rfdiffusion | 3.9.19 | ✅ | torch | ✅ **HEALTHY** |
| diffpepbuilder | 3.9.16 | ❌ CPU | — | ⚠️ **GPU 없음** |
| esmfold | 3.10.2 | ✅ | esm | ✅ **HEALTHY** |
| genmol | 3.11.1 | ✅ | — | ✅ **HEALTHY** |
| openfold3 | 3.11.1 | ✅ | — | ✅ **HEALTHY** |
| pepadmet | 3.7.16 | ✅ | torch 1.13 | ⚠️ **구버전 CUDA** |
| proteinmpnn | 3.11.1 | ✅ | — | ✅ **HEALTHY** |
| vllm-server | 3.11.1 | ✅ | — | ✅ **HEALTHY** |

### 9.3 STATUS_FILE / ARCHIVE_DIR 우선순위

| 항목 | 현황 | 긴급도 | 권장 조치 |
|------|------|--------|---------|
| STATUS_FILE — orchestrator 실행 | ✅ 자동 갱신 | — | 현행 유지 |
| STATUS_FILE — CLI ad-hoc | ❌ 미갱신 | **High** | JSONL append 즉시 추가 |
| ARCHIVE_DIRS — ad-hoc 결과 | ❌ 미노출 | **High** | `runs_local/` 경로 추가 |
| stability_predictor 통합 | 미완 (병렬 구현) | Medium | Phase 1~3 로드맵 실행 |
| GPU 모니터링 | 없음 | Low | M4와 협의 후 추가 |

---

## Appendix: 검증 명령 모음

```bash
# A. bio-tools 환경 전체 import 검증
conda run -n bio-tools python -m pytest \
    pipeline_local/tests/ -v --tb=short -q 2>&1 | tail -20

# B. Step08 단독 실행 (stub 모드)
conda run -n bio-tools python -c "
from pipeline_local.steps.step08_stability import evaluate_stability
results = evaluate_stability([{'seq_id': 'test', 'sequence': 'AGCKNFFWKTFTSC'}], {})
for r in results: print(r)
"

# C. stability_predictor U1.5 CLI
conda run -n bio-tools python -m pipeline_local.scripts.stability_predictor \
    --sequences AGCKNFFWKTFTSC AICKNFFWKTFTSC \
    --seq-ids ref var01

# D. 전체 환경 GPU 상태 스캔
for env in bio-tools boltz rfdiffusion diffpepbuilder esmfold genmol openfold3 pepadmet proteinmpnn vllm-server; do
    r=$(conda run -n $env python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null)
    echo "$env: GPU=$r"
done

# E. STATUS_FILE 현재 상태 확인
python3 -c "import json; d=json.load(open('/tmp/pipeline_local_status.json')); print('phase:', d.get('phase'), 'step:', d.get('current_step'))"

# F. ARCHIVE_DIRS 대시보드 파일 목록
conda run -n bio-tools python -c "
from pipeline_local.backend.state import list_archive_dashboard_files
for f in list_archive_dashboard_files(): print(f.name)
"
```

---

*보고서 생성: engineer-infra / 2026-05-13 / module-verification-2026-05-13 세션*
