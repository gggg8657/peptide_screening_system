# BioNeMo -- NVIDIA NIM API 클라이언트 라이브러리

NVIDIA BioNeMo 플랫폼의 5개 AI 모델을 **호스팅 API**로 사용하는 Python 클라이언트 라이브러리.
**로컬 GPU 불필요** -- HTTP 요청만 보냅니다.

---

## 아키텍처

모든 클라이언트는 `NVIDIABaseClient`를 상속하여 API 키 관리와 HTTP 통신을 공유합니다:

```
NVIDIABaseClient (api_base.py)
├── MolMIMClient      (molmim_client.py)     -- 소분자 생성/최적화
├── DiffDockClient    (diffdock_client.py)    -- 분자 도킹
├── RFdiffusionClient (rfdiffusion_client.py) -- 바인더 백본 설계
├── ProteinMPNNClient (proteinmpnn_client.py) -- 역접힘 서열 설계
└── ESMFoldClient     (esmfold_client.py)     -- 구조 예측
```

### 키 로딩 우선순위

1. 환경변수: `NGC_CLI_API_KEY` 또는 `NVIDIA_API_KEY`
2. `.env` 파일 (`bionemo/.env`)
3. 키 파일: `molmim.key` 또는 `ngc.key` (프로젝트 루트)

---

## 빠른 시작

### 1. API 키 발급

1. https://build.nvidia.com/nvidia/molmim-generate 접속
2. NVIDIA 계정으로 로그인
3. **"Get API Key"** 클릭
4. `nvapi-`로 시작하는 키 복사

### 2. 키 설정

```bash
# 프로젝트 루트에 키 파일 생성
echo "nvapi-YOUR_KEY" > ../molmim.key
```

### 3. 의존성 설치

```bash
conda activate bio-tools
pip install -r requirements.txt
```

### 4. 테스트

```bash
cd bionemo/
python molmim_client.py          # MolMIM 테스트
python -c "from diffdock_client import DiffDockClient; print('OK')"
python -c "from esmfold_client import ESMFoldClient; print('OK')"
```

---

## API 클라이언트 상세

### 1. `api_base.py` -- 공통 베이스 클래스

모든 클라이언트의 부모 클래스. 직접 사용하지 않음.

| 메서드 | 설명 |
|--------|------|
| `_load_api_key()` | 환경변수/파일에서 API 키 자동 탐색 |
| `_post(endpoint, payload)` | JSON POST 요청 + 에러 처리 |
| `_post_raw(endpoint, payload)` | Raw Response 반환 |

---

### 2. `molmim_client.py` -- 소분자 생성/최적화

**엔드포인트**: `health.api.nvidia.com/v1/biology/nvidia/molmim/generate`

시드 분자(SMILES)로부터 새로운 분자를 생성하거나 QED/plogP를 최적화합니다.

#### 사용법

```python
from molmim_client import MolMIMClient

client = MolMIMClient()

# CMA-ES로 QED 최적화
molecules = client.generate(
    smi="CCO",                 # 시드 분자
    num_molecules=10,          # 생성 수
    algorithm="CMA-ES",        # 최적화 알고리즘
    property_name="QED",       # 최적화 대상 (QED 또는 plogP)
    min_similarity=0.3,        # 최소 유사도
    particles=30,              # CMA-ES 파티클 수
    iterations=5,              # 반복 횟수
)

for mol in molecules:
    print(f"{mol['sample']:50s} QED={mol['score']:.4f}")

# 랜덤 샘플링
samples = client.sampling(
    smi="CC(=O)Oc1ccccc1C(=O)O",  # 아스피린
    num_samples=10,
    scaled_radius=1.0,
)
```

#### 파라미터

| 파라미터 | 기본값 | 범위 | 설명 |
|---------|--------|------|------|
| `smi` | (필수) | - | 시드 SMILES 문자열 |
| `algorithm` | `"CMA-ES"` | `"CMA-ES"`, `"none"` | 최적화 알고리즘 |
| `num_molecules` | 10 | 1~100 | 생성 분자 수 |
| `property_name` | `"QED"` | `"QED"`, `"plogP"` | 최적화 대상 |
| `min_similarity` | 0.3 | 0~0.7 | 시드 대비 최소 Tanimoto 유사도 |
| `particles` | 30 | 2~1000 | CMA-ES 파티클 수 |
| `iterations` | 5 | 1~1000 | CMA-ES 반복 횟수 |

> **참고**: 호스팅 API는 `/generate`만 지원. `/embedding`, `/hidden`, `/decode`는 Self-hosted NIM 필요.

---

### 3. `diffdock_client.py` -- 분자 도킹

**엔드포인트**: `health.api.nvidia.com/v1/biology/mit/diffdock`

