"""
RFdiffusion API Client
=======================
NVIDIA 호스팅 API를 통한 de novo 단백질/펩타이드 바인더 설계.

사용법:
    from rfdiffusion_client import RFdiffusionClient
    client = RFdiffusionClient()
    pdb = client.design_binder("sstr2.pdb", contigs="B1-369/0 10-30", hotspot_res=["B122","B127"])
"""

from pathlib import Path
from typing import Optional
try:
    from .api_base import NVIDIABaseClient
except ImportError:
    from api_base import NVIDIABaseClient


class RFdiffusionClient(NVIDIABaseClient):
    """RFdiffusion NIM API 클라이언트"""

    BASE_URL = "https://health.api.nvidia.com/v1/biology/ipd/rfdiffusion"

    def generate(
        self,
        input_pdb: str,
        contigs: str,
        hotspot_res: Optional[list[str]] = None,
        diffusion_steps: int = 50,
        random_seed: Optional[int] = None,
    ) -> dict:
        """
        de novo 단백질 구조 생성 (바인더 설계, 모티프 스캐폴딩 등)

        Args:
            input_pdb: 타겟 단백질 PDB 파일 내용 (문자열)
            contigs: 도메인 특정 언어 문자열
                예: "B1-369/0 10-30" = Chain B 보존 + 10-30잔기 새 펩타이드
            hotspot_res: 바인더가 접촉해야 할 타겟 잔기
                예: ["B122", "B127", "B200"]
            diffusion_steps: 확산 역전 스텝 수 (기본 50)
            random_seed: 재현성을 위한 시드 (None이면 랜덤)

        Returns:
            {"output_pdb": "PDB content...", "elapsed_ms": int}
        """
        payload = {
            "input_pdb": input_pdb,
            "contigs": contigs,
            "diffusion_steps": diffusion_steps,
        }
        if hotspot_res:
            payload["hotspot_res"] = hotspot_res
        if random_seed is not None:
            payload["random_seed"] = random_seed

        return self._post("generate", payload, timeout=300)

    def design_binder(
        self,
        pdb_path: str | Path,
        contigs: str,
        hotspot_res: Optional[list[str]] = None,
        diffusion_steps: int = 50,
        random_seed: Optional[int] = None,
    ) -> dict:
        """파일 경로로 바인더 설계"""
        pdb_content = Path(pdb_path).read_text()
        return self.generate(
            input_pdb=pdb_content,
            contigs=contigs,
            hotspot_res=hotspot_res,
            diffusion_steps=diffusion_steps,
            random_seed=random_seed,
        )

    def design_multiple(
        self,
        pdb_path: str | Path,
        contigs: str,
        hotspot_res: Optional[list[str]] = None,
        num_designs: int = 10,
        diffusion_steps: int = 50,
    ) -> list[dict]:
        """여러 바인더 설계 (seed 변경)"""
        results = []
        pdb_content = Path(pdb_path).read_text()

        for i in range(num_designs):
            print(f"  [{i+1}/{num_designs}] RFdiffusion 설계 중 (seed={i})...")
            try:
                result = self.generate(
                    input_pdb=pdb_content,
                    contigs=contigs,
                    hotspot_res=hotspot_res,
                    diffusion_steps=diffusion_steps,
                    random_seed=i,
                )
                result["design_idx"] = i
                results.append(result)
            except Exception as e:
                print(f"    오류: {e}")
                results.append({"design_idx": i, "error": str(e)})

        return results


def get_client(**kwargs) -> RFdiffusionClient:
    return RFdiffusionClient(**kwargs)


if __name__ == "__main__":
    client = get_client()
    print("RFdiffusion Client initialized")
    print(f"  Base URL: {client.base_url}")
    print(f"  API Key:  {'***' + client.api_key[-8:] if client.api_key else 'NOT SET'}")
