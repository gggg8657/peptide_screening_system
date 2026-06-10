"""
config_loader.py — model_paths.yaml 로드 및 모델 정보 조회

로컬 모델의 conda 환경, 스크립트 경로, GPU 장치 등 실행 메타데이터를
중앙 집중형 YAML에서 읽어 반환한다.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

# config 파일의 기본 경로 (이 파일 기준 상위 디렉토리의 config/)
_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "model_paths.yaml"


def load_model_config(config_path: Optional[str | Path] = None) -> dict:
    """model_paths.yaml을 로드해 파싱된 딕셔너리를 반환한다.

    Parameters
    ----------
    config_path:
        YAML 파일 경로. None이면 패키지 기본 경로를 사용한다.

    Returns
    -------
    dict
        YAML 전체 내용. 최상위 키: ``defaults``, ``models``

    Raises
    ------
    FileNotFoundError
        지정한 경로에 파일이 존재하지 않을 때.
    yaml.YAMLError
        YAML 파싱에 실패했을 때.
    """
    path = Path(config_path) if config_path is not None else _DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"model_paths.yaml을 찾을 수 없습니다: {path}"
        )

    with path.open("r", encoding="utf-8") as fh:
        config: dict = yaml.safe_load(fh)

    if not isinstance(config, dict):
        raise ValueError(f"잘못된 YAML 형식입니다 (dict 최상위 구조 필요): {path}")

    return config


def get_model_info(
    model_name: str,
    config_path: Optional[str | Path] = None,
) -> dict:
    """특정 모델의 실행 메타데이터를 반환한다.

    공통 ``defaults`` 값을 베이스로 두고, 모델별 설정으로 오버라이드한다.

    Parameters
    ----------
    model_name:
        model_paths.yaml의 ``models`` 섹션에 정의된 모델 키
        (예: ``"rfdiffusion"``, ``"esmfold"``).
    config_path:
        YAML 파일 경로. None이면 패키지 기본 경로를 사용한다.

    Returns
    -------
    dict
        다음 키를 포함한 딕셔너리::

            {
                "conda_env": str,
                "script": str | None,
                "model_dir": str | None,
                "gpu_device": int,
                "timeout": int,
            }

    Raises
    ------
    KeyError
        ``model_name``이 config에 존재하지 않을 때.
    """
    config = load_model_config(config_path)

    defaults: dict = config.get("defaults", {})
    models: dict = config.get("models", {})

    if model_name not in models:
        available = sorted(models.keys())
        raise KeyError(
            f"모델 '{model_name}'을 config에서 찾을 수 없습니다. "
            f"등록된 모델: {available}"
        )

    # defaults를 베이스로 모델별 값으로 오버라이드
    info: dict = {**defaults, **models[model_name]}
    return info


def list_models(config_path: Optional[str | Path] = None) -> list[str]:
    """등록된 모든 모델 이름 목록을 반환한다."""
    config = load_model_config(config_path)
    return sorted(config.get("models", {}).keys())
