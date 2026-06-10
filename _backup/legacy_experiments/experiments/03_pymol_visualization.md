# 실험 03: PyMOL 구조 시각화 테스트

## 목적

변환된 PDB 파일을 PyMOL(Open-Source)로 로드하여 시각화가 정상 작동하는지 확인한다.

## 환경

- **conda env**: `bio-tools`
- **PyMOL**: v3.1.0 (Open-Source, conda-forge)
- **OS**: Ubuntu 22.04 (WSL2)
- **디스플레이**: WSLg (X11 포워딩) 또는 headless 모드 (`pymol -c`)

## 실행 방법

### GUI 모드 (WSLg 필요)

```bash
conda activate bio-tools
pymol data/fold_test1/fold_test1_model_0.pdb
```

또는 헬퍼 스크립트 사용:

```bash
bash scripts/run_pymol_pdb.sh data/fold_test1/fold_test1_model_0.pdb
```

### Headless 모드 (GUI 없이 이미지 생성)

```bash
conda activate bio-tools
pymol -c -d "
load data/fold_test1/fold_test1_model_0.pdb;
show cartoon;
spectrum b, blue_white_red;
set ray_opaque_background, 1;
png output_model0.png, width=1920, height=1080, dpi=300, ray=1
"
```

### 다중 모델 중첩 비교

```bash
pymol -c -d "
load data/fold_test1/fold_test1_model_0.pdb, model0;
load data/fold_test1/fold_test1_model_1.pdb, model1;
load data/fold_test1/fold_test1_model_2.pdb, model2;
align model1, model0;
align model2, model0;
show cartoon;
color green, model0;
color cyan, model1;
color magenta, model2;
zoom
"
```

## 결과

- PDB 파일 정상 로드 확인 (model 0~4 모두)
- cartoon, sticks, surface 표현 모두 동작
- B-factor 기반 색상 스펙트럼 (`spectrum b`) 적용 가능
- `align` 명령으로 모델 간 RMSD 계산 가능

## WSL 특수 사항

| 항목 | 설명 |
|------|------|
| WSLg | Windows 11에서 기본 지원. GUI 자동 표시됨 |
| X11 미지원 환경 | `pymol -c` (headless)로 PNG/PSE 생성 가능 |
| WSL1 | OpenGL 미지원으로 GUI 불가. headless만 가능 |
| 원격 서버 | `pymol -c`로 스크립트 실행 후 이미지 파일만 전송 |

## 참고

- 상세 PyMOL 명령어 목록: `docs/PYMOL_REFERENCE.md`
- PDB 뷰어 비교표: `docs/PDB_VISUALIZATION_TOOLS.md`
