# A-01: SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹

## 메타
- 회의: KAERI-AIRL-MOM-2026-003 (2026-04-06)
- 담당: AI팀
- 기한: 5월 회의 전
- 상태: 신규
- 비고: A-10(SSTR3 에러 해결) 선행 완료 필요

---

## 배경

현행 파이프라인(`pipeline_local/core/selectivity_runner.py`)은 Boltz-2 구조 예측을
통해 off-target 도킹을 수행하며, iPTM 기반 `ddg` 프록시로 선택성을 산출한다.
Boltz-2는 binding box를 수동으로 지정할 필요가 없지만, **FlexPepDock 기반 legacy
코드(`offtarget_dock_pyrosetta_legacy.py`)나 향후 GNINA/AutoDock-GPU 병용 시
결합 포켓 좌표가 필수**가 된다.

회의에서 서호성 박사는 SSTR2(7T10/7T11) cryo-EM 구조에서 확인된 ECL/TM 핵심 잔기
범위(77-314)를 **네거티브 디자인의 정량적 근거**로도 활용하자고 제안하였다.
현재 프로젝트 데이터 디렉토리에는 다음 구조가 준비되어 있다:

| 서브타입 | PDB ID (local) | 출처 |
|---------|---------------|------|
| SSTR1   | 9IK8          | `data/somatostatin_receptor/SSTR1_9IK8.pdb` |
| SSTR2   | 7XNA          | `data/somatostatin_receptor/SSTR2_7XNA.pdb` |
| SSTR3   | 8XIR          | `data/somatostatin_receptor/SSTR3_8XIR.pdb` |
| SSTR4   | 7XMT          | `data/somatostatin_receptor/SSTR4_7XMT.pdb` |
| SSTR5   | 8ZBJ          | `data/somatostatin_receptor/SSTR5_8ZBJ.pdb` |

> **주의**: 회의록 원문은 SSTR2 기준 구조로 7T10을 언급하나, 로컬에는 7XNA가 배치되어
> 있다. A-01 수행 전 구조 ID 불일치를 확인/해소해야 한다.

---

## 수행 방법 (단계별)

### Step 1 — SSTR2 결합 포켓 중심 좌표 추출
1. `data/somatostatin_receptor/SSTR2_7XNA.pdb` (또는 7T10 원문 구조)를 PyMOL에서 로드.
2. Trp-Lys 모티프 인접 영역(TM5-208/209, TM6-272/273/276) 중심 원자 좌표 계산:
   ```python
   # PyMOL 예시
   com = cmd.centerofmass("resi 208+209+272+273+276")  # (x, y, z)
   ```
3. 결합 포켓 중심 좌표를 `data/somatostatin_receptor/binding_pocket_SSTR2.json`에 저장.

### Step 2 — SSTR1/3/4/5 → SSTR2 구조 정렬
```bash
# PyMOL 배치 cealign 예시
pymol -c -d "
load SSTR2_7XNA.pdb, ref;
load SSTR1_9IK8.pdb, sstr1;
cealign ref, sstr1;
save SSTR1_aligned.pdb, sstr1;
"
```
또는 TM-align CLI:
```bash
TMalign SSTR1_9IK8.pdb SSTR2_7XNA.pdb -o SSTR1_aligned
```

### Step 3 — 도킹 검색 박스 설정
- 기준: SSTR2 포켓 중심으로부터 반경 **15–20 Å**
- GNINA/AutoDock-GPU 입력 형식:
  ```yaml
  center_x: <cx>
  center_y: <cy>
  center_z: <cz>
  size_x: 30  # 2 × 15 Å
  size_y: 30
  size_z: 30
  ```
- Boltz-2 엔진은 결합 포켓 좌표 불필요 → 선택성 분석 `selectivity_runner.py`는 그대로 유지.

