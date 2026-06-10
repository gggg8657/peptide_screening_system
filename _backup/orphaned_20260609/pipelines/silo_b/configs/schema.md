# Silo B Config Schema

이 문서는 `sst14_mutation_default.yaml`의 모든 필드와 타입, 기본값, 검증 규칙을 정의한다.

## Top-level Fields
| Field | Type | Default | Description | Validation |
|---|---|---|---|---|
| `pipeline_name` | string | required | 파이프라인 실행 이름 | 비어 있으면 안 됨 |
| `config_version` | string | required | 스키마 호환 버전 | SemVer-like 형식 권장 |
| `schema_version` | integer | required | 스키마 버전 | 1 이상 |
| `created_utc` | string | required | 생성 시각(ISO-8601) | 파싱 가능한 UTC timestamp |
| `seed` | integer | 42 | 전역 시드 | 0~2^31-1 |
| `sequence_metadata` | object | required | 펩타이드/수용체 기본 메타데이터 | 필수 하위 필드 존재 |
| `constraints` | object | required | 제약 조건 | 제약 모순 검증 필요 |
| `generator` | object | required | 생성 전략/예산 | 총합 제약 검증 |
| `validation` | object | required | 필터/중복제거 설정 | threshold 값 범위 검사 |
| `scoring` | object | required | 스코어링 가중치 및 패널티 | 가중치 총합 범위 검사 |
| `orchestration` | object | required | 오케스트레이션/운영 설정 | 시간/배치 제약 검사 |

## `sequence_metadata`
### Fields
| Field | Type | Default | Description | Validation |
|---|---|---|---|---|
| `peptide.name` | string | required | 펩타이드 이름 | 공백 불가 |
| `peptide.template_sequence` | string | required | 원천 서열 | `^[ACDEFGHIKLMNPQRSTVWY]+$` |
| `peptide.length` | integer | required | 서열 길이 | `template_sequence` 길이와 일치 |
| `peptide.chain_id` | string | required | chain 식별자 | 1~5자 |
| `peptide.n_terminal_modification` | string | `"free_amino"` | N말단 변형 | 허용값: free_amino, acetyl |
| `peptide.c_terminal_modification` | string | `"free_carboxyl"` | C말단 변형 | 허용값: free_carboxyl, amidation |
| `peptide.source` | string | required | 설계 출처 | 빈 문자열 금지 |
| `receptor.name` | string | required | 타깃 수용체명 | 공백 금지 |
| `receptor.uniprot` | string | required | Uniprot accession | `^P\w{5,10}$` |
| `receptor.sequence_length` | integer | required | 수용체 길이 | 300~1000 |
| `receptor.binding_mode_hint` | string | optional | 결합 모드 힌트 | null 허용 |
| `disulfides[].id` | string | required | disulfide ID | 고유해야 함 |
| `disulfides[].residues` | list[int] | required | Cys 인덱스 쌍 | 길이=2, 1<=pos<=length, 서로 달라야 함 |
| `disulfides[].type` | string | `intrachain` | 결합 타입 | `intrachain` 권장 |
| `disulfides[].constrained` | boolean | true | 고정 여부 | bool |
| `chain_info.cysteine_positions` | list[int] | required | 잔기 Cys 위치 | disulfide positions 하위 집합 |
| `chain_info.cysteine_locked` | boolean | true | Cys 고정 플래그 | true 권장 |
| `pharmacophore.motif_name` | string | required | 모티프 이름 | non-empty |
| `pharmacophore.positions` | list[int] | required | 모티프 위치 | 1-based, 오름차순 |
| `pharmacophore.residues` | object(int->aa) | required | 위치별 서열 | positions와 키 일치, AA 1글자 코드 |
| `pharmacophore.mode` | string | `exact` | 모티프 강도 | `exact|soft` |

## `constraints`
### Fields
| Field | Type | Default | Description | Validation |
|---|---|---|---|---|
| `frozen_positions` | list[int] | [] | 절대 변경 금지 위치 | `template` 길이 범위
| `per_position_allowed_aas` | object | required | 위치별 허용 AA 집합 | 각 키는 int-like string, 값은 AA code list/집합 |
| `pairwise_rules[]` | list[obj] | [] | 위치 쌍/다중 제약 | 하드/소프트 규칙 타입 검증 |
| `pharmacophore` | object | required | 모티프 보존 규칙 | positions/residues 일치 검증 |

