# M2 검증 보고서: step04_qc / step05_docking / step05b_selectivity / step05c_boltz_cross

**작성**: reviewer-code  
**날짜**: 2026-05-13  
**범위**: `pipeline_local/steps/step04_qc.py` · `step05_docking.py` · `step05b_selectivity.py` · `step05c_boltz_cross.py`  
**판정**: **CONDITIONAL PASS** (Critical 1건 + High 4건 수정 필요)

---

## 1. 요약

| 모듈 | 판정 | 주요 이슈 |
|------|------|-----------|
| step04_qc | CONDITIONAL | `apply_plddt_gate` 결과 미사용(dead code) |
| step05_docking | CONDITIONAL | DiffPepBuilder 비활성화·미정리, affinity 추정 공식 단순화 |
| step05b_selectivity | FAIL | `save_selectivity_results` 미호출 → 05b 출력 파일 0건, STATUS 미갱신 |
| step05c_boltz_cross | CONDITIONAL | `work_dir` 이터레이션 미격리 → checkpoint 오염 가능 |

**ad-hoc vs 정식 path**: 핵심 불일치 2건 식별  
- ad-hoc(`archives_boltz_eval`) = `sequence` 키 기반 flat list; 정식 05c = `BoltzSelectivityResult`(seq_id + tier)  
- ad-hoc(`cand03_variants`) = 8 candidates × 5 receptors; 정식 05c = `sequence_map` fallback 경로로만 연결

---

## 2. 모듈별 입출력 & 의존성

### 2-1. step04_qc

**입력**
```
sequences: List[SequenceEntry]   ← Step03Output.sequences
config: Dict                     ← gate_thresholds, pocket_residues, run_id, output_base_dir
```

**출력**
```
Step04Output(qc_results: List[QCResult])
파일: {run_id}/04_qc/esmfold_{seq_id}.pdb
      {run_id}/04_qc/qc_summary.json
```

**QCResult 스키마**
```python
seq_id: str
plddt_mean: float         # 전체 평균 pLDDT (0~100)
plddt_interface: float    # 계면 잔기 pLDDT (0~100)
pdb_path: str             # ESMFold PDB 경로
passed_gate: bool
disulfide_intact: Optional[bool]    # SG-SG < 2.5Å
disulfide_distance: Optional[float]
```

**의존성**: `LocalModelRunner("esmfold")`, PyRosetta(`_try_form_disulfide`), `io_schemas.QCResult`

---

### 2-2. step05_docking

**입력**
```
candidates: List[QCResult]   ← Step04Output.passed()
receptor_pdb: str            ← Step01Output.receptor_pdb_path
config: Dict
```

**출력**
```
Step05Output(docking_results: List[DockingResult])
파일: {run_id}/05_docking/pose_{seq_id}_00.pdb
      {run_id}/05_docking/docking_scores.json
```

**DockingResult 스키마**
```python
seq_id: str
engine: str       # "boltz" (현재 DiffPepBuilder 비활성화)
score: float      # affinity_kcal (= -10 × iPTM, 근사값)
confidence: float
pose_pdb: str     # .pdb or .cif (structure_cif 폴백)
rank: int
```

**의존성**: `LocalModelRunner("boltz")`, `io_schemas.DockingResult`

---

### 2-3. step05b_selectivity

**입력**
```
candidates: List[DockingResult]           ← Step05Output.docking_results
offtarget_receptors: List[Dict]          ← config["off_target_receptors"]
config: Dict                              ← selectivity{top_k, engine, margin_min, ...}
```

**출력 (정의는 있으나 실제 파일 미저장 — 결함 §3-C 참조)**
```
Step05bOutput(selectivity_results, offtarget_docking_details)
파일(미저장): {run_id}/05b_selectivity/selectivity_scores.json
              {run_id}/05b_selectivity/{seq_id}_selectivity.json
```

**SelectivityResult 스키마**
```python
seq_id: str
sstr2_dock_score: float
offtarget_scores: Dict[str, float]   # {receptor: score}
offtarget_max_score: float
offtarget_max_receptor: str
selectivity_margin: float            # sstr2_score - max(off-target)
passed: bool
```

**의존성**: `subprocess(offtarget_dock.py)` (Production mode), numpy/random (estimation mode), `io_schemas.SelectivityResult`

