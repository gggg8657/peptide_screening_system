# pipeline_local — LOCAL MODE Pipeline

NVIDIA NIM API 없이 로컬 GPU에서 SSTR2 펩타이드 바인더 설계 파이프라인을 실행합니다.

## Prerequisites

### 1. Conda 환경

```bash
# PyRosetta + 구조 생물학 도구
conda activate bio-tools

# PyTorch / ESMFold / ProteinMPNN
# (bio-tools 환경 내 포함되어 있어야 합니다)
```

### 2. Ollama (로컬 LLM)

```bash
# 설치: https://ollama.com
# 서버 시작 (포트 11435 사용)
OLLAMA_HOST=127.0.0.1 OLLAMA_PORT=11435 ollama serve &

# 모델 풀
ollama pull qwen3:8b
```

포트는 `~/.zshrc`의 `CUDA_VISIBLE_DEVICES` 및 `OLLAMA_HOST` 설정을 따릅니다.

### 3. GPU 설정

현재 환경:
- H100 NVL x4
- `CUDA_VISIBLE_DEVICES=2` (기본값, `~/.zshrc`에서 변경)

## 실행 방법

### 기본 실행

```bash
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr/local_models/genmol-repo

python -m pipeline_local.run_pipeline_local
```

### 주요 CLI 옵션

```bash
# 반복 횟수 지정
python -m pipeline_local.run_pipeline_local --iterations 3

# 출력 디렉토리 지정
python -m pipeline_local.run_pipeline_local --output-dir /tmp/my_run

# LLM 모델 변경
python -m pipeline_local.run_pipeline_local --llm-model qwen3:14b

# Ollama 서버 주소 변경
python -m pipeline_local.run_pipeline_local --ollama-host 127.0.0.1:11434

# 체크포인트에서 재개
python -m pipeline_local.run_pipeline_local --resume --run-id local_20260326_1200_iter01

# Approach A 강제 (RFdiffusion + ProteinMPNN)
python -m pipeline_local.run_pipeline_local --no-approach-b

# 디버그 로그
python -m pipeline_local.run_pipeline_local --log-level DEBUG
```

## 설정 파일

| 파일 | 설명 |
|------|------|
| `config/pipeline_config_local.yaml` | 메인 파이프라인 설정 (NIM API 없음) |
| `config/gate_thresholds.yaml` | QC 게이트 임계값 (원본과 동일) |

### 주요 설정 항목

```yaml
# config/pipeline_config_local.yaml

mode: local

llm:
  provider: ollama
  model: qwen3:8b              # 모델 변경 가능
  base_url: http://127.0.0.1:11435

approach_b:
  enabled: true                # 기본: BLOSUM62 돌연변이 (RFdiffusion 불필요)

iteration:
  max_iterations: 5            # 로컬 리소스 고려

output_base_dir: runs_local/
```

## 파일 구조

```
pipeline_local/
├── __init__.py
├── orchestrator.py          # LocalPipelineOrchestrator (원본 로직 유지)
├── run_pipeline_local.py    # 메인 진입점
├── config/
│   ├── pipeline_config_local.yaml
│   └── gate_thresholds.yaml
└── README.md
```

에이전트와 LLM provider는 원본 AG_src에서 공유합니다 (`sys.path` 주입 방식).

## 출력

실행 결과는 `runs_local/<run_id>/` 하위에 저장됩니다:

```
runs_local/local_20260326_1430_iter01/
├── 00_config/          # 실행 시 복사된 설정 파일
├── 01_receptor/        # 수용체 PDB
├── 04_qc/              # ESMFold 예측 결과
├── 05_docking/         # 도킹 점수
├── 06_rosetta/         # PyRosetta FlexPepDock 정제 결과
├── 08_reports/         # 반복 보고서 + 최종 리포트
└── state/              # 체크포인트 JSON (--resume 재개용)
```
