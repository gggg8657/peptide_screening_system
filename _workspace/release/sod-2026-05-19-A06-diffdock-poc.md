# SOD 보고서 — 2026-05-19 A-06 DiffPepDock PoC

**작성**: engineer-backend  
**날짜**: 2026-05-19  
**브랜치**: `feat/a06-diffdock-poc`

---

## 작업 요약

A-06 액션 아이템에 따라 DiffPepDock (DiffPepBuilder의 protein-peptide docking 모듈)을 SSTR2+SST14에 PoC 적용하고 PyRosetta FlexPepDock, Boltz와 비교 평가를 완료했다.

---

## 환경 점검 결과

- `diffpepbuilder` conda env: **존재** (Python 3.9.16, PyTorch 2.1.0)
- `DiffPepDock` 모델 가중치: **존재** (`diffpepdock_v1.pth`, 1.2 GB)
- GPU: H100 NVL ×4, GPU 2/3 가용 (~95 GB 여유)
- **문제**: openmm `GLIBCXX_3.4.30` 미충족 → Amber/Rosetta postprocess 비활성화하여 우회

---

## 실행 결과

- 포즈 10개 생성 완료 (77.9초, H100 NVL 단일 GPU)
- Inter-pose Cα RMSD: 0.36~2.26 Å, 평균 0.75 Å
- 포즈 파일: `runs_local/diffdock_poc/poses/`

---

## 비교 요약

| 엔진 | 런타임/10포즈 | 점수 출력 | SS bond | SSTR2 현재 통합 |
|------|------------|---------|---------|--------------|
| FlexPepDock | ~6~13 sec | Rosetta ddG | 예 | 예 (PR#49) |
| Boltz | ~60~90 sec | ipTM (0~1) | 예 | 예 (step05) |
| DiffPepDock | **77.9 sec** | **없음** | **아니오** | 미통합 |

---

## 권고

**NOT_RECOMMENDED_FOR_PRODUCTION**

핵심 사유:
1. SST14 Cys3-Cys14 SS bond(환형 구조) 미지원
2. 친화도/신뢰도 점수 없음 (후보 순위화 불가)
3. openmm 환경 비호환 (postprocessing 불가)

현재 파이프라인(Boltz + FlexPepDock)이 모든 요건을 충족하므로 DiffPepDock 도입 기각.

---

## 생성 파일 목록

| 파일 | 경로 |
|------|------|
| RMSD 계산 스크립트 | `pipeline_local/scripts/compute_docking_rmsd.py` |
| DiffPepDock 추론 스크립트 | `pipeline_local/scripts/run_diffpepdock_inference.py` |
| PoC 실행 래퍼 | `pipeline_local/scripts/run_diffpepdock_poc.py` |
| pytest 테스트 (12개) | `pipeline_local/tests/test_compute_docking_rmsd.py` |
| 도킹 포즈 (10개) | `runs_local/diffdock_poc/poses/` |
| PoC JSON 보고서 | `runs_local/diffdock_poc/poc_report.json` |
| PoC Markdown 보고서 | `runs_local/diffdock_poc/poc_report.md` |

---

## 테스트 결과

```
12 passed in 0.27s (bio-tools conda env)
```

모든 단위 테스트 통과.

---

## engineer-infra 전달 사항

`diffpepbuilder` 환경 openmm GLIBCXX_3.4.30 비호환 문제:
- `conda install -c conda-forge libstdcxx-ng>=12` 시도 또는 openmm 버전 다운그레이드 검토 요청
- 해결 시 Amber/Rosetta postprocessing 재활성화 가능 (poc_report.md §9 참조)
