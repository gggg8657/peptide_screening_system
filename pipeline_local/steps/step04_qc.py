"""
step04_qc.py
============
Step 04: 빠른 구조 QC (Fast Structure Quality Control via ESMFold)

LocalModelRunner(esmfold)를 사용하여 Step03에서 설계된 펩타이드 서열의
구조를 빠르게 예측하고 pLDDT 기반 품질 관리(QC) 게이트를 적용한다.

Uses LocalModelRunner("esmfold") for local structure prediction of sequences
from Step03 and applies pLDDT-based QC gates.  Candidates failing either the
mean pLDDT or interface pLDDT threshold are rejected.

Gate criteria (from gate_thresholds.yaml):
    mean pLDDT    >= 75   (esmfold_plddt_min)
    interface pLDDT >= 70  (esmfold_interface_plddt_min)

Input:
    - sequences: List[SequenceEntry] from Step03
    - pocket_residues: interface residue numbers for interface pLDDT

Output:
    - 04_qc/esmfold_{seq_id}.pdb    (one per sequence)
    - 04_qc/qc_summary.json

Public API:
    run_qc(sequences, config)                              -> Step04Output
    predict_and_evaluate(sequence, seq_id)                 -> QCResult
    apply_plddt_gate(results, plddt_threshold,
                     interface_threshold)                  -> (passed, failed)
    compute_interface_plddt(pdb_text, interface_residues)  -> float
    save_qc_results(results, output_dir)                   -> paths
"""

from __future__ import annotations

import json
import logging
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema imports
# ---------------------------------------------------------------------------

