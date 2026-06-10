# A~E 클러스터 분류 기준 명세

> **작성일**: 2026-04-05
> **구현 파일**: `pyrosetta_flow/cluster_report.py`
> **참조**: meet_log_backup.md 스펙 기반

---

## 1. 개요

파이프라인에서 생성된 SST-14 유사체 후보를 5개 클러스터(A~E)로 분류한다. 분류는 결정적(deterministic)이며, runner 파이프라인과 pharmacology 모듈에서 이미 계산된 수치 필드만 사용한다.

### 분류 로직

```
A 기준 전부 충족? ─── Yes ──→ Cluster A
       │ No
B 기준 전부 충족? ─── Yes ──→ Cluster B
       │ No
C 기준 전부 충족? ─── Yes ──→ Cluster C
       │ No
D 기준 전부 충족? ─── Yes ──→ Cluster D
       │ No
       └──────────────────→ Cluster E (탐색/미분류)
```

- **각 클러스터의 모든 기준을 AND 조건으로 충족해야** 해당 클러스터로 배정
- **우선순위**: A > B > C > D > E — 여러 클러스터 기준을 동시에 충족하면 가장 높은 우선순위에 배정
- Cluster E는 A~D 어디에도 해당하지 않는 나머지 후보의 폴백

---

## 2. 클러스터별 기준

### Cluster A — High Affinity Core (고친화도 핵심)

| 기준 | 조건 | 근거 |
|------|------|------|
| ddG | <= -8.0 kcal/mol | SSTR2에 대한 강한 결합 에너지 |
| clash_score | <= 5.0 | 구조적 충돌 없는 안정적 도킹 |
| pLDDT | >= 75 | ESMFold 구조 예측 신뢰도 (없으면 면제) |
| FWKT pharmacophore | contact 유지 = True | F7-W8-K9-T10 약리작용기 보존 필수 |

> **pLDDT 면제 조건**: ESMFold 없이 PyRosetta만 사용하는 환경에서는 pLDDT가 생성되지 않으므로 해당 기준을 True(면제)로 처리. 나머지 3개 기준(ddG, clash, FWKT)만으로 판정.

### Cluster B — Selectivity-Optimised (선택성 최적화)

| 기준 | 조건 | 근거 |
|------|------|------|
| selectivity_margin | >= 3.0 kcal/mol | SSTR2 vs off-target 결합 에너지 차이 |
| ddG | < -5.0 kcal/mol | SSTR2에 대한 최소 결합 확인 |

> selectivity_margin = SSTR2 ddG - worst off-target ddG. 음수가 클수록 SSTR2에 선택적.

### Cluster C — Stability-Enhanced (안정성 강화)

| 기준 | 조건 | 근거 |
|------|------|------|
| instability_index | < 30 | Guruprasad 안정성 지수 (< 40 = 안정, < 30 = 매우 안정) |
| BLOSUM62 total_score | >= 0 | SST-14 대비 보존적 치환 (음수 = 비보존적) |
| protease_sites total | <= 9 | SST-14 native baseline(9개) 대비 감소 또는 동일 |

### Cluster D — Radiochemistry-Optimal (방사화학 최적)

| 기준 | 조건 | 근거 |
|------|------|------|
| GRAVY | -1.0 ~ +0.5 | 적절한 친수/소수 균형 (주사제 용해성) |
| net_charge (pH 7.4) | \|charge\| <= 1.0 | 낮은 전하 → 비특이적 결합 감소 |
| metal_coordination n_strong | >= 1 | DOTA/NOTA 킬레이터 결합 가능 잔기 존재 |

> n_strong: His, Cys, Asp, Glu 등 강한 금속 배위 잔기 수

### Cluster E — Exploratory Candidates (탐색 후보)

A~D 기준 어디에도 해당하지 않는 모든 후보. 추가 분석 또는 구조 최적화가 필요한 그룹.

---

