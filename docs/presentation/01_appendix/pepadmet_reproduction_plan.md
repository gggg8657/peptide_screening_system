# pepADMET 전 모델 독립 재현 계획

**작성일**: 2026-03-23
**목표**: pepADMET (JCIM 2026, 66, 936-946) 17개 예측 모델 전체 독립 재현
**이유**: 학술 연구 — 독립 재현(independent reproduction)으로 방법론 검증 필수

---

## 1. 재현 대상 모델 5그룹 / 17개

| 그룹 | 모델 수 | 아키텍처 | 데이터 규모 | 재현 난이도 |
|------|--------|---------|-----------|:---------:|
| Toxicity | 4 (binary, 6-class, 4-class, HC50) | MLR-GAT (RGCN + MLP + Attention) | 14,660 | 낮음 (코드+모델 공개) |
| Permeability | 5 (RRCK, PAMPA, Caco2-A/C/L) | GNN + LightGBM | 7,765 | 중간 |
| Half-life | 5 (HBN, HBM, MBN, MBM, MIM) | Transfer Learning (pre-train RT → fine-tune) | 970 + 350K RT | 높음 |
| Distribution | 2 (BBB, LogD) | RF / XGBoost / SVM | 850 + 257 | 낮음 |
| Absorption | 1 (F) | RF / XGBoost / SVM | 305 | 낮음 |

---

## 2. 데이터 수집 계획

### Phase 1: 즉시 확보 가능

| DB | 데이터 | 접근 방법 | 예상 수 | 용량 |
|----|--------|---------|--------|------|
| **pepADMET GitHub** | Toxicity (14,660 + features) | `git clone` | 14,660 | <50MB |
| **UniProt** | 서열 정보 보충 | REST API (programmatic) | 필요 시 | <10MB |

### Phase 2: 공개 DB 수집 (1-2주)

| DB | 데이터 | URL | 접근 방법 | 예상 수 |
|----|--------|-----|---------|--------|
| **PEPlife2** | Half-life (혈청/혈장) | webs.iiitd.edu.in/raghava/peplife2 | REST API (`api.php`) | ~500 |
| **THPdb** | FDA 치료 펩타이드 PK | webs.iiitd.edu.in/raghava/thpdb | 웹 다운로드 | ~800 |
| **PepTherDia** | 치료 펩타이드 PK | peptherdia 웹 | CSV 다운로드 | ~600 |
| **B3Pdb** | BBB 투과 펩타이드 | webs.iiitd.edu.in/raghava/b3pdb | 웹 다운로드 | 850 |
| **Brainpeps** | BBB 투과 보충 | 논문 supplementary | 수동 | ~300 |
| **CycPeptMPDB** | 사이클릭 펩타이드 투과도 | cycpeptmpdb.com | 다운로드 | ~7,765 |
| **DBAASP v3** | 항균/세포독성 펩타이드 | dbaasp.org | 다운로드 | ~15,000 |
| **Hemolytik** | 용혈 활성 데이터 | hemolytik.com | 다운로드 | ~6,000 |

### Phase 3: RT DB (Transfer Learning pre-train)

| 출처 | 설명 | 접근 방법 | 예상 수 | 용량 |
|------|------|---------|--------|------|
| **ProteomeTools** (PXD004732) | 합성 펩타이드 RT | PRIDE Archive 다운로드 | ~350,000 | ~200-500MB |
| **AlphaPeptDeep** | RT prediction 학습 데이터 | GitHub (MannLabs) | 보충용 | <100MB |
| **Chronologer** | RT prediction 데이터 | GitHub (searlelab) | 보충용 | <50MB |

**RT DB 수집 전략**:
- 1순위: PRIDE PXD004732 (ProteomeTools) — 가장 큰 공개 합성 펩타이드 RT DB
- 2순위: AlphaPeptDeep 논문 보충자료에서 사전 정제된 RT 데이터 활용
- 형식: 서열 + retention time (분) + modification 정보

---

## 3. 재현 순서 (의존성 기반)

