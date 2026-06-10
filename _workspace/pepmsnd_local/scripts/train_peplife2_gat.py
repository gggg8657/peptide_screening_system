#!/usr/bin/env python3
"""PEPlife2 필터링 CSV 기반 GAT 회귀 (PyG from_smiles; DGL 미사용).

공식 PepMSND fusion(model.py)과는 별개 — 연속 t½ 예측을 위해 동일 GAT 백본(PepMSND/Models/GAT.py)만 차용.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import r2_score
from scipy.stats import spearmanr
from torch.utils.data import Dataset, DataLoader
from torch_geometric.data import Batch, Data
from torch_geometric.nn import GATConv, global_mean_pool
from torch_geometric.utils import from_smiles

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "peplife2_processed"
CKPT_DIR = ROOT / "checkpoints"
LOG_PATH = ROOT / "training.log"


class GATEmbedding(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, heads: int = 2) -> None:
        super().__init__()
        self.conv1 = GATConv(input_dim, hidden_dim, heads=heads)
        self.conv2 = GATConv(hidden_dim * heads, output_dim, heads=2, concat=False)

    def forward(self, x, edge_index, batch):
        out = F.relu(self.conv1(x, edge_index))
        out = F.dropout(out, p=0.2, training=self.training)
        out = self.conv2(out, edge_index)
        out = global_mean_pool(out, batch)
        return F.relu(out)


class HalfLifeGAT(nn.Module):
    def __init__(self, in_dim: int = 9) -> None:
        super().__init__()
        self.backbone = GATEmbedding(in_dim, 64, 128, heads=2)
        self.head = nn.Linear(128, 1)

    def forward(self, data: Data) -> torch.Tensor:
        emb = self.backbone(data.x, data.edge_index, data.batch)
        return self.head(emb).squeeze(-1)


class GraphCSV(Dataset):
    def __init__(self, csv_path: Path) -> None:
        self.df = pd.read_csv(csv_path)
        self.graphs: list[Data] = []
        self.targets: list[float] = []
        bad = 0
        for _, row in self.df.iterrows():
            try:
                g = from_smiles(str(row["smiles"]))
                g.x = g.x.float()
            except Exception:
                bad += 1
                continue
            y = float(row["half_life_hours"])
            if y <= 0:
                bad += 1
                continue
            g.y = torch.tensor([np.log1p(y)], dtype=torch.float32)
            self.graphs.append(g)
            self.targets.append(y)
        self.dropped = bad

    def __len__(self) -> int:
        return len(self.graphs)

    def __getitem__(self, i: int) -> Data:
        return self.graphs[i]


def collate(batch: list[Data]) -> Batch:
    return Batch.from_data_list(batch)


def metrics_hours(y_true: np.ndarray, y_pred_log1p: np.ndarray) -> dict:
    pred_h = np.expm1(np.clip(y_pred_log1p, -10, 20))
    pred_h = np.clip(pred_h, 1e-6, 1e6)
    r2 = r2_score(y_true, pred_h)
    rho, _ = spearmanr(y_true, pred_h)
    mae = float(np.mean(np.abs(y_true - pred_h)))
    return {"r2_hours": float(r2) if not np.isnan(r2) else None, "spearman": float(rho) if rho == rho else None, "mae_hours": mae}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_csv", type=Path, default=PROC / "train.csv")
    ap.add_argument("--val_csv", type=Path, default=PROC / "val.csv")
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--test_csv", type=Path, default=PROC / "test.csv")
    ap.add_argument("--skip_test", action="store_true")
    ap.add_argument(
        "--output",
        type=Path,
        default=CKPT_DIR / "pepmsnd_peplife2_20260520_0723.pth",
    )
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.cuda.empty_cache()

    ds_tr = GraphCSV(args.train_csv)
    ds_va = GraphCSV(args.val_csv)
    print(f"train_rows={len(ds_tr)} dropped_smiles={ds_tr.dropped}", file=sys.stderr)
    print(f"val_rows={len(ds_va)} dropped_smiles={ds_va.dropped}", file=sys.stderr)

    in_dim = int(ds_tr[0].x.shape[1]) if len(ds_tr) else 9
    model = HalfLifeGAT(in_dim=in_dim).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
    crit = nn.MSELoss()

    tr_loader = DataLoader(ds_tr, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    va_loader = DataLoader(ds_va, batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    best_val = float("inf")
    best_state = None
    stall = 0
    t0 = time.time()

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line)
        with LOG_PATH.open("a") as f:
            f.write(line + "\n")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("")
    log(f"device={device} train_n={len(ds_tr)} val_n={len(ds_va)}")

    for epoch in range(1, args.epochs + 1):
        model.train()
        tr_loss = 0.0
        for batch in tr_loader:
            batch = batch.to(device)
            opt.zero_grad()
            pred = model(batch)
            loss = crit(pred, batch.y.squeeze())
            loss.backward()
            opt.step()
            tr_loss += loss.item()
        tr_loss /= max(len(tr_loader), 1)

        model.eval()
        val_loss = 0.0
        va_true_h: list[float] = []
        va_pred_log: list[float] = []
        with torch.no_grad():
            for batch in va_loader:
                batch = batch.to(device)
                pred = model(batch)
                loss = crit(pred, batch.y.squeeze())
                val_loss += loss.item()
                va_true_h.extend(torch.expm1(batch.y.squeeze()).cpu().numpy().tolist())
                va_pred_log.extend(pred.cpu().numpy().tolist())
        val_loss /= max(len(va_loader), 1)

        m = metrics_hours(np.array(va_true_h), np.array(va_pred_log))
        # log-space R² (모형이 직접 맞추는 척도)
        r2_log = r2_score(np.log1p(va_true_h), np.array(va_pred_log))

        log(
            f"epoch={epoch} train_loss={tr_loss:.4f} val_loss={val_loss:.4f} "
            f"val_R2log={r2_log:.4f} val_R2h={m['r2_hours']} val_rho={m['spearman']} val_mae_h={m['mae_hours']:.4f}"
        )

        if val_loss < best_val - 1e-6:
            best_val = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            stall = 0
        else:
            stall += 1
            if stall >= args.patience:
                log(f"early_stop epoch={epoch}")
                break

    elapsed = time.time() - t0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if best_state:
        model.load_state_dict(best_state)
    payload = {
        "model_state": model.state_dict(),
        "in_dim": in_dim,
        "meta": {
            "train_csv": str(args.train_csv),
            "val_csv": str(args.val_csv),
            "elapsed_sec": elapsed,
            "best_val_loss": best_val,
        },
    }

    if args.test_csv.exists() and not args.skip_test:
        ds_te = GraphCSV(args.test_csv)
        te_loader = DataLoader(ds_te, batch_size=args.batch_size, shuffle=False, collate_fn=collate)
        model.eval()
        te_h: list[float] = []
        te_pred: list[float] = []
        with torch.no_grad():
            for batch in te_loader:
                batch = batch.to(device)
                pred = model(batch)
                te_h.extend(torch.expm1(batch.y.squeeze()).cpu().numpy().tolist())
                te_pred.extend(pred.cpu().numpy().tolist())
        tm = metrics_hours(np.array(te_h), np.array(te_pred))
        payload["test_metrics_hours"] = tm
        log(f"test_metrics={json.dumps(tm)}")

    torch.save(payload, args.output)
    log(f"checkpoint_saved={args.output} elapsed_sec={elapsed:.1f}")


if __name__ == "__main__":
    main()
