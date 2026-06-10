# A-06 DiffPepDock PoC 보고서 — SSTR2+SST14

**날짜**: 2026-05-19  
**담당**: engineer-backend  
**모델**: DiffPepDock (DiffPepBuilder v1, checkpoint: diffpepdock_v1.pth 1.2 GB)  
**GPU**: NVIDIA H100 NVL (95830 MiB), CUDA_VISIBLE_DEVICES=2

---

## 1. 환경 점검 결과

| 항목 | 상태 | 비고 |
|------|------|------|
| conda env `diffpepbuilder` | 존재 | Python 3.9.16, PyTorch 2.1.0 |
| DiffPepDock 모델 가중치 | 존재 | `local_models/DiffPepBuilder/experiments/checkpoints/diffpepdock_v1.pth` (1.2 GB) |
| GPU VRAM | 가용 | H100 NVL ×4, GPU 2/3 여유 (~95 GB each) |
| openmm/pdbfixer | **비호환** | `GLIBCXX_3.4.30` 버전 미충족 → Amber/Rosetta postprocess 불가 |
| biopython | 사용 가능 | `bio-tools` 및 `diffpepbuilder` 환경 모두 |

**환경 메모**: openmm 8.0 이 요구하는 `libstdc++.so.6 GLIBCXX_3.4.30` 심볼이 시스템 libstdc++에 없음. amber_relax 및 rosetta_relax postprocessing 비활성화하여 우회 실행.

---

## 2. DiffPepDock 실행 결과

**입력**
- 수용체: `SSTR2_7XNA.pdb` (chain A, 472 잔기)  
- 펩타이드: `AGCKNFFWKTFTSC` (14aa, SST-14 선형 서열)  
- 결합 포켓 hotspot: A122(D122), A126(Q126), A196(N196), A197(W197), A276(N276), A291(K291), A295(D295)  
- 요청 포즈 수: 10  

**출력**
- 생성 포즈: **10개** (`runs_local/diffdock_poc/poses/`)
- 실행 시간: **77.9초** (H100 NVL, 단일 GPU)
- Postprocessing: 비활성화 (openmm 미호환)

---

## 3. RMSD 분석

참조 크리스탈 구조(SSTR2+SST14-14aa 선형 복합체)가 없어 **포즈 간 다양성 RMSD**를 측정함 (pose_000 기준, pose_001~009 비교).

| 지표 | 값 |
|------|-----|
| RMSD 범위 | 0.36 ~ 2.26 Å |
| RMSD 평균 | 0.75 Å |
| RMSD < 2.0 Å 비율 | 8/9 (88.9%) |
| 매칭 잔기 수 | 14 (전체 SST14 Cα) |

> **주의**: 이 RMSD는 포즈 내부 일관성(diversity)을 측정할 뿐, 실제 결합 정확도(accuracy vs. crystal)를 의미하지 않음.

---

## 4. 비교표: PyRosetta FlexPepDock vs. Boltz vs. DiffPepDock

