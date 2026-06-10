# Task #36 — BLOSUM Phase 4: DualB1B2 strategy (Union 정책)

## 배경
- Phase 1 ✅ PR #54 (모듈화)
- Phase 2 ✅ PR #55 (ESM-Scan)
- Phase 3 ✅ PR #56 (ProteinMPNN)
- 사용자 결정 (5/15): **dual merge 정책 = Union (중복 보존 + source merge)**

## 의뢰

### 1. 신규 strategy 파일
`pipeline_local/strategies/dual_b1_b2.py`:
```python
class DualB1B2Strategy:
    name = "dual_b1_b2"

    def __init__(self):
        from .proteinmpnn import ProteinMPNNStrategy
        from .esm_scan import ESMScanStrategy
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

    def _merge_with_provenance(self, v1, v2):
        """Union 정책 — 중복 sequence는 source를 'b1+b2'로 합침."""
        by_seq = {}
        for v in v1:
            v.source = "b1_proteinmpnn"
            by_seq[v.sequence] = v
        for v in v2:
            if v.sequence in by_seq:
                # 중복 — source merge
                existing = by_seq[v.sequence]
                existing.source = f"{existing.source}+b2_esm_scan"
            else:
                v.source = "b2_esm_scan"
                by_seq[v.sequence] = v
        # variant_id 재부여
        result = list(by_seq.values())
        for i, v in enumerate(result):
            v.variant_id = f"var_{i + 1:03d}"
        return result
```

### 2. config 스키마
```yaml
approach_b:
  strategy: "dual_b1_b2"
  seed_sequence: "AGCKNFFWKTFTSC"
  fixed_positions: {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"}
  max_variants: 200  # B-1 + B-2 union 후 cap (옵션)
  # B-1 (ProteinMPNN)
  proteinmpnn_opts:
    mode: "peptide_only"
    num_seq_per_target: 100
    sampling_temperature: 0.1
    fixed_positions: [3, 7, 8, 9, 10, 14]
  # B-2 (ESM-Scan)
  esm_scan_opts:
    model: "esm2_t33_650M_UR50D"
    score_quantile: 0.7
    max_mutations_per_variant: 3
```

### 3. registry 업데이트
```python
from .blosum import BlosumStrategy
from .esm_scan import ESMScanStrategy
from .proteinmpnn import ProteinMPNNStrategy
from .dual_b1_b2 import DualB1B2Strategy

STRATEGIES = {
    "blosum": BlosumStrategy,
    "esm_scan": ESMScanStrategy,
    "proteinmpnn": ProteinMPNNStrategy,
    "dual_b1_b2": DualB1B2Strategy,
}
```

### 4. max_variants cap (선택적)
- Union 결과 len > max_variants 시 두 가지 옵션:
  - **A**: 무작위 sample max_variants (sequence 중복 보존)
  - **B**: 단순 truncate (앞에서 max_variants개)
- 보고서에 어느 채택했는지 명시

### 5. 검증
- `pipeline_local/tests/test_strategies_dual_b1_b2.py`:
  - Strategy Protocol 준수
  - validate_env: B-1 또는 B-2 환경 실패 시 (False, "B-1: ..." 또는 "B-2: ...") 반환
  - generate: mock B-1, B-2 출력으로 smoke
  - Union 정책: 중복 sequence는 source "b1_proteinmpnn+b2_esm_scan"으로 합쳐짐
  - variant_id 재부여 (var_001, var_002, ...)
- 기존 test 모두 통과 유지

## 제약
- **branch 신설**: `feat/blosum-phase4-dual`
- **PR title**: `feat(strategies): BLOSUM Phase 4 — DualB1B2 strategy (ProteinMPNN ∪ ESM-Scan, Union merge)`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 손대지 말 것
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- 마감: PR 생성 + test 결과 보고