from pipeline_local.schemas.io_schemas import QCResult, Step04Output, SequenceEntry
from pipeline_local.core.local_runner import LocalModelRunner


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_PLDDT_MIN: float = 75.0
_DEFAULT_INTERFACE_PLDDT_MIN: float = 70.0


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def run_qc(
    sequences: List[SequenceEntry],
    config: Dict[str, Any],
) -> Step04Output:
    """모든 서열에 대해 ESMFold 구조 예측 + pLDDT QC 게이트를 실행한다.

    Orchestration entry for Step 04.

    Args:
        sequences: All SequenceEntry items from Step03Output.sequences.
        config:    Full pipeline configuration dict.

    Returns:
        Step04Output with QCResult for every evaluated sequence.
    """
    run_id: str = config.get("run_id", "default_run")
    output_base: Path = Path(config.get("output_base_dir", "runs")) / run_id
    out_dir: Path = output_base / "04_qc"
    out_dir.mkdir(parents=True, exist_ok=True)

    gate_cfg: Dict[str, Any] = config.get("gate_thresholds", {})
    plddt_min: float = float(gate_cfg.get("esmfold_plddt_min", _DEFAULT_PLDDT_MIN))
    interface_min: float = float(
        gate_cfg.get("esmfold_interface_plddt_min", _DEFAULT_INTERFACE_PLDDT_MIN)
    )
    pocket_residues: List[int] = config.get("receptor", {}).get("pocket_residues", [])

    # Disulfide bond gate configuration
    gates_enabled: Dict[str, bool] = gate_cfg.get("gates_enabled", {})
    disulfide_gate_enabled: bool = gates_enabled.get("disulfide", True)
    disulfide_max_dist: float = float(gate_cfg.get("disulfide_bond_max_distance", 2.5))
    disulfide_cys_pos: List[int] = gate_cfg.get("disulfide_cys_positions", [])

    logger.info(
        "[Step04] Running ESMFold QC on %d sequences (pLDDT>=%s, iface>=%s).",
        len(sequences),
        plddt_min,
        interface_min,
    )

    # ── 배치 모드: 모델 1회 로드 → N개 서열 연속 예측 ─────────────────────
    batch_payload = {
        "sequences": [
            {"seq_id": e.seq_id, "sequence": e.sequence} for e in sequences
        ]
    }
    # 배치 전체 타임아웃: 서열당 최대 30초 + 모델 로드 120초
    batch_timeout = max(600, len(sequences) * 30 + 120)
    runner = LocalModelRunner()
    try:
        batch_result = runner.run("esmfold", batch_payload, timeout=batch_timeout)
        raw_results: List[Dict[str, Any]] = batch_result.get("results", [])
    except Exception as exc:
        logger.error("[Step04] ESMFold batch 호출 실패: %s. 개별 예측으로 폴백.", exc)
        raw_results = []

    # seq_id → 배치 결과 맵
    batch_map: Dict[str, Dict[str, Any]] = {r["seq_id"]: r for r in raw_results}

    qc_results: List[QCResult] = []

    # ── 배치 결과가 없으면 개별 예측으로 폴백 ─────────────────────────────
    if not batch_map:
        logger.warning("[Step04] 배치 결과 없음 — 개별 predict_and_evaluate 폴백.")
        for entry in sequences:
            logger.info("[Step04] ESMFold predict (fallback): %s", entry.seq_id)
            try:
                result = predict_and_evaluate(
                    sequence=entry.sequence,
                    seq_id=entry.seq_id,
                    out_dir=out_dir,
                    pocket_residues=pocket_residues,
                    plddt_min=plddt_min,
                    interface_min=interface_min,
                    disulfide_cys_positions=disulfide_cys_pos if disulfide_cys_pos else None,
                    disulfide_max_distance=disulfide_max_dist,
                    disulfide_gate_enabled=disulfide_gate_enabled,
                )
                qc_results.append(result)
            except Exception as exc2:
                logger.error("[Step04] ESMFold failed for %s: %s", entry.seq_id, exc2)
                qc_results.append(
                    QCResult(
                        seq_id=entry.seq_id,
                        plddt_mean=0.0,
                        plddt_interface=0.0,
                        pdb_path="",
                        passed_gate=False,
                    )
                )
    else:
        # ── 배치 결과 후처리 ─────────────────────────────────────────────
        for entry in sequences:
            res = batch_map.get(entry.seq_id)
            if res is None or res.get("error") or not res.get("pdb"):
                logger.error(
                    "[Step04] 배치에서 %s 결과 없음 또는 오류: %s",
                    entry.seq_id, res,
                )
                qc_results.append(
                    QCResult(
                        seq_id=entry.seq_id,
                        plddt_mean=0.0,
                        plddt_interface=0.0,
                        pdb_path="",
                        passed_gate=False,
                    )
                )
                continue

            pdb_text: str = res["pdb"]
            plddt_mean: float = float(res.get("mean_plddt", 0.0))

            # PDB 저장
            pdb_file = out_dir / f"esmfold_{entry.seq_id}.pdb"
            try:
                pdb_file.write_text(pdb_text, encoding="utf-8")
            except OSError as exc2:
                logger.warning("[Step04] PDB 저장 실패 %s: %s", entry.seq_id, exc2)

            plddt_iface = (
                compute_interface_plddt(pdb_text, pocket_residues)
                if pocket_residues
                else plddt_mean
            )
            passed = bool(plddt_mean >= plddt_min and plddt_iface >= interface_min)

            # 이황화 결합 게이트
            disulfide_intact: Optional[bool] = None
            disulfide_distance: Optional[float] = None
            if disulfide_cys_pos and disulfide_gate_enabled:
                disulfide_intact, disulfide_distance = check_disulfide_bond(
                    pdb_text, disulfide_cys_pos, disulfide_max_dist,
                )
                if disulfide_intact is False:
                    passed = False
                    logger.info(
                        "[Step04] %s: FAILED disulfide gate (distance=%.2f A > %.1f A)",
                        entry.seq_id, disulfide_distance or 0.0, disulfide_max_dist,
                    )

            logger.info(
                "[Step04] %s: pLDDT=%.1f, iface_pLDDT=%.1f -> %s",
                entry.seq_id, plddt_mean, plddt_iface,
                "PASS" if passed else "FAIL",
            )
            qc_results.append(
                QCResult(
                    seq_id=entry.seq_id,
                    plddt_mean=round(plddt_mean, 2),
                    plddt_interface=round(plddt_iface, 2),
                    pdb_path=str(pdb_file),
                    passed_gate=passed,
                    disulfide_intact=disulfide_intact,
                    disulfide_distance=disulfide_distance,
                )
            )

    passed, failed = apply_plddt_gate(qc_results, plddt_min, interface_min)
    logger.info(
        "[Step04] QC gate: %d passed / %d failed.",
        len(passed),
        len(failed),
    )

    save_qc_results(qc_results, out_dir)
    return Step04Output(qc_results=qc_results)


