# Silo B — HIL SST-14 Mutant Generation

SST-14 (`AGCKNFFWKTFTSC`)을 템플릿으로 SSTR2 결합성을 개선한 돌연변이 후보를 생성하고,
Human-in-the-Loop(HIL) 3단계 게이트로 정제하는 파이프라인.

## 실행 흐름

```
Config → Constraint Compiler → Generator → Drugability Filter
  → Docking → Stability Estimator → Multi-Objective Scoring
  → HIL Gate 1 (static) → Gate 2 (docking triage) → Gate 3 (human)
  → Top Candidates
```

## 모듈 구조

| 모듈 | 파일 | 역할 |
|------|------|------|
| **Config** | `src/config.py` | Pydantic 기반 YAML 스키마 (30+ 모델, `extra=forbid`) |
| **Constraint** | `src/constraint_compiler.py` | frozen/pharmacophore/pairwise 제약 컴파일 + 시퀀스 검증 |
| **Generator** | `src/generator.py` | enumerate/sampling/GA-BO 전략 자동 선택, Hamming distance 기반 중복 제거 |
| **Filter** | `src/filters.py` | NG/DG deamidation, Met 산화, aggregation 필터 |
| **Docking** | `src/docking.py` | `DockingRunner` ABC — `PyRosettaDockingRunner` (FlexPepDock) + `MockDockingRunner` |
| **Stability** | `src/stability.py` | `StabilityEstimator` ABC — `SequenceStabilityEstimator` (Kyte-Doolittle 5지표) + `PyRosettaStabilityEstimator` (FastRelax ddG) |
| **Scoring** | `src/scoring.py` | dG/stability/druggability/diversity/HIL confidence 가중합 + violation 감점 |
| **Gates** | `src/gates.py` | 3단계 HIL 게이트 (static filter → docking triage → human review) |
| **Orchestrator** | `src/orchestrator.py` | 전체 파이프라인 오케스트레이션 + manifest 생성 |

## 설정

기본 설정: `configs/sst14_mutation_default.yaml`
스키마 문서: `configs/schema.md`

## 테스트

```bash
python3 -m pytest pipelines/silo_b/tests/ -q   # 24 tests
```

## 참조

- [Architecture](docs/ARCHITECTURE.md) — 6-layer 아키텍처, 3-Phase 파이프라인
- [Methodology](docs/METHODOLOGY.md) — 10단계 실행 흐름, 전략 의사결정 트리
- [Config Schema](configs/schema.md) — YAML 스키마 정의
- [System Architecture](../../docs/SYSTEM_ARCHITECTURE.md) — 전체 시스템 아키텍처
