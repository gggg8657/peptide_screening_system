from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MolMIMPort(Protocol):
    def generate(self, smi: str, num_molecules: int, **kwargs: Any) -> list[dict]: ...


@runtime_checkable
class DiffDockPort(Protocol):
    def dock_smiles(self, protein_pdb_path: Any, smiles: str, num_poses: int, **kwargs: Any) -> dict: ...


@runtime_checkable
class RFdiffusionPort(Protocol):
    def design_binder(self, pdb_path: Any, contigs: str, hotspot_res: list[str], **kwargs: Any) -> dict: ...


@runtime_checkable
class ProteinMPNNPort(Protocol):
    def predict(self, input_pdb: str, num_seq_per_target: int, **kwargs: Any) -> dict: ...
    def parse_fasta(self, raw: str) -> list[dict]: ...


@runtime_checkable
class ESMFoldPort(Protocol):
    def predict(self, sequence: str) -> dict: ...


@dataclass(frozen=True)
class NimClientBundle:
    molmim: MolMIMPort
    diffdock: DiffDockPort
    rfdiffusion: RFdiffusionPort
    proteinmpnn: ProteinMPNNPort
    esmfold: ESMFoldPort


def create_nim_bundle(api_key: str | None = None) -> NimClientBundle:
    """Construct real NIM clients from the bionemo package."""
    from bionemo.molmim_client import get_client as get_molmim
    from bionemo.diffdock_client import get_client as get_diffdock
    from bionemo.rfdiffusion_client import get_client as get_rfdiffusion
    from bionemo.proteinmpnn_client import get_client as get_proteinmpnn
    from bionemo.esmfold_client import get_client as get_esmfold

    kwargs = {"api_key": api_key} if api_key else {}
    return NimClientBundle(
        molmim=get_molmim(**kwargs),
        diffdock=get_diffdock(**kwargs),
        rfdiffusion=get_rfdiffusion(**kwargs),
        proteinmpnn=get_proteinmpnn(**kwargs),
        esmfold=get_esmfold(**kwargs),
    )
