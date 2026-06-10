# Silo A — 3-Arm SSTR2 Virtual Screening

SSTR2 타겟에 대해 소분자/펩타이드/de novo 3가지 경로로 병렬 가상 스크리닝을 수행하고,
통합 스코어링으로 cross-arm 랭킹하는 config-driven 파이프라인.

## 실행 흐름

```
Config (YAML) → NimClientBundle (DI)
  → Arm 1: MolMIM → DiffDock (소분자)
  → Arm 2: FlexPepDock (펩타이드 변이체)
  → Arm 3: RFdiffusion → ProteinMPNN → ESMFold (de novo)
  → UnifiedScorer (cross-arm normalization)
  → Ranked Candidates + Manifest
```

## 모듈 구조

| 모듈 | 파일 | 역할 |
|------|------|------|
| **Config** | `src/config.py` | Pydantic `SiloAConfig` — pocket, arm1/2/3, scoring, output |
| **Models** | `src/models.py` | `ArmName`, `RunStatus`, `CandidateRecord`, `ArmResult` |
| **Clients** | `src/clients.py` | `NimClientBundle` DI + 5개 Protocol 인터페이스 |
| **Arms** | `src/arms.py` | `ArmRunner` ABC + `Arm1SmallMolRunner`, `Arm2FlexPepRunner`, `Arm3DeNovoRunner` |
| **Scoring** | `src/scoring.py` | `UnifiedScorer` — arm별 가중치 정규화 + cross-arm 랭킹 |
| **Orchestrator** | `src/orchestrator.py` | `SiloAOrchestrator` — 3-arm 실행 → 통합 scoring → manifest 출력 |

## 설정

기본 설정: `configs/sstr2_a_default.yaml`

주요 설정 항목:
- `pocket`: 타겟 PDB, 리간드/수용체 체인, cutoff
- `arm1`: 시드 분자 (Paltusotine, L054522, Pasireotide), MolMIM/DiffDock 파라미터
- `arm2`: wildtype SST-14, 11개 변이체 (Ala scanning + conservative substitution)
- `arm3`: RFdiffusion 설계 수, pLDDT threshold
- `scoring`: qed/dock_confidence/delta_energy/plddt/diversity 가중치

## 테스트

```bash
python3 -m pytest pipelines/silo_a/tests/ -q   # 9 tests
```

## 참조

- [System Architecture](../../docs/SYSTEM_ARCHITECTURE.md) — 전체 시스템 아키텍처
- [BioNeMo Clients](../../bionemo/README.md) — NIM API 클라이언트 상세
