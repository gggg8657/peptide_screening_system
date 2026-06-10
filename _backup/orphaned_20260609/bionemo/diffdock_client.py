"""
DiffDock API Client
====================
NVIDIA 호스팅 API를 통한 분자 도킹.
단백질 PDB + 리간드 SDF → 도킹 포즈 예측.

사용법:
    from diffdock_client import DiffDockClient
    client = DiffDockClient()
    poses = client.dock_smiles("sstr2.pdb", "CCO")
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
try:
    from .api_base import NVIDIABaseClient
except ImportError:
    from api_base import NVIDIABaseClient

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


class DiffDockClient(NVIDIABaseClient):
    """DiffDock NIM API 클라이언트"""

    BASE_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"

    def dock(
        self,
        protein_pdb: str,
        ligand_sdf: str,
        num_poses: int = 10,
        time_divisions: int = 20,
        steps: int = 18,
    ) -> dict:
        """
        단백질-리간드 도킹

        Args:
            protein_pdb: 단백질 PDB 파일 내용 (문자열)
            ligand_sdf: 리간드 SDF 파일 내용 (문자열)
            num_poses: 생성할 포즈 수
            time_divisions: 확산 시간 분할
            steps: 확산 스텝 수

        Returns:
            {"output": [{"pose_pdb": "...", "confidence": float}, ...]}
        """
        payload = {
            "ligand": ligand_sdf,
            "ligand_file_type": "sdf",
            "protein": protein_pdb,
            "num_poses": num_poses,
            "time_divisions": time_divisions,
            "steps": steps,
            "save_trajectory": False,
            "is_staged": False,
        }
        return self._post("", payload, timeout=300)

    def dock_from_files(
        self,
        protein_pdb_path: str | Path,
        ligand_sdf_path: str | Path,
        num_poses: int = 10,
    ) -> dict:
        """파일 경로로 도킹"""
        protein_pdb = Path(protein_pdb_path).read_text()
        ligand_sdf = Path(ligand_sdf_path).read_text()
        return self.dock(protein_pdb, ligand_sdf, num_poses=num_poses)

    def dock_smiles(
        self,
        protein_pdb_path: str | Path,
        smiles: str,
        num_poses: int = 10,
    ) -> dict:
        """SMILES 문자열로 도킹 (RDKit로 SDF 변환)"""
        if not HAS_RDKIT:
            raise ImportError("RDKit가 필요합니다: conda install -c conda-forge rdkit")

        sdf_content = self._smiles_to_sdf(smiles)
        protein_pdb = Path(protein_pdb_path).read_text()
        return self.dock(protein_pdb, sdf_content, num_poses=num_poses)

    @staticmethod
    def _smiles_to_sdf(smiles: str) -> str:
        """SMILES → SDF 문자열 변환"""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"유효하지 않은 SMILES: {smiles}")
        mol = Chem.AddHs(mol)
        embed_status = AllChem.EmbedMolecule(mol, randomSeed=42)
        if embed_status != 0:
            raise RuntimeError(f"RDKit 좌표 생성 실패 (status={embed_status}): {smiles}")
        optimize_status = AllChem.MMFFOptimizeMolecule(mol)
        if optimize_status not in (0, 1):
            raise RuntimeError(f"RDKit 최적화 실패 (status={optimize_status}): {smiles}")

        with tempfile.NamedTemporaryFile(suffix=".sdf", mode="w", delete=False) as f:
            tmp_path = f.name
        try:
            writer = Chem.SDWriter(tmp_path)
            writer.write(mol)
            writer.close()
            return Path(tmp_path).read_text()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def dock_multiple_smiles(
        self,
        protein_pdb_path: str | Path,
        smiles_list: list[str],
        num_poses: int = 5,
    ) -> list[dict]:
        """여러 SMILES 배치 도킹"""
        results = []
        protein_pdb = Path(protein_pdb_path).read_text()

        for i, smi in enumerate(smiles_list):
            print(f"  [{i+1}/{len(smiles_list)}] Docking {smi[:50]}...")
            try:
                sdf = self._smiles_to_sdf(smi)
                result = self.dock(protein_pdb, sdf, num_poses=num_poses)
                result["smiles"] = smi
                results.append(result)
            except Exception as e:
                print(f"    오류: {e}")
                results.append({"smiles": smi, "error": str(e)})

        return results


def get_client(**kwargs) -> DiffDockClient:
    """기본 설정으로 DiffDock 클라이언트 생성"""
    return DiffDockClient(**kwargs)


if __name__ == "__main__":
    client = get_client()
    print("DiffDock Client initialized")
    print(f"  Base URL: {client.base_url}")
    print(f"  API Key:  {'***' + client.api_key[-8:] if client.api_key else 'NOT SET'}")
