"""
ProteinMPNN API Client
=======================
NVIDIA 호스팅 API를 통한 역접힘(inverse folding) -- 백본 구조 → 최적 서열.

사용법:
    from proteinmpnn_client import ProteinMPNNClient
    client = ProteinMPNNClient()
    sequences = client.predict("backbone.pdb")
"""

from pathlib import Path
from typing import Optional
try:
    from .api_base import NVIDIABaseClient
except ImportError:
    from api_base import NVIDIABaseClient


class ProteinMPNNClient(NVIDIABaseClient):
    """ProteinMPNN NIM API 클라이언트"""

    BASE_URL = "https://health.api.nvidia.com/v1/biology/ipd/proteinmpnn"

    def predict(
        self,
        input_pdb: str,
        num_seq_per_target: int = 8,
        sampling_temp: float = 0.2,
        ca_only: bool = False,
        use_soluble_model: bool = True,
    ) -> dict:
        """
        백본 구조 → 최적 아미노산 서열 예측

        Args:
            input_pdb: 입력 PDB 파일 내용 (문자열)
            num_seq_per_target: 타겟당 생성 서열 수
            sampling_temp: 샘플링 온도 (0-1, 낮을수록 보수적)
            ca_only: Cα 원자만 사용 여부
            use_soluble_model: 수용성 모델 사용 여부

        Returns:
            {"sequences": ["MKIT...", ...]}  (Multi-FASTA 형식)
        """
        # sampling_temp은 리스트 형태로 전달 필요
        if isinstance(sampling_temp, (int, float)):
            sampling_temp = [sampling_temp]
        payload = {
            "input_pdb": input_pdb,
            "num_seq_per_target": num_seq_per_target,
            "sampling_temp": sampling_temp,
            "ca_only": ca_only,
            "use_soluble_model": use_soluble_model,
        }
        return self._post("predict", payload, timeout=120)

    def predict_from_file(
        self,
        pdb_path: str | Path,
        num_seq_per_target: int = 8,
        sampling_temp: float = 0.2,
    ) -> dict:
        """파일 경로로 서열 예측"""
        pdb_content = Path(pdb_path).read_text()
        return self.predict(
            input_pdb=pdb_content,
            num_seq_per_target=num_seq_per_target,
            sampling_temp=sampling_temp,
        )

    @staticmethod
    def parse_fasta(fasta_text: str) -> list[dict]:
        """FASTA 텍스트를 파싱하여 리스트 반환"""
        entries = []
        current_header = None
        current_seq = []

        for line in fasta_text.strip().split("\n"):
            if line.startswith(">"):
                if current_header is not None:
                    entries.append({
                        "header": current_header,
                        "sequence": "".join(current_seq),
                    })
                current_header = line[1:].strip()
                current_seq = []
            else:
                current_seq.append(line.strip())

        if current_header is not None:
            entries.append({
                "header": current_header,
                "sequence": "".join(current_seq),
            })

        return entries


def get_client(**kwargs) -> ProteinMPNNClient:
    return ProteinMPNNClient(**kwargs)


if __name__ == "__main__":
    client = get_client()
    print("ProteinMPNN Client initialized")
    print(f"  Base URL: {client.base_url}")
    print(f"  API Key:  {'***' + client.api_key[-8:] if client.api_key else 'NOT SET'}")
