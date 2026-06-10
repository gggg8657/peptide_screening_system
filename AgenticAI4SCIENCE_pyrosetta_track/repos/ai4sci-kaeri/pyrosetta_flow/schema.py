from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass
class FlowConfig:
    template_pdb: str
    original_sequence: str = "AGCKNFFWKTFTSC"
    design_positions: List[int] = field(
        # 2026-06-10: Cys14(이황화 파트너) 제거. FWKT(7-10)는 _mutable_design_positions 가 필터.
        # 실제 변이 가능 = [1,2,4,5,6,11,12] (Cys3/14·FWKT 제외).
        default_factory=lambda: [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    )
    n_candidates: int = 8
    seed_base: int = 1000
    conda_env: str = "bio-tools"
    output_dir: str = "runs/pyrosetta_flow"
    peptide_chain: int = 1  # Chain A = SST14 peptide (14aa)
    max_iterations: int = 2
    top_k: int = 5
    objective_mode: str = "auto"  # auto | ddg_only | ddg_plus_constraints
    rosetta_ddg_max: float = -5.0
    rosetta_clash_max: int = 10
    gate_mode: str = "static"  # "static" | "adaptive" — adaptive uses baseline-relative + Critic adjustments
    planner_mode: str = "pyrosetta_only"  # default | pyrosetta_only
    max_parallel_workers: int = 32  # Max parallel FlexPepDock processes
    llm_model_override: str | None = None  # CLI/env override for LLM model name
    llm_provider: str | None = None  # "vllm" | "ollama" | None(auto-detect)
    llm_base_url: str | None = None  # vLLM/OpenAI 호환 base URL (예: http://localhost:8002)
    script_timeout: int = 600  # Subprocess timeout in seconds (2026-06-09: 300→600, FlexPepDock refine ~4min/candidate)
    n_baseline_trials: int = 3  # Best-of-N baseline refinement trials
    convergence_window_size: int = 3  # ConvergenceDetector window
    convergence_significance: float = 0.05  # Mann-Whitney U significance level
    bandit_n_focus: int = 3  # Thompson sampling focus positions
    max_dedup_trials: int = 50  # Max trials before accepting duplicate
    max_random_mutations: int = 3  # Max simultaneous random mutations per candidate
    validation_n_trials: int = 3  # Multi-trial validation (1=off, 3=default, 10=paper standard)
    validation_max_workers: int = 4  # Parallel workers for validation trials
    validation_early_stop_cv: float = 0.15  # CV threshold for early stopping (0=disabled)
    # 2026-06-09: 선택성(off-target SSTR1/3/4/5 실제 도킹) 최종 단계. 비싸므로(top-K×4수용체×~6min)
    # 기본 OFF. enable_selectivity=True 시 최종 top-K 후보에 selectivity_margin 산출.
    enable_selectivity: bool = False
    selectivity_top_k: int = 3  # 최종(post-loop) 선택성 도킹 대상 후보 수
    # 2026-06-10: in-loop 선택성 (조건부 게이트) — 매 iteration 유망 후보만 off-target 도킹.
    inloop_selectivity: bool = False
    selectivity_max_per_iter: int = 2  # iteration 당 최대 선택성 도킹 후보 수 (비용 제어)
    # 2026-06-10: 무한 엔진 — 첫 도킹만 native SST-14 baseline 측정, 이후 epoch 은 캐시 재사용.
    # 변이는 template_pdb 에서 시작하므로 baseline 은 순수 비교 기준값(재도킹 불필요).
    reuse_baseline: bool = False


@dataclass
class CandidateResult:
    iteration: int
    candidate_id: str
    sequence: str
    ddg: float
    total_score: float
    clash_score: float
    source: str = "mutate_then_dock"
    selected: bool = False
    objective_mode: str = "ddg_only"
    fail_reason: str = ""
    extra_scores: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IterationSummary:
    iteration: int
    run_id: str
    hypothesis: str
    objective_mode: str
    n_candidates: int
    best_ddg: float
    mean_ddg: float
    selected_ids: List[str] = field(default_factory=list)
    critic_hypothesis: str = ""
    report_paths: Dict[str, str] = field(default_factory=dict)


@dataclass
class FlowArtifacts:
    created_at: str
    run_id: str
    config: Dict[str, Any]
    notebook_mapping: List[Dict[str, str]]
    baseline: Dict[str, Any]
    iterations: List[Dict[str, Any]]
    final_candidates: List[Dict[str, Any]]
    summary: Dict[str, Any]

    @classmethod
    def from_parts(
        cls,
        run_id: str,
        config: FlowConfig,
        notebook_mapping: List[Dict[str, str]],
        baseline: Dict[str, Any],
        iterations: List[Dict[str, Any]],
        final_candidates: List[Dict[str, Any]],
        summary: Dict[str, Any],
    ) -> "FlowArtifacts":
        return cls(
            created_at=datetime.now(timezone.utc).isoformat(),
            run_id=run_id,
            config=asdict(config),
            notebook_mapping=notebook_mapping,
            baseline=baseline,
            iterations=iterations,
            final_candidates=final_candidates,
            summary=summary,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def write_json(self, path: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
