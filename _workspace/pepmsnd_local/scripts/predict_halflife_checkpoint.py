#!/usr/bin/env python3
"""학습 체크포인트로 혈중 t½(시간) 단일 예측.

SMILES: 표준 대문자 서열은 RDKit MolFromSequence; 이황화 고리는 pyrosetta_flow.smiles_converter.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Batch
from torch_geometric.nn import GATConv, global_mean_pool
from torch_geometric.utils import from_smiles

WORKSPACE = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
KAERI = REPO_ROOT / "AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri"
if KAERI.is_dir() and str(KAERI) not in sys.path:
    sys.path.insert(0, str(KAERI))

try:
    from pyrosetta_flow.smiles_converter import sequence_to_smiles as ss_smiles
except Exception:
    ss_smiles = None  # type: ignore


class GATEmbedding(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, heads: int = 2) -> None:
        super().__init__()
        self.conv1 = GATConv(input_dim, hidden_dim, heads=heads)
        self.conv2 = GATConv(hidden_dim * heads, output_dim, heads=2, concat=False)

    def forward(self, x, edge_index, batch):
        out = F.relu(self.conv1(x, edge_index))
        out = self.conv2(out, edge_index)
        out = global_mean_pool(out, batch)
        return F.relu(out)


class HalfLifeGAT(nn.Module):
    def __init__(self, in_dim: int = 9) -> None:
        super().__init__()
        self.backbone = GATEmbedding(in_dim, 64, 128, heads=2)
        self.head = nn.Linear(128, 1)

    def forward(self, data):
        emb = self.backbone(data.x, data.edge_index, data.batch)
        return self.head(emb).squeeze(-1)


def seq_to_smiles(sequence: str, ss_bond: tuple[int, int] | None) -> str | None:
    seq = sequence.strip()
    if ss_smiles is not None and ss_bond is not None:
        s = ss_smiles(seq, ss_bond_positions=ss_bond)
        if s:
            return s
    try:
        from rdkit import Chem

        mol = Chem.MolFromSequence(seq.upper())
        if mol is None:
            return None
        return Chem.MolToSmiles(mol)
    except Exception:
        return None


def predict_one(
    ckpt_path: Path,
    sequence: str,
    ss_bond: tuple[int, int] | None,
    device: torch.device,
) -> dict:
    smi = seq_to_smiles(sequence, ss_bond)
    if not smi:
        return {"ok": False, "error": "SMILES_failed", "sequence": sequence}

    ck = torch.load(ckpt_path, map_location=device)
    in_dim = int(ck.get("in_dim", 9))
    model = HalfLifeGAT(in_dim=in_dim).to(device)
    model.load_state_dict(ck["model_state"])
    model.eval()

    g = from_smiles(smi)
    g.x = g.x.float()
    b = Batch.from_data_list([g]).to(device)
    with torch.no_grad():
        pred_log = model(b).item()
    hours = float(torch.expm1(torch.tensor(pred_log)).item())
    hours = max(1e-6, min(hours, 1e6))
    return {
        "ok": True,
        "sequence": sequence,
        "smiles": smi,
        "half_life_hours": hours,
        "pred_log1p": pred_log,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, default=WORKSPACE / "checkpoints/pepmsnd_peplife2_20260520_0723.pth")
    ap.add_argument("--sequence", type=str, required=True)
    ap.add_argument("--ss-bond", type=str, default="", help='예: "3,14" (1-indexed Cys-Cys)')
    args = ap.parse_args()

    ss: tuple[int, int] | None = None
    if args.ss_bond.strip():
        a, b = args.ss_bond.split(",")
        ss = (int(a), int(b))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = predict_one(args.checkpoint, args.sequence, ss, device)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