def predict_and_evaluate(
    sequence: str,
    seq_id: str,
    out_dir: Optional[Path] = None,
    pocket_residues: Optional[List[int]] = None,
    plddt_min: float = _DEFAULT_PLDDT_MIN,
    interface_min: float = _DEFAULT_INTERFACE_PLDDT_MIN,
    disulfide_cys_positions: Optional[List[int]] = None,
    disulfide_max_distance: float = 2.5,
    disulfide_gate_enabled: bool = True,
) -> QCResult:
    """단일 서열에 대해 ESMFold 예측을 수행하고 QCResult를 반환한다.

    # LOCAL MODE: replaced NIM API call
    원본 코드: requests.post("https://health.api.nvidia.com/v1/biology/nvidia/esmfold", ...)
    대체: LocalModelRunner.run("esmfold", {"sequence": sequence})

    Args:
        sequence:         Amino acid sequence (one-letter code).
        seq_id:           Unique sequence identifier for file naming.
        out_dir:          Directory to write the predicted PDB.
        pocket_residues:  Residue numbers defining the binding interface.
        plddt_min:        Mean pLDDT threshold.
        interface_min:    Interface pLDDT threshold.

    Returns:
        QCResult with pLDDT scores and gate decision.
    """
    payload = {"sequence": sequence}

    runner = LocalModelRunner()
    # LOCAL MODE: replaced NIM API call
    data = runner.run("esmfold", payload)

    # run_esmfold.py 단일 모드 반환 키: {"pdb": ..., "mean_plddt": ...}
    # 'pdbs' 키는 wrapper가 반환하지 않음 — 'pdb'를 1순위로 읽는다.
    pdb_text: str = (
        data.get("pdb", "")
        or data.get("output_pdb", "")
        or data.get("result", {}).get("pdb", "")
    )
    if not pdb_text:
        raise RuntimeError(
            f"[Step04] ESMFold local model returned no PDB. Keys: {list(data.keys())}"
        )

    # Parse pLDDT from B-factor column BEFORE disulfide formation
    # (PyRosetta dump_pdb overwrites ESMFold pLDDT B-factors)
    plddt_mean = _extract_mean_plddt(pdb_text)

    # PyRosetta disulfide formation: ESMFold predicts linear structure,
    # so attempt to form Cys-Cys disulfide bond before gate evaluation.
    if disulfide_cys_positions:
        pdb_text = _try_form_disulfide(pdb_text, disulfide_cys_positions)

    # Save PDB
    pdb_path = ""
    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        pdb_file = out_dir / f"esmfold_{seq_id}.pdb"
        pdb_file.write_text(pdb_text, encoding="utf-8")
        pdb_path = str(pdb_file)
    plddt_iface = (
        compute_interface_plddt(pdb_text, pocket_residues or [])
        if pocket_residues
        else plddt_mean
    )

    passed = bool(plddt_mean >= plddt_min and plddt_iface >= interface_min)
    logger.info(
        "[Step04] %s: pLDDT=%.1f, iface_pLDDT=%.1f -> %s",
        seq_id,
        plddt_mean,
        plddt_iface,
        "PASS" if passed else "FAIL",
    )

    # Disulfide bond distance check
    disulfide_intact: Optional[bool] = None
    disulfide_distance: Optional[float] = None
    if disulfide_cys_positions and disulfide_gate_enabled:
        disulfide_intact, disulfide_distance = check_disulfide_bond(
            pdb_text, disulfide_cys_positions, disulfide_max_distance,
        )
        if disulfide_intact is False:
            passed = False
            logger.info(
                "[Step04] %s: FAILED disulfide gate (distance=%.2f A > %.1f A)",
                seq_id, disulfide_distance or 0.0, disulfide_max_distance,
            )

    return QCResult(
        seq_id=seq_id,
        plddt_mean=round(plddt_mean, 2),
        plddt_interface=round(plddt_iface, 2),
        pdb_path=pdb_path,
        passed_gate=passed,
        disulfide_intact=disulfide_intact,
        disulfide_distance=disulfide_distance,
    )


