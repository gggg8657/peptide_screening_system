# PyBioMed estate.py 패치 (옵션 C 실행)
**일시**: 2026-05-20
**근거**: A-03_research_pepadmet_environment.md (researcher 2026-05-20)

## 1. estate.py 위치 식별 결과
- pepADMET clone 내 번들 경로 확인:
  - 명령어: `find _workspace/pepadmet_local/pepADMET -path '*PyBioMed/PyMolecule/estate.py' -print`
  - 출력: 없음
- conda env 위치:
  - 명령어: `conda env list | grep pepadmet || true`
  - 출력: `pepadmet                 /home/dongjukim/miniforge3/envs/pepadmet`
- 찾은 `estate.py` 경로:
  - 명령어: `find /home/dongjukim/miniforge3/envs/pepadmet -path '*PyBioMed/PyMolecule/estate.py' -print`
  - 출력: `/home/dongjukim/miniforge3/envs/pepadmet/lib/python3.7/site-packages/PyBioMed/PyMolecule/estate.py`
- 패치 전 대상 호출 확인:
  - 명령어: `rg -n "round\\(j, 3\\)|round\\(" /home/dongjukim/miniforge3/envs/pepadmet/lib/python3.7/site-packages/PyBioMed/PyMolecule/estate.py`
  - 관련 출력: `164:        res["S" + str(i + 1)] = round(j, 3)`

## 2. 패치 diff
```diff
--- /home/dongjukim/miniforge3/envs/pepadmet/lib/python3.7/site-packages/PyBioMed/PyMolecule/estate.py.bak.20260520	2026-05-20 02:41:41.364248126 +0000
+++ /home/dongjukim/miniforge3/envs/pepadmet/lib/python3.7/site-packages/PyBioMed/PyMolecule/estate.py	2026-05-20 02:41:48.216247718 +0000
@@ -161,7 +161,7 @@
     temp = ESFP.FingerprintMol(mol)
     res = {}
     for i, j in enumerate(temp[1]):
-        res["S" + str(i + 1)] = round(j, 3)
+        res["S" + str(i + 1)] = round(float(j), 3)
 
     return res
```

패치 후 확인:
```text
164:        res["S" + str(i + 1)] = round(float(j), 3)
```

## 3. 백업 위치
- `/home/dongjukim/miniforge3/envs/pepadmet/lib/python3.7/site-packages/PyBioMed/PyMolecule/estate.py.bak.20260520`
- 백업 생성 출력:
```text
-rw-r--r-- 1 dongjukim dongjukim 11789 May 20 02:41 /home/dongjukim/miniforge3/envs/pepadmet/lib/python3.7/site-packages/PyBioMed/PyMolecule/estate.py.bak.20260520
```

## 4. calculate_descriptors.py 재시도 결과
- 실행 위치: `_workspace/pepadmet_local/pepADMET`
- 명령어:
```bash
conda run -n pepadmet python calculate_descriptors.py
```

- 실제 출력 요약:
```text
/home/dongjukim/miniforge3/envs/pepadmet/lib/python3.7/site-packages/joblib/_multiprocessing_helpers.py:46: UserWarning: [Errno 28] No space left on device.  joblib will operate in serial mode
  warnings.warn('%s.  joblib will operate in serial mode' % (e,))

Calculating descriptors: 100%|██████████| 4/4 [00:29<00:00,  7.30s/it]
Feature calculation completed
```

RDKit `onlyHeavy` deprecation warning이 여러 번 출력됐으나 실행은 종료 코드 0으로 완료됐다.

- 결과 CSV 검증 명령어:
```bash
conda run -n pepadmet python -c "import pandas as pd; p='data/example_feature_result.csv'; df=pd.read_csv(p); print('path:', p); print('shape:', df.shape); print('has_Error_column:', 'Error' in df.columns); print('non_null_Error:', int(df['Error'].notna().sum()) if 'Error' in df.columns else 'n/a'); print('rows:', len(df)); print('SMILES_null:', int(df['SMILES'].isna().sum()) if 'SMILES' in df.columns else 'missing'); print('SEQUENCE_values:', df['SEQUENCE'].tolist() if 'SEQUENCE' in df.columns else 'missing')"
```

- 실제 출력:
```text
path: data/example_feature_result.csv
shape: (4, 2135)
has_Error_column: False
non_null_Error: n/a
rows: 4
SMILES_null: 0
SEQUENCE_values: ['GLPALISWIKRKRL', 'IVPFLLGMVPKLVCLITKKC', 'KLKLKLKLKLKLKLKLKLKLKLKLKL', 'ILPILSLIGGLL']
```

- 판정: 성공. sample 4행 모두 `Error` 열 없이 descriptor CSV 생성 완료.

## 5. V-03 재검증 (선택)
### 5.1 입력 준비
- D-AA Octreotide SMILES는 PubChem PUG REST에서 실제 조회:
```bash
curl -fsS 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Octreotide/property/IsomericSMILES,CanonicalSMILES/JSON' | head -c 4000
```

