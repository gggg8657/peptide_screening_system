"""
ESMFold API Client
===================
NVIDIA 호스팅 API를 통한 단백질 구조 예측 (MSA 불필요).

사용법:
    from esmfold_client import ESMFoldClient
    client = ESMFoldClient()
    result = client.predict("AGCKNFFWKTFTSC")
    pdb, plddt = ESMFoldClient.extract_pdb(result), ESMFoldClient.extract_plddt(result)
"""

import logging
import re
from pathlib import Path
from typing import Optional
try:
    from .api_base import NVIDIABaseClient
except ImportError:
    from api_base import NVIDIABaseClient

logger = logging.getLogger(__name__)

# ── PDB에서 pLDDT 파싱용 (B-factor 컬럼) ───────────────────
_BFACTOR_RE = re.compile(r"^(?:ATOM|HETATM)", re.MULTILINE)


class ESMFoldClient(NVIDIABaseClient):
    """ESMFold NIM API 클라이언트"""

    BASE_URL = "https://health.api.nvidia.com/v1/biology/nvidia/esmfold"

    def predict(self, sequence: str) -> dict:
        """
        아미노산 서열 → 3D 구조 예측

        Args:
            sequence: 아미노산 서열 (예: "AGCKNFFWKTFTSC")

        Returns:
            API 응답 dict (키는 API 버전에 따라 다를 수 있음)
        """
        payload = {"sequence": sequence}
        return self._post("", payload, timeout=120)

    # ── 응답 파싱 유틸리티 (정적 메서드) ─────────────────────

    @staticmethod
    def extract_pdb(result: dict) -> Optional[str]:
        """API 응답에서 PDB 문자열을 추출.

        알려진 응답 키를 우선순위대로 시도:
          pdbs[0] → pdb → output → (문자열이면 그대로)
        """
        if not isinstance(result, dict):
            return None
        # 1) pdbs 리스트
        pdbs = result.get("pdbs")
        if isinstance(pdbs, list) and pdbs:
            return pdbs[0]
        # 2) pdb 단일 문자열
        pdb = result.get("pdb")
        if isinstance(pdb, str) and pdb:
            return pdb
        # 3) output (일부 NIM 버전)
        output = result.get("output")
        if isinstance(output, str) and ("ATOM" in output or "HETATM" in output):
            return output
        logger.warning("PDB 내용을 응답에서 추출할 수 없음: keys=%s", list(result.keys()))
        return None

    @staticmethod
    def extract_plddt(result: dict, pdb_content: Optional[str] = None) -> Optional[float]:
        """API 응답에서 mean pLDDT를 추출.

        시도 순서:
          1) mean_plddt 키
          2) plddt 키 (float 또는 list → 평균)
          3) plddt_scores 키 (list → 평균)
          4) PDB B-factor 컬럼에서 계산 (ESMFold은 pLDDT를 B-factor에 저장)
        """
        if not isinstance(result, dict):
            return None

        # 1) 직접 키
        val = result.get("mean_plddt")
        if isinstance(val, (int, float)):
            return float(val)

        # 2) plddt (스칼라 또는 리스트)
        val = result.get("plddt")
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, list) and val:
            return sum(val) / len(val)

        # 3) plddt_scores 리스트
        val = result.get("plddt_scores")
        if isinstance(val, list) and val:
            flat = val[0] if isinstance(val[0], list) else val
            return sum(flat) / len(flat) if flat else None

        # 4) PDB B-factor 폴백
        pdb_text = pdb_content or ESMFoldClient.extract_pdb(result)
        if pdb_text:
            return ESMFoldClient._plddt_from_bfactor(pdb_text)

        logger.warning("pLDDT를 응답에서 추출할 수 없음: keys=%s", list(result.keys()))
        return None

    @staticmethod
    def _plddt_from_bfactor(pdb_text: str) -> Optional[float]:
        """PDB ATOM 레코드의 B-factor 컬럼(61-66)에서 평균 pLDDT 계산."""
        bfactors = []
        for line in pdb_text.splitlines():
            if line.startswith(("ATOM", "HETATM")) and len(line) >= 66:
                try:
                    bfactors.append(float(line[60:66]))
                except ValueError:
                    continue
        if bfactors:
            return sum(bfactors) / len(bfactors)
        return None

    # ── 고수준 메서드 ────────────────────────────────────────

    def predict_and_save(
        self,
        sequence: str,
        output_path: str | Path,
    ) -> dict:
        """구조 예측 후 PDB 파일 저장"""
        result = self.predict(sequence)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        pdb_content = self.extract_pdb(result)
        if pdb_content:
            output_path.write_text(pdb_content)
            print(f"  PDB 저장: {output_path}")
        else:
            logger.warning("PDB 저장 실패: 응답에 PDB 내용 없음")

        return result

    def batch_predict(
        self,
        sequences: list[str],
    ) -> list[dict]:
        """여러 서열 배치 예측"""
        results = []
        for i, seq in enumerate(sequences):
            print(f"  [{i+1}/{len(sequences)}] ESMFold 예측: {seq[:30]}...")
            try:
                result = self.predict(seq)
                result["input_sequence"] = seq
                results.append(result)
            except Exception as e:
                print(f"    오류: {e}")
                results.append({"input_sequence": seq, "error": str(e)})
        return results


def get_client(**kwargs) -> ESMFoldClient:
    return ESMFoldClient(**kwargs)


if __name__ == "__main__":
    client = get_client()
    print("ESMFold Client initialized")
    print(f"  Base URL: {client.base_url}")
    print(f"  API Key:  {'***' + client.api_key[-8:] if client.api_key else 'NOT SET'}")
