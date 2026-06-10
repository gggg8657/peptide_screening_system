#!/usr/bin/env python3
"""
generate_sstr2_sst14_complex.py
================================
Task #38: Boltz-2로 SSTR2-SST14 complex PDB 생성

SSTR2 수용체(7XNA)와 SST-14 펩타이드(AGCKNFFWKTFTSC)의 결합 complex를
Boltz-2로 예측하여 top-3 PDB와 메타데이터를 생성한다.

출력:
    data/somatostatin_receptor/SSTR2_SST14_complex_boltz_{rank}.pdb (top-3)
    data/somatostatin_receptor/SSTR2_SST14_complex_metadata.json

iPTM/confidence >= 0.7 검증:
    - Cys3-Cys14 SS bond 보존 여부 (chain B residue 3, 14의 SG-SG 거리)
    - binding_pocket_SSTR2.json 정의 pocket 내 펩타이드 위치 검증
    - iPTM 점수 기록

사용법:
    conda run -n boltz python pipeline_local/scripts/generate_sstr2_sst14_complex.py \\
        --sstr2-pdb data/somatostatin_receptor/SSTR2_7XNA.pdb \\
        --out-dir runs_local/sstr2_sst14_complex \\
        --n-samples 5

GPU 설정:
    CUDA_VISIBLE_DEVICES=2,3 (기본값)
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

SST14_SEQUENCE = "AGCKNFFWKTFTSC"
SST14_ID = "SST14"

SSTR2_UNIPROT = "P30874"

# runs_local/alphafold_receptors 에 사전 다운로드된 MSA
SSTR2_MSA_PATH = Path("runs_local/alphafold_receptors/AF-P30874-F1-msa.a3m")

# binding pocket 정의 (binding_pocket_SSTR2.json)
BINDING_POCKET_FILE = Path(
    "data/somatostatin_receptor/binding_pocket_SSTR2.json"
)

# 원본 binding pocket 좌표 fallback — A-01 결과 (KAERI-AIRL-MOM-2026-003)
# binding_pocket_SSTR2.json 이 덮어씌워진 경우 대비 (center_x=0,y=0,z=0 → 원본 사용)
_SSTR2_POCKET_FALLBACK = {
    "center_x": -5.595,
    "center_y": -28.626,
    "center_z": 52.21,
    "radius": 13.035,
}

# iPTM 품질 임계값
IPTM_THRESHOLD = 0.7

# SS bond geometry 임계값 (Cys SG-SG 거리, Å)
SS_BOND_MAX_DIST = 2.3  # 이상적: 2.04 Å, 허용: < 2.3 Å

# SST-14에서 Cys 위치 (1-indexed)
CYS3_POS = 3
CYS14_POS = 14


# ---------------------------------------------------------------------------
# Boltz YAML 생성
# ---------------------------------------------------------------------------

def _write_boltz_yaml(
    out_path: Path,
    peptide_seq: str,
    peptide_id: str,
    receptor_seq: str,
    receptor_msa_path: Path,
) -> None:
    """Boltz-2 입력 YAML 작성 (covalent bond: Cys3-Cys14 SS bond)."""
    pep_msa = out_path.parent / f"{peptide_id}_self.a3m"
    pep_msa.write_text(f">query\n{peptide_seq}\n", encoding="utf-8")

    # Boltz YAML v1: constraints 블록으로 SS bond 명시
    # chain A = peptide (SST-14), chain B = receptor (SSTR2)
    yaml_content = (
        f"version: 1\n"
        f"sequences:\n"
        f"  - protein:\n"
        f"      id: A\n"
        f"      sequence: {peptide_seq}\n"
        f"      msa: {pep_msa.resolve()}\n"
        f"  - protein:\n"
        f"      id: B\n"
        f"      sequence: {receptor_seq}\n"
        f"      msa: {receptor_msa_path.resolve()}\n"
        f"constraints:\n"
        f"  - bond:\n"
        f"      atom1: [A, {CYS3_POS}, SG]\n"
        f"      atom2: [A, {CYS14_POS}, SG]\n"
    )
    out_path.write_text(yaml_content, encoding="utf-8")
    logger.info("[YAML] 생성: %s", out_path)


# ---------------------------------------------------------------------------
# Boltz predict 실행
# ---------------------------------------------------------------------------

def run_boltz_predict(
    yaml_path: Path,
    out_dir: Path,
    boltz_env: str = "boltz",
    cuda_devices: str = "2,3",
    n_samples: int = 5,
    recycling_steps: int = 3,
    sampling_steps: int = 100,
    timeout: int = 1800,
) -> subprocess.CompletedProcess:
    """Boltz-2 predict 실행."""
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "conda", "run", "--no-capture-output", "-n", boltz_env,
        "boltz", "predict", str(yaml_path.resolve()),
        "--out_dir", str(out_dir.resolve()),
        "--recycling_steps", str(recycling_steps),
        "--sampling_steps", str(sampling_steps),
        "--diffusion_samples", str(n_samples),
        "--output_format", "pdb",
        "--override",
        "--num_workers", "0",
        "--no_kernels",
        "--model", "boltz2",
    ]

    env = {**os.environ, "CUDA_VISIBLE_DEVICES": cuda_devices}

    logger.info("[Boltz] 실행: %s", " ".join(cmd[:8]) + " ...")
    logger.info("[Boltz] CUDA_VISIBLE_DEVICES=%s", cuda_devices)
    t0 = time.time()

    try:
        proc = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        logger.error("[Boltz] TIMEOUT (%ds)", timeout)
        raise

    elapsed = time.time() - t0
    logger.info("[Boltz] 완료: rc=%d, 소요시간=%.1fs", proc.returncode, elapsed)
    return proc


# ---------------------------------------------------------------------------
# 결과 파싱
# ---------------------------------------------------------------------------

def _find_confidence_files(out_dir: Path, yaml_stem: str) -> List[Path]:
    """boltz predict 출력에서 confidence JSON 파일 목록 반환 (model 번호 순)."""
    # 경로 패턴: out_dir/boltz_results_{yaml_stem}/predictions/{yaml_stem}/confidence_*_model_N.json
    pred_dir = out_dir / f"boltz_results_{yaml_stem}" / "predictions" / yaml_stem
    if pred_dir.exists():
        files = sorted(pred_dir.glob("confidence_*_model_*.json"))
        if files:
            return files
    # fallback: rglob
    files = sorted(out_dir.rglob("confidence_*_model_*.json"))
    return files


def _find_pdb_files(out_dir: Path, yaml_stem: str) -> List[Path]:
    """boltz predict 출력에서 PDB 파일 목록 반환 (model 번호 순)."""
    pred_dir = out_dir / f"boltz_results_{yaml_stem}" / "predictions" / yaml_stem
    if pred_dir.exists():
        files = sorted(pred_dir.glob("*_model_*.pdb"))
        if files:
            return files
    files = sorted(out_dir.rglob("*_model_*.pdb"))
    return files


def _parse_model_index(path: Path) -> int:
    """파일명에서 model 번호 추출. 예: ..._model_2.pdb → 2."""
    stem = path.stem
    parts = stem.rsplit("_model_", 1)
    if len(parts) == 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    return 0


def parse_results(
    out_dir: Path,
    yaml_stem: str,
) -> List[Dict[str, Any]]:
    """Boltz predict 결과를 파싱하여 model 별 메타데이터 반환.

    Returns:
        List of dicts (iPTM 내림차순 정렬):
            {model_idx, iptm, ptm, confidence_score, pdb_path}
    """
    conf_files = _find_confidence_files(out_dir, yaml_stem)
    pdb_files = _find_pdb_files(out_dir, yaml_stem)

    # model_idx → 파일 매핑
    pdb_map = {_parse_model_index(p): p for p in pdb_files}
    conf_map = {_parse_model_index(p): p for p in conf_files}

    all_indices = sorted(set(list(pdb_map.keys()) + list(conf_map.keys())))
    if not all_indices:
        logger.error("[결과] PDB/confidence 파일 없음: %s", out_dir)
        return []

    results = []
    for idx in all_indices:
        entry: Dict[str, Any] = {"model_idx": idx}

        # confidence 파싱
        cf = conf_map.get(idx)
        if cf and cf.exists():
            try:
                with open(cf, encoding="utf-8") as f:
                    cdata = json.load(f)
                entry["iptm"] = float(cdata.get("iptm", 0.0))
                entry["ptm"] = float(cdata.get("ptm", 0.0))
                entry["confidence_score"] = float(cdata.get("confidence_score", 0.0))
                entry["confidence_path"] = str(cf)
            except Exception as e:
                logger.warning("[결과] confidence 파싱 실패 model_%d: %s", idx, e)
                entry["iptm"] = 0.0
                entry["ptm"] = 0.0
                entry["confidence_score"] = 0.0
        else:
            entry["iptm"] = 0.0
            entry["ptm"] = 0.0
            entry["confidence_score"] = 0.0

        pf = pdb_map.get(idx)
        entry["pdb_path"] = str(pf) if pf and pf.exists() else None

        results.append(entry)

    # iPTM 내림차순 정렬
    results.sort(key=lambda x: x["iptm"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# SS Bond 검증
# ---------------------------------------------------------------------------

def _parse_atom_coords(pdb_path: Path) -> Dict[Tuple[str, int, str], Tuple[float, float, float]]:
    """PDB에서 {(chain, resnum, atom_name): (x, y, z)} 파싱."""
    coords = {}
    with open(pdb_path, "r", errors="replace") as f:
        for line in f:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            if len(line) < 54:
                continue
            atom_name = line[12:16].strip()
            chain = line[21].strip()
            try:
                resnum = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
            except ValueError:
                continue
            coords[(chain, resnum, atom_name)] = (x, y, z)
    return coords


def _dist3d(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def check_ss_bond(pdb_path: Path, peptide_chain: str = "A") -> Dict[str, Any]:
    """Cys3-Cys14 SS bond (SG-SG 거리) 검증.

    Returns:
        {ok: bool, sg3_sg14_dist: float, threshold: float, note: str}
    """
    coords = _parse_atom_coords(pdb_path)

    sg3 = coords.get((peptide_chain, CYS3_POS, "SG"))
    sg14 = coords.get((peptide_chain, CYS14_POS, "SG"))

    if sg3 is None or sg14 is None:
        # chain 이름이 다를 수 있으니 체인 전체 탐색
        all_chains = sorted({k[0] for k in coords})
        for ch in all_chains:
            sg3 = sg3 or coords.get((ch, CYS3_POS, "SG"))
            sg14 = sg14 or coords.get((ch, CYS14_POS, "SG"))
            if sg3 and sg14:
                peptide_chain = ch
                break

    if sg3 is None:
        return {
            "ok": False,
            "sg3_sg14_dist": None,
            "threshold": SS_BOND_MAX_DIST,
            "note": f"Cys{CYS3_POS} SG 원자 미발견",
        }
    if sg14 is None:
        return {
            "ok": False,
            "sg3_sg14_dist": None,
            "threshold": SS_BOND_MAX_DIST,
            "note": f"Cys{CYS14_POS} SG 원자 미발견",
        }

    dist = _dist3d(sg3, sg14)
    ok = dist <= SS_BOND_MAX_DIST
    return {
        "ok": ok,
        "sg3_sg14_dist": round(dist, 3),
        "threshold": SS_BOND_MAX_DIST,
        "note": (
            f"SG-SG 거리 {dist:.3f} Å ({'OK' if ok else 'FAIL, 임계값 초과'})"
        ),
    }


# ---------------------------------------------------------------------------
# Binding Pocket 위치 검증
# ---------------------------------------------------------------------------

def check_pocket_placement(
    pdb_path: Path,
    pocket_json: Path,
    peptide_chain: str = "A",
) -> Dict[str, Any]:
    """펩타이드 CA centroid가 binding pocket 구 내에 있는지 검증.

    Returns:
        {ok: bool, centroid: [x,y,z], pocket_center: [x,y,z], dist: float, radius: float}
    """
    if not pocket_json.exists():
        return {"ok": False, "note": f"binding pocket JSON 없음: {pocket_json}"}

    with open(pocket_json, encoding="utf-8") as f:
        pocket = json.load(f)

    cx, cy, cz = pocket["center_x"], pocket["center_y"], pocket["center_z"]
    # "radius" 또는 "radius_angstrom" 필드 호환 처리
    radius = pocket.get("radius") or pocket.get("radius_angstrom")
    if radius is None:
        return {"ok": False, "note": "binding pocket JSON에 radius/radius_angstrom 필드 없음"}

    # binding_pocket_SSTR2.json이 (0,0,0)으로 덮어씌워진 경우 fallback 사용
    # A-01 원본 좌표: center_x=-5.595, center_y=-28.626, center_z=52.21
    if cx == 0.0 and cy == 0.0 and cz == 0.0:
        logger.warning(
            "[Pocket] center=(0,0,0) 감지 — binding_pocket_SSTR2.json 덮어씌워짐으로 판단. "
            "A-01 원본 fallback 좌표 사용 (center_x=-5.595, center_y=-28.626, center_z=52.21)"
        )
        cx = _SSTR2_POCKET_FALLBACK["center_x"]
        cy = _SSTR2_POCKET_FALLBACK["center_y"]
        cz = _SSTR2_POCKET_FALLBACK["center_z"]
        radius = _SSTR2_POCKET_FALLBACK["radius"]

    coords = _parse_atom_coords(pdb_path)

    # 펩타이드 체인 CA 원자 수집
    ca_coords = [
        v for (ch, rn, an), v in coords.items()
        if ch == peptide_chain and an == "CA"
    ]

    if not ca_coords:
        # 체인 미발견 시 모든 짧은 체인 탐색 (14aa = 14 CA)
        chain_ca: Dict[str, List] = {}
        for (ch, rn, an), v in coords.items():
            if an == "CA":
                chain_ca.setdefault(ch, []).append(v)
        # 가장 짧은 체인을 펩타이드로 가정
        if chain_ca:
            peptide_chain = min(chain_ca, key=lambda c: len(chain_ca[c]))
            ca_coords = chain_ca[peptide_chain]

    if not ca_coords:
        return {"ok": False, "note": "펩타이드 CA 원자 미발견"}

    mx = sum(p[0] for p in ca_coords) / len(ca_coords)
    my = sum(p[1] for p in ca_coords) / len(ca_coords)
    mz = sum(p[2] for p in ca_coords) / len(ca_coords)

    dist = _dist3d((mx, my, mz), (cx, cy, cz))
    ok = dist <= radius

    return {
        "ok": ok,
        "centroid": [round(mx, 3), round(my, 3), round(mz, 3)],
        "pocket_center": [round(cx, 3), round(cy, 3), round(cz, 3)],
        "dist": round(dist, 3),
        "radius": round(radius, 3),
        "note": (
            f"centroid→pocket거리 {dist:.1f} Å, "
            f"pocket반경 {radius:.1f} Å ({'내부 OK' if ok else '외부 FAIL'})"
        ),
    }


# ---------------------------------------------------------------------------
# SSTR2 서열 추출 (PDB에서)
# ---------------------------------------------------------------------------

_THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def extract_receptor_seq_from_pdb(pdb_path: Path) -> str:
    """SSTR2 PDB에서 가장 긴 체인의 서열 추출."""
    chain_res: Dict[str, List[Tuple[int, str]]] = {}
    seen: Dict[str, set] = {}

    with open(pdb_path, "r", errors="replace") as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            if len(line) < 54:
                continue
            atom_name = line[12:16].strip()
            if atom_name != "CA":
                continue
            resname = line[17:20].strip()
            chain_id = line[21]
            try:
                resseq = int(line[22:26].strip())
            except ValueError:
                continue
            aa = _THREE_TO_ONE.get(resname)
            if aa is None:
                continue
            key = (resseq, line[26].strip())
            if key not in seen.setdefault(chain_id, set()):
                seen[chain_id].add(key)
                chain_res.setdefault(chain_id, []).append((resseq, aa))

    if not chain_res:
        raise ValueError(f"PDB에서 CA 원자를 찾을 수 없습니다: {pdb_path}")

    best = max(chain_res, key=lambda c: len(chain_res[c]))
    seq = "".join(aa for _, aa in sorted(chain_res[best]))
    logger.info("[PDB] 수용체 체인 %s, %d aa 추출", best, len(seq))
    return seq


# ---------------------------------------------------------------------------
# 메인 로직
# ---------------------------------------------------------------------------

def run(
    sstr2_pdb: Path,
    out_dir: Path,
    data_out_dir: Path,
    n_samples: int = 5,
    top_k: int = 3,
    boltz_env: str = "boltz",
    cuda_devices: str = "2,3",
    recycling_steps: int = 3,
    sampling_steps: int = 100,
    timeout: int = 1800,
) -> Dict[str, Any]:
    """메인 실행 함수.

    Returns:
        메타데이터 dict (metadata JSON 내용과 동일)
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_out_dir = Path(data_out_dir)
    data_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 수용체 서열 추출
    receptor_seq = extract_receptor_seq_from_pdb(sstr2_pdb)
    logger.info("[Setup] 수용체 서열 %d aa", len(receptor_seq))

    # 2. MSA 경로 확인
    msa_path = SSTR2_MSA_PATH
    if not msa_path.exists():
        msa_path = Path("runs_local/alphafold_receptors/AF-P30874-F1-msa.a3m")
    if not msa_path.exists():
        logger.error("[Setup] SSTR2 MSA 없음: %s", msa_path)
        raise FileNotFoundError(f"SSTR2 MSA 파일 없음: {msa_path}")
    logger.info("[Setup] MSA: %s (%d bytes)", msa_path, msa_path.stat().st_size)

    # 3. YAML 생성
    yaml_stem = f"SSTR2_SST14_complex"
    yaml_path = out_dir / f"{yaml_stem}.yaml"
    _write_boltz_yaml(
        out_path=yaml_path,
        peptide_seq=SST14_SEQUENCE,
        peptide_id=SST14_ID,
        receptor_seq=receptor_seq,
        receptor_msa_path=msa_path,
    )

    # 4. Boltz 실행
    boltz_out = out_dir / "boltz_out"
    proc = run_boltz_predict(
        yaml_path=yaml_path,
        out_dir=boltz_out,
        boltz_env=boltz_env,
        cuda_devices=cuda_devices,
        n_samples=n_samples,
        recycling_steps=recycling_steps,
        sampling_steps=sampling_steps,
        timeout=timeout,
    )

    if proc.returncode != 0:
        logger.error("[Boltz] 비정상 종료 rc=%d", proc.returncode)
        raise RuntimeError(f"Boltz predict 실패: rc={proc.returncode}")

    # 5. 결과 파싱
    model_results = parse_results(boltz_out, yaml_stem)
    logger.info("[결과] 총 %d 모델 파싱", len(model_results))

    if not model_results:
        raise RuntimeError("Boltz 결과 파일이 없습니다")

    # 6. Top-K 선택 + 검증
    top_k_results = model_results[:top_k]
    metadata_entries = []

    for rank_idx, entry in enumerate(top_k_results, start=1):
        pdb_src = Path(entry["pdb_path"]) if entry.get("pdb_path") else None
        iptm = entry.get("iptm", 0.0)

        # 최종 출력 경로
        dest_pdb = data_out_dir / f"SSTR2_SST14_complex_boltz_{rank_idx}.pdb"

        validation: Dict[str, Any] = {
            "rank": rank_idx,
            "model_idx": entry["model_idx"],
            "iptm": iptm,
            "ptm": entry.get("ptm", 0.0),
            "confidence_score": entry.get("confidence_score", 0.0),
            "iptm_pass": iptm >= IPTM_THRESHOLD,
            "pdb_dest": str(dest_pdb),
        }

        if pdb_src and pdb_src.exists():
            # PDB 복사
            shutil.copy2(str(pdb_src), str(dest_pdb))
            logger.info(
                "[Rank%d] iPTM=%.3f → %s", rank_idx, iptm, dest_pdb.name
            )

            # SS bond 검증
            ss_check = check_ss_bond(dest_pdb)
            validation["ss_bond"] = ss_check
            logger.info(
                "[Rank%d] SS bond: %s", rank_idx, ss_check["note"]
            )

            # Binding pocket 검증
            pocket_check = check_pocket_placement(dest_pdb, BINDING_POCKET_FILE)
            validation["pocket_placement"] = pocket_check
            logger.info(
                "[Rank%d] Pocket: %s", rank_idx, pocket_check.get("note", "N/A")
            )
        else:
            logger.warning("[Rank%d] PDB 파일 없음", rank_idx)
            validation["ss_bond"] = {"ok": False, "note": "PDB 없음"}
            validation["pocket_placement"] = {"ok": False, "note": "PDB 없음"}

        metadata_entries.append(validation)

    # 7. 메타데이터 저장
    metadata = {
        "task": "Task #38 — SSTR2-SST14 complex Boltz docking",
        "date": "2026-05-19",
        "input": {
            "receptor": str(sstr2_pdb),
            "peptide": SST14_SEQUENCE,
            "receptor_msa": str(msa_path),
        },
        "config": {
            "boltz_env": boltz_env,
            "cuda_devices": cuda_devices,
            "n_samples": n_samples,
            "top_k": top_k,
            "recycling_steps": recycling_steps,
            "sampling_steps": sampling_steps,
        },
        "n_models_total": len(model_results),
        "all_models": [
            {
                "model_idx": r["model_idx"],
                "iptm": r["iptm"],
                "ptm": r.get("ptm", 0.0),
                "confidence_score": r.get("confidence_score", 0.0),
            }
            for r in model_results
        ],
        "top_k_validation": metadata_entries,
        "proteinmpnn_receptor_context_ready": any(
            e["iptm"] >= IPTM_THRESHOLD for e in metadata_entries
        ),
    }

    meta_path = data_out_dir / "SSTR2_SST14_complex_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info("[메타] 저장: %s", meta_path)

    # 8. 요약 보고
    _print_summary(metadata)

    return metadata


