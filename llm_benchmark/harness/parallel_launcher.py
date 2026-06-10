#!/usr/bin/env python3
"""Parallel experiment launcher — groups by model, parallelizes within group.

Usage:
    python -m llm_benchmark.harness.parallel_launcher phase1
    python -m llm_benchmark.harness.parallel_launcher phase1 --dry-run
    python -m llm_benchmark.harness.parallel_launcher phase2a --max-parallel 6
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

logger = logging.getLogger("parallel_launcher")

BENCHMARK_ROOT = Path(__file__).resolve().parent.parent
CONFIGS_DIR = BENCHMARK_ROOT / "configs"
OUTPUTS_DIR = BENCHMARK_ROOT / "outputs"

# Maximum parallel experiments per model group
# Each experiment uses ~4 FlexPepDock workers. 192 cores → safe up to ~10
DEFAULT_MAX_PARALLEL = 6


# ─────────────────────────────────────────────────────────────
# Config loading
# ─────────────────────────────────────────────────────────────

def load_phase_config(phase: str) -> Dict[str, Any]:
    """Load phase matrix YAML."""
    path = CONFIGS_DIR / f"{phase}_matrix.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def load_model_config(model_id: str) -> Dict[str, Any]:
    """Load model config by ID."""
    path = CONFIGS_DIR / "models" / f"{model_id}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────────────────────
# Model swap
# ─────────────────────────────────────────────────────────────

def swap_vllm_model(hf_id: str, port: int = 8002, timeout: int = 120) -> bool:
    """Stop current vLLM, start new model, wait for health."""
    logger.info("⏳ Swapping vLLM model → %s", hf_id)

    # Kill existing
    subprocess.run(["pkill", "-f", "vllm.entrypoints"], capture_output=True)
    time.sleep(5)

    # Verify killed
    result = subprocess.run(["pgrep", "-f", "vllm.entrypoints"], capture_output=True)
    if result.returncode == 0:
        logger.warning("vLLM still alive, force killing...")
        subprocess.run(["pkill", "-9", "-f", "vllm.entrypoints"], capture_output=True)
        time.sleep(3)

    # Start new
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "3"

    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", hf_id,
        "--port", str(port),
        "--trust-remote-code",
        "--max-model-len", "4096",
        "--gpu-memory-utilization", "0.9",
    ]

    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info("  vLLM PID=%d, waiting for health check...", proc.pid)

    import urllib.request
    for i in range(timeout // 2):
        time.sleep(2)
        try:
            resp = urllib.request.urlopen(f"http://localhost:{port}/v1/models", timeout=3)
            data = json.loads(resp.read())
            loaded = data.get("data", [{}])[0].get("id", "")
            logger.info("✅ vLLM ready: %s", loaded)
            return True
        except Exception:
            if i % 10 == 9:
                logger.info("  still waiting... (%ds)", (i + 1) * 2)

    logger.error("❌ vLLM failed to start: %s", hf_id)
    proc.kill()
    return False


def get_current_vllm_model(port: int = 8002) -> str | None:
    """Check what model is currently loaded in vLLM."""
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"http://localhost:{port}/v1/models", timeout=3)
        data = json.loads(resp.read())
        return data.get("data", [{}])[0].get("id")
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Single experiment runner (called in subprocess)
# ─────────────────────────────────────────────────────────────

def run_single_experiment(exp_spec: Dict[str, Any], phase_config: Dict[str, Any]) -> Dict[str, Any]:
    """Run one experiment. Called via ProcessPoolExecutor."""
    exp_id = exp_spec["id"]
    model_id = exp_spec["model"]
    flow = exp_spec.get("flow", phase_config.get("flow", "sequential"))
    seed = exp_spec["seed"]

    model_cfg = load_model_config(model_id)
    hf_id = model_cfg["hf_id"]

    phase = f"phase{phase_config['phase']}"
    if isinstance(phase_config["phase"], str):
        phase = phase_config["phase"]

    gate_mode = exp_spec.get("gate_mode", "static")
    # Build unique dir name including group/config variants
    dir_parts = [model_id, flow, gate_mode]
    group = exp_spec.get("group")
    if group:
        dir_parts.append(group)
    n_cand_spec = exp_spec.get("n_candidates")
    max_iter_spec = exp_spec.get("max_iterations")
    if n_cand_spec and n_cand_spec != phase_config.get("n_candidates"):
        dir_parts.append(f"c{n_cand_spec}")
    if max_iter_spec and max_iter_spec != phase_config.get("max_iterations"):
        dir_parts.append(f"i{max_iter_spec}")
    dir_parts.append(f"s{seed}")
    output_dir = str(OUTPUTS_DIR / phase / "__".join(dir_parts))

    # Skip if done
    status_file = Path(output_dir) / "status.json"
    if status_file.exists():
        try:
            status = json.loads(status_file.read_text())
            if status.get("state") == "done":
                return {"id": exp_id, "status": "skipped", "reason": "already done"}
        except Exception:
            pass

    # Import runner
    sys.path.insert(0, str(BENCHMARK_ROOT))
    from llm_benchmark.runners.base import ExperimentConfig, SequentialFlowRunner
    from llm_benchmark.runners import get_runner

    n_cand = exp_spec.get("n_candidates", phase_config.get("n_candidates", 4))
    max_iter = exp_spec.get("max_iterations", phase_config.get("max_iterations", 3))
    top_k = exp_spec.get("top_k", phase_config.get("top_k", 3))

    config = ExperimentConfig(
        experiment_id=exp_id,
        model_id=model_id,
        model_hf_id=hf_id,
        flow=flow,
        seed=seed,
        n_candidates=n_cand,
        max_iterations=max_iter,
        top_k=top_k,
        output_dir=output_dir,
        extra={k: v for k, v in exp_spec.items()
               if k not in ("id", "model", "flow", "seed",
                            "n_candidates", "max_iterations", "top_k",
                            "vllm_port")}
              | {"vllm_port": exp_spec.get("vllm_port", 8002)},
    )

    runner_cls = get_runner(flow)
    runner = runner_cls(config)
    result = runner.run()

    return {
        "id": exp_id,
        "status": "done" if result.get("success") else "failed",
        "elapsed_s": result.get("elapsed_s", 0),
        "error": result.get("error"),
    }


# ─────────────────────────────────────────────────────────────
# Group experiments by model for sequential model swaps
# ─────────────────────────────────────────────────────────────

def group_by_model(experiments: List[Dict]) -> Dict[str, List[Dict]]:
    """Group experiments by model ID, preserving order."""
    groups: Dict[str, List[Dict]] = {}
    for exp in experiments:
        model = exp["model"]
        groups.setdefault(model, []).append(exp)
    return groups


# ─────────────────────────────────────────────────────────────
# Main parallel launcher
# ─────────────────────────────────────────────────────────────

def _run_model_batch(
    model_id: str,
    exps: List[Dict],
    phase_config: Dict[str, Any],
    slot_id: int,
    max_parallel: int,
    dry_run: bool,
) -> List[Dict[str, Any]]:
    """Run all experiments for one model on a given vLLM slot."""
    from llm_benchmark.harness.model_swap import start_model, SLOTS

    model_cfg = load_model_config(model_id)
    hf_id = model_cfg["hf_id"]
    port = SLOTS[slot_id].port
    results: List[Dict[str, Any]] = []

    # Inject vllm_port into each experiment
    for exp in exps:
        exp["vllm_port"] = port

    if dry_run:
        logger.info("  [DRY RUN] Slot %d (GPU %d, port %d): %s — %d experiments",
                     slot_id, SLOTS[slot_id].gpu_id, port, model_id, len(exps))
        for exp in exps:
            flow = exp.get("flow", phase_config.get("flow", "sequential"))
            logger.info("    %s: model=%s flow=%s seed=%d port=%d",
                        exp["id"], model_id, flow, exp["seed"], port)
            results.append({"id": exp["id"], "status": "dry_run"})
        return results

    # Start model on slot
    ok = start_model(slot_id, hf_id)
    if not ok:
        logger.error("  Slot %d: model load failed — skipping %s", slot_id, model_id)
        for exp in exps:
            results.append({"id": exp["id"], "status": "skipped", "reason": "model_load_failed"})
        return results

    # Run experiments in parallel
    batch_start = time.time()
    with ProcessPoolExecutor(max_workers=min(max_parallel, len(exps))) as pool:
        futures = {
            pool.submit(run_single_experiment, exp, phase_config): exp
            for exp in exps
        }
        for future in as_completed(futures):
            exp = futures[future]
            try:
                result = future.result(timeout=7200)
                results.append(result)
                logger.info("  ✓ %s: %s (%.0fs)", result["id"], result.get("status"), result.get("elapsed_s", 0))
            except Exception as exc:
                results.append({"id": exp["id"], "status": "error", "error": str(exc)})
                logger.error("  ✗ %s: %s", exp["id"], exc)

    logger.info("  Slot %d batch done: %.1f min", slot_id, (time.time() - batch_start) / 60)
    return results


def run_phase_parallel(
    phase: str,
    max_parallel: int = DEFAULT_MAX_PARALLEL,
    dual_gpu: bool = True,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Run all experiments in a phase with 2-GPU model-grouped parallelism.

    Strategy (dual_gpu=True):
      1. Group experiments by model
      2. Pair model groups: (M_A on slot 0/GPU 2, M_B on slot 1/GPU 3)
      3. Run both groups simultaneously
      4. Unpaired remainder runs on slot 1 alone

    Strategy (dual_gpu=False):
      Same as before — single GPU sequential swap.
    """
    phase_config = load_phase_config(phase)
    experiments = phase_config.get("experiments", [])

    if not experiments:
        logger.error("No experiments in %s", phase)
        return []

    model_groups = group_by_model(experiments)
    model_list = list(model_groups.items())
    all_results: List[Dict[str, Any]] = []

    total_models = len(model_list)
    total_exps = len(experiments)
    n_slots = 2 if dual_gpu else 1

    logger.info("=" * 60)
    logger.info("Phase: %s — %d experiments across %d models", phase, total_exps, total_models)
    logger.info("GPU slots: %d | Max parallel per slot: %d", n_slots, max_parallel)
    logger.info("=" * 60)

    # Pair models for 2-GPU execution
    i = 0
    batch_num = 0
    while i < total_models:
        batch_num += 1
        pair = model_list[i:i + n_slots]
        i += n_slots

        logger.info("")
        logger.info("━" * 60)
        pair_desc = " + ".join(f"{mid}(slot {s})" for s, (mid, _) in enumerate(pair))
        logger.info("Batch %d: %s", batch_num, pair_desc)
        logger.info("━" * 60)

        if dual_gpu and len(pair) == 2:
            # Load models SEQUENTIALLY (CUDA init conflict if parallel)
            # then run experiments on both slots in PARALLEL
            from concurrent.futures import ThreadPoolExecutor
            from llm_benchmark.harness.model_swap import start_model as _start

            slot_ready = {}
            for slot_id, (model_id, exps) in enumerate(pair):
                if dry_run:
                    slot_ready[slot_id] = True
                    continue
                model_cfg = load_model_config(model_id)
                hf_id = model_cfg["hf_id"]
                logger.info("  Loading slot %d: %s ...", slot_id, hf_id)
                slot_ready[slot_id] = _start(slot_id, hf_id)
                if not slot_ready[slot_id]:
                    logger.error("  Slot %d: model load failed — %s", slot_id, model_id)

            # Run experiments in parallel on both slots
            with ThreadPoolExecutor(max_workers=2) as tpool:
                futures = []
                for slot_id, (model_id, exps) in enumerate(pair):
                    if not slot_ready.get(slot_id, False) and not dry_run:
                        for exp in exps:
                            all_results.append({"id": exp["id"], "status": "skipped", "reason": "model_load_failed"})
                        continue
                    f = tpool.submit(
                        _run_model_batch,
                        model_id, exps, phase_config, slot_id, max_parallel, dry_run,
                    )
                    futures.append(f)
                for f in futures:
                    all_results.extend(f.result())
        else:
            # Single model or single-GPU mode
            for slot_idx, (model_id, exps) in enumerate(pair):
                slot_id = 1  # default slot
                batch_results = _run_model_batch(
                    model_id, exps, phase_config, slot_id, max_parallel, dry_run,
                )
                all_results.extend(batch_results)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE %s COMPLETE", phase)
    done = sum(1 for r in all_results if r["status"] == "done")
    failed = sum(1 for r in all_results if r["status"] == "failed")
    skipped = sum(1 for r in all_results if r["status"] == "skipped")
    logger.info("  Done: %d | Failed: %d | Skipped: %d | Total: %d",
                done, failed, skipped, len(all_results))
    logger.info("=" * 60)

    # Write summary
    summary_path = OUTPUTS_DIR / phase / "_phase_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")

    return all_results


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Parallel experiment launcher")
    parser.add_argument("phase", choices=["phase1", "phase2a", "phase2b", "phase3", "v2_phase1", "v2_phase2"],
                        help="Which phase to run")
    parser.add_argument("--max-parallel", type=int, default=DEFAULT_MAX_PARALLEL,
                        help="Max concurrent experiments per model group (default: 6)")
    parser.add_argument("--dual-gpu", action="store_true", default=True,
                        help="Use 2 GPUs for parallel model serving (default: True)")
    parser.add_argument("--single-gpu", action="store_true",
                        help="Force single GPU mode")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print plan without executing")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    dual = args.dual_gpu and not args.single_gpu
    run_phase_parallel(args.phase, max_parallel=args.max_parallel, dual_gpu=dual, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
