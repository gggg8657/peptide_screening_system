"""
pipeline_local/tests/test_admet_divergence_guard.py
====================================================
PRST mismatch fix (2026-05-26) — ADMET_DIVERGENCE_THRESHOLD guard 회귀.

PRST-001~004 케이스에서 pepADMET retrained = 1.00, ADMET-AI raw = 0.10~0.25
와 같이 두 소스 값이 크게 다를 때 자동으로 ADMET_DIVERGENCE_HIGH warning 을
발생시켜 정직하게 OOD 의심을 알려야 한다.
"""
from __future__ import annotations

from pipeline_local.scripts.composite_scorer import (
    ADMET_DIVERGENCE_THRESHOLD,
    _check_admet_divergence,
)


def test_divergence_high_pepadmet_1_0_vs_admet_ai_0_1() -> None:
    """PRST-001 케이스: pepADMET=1.00, ADMET-AI=0.10 → 차이 0.90 → 발생."""
    result = {
        "pepadmet": {"admet_tox": 1.00},
        "admet_ai": {"admet_tox": 0.10},
    }
    msg = _check_admet_divergence(result)
    assert msg is not None, "차이 0.90 인데 divergence warning 미발생"
    assert "1.000" in msg and "0.100" in msg
    assert "OOD" in msg or "validation" in msg.lower()


def test_divergence_high_top_level_keys() -> None:
    """nested dict 가 아닌 top-level pepadmet_tox / admet_ai_tox 도 인식해야 함."""
    result = {
        "pepadmet_tox": 0.95,
        "admet_ai_tox": 0.20,
    }
    msg = _check_admet_divergence(result)
    assert msg is not None
    assert "0.950" in msg and "0.200" in msg


def test_divergence_below_threshold_no_warning() -> None:
    """차이가 임계값 미만이면 warning 미발생."""
    delta = ADMET_DIVERGENCE_THRESHOLD - 0.05
    result = {
        "pepadmet": {"admet_tox": 0.50},
        "admet_ai": {"admet_tox": 0.50 - delta},
    }
    msg = _check_admet_divergence(result)
    assert msg is None, f"차이 {delta:.3f} < 임계값 → warning 발생하면 안 됨"


def test_divergence_one_source_missing_no_warning() -> None:
    """한 쪽 값만 있으면 divergence 판정 불가 → None."""
    result_only_pepadmet = {"pepadmet": {"admet_tox": 1.00}}
    assert _check_admet_divergence(result_only_pepadmet) is None

    result_only_admet_ai = {"admet_ai": {"admet_tox": 0.10}}
    assert _check_admet_divergence(result_only_admet_ai) is None


def test_divergence_uses_alt_keys() -> None:
    """toxicity_probability / toxicity_score 키도 인식해야 함."""
    result = {
        "pepadmet": {"toxicity_probability": 0.85},
        "admet_ai": {"toxicity_score": 0.10},
    }
    msg = _check_admet_divergence(result)
    assert msg is not None
