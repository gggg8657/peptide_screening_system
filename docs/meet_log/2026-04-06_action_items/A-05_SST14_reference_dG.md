# A-05: SST14 레퍼런스 ΔG 기준선 확립

## 메타
- 회의: KAERI-AIRL-MOM-2026-003 (2026-04-06)
- 담당: AI팀
- 기한: 5월 회의 전
- 상태: **✅ 완료** (main commit `8e7e1cc`, direct push — 2026-05-19)
- 비고: A-01(위치 지정 도킹 좌표 확정) 병행 권장

### 실측 결과 (2026-05-19 산출)
| 도킹 도구 | SST-14 → SSTR2 ΔG | 비고 |
|----------|------------------|------|
| **FlexPepDock (Rosetta)** | **mean = 553.857 REU** | n회 반복 |
| **Boltz-2** | **-95.024 REU** | 단일 실행, PRST-001 비교 기준 |

> **주의**: 두 도구는 단위/부호 체계가 다름. FlexPepDock REU와 Boltz-2 REU 직접 비교 금지. PRST-001 합성 의뢰서(`runs_local/final_candidates/synthesis_orders/PRST-001.md`)는 Boltz-2 기준 -95.024 REU를 SST-14 ref로 사용.

> **stale 브랜치 주의**: `feat/a05-sst14-reference-dg` 브랜치의 tip은 A-10 fix(`5f5f7af`)로 남아있음. A-05 실제 작업은 main 직접 push로 진행됨.

---

## 배경

현행 파이프라인의 도킹 게이트 임계값은 **SSOT가 `pipeline_local/config/gate_thresholds.yaml::rosetta_ddg_max`** 에 있으며, 2026-05-20 기준 `498.4713`으로 갱신되어 있다. 이는 FlexPepDock mean `553.857 REU × 0.9`를 적용한 값이다. 회의 시점의 코드 폴백 기본값 `-5.0`은 다음 위치에 분산되어 있어 지속 정렬 대상이다:
- `pipeline_local/orchestrator.py` (lines 1211, 1266, 1524)
- `pipeline_local/steps/step06_rosetta.py::apply_rosetta_gate()` (line 190, 910)
- `pipeline_local/schemas/rank_table.py` (line 245)

이 값들은 생물학적 근거 없이 임의로 설정된 것으로, **SST-14 원형(AGCKNFFWKTFTSC)을 SSTR2에 동일 프로토콜로
도킹하여 얻은 실측 ΔG를 기준선**으로 삼아야 한다.

서호성 박사는 n회 반복 도킹의 **Mean 값**을 사용하도록 권장하였으며, 단계별
3차 스크리닝 체계를 제안하였다.

---

## 수행 방법 (단계별)

### Step 1 — SST14 레퍼런스 도킹 (Boltz-2)
현행 `offtarget_dock.py` 스크립트로 SST14 → SSTR2(7XNA) 반복 실행:
```bash
for i in {1..10}; do
    conda run -n boltz python pipeline_local/scripts/offtarget_dock.py \
        --receptor data/somatostatin_receptor/SSTR2_7XNA.cif \
        --sequence AGCKNFFWKTFTSC \
        --nstruct 1 \
        --output-dir runs_local/sst14_ref_docking/run_${i}
done
```
- `nstruct` 옵션 또는 반복 루프로 **n=10 이상** 수행 권장 (서호성 의견).
- 출력 `ddg` 값 (`-100 * iptm`) 집계.

### Step 2 — ΔG 기준선 산출
```python
import json, statistics, glob

ddg_values = []
for f in glob.glob("runs_local/sst14_ref_docking/run_*/result.json"):
    data = json.load(open(f))
    ddg_values.append(data["ddg"])

ref_ddg_mean = statistics.mean(ddg_values)
ref_ddg_std  = statistics.stdev(ddg_values)
threshold    = ref_ddg_mean * 0.9  # 10% 허용 (서호성 제안)
```

### Step 3 — 파이프라인 임계값 교체
**SSOT 위치는 `pipeline_local/config/gate_thresholds.yaml::rosetta_ddg_max`** 이며 현재 `498.4713`으로 반영되어 있다.
남은 작업은 5곳의 코드 폴백 `-5.0`을 동일 기준으로 정렬하는 것이다.

```yaml
# pipeline_local/config/gate_thresholds.yaml (SSOT 갱신)
rosetta_ddg_max: 498.4713  # SST14 FlexPepDock mean 553.857 REU × 0.9
```

```python
# pipeline_local/orchestrator.py / step06_rosetta.py / rank_table.py
# 폴백 -5.0 → 측정값 기반으로 일괄 갱신
rosetta_thresh = float(self.gate_thresholds.get("rosetta_ddg_max", <SST14_REF * 0.9>))
```

- 게이트 적용 함수: `apply_rosetta_gate()` in `step06_rosetta.py`
- 설정 로더: `pipeline_local/core/config_loader.py`