def apply_plddt_gate(
    results: List[QCResult],
    plddt_threshold: float = _DEFAULT_PLDDT_MIN,
    interface_threshold: float = _DEFAULT_INTERFACE_PLDDT_MIN,
) -> Tuple[List[QCResult], List[QCResult]]:
    """pLDDT 임계값 기반 게이트를 적용하여 통과/실패 목록을 반환한다.

    A candidate passes if BOTH of the following hold:
        ``plddt_mean >= plddt_threshold``  AND
        ``plddt_interface >= interface_threshold``

    Args:
        results:             List of QCResult objects to evaluate.
        plddt_threshold:     Mean pLDDT minimum (default 75).
        interface_threshold: Interface pLDDT minimum (default 70).

    Returns:
        Tuple ``(passed, failed)`` where each element is a List[QCResult].
    """
    passed: List[QCResult] = []
    failed: List[QCResult] = []
    for r in results:
        plddt_ok = r.plddt_mean >= plddt_threshold and r.plddt_interface >= interface_threshold
        # passed_gate includes disulfide bond check from predict_and_evaluate()
        gate_ok = getattr(r, "passed_gate", True)
        if plddt_ok and gate_ok:
            passed.append(r)
        else:
            failed.append(r)
    return passed, failed


def compute_interface_plddt(
    pdb_text: str,
    interface_residues: List[int],
) -> float:
    """PDB B-factor 컬럼에서 계면 잔기의 평균 pLDDT를 계산한다.

    ESMFold writes per-residue pLDDT into the B-factor (tempFactor) column.
    This function extracts those values for the specified *interface_residues*
    and returns their mean.

    Args:
        pdb_text:            Full PDB text from ESMFold.
        interface_residues:  List of residue sequence numbers to include.

    Returns:
        Mean pLDDT of interface residues, or overall mean if no match found.
    """
    if not interface_residues:
        return _extract_mean_plddt(pdb_text)

    res_set = set(interface_residues)
    values: List[float] = []

    for line in pdb_text.splitlines():
        if not line.startswith("ATOM"):
            continue
        try:
            res_num = int(line[22:26].strip())
            b_factor = float(line[60:66].strip())
        except (ValueError, IndexError):
            continue
        if res_num in res_set:
            values.append(b_factor)

    if not values:
        logger.debug(
            "[Step04] compute_interface_plddt: no matching residues found for %s; "
            "returning overall pLDDT.",
            interface_residues[:5],
        )
        return _extract_mean_plddt(pdb_text)

    return sum(values) / len(values)


