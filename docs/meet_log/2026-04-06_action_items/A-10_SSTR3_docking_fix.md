# A-10: SSTR3 도킹 에러 해결

## 메타
- 회의: KAERI-AIRL-MOM-2026-003 (2026-04-06)
- 담당: AI팀
- 기한: 5월 회의 전
- 상태: **✅ 완료** (PR #60 머지; SSTR4 시그니처 중복 BUG 후속 해결 확인 — 2026-05-20)
- 비고: A-01(SSTR1/3/4/5 위치 지정 도킹) 선행 조건

---

## 배경

현행 선택성 분석 파이프라인(`pipeline_local/core/selectivity_runner.py`)에서
SSTR3 도킹이 에러를 반환하거나 비정상 결과를 출력하는 문제가 보고되었다.
로컬 구조 파일은 `data/somatostatin_receptor/SSTR3_8XIR.pdb/cif`로 배치되어 있으나,
구조 전처리(missing residues, clashes, 비정상 B-factor 등)가 미완료 상태로
추정된다.

SSTR3가 도킹에서 제외되면 4-subtype 선택성 프로파일이 불완전해지므로,
A-01에 앞서 반드시 해결해야 한다.

---

## 수행 방법 (단계별)

### Step 1 — 현재 에러 재현 및 원인 파악
```bash
conda run -n boltz python pipeline_local/scripts/offtarget_dock.py \
    --receptor data/somatostatin_receptor/SSTR3_8XIR.cif \
    --sequence AGCKNFFWKTFTSC \
    --nstruct 1 \
    --output-dir runs_local/sstr3_debug
```
에러 메시지 분류:
- `KeyError: chain` / `missing atoms` → 누락 잔기
- `RuntimeError: clash` / `bad geometry` → 충돌 원자
- `UserWarning: B-factor > 100` → 비정상 B-factor
- CIF 파싱 실패 → 포맷 불일치

### Step 2 — PDB 구조 검사
```bash
# 누락 잔기 확인
grep "REMARK 465" data/somatostatin_receptor/SSTR3_8XIR.pdb | head -20

# 충돌 원자 확인 (MolProbity 또는 PyMOL)
pymol -c -d "
load SSTR3_8XIR.pdb;
find_clashes sele, cutoff=0.4;
"

# 체인/잔기 번호 확인
grep "^ATOM\|^HETATM" data/somatostatin_receptor/SSTR3_8XIR.pdb | \
    awk '{print $5, $6}' | sort -u | head -30
```

### Step 3 — 구조 전처리 (문제 유형별)

#### 3a. 누락 잔기 재구축
```bash
# SWISS-MODEL 웹 서버 (웹 기반, 내부망 제한 확인 필요)
# 또는 Modeller CLI
cat > model_sstr3.py << 'EOF'
from modeller import Environ, Model, Alignment
env = Environ()
env.io.atom_files_directory = ['data/somatostatin_receptor']
m = Model(env, file='SSTR3_8XIR', model_segment=('FIRST:A','LAST:A'))
# 누락 루프 재구축 후 저장
m.write(file='SSTR3_8XIR_modelled.pdb')
EOF
python model_sstr3.py
```

#### 3b. 충돌 원자 해소
```bash
# PyRosetta 에너지 최소화
python -c "
import pyrosetta
pyrosetta.init()
pose = pyrosetta.pose_from_pdb('data/somatostatin_receptor/SSTR3_8XIR.pdb')
sf = pyrosetta.get_fa_scorefxn()
from pyrosetta.rosetta.protocols.minimization_packing import MinMover
mm = pyrosetta.MoveMap(); mm.set_bb(True); mm.set_chi(True)
min_mover = MinMover(mm, sf, 'lbfgs_armijo_nonmonotone', 0.01, True)
min_mover.apply(pose)
pose.dump_pdb('data/somatostatin_receptor/SSTR3_8XIR_minimized.pdb')
"
```

#### 3c. 비정상 B-factor 처리
```python
# B-factor > 100 원자를 100으로 클램핑 또는 제거
from Bio.PDB import PDBParser, PDBIO

parser = PDBParser(QUIET=True)
structure = parser.get_structure("SSTR3", "data/somatostatin_receptor/SSTR3_8XIR.pdb")
for atom in structure.get_atoms():
    if atom.bfactor > 100:
        atom.bfactor = 100.0  # 클램핑 또는 주의 표시

io = PDBIO()
io.set_structure(structure)
io.save("data/somatostatin_receptor/SSTR3_8XIR_fixed.pdb")
```

### Step 4 — 전처리 완료 구조로 도킹 재실행
```bash
conda run -n boltz python pipeline_local/scripts/offtarget_dock.py \
    --receptor data/somatostatin_receptor/SSTR3_8XIR_fixed.cif \
    --sequence AGCKNFFWKTFTSC \
    --nstruct 3 \
    --output-dir runs_local/sstr3_redocking
```
- 결과 `ddg` 값이 SSTR2 기준 ΔG(A-05 산출값)와 비교 가능한 범위에 있는지 확인.

### Step 5 — 수정된 구조 파일 정식 등록
- 최종 고정 구조: `data/somatostatin_receptor/SSTR3_8XIR_preprocessed.pdb`
- 변경 이력 `data/somatostatin_receptor/README.md`에 기록.
- `selectivity_runner.py` 내 SSTR3 경로 참조 갱신.

---

## 판단 기준 / KPI

| 지표 | 기준 |
|------|------|
| 도킹 에러 없이 완료 | JSON 결과 반환 (에러 필드 없음) |
| `ddg` 값 범위 | -200 < ddg < 0 (비정상 수치 없음) |
| `iptm` 값 범위 | 0.0 < iptm ≤ 1.0 |
| SSTR2 대비 선택성 배수 산출 가능 | `compute_full_selectivity()` 정상 실행 |

---

## 활용 도구 / 기술 스택

| 도구 | 용도 |
|------|------|
| PyMOL | clash 확인, 구조 시각화 |
| MolProbity (웹) | 구조 품질 평가 |
| Modeller / SWISS-MODEL | 누락 루프 재구축 |
| PyRosetta FastRelax / MinMover | 에너지 최소화 |
| BioPython | B-factor 처리 |
| Boltz-2 (`offtarget_dock.py`) | 재도킹 검증 |

---

## 서호성 박사 의견

- 회의록에서 A-10을 별도로 언급한 만큼 SSTR3 구조 품질 문제가 실제로 존재함.
- **필수 점검 항목**:
  1. 구조 전처리 누락 (missing residues)
  2. 충돌 원자 (clashes)
  3. 비정상 B-factor

---

## 본 프로젝트 매핑

- **관련 파일 (READ-ONLY 원칙 — `data/` 수정 금지)**:
  - `data/somatostatin_receptor/SSTR3_8XIR.pdb/.cif` — 원본 구조 (수정 금지)
  - 전처리 완료본은 `data/somatostatin_receptor/SSTR3_8XIR_preprocessed.pdb`로
    **별도 파일**로 생성하여 원본 보존
- **관련 모듈**:
  - `pipeline_local/core/selectivity_runner.py` — SSTR3 수용체 경로 참조
  - `pipeline_local/scripts/offtarget_dock.py` — 전처리 완료 후 재실행
  - `pipeline_local/tests/test_offtarget_dock_boltz.py` — 테스트 갱신 필요

> **주의**: `data/` 디렉토리는 READ-ONLY 경계. 원본 파일 수정 금지.
> 전처리 완료 구조는 `data/somatostatin_receptor/SSTR3_8XIR_preprocessed.pdb`
> 또는 `runs_local/sstr3_debug/` 아래에 저장.

### 후속 BUG 클로저 — SSTR4 시그니처 중복

- 문제: 공유 모티프 `VILRYAKMKTA`가 SSTR1/SSTR4 양쪽 시그니처로 쓰이면 SSTR4 구조가 SSTR1로 오매칭될 수 있음.
- 현재 상태: `pipeline_local/scripts/offtarget_dock.py::_SSTR_SIGNATURES`는 해당 공유 모티프를 제거하고 SSTR1/SSTR4 고유 시그니처만 유지한다.
- 회귀 테스트: `pipeline_local/tests/test_offtarget_dock_cif_chain.py`가 서명 중복 금지와 SSTR4→SSTR1 오매칭 방지를 단언한다.
- 검증: `python3 -m pytest pipeline_local/tests/test_offtarget_dock_cif_chain.py -q` → 24 passed; `python3 -m pytest pipeline_local/tests/test_offtarget_dock_boltz.py -q` → 24 passed, 4 skipped.

---

## 의존성 / 연관 액션 아이템

| 의존 관계 | 액션 |
|----------|------|
| 후행 필수 | **A-01** (SSTR1/3/4/5 위치 지정 도킹 — SSTR3 에러 해소 후 진행) |
| 에러 재현 보고 대상 | orchestrator 또는 engineer-backend에게 에러 원문 공유 |
