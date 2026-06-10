# BLOSUM 변이 전략 모듈화 가능성 검토

> **Task #24** — 사용자 요청: "Silo B-1 B-2 나눠서 모드로 선택해서 구동할 수 있도록 모듈화 잘 진행. 모듈별로 잘 만들고 I/O 잘 나눈다음에 검토하고 보고해봐 가능한지 불가능한지."
> **수행**: orchestrator (본 세션)
> **참조**: `sod-2026-05-15-blosum-mutation-strategy-research.md` (researcher 보고서)

## 결론: 가능 (LOW~MED 난이도)

기존 `step03b_blosum_mutation.py`의 I/O가 dataclass 기반으로 깔끔히 분리되어 있어 Strategy 패턴 추상화가 즉시 가능.

## 현재 I/O 구조 (이미 잘 정의됨)

### Input: `config: Dict[str, Any]` (yaml `approach_b` 섹션)
```yaml
approach_b:
  enabled: true
  strategy: "blosum"        # 신설 — strategy 디스패처 키
  seed_sequence: "AGCKNFFWKTFTSC"
  fixed_positions: {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"}
  max_variants: 200
  max_mutations_per_variant: 3
  # 이하 strategy별 옵션
  blosum_opts:
    min_blosum_score: 0
    hydrophobicity_max_delta: 2.0
  proteinmpnn_opts:
    num_seq_per_target: 100
    receptor_pdb: "data/somatostatin_receptor/SSTR2_*.pdb"
    sampling_temperature: 0.1
  esm_scan_opts:
    model: "esm2_t33_650M_UR50D"
    score_quantile: 0.7
```

### Output: `Step03bOutput` (dataclass, `pipeline_local/schemas/io_schemas.py`)
```python
@dataclass
class VariantEntry:
    variant_id: str
    sequence: str
    parent_sequence: str
    mutations: List[str]       # e.g. ["A1G", "K4R"]
    n_mutations: int
    blosum_total_score: int    # BLOSUM은 평가용 (모든 strategy 결과에 계산)
    source: str                # strategy 별칭 ("blosum"|"proteinmpnn"|"esm_scan"|"hybrid_b1_b2")

@dataclass
class Step03bOutput:
    variants: List[VariantEntry]
    seed_sequence: str
    fixed_positions: Dict[int, str]
    total_generated: int
    strategy: str
```

→ Strategy 추가가 데이터 모델 변경 없이 가능. `source` 필드만 strategy 이름으로 채우면 됨.

## 제안 모듈 구조

```
pipeline_local/steps/
  step03b_blosum_mutation.py           # 진입점 (현재 코드 유지 + dispatcher 추가)
  
pipeline_local/strategies/             # 신규 디렉토리
  __init__.py
  base.py                              # MutationStrategy Protocol
  blosum.py                            # 현재 generate_single_mutants/combinatorial 로직 이전
  proteinmpnn.py                       # 1순위 (Hybrid: ProteinMPNN + pharmacophore filter)
  esm_scan.py                          # 2순위 (ESM-Scan zero-shot scoring)
  dual_b1_b2.py                        # Silo B-1 + B-2 union 실행 (사용자 요청)
  registry.py                          # name → class 매핑
```

### `base.py`
```python
from typing import Protocol
from pipeline_local.schemas.io_schemas import Step03bOutput

class MutationStrategy(Protocol):
    name: str  # "blosum" | "proteinmpnn" | "esm_scan" | "dual_b1_b2"

    def generate(self, config: dict) -> Step03bOutput:
        """변이체 생성. config는 approach_b 섹션."""
        ...

    def validate_env(self) -> tuple[bool, str | None]:
        """환경 검증 (conda env, GPU, receptor PDB 등). 실패 시 (False, 에러)."""
        ...
```

### `registry.py`
```python
from .blosum import BlosumStrategy
from .proteinmpnn import ProteinMPNNStrategy
from .esm_scan import ESMScanStrategy
from .dual_b1_b2 import DualB1B2Strategy

STRATEGIES = {
    "blosum": BlosumStrategy,
    "proteinmpnn": ProteinMPNNStrategy,
    "esm_scan": ESMScanStrategy,
    "dual_b1_b2": DualB1B2Strategy,  # 사용자 요청 모드: B-1 + B-2 union
}

def get_strategy(name: str) -> MutationStrategy:
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'. Available: {list(STRATEGIES)}")
    return STRATEGIES[name]()
```

