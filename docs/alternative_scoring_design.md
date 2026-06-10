# Alternative Scoring Methods — 상세 구현 설계서

> **작성일**: 2026-03-10
> **목적**: 현재 가중합(Weighted Sum) 스코어링의 한계를 보완/대체할 4가지 방법론의 구현 설계
> **대상 시스템**: SSTR2 AI Co-Scientist — Silo B Pipeline

---

## 목차

1. [현재 스코어링 분석](#1-현재-스코어링-분석)
2. [Part A: NSGA-II Pareto Ranking](#2-part-a-nsga-ii-pareto-ranking)
3. [Part B: ESM-2 Pseudo-perplexity](#3-part-b-esm-2-pseudo-perplexity)
4. [Part C: GNINA CNN Rescoring](#4-part-c-gnina-cnn-rescoring)
5. [Part D: Bayesian Optimization](#5-part-d-bayesian-optimization)
6. [구현 로드맵](#6-구현-로드맵)
7. [의존성](#7-의존성)

---

## 1. 현재 스코어링 분석

### 1.1 Silo B `MultiObjectiveScorer` (scoring.py)

현재 단일 가중합(weighted sum) 방식:

```
final = 0.45×norm(ddG) + 0.20×norm(stability) + 0.15×norm(druggability)
      + 0.10×norm(diversity) + 0.10×norm(hil_confidence) - penalties
```

| Objective | Weight | Goal | Clip Range |
|-----------|--------|------|------------|
| `docking_delta_g` | 0.45 | minimize | [-14, 0] |
| `stability` | 0.20 | maximize | [-12, 8] |
| `druggability` | 0.15 | maximize | [0, 1] |
| `diversity` | 0.10 | maximize | [0, 1] |
| `hil_confidence` | 0.10 | maximize | [0, 1] |

Penalties: `hard_violation=8.0`, `soft_violation=0.4/rule`, `duplicate=0.5`

### 1.2 QCRankerAgent (qc_ranker.py) — PyRosetta 전용 가중치

```
ddg: 0.70, total_score: 0.20, clash: 0.10
```

pLDDT/dock_score/lddt/selectivity 모두 0.0 (ESMFold/DiffDock 미사용)

### 1.3 가중합의 근본적 한계

| # | 한계 | 설명 |
|---|------|------|
| 1 | **Trade-off 은폐** | ddG=-12 + stability=낮음 vs ddG=-8 + stability=높음 → 같은 점수이나 약리학적 의미 전혀 다름 |
| 2 | **가중치 자의성** | 0.45/0.20/0.15/0.10/0.10 — 물리적 근거 없는 임의 비율 |
| 3 | **비선형 관계 무시** | ddG와 stability 사이의 볼록 trade-off surface를 1차 선형함수로 투사 |
| 4 | **Pareto-optimal 해 누락** | 가중합은 non-convex Pareto front의 해를 찾을 수 없음 |

---

## 2. Part A: NSGA-II Pareto Ranking

> **우선순위: 1 (최우선)**
> **통합 난이도: 쉬움** | **코드량: ~200줄** | **추가 모델 불필요**

### 2.1 설계 원리

가중합 대신 Non-dominated Sorting + Crowding Distance로 Pareto front 전체를 보존.
NSGA-II는 crowding distance로 다양성도 자동 유지.

### 2.2 pymoo Problem 클래스 설계

```python
# pyrosetta_flow/pareto_ranking.py
from __future__ import annotations
import numpy as np
from pymoo.core.problem import Problem
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from typing import Any


class CandidateRankingProblem(Problem):
    """이미 평가된 후보들의 Pareto 랭킹용.
    실제 진화 탐색이 아니라 non-dominated sorting만 수행.

    Objectives (모두 minimize):
      f1: ddG (낮을수록 좋음, 이미 minimize)
      f2: -stability_score (높을수록 좋으므로 부호 반전)
      f3: -druggability (높을수록 좋으므로 부호 반전)
      f4: -diversity (높을수록 좋으므로 부호 반전)

    Constraints:
      g1: hard_violations <= 0 (위반 시 infeasible)
      g2: clash_score <= clash_max
    """

    def __init__(self, candidates: list[dict], clash_max: float = 10.0):
        self.candidates = candidates
        self.clash_max = clash_max
        n = len(candidates)
        super().__init__(
            n_var=n,        # dummy — 실제 탐색 아님
            n_obj=4,
            n_ieq_constr=2,
            xl=0, xu=1,
        )

    def _evaluate_candidates(self) -> tuple[np.ndarray, np.ndarray]:
        """후보 배열을 objective/constraint 행렬로 변환."""
        n = len(self.candidates)
        F = np.zeros((n, 4))
        G = np.zeros((n, 2))

        for i, c in enumerate(self.candidates):
            F[i, 0] = float(c.get("ddg", 999.0))           # minimize
            F[i, 1] = -float(c.get("stability", 0.0))       # maximize → negate
            F[i, 2] = -float(c.get("druggability", 0.0))    # maximize → negate
            F[i, 3] = -float(c.get("diversity", 0.0))       # maximize → negate

            hard = c.get("hard_violations", 0)
            if isinstance(hard, (list, tuple)):
                hard = len(hard)
            G[i, 0] = float(hard)                            # <= 0 feasible
            G[i, 1] = float(c.get("clash_score", 0.0)) - self.clash_max

        return F, G
```

### 2.3 Pareto Rank 부여 함수

```python
def pareto_rank_candidates(
    candidates: list[dict],
    clash_max: float = 10.0,
) -> list[dict]:
    """Non-dominated sorting으로 Pareto rank 부여.

    Returns: candidates에 'pareto_rank', 'crowding_distance' 필드 추가.
    """
    from pymoo.util.misc import calc_crowding_distance

    problem = CandidateRankingProblem(candidates, clash_max)
    F, G = problem._evaluate_candidates()

    # Infeasible 후보 처리
    feasible_mask = np.all(G <= 0, axis=1)
    feasible_indices = np.where(feasible_mask)[0]
    infeasible_indices = np.where(~feasible_mask)[0]

    ranked = [dict(c) for c in candidates]

    if len(feasible_indices) > 0:
        F_feasible = F[feasible_indices]
        nds = NonDominatedSorting()
        fronts = nds.do(F_feasible)

        for rank_idx, front in enumerate(fronts):
            cd = calc_crowding_distance(F_feasible[front])
            for j, local_idx in enumerate(front):
                global_idx = feasible_indices[local_idx]
                ranked[global_idx]["pareto_rank"] = rank_idx + 1
                ranked[global_idx]["crowding_distance"] = round(float(cd[j]), 4)

    # Infeasible → max_rank + 1
    max_rank = max((r.get("pareto_rank", 0) for r in ranked), default=0)
    for idx in infeasible_indices:
        ranked[idx]["pareto_rank"] = max_rank + 1
        ranked[idx]["crowding_distance"] = 0.0

    # Sort: pareto_rank ASC, crowding_distance DESC
    ranked.sort(key=lambda x: (x.get("pareto_rank", 999), -x.get("crowding_distance", 0)))
    return ranked
```

### 2.4 Pareto Front 최종 후보 선택

```python
def select_from_pareto_front(
    ranked: list[dict],
    top_k: int = 5,
    strategy: str = "knee",
) -> list[dict]:
    """Pareto front에서 최종 후보 선택.

    Strategies:
      - "knee": Pareto front 1에서 knee point (ddG-stability trade-off 최적)
      - "crowding": crowding distance 최대 (다양성 우선)
      - "ddg_primary": Pareto front 1 내에서 ddG 최소
    """
    front1 = [c for c in ranked if c.get("pareto_rank") == 1]

    if not front1:
        return ranked[:top_k]

    if strategy == "ddg_primary":
        front1.sort(key=lambda x: x.get("ddg", 999))
        return front1[:top_k]

    elif strategy == "crowding":
        front1.sort(key=lambda x: -x.get("crowding_distance", 0))
        return front1[:top_k]

    elif strategy == "knee":
        if len(front1) < 2:
            return front1[:top_k]
        ddgs = [c["ddg"] for c in front1]
        stabs = [-c.get("stability", 0) for c in front1]
        ddg_min, ddg_max = min(ddgs), max(ddgs)
        stab_min, stab_max = min(stabs), max(stabs)

        for c in front1:
            nd = (c["ddg"] - ddg_min) / (ddg_max - ddg_min + 1e-8)
            ns = (-c.get("stability", 0) - stab_min) / (stab_max - stab_min + 1e-8)
            c["_knee_dist"] = (nd**2 + ns**2) ** 0.5

        front1.sort(key=lambda x: x["_knee_dist"])
        return front1[:top_k]

    return front1[:top_k]
```

### 2.5 runner.py 통합 포인트

`runner.py` line ~580 — `step06_score` 완료 후, QC 랭킹 전에 삽입:

```python
from .pareto_ranking import pareto_rank_candidates, select_from_pareto_front

pareto_input = [
    {
        "candidate_id": c.candidate_id,
        "sequence": c.sequence,
        "ddg": c.ddg,
        "stability": c.total_score,
        "druggability": 0.0,              # 향후 pharmacology 연동
        "diversity": 0.0,                 # 향후 sequence diversity 연동
        "clash_score": c.clash_score,
        "hard_violations": 1 if c.fail_reason else 0,
    }
    for c in candidates
]
pareto_ranked = pareto_rank_candidates(pareto_input, clash_max=config.rosetta_clash_max)
pareto_selected = select_from_pareto_front(
    pareto_ranked, top_k=config.top_k, strategy="knee"
)

# Emit pareto data for UI
emitter.set_pareto_front({
    "front_sizes": {
        str(r): len([c for c in pareto_ranked if c["pareto_rank"] == r])
        for r in set(c["pareto_rank"] for c in pareto_ranked)
    },
    "selected_ids": [c["candidate_id"] for c in pareto_selected],
    "strategy": "knee",
})
```

### 2.6 UI: ParetoScatterPlot 컴포넌트

```tsx
// frontend/src/components/ParetoScatterPlot.tsx
interface ParetoPoint {
  candidate_id: string;
  ddg: number;
  stability: number;
  pareto_rank: number;
  crowding_distance: number;
  selected: boolean;
}

// Recharts ScatterChart 기반
// - Pareto rank 1: 파란 ●, rank 2: 회색 ○, infeasible: 빨간 ×
// - 선택된 후보: 별 마커 ★
// - Pareto front 1 연결선 (convex hull)
// - Tooltip: candidate_id, sequence, 모든 objective 값
// - Knee point 강조 표시
```

### 2.7 테스트 전략

| 테스트 | 검증 내용 |
|--------|----------|
| `test_dominated_sorting_basic` | A가 모든 목적에서 B보다 나으면 A.rank < B.rank |
| `test_non_dominated_front` | Trade-off 관계의 2개 후보는 같은 front |
| `test_infeasible_last` | hard_violations > 0 → 항상 최하위 rank |
| `test_crowding_distance_diversity` | Front 양 끝 점은 crowding_distance = inf |
| `test_knee_selection` | 3점 직선 위에서 중간점이 knee |
| `test_empty_candidates` | 빈 리스트 → 빈 리스트 반환 |
| `test_single_candidate` | 후보 1개 → pareto_rank=1 |

### 2.8 장단점 — 가중합 완전 대체 vs 병행

| | 완전 대체 | 병행 사용 (권장) |
|--|----------|----------------|
| **장점** | 단순, 혼란 없음 | 기존 호환성 유지, A/B 비교 가능 |
| **단점** | 기존 실험 결과 재현 불가 | 두 시스템 유지 비용 |
| **결론** | — | `scoring_mode: "weighted" | "pareto"` 설정으로 선택 |

---

## 3. Part B: ESM-2 Pseudo-perplexity

> **우선순위: 3**
> **통합 난이도: 쉬움** | **코드량: ~150줄** | **모델: esm2_t33_650M_UR50D (HuggingFace)**

### 3.1 모델 선택

| 항목 | 값 |
|------|---|
| 모델 | `facebook/esm2_t33_650M_UR50D` (650M params, 33 layers) |
| CPU 추론 | ~0.8초/서열 (14 residue) |
| GPU (A100) | ~0.05초/서열 |
| VRAM | ~2.5GB (fp32), ~1.3GB (fp16) |

### 3.2 Masked Marginal Scoring 원리

각 위치 *i*를 순차적으로 마스킹하고, 해당 위치의 원래 잔기에 대한 로그 확률을 합산:

```
PLL = Σᵢ log P(xᵢ | x₋ᵢ)
Pseudo-perplexity = exp(-PLL / L)
```

- **낮은 pseudo-perplexity** = 진화적으로 더 그럴듯한 서열
- **ΔpPPL < 0** (SST-14 대비): 후보가 native보다 유리
- **ΔpPPL > 0**: native보다 불리

### 3.3 핵심 구현

```python
# backend/esm2_perplexity.py
import math
import torch
from transformers import AutoTokenizer, EsmForMaskedLM

_MODEL_NAME = "facebook/esm2_t33_650M_UR50D"
_model = None
_tokenizer = None


def _load_model(device: str = "cpu"):
    """Lazy singleton model loading."""
    global _model, _tokenizer
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _model = EsmForMaskedLM.from_pretrained(_MODEL_NAME)
        _model.to(device)
        _model.eval()
    return _model, _tokenizer


def masked_marginal_score(sequence: str, device: str = "cpu") -> dict:
    """Masked marginal pseudo-log-likelihood scoring."""
    model, tokenizer = _load_model(device)
    encoded = tokenizer(sequence, return_tensors="pt").to(device)
    input_ids = encoded["input_ids"]  # [1, L+2] (BOS/EOS)

    L = len(sequence)
    log_probs = []

    with torch.no_grad():
        for i in range(L):
            pos = i + 1  # BOS offset
            masked = input_ids.clone()
            masked[0, pos] = tokenizer.mask_token_id
            logits = model(masked).logits
            log_softmax = torch.log_softmax(logits[0, pos], dim=-1)
            original_token_id = input_ids[0, pos].item()
            log_probs.append(log_softmax[original_token_id].item())

    pll = sum(log_probs)
    pseudo_ppl = math.exp(-pll / L)

    return {
        "pseudo_log_likelihood": round(pll, 4),
        "pseudo_perplexity": round(pseudo_ppl, 4),
        "per_position_log_probs": [round(lp, 4) for lp in log_probs],
        "length": L,
        "model": _MODEL_NAME,
    }


def delta_pseudo_perplexity(
    candidate_seq: str,
    reference_seq: str = "AGCKNFFWKTFTSC",
    device: str = "cpu",
) -> dict:
    """SST-14 대비 상대 pseudo-perplexity.

    ΔpPPL = pPPL(candidate) - pPPL(SST-14)
    ΔpPPL < 0: 후보가 더 그럴듯 | > 0: 덜 그럴듯
    """
    ref = masked_marginal_score(reference_seq, device)
    cand = masked_marginal_score(candidate_seq, device)
    delta = cand["pseudo_perplexity"] - ref["pseudo_perplexity"]

    return {
        "candidate_ppl": cand["pseudo_perplexity"],
        "reference_ppl": ref["pseudo_perplexity"],
        "delta_ppl": round(delta, 4),
        "delta_pll": round(cand["pseudo_log_likelihood"] - ref["pseudo_log_likelihood"], 4),
        "interpretation": (
            "favorable" if delta < 0
            else "neutral" if abs(delta) < 0.5
            else "unfavorable"
        ),
    }


def batch_masked_marginal_score(
    sequences: list[str],
    device: str = "cpu",
    reference: str = "AGCKNFFWKTFTSC",
) -> list[dict]:
    """배치 처리: reference는 1회만 계산 후 캐시."""
    ref_result = masked_marginal_score(reference, device)
    results = []
    for seq in sequences:
        cand = masked_marginal_score(seq, device)
        delta = cand["pseudo_perplexity"] - ref_result["pseudo_perplexity"]
        results.append({
            "sequence": seq,
            "pseudo_perplexity": cand["pseudo_perplexity"],
            "pseudo_log_likelihood": cand["pseudo_log_likelihood"],
            "delta_ppl": round(delta, 4),
        })
    return results
```

### 3.4 pharmacology.py 통합 (14번째 metric)

```python
# pharmacology.py — compute_pharmacology() 수정
def compute_pharmacology(
    sequence: str,
    reference: str = SST14_NATIVE,
    include_esm2: bool = False,
) -> dict:
    result = { ... }  # 기존 13개 metric

    if include_esm2:
        from .esm2_perplexity import delta_pseudo_perplexity
        device = "cuda" if torch.cuda.is_available() else "cpu"
        result["esm2_perplexity"] = delta_pseudo_perplexity(sequence, reference, device)

    return result
```

### 3.5 방사성의약품 관점 해석

| 점수 | 의미 |
|------|------|
| ΔpPPL ≪ 0 | 진화적으로 자연스러운 변이 → 생체 내 안정성/프로테아제 저항성 기대 |
| ΔpPPL ≈ 0 | SST-14 수준 자연스러움 → 기존 약리 프로파일 유지 |
| ΔpPPL ≫ 0 | 부자연스러운 서열 → 면역원성 또는 불안정성 위험 |

### 3.6 성능 추정

| 환경 | 14aa 서열 | 22,000 후보 전체 |
|------|----------|-----------------|
| CPU (i7-12700) | ~0.8초 | ~4.9시간 |
| GPU (RTX 3090) | ~0.08초 | ~29분 |
| GPU (A100) | ~0.05초 | ~18분 |

**권장**: GPU 배치 처리, 또는 QC 통과 top-100 필터링 후 적용

---

## 4. Part C: GNINA CNN Rescoring

> **우선순위: 2**
> **통합 난이도: 쉬움** | **코드량: ~250줄** | **CLI 기반**

### 4.1 설치

```bash
# conda-forge
conda install -c conda-forge gnina
# 또는
mamba install -c conda-forge gnina

gnina --version
```

### 4.2 FlexPepDock PDB → GNINA 입력 변환

```python
# pyrosetta_flow/gnina_rescoring.py
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def split_receptor_peptide(
    complex_pdb: str | Path,
    receptor_chain: str = "A",
    peptide_chain: str = "B",
) -> tuple[Path, Path]:
    """복합체 PDB를 receptor/peptide 개별 파일로 분리."""
    complex_pdb = Path(complex_pdb)
    receptor_lines, peptide_lines = [], []

    with open(complex_pdb) as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                chain = line[21]
                if chain == receptor_chain:
                    receptor_lines.append(line)
                elif chain == peptide_chain:
                    peptide_lines.append(line)
            elif line.startswith("END"):
                receptor_lines.append(line)
                peptide_lines.append(line)

    rec_path = complex_pdb.with_suffix(".receptor.pdb")
    pep_path = complex_pdb.with_suffix(".peptide.pdb")
    rec_path.write_text("".join(receptor_lines))
    pep_path.write_text("".join(peptide_lines))

    return rec_path, pep_path


def gnina_rescore(
    complex_pdb: str | Path,
    receptor_chain: str = "A",
    peptide_chain: str = "B",
    gnina_bin: str = "gnina",
    cnn_scoring: str = "rescore",
) -> dict[str, Any]:
    """GNINA CNN rescoring of a FlexPepDock output.

    Returns: gnina_cnn_score, gnina_cnn_affinity, gnina_vina_score
    """
    complex_pdb = Path(complex_pdb)
    rec_path, pep_path = split_receptor_peptide(
        complex_pdb, receptor_chain, peptide_chain
    )

    try:
        with tempfile.NamedTemporaryFile(suffix=".sdf", delete=False) as tmp:
            out_path = tmp.name

        cmd = [
            gnina_bin,
            "--receptor", str(rec_path),
            "--ligand", str(pep_path),
            "--score_only",
            "--cnn_scoring", cnn_scoring,
            "--out", out_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        scores = _parse_gnina_output(result.stdout)
        scores["gnina_returncode"] = result.returncode
        return scores

    finally:
        for p in [rec_path, pep_path]:
            if p.exists():
                p.unlink()


def _parse_gnina_output(stdout: str) -> dict[str, Any]:
    """GNINA stdout 파싱."""
    scores = {"gnina_cnn_score": 0.0, "gnina_cnn_affinity": 0.0, "gnina_vina_score": 0.0}

    for line in stdout.splitlines():
        line = line.strip()
        if "CNNscore" in line:
            try: scores["gnina_cnn_score"] = float(line.split()[-1])
            except (ValueError, IndexError): pass
        elif "CNNaffinity" in line:
            try: scores["gnina_cnn_affinity"] = float(line.split()[-1])
            except (ValueError, IndexError): pass
        elif line.startswith("Affinity:") or "minimizedAffinity" in line:
            try: scores["gnina_vina_score"] = float(line.split()[-1])
            except (ValueError, IndexError): pass

    return scores


def batch_gnina_rescore(
    pdb_paths: list[str | Path],
    receptor_chain: str = "A",
    peptide_chain: str = "B",
    max_workers: int = 4,
) -> list[dict]:
    """병렬 GNINA rescoring."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = [None] * len(pdb_paths)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(gnina_rescore, pdb, receptor_chain, peptide_chain): i
            for i, pdb in enumerate(pdb_paths)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try: results[idx] = future.result()
            except Exception as e: results[idx] = {"error": str(e), "gnina_cnn_score": 0.0}

    return results
```

### 4.3 runner.py 통합 — FlexPepDock 후 Rescoring

`runner.py` — FlexPepDock refinement 완료 직후, QC 전:

```python
if config.enable_gnina_rescore:
    t_gnina = emitter.start_rosetta_substep("step06_gnina")
    emitter.append_timeline_event(iteration, "gnina", "running", "GNINA CNN rescoring")

    pdb_paths = [
        iter_dir / f"cand_{int(c.candidate_id.split('cand')[1]):03d}.pdb"
        for c in candidates if not c.fail_reason
    ]
    gnina_results = batch_gnina_rescore(
        pdb_paths,
        receptor_chain="A",
        peptide_chain=str(config.peptide_chain),
        max_workers=config.max_parallel_workers,
    )

    success_idx = 0
    for c in candidates:
        if not c.fail_reason and success_idx < len(gnina_results):
            c.gnina_cnn_score = gnina_results[success_idx].get("gnina_cnn_score", 0.0)
            c.gnina_cnn_affinity = gnina_results[success_idx].get("gnina_cnn_affinity", 0.0)
            success_idx += 1

    emitter.complete_rosetta_substep("step06_gnina", t_gnina)
```

### 4.4 Consensus Scoring — Exponential Rank Aggregation

```python
# pyrosetta_flow/consensus_scoring.py
import math


def exponential_rank_consensus(
    candidates: list[dict],
    score_keys: list[str] = ["ddg", "gnina_cnn_score", "total_score"],
    directions: dict[str, str] | None = None,
    tau: float = 0.1,
) -> list[dict]:
    """Exponential rank aggregation (Fagin et al. 2003 변형).

    consensus_score(i) = Σ_k exp(-rank_k(i) / (τ × N))
    τ: 온도 (낮을수록 상위 순위 강조)
    """
    if directions is None:
        directions = {
            "ddg": "minimize",
            "gnina_cnn_score": "maximize",
            "total_score": "minimize",
        }

    n = len(candidates)
    if n == 0:
        return []

    # 각 metric별 순위
    ranks: dict[str, list[int]] = {}
    for key in score_keys:
        reverse = directions.get(key, "minimize") == "maximize"
        sorted_indices = sorted(
            range(n),
            key=lambda i: float(candidates[i].get(key, 999.0)),
            reverse=reverse,
        )
        rank_map = [0] * n
        for rank, idx in enumerate(sorted_indices):
            rank_map[idx] = rank + 1
        ranks[key] = rank_map

    # Consensus score
    result = []
    for i, c in enumerate(candidates):
        entry = dict(c)
        score = sum(
            math.exp(-ranks[key][i] / (tau * n))
            for key in score_keys
        )
        entry["consensus_score"] = round(score, 6)
        entry["ranks"] = {key: ranks[key][i] for key in score_keys}
        result.append(entry)

    result.sort(key=lambda x: -x["consensus_score"])
    return result
```

### 4.5 UI — CandidateTable 컬럼 추가

```tsx
// CandidateTable.tsx — 추가 컬럼
{
  header: "GNINA",
  accessorKey: "gnina_cnn_score",
  cell: ({ getValue }) => {
    const v = getValue<number>();
    return v > 0 ? (
      <span className={v > 0.7 ? "text-green-600" : v > 0.4 ? "text-yellow-600" : "text-red-600"}>
        {v.toFixed(3)}
      </span>
    ) : "—";
  },
},
{
  header: "Consensus",
  accessorKey: "consensus_score",
  cell: ({ getValue }) => getValue<number>()?.toFixed(4) ?? "—",
},
```

---

## 5. Part D: Bayesian Optimization (보너스)

> **우선순위: 4 (Phase 2용)**
> **통합 난이도: 보통** | **코드량: ~400줄** | **의존: ESM-2 + botorch**

### 5.1 GP Surrogate on ESM-2 Embeddings

```python
# pyrosetta_flow/bayesian_opt.py
import torch
from botorch.models import SingleTaskGP
from botorch.fit import fit_gpytorch_mll
from gpytorch.mlls import ExactMarginalLogLikelihood
from botorch.acquisition import ExpectedImprovement, UpperConfidenceBound
from botorch.optim import optimize_acqf


def get_esm2_embedding(
    sequence: str, model=None, tokenizer=None, device: str = "cpu",
) -> torch.Tensor:
    """ESM-2 last layer mean pooling → 1280-dim embedding."""
    if model is None:
        from transformers import AutoTokenizer, EsmModel
        tokenizer = AutoTokenizer.from_pretrained("facebook/esm2_t33_650M_UR50D")
        model = EsmModel.from_pretrained("facebook/esm2_t33_650M_UR50D").to(device).eval()

    encoded = tokenizer(sequence, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        outputs = model(**encoded)

    hidden = outputs.last_hidden_state[0, 1:-1, :]  # [L, 1280]
    return hidden.mean(dim=0)  # [1280]


def build_gp_surrogate(
    X: torch.Tensor,   # [N, D]
    Y: torch.Tensor,   # [N, 1]
) -> SingleTaskGP:
    """GP surrogate 구축 + MLL 학습."""
    Y_mean, Y_std = Y.mean(), Y.std() + 1e-8
    Y_norm = (Y - Y_mean) / Y_std

    gp = SingleTaskGP(X, Y_norm)
    mll = ExactMarginalLogLikelihood(gp.likelihood, gp)
    fit_gpytorch_mll(mll)

    gp._y_mean = Y_mean
    gp._y_std = Y_std
    return gp
```

### 5.2 BayesianPeptideOptimizer 클래스

```python
class BayesianPeptideOptimizer:
    """GP-BO wrapper for peptide design.

    Thompson Sampling bandit과의 관계:
    - 기존 bandit: position별 독립 Beta 분포 → 위치 간 상관 무시
    - GP-BO: embedding 공간에서 서열 전체의 상관 구조를 학습
    """

    def __init__(self, pca_dim: int = 50, device: str = "cpu"):
        self.pca_dim = pca_dim
        self.device = device
        self.X_all, self.Y_all = [], []
        self._pca = None

    def observe(self, sequence: str, ddg: float):
        emb = get_esm2_embedding(sequence, device=self.device)
        self.X_all.append(emb)
        self.Y_all.append(ddg)

    def suggest(self, candidate_pool: list[str], n_suggest: int = 5) -> list[str]:
        if len(self.X_all) < 3:
            import random
            return random.sample(candidate_pool, min(n_suggest, len(candidate_pool)))

        X = torch.stack(self.X_all)
        Y = torch.tensor(self.Y_all, dtype=torch.float64).unsqueeze(-1)

        from sklearn.decomposition import PCA
        if self._pca is None:
            self._pca = PCA(n_components=min(self.pca_dim, X.shape[0] - 1))

        X_pca = torch.tensor(self._pca.fit_transform(X.numpy()), dtype=torch.float64)
        gp = build_gp_surrogate(X_pca, Y)

        pool_emb = torch.stack([
            get_esm2_embedding(seq, device=self.device) for seq in candidate_pool
        ])
        pool_pca = torch.tensor(self._pca.transform(pool_emb.numpy()), dtype=torch.float64)

        with torch.no_grad():
            posterior = gp.posterior(pool_pca)
            samples = posterior.rsample()  # GP-Thompson Sampling
            pred_ddg = samples.squeeze()

        top_indices = pred_ddg.argsort()[:n_suggest]
        return [candidate_pool[i] for i in top_indices]
```

### 5.3 Thompson Sampling Bandit과의 비교

| 측면 | 현재 Thompson Sampling | GP-BO |
|------|----------------------|-------|
| 모델 | 위치별 독립 Beta(α,β) | 서열 전체 GP posterior |
| 상관구조 | 위치 간 독립 가정 | ESM-2 embedding으로 위치 간 상관 학습 |
| 탐색/활용 | Beta 분포 샘플링 | EI/UCB or GP-TS |
| 계산 비용 | O(1) per position | O(N³) GP fitting + ESM-2 forward |
| 적합 단계 | 초기 탐색 (빠른 위치 선별) | 후기 정밀 최적화 (top-100 이후) |

**권장 2단계 전략:**
1. **Phase 1** (iteration 1-3): Thompson Sampling bandit으로 유망 위치 탐색
2. **Phase 2** (iteration 4+): GP-BO로 embedding 기반 정밀 서열 최적화

---

## 6. 구현 로드맵

### Phase 1 — 즉시 구현 (1-2일)

| 순위 | 방법 | 난이도 | 코드량 | 효과 |
|------|------|--------|--------|------|
| **1** | NSGA-II Pareto Ranking | 쉬움 | ~200줄 | 가중합 편향 제거, 다양한 후보 동시 평가 |
| **2** | GNINA CNN Rescoring | 쉬움 | ~250줄 | 독립적 2nd opinion docking score |

### Phase 2 — 1주일

| 순위 | 방법 | 난이도 | 코드량 | 효과 |
|------|------|--------|--------|------|
| **3** | ESM-2 Pseudo-perplexity | 쉬움 | ~150줄 | Zero-shot fitness proxy, 진화적 정보 |
| **4** | Bayesian Optimization | 보통 | ~400줄 | FlexPepDock 호출 비용 10x 절감 |

### Phase 3 — 2-3주 (선택)

| 방법 | 비고 |
|------|------|
| MM-GBSA Rescoring | top-50 정밀 재평가 |
| Ensemble Consensus | FlexPepDock + GNINA + Vina 결합 |
| ESM-IF1 Inverse Folding | 구조-서열 적합성 검증 |

---

## 7. 의존성

```txt
# requirements-scoring.txt
pymoo>=0.6.0            # Part A: NSGA-II
transformers>=4.30.0    # Part B: ESM-2
torch>=2.0              # Part B, D
gnina                   # Part C: conda-forge only
botorch>=0.9.0          # Part D: Bayesian Optimization
gpytorch>=1.10          # Part D
scikit-learn>=1.3       # Part D: PCA
```

---

## 부록: 전체 대안 방법론 서베이 (8카테고리)

리서치 단계에서 조사한 전체 방법론 목록 (상세 설계 대상 4개 외):

| 카테고리 | 방법 | 통합 | 우선순위 |
|----------|------|------|---------|
| ML/DL Binding | PPI-Graphomer | 보통 | 중간 |
| ML/DL Binding | **GNINA CNN** | **쉬움** | **높음** |
| ML/DL Binding | ProAffinity-GNN | 보통 | 낮음 |
| Foundation Model | **ESM-2 Perplexity** | **쉬움** | **높음** |
| Foundation Model | ESM-IF1 Inverse Folding | 보통 | 중간 |
| Physics-based | MM-GBSA/PBSA | 보통 | 중간 |
| Physics-based | FEP | 어려움 | 낮음 |
| Multi-objective | **NSGA-II Pareto** | **쉬움** | **높음** |
| Multi-objective | Hypervolume Indicator | 쉬움 | 중간 |
| Ensemble | FlexPepDock+GNINA+Vina | 보통 | 중간 |
| Ensemble | ESSENCE-Dock | 보통 | 낮음 |
| ML Force Field | OpenMM-ML + ANI-2x | 어려움 | 낮음 |
| Bayesian Opt | **BoGA** | **보통** | **높음** |
| Bayesian Opt | LaMBO | 어려움 | 낮음 |
| De novo Design | RFdiffusion + ProteinMPNN | 어려움 | 낮음 |
| Fingerprint | Tanimoto (RDKit) | 쉬움 | 낮음 |
| Pharmacophore | Shape-based Scoring | 보통 | 중간 |
