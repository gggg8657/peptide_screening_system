"""Compare GNN atom feature tensors between stereoisomer SMILES."""
import sys

sys.path.insert(0, "pepADMET")
from utils.build_dataset import construct_RGCN_bigraph_from_smiles
import torch

smi_d = "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H](NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@H](N)Cc1ccccc1)[C@H](C)O)C(=O)O"
smi_l = "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H](NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@@H](N)Cc1ccccc1)[C@H](C)O)C(=O)O"

gd = construct_RGCN_bigraph_from_smiles(smi_d)
gl = construct_RGCN_bigraph_from_smiles(smi_l)
ad = gd.ndata["atom"]
al = gl.ndata["atom"]
print("atom tensor equal?", torch.equal(ad, al))
print("max abs diff:", (ad.float() - al.float()).abs().max().item())
print("nodes", gd.number_of_nodes(), gl.number_of_nodes())
