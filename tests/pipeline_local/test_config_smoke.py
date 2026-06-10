"""pipeline_local 설정·아카이브·LLM 팩토리 스모크 (외부 서버 불필요)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
_AG = ROOT / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri"
for _p in (ROOT, _AG):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def test_pipeline_config_yaml_loads() -> None:
    p = ROOT / "pipeline_local" / "config" / "pipeline_config_local.yaml"
    assert p.is_file()
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert data.get("llm", {}).get("provider") in ("ollama", "vllm", "none", None)


def test_create_provider_matches_yaml_provider() -> None:
    from AG_src.llm import create_provider

    p = ROOT / "pipeline_local" / "config" / "pipeline_config_local.yaml"
    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    prov = create_provider(cfg)
    name = type(prov).__name__
    yaml_prov = str(cfg.get("llm", {}).get("provider", "none")).lower()
    if yaml_prov == "vllm":
        assert name == "VLLMProvider"
    elif yaml_prov == "ollama":
        assert name == "OllamaProvider"
    elif yaml_prov == "none":
        assert name == "NoneProvider"


def test_archive_dirs_and_find_invalid() -> None:
    from pipeline_local.backend.state import ARCHIVE_DIRS, find_dashboard_archive

    assert len(ARCHIVE_DIRS) >= 1
    assert find_dashboard_archive("") is None
    assert find_dashboard_archive("../x") is None


def test_dual_flag_updates_effective_config(tmp_path: Path) -> None:
    """``run_pipeline_local`` 가 쓰는 effective YAML 에 dual_silo.enabled 반영 패턴 검증."""
    src = ROOT / "pipeline_local" / "config" / "pipeline_config_local.yaml"
    cfg = yaml.safe_load(src.read_text(encoding="utf-8"))
    cfg.setdefault("dual_silo", {})["enabled"] = True
    out = tmp_path / "eff.yaml"
    out.write_text(yaml.dump(cfg, allow_unicode=True), encoding="utf-8")
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert loaded["dual_silo"]["enabled"] is True