### Step 4 — 셀렉티비티 배수 산출
현행 파이프라인의 `compute_full_selectivity()` 함수 활용:
```python
from pipeline_local.core.selectivity_runner import compute_full_selectivity

result = compute_full_selectivity(
    sstr2_ddg=sstr2_ddg,
    offtarget_ddgs={"SSTR1": sstr1_ddg, "SSTR3": sstr3_ddg, ...},
    seq_id="SST14_ref",
    sequence="AGCKNFFWKTFTSC",
)
# result["selectivity_ratio"], result["tier"]
```
- 핵심 잔기 정보는 `네거티브 디자인` 단계(Step06 이후)에 적용 예정.

### Step 5 — SSTR3 재도킹
SSTR3 전처리 완료(A-10 선행) 후 동일 프로토콜로 재실행.

---

## 판단 기준 / KPI

| 지표 | 최소 | 권장 |
|------|------|------|
| SSTR2 vs 각 off-target 선택성 배수 | ≥100× | ≥300× |
| 구조 정렬 TM-score (SSTR1/3/4/5 vs SSTR2) | ≥0.7 | ≥0.8 |
| 셀렉티비티 tier | ≥1 | ≥2 |

---

## 활용 도구 / 기술 스택

| 도구 | 용도 |
|------|------|
| PyMOL (`cealign`) | 구조 정렬 |
| TM-align | 대안 구조 정렬 |
| Boltz-2 (`offtarget_dock.py`) | off-target iPTM 예측 |
| PyRosetta FlexPepDock (legacy) | `offtarget_dock_pyrosetta_legacy.py` |
| `compute_full_selectivity()` | WSM/MSM/Tier 산출 |

---

## 서호성 박사 의견

- SSTR2 결합 영역은 **ECL/TM 핵심 잔기 표** 기준 잔기 77–314 범위로 한정.
- 전체 369aa 대비 블라인드 도킹과 속도 차이는 크지 않지만, **핵심 잔기 정보**를
  네거티브 디자인의 정량적 근거로 활용하는 것이 핵심 목적.
- 셀렉티비티 핵심 잔기(* 표시):

  | 도메인 | 잔기 범위 | 셀렉티비티 관련 잔기 |
  |--------|---------|-----------------|
  | ECL1   | 105–111 | 106 |
  | ECL2   | 178–201 | 192*, 193*, 195*, 197* |
  | ECL3   | 282–287 | 284*, 286* |
  | TM2    | 77–104  | 99*, 102 |
  | TM3    | 112–145 | 122*, 126* |
  | TM4    | 156–179 | 177* |
  | TM5    | 202–237 | 205*, 208*, 209*, 212* |
  | TM6    | 245–281 | 272*, 273*, 276*, 279* |
  | TM7    | 288–314 | 291*, 294*, 298* |

---

## 본 프로젝트 매핑

- **관련 디렉토리**:
  - `data/somatostatin_receptor/` — SSTR1-5 PDB/CIF 구조 파일
  - `pipeline_local/scripts/` — `offtarget_dock.py`, `flexpep_dock.py`
  - `pipeline_local/core/` — `selectivity_runner.py`
  - `pipeline_local/steps/` — `step05b_selectivity.py`
- **관련 모듈/스크립트**:
  - `SelectivityRunner.dock_against_receptor()` — Boltz-2 기반 off-target 도킹
  - `compute_full_selectivity()` — WSM/MSM/SR/Tier 계산
  - `step05b_selectivity.py` — 파이프라인 Step 05b 진입점
  - `pipeline_local/scripts/pharmacology_guards.py` — 약리학 KPI 가드 (Stage 5)

---

## 의존성 / 연관 액션 아이템

| 의존 관계 | 액션 |
|----------|------|
| 선행 필수 | **A-10** (SSTR3 전처리 에러 해결) |
| 결과 활용 | **A-05** (SST14 레퍼런스 ΔG — 선택성 배수 분모) |
| GPU 가용성 확인 필요 시 | **A-07** (DGX 증설 검토) |
