# 오픈소스 PDB 시각화 도구

fold_test1의 CIF를 Biopython으로 PDB로 변환한 뒤, 아래 뷰어로 시각화할 수 있다.

---

## 요약 표

| 도구 | 유형 | 라이선스 | PDB/mmCIF | 특징 |
|------|------|----------|-----------|------|
| **Mol*** | 웹/임베드 | Apache 2.0 | ✅ | 대형 구조·트레젝토리, PDBe/RCSB 공식 뷰어 |
| **PyMOL (Open-Source)** | 데스크톱 | BSD-like | ✅ | 업계 표준, 스크립팅·출판용 |
| **NGL Viewer** | 웹/라이브러리 | MIT | ✅ | WebGL, Jupyter(NGLView), 단일 ngl.js |
| **3Dmol.js** | 웹/임베드 | BSD | ✅ | URL/선언적 API, Jupyter 연동 |
| **Jmol / JSmol** | 데스크톱/웹 | LGPL | ✅ | Java 앱 + HTML5(JSmol), 교육·다국어 |

---

## 1. Mol* (Molstar)

- **사이트:** https://molstar.org/
- **저장소:** https://github.com/molstar/molstar
- **라이선스:** Apache 2.0
- **유형:** 웹 앱, 다른 사이트에 임베드 가능 (WebGL)

**특징:**
- PDBe, RCSB PDB, AlphaFold DB 등에서 공식 사용
- 대형 구조(수백만 원자), 트레젝토리, Cryo-EM 볼륨 지원
- BinaryCIF, mmCIF, PDB 지원
- MolViewSpec로 뷰 상태 공유·재현
- **로컬 PDB 보기:** https://molstar.org/viewer/ 에서 로컬 파일 드래그앤드롭 또는 URL로 로드

**로컬 파일로 보는 방법:**  
뷰어 페이지에서 “Load” → 로컬 `fold_test1_model_0.pdb` 등 선택.

---

## 2. PyMOL (Open-Source)

- **저장소:** https://github.com/schrodinger/pymol-open-source
- **라이선스:** BSD-like (Schrodinger)
- **유형:** 데스크톱 GUI (C/Python)

**특징:**
- 구조生物学・創薬에서 널리 쓰이는 표준 도구
- 고품질 렌더링, 스크립팅(PyMOL script), 출판용 이미지
- PDB, mmCIF 등 지원
- **설치:** conda `conda install -c conda-forge pymol-open-source` 또는 [INSTALL](https://github.com/schrodinger/pymol-open-source/blob/master/INSTALL) 참고

**사용 예:**
```bash
pymol "fold_test1 (1)/fold_test1_model_0.pdb"
```

---

## 3. NGL Viewer

- **사이트:** https://nglviewer.org/ngl/
- **저장소:** https://github.com/nglviewer/ngl
- **라이선스:** MIT
- **유형:** 웹 앱, JavaScript 라이브러리 (단일 `ngl.js`)

**특징:**
- PDB, mmCIF, MMTF, SDF, density 등 지원
- Jupyter 위젯: [NGLView](https://github.com/nglviewer/nglview) (`pip install nglview`)
- 데모: https://nglviewer.github.io/ngl/

**로컬 PDB:**  
로컬 서버로 디렉터리 서빙 후 웹 앱에서 파일 선택하거나, NGLView로 노트북에서 직접 로드.

---

## 4. 3Dmol.js

- **사이트:** https://3dmol.csb.pitt.edu/
- **저장소:** https://github.com/3dmol/3Dmol.js
- **라이선스:** BSD
- **유형:** JavaScript 라이브러리, 웹/임베드

**특징:**
- URL/선언적 API로 뷰어 임베드
- 웹페이지 2줄 수준으로 삽입, Jupyter 연동
- PDB/mmCIF 지원

**로컬 PDB:**  
로컬 HTTP 서버로 `fold_test1 (1)` 서빙 후, 3Dmol.js 뷰어에 해당 URL 넘겨서 로드.

---

## 5. Jmol / JSmol

- **사이트:** https://jmol.sourceforge.net/
- **라이선스:** LGPL
- **유형:** 데스크톱 Java 앱 (Jmol), 웹 HTML5 (JSmol)

**특징:**
- PDB, mmCIF, CIF, SDF 등 다양한 포맷
- JSmol은 Java 없이 브라우저에서 동작
- 교육·다국어 지원, 스크립팅

**로컬 PDB:**  
Jmol 앱에서 File → Open으로 `.pdb` 선택. 웹에서는 JSmol로 로컬 파일을 서빙해 로드.

---

## 이 레포에서 PyMOL로 보기 (bio-tools env)

- **설치 (이미 완료):** `conda activate bio-tools` 후 `conda install -c conda-forge pymol-open-source`
- **실행 예:**
  ```bash
  conda activate bio-tools
  pymol "fold_test1 (1)/fold_test1_model_0.pdb"
  ```
  또는 여러 모델 한 번에:
  ```bash
  pymol "fold_test1 (1)/fold_test1_model_0.pdb" "fold_test1 (1)/fold_test1_model_1.pdb"
  ```
- **스크립트:** `./scripts/run_pymol_pdb.sh` (인자 없으면 model_0.pdb 로드)
- **WSL:** Windows 11 WSLg 또는 X 서버 필요. GUI가 안 뜨면 `pymol -c "fold_test1 (1)/fold_test1_model_0.pdb" -d "png out.png; quit"` 로 이미지만 저장 가능.

---

## 이 레포에서 PDB 만든 뒤 보는 방법

1. **변환 (이미 실행됨):**
   ```bash
   conda activate bio-tools
   python scripts/cif_to_pdb.py "fold_test1 (1)"
   ```
   → `fold_test1 (1)/fold_test1_model_0.pdb` 등 13개 PDB 생성.

2. **웹으로 보기 (설치 없음):**
   - https://molstar.org/viewer/ 접속 → “Load”로 `fold_test1_model_0.pdb` 등 업로드.
   - 또는 로컬에서 `python -m http.server 8000` 후 브라우저로 `http://localhost:8000`에서 해당 폴더 열어 PDB 경로를 NGL/3Dmol 예제에 넣어 사용.

3. **데스크톱으로 보기:**
   - PyMOL: `conda install -c conda-forge pymol-open-source` 후 `pymol "fold_test1 (1)/fold_test1_model_0.pdb"`
   - Jmol: Jmol.jar로 같은 PDB 파일 열기.

---

## 참고 문헌

- Mol*: Sehnal et al., *Nucleic Acids Research* 2021, doi:10.1093/nar/gkab314
- NGL: Rose et al., *Bioinformatics* 2018, doi:10.1093/bioinformatics/bty419
- 3Dmol.js: Rego & Koes, *Bioinformatics* 2015
- Jmol: http://www.jmol.org/