```
Phase A: 환경 구축 (1일)
━━━━━━━━━━━━━━━━━━━━━
  conda create -n pepadmet python=3.7
  PyTorch 1.13.1 + DGL 0.4.3 + RDKit + PyBioMed + modlAMP
  pepADMET repo clone

Phase B: 독성 모델 검증 (1일)
━━━━━━━━━━━━━━━━━━━━━━━━━━
  기존 .pth로 추론 → 논문 성능 재현 확인
  학습 코드 (Train.ipynb) 재실행 → 독립 학습 성능 비교
  ↓ 의존성 없음, GitHub 데이터로 즉시 가능

Phase C: 전통 ML 모델 (BBB, LogD, F) (3-5일)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  B3Pdb/Brainpeps → BBB 분류 모델 (RF/SVM)
  논문 supplementary → LogD 회귀 (GBT)
  논문 supplementary → F 분류 (RF/XGBoost)
  ↓ Phase 2 데이터 수집 후

Phase D: Permeability GNN (1-2주)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CycPeptMPDB → 5개 세포주별 독립 모델
  GNN 아키텍처 재구현 (MY_GNN.py 참조)
  LightGBM descriptor 모델 + GNN 그래프 모델
  ↓ Phase 2 데이터 + descriptor 계산 완료 후

Phase E: Half-life Transfer Learning (2-4주)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 1: RT DB 350K로 embedding pre-train
  Step 2: PEPlife2 + THPdb 970개로 5종 fine-tune
  ↓ Phase 3 RT DB 수집 완료 후 (가장 긴 의존성)
```

---

## 4. conda env 설계

```bash
# pepadmet env — 기존 env와 완전 분리
conda create -n pepadmet python=3.7.16
conda activate pepadmet

# 핵심 의존성
pip install torch==1.13.1+cu117 -f https://download.pytorch.org/whl/torch_stable.html
pip install dgl==0.4.3
pip install scikit-learn==1.0.2 numpy==1.21.5 pandas==1.3.5
pip install rdkit-pypi==2022.9.5  # 2020.09.1 대신 pip 호환 버전
pip install modlamp==4.3.0 openbabel-wheel==3.1.1.1
pip install PyBioMed  # 또는 git+https://github.com/gadsbyfly/PyBioMed.git
pip install lightgbm xgboost  # 전통 ML
pip install tqdm matplotlib
```

기존 env 충돌 없음:
| env | Python | PyTorch | 용도 |
|-----|--------|---------|------|
| bio-tools | 3.12 | 2.1+cu124 | ESMFold, ProteinMPNN |
| rfdiffusion | 3.9 | 1.13+cu117 | RFdiffusion |
| diffpepdock | 3.10 | 2.1+cu118 | DiffPepDock |
| **pepadmet** | **3.7** | **1.13+cu117** | **pepADMET 재현** |

---

## 5. Feature 계산 파이프라인 (2,133 features)

```python
# calculate_descriptors.py 기반 — 3종 소스 결합
from PyBioMed.PyProtein import PyProtein  # 1,245 features
from modlamp.descriptors import GlobalDescriptor  # 10 features
from rdkit.Chem import AllChem, Descriptors  # ~878 features

# 입력: (SMILES, SEQUENCE) 쌍
# 출력: 2,133차원 feature vector

# SMILES 변환 필요 (SST-14 유사체):
# 서열 → Helm notation → RDKit Mol → canonical SMILES
# Cys3-Cys14 SS bond: SMILES에 CSSC 패턴 포함
```

**SMILES 변환 전략**:
1. RDKit `Chem.MolFromSequence()` (선형 펩타이드)
2. SS bond 수동 추가: Cys3-Cys14 사이 ring closure
3. 검증: pepADMET 웹에서 동일 서열 입력 → SMILES 비교

---

## 6. 모델별 재현 상세

### 6.1 Toxicity (MLR-GAT) — 난이도: 낮음

| 항목 | 내용 |
|------|------|
| 코드 | `Train.ipynb` + `MY_GNN.py` (완전 공개) |
| 데이터 | `data/Toxicity.csv` (14,660 + 2,133 features, 공개) |
| 모델 | `toxicity_early_stop.pth` (공개) |
| 설정 | batch=128, epochs=300, patience=50, lr=1e-3, weight_decay=1e-5 |
| 검증 기준 | AUC ±0.02 이내 (binary: 0.885, 6-class: 0.949) |
| 소요 | 1일 (추론만) / 2일 (재학습 포함) |

### 6.2 BBB / LogD / F (전통 ML) — 난이도: 낮음

| 항목 | BBB | LogD | F |
|------|-----|------|---|
| 데이터 | 850 (B3Pdb) | 257 | 305 |
| 모델 | RF | GBT | RF/XGBoost |
| Feature | 2,133 → RFE-RF subset | 동일 | 동일 |
| 검증 | AUC 0.889 ±0.02 | R² 0.818 ±0.03 | AUC 0.900 ±0.02 |
| 소요 | 1일 (데이터 확보 후) | 1일 | 1일 |

### 6.3 Permeability (GNN + LightGBM) — 난이도: 중간

