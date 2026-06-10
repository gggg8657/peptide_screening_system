import pandas as pd

tox_path = "pepADMET/data/Toxicity.csv"
ex_path = "pepADMET/data/example_feature_result.csv"
tox = pd.read_csv(tox_path, nrows=1)
ex = pd.read_csv(ex_path, nrows=1)
tox_desc_cols = list(tox.columns[6:])
ex_cols = set(ex.columns)
print("Toxicity n descriptor cols:", len(tox_desc_cols))
print("example_feature_result cols:", len(ex_cols))
missing = [c for c in tox_desc_cols if c not in ex_cols]
extra = [
    c
    for c in ex_cols
    if c not in tox_desc_cols and c not in ("SMILES", "SEQUENCE", "Error")
]
print("tox descriptors missing from example calc:", len(missing))
print("sample missing:", missing[:20])
print("extra in example not in tox:", len(extra))
print("sample extra:", list(extra)[:20])
