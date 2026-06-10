from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List
import random

from .schema import CandidateResult, FlowConfig

AA_NO_CYS = list("ADEFGHIKLMNPQRSTVWY")


def notebook_mapping() -> List[Dict[str, str]]:
    """Notebook 단계와 파이프라인 모듈 단계의 대응표."""
    return [
        {"notebook": "SSTR2-SST14 구조 입력 준비", "pipeline": "validate_template_pose"},
        {"notebook": "SST14 변이 생성", "pipeline": "generate_random_mutant"},
        {"notebook": "mutate -> dock -> ddG 평가", "pipeline": "run_mutate_then_dock_iteration"},
        {"notebook": "후보 선별 + 다음 실험 가설", "pipeline": "run_planner_critic_loop"},
        {"notebook": "실험 요약 기록", "pipeline": "run_reporter_and_emit_artifacts"},
    ]


def validate_config(config: FlowConfig) -> None:
    if not Path(config.template_pdb).exists():
        raise FileNotFoundError(f"Template PDB not found: {config.template_pdb}")
    if config.n_candidates < 1:
        raise ValueError("n_candidates must be >= 1")
    if not config.design_positions:
        raise ValueError("design_positions must not be empty")


MAX_RANDOM_MUTATIONS = 3


def generate_random_mutant(
    original_seq: str,
    design_positions: List[int],
    rng: random.Random,
    n_mutations: int | None = None,
    max_random_mutations: int = MAX_RANDOM_MUTATIONS,
) -> str:
    seq = list(original_seq)
    valid_positions = [p for p in design_positions if 1 <= p <= len(seq)]
    if not valid_positions:
        return original_seq
    if n_mutations is None:
        n_mutations = rng.randint(1, max(1, min(max_random_mutations, len(valid_positions))))
    mutate_positions = rng.sample(valid_positions, k=min(n_mutations, len(valid_positions)))
    for pos in mutate_positions:
        idx = pos - 1
        current = seq[idx]
        candidates = [aa for aa in AA_NO_CYS if aa != current]
        seq[idx] = rng.choice(candidates)
    return "".join(seq)


def generate_guided_mutant(
    original_seq: str,
    design_positions: List[int],
    guidance: Dict[str, Any],
    rng: random.Random,
) -> str:
    """Planner guidance를 반영한 mutation 생성.

    guidance = {
        "focus_positions": [5, 6],
        "suggested_mutations": {"5": ["W", "F"], "6": ["E", "D"]},
    }
    """
    seq = list(original_seq)
    focus = guidance.get("focus_positions", [])
    suggestions = guidance.get("suggested_mutations", {})

    # focus_positions 중 design_positions에 있는 것만 사용
    valid_focus = [p for p in focus if p in design_positions and 1 <= p <= len(seq)]

    if not valid_focus:
        # guidance가 비어있으면 random fallback
        return generate_random_mutant(original_seq, design_positions, rng)

    # 1~MAX_RANDOM_MUTATIONS개 focus position 선택
    n_mut = rng.randint(1, max(1, min(MAX_RANDOM_MUTATIONS, len(valid_focus))))
    chosen = rng.sample(valid_focus, k=min(n_mut, len(valid_focus)))

    for pos in chosen:
        idx = pos - 1
        pos_key = str(pos)
        if pos_key in suggestions and suggestions[pos_key]:
            # Planner가 추천한 아미노산 중 현재와 다른 것 선택
            candidates = [aa for aa in suggestions[pos_key] if aa != seq[idx] and aa != "C"]
            if candidates:
                seq[idx] = rng.choice(candidates)
                continue
        # 추천 없으면 랜덤
        candidates = [aa for aa in AA_NO_CYS if aa != seq[idx]]
        seq[idx] = rng.choice(candidates)

    return "".join(seq)


def candidate_to_dict(candidate: CandidateResult) -> Dict[str, object]:
    return asdict(candidate)


def choose_objective_mode(requested: str, iteration: int) -> str:
    if requested in {"ddg_only", "ddg_plus_constraints"}:
        return requested
    # auto mode: 초반 탐색은 ddg_only, 이후는 제약 포함
    return "ddg_only" if iteration == 1 else "ddg_plus_constraints"


def get_bandit_guidance(records: List[Dict[str, Any]], n_focus: int = 3) -> Dict[str, Any]:
    """Create a PositionBandit, initialize from history, and return guidance dict.

    The returned dict is compatible with Planner's mutation_guidance format:
        {"focus_positions": [5, 6, 11], "source": "bandit_thompson"}
    """
    from .bandit import PositionBandit

    bandit = PositionBandit()
    bandit.initialize_from_history(records)
    focus = bandit.sample_focus_positions(n=n_focus)
    return {
        "focus_positions": focus,
        "source": "bandit_thompson",
        "arm_stats": {str(k): v for k, v in bandit.get_arm_stats().items()},
    }
