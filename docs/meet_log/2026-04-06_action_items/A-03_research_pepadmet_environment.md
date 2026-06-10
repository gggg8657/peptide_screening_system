# pepADMET 동결 환경 조사 (V-02b 후속)

**조사일**: 2026-05-20
**조사자**: researcher subagent
**상위 보고**: `../../../_workspace/pepadmet_local/V02-V03_validation_2026-05-20.md`

---

## 검색 전략 (재현 가능성)

| 단계 | 소스 | 쿼리/URL |
|------|------|---------|
| 1 | WebFetch | `https://github.com/ifyoungnet/pepADMET` (root 파일 목록) |
| 2 | WebFetch | `https://github.com/ifyoungnet/pepADMET/tree/main/requirements` (버전 핀) |
| 3 | WebFetch | `https://github.com/ifyoungnet/pepADMET/blob/main/calculate_descriptors.py` (import 분석) |
| 4 | WebFetch | `https://github.com/ifyoungnet/pepADMET/issues` (Issue 검색) |
| 5 | WebFetch | `https://github.com/gadsbyfly/PyBioMed/issues` (동일 에러 검색) |
| 6 | WebFetch | `https://github.com/gadsbyfly/PyBioMed/blob/master/PyBioMed/PyMolecule/estate.py` (에러 추적) |
| 7 | WebFetch | `https://github.com/alexarnimueller/modlAMP/blob/master/modlamp/descriptors.py` (modlamp 분석) |
| 8 | WebFetch | `https://discuss.pytorch.org/t/running-pytorch-1-13-on-h100/212333` (sm_90 호환) |
| 9 | WebFetch | `https://www.dgl.ai/pages/start.html` (DGL 호환 행렬) |
| 10 | WebFetch | `https://docs.nvidia.com/deeplearning/frameworks/dgl-release-notes/rel-25-01.html` (NVIDIA DGL H100) |
| 11 | WebFetch | `https://github.com/swansonk14/admet_ai` (ADMET-AI 분석) |
| 12 | WebSearch | `pepADMET github "_vectSt6vectorIiSaIiEE" "__round__" error calculate_descriptors` |
| 13 | WebSearch | `DGL PyTorch sm_90 H100 compatibility matrix 2024 2025` |

---

## 1. 공식 동결 환경 (실측 기반)

### 발견 여부: **부분 존재** (requirements 파일 1개, conda environment.yml 없음)

| 파일 | 존재 | 비고 |
|------|------|------|
| `requirements` (텍스트, 루트 위치) | **있음** | 11개 패키지 버전 핀 |
| `environment.yml` | **없음** | — |
| `requirements.txt` | **없음** | (`requirements`라는 확장자 없는 파일만 존재) |
| `pyproject.toml` | **없음** | — |
| `Dockerfile` | **없음** | — |
| `INSTALL.md` | **없음** | — |
| `conda export` / Docker Hub 이미지 | **없음** (확인 불가) | 저자에게 직접 문의 필요 |

### 공식 `requirements` 파일 (커밋 2eaaea9 기준, 완전 목록)

| 패키지 | 명시 버전 |
|--------|---------|
| scikit-learn | 1.0.2 |
| python | 3.7.16 |
| numpy | 1.21.5 |
| pandas | 1.3.5 |
| tqdm | 4.65.0 |
| **dgl** | **0.4.3** |
| PyBioMed | 1.0 |
| rdkit | 2020.09.1.0 |
| **modlamp** | **4.3.0** |
| openbabel | 3.1.1 |
| **torch** | **1.13.1** |

**비고**: 우리 환경의 실측값(`RDKit 2022.09.5`)이 공식 명시 버전(`RDKit 2020.09.1.0`)과 다름 — 이 차이가 에러의 원인으로 유력.

### 저자 별도 동결 환경 공개 여부

- 검색 결과 발견 안 됨.
- 웹 플랫폼 `https://pepadmet.ddai.tech/documentation` 은 웹 서비스 형태만 소개하며 로컬 설치 가이드 없음.
- 저자 연락처: Prof. Jie Dong, jiedong@csu.edu.cn (README 기재)

---

## 2. GitHub Issues 동일 에러 사례

### pepADMET 레포 (https://github.com/ifyoungnet/pepADMET)