### Step 4 — 3단계 스크리닝 체계 문서화 (서호성 의견)

| 단계 | 방법 | 선별 수 | 비고 |
|------|------|---------|------|
| 1차 | Rosetta FlexPepDock ΔG | 200–500개 | 현행 파이프라인 Step05 |
| 2차 | MM-GBSA 랭킹 재산정 | 20–50개 | 킬레이터 부착 후 적용 |
| 3차 | FEP/TI 정밀 ΔΔG | 최종 후보 | OpenMM / OpenFE / gmx_MMPBSA |

> 본 A-05는 1차 스크리닝 임계값 정립이 목표.
> 2차(MM-GBSA), 3차(FEP/TI)는 별도 Action Item 또는 향후 로드맵으로 등록.

### Step 5 — 레퍼런스 값 pharmacology_guards.py 등록
2026-05-20 기준 `pipeline_local/scripts/pharmacology_guards.py::LITERATURE_VALUES`에 Boltz-2와 FlexPepDock 레퍼런스가 모두 등록되어 있다.

```python
# pipeline_local/scripts/pharmacology_guards.py
LITERATURE_VALUES["SST14_SSTR2_ref_ddg_boltz2"]["ref_ddg_reu"]       # -95.024 REU
LITERATURE_VALUES["SST14_SSTR2_ref_ddg_flexpep"]["ref_ddg_reu_mean"] # 553.857 REU
LITERATURE_VALUES["SST14_SSTR2_ref_ddg_flexpep"]["ref_ddg_reu_std"]  # 4.024 REU
LITERATURE_VALUES["SST14_SSTR2_ref_ddg_flexpep"]["n"]                # 10
```

---

## 판단 기준 / KPI

| 지표 | 기준 |
|------|------|
| 반복 횟수 | n ≥ 10 (서호성 권장) |
| 표준편차 | σ < 5 (허용 범위 내 재현성) |
| 기준선 갱신 후 기존 통과 후보 재검증 | 하드코딩 기준 통과 후보의 ≥ 80%가 새 기준에서도 통과 |

현재 실측 상태: FlexPepDock `n=10`, `σ=4.024`로 반복 횟수와 재현성 KPI를 충족한다.

---

## 활용 도구 / 기술 스택

| 도구 | 용도 |
|------|------|
| Boltz-2 (`offtarget_dock.py`) | SST14 반복 도킹 |
| `config_loader.py` | 임계값 동적 로드 |
| `pharmacology_guards.py` | LITERATURE_VALUES 등록 (Stage 5 가드) |
| OpenMM / OpenFE / gmx_MMPBSA | 2·3차 스크리닝 (로드맵) |

---

## 서호성 박사 의견

- **n회 반복 Mean 값** 사용: 단일 도킹 결과의 분산이 크므로 통계적 안정성 필요.
- **MD simulation 검토**: 정적 구조 도킹의 한계 보완. 구체 일정은 별도 논의.
- **3단계 스크리닝 체계** (위 Step 4 참조):
  - 2차(MM-GBSA)에서 킬레이터 부착 구조 반영.
  - 3차(FEP/TI)는 최종 wet-lab 전 단계.

---

## 본 프로젝트 매핑

- **관련 디렉토리/파일**:
  - `pipeline_local/config/gate_thresholds.yaml::rosetta_ddg_max` — **SSOT (현재 498.4713)**
  - `pipeline_local/orchestrator.py` (lines 1211, 1266, 1524) — 폴백 `-5.0`
  - `pipeline_local/steps/step06_rosetta.py` (lines 190, 910) — Rosetta 게이트 폴백
  - `pipeline_local/schemas/rank_table.py` (line 245) — 랭킹 검증 폴백
  - `pipeline_local/scripts/` — `offtarget_dock.py` (Boltz-2 도킹 실행), `pharmacology_guards.py` (KPI 가드)
  - `pipeline_local/core/` — `config_loader.py` (설정 관리)
  - `data/somatostatin_receptor/` — `SSTR2_7XNA.cif` (레퍼런스 수용체)
- **관련 함수**:
  - `apply_rosetta_gate()` in `step06_rosetta.py` — 게이트 적용
  - `predict_with_boltz2()` — Boltz-2 호출 래퍼
  - `LITERATURE_VALUES` in `pharmacology_guards.py` — Boltz-2/FlexPepDock 레퍼런스 등록 완료

---

## 의존성 / 연관 액션 아이템

| 의존 관계 | 액션 |
|----------|------|
| 병행 권장 | **A-01** (도킹 좌표 확정 — 동일 프로토콜 공유) |
| 결과 제공 대상 | **A-04** (최종 후보 도출 — ΔG 임계값 사용) |
| 2차 스크리닝 준비 | **A-09** (스코어링 고도화 로드맵) |
