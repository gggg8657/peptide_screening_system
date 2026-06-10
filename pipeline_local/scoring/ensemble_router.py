"""3계층 혈중 반감기 라우터 — Layer 2는 로컬 PEPlife2-GAT 회귀 호출."""
from __future__ import annotations

import re
from typing import Any, Dict

from pipeline_local.scoring.layer2_ensemble import compute_layer2_halflife


def contains_d_amino_acid(sequence: str) -> bool:
    """PEPlife2 등 데이터셋 관례: 소문자 잔기 = D-형 등 비표준."""
    return bool(sequence and re.search(r"[a-z]", sequence))


def is_cyclic_ss_candidate(sequence: str) -> bool:
    """이중 Cys(이황화 가능)를 링크로 보는 최소 휴리스틱."""
    return sequence.upper().count("C") >= 2


def is_linear_l_aa_sequence(sequence: str) -> bool:
    """표준 20aa 대문자 단일 문자열."""
    if not sequence:
        return False
    if contains_d_amino_acid(sequence):
        return False
    if is_cyclic_ss_candidate(sequence):
        return False
    return bool(re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", sequence.strip()))


def analyze_halflife_candidate(sequence: str, has_dota: bool = False) -> Dict[str, Any]:
    has_dota_flag = has_dota or bool(re.search(r"dota|dotaga|chelator", sequence, re.IGNORECASE))
    has_d_aa = contains_d_amino_acid(sequence)
    has_cyclic = is_cyclic_ss_candidate(sequence) and not has_dota_flag
    is_l_aa = is_linear_l_aa_sequence(sequence) and not has_dota_flag
    return {
        "is_l_aa": is_l_aa,
        "has_d_aa": has_d_aa,
        "has_cyclic": has_cyclic,
        "has_dota": has_dota_flag,
    }


def route_halflife_prediction(sequence: str, has_dota: bool = False) -> str:
    info = analyze_halflife_candidate(sequence, has_dota=has_dota)
    if info["has_dota"]:
        return "layer3_dota_admet_ai_md_proxy_stub"
    if info["has_d_aa"] or info["has_cyclic"]:
        return "layer2_daa_cyclic_pepmsnd"
    if info["is_l_aa"]:
        return "layer1_l_aa_ensemble_stub"
    return "unavailable"


def run_routed_halflife(
    sequence: str,
    *,
    has_dota: bool = False,
    cuda_visible_devices: str | None = None,
) -> Dict[str, Any]:
    """라우팅 후 Layer 2만 실구현; Layer 1/3은 스텁 메타만."""
    route = route_halflife_prediction(sequence, has_dota=has_dota)
    base: Dict[str, Any] = {"route": route, "sequence": sequence.strip()}
    if route == "layer2_daa_cyclic_pepmsnd":
        base.update(
            compute_layer2_halflife(
                sequence,
                has_dota=has_dota,
                cuda_visible_devices=cuda_visible_devices,
            )
        )
        return base
    if route == "layer1_l_aa_ensemble_stub":
        base["ensemble_halflife_hours"] = None
        base["warnings"] = ["Layer 1 ensemble 미연결(스텁) — pipeline_local.scoring.layer1_ensemble 필요"]
        return base
    if route == "layer3_dota_admet_ai_md_proxy_stub":
        base["ensemble_halflife_hours"] = None
        base["warnings"] = ["Layer 3 DOTA/ADMET 스텁"]
        return base
    base["ensemble_halflife_hours"] = None
    base["warnings"] = ["라우팅 불가 시퀀스"]
    return base