### `per_position_allowed_aas` 규칙
- value 타입: 배열 of amino acid 1-letter code (`A,C,D,E,F,G,H,I,K,L,M,N,P,Q,R,S,T,V,W,Y`
- 기본값: 빈 배열이면 해당 위치 허용 AA 없음으로 간주되어 후보 생성 실패

### pairwise_rules example
1) Hard exclusion (`not_both_in_set`)
```yaml
- id: hydrophobic_adjacent_guard
  type: hard
  description: "Positions 5 and 6 cannot both be strongly hydrophobic"
  positions: [5, 6]
  mode: not_both_in_set
  aa_set: [F, W, Y, L, I, V, M]
```
2) Soft max count (`max_count`)
```yaml
- id: basic_count_guard
  type: soft
  description: "limit positive residues"
  positions: [1,2,4,5,6,11,12,13]
  mode: max_count
  aa_set: [K, R, H]
  max_count: 2
  penalty_weight: 1.2
```
3) Soft not-both-equal (`not_both_equal`)
```yaml
- id: proline_pair_guard
  type: soft
  positions: [1,2]
  mode: not_both_equal
  aa_value: P
  penalty_weight: 0.8
```

### Validation rules
- `frozen_positions`은 `per_position_allowed_aas`와 충돌하면 실패.
- `pairwise_rules.positions`는 길이 2 이상이어야 하며 빈 목록 금지.
- `pharmacophore` 위치는 `disulfide` 및 `frozen` 제약과 충돌 불가.

## `generator`
### Fields
| Field | Type | Default | Description | Validation |
|---|---|---|---|---|
| `strategy.primary` | string | required | 후보 생성 기본 전략 | enum/ sampling/ga/bo/ga_bo |
| `strategy.fallback.low_space_threshold` | int | 1200 | enum fallback 임계 후보 수 | >0 |
| `strategy.fallback.low_density_threshold` | float | 0.05 | 제약 밀도 임계값 | 0~1 |
| `strategy.fallback.fallback_primary` | string | sampling | 1차 fallback 전략 | 위와 동일 |
| `strategy.fallback.fallback_secondary` | string | enum | 2차 fallback 전략 | 위와 동일 |
| `budget.total_candidates` | int | required | 전체 생성 수 | >0 |
| `budget.adaptive_rounds` | int | 3 | 적응 라운드 수 | >0 |
| `budget.per_round_max` | int | required | 라운드당 최대 생성 수 | `<= total_candidates`
| `budget.approach_b_allocation_ratio` | float | 0.85 | B 후보 비율 | 0~1 |
| `budget.approach_a_allocation_ratio` | float | 0.15 | A 후보 비율 | 위와 합 1.0 |
| `diversity_policy.min_hamming_distance` | int | 3 | 최소 차이 거리 | >=0 |
| `diversity_policy.max_seq_identity` | float | 0.88 | 최대 중복도 | 0~1 |
| `diversity_policy.ngram_diversity_weight` | float | 0.12 | 점수 가중치 | 0~1 |
| `diversity_policy.cluster_before_docking` | bool | true | 사전 군집 필터 | bool |
| `mutation.mutation_rate` | float | 0.30 | 변이율 | 0~1 |
| `mutation.mutation_mode` | string | position_uniform | 변이 모드 | 문자열 토큰 |
| `mutation.preserve_motif` | bool | true | 필수 모티프 보호 | bool |
| `approach_b.enabled` | bool | true | Approach B 사용 | bool |
| `approach_b.docking_timeout_sec` | int | 15 | 도킹 timeout | >=1 |
| `approach_b.batch_size` | int | 64 | B 배치 크기 | >0 |
| `approach_b.max_fail_retries` | int | 2 | 실패 재시도 | >=0 |
| `approach_a.enabled` | bool | true | A 정밀 정제 사용 | bool |
| `approach_a.trigger.gate2_pass_top_k` | int | 350 | Gate2 통과 상위 수 | >0 |
| `approach_a.trigger.min_docking_z` | float | -0.75 | A 진입 임계점 | <-1~1 |
| `approach_a.trigger.min_diversity_gap` | float | 0.25 | 다양성 기준 | 0~1 |
| `approach_a.timeout_sec_per_candidate` | int | 142 | 정제 시간 제약 | >=1 |
| `approach_a.batch_size` | int | 12 | A 배치 크기 | >0 |

## `validation`
### Fields
| Field | Type | Default | Description | Validation |
|---|---|---|---|---|
| `drugability_filters.enabled` | bool | true | drug-like 규칙 사용 | bool |
| `drugability_filters.max_molecular_weight` | int | 2800 | MW 상한 | >0 |
| `drugability_filters.min_logp` | float | -2.0 | 하한 | <= max_logp |
| `drugability_filters.max_logp` | float | 5.5 | 상한 | >= min_logp |
| `drugability_filters.max_positive_charge` | int | 3 | 양전하 상한 | >=0 |
| `drugability_filters.min_topology_stability_score` | float | 0.62 | 안정성 최소값 | 0~1 |
| `drugability_filters.max_hydrophobic_fragment_ratio` | float | 0.66 | 극성 비율 제한 | 0~1 |
| `structure.require_disulfide_geometry` | bool | true | disulfide 기하 필수 | bool |
| `structure.max_steric_clash` | float | 0.25 | 충돌 임계 | 0~1 |
| `structure.max_backbone_rmsd_to_template` | float | 3.8 | RMSD 상한 | >=0 |
| `dedupe.enabled` | bool | true | 중복 제거 사용 | bool |
| `dedupe.sequence_identity_threshold` | float | 0.85 | 유사도 기준 | 0~1 |
| `dedupe.keep_top_by_identity` | int | 1 | 대표군 대표 수 | >=1 |
| `dedupe.torsion_fingerprint_kl_threshold` | float | 0.30 | 회전 fingerprint 임계 | 0~1 |
| `dedupe.near_neighbour_window` | int | 128 | 인덱싱 윈도우 | >=8 |

