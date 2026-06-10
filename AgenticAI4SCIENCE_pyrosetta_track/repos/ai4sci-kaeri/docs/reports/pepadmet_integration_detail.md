# pepADMET 통합 상세 계획서

**작성일**: 2026-04-02  
**작성자**: admet-prep (engineer-backend)  
**태스크**: Task #2 — pepADMET 통합 + SST-14 SMILES 변환 프로토타입

---

## 1. 환경 사전 점검 결과

### 1.1 conda Python 3.7.16 가용성

```
PackagesNotFoundError: python=3.7.16 not available from conda-forge
```

**결론**: Python 3.7.16은 현재 conda-forge 채널에서 제공하지 않음.

**대안**: Python 3.8.20 사용 가능 (`python=3.8.20-h4a871b0_2_cpython`)

pepADMET requirements 호환성:
- torch 1.13.1 → Python 3.8 완전 지원
- scikit-learn 1.0.2 → Python 3.8 완전 지원
- dgl 0.4.3 → **주의**: 매우 구버전, Python 3.8 + PyTorch 1.13.1 조합 재확인 필요
- PyBioMed-1.0 → pip 설치 (Python 3.8 호환)
- rdkit 2020.09.1.0 → bio-tools에 최신 rdkit 이미 설치됨 (재사용 가능)

### 1.2 RDKit 가용성

```bash
conda run -n bio-tools python3 -c "from rdkit import Chem; print('RDKit OK')"
# 출력: RDKit OK
```

**결론**: bio-tools 환경에서 RDKit 사용 가능.

### 1.3 pepADMET GitHub Clone

```bash
git clone https://github.com/ifyoungnet/pepADMET.git /tmp/pepadmet_test --depth 1
# 성공 — 클론 완료
```

**결론**: 네트워크 접근 가능, 클론 정상.

---

## 2. pepADMET 분석

### 2.1 레포 구조

```
pepADMET/
├── calculate_descriptors.py   # 2133 분자 디스크립터 계산
├── build_graph_dataset.py     # DGL 그래프 데이터셋 빌드
├── Train.ipynb                # 전체 학습 워크플로우
├── data/
│   ├── example.csv            # 입력 형식: SEQUENCE, SMILES
│   ├── example_feature_result.csv  # 출력 형식 (2133 features)
│   ├── Toxicity.csv           # 학습 데이터
│   └── Toxicity.bin           # DGL 그래프 바이너리
├── model/
│   └── toxicity_early_stop.pth  # 사전학습 GNN 모델
└── utils/
    ├── MY_GNN.py              # GNN 아키텍처
    └── weight_visualization.py
```

### 2.2 입력 형식

`data/example.csv` 형식:
```csv
SEQUENCE,SMILES
GLPALISWIKRKRL,CC[C@@H](...
IVPFLLGMVPKLVCLITKKC,CC[C@@H](...CSSC...  ← SS bond 포함 예시
```

- **SEQUENCE**: 아미노산 서열 (1문자 코드)
- **SMILES**: 완전한 분자 SMILES (SS bond는 `CSSC` 패턴으로 표현)

### 2.3 디스크립터 구성 (2133개)

| 출처 | 디스크립터 | 개수 |
|------|-----------|------|
| PyBioMed.PyProtein | AAComp (아미노산 조성) | 20 |
| PyBioMed.PyProtein | MoreauBrotoAuto (자기상관) | 240 |
| PyBioMed.PyProtein | QSO (준서열 오더) | 50 |
| PyBioMed.PyProtein | SOCN (서열 오더 결합수) | 45 |
| PyBioMed.PyProtein | Triad | 343 |
| PyBioMed.PyProtein | CTD (조성/전이/분포) | 147 |
| PyBioMed.PyProtein | DPComp (이중펩타이드 조성) | 400 |
| PyBioMed.Pymolecule | 분자 디스크립터 (RDKit 기반) | ~688 |
| modlamp | GlobalDescriptor | ~200 |