관련 출력:
```text
"CID": 448601,
"SMILES": "C[C@H]([C@H]1C(=O)N[C@@H](CSSC[C@@H](C(=O)N[C@H](C(=O)N[C@@H](C(=O)N[C@H](C(=O)N1)CCCCN)CC2=CNC3=CC=CC=C32)CC4=CC=CC=C4)NC(=O)[C@@H](CC5=CC=CC=C5)N)C(=O)N[C@H](CO)[C@@H](C)O)O"
```

- L-AA 대조군 `FCFWKTCT` SMILES는 로컬 `smiles_converter.py` 직접 로드로 생성:
```text
sequence: FCFWKTCT
smiles: C[C@@H](O)[C@H](NC(=O)[C@@H]1CSSC[C@H](NC(=O)[C@@H](N)Cc2ccccc2)C(=O)N[C@@H](Cc2ccccc2)C(=O)N[C@@H](Cc2c[nH]c3ccccc23)C(=O)N[C@@H](CCCCN)C(=O)N[C@@H]([C@@H](C)O)C(=O)N1)C(=O)O
mw: 1032.419744868
```

참고: `pyrosetta_flow.smiles_converter` package import는 pepadmet Python 3.7에서 상위 `pyrosetta_flow/__init__.py` import 중 walrus 문법 때문에 실패하여 파일 직접 로드 방식을 사용했다.

### 5.2 toxicity 예측 출력
- 명령어:
```bash
PEPADMET_REPO=/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/pepadmet_local/pepADMET \
conda run --no-capture-output -n pepadmet python3 \
/home/dongjukim/Documents/workspace/repos/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/pyrosetta_flow/pepadmet_infer_script.py \
'[{"sequence":"FCFWKTCT","label":"octreotide_DAA_pubchem","smiles":"C[C@H]([C@H]1C(=O)N[C@@H](CSSC[C@@H](C(=O)N[C@H](C(=O)N[C@@H](C(=O)N[C@H](C(=O)N1)CCCCN)CC2=CNC3=CC=CC=C32)CC4=CC=CC=C4)NC(=O)[C@@H](CC5=CC=CC=C5)N)C(=O)N[C@H](CO)[C@@H](C)O)O"},{"sequence":"FCFWKTCT","label":"octreotide_LAA_converter","smiles":"C[C@@H](O)[C@H](NC(=O)[C@@H]1CSSC[C@H](NC(=O)[C@@H](N)Cc2ccccc2)C(=O)N[C@@H](Cc2ccccc2)C(=O)N[C@@H](Cc2c[nH]c3ccccc23)C(=O)N[C@@H](CCCCN)C(=O)N[C@@H]([C@@H](C)O)C(=O)N1)C(=O)O"}]'
```

- 실제 출력 중 JSON 결과:
```json
[
  {
    "sequence": "FCFWKTCT",
    "available": true,
    "binary_toxicity": 1.0,
    "is_toxic": true,
    "toxicity_type": "hemostasis",
    "toxicity_type_confidence": 1.0,
    "neurotoxicity_type": "Na_inhibitor",
    "neurotoxicity_confidence": 1.0,
    "hc50": -14.4873
  },
  {
    "sequence": "FCFWKTCT",
    "available": true,
    "binary_toxicity": 1.0,
    "is_toxic": true,
    "toxicity_type": "hemostasis",
    "toxicity_type_confidence": 1.0,
    "neurotoxicity_type": "Na_inhibitor",
    "neurotoxicity_confidence": 1.0,
    "hc50": -14.8955
  }
]
```

- 판정:
  - D-AA PubChem SMILES와 L-AA converter SMILES 모두 graph build 및 descriptor 생성에 성공했다.
  - 두 결과 모두 `available=true`, `binary_toxicity=1.0`, `toxicity_type=hemostasis`, `neurotoxicity_type=Na_inhibitor`.
  - `hc50`만 D-AA `-14.4873`, L-AA `-14.8955`로 차이가 있었다.
  - 출력 스키마가 입력 `label`을 보존하지 않으므로 결과 순서는 입력 순서 기준이다.

## 6. 다음 단계
- 패치 성공: `pharmacology_guards.py`의 `d_amino_acid_support='partial'`을 즉시 `partial-tested`로 올릴 수 있는 실행 증거는 확보했다.
- 다만 pepADMET 모델의 D-AA 학습 도메인 포함 여부는 여전히 별도 근거가 필요하다. 이번 검증은 "D-AA stereochemical SMILES 입력이 로컬 파이프라인에서 에러 없이 처리된다"는 실행 가능성 검증이다.
- 옵션 A(RDKit 다운그레이드)는 현재 sample descriptor 및 V-03 추론이 성공했으므로 즉시 필요하지 않다.
