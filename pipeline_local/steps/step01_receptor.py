"""
step01_receptor.py
==================
Step 01: SSTR2 구조 준비 (Receptor Structure Preparation)

수용체(SSTR2) PDB 구조를 준비하고 결합 포켓(binding pocket)을 정의한다.
구조 예측에는 LocalModelRunner(openfold3)를 사용하며, 사용할 수 없을 때는
data/ 디렉토리의 기존 PDB 파일로 폴백(fallback)한다.

Prepares the SSTR2 receptor PDB and defines the binding pocket.
Uses LocalModelRunner for openfold3 structure prediction; falls back to a
pre-existing PDB from the data/ directory when unavailable.

Input:
    - SSTR2 protein sequence (FASTA / plain string)
    - Ligand/complex PDB (optional, for pocket extraction from known complex)
    - Or: pre-existing receptor PDB in data/

Output:
    - 01_receptor/sstr2_receptor.pdb   -- cleaned receptor-only PDB
    - 01_receptor/binding_pocket.json  -- pocket residue numbers + centroid

Public API:
    prepare_receptor(config)               -> Step01Output
    analyze_binding_pocket(pdb, chain, d)  -> dict
    extract_receptor_chain(pdb, chain)     -> str  (PDB text)
    fallback_load_existing(data_dir)       -> Step01Output
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------

from pipeline_local.schemas.io_schemas import Step01Output
from pipeline_local.core.local_runner import LocalModelRunner
from pipeline_local.core.structure_io import detect_format, read_structure_text


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_RECEPTOR_CHAIN: str = "B"
_DEFAULT_POCKET_CUTOFF: float = 5.0   # Angstroms


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def prepare_receptor(config: Dict[str, Any]) -> Step01Output:
    """SSTR2 수용체 구조를 준비하고 포켓 정의를 반환한다.

    Orchestration entry point for Step 01.  Tries the following in order:

    1. If ``config["receptor"]["existing_pdb"]`` is set and the file exists,
       load it directly (fastest path – no model call).
    2. Otherwise call LocalModelRunner("openfold3") to predict the structure.
    3. On any failure, fall back to ``fallback_load_existing()``.

    Args:
        config: Pipeline configuration dict loaded from pipeline_config.yaml.
                Must contain ``receptor``, ``output_base_dir``, and ``run_id``
                keys (plus optionally ``receptor.existing_pdb``).

    Returns:
        Step01Output with paths to the receptor PDB and pocket JSON.
    """
    run_id: str = config.get("run_id", "default_run")
    output_base: Path = Path(config.get("output_base_dir", "runs")) / run_id
    out_dir: Path = output_base / "01_receptor"
    out_dir.mkdir(parents=True, exist_ok=True)

    receptor_cfg: Dict[str, Any] = config.get("receptor", {})
    data_dir: Path = Path(config.get("data_dir", "data"))

    # ------------------------------------------------------------------
    # Path 1: existing structure supplied in config
    # existing_structure (신규 키) 또는 existing_pdb (하위 호환) 둘 다 허용
    # .cif / .mmcif 확장자도 지원
    # ------------------------------------------------------------------
    existing_pdb: Optional[str] = (
        receptor_cfg.get("existing_structure") or receptor_cfg.get("existing_pdb")
    )
    if existing_pdb and Path(existing_pdb).exists():
        fmt = detect_format(existing_pdb)
        logger.info("[Step01] Pre-existing receptor structure (%s): %s", fmt.upper(), existing_pdb)
        receptor_chain = receptor_cfg.get("chain", _DEFAULT_RECEPTOR_CHAIN)
        receptor_pdb_text = read_structure_text(existing_pdb)
        if fmt == "pdb":
            receptor_pdb_text = extract_receptor_chain(receptor_pdb_text, receptor_chain)
        else:
            # CIF → PDB 변환: RFdiffusion은 PDB 형식만 읽을 수 있음
            logger.info("[Step01] CIF 형식 감지 — PyRosetta로 PDB 변환 시도")
            receptor_pdb_text = _convert_cif_to_pdb(existing_pdb, receptor_pdb_text)
        return _finalize_output(
            receptor_pdb_text=receptor_pdb_text,
            pocket_residues=receptor_cfg.get("pocket_residues", []),
            chain_id=receptor_chain,
            out_dir=out_dir,
        )

    # ------------------------------------------------------------------
    # Path 2: LocalModelRunner — openfold3
    # ------------------------------------------------------------------
    try:
        logger.info("[Step01] Calling local openfold3 model to predict SSTR2 structure...")
        receptor_pdb_text = _call_openfold3_local(receptor_cfg, config)
        receptor_chain = receptor_cfg.get("chain", _DEFAULT_RECEPTOR_CHAIN)
        receptor_pdb_text = extract_receptor_chain(receptor_pdb_text, receptor_chain)
        return _finalize_output(
            receptor_pdb_text=receptor_pdb_text,
            pocket_residues=receptor_cfg.get("pocket_residues", []),
            chain_id=receptor_chain,
            out_dir=out_dir,
        )
    except Exception as exc:
        logger.warning(
            "[Step01] Local openfold3 failed (%s). Falling back to pre-existing structure.",
            exc,
        )

    # ------------------------------------------------------------------
    # Path 3: fallback
    # ------------------------------------------------------------------
    return fallback_load_existing(data_dir, out_dir, receptor_cfg)


def analyze_binding_pocket(
    receptor_pdb: str,
    ligand_chain: str,
    distance_cutoff: float = _DEFAULT_POCKET_CUTOFF,
) -> Dict[str, Any]:
    """수용체 PDB와 리간드 체인을 기반으로 결합 포켓을 분석한다.

    Identifies receptor residues within *distance_cutoff* Angstroms of any
    atom in *ligand_chain*.  Returns residue numbers, a centroid, and a
    bounding-sphere radius.

    Args:
        receptor_pdb:    Full PDB text (may contain multiple chains).
        ligand_chain:    Chain ID of the ligand / peptide in *receptor_pdb*.
        distance_cutoff: Distance threshold in Angstroms.

    Returns:
        dict with keys:
            ``pocket_residues`` (List[int]),
            ``centroid``        (List[float]),
            ``radius``          (float).
    """
    try:
        from Bio.PDB import PDBParser  # type: ignore
        from io import StringIO
        import numpy as np

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure("complex", StringIO(receptor_pdb))

        ligand_coords: List[Tuple[float, float, float]] = []
        receptor_atoms: List[Any] = []

        for model in structure:
            for chain in model:
                for residue in chain:
                    for atom in residue:
                        if chain.id == ligand_chain:
                            ligand_coords.append(atom.get_vector().get_array())
                        else:
                            receptor_atoms.append((chain.id, residue.id[1], atom))

        if not ligand_coords:
            logger.warning(
                "[Step01] No atoms found in ligand chain '%s'. "
                "Returning empty pocket.",
                ligand_chain,
            )
            return {"pocket_residues": [], "centroid": [0.0, 0.0, 0.0], "radius": 0.0}

        ligand_arr = _np_array(ligand_coords)
        pocket_residue_set: set = set()

        for chain_id, res_num, atom in receptor_atoms:
            atom_coord = _np_array([atom.get_vector().get_array()])
            dists = _cdist_min(atom_coord, ligand_arr)
            if dists <= distance_cutoff:
                pocket_residue_set.add(res_num)

        centroid = ligand_arr.mean(axis=0).tolist()
        radius = float(
            max(
                float(_np_norm(coord - _np_array([centroid])))
                for coord in ligand_arr
            )
        ) if len(ligand_arr) > 0 else 0.0

        logger.info(
            "[Step01] Pocket analysis: %d residues within %.1f Å of ligand chain '%s'.",
            len(pocket_residue_set),
            distance_cutoff,
            ligand_chain,
        )
        return {
            "pocket_residues": sorted(pocket_residue_set),
            "centroid": centroid,
            "radius": radius,
        }

    except ImportError:
        logger.warning(
            "[Step01] BioPython/numpy not available. "
            "Returning empty pocket from analyze_binding_pocket()."
        )
        return {"pocket_residues": [], "centroid": [0.0, 0.0, 0.0], "radius": 0.0}


def extract_receptor_chain(complex_pdb: str, receptor_chain: str = "B") -> str:
    """복합체 PDB에서 수용체 체인만 추출하여 반환한다.

    Filters the PDB text so that only ATOM/HETATM records belonging to
    *receptor_chain* are retained.  TER and END records are preserved.

    Args:
        complex_pdb:     Full PDB text potentially containing multiple chains.
        receptor_chain:  Chain identifier to keep (default ``"B"``).

    Returns:
        Filtered PDB text containing only the receptor chain records.
    """
    lines_out: List[str] = []
    for line in complex_pdb.splitlines():
        record = line[:6].strip()
        if record in ("ATOM", "HETATM"):
            # Column 22 (0-indexed 21) is the chain ID in standard PDB format
            if len(line) >= 22 and line[21] == receptor_chain:
                lines_out.append(line)
        elif record in ("TER", "END", "REMARK", "HEADER", "TITLE", "CRYST1"):
            lines_out.append(line)
    if not lines_out or lines_out[-1].strip() != "END":
        lines_out.append("END")
    logger.info(
        "[Step01] Extracted chain '%s': %d ATOM/HETATM lines.",
        receptor_chain,
        sum(1 for l in lines_out if l[:6].strip() in ("ATOM", "HETATM")),
    )
    return "\n".join(lines_out) + "\n"


def fallback_load_existing(
    data_dir: Path,
    out_dir: Optional[Path] = None,
    receptor_cfg: Optional[Dict[str, Any]] = None,
) -> Step01Output:
    """data/ ディレクトリの既存 SSTR2 PDB を読み込む（フォールバック）。

    Loads a pre-existing SSTR2 PDB from *data_dir* when local model
    prediction is unavailable.  Searches for files matching ``sstr2*.pdb``
    or ``receptor*.pdb`` (case-insensitive).

    Args:
        data_dir:     Directory to search for pre-existing PDB files.
        out_dir:      Destination directory for copied output files.
                      If None, uses ``data_dir``.
        receptor_cfg: Optional receptor section from pipeline_config.yaml.

    Returns:
        Step01Output populated from the found PDB.

    Raises:
        FileNotFoundError: When no suitable PDB file is found in *data_dir*.
    """
    receptor_cfg = receptor_cfg or {}
    data_path = Path(data_dir)
    out_path = Path(out_dir) if out_dir else data_path

    # Search patterns in priority order (PDB 우선, CIF/mmCIF 폴백)
    candidates: List[Path] = []
    for pattern in ("sstr2*.pdb", "receptor*.pdb", "*.pdb",
                    "sstr2*.cif", "receptor*.cif", "*.cif", "*.mmcif"):
        candidates.extend(sorted(data_path.glob(pattern)))
    if not candidates:
        raise FileNotFoundError(
            f"[Step01] No receptor structure found in {data_path}. "
            "Provide 'receptor.existing_structure' in config or place a .pdb/.cif in the data/ dir."
        )

    chosen = candidates[0]
    fmt = detect_format(str(chosen))
    logger.info("[Step01] Fallback: loading receptor structure (%s) from %s", fmt.upper(), chosen)

    receptor_chain = receptor_cfg.get("chain", _DEFAULT_RECEPTOR_CHAIN)
    pdb_text = chosen.read_text(encoding="utf-8")
    if fmt == "pdb":
        chains_present = {l[21] for l in pdb_text.splitlines() if l[:4] == "ATOM" and len(l) >= 22}
        if len(chains_present) > 1:
            pdb_text = extract_receptor_chain(pdb_text, receptor_chain)
    else:
        # CIF → PDB 변환: RFdiffusion은 PDB 형식만 읽을 수 있음
        logger.info("[Step01] Fallback: CIF 형식 — PyRosetta로 PDB 변환 시도")
        pdb_text = _convert_cif_to_pdb(str(chosen), pdb_text)

    pocket_residues: List[int] = receptor_cfg.get("pocket_residues", [])
    return _finalize_output(
        receptor_pdb_text=pdb_text,
        pocket_residues=pocket_residues,
        chain_id=receptor_chain,
        out_dir=out_path,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _finalize_output(
    receptor_pdb_text: str,
    pocket_residues: List[int],
    chain_id: str,
    out_dir: Path,
) -> Step01Output:
    """Write output files and return a Step01Output dataclass."""
    out_dir.mkdir(parents=True, exist_ok=True)

    receptor_pdb_path = out_dir / "sstr2_receptor.pdb"
    receptor_pdb_path.write_text(receptor_pdb_text, encoding="utf-8")
    logger.info("[Step01] Receptor PDB written -> %s", receptor_pdb_path)

    pocket_info: Dict[str, Any] = {
        "chain_id": chain_id,
        "pocket_residues": pocket_residues,
        "n_residues": len(pocket_residues),
    }
    pocket_json_path = out_dir / "binding_pocket.json"
    pocket_json_path.write_text(
        json.dumps(pocket_info, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("[Step01] Pocket JSON written -> %s", pocket_json_path)

    return Step01Output(
        receptor_pdb_path=str(receptor_pdb_path),
        pocket_residues=pocket_residues,
        chain_id=chain_id,
        pocket_json_path=str(pocket_json_path),
    )


def _call_openfold3_local(receptor_cfg: Dict[str, Any], config: Dict[str, Any]) -> str:
    """LocalModelRunner를 통해 openfold3 구조 예측 결과 PDB 텍스트를 반환한다.

    # LOCAL MODE: replaced NIM API call
    원본 코드: requests.post("https://health.api.nvidia.com/v1/biology/openfold/openfold3", ...)
    대체: LocalModelRunner.run("openfold3", {"sequences": [...]})

    Args:
        receptor_cfg: Receptor section from pipeline_config.
        config:       Full pipeline config.

    Returns:
        PDB text string from local openfold3 model.

    Raises:
        RuntimeError: On model error or missing sequence.
    """
    sequence: Optional[str] = receptor_cfg.get("sequence")
    if not sequence:
        raise RuntimeError(
            "[Step01] 'receptor.sequence' must be set in config to use openfold3."
        )

    runner = LocalModelRunner()
    # LOCAL MODE: replaced NIM API call
    result = runner.run(
        "openfold3",
        {
            "sequences": [{"protein": {"id": "A", "sequence": sequence}}]
        },
    )

    pdb_text: Optional[str] = (
        result.get("output_pdb")
        or result.get("pdb")
        or result.get("result", {}).get("pdb")
    )

    # run_openfold3.py는 {"mmcif": ..., "confidence": ...} 형식으로 반환한다.
    # "output_pdb"/"pdb" 키가 없을 때 "mmcif" 키를 처리하여 CIF→PDB 변환.
    if not pdb_text:
        mmcif_text: Optional[str] = result.get("mmcif")
        if mmcif_text:
            logger.info(
                "[Step01] openfold3 결과에서 'mmcif' 키 감지 — CIF→PDB 변환 시도"
            )
            import os
            import tempfile
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".cif", prefix="openfold3_")
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
                    tmp_f.write(mmcif_text)
                pdb_text = _convert_cif_to_pdb(tmp_path, mmcif_text)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    if not pdb_text:
        raise RuntimeError(
            f"[Step01] openfold3 local model returned no PDB or mmCIF. "
            f"Keys: {list(result.keys())}"
        )
    return pdb_text


# ---------------------------------------------------------------------------
# CIF → PDB 변환 헬퍼
# ---------------------------------------------------------------------------


def _convert_cif_to_pdb(cif_path: str, cif_text: str) -> str:
    """CIF/mmCIF 텍스트를 PDB 형식으로 변환한다.

    RFdiffusion은 PDB 형식만 지원하므로 CIF 입력 시 반드시 변환이 필요하다.
    PyRosetta를 우선 시도하고, 실패 시 BioPython MMCIF2Dict → minimal PDB 생성.

    Args:
        cif_path: 원본 CIF 파일 경로 (PyRosetta 로드에 사용).
        cif_text: CIF 텍스트 내용 (BioPython 폴백에 사용).

    Returns:
        PDB 형식 텍스트. 변환 실패 시 원본 cif_text를 그대로 반환하고 경고 로그 출력.
    """
    # 1순위: PyRosetta
    try:
        import pyrosetta  # type: ignore
        from pyrosetta import pose_from_file  # type: ignore

        if not pyrosetta.rosetta.core.init.is_initialized():
            pyrosetta.init("-mute all", silent=True)
        pose = pose_from_file(cif_path)
        pdb_text = pyrosetta.rosetta.core.io.pose_to_pdbstring(pose)
        logger.info("[Step01] CIF → PDB 변환 성공 (PyRosetta): %d 잔기", pose.total_residue())
        return pdb_text
    except Exception as exc:
        logger.warning("[Step01] PyRosetta CIF→PDB 실패 (%s). BioPython 시도.", exc)

    # 2순위: BioPython MMCIF2Dict → ATOM 레코드 재구성
    try:
        from Bio.PDB import MMCIFParser  # type: ignore
        from Bio.PDB import PDBIO  # type: ignore
        from io import StringIO

        parser = MMCIFParser(QUIET=True)
        structure = parser.get_structure("receptor", StringIO(cif_text))
        buf = StringIO()
        io_obj = PDBIO()
        io_obj.set_structure(structure)
        io_obj.save(buf)
        pdb_out = buf.getvalue()
        if pdb_out.strip():
            logger.info("[Step01] CIF → PDB 변환 성공 (BioPython MMCIF parser).")
            return pdb_out
    except Exception as exc:
        logger.warning("[Step01] BioPython CIF→PDB 실패 (%s). 원본 텍스트 사용 (RFdiffusion이 실패할 수 있음).", exc)

    return cif_text


# ---------------------------------------------------------------------------
# numpy shims (avoid hard dependency for pure I/O paths)
# ---------------------------------------------------------------------------


def _np_array(lst: Any) -> Any:
    try:
        import numpy as np
        return np.array(lst, dtype=float)
    except ImportError:
        return lst


def _cdist_min(a: Any, b: Any) -> float:
    try:
        import numpy as np
        diffs = np.array(b) - np.array(a)
        return float(np.linalg.norm(diffs, axis=1).min())
    except Exception:
        return 0.0


def _np_norm(arr: Any) -> float:
    try:
        import numpy as np
        return float(np.linalg.norm(arr))
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# CLI / standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Step01: Receptor preparation standalone test")
    parser.add_argument("--data-dir", default="data", help="Directory with pre-existing PDB")
    parser.add_argument("--output-dir", default="runs/test_run/01_receptor")
    args = parser.parse_args()

    dummy_cfg: Dict[str, Any] = {
        "run_id": "test_run",
        "output_base_dir": "runs",
        "data_dir": args.data_dir,
        "receptor": {
            "chain": "B",
            "pocket_residues": [119, 122, 127, 184, 197, 205, 272, 294],
        },
    }
    try:
        result = prepare_receptor(dummy_cfg)
        print(f"Step01 result: {result}")
    except FileNotFoundError as e:
        print(f"[WARN] {e}")
        print("Place a SSTR2 PDB file in the data/ directory to test fallback loading.")