def _print_summary(metadata: Dict[str, Any]) -> None:
    """결과 요약 출력."""
    print("\n" + "=" * 60)
    print("SSTR2-SST14 Complex Boltz Docking 결과 요약")
    print("=" * 60)
    top_k = metadata["top_k_validation"]
    for entry in top_k:
        rank = entry["rank"]
        iptm = entry["iptm"]
        iptm_ok = "PASS" if entry["iptm_pass"] else "FAIL"
        ss = entry.get("ss_bond", {})
        ss_ok = "OK" if ss.get("ok") else "FAIL"
        ss_dist = ss.get("sg3_sg14_dist")
        pocket = entry.get("pocket_placement", {})
        pocket_ok = "OK" if pocket.get("ok") else "FAIL"
        dist = pocket.get("dist", "N/A")
        radius = pocket.get("radius", "N/A")
        print(
            f"  Rank{rank}: iPTM={iptm:.3f} [{iptm_ok}] | "
            f"SS bond SG-SG={ss_dist} Å [{ss_ok}] | "
            f"Pocket dist={dist}/{radius} Å [{pocket_ok}]"
        )
    ready = metadata.get("proteinmpnn_receptor_context_ready", False)
    print(f"\nProteinMPNN receptor_context 활성화 가능: {'YES' if ready else 'NO'}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Boltz-2로 SSTR2-SST14 complex 생성"
    )
    p.add_argument(
        "--sstr2-pdb",
        default="data/somatostatin_receptor/SSTR2_7XNA.pdb",
        help="SSTR2 수용체 PDB 파일 경로",
    )
    p.add_argument(
        "--out-dir",
        default="runs_local/sstr2_sst14_complex",
        help="Boltz 작업 디렉토리",
    )
    p.add_argument(
        "--data-out-dir",
        default="data/somatostatin_receptor",
        help="최종 PDB/metadata 저장 디렉토리",
    )
    p.add_argument("--n-samples", type=int, default=5, help="diffusion samples 수")
    p.add_argument("--top-k", type=int, default=3, help="저장할 top-K 모델 수")
    p.add_argument("--boltz-env", default="boltz", help="conda 환경 이름")
    p.add_argument(
        "--cuda-devices", default="2,3", help="CUDA_VISIBLE_DEVICES 값"
    )
    p.add_argument(
        "--recycling-steps", type=int, default=3, help="recycling steps"
    )
    p.add_argument(
        "--sampling-steps", type=int, default=100, help="sampling steps"
    )
    p.add_argument("--timeout", type=int, default=1800, help="subprocess timeout (초)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    # 작업 디렉토리를 repo 루트 기준으로 설정
    repo_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(repo_root)
    logger.info("[Main] 작업 디렉토리: %s", repo_root)

    try:
        metadata = run(
            sstr2_pdb=Path(args.sstr2_pdb),
            out_dir=Path(args.out_dir),
            data_out_dir=Path(args.data_out_dir),
            n_samples=args.n_samples,
            top_k=args.top_k,
            boltz_env=args.boltz_env,
            cuda_devices=args.cuda_devices,
            recycling_steps=args.recycling_steps,
            sampling_steps=args.sampling_steps,
            timeout=args.timeout,
        )
        sys.exit(0)
    except Exception as e:
        logger.error("[Fatal] %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
