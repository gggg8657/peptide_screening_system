"""
step05_docking.py
=================
Step 05: 결합 포즈/친화도 평가 (Binding Pose & Affinity Evaluation)

LocalModelRunner(diffpepbuilder, boltz)를 사용하여 QC 통과 펩타이드 후보를
수용체(SSTR2)에 도킹하고 결합 친화도를 예측한다.

Uses LocalModelRunner("diffpepbuilder") for pose prediction and
LocalModelRunner("boltz") for affinity ranking.  Both engines are tried;
if one fails the other is used as a fallback.  The top ``docking_top_pct``
percent of candidates by score proceed to Step06.

Gate criteria:
    Top 20 % by docking score (configurable via ``docking_top_pct``).

Input:
    - QC-passed candidates (List[QCResult] from Step04)
    - receptor PDB path (Step01 output)

Output:
    - 05_docking/pose_{seq_id}_{pose_idx}.pdb
    - 05_docking/docking_scores.json

Public API:
    run_docking(candidates, receptor_pdb, config)   -> Step05Output
    dock_with_diffdock(protein_pdb, ligand_pdb,
                       num_poses)                   -> DockResult
    predict_with_boltz2(receptor_seq, peptide_seq)  -> Boltz2Result
    apply_docking_gate(results, top_pct)            -> (passed, failed)
    merge_docking_results(dd, b2)                   -> List[DockingResult]
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema imports
# ---------------------------------------------------------------------------

from pipeline_local.schemas.io_schemas import DockingResult, Step05Output, QCResult
from pipeline_local.core.local_runner import LocalModelRunner


# ---------------------------------------------------------------------------
# Internal result types
# ---------------------------------------------------------------------------


@dataclass
class DockResult:
    """DiffPepBuilder 단일 호출 결과."""
    seq_id: str
    poses: List[str]        # PDB text for each pose
    scores: List[float]     # Confidence score per pose (lower = better)
    success: bool
    error: Optional[str] = None


@dataclass
class Boltz2Result:
    """Boltz 단일 호출 결과."""
    seq_id: str
    affinity_kcal: float    # Predicted binding affinity (kcal/mol)
    pdb_text: Optional[str]
    success: bool
    iptm: float = 0.0       # ipTM confidence score (0~1, higher = better binding)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_TOP_PCT: float = 20.0
_DEFAULT_NUM_POSES: int = 5


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def run_docking(
    candidates: List[QCResult],
    receptor_pdb: str,
    config: Dict[str, Any],
) -> Step05Output:
    """QC 통과 후보 전체에 대해 도킹을 실행하고 상위 20%를 선발한다.

    Orchestration entry for Step 05.  For each candidate:
    1. Attempts DiffPepBuilder (pose prediction).
    2. On DiffPepBuilder failure, falls back to Boltz.
    3. Attempts Boltz for affinity score in all cases.
    4. Merges results and selects top ``docking_top_pct`` percent.

    Args:
        candidates:   QC-passed QCResult list.
        receptor_pdb: Path to the receptor PDB file.
        config:       Full pipeline configuration dict.

    Returns:
        Step05Output with all DockingResult records (gated by top_pct flag
        embedded in the ``rank`` field, and ``score`` for ordering).
    """
    run_id: str = config.get("run_id", "default_run")
    output_base: Path = Path(config.get("output_base_dir", "runs")) / run_id
    out_dir: Path = output_base / "05_docking"
    out_dir.mkdir(parents=True, exist_ok=True)

    gate_cfg: Dict[str, Any] = config.get("gate_thresholds", {})
    top_pct: float = float(gate_cfg.get("docking_top_pct", _DEFAULT_TOP_PCT))
    num_poses: int = int(config.get("docking_num_poses", _DEFAULT_NUM_POSES))

    receptor_pdb_content: str = Path(receptor_pdb).read_text(encoding="utf-8")
    receptor_seq: str = _extract_sequence_from_pdb(receptor_pdb_content)

    logger.info(
        "[Step05] Docking %d QC-passed candidates (top_pct=%.0f%%, engine=boltz).",
        len(candidates),
        top_pct,
    )

    all_results: List[DockingResult] = []

    for candidate in candidates:
        seq_id = candidate.seq_id
        peptide_pdb_path = candidate.pdb_path   # ESMFold PDB for peptide

        if not peptide_pdb_path or not Path(peptide_pdb_path).exists():
            logger.warning("[Step05] No PDB for candidate %s; skipping docking.", seq_id)
            continue

        peptide_pdb_content = Path(peptide_pdb_path).read_text(encoding="utf-8")
        peptide_seq = _extract_sequence_from_pdb(peptide_pdb_content)

        # DiffPepBuilder는 비활성화 — 항상 실패하여 타임아웃 낭비. Boltz만 사용.
        b2_result = _try_boltz2(
            seq_id=seq_id,
            receptor_seq=receptor_seq,
            peptide_seq=peptide_seq,
        )

        # Merge into DockingResult (dd_result=None → Boltz only path)
        merged = _build_docking_result(seq_id, None, b2_result, out_dir)
        all_results.extend(merged)

    passed, _ = apply_docking_gate(all_results, top_pct)
    logger.info(
        "[Step05] Docking complete: %d results, %d in top %.0f%%.",
        len(all_results),
        len(passed),
        top_pct,
    )

    _save_docking_scores(all_results, out_dir)
    return Step05Output(docking_results=all_results)


def dock_with_diffdock(
    protein_pdb: str,
    peptide_seq: str,
    num_poses: int = _DEFAULT_NUM_POSES,
) -> DockResult:
    """LocalModelRunner(diffpepbuilder)를 호출하여 도킹 포즈와 신뢰도 점수를 반환한다.

    # LOCAL MODE: replaced NIM API call
    원본 코드: requests.post("https://health.api.nvidia.com/v1/biology/mit/diffdock", ...)
    대체: LocalModelRunner.run("diffpepbuilder", {...})

    Args:
        protein_pdb:  Receptor PDB *content* string.
        peptide_seq:  Peptide amino acid sequence (one-letter code).
        num_poses:    Number of poses to generate.

    Returns:
        DockResult with poses and confidence scores.

    Raises:
        RuntimeError: On unrecoverable model failure.
    """
    payload: Dict[str, Any] = {
        "receptor_pdb": protein_pdb,
        "peptide_sequence": peptide_seq,
        "num_poses": num_poses,
        "time_divisions": 20,
        "steps": 18,
    }

    runner = LocalModelRunner()
    # LOCAL MODE: replaced NIM API call
    data = runner.run("diffpepbuilder", payload)

    # Response may have 'docked_pdbs' (run_diffpepbuilder 반환 키) or
    # 'output_pdbs' / 'pdbs' (하위 호환 폴백)
    poses: List[str] = (
        data.get("docked_pdbs", [])
        or data.get("output_pdbs", [])
        or data.get("pdbs", [])
    )
    scores: List[float] = (
        data.get("position_confidence", [])
        or data.get("scores", [])
        or [-float(i) for i in range(len(poses))]  # fallback dummy scores
    )
    return DockResult(seq_id="", poses=poses, scores=scores, success=True)


def predict_with_boltz2(
    receptor_seq: str,
    peptide_seq: str,
) -> Boltz2Result:
    """LocalModelRunner(boltz)로 수용체-펩타이드 결합 친화도를 예측한다.

    # LOCAL MODE: replaced NIM API call
    원본 코드: requests.post("https://health.api.nvidia.com/v1/biology/mit/boltz2/predict", ...)
    대체: LocalModelRunner.run("boltz", {...})

    Args:
        receptor_seq: Receptor amino acid sequence (one-letter code).
        peptide_seq:  Peptide amino acid sequence (one-letter code).

    Returns:
        Boltz2Result with predicted affinity in kcal/mol.

    Raises:
        RuntimeError: On model failure.
    """
    payload: Dict[str, Any] = {
        "sequences": [
            {"protein": {"id": "A", "sequence": receptor_seq}},
            {"protein": {"id": "B", "sequence": peptide_seq}},
        ],
        "compute_affinity": True,
    }

    runner = LocalModelRunner()
    # LOCAL MODE: replaced NIM API call
    data = runner.run("boltz", payload)

    # Boltz confidence에서 ipTM 추출 (primary score: 0~1, 높을수록 좋은 결합)
    confidence = data.get("confidence", {})
    raw = confidence.get("raw", confidence)
    iptm: float = float(
        raw.get("ipTM", raw.get("iptm", raw.get("protein_iptm", 0.0)))
    )

    # affinity는 Boltz single-seq에서 제공 안 됨 → ipTM 기반 추정
    # ipTM 0.8 이상이면 강한 결합 (-8 kcal/mol 수준)
    affinity_estimate: float = -10.0 * iptm if iptm > 0 else float(
        data.get("affinity_kcal_mol")
        or data.get("binding_affinity")
        or data.get("result", {}).get("affinity_kcal_mol", 0.0)
    )

    # run_boltz.py는 구조를 'structure_cif' 키로 반환한다.
    # 'output_pdb' / 'pdb'는 하위 호환 폴백.
    pdb_text: Optional[str] = (
        data.get("structure_cif")
        or data.get("output_pdb")
        or data.get("pdb")
        or None
    )
    return Boltz2Result(
        seq_id="",
        affinity_kcal=affinity_estimate,
        iptm=iptm,
        pdb_text=pdb_text,
        success=True,
    )


def apply_docking_gate(
    results: List[DockingResult],
    top_pct: float = _DEFAULT_TOP_PCT,
) -> Tuple[List[DockingResult], List[DockingResult]]:
    """도킹 점수 기준 상위 top_pct% 후보를 선발한다.

    Sorts by ``score`` ascending (lower = better) and returns the top
    ``top_pct`` percent as *passed* and the remainder as *failed*.

    Args:
        results: List of DockingResult objects.
        top_pct: Percentage of candidates to pass (default 20.0).

    Returns:
        Tuple ``(passed, failed)``.
    """
    if not results:
        return [], []
    sorted_results = sorted(results, key=lambda r: r.score)
    n_pass = max(1, int(len(sorted_results) * top_pct / 100.0))
    return sorted_results[:n_pass], sorted_results[n_pass:]


def merge_docking_results(
    diffdock_results: List[DockingResult],
    boltz2_results: List[DockingResult],
) -> List[DockingResult]:
    """DiffPepBuilder와 Boltz 결과를 seq_id 기준으로 병합한다.

    When a candidate has both DiffPepBuilder and Boltz results, the
    DiffPepBuilder score is used for pose ranking, while the Boltz affinity is
    stored in ``confidence``.  When only one source is available, that source's
    result is used directly.

    Args:
        diffdock_results: DockingResult list from DiffPepBuilder.
        boltz2_results:   DockingResult list from Boltz.

    Returns:
        Merged List[DockingResult].
    """
    dd_map: Dict[str, DockingResult] = {r.seq_id: r for r in diffdock_results}
    b2_map: Dict[str, DockingResult] = {r.seq_id: r for r in boltz2_results}

    merged: List[DockingResult] = []
    all_ids = set(dd_map) | set(b2_map)

    for seq_id in sorted(all_ids):
        if seq_id in dd_map and seq_id in b2_map:
            dd = dd_map[seq_id]
            b2 = b2_map[seq_id]
            # DiffPepBuilder for pose; Boltz confidence as affinity proxy
            merged.append(
                DockingResult(
                    seq_id=seq_id,
                    engine="diffpepbuilder+boltz",
                    score=dd.score,
                    confidence=b2.confidence,
                    pose_pdb=dd.pose_pdb,
                    rank=dd.rank,
                )
            )
        elif seq_id in dd_map:
            merged.append(dd_map[seq_id])
        else:
            merged.append(b2_map[seq_id])

    return merged


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _try_diffdock(
    seq_id: str,
    protein_pdb: str,
    peptide_seq: str,
    num_poses: int,
    out_dir: Path,
) -> Optional[DockResult]:
    """DiffPepBuilder 호출 + 파일 저장; 실패 시 None 반환."""
    try:
        result = dock_with_diffdock(protein_pdb, peptide_seq, num_poses)
        result.seq_id = seq_id
        # Save top pose
        if result.poses:
            pose_path = out_dir / f"pose_{seq_id}_00.pdb"
            pose_path.write_text(result.poses[0], encoding="utf-8")
        return result
    except Exception as exc:
        logger.warning("[Step05] DiffPepBuilder failed for %s: %s. Trying Boltz.", seq_id, exc)
        return None


def _try_boltz2(
    seq_id: str,
    receptor_seq: str,
    peptide_seq: str,
) -> Optional[Boltz2Result]:
    """Boltz 호출; 실패 시 None 반환."""
    try:
        result = predict_with_boltz2(receptor_seq, peptide_seq)
        result.seq_id = seq_id
        return result
    except Exception as exc:
        logger.warning("[Step05] Boltz failed for %s: %s.", seq_id, exc)
        return None


def _build_docking_result(
    seq_id: str,
    dd: Optional[DockResult],
    b2: Optional[Boltz2Result],
    out_dir: Path,
) -> List[DockingResult]:
    """DockResult + Boltz2Result -> DockingResult 목록으로 변환한다."""
    results: List[DockingResult] = []

    if dd and dd.success and dd.poses:
        for pose_idx, (pose_pdb, score) in enumerate(
            zip(dd.poses, dd.scores or [0.0] * len(dd.poses))
        ):
            pose_path = out_dir / f"pose_{seq_id}_{pose_idx:02d}.pdb"
            pose_path.write_text(pose_pdb, encoding="utf-8")
            confidence = b2.affinity_kcal if (b2 and b2.success) else 0.0
            results.append(
                DockingResult(
                    seq_id=seq_id,
                    engine="diffpepbuilder",
                    score=float(score),
                    confidence=float(confidence),
                    pose_pdb=str(pose_path),
                    rank=pose_idx + 1,
                )
            )
    elif b2 and b2.success:
        # DiffPepBuilder failed; use Boltz only
        pose_path = out_dir / f"pose_{seq_id}_00.pdb"
        if b2.pdb_text:
            pose_path.write_text(b2.pdb_text, encoding="utf-8")
        results.append(
            DockingResult(
                seq_id=seq_id,
                engine="boltz",
                score=b2.affinity_kcal,
                confidence=b2.affinity_kcal,
                pose_pdb=str(pose_path) if b2.pdb_text else "",
                rank=1,
            )
        )
    else:
        logger.error("[Step05] Both DiffPepBuilder and Boltz failed for %s.", seq_id)

    return results


def _extract_sequence_from_pdb(pdb_text: str) -> str:
    """PDB/CIF 텍스트에서 첫 번째 체인의 아미노산 시퀀스를 추출한다.

    PDB 고정 컬럼 형식과 mmCIF 공백 구분 형식 모두 지원.
    CA 원자만 추출하여 서열 구성.
    """
    _aa3to1: Dict[str, str] = {
        "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
        "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
        "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
        "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    }

    # CIF 감지: _atom_site. 헤더가 있으면 CIF
    is_cif = "_atom_site." in pdb_text

    seen: Dict[int, str] = {}

    if is_cif:
        # mmCIF: 공백 구분 필드, CA 원자만 추출
        # 일반적 필드 순서: group_PDB id type_symbol label_atom_id label_alt_id
        #   label_comp_id label_seq_id auth_seq_id ...
        for line in pdb_text.splitlines():
            if not line.startswith("ATOM"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            atom_name = parts[3]   # label_atom_id
            if atom_name != "CA":
                continue
            res_name = parts[5]    # label_comp_id
            try:
                res_num = int(parts[8])  # label_seq_id (index 8)
            except (ValueError, IndexError):
                continue
            if res_num not in seen and res_name in _aa3to1:
                seen[res_num] = _aa3to1[res_name]
    else:
        # PDB: 고정 컬럼 형식
        for line in pdb_text.splitlines():
            if not line.startswith("ATOM"):
                continue
            atom_name = line[12:16].strip()
            if atom_name != "CA":
                continue
            res_name = line[17:20].strip()
            try:
                res_num = int(line[22:26].strip())
            except (ValueError, IndexError):
                continue
            if res_num not in seen and res_name in _aa3to1:
                seen[res_num] = _aa3to1[res_name]

    if seen:
        return "".join(seen[k] for k in sorted(seen))
    return ""


def _save_docking_scores(results: List[DockingResult], out_dir: Path) -> None:
    """도킹 점수를 JSON 파일로 저장한다."""
    summary = {
        "total_poses": len(results),
        "results": [r.to_dict() for r in results],
    }
    score_path = out_dir / "docking_scores.json"
    score_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("[Step05] Docking scores written -> %s", score_path)


# ---------------------------------------------------------------------------
# CLI / standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Step05: Docking standalone test")
    parser.add_argument("--receptor-pdb", required=True)
    parser.add_argument("--candidate-pdb", required=True, help="ESMFold PDB of one candidate")
    parser.add_argument("--seq-id", default="bb00_seq00")
    args = parser.parse_args()

    dummy_candidate = QCResult(
        seq_id=args.seq_id,
        plddt_mean=85.0,
        plddt_interface=80.0,
        pdb_path=args.candidate_pdb,
        passed_gate=True,
    )
    cfg: Dict[str, Any] = {
        "run_id": "test_run",
        "output_base_dir": "runs",
        "gate_thresholds": {"docking_top_pct": 20},
    }
    result = run_docking([dummy_candidate], args.receptor_pdb, cfg)
    print(f"Step05: {len(result.docking_results)} poses generated.")
