# PyRosetta Flow Results Guide

> PyRosetta-only agentic mutate→dock 실행 결과 확인 및 검증 절차
>
> **최종 업데이트: 2026-03-04**

## 1) Iteration 산출물 위치

| 산출물 | 경로 |
|--------|------|
| PDB 구조 | `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/cand_YYY.pdb` |
| PyMOL 렌더 스크립트 | `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/07_viz/*_render.pml` |
| 반복 요약 보고서 | `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/08_reports/summary.md` |
| 랭킹 테이블 | `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/08_reports/rank_table.csv` |
| 검증 결과 | `runs/pyrosetta_flow/09_validation/validation_*.json` |
| 전체 아티팩트 | `runs/pyrosetta_flow/pyrosetta_flow_artifacts.json` |
| 실험 로그 (누적) | `runs/pyrosetta_flow/experiment_log.jsonl` |
| 아카이브 (과거 실행) | `runs/pyrosetta_flow/archives/*_dashboard.json` + PDB 파일 |
| Paper validation 데이터 | `runs/pyrosetta_flow/paper_validation_4paper/{ID}*.pdb` |

## 2) 3D 확인 절차

### 방법 A: Web UI Mol* 뷰어 (권장)

Web UI 대시보드의 **3D Molecule Viewer** 섹션에서 후보 PDB를 인터랙티브하게 탐색할 수 있다.

1. Backend + Frontend 실행 (`python backend/api_server.py` + `cd frontend && npm run dev`)
2. `http://localhost:5173` 접속
3. Candidate Table에서 후보 선택
4. 3D Viewer에서 드롭다운으로 PDB 파일 선택
5. View Mode 전환: Complex / Backbone / Contacts / Electrostatics

**PDB 직접 접근:**
```bash
curl http://localhost:8787/api/structures/pyrosetta_flow/sst14_agentic_mutdock/iter_01/cand_001.pdb
```

### 방법 B: PyMOL GUI

```bash
# 후보 구조 열기
pymol runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/cand_YYY.pdb

# 렌더 스크립트 실행
pymol -c runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/07_viz/*_render.pml
```

## 3) 약리학 검증 절차

### 방법 A: Web UI 통합 검증

1. Candidate Table에서 대상 후보를 체크박스로 선택
2. **Validation Panel**에서 프리셋 선택:
   - `PRRT 방사성의약품` (11개 기준) 또는 `일반 펩타이드` (8개 기준)
3. **Run Validation** 클릭
4. 결과: PASS(≥80%) / CAUTION(60~80%) / FAIL(<60%)
5. **상세 보기**로 각 기준별 실제 값·임계값·통과 여부 확인

### 방법 B: API 직접 호출

```bash
# 통합 검증
curl -X POST http://localhost:8787/api/validate/unified \
  -H "Content-Type: application/json" \
  -d '{"sequences":["AGCKVFFWKTFHSC"],"criteria":["gravy","boman_index","instability_index"]}'

# 약리학 속성 계산
curl -X POST http://localhost:8787/api/pharmacology/batch \
  -H "Content-Type: application/json" \
  -d '{"sequences":["AGCKVFFWKTFHSC"],"reference":"AGCKNFFWKTFTSC"}'

# ADMET 분석
curl http://localhost:8787/api/admet/AGCKVFFWKTFHSC
```

## 4) API 상태 확인 포인트

- 상태 엔드포인트: `http://localhost:8787/api/status`
- 핵심 필드:
  - `timeline`: iteration별 이벤트 흐름과 continue 이벤트 확인
  - `rosetta_substeps`: mutate/refine/score/qc 단계 상태 확인
  - `historical_candidates`: 누적 후보 기록 확인
  - `best_candidate`: 현재까지 최적 후보 (반복별 갱신)
  - `convergence`: ddG 수렴 추이

## 5) 실행 예시

### 기본 실행 (Web UI)

```bash
# 터미널 1: Backend API Server
python backend/api_server.py

# 터미널 2: Frontend
cd frontend && npm run dev

# 브라우저에서 http://localhost:5173 접속
# Experiment Control에서 "PyRosetta Only" 선택 → Start
```

### CLI 직접 실행

```bash
python scripts/run_pyrosetta_flow.py \
  --input data/fold_test1_model_0.pdb \
  --max-iterations 5 \
  --n-candidates 8 \
  --seed-base 1000 \
  --conda-env bio-tools \
  --objective-mode auto \
  --planner-mode pyrosetta-only \
  --output-json runs/pyrosetta_flow/pyrosetta_flow_artifacts.json
```

