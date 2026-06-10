"""Experiment launcher — iterates experiment matrix and runs each experiment."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from llm_benchmark.runners import get_runner
from llm_benchmark.runners.base import ExperimentConfig
from llm_benchmark.harness.model_swap import swap_model

logger = logging.getLogger(__name__)

BENCHMARK_ROOT = Path(__file__).resolve().parent.parent
CONFIGS_DIR = BENCHMARK_ROOT / "configs"
OUTPUTS_DIR = BENCHMARK_ROOT / "outputs"


def load_matrix(phase: str) -> List[Dict[str, Any]]:
    """Load experiment matrix for a given phase."""
    matrix_file = CONFIGS_DIR / f"{phase}_matrix.yaml"
    with open(matrix_file) as f:
        data = yaml.safe_load(f)
    return data.get("experiments", [])


def load_model_config(model_id: str) -> Dict[str, Any]:
    """Load model config by ID."""
    model_file = CONFIGS_DIR / "models" / f"{model_id}.yaml"
    with open(model_file) as f:
        return yaml.safe_load(f)


def run_phase(phase: str, dry_run: bool = False) -> None:
    """Run all experiments in a phase matrix."""
    experiments = load_matrix(phase)
    if not experiments:
        logger.error("No experiments found in %s", phase)
        return

    current_model = None

    for exp_spec in experiments:
        exp_id = exp_spec["id"]
        model_id = exp_spec["model"]
        flow = exp_spec.get("flow", "sequential")
        seed = exp_spec["seed"]

        model_cfg = load_model_config(model_id)
        hf_id = model_cfg["hf_id"]

        output_dir = str(OUTPUTS_DIR / phase / f"{model_id}__{flow}__s{seed}")

        # Check if already completed
        status_file = Path(output_dir) / "status.json"
        if status_file.exists():
            status = json.loads(status_file.read_text())
            if status.get("state") == "done":
                logger.info("Skipping %s — already done", exp_id)
                continue

        # Swap model if needed
        if hf_id != current_model:
            logger.info("Model swap: %s → %s", current_model, hf_id)
            if not dry_run:
                ok = swap_model(hf_id)
                if not ok:
                    logger.error("Model swap failed for %s — skipping", hf_id)
                    continue
            current_model = hf_id

        config = ExperimentConfig(
            experiment_id=exp_id,
            model_id=model_id,
            model_hf_id=hf_id,
            flow=flow,
            seed=seed,
            n_candidates=exp_spec.get("n_candidates", 4),
            max_iterations=exp_spec.get("max_iterations", 3),
            top_k=exp_spec.get("top_k", 3),
            output_dir=output_dir,
            extra={k: v for k, v in exp_spec.items()
                   if k not in ("id", "model", "flow", "seed",
                                "n_candidates", "max_iterations", "top_k")},
        )

        logger.info("▶ Running %s: model=%s flow=%s seed=%d", exp_id, model_id, flow, seed)
        if dry_run:
            logger.info("  [DRY RUN] Would run %s", exp_id)
            continue

        runner_cls = get_runner(flow)
        runner = runner_cls(config)
        result = runner.run()
        logger.info("  Result: %s (%.1fs)", "OK" if result["success"] else "FAIL", result["elapsed_s"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    phase = sys.argv[1] if len(sys.argv) > 1 else "phase1"
    dry_run = "--dry-run" in sys.argv
    run_phase(phase, dry_run=dry_run)