단백질(PDB) + 리간드(SDF/SMILES) → 도킹 포즈 예측. Blind docking 지원.

#### 사용법

```python
from diffdock_client import DiffDockClient

client = DiffDockClient()

# 파일 경로로 도킹
result = client.dock_from_files(
    protein_pdb_path="sstr2_receptor.pdb",
    ligand_sdf_path="ligand.sdf",
    num_poses=10,
)

# SMILES로 도킹 (RDKit으로 자동 SDF 변환)
result = client.dock_smiles(
    protein_pdb_path="sstr2_receptor.pdb",
    smiles="CCO",
    num_poses=5,
)

# 포즈 접근
for pose in result.get("trajectory", []):
    print(pose[:200])  # PDB 텍스트
```

#### 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `protein_pdb` | (필수) | 단백질 PDB 문자열 |
| `ligand_sdf` | (필수) | 리간드 SDF 문자열 |
| `num_poses` | 10 | 생성 포즈 수 |
| `time_divisions` | 20 | Diffusion time steps |
| `steps` | 18 | 추론 steps |

> **의존성**: SMILES 도킹 시 `rdkit` 필요 (SDF 변환용). PDB/SDF 직접 전달 시 불필요.

---

### 4. `rfdiffusion_client.py` -- De Novo 바인더 백본 설계

**엔드포인트**: `health.api.nvidia.com/v1/biology/ipd/rfdiffusion`

타겟 단백질의 바인딩 포켓에 맞는 새로운 펩타이드/단백질 **백본 구조**를 생성합니다.

#### 사용법

```python
from rfdiffusion_client import RFdiffusionClient

client = RFdiffusionClient()

# SSTR2 바인딩 포켓에 10~30잔기 바인더 설계
result = client.design_binder(
    pdb_path="sstr2_receptor.pdb",
    contigs="B1-369/0 10-30",                    # 수용체 + 바인더 길이
    hotspot_res=["B122", "B127", "B197", "B205"], # 포켓 핫스팟
    num_designs=5,
    diffusion_steps=50,
)

# 결과: PDB 텍스트 (백본 좌표)
backbone_pdb = result["output"]
```

#### 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `input_pdb` | (필수) | 타겟 단백질 PDB 문자열 |
| `contigs` | (필수) | 체인 정의 (예: `"B1-369/0 10-30"`) |
| `hotspot_res` | `None` | 바인딩 핫스팟 잔기 리스트 |
| `diffusion_steps` | 50 | Diffusion 스텝 수 |

> **출력**: 백본(CA, N, C, O)만 포함된 PDB. 서열 설계를 위해 ProteinMPNN 후속 필요.

---

### 5. `proteinmpnn_client.py` -- 역접힘 (서열 설계)

**엔드포인트**: `health.api.nvidia.com/v1/biology/ipd/proteinmpnn`

3D 백본 구조를 입력으로 **최적 아미노산 서열**을 예측합니다 (Inverse Folding).

#### 사용법

```python
from proteinmpnn_client import ProteinMPNNClient

client = ProteinMPNNClient()

# 백본 PDB → 서열
result = client.predict_from_file(
    pdb_path="backbone.pdb",
    num_seq_per_target=8,
    sampling_temp=0.2,
)

# FASTA 파싱
sequences = ProteinMPNNClient.parse_fasta(result["sequences"])
for seq in sequences:
    print(f">{seq['header']}")
    print(seq['sequence'])
```

#### 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `input_pdb` | (필수) | 백본 PDB 문자열 |
| `num_seq_per_target` | 8 | 타겟당 생성 서열 수 |
| `sampling_temp` | 0.2 | 샘플링 온도 (낮을수록 보수적) |

> **주의**: `sampling_temp`는 내부적으로 `[0.2]` 형태의 리스트로 변환됩니다 (API 요구사항).

---

### 6. `esmfold_client.py` -- 구조 예측

**엔드포인트**: `health.api.nvidia.com/v1/biology/nvidia/esmfold`

아미노산 서열을 입력으로 **3D 구조(PDB)**를 예측합니다. MSA 불필요 (alignment-free).

#### 사용법

```python
from esmfold_client import ESMFoldClient

client = ESMFoldClient()

# 서열 → 구조
result = client.predict("AGCKNFFWKTFTSC")
pdb_text = result.get("pdbs") or result.get("output", "")
plddt = result.get("mean_plddt", 0)

print(f"pLDDT: {plddt:.1f}")

# PDB 파일 저장
with open("predicted.pdb", "w") as f:
    f.write(pdb_text)
```

#### 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `sequence` | (필수) | 아미노산 서열 (1문자 코드) |

#### pLDDT 해석

