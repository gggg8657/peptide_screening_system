# PRST-001~004 pepADMET 재검증

일시: 2026-05-20
선행: V-02/V-03 (D-AA 추론 작동)

## 1. 입력 서열·SMILES 4건

SMILES 변환은 `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/pyrosetta_flow/smiles_converter.py`의 `sequence_to_smiles()`를 사용했다. 기본 Python 환경에는 RDKit이 없어 `None`이 반환되었고, `conda run --no-capture-output -n pepadmet python3` 환경에서 파일 단위 `importlib` 로드로 변환했다. 4건 모두 변환 성공.

| 후보 | 서열 | SMILES 변환 | Exact MW |
|---|---|---:|---:|
| PRST-001 | AGCKNIIWKTITSC | 성공 | 1534.763605 |
| PRST-002 | AGCKNFIWKTITSC | 성공 | 1568.747955 |
| PRST-003 | AGCRNFIWKTITSC | 성공 | 1596.754103 |
| PRST-004 | AICKNFIWKTITSC | 성공 | 1624.810555 |

```json
[
  {
    "label": "PRST-001",
    "sequence": "AGCKNIIWKTITSC",
    "smiles": "CC[C@H](C)[C@@H]1NC(=O)[C@H](CC(N)=O)NC(=O)[C@H](CCCCN)NC(=O)[C@@H](NC(=O)CNC(=O)[C@H](C)N)CSSC[C@@H](C(=O)O)NC(=O)[C@H](CO)NC(=O)[C@H]([C@@H](C)O)NC(=O)[C@H]([C@@H](C)CC)NC(=O)[C@H]([C@@H](C)O)NC(=O)[C@H](CCCCN)NC(=O)[C@H](Cc2c[nH]c3ccccc23)NC(=O)[C@H]([C@@H](C)CC)NC1=O"
  },
  {
    "label": "PRST-002",
    "sequence": "AGCKNFIWKTITSC",
    "smiles": "CC[C@H](C)[C@@H]1NC(=O)[C@H](Cc2ccccc2)NC(=O)[C@H](CC(N)=O)NC(=O)[C@H](CCCCN)NC(=O)[C@@H](NC(=O)CNC(=O)[C@H](C)N)CSSC[C@@H](C(=O)O)NC(=O)[C@H](CO)NC(=O)[C@H]([C@@H](C)O)NC(=O)[C@H]([C@@H](C)CC)NC(=O)[C@H]([C@@H](C)O)NC(=O)[C@H](CCCCN)NC(=O)[C@H](Cc2c[nH]c3ccccc23)NC1=O"
  },
  {
    "label": "PRST-003",
    "sequence": "AGCRNFIWKTITSC",
    "smiles": "CC[C@H](C)[C@@H]1NC(=O)[C@H](Cc2ccccc2)NC(=O)[C@H](CC(N)=O)NC(=O)[C@H](CCCNC(=N)N)NC(=O)[C@@H](NC(=O)CNC(=O)[C@H](C)N)CSSC[C@@H](C(=O)O)NC(=O)[C@H](CO)NC(=O)[C@H]([C@@H](C)O)NC(=O)[C@H]([C@@H](C)CC)NC(=O)[C@H]([C@@H](C)O)NC(=O)[C@H](CCCCN)NC(=O)[C@H](Cc2c[nH]c3ccccc23)NC1=O"
  },
  {
    "label": "PRST-004",
    "sequence": "AICKNFIWKTITSC",
    "smiles": "CC[C@H](C)[C@H](NC(=O)[C@H](C)N)C(=O)N[C@H]1CSSC[C@@H](C(=O)O)NC(=O)[C@H](CO)NC(=O)[C@H]([C@@H](C)O)NC(=O)[C@H]([C@@H](C)CC)NC(=O)[C@H]([C@@H](C)O)NC(=O)[C@H](CCCCN)NC(=O)[C@H](Cc2c[nH]c3ccccc23)NC(=O)[C@H]([C@@H](C)CC)NC(=O)[C@H](Cc2ccccc2)NC(=O)[C@H](CC(N)=O)NC(=O)[C@H](CCCCN)NC1=O"
  }
]
```

## 2. pepADMET 추론 결과 (원문 JSON 첨부)

실행 명령:

```bash
PEPADMET_REPO=/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/pepadmet_local/pepADMET \
conda run --no-capture-output -n pepadmet python3 \
/home/dongjukim/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/pyrosetta_flow/pepadmet_infer_script.py \
'[{"sequence":"...","label":"PRST-001","smiles":"..."}, ...]'
```

실행 중 RDKit `onlyHeavy` deprecation warning과 `MY_GNN.py:123` tensor copy warning이 출력됐으나, 4건 모두 `available: true`로 결과가 생성됐다. `pepadmet_infer_script.py`는 입력 `label`을 결과에 보존하지 않아, 아래 JSON은 입력 순서와 `sequence`로 후보 ID를 매핑했다.

