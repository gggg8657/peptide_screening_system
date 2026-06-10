# ENVIRONMENT.md

## ENV_NAME

`bio-tools`

## PYTHON

`3.11`

## CUDA

`cpu`

## CREATE

```bash
conda create -n bio-tools python=3.11
conda activate bio-tools
pip install -r /home/helloworld/Documents/workspace/repos/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/AG_src/requirements.txt
```

## ACTIVATE

```bash
conda activate bio-tools
```

## VERIFY

```bash
python -V
python -c "import pyrosetta; print('pyrosetta ok')"
```

## RUN

```bash
cd /home/helloworld/Documents/workspace/repos/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
python scripts/run_pyrosetta_flow.py \
  --input <template_complex.pdb> \
  --n-candidates 8 \
  --max-iterations 2 \
  --objective-mode auto \
  --top-k 5

# or entrypoint wiring
python run_pipeline_live.py --enable-pyrosetta-flow --pyrosetta-input <template_complex.pdb>
```

## TEST/SMOKE

```bash
cd /home/helloworld/Documents/workspace/repos/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri
python -m compileall pyrosetta_flow scripts/run_pyrosetta_flow.py run_pipeline_live.py
```

## NOTES

- `<template_complex.pdb>`는 수용체+펩타이드 복합체 템플릿이어야 한다.
- 기본 체인 가정은 receptor=1, peptide=2 이다. 다르면 `--peptide-chain`을 사용한다.
- objective는 `auto`일 때 iteration 1=`ddg_only`, 이후=`ddg_plus_constraints`로 전환된다.
- PyRosetta 미설치 환경에서는 `import pyrosetta` 검증 단계에서 실패한다.
