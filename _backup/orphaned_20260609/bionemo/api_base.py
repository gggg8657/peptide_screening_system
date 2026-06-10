"""
공통 API 베이스 클래스
=====================
모든 NVIDIA NIM API 클라이언트가 상속하는 베이스 클래스.
molmim.key / .env / 환경변수에서 키를 자동 로드한다.

재시도 정책: 429(Rate Limit) / 500 / 502 / 503 / 504 에 대해
지수 백오프(exponential backoff)로 최대 3회 재시도.
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 재시도 대상 HTTP 상태 코드
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0  # 초 단위 (2, 4, 8 ...)


class NVIDIABaseClient:
    """NVIDIA NIM API 공통 베이스 클라이언트"""

    BASE_URL = ""  # 서브클래스에서 오버라이드

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = _MAX_RETRIES,
    ):
        self.api_key = api_key or self._load_api_key()
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.max_retries = max_retries
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    @staticmethod
    def _load_api_key() -> str:
        """환경변수 → .env → molmim.key/ngc.key 순서로 API 키 탐색"""
        # 1. 환경변수
        for env_var in ("NGC_CLI_API_KEY", "NVIDIA_API_KEY"):
            key = os.getenv(env_var)
            if key:
                logger.debug("API 키 로드: 환경변수 %s", env_var)
                return key

        # 2. .env 파일
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if "API_KEY=" in line and not line.startswith("#"):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and "your-" not in val:
                        logger.debug("API 키 로드: %s", env_path)
                        return val

        # 3. 키 파일 (프로젝트 루트)
        for search in [Path(__file__).parent.parent, Path.cwd()]:
            for name in ["molmim.key", "ngc.key"]:
                key_file = search / name
                if key_file.exists():
                    val = key_file.read_text().strip()
                    if val:
                        logger.debug("API 키 로드: %s", key_file)
                        return val

        raise ValueError(
            "NVIDIA API 키를 찾을 수 없습니다.\n"
            "방법 1: 환경변수 NGC_CLI_API_KEY 설정\n"
            "방법 2: bionemo/.env 파일에 NGC_CLI_API_KEY=xxx\n"
            "방법 3: 프로젝트 루트에 molmim.key 파일"
        )

    def _request_with_retry(
        self, method: str, url: str, timeout: int, **kwargs
    ) -> requests.Response:
        """지수 백오프 재시도가 포함된 HTTP 요청"""
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.request(
                    method, url, headers=self.headers, timeout=timeout, **kwargs
                )
                if resp.status_code == 200:
                    return resp
                if resp.status_code not in _RETRYABLE_STATUS_CODES:
                    # 재시도 불가능한 오류는 즉시 실패
                    raise RuntimeError(
                        f"API 오류 [{resp.status_code}]: {resp.text[:500]}"
                    )
                # 재시도 가능 — 백오프 후 재시도
                wait = _BACKOFF_BASE ** attempt
                if resp.status_code == 429:
                    # Retry-After 헤더가 있으면 존중
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = max(wait, float(retry_after))
                        except ValueError:
                            pass
                logger.warning(
                    "API %d 응답, %d/%d 재시도 (%.1fs 대기): %s",
                    resp.status_code, attempt + 1, self.max_retries, wait, url,
                )
                time.sleep(wait)
                last_exc = RuntimeError(
                    f"API 오류 [{resp.status_code}]: {resp.text[:500]}"
                )
            except requests.exceptions.ConnectionError as e:
                wait = _BACKOFF_BASE ** attempt
                logger.warning(
                    "연결 오류, %d/%d 재시도 (%.1fs 대기): %s",
                    attempt + 1, self.max_retries, wait, e,
                )
                time.sleep(wait)
                last_exc = e
            except requests.exceptions.Timeout as e:
                wait = _BACKOFF_BASE ** attempt
                logger.warning(
                    "타임아웃, %d/%d 재시도 (%.1fs 대기): %s",
                    attempt + 1, self.max_retries, wait, e,
                )
                time.sleep(wait)
                last_exc = e

        raise RuntimeError(
            f"API 요청 실패 ({self.max_retries}회 재시도 후): {last_exc}"
        )

    def _post(self, endpoint: str, payload: dict, timeout: int = 120) -> dict:
        """API POST 요청 (재시도 포함)"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        resp = self._request_with_retry("POST", url, timeout=timeout, json=payload)
        return resp.json()

    def _post_raw(self, endpoint: str, payload: dict, timeout: int = 120) -> requests.Response:
        """API POST 요청 (raw Response 반환, 재시도 포함)"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        return self._request_with_retry("POST", url, timeout=timeout, json=payload)
