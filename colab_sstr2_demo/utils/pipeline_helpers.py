"""SSTR2-SST14 Peptide Design Pipeline Helpers.

이 모듈은 SSTR2-SST14 펩타이드 설계 파이프라인에서 사용하는 모든 헬퍼 함수를 포함합니다.
Colab 공유 노트북에서 import하여 사용합니다.

Usage:
    import sys; sys.path.insert(0, ".")
    from utils.pipeline_helpers import *
"""

from __future__ import annotations

import os
import csv
import time
import json as _json
from collections import defaultdict, OrderedDict
from typing import List, Optional, Set

import pandas as pd
import py3Dmol
from IPython.display import display, HTML, IFrame
from tqdm.notebook import tqdm

from utils.peptide_design_utils import get_design_positions, find_cys_positions

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

AA3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "MSE": "M",
}

HYDROPHOBIC = set("AILMFWVY")
BASIC = set("KRH")
ACIDIC = set("DE")

_3D_HTML_DIR = "3d_views"


# ──────────────────────────────────────────────────────────────
# CIF / PDB file handling
# ──────────────────────────────────────────────────────────────

def cif_to_pdb(cif_path: str, pdb_path: str, structure_id="AF3_MODEL"):
    """BioPython을 이용한 CIF → PDB 변환."""
    from Bio.PDB import MMCIFParser, PDBIO

    parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure(structure_id, cif_path)
    io = PDBIO()
    io.set_structure(structure)
    io.save(pdb_path)
    return pdb_path


