# ENVIRONMENT.md

## Runtime Environment

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.12.12 | `bio-tools` conda 환경 |
| Node.js | 20.20.0 | 프론트엔드 빌드/개발 |
| npm | 11.11.0 | 패키지 관리 |
| Conda env | `bio-tools` | CPU 기본, GPU PyTorch/PyRosetta 선택 |
| CUDA | `cpu` (default) | GPU 환경 시 CUDA 12.x 호환 |

## Python Packages (bio-tools)

| Package | Version |
|---------|---------|
| PyRosetta | 2026.06+release |
| PyMOL (open-source) | 3.1.0 |
| FastAPI + uvicorn | backend API 서버 |
| pytest | 테스트 프레임워크 |

## Frontend Dependencies (주요)

| Package | Version |
|---------|---------|
| react | ^19.2.0 |
| react-dom | ^19.2.0 |
| molstar | ^5.6.1 |
| vitest | ^4.0.18 |
| @testing-library/react | ^16.3.2 |
| @testing-library/jest-dom | ^6.9.1 |
| @testing-library/user-event | ^14.6.1 |
| @vitejs/plugin-react | ^5.1.1 |
| lucide-react | ^0.574.0 |
| @radix-ui/react-tooltip | ^1.2.8 |

## CREATE

```bash
conda create -n bio-tools python=3.12 -y
conda activate bio-tools
pip install -r requirements.txt    # if/when provided
```

## ACTIVATE

```bash
conda activate bio-tools
```

## VERIFY

```bash
python -V                           # 3.12.12
python -c "import pyrosetta; print(pyrosetta.__version__)"
node -v                             # v20.20.0
npm -v                              # 11.11.0
```

## RUN

작업 디렉터리: `repos/ai4sci-kaeri` (이 레포의 Python/Node 루트).

```bash
conda activate bio-tools
cd repos/ai4sci-kaeri

# 백엔드 API (FastAPI) — 터미널 1
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8787

# 프론트엔드 (Vite) — 터미널 2
cd frontend && npm install && npm run dev
# 브라우저: http://localhost:5173  (Vite가 /api → 8787 로 프록시)

# 파이프라인 (별도 터미널, 실시간 대시보드용 상태 JSON 생성)
python scripts/run_pyrosetta_flow.py --input data/fold_test1_model_0.pdb --max-iterations 5 --planner-mode pyrosetta-only

# 메인 진입점
python run_pipeline_live.py --enable-pyrosetta-flow --pyrosetta-input data/fold_test1_model_0.pdb
```

**Live vs Mock (Silo B 대시보드)**  
`PIPELINE_STATUS_FILE`(기본 `/tmp/pipeline_local_status.json`)이 없으면 헤더에 **Mock**이 뜨고 후보/스텝은 `mockData`를 씁니다. 파이프라인이 상태를 쓰거나, 상단 **Run history**에서 아카이브 런을 고르면 실데이터 뷰로 전환됩니다.

**pepADMET 독성 (선택)**  
`PRST_N_FM/local_models/pepadmet/repo` 클론 + `conda` 환경 `pepadmet` 필요. 없으면 ADMET API의 `pepadmet` 필드는 `available: false`. 빠른 응답만 필요하면 `SKIP_PEPADMET=1`로 병합 생략.

## TEST

```bash
# 프론트엔드 (32 tests — Vitest + RTL)
cd frontend && npx vitest run

# 백엔드 + 파이프라인 (118 tests — pytest, 93% coverage)
python -m pytest pyrosetta_flow/tests/ -v

# 컴파일 체크
python -m compileall pyrosetta_flow AG_src scripts
```

## NOTES

- PyRosetta and GPU stack can vary by machine; verify import/runtime before long runs.
- Results are saved under `runs/pyrosetta_flow/sst14_agentic_mutdock/iter_XX/`.
- Status API fields to check: `timeline`, `rosetta_substeps`, `historical_candidates`.
- Backend is FastAPI with 6 routers in `backend/routers/` (admet, analysis, experiment, static, status, validation).
