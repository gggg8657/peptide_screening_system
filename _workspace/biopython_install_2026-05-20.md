# biopython 설치 + step06/07 stub 해제

**일시**: 2026-05-20  
**작업자**: Cursor (실제 명령 실행 기반 검증 보고서)

---

## 1. 환경 점검 결과

### conda env 목록 (실제 출력)

```text
$ conda env list

# conda environments:
#
# * -> active
# + -> frozen
base                 *   /home/dongjukim/miniforge3
bio-tools                /home/dongjukim/miniforge3/envs/bio-tools
boltz                    /home/dongjukim/miniforge3/envs/boltz
diffpepbuilder           /home/dongjukim/miniforge3/envs/diffpepbuilder
esmfold                  /home/dongjukim/miniforge3/envs/esmfold
genmol                   /home/dongjukim/miniforge3/envs/genmol
openfold3                /home/dongjukim/miniforge3/envs/openfold3
pepadmet                 /home/dongjukim/miniforge3/envs/pepadmet
peptools                 /home/dongjukim/miniforge3/envs/peptools
proteinmpnn              /home/dongjukim/miniforge3/envs/proteinmpnn
pybamm-inv               /home/dongjukim/miniforge3/envs/pybamm-inv
rfdiffusion              /home/dongjukim/miniforge3/envs/rfdiffusion
vllm-server              /home/dongjukim/miniforge3/envs/vllm-server
```

(세션 시점 활성 환경: `base`)

### pipeline_local 사용 env

| 출처 | 권장/사용 conda env |
|------|---------------------|
| `pipeline_local/start_server.sh` (`_find_python`) | **`bio-tools`** (`$HOME/miniforge3/envs/bio-tools/bin/python` 우선) |
| `pipeline_local/README.md` (Prerequisites) | **`conda activate bio-tools`** (PyRosetta + 구조 생물학 도구) |
| 레포 스펙 | `environment-bio-tools.yml`에 **`biopython`** conda 의존성 명시 |

### biopython 현재 상태

| 환경 | import `MMCIFParser` | 패키지 버전 |
|------|---------------------|-------------|
| **bio-tools** | 성공 `<class 'Bio.PDB.MMCIFParser.MMCIFParser'>` | **1.79** (`pip show biopython`) |
| **peptools** | 성공 (별도 용도: `requirements_peptools.txt`) | **1.87** |
| **base** (활성) | 실패 `ModuleNotFoundError: No module named 'Bio'` | 미설치 |

### 기존 환경 백업 권고

- 다른 세션과 공유하는 **base를 직접 변경하기 전**: `conda list --explicit > ~/backup-env-base-$(date +%Y%m%d).txt` 또는 `conda env export -n bio-tools > ~/backup-bio-tools.yml` 등으로 **스냅샷 저장** 후 진행할 것을 권장합니다.
- 본 세션에서는 **설치 패키지를 변경하지 않았습니다** (`bio-tools`에 이미 biopython 존재).

---

## 2. 설치 명령어 + 실제 출력

### 결론: `bio-tools`에는 추가 설치 불필요

`bio-tools`는 이미 biopython이 들어 있습니다. 따라서 **`conda activate bio-tools` 후 테스트·서버 실행**이면 mmCIF→PDB 경로가 정상적으로 Bio를 사용할 수 있습니다.

### conda dry-run (참고) — 디스크 부족으로 실패

설치 재현 가능성 확인을 위해 `conda ... --dry-run`을 시도했으나 **솔버 단계에서 디스크 공간 부족**으로 종료되었습니다.

```text
$ conda install -n bio-tools -c conda-forge biopython --dry-run
...
NoSpaceLeftError: No space left on devices.
```

> **후속 조치 제안**: miniforge 캐시 정리 (`conda clean -a`) 또는 디스크 여유 확보 후, 새 패키지를 conda로 재조정해야 할 때 다시 검토.

### base에 pip로 설치하는 경우 — dry-run만 수행 (미적용)

정책상 base는 손대지 않았으며, 호환 가능 여부 확인만 했습니다.

```text
$ /home/dongjukim/miniforge3/bin/python -m pip install biopython --dry-run
Collecting biopython
  Downloading biopython-1.87-cp313-cp313-manylinux2014_x86_64...
Requirement already satisfied: numpy ...
Would install biopython-1.87
```

**실제 적용은 하지 않음** — 사용자 규칙(기본값 base 회피) 준수.

---

## 3. 검증 결과

### import 테스트 (`bio-tools`)

```text
$ conda run -n bio-tools python -c "from Bio.PDB import MMCIFParser; print(MMCIFParser)"
<class 'Bio.PDB.MMCIFParser.MMCIFParser'>
```

### pytest `test_compute_docking_rmsd.py`

**실행기**: 리포지토리 루트, `pytest pipeline_local/tests/test_compute_docking_rmsd.py -v`.

| 구분 | 인터프리터 | 결과 |
|------|-----------|------|
| **Before** | `base` `/home/dongjukim/miniforge3/bin/python` (Python **3.13.12**) | **12 ERROR** (전부 동일 근본 원인: `No module named 'Bio'`) |
| **After** (환경 일치 시) | `conda run -n bio-tools` (Python **3.11.15**) | **12 PASSED**, **0 ERROR** |

`base`에서의 단일 테스트 메시지 예:

```text
[ERROR] biopython required: pip install biopython (No module named 'Bio')
```

### pytest 변화 요약

- **`test_compute_docking_rmsd.py` 관점**: ERROR **12 → 0** (인터프리터를 `bio-tools`로 맞춘 경우).

