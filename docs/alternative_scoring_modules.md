# 대안 스코어링 모듈 기술 문서

> 작성일: 2026-03-12
> 위치: `pyrosetta_flow/` 하위 3개 모듈
> 용도: Silo B 가중합 스코어링 대체/보완

## 개요

기존 Silo B의 가중합 스코어링(0.45/0.20/0.15/0.10/0.10)을 대체하기 위한 3개 모듈.
모두 Silo B 내부 개선으로, 별도 Silo나 Arm이 아님.

| 모듈 | 파일 | 테스트 | 핵심 의존성 |
|------|------|--------|-------------|
| NSGA-II Pareto Ranking | `pareto_ranking.py` | 9 passed | pymoo |
| GNINA CNN Rescoring | `gnina_rescoring.py` | 24 passed | gnina binary (optional) |
| Bayesian Optimization | `bayesian_optimizer.py` | 24 passed, 3 skipped | numpy (필수), botorch (optional) |

---

## 1. NSGA-II Pareto Ranking (`pareto_ranking.py`)

### 목적
다목적 최적화에서 가중합 대신 Pareto 지배 관계로 후보 순위 결정.

### 목적함수 (모두 최소화)
1. `ddG` — 결합 에너지 (낮을수록 좋음)
2. `-stability` — 안정성 (부호 반전)
3. `-druggability` — 약물성 (부호 반전)
4. `-diversity` — 다양성 (부호 반전)

### 제약 조건
- `hard_violations <= 0` — FWKT 보존, SS bond 등 5개 규칙
- `clash_score <= threshold` (기본 10.0)

### API

```python
from pyrosetta_flow.pareto_ranking import pareto_rank_candidates, select_from_pareto_front

# 후보에 pareto_rank, crowding_distance 추가 (in-place)
ranked = pareto_rank_candidates(candidates, clash_threshold=10.0)

# 상위 N개 선택 (rank 오름차순 → crowding distance 내림차순)
top = select_from_pareto_front(ranked, n=50)
```

### 설계 결정
- **Infeasible 후보 처리**: 제약 위반 후보는 모든 feasible front 뒤로 밀림
- **Crowding Distance**: front 내에서 해 공간 다양성 보존 (경계점은 ∞)
- **pymoo 활용**: `NonDominatedSorting`, `calc_crowding_distance` 직접 사용

---

## 2. GNINA CNN Rescoring (`gnina_rescoring.py`)

### 목적
FlexPepDock 출력 PDB에 대해 GNINA의 CNN 기반 결합 스코어를 추가 계산.
3개 스코어 항목을 ECR(Exponential Rank Consensus)로 통합.

### 스코어 항목
| 키 | 설명 | 방향 |
|----|------|------|
| `gnina_cnn_score` | CNN 결합 확률 | 낮을수록 좋음 |
| `gnina_cnn_affinity` | CNN 친화도 예측 | 낮을수록 좋음 |
| `gnina_vina_score` | AutoDock Vina 스코어 | 낮을수록 좋음 |

### API

```python
from pyrosetta_flow.gnina_rescoring import (
    gnina_rescore,
    batch_gnina_rescore,
    exponential_rank_consensus,
)

# 단일 PDB 리스코어링
scores = gnina_rescore("complex.pdb", receptor_chain="A", peptide_chain="B")

# 배치 병렬 처리
all_scores = batch_gnina_rescore(pdb_paths, max_workers=4)

# ECR 통합 순위
ranked = exponential_rank_consensus(candidates)
# → 각 후보에 ecr_score, ecr_ranks 추가
```

### Dry-Run 모드
GNINA 바이너리 미설치 시 자동으로 mock 스코어 반환 (`gnina_dry_run: 1.0` 플래그).
파이프라인이 중단 없이 실행됨.

### ECR 수식
```
ECR_i = Σ_k exp(-rank_{i,k} / N)
```
- N: 후보 수, k: 스코어 항목, rank: 해당 항목 내 순위 (1-based)
- NaN 값은 최하위 순위로 처리

---

## 3. Bayesian Optimization (`bayesian_optimizer.py`)

### 목적
GP surrogate로 탐색 공간을 모델링하여 유망한 다음 변이 위치/아미노산 제안.
Thompson Sampling을 보완하는 exploration-exploitation 균형.

### 아키텍처

```
PeptideEmbedder (ABC)
├── OneHotEmbedder   ← 기본 (numpy only, seq_len × 20 차원)
└── ESM2Embedder     ← Optional (transformers + torch 필요)

BayesianPeptideOptimizer
├── BoTorch backend  ← ModelListGP + qNEHVI (torch 필요)
└── Fallback backend ← _FallbackGP (RBF kernel, numpy only) + UCB
```

### API

```python
from pyrosetta_flow.bayesian_optimizer import (
    BayesianPeptideOptimizer,
    OneHotEmbedder,
)

embedder = OneHotEmbedder(max_len=14)
optimizer = BayesianPeptideOptimizer(
    embedder=embedder,
    objectives=["ddG", "stability"],
    maximize=[False, True],  # ddG 최소화, stability 최대화
)

# 관측 데이터로 GP 피팅
optimizer.fit(observed_candidates)

# 다음 변이 후보 제안 (SST-14 기준, 위치 0,1,3,4,5 변이 가능)
suggestions = optimizer.suggest(
    n=10,
    reference_seq="AGCKNFFWKTFTSC",
    allowed_positions=[0, 1, 3, 4, 5],
)
# → [{"sequence": "...", "position": 3, "mutation": "R", "acquisition_value": 0.85}, ...]
```

### Graceful Degradation
| 환경 | GP Backend | Acquisition |
|------|-----------|-------------|
| botorch + torch | `SingleTaskGP` × N objectives | qNEHVI (hypervolume improvement) |
| numpy only | `_FallbackGP` (RBF kernel) × N | UCB (β=2.0) |

### 제한 사항
- **ESM-2 미사용 시**: OneHot 임베딩은 서열 유사성을 물리화학적으로 반영하지 못함
- **FallbackGP**: 역행렬 기반으로 대규모 데이터(>1000)에서 느려짐
- **단일점 변이만**: 현재 `suggest()`는 단일 위치 변이만 열거

---

## 파이프라인 통합 (예정)

`runner.py`의 scoring 단계에서 순차 호출:

```
기존 FlexPepDock 스코어
  → GNINA CNN 리스코어링 (선택)
  → ECR 통합
  → Pareto Ranking (NSGA-II)
  → 상위 후보 선택
  → Bayesian Optimization으로 다음 라운드 변이 제안
```

### 환경 요구사항
- `conda activate bio-tools` (Python 3.12, PyTorch cu124)
- `pip install pymoo` (Pareto ranking)
- GNINA v1.3.2 바이너리 (`local_models/gnina/gnina`) + cuDNN 9
- botorch (optional, BO 고급 기능)

---

## 테스트 실행

```bash
cd pyrosetta_flow
python -m pytest tests/test_pareto_ranking.py -v      # 9 tests
python -m pytest tests/test_gnina_rescoring.py -v      # 24 tests
python -m pytest tests/test_bayesian_optimizer.py -v   # 24+3 tests
```
