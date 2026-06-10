# binding_pocket_extract FAIL fix (2026-05-20)

## 재현

명령:

```bash
conda run -n bio-tools pytest pipeline_local/tests/test_binding_pocket_extract.py::TestExtractPocketCenter::test_pdb_and_cif_give_same_center -v
```

실패 출력:

```text
pipeline_local/tests/test_binding_pocket_extract.py::TestExtractPocketCenter::test_pdb_and_cif_give_same_center FAILED [100%]

E           AssertionError: center_x 불일치: PDB=-4.664, CIF=-0.588, 차이=4.076 Å > 허용 1.0 Å
E           assert 4.0756000000000006 <= 1.0

FAILED pipeline_local/tests/test_binding_pocket_extract.py::TestExtractPocketCenter::test_pdb_and_cif_give_same_center
```

## 실패 원인

원인은 좌표 정밀도(PDB 8.3f vs CIF)가 아니라, PDB/CIF 파서가 서로 다른 원자 집합과 서로 다른 잔기 번호 체계를 사용한 것이다.

1. CIF 파서가 `_atom_site.label_seq_id`/`label_asym_id`를 사용했다.
   - A-01 입력 `[208, 209, 272, 273, 276]`은 PDB 저자 잔기 번호 기준이다.
   - CIF의 `label_seq_id` 기준으로는 다른 잔기가 선택됐다.
   - 실제 선택: LEU label_seq_id 208(auth_seq_id 183), ARG 209(auth 184), THR 272(auth 1009), PHE 273(auth 1010), GLY 276(auth 1013).
   - 올바른 선택은 `auth_seq_id` 기준 PHE208, ILE209, PHE272, TYR273, ASN276이다.

2. `extract_pocket_center()`에서 PDB는 CA-only, CIF는 all-atom으로 계산했다.
   - 기존 PDB 중심: `[-4.6638, -28.5350, 50.8738]` (CA 5개)
   - 기존 CIF 중심: `[-0.5882, -38.3861, 26.5150]` (`label_seq_id` 기반 wrong residues all-atom 41개)
   - 따라서 `center_x`가 4.076 Å 차이났다.

3. PDB 파일에는 해당 잔기에 수소 44개가 포함되어 있고 CIF에는 수소가 없었다.
   - 같은 원자 집합을 보장하려면 PDB/CIF 모두 heavy atom만 사용해야 한다.

## 수정 내용

- `pipeline_local/scripts/extract_binding_pocket.py`
  - CIF 파서가 `auth_seq_id`/`auth_asym_id`를 사용하도록 변경.
  - CIF/PDB 모두 heavy atom만 선택하도록 통일.
  - altloc은 primary conformer(`blank/.`/`?`/`A`)만 사용.
  - PDB용 `_parse_all_atom_coords_pdb()` 추가.
  - `extract_pocket_center()`의 PDB branch를 CA-only에서 heavy atom centroid로 변경.

- `pipeline_local/tests/test_binding_pocket_extract.py`
  - PDB/CIF 좌표 tolerance를 `1.0 Å`에서 `0.5 Å`로 강화.

- `data/somatostatin_receptor/binding_pocket_SSTR2.json`
  - 저장된 A-01 docking center를 새 표준 계산값으로 갱신.
  - `binding_pocket_center_residues` 필드를 추가해 중심 계산 잔기를 명시.

수정 후 직접 계산값:

```text
PDB {'center_x': -4.9562, 'center_y': -27.489, 'center_z': 50.2767, 'radius_angstrom': 8.5123, ...}
CIF {'center_x': -4.9562, 'center_y': -27.489, 'center_z': 50.2767, 'radius_angstrom': 8.5123, ...}
diffs {'center_x': 0.0, 'center_y': 0.0, 'center_z': 0.0}
```

## Diff 요약

```diff
diff --git a/pipeline_local/scripts/extract_binding_pocket.py b/pipeline_local/scripts/extract_binding_pocket.py
-    """mmCIF _atom_site 루프에서 지정 잔기의 모든 원자 좌표를 수집한다
+    """mmCIF _atom_site 루프에서 지정 잔기의 heavy atom 좌표를 수집한다
+    PDB 파일의 저자 잔기 번호와 맞추기 위해 auth_seq_id/auth_asym_id를 사용한다.

-                needed = {"group_PDB", "label_comp_id", "label_asym_id",
-                          "label_seq_id", "Cartn_x", "Cartn_y", "Cartn_z"}
+                needed = {"group_PDB", "type_symbol", "label_alt_id", "label_comp_id",
+                          "auth_asym_id", "auth_seq_id", "Cartn_x", "Cartn_y", "Cartn_z"}

-                chain_id = parts[col_map["label_asym_id"]]
+                element = parts[col_map["type_symbol"]].upper()
+                if element in {"H", "D"}:
+                    continue
+                altloc = parts[col_map["label_alt_id"]]
+                if altloc not in (".", "?", "A"):
+                    continue
+                chain_id = parts[col_map["auth_asym_id"]]

-                    resseq = int(parts[col_map["label_seq_id"]])
+                    resseq = int(parts[col_map["auth_seq_id"]])

+def _parse_all_atom_coords_pdb(...):
+    ...
+    if element in {"H", "D"}:
+        continue

-        # PDB 파일: CA 원자 기준으로 포켓 중심 계산
+        # PDB 파일: CIF와 동일하게 heavy atom 기준으로 포켓 중심 계산
-        ca_records = _parse_ca_coords(str(pdb_path), residue_ids, chain)
-        coords = np.array([[r["x"], r["y"], r["z"]] for r in ca_records], dtype=float)
+        coords = _parse_all_atom_coords_pdb(str(pdb_path), residue_ids, chain)

diff --git a/pipeline_local/tests/test_binding_pocket_extract.py b/pipeline_local/tests/test_binding_pocket_extract.py
-COORD_TOLERANCE = 1.0
+COORD_TOLERANCE = 0.5

diff --git a/data/somatostatin_receptor/binding_pocket_SSTR2.json b/data/somatostatin_receptor/binding_pocket_SSTR2.json
+  "binding_pocket_center_residues": [208, 209, 272, 273, 276],
-  "center_x": -5.595,
-  "center_y": -28.626,
-  "center_z": 52.21,
+  "center_x": -4.9562,
+  "center_y": -27.489,
+  "center_z": 50.2767,
```

## 검증

타깃 테스트:

```bash
conda run -n bio-tools pytest pipeline_local/tests/test_binding_pocket_extract.py::TestExtractPocketCenter::test_pdb_and_cif_give_same_center -v
```

결과:

```text
1 passed in 0.21s
```

전체 테스트:

```bash
conda run -n bio-tools pytest pipeline_local/tests/test_binding_pocket_extract.py -v
```

결과:

```text
27 passed in 0.26s
```

## Commit message 제안

```text
fix(binding-pocket): align PDB/CIF pocket atom selection

Use author residue numbering (auth_seq_id/auth_asym_id) for mmCIF and compute
the A-01 pocket center from the same heavy-atom set for PDB and CIF. The
4.076 Å center_x regression was caused by CIF using label_seq_id, which selected
different residues, while PDB used CA-only coordinates and CIF used all atoms.
```