**중요**: 현재 대부분 실행은 **estimation mode** — `sstr2_complex_pdb` 인수를 orchestrator가 전달하지 않으므로 실제 PyRosetta 도킹이 발생하지 않음.

---

### 2-4. step05c_boltz_cross

**입력**
```
candidates: List[DockingResult]            ← Step05Output.docking_results
offtarget_receptors: List[Dict]           ← SSTR1/3/4/5 (하드코딩, orchestrator)
sstr2_receptor: Dict                       ← {"name":"SSTR2","uniprot":"P30874"}
config: Dict                               ← alphafold_msa_dir, boltz_env, cuda_device,
                                              tier_thresholds, pair_timeout,
                                              checkpoint_interval, work_dir, sequence_map
```

**출력**
```
Step05cOutput(results, passed_candidates, n_total, n_passed)
파일(save_step05c_results 미호출 — 결함 §3-D): {work_dir}/boltz_cross_validation.json
                                                 {work_dir}/partial_results.json (checkpoint)
                                                 {work_dir}/{pair_id}/boltz_out/...
```

**BoltzSelectivityResult 스키마**
```python
seq_id: str
sequence: str
sstr2_iptm: float
offtarget_iptm: Dict[str, float]   # {SSTR1,SSTR3,SSTR4,SSTR5: iPTM}
selectivity_margin: float          # sstr2_iptm - max(offtarget_iptm)
best_receptor: str
tier: str                          # T0/T1/T2/T3
```

**의존성**: `subprocess(conda run boltz predict)`, `urllib.request` (AlphaFoldDB MSA), `io_schemas.BoltzSelectivityResult`

---

## 3. 결함 목록

### 🔴 Critical

#### C-1. step05b_selectivity: `save_selectivity_results` 미호출 → 출력 파일 0건
**위치**: `pipeline_local/orchestrator.py:859~874`  
**신뢰**: HIGH (직접 코드 확인)

```python
# 현재 orchestrator (줄 859~874) — save 호출 없음
step05b_output = step05b_selectivity.run_selectivity_screening(...)
self._logger.info("[Step05b] %d/%d 선택성 게이트 통과", ...)
# ← save_selectivity_results() 호출 누락!
```

실제 확인:
```
find runs_local -path "*/05b_selectivity/*.json"  → 결과 0건
```

`05b_selectivity/` 디렉토리는 생성되지만(`_write_status`에 경로 등록) 파일은 비어 있음.  
`save_selectivity_results(step05b_output, out_dir / "05b_selectivity")` 호출을 orchestrator에 추가해야 함.

---

### 🟠 High

#### H-1. step04_qc: `apply_plddt_gate` 결과 미사용 (dead code)
**위치**: `step04_qc.py:225~230`  
**신뢰**: HIGH

```python
passed, failed = apply_plddt_gate(qc_results, plddt_min, interface_min)
logger.info("[Step04] QC gate: %d passed / %d failed.", len(passed), len(failed))
# ↑ 결과는 로그에만 사용. return Step04Output(qc_results=qc_results) ← 전체 포함
```

`qc_summary.json`의 `passed` 카운트는 `r.passed_gate`로 계산하므로 일치하지만,  
`apply_plddt_gate`는 **pLDDT 재계산** (이미 `passed_gate`에 포함된 내용과 중복)하여 **이중 필터** 위험을 내포함.  
`passed_gate=False`인 항목이 pLDDT 조건을 만족할 때 `gate_ok`를 `True`로 읽어 결과 불일치 가능.

**권장**: `apply_plddt_gate`를 제거하거나 반환값을 Step04Output 생성에 사용.

#### H-2. step05_docking: DiffPepBuilder 코드 미삭제
**위치**: `step05_docking.py:144, 355~373, 303~347`  
**신뢰**: HIGH

```python
# step05_docking.py:144
# DiffPepBuilder는 비활성화 — 항상 실패하여 타임아웃 낭비. Boltz만 사용.
b2_result = _try_boltz2(...)
```

