"""
step02_backbone.py
==================
Step 02: 포켓 타겟 de novo 펩타이드 백본 생성 (Backbone Generation)

LocalModelRunner(rfdiffusion)를 사용하여 SSTR2 결합 포켓을 타겟으로 하는
de novo 펩타이드 백본 구조를 병렬로 N개 생성한다.

Uses LocalModelRunner("rfdiffusion") for local model inference to generate N
de-novo peptide backbone structures targeting the SSTR2 binding pocket.
Backbones are generated concurrently (one thread per backbone) using different
random seeds.

Input:
    - Receptor PDB (output of Step01)
    - Pocket definition (pocket_residues, contigs string, hotspot_res list)
    - n_backbone (N), diffusion_steps from pipeline_config.yaml

Output:
    - 02_backbone/backbone_00.pdb .. backbone_{N-1:02d}.pdb

Public API:
    generate_backbones(receptor_pdb, pocket_info, config) -> Step02Output
    generate_single_backbone(receptor_pdb, contigs, hotspot_res,
                             seed, diffusion_steps)         -> str (PDB text)
    validate_backbone(backbone_pdb)                         -> bool
    save_backbone(pdb_content, output_dir, index)           -> Path
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema imports
# ---------------------------------------------------------------------------

from pipeline_local.schemas.io_schemas import Step02Output
from pipeline_local.core.local_runner import LocalModelRunner


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_DIFFUSION_STEPS: int = 50
_DEFAULT_N_BACKBONE: int = 10
_MIN_ATOM_COUNT: int = 50          # Minimum ATOM lines for a valid backbone
_REQUIRED_BINDER_CHAIN: str = "A"  # RFdiffusion outputs new chain as A


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def generate_backbones(
    receptor_pdb: str,
    pocket_info: Dict[str, Any],
    config: Dict[str, Any],
) -> Step02Output:
    """N개의 de novo 펩타이드 백본을 병렬로 생성한다.

    Orchestration entry for Step 02.  Spawns ``n_backbone`` concurrent
    RFdiffusion calls, each with a unique integer seed.

    Args:
        receptor_pdb: Path to the receptor PDB file (Step01 output).
        pocket_info:  Dict with at minimum ``pocket_residues`` (List[int]).
        config:       Full pipeline configuration dict.

    Returns:
        Step02Output with paths to all successfully generated backbone PDBs.
    """
    run_id: str = config.get("run_id", "default_run")
    output_base: Path = Path(config.get("output_base_dir", "runs")) / run_id
    out_dir: Path = output_base / "02_backbone"
    out_dir.mkdir(parents=True, exist_ok=True)

    iteration_cfg: Dict[str, Any] = config.get("iteration", {})
    n_backbone: int = int(iteration_cfg.get("n_backbone", _DEFAULT_N_BACKBONE))
    diffusion_steps: int = int(iteration_cfg.get("diffusion_steps", _DEFAULT_DIFFUSION_STEPS))
    contigs: str = config.get("contigs", "B1-369/0 10-30")
    hotspot_res: List[str] = config.get("hotspot_res", [])

    # Read receptor PDB content
    receptor_pdb_content: str = Path(receptor_pdb).read_text(encoding="utf-8")

    design_params: Dict[str, Any] = {
        "contigs": contigs,
        "hotspot_res": hotspot_res,
        "diffusion_steps": diffusion_steps,
        "n_backbone": n_backbone,
    }

    logger.info(
        "[Step02] Generating %d backbones (contigs='%s', hotspot=%s, steps=%d).",
        n_backbone,
        contigs,
        hotspot_res,
        diffusion_steps,
    )

    backbone_paths: List[str] = []
    failed_seeds: List[int] = []

    # LOCAL MODE: 순차 실행 (GPU 메모리 충돌 방지, subprocess가 매번 모델 로드)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_idx = {
            executor.submit(
                _generate_and_save,
                receptor_pdb_content,
                contigs,
                hotspot_res,
                seed,
                diffusion_steps,
                out_dir,
                seed,  # seed == backbone index for reproducibility
            ): seed
            for seed in range(n_backbone)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                path = future.result()
                if path:
                    backbone_paths.append(str(path))
                    logger.info("[Step02] Backbone %02d saved -> %s", idx, path)
                else:
                    failed_seeds.append(idx)
                    logger.warning("[Step02] Backbone %02d failed validation, skipped.", idx)
            except Exception as exc:
                failed_seeds.append(idx)
                logger.error("[Step02] Backbone %02d error: %s", idx, exc)

    backbone_paths.sort()  # deterministic order
    logger.info(
        "[Step02] Generated %d/%d backbones successfully (%d failed: %s).",
        len(backbone_paths),
        n_backbone,
        len(failed_seeds),
        failed_seeds,
    )

    # 백본 0개 생성 시 명시적 에러 → orchestrator가 catch하여 STATUS_FILE에 기록
    if not backbone_paths:
        raise RuntimeError(
            f"[Step02] Backbone generation failed: 0 PDBs generated out of {n_backbone} "
            f"(all {len(failed_seeds)} seeds failed). "
            "Check RFdiffusion logs or conda env."
        )

    return Step02Output(
        backbone_pdbs=backbone_paths,
        design_params=design_params,
        n_generated=len(backbone_paths),
    )


def generate_single_backbone(
    receptor_pdb: str,
    contigs: str,
    hotspot_res: List[str],
    seed: int,
    diffusion_steps: int = _DEFAULT_DIFFUSION_STEPS,
) -> str:
    """LocalModelRunner(rfdiffusion)를 단일 호출하여 백본 PDB 텍스트를 반환한다.

    # LOCAL MODE: replaced NIM API call
    원본 코드: requests.post("https://health.api.nvidia.com/v1/biology/ipd/rfdiffusion/generate", ...)
    대체: LocalModelRunner.run("rfdiffusion", {...})

    Args:
        receptor_pdb:     PDB *content* string (not a file path).
        contigs:          Contig string, e.g. ``"B1-369/0 10-30"``.
        hotspot_res:      List of hotspot residue IDs, e.g. ``["B122", "B127"]``.
        seed:             Random seed for reproducibility.
        diffusion_steps:  Number of diffusion reversal steps.

    Returns:
        Generated backbone PDB text string.

    Raises:
        RuntimeError: On model failure.
    """
    payload: Dict[str, Any] = {
        "input_pdb": receptor_pdb,
        "contigs": contigs,
        "diffusion_steps": diffusion_steps,
        "random_seed": seed,
    }
    if hotspot_res:
        payload["hotspot_res"] = hotspot_res

    logger.debug("[Step02] LocalModelRunner rfdiffusion (seed=%d, steps=%d)", seed, diffusion_steps)

    runner = LocalModelRunner()
    # LOCAL MODE: replaced NIM API call
    data = runner.run("rfdiffusion", payload)

    # wrapper는 output_pdbs (리스트), step02는 output_pdb (단수) 기대
    output_pdbs = data.get("output_pdbs", [])
    pdb_text: Optional[str] = (
        (output_pdbs[0] if output_pdbs else None)
        or data.get("output_pdb")
        or data.get("pdb")
        or data.get("result", {}).get("output_pdb")
    )
    if not pdb_text:
        raise RuntimeError(
            f"[Step02] RFdiffusion local model returned no 'output_pdb'. Keys: {list(data.keys())}"
        )
    return pdb_text


def validate_backbone(backbone_pdb: str) -> bool:
    """백본 PDB 텍스트의 최소 유효성을 검사한다.

    Checks:
    * Minimum ATOM record count (``_MIN_ATOM_COUNT``).
    * Presence of at least one chain record.

    Args:
        backbone_pdb: PDB text to validate.

    Returns:
        True when the backbone passes all checks.
    """
    atom_lines = [l for l in backbone_pdb.splitlines() if l.startswith("ATOM")]
    if len(atom_lines) < _MIN_ATOM_COUNT:
        logger.warning(
            "[Step02] validate_backbone: only %d ATOM lines (min=%d).",
            len(atom_lines),
            _MIN_ATOM_COUNT,
        )
        return False

    chains_present = {l[21] for l in atom_lines if len(l) >= 22}
    if not chains_present:
        logger.warning("[Step02] validate_backbone: no chain IDs found in ATOM records.")
        return False

    logger.debug(
        "[Step02] validate_backbone: %d ATOM lines, chains=%s -> OK",
        len(atom_lines),
        chains_present,
    )
    return True


def save_backbone(pdb_content: str, output_dir: Path, index: int) -> Path:
    """백본 PDB 텍스트를 파일에 저장하고 경로를 반환한다.

    Args:
        pdb_content: PDB text string to write.
        output_dir:  Target directory (created if missing).
        index:       0-based backbone index, used to form the filename.

    Returns:
        Path to the written file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"backbone_{index:02d}.pdb"
    path.write_text(pdb_content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _generate_and_save(
    receptor_pdb_content: str,
    contigs: str,
    hotspot_res: List[str],
    seed: int,
    diffusion_steps: int,
    out_dir: Path,
    index: int,
) -> Optional[Path]:
    """단일 백본 생성 + 검증 + 저장 (ThreadPoolExecutor 작업 단위)."""
    try:
        pdb_text = generate_single_backbone(
            receptor_pdb=receptor_pdb_content,
            contigs=contigs,
            hotspot_res=hotspot_res,
            seed=seed,
            diffusion_steps=diffusion_steps,
        )
    except Exception as exc:
        logger.error("[Step02] generate_single_backbone(seed=%d) failed: %s", seed, exc)
        return None

    if not validate_backbone(pdb_text):
        return None

    return save_backbone(pdb_text, out_dir, index)


# ---------------------------------------------------------------------------
# CLI / standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Step02: Backbone generation standalone test")
    parser.add_argument("--receptor-pdb", required=True, help="Path to receptor PDB")
    parser.add_argument("--n-backbone", type=int, default=2)
    parser.add_argument("--output-dir", default="runs/test_run")
    args = parser.parse_args()

    cfg: Dict[str, Any] = {
        "run_id": "test_run",
        "output_base_dir": args.output_dir,
        "contigs": "B1-369/0 10-30",
        "hotspot_res": ["B122", "B127", "B184", "B197", "B205", "B272", "B294"],
        "iteration": {"n_backbone": args.n_backbone, "diffusion_steps": 50},
    }
    result = generate_backbones(args.receptor_pdb, {}, cfg)
    print(f"Step02 result: {result.n_generated} backbones at {result.backbone_pdbs}")
