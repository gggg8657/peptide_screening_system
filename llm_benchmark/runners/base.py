"""Base flow runner — wraps existing pyrosetta_flow sequential runner."""
from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Upstream imports — reuse existing pyrosetta_flow code, no duplication
REPO_ROOT = Path(__file__).resolve().parent.parent.parent / \
    "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri"
sys.path.insert(0, str(REPO_ROOT))


@dataclass
class AgentTurn:
    """Single agent interaction record for logging."""
    experiment_id: str
    iteration: int
    agent: str
    input_prompt: str
    raw_response: str
    parsed_output: Dict[str, Any]
    parse_success: bool
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    debate_round: Optional[int] = None  # collaborative only


@dataclass
class ExperimentConfig:
    """Frozen experiment configuration."""
    experiment_id: str
    model_id: str
    model_hf_id: str
    flow: str
    seed: int
    n_candidates: int
    max_iterations: int
    top_k: int
    output_dir: str
    extra: Dict[str, Any] = field(default_factory=dict)


class SequentialFlowRunner:
    """Wraps pyrosetta_flow.runner.run_pyrosetta_agentic_mutdock_flow.

    Adds structured agent logging on top of the existing sequential flow.
    """

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.agent_logs: List[AgentTurn] = []
        self._output_dir = Path(config.output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._agent_log_dir = self._output_dir / "agent_log"
        self._agent_log_dir.mkdir(exist_ok=True)

    def run(self) -> Dict[str, Any]:
        """Execute the sequential flow and return results with metrics."""
        from pyrosetta_flow.schema import FlowConfig
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow

        flow_config = FlowConfig(
            template_pdb=str(REPO_ROOT / "data" / "fold_test1_model_0.pdb"),
            output_dir=str(self._output_dir / "pyrosetta_flow"),
            max_iterations=self.config.max_iterations,
            n_candidates=self.config.n_candidates,
            top_k=self.config.top_k,
            original_sequence="AGCKNFFWKTFTSC",
            peptide_chain=1,
            conda_env="bio-tools",
            seed_base=self.config.seed,
            llm_model_override=self.config.model_hf_id,
            llm_provider="vllm",
            llm_base_url=f"http://localhost:{self.config.extra.get('vllm_port', 8002)}",
            planner_mode="pyrosetta_only",
            validation_n_trials=1,
            gate_mode=self.config.extra.get("gate_mode", "static"),
        )

        self._write_config_snapshot(flow_config)
        start = time.time()

        try:
            result = run_pyrosetta_agentic_mutdock_flow(flow_config)
            elapsed = time.time() - start
            self._write_status("done", elapsed)
            self._compute_ses()
            return {"success": True, "result": result, "elapsed_s": elapsed}
        except Exception as exc:
            elapsed = time.time() - start
            self._write_status("failed", elapsed, str(exc))
            logger.error("Experiment %s failed: %s", self.config.experiment_id, exc)
            return {"success": False, "error": str(exc), "elapsed_s": elapsed}

    def _write_config_snapshot(self, flow_config) -> None:
        from dataclasses import asdict
        snapshot = {
            "experiment": {
                "id": self.config.experiment_id,
                "model": self.config.model_id,
                "model_hf_id": self.config.model_hf_id,
                "flow": self.config.flow,
                "seed": self.config.seed,
            },
            "flow_config": asdict(flow_config),
        }
        (self._output_dir / "config_snapshot.json").write_text(
            json.dumps(snapshot, indent=2, default=str), encoding="utf-8"
        )

    def _compute_ses(self) -> None:
        """Compute SES from iteration manifests and write ses_score.json."""
        try:
            from llm_benchmark.scoring.ses import CandidateScore, compute_ses

            flow_dir = self._output_dir / "pyrosetta_flow" / "sst14_agentic_mutdock"
            candidates = []
            first_hit_iter = 0

            FWKT_POS = {7, 8, 9, 10}  # 1-indexed
            FWKT_REF = {7: "F", 8: "W", 9: "K", 10: "T"}
            SST14 = "AGCKNFFWKTFTSC"

            for iter_dir in sorted(flow_dir.glob("iter_*")):
                mf = iter_dir / "08_reports" / "iteration_manifest.json"
                if not mf.exists():
                    continue
                iter_num = int(iter_dir.name.split("_")[1])
                manifest = json.loads(mf.read_text())

                for c in manifest.get("candidates", []):
                    seq = c.get("sequence", "")
                    ddg = c.get("ddg", 999.0)
                    clash = c.get("clash_count", 0) or 0

                    # Check FWKT conservation
                    fwkt_ok = True
                    if len(seq) >= 14:
                        for pos, expected in FWKT_REF.items():
                            if seq[pos - 1] != expected:
                                fwkt_ok = False
                                break
                    else:
                        fwkt_ok = False

                    cs = CandidateScore(
                        candidate_id=c.get("candidate_id", ""),
                        sequence=seq,
                        ddg=ddg,
                        clash_score=float(clash),
                        fwkt_conserved=fwkt_ok,
                        cluster_id=c.get("cluster_id"),
                    )
                    candidates.append(cs)

                    # Track first hit iteration
                    from llm_benchmark.scoring.ses import is_hit
                    if first_hit_iter == 0 and is_hit(cs):
                        first_hit_iter = iter_num

            if not candidates:
                return

            ses_result = compute_ses(
                candidates=candidates,
                first_hit_iter=first_hit_iter,
                max_iterations=self.config.max_iterations,
            )

            (self._output_dir / "ses_score.json").write_text(
                json.dumps(ses_result, indent=2), encoding="utf-8"
            )
            logger.info("SES: %.4f (hits=%d/%d, ddG=%.2f)",
                        ses_result["ses"], ses_result["n_hits"], ses_result["n_total"], ses_result["best_ddg"])
        except Exception as exc:
            logger.warning("SES computation failed: %s", exc)

    def _write_status(self, state: str, elapsed: float, error: str = "") -> None:
        status = {
            "experiment_id": self.config.experiment_id,
            "state": state,
            "elapsed_s": round(elapsed, 1),
            "error": error or None,
        }
        (self._output_dir / "status.json").write_text(
            json.dumps(status, indent=2), encoding="utf-8"
        )
