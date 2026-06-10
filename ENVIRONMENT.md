# Environment Specification

> Single Source of Truth for reproducing the project environment.

---

## Quick Reference

| 항목 | 값 |
|------|-----|
| **ENV_NAME** | `bio-tools` |
| **PYTHON** | 3.10 ~ 3.12 |
| **CUDA** | 불필요 (NVIDIA NIM API는 클라우드 추론) |
| **OS** | Ubuntu 22.04 / WSL2 |

---

## CREATE

```bash
# 권장: environment.yml에서 생성
conda env create -f environment-bio-tools.yml

# 또는 수동
conda create -n bio-tools python=3.11
conda activate bio-tools
pip install -r bionemo/requirements.txt
```

## ACTIVATE

```bash
conda activate bio-tools
```

## VERIFY (최소 2개)

```bash
# 1. Python 버전
python -V

# 2. 핵심 패키지 import
python -c "import Bio; print('Biopython:', Bio.__version__)"

# 3. PyRosetta (선택, 라이선스 필요)
python -c "import pyrosetta; pyrosetta.init(); print('PyRosetta: OK')"

# 4. 전체 환경 스모크 테스트
python scripts/verify_bio_tools_env.py
```

## RUN (대표 커맨드)

```bash
# SSTR2 바인딩 포켓 분석
python bionemo/04_sstr2_pocket_analysis.py

# 전체 3-Arm 파이프라인 실행
bash scripts/run_sstr2_pipeline.sh

# Jupyter 노트북 (FastDesign 데모)
jupyter notebook notebooks/SSTR2_SST14_demo.ipynb
```

## TEST / SMOKE (최소 1개)

```bash
# 파이프라인 유닛 테스트 (권장)
python3 -m pytest pipelines/silo_a/tests/ -q   # 9 tests
python3 -m pytest pipelines/silo_b/tests/ -q   # 24 tests

# BioNeMo 클라이언트 import 테스트 (API 키 불필요)
python -c "
from bionemo import MolMIMClient, DiffDockClient, ESMFoldClient
from bionemo import RFdiffusionClient, ProteinMPNNClient
print('All BioNeMo clients imported OK')
"

# 구문 검사
python -m compileall bionemo/ scripts/ pipelines/ -q
```

## API KEY 설정

NVIDIA NIM API 사용 시 필요 (`nvapi-` 접두사):

```bash
# 방법 1: 환경변수
export NGC_CLI_API_KEY="nvapi-YOUR_KEY"

# 방법 2: 키 파일
echo "nvapi-YOUR_KEY" > molmim.key

# 방법 3: .env 파일
echo 'NGC_CLI_API_KEY=nvapi-YOUR_KEY' > bionemo/.env
```

## NOTES

- **PyRosetta**: 학술 라이선스 필요 ([RosettaCommons](https://www.rosettacommons.org/software/license-and-download))
- **RDKit**: conda 전용 (`conda install -c conda-forge rdkit`), pip로는 `rdkit-pypi`
- **FoldMason**: bioconda 채널 필요
- **GPU**: 로컬 GPU 불필요. 모든 AI 추론은 NVIDIA 호스팅 API 사용
- **데이터 경로**: AlphaFold3 결과는 `data/fold_test1/`, 실험 결과는 `results/`
