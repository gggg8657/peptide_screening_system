"""Step 03b: Approach B mutation strategy dispatcher.

기존 BLOSUM 구현은 pipeline_local/strategies/blosum.py로 이전됨.
config.approach_b.strategy 키를 통해 4 strategy 선택 가능:
  - dual_b1_b2 (default): ProteinMPNN ∪ ESM-Scan Union — 약품 합성 펩타이드 탐색용
  - proteinmpnn: structure-aware (receptor binding 관점)
  - esm_scan: sequence-context (zero-shot ESM-2)
  - blosum: 평가 전용 (자연 진화 보수성, drug design에는 부적합)

설계 근거 (2026-05-19):
- BLOSUM은 자연 진화 mutation 빈도 기반 → 약품용 합성 펩타이드 탐색에 부적합
- A/B 실험 (`_workspace/release/sod-2026-05-19-strategy-ab-experiment.md`)
  - blosum: hamming 1.12 (보수적, drug space 못 봄)
  - proteinmpnn: hamming 7.60 (structure-aware 최광범위)
  - dual_b1_b2: hamming 7.32 (ProteinMPNN+ESM 통합)
- 사용자 결정: dual_b1_b2 default. BLOSUM은 평가만.
"""

from __future__ import annotations

from pipeline_local.schemas.io_schemas import Step03bOutput
from pipeline_local.strategies.registry import STRATEGIES, get_strategy

# 약품 합성 펩타이드 탐색에 적합한 default — Phase 5 A/B 실험 결과 채택 (2026-05-19)
DEFAULT_STRATEGY = "dual_b1_b2"


def run_approach_b(config: dict) -> Step03bOutput:
    ab_cfg = config.get("approach_b", config)
    strategy_name = ab_cfg.get("strategy", DEFAULT_STRATEGY)

    # Backward compatibility: before strategy dispatch existed, approach_b.strategy
    # meant the BLOSUM combinatorial generation mode ("random" or "greedy").
    if strategy_name not in STRATEGIES:
        strategy_name = "blosum"

    strategy = get_strategy(strategy_name)
    ok, err = strategy.validate_env()
    if not ok:
        raise RuntimeError(f"Strategy '{strategy_name}' 환경 검증 실패: {err}")
    return strategy.generate(config)