def check_disulfide_bond(
    pdb_text: str,
    cys_positions: List[int],
    max_distance: float = 2.5,
) -> Tuple[bool, Optional[float]]:
    """PDB에서 시스테인 SG 원자 간 거리를 측정하여 이황화 결합 유지 여부를 확인한다.

    Checks whether the sulfur-sulfur (SG-SG) distance between two cysteine
    residues is within covalent bond range.  A typical S-S bond is ~2.05 A;
    distances exceeding *max_distance* indicate a broken disulfide.

    Args:
        pdb_text:       Full PDB text (e.g. from ESMFold).
        cys_positions:  Two residue sequence numbers (1-indexed) to check.
                        e.g. [3, 13] for Cys3-Cys13.
        max_distance:   Maximum SG-SG distance in Angstroms (default 2.5).

    Returns:
        Tuple of (intact: bool, distance: float or None).
        ``intact`` is True when distance <= max_distance.
        ``distance`` is None when SG atoms could not be found.
    """
    if len(cys_positions) != 2:
        logger.warning("[Step04] check_disulfide_bond: expected 2 positions, got %d", len(cys_positions))
        return True, None  # Cannot check, assume intact

    pos_a, pos_b = cys_positions[0], cys_positions[1]
    sg_coords: Dict[int, Tuple[float, float, float]] = {}

    for line in pdb_text.splitlines():
        if not line.startswith("ATOM"):
            continue
        atom_name = line[12:16].strip()
        if atom_name != "SG":
            continue
        try:
            res_num = int(line[22:26].strip())
        except (ValueError, IndexError):
            continue
        if res_num in (pos_a, pos_b):
            try:
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                sg_coords[res_num] = (x, y, z)
            except (ValueError, IndexError):
                continue

    if pos_a not in sg_coords or pos_b not in sg_coords:
        logger.warning(
            "[Step04] check_disulfide_bond: SG atoms not found for positions %d, %d. "
            "Found SG at: %s. Marking as BROKEN (Cys may be mutated).",
            pos_a, pos_b, list(sg_coords.keys()),
        )
        return False, None  # Cannot measure -> assume broken (Cys likely mutated)

    xa, ya, za = sg_coords[pos_a]
    xb, yb, zb = sg_coords[pos_b]
    distance = math.sqrt((xa - xb) ** 2 + (ya - yb) ** 2 + (za - zb) ** 2)
    intact = distance <= max_distance

    logger.info(
        "[Step04] Disulfide check Cys%d-Cys%d: SG-SG distance=%.2f A -> %s (max=%.1f)",
        pos_a, pos_b, distance, "INTACT" if intact else "BROKEN", max_distance,
    )
    return intact, round(distance, 3)


