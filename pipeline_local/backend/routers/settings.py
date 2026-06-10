"""Settings endpoints — 로컬 모드 런타임 설정 관리.

NIM API 관련 필드(nim_api_key, nim_endpoint_mode)를 제거하고
ollama_host 필드를 추가한다.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from pipeline_local.backend.state import runtime_settings

router = APIRouter()


class ExecutionStrategy(str, Enum):
    sequential = "sequential"
    parallel   = "parallel"


class SettingsModel(BaseModel):
    execution_strategy:  Optional[ExecutionStrategy] = Field(
        None, description="파이프라인 실행 전략"
    )
    max_iterations:      Optional[int] = Field(
        None, ge=1, le=100, description="최대 파이프라인 반복 횟수"
    )
    n_candidates:        Optional[int] = Field(
        None, ge=1, le=200, description="반복당 후보 수"
    )
    top_k:               Optional[int] = Field(
        None, ge=1, le=50,  description="선택할 상위 K 후보"
    )
    llm_model:           Optional[str] = Field(
        None, min_length=1, max_length=120, description="LLM 모델 id (Ollama 태그 또는 vLLM served name)"
    )
    llm_provider:        Optional[str] = Field(
        None, max_length=32, description='ollama | vllm | none (None이면 YAML 우선)'
    )
    llm_base_url:        Optional[str] = Field(
        None, max_length=200, description="vLLM/OpenAI 호환 베이스 URL (예: http://127.0.0.1:8001)"
    )
    ollama_host:         Optional[str] = Field(
        None, max_length=100, description="Ollama 서버 주소 (예: 127.0.0.1:11435)"
    )
    validation_n_trials: Optional[int] = Field(
        None, ge=1, le=50,  description="검증 시험 횟수"
    )


@router.get("/settings")
def get_settings():
    """현재 런타임 설정을 반환한다."""
    return dict(runtime_settings)


@router.put("/settings")
def update_settings(body: SettingsModel):
    """런타임 설정을 부분 업데이트한다 (None 값은 무시)."""
    updates = body.model_dump(exclude_none=True)
    runtime_settings.update(updates)
    return dict(runtime_settings)