## 3. 입력 필드 요구사항

`classify_cluster(candidate)` 함수에 전달되는 dict에 필요한 키:

| 필드 | 출처 | 필수 | 사용 클러스터 |
|------|------|------|-------------|
| `ddG` | runner.py (PyRosetta docking) | O | A, B |
| `clash_score` | runner.py (Rosetta scoring) | O | A |
| `pLDDT` | ESMFold wrapper | X (없으면 면제) | A |
| `structural_rules` | pharma_properties.py | O | A (FWKT) |
| `selectivity_margin` | selectivity module | X | B |
| `instability_index` | pharmacology.py | O | C |
| `blosum62` | pharmacology.py | O | C |
| `protease_sites` | pharmacology.py | O | C |
| `gravy` | pharmacology.py | O | D |
| `net_charge_ph74` | pharmacology.py | O | D |
| `metal_coordination` | pharmacology.py | O | D |

---

## 4. 반환 형식

```python
{
    "cluster": "A",                          # A/B/C/D/E
    "cluster_name": "High Affinity Core",    # 클러스터 설명
    "priority": 1,                           # 1(A) ~ 5(E)
    "criteria_met": {                        # 각 기준별 통과 여부
        "A": {
            "ddG_lte_minus8": True,
            "clash_lte_5": True,
            "pLDDT_gte_75": True,
            "pLDDT_available": False,        # 정보성 플래그
            "fwkt_contact": True
        }
    },
    "note": "All four A-criteria satisfied: ..."
}
```

---

## 5. 배치 분류

```python
from pyrosetta_flow.cluster_report import batch_classify

results = batch_classify(candidates_list)
# returns: {
#   "classified": [...],        # 후보별 분류 결과
#   "summary": {"A": 3, "B": 5, "C": 2, "D": 1, "E": 4},
#   "total": 15
# }
```

---

## 6. 클러스터 분류 흐름도

```
                    ┌─────────────┐
                    │  후보 입력   │
                    └──────┬──────┘
                           │
                ┌──────────▼──────────┐
                │ ddG <= -8.0         │
                │ clash <= 5.0        │──── 전부 Yes ──→ [A] High Affinity Core
                │ pLDDT >= 75 (면제)  │
                │ FWKT contact        │
                └──────────┬──────────┘
                       No  │
                ┌──────────▼──────────┐
                │ selectivity >= 3.0  │──── 전부 Yes ──→ [B] Selectivity-Optimised
                │ ddG < -5.0          │
                └──────────┬──────────┘
                       No  │
                ┌──────────▼──────────┐
                │ instability < 30    │
                │ BLOSUM62 >= 0       │──── 전부 Yes ──→ [C] Stability-Enhanced
                │ protease <= 9       │
                └──────────┬──────────┘
                       No  │
                ┌──────────▼──────────┐
                │ GRAVY: -1.0~+0.5   │
                │ |charge| <= 1.0     │──── 전부 Yes ──→ [D] Radiochem-Optimal
                │ n_strong >= 1       │
                └──────────┬──────────┘
                       No  │
                           ▼
                  [E] Exploratory Candidates
```

---

## 7. 설계 의사결정 기록

| 항목 | 결정 | 이유 |
|------|------|------|
| AND 조건 | 각 클러스터 내 모든 기준 동시 충족 필요 | 하나라도 미달이면 해당 특성을 대표한다고 볼 수 없음 |
| 우선순위 A>B>C>D | A(친화도) > B(선택성) > C(안정성) > D(방사화학) | 약물 개발 파이프라인에서 타겟 결합이 최우선 |
| pLDDT 면제 | ESMFold 미사용 시 True 처리 | PyRosetta-only 환경에서도 분류 가능하도록 |
| protease baseline 9 | SST-14 native 기준 | 원본 대비 개선 여부 판단 |
| E 클러스터 | 나머지 전부 | 탈락이 아닌 "추가 분석 필요" 의미 |
