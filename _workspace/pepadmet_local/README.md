# pepADMET local setup

This directory keeps the local pepADMET clone, reproducibility notes, and small maintenance scripts used for the `pepadmet` conda environment.

## Install flow

1. Clone pepADMET into this workspace.

   ```bash
   git clone https://github.com/ifyoungnet/pepADMET.git _workspace/pepadmet_local/pepADMET
   ```

2. Create or restore the conda environment named `pepadmet`.

   The upstream `requirements` file pins Python 3.7.16, DGL 0.4.3, PyBioMed 1.0, RDKit 2020.09.1.0, modlamp 4.3.0, torch 1.13.1, and related packages. Keep the environment name as `pepadmet`; the patch script refuses to edit any other env.

3. Apply the PyBioMed `estate.py` compatibility patch.

   ```bash
   bash _workspace/pepadmet_local/scripts/apply_estate_patch.sh
   ```

   To also run the pepADMET sample descriptor generation:

   ```bash
   bash _workspace/pepadmet_local/scripts/apply_estate_patch.sh --verify
   ```

   To preview the detected env, target file, and intended actions without changing files:

   ```bash
   bash _workspace/pepadmet_local/scripts/apply_estate_patch.sh --dry-run
   ```

## PyBioMed estate.py patch

The local `pepadmet` env previously failed in PyBioMed when RDKit returned a C++ vector wrapper from `EState.Fingerprinter.FingerprintMol()`. PyBioMed called Python `round()` directly on that value:

```python
round(j, 3)
```

The local compatibility patch converts the value first:

```python
round(float(j), 3)
```

The script is idempotent. If `round(float(j), 3)` is already present, it exits without editing. If the file is unpatched, it creates a timestamped backup such as `estate.py.bak.20260520_024200`, applies the `sed` replacement, and verifies the patched line with `grep`.

Patch rationale and environment investigation are documented in:

- `docs/meet_log/2026-04-06_action_items/A-03_research_pepadmet_environment.md`
- `_workspace/pepadmet_local/V02-V03_patch_estate_2026-05-20.md`

Patch logs are appended to:

```text
_workspace/pepadmet_local/apply_estate_patch.log
```