def save_qc_results(results: List[QCResult], output_dir: Path) -> Dict[str, str]:
    """QC 결과를 qc_summary.json 파일로 저장하고 경로 딕셔너리를 반환한다.

    Args:
        results:    List of QCResult objects.
        output_dir: Directory to write qc_summary.json.

    Returns:
        Dict mapping ``"qc_summary"`` to the written JSON path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r.passed_gate),
        "failed": sum(1 for r in results if not r.passed_gate),
        "results": [r.to_dict() for r in results],
    }
    summary_path = output_dir / "qc_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("[Step04] QC summary written -> %s", summary_path)
    return {"qc_summary": str(summary_path)}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _try_form_disulfide(pdb_text: str, cys_positions: List[int]) -> str:
    """PyRosetta로 이황화결합 형성 시도. 실패 시 원본 pdb_text 반환.

    ESMFold는 선형 구조로 예측하므로 Cys 간 SG-SG 거리가 크게 벌어짐.
    PyRosetta form_disulfide + chi minimization으로 결합을 형성한 뒤
    PDB 텍스트를 반환한다.

    Args:
        pdb_text:       ESMFold로 예측한 원본 PDB 텍스트.
        cys_positions:  이황화결합을 형성할 Cys 잔기 번호 쌍 (1-indexed).
                        e.g. [3, 14]

    Returns:
        이황화결합이 형성된 PDB 텍스트. 실패 시 원본 반환.
    """
    if len(cys_positions) < 2:
        return pdb_text

    try:
        import pyrosetta  # type: ignore
        import pyrosetta.rosetta.core.conformation as conformation  # type: ignore
        from pyrosetta.rosetta.protocols.minimization_packing import MinMover  # type: ignore

        pyrosetta.init("-mute all")

        # Write pdb_text to temp file (pose_from_pdbstring availability varies)
        tmp_in = tempfile.NamedTemporaryFile(
            mode="w", suffix=".pdb", delete=False, encoding="utf-8"
        )
        tmp_in.write(pdb_text)
        tmp_in.close()

        pose = pyrosetta.pose_from_pdb(tmp_in.name)
        os.unlink(tmp_in.name)

        res_i, res_j = cys_positions[0], cys_positions[1]
        n_res = pose.total_residue()

        if res_i > n_res or res_j > n_res:
            logger.warning(
                "[Step04] _try_form_disulfide: positions %d/%d out of range (n_res=%d)",
                res_i, res_j, n_res,
            )
            return pdb_text

        name3_i = pose.residue(res_i).name3()
        name3_j = pose.residue(res_j).name3()
        if name3_i not in ("CYS", "CYD") or name3_j not in ("CYS", "CYD"):
            logger.warning(
                "[Step04] _try_form_disulfide: residues %d(%s)/%d(%s) not CYS",
                res_i, name3_i, res_j, name3_j,
            )
            return pdb_text

        # Form the disulfide bond in the conformation
        conformation.form_disulfide(pose.conformation(), res_i, res_j, True, False)
        logger.info(
            "[Step04] Disulfide formed: Cys%d-Cys%d (PyRosetta)", res_i, res_j
        )

        # Chi minimization only (fast; backbone unchanged to preserve pLDDT context)
        sfxn = pyrosetta.get_fa_scorefxn()
        mmap = pyrosetta.MoveMap()
        mmap.set_bb(False)
        mmap.set_chi(True)
        mmap.set_jump(False)
        min_mover = MinMover()
        min_mover.movemap(mmap)
        min_mover.score_function(sfxn)
        min_mover.max_iter(200)
        min_mover.apply(pose)

        # Dump to temp file and read back as string
        tmp_out = tempfile.NamedTemporaryFile(
            mode="w", suffix=".pdb", delete=False, encoding="utf-8"
        )
        tmp_out.close()
        pose.dump_pdb(tmp_out.name)
        result_text = Path(tmp_out.name).read_text(encoding="utf-8")
        os.unlink(tmp_out.name)
        return result_text

    except Exception as exc:
        logger.warning("[Step04] _try_form_disulfide failed: %s", exc)
        return pdb_text  # 실패 시 원본 반환


def _extract_mean_plddt(pdb_text: str) -> float:
    """PDB ATOM 레코드의 B-factor 컬럼에서 평균 pLDDT를 추출한다."""
    values: List[float] = []
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM"):
            continue
        try:
            b_factor = float(line[60:66].strip())
            values.append(b_factor)
        except (ValueError, IndexError):
            continue
    return sum(values) / len(values) if values else 0.0


# ---------------------------------------------------------------------------
# CLI / standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Step04: ESMFold QC standalone test")
    parser.add_argument(
        "--fasta",
        required=True,
        help="FASTA file with sequences to evaluate",
    )
    parser.add_argument("--output-dir", default="runs/test_run")
    args = parser.parse_args()

    # Parse sequences from FASTA
    entries: List[SequenceEntry] = []
    fasta_path = Path(args.fasta)
    lines = fasta_path.read_text().splitlines()
    seq_id = ""
    seq_buf: List[str] = []
    idx = 0
    for line in lines:
        line = line.strip()
        if line.startswith(">"):
            if seq_id and seq_buf:
                entries.append(
                    SequenceEntry(
                        backbone_idx=idx // 8,
                        seq_idx=idx % 8,
                        sequence="".join(seq_buf),
                        fasta_path=args.fasta,
                        seq_id=seq_id,
                    )
                )
                idx += 1
            seq_id = line[1:].split()[0]
            seq_buf = []
        else:
            seq_buf.append(line)
    if seq_id and seq_buf:
        entries.append(
            SequenceEntry(
                backbone_idx=idx // 8,
                seq_idx=idx % 8,
                sequence="".join(seq_buf),
                fasta_path=args.fasta,
                seq_id=seq_id,
            )
        )

    cfg: Dict[str, Any] = {
        "run_id": "test_run",
        "output_base_dir": args.output_dir,
    }
    result = run_qc(entries, cfg)
    print(f"Step04: {len(result.passed())} passed / {len(result.qc_results)} total")
