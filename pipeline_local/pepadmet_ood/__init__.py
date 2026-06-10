"""pepadmet_ood — pepADMET OOD detection module.

Usage:
    from pipeline_local.pepadmet_ood.ood_detection import OODDetector

Note:
    Requires pepadmet-upgrade conda env (DGL, PyTorch) and
    pepADMET/utils/MY_GNN.py patched version (4 patches — see retrain_toxicity.py).
    Model checkpoint: _workspace/pepadmet_local/pepADMET/model/toxicity_retrained_2026-05-21.pth
    (stored locally, not tracked — 58MB; git LFS unavailable on this repo).

pepADMET 소스 복사 절차 (초기 설정 1회):
    cp pipeline_local/pepadmet_ood/ood_detection.py \
       _workspace/pepadmet_local/pepADMET/utils/ood_detection.py
"""