def parse_pdb_residues(pdb_path: str):
    """PDB를 ATOM/HETATM 라인 기준으로 파싱하여 chain → residue dict."""
    chains = defaultdict(OrderedDict)
    with open(pdb_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not (line.startswith("ATOM") or line.startswith("HETATM")):
                continue
            if len(line) < 27:
                continue
            chain_id = line[21].strip() or "?"
            resname = line[17:20].strip().upper()
            resseq_raw = line[22:26].strip()
            icode = line[26].strip()
            try:
                resseq = int(resseq_raw)
            except ValueError:
                continue
            key = (resseq, icode)
            if key not in chains[chain_id]:
                chains[chain_id][key] = resname
    return chains


def residues_to_seq(res_dict: OrderedDict):
    return "".join(AA3_TO_1.get(res3, "X") for res3 in res_dict.values())


def contiguous_ranges(res_keys):
    nums = [k[0] for k in res_keys]
    if not nums:
        return []
    ranges = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
        else:
            ranges.append((start, prev))
            start = prev = n
    ranges.append((start, prev))
    return [f"{a}-{b}" if a != b else f"{a}" for a, b in ranges]


def summarize_pdb(pdb_path, show_seq="head"):
    """PDB 파일의 체인별 잔기 수, 범위, 서열을 요약 DataFrame으로 반환."""
    chains = parse_pdb_residues(pdb_path)
    rows = []
    for cid, res_dict in chains.items():
        keys = list(res_dict.keys())
        seq = residues_to_seq(res_dict)
        if show_seq == "head":
            seq_out = seq[:60] + ("..." if len(seq) > 60 else "")
        elif show_seq == "full":
            seq_out = seq
        else:
            seq_out = ""
        rows.append({
            "chain": cid,
            "length": len(keys),
            "pdb_res_min": keys[0][0] if keys else None,
            "pdb_res_max": keys[-1][0] if keys else None,
            "ranges": ", ".join(contiguous_ranges(keys)),
            "seq": seq_out,
        })
    return pd.DataFrame(rows).sort_values(["chain"]).reset_index(drop=True)


# ──────────────────────────────────────────────────────────────
# 3D visualization (py3Dmol)
# ──────────────────────────────────────────────────────────────

def _display_view(view, html_name="view"):
    """py3Dmol 뷰를 Colab/Jupyter에서 표시하고 HTML로도 저장."""
    os.makedirs(_3D_HTML_DIR, exist_ok=True)
    html_path = os.path.join(_3D_HTML_DIR, f"{html_name}.html")
    abs_path = os.path.abspath(html_path)

    try:
        full_html = view._make_html()
    except Exception:
        full_html = (
            '<!DOCTYPE html><html><head>'
            '<script src="https://3Dmol.org/build/3Dmol-min.js"></script>'
            f'</head><body>{view._repr_html_()}</body></html>'
        )

    with open(html_path, "w") as f:
        f.write(full_html)

    try:
        display(HTML(view._repr_html_()))
    except Exception:
        pass

    display(HTML(
        f'<p>3D view saved: <a href="{html_path}" target="_blank">'
        f'<code>{html_path}</code></a></p>'
    ))


def show_structure_3d(pdb_path, width=800, height=500,
                      receptor_color="lightblue", peptide_color="orange",
                      surface_receptor=False, stick_peptide=True,
                      label=None):
    """PDB 파일을 py3Dmol 인터랙티브 3D 뷰어로 표시."""
    with open(pdb_path, "r") as f:
        pdb_data = f.read()

    view = py3Dmol.view(width=width, height=height)
    view.addModel(pdb_data, "pdb")

    view.setStyle({"chain": "A"}, {"cartoon": {"color": receptor_color, "opacity": 0.85}})
    view.setStyle({"chain": "B"}, {"cartoon": {"color": peptide_color}})
    if stick_peptide:
        view.addStyle({"chain": "B"}, {"stick": {"colorscheme": "orangeCarbon", "radius": 0.15}})
    if surface_receptor:
        view.addSurface(py3Dmol.VDW, {"opacity": 0.3, "color": receptor_color}, {"chain": "A"})
    if label:
        view.addLabel(label, {"backgroundColor": "white", "fontColor": "black",
                              "fontSize": 14, "position": {"x": 0, "y": 0, "z": 0}})

    view.zoomTo()
    view.setBackgroundColor("white")

    _name = os.path.splitext(os.path.basename(pdb_path))[0]
    _display_view(view, html_name=f"structure_{_name}")
    return view


def show_comparison_3d(pdb_paths, labels=None, width=800, height=500,
                       receptor_color="lightblue", peptide_colors=None):
    """여러 PDB 구조를 나란히 그리드로 비교 표시."""
    n = len(pdb_paths)
    if labels is None:
        labels = [f"#{i+1}" for i in range(n)]
    if peptide_colors is None:
        _palette = ["orange", "hotpink", "lime", "cyan", "yellow", "red", "magenta"]
        peptide_colors = [_palette[i % len(_palette)] for i in range(n)]

    cols = min(n, 3)
    rows = (n + cols - 1) // cols

    view = py3Dmol.view(width=width, height=height * rows // max(rows, 1),
                        viewergrid=(rows, cols), linked=False)

    for idx, pdb_path in enumerate(pdb_paths):
        r, c = divmod(idx, cols)
        with open(pdb_path, "r") as f:
            pdb_data = f.read()

        view.addModel(pdb_data, "pdb", viewer=(r, c))
        view.setStyle({"chain": "A"}, {"cartoon": {"color": receptor_color, "opacity": 0.8}}, viewer=(r, c))
        view.setStyle({"chain": "B"}, {"cartoon": {"color": peptide_colors[idx]}}, viewer=(r, c))
        view.addStyle({"chain": "B"}, {"stick": {"colorscheme": "orangeCarbon", "radius": 0.12}}, viewer=(r, c))

        view.addLabel(labels[idx],
                      {"backgroundColor": "white", "fontColor": "black", "fontSize": 12,
                       "position": {"x": -20, "y": 20, "z": 0}, "backgroundOpacity": 0.8},
                      viewer=(r, c))
        view.zoomTo(viewer=(r, c))

    view.setBackgroundColor("white")

    _names = "_".join(os.path.splitext(os.path.basename(p))[0][:15] for p in pdb_paths[:3])
    _display_view(view, html_name=f"comparison_{_names}")
    return view


# ──────────────────────────────────────────────────────────────
# Structure standardization (PyRosetta)
# ──────────────────────────────────────────────────────────────

def find_peptide_chain_pose(pose, peptide_len=14):
    """Pose에서 길이가 peptide_len인 체인을 탐지."""
    info = []
    for ch in range(1, pose.num_chains() + 1):
        seq = pose.chain_sequence(ch)
        info.append((ch, len(seq), seq))
    df = pd.DataFrame(info, columns=["pose_chain_id", "length", "sequence"])
    display(df)
    hits = [ch for ch, ln, seq in info if ln == peptide_len]
    if len(hits) != 1:
        raise RuntimeError(f"길이=={peptide_len} 체인 탐지 결과가 1개가 아닙니다: {hits}")
    return hits[0]


def extract_chain_pose_by_dump(original_pose, chain_id: int):
    """특정 체인만 추출하여 별도 Pose로 반환."""
    import pyrosetta

    tmp_full = "__tmp_full.pdb"
    tmp_chain = f"__tmp_chain_{chain_id}.pdb"
    original_pose.dump_pdb(tmp_full)

    first_res = original_pose.chain_begin(chain_id)
    pdbinfo = original_pose.pdb_info()
    chain_letter = pdbinfo.chain(first_res) if pdbinfo is not None else ""
    if not chain_letter or chain_letter.strip() == "":
        chain_letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[chain_id - 1]

    with open(tmp_full, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    with open(tmp_chain, "w", encoding="utf-8") as out:
        for line in lines:
            if (line.startswith("ATOM") or line.startswith("HETATM")) and len(line) > 21:
                if line[21] == chain_letter:
                    out.write(line)
            if line.startswith("TER"):
                out.write(line)
        out.write("END\n")

    new_pose = pyrosetta.pose_from_pdb(tmp_chain)
    os.remove(tmp_full)
    os.remove(tmp_chain)
    return new_pose


def standardize_to_AB(pose, peptide_chain_id, out_pdb="standardized_raw.pdb"):
    """체인을 A=receptor, B=peptide로 표준화하여 PDB 저장."""
    receptor_chains = [ch for ch in range(1, pose.num_chains() + 1) if ch != peptide_chain_id]
    if not receptor_chains:
        raise RuntimeError("receptor chain이 없습니다.")

    rec_pose = extract_chain_pose_by_dump(pose, receptor_chains[0])
    for ch in receptor_chains[1:]:
        rec_pose.append_pose_by_jump(extract_chain_pose_by_dump(pose, ch), rec_pose.total_residue())

    pep_pose = extract_chain_pose_by_dump(pose, peptide_chain_id)
    rec_pose.append_pose_by_jump(pep_pose, rec_pose.total_residue())

    rec_pose.dump_pdb(out_pdb)
    print(f"[OK] standardized saved -> {out_pdb} (A=receptor, B=peptide)")
    return rec_pose


# ──────────────────────────────────────────────────────────────
# Relax
# ──────────────────────────────────────────────────────────────

def relax_peptide_only(in_pdb="standardized_raw.pdb",
                       out_pdb="standardized_relaxed.pdb",
                       peptide_chain_number=2):
    """Receptor를 고정하고 펩타이드만 FastRelax."""
    import pyrosetta
    from pyrosetta.rosetta.protocols.relax import FastRelax
    from pyrosetta.rosetta.core.kinematics import MoveMap
    from pyrosetta.rosetta.core.select.residue_selector import ChainSelector

    pose = pyrosetta.pose_from_pdb(in_pdb)

    mm = MoveMap()
    mm.set_bb(False)
    mm.set_chi(False)
    mm.set_jump(False)

    pep_selector = ChainSelector(peptide_chain_number)
    pep_res = pep_selector.apply(pose)
    for i in range(1, pose.total_residue() + 1):
        if pep_res[i]:
            mm.set_bb(i, True)
            mm.set_chi(i, True)

    scorefxn = pyrosetta.get_score_function()
    relax = FastRelax()
    relax.set_scorefxn(scorefxn)
    relax.set_movemap(mm)

    pre = scorefxn(pose)

    print(f"Peptide-only FastRelax 시작 (score before: {pre:.2f})")
    t0 = time.time()

    pbar = tqdm(total=1, desc="FastRelax", bar_format="{l_bar}{bar}| {elapsed}<{remaining}")
    relax.apply(pose)
    pbar.update(1)
    pbar.close()

    elapsed = time.time() - t0
    post = scorefxn(pose)

    pose.dump_pdb(out_pdb)
    print(f"Relax 완료 ({elapsed:.1f}s) -> {out_pdb}")
    print(f"  score: {pre:.2f} -> {post:.2f} (delta={post - pre:+.2f})")
    return pre, post


# ──────────────────────────────────────────────────────────────
# Scoring / Analysis
# ──────────────────────────────────────────────────────────────

def stability_pk_proxy_scores(seq: str):
    """간이 안정성/PK 프록시 스코어 계산."""
    seq = seq.strip().upper()
    kr = sum(1 for x in seq if x in "KR")
    arom = sum(1 for x in seq if x in "FYW")
    cleavage_risk = 2.0 * kr + 1.0 * arom

    hyd = sum(1 for x in seq if x in HYDROPHOBIC)
    hydrophobic_fraction = hyd / max(len(seq), 1)

    pos = sum(1 for x in seq if x in BASIC)
    neg = sum(1 for x in seq if x in ACIDIC)
    net_charge_proxy = pos - neg

    pk_penalty = 5.0 * max(0.0, hydrophobic_fraction - 0.50) + 0.5 * abs(net_charge_proxy)
    return {
        "cleavage_risk": cleavage_risk,
        "hydrophobic_fraction": hydrophobic_fraction,
        "net_charge_proxy": net_charge_proxy,
        "pk_penalty": pk_penalty,
    }


def analyze_interface(pose):
    """InterfaceAnalyzerMover로 dG/dSASA 계산."""
    from pyrosetta.rosetta.protocols.analysis import InterfaceAnalyzerMover

    iam = InterfaceAnalyzerMover(1)
    iam.set_pack_separated(True)
    iam.set_compute_packstat(True)
    iam.apply(pose)
    return iam.get_interface_dG(), iam.get_interface_delta_sasa()


# ──────────────────────────────────────────────────────────────
# FastDesign
# ──────────────────────────────────────────────────────────────

def peptide_seq(pose, peptide_chain_id=2):
    return pose.chain_sequence(peptide_chain_id)


def diff_positions(original, new):
    return [i for i, (o, n) in enumerate(zip(original, new), start=1) if o != n]


def _hamming_distance(s1, s2):
    return sum(1 for a, b in zip(s1, s2) if a != b)


def build_task_factory(pose, peptide_chain_id=2, design_positions=None):
    """TaskFactory: 지정 위치만 설계, Cys/receptor 고정."""
    from pyrosetta.rosetta.core.pack.task import TaskFactory
    from pyrosetta.rosetta.core.pack.task.operation import (
        OperateOnResidueSubset, PreventRepackingRLT, RestrictToRepackingRLT
    )
    from pyrosetta.rosetta.core.select.residue_selector import (
        ChainSelector, NotResidueSelector, ResidueNameSelector,
        AndResidueSelector, OrResidueSelector, ResidueIndexSelector
    )

    pep_selector = ChainSelector(peptide_chain_id)
    rec_selector = NotResidueSelector(pep_selector)

    cys_selector = ResidueNameSelector("CYS")
    pep_cys_selector = AndResidueSelector(pep_selector, cys_selector)

    cant_touch = OrResidueSelector(rec_selector, pep_cys_selector)

    tf = TaskFactory()
    tf.push_back(OperateOnResidueSubset(PreventRepackingRLT(), cant_touch))

    if design_positions:
        pep_start = pose.chain_begin(peptide_chain_id)
        pep_end = pose.chain_end(peptide_chain_id)

        design_abs = set()
        for dp in design_positions:
            abs_idx = pep_start + dp - 1
            if abs_idx <= pep_end:
                design_abs.add(abs_idx)

        repack_only_indices = []
        for resi in range(pep_start, pep_end + 1):
            if resi not in design_abs:
                resname = pose.residue(resi).name3().strip()
                if resname != "CYS":
                    repack_only_indices.append(str(resi))

        if repack_only_indices:
            repack_selector = ResidueIndexSelector(",".join(repack_only_indices))
            tf.push_back(OperateOnResidueSubset(RestrictToRepackingRLT(), repack_selector))

        print(f"  TaskFactory: design={list(design_positions)} (abs={sorted(design_abs)}), "
              f"repack_only={repack_only_indices}, frozen=receptor+Cys")

    return tf


def fastdesign_candidates(input_pdb="standardized_relaxed.pdb", n=20,
                          design_pos=None, seed_base=1000, max_retries=3):
    """FastDesign으로 펩타이드 후보를 생성한다.

    Args:
        input_pdb: 입력 PDB (Chain A=receptor, Chain B=peptide)
        n: 생성할 후보 수
        design_pos: 설계 가능 위치 (str). None이면 Cys 자동 탐지하여 제외.
        seed_base: random seed 시작값
        max_retries: 중복 서열 발생 시 최대 재시도 횟수
    """
    import pyrosetta
    from pyrosetta.rosetta.numeric.random import rg as rosetta_rg
    from pyrosetta.rosetta.protocols.denovo_design.movers import FastDesign as _FastDesign

    base_pose = pyrosetta.pose_from_pdb(input_pdb)
    orig_seq = peptide_seq(base_pose, 2)

    if design_pos is None:
        design_positions = get_design_positions(orig_seq)
        cys_pos = find_cys_positions(orig_seq)
        print(f"  Auto-detected Cys at positions {cys_pos} -> excluded from design")
        print(f"  Design positions: {design_positions}")
    else:
        design_positions = [int(x.strip()) for x in design_pos.split(",") if x.strip()]
    allowed = set(design_positions)

    rows = []
    seen_seqs = set()
    duplicate_count = 0
    os.makedirs("candidates", exist_ok=True)

    t_total = time.time()
    timings = []

    pbar = tqdm(range(1, n + 1), desc="FastDesign", unit="candidate",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]")

    for k in pbar:
        t_start = time.time()
        new_seq = None

        for retry in range(max_retries + 1):
            seed = seed_base + k * 100 + retry
            rosetta_rg().set_seed(seed)

            pose = pyrosetta.pose_from_pdb(input_pdb)
            tf = build_task_factory(pose, peptide_chain_id=2, design_positions=allowed)
            fd = _FastDesign()
            fd.set_scorefxn(pyrosetta.get_score_function())
            fd.set_task_factory(tf)
            fd.apply(pose)

            new_seq = peptide_seq(pose, 2)

            if new_seq not in seen_seqs or retry == max_retries:
                if new_seq in seen_seqs:
                    duplicate_count += 1
                break

        seen_seqs.add(new_seq)

        diffs = diff_positions(orig_seq, new_seq)
        outside = [p for p in diffs if orig_seq[p - 1] == "C"]

        dG, dSASA = analyze_interface(pose)
        stab = stability_pk_proxy_scores(new_seq)

        out_name = f"candidate_{k:03d}.pdb"
        out_path = os.path.join("candidates", out_name)
        pose.dump_pdb(out_path)

        elapsed_k = time.time() - t_start
        timings.append(elapsed_k)
        avg_time = sum(timings) / len(timings)
        remaining_est = avg_time * (n - k)
        seq_dist = _hamming_distance(orig_seq, new_seq)

        pbar.set_postfix_str(
            f"#{k} {new_seq[:8]}... dG={dG:.1f} dist={seq_dist} | "
            f"{elapsed_k:.0f}s left~{remaining_est / 60:.1f}m"
        )

        rows.append({
            "candidate": out_name,
            "pdb_path": out_path,
            "seq": new_seq,
            "dG_REU": dG,
            "dSASA": dSASA,
            "mut_positions": diffs,
            "mut_outside_allowed": outside,
            "design_time_s": elapsed_k,
            "seq_distance": seq_dist,
            **stab,
        })

    total_elapsed = time.time() - t_total
    unique_count = len(set(r["seq"] for r in rows))
    print(f"\nFastDesign 완료: {n}개 후보, 총 {total_elapsed / 60:.1f}분 "
          f"(평균 {total_elapsed / n:.0f}s/후보)")
    print(f"  유일 서열: {unique_count}/{n}개 | 중복 재시도: {duplicate_count}회")

    df = pd.DataFrame(rows)
    df["rank_score"] = (-df["dG_REU"]) - 0.5 * df["cleavage_risk"] - 1.0 * df["pk_penalty"]
    df["is_unique"] = ~df["seq"].duplicated(keep="first")
    df = df.sort_values(["rank_score"], ascending=False).reset_index(drop=True)
    return df, orig_seq, design_positions


# ──────────────────────────────────────────────────────────────
# Filtering
# ──────────────────────────────────────────────────────────────

def is_cys_violation(x):
    """mut_outside_allowed에 값이 있으면 Cys 변이 발생 (위반)."""
    if isinstance(x, list):
        return len(x) > 0
    if isinstance(x, str):
        try:
            return len(_json.loads(x)) > 0
        except Exception:
            return bool(x.strip() and x.strip() != "[]")
    return False


def filter_candidates(df_candidates):
    """Cys 변이 후보를 필터링하여 (통과, 탈락) 반환."""
    df = df_candidates.copy()
    df["cys_violated"] = df["mut_outside_allowed"].apply(is_cys_violation)
    df_pass = df[~df["cys_violated"]].copy()
    df_fail = df[df["cys_violated"]].copy()

    unique_seqs = df_pass["seq"].nunique() if len(df_pass) > 0 else 0

    print(f"[필터링 결과] 전체 후보: {len(df)}")
    print(f"  - 통과(Cys 보존): {len(df_pass)} (유일 서열: {unique_seqs}개)")
    print(f"  - 탈락(Cys 변이): {len(df_fail)}")

    if "seq_distance" in df_pass.columns and len(df_pass) > 0:
        print(f"  - 원래 서열 대비 변이 수: 평균 {df_pass['seq_distance'].mean():.1f}, "
              f"범위 {df_pass['seq_distance'].min()}-{df_pass['seq_distance'].max()}")

    return df_pass, df_fail


# ──────────────────────────────────────────────────────────────
# FlexPepDock
# ──────────────────────────────────────────────────────────────

def flexpepdock_refine(df_in, topk=10):
    """FlexPepDock으로 상위 후보를 refine + 재스코어링."""
    import pyrosetta
    from pyrosetta.rosetta.protocols.flexpep_docking import FlexPepDockingProtocol

    os.makedirs("refined", exist_ok=True)
    rows = []
    top = df_in.head(topk)
    n_total = len(top)

    t_total = time.time()
    timings = []

    pbar = tqdm(top.iterrows(), total=n_total, desc="FlexPepDock Refine", unit="candidate",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]")

    for idx, (i, row) in enumerate(pbar, start=1):
        t_start = time.time()

        in_pdb = row["pdb_path"]
        pose = pyrosetta.pose_from_pdb(in_pdb)

        fpd = FlexPepDockingProtocol()
        fpd.apply(pose)

        dG, dSASA = analyze_interface(pose)
        seq = peptide_seq(pose, 2)
        stab = stability_pk_proxy_scores(seq)

        out_name = os.path.basename(row["candidate"]).replace("candidate_", "refined_")
        out_path = os.path.join("refined", out_name)
        pose.dump_pdb(out_path)

        elapsed_k = time.time() - t_start
        timings.append(elapsed_k)
        avg_time = sum(timings) / len(timings)
        remaining_est = avg_time * (n_total - idx)

        pbar.set_postfix_str(
            f"{row['candidate']} dG={dG:.1f} | {elapsed_k:.0f}s left~{remaining_est / 60:.1f}m"
        )

        rows.append({
            "input": row["candidate"],
            "input_pdb": in_pdb,
            "output": out_name,
            "pdb_path": out_path,
            "seq": seq,
            "dG_REU": dG,
            "dSASA": dSASA,
            **stab,
            "mut_outside_allowed": row.get("mut_outside_allowed", None),
            "refine_time_s": elapsed_k,
        })

    total_elapsed = time.time() - t_total
    if n_total > 0:
        print(f"\nFlexPepDock 완료: {n_total}개 후보, 총 {total_elapsed / 60:.1f}분 "
              f"(평균 {total_elapsed / n_total:.0f}s/후보)")

    df = pd.DataFrame(rows)
    if len(df) > 0:
        df["rank_score"] = (-df["dG_REU"]) - 0.5 * df["cleavage_risk"] - 1.0 * df["pk_penalty"]
        df = df.sort_values(["rank_score"], ascending=False).reset_index(drop=True)
    return df