### `tier1_rosetta` 관련 파일 (`test_tier1_rosetta_fixes.py`) 동일 환경 이슈

| 인터프리터 | 결과 |
|-----------|------|
| **base** | **2 FAILED**, 7 PASSED (mmCIF 실입력 테스트에서 변환 실패 → chain B 미생성) |
| **bio-tools** | **9 PASSED** |

실패 로그 예 (`base`):

```text
WARNING ... [Step06] mmCIF→PDB 변환 실패 (No module named 'Bio'), 원본 반환
AssertionError: ... chains={'A': 2904}
```

### `grep`: mmCIF / MMCIFParser / biopython (지정 명령)

```text
$ grep -rn 'mmCIF\|MMCIFParser\|biopython' pipeline_local/steps/step06_rosetta.py pipeline_local/steps/step07_analysis.py

pipeline_local/steps/step06_rosetta.py:520:    """mmCIF 텍스트를 PDB 텍스트로 변환한다.
pipeline_local/steps/step06_rosetta.py:522:    Tier 1 fix (F1 / Stage 9 postmortem CRIT-1): Boltz가 mmCIF 형식으로
pipeline_local/steps/step06_rosetta.py:526:    Bio.PDB MMCIFParser + PDBIO를 사용. 실패 시 원본 텍스트 반환 (fail-soft).
pipeline_local/steps/step06_rosetta.py:530:        from Bio.PDB import MMCIFParser, PDBIO  # type: ignore[import-not-found]
pipeline_local/steps/step06_rosetta.py:531:        parser = MMCIFParser(QUIET=True)
pipeline_local/steps/step06_rosetta.py:539:            logger.warning("[Step06] mmCIF→PDB 변환 결과 빈 텍스트, 원본 반환")
pipeline_local/steps/step06_rosetta.py:543:            logger.warning("[Step06] mmCIF→PDB 변환 실패 (%s), 원본 반환", exc)
pipeline_local/steps/step06_rosetta.py:548:    """텍스트가 mmCIF 형식인지 판별한다 (PDB 아닌 경우 cif 가정)."""
pipeline_local/steps/step06_rosetta.py:565:    Tier 1 fix (F1): peptide_pdb 또는 receptor_pdb가 mmCIF 형식이면
pipeline_local/steps/step06_rosetta.py:566:    PDB로 변환 후 처리. Boltz는 mmCIF 출력이라 변환 없이 ATOM 추출 시
pipeline_local/steps/step06_rosetta.py:569:    # F1 fix: mmCIF input detect + convert
pipeline_local/steps/step06_rosetta.py:571:        logger.info("[Step06] peptide input이 mmCIF 형식 — PDB 변환 (F1 fix)")
pipeline_local/steps/step06_rosetta.py:574:        logger.info("[Step06] receptor input이 mmCIF 형식 — PDB 변환 (F1 fix)")
```

(`step07_analysis.py`에서는 위 패턴 문자열 매칭으로는 **MMCIF 문자열 미출력**; Step07은 `Bio.PDB.PDBParser` 계면 분석용 import.)

### step06/07 “stub” 해제 여부

| 파일 | 상태 |
|------|------|
| **step06_rosetta.py** | mmCIF→PDB 코드는 **`MMCIFParser` 기반 실구현**(이미 “해제”됨). Bio 미설치 시 **fail-soft**로 원본 문자열 반환 → 상위 테스트에서 chain B 단절처럼 보일 수 있음. **별도의 mmCIF “stub 블록”은 없음.** (별도로 PyRosetta 불가 시 **에너지 계산 `_stub_rosetta_result`** 는 그대로 존재.) |
| **step07_analysis.py** | Bio import 실패 시 **InterfaceReport 빈 값 stub** 분기 존재. Bio 사용 시에도 일부 필드 주석상 **근사값(stub 성격)** (`buried_sasa` 등). **MMCIF 전용 스텝은 아님.** |

---

## 4. 잔여 작업 (있을 경우)

1. **CI / 로컬 기본 인터프리터**: 전체 `pytest`를 `base`(Python 3.13, Bio 없음)로 돌리면 동일 패턴 ERROR/FAIL이 재발합니다. **`bio-tools`로 실행**하는 스크립트·문서·CI 매트릭스 정렬이 필요할 수 있습니다.
2. **`NoSpaceLeftError`**: conda 기반 패키지 조정 전 **디스크 여유 확보** 필요.
3. **stub “완전 제거”**: Step07의 **SASA/H-bond 근사** 등은 Bio 설치만으로 바뀌지 않으며, 로직 교체 또는 외부 도구 연동 시 별도 위임이 맞음.

검증에 사용한 명령:

```bash
cd /home/dongjukim/Documents/workspace/repos/SST14-M_scr
conda run -n bio-tools pytest pipeline_local/tests/test_compute_docking_rmsd.py -v
conda run -n bio-tools pytest pipeline_local/tests/test_tier1_rosetta_fixes.py -v
```

---

## 5. 권고사항

- **커밋**: 본 세션에서 레포 코드/의존성 파일은 수정하지 않았습니다. 변경이 필요하면 “pytest를 `bio-tools`에서 실행”을 문서·스크립트로 고정하는 PR을 별도로 권합니다.
- **다음 단계**:
  - 일상 검증: `conda activate bio-tools` 후 pytest / 파이프라인 실행.
  - 디스크: `conda clean` 및 패키지 캐시 정리 검토 (위 dry-run 실패 대응).
  - 선택: 공유·자동화용 **전용 테스트 env**(bio-tools 미러 또는 경량 env) 명시 버전 pinning.
