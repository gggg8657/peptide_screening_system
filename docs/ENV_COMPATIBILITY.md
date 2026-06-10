# 환경 호환성 정리: PyRosetta, Biopython, AutoDock-GPU, AlphaFold3, MCP

## 요약 결론

| 구분 | 한 환경에서 모두? | 권장 |
|------|-------------------|------|
| **PyRosetta + Biopython + AutoDock-GPU 워크플로** | ✅ 가능 | 하나의 conda 환경 (`bio-tools`) |
| **AlphaFold3** | ⚠️ 별도 권장 | 전용 Docker 또는 별도 env (`alphafold`) |
| **MCP 서버** | ✅ 대부분 가능 | `bio-tools`에 포함 또는 경량 별도 env |

**최소 보장**: PyRosetta, Biopython, AutoDock-GPU(Meeko + 바이너리)는 **하나의 conda 환경**에서 실행.  
AlphaFold3와 MCP는 아래대로 분리 권장.

---

## 1. 컴포넌트별 요구사항

### PyRosetta
- **타입**: Python 패키지 (pip/conda)
- **Python**: 3.6–3.14 (conda 채널 기준), pip은 quarterly wheel로 버전별 제공
- **CUDA**: 불필요 (CPU)
- **비고**: 라이선스(학술/비영리). `conda install -c conda.rosettacommons.org -c conda-forge pyrosetta` 또는 pip quarterly 빌드

### Biopython
- **타입**: Python 패키지
- **Python**: 3.x
- **비고**: conda-forge / pip 모두 무난

### AutoDock-GPU
- **타입**: **C/C++ 빌드 바이너리** (Python 패키지 아님)
- **시스템**: CUDA 11+ 또는 OpenCL, GCC ≥ 9, C++17
- **Python 쪽**: 워크플로 전처리용 **Meeko** (pip/conda), 그리드 계산용 **AutoGrid** (별도 빌드)
- **비고**: `make DEVICE=GPU` 등으로 빌드 후 `bin/autodock_gpu_*wi` 실행. 같은 conda env에서 Meeko만 설치하고, 바이너리는 PATH 또는 절대경로로 호출하면 됨.

### AlphaFold2 / AlphaFold3
- **타입**: Python + Docker 권장 (공식은 Docker)
- **Python**: 보통 3.8–3.10 구간 권장 (JAX/TF 등과 충돌 이력 있음)
- **CUDA**: 11.x, GPU 필수
- **비고**: 의존성 무겁고(JAX, TensorFlow, 특정 CUDA) PyRosetta/Meeko와 한 env에 넣으면 버전 충돌 위험. **별도 Docker 또는 전용 conda env 권장.**

### MCP 서버
- **타입**: 사용하는 MCP 서버 구현에 따름
- **비고**: 일반 Python 기반 MCP라면 `bio-tools`와 같은 env에서 가능. 무거운 전용 의존성이 있으면 별도 env 제안.

---

## 2. 권장 환경 구성

### 환경 1: `bio-tools` (신규 생성 대상)
- **용도**: PyRosetta, Biopython, AutoDock-GPU 워크플로(Meeko), 공통 스크립트, 가벼운 MCP
- **포함**: python 3.10–3.12, pyrosetta, biopython, meeko, (선택) numpy, pandas
- **AutoDock-GPU 바이너리**: WSL 시스템에 별도 빌드 후 `PATH` 또는 스크립트에서 경로 지정
- **AutoGrid**: 동일하게 시스템/별도 경로에 빌드 후 사용

### 환경 2: `alphafold` (추후 구성)
- **용도**: AlphaFold2/3 전용
- **방법**: 공식 Docker 사용 또는 [AlphaFold 설치 가이드](https://github.com/google-deepmind/alphafold#installation-and-running-your-first-prediction) 기준 전용 conda env
- **비고**: AF3 공개 저장소/설치 방법 확정 후 동일 원칙으로 env 또는 Docker로 분리

### MCP 서버
- 경량이면 `bio-tools`에 함께 설치
- 전용 대형 의존성 있으면 별도 env (예: `mcp-server`) 생성 후 해당 env에서만 실행

---

## 3. AutoDock-GPU 바이너리 빌드 (WSL)

같은 환경에서 “돌린다”는 것은 **Meeko로 전처리 + 이 바이너리 실행**까지를 하나의 워크플로로 쓰는 의미이므로, 바이너리는 아래처럼 따로 빌드하면 됨.

### 3.1 사전 준비 (WSL)

- **빌드 도구**: `sudo apt install build-essential`
- **CUDA 개발 패키지** (둘 중 하나):
  - Ubuntu/Debian: `sudo apt install nvidia-cuda-dev` → 이후 `GPU_INCLUDE_PATH=/usr/include`, `GPU_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu`
  - 또는 [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) 설치 → `GPU_INCLUDE_PATH=/usr/local/cuda/include`, `GPU_LIBRARY_PATH=/usr/local/cuda/lib64`

### 3.2 이 레포에서 빌드하기

- 소스는 `tools/AutoDock-GPU`에 클론해 두었음 (`tools/`는 .gitignore).
- **한 번에 빌드**: `./scripts/build_autodock_gpu.sh` (CUDA 경로가 없으면 안내 메시지 후 종료. 위 사전 준비 후 다시 실행.)
- 수동 빌드:
  ```bash
  export GPU_INCLUDE_PATH=/usr/include   # 또는 /usr/local/cuda/include
  export GPU_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu   # 또는 /usr/local/cuda/lib64
  cd tools/AutoDock-GPU && make DEVICE=GPU NUMWI=64
  ```
- 실행 파일: `tools/AutoDock-GPU/bin/autodock_gpu_64wi` → PATH에 추가하거나 절대 경로로 호출.

AutoGrid는 [ccsb-scripps/AutoGrid](https://github.com/ccsb-scripps/autogrid) 에서 meson/autotools로 빌드 후 동일하게 PATH 또는 경로 지정.

---

## 4. 다음 액션 제안

1. ~~**지금 진행**: `bio-tools` conda 환경 생성 → PyRosetta, Biopython, Meeko 설치~~ → 완료.
2. **AutoDock-GPU**: CUDA 툴킷 설치 후 `./scripts/build_autodock_gpu.sh` 실행 → `bio-tools` env에서 Meeko + 바이너리로 실행 테스트.
3. **AlphaFold3**: 전용 Docker 권장 (공식 가이드). conda 전용 env는 AF3 공개 설치법 확정 후 `environment-alphafold.yml` 추가. `ENVIRONMENT.md`에 AlphaFold 섹션 반영됨.
4. **MCP**: 사용할 MCP 서버 목록 정한 뒤, `bio-tools` 포함 여부 또는 별도 env 결정.
