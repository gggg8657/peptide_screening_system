"""Single-molecule descriptor test for pepADMET calculate_descriptors."""
import sys

sys.path.insert(0, "pepADMET")
from calculate_descriptors import calculate_descriptors

smi_d = "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H](NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@H](N)Cc1ccccc1)[C@H](C)O)C(=O)O"
smi_l = "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H](NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@@H](N)Cc1ccccc1)[C@H](C)O)C(=O)O"
seq = "FCFWKTCT"

for name, smi in [("D-Phe+D-Trp", smi_d), ("L-Phe+D-Trp", smi_l)]:
    r = calculate_descriptors((smi, seq))
    print("===", name, "===")
    if "Error" in r:
        print("Error:", r["Error"][:500])
    else:
        print("OK keys:", len(r))
        print("sample keys:", list(r.keys())[:8])
