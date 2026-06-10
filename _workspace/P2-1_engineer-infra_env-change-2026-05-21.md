# 환경 변경 메모: pepadmet-upgrade — dgl≥2.4 + torch≥2.4 업그레이드

**날짜**: 2026-05-21  
**담당**: engineer-infra  
**태스크**: A.A5Pb-env (Task #8)  
**롤백 보호**: 기존 `pepadmet` env 미수정 (python 3.7 / dgl 0.4.3 / torch 1.13.1+cu117 원형 보존)

---

## 1. 신규 환경

| 항목 | 값 |
|------|-----|
| **env 이름** | `pepadmet-upgrade` |
| **활성화 명령** | `conda activate pepadmet-upgrade` |
| **Python** | 3.10.20 |
| **CUDA_VISIBLE_DEVICES** | 2 (GPU 0,1,3 다른 세션 점유 중) |

---

## 2. 업그레이드 의존성 버전 표

| 패키지 | 구 (pepadmet) | 신 (pepadmet-upgrade) | 비고 |
|--------|--------------|----------------------|------|
| python | 3.7.16 | **3.10.20** | |
| dgl | 0.4.3 | **2.4.0+cu121** | data.dgl.ai wheel |
| torch | 1.13.1+cu117 | **2.4.1+cu121** | H100 CUDA 12.3 호환 |
| rdkit | 2020.09.1.0 | **2026.3.2** | pip install rdkit |
| scikit-learn | 1.0.2 | **1.7.2** | |
| modlamp | 4.3.0 | **4.3.2** | |
| openbabel | 3.1.1 | **3.1.x** | conda-forge |
| PyBioMed | 1.0 | **1.0** | (동일) |
| numpy | 1.21.5 | **2.2.6** | torch 2.4+ NumPy 2.x 지원 |
| pandas | 1.3.5 | **2.3.3** | |
| ipython | (없음) | **8.39.0** | weight_visualization.py 의존 |
| seaborn | (없음) | **0.13.2** | weight_visualization.py 의존 |

---

## 3. MY_GNN.py API 수정 사항

파일: `_workspace/pepadmet_local/pepADMET/utils/MY_GNN.py`

### 3.1 dgl.readout.sum_nodes → dgl.sum_nodes (Line 10)

| | 내용 |
|--|------|
| **파일:줄** | `MY_GNN.py:10` |
| **변경 전** | `from dgl.readout import sum_nodes` |
| **변경 후** | `from dgl import sum_nodes  # dgl 1.x+ API` |
| **사유** | dgl 1.x에서 `dgl.readout` 모듈 재구조화. `sum_nodes`는 `dgl` 패키지 최상위로 이동 |

### 3.2 FPN.forward: torch.tensor → torch.as_tensor (Line 123)

| | 내용 |
|--|------|
| **파일:줄** | `MY_GNN.py:123` |
| **변경 전** | `descriptor = torch.tensor(descriptor)` |
| **변경 후** | `descriptor = torch.as_tensor(np.array(descriptor))  # 비균일 ndarray 리스트 tensor 경고 방지` |
| **사유** | PyTorch 2.x에서 비균일 ndarray 리스트를 `torch.tensor()`에 넘길 때 UserWarning 발생. `np.array()` 변환 후 `torch.as_tensor()` 사용으로 해결. 학습 로직 변경 없음 |

### 3.3 collate_molgraphs: set_n/e_initializer 제거 (Lines 758-759)

| | 내용 |
|--|------|
| **파일:줄** | `MY_GNN.py:758-760` |
| **변경 전** | `bg.set_n_initializer(dgl.init.zero_initializer)` / `bg.set_e_initializer(dgl.init.zero_initializer)` |
| **변경 후** | 두 줄 주석 처리 (기능 동일) |
| **사유** | dgl 1.0에서 deprecated, dgl 2.x에서 완전 삭제. `dgl.init` 모듈 자체 제거됨. `dgl.batch()` 후 initializer 설정은 2.x에서 불필요 (기본값이 zero initializer) |

---

## 4. build_dataset.py 최소 API 수정 (smoke test 통과 필요)

파일: `_workspace/pepadmet_local/pepADMET/utils/build_dataset.py`

> **주의**: 원래 지침은 MY_GNN.py만 수정이나, build_dataset.py line 8의 import 변경 없이는 smoke test가 ImportError로 차단됨. 순수 경로 변경(학습 로직 0)이므로 최소 수정 적용. team-lead 검토 후 롤백 가능.

| | 내용 |
|--|------|
| **파일:줄** | `build_dataset.py:8` |
| **변경 전** | `from dgl.data.graph_serialize import save_graphs, load_graphs, load_labels` |
| **변경 후** | `from dgl import save_graphs, load_graphs  # dgl 2.x: dgl.data.graph_serialize 모듈 제거` |
| **사유** | dgl 2.x에서 `dgl.data.graph_serialize` 모듈 완전 제거. `save_graphs`/`load_graphs`는 `dgl` 최상위로 이동. `load_labels`는 코드 내 미사용 확인됨 |

**추가 주의**: `build_dataset.py`의 `DGLGraph()`, `g.add_nodes()`, `g.add_edges()` (lines 1, 184, 189, 212)는 dgl 2.x에서 deprecated. `.bin` 파일이 이미 존재하므로 데이터셋 재빌드(`build_graph_dataset.py` 실행) 시에는 추가 수정 필요. 현재 smoke test(기존 .bin 로드)는 통과됨.

---

## 5. Smoke Test 결과

```
# Smoke Test 1
python -c "import dgl, torch; print(dgl.__version__, torch.__version__, torch.cuda.is_available())"
> 2.4.0+cu121 2.4.1+cu121 True

# Smoke Test 2: Train.ipynb 첫 cell (학습 시작 직전)
> imports OK
> dataset loaded, train: 45 val: 45 test: 45
> device: cuda
> model init OK, params: 15040593
> forward pass OK, tasks: ['task_0', 'task_1', 'task_2', 'task_3']
> === ALL SMOKE TESTS PASSED ===
```

---

## 6. GPU 가용 현황

```
nvidia-smi 결과 (2026-05-21 03:xx KST):
GPU 0: NVIDIA H100 NVL — 89787/95830 MiB (다른 세션 점유)
GPU 1: NVIDIA H100 NVL — 89417/95830 MiB (다른 세션 점유)
GPU 2: NVIDIA H100 NVL — 18579/95830 MiB ← 가용 (추천)
GPU 3: NVIDIA H100 NVL — 86287/95830 MiB (다른 세션 점유)
```

**권고**: `CUDA_VISIBLE_DEVICES=2` 설정 후 학습 실행

---

## 7. 검증 명령

```bash
conda activate pepadmet-upgrade
CUDA_VISIBLE_DEVICES=2 python -c "import dgl, torch; print(dgl.__version__, torch.__version__, torch.cuda.is_available())"
# 기대값: 2.4.0+cu121 2.4.1+cu121 True
```

---

## 8. 롤백

기존 `pepadmet` env 미수정 상태:
```bash
conda activate pepadmet  # python 3.7.12 / dgl 0.4.3 / torch 1.13.1+cu117
```

---

## 9. 재현 파일

| 파일 | 설명 |
|------|------|
| `_workspace/pepadmet_local/pepadmet_upgrade_pip_freeze.txt` | pip freeze (78 패키지) |
| `_workspace/pepadmet_local/pepadmet_upgrade_conda_export.yml` | conda env export |