`_try_diffdock`, `dock_with_diffdock`, `merge_docking_results` 함수 3개가 사문화된 채 잔존.  
docstring의 "engine=boltz" 설명과 `run_docking` 내 로그 "engine=boltz"가 불일치.  
**권장**: 비활성화 코드 제거 또는 `@deprecated` 마킹 + 함수 정리.

#### H-3. step05_docking: affinity 추정 공식 단순화 오류
**위치**: `step05_docking.py:257`  
**신뢰**: HIGH

```python
affinity_estimate: float = -10.0 * iptm if iptm > 0 else float(...)
```

`score` 필드(도킹 게이트 기준)가 이 값으로 설정됨. iPTM 0.7 → -7.0 kcal/mol, iPTM 0.95 → -9.5 kcal/mol로 단조 변환되어 **실제 affinity와 무관한 임의 선형 스케일**.  
Step05b에서 이 score를 `sstr2_dock_score` 기준으로 selectivity margin 계산 → **선택성 결과 신뢰도 저하**.  
**권장**: score 필드에 `iptm` 원값 저장 + UI에 "affinity 미결정" 경고 표시.

#### H-4. step05c_boltz_cross: `work_dir`이 이터레이션 미격리
**위치**: `orchestrator.py:898~901`  
**신뢰**: HIGH

```python
_work_dir = (
    Path(self.config.get("output_dir", "runs_local"))
    / "step05c_boltz_cross"   # ← run_id 없음, iteration 없음
)
```

다중 이터레이션 실행 시 모든 이터레이션이 동일 `partial_results.json` 공유 → 이전 이터레이션 페어를 "완료"로 간주하고 스킵.  
**권장**: `/ run_id / f"iter{iteration:02d}" / "step05c_boltz_cross"` 형태로 격리.

---

### 🟡 Medium

#### M-1. step05c_boltz_cross: `save_step05c_results` 미호출
**위치**: `orchestrator.py:923~934`  
**신뢰**: HIGH

`save_step05c_results(step05c_output, out_dir / "05c_boltz_cross")` 호출 없음.  
`partial_results.json`(checkpoint)은 저장되나 `boltz_cross_validation.json` 미생성.

#### M-2. step05b_selectivity: STATUS_FILE 미갱신
**위치**: orchestrator에서 step05b/c 완료 후 `_write_status` 미호출  
**신뢰**: HIGH

step05b 실행 → step05c(enabled=false 스킵) → 바로 step06 STATUS 기록.  
UI에서 step05b/c 완료 여부를 확인할 수 없음.

#### M-3. step05b_selectivity: estimation mode가 기본 경로
**위치**: `step05b_selectivity.py:251`  
**신뢰**: HIGH

```python
if receptor_pdb and Path(receptor_pdb).exists() and sstr2_complex_pdb and ...
```

orchestrator가 `sstr2_complex_pdb`를 전달하지 않으므로 항상 estimation mode.  
estimation mode는 `hash(candidate_pdb, receptor_pdb, seed)`로 noise 추가 → **결정론적이지만 실측 기반 아님**.  
모든 정식 run의 05b 결과는 estimation mode 기반임을 문서화해야 함.

#### M-4. step04_qc: PyRosetta 매번 재초기화
**위치**: `step04_qc.py:539`  
**신뢰**: MED

```python
pyrosetta.init("-mute all")  # _try_form_disulfide 내부, 서열마다 호출
```

batch 경로에서는 `_try_form_disulfide`가 호출되지 않지만, fallback 개별 예측 경로에서는  
N개 서열 × `pyrosetta.init()` 반복 → 느림.

---

### 🔵 Low

#### L-1. step05_docking: CIF 파일이 `pose_pdb` 경로에 저장되지 않음
**위치**: `step05_docking.py:419~421`  
**신뢰**: HIGH

```python
# b2.pdb_text = structure_cif (CIF 형식일 수 있음)
pose_path = out_dir / f"pose_{seq_id}_00.pdb"  # 확장자 .pdb 고정
if b2.pdb_text:
    pose_path.write_text(b2.pdb_text, encoding="utf-8")
```

Boltz가 CIF를 반환하면 `.pdb` 확장자로 저장. 다운스트림 PDB 파서 오류 가능.

#### L-2. step05c_boltz_cross: `iptm` vs `pair_chains_iptm` 키 우선순위
**위치**: `step05c_boltz_cross.py:521~526`  
**신뢰**: MED

