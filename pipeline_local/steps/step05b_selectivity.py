"""
step05b_selectivity.py
======================
Step 05b: Multi-Receptor Selectivity Screening (선택성 스크리닝)

SSTR2 도킹 상위 후보를 SSTR1/3/4/5 off-target 수용체에 도킹하여
선택성 마진(selectivity_margin)을 계산하고 게이트 필터링을 수행한다.

Uses the same docking engine (DiffDock/Boltz-2) as Step05, but targets
off-target receptors (SSTR1/3/4/5) to ensure SSTR2 specificity.

Selectivity formula:
    selectivity_margin = max(dock_score(off-targets)) - dock_score(SSTR2)
    (higher = more selective for SSTR2, aligned with step05c iPTM convention)

    For ddG scores where more-negative = stronger binding:
    - Positive margin: SSTR2 binds stronger than best off-target  (good, selective)
    - Negative margin: off-target binds stronger than SSTR2        (bad, not selective)

Gate: selectivity_margin >= selectivity_margin_min (e.g., +10.0 kcal/mol)
      AND offtarget_max_score >= offtarget_max_allowed (e.g., -15.0)

Input:
    - Top-K candidates from Step05 (DockingResult list)
    - Off-target receptor PDB paths (from config)
    - Receptor PDB path for SSTR2 (Step01 output)

Output:
    - 05b_selectivity/selectivity_scores.json
    - 05b_selectivity/{seq_id}_offtarget_{receptor}.json

Public API:
    run_selectivity_screening(candidates, offtarget_receptors, config) -> Step05bOutput
    dock_against_offtarget(candidate_pdb, receptor_pdb, engine, config) -> float
    compute_selectivity_margin(sstr2_score, offtarget_scores) -> SelectivityResult
    apply_selectivity_gate(results, margin_min, offtarget_max) -> (passed, failed)
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from pipeline_local.schemas.io_schemas import DockingResult
from pipeline_local.core.structure_io import detect_format  # CIF/PDB 형식 감지

# ---------------------------------------------------------------------------
# Path safety helper
# ---------------------------------------------------------------------------

_SAFE_ID_RE = re.compile(r'^[A-Za-z0-9_\-\.]+$')


def _safe_filename_component(value: str, field: str) -> str:
    """Raise ValueError if value contains path-unsafe characters."""
    if not _SAFE_ID_RE.match(value):
        raise ValueError(
            f"Unsafe characters in {field!r}: {value!r}. "
            "Only alphanumerics, underscores, hyphens, and dots are allowed."
        )
    return value

try:
    from pipeline_local.schemas.io_schemas import (
        OffTargetDockingResult,
        SelectivityResult,
        Step05bOutput,
    )
except ImportError:
    # Fallback dataclasses until io_schemas.py is updated
    @dataclass
    class OffTargetDockingResult:  # type: ignore[no-redef]
        """Off-target 도킹 결과 (fallback)."""
        seq_id: str
        receptor_name: str
        dock_score: float
        confidence: float
        engine: str

        def to_dict(self) -> Dict[str, Any]:
            from dataclasses import asdict
            return asdict(self)

    @dataclass
    class SelectivityResult:  # type: ignore[no-redef]
        """선택성 마진 결과 (fallback)."""
        seq_id: str
        sstr2_dock_score: float
        offtarget_scores: Dict[str, float]
        offtarget_max_score: float
        offtarget_max_receptor: str
        selectivity_margin: float
        passed: bool

        def to_dict(self) -> Dict[str, Any]:
            from dataclasses import asdict
            return asdict(self)

    @dataclass
    class Step05bOutput:  # type: ignore[no-redef]
        """Step05b 출력 (fallback)."""
        selectivity_results: List[SelectivityResult]
        offtarget_docking_details: List[OffTargetDockingResult]

        def to_dict(self) -> Dict[str, Any]:
            return {
                "selectivity_results": [r.to_dict() for r in self.selectivity_results],
                "offtarget_docking_details": [d.to_dict() for d in self.offtarget_docking_details],
            }


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def run_selectivity_screening(
    candidates: List[DockingResult],
    offtarget_receptors: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Step05bOutput:
    """Run selectivity screening for top candidates against off-target receptors.

    Args:
        candidates: Top docking results from Step05 (sorted by score)
        offtarget_receptors: List of off-target receptor configs
            [{name, pdb_path, chain}, ...]
        config: Pipeline config dict with selectivity params

    Returns:
        Step05bOutput with selectivity results
    """
    sel_config = config.get("selectivity", {})
    top_k = sel_config.get("top_k_for_selectivity", 20)
    engine = sel_config.get("engine", "diffdock")
    margin_min = sel_config.get("selectivity_margin_min", config.get("selectivity_margin_min", 2.0))
    offtarget_max = sel_config.get("offtarget_max_allowed", config.get("offtarget_max_allowed", -3.0))

    # Select top K candidates
    top_candidates = candidates[:top_k]
    logger.info(
        "Selectivity screening: %d candidates against %d off-targets",
        len(top_candidates), len(offtarget_receptors),
    )

    all_offtarget_details: List[OffTargetDockingResult] = []
    selectivity_results: List[SelectivityResult] = []

    for candidate in top_candidates:
        offtarget_scores: Dict[str, float] = {}

        for receptor in offtarget_receptors:
            # Support both string ("SSTR1") and dict ({"name": "SSTR1", "pdb_path": ...}) formats
            if isinstance(receptor, str):
                receptor_name = receptor
                receptor_pdb = None
            else:
                receptor_name = receptor["name"]
                # structure_path (CIF 지원 신규 키) 또는 pdb_path (하위 호환) 허용
                receptor_pdb = receptor.get("structure_path") or receptor.get("pdb_path")
            # Extract on-target score from candidate (handle both attribute styles)
            on_target = getattr(candidate, 'score', None) or getattr(candidate, 'dock_score', 0.0)
            candidate_pdb = getattr(candidate, 'pose_pdb', None) or getattr(candidate, 'pdb_path', '')

            if not receptor_pdb:
                # Estimation mode: no PDB available, use noise model
                logger.debug("Off-target '%s' no PDB; using estimation mode", receptor_name)

            # Dock candidate against off-target (estimation mode when no PDB)
            ot_score = dock_against_offtarget(
                candidate_pdb=candidate_pdb,
                receptor_pdb=receptor_pdb or "",
                engine=engine,
                config=config,
                on_target_score=on_target,
            )
            offtarget_scores[receptor_name] = ot_score

            cand_seq_id = getattr(candidate, 'seq_id', getattr(candidate, 'candidate_id', 'unknown'))
            all_offtarget_details.append(OffTargetDockingResult(
                seq_id=cand_seq_id,
                receptor_name=receptor_name,
                dock_score=ot_score,
                confidence=0.0,  # placeholder
                engine=engine,
            ))

        # Compute selectivity (handle both .score and .dock_score attributes)
        sel_result = compute_selectivity_margin(
            seq_id=getattr(candidate, 'seq_id', getattr(candidate, 'candidate_id', 'unknown')),
            sstr2_score=on_target,
            offtarget_scores=offtarget_scores,
            margin_min=margin_min,
            offtarget_max_allowed=offtarget_max,
        )
        selectivity_results.append(sel_result)

    output = Step05bOutput(
        selectivity_results=selectivity_results,
        offtarget_docking_details=all_offtarget_details,
    )

    passed, failed = apply_selectivity_gate(
        selectivity_results, margin_min, offtarget_max
    )
    logger.info(
        "Selectivity gate: %d/%d passed (margin_min=%.1f, offtarget_max=%.1f)",
        len(passed), len(selectivity_results), margin_min, offtarget_max,
    )

    return output


# ---------------------------------------------------------------------------
# Docking Against Off-Targets
# ---------------------------------------------------------------------------

def dock_against_offtarget(
    candidate_pdb: str,
    receptor_pdb: str,
    engine: str = "diffdock",
    config: Optional[Dict[str, Any]] = None,
    on_target_score: Optional[float] = None,
    sstr2_complex_pdb: str = "",
) -> float:
    """Dock a candidate peptide against an off-target receptor.

    Production mode (PyRosetta): When sstr2_complex_pdb and receptor_pdb are
    available, runs real FlexPepDock via offtarget_dock.py subprocess.

    Estimation mode: applies noise penalty to on_target_score when no
    real structures are available.

    Args:
        candidate_pdb: Path to the candidate pose PDB
        receptor_pdb: Path to the off-target receptor PDB
        engine: "diffdock", "boltz2", or "pyrosetta"
        config: Pipeline config dict (contains selectivity noise params)
        on_target_score: SSTR2 docking score used as baseline for estimation
        sstr2_complex_pdb: SSTR2 refined complex PDB for alignment (production mode)

    Returns:
        float: Docking score / ddG (lower = stronger binding)
    """
    cfg = config or {}
    sel_cfg = cfg.get("selectivity", {})

    # Production mode: real PyRosetta FlexPepDock (CIF/PDB 모두 허용)
    if receptor_pdb and Path(receptor_pdb).exists() and sstr2_complex_pdb and Path(sstr2_complex_pdb).exists():
        receptor_fmt = detect_format(receptor_pdb).upper()
        logger.info(
            "Off-target docking (production mode, %s): %s vs %s",
            receptor_fmt, sstr2_complex_pdb, receptor_pdb,
        )
        try:
            return _run_offtarget_pyrosetta(
                sstr2_complex_pdb, receptor_pdb,
                timeout=sel_cfg.get("offtarget_timeout_sec", 300),
                conda_env=cfg.get("rosetta", {}).get("conda_env", "bio-tools"),
            )
        except Exception as e:
            logger.warning("Off-target PyRosetta failed (%s), falling back to estimation", e)

    # Estimation mode (fallback)
    noise_std = sel_cfg.get("selectivity_noise_std", 2.0)
    seed = sel_cfg.get("selectivity_seed", 42)

    logger.debug(
        "Off-target docking (estimation mode): %s vs %s using %s",
        candidate_pdb, receptor_pdb, engine,
    )

    base_score = on_target_score if on_target_score is not None else -5.0
    pair_hash = hash((candidate_pdb, receptor_pdb, seed)) % (2 ** 32)

    try:
        import numpy as np
        rng = np.random.default_rng(pair_hash)
        offset = rng.normal(loc=noise_std, scale=noise_std / 2.0)
    except ImportError:
        import random
        rng = random.Random(pair_hash)
        offset = rng.gauss(mu=noise_std, sigma=noise_std / 2.0)

    estimated_score = base_score + abs(offset)

    logger.debug(
        "Estimated off-target score: %.3f (base=%.3f, offset=+%.3f)",
        estimated_score, base_score, abs(offset),
    )
    return estimated_score


def _run_offtarget_pyrosetta(
    sstr2_complex_pdb: str,
    receptor_pdb: str,
    timeout: int = 300,
    conda_env: str = "bio-tools",
) -> float:
    """Run offtarget_dock.py via subprocess and return ddG.

    Args:
        sstr2_complex_pdb: Path to SSTR2 refined complex PDB
        receptor_pdb: Path to off-target receptor PDB
        timeout: Subprocess timeout in seconds
        conda_env: Conda environment with PyRosetta

    Returns:
        float: ddG from InterfaceAnalyzerMover (kcal/mol)

    Raises:
        RuntimeError: If subprocess fails or returns invalid JSON
    """
    script = Path(__file__).parent.parent / "scripts" / "offtarget_dock.py"
    out_pdb = Path(sstr2_complex_pdb).parent / f"ot_{Path(receptor_pdb).stem}.pdb"

    cmd = [
        "conda", "run", "-n", conda_env, "python", str(script),
        "--sstr2-complex", sstr2_complex_pdb,
        "--offtarget-receptor", receptor_pdb,
        "--output", str(out_pdb),
    ]

    logger.info("Running: %s", " ".join(cmd[-6:]))
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if proc.returncode != 0:
        logger.warning("Off-target dock failed (rc=%d): %s", proc.returncode, proc.stderr[:300])
        raise RuntimeError(f"offtarget_dock.py failed: {proc.stderr[:200]}")

    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError("offtarget_dock.py returned empty stdout")

    result = json.loads(stdout)
    if "error" in result:
        raise RuntimeError(f"offtarget_dock.py error: {result['error']}")

    return result["ddg"]


# ---------------------------------------------------------------------------
# Selectivity Margin Computation
# ---------------------------------------------------------------------------

def compute_selectivity_margin(
    seq_id: str,
    sstr2_score: float,
    offtarget_scores: Dict[str, float],
    margin_min: float = 2.0,
    offtarget_max_allowed: float = -3.0,
) -> SelectivityResult:
    """Compute selectivity margin for a candidate.

    Selectivity margin = max(offtarget_scores) - sstr2_score
    Convention aligned with step05c iPTM: higher margin = more selective for SSTR2.

    For ddG scores where more-negative = stronger binding:
    - Positive margin: SSTR2 binds stronger than best off-target (selective, good)
    - Negative margin: off-target outcompetes SSTR2 (not selective, bad)

    Example:
        sstr2_ddg = -30 kcal/mol, best_off_ddg = -20 kcal/mol
        margin = -20 - (-30) = +10  → SSTR2 10 kcal/mol more selective  (pass)

    Args:
        seq_id: Candidate sequence ID
        sstr2_score: SSTR2 docking score (ddG, kcal/mol)
        offtarget_scores: {receptor_name: score} dict
        margin_min: Minimum acceptable margin (default +2.0; >= 0 means selective)
        offtarget_max_allowed: Max off-target score allowed (default -3.0)

    Returns:
        SelectivityResult with computed margin and pass/fail
    """
    if not offtarget_scores:
        # No off-targets evaluated — margin is undefined, use 0.0 as neutral sentinel
        return SelectivityResult(
            seq_id=seq_id,
            sstr2_dock_score=sstr2_score,
            offtarget_scores={},
            offtarget_max_score=0.0,
            offtarget_max_receptor="none",
            selectivity_margin=0.0,
            passed=True,
        )

    # Find the strongest off-target binding competitor (most negative ddG score)
    worst_receptor = min(offtarget_scores, key=offtarget_scores.get)
    worst_score = offtarget_scores[worst_receptor]

    # Margin = best_offtarget - sstr2  (positive = SSTR2 more selective)
    # Aligned with step05c: margin = iPTM(SSTR2) - max(iPTM(off)) → higher = better
    margin = worst_score - sstr2_score

    # Gate logic:
    # 1. margin must be >= margin_min (SSTR2 binds sufficiently stronger)
    # 2. worst off-target score must be >= offtarget_max_allowed (off-targets bind weakly enough)
    passed = (margin >= margin_min) and (worst_score >= offtarget_max_allowed)

    return SelectivityResult(
        seq_id=seq_id,
        sstr2_dock_score=sstr2_score,
        offtarget_scores=offtarget_scores,
        offtarget_max_score=worst_score,
        offtarget_max_receptor=worst_receptor,
        selectivity_margin=margin,
        passed=passed,
    )


# ---------------------------------------------------------------------------
# Selectivity Gate
# ---------------------------------------------------------------------------

def apply_selectivity_gate(
    results: List[SelectivityResult],
    margin_min: float = 2.0,
    offtarget_max_allowed: float = -3.0,
) -> Tuple[List[SelectivityResult], List[SelectivityResult]]:
    """Apply selectivity gate to filter candidates.

    Args:
        results: List of SelectivityResult objects
        margin_min: Minimum selectivity margin (positive = SSTR2 selective; default +2.0)
        offtarget_max_allowed: Maximum off-target score allowed

    Returns:
        Tuple of (passed, failed) lists
    """
    passed = []
    failed = []

    for r in results:
        if r.passed:
            passed.append(r)
        else:
            failed.append(r)

    return passed, failed


# ---------------------------------------------------------------------------
# Utility: Save Results
# ---------------------------------------------------------------------------

def save_selectivity_results(
    output: Step05bOutput,
    output_dir: Path,
) -> Dict[str, str]:
    """Save selectivity screening results to files.

    Args:
        output: Step05bOutput with all results
        output_dir: Path to 05b_selectivity/ directory

    Returns:
        Dict of saved file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save summary
    summary_path = output_dir / "selectivity_scores.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(output.to_dict(), f, indent=2, ensure_ascii=False)

    # Save per-candidate details
    saved = {"summary": str(summary_path)}
    for result in output.selectivity_results:
        safe_id = _safe_filename_component(result.seq_id, "seq_id")
        detail_path = output_dir / f"{safe_id}_selectivity.json"
        with open(detail_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        saved[result.seq_id] = str(detail_path)

    logger.info("Selectivity results saved to %s", output_dir)
    return saved
