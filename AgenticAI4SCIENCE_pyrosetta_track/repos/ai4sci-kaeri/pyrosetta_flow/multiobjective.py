"""multiobjective.py
=================
SSTR2 방사성의약품 스크리닝 다목적 통합 (ΔG + 반감기 + 선택성 + ADMET).

목표(goal): SST-14(AGCKNFFWKTFTSC) 변이체 중
  - ddG ↓               : SSTR2에 강하게 결합
  - half_life_h ↑        : 혈중 반감기가 길다
  - selectivity_margin ↑ : SSTR1/3/4/5(off-target) 대비 SSTR2 선택적
  - admet_score ↑        : ADMET 프로파일이 합리적 (용해도/안정성/결합경향)

비용 계층화 (cost-tiered) — 실제 도킹은 비싸므로:
  Layer 0 (모든 후보, 서열만, μs):  half_life + ADMET surrogate
  Layer 1 (top-K, 실제 PyRosetta):  selectivity off-target docking

honest disclaimer (VR-cycle-09 / H-06):
  half_life_h, admet_score 는 **랭킹용 surrogate** 다. 임상 반감기·임상 ADMET 수치가
  아니며, in-vitro 혈청 안정성/투과도 assay 로 검증되지 않았다. ddG·selectivity_margin
  은 실제 PyRosetta FlexPepDock 결과(REU/kcal·mol)지만 절대 친화도(Ki/Kd)가 아니다.

이 모듈은 pyrosetta_flow 후보 dict(키: sequence, ddg, total_score, clash_score, …)를
입력받아 extra_scores 를 채우고, pareto_ranking 이 기대하는 키(stability, druggability)로
매핑한다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

NATIVE_SST14 = "AGCKNFFWKTFTSC"

# ---------------------------------------------------------------------------
# 의존 모듈 (지연 import — 일부 환경에서 PyRosetta/AG_src 부재 가능)
# ---------------------------------------------------------------------------

try:  # 반감기 surrogate (서열 기반)
    from AG_src.pipeline.step08_stability import predict_half_life as _predict_half_life
    _HAS_HALFLIFE = True
except Exception:  # pragma: no cover
    _predict_half_life = None  # type: ignore[assignment]
    _HAS_HALFLIFE = False

try:  # ADMET-reasonableness surrogate (문헌 기반 물성)
    from AG_src.pipeline.pharma_properties import PharmaProperties as _PharmaProperties
    _HAS_PHARMA = True
except Exception:  # pragma: no cover
    _PharmaProperties = None  # type: ignore[assignment]
    _HAS_PHARMA = False


# ---------------------------------------------------------------------------
# ADMET-reasonableness scoring
# ---------------------------------------------------------------------------

# "합리적(reasonable)" 범위 — 문헌 휴리스틱. 점수는 0(나쁨)~1(좋음).
#   Instability Index < 40  → 안정 (Guruprasad 1990)
#   GRAVY < 0               → 수용성(친수성), 펩타이드 약물에 유리
#   Boman 2.48 부근~높음    → 단백질 결합 경향(수용체 결합에 유리하나 과도하면 비특이)
#   pI 중성 근처(6~8)        → 제형/용해 안정


def admet_reasonableness(props: Dict[str, float]) -> float:
    """4개 물성에서 0~1 합리성 점수를 합성한다 (가중 평균).

    각 항목을 0~1 부분점수로 변환 후 평균. surrogate 임을 잊지 말 것.
    """
    ii = props.get("instability_index", 50.0)
    gravy = props.get("gravy", 0.0)
    boman = props.get("boman_index", 0.0)
    pi = props.get("pi", 7.0)

    # Instability: <40 만점, 40~80 선형 감점, >80 0점
    s_ii = 1.0 if ii < 40 else max(0.0, 1.0 - (ii - 40.0) / 40.0)
    # GRAVY: <=-1 만점(매우 친수), 0 에서 0.5, >=1 0점 (소수성 과다 → 응집/저용해)
    s_gravy = min(1.0, max(0.0, (1.0 - gravy) / 2.0))
    # Boman: 2.0~3.5 이상이 단백질 결합 펩타이드에 적정. 1.0 미만이면 결합경향 약함.
    if boman < 1.0:
        s_boman = max(0.0, boman / 1.0) * 0.5
    elif boman <= 4.0:
        s_boman = 0.5 + 0.5 * (boman - 1.0) / 3.0
    else:
        s_boman = 1.0
    # pI: 6~8 만점, 멀어질수록 감점
    s_pi = max(0.0, 1.0 - abs(pi - 7.0) / 5.0)

    # 가중: 안정성·용해를 더 중시
    score = 0.35 * s_ii + 0.30 * s_gravy + 0.15 * s_boman + 0.20 * s_pi
    return round(score, 4)


# ---------------------------------------------------------------------------
# Layer 0 — cheap objectives (모든 후보)
# ---------------------------------------------------------------------------

# 반감기 정규화: native(~16h) 대비. 0~1 로 사용(stability objective).
_HALFLIFE_REF_H = 16.0


def cheap_objectives(sequence: str, reference_seq: str = NATIVE_SST14) -> Dict[str, Any]:
    """서열만으로 계산 가능한 저비용 목적값 + ADMET surrogate.

    Returns dict keys:
        half_life_h, gravy, boman_index, instability_index, aliphatic_index, pi,
        admet_score, stability_norm  (모두 surrogate / ranking 용)
    """
    seq = (sequence or "").upper()
    out: Dict[str, Any] = {"sequence": seq}

    # 반감기 — 앙상블 (휴리스틱 A + RF C, log10 정규화 평균). RF 미가용 시 휴리스틱 단독 fallback.
    # 2026-06-09: 단일 추정기 대신 두 상보적 모델 결합 (A=SST-14 절대 스케일, C=PEPlife2 데이터 일반화).
    if seq:
        try:
            from .halflife_ensemble import ensemble_halflife
            ens = ensemble_halflife(seq, modifications=[])
            out["half_life_h"] = ens["half_life_h"]
            out["half_life_heuristic_h"] = ens["half_life_heuristic_h"]
            out["half_life_rf_h"] = ens["half_life_rf_h"]
            out["halflife_source"] = ens["halflife_source"]
            out["stability_norm"] = ens["stability_norm"]
        except Exception as exc:  # pragma: no cover — 앙상블 실패 시 레거시 휴리스틱
            logger.warning("halflife ensemble 실패(%s) → 휴리스틱 단독", exc)
            hl = float(_predict_half_life(seq, [])) if _HAS_HALFLIFE else float("nan")
            out["half_life_h"] = hl
            import math as _m
            out["stability_norm"] = (round(min(1.0, max(0.0, (_m.log10(hl) - _m.log10(0.02)) /
                                     (_m.log10(200.0) - _m.log10(0.02)))), 4)
                                     if hl == hl and hl > 0 else 0.0)
    else:
        out["half_life_h"] = float("nan")
        out["stability_norm"] = 0.0

    # ADMET-reasonableness (물성 surrogate)
    if _HAS_PHARMA and seq:
        try:
            pp = _PharmaProperties(reference_seq=reference_seq)
            # Cys3-Cys14 SS bond → pI 계산 시 해당 Cys 제외 (0-indexed)
            cys = {i for i, a in enumerate(seq) if a == "C"}
            ss = {min(cys), max(cys)} if len(cys) >= 2 else None
            props = {
                "gravy": round(pp.calculate_gravy(seq), 4),
                "boman_index": round(pp.calculate_boman_index(seq), 4),
                "instability_index": round(pp.calculate_instability_index(seq), 4),
                "aliphatic_index": round(pp.calculate_aliphatic_index(seq), 4),
                "pi": pp.calculate_pi(seq, ss_bond_cysteines=ss),
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("PharmaProperties 실패(%s)", exc)
            props = {}
    else:
        props = {}
    out.update(props)
    out["admet_score"] = admet_reasonableness(props) if props else 0.0
    return out


# ---------------------------------------------------------------------------
# pepADMET 실제 독성 ML 추론 (B, 2026-06-09) — physicochemical surrogate 보강
# ---------------------------------------------------------------------------
# pepADMET GNN(toxicity_early_stop.pth)을 pepadmet conda env subprocess 로 배치 추론.
# 독성 후보는 admet_score 에 페널티 → 안전성을 다목적 랭킹에 반영.
_TOXIC_ADMET_PENALTY = 0.4   # native보다 심하게 독성↑ 후보의 admet_score 곱셈 페널티 하한
# 2026-06-10: pepADMET binary(is_toxic)는 비변별적 — oxytocin·native SST-14 까지 전부 toxic 판정.
# 따라서 게이트는 hc50 **연속값을 native 대비 상대(home-advantage)** 로 평가한다 (Δmargin 과 대칭).
_HC50_NATIVE_TOLERANCE = 5.0   # native hc50 ±이 밴드는 "동급"으로 간주 (페널티 없음)
_HC50_PENALTY_SCALE = 200.0    # native 초과 독성분(hc50)당 선형 감점 스케일
_NATIVE_HC50: Optional[float] = None  # native SST-14 hc50 기준선 (지연 로드)


def _native_hc50_baseline() -> Optional[float]:
    """native SST-14 의 pepADMET hc50 기준선 (home-advantage). 1회 로드 후 캐시."""
    global _NATIVE_HC50
    if _NATIVE_HC50 is not None:
        return _NATIVE_HC50
    import json as _json
    from pathlib import Path as _P
    # multiobjective.py -> pyrosetta_flow -> repo_root
    path = _P(__file__).resolve().parents[1] / "data/somatostatin_receptor/curated/native_toxicity_baseline.json"
    try:
        if path.exists():
            _NATIVE_HC50 = float(_json.loads(path.read_text()).get("hc50"))
    except Exception as exc:  # pragma: no cover
        logger.warning("native hc50 baseline 로드 실패(%s)", exc)
    return _NATIVE_HC50


def predict_toxicity_for_sequences(sequences: List[str]) -> Dict[str, Dict[str, Any]]:
    """pepADMET 독성 배치 추론. {sequence: result}. 미설치/실패 시 빈 dict (graceful)."""
    seqs = [s for s in dict.fromkeys(sequences) if s]  # 중복 제거, 순서 유지
    if not seqs:
        return {}
    try:
        from .pepadmet_runner import predict_toxicity_batch
    except Exception as exc:  # pragma: no cover
        logger.warning("pepadmet_runner import 실패(%s) — 독성 skip", exc)
        return {}
    try:
        results = predict_toxicity_batch(seqs)
    except Exception as exc:
        logger.warning("pepADMET 독성 추론 실패(%s) — skip", exc)
        return {}
    return {r.get("sequence"): r for r in results if isinstance(r, dict) and r.get("sequence")}


def apply_toxicity_to_extra(extra: Dict[str, Any], tox: Dict[str, Any]) -> None:
    """pepADMET 독성 결과를 extra_scores 에 기록하고 admet_score 에 페널티 반영 (in-place).

    available=False(추론 불가)면 admet_score 를 건드리지 않는다 (fail-closed: 가짜 안전판정 X).

    2026-06-10 수정: binary is_toxic 는 비변별적(전부 True)이라 게이트에 **쓰지 않는다**. 대신
    hc50 을 native SST-14 기준선 대비(home-advantage)로 평가한다 — Δmargin 과 동일 철학.
      - hc50_vs_native = hc50 − native_hc50  (>0 = native보다 안전, <0 = 더 독성)
      - native ±_HC50_NATIVE_TOLERANCE 밴드 = "동급" → 페널티 없음
      - 그보다 독성↑ 일 때만 초과분에 선형 비례 페널티(하한 _TOXIC_ADMET_PENALTY)
    """
    if not tox or not tox.get("available"):
        return
    extra["pepadmet_toxic"] = bool(tox.get("is_toxic"))          # 기록만 (비변별적, 게이트 미사용)
    extra["pepadmet_toxicity_type"] = tox.get("toxicity_type")
    extra["pepadmet_binary_toxicity"] = tox.get("binary_toxicity")
    hc50 = tox.get("hc50")
    extra["pepadmet_hc50"] = hc50

    native_hc50 = _native_hc50_baseline()
    if not isinstance(hc50, (int, float)) or native_hc50 is None:
        return
    delta = hc50 - native_hc50                                   # >0 안전, <0 독성↑
    extra["hc50_vs_native"] = round(delta, 3)
    more_toxic = delta < -_HC50_NATIVE_TOLERANCE
    extra["more_toxic_than_native"] = bool(more_toxic)
    if more_toxic:
        excess = -(delta + _HC50_NATIVE_TOLERANCE)               # native 초과 독성분 (>0)
        factor = max(_TOXIC_ADMET_PENALTY, 1.0 - excess / _HC50_PENALTY_SCALE)
        base = extra.get("admet_score")
        if isinstance(base, (int, float)):
            extra["admet_score"] = round(base * factor, 4)


def enrich_candidates(
    candidates: List[Dict[str, Any]],
    reference_seq: str = NATIVE_SST14,
) -> List[Dict[str, Any]]:
    """각 후보 dict 에 cheap_objectives 결과를 병합한다 (in-place + 반환).

    후보는 'sequence' 키를 가져야 한다. 결과는 후보 dict 최상위와
    extra_scores(존재 시)에 모두 기록한다.
    """
    for c in candidates:
        seq = c.get("sequence") or c.get("seq") or ""
        obj = cheap_objectives(seq, reference_seq=reference_seq)
        for k, v in obj.items():
            if k == "sequence":
                continue
            c[k] = v
        es = c.setdefault("extra_scores", {})
        if isinstance(es, dict):
            es.update({k: v for k, v in obj.items() if k != "sequence"})
        # pareto_ranking 키 매핑: stability(반감기), druggability(ADMET)
        c.setdefault("stability", obj["stability_norm"])
        c.setdefault("druggability", obj["admet_score"])
    return candidates


# ---------------------------------------------------------------------------
# 다목적 스칼라 점수 (UI 표시 / 단일 랭킹용 보조)
# ---------------------------------------------------------------------------

@dataclass
class ObjectiveWeights:
    ddg: float = 0.40           # 결합 (최우선)
    selectivity: float = 0.25   # SSTR2 선택성
    stability: float = 0.20     # 반감기
    admet: float = 0.15         # ADMET 합리성


def multiobjective_scalar(
    cand: Dict[str, Any],
    weights: ObjectiveWeights = ObjectiveWeights(),
    ddg_ref: float = 0.0,
    ddg_scale: float = 50.0,
) -> float:
    """후보의 다목적 스칼라 점수(높을수록 좋음). UI 정렬 보조용.

    ddg 는 음수가 좋으므로 (ddg_ref - ddg)/ddg_scale 로 0~1 근사.
    selectivity_margin 은 양수가 좋음 → 0~1 포화.
    stability/admet 은 이미 0~1.
    """
    ddg = float(cand.get("ddg", cand.get("ddG", 0.0)))
    s_ddg = max(0.0, min(1.0, (ddg_ref - ddg) / ddg_scale))
    margin = float(cand.get("selectivity_margin", 0.0))
    s_sel = max(0.0, min(1.0, margin / 20.0)) if margin == margin else 0.0
    s_stab = float(cand.get("stability_norm", cand.get("stability", 0.0)))
    s_admet = float(cand.get("admet_score", cand.get("druggability", 0.0)))
    score = (
        weights.ddg * s_ddg
        + weights.selectivity * s_sel
        + weights.stability * s_stab
        + weights.admet * s_admet
    )
    return round(score, 4)


def select_topk_for_selectivity(
    candidates: List[Dict[str, Any]],
    k: int = 5,
    clash_max: float = 10.0,
) -> List[Dict[str, Any]]:
    """선택성(비싼 off-target 도킹) 대상 top-K 선별.

    clash 게이트 통과 후보를 ddg 오름차순(좋은 순)으로 정렬해 상위 K.
    """
    feasible = [
        c for c in candidates
        if float(c.get("clash_score", 999.0)) <= clash_max
    ]
    pool = feasible or candidates
    pool = sorted(pool, key=lambda c: float(c.get("ddg", c.get("ddG", 999.0))))
    return pool[:k]


# ---------------------------------------------------------------------------
# Layer 1 — selectivity (top-K, 실제 off-target PyRosetta 도킹) — 비쌈
# ---------------------------------------------------------------------------

# 2026-06-09: 큐레이션된 단일체인 off-target 수용체 (SSTR2 프레임에 0.93~0.95 사전정렬).
# 원본 *_aligned.pdb 는 G단백질 포함 멀티체인이라 부적합 → CA-overlap 으로 수용체 체인
# 식별·추출(SSTR1=D, SSTR3=A, SSTR4=R, SSTR5=R). offtarget_dock.py --pre-aligned 로 사용.
DEFAULT_OFFTARGET_RECEPTORS = {
    "SSTR1": "data/somatostatin_receptor/curated/SSTR1_receptor.pdb",
    "SSTR3": "data/somatostatin_receptor/curated/SSTR3_receptor.pdb",
    "SSTR4": "data/somatostatin_receptor/curated/SSTR4_receptor.pdb",
    "SSTR5": "data/somatostatin_receptor/curated/SSTR5_receptor.pdb",
}

_NATIVE_BASELINE_CACHE: Dict[str, Any] = {}


def _native_selectivity_baseline(root) -> Optional[float]:
    """native SST-14 의 동일프로토콜 selectivity_margin (home-advantage 기준선). 캐시."""
    import json as _json
    from pathlib import Path as _P
    key = str(root)
    if key in _NATIVE_BASELINE_CACHE:
        return _NATIVE_BASELINE_CACHE[key]
    path = _P(root) / "data/somatostatin_receptor/curated/native_selectivity_baseline.json"
    val = None
    try:
        if path.exists():
            val = float(_json.loads(path.read_text()).get("margin"))
    except Exception as exc:  # pragma: no cover
        logger.warning("native baseline 로드 실패(%s)", exc)
    _NATIVE_BASELINE_CACHE[key] = val
    return val


def screen_selectivity(
    sstr2_complex_pdb: str,
    on_target_ddg: float,
    offtarget_receptors: Optional[Dict[str, str]] = None,
    repo_root: Optional[str] = None,
    conda_env: str = "bio-tools",
    timeout: int = 600,
    margin_min: float = 10.0,
    offtarget_max_allowed: float = -15.0,
) -> Dict[str, Any]:
    """한 후보의 SSTR2 정밀화 복합체를 SSTR1/3/4/5 에 off-target 도킹하여 선택성 계산.

    실제 PyRosetta(offtarget_dock.py via step05b.dock_against_offtarget)를 호출하므로
    비싸다(수용체당 수분). top-K 후보에만 사용할 것.

    Returns dict:
        offtarget_ddg: {receptor: ddg}, selectivity_margin, worst_offtarget,
        is_selective(bool), gate_pass(bool)
      selectivity_margin = min(offtarget_ddg) - sstr2_ddg
        (양수 = SSTR2 에 더 강하게 결합 = 선택적, G-2 SSOT)
    """
    import os
    from pathlib import Path as _P

    offtarget_receptors = offtarget_receptors or DEFAULT_OFFTARGET_RECEPTORS
    root = _P(repo_root) if repo_root else _P(__file__).resolve().parents[1]

    try:
        from AG_src.pipeline.step05b_selectivity import (
            dock_against_offtarget,
            compute_selectivity_margin,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("selectivity import 실패(%s) — skip", exc)
        return {"selectivity_margin": None, "error": str(exc)}

    cfg = {
        "selectivity": {"offtarget_timeout_sec": timeout},
        "rosetta": {"conda_env": conda_env},
    }
    # 2026-06-10: on-target SSTR2(동일 프로토콜, baseline) + off-target SSTR1/3/4/5 를 **병렬** 도킹.
    #   - SSTR2 도 off-target 과 동일 transplant+pre-relax 로 재서 margin 편향 제거(이전 아티팩트 수정).
    #   - 수용체 병렬화로 in-loop 비용 절감(순차 ~25분 → 병렬 ~6분/후보).
    from concurrent.futures import ThreadPoolExecutor as _TPE
    receptors: Dict[str, str] = {
        "SSTR2": str(root / "data/somatostatin_receptor/curated/SSTR2_receptor.pdb")
    }
    for name, rel in offtarget_receptors.items():
        receptors[name] = rel if os.path.isabs(rel) else str(root / rel)
    receptors = {n: p for n, p in receptors.items() if _P(p).exists()}

    def _dock_one(item):
        name, rpath = item
        try:
            v = float(dock_against_offtarget(
                candidate_pdb=sstr2_complex_pdb, receptor_pdb=rpath, engine="pyrosetta",
                config=cfg, on_target_score=on_target_ddg, sstr2_complex_pdb=sstr2_complex_pdb,
            ))
            return name, (round(v, 4) if v == v else None)   # NaN(fail-closed) → None
        except Exception as exc:
            logger.warning("도킹 실패 %s: %s", name, exc)
            return name, None

    with _TPE(max_workers=min(6, len(receptors)) or 1) as _ex:
        dock_results = dict(_ex.map(_dock_one, list(receptors.items())))

    sstr2_ddg_same = dock_results.pop("SSTR2", None)
    offtarget_ddg = {n: v for n, v in dock_results.items() if v is not None}
    if not offtarget_ddg:
        return {"selectivity_margin": None, "offtarget_ddg": {}}

    # baseline: 동일 프로토콜 우선, 실패 시 루프 ddg 폴백
    baseline = sstr2_ddg_same if sstr2_ddg_same is not None else on_target_ddg
    worst = min(offtarget_ddg.values())                 # 가장 강한(낮은) off-target
    margin = worst - baseline                             # 양수 = SSTR2 가 더 강함(선택적)
    # 2026-06-10 home-advantage 보정: native SST-14 도 동일 프로토콜에서 +margin(SSTR2 수용체가
    # source 복합체 유래) → 절대 margin 은 편향. native baseline 대비 Δmargin 이 진짜 선택성 신호.
    nat_margin = _native_selectivity_baseline(root)
    delta_margin = round(margin - nat_margin, 4) if nat_margin is not None else None
    out: Dict[str, Any] = {
        "offtarget_ddg": offtarget_ddg,
        "worst_offtarget": worst,
        "sstr2_ddg_sameprotocol": sstr2_ddg_same,
        "sstr2_ddg_loop": on_target_ddg,
        "selectivity_margin": round(margin, 4),
        "native_margin": nat_margin,
        "delta_margin": delta_margin,                 # >0 = native 보다 SSTR2-선택적 (home-adv 보정)
        "more_selective_than_native": (delta_margin is not None and delta_margin > 0),
        "is_selective": margin >= margin_min,
    }
    try:
        out["selectivity_detail"] = compute_selectivity_margin(
            seq_id="cand", sstr2_score=baseline, offtarget_scores=offtarget_ddg,
            margin_min=margin_min, offtarget_max_allowed=offtarget_max_allowed,
        )
    except Exception:
        pass
    return out