```python
val = data.get("iptm")            # 전체 복합체 iPTM
val2 = pci.get("0", {}).get("1") # 체인 0-1 쌍 iPTM (더 구체적)
```

Boltz confidence.json에서 두 값이 다를 수 있음. 어떤 값을 selectivity 기준으로 쓸지 정책 필요.

---

## 4. ad-hoc vs 정식 path 비교 (핵심)

### 4-1. 스키마 매핑

| 항목 | ad-hoc (`archives_boltz_eval`) | ad-hoc (`cand03_variants`) | 정식 (`Step05cOutput`) |
|------|-------------------------------|---------------------------|------------------------|
| 총 레코드 | **1,615페어** | **40페어** | `BoltzSelectivityResult` 리스트 |
| 후보 식별자 | `sequence` (아미노산 문자열) | `candidate_id` (ex: `var01_I2L`) | `seq_id` (ex: `bb00_seq00`) |
| 수용체 커버리지 | SSTR1/2/3/4/5 ✓ | SSTR1/2/3/4/5 ✓ | SSTR1/2/3/4/5 (UNIPROT_MAP) |
| iPTM 필드 | `iptm` + `pair_chains_iptm` | `iptm` | `sstr2_iptm`, `offtarget_iptm` |
| 추가 신뢰 지표 | `ptm`, `confidence`, `complex_plddt`, `complex_iplddt` | `ptm`, `confidence`, `complex_plddt` | **없음** (selectivity_margin, tier만) |
| GPU 메타 | `gpu_id`, `elapsed_sec`, `timestamp` | 없음 | 없음 |
| Tier 분류 | 없음 | 없음 | `tier` (T0~T3) |
| 저장 형식 | flat JSON list | flat JSON list | 구조화 dataclass → JSON |

### 4-2. 데이터 통합 방법 (권장)

**ad-hoc 1615페어 → 정식 Step05cOutput 변환 ETL**:

```python
# archives_boltz_eval/all_results.json 활용 예
from pipeline_local.schemas.io_schemas import BoltzSelectivityResult, Step05cOutput
from pipeline_local.steps.step05c_boltz_cross import compute_selectivity_margin, classify_tier

with open("runs_local/archives_boltz_eval/all_results.json") as f:
    raw = json.load(f)

# sequence → {receptor: iptm} 매트릭스로 그룹핑
matrix: Dict[str, Dict[str, float]] = {}
for r in raw:
    seq = r["sequence"]
    rec = r["receptor"]
    if seq not in matrix:
        matrix[seq] = {}
    matrix[seq][rec] = r["iptm"]

results = []
for seq, iptm_map in matrix.items():
    sstr2_iptm = iptm_map.get("SSTR2", 0.0)
    offtarget = {k: v for k, v in iptm_map.items() if k != "SSTR2"}
    margin, best = compute_selectivity_margin(sstr2_iptm, offtarget)
    tier = classify_tier(margin)
    results.append(BoltzSelectivityResult(
        seq_id=seq[:14],   # 또는 별도 매핑
        sequence=seq,
        sstr2_iptm=sstr2_iptm,
        offtarget_iptm=offtarget,
        selectivity_margin=margin,
        best_receptor=best,
        tier=tier,
    ))
```

**불일치 주의**:
1. `sequence` 기반 식별자 vs `seq_id` 기반 → 변환 필요
2. ad-hoc에는 `ptm`, `complex_plddt`, `elapsed_sec` 등 정식 schema에 없는 필드 존재 → 버림 또는 별도 메타 필드로 보존 권장
3. `cand03_variants`(40페어)는 `candidate_id`가 이미 변이체 ID이므로 `seq_id`로 직접 사용 가능

### 4-3. 일치/불일치 요약

| 항목 | 일치 여부 | 비고 |
|------|-----------|------|
| iPTM 측정 방식 | ✓ 동일 (Boltz-2 confidence.json) | |
| 수용체 5종 커버리지 | ✓ 동일 | |
| selectivity_margin 공식 | ✗ **불일치** — ad-hoc은 margin 미계산, 정식은 `sstr2_iptm - max(off)` | |
| Tier 분류 | ✗ **불일치** — ad-hoc 없음, 정식만 T0~T3 | |
| 추가 신뢰 지표 보존 | ✗ **불일치** — 정식 schema에 `ptm`, `complex_plddt` 필드 없음 | |
| 이터레이션 격리 | ✗ **불일치** — ad-hoc은 독립 run, 정식은 work_dir 공유 오류 (H-4) | |