| 범위 | 신뢰도 | 의미 |
|------|--------|------|
| > 90 | 매우 높음 | 정확한 구조 |
| 70~90 | 높음 | 신뢰할 수 있는 구조 |
| 50~70 | 중간 | 대략적 구조, 유동 영역 가능 |
| < 50 | 낮음 | 구조 불확실 |

---

## 파이프라인 스크립트

### MolMIM 시나리오 (01~03)

| 스크립트 | 설명 | 실행 |
|---------|------|------|
| `01_embedding_similarity.py` | 4개 시드별 CMA-ES 생성 + 랜덤 vs 최적화 비교 | `python 01_embedding_similarity.py` |
| `02_molecule_generation.py` | 시드 기반 랜덤/CMA-ES/plogP 3가지 모드 | `python 02_molecule_generation.py --smi "c1ccccc1"` |
| `03_property_optimization.py` | 다단계 최적화 (라운드별 베스트 → 다음 시드) | `python 03_property_optimization.py --rounds 3` |

### SSTR2 Virtual Screening (04~07)

| 스크립트 | 단계 | 입력 | 출력 | 실행 |
|---------|------|------|------|------|
| `04_sstr2_pocket_analysis.py` | Step 0 | AF3 복합체 PDB | `binding_pocket.json`, `sstr2_receptor.pdb` | `bash ../scripts/run_pocket_analysis.sh` |
| `05_sstr2_smallmol_screen.py` | Arm 1 | 시드 SMILES + SSTR2 PDB | MolMIM 후보 + DiffDock 포즈 | `bash ../scripts/run_arm1.sh` |
| `06_sstr2_flexpep_dock.py` | Arm 2 | Somatostatin 서열 | 13개 변이체 분석 | `bash ../scripts/run_arm2.sh` |
| `07_sstr2_denovo_binder.py` | Arm 3 | SSTR2 PDB + 핫스팟 | RFdiff 백본 + MPNN 서열 + ESMFold 구조 | `bash ../scripts/run_arm3.sh` |

전체 파이프라인 일괄 실행:

```bash
bash scripts/run_sstr2_pipeline.sh
```

---

## 모델 정보

| 모델 | 파라미터 | 학습 데이터 | 논문 |
|------|---------|-----------|------|
| MolMIM | 65.2M | ZINC-15 (1.54B 분자) | [arXiv:2208.09016](https://arxiv.org/abs/2208.09016) |
| DiffDock | - | PDBBind 2020 | [arXiv:2210.01776](https://arxiv.org/abs/2210.01776) |
| RFdiffusion | - | PDB (구조 데이터) | [Nature 2023](https://www.nature.com/articles/s41586-023-06415-8) |
| ProteinMPNN | - | PDB (구조 데이터) | [Science 2022](https://www.science.org/doi/10.1126/science.add2187) |
| ESMFold | 650M | UniRef50 | [Science 2023](https://www.science.org/doi/10.1126/science.ade2574) |

---

## 파일 구조

```
bionemo/
├── README.md                       # 이 문서
├── __init__.py
├── .env.example                    # API 키 템플릿
├── requirements.txt                # pip 의존성
│
├── api_base.py                     # 공통 베이스 (NVIDIABaseClient)
├── molmim_client.py                # MolMIM 클라이언트
├── diffdock_client.py              # DiffDock 클라이언트
├── rfdiffusion_client.py           # RFdiffusion 클라이언트
├── proteinmpnn_client.py           # ProteinMPNN 클라이언트
├── esmfold_client.py               # ESMFold 클라이언트
│
├── 01_embedding_similarity.py      # MolMIM 시나리오 1
├── 02_molecule_generation.py       # MolMIM 시나리오 2
├── 03_property_optimization.py     # MolMIM 시나리오 3
├── 04_sstr2_pocket_analysis.py     # SSTR2 바인딩 포켓 분석
├── 05_sstr2_smallmol_screen.py     # SSTR2 소분자 스크리닝
├── 06_sstr2_flexpep_dock.py        # SSTR2 펩타이드 변이체
└── 07_sstr2_denovo_binder.py       # SSTR2 De Novo 바인더
```

---

## 참고 자료

- [MolMIM NIM 문서](https://docs.nvidia.com/nim/bionemo/molmim/latest/index.html)
- [DiffDock NIM 문서](https://docs.nvidia.com/nim/bionemo/diffdock/latest/index.html)
- [RFdiffusion NIM 문서](https://docs.nvidia.com/nim/bionemo/rfdiffusion/latest/index.html)
- [ProteinMPNN NIM 문서](https://docs.nvidia.com/nim/bionemo/proteinmpnn/latest/index.html)
- [ESMFold NIM 문서](https://docs.nvidia.com/nim/bionemo/esmfold/latest/index.html)
- [NVIDIA API Catalog](https://build.nvidia.com) (API 키 발급)