### `step03b_blosum_mutation.py` (dispatcher만)
```python
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

### `dual_b1_b2.py` (사용자 요청 핵심 모드)
```python
class DualB1B2Strategy:
    name = "dual_b1_b2"

    def __init__(self):
        self.b1 = ProteinMPNNStrategy()  # 1순위
        self.b2 = ESMScanStrategy()      # 2순위

    def validate_env(self):
        ok1, err1 = self.b1.validate_env()
        ok2, err2 = self.b2.validate_env()
        if not ok1:
            return False, f"B-1 (ProteinMPNN): {err1}"
        if not ok2:
            return False, f"B-2 (ESM-Scan): {err2}"
        return True, None

    def generate(self, config: dict) -> Step03bOutput:
        out1 = self.b1.generate(config)
        out2 = self.b2.generate(config)
        merged = self._merge_with_provenance(out1.variants, out2.variants)
        return Step03bOutput(
            variants=merged,
            seed_sequence=out1.seed_sequence,
            fixed_positions=out1.fixed_positions,
            total_generated=len(merged),
            strategy="dual_b1_b2",
        )

    def _merge_with_provenance(self, v1: List[VariantEntry], v2: List[VariantEntry]) -> List[VariantEntry]:
        """
        - 중복 sequence는 양쪽 source를 'b1+b2' 로 합침
        - variant_id 재부여
        - source 필드에 provenance 보존
        """
        ...
```

## 단계별 구현 난이도

| Strategy | 구현 난이도 | 환경 의존 | 의존 자원 |
|---|---|---|---|
| **blosum** (기존) | DONE | 내장 | - |
| **esm_scan** | LOW | ESM-2 weight (~2GB) | GPU H100 ×1 |
| **proteinmpnn** | MED | ProteinMPNN conda env + SSTR2-SST14 complex PDB | GPU H100 ×1 |
| **dual_b1_b2** | LOW (위 두 개 이후) | 위 두 개 합 | 위 두 개 합 |

## 호환성 영향

| 기존 코드 | 변경 영향 |
|---|---|
| `orchestrator.py: step03b_blosum_mutation.run_approach_b(config)` | 호출 시그니처 동일, **변경 없음** |
| `pipeline_config.yaml: approach_b.strategy` | 키 추가만 (default "blosum") |
| `Step03bOutput` / `VariantEntry` dataclass | **변경 없음** |
| `step04_qc`, `step05_docking` 이후 단계 | source 필드 새 값 허용 (assertion 점검 필요) |

## 검증 필요 항목 (researcher 보고서 기반)

- **ProteinMPNN의 14aa 환형 펩타이드 fixed_positions quality** — 문헌이 단백질 단위 적용 위주. 우선 ESM-Scan으로 시작 후 ProteinMPNN smoke test.
- **SSTR2-SST14 complex PDB** — `data/somatostatin_receptor/SSTR2_*.pdb` 확인 (BE PR #41에서 preflight_check 함수로 확인 가능). 7YAE는 octreotide 기준이라 SST14 native conformation 필요 시 alphafold prediction 또는 homology modeling.
- **ESM-Scan 14aa context window** — ESM-2의 BERT-like 모델은 short context도 처리 가능하나 confidence 낮을 수 있음.

## 권고 (구현 순서)

1. **Phase 1 (~반나절)**: 디렉토리 + Protocol + registry + BLOSUM 이전 (기존 코드 그대로 wrap, 동작 동일).
2. **Phase 2 (~1일)**: ESM-Scan strategy 구현 (LOW 난이도, 즉시 비교 가능).
3. **Phase 3 (~1-2일)**: ProteinMPNN strategy 구현 + SSTR2-SST14 PDB 준비.
4. **Phase 4 (~반나절)**: DualB1B2 + merge 로직 + iteration 비교 메트릭.
5. **Phase 5**: A/B 실험 — 동일 seed 1 iteration에서 blosum vs esm_scan vs proteinmpnn vs dual_b1_b2 비교 보고.

## 사용자 결정 (2026-05-15)

- **구현 일정**: **다음 SOD로 이월** (오늘은 Task #25 FE 집중)
- **dual 모드 merge 정책**: **Union (중복 보존 + source merge)**
- **A/B 실험 자동화 / GPU 자원 정책**: 다음 SOD 구현 시 추가 결정

## (이월) 추후 결정 필요

- **dual 모드 merge 정책**: union (중복 보존, source merge) vs intersect (양쪽에서 나온 것만) vs prioritized (B-1 우선, 부족 시 B-2 보충)
- **A/B 실험 자동화**: 매 run마다 4 strategy 모두 실행 vs config에서 선택
- **ProteinMPNN GPU 자원 정책**: Boltz/FlexPepDock과 동시 실행 가능 여부 (lock 필요?)

## 결론 요약

**가능. 권장.**
- 기존 I/O 추상화가 깔끔해서 Strategy 패턴 wrap 가능
- 사용자 요청 "B-1/B-2 모드 선택 + 모듈화"는 위 구조로 직접 충족
- 구현 난이도 LOW(blosum/esm_scan) ~ MED(proteinmpnn)
- 후속 작업: 위 5 Phase 단계별 PR