| 항목 | FlexPepDock | Boltz | DiffPepDock (이번 PoC) |
|------|------------|-------|----------------------|
| 방법론 | Rosetta physics + MC | SE(3) diffusion (AF3-class) | SE(3) diffusion (peptide-specific) |
| 런타임 (10 포즈) | ~6~13 sec (CPU+Rosetta) | ~60~90 sec / pred (GPU) | **77.9 sec** (GPU) |
| GPU 필요 | 불필요 | 필요 | 필요 |
| 점수 출력 | Rosetta ddG (kcal/mol) | ipTM (0~1) | **없음 (v1)** |
| SS bond 지원 | 예 (DisulfideBondMover) | 예 (CCD) | **아니오 (선형 서열만)** |
| 환형 펩타이드 | 부분 (constraints XML) | 예 (CCD SSTatom) | **아니오** |
| 수용체 유연성 | 예 (FlexPepDock) | 부분 | 아니오 |
| 이미 통합됨 | 예 (PR #49) | 예 (step05_docking.py) | 미통합 |
| MSA 필요 | 아니오 | 선택 | 아니오 |
| SSTR2 ipTM (SST14) | N/A (ddG 기준) | **0.825~0.906** | 없음 |

---

## 5. DiffPepDock 장단점

### 장점
- 펩타이드 특화 diffusion 모델 (PepPC-F 데이터셋 학습)
- 단일 추론 패스에서 다중 포즈 생성
- Boltz 대비 경량 (MSA/template 불필요)
- 빠른 inference (77.9 sec/10 poses)

### 단점
- **SS bond(이황화결합) 미지원**: SST14의 Cys3-Cys14 환형 구조를 선형 서열로만 처리 → 약리 핵심 pharmacophore (FWKT) 제시 불가
- **친화도/신뢰도 점수 없음**: 포즈 순위화 불가 → 스크리닝 도구로 사용 불가
- openmm GLIBCXX 비호환 → Amber/Rosetta relax 불가
- 환형/제약 펩타이드 학습 데이터 부재 (out-of-distribution)
- 수용체 side-chain 유연성 없음

---

## 6. SSTR2-SST14 특화 우려사항

SST-14는 Cys3-Cys14 이황화결합으로 형성된 **환형 펩타이드**이며, FWKT (Phe7-Trp8-Lys9-Thr10) 약리단이 환형 구조에 의해 올바른 공간 배치를 가진다. DiffPepDock v1은 선형 아미노산 서열만 입력받으므로 이 핵심 구조적 특징을 재현하지 못한다. 생성된 10개 포즈는 선형 SST-14에 해당하는 잘못된 형태학적 모델이다.

---

## 7. 권고

### 최종 판정: **PoC만 — 운영 도입 미추천**

**기각 사유**:
1. **Critical**: SS bond(Cys3-Cys14) 미지원 → 생물학적으로 부정확한 포즈 생성
2. **Critical**: 친화도/신뢰도 점수 없음 → 후보 순위화 불가
3. openmm 환경 비호환 → postprocessing 불가 (infra 수준 수정 필요)
4. 진입 기준(RMSD ≤ 2.0 Å @≥80% vs. crystal reference) 검증 불가 (참조 구조 없음)

**대안**:
- **Boltz**: 이미 통합됨, SS bond CCD 지원, ipTM score 출력 → 현재 최선
- **FlexPepDock**: DisulfideBondMover 지원, ddG 계산 가능 → 정밀 평가 시 사용
- **DiffPepDock v2 (미래)**: 환형 펩타이드/SMILES 입력 지원 시 재검토

### 게이트 기준 충족 여부

| 기준 | 결과 |
|------|------|
| RMSD ≤ 2.0 Å vs. crystal ≥ 80% | **해당 없음** (SSTR2+SST14-14aa 크리스탈 없음) |
| 친화도 점수 출력 | **미충족** (DiffPepDock v1 미제공) |
| SS bond 지원 | **미충족** |

---

## 8. 생성 파일

| 파일 | 경로 |
|------|------|
| 도킹 포즈 (10개) | `runs_local/diffdock_poc/poses/` |
| PoC 결과 JSON | `runs_local/diffdock_poc/poc_report.json` |
| RMSD 계산 스크립트 | `pipeline_local/scripts/compute_docking_rmsd.py` |
| 추론 실행 스크립트 | `pipeline_local/scripts/run_diffpepdock_inference.py` |
| RMSD pytest 테스트 | `pipeline_local/tests/test_compute_docking_rmsd.py` |

---

## 9. 환경 이슈 요약 (engineer-infra 전달용)

**openmm GLIBCXX 문제**:
- 환경: `diffpepbuilder` conda env
- 오류: `ImportError: libstdc++.so.6: version GLIBCXX_3.4.30 not found (required by libOpenMM.so.8.0)`
- 영향: `analysis.postprocess` (Amber relax, Rosetta relax) 전체 비활성화
- 수정 방법: `conda install -c conda-forge libstdcxx-ng>=12` 또는 openmm 버전 다운그레이드 검토

---

*보고서 자동 생성: 2026-05-19 engineer-backend*
