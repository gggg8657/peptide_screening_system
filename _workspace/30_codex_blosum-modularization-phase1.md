# Task #30 — BLOSUM 모듈화 Phase 1

## 배경
5/15 보고서 (`_workspace/release/sod-2026-05-15-blosum-strategy-modularization-review.md`) Phase 1 적용. **기존 동작 보존 + 모듈 추상화만** — Phase 2-5 (ESM-Scan, ProteinMPNN, DualB1B2, A/B 실험)는 후속.

## 의뢰

### 1. 신설 디렉토리
```
pipeline_local/strategies/
  __init__.py
  base.py       # MutationStrategy Protocol + StrategyConfig dataclass
  registry.py   # name → class 매핑 + get_strategy()
  blosum.py     # 기존 BlosumStrategy 구현 (현재 step03b 로직 이전)
```

### 2. base.py
```python
from typing import Protocol
from pipeline_local.schemas.io_schemas import Step03bOutput

class MutationStrategy(Protocol):
    name: str  # "blosum" | "proteinmpnn" | "esm_scan" | "dual_b1_b2"

    def generate(self, config: dict) -> Step03bOutput: ...
    def validate_env(self) -> tuple[bool, str | None]: ...
```

### 3. blosum.py — 기존 로직 이전
- `pipeline_local/steps/step03b_blosum_mutation.py` 의 다음 함수 + 데이터를 이전:
  - `BLOSUM62`, `KYTE_DOOLITTLE`, `load_blosum62`, `get_blosum_score`, `get_plausible_substitutions`
  - `validate_constraints`, `_compute_hydrophobicity`, `hydrophobicity_check`, `compute_blosum_distance`
  - `generate_single_mutants`, `generate_combinatorial_variants`
  - `run_approach_b` 로직 (BlosumStrategy.generate()로)
- `class BlosumStrategy:` 의 `name = "blosum"`, `generate(config)`, `validate_env()` (항상 True)

### 4. registry.py
```python
from .blosum import BlosumStrategy

STRATEGIES = {
    "blosum": BlosumStrategy,
}

def get_strategy(name: str):
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'. Available: {list(STRATEGIES)}")
    return STRATEGIES[name]()
```

### 5. step03b_blosum_mutation.py — dispatcher로 축소
```python
"""Step 03b: Approach B BLOSUM62 mutation (dispatcher).

기존 구현은 pipeline_local/strategies/blosum.py로 이전됨.
config.approach_b.strategy 키를 통해 다른 strategy 선택 가능 (Phase 2 이후).
"""
from pipeline_local.schemas.io_schemas import Step03bOutput
from pipeline_local.strategies.registry import get_strategy


def run_approach_b(config: dict) -> Step03bOutput:
    ab_cfg = config.get("approach_b", config)
    strategy_name = ab_cfg.get("strategy", "blosum")
    strategy = get_strategy(strategy_name)
    ok, err = strategy.validate_env()
    if not ok:
        raise RuntimeError(f"Strategy '{strategy_name}' 환경 검증 실패: {err}")
    return strategy.generate(config)
```

### 6. 검증 (필수)
- 기존 동작 보존 — `run_approach_b(existing_config)` 결과가 동일
- pytest `pipeline_local/tests/` 기존 테스트 전부 통과
- `from pipeline_local.steps.step03b_blosum_mutation import run_approach_b` import 호환 (orchestrator.py:121 호환)
- 신규 unit test: `pipeline_local/tests/test_strategies_blosum.py` (Strategy Protocol 준수 + Phase 1 smoke)

### 제약
- **branch 신설**: `feat/blosum-strategy-phase1`
- **PR title**: `feat(strategies): BLOSUM Phase 1 — Strategy Protocol + registry + blosum 이전 (동작 보존)`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 손대지 말 것
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- Python 3.11.15 (bio-tools conda env)
- 마감: PR 생성 + test 결과 + 변경/신설 파일 보고
