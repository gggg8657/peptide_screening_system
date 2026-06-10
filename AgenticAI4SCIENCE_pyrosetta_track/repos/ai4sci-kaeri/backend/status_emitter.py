"""
Pipeline Status Emitter
========================
Writes pipeline status to a shared JSON file so the API server can serve
it to the React frontend dashboard.

Usage in run_pipeline_live.py:
    from backend.status_emitter import StatusEmitter

    emitter = StatusEmitter(run_id="live_run_001")
    emitter.update_step("step02", "running")
    emitter.update_step("step02", "completed", duration="34m")
    emitter.update_agent("planner", status="active", message="Planning...")
    emitter.set_candidates([...])
    emitter.flush()
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


STATUS_FILE = Path(os.environ.get(
    "PIPELINE_STATUS_FILE",
    # 2026-05-14: writer 경로 통일 (P1-2 reader와 일치, P01 패치)
    "/tmp/pipeline_local_status.json",
))

ARCHIVE_DIR = Path(os.environ.get(
    "PIPELINE_ARCHIVE_DIR",
    "runs/pyrosetta_flow/archives",
))

# Default pipeline steps matching the frontend's expected structure
DEFAULT_STEPS = [
    {"id": "step01", "label": "OpenFold3",    "shortLabel": "Step01", "status": "pending"},
    {"id": "step02", "label": "RFdiffusion",  "shortLabel": "Step02", "status": "pending"},
    {"id": "step03", "label": "ProteinMPNN",  "shortLabel": "Step03", "status": "pending"},
    {"id": "step03b",   "label": "BLOSUM Mutation",      "shortLabel": "Step03b",    "status": "pending"},
    {"id": "step03b_qc","label": "Stability Pre-screen", "shortLabel": "Step03b-QC", "status": "pending"},
    {"id": "step04", "label": "ESMFold QC",   "shortLabel": "Step04", "status": "pending"},
    {"id": "step05", "label": "DiffDock",     "shortLabel": "Step05", "status": "pending"},
    {"id": "step06_baseline", "label": "PyRosetta baseline", "shortLabel": "Step06-BL", "status": "pending"},
    {"id": "step06", "label": "PyRosetta",    "shortLabel": "Step06", "status": "pending"},
    {"id": "step05b","label": "Selectivity",  "shortLabel": "Step05b","status": "pending"},
    {"id": "step07", "label": "Analysis",     "shortLabel": "Step07", "status": "pending"},
    {"id": "step08", "label": "Stability",    "shortLabel": "Step08", "status": "pending"},
    {"id": "step09", "label": "MolMIM",       "shortLabel": "Step09", "status": "pending"},
]

DEFAULT_AGENTS = [
    {"id": "planner",      "name": "Planner",      "type": "LLM",  "status": "idle", "lastMessage": "", "taskCount": 0, "last_active_ts": None, "is_runtime_active": False},
    {"id": "qc-ranker",    "name": "QC & Ranker",  "type": "Code", "status": "idle", "lastMessage": "", "taskCount": 0, "last_active_ts": None, "is_runtime_active": False},
    {"id": "diversity-mgr", "name": "DiversityMgr", "type": "Code", "status": "idle", "lastMessage": "", "taskCount": 0, "last_active_ts": None, "is_runtime_active": False},
    {"id": "critic",       "name": "Critic",       "type": "LLM",  "status": "idle", "lastMessage": "", "taskCount": 0, "last_active_ts": None, "is_runtime_active": False},
    {"id": "reporter",     "name": "Reporter",     "type": "LLM",  "status": "idle", "lastMessage": "", "taskCount": 0, "last_active_ts": None, "is_runtime_active": False},
]

DEFAULT_ROSETTA_SUBSTEPS = [
    {"id": "step06_prepare", "label": "Prepare", "status": "pending"},
    {"id": "step06_mutate", "label": "Mutate", "status": "pending"},
    {"id": "step06_refine", "label": "Refine", "status": "pending"},
    {"id": "step06_score", "label": "Score", "status": "pending"},
    {"id": "step06_qc", "label": "QC Gate", "status": "pending"},
    {"id": "step06_critic", "label": "Critic", "status": "pending"},
    {"id": "step06_reporter", "label": "Reporter", "status": "pending"},
]


class StatusEmitter:
    """Manages pipeline status and writes it to a shared JSON file."""

    def __init__(
        self,
        run_id: str = "live_run",
        total_iterations: int = 5,
        status_file: Optional[Path] = None,
        llm_model: str = "NoneProvider (rule-based)",
        archive_dir: Optional[Path] = None,
    ) -> None:
        self._file = status_file or STATUS_FILE
        self._archive_dir = archive_dir or ARCHIVE_DIR
        self._archive_previous_run()
        self._state: Dict[str, Any] = {
            "run_id": run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "iteration": 1,
            "total_iterations": total_iterations,
            "llm_model": llm_model,
            "target": "SSTR2",
            "reference": "DOTATATE (AGCKNFFWKTFTSC, 14-aa)",
            "steps": [dict(s) for s in DEFAULT_STEPS],
            "agents": [dict(a) for a in DEFAULT_AGENTS],
            "rosetta_substeps": [dict(s) for s in DEFAULT_ROSETTA_SUBSTEPS],
            "timeline": [],
            "candidates": [],
            "historical_candidates": [],
            "qc_gates": [],
            "convergence": [],
            "live_apis": {"esmfold": "pending", "molmim": "pending"},
            "best_candidate": None,
            "molecules": [],
            "visualization_images": [],
            "baseline": None,
            "completed": False,
        }
        self.flush()

    def flush(self) -> None:
        """Write current state to the status file (atomic + locked).

        Uses fcntl.flock() to prevent concurrent write corruption from
        parallel pipeline workers (C5 fix).
        """
        self._state["updated_at"] = datetime.now(timezone.utc).isoformat()
        content = json.dumps(self._state, ensure_ascii=False, indent=2)
        tmp_path = self._file.with_suffix(".tmp")
        lock_path = self._file.with_suffix(".lock")
        with open(lock_path, "w") as lock_fd:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
            try:
                tmp_path.write_text(content, encoding="utf-8")
                tmp_path.rename(self._file)
            finally:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)

    # ── Step updates ──────────────────────────────────────────────────────

    def update_step(
        self,
        step_id: str,
        status: str,
        duration: Optional[str] = None,
    ) -> None:
        """Update a pipeline step's status."""
        for step in self._state["steps"]:
            if step["id"] == step_id:
                step["status"] = status
                if duration:
                    step["duration"] = duration
                break
        self.flush()

    def start_step(self, step_id: str) -> float:
        """Mark step as running and return start timestamp."""
        self.update_step(step_id, "running")
        return time.time()

    def complete_step(self, step_id: str, start_time: float) -> None:
        """Mark step as completed with elapsed duration."""
        elapsed = time.time() - start_time
        if elapsed < 60:
            duration = f"{elapsed:.0f}s"
        else:
            duration = f"{elapsed / 60:.1f}m"
        self.update_step(step_id, "completed", duration=duration)

    def fail_step(self, step_id: str, start_time: float) -> None:
        """Mark step as failed."""
        elapsed = time.time() - start_time
        duration = f"{elapsed:.0f}s" if elapsed < 60 else f"{elapsed / 60:.1f}m"
        self.update_step(step_id, "failed", duration=duration)

    # ── Agent updates ─────────────────────────────────────────────────────

    def update_agent(
        self,
        agent_id: str,
        status: str = "idle",
        message: str = "",
        task_count_delta: int = 0,
        report: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update an agent's status, message, and optional report data."""
        for agent in self._state["agents"]:
            if agent["id"] == agent_id:
                agent["status"] = status
                if message:
                    agent["lastMessage"] = message
                agent["taskCount"] = agent.get("taskCount", 0) + task_count_delta
                if report is not None:
                    agent["report"] = report
                if status == "active":
                    agent["last_active_ts"] = datetime.now(timezone.utc).isoformat()
                    agent["is_runtime_active"] = True
                break
        self.flush()

    # ── Candidate / QC updates ────────────────────────────────────────────

    def set_candidates(self, candidates: List[Dict[str, Any]]) -> None:
        """Accumulate candidates across iterations, re-ranking by ddG.

        2026-06-09 fix: 동일 id 가 재전송되면 무시하지 않고 **non-None 필드를 병합**한다.
        (QC ranker 가 enrichment 없는 후보를 먼저 push 한 뒤 dashboard-enrich 가 동일 id 로
        half_life_h/admet_score/mo_score 를 push 하는데, 이전 구현은 후자를 드롭해
        대시보드에 다목적 필드가 None 으로 남았다.)
        """
        existing = self._state.get("candidates", [])
        by_id = {c["id"]: c for c in existing}
        for c in candidates:
            cid = c["id"]
            if cid not in by_id:
                existing.append(c)
                by_id[cid] = c
            else:
                # 기존 엔트리에 새 값(None 아님) 병합 — 더 풍부한 쪽으로 갱신
                for k, v in c.items():
                    if v is not None:
                        by_id[cid][k] = v
        # Re-rank by ddG ascending (lower is better)
        existing.sort(key=lambda x: float(x.get("ddG", 999.0)))
        for idx, c in enumerate(existing):
            c["rank"] = idx + 1
        self._state["candidates"] = existing
        self.flush()

    def set_historical_candidates(self, candidates: List[Dict[str, Any]]) -> None:
        """Replace historical aggregated candidate rankings."""
        self._state["historical_candidates"] = candidates
        self.flush()

    def set_qc_gates(self, gates: List[Dict[str, Any]]) -> None:
        """Replace QC gate results."""
        self._state["qc_gates"] = gates
        self.flush()

    def add_convergence_point(
        self,
        iteration: int,
        best_ddg: float,
        top_candidates: int,
        converged: bool = False,
    ) -> None:
        """Append a convergence data point."""
        self._state["convergence"].append({
            "iteration": iteration,
            "bestDdG": best_ddg,
            "topCandidates": top_candidates,
            "converged": converged,
        })
        self.flush()

    def set_convergence(self, data: Dict[str, Any]) -> None:
        """Write convergence detection results to state."""
        self._state["convergence_status"] = data
        self.flush()

    def set_baseline(self, baseline: Dict[str, Any]) -> None:
        """Set baseline (reference) refinement results for comparison."""
        self._state["baseline"] = baseline
        self.flush()

    def set_best_candidate(self, candidate: Dict[str, Any]) -> None:
        """Set the current best candidate."""
        self._state["best_candidate"] = candidate
        self.flush()

    def set_molecules(self, molecules: List[Dict[str, Any]]) -> None:
        """Set MolMIM molecule results."""
        self._state["molecules"] = molecules
        self.flush()

    def set_visualization_images(self, images: List[Dict[str, Any]]) -> None:
        """Set visualization image paths for current iteration."""
        self._state["visualization_images"] = images
        self.flush()

    # ── API status ────────────────────────────────────────────────────────

    def set_api_status(self, api_name: str, status: str) -> None:
        """Update a live API's status (pending/live/failed)."""
        self._state["live_apis"][api_name] = status
        self.flush()

    # ── Iteration / completion ────────────────────────────────────────────

    def set_iteration(self, iteration: int) -> None:
        """Update current iteration number."""
        self._state["iteration"] = iteration
        self.flush()

    def set_total_iterations(self, total_iterations: int) -> None:
        """Update total iteration count shown in the dashboard."""
        self._state["total_iterations"] = max(1, int(total_iterations))
        self.flush()

    def reset_steps(self, skip_steps: Optional[List[str]] = None) -> None:
        """Reset all step statuses to pending for a new iteration."""
        skip = set(skip_steps or [])
        for step in self._state["steps"]:
            if step["id"] not in skip:
                step["status"] = "pending"
                step.pop("duration", None)
        self.flush()

    # ── Rosetta sub-step updates ───────────────────────────────────────────

    def update_rosetta_substep(
        self,
        substep_id: str,
        status: str,
        duration: Optional[str] = None,
    ) -> None:
        """Update a PyRosetta internal sub-step status."""
        for substep in self._state["rosetta_substeps"]:
            if substep["id"] == substep_id:
                substep["status"] = status
                if duration:
                    substep["duration"] = duration
                break
        self.flush()

    def start_rosetta_substep(self, substep_id: str) -> float:
        """Mark rosetta sub-step running and return start timestamp."""
        self.update_rosetta_substep(substep_id, "running")
        return time.time()

    def complete_rosetta_substep(self, substep_id: str, start_time: float) -> None:
        """Mark rosetta sub-step completed with elapsed duration."""
        elapsed = time.time() - start_time
        duration = f"{elapsed:.0f}s" if elapsed < 60 else f"{elapsed / 60:.1f}m"
        self.update_rosetta_substep(substep_id, "completed", duration=duration)

    def fail_rosetta_substep(self, substep_id: str, start_time: float) -> None:
        """Mark rosetta sub-step failed with elapsed duration."""
        elapsed = time.time() - start_time
        duration = f"{elapsed:.0f}s" if elapsed < 60 else f"{elapsed / 60:.1f}m"
        self.update_rosetta_substep(substep_id, "failed", duration=duration)

    def reset_rosetta_substeps(self) -> None:
        """Reset all PyRosetta internal sub-steps to pending."""
        for substep in self._state["rosetta_substeps"]:
            substep["status"] = "pending"
            substep.pop("duration", None)
        self.flush()

    # ── Timeline updates ───────────────────────────────────────────────────

    def append_timeline_event(
        self,
        iteration: int,
        stage: str,
        status: str,
        message: str = "",
    ) -> None:
        """Append iteration timeline event for loop visualization."""
        self._state["timeline"].append(
            {
                "iteration": iteration,
                "stage": stage,
                "status": status,
                "message": message,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.flush()

    def set_llm_model(self, model: str) -> None:
        """Update the LLM model label."""
        self._state["llm_model"] = model
        self.flush()

    def set_completed(self) -> None:
        """Mark the pipeline as completed and save archive snapshot."""
        self._state["completed"] = True
        self.flush()
        self._save_archive()

    # ── Archival ─────────────────────────────────────────────────────────

    def _archive_previous_run(self) -> None:
        """If previous status file has a completed run, archive it before overwriting."""
        if not self._file.exists():
            return
        try:
            prev = json.loads(self._file.read_text(encoding="utf-8"))
            if prev.get("completed") and prev.get("run_id"):
                self._archive_dir.mkdir(parents=True, exist_ok=True)
                archive_path = self._archive_dir / f'{prev["run_id"]}_dashboard.json'
                if not archive_path.exists():
                    archive_path.write_text(
                        json.dumps(prev, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
        except (json.JSONDecodeError, OSError):
            pass

    def _save_archive(self) -> None:
        """Save current completed run to archive directory, including PDB files."""
        run_id = self._state.get("run_id", "unknown")
        self._archive_dir.mkdir(parents=True, exist_ok=True)

        # Copy PDB files referenced by candidates into archive subdirectory
        pdb_archive_dir = self._archive_dir / run_id
        candidates = self._state.get("candidates", [])
        for c in candidates:
            pdb_path = c.get("pdb_path")
            if not pdb_path:
                continue
            src = Path(pdb_path)
            if not src.is_absolute():
                src = Path(self._file).parent.parent / pdb_path
            if src.exists() and src.is_file():
                dest_dir = pdb_archive_dir / src.parent.name
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / src.name
                if not dest.exists():
                    shutil.copy2(src, dest)
                # Update candidate to use archive-relative path
                c["pdb_path"] = str(Path("archives") / run_id / src.parent.name / src.name)

        archive_path = self._archive_dir / f"{run_id}_dashboard.json"
        archive_path.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