- **발견 결과**: Issues 0건 (오픈·클로즈드 모두 없음).
- `_vectSt6vectorIiSaIiEE`, `__round__`, `calculate_descriptors` 에러 보고 없음.
- 저자/메인테이너 응답: 확인 불가 (Issue 없음).

### PyBioMed 레포 (https://github.com/gadsbyfly/PyBioMed)

- `_vectSt6vectorIiSaIiEE` / `__round__` 관련 Issue: **발견 안 됨**.
- 확인된 관련 Issue:
  - **Issue #11** (2020-05-11): `AttributeError: type object 'PeriodicTable' has no attribute 'nameTable'` — Kappa Descriptor 계산 실패, 해결 응답 없음, 열린 상태.
  - **Issue #3, #22** (2020~2023): Python 3 호환성 결여 보고 다수.
  - **Issue #18** (2022): `AttributeError: 'url' has no attribute 'urlretrieve'` — Python 3 urllib 변경 대응 미비.
- RDKit 버전 명시 없음 (Issue #20에서 질문했으나 미응답).

### 결론

동일 에러에 대한 공개 Issue/해결 사례 없음. 버그 보고 자체가 이루어지지 않은 상태.

---

## 3. 에러 근본 원인 분석 (문헌 + 소스코드 추적)

### 에러 메시지 해석

```
type _vectSt6vectorIiSaIiEE doesn't define __round__ method
```

- `_vectSt6vectorIiSaIiEE`: C++ 이름 맹글링 — `std::vector<int, std::allocator<int>>`의 Boost.Python 래퍼 타입 이름. **RDKit 내부 타입**.
- 에러 발생 경로: Python `round()` 내장 함수가 이 타입에 `__round__` 메서드를 요구했으나 미정의 → `TypeError`.

### 소스코드 추적 결과

`calculate_descriptors.py`가 호출하는 계층:

```
calculate_descriptors.py
  └─ PyBioMed.Pymolecule.GetAllDescriptor()
        └─ PyBioMed.PyMolecule.estate.py (GetEstate)
              └─ EState.Fingerprinter.FingerprintMol(mol)  ← RDKit
                    └─ 반환값 일부가 C++ _vect 타입
              └─ round(j, 3)  ← __round__ 미정의 타입에 적용 → 에러 발생
```

- `estate.py`의 `CalculateEstate()` 등 함수들이 RDKit `EState.Fingerprinter.FingerprintMol()` 반환값에 직접 `round()` 호출.
- modlamp `GlobalDescriptor.calculate_all()`은 RDKit 비의존적 (NumPy 기반) → modlamp 자체는 에러 원인 아님.

### RDKit 버전 불일치 가설

- 공식 명시: `rdkit 2020.09.1.0` → 이 버전의 EState 반환 타입은 Python `round()` 호환.
- 실측 환경: `RDKit 2022.09.5` → 이 버전에서 일부 내부 타입이 변경되어 `round()` 호환성 깨진 것으로 추정.
- 근거: RDKit 2020→2022 사이 DataStructs/EState 관련 API 변경 이력 존재 (공식 Backwards Incompatible Changes 문서 참고).

### PyBioMed/modlamp 호환성 매트릭스 (조사 결과 기반)

| PyBioMed | RDKit | Python | 상태 |
|----------|-------|--------|------|
| 1.0 | 2020.09.1.0 | 3.7.x | **저자 명시 조합** (검증 필요) |
| 1.0 | 2022.09.5 | 3.7.12 | **우리 환경** — 에러 발생 실증 |
| 1.0 | 2022.09.x 이상 | 3.8+ | 추정 비호환 (확인 안 됨) |

**PyBioMed는 Python 3 공식 지원 미완료** (Issue #3, #22 참고). 유지보수 중단 상태.

---

## 4. sm_90 호환 PyTorch + DGL 매트릭스

### PyTorch sm_90 (H100) 지원

- **PyTorch 1.13.x + CUDA 11.7**: sm_90 **비지원** (H100 Hopper 아키텍처 지원은 CUDA 11.8+부터)
  - 출처: PyTorch GitHub Issue #90761, PyTorch Forum "Running PyTorch 1.13 on H100"
- **PyTorch 2.0+**: sm_90 **정식 지원** (CUDA 11.8 이상 빌드 필요)
- **PyTorch 2.1+**: sm_90 **권장** (CUDA 12.x 지원 포함)
- 경고 없는 안정 운영 최소: **PyTorch >= 2.0 + CUDA >= 11.8**

### DGL 호환 행렬 (공식 dgl.ai install 페이지 기준, 2024-2025)

| DGL | PyTorch | CUDA | sm_90 (H100) |
|-----|---------|------|--------------|
| 0.4.3 | 1.13.x | 11.7 | **비지원** |
| 1.0+ | 2.0 | 11.8 | 지원 |
| 1.1+ | 2.1 | 11.8 / 12.1 | 지원 |
| 2.5 (NVIDIA DGL 25.01) | 2.x | 12.8 | **공식 H100 지원** (Pascal, Volta, Turing, Ampere, Hopper 전부) |

- NVIDIA 공식 DGL 컨테이너(DGL Release 25.01): DGL 2.5, CUDA 12.8, H100 공식 타겟.
- pepADMET의 `dgl 0.4.3`은 H100 환경에서 sm_90 경고와 함께 동작하나 최적화·안정성 미보장.

### DGL API 호환성 주의사항

- DGL 0.x → 1.x 사이 주요 API 변경 존재 (graph construction, feature API 등).
- pepADMET `build_graph_dataset.py` 및 `My_GNN.py`가 dgl 0.4 API 사용 확정 (`construct_RGCN_bigraph_from_smiles` 등).
- DGL 1.x/2.x 업그레이드 시 `dgl.graph()`, `dgl.heterograph()` API 호환성 검토 필요.

---

## 5. 대안: ADMET-AI 활용 가능성

| 항목 | 내용 |
|------|------|
| 레포 | https://github.com/swansonk14/admet_ai |
| 논문 | Swanson et al. 2024, *Bioinformatics* (Chemprop-RDKit 기반) |
| 설치 | `pip install admet-ai`, Python 3.14 conda 예시 |
| 모델 아키텍처 | Chemprop v2 (GNN) + RDKit 200개 물리화학적 피처 |
| PyTorch 버전 | 미명시 (Chemprop v2 기준 modern PyTorch 호환, sm_90 지원 가능성 높음) |
| 입력 방식 | SMILES 지원 (텍스트/CSV), RDKit 의존 |

**펩타이드 처리 가능 여부**: 기술적으로 SMILES 입력 가능하나,
- 펩타이드 특화 데이터셋 없음 (TDC 소분자 ADMET 데이터셋 기반).
- pepADMET의 펩타이드 특화 endpoint (용혈성, 세포 투과성, 항균 활성, 펩타이드 반감기 등) 포함하지 않음.
- 펩타이드 대체 도구로는 **pepADMET 이외 대안 없음** (펩타이드 특화 포괄 ADMET 도구 부재).

**대체 시 장단점**:

| 구분 | 장점 | 단점 |
|------|------|------|
| ADMET-AI | sm_90 호환, 유지보수 활성, pip install 간단 | 펩타이드 endpoint 없음, 소분자 훈련 데이터 |
| pepADMET (현재) | 펩타이드 특화 2133 descriptor + GNN | 환경 깨짐, 유지보수 중단, D-AA 부분 지원 불명확 |

---

## 6. PRST_N_FM 적용 권장사항

### 최단 해결 경로: 옵션 A (RDKit 버전 다운그레이드)

**전제**: `_vectSt6vectorIiSaIiEE` 에러가 RDKit 버전 불일치에서 발생한다는 가설 기반.

**옵션 A — RDKit 2020.09.1 다운그레이드** (권장, 예상 1~2시간)
```bash
conda activate pepadmet
conda install rdkit=2020.09.1 -c rdkit -c conda-forge
python calculate_descriptors.py  # 에러 해소 여부 검증
```
- 위험: `2020.09.1` 버전이 현재 conda 채널에서 제공 안 될 가능성 (구버전 채널 탐색 필요).
- 대안: `conda install -c conda-forge rdkit=2020.09.1.0`

**옵션 B — 저자 환경 재현 (conda env from scratch)** (예상 2~4시간)
```bash
conda create -n pepadmet_clean python=3.7.16
conda activate pepadmet_clean
conda install -c conda-forge rdkit=2020.09.1.0 openbabel=3.1.1
conda install -c dglteam dgl-cuda11.7=0.4.3
pip install modlamp==4.3.0 PyBioMed==1.0
pip install torch==1.13.1+cu117 --index-url https://download.pytorch.org/whl/cu117
pip install scikit-learn==1.0.2 numpy==1.21.5 pandas==1.3.5 tqdm==4.65.0
python calculate_descriptors.py
```

**옵션 C — PyBioMed estate.py 패치** (예상 1시간, codex 위임 가능)
- `estate.py`의 모든 `round(j, 3)` 호출을 `round(float(j), 3)`으로 변경.
- RDKit _vect 타입을 float으로 명시 변환 후 round 적용.
- 위험: 다른 descriptor 계산 파일에도 동일 패턴 존재 가능 → 전수 조사 필요.

**옵션 D — PyTorch + DGL 현대화 (sm_90 완전 지원)** (예상 4~8시간, 별도 이슈)
- torch 2.1+ + dgl 1.1+ + CUDA 12.x 재설치.
- pepADMET GNN 코드의 dgl 0.4 API 의존성 패치 필요 (codex 위임 적합).
- pepADMET 에러 해소와 별개 이슈 — 병렬 진행 가능.

### 권장 실행 순서

1. **즉시 (옵션 A)**: pepadmet 환경에서 rdkit 다운그레이드 시도 → 30분 내 에러 해소 여부 확인
2. **옵션 A 실패 시 (옵션 C)**: codex에 `PyBioMed estate.py` 패치 위임 (명시적 float 변환)
3. **병렬 (옵션 D)**: engineer-infra에 sm_90 호환 torch/dgl 재설치 의뢰

### 위임 대상

| 옵션 | 위임 대상 | 예상 토큰 |
|------|---------|---------|
| A | engineer-infra (conda 조작) | 낮음 |
| B | engineer-infra | 중간 |
| C | codex (`python estate.py patch`) | 낮음 |
| D | engineer-infra | 높음 |

---

## 7. 미확인 / 검증 필요

- [ ] **RDKit 2020.09.1.0이 현재 conda 채널에서 설치 가능한지 실측** — 구버전 패키지 가용성 확인 필요
- [ ] **옵션 A 시도 후 에러 해소 여부** — 가설 검증 필요 (직접 실행 또는 engineer-infra 위임)
- [ ] **PyBioMed 다른 descriptor 파일 (`topology.py`, `charge.py` 등)에도 동일 `round()` 패턴 존재 여부** — 옵션 C 범위 확정 전 전수 조사 필요
- [ ] **저자 Jie Dong (jiedong@csu.edu.cn) 에게 동결 환경 파일 요청** — paywall/공개 자료로 확인 불가
- [ ] **pepADMET JCIM 논문 (Tan et al. 2026) 보충 자료에 환경 파일 포함 여부** — 논문 접근 필요
- [ ] **DGL 0.4 → 1.x 업그레이드 시 `build_graph_dataset.py` / `My_GNN.py` API 호환성** — 코드 전수 리뷰 필요 (codex 적합)
- [ ] **ADMET-AI가 환형 펩타이드 SMILES (SS bond, DOTA 킬레이터) 처리 가능 여부** — 소분자 훈련 기반이므로 실질 활용도 검토 필요

---

## 참고 자료 (인용)

- pepADMET GitHub: https://github.com/ifyoungnet/pepADMET (accessed 2026-05-20)
- PyBioMed GitHub: https://github.com/gadsbyfly/PyBioMed (accessed 2026-05-20)
- PyBioMed Issue #11: https://github.com/gadsbyfly/PyBioMed/issues/11
- modlAMP descriptors.py: https://github.com/alexarnimueller/modlAMP/blob/master/modlamp/descriptors.py
- PyTorch H100 Forum: https://discuss.pytorch.org/t/running-pytorch-1-13-on-h100/212333
- DGL Install Page: https://www.dgl.ai/pages/start.html
- NVIDIA DGL Release 25.01: https://docs.nvidia.com/deeplearning/frameworks/dgl-release-notes/rel-25-01.html
- ADMET-AI GitHub: https://github.com/swansonk14/admet_ai
- V-02/V-03 검증 보고서: `_workspace/pepadmet_local/V02-V03_validation_2026-05-20.md`
