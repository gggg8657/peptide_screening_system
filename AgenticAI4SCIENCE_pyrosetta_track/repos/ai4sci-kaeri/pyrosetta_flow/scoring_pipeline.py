"""scoring_pipeline.py
===================
대안 스코어링 체인 (god-object runner.py 에서 분리, 2026-06-09 P1).

FlexPepDock ddG 결과에 부가 스코어링을 적용한다 (각 단계 graceful skip):
  0. cheap objectives — 반감기/ADMET surrogate (multiobjective)
  1. GNINA rescore — CNN 도킹 스코어 (binary 없으면 dry-run)
  2. ECR consensus — GNINA+ddG 통합 순위
  3. Pareto ranking — NSGA-II 다목적 순위 (pymoo)
  4. BO suggest — 다음 iteration 추천 위치 (로그만)

runner.py 는 `_apply_alternative_scoring` 을 re-export 하여 하위호환을 유지한다.
GNINA/Pareto 옵셔널 의존은 본 모듈이 자체 보유. BO 는 bo_optimizer 인자(None 여부)로만 분기.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import CandidateResult

# ── 옵셔널 스코어링 의존 (graceful) ──────────────────────────────────────
batch_gnina_rescore = None  # type: ignore[assignment]
exponential_rank_consensus = None  # type: ignore[assignment]
_HAS_GNINA = False
try:
    from .gnina_rescoring import batch_gnina_rescore, exponential_rank_consensus  # type: ignore[assignment]
    _HAS_GNINA = True
except ImportError:  # pragma: no cover
    pass

pareto_rank_candidates = None  # type: ignore[assignment]
_HAS_PARETO = False
try:
    from .pareto_ranking import pareto_rank_candidates  # type: ignore[assignment]
    _HAS_PARETO = True
except ImportError:  # pragma: no cover
    pass


def _apply_alternative_scoring(
    candidates: List["CandidateResult"],
    iter_dir: "Path",
    iteration: int,
    bo_optimizer: Optional[Any] = None,
) -> List["CandidateResult"]:
    """FlexPepDock 결과에 대안 스코어링 체인을 적용합니다 (optional).

    각 단계는 독립적으로 graceful skip됩니다.

    파이프라인:
        0. cheap objectives — 반감기 + ADMET surrogate (모든 후보)
        1. GNINA rescore  — PDB 파일이 있으면 CNN 스코어 추가 (dry-run fallback)
        2. ECR consensus  — GNINA + ddG 통합 순위 (gnina 결과 있을 때만)
        3. Pareto ranking — NSGA-II 다목적 순위 (pymoo 필요)
        4. BO suggest     — 다음 iteration용 추천 위치/잔기 반환 (부수효과 없음)

    Args:
        candidates: FlexPepDock 결과 CandidateResult 리스트
        iter_dir: 현재 iteration PDB 파일 디렉토리
        iteration: 현재 iteration 번호 (로그용)
        bo_optimizer: 이미 생성된 BayesianPeptideOptimizer 인스턴스 (None이면 BO 단계 skip)

    Returns:
        candidates 리스트 (in-place 수정 + 반환). 각 CandidateResult.extra_scores 갱신.
    """
    if not candidates:
        return candidates

    prefix = f"  [alt-score iter{iteration:02d}]"

    # ------------------------------------------------------------------
    # Step 0: 다목적 cheap objectives — 반감기(half-life) + ADMET surrogate
    #   서열만으로 계산(저비용). 모든 후보에 적용. selectivity(off-target 실제
    #   도킹)는 비싸므로 top-K 에서만 별도 단계로 수행한다.
    #   honest disclaimer: half_life/admet 은 ranking surrogate (임상 수치 아님).
    # ------------------------------------------------------------------
    try:
        from .multiobjective import cheap_objectives
        for cand in candidates:
            obj = cheap_objectives(cand.sequence)
            cand.extra_scores.update({
                k: v for k, v in obj.items() if k != "sequence"
            })
        hl_vals = [c.extra_scores.get("half_life_h") for c in candidates
                   if c.extra_scores.get("half_life_h") == c.extra_scores.get("half_life_h")]
        if hl_vals:
            print(
                f"{prefix} cheap-objectives: half-life {min(hl_vals):.1f}~{max(hl_vals):.1f}h, "
                f"ADMET surrogate computed for {len(candidates)} candidates",
                file=sys.stderr,
            )
    except Exception as exc:
        print(f"{prefix} cheap-objectives failed (non-fatal): {exc}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Step 0.5: pepADMET 실제 독성 ML 추론 (배치 subprocess) → admet_score 페널티
    #   2026-06-09 B: pepADMET GNN(toxicity_early_stop.pth)을 pepadmet env 로 배치 추론.
    #   독성 후보는 admet_score 에 페널티. 미설치/실패 시 graceful skip (fail-closed: 가짜 안전판정 X).
    # ------------------------------------------------------------------
    try:
        import os as _os
        if _os.environ.get("SST_DISABLE_PEPADMET_TOX", "").lower() in ("1", "true", "yes"):
            raise RuntimeError("pepADMET toxicity disabled via SST_DISABLE_PEPADMET_TOX")
        from .multiobjective import predict_toxicity_for_sequences, apply_toxicity_to_extra
        tox_seqs = [c.sequence for c in candidates if not c.fail_reason and c.sequence]
        tox_map = predict_toxicity_for_sequences(tox_seqs)
        if tox_map:
            n_toxic = 0
            for cand in candidates:
                tox = tox_map.get(cand.sequence)
                if tox:
                    apply_toxicity_to_extra(cand.extra_scores, tox)
                    if tox.get("is_toxic"):
                        n_toxic += 1
            print(f"{prefix} pepADMET toxicity: {n_toxic}/{len(tox_map)} toxic (admet 페널티 반영)",
                  file=sys.stderr)
    except Exception as exc:
        print(f"{prefix} pepADMET toxicity skipped (non-fatal): {exc}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Step 1: GNINA rescore (optional, dry-run when binary missing)
    # ------------------------------------------------------------------
    gnina_scores_by_id: Dict[str, Dict[str, float]] = {}
    if _HAS_GNINA:
        pdb_paths: List[str] = []
        cand_ids: List[str] = []
        for cand in candidates:
            if cand.fail_reason:
                continue
            # cand_{NNN}.pdb 형태로 PDB 위치 추론
            try:
                num_str = cand.candidate_id.split("cand")[-1]
                pdb_path = iter_dir / f"cand_{int(num_str):03d}.pdb"
            except (ValueError, IndexError):
                continue
            if pdb_path.exists():
                pdb_paths.append(str(pdb_path))
                cand_ids.append(cand.candidate_id)

        if pdb_paths:
            try:
                gnina_results = batch_gnina_rescore(pdb_paths, max_workers=2)
                for cand_id, scores in zip(cand_ids, gnina_results):
                    gnina_scores_by_id[cand_id] = scores
                dry = any(s.get("gnina_dry_run") for s in gnina_results)
                mode_tag = "dry-run" if dry else "live"
                print(
                    f"{prefix} GNINA rescore {len(pdb_paths)} PDBs [{mode_tag}]",
                    file=sys.stderr,
                )
            except Exception as exc:
                print(
                    f"{prefix} GNINA rescore failed (non-fatal): {exc}",
                    file=sys.stderr,
                )

    # ------------------------------------------------------------------
    # Step 2: ECR consensus (GNINA scores 있으면 ddG와 통합)
    # ------------------------------------------------------------------
    ecr_by_id: Dict[str, float] = {}
    if _HAS_GNINA and gnina_scores_by_id:
        ecr_input: List[Dict] = []
        for cand in candidates:
            g = gnina_scores_by_id.get(cand.candidate_id, {})
            ecr_input.append({
                "candidate_id": cand.candidate_id,
                "ddg": cand.ddg,
                "gnina_cnn_score": g.get("gnina_cnn_score", float("nan")),
                "gnina_cnn_affinity": g.get("gnina_cnn_affinity", float("nan")),
                "gnina_vina_score": g.get("gnina_vina_score", float("nan")),
            })
        try:
            ecr_results = exponential_rank_consensus(
                ecr_input,
                score_keys=["ddg", "gnina_cnn_score", "gnina_cnn_affinity", "gnina_vina_score"],
            )
            for row in ecr_results:
                ecr_by_id[row["candidate_id"]] = float(row.get("ecr_score", 0.0))
            print(
                f"{prefix} ECR consensus computed for {len(ecr_results)} candidates",
                file=sys.stderr,
            )
        except Exception as exc:
            print(
                f"{prefix} ECR consensus failed (non-fatal): {exc}",
                file=sys.stderr,
            )

    # GNINA 및 ECR 스코어를 extra_scores에 저장 (Pareto 단계 이전)
    for cand in candidates:
        if cand.candidate_id in gnina_scores_by_id:
            cand.extra_scores.update(gnina_scores_by_id[cand.candidate_id])
        if cand.candidate_id in ecr_by_id:
            cand.extra_scores["ecr_score"] = ecr_by_id[cand.candidate_id]

    # ------------------------------------------------------------------
    # Step 3: Pareto ranking (pymoo 기반 NSGA-II)
    # ------------------------------------------------------------------
    if _HAS_PARETO:
        pareto_input: List[Dict] = []
        for cand in candidates:
            # stability: Step 0 에서 계산한 반감기 기반 surrogate(0~1, 높을수록 안정).
            #   부재 시 clash 기반 proxy 로 폴백.
            stability_val = cand.extra_scores.get("stability_norm")
            if stability_val is None:
                stability_val = max(0.0, 40.0 - cand.clash_score) / 40.0
            # druggability: ADMET surrogate(0~1). 부재 시 ECR 폴백.
            drug_val = cand.extra_scores.get("admet_score")
            if drug_val is None:
                drug_val = ecr_by_id.get(cand.candidate_id, 0.0)
            pareto_input.append({
                "candidate_id": cand.candidate_id,
                "ddG": cand.ddg,
                "stability": float(stability_val),      # 반감기 기반(높을수록 좋음)
                "druggability": float(drug_val),         # ADMET 합리성(높을수록 좋음)
                "diversity": 0.0,                         # diversity는 현재 미계산
                "hard_violations": 1 if cand.fail_reason else 0,
                "clash_score": cand.clash_score,
            })
        try:
            ranked = pareto_rank_candidates(pareto_input, clash_threshold=10.0)
            # pareto_rank, crowding_distance를 candidate extra_scores에 반영
            rank_map: Dict[str, Dict[str, Any]] = {
                r["candidate_id"]: {
                    "pareto_rank": r.get("pareto_rank", 999),
                    "crowding_distance": r.get("crowding_distance", 0.0),
                }
                for r in ranked
            }
            for cand in candidates:
                cand.extra_scores.update(rank_map.get(cand.candidate_id, {}))
            front0_count = sum(1 for r in ranked if r.get("pareto_rank", 999) == 0)
            print(
                f"{prefix} Pareto ranking done — front-0: {front0_count}/{len(ranked)} candidates",
                file=sys.stderr,
            )
        except Exception as exc:
            print(
                f"{prefix} Pareto ranking failed (non-fatal): {exc}",
                file=sys.stderr,
            )

    # ------------------------------------------------------------------
    # Step 4: Bayesian Optimization suggest (부수효과 없음 — 로그만)
    #   bo_optimizer 가 전달되면 BO 가용한 것 (runner 가 _HAS_BO 시에만 생성·전달).
    # ------------------------------------------------------------------
    if bo_optimizer is not None:
        valid_obs = [
            c for c in candidates
            if not c.fail_reason and c.ddg < 900
        ]
        if len(valid_obs) >= 2:
            try:
                obs_dicts = [
                    {
                        "sequence": c.sequence,
                        "ddg": c.ddg,
                        "ecr_score": ecr_by_id.get(c.candidate_id, 0.0),
                    }
                    for c in valid_obs
                ]
                bo_optimizer.fit(obs_dicts)
                suggestions = bo_optimizer.suggest(
                    n=3,
                    reference_seq=valid_obs[0].sequence,
                )
                if suggestions:
                    top_pos = [s.get("position") for s in suggestions[:3]]
                    print(
                        f"{prefix} BO suggest top-3 positions: {top_pos}",
                        file=sys.stderr,
                    )
            except Exception as exc:
                print(
                    f"{prefix} BO suggest failed (non-fatal): {exc}",
                    file=sys.stderr,
                )

    return candidates