## `scoring`
### Fields
| Field | Type | Default | Description | Validation |
|---|---|---|---|---|
| `primary.docking_delta_g.weight` | float | 0.45 | 도킹 가중치 | 0~1 |
| `primary.docking_delta_g.goal` | string | minimize | 방향 | minimize|maximize |
| `primary.docking_delta_g.clip.min` | float | -14.0 | 클립 하한 | <= clip.max |
| `primary.docking_delta_g.clip.max` | float | 0.0 | 클립 상한 | >= clip.min |
| `primary.stability.weight` | float | 0.20 | 구조 안정성 가중치 | 0~1 |
| `primary.stability.source` | string | pRosetta_ddG | 데이터 소스 | non-empty |
| `primary.stability.clip` | object | required | 정규화 범위 | min<=max |
| `auxiliary.druggability.weight` | float | 0.15 | drugability 가중치 | 0~1 |
| `auxiliary.diversity.weight` | float | 0.10 | 다양성 가중치 | 0~1 |
| `auxiliary.hil_confidence.weight` | float | 0.10 | HIL 가중치 | 0~1 |
| `penalties.hard_violation` | float | 8.0 | 하드 위반 패널티 | >=0 |
| `penalties.soft_violation_per_rule` | float | 0.4 | 소프트 규칙 패널티 | >=0 |
| `penalties.duplicate_penalty` | float | 0.5 | 중복 패널티 | >=0 |
| `normalization.method` | string | minmax | 정규화 방식 | minmax|zscore |
| `normalization.epsilon` | float | 1e-8 | 0 분할 회피 | >0 |

## `orchestration`
### Fields
| Field | Type | Default | Description | Validation |
|---|---|---|---|---|
| `batch_size.generation` | int | 2048 | 생성 batch 크기 | >0 |
| `batch_size.docking` | int | 64 | 도킹 batch 크기 | >0 |
| `batch_size.approach_a` | int | 12 | 정제 batch 크기 | >0 |
| `adaptive_steps` | int | 4 | 적응 반복 횟수 | >=1 |
| `stop_criteria.min_candidates_for_gate2` | int | 250 | gate2 최소 후보 수 | >=1 |
| `stop_criteria.min_gate2_ratio` | float | 0.05 | gate2 pass 비율 하한 | 0~1 |
| `stop_criteria.max_wallclock_hours` | int | 24 | 총 소요 제한시간 | >0 |
| `hil_gates.gate_1.enabled` | bool | true | Gate1 사용 | bool |
| `hil_gates.gate_2.enabled` | bool | true | Gate2 사용 | bool |
| `hil_gates.gate_3.enabled` | bool | true | Gate3 사용 | bool |
| `seed_lineage.base_seed` | int | 42 | 베이스 시드 | >=0 |
| `seed_lineage.stage_seeds[]` | map string->int | required | 단계별 시드 | 중복 불필요 |
| `output.manifest_path` | string | outputs/... | 매니페스트 경로 | non-empty |
| `output.candidates_path` | string | outputs/... | 후보 저장 경로 | non-empty |
| `output.logs_path` | string | outputs/... | 로그 경로 | non-empty |
| `output.checkpoint_interval` | int | 300 | 체크포인트 간격(초) | >0 |

## Examples for constraint types
- Per-position whitelist (Cys positions fixed):
```yaml
per_position_allowed_aas:
  3: [C]
  14: [C]
```
- Hard pairwise disallow rule:
```yaml
- id: hydrophobic_adjacent_guard
  type: hard
  positions: [5,6]
  mode: not_both_in_set
  aa_set: [F,W,Y,L,I,V,M]
```
- Soft count cap rule:
```yaml
- id: basic_count_guard
  type: soft
  positions: [1,2,4,5,6,11,12,13]
  mode: max_count
  aa_set: [K,R,H]
  max_count: 2
  penalty_weight: 1.2
```
- Pharmacophore preservation:
```yaml
pharmacophore:
  require_positions: [7,8,9,10]
  required_residues:
    7: F
    8: W
    9: K
    10: T
  preserve_geometry: true
```
