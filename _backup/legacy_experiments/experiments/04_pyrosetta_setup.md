# 실험 04: PyRosetta 환경구축

## 목적

PyRosetta(Rosetta 분자 모델링의 Python 인터페이스)를 conda 환경에 설치하고 정상 동작을 확인한다. 향후 scoring, relax, docking 실험의 기반이 된다.

## 환경

- **conda env**: `bio-tools`
- **PyRosetta**: 2026.06+release (conda, RosettaCommons 채널)
- **Python**: 3.12
- **OS**: Ubuntu 22.04 (WSL2)

## 설치 방법

### Conda (권장)

```bash
conda activate bio-tools

# RosettaCommons 채널에서 설치
conda install -c https://conda.rosettacommons.org -c conda-forge pyrosetta
```

### Pip (대안)

```bash
pip install pyrosetta \
  --find-links https://west.rosettacommons.org/pyrosetta/quarterly/release
```

## 라이선스

- **학술 라이선스** 필요: https://www.rosettacommons.org/software/license-and-download
- 상업용은 별도 라이선스.
- 라이선스 없이도 conda install은 되지만, 일부 기능이 제한될 수 있음.

## 동작 확인

```bash
conda activate bio-tools
python -c "
import pyrosetta
pyrosetta.init()
print('PyRosetta version:', pyrosetta.__version__)
print('Init successful')
"
```

### 확인 결과

```
PyRosetta version: 2026.06+release.1a56185c25
Init successful
```

## 설치 포함 패키지 (bio-tools env)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| pyrosetta | 2026.06 | 분자 모델링 |
| biopython | 1.86 | 구조 파싱/변환 |
| pymol-open-source | 3.1.0 | 분자 시각화 |
| foldmason | 4.dd3c235 | 구조 정렬 |
| rdkit | 2025.03.6 | 화학 정보학 |
| meeko | 0.7.1 | AutoDock 전처리 |
| numpy | - | 수치 계산 |
| scipy | - | 과학 계산 |

## 향후 실험 계획

1. **Scoring**: PDB 구조의 Rosetta 에너지 스코어 계산
2. **Relax**: 구조 최적화 (FastRelax 프로토콜)
3. **Docking**: 리간드-단백질 도킹 (RosettaLigand)
4. **Design**: 잔기 돌연변이 효과 예측 (ddG 계산)

## 특수 사항

- PyRosetta 설치 용량이 크므로 (~1.4 GB) 디스크 여유 확인 필요.
- `pyrosetta.init()` 호출 시 Rosetta 데이터베이스를 로드하므로 첫 실행에 수 초 소요.
- bioconda에서 FoldMason 설치 시 일부 패키지(rdkit, glew, libpq)가 다운그레이드될 수 있으나, PyRosetta 동작에 영향 없음 확인.
- environment-bio-tools.yml에 모든 채널과 의존성이 정의되어 있으므로, 새 환경에서는 `conda env create -f environment-bio-tools.yml`로 한번에 설치 가능.
