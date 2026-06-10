"""
pipeline_local — 로컬 모델 실행 인프라
NIM API 의존성 없이 로컬 conda 환경에서 각 모델을 서브프로세스로 실행한다.
"""

__version__ = "0.1.0"
__all__ = ["LocalModelRunner", "load_model_config", "get_model_info"]

from pipeline_local.core.local_runner import LocalModelRunner
from pipeline_local.core.config_loader import load_model_config, get_model_info
