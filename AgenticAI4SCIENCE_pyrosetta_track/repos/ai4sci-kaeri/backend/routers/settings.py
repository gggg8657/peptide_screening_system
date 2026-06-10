"""Settings endpoints — runtime configuration management."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.state import runtime_settings

router = APIRouter()


class ExecutionStrategy(str, Enum):
    sequential = "sequential"
    parallel = "parallel"


class NimEndpointMode(str, Enum):
    cloud = "cloud"
    local = "local"


class SettingsModel(BaseModel):
    execution_strategy: Optional[ExecutionStrategy] = Field(None, description="Pipeline execution strategy")
    max_iterations: Optional[int] = Field(None, ge=1, le=100, description="Maximum pipeline iterations")
    n_candidates: Optional[int] = Field(None, ge=1, le=200, description="Number of candidates per iteration")
    top_k: Optional[int] = Field(None, ge=1, le=50, description="Top-K candidates to select")
    llm_model: Optional[str] = Field(None, min_length=1, max_length=100, description="LLM model name")
    nim_api_key: Optional[str] = Field(None, max_length=200, description="NVIDIA NIM API key")
    nim_endpoint_mode: Optional[NimEndpointMode] = Field(None, description="NIM endpoint mode")
    validation_n_trials: Optional[int] = Field(None, ge=1, le=50, description="Number of validation trials")


@router.get("/settings")
def get_settings():
    return dict(runtime_settings)


@router.put("/settings")
def update_settings(body: SettingsModel):
    updates = body.model_dump(exclude_none=True)
    runtime_settings.update(updates)
    return dict(runtime_settings)