```json
[
  {
    "sequence": "AGCKNIIWKTITSC",
    "available": true,
    "binary_toxicity": 1.0,
    "is_toxic": true,
    "toxicity_type": "hemostasis",
    "toxicity_type_confidence": 1.0,
    "neurotoxicity_type": "Na_inhibitor",
    "neurotoxicity_confidence": 1.0,
    "hc50": -38.6135
  },
  {
    "sequence": "AGCKNFIWKTITSC",
    "available": true,
    "binary_toxicity": 1.0,
    "is_toxic": true,
    "toxicity_type": "hemostasis",
    "toxicity_type_confidence": 1.0,
    "neurotoxicity_type": "Na_inhibitor",
    "neurotoxicity_confidence": 1.0,
    "hc50": -41.7199
  },
  {
    "sequence": "AGCRNFIWKTITSC",
    "available": true,
    "binary_toxicity": 1.0,
    "is_toxic": true,
    "toxicity_type": "hemostasis",
    "toxicity_type_confidence": 1.0,
    "neurotoxicity_type": "Na_inhibitor",
    "neurotoxicity_confidence": 1.0,
    "hc50": -43.622
  },
  {
    "sequence": "AICKNFIWKTITSC",
    "available": true,
    "binary_toxicity": 1.0,
    "is_toxic": true,
    "toxicity_type": "hemostasis",
    "toxicity_type_confidence": 1.0,
    "neurotoxicity_type": "Na_inhibitor",
    "neurotoxicity_confidence": 1.0,
    "hc50": -45.3764
  }
]
```

## 3. 합성 의뢰서 0.10 값 vs pepADMET 실측 비교 매트릭스

의뢰서의 ADMET 값은 4건 모두 0.10이 아니라, PRST-001=0.10, PRST-002=0.12, PRST-003=0.20, PRST-004=0.25로 기록되어 있었다.

| 후보 | 서열 | 의뢰서 ADMET | pepADMET binary_toxicity | toxicity_type | neurotoxicity_type | hc50 | 불일치 여부 |
|---|---|---:|---:|---|---|---:|---|
| PRST-001 | AGCKNIIWKTITSC | 0.10 | 1.00 | hemostasis | Na_inhibitor | -38.6135 | 불일치 (+0.90, 10.00x) |
| PRST-002 | AGCKNFIWKTITSC | 0.12 | 1.00 | hemostasis | Na_inhibitor | -41.7199 | 불일치 (+0.88, 8.33x) |
| PRST-003 | AGCRNFIWKTITSC | 0.20 | 1.00 | hemostasis | Na_inhibitor | -43.6220 | 불일치 (+0.80, 5.00x) |
| PRST-004 | AICKNFIWKTITSC | 0.25 | 1.00 | hemostasis | Na_inhibitor | -45.3764 | 불일치 (+0.75, 4.00x) |

toxic 분류 후보: PRST-001, PRST-002, PRST-003, PRST-004 전부 (`is_toxic: true`, `binary_toxicity > 0.5`).

## 4. 결론

- 합성 의뢰서의 ADMET 값은 현 pepADMET 재추론 결과와 일치하지 않는다. 재추론 기준 4개 후보 모두 `binary_toxicity=1.0`이며 toxic 분류다.
- 0.10 값의 직접 출처는 실제 pepADMET 출력으로 확인되지 않았다. `runs_local/final_candidates/p1_sprint_prst001_004/all_candidates.csv`에는 `admet_tox`가 0.10/0.12/0.20/0.25로 들어 있으나, 같은 행의 `enrichment_notes`에는 `admet wrapper returned no toxicity score`가 기록되어 있다.
- 코드 흔적상 `pipeline_local/scripts/composite_scorer_cli.py`의 예시 후보 입력에 동일한 `admet_tox` 값들이 하드코딩되어 있고, `pipeline_local/scripts/composite_scorer.py`는 wrapper가 toxicity score를 반환하지 못하면 기존 `admet_tox`를 유지한다. 따라서 의뢰서 값은 “실제 pepADMET 추론값”이 아니라 composite scorer 입력/예시값 또는 fallback 입력값에서 전파됐을 가능성이 높다.
- 권고: PRST-001~004 합성 의뢰서의 ADMET 독성 확률 및 Hard Cutoff PASS 판정을 갱신해야 한다. 현 pepADMET 출력만 기준으로 하면 4개 후보 모두 `admet_tox_max=0.3` cutoff를 통과하지 못한다.
- 추가 검증 필요: `hc50`의 단위/부호 해석은 `pepadmet_infer_script.py` 출력만으로 확정하지 않았다. 본 보고서에서는 원문 출력값만 기록했다.