| 항목 | 내용 |
|------|------|
| 데이터 | CycPeptMPDB 기반 5종 (RRCK 181, PAMPA 6698, Caco2-A/C/L) |
| 아키텍처 | Dual-path: GNN (분자 그래프) + LightGBM (descriptor) |
| 핵심 구현 | `build_graph_dataset.py` 참조하여 그래프 전처리 |
| 검증 | R² 0.435-0.657 범위 (세포주별) |
| 소요 | 1-2주 (GNN 아키텍처 재구현 포함) |

### 6.4 Half-life (Transfer Learning) — 난이도: 높음

| 항목 | 내용 |
|------|------|
| **Pre-train** | RT DB ~350K → embedding 학습 |
| **Fine-tune** | 5종: HBN(182), HBM(117), MBN(106), MBM(187), MIM(378) |
| 아키텍처 | Pre-train 모델의 embedding layer → fine-tune에 parameter sharing |
| 핵심 전략 | Enzymatic cleavage features (protease cleavage site 수) 추가 |
| 검증 | R² 0.84-0.984 (조직별) |
| **병목** | RT DB 350K 수집 + 전처리 |
| 소요 | 2-4주 |

---

## 7. 검증 계획

### 재현 성능 판단 기준

| 메트릭 | 허용 범위 | 판정 |
|--------|----------|------|
| AUC (분류) | 논문 ±0.02 | 성공적 재현 |
| AUC (분류) | 논문 ±0.05 | 합리적 재현 (데이터 차이 감안) |
| R² (회귀) | 논문 ±0.03 | 성공적 재현 |
| R² (회귀) | 논문 ±0.10 | 합리적 재현 |
| R² (회귀) | 논문 -0.10 이상 차이 | 재현 실패 → 원인 분석 |

### 검증 대상 논문 성능

| 모델 | 논문 성능 | 재현 목표 (하한) |
|------|---------|----------------|
| Toxicity binary | AUC 0.885 | ≥ 0.865 |
| Toxicity 6-class | AUC 0.949 | ≥ 0.929 |
| BBB | AUC 0.889 | ≥ 0.869 |
| F | AUC 0.900 | ≥ 0.880 |
| LogD | R² 0.818 | ≥ 0.788 |
| PAMPA | R² 0.657 | ≥ 0.627 |
| HBN T½ | R² 0.840 | ≥ 0.750 |
| MBN T½ | R² 0.984 | ≥ 0.900 |

---

## 8. 위험 요소 + 대안

| 위험 | 확률 | 영향 | 대안 |
|------|:----:|:----:|------|
| RT DB 350K 수집 실패 | 중 | 높음 | AlphaPeptDeep 사전학습 모델 차용, 또는 RT 없이 half-life만으로 학습 (TL 없이 baseline) |
| PEPlife2 서버 다운 | 중 | 중 | PepTherDia/THPdb에서 보충, 논문 supplementary에서 수동 수집 |
| CycPeptMPDB 접근 불가 | 낮 | 중 | 논문 supplementary에서 데이터 추출, 또는 저자 컨택 |
| DGL 0.4.3 설치 실패 (Python 3.7 EOL) | 중 | 높음 | DGL 최신 버전 + 코드 마이그레이션, 또는 Docker 이미지 |
| PyBioMed 호환 문제 | 중 | 중 | descriptor 일부 수동 구현 또는 대체 패키지 |
| 재현 성능 미달 | 중 | 중 | 데이터 분할 차이 허용, 하이퍼파라미터 grid search 재실행 |

---

## 9. 타임라인

| 주차 | 작업 | 산출물 |
|------|------|--------|
| **W1** | env 구축 + 독성 모델 검증 + 데이터 수집 시작 | pepadmet env, toxicity 재현 보고서 |
| **W2** | BBB/LogD/F 재학습 + CycPeptMPDB 수집 | 전통 ML 3모델 재현 |
| **W3** | Permeability GNN 재구현 + RT DB 수집 | GNN 5모델 학습 시작 |
| **W4** | Permeability 완료 + Half-life TL pre-train | permeability 재현, RT embedding |
| **W5** | Half-life fine-tune 5종 + 전체 검증 | **17개 모델 전체 재현 완료** |
| **W6** | SST-14 22k 후보 일괄 ADMET 프로파일링 | 후보 ADMET 보고서 |

---

## 10. 다운로드 스크립트

`scripts/download_pepadmet.sh` — 자동/반자동 데이터 수집
- `--pack` 옵션: conda env 오프라인 이식용 tar.gz 생성
- 예상 총 용량: ~4-5GB (env + 데이터)
