"""Partial descriptors (PyMolecule + PyProtein only) to see D vs L sensitivity."""
import sys

sys.path.insert(0, "pepADMET")
from rdkit import Chem
from PyBioMed import Pymolecule
from PyBioMed.PyProtein import PyProtein
from collections import Counter


def calculate_des(seq):
    des = {}
    protein_class = PyProtein.PyProtein(seq)
    des.update(protein_class.GetAAComp())
    des.update(protein_class.GetMoreauBrotoAuto())
    des.update(protein_class.GetQSO())
    des.update(protein_class.GetSOCN())
    des.update(protein_class.GetTriad())
    des.update(protein_class.GetCTD())
    des.update(protein_class.GetDPComp())
    return des


def add_suffix_for_duplicates(dicts, sources):
    all_keys = []
    for d in dicts:
        all_keys.extend(d.keys())
    counter = Counter(all_keys)
    final_dict = {}
    for d, source in zip(dicts, sources):
        for k, v in d.items():
            new_key = f"{k}_{source}" if counter[k] > 1 else k
            final_dict[new_key] = v
    return final_dict


def partial_fp(smile_one, seq_one):
    mol = Pymolecule.PyMolecule()
    mol.ReadMolFromSmile(smile_one)
    fp_SM = mol.GetAllDescriptor()
    des = calculate_des(seq_one)
    return add_suffix_for_duplicates([fp_SM, des], ["Pymolecule", "PyProtein"])


smi_d = "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H](NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@H](N)Cc1ccccc1)[C@H](C)O)C(=O)O"
smi_l = "C[C@H](O)[C@H](NC(=O)[C@H](CS)NC(=O)[C@@H](NC(=O)[C@H](CCCCN)NC(=O)[C@@H](Cc1c[nH]c2ccccc12)NC(=O)[C@H](Cc1ccccc1)NC(=O)[C@H](CS)NC(=O)[C@@H](N)Cc1ccccc1)[C@H](C)O)C(=O)O"
seq = "FCFWKTCT"

fd = partial_fp(smi_d, seq)
fl = partial_fp(smi_l, seq)
diff_keys = []
for k in fd:
    if k not in fl:
        diff_keys.append((k, "missing L"))
        continue
    if fd[k] != fl[k]:
        diff_keys.append((k, fd[k], fl[k]))

print("partial descriptor keys:", len(fd))
print("keys with value differences:", sum(1 for x in diff_keys if len(x) == 3))
for row in diff_keys[:25]:
    print(row)
