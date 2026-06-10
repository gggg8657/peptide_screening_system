"""
MolMIM API Client
=================
NVIDIA API Catalog (build.nvidia.com) 또는 Self-hosted NIM에 접속하는 클라이언트.
GPU 불필요 -- HTTP 요청만 보냄.

사용법:
    from molmim_client import MolMIMClient
    client = MolMIMClient()  # .env 또는 ngc.key에서 키 자동 로드
    emb = client.embedding("CCO")
"""

import os
import json
import requests
from typing import Optional

try:
    from .api_base import NVIDIABaseClient
except ImportError:
    from api_base import NVIDIABaseClient


class MolMIMClient(NVIDIABaseClient):
    """MolMIM NIM API 클라이언트 (5개 엔드포인트 지원)"""

    # NVIDIA 호스팅 API 기본 URL
    BASE_URL = "https://health.api.nvidia.com/v1/biology/nvidia/molmim"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        # MOLMIM_BASE_URL 환경변수를 우선 적용
        effective_url = base_url or os.getenv("MOLMIM_BASE_URL")
        super().__init__(api_key=api_key, base_url=effective_url)

    def _post(self, endpoint: str, payload: dict, timeout: int = 120) -> dict:
        """API POST 요청 (molecules JSON 문자열 자동 파싱 추가)"""
        data = super()._post(endpoint, payload, timeout=timeout)
        # 호스팅 API는 molecules 필드에 JSON 문자열을 반환하는 경우가 있음
        if isinstance(data.get("molecules"), str):
            data["molecules"] = json.loads(data["molecules"])
        return data

    # ─── 엔드포인트 1: 임베딩 ───────────────────────────────

    def embedding(self, smiles: str | list[str]) -> list:
        """
        SMILES → 512차원 임베딩 벡터

        Args:
            smiles: 단일 SMILES 문자열 또는 리스트
        Returns:
            임베딩 벡터 리스트 [[512 floats], ...]
        """
        if isinstance(smiles, str):
            smiles = [smiles]
        result = self._post("embedding", {"sequences": smiles})
        return result.get("embeddings", result)

    # ─── 엔드포인트 2: 숨은 상태 ─────────────────────────────

    def hidden(self, smiles: str | list[str]) -> dict:
        """
        SMILES → 숨은 상태 (재구성/생성에 사용)

        Returns:
            {"hidden_states": [...], "pad_masks": [...]}
        """
        if isinstance(smiles, str):
            smiles = [smiles]
        return self._post("hidden", {"sequences": smiles})

    # ─── 엔드포인트 3: 디코딩 ────────────────────────────────

    def decode(self, hidden_states: list, pad_masks: list) -> list[str]:
        """
        숨은 상태 → SMILES 복원

        Returns:
            복원된 SMILES 리스트
        """
        result = self._post("decode", {
            "hidden_states": hidden_states,
            "pad_masks": pad_masks,
        })
        return result.get("sequences", result)

    # ─── 엔드포인트 4: 샘플링 ────────────────────────────────
    # 호스팅 API에서는 /sampling이 없으므로 /generate + algorithm="none"으로 대체

    def sampling(
        self,
        smi: str,
        num_samples: int = 10,
        scaled_radius: float = 0.7,
    ) -> list[dict]:
        """
        시드 분자 주변 잠재공간에서 새 분자 샘플링
        (호스팅 API: /generate + algorithm="none" 사용)

        Args:
            smi: 시드 SMILES
            num_samples: 생성할 분자 수
            scaled_radius: 샘플링 반경 (작을수록 유사)
        Returns:
            [{"sample": "SMILES", "score": float}, ...]
        """
        result = self._post("generate", {
            "smi": smi,
            "algorithm": "none",
            "num_molecules": num_samples,
            "particles": num_samples,
            "scaled_radius": scaled_radius,
        })
        return result.get("molecules", result)

    # ─── 엔드포인트 5: 생성 (CMA-ES 최적화) ─────────────────

    def generate(
        self,
        smi: str,
        num_molecules: int = 10,
        algorithm: str = "CMA-ES",
        property_name: str = "QED",
        minimize: bool = False,
        min_similarity: float = 0.3,
        particles: int = 20,
        iterations: int = 3,
    ) -> list[dict]:
        """
        CMA-ES 알고리즘으로 목표 물성 최적화된 분자 생성

        Args:
            smi: 시드 SMILES
            num_molecules: 생성 분자 수
            algorithm: "CMA-ES"
            property_name: 최적화 대상 (QED, logP 등)
            minimize: True면 최소화, False면 최대화
            min_similarity: 시드 대비 최소 유사도
            particles: CMA-ES 파티클 수
            iterations: 반복 횟수
        Returns:
            [{"smiles": "...", "score": float, "similarity": float}, ...]
        """
        result = self._post("generate", {
            "smi": smi,
            "num_molecules": num_molecules,
            "algorithm": algorithm,
            "property_name": property_name,
            "minimize": minimize,
            "min_similarity": min_similarity,
            "particles": particles,
            "iterations": iterations,
        })
        return result.get("molecules", result)

    # ─── 유틸리티 ───────────────────────────────────────────

    def health_check(self) -> bool:
        """API 서버 상태 확인"""
        try:
            resp = requests.get(
                f"{self.base_url}/health/ready",
                headers=self.headers,
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False


# ─── 간편 사용 ───────────────────────────────────────────────

def get_client(**kwargs) -> MolMIMClient:
    """기본 설정으로 클라이언트 생성"""
    return MolMIMClient(**kwargs)


if __name__ == "__main__":
    client = get_client()
    print("MolMIM Client initialized")
    print(f"  Base URL: {client.base_url}")
    print(f"  API Key:  {'***' + client.api_key[-8:] if client.api_key else 'NOT SET'}")

    # 테스트 1: 분자 생성 (CMA-ES)
    print("\n[TEST 1] Generate with CMA-ES (seed: CCO, QED maximize)")
    try:
        mols = client.generate(
            smi="CCO",
            num_molecules=3,
            algorithm="CMA-ES",
            property_name="QED",
            min_similarity=0.3,
            particles=8,
            iterations=3,
        )
        for i, mol in enumerate(mols, 1):
            if isinstance(mol, dict):
                print(f"  {i}. {mol.get('sample', mol.get('smiles', '?')):40s} "
                      f"score={mol.get('score', '?')}")
            else:
                print(f"  {i}. {mol}")
    except Exception as e:
        print(f"  Error: {e}")

    # 테스트 2: 랜덤 샘플링
    print("\n[TEST 2] Random sampling (seed: CCO)")
    try:
        samples = client.sampling(smi="CCO", num_samples=3, scaled_radius=1.0)
        for i, mol in enumerate(samples, 1):
            if isinstance(mol, dict):
                print(f"  {i}. {mol.get('sample', '?'):40s} "
                      f"similarity={mol.get('score', '?')}")
            else:
                print(f"  {i}. {mol}")
    except Exception as e:
        print(f"  Error: {e}")
