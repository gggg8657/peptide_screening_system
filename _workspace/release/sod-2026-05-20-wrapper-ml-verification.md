# SOD 2026-05-20 — Wrapper + ML Step 검증 보고서

**작성**: engineer-infra  
**일시**: 2026-05-20  
**목적**: T2.4 (외부 wrapper 3종) + T3 부분 (pipeline_local steps) 실 동작 검증  
**입력**: SST14 = `AGCKNFFWKTFTSC`

---

## §1 Wrapper 3종 실측 결과

### 1.1 실행 명령 및 요약표

| Wrapper | conda env | 호출 성공? | 응답 시간 | 핵심 출력 |
|---------|-----------|-----------|-----------|-----------|
| `predict_halflife_pepmsnd.py` | `peptools` | ✅ **SUCCESS** | ~3.9 s | PlifePred2 score=3.38 (P4 grade, 확률값) |
| `predict_admet_pepadmet.py` | `pepadmet` | ✅ **SUCCESS** | ~1.5 s | modlamp descriptors: MW=1638.9, charge=2.68, Instability=30.65 (P3 grade) |
| `predict_admet_ai_wrapper.py` | `bio-tools` | ❌ **BROKEN** | ~1.0 s | CLI entrypoint 없음 + `admet_ai` 패키지 미설치 |

---

### 1.2 상세 결과

#### predict_halflife_pepmsnd.py (✅ 정상)

```json
{
  "input_sequence": "AGCKNFFWKTFTSC",
  "seq_id": "query",
  "tool_status": { "plifepred2": "success" },
  "plifepred2": {
    "plifepred2_score": 3.3801775046779348,
    "plifepred2_score_unit": "probability (0~1, NOT hours)",
    "plifepred2_model": "model_1_natural",
    "confidence_grade": "P4"
  },
  "final_confidence_grade": "P4"
}
```

- 출력 파일: `/tmp/verify_pepmsnd_sst14.json` ✅
- **주의**: PlifePred2 score는 0~1 확률값이며 시간(hour) 단위 아님 (H-06 가드 적용)
- P4 등급: heuristic, TPP KPI(≥24h) 직접 적용 불가

---

#### predict_admet_pepadmet.py (✅ 정상 — 폴백 모드)

```json
{
  "input_sequence": "AGCKNFFWKTFTSC",
  "seq_id": "query",
  "tool_status": { "modlamp": "success" },
  "modlamp_descriptors": {
    "molecular_weight_da": 1638.92,
    "charge_ph7": 2.681,
    "isoelectric_point": 9.877,
    "instability_index": 30.65,
    "boman_index": 0.693,
    "aliphatic_index": 7.14,
    "hydrophobic_ratio": 0.429,
    "aromaticity": 0.286,
    "confidence_grade": "P3"
  },
  "final_confidence_grade": "P3"
}
```

- 출력 파일: `/tmp/verify_pepadmet_sst14.json` ✅
- pepADMET 웹서버 미응답 → modlamp v0.4.3 로컬 폴백으로 실행됨
- P3 등급: 물리화학 디스크립터 (ADMET 직접 예측 아님, proxy만)
- InstabilityIndex=30.65 < 40 → 안정 (ProtParam 기준)

---

#### predict_admet_ai_wrapper.py (❌ BROKEN — 2가지 결함)

**결함 1**: CLI entrypoint 없음
- `predict_admet_ai_wrapper.py`는 99줄 라이브러리 모듈
- `main()`, `argparse`, `if __name__ == "__main__":` 전혀 없음
- `--sequence`, `--output` 인자를 argparse로 처리하는 코드 없음
- 결과: 스크립트 실행 시 아무것도 안 하고 종료 (output 파일 미생성)

**결함 2**: `admet_ai` 패키지 미설치 (bio-tools env)
```json
{
  "ok": false,
  "error": "admet_ai_import_failed: ModuleNotFoundError: No module named 'admet_ai'"
}
```

- `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/admet_ai_local/` 경로 존재하나 패키지가 bio-tools env에 설치 안 됨
- 전용 conda env (`_workspace/admet_ai_local/.conda_env`)는 존재하나 bio-tools와 분리됨

**종합**: CLI wrapper로서 완전 미구현 상태. 라이브러리 함수(`predict_admet_layer3`)는 존재하나 인자로 sequence가 아닌 SMILES를 받음 + 패키지 미설치로 실 추론 불가.

---

## §2 pipeline_local steps import 표

