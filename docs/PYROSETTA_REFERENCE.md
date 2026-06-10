# PyRosetta 완전 가이드

> **Python Interface to Rosetta Molecular Modeling Suite**
> 버전: 2026.06+release
> 공식 사이트: https://www.pyrosetta.org
> 문서: https://graylab.jhu.edu/PyRosetta.documentation/
> 라이선스: 학술 라이선스 필요 ([RosettaCommons](https://www.rosettacommons.org/software/license-and-download))

---

## 목차

1. [개요](#개요)
2. [설치 및 초기화](#설치-및-초기화)
3. [Pose -- 핵심 데이터 구조](#pose----핵심-데이터-구조)
4. [Scoring Functions](#scoring-functions)
5. [Relax Protocols](#relax-protocols)
6. [Docking](#docking)
7. [Protein Design](#protein-design)
8. [ddG Calculations](#ddg-calculations)
9. [Loop Modeling](#loop-modeling)
10. [Constraint / Restraint System](#constraint--restraint-system)
11. [Fragment-Based Modeling](#fragment-based-modeling)
12. [Cyclic Peptide Tools](#cyclic-peptide-tools)
13. [Small Molecule Handling](#small-molecule-handling)
14. [Energy Decomposition](#energy-decomposition)
15. [RosettaScripts Integration](#rosettascripts-integration)
16. [Symmetry Handling](#symmetry-handling)
17. [펩타이드 리간드 설계 워크플로우](#펩타이드-리간드-설계-워크플로우)

---

## 개요

PyRosetta는 Rosetta 분자 모델링 스위트의 완전한 Python 인터페이스로, 단백질 구조 예측, 설계, 도킹, 에너지 계산 등을 Python에서 직접 수행할 수 있게 합니다.

### 핵심 기능 요약

| 기능 | 용도 | 핵심 클래스 |
|------|------|-----------|
| Scoring | 구조 에너지 평가 | `ScoreFunction`, `get_fa_scorefxn()` |
| Relax | 구조 최적화/이완 | `FastRelax`, `MinMover` |
| Docking | 단백질-리간드/펩타이드 도킹 | `FlexPepDock`, `DockingProtocol` |
| Design | 서열 설계/최적화 | `PackRotamersMover`, `FastDesign` |
| ddG | 돌연변이 에너지 효과 | `CartesianddG`, `MutateResidue` |
| Loop Modeling | 루프 구조 빌딩 | `LoopModeler`, `KIC` |
| Constraints | 거리/각도 제약 조건 | `AtomPairConstraint`, `ConstraintSetMover` |
| Cyclic Peptides | 고리 펩타이드 모델링 | `PeptideCyclizeMover` |
| Ligands | 소분자 파라미터화 | `molfile_to_params` |

---

## 설치 및 초기화

### Conda 설치 (권장)

```bash
conda install -c https://conda.rosettacommons.org -c conda-forge pyrosetta
```

### Pip 설치 (대안)

```bash
pip install pyrosetta \
  --find-links https://west.rosettacommons.org/pyrosetta/quarterly/release
```

### 초기화

```python
import pyrosetta

# 기본 초기화
pyrosetta.init()

# 옵션 지정 초기화
pyrosetta.init(extra_options="""
    -beta_nov16
    -in:file:extra_res_fa LIG.params
    -mute all
""")

# 확인
print(f"PyRosetta version: {pyrosetta.__version__}")
```

### 주요 초기화 옵션

| 옵션 | 설명 |
|------|------|
| `-beta_nov16` | 최신 beta 스코어 함수 사용 |
| `-in:file:extra_res_fa X.params` | 비표준 잔기 파라미터 파일 로드 |
| `-mute all` | 로그 출력 최소화 |
| `-ignore_unrecognized_res` | 인식 불가 잔기 무시 |
| `-corrections:beta_nov16` | beta 보정 활성화 |
| `-run:preserve_header` | PDB 헤더 보존 |

---

## Pose -- 핵심 데이터 구조

**Pose**는 PyRosetta의 중앙 객체로, 단백질의 서열, 3D 좌표, 에너지, FoldTree를 모두 포함합니다.

### Pose 생성

```python
from pyrosetta import pose_from_pdb, pose_from_sequence

# PDB 파일에서
pose = pose_from_pdb("sstr2_complex.pdb")

# 서열에서 (이상적 좌표)
pose = pose_from_sequence("AGCKNFFWKTFTSC")

# 빈 Pose 생성 후 조합
from pyrosetta.rosetta.core.pose import Pose
pose = Pose()
```

### Pose 조회

```python
# 기본 정보
print(pose.total_residue())         # 총 잔기 수
print(pose.sequence())              # 서열
print(pose.pdb_info().chain(1))     # 잔기 1의 체인 ID
print(pose.residue(1).name())       # 잔기 1의 이름

# 좌표
xyz = pose.residue(1).xyz("CA")     # CA 원자 좌표
print(f"CA: ({xyz.x:.2f}, {xyz.y:.2f}, {xyz.z:.2f})")

# 백본 각도
phi = pose.phi(10)
psi = pose.psi(10)
omega = pose.omega(10)
chi1 = pose.chi(1, 10)             # 잔기 10의 chi1
```

### Pose 수정

```python
# 백본 각도 설정
pose.set_phi(10, -60.0)
pose.set_psi(10, -45.0)
pose.set_omega(10, 180.0)
pose.set_chi(1, 10, -60.0)

# 잔기 변이 (돌연변이)
from pyrosetta.rosetta.protocols.simple_moves import MutateResidue
mutater = MutateResidue(target=10, new_res="ALA")
mutater.apply(pose)

# Pose 저장
pose.dump_pdb("output.pdb")
```

### FoldTree -- 체인 연결 구조

FoldTree는 잔기 간 연결 관계와 강체 운동(jump)을 정의합니다.

```python
from pyrosetta.rosetta.core.kinematics import FoldTree

ft = FoldTree()
# 수용체(1-369) + 점프 + 펩타이드(370-383)
ft.add_edge(1, 369, -1)        # 수용체 내부 연결 (peptide edge)
ft.add_edge(1, 370, 1)         # 수용체↔펩타이드 jump
ft.add_edge(370, 383, -1)      # 펩타이드 내부 연결
pose.fold_tree(ft)

# 현재 FoldTree 확인
print(pose.fold_tree())
```

### Pose 합치기

```python
from pyrosetta.rosetta.core.pose import append_pose_to_pose

receptor = pose_from_pdb("sstr2_receptor.pdb")
peptide = pose_from_pdb("peptide.pdb")

# 새 체인으로 추가
append_pose_to_pose(receptor, peptide, new_chain=True)
# 이제 receptor에 펩타이드가 추가됨
```

---

## Scoring Functions

Rosetta 스코어 함수는 분자의 에너지를 여러 항(term)의 가중합으로 평가합니다.

### 스코어 함수 종류

| 스코어 함수 | 특징 | 용도 |
|------------|------|------|
| `ref2015` | 기본 전원자(full-atom) | 표준 설계/도킹/이완 |
| `ref2015_cart` | 카테시안 공간 버전 | ddG 계산, 카테시안 최소화 |
| `beta_nov16` | 개선된 용매화/토션 | 최신 벤치마크, 정밀 도킹 |
| `score3` / `score5` | 센트로이드(centroid) | 빠른 초기 탐색 |
| `ligand` / `ligand_soft_rep` | 리간드 전용 | 소분자 도킹 |

### 사용법

```python
from pyrosetta import get_fa_scorefxn, create_score_function

# 기본 전원자 스코어 함수
sfxn = get_fa_scorefxn()

# 특정 스코어 함수 생성
sfxn_cart = create_score_function("ref2015_cart")
sfxn_beta = create_score_function("beta_nov16")

# 스코어 계산
total_score = sfxn(pose)
print(f"Total score: {total_score:.2f} REU")

# 가중치 조회/수정
from pyrosetta.rosetta.core.scoring import ScoreType
weight = sfxn.get_weight(ScoreType.fa_atr)
sfxn.set_weight(ScoreType.atom_pair_constraint, 1.0)  # 제약 조건 활성화
```

### 주요 에너지 항(Score Terms)

| 항 | 설명 | 양수/음수 |
|----|------|----------|
| `fa_atr` | van der Waals 인력 | 음수 (좋음) |
| `fa_rep` | van der Waals 반발 | 양수 (나쁨) |
| `fa_sol` | 용매화 에너지 (Lazaridis-Karplus) | 양수 |
| `fa_elec` | 정전기 상호작용 | 음수/양수 |
| `hbond_sr_bb` | 단거리 백본 수소결합 | 음수 |
| `hbond_lr_bb` | 장거리 백본 수소결합 | 음수 |
| `hbond_bb_sc` | 백본-측쇄 수소결합 | 음수 |
| `hbond_sc` | 측쇄-측쇄 수소결합 | 음수 |
| `rama_prepro` | 라마찬드란 선호도 | 양수/음수 |
| `fa_dun` | 로타머 확률 (Dunbrack) | 양수 |
| `p_aa_pp` | 아미노산 성향 | 양수/음수 |
| `ref` | 참조 에너지 (아미노산별) | 보정 |
| `atom_pair_constraint` | 원자쌍 제약 조건 | 제약 |
| `coordinate_constraint` | 좌표 제약 조건 | 제약 |

---

## Relax Protocols

구조를 Rosetta 에너지 지형에서 최적화(이완)합니다.

### FastRelax

가장 널리 쓰이는 이완 프로토콜. 반복적으로 팩킹(측쇄 최적화) + 최소화를 수행하며, fa_rep 가중치를 점진적으로 증가시킵니다.

```python
from pyrosetta.rosetta.protocols.relax import FastRelax
from pyrosetta.rosetta.core.kinematics import MoveMap

sfxn = get_fa_scorefxn()

# 기본 FastRelax (5 사이클)
relax = FastRelax(sfxn, 5)
relax.apply(pose)

# MoveMap으로 유연 영역 제한
mm = MoveMap()
mm.set_bb(False)    # 백본 고정
mm.set_chi(False)   # 측쇄 고정

# 펩타이드 + 바인딩 사이트만 이완
for i in range(pep_start, pep_end + 1):
    mm.set_bb(i, True)
    mm.set_chi(i, True)
for i in binding_site_residues:
    mm.set_chi(i, True)

relax.set_movemap(mm)
relax.apply(pose)
```

### MinMover

단일 최소화 단계만 수행합니다.

```python
from pyrosetta.rosetta.protocols.minimization_packing import MinMover

mm = MoveMap()
mm.set_bb(True)
mm.set_chi(True)

min_mover = MinMover()
min_mover.movemap(mm)
min_mover.score_function(sfxn)
min_mover.min_type("lbfgs_armijo_nonmonotone")
min_mover.tolerance(0.001)
min_mover.apply(pose)
```

### 카테시안 이완 (ddG 전처리용)

```python
sfxn_cart = create_score_function("ref2015_cart")
relax_cart = FastRelax(sfxn_cart, 3)
relax_cart.cartesian(True)
relax_cart.apply(pose)
```

---

## Docking

### FlexPepDock -- 펩타이드-단백질 도킹

SSTR2 같은 수용체에 펩타이드를 도킹하는 핵심 프로토콜입니다.

#### 도킹 모드

| 모드 | 설명 | 초기 구조 |
|------|------|----------|
| Refinement (`pep_refine`) | 근사 결합 모드 최적화 | 대략적 포즈 필요 |
| Ab-initio (`lowres_abinitio`) | 펩타이드 접힘 + 도킹 | 확장된 펩타이드 |
| Global | 바인딩 사이트 미상 시 | 여러 시작점 |

#### RosettaScripts XML로 실행

```python
# flexpepdock_refine.xml
xml_script = """
<ROSETTASCRIPTS>
  <SCOREFXNS>
    <ScoreFunction name="ref" weights="ref2015"/>
  </SCOREFXNS>
  <MOVERS>
    <FlexPepDock name="fpd"
      scorefxn="ref"
      pep_refine="1"
      lowres_abinitio="0"
    />
  </MOVERS>
  <PROTOCOLS>
    <Add mover="fpd"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
"""

from pyrosetta.rosetta.protocols.rosetta_scripts import XmlObjects
xml = XmlObjects.create_from_string(xml_script)
fpd = xml.get_mover("fpd")
fpd.apply(pose)
```

#### Ab-initio 모드 (펩타이드 구조 미상 시)

```python
xml_abinitio = """
<ROSETTASCRIPTS>
  <SCOREFXNS>
    <ScoreFunction name="ref" weights="ref2015"/>
  </SCOREFXNS>
  <MOVERS>
    <FlexPepDock name="fpd_abinitio"
      scorefxn="ref"
      pep_refine="1"
      lowres_abinitio="1"
    />
  </MOVERS>
  <PROTOCOLS>
    <Add mover="fpd_abinitio"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
"""
# 참고: Ab-initio 모드에서는 fragment 파일(3/5/9-mer)이 권장됨
# -frag3 frags.3mers -frag5 frags.5mers -frag9 frags.9mers
```

### RosettaLigand -- 소분자 도킹

```python
# 1. 리간드 파라미터 파일 생성
# bash: python molfile_to_params.py ligand.mol -n LIG

# 2. PyRosetta 초기화 시 로드
pyrosetta.init(extra_options="-in:file:extra_res_fa LIG.params")

# 3. 복합체 로드 및 도킹
pose = pose_from_pdb("receptor_ligand_complex.pdb")

# HighResDocker를 통한 도킹 (RosettaScripts 권장)
xml_ligand = """
<ROSETTASCRIPTS>
  <SCOREFXNS>
    <ScoreFunction name="ligand_soft" weights="ligand_soft_rep"/>
    <ScoreFunction name="hard" weights="ref2015"/>
  </SCOREFXNS>
  <MOVERS>
    <Transform name="transform" chain="X"
      move_distance="5.0" box_size="7.0"
      angle="360" cycles="500" repeats="1"
      temperature="5"/>
    <HighResDocker name="highres"
      scorefxn="hard" cycles="6"
      repack_every_Nth="3"/>
  </MOVERS>
  <PROTOCOLS>
    <Add mover="transform"/>
    <Add mover="highres"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
"""
```

### 단백질-단백질 도킹

```python
from pyrosetta.rosetta.protocols.docking import DockingProtocol

# Jump 설정 (체인 A vs 체인 B)
dock = DockingProtocol()
dock.set_docking_local_refine(True)   # 로컬 리파인먼트만
dock.set_docking_ft(True)             # 풀 프로토콜
dock.apply(pose)
```

---

## Protein Design

### PackRotamersMover -- 측쇄 팩킹/설계

```python
from pyrosetta.rosetta.protocols.minimization_packing import PackRotamersMover
from pyrosetta.rosetta.core.pack.task import TaskFactory, operation

# TaskFactory: 어떤 잔기를 어떻게 처리할지 정의
tf = TaskFactory()

# 전체 리팩킹만 (측쇄 최적화, 서열 변경 없음)
tf.push_back(operation.RestrictToRepacking())

pack = PackRotamersMover()
pack.score_function(sfxn)
pack.task_factory(tf)
pack.apply(pose)
```

#### 설계 모드 (서열 변경 허용)

```python
from pyrosetta.rosetta.core.pack.task import TaskFactory, operation
from pyrosetta.rosetta.core.select.residue_selector import (
    ChainSelector, NeighborhoodResidueSelector
)

tf = TaskFactory()

# 펩타이드 체인만 설계 허용
peptide_selector = ChainSelector("A")

# 수용체는 리팩킹만
receptor_selector = ChainSelector("B")
restrict_to_repack = operation.OperateOnResidueSubset(
    operation.RestrictToRepackingRLT(), receptor_selector
)
tf.push_back(restrict_to_repack)

# 펩타이드-수용체 인터페이스 주변만 설계
neighborhood = NeighborhoodResidueSelector(peptide_selector, 8.0, True)

# 나머지는 고정
prevent_repack = operation.OperateOnResidueSubset(
    operation.PreventRepackingRLT(),
    neighborhood,
    flip_subset=True  # 선택 안 된 잔기에 적용
)
tf.push_back(prevent_repack)

pack = PackRotamersMover()
pack.score_function(sfxn)
pack.task_factory(tf)
pack.apply(pose)
```

### FastDesign -- 설계 + 최적화 통합

```python
xml_design = """
<ROSETTASCRIPTS>
  <SCOREFXNS>
    <ScoreFunction name="ref" weights="ref2015"/>
  </SCOREFXNS>
  <RESIDUE_SELECTORS>
    <Chain name="peptide" chains="A"/>
    <Neighborhood name="interface" selector="peptide" distance="8.0"
                  include_focus_in_subset="true"/>
  </RESIDUE_SELECTORS>
  <TASKOPERATIONS>
    <DesignRestrictions name="design_peptide">
      <Action selector_logic="peptide" aas="ACDEFGHIKLMNPQRSTVWY"/>
      <Action selector_logic="NOT peptide" aas="NATAA"/>
    </DesignRestrictions>
  </TASKOPERATIONS>
  <MOVERS>
    <FastDesign name="fast_design" scorefxn="ref"
      task_operations="design_peptide" repeats="3"/>
  </MOVERS>
  <PROTOCOLS>
    <Add mover="fast_design"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
"""
```

---

## ddG Calculations

돌연변이의 결합 에너지 변화(ΔΔG)를 예측합니다.

### Cartesian ddG 프로토콜

가장 정확한 ddG 계산법 (Cartesian 최소화 기반):

```python
def compute_ddg(pose, resid, new_aa, sfxn_cart):
    """
    돌연변이 ΔΔG 계산 (Cartesian protocol)
    양수 = 불안정화 (안 좋음), 음수 = 안정화 (좋음)
    """
    from pyrosetta.rosetta.protocols.simple_moves import MutateResidue
    from pyrosetta.rosetta.protocols.relax import FastRelax
    from pyrosetta.rosetta.core.kinematics import MoveMap

    # 1. 야생형 이완
    wt_pose = pose.clone()
    relax = FastRelax(sfxn_cart, 3)
    relax.cartesian(True)

    # 돌연변이 주변 8Å만 이완
    mm = MoveMap()
    mm.set_bb(False)
    mm.set_chi(False)
    ca_xyz = pose.residue(resid).xyz("CA")
    for i in range(1, pose.total_residue() + 1):
        dist = (pose.residue(i).xyz("CA") - ca_xyz).norm()
        if dist <= 8.0:
            mm.set_bb(i, True)
            mm.set_chi(i, True)
    relax.set_movemap(mm)
    relax.apply(wt_pose)
    wt_score = sfxn_cart(wt_pose)

    # 2. 돌연변이 도입 + 이완
    mut_pose = pose.clone()
    MutateResidue(target=resid, new_res=new_aa).apply(mut_pose)
    relax.apply(mut_pose)
    mut_score = sfxn_cart(mut_pose)

    # 3. ΔΔG = E(mutant) - E(wildtype)
    ddg = mut_score - wt_score
    return ddg

# 사용 예: Somatostatin W8A의 ΔΔG
sfxn_cart = create_score_function("ref2015_cart")
ddg = compute_ddg(pose, resid=8, new_aa="ALA", sfxn_cart=sfxn_cart)
print(f"W8A ΔΔG = {ddg:.2f} REU")
# 양수 = Trp8이 결합에 중요 (알라닌 치환 시 불안정화)
```

### 결합 ΔΔG (Interface ddG)

```python
def compute_binding_ddg(complex_pose, jump_id=1, sfxn=None):
    """
    결합 에너지: ΔG_bind = E(complex) - E(receptor_alone) - E(ligand_alone)
    """
    if sfxn is None:
        sfxn = get_fa_scorefxn()

    # 복합체 에너지
    e_complex = sfxn(complex_pose)

    # 분리: jump 방향으로 1000Å 이동
    from pyrosetta.rosetta.protocols.rigid import RigidBodyTransMover
    separated = complex_pose.clone()
    trans = RigidBodyTransMover(separated, jump_id)
    trans.step_size(1000.0)
    trans.apply(separated)
    e_separated = sfxn(separated)

    dg_bind = e_complex - e_separated
    return dg_bind
```

---

## Loop Modeling

수용체의 유연한 루프 영역이나 펩타이드 링커를 모델링합니다.

### KIC (Kinematic Closure)

```python
# KIC 루프 모델링 (RosettaScripts)
xml_loop = """
<ROSETTASCRIPTS>
  <MOVERS>
    <LoopModeler name="loop_model" loops_file="loops.txt"
      config="kic" perturb_sequence="no"
      fast="false"/>
  </MOVERS>
  <PROTOCOLS>
    <Add mover="loop_model"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
"""

# loops.txt 형식:
# LOOP start end cut skip_rate extend
# LOOP 180 195 188 0 1
```

### CCD (Cyclic Coordinate Descent)

```python
# CCD 루프 빌딩 -- 빠른 루프 닫기
xml_ccd = """
<ROSETTASCRIPTS>
  <MOVERS>
    <LoopModeler name="loop_ccd" loops_file="loops.txt"
      config="ccd" fast="true"/>
  </MOVERS>
  <PROTOCOLS>
    <Add mover="loop_ccd"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
"""
```

---

## Constraint / Restraint System

실험 데이터(NOE, 크로스링크 등)를 구조 계산에 반영하거나, 원하는 기하학적 조건을 강제합니다.

### 제약 조건 유형

| 유형 | 설명 | 용도 |
|------|------|------|
| `AtomPairConstraint` | 두 원자 간 거리 제약 | 수소결합, 접촉 |
| `CoordinateConstraint` | 절대 좌표 고정 | 수용체 고정, 리간드 위치 |
| `AngleConstraint` | 세 원자 각도 제약 | 기하학적 조건 |
| `DihedralConstraint` | 네 원자 이면각 제약 | 백본 각도, cis/trans |
| `AmbiguousConstraint` | 여러 제약 중 최소 | 대칭/교환 가능 접촉 |

### 함수 유형

| 함수 | 설명 | 파라미터 |
|------|------|---------|
| `HARMONIC` | 하모닉 포텐셜 | x0 sd |
| `GAUSSIANFUNC` | 가우시안 | mean sd WEIGHT |
| `BOUNDED` | 구간 내 자유 | lb ub sd |
| `FLAT_HARMONIC` | 중심 부근 자유, 외부 하모닉 | x0 sd tol |
| `FADE` | 점진적 감쇠 | lb ub d dfade |

### 제약 파일 작성

```
# constraints.cst
# Trp8(CA) -- SSTR2 B197(CA) 거리 = 5Å 유지
AtomPair CA 8A CA 197B HARMONIC 5.0 0.5

# Lys9(NZ) -- SSTR2 B122(OD2) 염다리 유지
AtomPair NZ 9A OD2 122B HARMONIC 2.8 0.3

# 이황화 결합 (Cys3-Cys14)
AtomPair SG 3A SG 14A HARMONIC 2.04 0.1

# 좌표 고정 (수용체 백본)
CoordinateConstraint CA 197B CA 1B 10.5 12.3 45.2 HARMONIC 0.0 0.5
```

### Python에서 제약 조건 적용

```python
from pyrosetta.rosetta.core.scoring.constraints import (
    AtomPairConstraint,
    ConstraintSet,
)
from pyrosetta.rosetta.core.scoring.func import HarmonicFunc
from pyrosetta.rosetta.core.id import AtomID

# 수동 제약 추가
atom1 = AtomID(pose.residue(8).atom_index("CA"), 8)
atom2 = AtomID(pose.residue(197).atom_index("CA"), 197)
func = HarmonicFunc(5.0, 0.5)  # 목표 5Å, sd 0.5Å
constraint = AtomPairConstraint(atom1, atom2, func)
pose.add_constraint(constraint)

# 스코어 함수에 제약 가중치 추가
sfxn.set_weight(ScoreType.atom_pair_constraint, 1.0)
sfxn.set_weight(ScoreType.coordinate_constraint, 1.0)
```

### 파일에서 제약 조건 로드

```python
# RosettaScripts에서
xml_cst = """
<ROSETTASCRIPTS>
  <MOVERS>
    <ConstraintSetMover name="add_cst" add_constraints="true"
      cst_file="constraints.cst"/>
  </MOVERS>
  <PROTOCOLS>
    <Add mover="add_cst"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
"""
```

---

## Fragment-Based Modeling

짧은 구조 단편(3/5/9-mer)을 사용하여 컨포메이션 탐색을 수행합니다.

### Fragment 생성 (Fragment Picker)

```bash
# Robetta 서버 (http://robetta.bakerlab.org/) 또는 로컬 실행
# 입력: 서열, PSIPRED 2차 구조 예측
# 출력: frags.3mers.gz, frags.9mers.gz

# 로컬 실행 (Rosetta 필요)
fragment_picker.linuxgccrelease \
  -in:file:fasta peptide.fasta \
  -in:file:vall_path vall.jul19.2011.gz \
  -frags:ss_pred psipred_ss2 \
  -frags:n_frags 200 \
  -frags:frag_sizes 3 5 9 \
  -out:file:frag_prefix frags
```

### Fragment 사용

```python
# FlexPepDock ab-initio에서 사용
pyrosetta.init(extra_options="""
    -frag3 frags.3mers
    -frag5 frags.5mers
    -frag9 frags.9mers
""")
```

---

## Cyclic Peptide Tools

Octreotide, DOTATATE 같은 고리 펩타이드 모델링에 필수적인 도구입니다.

### PeptideCyclizeMover

N-말단과 C-말단 사이의 펩타이드 결합을 형성하여 고리를 닫습니다.

```python
# RosettaScripts XML
xml_cyclize = """
<ROSETTASCRIPTS>
  <MOVERS>
    <PeptideCyclizeMover name="cyclize"/>
    <DeclareBond name="disulfide"
      atom1="SG" res1="3" atom2="SG" res2="14"
      add_termini="false"/>
  </MOVERS>
  <PROTOCOLS>
    <Add mover="cyclize"/>
    <Add mover="disulfide"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
"""
```

### CrankshaftFlipMover

고리 펩타이드의 백본 컨포메이션 탐색:

```python
# phi/psi 부호 반전 + omega 플립으로 고리 내 새로운 컨포메이션 생성
# 선형/고리 펩타이드, 펩토이드, N-메틸 아미노산 지원
xml_crankshaft = """
<ROSETTASCRIPTS>
  <MOVERS>
    <CrankshaftFlipMover name="crank"
      residue_selector="peptide"/>
  </MOVERS>
</ROSETTASCRIPTS>
"""
```

### simple_cycpep_predict

고리 펩타이드의 de novo 구조 예측:

```bash
# Rosetta 앱으로 실행
simple_cycpep_predict.linuxgccrelease \
  -cyclic_peptide:sequence_file sequence.txt \
  -cyclic_peptide:genkic_closure_attempts 10000 \
  -nstruct 1000 \
  -out:prefix cycpep_
```

### 이황화 결합 형성

```python
from pyrosetta.rosetta.protocols.simple_moves import DisulfideInsertionMover

# Cys3-Cys14 이황화 결합 (Somatostatin)
disulfide = DisulfideInsertionMover(3, 14)
disulfide.apply(pose)
```

---

## Small Molecule Handling

비표준 잔기(킬레이터, 링커, D-아미노산)를 Rosetta에서 다루는 방법입니다.

### molfile_to_params -- 파라미터 파일 생성

```bash
# Rosetta scripts 디렉토리에 위치
python molfile_to_params.py ligand.mol -n LIG -p LIG

# 출력:
#   LIG.params    -- 토폴로지/파라미터 파일
#   LIG_0001.pdb  -- 3D 좌표 (콘포머)

# SDF 파일도 가능
python molfile_to_params.py ligand.sdf -n LIG

# 킬레이터 (DOTA) 예시
python molfile_to_params.py DOTA.mol -n DOT -p DOT
```

### PyRosetta에서 로드

```python
pyrosetta.init(extra_options="""
    -in:file:extra_res_fa LIG.params DOT.params
""")

# 또는 런타임에 추가
from pyrosetta.rosetta.core.chemical import ChemicalManager
chm = ChemicalManager.get_instance()
rts = chm.residue_type_set("fa_standard")
# rts에 params 파일의 잔기가 포함됨
```

### D-아미노산

```python
# Rosetta는 D-아미노산을 기본 지원
# 서열에서 소문자로 표기하거나 DALL 접두사 사용
pose = pose_from_sequence("AGCKNFFwKTFTSC")  # w = D-Trp

# 또는 후처리로 L→D 변환
from pyrosetta.rosetta.protocols.simple_moves import MutateResidue
MutateResidue(target=8, new_res="DTRP").apply(pose)
```

### 비표준 아미노산 (NCAA)

```python
# N-메틸 아미노산, 베타 아미노산 등
# 별도 params 파일 필요

# Rosetta NCAA 데이터베이스에서 기본 제공되는 것들:
# - D-아미노산 (DALA, DARG, ...)
# - 인산화 (SEP, TPO, PTR)
# - 메틸화 (MLY, MLZ, ...)
# - 아세틸화 (ALY, ...)
```

---

## Energy Decomposition

총 에너지를 잔기별, 항별로 분해하여 핫스팟 잔기를 식별합니다.

### 잔기별 에너지

```python
sfxn(pose)  # 먼저 스코어링

# 잔기별 총 에너지
for i in range(1, pose.total_residue() + 1):
    total_e = pose.energies().residue_total_energy(i)
    chain = pose.pdb_info().chain(i)
    resn = pose.residue(i).name3()
    resi = pose.pdb_info().number(i)
    print(f"{chain}{resi}({resn}): {total_e:.2f}")
```

### 항별 에너지 분해

```python
from pyrosetta.rosetta.core.scoring import ScoreType

sfxn(pose)

# 특정 잔기의 각 항 에너지
resid = 8  # Trp8
energies = pose.energies().residue_total_energies(resid)
for st in [ScoreType.fa_atr, ScoreType.fa_rep, ScoreType.fa_sol,
           ScoreType.fa_elec, ScoreType.hbond_sc]:
    val = energies[st]
    print(f"  {st.name}: {val:.3f}")
```

### 잔기쌍 상호작용 에너지

```python
from pyrosetta.toolbox.atom_pair_energy import etable_atom_pair_energies

# 두 잔기 간 상호작용 에너지 분해
res_i = pose.residue(8)    # Trp8 (펩타이드)
res_j = pose.residue(197)  # Trp197 (수용체)

atr, rep, sol, elec = etable_atom_pair_energies(res_i, res_j, sfxn)
print(f"Trp8-Trp197: atr={atr:.2f} rep={rep:.2f} sol={sol:.2f} elec={elec:.2f}")
print(f"Total interaction: {atr + rep + sol + elec:.2f}")
```

### 인터페이스 에너지 분석

```python
def interface_energy_analysis(pose, chain_A="A", chain_B="B", sfxn=None):
    """인터페이스 잔기별 에너지 기여도 분석"""
    if sfxn is None:
        sfxn = get_fa_scorefxn()
    sfxn(pose)

    results = []
    for i in range(1, pose.total_residue() + 1):
        chain = pose.pdb_info().chain(i)
        if chain not in (chain_A, chain_B):
            continue

        total_e = pose.energies().residue_total_energy(i)
        resn = pose.residue(i).name3()
        resi = pose.pdb_info().number(i)

        results.append({
            "chain": chain,
            "resi": resi,
            "resn": resn,
            "total_energy": total_e,
        })

    # 에너지 기여도 순으로 정렬 (음수 = 안정화)
    results.sort(key=lambda x: x["total_energy"])

    print("\n=== Top stabilizing residues ===")
    for r in results[:10]:
        print(f"  {r['chain']}{r['resi']}({r['resn']}): {r['total_energy']:.2f}")

    print("\n=== Top destabilizing residues ===")
    for r in results[-5:]:
        print(f"  {r['chain']}{r['resi']}({r['resn']}): {r['total_energy']:.2f}")

    return results
```

---

## RosettaScripts Integration

Python에서 RosettaScripts XML 프로토콜을 실행합니다.

### XmlObjects

```python
from pyrosetta.rosetta.protocols.rosetta_scripts import XmlObjects

# XML 파일에서
xml = XmlObjects.create_from_file("protocol.xml")

# XML 문자열에서
xml = XmlObjects.create_from_string("""
<ROSETTASCRIPTS>
  <MOVERS>
    <FastRelax name="relax" repeats="3"/>
  </MOVERS>
  <PROTOCOLS>
    <Add mover="relax"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
""")

# Mover 추출 및 적용
mover = xml.get_mover("relax")
mover.apply(pose)

# Filter 추출
# filter = xml.get_filter("my_filter")
# passed = filter.apply(pose)
# score = filter.score(pose)
```

### 자주 사용하는 RosettaScripts 조합

```xml
<!-- 복합 프로토콜: 제약 조건 + 이완 + 설계 + 필터 -->
<ROSETTASCRIPTS>
  <SCOREFXNS>
    <ScoreFunction name="ref_cst" weights="ref2015">
      <Reweight scoretype="atom_pair_constraint" weight="1.0"/>
      <Reweight scoretype="coordinate_constraint" weight="0.5"/>
    </ScoreFunction>
  </SCOREFXNS>

  <RESIDUE_SELECTORS>
    <Chain name="peptide" chains="A"/>
    <Chain name="receptor" chains="B"/>
    <Neighborhood name="interface" selector="peptide" distance="8.0"/>
  </RESIDUE_SELECTORS>

  <MOVERS>
    <ConstraintSetMover name="add_cst" cst_file="constraints.cst"/>
    <FastRelax name="relax" scorefxn="ref_cst" repeats="3"/>
    <PackRotamersMover name="design" scorefxn="ref_cst"/>
  </MOVERS>

  <FILTERS>
    <Ddg name="ddg_filter" scorefxn="ref_cst" threshold="-10"
         jump="1" repeats="3"/>
    <Sasa name="sasa_filter" threshold="800"/>
  </FILTERS>

  <PROTOCOLS>
    <Add mover="add_cst"/>
    <Add mover="relax"/>
    <Add mover="design"/>
    <Add filter="ddg_filter"/>
    <Add filter="sasa_filter"/>
  </PROTOCOLS>
</ROSETTASCRIPTS>
```

---

## Symmetry Handling

대칭 구조(이합체, 삼합체, 케이지)를 효율적으로 처리합니다.

```python
# 대칭 정의 파일 생성 (Rosetta 유틸리티)
# bash: make_symmdef_file.pl -m NCS -a A -i B -p dimer.pdb > C2.symm

# PyRosetta에서 대칭 적용
pyrosetta.init(extra_options="-symmetry_definition C2.symm")
pose = pose_from_pdb("dimer.pdb")

# 대칭 상태에서 스코어링/이완/도킹 수행
# (비대칭 단위만 계산, 나머지는 대칭 연산으로 유도)

# 비대칭 단위 추출
from pyrosetta.rosetta.core.pose.symmetry import extract_asymmetric_unit
asym_pose = extract_asymmetric_unit(pose)
asym_pose.dump_pdb("monomer.pdb")
```

---

## 펩타이드 리간드 설계 워크플로우

> SSTR2 타겟의 Octreotide 유사 펩타이드 설계를 예제로 한 전체 파이프라인

### 워크플로우 개요

```
1. 구조 준비
   AlphaFold3 복합체 → PDB 추출 → 바인딩 포켓 분석
          ↓
2. 초기 이완
   FastRelax (ref2015_cart) → 에너지 최소화
          ↓
3. Alanine Scanning (in silico)
   각 잔기 → Ala 돌연변이 → ΔΔG 계산 → 핫스팟 식별
          ↓
4. 설계
   핫스팟 보존 + 나머지 잔기 설계 (FastDesign)
          ↓
5. 도킹 검증
   FlexPepDock refinement → 에너지/RMSD 평가
          ↓
6. 고리화 (옵션)
   PeptideCyclizeMover + 이황화 결합
          ↓
7. 랭킹
   총 에너지, ΔΔG, 인터페이스 SASA 기준 순위
```

### 전체 코드 예제

```python
#!/usr/bin/env python3
"""
sstr2_peptide_design.py
SSTR2 타겟 펩타이드 리간드 설계 전체 파이프라인
"""
import pyrosetta
from pyrosetta import pose_from_pdb, get_fa_scorefxn, create_score_function
from pyrosetta.rosetta.protocols.relax import FastRelax
from pyrosetta.rosetta.protocols.simple_moves import MutateResidue
from pyrosetta.rosetta.core.kinematics import MoveMap

# === 1. 초기화 ===
pyrosetta.init(extra_options="-mute all")
sfxn = get_fa_scorefxn()
sfxn_cart = create_score_function("ref2015_cart")

# === 2. 구조 로드 ===
pose = pose_from_pdb("data/fold_test1/fold_test1_model_0.pdb")
print(f"Loaded: {pose.total_residue()} residues")
print(f"Chain A (Somatostatin): {pose.sequence()[:14]}")

# === 3. 초기 이완 ===
relax = FastRelax(sfxn_cart, 3)
relax.cartesian(True)
relax_pose = pose.clone()
relax.apply(relax_pose)
print(f"After relax: {sfxn(relax_pose):.2f} REU")

# === 4. Alanine Scanning ===
print("\n=== Alanine Scanning ===")
wt_score = sfxn_cart(relax_pose)
hotspots = []

for i in range(1, 15):  # 펩타이드 잔기 1-14
    if relax_pose.residue(i).name3() == "ALA":
        continue
    if relax_pose.residue(i).name3() in ("GLY", "CYS"):
        continue  # Gly/Cys는 스킵

    mut_pose = relax_pose.clone()
    MutateResidue(target=i, new_res="ALA").apply(mut_pose)

    # 로컬 이완
    mm = MoveMap()
    mm.set_bb(False)
    mm.set_chi(False)
    for j in range(max(1, i-3), min(pose.total_residue(), i+4)):
        mm.set_chi(j, True)
    local_relax = FastRelax(sfxn_cart, 1)
    local_relax.cartesian(True)
    local_relax.set_movemap(mm)
    local_relax.apply(mut_pose)

    ddg = sfxn_cart(mut_pose) - wt_score
    resn = relax_pose.residue(i).name3()
    print(f"  {resn}{i} → ALA: ΔΔG = {ddg:+.2f}")

    if ddg > 2.0:  # 2 REU 이상 불안정화 = 핫스팟
        hotspots.append(i)

print(f"\nHotspot residues: {hotspots}")

# === 5. 설계 (핫스팟 보존) ===
# 핫스팟은 보존, 나머지는 설계 허용
# ... (FastDesign XML 사용 -- 위 섹션 참고)

# === 6. 결과 저장 ===
relax_pose.dump_pdb("results/designed_peptide.pdb")
print("Done! Saved to results/designed_peptide.pdb")
```

### 방사성 의약품 관련 설계 고려사항

| 고려사항 | PyRosetta 도구 | 설명 |
|---------|---------------|------|
| 킬레이터 부착 위치 | `molfile_to_params` + 에너지 분해 | 바인딩에 기여하지 않는 잔기(N/C 말단 등)에 킬레이터 부착 |
| 링커 길이 최적화 | `Loop Modeling` + 제약 조건 | 킬레이터-펩타이드 간 최적 거리 |
| 대사 안정성 | D-아미노산, N-메틸 | 프로테아제 저항성 향상 |
| 고리화 | `PeptideCyclizeMover` | 안정성/선택성 향상 |
| 수용체 선택성 | `ddG` + FoldMason 정렬 | SSTR2 선택적 잔기 식별 |
| 수소결합 네트워크 | `Constraint` + 에너지 분해 | 핵심 상호작용 보존 |

---

## 참고 자료

- **공식 문서**: https://graylab.jhu.edu/PyRosetta.documentation/
- **PyRosetta4 노트북**: https://rosettacommons.github.io/PyRosetta.notebooks/
- **RosettaScripts 문서**: https://www.rosettacommons.org/docs/latest/scripting_documentation/RosettaScripts/
- **FlexPepDock**: https://www.rosettacommons.org/docs/latest/application_documentation/docking/flex-pep-dock
- **ddG 프로토콜**: https://www.rosettacommons.org/docs/latest/cartesian-ddG
- **고리 펩타이드**: https://www.rosettacommons.org/docs/latest/application_documentation/design/simple_cycpep_predict
- **라이선스**: https://www.rosettacommons.org/software/license-and-download
