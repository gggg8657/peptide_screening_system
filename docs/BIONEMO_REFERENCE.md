# BioNeMo / NVIDIA NIM API 완전 가이드

> **NVIDIA BioNeMo Platform -- 생체분자 AI 모델 API**
> API Catalog: https://build.nvidia.com
> 문서: https://docs.nvidia.com/nim/bionemo/
> 인증: `nvapi-` 접두사 API 키 (모든 모델 공통)
> GPU 요구사항: **불필요** (호스팅 API 사용 시)

---

## 목차

1. [개요](#개요)
2. [인증 및 공통 설정](#인증-및-공통-설정)
3. [소분자 생성 -- MolMIM](#소분자-생성----molmim)
4. [소분자 생성 -- GenMol](#소분자-생성----genmol)
5. [분자 도킹 -- DiffDock](#분자-도킹----diffdock)
6. [바인더 백본 설계 -- RFdiffusion](#바인더-백본-설계----rfdiffusion)
7. [역접힘 서열 설계 -- ProteinMPNN](#역접힘-서열-설계----proteinmpnn)
8. [구조 예측 -- ESMFold](#구조-예측----esmfold)
9. [단백질 언어 모델 -- ESM2](#단백질-언어-모델----esm2)
10. [복합체 예측 -- OpenFold3](#복합체-예측----openfold3)
11. [복합체 예측 -- Boltz-2](#복합체-예측----boltz-2)
12. [구조 예측 -- AlphaFold2 / AlphaFold2-Multimer](#구조-예측----alphafold2--alphafold2-multimer)
13. [MSA 생성 -- MSA-Search (ColabFold)](#msa-생성----msa-search-colabfold)
14. [DNA 기반 모델 -- Evo2-40B](#dna-기반-모델----evo2-40b)
15. [모델 선택 가이드](#모델-선택-가이드)
16. [응용 워크플로우](#응용-워크플로우)

---

## 개요

NVIDIA BioNeMo는 생체분자 AI 모델을 호스팅 API(build.nvidia.com)로 제공하는 플랫폼입니다. 로컬 GPU 없이 HTTP 요청만으로 단백질 구조 예측, 분자 생성, 도킹, 단백질 설계 등을 수행할 수 있습니다.

### 사용 가능한 모델 전체 목록

| 모델 | 제공자 | 기능 | 상태 |
|------|--------|------|------|
| **MolMIM** | NVIDIA | 소분자 생성/QED 최적화 | 사용 중 |
| **GenMol** | NVIDIA | Fragment-based 소분자 생성 | 미사용 |
| **DiffDock** | MIT | Blind molecular docking | 사용 중 |
| **RFdiffusion** | IPD (Baker Lab) | De novo 바인더 백본 설계 | 사용 중 |
| **ProteinMPNN** | IPD (Baker Lab) | 역접힘 (backbone→sequence) | 사용 중 |
| **ESMFold** | Meta/NVIDIA | Alignment-free 구조 예측 | 사용 중 |
| **ESM2-650M** | Meta | 단백질 언어 모델/임베딩 | 미사용 |
| **OpenFold3** | OpenFold | AlphaFold3 재구현 (복합체) | 미사용 |
| **OpenFold2** | OpenFold | AlphaFold2 재구현 | 미사용 |
| **Boltz-2** | MIT | 복합체 구조 + 친화도 예측 | 미사용 |
| **AlphaFold2** | DeepMind | 단백질 구조 예측 | 미사용 |
| **AlphaFold2-Multimer** | DeepMind | 복합체 구조 예측 | 미사용 |
| **MSA-Search** | ColabFold | 서열 → MSA 생성 | 미사용 |
| **Evo2-40B** | ARC | DNA foundation model | 미사용 |

---

## 인증 및 공통 설정

### API 키 발급

1. https://build.nvidia.com 접속
2. NVIDIA 계정 로그인
3. 원하는 모델 페이지에서 **"Get API Key"** 클릭
4. `nvapi-`로 시작하는 키 복사

### 키 설정

```bash
# 방법 1: 키 파일 (권장)
echo "nvapi-YOUR_KEY" > molmim.key

# 방법 2: 환경변수
export NVIDIA_API_KEY="nvapi-YOUR_KEY"

# 방법 3: .env 파일
echo 'NGC_CLI_API_KEY=nvapi-YOUR_KEY' > bionemo/.env
```

### 공통 API 호출 패턴

```python
import requests

API_KEY = "nvapi-YOUR_KEY"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

# POST 요청
response = requests.post(
    "https://health.api.nvidia.com/v1/biology/{org}/{model}/{endpoint}",
    headers=headers,
    json=payload,
    timeout=120,
)
result = response.json()
```

### 프로젝트 클라이언트 구조

```
bionemo/
├── api_base.py          # NVIDIABaseClient (공통 베이스)
├── molmim_client.py     # MolMIMClient
├── diffdock_client.py   # DiffDockClient
├── rfdiffusion_client.py # RFdiffusionClient
├── proteinmpnn_client.py # ProteinMPNNClient
└── esmfold_client.py    # ESMFoldClient
```

---

## 소분자 생성 -- MolMIM

> **Molecular Mutual Information Machine**
> 엔드포인트: `health.api.nvidia.com/v1/biology/nvidia/molmim/generate`
> 파라미터: 65.2M | 학습: ZINC-15 (1.54B 분자)
> 클라이언트: `bionemo/molmim_client.py`

### 기능

시드 SMILES 분자로부터 새로운 분자를 생성합니다. CMA-ES 알고리즘으로 QED(약물유사성) 또는 plogP를 최적화할 수 있습니다.

### 사용법

```python
from molmim_client import MolMIMClient

client = MolMIMClient()

# CMA-ES QED 최적화
molecules = client.generate(
    smi="c1ccc2c(c1)c(=O)n(c(=O)[nH]2)CC(=O)O",  # SSTR2 작용제 scaffold
    num_molecules=10,
    algorithm="CMA-ES",
    property_name="QED",
    min_similarity=0.3,
    particles=30,
    iterations=5,
)

for mol in molecules:
    print(f"SMILES: {mol['sample']:60s}  QED: {mol['score']:.4f}")
```

### 파라미터

| 파라미터 | 기본값 | 범위 | 설명 |
|---------|--------|------|------|
| `smi` | (필수) | - | 시드 SMILES |
| `algorithm` | `"CMA-ES"` | `"CMA-ES"`, `"none"` | 최적화 vs 랜덤 |
| `num_molecules` | 10 | 1~100 | 생성 수 |
| `property_name` | `"QED"` | `"QED"`, `"plogP"` | 최적화 대상 |
| `minimize` | `false` | - | true=최소화, false=최대화 |
| `min_similarity` | 0.3 | 0~0.7 | Tanimoto 최소 유사도 |
| `particles` | 30 | 2~1000 | CMA-ES 파티클 수 |
| `iterations` | 5 | 1~1000 | CMA-ES 반복 |

### 호스팅 vs Self-hosted

| 엔드포인트 | 호스팅 | Self-hosted | 설명 |
|-----------|--------|------------|------|
| `/generate` | O | O | CMA-ES / 랜덤 생성 |
| `/embedding` | X | O | SMILES→512차원 벡터 |
| `/hidden` | X | O | SMILES→잠재 표현 |
| `/decode` | X | O | 잠재 표현→SMILES |
| `/sampling` | X | O | 잠재공간 샘플링 |

---

## 소분자 생성 -- GenMol

> **Fragment-Based Discrete Diffusion**
> 엔드포인트: `health.api.nvidia.com/v1/biology/nvidia/genmol/generate`
> 클라이언트: 미구현 (curl/requests 직접 사용)

### 기능

Fragment 기반 이산 확산(discrete diffusion)으로 분자를 생성합니다. 마스킹된 SMILES에서 새로운 분자 조각을 생성할 수 있어, MolMIM보다 세밀한 제어가 가능합니다.

### 사용법

```python
import requests

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

# 기본 생성
payload = {
    "smiles": "c1ccc2c(c1)[nH]cc2CC(=O)NC",  # 인돌 scaffold
    "num_molecules": 20,
    "temperature": 1.0,
    "noise": 0.5,
    "step_size": 1,
    "scoring": "QED",
    "unique": True,
}

resp = requests.post(
    "https://health.api.nvidia.com/v1/biology/nvidia/genmol/generate",
    headers=headers,
    json=payload,
    timeout=120,
)
result = resp.json()

for mol in result.get("molecules", []):
    print(f"SMILES: {mol['smiles']}  Score: {mol.get('score', 'N/A')}")
```

### 마스크 기반 생성 (Fragment Growing)

```python
# [MASK] 토큰으로 특정 위치만 새로 생성
payload = {
    "smiles": "c1ccc2c(c1)[nH]cc2[MASK]",  # 인돌 + 새 fragment
    "num_molecules": 10,
    "temperature": 0.8,
}
```

### 파라미터

| 파라미터 | 기본값 | 범위 | 설명 |
|---------|--------|------|------|
| `smiles` | (필수) | - | 시드 SMILES (마스크 가능) |
| `num_molecules` | 10 | 1~1000 | 생성 수 |
| `temperature` | 1.0 | 0.1~2.0 | 다양성 (높을수록 다양) |
| `noise` | 0.5 | 0~1.0 | 노이즈 수준 |
| `step_size` | 1 | - | Diffusion step 크기 |
| `scoring` | `"QED"` | `"QED"`, `"LogP"` | 스코어링 기준 |
| `unique` | `true` | - | 중복 제거 |

### MolMIM vs GenMol 비교

| 항목 | MolMIM | GenMol |
|------|--------|--------|
| 방법 | VAE + CMA-ES | Discrete diffusion |
| 제어 | 전체 분자 최적화 | Fragment 수준 제어 |
| 마스킹 | 불가 | `[MASK]` 지원 |
| 생성 수 | 1~100 | 1~1000 |
| 최적화 | QED, plogP | QED, LogP |
| 유사도 제어 | `min_similarity` | `noise`, `temperature` |
| 적합한 경우 | 시드 기반 전체 최적화 | 특정 fragment 변경/확장 |

---

## 분자 도킹 -- DiffDock

> **Diffusion-Based Molecular Docking**
> 엔드포인트: `health.api.nvidia.com/v1/biology/mit/diffdock`
> 클라이언트: `bionemo/diffdock_client.py`

### 기능

단백질(PDB) + 리간드(SDF/SMILES) 입력으로 3D 결합 포즈를 예측합니다. Blind docking(바인딩 사이트 미지정)을 지원합니다.

### 사용법

```python
from diffdock_client import DiffDockClient

client = DiffDockClient()

# PDB + SDF 파일 도킹
result = client.dock_from_files(
    protein_pdb_path="results/sstr2_docking/sstr2_receptor.pdb",
    ligand_sdf_path="ligand.sdf",
    num_poses=10,
)

# SMILES로 도킹 (RDKit 자동 변환)
result = client.dock_smiles(
    protein_pdb_path="results/sstr2_docking/sstr2_receptor.pdb",
    smiles="Cn1c(=O)c(C(=O)O)c(CC(=O)C(C)(C)C)c2ccccc21",
    num_poses=5,
)

# 결과: 포즈별 PDB 텍스트 + confidence score
for i, pose_pdb in enumerate(result.get("trajectory", [])):
    with open(f"pose_{i}.pdb", "w") as f:
        f.write(pose_pdb)
```

### 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `protein` | (필수) | PDB 문자열 |
| `ligand` | (필수) | SDF 문자열 |
| `num_poses` | 10 | 생성 포즈 수 |
| `time_divisions` | 20 | Diffusion time steps |
| `steps` | 18 | 추론 steps |

### Confidence Score 해석

| Score 범위 | 의미 |
|-----------|------|
| > -1.0 | 높은 신뢰도 결합 |
| -1.0 ~ -3.0 | 중간 신뢰도 |
| < -3.0 | 낮은 신뢰도 |

---

## 바인더 백본 설계 -- RFdiffusion

> **Generative Protein Backbone Design**
> 엔드포인트: `health.api.nvidia.com/v1/biology/ipd/rfdiffusion/generate`
> 클라이언트: `bionemo/rfdiffusion_client.py`

### 기능

타겟 단백질의 바인딩 포켓에 맞는 새로운 펩타이드/단백질 **백본 구조(CA, N, C, O)**를 de novo로 설계합니다. 출력은 백본만 포함하며, 서열은 ProteinMPNN으로 후속 설계합니다.

### 사용법

```python
from rfdiffusion_client import RFdiffusionClient

client = RFdiffusionClient()

# SSTR2 바인딩 포켓에 10~30잔기 바인더 설계
result = client.design_binder(
    pdb_path="results/sstr2_docking/sstr2_receptor.pdb",
    contigs="B1-369/0 10-30",
    hotspot_res=["B122", "B127", "B184", "B197", "B205"],
    num_designs=5,
    diffusion_steps=50,
)

backbone_pdb = result["output"]
with open("backbone_new.pdb", "w") as f:
    f.write(backbone_pdb)
```

### Contigs 문법

```
B1-369/0 10-30
  │         │
  │         └── 새 바인더: 10~30잔기 (범위 내 랜덤)
  └── 타겟: 체인 B, 잔기 1~369 (고정)

# 다른 예:
"A1-100/0 20-20"     # 정확히 20잔기 바인더
"B1-369/0 15-25"     # 15~25잔기 바인더
"A1-50/0 10-10/0 A60-100"  # scaffold 삽입
```

### Hotspot Residues

타겟의 특정 잔기에 바인더가 접촉하도록 유도합니다:

```python
hotspot_res = [
    "B122",   # ASP -- 음전하
    "B127",   # PHE -- 방향족
    "B184",   # ARG -- 양전하
    "B197",   # TRP -- 방향족 (핵심)
    "B205",   # TYR -- 수소결합
    "B272",   # PHE -- 방향족
    "B294",   # PHE -- 방향족
]
```

---

## 역접힘 서열 설계 -- ProteinMPNN

> **Inverse Folding -- Backbone to Sequence**
> 엔드포인트: `health.api.nvidia.com/v1/biology/ipd/proteinmpnn/predict`
> 클라이언트: `bionemo/proteinmpnn_client.py`

### 기능

3D 백본 구조를 입력으로 해당 구조를 안정적으로 접을 수 있는 최적 아미노산 서열을 예측합니다.

### 사용법

```python
from proteinmpnn_client import ProteinMPNNClient

client = ProteinMPNNClient()

# 백본 PDB → 서열
result = client.predict_from_file(
    pdb_path="backbone_new.pdb",
    num_seq_per_target=8,
    sampling_temp=0.2,
)

# FASTA 파싱
sequences = ProteinMPNNClient.parse_fasta(result["sequences"])
for seq in sequences:
    print(f">{seq['header']}")
    print(f" {seq['sequence']}")
```

### 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `input_pdb` | (필수) | 백본 PDB 문자열 |
| `num_seq_per_target` | 8 | 타겟당 서열 수 |
| `sampling_temp` | 0.2 | 낮을수록 보수적 (0.1~1.0) |
| `is_soluble` | `true` | 가용성 단백질 모드 |

### Sampling Temperature 가이드

| 온도 | 다양성 | 용도 |
|------|--------|------|
| 0.1 | 매우 낮음 | 가장 안정적 서열, 보수적 |
| 0.2 | 낮음 | 기본값, 안정성 우선 |
| 0.5 | 중간 | 다양한 후보 탐색 |
| 1.0 | 높음 | 최대 다양성 |

---

## 구조 예측 -- ESMFold

> **Alignment-Free Protein Structure Prediction**
> 엔드포인트: `health.api.nvidia.com/v1/biology/nvidia/esmfold`
> 파라미터: 650M | 클라이언트: `bionemo/esmfold_client.py`

### 기능

아미노산 서열만으로 3D 단백질 구조를 예측합니다. MSA(다중 서열 정렬)가 불필요하여 빠릅니다.

### 사용법

```python
from esmfold_client import ESMFoldClient

client = ESMFoldClient()

result = client.predict("AALARTIAARFRKELEA")
pdb_text = result.get("pdbs") or result.get("output", "")
plddt = result.get("mean_plddt", 0)

print(f"pLDDT: {plddt:.1f}")

with open("predicted.pdb", "w") as f:
    f.write(pdb_text)
```

### pLDDT 해석

| 범위 | 신뢰도 | 설계 판단 |
|------|--------|----------|
| > 90 | 매우 높음 | 구조 확실, 도킹에 적합 |
| 70~90 | 높음 | 신뢰 가능, 대부분 사용 가능 |
| 50~70 | 중간 | 유동 영역 가능, 주의 |
| < 50 | 낮음 | 구조 불확실, 재설계 권장 |

### AlphaFold3 vs ESMFold

| 항목 | ESMFold | AlphaFold3 |
|------|---------|-----------|
| MSA 필요 | 불필요 | 필요 (MSA-Search) |
| 속도 | 빠름 (수초) | 느림 (수분) |
| 정확도 | 중간 | 높음 |
| 복합체 | 단일 체인만 | 복합체 지원 |
| API 접근 | build.nvidia.com | 서버 전용 |
| 용도 | 빠른 검증, 스크리닝 | 최종 구조 예측 |

---

## 단백질 언어 모델 -- ESM2

> **Evolutionary Scale Modeling 2**
> 엔드포인트: `health.api.nvidia.com/v1/biology/meta/esm2-650m`
> 파라미터: 650M

### 기능

아미노산 서열을 입력으로 **고차원 임베딩 벡터**를 생성합니다. 구조 예측 없이 서열 수준에서 기능, 유사성, 변이 효과를 분석할 수 있습니다.

### 사용법

```python
import requests

payload = {
    "sequences": ["AGCKNFFWKTFTSC"],  # Somatostatin-14
}

resp = requests.post(
    "https://health.api.nvidia.com/v1/biology/meta/esm2-650m",
    headers=headers,
    json=payload,
    timeout=120,
)
result = resp.json()

# 결과: 잔기별 임베딩 (14 x 1280 차원)
embeddings = result.get("embeddings", [])
```

### 활용 방법

| 활용 | 방법 | 설명 |
|------|------|------|
| **서열 유사성** | 임베딩 코사인 유사도 | 두 펩타이드의 기능적 유사성 |
| **변이 효과 예측** | Masked language modeling | 각 위치의 아미노산 확률 → 돌연변이 영향 |
| **기능 예측** | 임베딩 → 분류기 | 결합 여부, 안정성 예측 |
| **클러스터링** | 임베딩 → UMAP/t-SNE | 펩타이드 라이브러리 구조화 |

### 변이 효과 예측 (Zero-shot)

```python
# Masked language modeling으로 각 위치의 아미노산 확률 예측
# 야생형 대비 돌연변이의 log-likelihood ratio = 변이 효과

# 예: Somatostatin W8A의 효과
# 위치 8에서 W의 확률이 A보다 훨씬 높으면 → W8이 중요
# log(P(W|context)) - log(P(A|context)) > 0 → W 선호 (A 돌연변이 해로움)
```

---

## 복합체 예측 -- OpenFold3

> **AlphaFold3 오픈소스 재구현**
> 엔드포인트: `health.api.nvidia.com/v1/biology/openfold/openfold3`
> 문서: https://docs.api.nvidia.com/nim/reference/openfold-openfold3

### 기능

단백질, DNA, RNA, 리간드를 포함하는 **복합체 구조**를 예측합니다. AlphaFold3의 PyTorch 재구현으로, 호스팅 API를 통해 프로그래밍 방식으로 접근 가능합니다.

### 사용법

```python
import requests

payload = {
    "sequences": [
        {
            "protein": {
                "id": "A",
                "sequence": "AGCKNFFWKTFTSC",  # Somatostatin
            }
        },
        {
            "protein": {
                "id": "B",
                "sequence": "MDEMKPF...SSTR2_SEQUENCE...",  # SSTR2
            }
        },
    ],
    # 선택: MSA, 템플릿, 리간드 추가 가능
}

resp = requests.post(
    "https://health.api.nvidia.com/v1/biology/openfold/openfold3",
    headers=headers,
    json=payload,
    timeout=600,
)
result = resp.json()
# 출력: mmCIF 형식 복합체 구조
```

### 입력 유형

| 입력 | 형식 | 예 |
|------|------|-----|
| 단백질 | 서열 (1문자 코드) | `"AGCKNFFWKTFTSC"` |
| DNA | 서열 | `"ATCGATCG"` |
| RNA | 서열 | `"AUCGAUCG"` |
| 리간드 | CCD 코드 또는 SMILES | `"ATP"` 또는 `"CCO"` |
| MSA | A3M 형식 | MSA-Search 출력 |
| 템플릿 | mmCIF | 유사 구조 |

### AlphaFold3 Server vs OpenFold3 API 비교

| 항목 | AlphaFold3 Server | OpenFold3 API |
|------|-------------------|--------------|
| 접근 | 웹 UI만 | REST API |
| 프로그래밍 | 불가 | Python/curl |
| 자동화 | 수동 제출 | 파이프라인 통합 |
| 리간드 | CCD만 | CCD + SMILES |
| 비용 | 무료 | API 크레딧 |

---

## 복합체 예측 -- Boltz-2

> **Biomolecular Structure & Affinity Prediction**
> 엔드포인트: `health.api.nvidia.com/v1/biology/mit/boltz2/predict`
> 출시: 2025.06 | 문서: https://docs.api.nvidia.com/nim/reference/mit-boltz2

### 기능

단백질-리간드/펩타이드 복합체의 3D 구조와 **결합 친화도(binding affinity)**를 함께 예측합니다. 구조 예측 + 친화도 예측을 하나의 모델로 수행하는 것이 핵심 차별점입니다.

### 사용법

```python
import requests

payload = {
    "sequences": [
        {
            "protein": {
                "id": "A",
                "sequence": "AALARTIAARFRKELEA",  # De novo 펩타이드
            }
        },
        {
            "protein": {
                "id": "B",
                "sequence": "MDEMKPF...SSTR2...",  # 수용체
            }
        },
    ],
    # 선택: 제약 조건, 리간드(SMILES) 추가 가능
}

resp = requests.post(
    "https://health.api.nvidia.com/v1/biology/mit/boltz2/predict",
    headers=headers,
    json=payload,
    timeout=600,
)
result = resp.json()
# 출력: 복합체 구조 + 친화도 점수
```

### 제한 사항

| 항목 | 제한 |
|------|------|
| 최대 잔기/체인 | 4,096 |
| 최대 폴리머 수 | 12 |
| 지원 유형 | 단백질, DNA, RNA, 소분자 |

### Boltz-2 vs OpenFold3 비교

| 항목 | Boltz-2 | OpenFold3 |
|------|---------|-----------|
| 기반 | 독자 아키텍처 | AlphaFold3 재구현 |
| 친화도 예측 | O (핵심 기능) | X |
| MSA 필요 | 불필요 | 선택적 |
| 출시 | 2025.06 | 2025.10 |
| 적합 용도 | 리간드 순위 매기기 | 정밀 복합체 구조 |

---

## 구조 예측 -- AlphaFold2 / AlphaFold2-Multimer

> 엔드포인트:
> - `health.api.nvidia.com/v1/biology/deepmind/alphafold2`
> - `health.api.nvidia.com/v1/biology/deepmind/alphafold2-multimer`

### 기능

- **AlphaFold2**: 단일 단백질 서열 → 3D 구조 예측 (MSA 기반)
- **AlphaFold2-Multimer**: 여러 체인의 복합체 구조 예측

### 사용법

```python
# 단일 단백질 구조 예측
payload = {
    "sequence": "AGCKNFFWKTFTSC",
}

resp = requests.post(
    "https://health.api.nvidia.com/v1/biology/deepmind/alphafold2/predict-structure-from-sequence",
    headers=headers,
    json=payload,
    timeout=600,
)

# MSA → 구조 (2단계)
# Step 1: MSA 생성
msa_resp = requests.post(
    ".../alphafold2/predict-MSA-from-sequence",
    headers=headers,
    json={"sequence": "AGCKNFFWKTFTSC"},
)

# Step 2: MSA → 구조
struct_resp = requests.post(
    ".../alphafold2/predict-structure-from-MSA",
    headers=headers,
    json={"msa": msa_resp.json()["msa"]},
)
```

### AlphaFold2 vs ESMFold vs OpenFold3

| 항목 | AlphaFold2 | ESMFold | OpenFold3 |
|------|-----------|---------|-----------|
| MSA | 필요 | 불필요 | 선택적 |
| 정확도 | 매우 높음 | 중간 | 매우 높음 |
| 속도 | 느림 | 빠름 | 느림 |
| 복합체 | Multimer만 | X | O (단백질+DNA+RNA+리간드) |
| 리간드 | X | X | O |

---

## MSA 생성 -- MSA-Search (ColabFold)

> **Multiple Sequence Alignment Search**
> 엔드포인트: `health.api.nvidia.com/v1/biology/colabfold/msa-search/predict`

### 기능

단백질 서열로부터 MSA(다중 서열 정렬)를 생성합니다. AlphaFold2, OpenFold2/3의 전처리 단계로 사용됩니다.

### 사용법

```python
payload = {
    "sequence": "MDEMKPF...SSTR2...",
    # 선택: 데이터베이스, e-value 등
}

resp = requests.post(
    "https://health.api.nvidia.com/v1/biology/colabfold/msa-search/predict",
    headers=headers,
    json=payload,
    timeout=300,
)
result = resp.json()
msa_a3m = result.get("a3m", "")

# AlphaFold2에 전달
# struct = alphafold2.predict_from_msa(msa_a3m)
```

---

## DNA 기반 모델 -- Evo2-40B

> **DNA Foundation Model**
> 엔드포인트: `health.api.nvidia.com/v1/biology/arc/evo2-40b`
> 파라미터: 40B | 출시: 2025.02

### 기능

최대 ~100만 bp 길이의 DNA 서열을 처리하는 대규모 기반 모델. 유전자 기능 예측, DNA 서열 생성, 변이 효과 예측 등을 수행합니다.

### 사용법

```python
payload = {
    "sequence": "ATGGATGAGATG...",  # DNA 서열
    # 선택: taxonomy 정보
}

resp = requests.post(
    "https://health.api.nvidia.com/v1/biology/arc/evo2-40b",
    headers=headers,
    json=payload,
    timeout=300,
)
```

### 활용

| 활용 | 설명 |
|------|------|
| 유전자 기능 예측 | Zero-shot으로 프로모터/인핸서 식별 |
| 변이 효과 | SNP/InDel의 기능적 영향 예측 |
| 서열 생성 | 새로운 유전자 서열 설계 |
| 종 특이적 분석 | 분류군(taxonomy) 조건부 예측 |

---

## 모델 선택 가이드

### 작업별 권장 모델

| 작업 | 1순위 | 2순위 | 설명 |
|------|-------|-------|------|
| **소분자 생성** | GenMol | MolMIM | GenMol=fragment 제어, MolMIM=전체 최적화 |
| **소분자 도킹** | DiffDock | - | 유일한 도킹 NIM |
| **펩타이드 백본 설계** | RFdiffusion | - | De novo 백본 생성 |
| **서열 설계 (역접힘)** | ProteinMPNN | - | 백본→최적 서열 |
| **빠른 구조 검증** | ESMFold | - | MSA 불필요, 수초 |
| **정밀 구조 예측** | OpenFold3 | AlphaFold2 | 복합체=OF3, 단일=AF2 |
| **복합체 + 친화도** | Boltz-2 | OpenFold3 | 친화도 순위=Boltz-2 |
| **서열 임베딩** | ESM2 | - | 유사성/변이 효과 분석 |
| **MSA 생성** | MSA-Search | - | AF2/OF 전처리 |
| **DNA 분석** | Evo2-40B | - | 유전체 수준 |

### 정확도 vs 속도 트레이드오프

```
빠름 ◄──────────────────────────────────────► 정확함
ESMFold     DiffDock     AlphaFold2     OpenFold3     Boltz-2
(수초)      (수십초)      (수분)          (수분)       (수분+친화도)
```

---

## 응용 워크플로우

### 워크플로우 1: 펩타이드 리간드 발굴 파이프라인

SSTR2, PSMA, FAP 등 수용체에 대한 de novo 펩타이드 바인더 발굴:

```
Step 1: 수용체 구조 준비
  AlphaFold3 Server / OpenFold3 API
  → 수용체 3D 구조
          ↓
Step 2: 바인딩 포켓 분석
  Biopython NeighborSearch
  → 핫스팟 잔기 리스트
          ↓
Step 3: De Novo 백본 설계
  RFdiffusion (contigs + hotspots)
  → 10~50개 백본 PDB
          ↓
Step 4: 서열 설계
  ProteinMPNN (temp=0.2, 8 seq/backbone)
  → 80~400개 서열
          ↓
Step 5: 빠른 구조 검증
  ESMFold (pLDDT > 70 필터)
  → 상위 후보 50~100개
          ↓
Step 6: 정밀 복합체 검증
  Boltz-2 (수용체 + 펩타이드 → 구조 + 친화도)
  또는 OpenFold3 (수용체 + 펩타이드 → ipTM)
  → 최종 후보 10~20개
          ↓
Step 7: 에너지 검증
  PyRosetta FlexPepDock refinement
  → 결합 에너지, ΔΔG, RMSD
```

### 워크플로우 2: 소분자 스크리닝 파이프라인

```
Step 1: 시드 분자 선정
  문헌/데이터베이스에서 타겟 관련 scaffold
          ↓
Step 2: 분자 생성
  MolMIM (CMA-ES QED 최적화, 100개)
  + GenMol (fragment growing, 100개)
          ↓
Step 3: 도킹
  DiffDock (각 분자 10포즈 → 2000개 포즈)
  → confidence score 기준 필터
          ↓
Step 4: 복합체 검증
  OpenFold3 (수용체 + 리간드 → 3D 복합체)
  → 상위 20개 후보
          ↓
Step 5: 시각화 / 분석
  PyMOL (인터페이스 분석, 이미지 생성)
```

### 워크플로우 3: SSTR2 타겟 방사성의약품 설계

```
Step 1: SSTR2 구조 (AlphaFold3/OpenFold3)
Step 2: 바인딩 포켓 분석 (Biopython)
Step 3: 펩타이드 설계
  ├── Arm A: Somatostatin 변이체 (ddG scanning)
  ├── Arm B: De novo (RFdiffusion → MPNN → ESMFold)
  └── Arm C: 소분자 (MolMIM/GenMol → DiffDock)
Step 4: 복합체 검증 (Boltz-2 / OpenFold3)
Step 5: 킬레이터 부착 위치 선정
  - 에너지 분해로 비결합 잔기 식별
  - N/C 말단 또는 Lys 측쇄 (비핵심 잔기)
Step 6: PyRosetta 고리화 + 안정성 최적화
  - PeptideCyclizeMover (이황화 결합)
  - D-아미노산 도입 (프로테아제 저항성)
Step 7: 최종 후보 선별
  - 결합 친화도 (Boltz-2 / FlexPepDock)
  - 구조 안정성 (pLDDT > 70)
  - 약물유사성 (QED > 0.5)
```

### NVIDIA Blueprint 참고

NVIDIA에서 제공하는 사전 구축된 워크플로우:

| Blueprint | 설명 | URL |
|-----------|------|-----|
| Protein Binder Design | RFdiffusion + ProteinMPNN 파이프라인 | [build.nvidia.com](https://build.nvidia.com/nvidia/protein-binder-design-for-drug-discovery) |
| Generative Virtual Screening | GenMol + DiffDock 파이프라인 | [build.nvidia.com](https://build.nvidia.com/nvidia/generative-virtual-screening-for-drug-discovery) |
| Genomics Analysis | fq2bam + DeepVariant | [build.nvidia.com](https://build.nvidia.com/nvidia/genomics-analysis) |

---

## 참고 자료

### 모델별 문서

| 모델 | NIM 문서 | API Reference |
|------|---------|--------------|
| MolMIM | [docs](https://docs.nvidia.com/nim/bionemo/molmim/) | [API](https://docs.api.nvidia.com/nim/reference/nvidia-molmim) |
| GenMol | [docs](https://docs.nvidia.com/nim/bionemo/genmol/) | [API](https://docs.api.nvidia.com/nim/reference/nvidia-genmol) |
| DiffDock | [docs](https://docs.nvidia.com/nim/bionemo/diffdock/) | [API](https://docs.api.nvidia.com/nim/reference/mit-diffdock) |
| RFdiffusion | [docs](https://docs.nvidia.com/nim/bionemo/rfdiffusion/) | [API](https://docs.api.nvidia.com/nim/reference/ipd-rfdiffusion) |
| ProteinMPNN | [docs](https://docs.nvidia.com/nim/bionemo/proteinmpnn/) | [API](https://docs.api.nvidia.com/nim/reference/ipd-proteinmpnn) |
| ESMFold | [docs](https://docs.nvidia.com/nim/bionemo/esmfold/) | [API](https://docs.api.nvidia.com/nim/reference/meta-esmfold) |
| ESM2 | - | [API](https://docs.api.nvidia.com/nim/reference/meta-esm2-650m) |
| OpenFold3 | - | [API](https://docs.api.nvidia.com/nim/reference/openfold-openfold3) |
| Boltz-2 | - | [API](https://docs.api.nvidia.com/nim/reference/mit-boltz2) |
| AlphaFold2 | - | [API](https://docs.api.nvidia.com/nim/reference/deepmind-alphafold2) |
| MSA-Search | - | [API](https://docs.api.nvidia.com/nim/reference/colabfold-msa-search) |
| Evo2-40B | - | [API](https://docs.api.nvidia.com/nim/reference/arc-evo2-40b) |

### 논문

| 모델 | 논문 |
|------|------|
| MolMIM | [arXiv:2208.09016](https://arxiv.org/abs/2208.09016) |
| DiffDock | [arXiv:2210.01776](https://arxiv.org/abs/2210.01776) |
| RFdiffusion | [Nature 2023](https://www.nature.com/articles/s41586-023-06415-8) |
| ProteinMPNN | [Science 2022](https://www.science.org/doi/10.1126/science.add2187) |
| ESMFold | [Science 2023](https://www.science.org/doi/10.1126/science.ade2574) |
| ESM2 | [Science 2023](https://www.science.org/doi/10.1126/science.ade2574) |
| AlphaFold2 | [Nature 2021](https://www.nature.com/articles/s41586-021-03819-2) |
| AlphaFold3 | [Nature 2024](https://www.nature.com/articles/s41586-024-07487-w) |
| Boltz-1/2 | [arXiv:2410.11117](https://arxiv.org/abs/2410.11117) |
| Evo2 | [arXiv:2502.06563](https://arxiv.org/abs/2502.06563) |