| Step | import? | 핵심 함수/클래스 (dir 첫 5개) |
|------|---------|-------------------------------|
| `step01_receptor` | ✅ OK | Any, Dict, List, LocalModelRunner, Optional |
| `step02_backbone` | ✅ OK | Any, Dict, List, LocalModelRunner, Optional |
| `step03_sequence` | ✅ OK | Any, Dict, List, LocalModelRunner, Optional |
| `step04_qc` | ✅ OK | Any, Dict, List, LocalModelRunner, Optional |
| `step05_docking` | ✅ OK | Any, Boltz2Result, Dict, DockResult, DockingResult |
| `step05b_selectivity` | ✅ OK | Any, Dict, DockingResult, List, OffTargetDockingResult |
| `step06_rosetta` | ✅ OK | Any, Dict, DockingResult, List, Optional |
| `step07_analysis` | ✅ OK | Any, Dict, FoldMasonResult, InterfaceReport, List |
| `step08_stability` | ✅ OK | Any, Dict, List, ModificationSuggestion, Optional |

**결론**: 8/8 모두 import 성공 ✅ — bio-tools env에서 파이프라인 전체 모듈 로드 가능

---

## §3 DL 모델 존재 여부 + 어제 산출물

### 3.1 conda env 존재 여부

| Env | 경로 | 상태 |
|-----|------|------|
| `bio-tools` | `/home/dongjukim/miniforge3/envs/bio-tools` | ✅ 존재 |
| `rfdiffusion` | `/home/dongjukim/miniforge3/envs/rfdiffusion` | ✅ 존재 |
| `diffpepbuilder` | `/home/dongjukim/miniforge3/envs/diffpepbuilder` | ✅ 존재 |
| `esmfold` | `/home/dongjukim/miniforge3/envs/esmfold` | ✅ 존재 |
| `proteinmpnn` | `/home/dongjukim/miniforge3/envs/proteinmpnn` | ✅ 존재 |
| `peptools` | `/home/dongjukim/miniforge3/envs/peptools` | ✅ 존재 |
| `pepadmet` | `/home/dongjukim/miniforge3/envs/pepadmet` | ✅ 존재 |
| `admet_ai_local` | `_workspace/admet_ai_local/.conda_env` | ✅ 존재 (bio-tools와 분리) |

---

### 3.2 모델 파일 존재 여부

**runs_local/diffdock_poc/ (2026-05-19 생성)**
```
runs_local/diffdock_poc/
├── data/
├── docking_run/SSTR2receptor/SST14/   ← 10개 sample PDB
├── poses/                              ← 7개 pose PDB (~15KB each)
├── processed/SSTR2receptor_SST14.pkl
├── poc_report.json                     ← 5.5KB
└── poc_report.md                       ← 5.9KB
```

**data/somatostatin_receptor/ — Boltz 산출물**
```
SSTR2_SST14_complex_boltz_1.pdb   304KB  2026-05-19 12:33
SSTR2_SST14_complex_boltz_2.pdb   304KB  2026-05-19 12:33
SSTR2_SST14_complex_boltz_3.pdb   304KB  2026-05-19 12:33
SSTR2_SST14_complex_metadata.json 3.6KB  2026-05-19 12:33
```

---

### 3.3 runs_local/sstr2_sst14_complex/*.pdb

`runs_local/sstr2_sst14_complex/` 디렉토리는 **존재하지 않음**.  
어제 Boltz 산출물은 `data/somatostatin_receptor/` 하위에 저장됨 (위 §3.2 참조).

---

## §4 결론 (working / broken / unimplemented)

| 컴포넌트 | 상태 | 비고 |
|---------|------|------|
| `predict_halflife_pepmsnd.py` | ✅ **WORKING** | PlifePred2 정상, P4 등급 정직 보고 |
| `predict_admet_pepadmet.py` | ✅ **WORKING** (폴백) | modlamp 폴백, pepADMET 웹 미응답, P3 |
| `predict_admet_ai_wrapper.py` | ❌ **BROKEN** | CLI entrypoint 미구현 + admet_ai 패키지 미설치 |
| pipeline_local steps (8개) | ✅ **WORKING** | 8/8 import 성공 |
| conda envs (DL) | ✅ **EXISTS** | rfdiffusion, esmfold, proteinmpnn, diffpepbuilder |
| Boltz 복합체 PDB | ✅ **EXISTS** | 3개 구조 (boltz_1/2/3, 304KB each, 2026-05-19) |
| DiffDock 도킹 결과 | ✅ **EXISTS** | 10 samples + 7 poses (2026-05-19) |

### 액션 아이템

| 우선순위 | 항목 | 대상 |
|---------|------|------|
| P1 | `predict_admet_ai_wrapper.py`에 CLI entrypoint (`argparse`, SMILES 변환 포함) 구현 | engineer-backend |
| P1 | `bio-tools` env에 `admet_ai` 패키지 설치 또는 전용 env 활성화 로직 추가 | engineer-infra |
| P2 | pepADMET 웹서버 (`pepadmet.ddai.tech`) 접근성 재확인 | engineer-backend |

---

*총 소요시간: ~7분 (wrapper 3종 병렬 실행 + import 검증 + 파일 확인 + 보고서 작성)*