---

## 5. STATUS_FILE 갱신 분석

| 단계 | `_write_status` 호출 | 파일 저장 |
|------|---------------------|-----------|
| step04 | ✓ (orchestrator L770, L795) | qc_summary.json ✓ |
| step05 | ✓ (orchestrator L806, L836) | docking_scores.json ✓ |
| **step05b** | **✗ 미호출** | selectivity_scores.json **✗** |
| **step05c** | **✗ 미호출** | boltz_cross_validation.json **✗** |
| step06 | ✓ (orchestrator L974) | — |

step05b/c는 메모리 내에서 실행·로깅되지만 UI Status 반영과 파일 영속화가 모두 누락됨.

---

## 6. 결함 우선순위 (Impact ÷ Effort)

| # | 결함 | Impact | Effort | 우선순위 |
|---|------|--------|--------|----------|
| C-1 | step05b save 미호출 | Critical (파일 0건) | Low (1줄 추가) | **최우선** |
| H-4 | step05c work_dir 미격리 | High (checkpoint 오염) | Low (경로 수정) | **2순위** |
| M-1 | step05c save 미호출 | High (파일 미저장) | Low (1줄 추가) | **2순위** |
| M-2 | step05b/c STATUS 미갱신 | Medium (UI 오정보) | Low (2줄 추가) | **3순위** |
| H-1 | apply_plddt_gate dead code | Medium (잠재 불일치) | Low (리팩토링) | **4순위** |
| H-2 | DiffPepBuilder 미삭제 | Low (유지보수 부담) | Medium (코드 정리) | **5순위** |
| H-3 | affinity 공식 단순화 | Medium (선택성 신뢰도) | Medium (설계 결정) | **5순위** |
| M-3 | estimation mode 기본화 | Medium (결과 신뢰도) | High (인프라) | **6순위** |

---

## 7. 권장 리팩토링

### 7-1. 즉시 수정 (1~2줄)

```python
# orchestrator.py — step05b 이후 (줄 ~874)
if step05b_output is not None:
    _05b_dir = output_base / run_id / "05b_selectivity"
    _05b_dir.mkdir(parents=True, exist_ok=True)
    step05b_selectivity.save_selectivity_results(step05b_output, _05b_dir)
    self._write_status("step05b_selectivity", "completed", ...)

# orchestrator.py — step05c 이후 (줄 ~934)
if step05c_output is not None:
    _05c_dir = output_base / run_id / "05c_boltz_cross"
    step05c_boltz_cross.save_step05c_results(step05c_output, _05c_dir)
    self._write_status("step05c_boltz_cross", "completed", ...)
```

### 7-2. step05c work_dir 격리

```python
# orchestrator.py:899
_work_dir = (
    Path(self.config.get("output_base_dir", "runs_local"))
    / run_id
    / f"iter{iteration:02d}"
    / "step05c_boltz_cross"
)
```

### 7-3. step04 apply_plddt_gate 정리

```python
# step04_qc.py:225 — 아래 중 하나 선택
# 안 A: 반환값을 사용 (filtering 명시화)
passed, failed = apply_plddt_gate(qc_results, plddt_min, interface_min)
return Step04Output(qc_results=qc_results)  # 기존 유지, gate 결과는 로그용

# 안 B: apply_plddt_gate 제거 (passed_gate 필드로 이미 충분)
# apply_plddt_gate 삭제 → 이미 run_qc 배치/fallback 경로에서 passed_gate 설정
```

### 7-4. DiffPepBuilder 코드 정리

```python
# step05_docking.py에서 삭제 권장 (140+ 줄):
# - dock_with_diffdock()
# - _try_diffdock()
# - merge_docking_results()
# - DockResult dataclass
```

---

## 8. UI 표시 권장

### 8-1. Selectivity Matrix 뷰 (step05b/c)