### 2.4 예측 타겟 (독성)

- `toxicity_nontoxicity`: 독성/비독성 이진 분류
- `toxicity_type_class`: 독성 유형 다중 분류
- `neurotoxicity_type_class`: 신경독성 분류
- `HC50`: 용혈 농도 (반수치사)

**주의**: 현재 공개된 사전학습 모델은 **독성 예측만** 포함. ADMET 전체(흡수/분포/대사/배설) 예측 모델은 웹서비스(pepadmet.ddai.tech)에만 있음.

---

## 3. SST-14 SMILES 변환 프로토타입

### 3.1 변환 코드

```python
from rdkit import Chem
from rdkit.Chem import AllChem, RWMol

def sst14_to_cyclic_smiles(sequence: str = "AGCKNFFWKTFTSC") -> str:
    """
    SST-14 서열을 Cys3-Cys14 이황화 결합 포함 cyclic SMILES로 변환.
    pepADMET example.csv 입력 형식과 호환.
    """
    mol = Chem.MolFromSequence(sequence)
    if mol is None:
        raise ValueError(f"Failed to parse sequence: {sequence}")
    
    # S 원자 인덱스 추출 (Cys3=idx14, Cys14=idx113)
    s_atoms = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'S']
    assert len(s_atoms) == 2, f"Expected 2 Cys, found {len(s_atoms)}"
    
    # RWMol로 SS bond 형성
    rw = RWMol(mol)
    for idx in s_atoms:
        atom = rw.GetAtomWithIdx(idx)
        atom.SetNoImplicit(True)
        atom.SetNumExplicitHs(0)
    rw.AddBond(s_atoms[0], s_atoms[1], Chem.BondType.SINGLE)
    Chem.SanitizeMol(rw)
    
    return Chem.MolToSmiles(rw.GetMol())
```

### 3.2 검증 결과

```
SST-14 Cyclic SMILES (SS bond):
C[C@H](N)C(=O)NCC(=O)N[C@H]1CSSC[C@@H](C(=O)O)NC(=O)...NC1=O

분자량: 1637.91 Da
기대값: ~1638 Da  ✓ 일치

SS bond 패턴 (CSSC): True  ✓ example.csv 형식과 일치
```

### 3.3 pepADMET 입력 CSV 생성 예시

```python
import pandas as pd

def build_pepadmet_input(candidates: list[dict]) -> pd.DataFrame:
    """
    Silo B 후보군 → pepADMET example.csv 형식 변환
    candidates: [{"sequence": "AGCKNFFWKTFTSC", "has_ss": True}, ...]
    """
    rows = []
    for c in candidates:
        smiles = sst14_to_cyclic_smiles(c["sequence"])
        rows.append({"SEQUENCE": c["sequence"], "SMILES": smiles})
    return pd.DataFrame(rows)
```

---

## 4. 통합 전략 및 리스크

### 4.1 권장 conda 환경 설계

```yaml
# environment_pepadmet.yml
name: pepadmet
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.8
  - pip
  - pip:
    - torch==1.13.1+cpu  # CPU fallback (독성 예측만이면 CPU 충분)
    - scikit-learn==1.0.2
    - numpy==1.21.5
    - pandas==1.3.5
    - tqdm==4.65.0
    - PyBioMed==1.0
    - rdkit==2022.09.5   # 2020.09.1 대신 최신 호환 버전
    - modlamp==4.3.0
    - openbabel-wheel     # openbabel 3.1.1 대체
    - dgl==0.9.1          # 0.4.3 대신 PyTorch 1.13.1 호환 최신 버전
```

### 4.2 리스크 및 대응

