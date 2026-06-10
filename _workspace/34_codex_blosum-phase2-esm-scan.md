# Task #34 — BLOSUM Phase 2: ESM-Scan strategy 구현

## 배경
PR #54로 Phase 1 (모듈화) 완료. 이제 BLOSUM 외 실 변이 strategy 추가.
researcher 보고서 (sod-2026-05-15-blosum-mutation-strategy-research.md): ESM-Scan zero-shot scoring으로 BLOSUM 대체. LOW 난이도.

## 의뢰

### 1. 신규 strategy 파일
`pipeline_local/strategies/esm_scan.py` 신설:
```python
class ESMScanStrategy:
    name = "esm_scan"

    def generate(self, config: dict) -> Step03bOutput: ...
    def validate_env(self) -> tuple[bool, str | None]: ...
```

### 2. 구현 원칙
- **변이 생성**: seed sequence (SST-14) 의 각 *가변* position (fixed_positions 제외) 에서
  - ESM-2 (esm2_t33_650M_UR50D 등) 사용하여 위치별 amino acid log-probability 계산
  - score_quantile (config) 이상의 substitution만 후보로 채택
- **fixed_positions 보존**: FWKT + Cys3-Cys14 그대로
- **scoring 교체**: BLOSUM score 대신 ESM log-prob delta
- **출력 형식**: Step03bOutput 그대로 (source="esm_scan"), VariantEntry.blosum_total_score는 계산해서 채움 (평가용)

### 3. 환경
- conda env: `bio-tools` (PyRosetta 설치됐지만 이건 ESM)
- ESM library: `pip install fair-esm` 또는 huggingface `transformers` + `facebook/esm2_t33_650M_UR50D`
- GPU: H100 ×4 중 device 2 (`CUDA_VISIBLE_DEVICES=2`)
- 모델 로드 시간 ~30초, 추론 ~1초/시퀀스

### 4. config 스키마 (yaml)
```yaml
approach_b:
  enabled: true
  strategy: "esm_scan"
  seed_sequence: "AGCKNFFWKTFTSC"
  fixed_positions: {3: "C", 7: "F", 8: "W", 9: "K", 10: "T", 14: "C"}
  max_variants: 200
  esm_scan_opts:
    model: "esm2_t33_650M_UR50D"
    score_quantile: 0.7         # 상위 30% substitution만 채택
    device: "cuda:0"             # 또는 "cpu" fallback
    max_mutations_per_variant: 3
```

### 5. registry 업데이트
`pipeline_local/strategies/registry.py`:
```python
from .blosum import BlosumStrategy
from .esm_scan import ESMScanStrategy

STRATEGIES = {
    "blosum": BlosumStrategy,
    "esm_scan": ESMScanStrategy,
}
```

### 6. 검증 (필수)
- 신규 unit test: `pipeline_local/tests/test_strategies_esm_scan.py`
  - Strategy Protocol 준수
  - validate_env: ESM 패키지 미설치 시 (False, error msg) 반환
  - generate: mock ESM scoring으로 smoke (max_variants=5)
- 기존 test 412개 모두 통과 유지

### 7. validate_env fallback
- ESM 패키지 미설치 시 graceful 실패 (RuntimeError 발생 X, validate_env False 반환)
- 실 GPU 추론 없이도 smoke test 가능하도록 monkeypatch 지원

## 제약
- **branch 신설**: `feat/blosum-phase2-esm-scan`
- **PR title**: `feat(strategies): BLOSUM Phase 2 — ESM-Scan zero-shot scoring strategy`
- 본 세션 컨벤션: 다른 세션 미커밋 파일 손대지 말 것
- 작업 디렉토리: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/`
- 마감: PR 생성 + test 결과 + 변경/신설 파일 보고
