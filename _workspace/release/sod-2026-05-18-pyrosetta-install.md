# PyRosetta 설치 계획 — SOD 2026-05-19

작성: engineer-infra  
날짜: 2026-05-19  
대상 env: `bio-tools` (`/home/dongjukim/miniforge3/envs/bio-tools/`)

---

## 1. 현재 환경 상태

| 항목 | 상태 |
|------|------|
| conda env `bio-tools` | 존재 (`/home/dongjukim/miniforge3/envs/bio-tools/`) |
| Python (bio-tools) | **3.11.15** (문서의 3.12와 다름 — 실제 3.11) |
| PyRosetta | **미설치** (`import pyrosetta` AttributeError) |
| `flexpep_dock.py` | 존재 (`AgenticAI4SCIENCE_pyrosetta_track/.../AG_src/scripts/flexpep_dock.py`) |
| SSTR2 PDB | **.cif만 존재** (`.pdb` 없음) — `data/somatostatin_receptor/SSTR2_7XNA.cif` |
| SSTR1/3/4/5 | `.pdb` + `.cif` 모두 존재 |
| 디스크 여유 | 238 GB (97% 사용) — PyRosetta ~5-8GB 설치 가능 |
| BE uvicorn | PID 1796853, port 8787, **실행 중** |
| graylab conda 채널 | HTTP 200, **인증 없이 접근 가능** (패키지 다운로드 포함) |
| graylab wheel 페이지 | HTTP 401 (직접 wheel 다운로드는 인증 필요) |

### CLI 호환성 불일치 발견

`flexpepdock_worker.py`는 `flexpep_dock.py`를 다음 인자로 호출:
```
--receptor <pdb> --sequence <seq> --output-prefix <dir> --cycles N --nstruct N ...
```

그런데 `flexpep_dock.py`의 실제 argparse는:
```
--input <pdb> --output <pdb> --protocol --reference-complex --target-sequence --peptide-chain
```

**`--receptor`, `--sequence`, `--output-prefix`, `--cycles`, `--nstruct`, `--flex-pep-freedom`, `--ddg-cycle` 인자가 존재하지 않음** — PyRosetta 설치 후에도 즉시 작동하지 않으며 worker 또는 script 수정이 필요함.

---

## 2. stub fallback 트리거 조건 분석

현재 stub이 발생하는 경로 (2가지):

**경로 A** — `preflight_check()` (L366-380): conda run으로 `import pyrosetta` 시도 실패 시 경고만 남기고 계속 진행 (hard block 아님)

**경로 B** — `_run_flexpepdock_for_receptor()` (L443-445): `flexpep_dock.py` 스크립트 탐색 시 `pipeline_local/scripts/flexpep_dock.py`를 1순위로 찾음 → 해당 경로에 파일 없음 → stub 반환

현재 stub의 **실제 원인은 PyRosetta 미설치가 아님** — `flexpep_dock.py`가 worker가 찾는 경로(`pipeline_local/scripts/`)에 없어서 발생. PyRosetta 설치 후에도 stub이 유지될 것.

추가: SSTR2는 `.pdb`가 없고 `.cif`만 있어 `get_receptor_pdb_path()` L55-56 fallback(cif)으로는 처리되지만 `flexpep_dock.py --input`이 `.cif`를 지원하는지 별도 확인 필요.

---

## 3. 권장 설치 방법 — Option A (graylab conda, 인증 불필요)

**graylab conda 채널은 인증 없이 HTTP 200 접근 + 패키지 다운로드 가능** (테스트 확인).  
bio-tools Python이 3.11이므로 `py311` 빌드를 사용.

### Step 1: PyRosetta 설치 (사용자 실행 또는 동의 필요)

```bash
# 예상 다운로드: ~1.5GB tar.bz2, 설치 후 ~5-8GB
conda install -n bio-tools -c https://conda.graylab.jhu.edu pyrosetta -y
```

설치 시간 예상: 15-30분 (다운로드 속도에 따라)

### Step 2: smoke test

```bash
conda run -n bio-tools python -c "
import pyrosetta
pyrosetta.init('-mute all')
print('PyRosetta OK:', pyrosetta.__version__ if hasattr(pyrosetta,'__version__') else 'installed')
"
```

### Step 3: CLI 불일치 수정 (엔지니어 작업 필요)

PyRosetta 설치 후에도 stub이 해제되려면 두 가지 중 하나 수정:

**방법 1 (권장)** — `flexpepdock_worker.py`가 호출하는 CLI 인자를 `flexpep_dock.py`의 실제 인터페이스(`--input`, `--output`, `--target-sequence` 등)에 맞게 수정

**방법 2** — `flexpep_dock.py`에 worker가 기대하는 CLI 인자(`--receptor`, `--sequence`, `--output-prefix`, `--cycles`, `--nstruct` 등) 추가

### Step 4: SSTR2 PDB 변환 (선택, .cif 지원 확인 전)

```bash
# .cif → .pdb 변환 (PyRosetta 설치 후)
conda run -n bio-tools python -c "
import pyrosetta
pyrosetta.init('-mute all')
from pyrosetta.io import pose_from_file
import pyrosetta.rosetta.core.io.pdb as pdb_io
pose = pose_from_file('data/somatostatin_receptor/SSTR2_7XNA.cif')
pose.dump_pdb('data/somatostatin_receptor/SSTR2_7XNA.pdb')
print('SSTR2 PDB 변환 완료')
"
```

### Step 5: BE 재시작 (설치 완료 후)

```bash
# PID 1796827(부모), 1796853(uvicorn) 종료
kill 1796827 1796853

# bio-tools env에서 재시작
conda run -n bio-tools uvicorn backend.main:app --host 127.0.0.1 --port 8787 &
```

---

## 4. 사용자 인터랙션 필요 항목

| 단계 | 인터랙션 유형 | 명령 |
|------|-------------|------|
| PyRosetta 라이선스 동의 | conda install 중 EULA 표시될 수 있음 — `y` 입력 필요 | Step 1 |
| conda install 실행 승인 | 디스크 5-8GB 사용 승인 | Step 1 |
| BE 재시작 승인 | 서비스 중단 10초 이하 | Step 5 |

**주의**: graylab EULA 확인 없이 conda install 진행 시 라이선스 동의 프롬프트가 터미널에 표시됨. 학술/비상업용 사용은 무료이나 서명 등록 없이 설치 가능한지 실행 시 확인 필요.

---

## 5. 작업 우선순위 요약

1. **즉시 필요**: PyRosetta conda install (사용자 실행)
2. **PyRosetta 설치 후**: CLI 불일치 수정 (engineer-backend 위임 또는 infra 직접 수정)
3. **선택 사항**: SSTR2 .cif → .pdb 변환 (PyRosetta 설치 후 가능)
4. **완료 후**: BE 재시작 + smoke test + job 제출 테스트
