# 실험 01: CIF -> PDB 변환

## 목적

AlphaFold3에서 출력된 mmCIF 파일을 PDB 형식으로 변환하여 PyMOL, FoldMason 등 후속 도구에서 사용할 수 있도록 한다.

## 환경

- **conda env**: `bio-tools`
- **핵심 패키지**: Biopython 1.86 (`Bio.PDB.MMCIFParser`, `Bio.PDB.PDBIO`)
- **OS**: Ubuntu 22.04 (WSL2)

## 입력 데이터

`data/fold_test1/` 내 AlphaFold3 결과:

| 파일 | 설명 |
|------|------|
| `fold_test1_model_{0-4}.cif` | 5개 모델 (mmCIF) |
| `templates/fold_test1_template_hit_{0-3}_chains_{a,b}.cif` | 8개 템플릿 구조 |

총 **13개** CIF 파일.

## 실행 방법

```bash
conda activate bio-tools
python scripts/cif_to_pdb.py data/fold_test1
```

스크립트는 `data/fold_test1/` 하위의 모든 `.cif` 파일을 재귀 탐색하여 같은 위치에 `.pdb`를 생성한다.

## 결과

13개 CIF -> 13개 PDB 변환 완료:

```
fold_test1_model_0.cif -> fold_test1_model_0.pdb
fold_test1_model_1.cif -> fold_test1_model_1.pdb
fold_test1_model_2.cif -> fold_test1_model_2.pdb
fold_test1_model_3.cif -> fold_test1_model_3.pdb
fold_test1_model_4.cif -> fold_test1_model_4.pdb
templates/fold_test1_template_hit_0_chains_a.cif -> .pdb
templates/fold_test1_template_hit_0_chains_b.cif -> .pdb
templates/fold_test1_template_hit_1_chains_a.cif -> .pdb
templates/fold_test1_template_hit_1_chains_b.cif -> .pdb
templates/fold_test1_template_hit_2_chains_a.cif -> .pdb
templates/fold_test1_template_hit_2_chains_b.cif -> .pdb
templates/fold_test1_template_hit_3_chains_a.cif -> .pdb
templates/fold_test1_template_hit_3_chains_b.cif -> .pdb
Done: 13/13 converted.
```

## 특수 사항

- Biopython의 `PDBIO`는 mmCIF에만 있는 일부 메타데이터(예: `_atom_site.label_seq_id` 등)를 PDB 형식에 맞게 자동 변환한다.
- 매우 큰 구조의 경우 PDB 형식 제한(99999 원자, 9999 잔기)에 걸릴 수 있으나, fold_test1 크기에서는 문제없음.
- 변환 후 PDB 파일은 PyMOL, FoldMason 모두에서 정상 로드 확인됨.