```
후보       SSTR1  SSTR2  SSTR3  SSTR4  SSTR5  Margin  Tier
bb00_seq00  0.93   0.97   0.92   0.90   0.89  +0.04   T3 🟢
bb00_seq01  0.94   0.95   0.94   0.91   0.90  +0.01   T2 🟡
bb01_seq02  0.96   0.93   0.95   0.92   0.91  -0.02   T1 🟠
```

현재 UI에 이 매트릭스 뷰가 없음 → selectivity router 또는 별도 탭으로 추가 권장.

### 8-2. Tier 뱃지 (step05c)

```
T3 ███ SSTR2 선택적 (margin ≥ +0.03)
T2 ██  SSTR2 우세   (margin ≥ 0.00)
T1 █   주의 필요    (margin ≥ -0.03)
T0     탈락          (margin < -0.03)
```

Phase 1: `BoltzSelectivityResult.tier` → UI chip 색상 매핑  
Phase 2: iPTM matrix 히트맵 (5×N 수용체 격자)

### 8-3. iPTM 해석 경고 (⚠️ 의무)

```
⚠️ iPTM 경고: geometry 신뢰도 기반 1차 스크리닝 결과입니다.
   SST-14 실측 검증에서 Ki↔iPTM 순위 일치 0/5.
   정량 선택성 평가(FEP/Ki assay)로 확정이 필요합니다.
```

step05c_boltz_cross.py:19~35에 이미 상세 문서화됨 → UI 경고 배너로 노출 필요.

---

## 9. 신규 기능 제안

### P-1. ad-hoc → 정식 ETL 유틸리티
`archives_boltz_eval/all_results.json`(1615페어)를 `Step05cOutput`으로 변환하는  
`pipeline_local/utils/import_adhoc_boltz.py` 유틸리티 — 한 번 실행으로 과거 ad-hoc 데이터를  
정식 Tier 분류와 비교 가능하게 만듦.

### P-2. step05b Production Mode 활성화
orchestrator에서 step06 rosetta refinement의 complex PDB를 step05b에 피드백:
```python
# step06 완료 후 step05b production mode 재실행 (정밀 선택성)
if step06_out and step05b_output:
    sstr2_complex = step06_out.top_result().pdb_path
    step05b_selectivity.run_selectivity_screening(
        candidates=top_candidates,
        ...
        sstr2_complex_pdb=sstr2_complex,  # production mode 활성화
    )
```

### P-3. step05c 증분 실행 지원 (현재 checkpoint 존재)
`partial_results.json`이 이미 구현됨(work_dir 격리 수정 후) → UI에  
"Boltz 교차검증 재개" 버튼 추가로 중단된 run 복구 가능.

### P-4. `complex_plddt` 필드 정식 schema 편입
ad-hoc 데이터에는 있지만 정식 `BoltzSelectivityResult`에 없는 `complex_plddt`, `ptm` 필드를  
schema에 Optional로 추가하여 신뢰도 지표를 보존.

---

## 10. 누락된 테스트 케이스

| 항목 | 필요 이유 | 신뢰 |
|------|-----------|------|
| `save_selectivity_results` → 파일 실제 생성 확인 | C-1 재발 방지 | HIGH |
| `apply_plddt_gate` vs `passed_gate` 일관성 테스트 | H-1 이중 필터 검출 | HIGH |
| `work_dir` 이터레이션 격리 → checkpoint 독립성 | H-4 재발 방지 | HIGH |
| DiffPepBuilder 비활성화 상태 회귀 테스트 | H-2 재활성화 방지 | MED |
| estimation mode 결정론성 (same seed → same score) | M-3 신뢰도 문서화 | MED |
| ad-hoc 1615페어 ETL → Tier 분포 검증 | P-1 구현 후 | LOW |

---

## 11. §검증 필요 항목

| ID | 항목 | 신뢰 |
|----|------|------|
| V-1 | step05b estimation mode의 실제 selectivity margin 분포가 실측과 얼마나 다른가 | LOW (추론) |
| V-2 | affinity_estimate = -10 × iPTM 공식의 문헌적 근거 또는 실측 calibration | LOW (추론) |
| V-3 | step05c `iptm` vs `pair_chains_iptm` 두 값의 평균 차이 크기 | MED |

---

*보고서 종료*