## 6) 계획 검증 체크리스트

### 6-1. N회 루프 검증

실행 후 artifact JSON에서 `iterations` 길이와 상태 이벤트를 확인합니다.

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path("runs/pyrosetta_flow/pyrosetta_flow_artifacts.json")
d = json.loads(p.read_text(encoding="utf-8"))
iters = d.get("iterations", [])
print("iterations_len =", len(iters))
print("summary_iterations =", d.get("summary", {}).get("iterations"))
PY
```

### 6-2. Planner 문구 검증 (금지 키워드)

각 iteration hypothesis에 금지 키워드가 없는지 확인합니다.

```bash
python - <<'PY'
import json
from pathlib import Path
blocked = ("rfdiffusion", "proteinmpnn", "esmfold")
d = json.loads(Path("runs/pyrosetta_flow/pyrosetta_flow_artifacts.json").read_text(encoding="utf-8"))
for i, it in enumerate(d.get("iterations", []), 1):
    hyp = (it.get("summary", {}) or {}).get("hypothesis", "")
    hit = [k for k in blocked if k in hyp.lower()]
    print(f"iter_{i:02d}:", "OK" if not hit else f"FOUND {hit}")
PY
```

### 6-3. 산출물 존재 검증

최소 1개 iteration에서 아래 파일이 존재해야 합니다.

- `cand_*.pdb`
- `07_viz/*_render.pml`
- `08_reports/summary.md`
- `08_reports/rank_table.csv`

### 6-4. 정적 검증

```bash
python -m compileall pyrosetta_flow AG_src scripts backend
```

### 6-5. 약리학 검증 (신규)

```bash
python - <<'PY'
import json, sys
sys.path.insert(0, ".")
from backend.pharmacology import compute_pharmacology
result = compute_pharmacology("AGCKVFFWKTFHSC", reference="AGCKNFFWKTFTSC")
print(json.dumps(result, indent=2, default=str))
PY
```

## 7) Paper Validation 데이터 (`paper_validation_4paper`)

논문용 벤치마크 검증 데이터로, **top-3 mean of 10 trials** 메트릭을 사용한다.

### 구조

7개 펩타이드 × (1 baseline + 5 trials) = 41 PDB 파일:

| ID | 서열 | 유형 | ddG (best) |
|----|------|------|------------|
| **NOV-01** | YSCKNFFWKTFTSN | Novel analog | **-43.52** |
| NOV-02 | AGCKNDFWKTFGSE | Novel analog | -43.28 |
| LIT-03 | APCKNFFWKTFSSC | 문헌 analog | -42.36 |
| LIT-02 | FCCKNFFWKTCTSC | 문헌 analog | -42.35 |
| SAN-02 | AGCKNFFWATFTSC | Sanity (K10→A) | -40.70 |
| SAN-01 | AGCKNFFAKTFTSC | Sanity (W9→A) | -38.34 |
| **LIT-01** | AGCKNFFWKTFTSC | **SST-14 native** | **-36.71** |

**주요 결과:** NOV-01이 rank 1, LIT-01 (SST-14 native)이 rank 7 — novel analog가 native 서열을 유의미하게 능가함을 입증.

### 파일 명명 규칙

```
{ID}_{SEQUENCE}.pdb        ← baseline (best-of-N)
{ID}_{SEQUENCE}_t0.pdb     ← trial 0
{ID}_{SEQUENCE}_t1.pdb     ← trial 1
...
{ID}_{SEQUENCE}_t4.pdb     ← trial 4
```

> **참고:** LIT-03은 `_t1.pdb`가 누락되어 5개 파일만 존재한다.

## 8) 아카이브 구조 (L4)

`StatusEmitter._save_archive()`가 실행 종료 시 자동으로 아카이브를 생성한다:

```
runs/pyrosetta_flow/archives/
  +-- {run_id}/
       +-- dashboard.json          ← 대시보드 상태 스냅샷
       +-- iter_01/                ← PDB 파일 복사본
       |    +-- cand_001.pdb
       |    +-- cand_002.pdb
       +-- iter_02/
            +-- cand_001.pdb
            +-- ...
```

- PDB 파일은 후보의 `pdb_path` 필드에서 자동 복사됨
- 후보 JSON의 `pdb_path`가 아카이브 상대 경로로 업데이트됨
- `fcntl.flock` 기반 원자적 쓰기로 동시 접근 안전
