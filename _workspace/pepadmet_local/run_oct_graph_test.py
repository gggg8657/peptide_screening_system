"""Test SMILES -> DGL graph for octreotide variants."""
import sys

sys.path.insert(0, "pepADMET")
from utils.build_dataset import construct_RGCN_bigraph_from_smiles

smi_d = "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H](NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@H](N)Cc1ccccc1)[C@H](C)O)C(=O)O"
smi_l = "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H](NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@@H](N)Cc1ccccc1)[C@H](C)O)C(=O)O"

for name, smi in [("D-Phe+D-Trp", smi_d), ("L-Phe+D-Trp", smi_l)]:
    try:
        g = construct_RGCN_bigraph_from_smiles(smi)
        print(name, "graph OK nodes:", g.number_of_nodes(), "edges:", g.number_of_edges())
    except Exception as e:
        print(name, "FAILED", e)