| 리스크 | 심각도 | 대응 방안 |
|--------|--------|----------|
| dgl 0.4.3 설치 불가 | 높음 | dgl 0.9.x 또는 1.x 사용, API 호환 확인 |
| PyBioMed 1.0 pip 설치 실패 | 중간 | fork/로컬 설치 또는 수동 descriptor 계산 |
| 웹 전용 ADMET (흡수/분포 등) | 높음 | PharmPapp 병용 (pepADMET = 독성만, PharmPapp = 나머지) |
| openbabel 설치 복잡도 | 중간 | openbabel-wheel (pip) 또는 conda-forge |
| 테더링 환경 대용량 | 중간 | PyTorch CPU only (~500MB), DGL GPU 제외 |

### 4.3 웹 API 대안 (로컬 설치 불가 시)

pepADMET 공식 웹서비스: `https://pepadmet.ddai.tech`
- REST API 제공 여부 미확인 → 추가 조사 필요
- 배치 처리 가능 여부 미확인

**권장**: 로컬 설치 우선 시도 → 실패 시 웹 배치 제출 + 결과 파싱

---

## 5. 구현 로드맵

### Phase 1: 환경 구성 (즉시)

```bash
# Step 1: pepadmet conda env 생성
conda create -n pepadmet python=3.8 -y

# Step 2: 기본 패키지 설치
conda run -n pepadmet pip install torch==1.13.1 scikit-learn==1.0.2 numpy==1.21.5 pandas==1.3.5

# Step 3: 생물정보 패키지
conda run -n pepadmet pip install modlamp tqdm openbabel-wheel
conda run -n pepadmet pip install git+https://github.com/gadsbyfly/PyBioMed.git

# Step 4: DGL (PyTorch 1.13.1 호환)
conda run -n pepadmet pip install dgl==0.9.1 -f https://data.dgl.ai/wheels/repo.html
```

### Phase 2: SMILES 변환 모듈 (본 프로토타입 기반)

파일: `pipelines/silo_b/src/smiles_converter.py`

```python
# 함수 구현 완료 (Section 3.1 참조)
# 추가 구현 필요:
# - peptide_to_smiles(seq, ss_bonds=None)  # 범용 SS bond 지정
# - validate_smiles(smiles)               # RDKit 유효성 검사
# - batch_convert(sequences)             # 배치 처리
```

### Phase 3: pepADMET 래퍼 (환경 확인 후)

파일: `pipelines/silo_b/src/pepadmet_scorer.py`

```python
class PepADMETScorer:
    def __init__(self, model_path: str, env: str = "pepadmet"):
        self.model_path = model_path
        self.env = env
    
    def predict_toxicity(self, candidates: list[dict]) -> pd.DataFrame:
        """
        candidates: [{"sequence": "...", "smiles": "..."}, ...]
        returns: DataFrame with toxicity predictions
        """
        ...
    
    def run_as_subprocess(self, input_csv: str) -> pd.DataFrame:
        """conda run -n pepadmet 방식으로 격리 실행"""
        ...
```

### Phase 4: 파이프라인 통합

통합 위치: `pipelines/silo_b/src/scoring.py` 의 `MultiObjectiveScorer`

```python
# 추가 스코어 항목
scores["pepadmet_toxicity"] = pepadmet_scorer.predict_toxicity(candidate)
scores["pepadmet_hc50"] = ...  # 용혈 독성
```

---

## 6. 요약

| 항목 | 결과 |
|------|------|
| Python 3.7.16 가용성 | ✗ 없음 → 3.8.20 사용 |
| RDKit (bio-tools) | ✓ 사용 가능 |
| SST-14 cyclic SMILES | ✓ 생성 성공 (MW=1637.91, CSSC 패턴 확인) |
| pepADMET clone | ✓ 성공 |
| 즉시 통합 가능 범위 | SMILES 변환 + 독성 예측 (로컬) |
| 추가 조사 필요 | dgl 0.4.3→0.9 호환성, 전체 ADMET 웹API |

**다음 액션**: pepadmet conda env 실제 생성 + dgl 설치 테스트 → `smiles_converter.py` 구현
