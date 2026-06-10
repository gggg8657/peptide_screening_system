# infra: biopython 설치 + pepADMET 로컬 클론 보고서
**날짜**: 2026-05-20  
**담당**: engineer-infra (gate2-closure-20260520 팀)  
**Task**: #5 — biopython 설치 + pepADMET 로컬 클론 시도

---

## Part 1: biopython 설치 결과

### 결론: 이미 설치됨 ✅

```
conda env: bio-tools (Python 3.11.15)
biopython: 1.79 (이미 설치 완료)
검증 명령: conda run -n bio-tools python -c "import Bio; print(Bio.__version__)"
출력: 1.79
```

### 12 ERROR 해소 확인

| 항목 | 결과 |
|------|------|
| step07 테스트 (6개) | 6 PASSED, 0 ERROR |
| step06 테스트 | 해당 없음 (test file 없음) |
| 전체 pytest (629 items) | 617 passed, 5 failed*, 5 skipped, 2 xfailed |

> *5 failed = SSTR4 시그니처 충돌 (Task #3에서 처리 중) — biopython 무관

**결론**: biopython 관련 ImportError/ERROR 0건. 이미 사전 설치 완료 상태.

---

## Part 2: pepADMET 로컬 클론 결과

### 클론 완료 ✅

```
위치: /home/dongjukim/Documents/workspace/extern/pepADMET/
소스: https://github.com/ifyoungnet/pepADMET.git
```

### conda 환경

`pepadmet` 환경이 이미 존재하며 필요 패키지 설치 완료.

**기존 환경 (`pepadmet`):**
```
Python       3.7.12  (conda-forge)
torch        1.13.1+cu117
dgl          0.4.3
rdkit-pypi   2022.9.5
PyBioMed     1.0
modlamp      4.3.0
openbabel-wheel 3.1.1.22
scikit-learn 1.0.2
numpy        1.21.5
pandas       1.3.5
```

**이번에 추가 설치된 패키지 (headless 서버용 X11 라이브러리):**
```
xorg-libxrender  0.9.12  (openbabel plugin 로딩에 필요)
xorg-libxext     1.3.7
xorg-libx11      1.8.13  (업데이트)
```

**패치된 파일:**
```
파일: miniforge3/envs/pepadmet/lib/python3.7/site-packages/PyBioMed/PyMolecule/constitution.py
이유: RDKit 2022.9.5에서 일부 constitional descriptor가 vector 반환 → round() 실패
수정: vector 타입 처리 + try/except 추가 (0.0으로 fallback)
```

---

## Part 3: SST14 Inference 결과

### 입력
```
Sequence: AGCKNFFWKTFTSC
SMILES:   N[C@@H](C)C(=O)NCC(=O)N[C@@H](CSSC[C@@H]... (Cys3-Cys14 SS bond)
```

### 분자 그래프
```
Nodes: 121 atoms
Edges: 250 bonds (undirected)
```

### 기술자 계산
```
계산된 features: 2068 (2133 필요 → 65개 0-padding)
실패 원인: PyBioMed GetAllDescriptor() 일부 descriptor RDKit 호환성 문제
PyProtein + modlamp 기술자: 완전 계산 성공
PyMolecule 기술자: constitution.py 패치 후 부분 성공
```

### 모델 예측 (toxicity_early_stop.pth)

```json
{
  "toxicity_nontoxicity": 1.0,
  "toxicity_type_class": {
    "class": 4,
    "probs": [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
  },
  "neurotoxicity_type_class": {
    "class": 3,
    "probs": [0.0, 0.0, 0.0, 1.0]
  },
  "HC50": -27939.2637
}
```

> ⚠️ **신뢰도 경고**: extreme probability (1.0/0.0) + 음수 HC50은 비정상적.
> 원인 추정: 65개 zero-padding (2068/2133) + RDKit/PyBioMed 버전 불일치.
> 재학습 또는 정확한 2133 기술자 계산 없이는 수치 신뢰 불가.

---

## Part 4: 29 endpoint 출력 일치 확인

| 항목 | 결과 |
|------|------|
| GitHub repo 제공 endpoints | **4개** (toxicity_nontoxicity, toxicity_type_class, neurotoxicity_type_class, HC50) |
| 웹 플랫폼 ADMET endpoints | **29개** (https://pepadmet.ddai.tech) |
| 로컬에서 29개 재현 가능 여부 | ❌ **불가** — 나머지 25개 모델/코드 GitHub에 없음 |

**결론**: pepADMET GitHub repo는 독성 예측 모듈(4 tasks)만 공개. 전체 29 ADMET endpoint는 웹 플랫폼 전용. 로컬 29-endpoint 재현 불가.

---

## 요약

| 항목 | 결과 | 비고 |
|------|------|------|
| biopython 설치 (bio-tools) | ✅ 이미 1.79 설치 | ERROR 0건 |
| step06/07 pytest ERROR 해소 | ✅ 6 PASSED | biopython 무관 |
| pepADMET 클론 | ✅ /extern/pepADMET/ | |
| pepadmet conda env | ✅ 기존 env 활용 | xorg-libxrender 추가 |
| SST14 inference | ✅ 실행 완료 | 수치 신뢰도 제한적 |
| 29 endpoint 재현 | ❌ 불가 | repo에 4 tasks만 있음 |
| V-04 / V-05 | ⚠️ 미해결 | 29-endpoint 로컬화 불가 |

---

## conda env 변경사항 (pepadmet)

```bash
# 추가된 패키지
conda install -n pepadmet -y xorg-libxrender xorg-libxext xorg-libx11 -c conda-forge

# 검증
conda run -n pepadmet python -c "
import torch, dgl, rdkit
from PyBioMed.PyProtein import PyProtein
import modlamp
print('All imports OK')
"
```

## Action Items (다음 단계)

1. **V-04/V-05 미해결**: 29-endpoint 로컬화를 위해서는 pepADMET 저자에게 모델 코드 요청 또는 웹 API 연동 구현 필요
2. **기술자 계산 정확도**: rdkit-pypi 2022.9.5 → 2020.09.1.0 다운그레이드 또는 constitution.py 완전 패치 검토
3. **HC50 이상값**: 정상 범위 학습 데이터 확인 필요 (음수는 의미 없음)
