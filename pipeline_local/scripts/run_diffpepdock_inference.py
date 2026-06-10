#!/usr/bin/env python3
"""
run_diffpepdock_inference.py
============================
DiffPepDock 추론 전용 스크립트 (postprocess 없음).

postprocess 모듈의 openmm/pdbfixer 의존성 문제를 우회하기 위해
run_docking.py 에서 postprocess 관련 코드를 제거한 최소 버전.

사용법:
    conda run -n diffpepbuilder \\
        CUDA_VISIBLE_DEVICES=2 BASE_PATH=<DiffPepBuilder root> \\
        python pipeline_local/scripts/run_diffpepdock_inference.py \\
            --metadata-csv runs_local/diffdock_poc/processed/metadata_test.csv \\
            --num-poses 10 \\
            --output-dir runs_local/diffdock_poc/docking_run
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# DiffPepBuilder root 설정
# ---------------------------------------------------------------------------

_DIFFPEP_ROOT = Path(os.environ.get(
    "BASE_PATH",
    "/home/dongjukim/Documents/workspace/repos/SST14-M_scr/local_models/DiffPepBuilder"
))

# sys.path에 DiffPepBuilder 추가
for p in [str(_DIFFPEP_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# pyrootutils로 root 설정 (DiffPepBuilder 내부 import 경로 해결)
import pyrootutils
root = pyrootutils.setup_root(
    search_from=str(_DIFFPEP_ROOT / "experiments"),
    indicator=[".git"],
    pythonpath=True,
    dotenv=True
)

# ---------------------------------------------------------------------------
# openmm/pdbfixer mock (import 체인 차단)
# analysis.amber_minimize → analysis.cleanup → pdbfixer → openmm 순으로 실패.
# sys.modules에 stub을 먼저 주입하여 실제 import를 차단한다.
# ---------------------------------------------------------------------------

import types
import sys as _sys

def _make_stub_module(name: str) -> types.ModuleType:
    """빈 모듈 stub 생성."""
    m = types.ModuleType(name)
    _sys.modules[name] = m
    return m


# openmm 전체를 stub으로 대체
for _mod_name in [
    "openmm", "openmm.unit", "openmm.app",
    "openmm.app.internal", "openmm.app.internal.pdbstructure",
    "pdbfixer",
]:
    if _mod_name not in _sys.modules:
        _m = _make_stub_module(_mod_name)
        # openmm.app.PDBFile stub
        if _mod_name == "openmm.app":
            _m.PDBFile = object
            _m.ForceField = object
            _m.Modeller = object
            _m.Simulation = object
        elif _mod_name == "openmm.unit":
            # unit.kilocalorie_per_mole 등 속성 접근 방어
            class _UnitStub:
                def __getattr__(self, _k):
                    return object()
            _m.__class__ = type(_m)
            _m.kilocalories_per_mole = None
            _m.angstrom = None
        elif _mod_name == "pdbfixer":
            _m.PDBFixer = object

# analysis.cleanup stub
if "analysis.cleanup" not in _sys.modules:
    _cleanup = _make_stub_module("analysis.cleanup")
    _cleanup.fix_pdb = lambda *a, **kw: None
    _cleanup.clean_structure = lambda *a, **kw: None

# analysis.amber_minimize stub
if "analysis.amber_minimize" not in _sys.modules:
    _amber = _make_stub_module("analysis.amber_minimize")
    class _AmberRelaxation:
        def __init__(self, *a, **kw): pass
        def process(self, *a, **kw): return "", [], []
    _amber.AmberRelaxation = _AmberRelaxation

# analysis.postprocess stub
if "analysis.postprocess" not in _sys.modules:
    _pp = _make_stub_module("analysis.postprocess")
    class _Postprocess:
        def __init__(self, *a, **kw): pass
        def run(self, *a, **kw): pass
    _pp.Postprocess = _Postprocess

# analysis.postprocess_utils stub
if "analysis.postprocess_utils" not in _sys.modules:
    _ppu = _make_stub_module("analysis.postprocess_utils")
    class _PCLIO:
        def __init__(self, *a, **kw): pass
    _ppu.PCLIO = _PCLIO
    _ppu.summarize_statistics = lambda *a, **kw: {}

# ---------------------------------------------------------------------------
# 필수 import (postprocess 제외)
# ---------------------------------------------------------------------------

import tree
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from openfold.utils import rigid_utils

from analysis import utils as au
from data import utils as du
from data import residue_constants
from data.pdb_data_loader import PdbDataset
from experiments.train import Experiment

# ---------------------------------------------------------------------------
# postprocess mock (postprocess.run_postprocess=False 경우 사용)
# ---------------------------------------------------------------------------


class _MockPostprocess:
    """postprocess 모듈 없이 실행하기 위한 stub."""
    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs) -> None:
        pass


# ---------------------------------------------------------------------------
# BatchDockDataset (run_docking.py에서 복사)
# ---------------------------------------------------------------------------


class BatchDockDataset(PdbDataset):
    def __init__(self, *, data_conf, diffuser):
        super().__init__(data_conf=data_conf, diffuser=diffuser, is_training=False)

    def sample_init_peptide(self, peptide_seq: str):
        sample_length = len(peptide_seq)
        res_mask = np.ones(sample_length)
        fixed_mask = np.zeros_like(res_mask)
        ref_sample = self.diffuser.sample_ref(n_samples=sample_length, as_tensor_7=True)
        aatype = np.array([
            residue_constants.restype_order.get(res, residue_constants.restype_num)
            for res in peptide_seq
        ])
        init_feats = {
            "aatype": aatype,
            "res_mask": res_mask,
            "fixed_mask": fixed_mask,
            "torsion_angles_sin_cos": np.zeros((sample_length, 7, 2)),
            "sc_ca_t": np.zeros((sample_length, 3)),
            **ref_sample,
        }
        init_feats = tree.map_structure(
            lambda x: x if torch.is_tensor(x) else torch.tensor(x), init_feats
        )
        return init_feats

    def process_receptor(self, raw_feats):
        bb_rigid = rigid_utils.Rigid.from_tensor_4x4(raw_feats["rigidgroups_0"])[:, 0]
        fixed_mask = np.ones_like(raw_feats["ligand_mask"])
        rigids_0 = bb_rigid.to_tensor_7()
        sc_ca_t = torch.zeros_like(bb_rigid.get_trans())
        receptor_feats = {
            "aatype": raw_feats["aatype"],
            "res_mask": raw_feats["res_mask"],
            "fixed_mask": fixed_mask,
            "torsion_angles_sin_cos": raw_feats["torsion_angles_sin_cos"],
            "sc_ca_t": sc_ca_t,
            "rigids_t": rigids_0,
        }
        receptor_feats = tree.map_structure(
            lambda x: x if torch.is_tensor(x) else torch.tensor(x), receptor_feats
        )
        return receptor_feats

    def __len__(self):
        return len(self.csv)

    def __getitem__(self, idx):
        csv_row = self.csv.iloc[idx]
        pdb_name = csv_row["pdb_name"]
        peptide_id = csv_row["peptide_id"]
        processed_file_path = csv_row["processed_path"]
        raw_feats = self._process_csv_row(processed_file_path)

        peptide_seq = csv_row["peptide_seq"]
        peptide_len = len(peptide_seq)
        peptide_feats = self.sample_init_peptide(peptide_seq)
        receptor_feats = self.process_receptor(raw_feats)

        final_feats = tree.map_structure(
            lambda pf, rf: torch.cat((pf, rf), dim=0),
            peptide_feats, receptor_feats
        )

        coordinate_bias = raw_feats["coordinate_bias"]
        new_coordinate_bias = np.concatenate(
            [coordinate_bias, np.tile(coordinate_bias[-1], (peptide_len, 1))], axis=0
        )
        final_feats["coordinate_bias"] = torch.tensor(new_coordinate_bias)

        receptor_chain_idx = raw_feats["chain_idx"]
        receptor_seq_idx = raw_feats["seq_idx"]
        peptide_chain_idx = np.zeros(peptide_len, dtype=int)
        peptide_seq_idx = np.arange(1, peptide_len + 1)

        unique_chain_idx = np.unique(receptor_chain_idx)
        chain_idx_mapping = {
            old_idx: new_idx for new_idx, old_idx in enumerate(unique_chain_idx, start=1)
        }
        new_receptor_chain_idx = np.vectorize(chain_idx_mapping.get)(receptor_chain_idx)
        new_receptor_seq_idx = receptor_seq_idx + peptide_len + 100

        chain_idx = np.concatenate([peptide_chain_idx, new_receptor_chain_idx])
        seq_idx = np.concatenate([peptide_seq_idx, new_receptor_seq_idx])

        final_feats["chain_idx"] = torch.tensor(chain_idx)
        final_feats["seq_idx"] = torch.tensor(seq_idx)

        esm_embed = du.read_pkl(processed_file_path)["esm_embed"]
        assert esm_embed.shape[0] == seq_idx.shape[0]
        final_feats["esm_embed"] = torch.tensor(esm_embed)

        final_feats = du.pad_feats(final_feats, csv_row["modeled_seq_len"])
        return final_feats, pdb_name, peptide_id


class EvalRepeatLengthSampler(torch.utils.data.Sampler):
    def __init__(self, *, dataset, num_repeat: int, batch_size: int,
                 world_size: int = 1, rank: int = 0, shuffle: bool = False):
        self.dataset = dataset
        self.csv = getattr(dataset, "csv", None)
        assert self.csv is not None
        self.num_repeat = int(num_repeat)
        self.batch_size = int(batch_size)
        self.world_size = int(world_size)
        self.rank = int(rank)
        self.shuffle = bool(shuffle)

        if "modeled_seq_len" in self.csv.columns:
            by_len = {}
            for idx in range(len(self.csv)):
                L = int(self.csv.iloc[idx]["modeled_seq_len"])
                by_len.setdefault(L, []).append(idx)
        else:
            by_len = {0: list(range(len(self.csv)))}

        if self.shuffle:
            import random
            rng = random.Random(0)
            for L in by_len:
                rng.shuffle(by_len[L])

        for L, lst in by_len.items():
            by_len[L] = [lst[i] for i in range(self.rank, len(lst), self.world_size)]

        batches = []
        for L in sorted(by_len.keys()):
            stream = []
            for idx in by_len[L]:
                stream.extend([idx] * self.num_repeat)
            p = 0
            N = len(stream)
            while p < N:
                q = min(p + self.batch_size, N)
                batches.append(stream[p:q])
                p = q
        self._batches = batches

    def __iter__(self):
        for b in self._batches:
            yield b

    def __len__(self):
        return len(self._batches)


# ---------------------------------------------------------------------------
# 추론 실행
# ---------------------------------------------------------------------------


def run_inference(
    metadata_csv: str,
    output_dir: str,
    num_poses: int = 10,
    gpu_id: int = 0,
) -> list:
    """
    DiffPepDock 추론 실행 (postprocess 없음).

    Returns
    -------
    list of saved PDB paths
    """
    from omegaconf import OmegaConf

    checkpoint_path = str(_DIFFPEP_ROOT / "experiments" / "checkpoints" / "diffpepdock_v1.pth")

    # Hydra config 수동 구성 (docking.yaml 기반)
    conf = OmegaConf.load(str(_DIFFPEP_ROOT / "config" / "docking.yaml"))

    # base, eval yaml merge
    base_conf = OmegaConf.load(str(_DIFFPEP_ROOT / "config" / "base.yaml"))
    eval_conf = OmegaConf.load(str(_DIFFPEP_ROOT / "config" / "eval.yaml"))

    # 순서: base → eval → docking → override
    merged = OmegaConf.merge(base_conf, eval_conf, conf)

    # PoC override
    merged.data.val_csv_path = metadata_csv
    merged.data.num_repeat_per_eval_sample = num_poses
    merged.data.min_t = 0.01
    merged.data.num_t = 200
    merged.data.mask_lig_seq = False
    merged.data.center_pos_noise = True
    merged.data.center_pos_noise_std = 5.0
    merged.experiment.name = "docking"
    merged.experiment.eval_batch_size = num_poses
    merged.experiment.num_loader_workers = 2
    merged.experiment.use_ddp = False
    merged.experiment.use_gpu = True
    merged.experiment.num_gpus = 1
    merged.experiment.eval_ckpt_path = checkpoint_path
    merged.experiment.eval_dir = output_dir
    merged.experiment.noise_scale = 1.0
    merged.experiment.flip_align = False
    merged.experiment.save_traj = False
    merged.postprocess.run_postprocess = False

    os.makedirs(output_dir, exist_ok=True)

    exp = Experiment(conf=merged)
    device = f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu"
    exp._model = exp.model.to(device)
    exp._model.eval()

    test_dataset = BatchDockDataset(
        data_conf=merged.data,
        diffuser=exp._diffuser
    )

    per_gpu_bs = merged.experiment.eval_batch_size
    num_repeat = merged.data.get("num_repeat_per_eval_sample", 1)

    eval_batch_sampler = EvalRepeatLengthSampler(
        dataset=test_dataset,
        num_repeat=num_repeat,
        batch_size=per_gpu_bs,
        world_size=1,
        rank=0,
        shuffle=False,
    )

    test_loader = du.create_data_loader(
        test_dataset,
        sampler=None,
        batch_size=None,
        shuffle=False,
        num_workers=merged.experiment.num_loader_workers,
        np_collate=False,
        length_batch=False,
        drop_last=False,
        batch_sampler=eval_batch_sampler
    )

    per_target_sample_ctr: dict = defaultdict(int)
    saved_paths = []

    for test_feats, pdb_names, peptide_ids in test_loader:
        res_mask = du.move_to_np(test_feats["res_mask"].bool())
        fixed_mask = du.move_to_np(test_feats["fixed_mask"].bool())
        gt_aatype = du.move_to_np(test_feats["aatype"])
        seq_idx = du.move_to_np(test_feats["seq_idx"])
        chain_idx = du.move_to_np(test_feats["chain_idx"])
        coordinate_bias = du.move_to_np(test_feats["coordinate_bias"])
        batch_size = res_mask.shape[0]

        test_feats = tree.map_structure(lambda x: x.to(device), test_feats)

        infer_out = exp.inference_fn(
            data_init=test_feats,
            num_t=merged.data.num_t,
            min_t=merged.data.min_t,
            aux_traj=False,
            noise_scale=merged.experiment.noise_scale
        )

        final_prot = infer_out["prot_traj"][0]

        for i in range(batch_size):
            pdb_name = pdb_names[i]
            peptide_id = peptide_ids[i]
            unpad_seq_idx = seq_idx[i][res_mask[i]]
            unpad_chain_idx = chain_idx[i][res_mask[i]]
            unpad_fixed_mask = fixed_mask[i][res_mask[i]]
            unpad_prot = final_prot[i][res_mask[i]]
            unpad_gt_aatype = gt_aatype[i][res_mask[i]]
            unpad_coordinate_bias = coordinate_bias[i][res_mask[i]]

            peptide_seq_dir = os.path.join(output_dir, pdb_name, peptide_id)
            os.makedirs(peptide_seq_dir, exist_ok=True)

            sample_id = per_target_sample_ctr[(pdb_name, peptide_id)]
            per_target_sample_ctr[(pdb_name, peptide_id)] += 1

            pdb_out = os.path.join(
                peptide_seq_dir,
                f"{pdb_name}_{peptide_id}_sample_{sample_id:03d}.pdb"
            )
            b_factors = np.tile(1 - unpad_fixed_mask[..., None], 37) * 100

            saved_path = au.write_prot_to_pdb(
                unpad_prot,
                pdb_out,
                coordinate_bias=unpad_coordinate_bias,
                aatype=unpad_gt_aatype,
                residue_index=unpad_seq_idx,
                chain_index=unpad_chain_idx,
                no_indexing=True,
                b_factors=b_factors,
            )
            print(f"[DiffPepDock] Saved pose {sample_id}: {saved_path}")
            saved_paths.append(saved_path)

    return saved_paths


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DiffPepDock inference without postprocessing")
    p.add_argument(
        "--metadata-csv", type=str,
        default="/home/dongjukim/Documents/workspace/repos/SST14-M_scr/runs_local/diffdock_poc/processed/metadata_test.csv"
    )
    p.add_argument("--num-poses", type=int, default=10)
    p.add_argument("--output-dir", type=str,
                   default="/home/dongjukim/Documents/workspace/repos/SST14-M_scr/runs_local/diffdock_poc/docking_run")
    p.add_argument("--gpu-id", type=int, default=0)
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    start = time.time()
    paths = run_inference(
        metadata_csv=args.metadata_csv,
        output_dir=args.output_dir,
        num_poses=args.num_poses,
        gpu_id=args.gpu_id,
    )
    elapsed = time.time() - start
    print(f"\n[DiffPepDock] Done: {len(paths)} poses in {elapsed:.1f}s")
    print(f"[DiffPepDock] Poses saved to: {args.output_dir}")
