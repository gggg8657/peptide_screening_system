# PyMOL 완전 가이드

> **Molecular Graphics System**  
> 버전: 3.1.0 (Open-Source)  
> 공식 사이트: https://pymol.org  
> 문서: https://pymol.org/dokuwiki/

---

## 목차

1. [개요](#개요)
2. [설치](#설치)
3. [기본 사용법](#기본-사용법)
4. [표현 방식 (Representations)](#표현-방식-representations)
5. [선택 문법 (Selections)](#선택-문법-selections)
6. [색상 및 렌더링](#색상-및-렌더링)
7. [뷰 제어](#뷰-제어)
8. [정렬 및 중첩](#정렬-및-중첩)
9. [측정](#측정)
10. [분자 편집](#분자-편집)
11. [무비 제작](#무비-제작)
12. [스크립팅](#스크립팅)
13. [고급 기능](#고급-기능)
14. [명령어 레퍼런스](#명령어-레퍼런스)

---

## 개요

PyMOL은 단백질, 핵산, 소분자 등 분자 구조를 시각화하는 **업계 표준** 도구입니다.

### 핵심 특징

| 특징 | 설명 |
|------|------|
| **고품질 렌더링** | 레이트레이싱으로 출판 품질 이미지 |
| **다양한 표현** | Cartoon, Surface, Sticks, Spheres 등 |
| **강력한 선택** | 복잡한 원자 선택 문법 |
| **Python 통합** | 완전한 Python API |
| **구조 정렬** | 서열/구조 기반 중첩 |
| **무비 제작** | 애니메이션 및 비디오 생성 |
| **확장성** | 플러그인 및 스크립트 지원 |

---

## 설치

### Conda (권장)

```bash
conda install -c conda-forge pymol-open-source
```

### 확인

```bash
pymol --version
# PyMOL 3.1.0
```

### WSL에서 실행

WSL에서 GUI 사용 시:
- **Windows 11**: WSLg 자동 지원
- **Windows 10**: X 서버 필요 (VcXsrv, X410 등)

```bash
# X 서버 설정 (Windows 10)
export DISPLAY=:0

# 실행
pymol structure.pdb
```

---

## 기본 사용법

### 명령줄 실행

```bash
# GUI 모드
pymol structure.pdb

# 여러 파일
pymol model1.pdb model2.pdb model3.pdb

# 헤드리스 모드 (이미지만 저장)
pymol -c structure.pdb -d "png output.png; quit"
```

### 기본 명령어

```python
# 파일 로드
load structure.pdb

# 저장
save output.pdb, selection
save image.png

# 종료
quit
```

### 도움말

```python
help                    # 전체 도움말
help commands           # 명령어 목록
help <command>          # 특정 명령어 도움말
help selections         # 선택 문법
```

---

## 표현 방식 (Representations)

### 사용 가능한 표현

| 표현 | 설명 | 용도 |
|------|------|------|
| **lines** | 결합을 선으로 표시 | 기본, 빠른 탐색 |
| **sticks** | 두꺼운 막대 | 리간드, 활성 부위 |
| **spheres** | 원자를 구로 표시 | 공간 충전 모델 |
| **cartoon** | 2차 구조 리본 | 단백질 전체 구조 |
| **ribbon** | 간단한 리본 | 빠른 개요 |
| **surface** | 분자 표면 | 결합 포켓, 상호작용 |
| **mesh** | 메쉬 표면 | 반투명 표면 |
| **dots** | 점 표면 | 가벼운 표면 |
| **labels** | 텍스트 라벨 | 잔기/원자 표시 |
| **nonbonded** | 비결합 원자 | 물, 이온 |
| **nb_spheres** | 비결합 구 | 물 분자 |

### 명령어

```python
# 표현 켜기
show cartoon               # 전체에 cartoon
show sticks, resi 100      # 잔기 100에 sticks
show surface, chain A      # 체인 A에 surface

# 표현 끄기
hide everything            # 모든 표현 끄기
hide lines                 # lines만 끄기
hide cartoon, chain B      # 체인 B의 cartoon 끄기

# 표현 교체 (as = hide all + show)
as cartoon                 # cartoon만 표시
as sticks, organic         # 유기 분자를 sticks로

# 모든 표현 보기
show everything
```

### Cartoon 스타일

```python
# Cartoon 타입 설정
cartoon loop               # 루프 스타일
cartoon tube               # 튜브 스타일
cartoon automatic          # 자동 (기본)
cartoon oval               # 타원형 나선
cartoon rectangle          # 직사각형 시트

# 설정
set cartoon_oval_length, 1.2
set cartoon_rect_length, 1.4
set cartoon_loop_radius, 0.3
```

---

## 선택 문법 (Selections)

### 기본 선택자

| 선택자 | 단축형 | 예시 | 설명 |
|--------|--------|------|------|
| `name` | `n.` | `name CA` | 원자 이름 |
| `resn` | `r.` | `resn ALA` | 잔기 이름 |
| `resi` | `i.` | `resi 100` | 잔기 번호 |
| `chain` | `c.` | `chain A` | 체인 ID |
| `segi` | `s.` | `segi SEG1` | 세그먼트 |
| `elem` | `e.` | `elem C` | 원소 |
| `alt` | - | `alt A` | 대체 위치 |
| `id` | - | `id 100` | 원자 ID |

### 특수 선택자

| 선택자 | 설명 |
|--------|------|
| `all` / `*` | 모든 원자 |
| `none` | 선택 없음 |
| `hydrogen` / `h.` | 수소 원자 |
| `hetatm` | HETATM 레코드 |
| `organic` | 유기 분자 (리간드) |
| `solvent` | 용매 (물) |
| `polymer` | 고분자 (단백질, 핵산) |
| `visible` / `v.` | 보이는 원자 |
| `enabled` | 활성화된 객체 |

### 논리 연산자

```python
# AND
select mysel, chain A and resi 100
select mysel, c. A & i. 100

# OR
select mysel, resn ALA or resn GLY
select mysel, r. ALA | r. GLY

# NOT
select mysel, not hydrogen
select mysel, ! h.

# 복합
select active_site, chain A and resi 100-120 and not hydrogen
```

### 거리 기반 선택

```python
# around: 주변 원자
select near_ligand, organic around 5     # 리간드 5Å 이내

# within: 거리 내 원자
select contacts, chain A within 4 of chain B

# expand: 선택 확장
select expanded, resi 100 expand 3

# gap: 갭 거리
select far, chain A gap 10
```

### 구조 기반 선택

```python
# byres: 잔기 단위로 확장
select whole_res, byres (name CA within 5 of organic)
byres organic around 4

# byobj: 객체 단위로 확장
select whole_obj, byobj chain A

# bycalpha: CA 기준
select backbone, bycalpha all
```

### 범위 및 패턴

```python
# 잔기 범위
resi 10-50                # 10부터 50
resi 10+20+30            # 10, 20, 30

# 체인 여러 개
chain A+B+C

# 와일드카드
resn AL*                 # ALA, ALN 등
name C*                  # C, CA, CB 등
```

### 속성 비교

```python
# B-factor
select high_b, b > 50
select low_b, b < 20

# Occupancy
select partial, q < 1.0

# Formal charge
select positive, formal_charge > 0

# Partial charge
select polar, partial_charge > 0.3 or partial_charge < -0.3
```

### 선택 저장 및 사용

```python
# 선택 생성
select active_site, resi 100-120 and chain A

# 선택 사용
show sticks, active_site
color red, active_site

# 선택 삭제
delete active_site
```

---

## 색상 및 렌더링

### 기본 색상

```python
# 단일 색상
color red, chain A
color blue, organic
color yellow, resi 100

# 원소별 색상 (CPK)
util.cbaw               # 탄소=흰색
util.cbag               # 탄소=회색
util.cbac               # 탄소=청록색
util.cbam               # 탄소=마젠타
util.cbay               # 탄소=노랑
util.cbas               # 탄소=연어색
util.cbap               # 탄소=분홍
```

### 스펙트럼 색상

```python
# 잔기 번호로 스펙트럼
spectrum count, rainbow, chain A

# B-factor로 색상
spectrum b, blue_white_red

# 체인별 색상
util.cbc                # 체인별 색상

# 2차 구조별
util.cbss               # helix=red, sheet=yellow, loop=green
```

### 사용자 정의 색상

```python
# 새 색상 정의
set_color mycolor, [0.8, 0.2, 0.5]
color mycolor, selection

# RGB 직접
color 0x00FF00, selection      # 녹색
```

### 배경 색상

```python
bg_color white
bg_color black
bg_color gray
```

### 렌더링

```python
# 레이트레이싱 (고품질)
ray                            # 현재 크기
ray 1920, 1080                 # 지정 크기
ray 4000, 3000                 # 출판용 고해상도

# 빠른 그리기
draw                           # 안티앨리어싱 없음
draw 1920, 1080

# PNG 저장
png output.png                 # 현재 뷰
png output.png, ray=1          # 레이트레이싱 후 저장
png output.png, 1920, 1080, ray=1
```

### 렌더링 설정

```python
# 안티앨리어싱
set antialias, 2

# 그림자
set ray_shadows, on
set ray_shadow_decay_factor, 0.1

# 조명
set light_count, 4
set spec_reflect, 1.5

# 투명도
set transparency, 0.5, surface
set cartoon_transparency, 0.3
```

---

## 뷰 제어

### 기본 뷰 조작

```python
# 줌
zoom                     # 전체 보기
zoom chain A             # 선택 영역에 맞춤
zoom resi 100, 5         # 5Å 버퍼로 줌

# 중심
center resi 100
origin resi 100          # 회전 중심 설정

# 방향 설정
orient                   # 주축 정렬
orient chain A
```

### 회전 및 이동

```python
# 회전 (도 단위)
turn x, 90               # X축으로 90도
turn y, 45
turn z, 180

# 이동
move x, 10               # X 방향 10단위
move y, -5

# 클리핑
clip near, -5            # 앞 클리핑 조절
clip far, 10
clip slab, 20            # 슬래브 두께
```

### 뷰 저장/복원

```python
# 뷰 저장
view myview, store

# 뷰 복원
view myview, recall

# 현재 뷰 행렬
get_view                 # 18개 숫자 출력
set_view ([...])         # 뷰 설정
```

### Scene 관리

```python
# Scene 저장 (뷰 + 표현 + 색상)
scene F1, store          # F1 키에 저장
scene myname, store

# Scene 복원
scene F1, recall
scene myname

# Scene 목록
scene                    # 목록 출력

# Scene 삭제
scene myname, clear
```

### 창 설정

```python
# 뷰포트 크기
viewport 1920, 1080

# 전체 화면
full_screen on
full_screen off
```

---

## 정렬 및 중첩

### align (서열 기반)

```python
# 기본 정렬
align mobile, target

# 결과 객체 생성
align protA, protB, object=alignment

# 파라미터
align protA, protB, cycles=5, cutoff=2.0

# CA 원자만
align protA////CA, protB////CA
```

### super (구조 기반)

```python
# 서열 유사성 낮을 때 권장
super mobile, target

# 파라미터
super protA, protB, cycles=5, cutoff=2.0, object=super_aln
```

### cealign (CE 알고리즘)

```python
# 가장 강력한 구조 정렬
cealign target, mobile

# 결과
cealign protB, protA, object=ce_aln
```

### pair_fit (원자 쌍 피팅)

```python
# 특정 원자 쌍으로 정렬
pair_fit \
  protA///10/CA, protB///10/CA, \
  protA///20/CA, protB///20/CA, \
  protA///30/CA, protB///30/CA
```

### fit (좌표 피팅)

```python
# 동일 원자 수 필요
fit mobile, target
```

### RMSD 계산

```python
# 현재 좌표 RMSD
rms_cur mobile, target

# 피팅 후 RMSD
rms mobile, target

# 내부 상태 RMSD
intra_rms mobile
intra_fit mobile        # 상태간 피팅
```

---

## 측정

### 거리 측정

```python
# 두 원자 간 거리
distance dist1, /protA/A/100/CA, /protA/A/200/CA

# 선택 간 거리
distance polar_contacts, chain A, chain B, mode=2

# 모드
# mode=0: 모든 원자 쌍
# mode=2: 극성 접촉
# mode=4: 수소 결합
```

### 각도 측정

```python
# 세 원자 각도
angle ang1, \
  /prot/A/100/N, \
  /prot/A/100/CA, \
  /prot/A/100/C
```

### 이면각 측정

```python
# 네 원자 이면각
dihedral dih1, \
  /prot/A/100/N, \
  /prot/A/100/CA, \
  /prot/A/100/C, \
  /prot/A/101/N
```

### 자동 측정 표시

```python
# 극성 접촉 표시
distance hbonds, chain A, chain B, mode=2
show dashes, hbonds

# 스타일 설정
set dash_color, yellow, hbonds
set dash_width, 2.0
set dash_gap, 0.3
```

---

## 분자 편집

### 원자/잔기 조작

```python
# 삭제
remove hydrogen          # 수소 제거
remove solvent           # 물 제거
remove resi 100          # 잔기 삭제

# 이름 변경
set_name old_name, new_name

# 복사
create new_obj, selection

# 추출 (원본에서 제거)
extract new_obj, selection
```

### 구조 수정

```python
# 수소 추가
h_add selection
h_fill                   # 불완전한 원자에 H 추가

# 결합 수정
bond atom1, atom2        # 결합 추가
unbond atom1, atom2      # 결합 제거

# 원자 치환
replace O, N, 3          # N으로 3개 결합

# 회전
rotate x, 45, selection
rotate y, 90, selection, origin=[0,0,0]

# 이동
translate [10, 0, 0], selection
```

### 이면각 설정

```python
# 이면각 직접 설정
set_dihedral \
  /prot/A/100/N, \
  /prot/A/100/CA, \
  /prot/A/100/C, \
  /prot/A/101/N, \
  180.0
```

### Undo/Redo

```python
undo
redo
```

---

## 무비 제작

### 프레임 설정

```python
# 프레임 수 설정
mset 1 x100              # 100 프레임

# 상태 기반
mset 1 -60               # 상태 1-60 사용
mset 1 x30 1 -60 60 x30  # 혼합
```

### 키프레임 애니메이션

```python
# 뷰 키프레임
mview store, 1           # 프레임 1에 현재 뷰 저장
# ... 뷰 변경 ...
mview store, 50          # 프레임 50에 뷰 저장
mview store, 100

# 보간
mview interpolate        # 중간 프레임 생성
```

### 씬 기반 애니메이션

```python
# Scene 전환 무비
scene S1, store
# ... 설정 변경 ...
scene S2, store

mset 1 x200
mview store, 1, scene=S1
mview store, 100, scene=S2
mview store, 200, scene=S1
mview interpolate
```

### 재생 제어

```python
mplay                    # 재생
mstop                    # 정지
mrewind                  # 처음으로
frame 50                 # 특정 프레임으로
forward                  # 앞으로
backward                 # 뒤로
```

### 내보내기

```python
# PNG 시퀀스
mpng frame_              # frame_0001.png, frame_0002.png, ...

# 레이트레이싱 적용
set ray_trace_frames, 1
mpng movie_frame_, ray=1
```

### FFmpeg로 비디오 변환

```bash
ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p movie.mp4
```

---

## 스크립팅

### 명령줄에서 스크립트 실행

```bash
pymol -c script.pml
pymol structure.pdb -d "run script.py"
```

### PML 스크립트

```python
# script.pml
load structure.pdb
hide everything
show cartoon
color spectrum
orient
ray 1920, 1080
png output.png
quit
```

### Python 스크립트

```python
# script.py
from pymol import cmd

cmd.load("structure.pdb")
cmd.hide("everything")
cmd.show("cartoon")
cmd.spectrum("count", "rainbow")
cmd.orient()
cmd.ray(1920, 1080)
cmd.png("output.png")
```

### Python API

```python
from pymol import cmd

# 명령 실행
cmd.do("load structure.pdb")

# 직접 호출
cmd.load("structure.pdb")
cmd.select("active", "resi 100-120")
cmd.show("sticks", "active")

# 정보 얻기
atoms = cmd.get_model("selection")
for atom in atoms.atom:
    print(atom.name, atom.resi, atom.coord)

# 좌표 얻기
coords = cmd.get_coords("selection")

# 거리 얻기
d = cmd.get_distance("/prot/A/10/CA", "/prot/A/20/CA")
```

### 사용자 정의 함수

```python
from pymol import cmd

def my_highlight(selection="all"):
    """잔기 하이라이트"""
    cmd.show("cartoon", "all")
    cmd.show("sticks", selection)
    cmd.color("yellow", selection)
    cmd.zoom(selection, 5)

# PyMOL에 등록
cmd.extend("highlight", my_highlight)

# 사용
# PyMOL> highlight resi 100-120
```

---

## 고급 기능

### 표면 계산

```python
# 분자 표면
show surface, protein

# 전기적 표면 (APBS 필요)
# 외부 도구로 .dx 파일 생성 후
load electrostatics.dx, emap
ramp_new eramp, emap, [-5, 0, 5]
set surface_color, eramp, protein
```

### 등고선/메쉬

```python
# 전자 밀도 맵
load map.ccp4, emap
isomesh mesh1, emap, 1.5          # 1.5σ 레벨
isomesh mesh2, emap, 3.0          # 3.0σ 레벨

# 스타일
color blue, mesh1
set mesh_width, 0.5
```

### 대칭 확장

```python
# 결정학적 대칭 mates
symexp prefix, object, selection, cutoff
symexp sym, protein, all, 5       # 5Å 이내 대칭 복사체
```

### 스테레오 뷰

```python
# 스테레오 모드
stereo on                 # 기본
stereo crosseye           # 교차시
stereo walleye           # 평행시
stereo quadbuffer        # 3D 안경 (하드웨어 필요)
stereo off
```

### 라벨링

```python
# 잔기 라벨
label n. CA, "%s-%s" % (resn, resi)

# 스타일
set label_color, black
set label_size, 14
set label_font_id, 7

# 위치 조정
set label_position, [0, 0, 2]
```

### 세션 저장

```python
# 전체 상태 저장
save session.pse

# 로드
load session.pse
```

---

## 명령어 레퍼런스

### 입출력

| 명령어 | 설명 |
|--------|------|
| `load` | 파일 로드 |
| `save` | 파일 저장 |
| `fetch` | PDB에서 다운로드 |
| `delete` | 객체 삭제 |
| `reinitialize` | 초기화 |

### 표현

| 명령어 | 설명 |
|--------|------|
| `show` | 표현 켜기 |
| `hide` | 표현 끄기 |
| `as` | 표현 교체 |
| `cartoon` | cartoon 스타일 |
| `label` | 라벨 표시 |

### 색상

| 명령어 | 설명 |
|--------|------|
| `color` | 색상 설정 |
| `spectrum` | 스펙트럼 색상 |
| `set_color` | 색상 정의 |
| `bg_color` | 배경색 |
| `recolor` | 다시 색칠 |

### 뷰

| 명령어 | 설명 |
|--------|------|
| `zoom` | 줌 |
| `center` | 중심 설정 |
| `orient` | 방향 정렬 |
| `origin` | 회전 중심 |
| `turn` | 회전 |
| `move` | 이동 |
| `clip` | 클리핑 |
| `view` | 뷰 저장/복원 |
| `scene` | 씬 관리 |

### 정렬

| 명령어 | 설명 |
|--------|------|
| `align` | 서열 기반 정렬 |
| `super` | 구조 기반 정렬 |
| `cealign` | CE 정렬 |
| `fit` | 좌표 피팅 |
| `pair_fit` | 원자쌍 피팅 |
| `rms` | RMSD 계산 |
| `rms_cur` | 현재 RMSD |

### 측정

| 명령어 | 설명 |
|--------|------|
| `distance` | 거리 측정 |
| `angle` | 각도 측정 |
| `dihedral` | 이면각 측정 |
| `get_area` | 표면적 |

### 편집

| 명령어 | 설명 |
|--------|------|
| `remove` | 원자 삭제 |
| `create` | 객체 생성 |
| `extract` | 추출 |
| `alter` | 속성 변경 |
| `h_add` | 수소 추가 |
| `rotate` | 회전 |
| `translate` | 이동 |
| `bond` / `unbond` | 결합 수정 |

### 렌더링

| 명령어 | 설명 |
|--------|------|
| `ray` | 레이트레이싱 |
| `draw` | 빠른 그리기 |
| `png` | PNG 저장 |
| `mpng` | 무비 PNG |

### 무비

| 명령어 | 설명 |
|--------|------|
| `mset` | 프레임 설정 |
| `mview` | 뷰 키프레임 |
| `mplay` / `mstop` | 재생/정지 |
| `frame` | 프레임 이동 |

### 설정

| 명령어 | 설명 |
|--------|------|
| `set` | 설정 변경 |
| `get` | 설정 조회 |
| `unset` | 설정 해제 |

---

## 유용한 팁

### 출판용 이미지

```python
# 고품질 설정
set ray_shadows, off
set antialias, 2
set ray_trace_mode, 1
bg_color white

# 렌더링
ray 4000, 3000
png figure.png, dpi=300
```

### 리간드-단백질 시각화

```python
# 기본 설정
hide everything
show cartoon, polymer
show sticks, organic
show sticks, byres organic around 4
color gray, polymer
util.cbay organic
distance hbonds, organic, byres organic around 4, mode=2
zoom organic, 8
```

### 여러 구조 비교

```python
# 로드
fetch 1abc 2def 3ghi

# 정렬
align 2def, 1abc
align 3ghi, 1abc

# 색상
color red, 1abc
color green, 2def
color blue, 3ghi

# 투명도
set cartoon_transparency, 0.5
```

---

## 펩타이드 리간드 설계 응용

> 이 섹션은 SSTR2, PSMA, FAP 등 수용체 타겟에 대한 펩타이드 리간드 설계 과정에서 PyMOL을 활용하는 방법을 다룹니다.

### Pharmacophore 시각화

바인딩 포켓 표면 위에 리간드의 약효단(수소결합 donor/acceptor, 방향족, 양전하)을 표시합니다.

```python
# 수용체 표면 + 리간드 약효단 표시
hide everything
show cartoon, chain B             # SSTR2 수용체
show surface, chain B
set transparency, 0.7, chain B

show sticks, chain A              # 펩타이드 리간드 (Somatostatin)
util.cbay chain A                 # 탄소=노란색 (리간드 강조)

# 수소결합 donor/acceptor 표시 (극성 접촉)
distance hbonds, chain A, chain B, mode=2
set dash_color, yellow, hbonds
set dash_width, 2.5
set dash_gap, 0.2

# 방향족 잔기 강조 (Phe, Trp, Tyr)
select aromatics, chain A and resn PHE+TRP+TYR
show spheres, aromatics and name CG+CD1+CD2+CE1+CE2+CZ+CH2+NE1
set sphere_scale, 0.3, aromatics

# 양전하 잔기 강조 (Lys, Arg)
select positive, chain A and resn LYS+ARG
color blue, positive and name NZ+NH1+NH2+NE
show spheres, positive and name NZ+NH1+NH2+NE
set sphere_scale, 0.4, positive

# 바인딩 포켓 잔기 라벨
select pocket, chain B within 5 of chain A
label pocket and name CA, "%s%s" % (resn, resi)
set label_size, 12
set label_color, white
```

### 도킹 포즈 비교

DiffDock, FlexPepDock 등에서 생성한 여러 도킹 포즈를 중첩하여 비교합니다.

```python
# 여러 도킹 포즈 로드
load sstr2_receptor.pdb, receptor
load pose_1.pdb, pose1
load pose_2.pdb, pose2
load pose_3.pdb, pose3

# 수용체에 정렬
align pose1, receptor
align pose2, receptor
align pose3, receptor

# 수용체: 회색 cartoon
hide everything
show cartoon, receptor
color gray80, receptor

# 포즈별 색상 (confidence/score 기반)
show sticks, pose1
show sticks, pose2
show sticks, pose3
color tv_red, pose1       # 최고 confidence
color tv_orange, pose2    # 중간
color tv_blue, pose3      # 낮은

# 공통 바인딩 부위 하이라이트
select common_site, receptor within 4 of (pose1 or pose2 or pose3)
show sticks, common_site
color palegreen, common_site

# 포즈 간 RMSD 계산
rms_cur pose2, pose1
rms_cur pose3, pose1

zoom pose1 or pose2 or pose3, 8
```

#### Confidence 기반 스펙트럼 색상

```python
# DiffDock confidence를 B-factor에 매핑하여 스펙트럼 표시
# (사전에 PDB B-factor를 confidence로 설정한 경우)
spectrum b, red_white_blue, pose1
# 낮은 confidence=빨강, 높은 confidence=파랑
```

### 킬레이터-펩타이드 복합체 시각화

방사성 의약품에서 DOTA/NOTA 킬레이터 + 링커 + 펩타이드 구조를 시각화합니다.

```python
# 킬레이터-링커-펩타이드 복합체 로드
load DOTA_octreotide.pdb, complex

# 구성요소별 분리 표시
# 가정: 킬레이터=잔기 1, 링커=잔기 2-3, 펩타이드=잔기 4-11
hide everything

# 킬레이터 (DOTA/NOTA) -- ball-and-stick
select chelator, resi 1
show sticks, chelator
show spheres, chelator and elem Ga+Lu+Y+In+Cu  # 금속 이온
set sphere_scale, 0.5, chelator
color magenta, chelator
color orange, chelator and elem Ga+Lu+Y+In+Cu

# 링커 -- 투명 sticks
select linker, resi 2-3
show sticks, linker
color gray50, linker
set stick_transparency, 0.3, linker

# 펩타이드 -- cartoon + sticks
select peptide, resi 4-11
show cartoon, peptide
show sticks, peptide and sidechain
util.cbac peptide            # 탄소=청록색

# 거리 측정 (금속-배위 원자)
distance metal_coord, chelator and elem Lu, chelator and elem N+O, mode=0
set dash_color, orange, metal_coord
set dash_width, 3.0

# 전체 구조 줌
zoom complex, 5
```

### B-factor / pLDDT 신뢰도 맵

ESMFold, AlphaFold3 결과의 신뢰도를 색상 스펙트럼으로 표현합니다.

```python
# AlphaFold3/ESMFold 결과 로드 (B-factor에 pLDDT 저장됨)
load esmfold_predicted.pdb, predicted

# pLDDT 스펙트럼 표시
hide everything
show cartoon, predicted

# pLDDT 색상 (파랑=높음, 빨강=낮음)
spectrum b, red_white_blue, predicted, minimum=0, maximum=100

# 신뢰도 범위별 세분화
select very_high, predicted and b > 90
select high, predicted and b > 70 and b <= 90
select medium, predicted and b > 50 and b <= 70
select low, predicted and b <= 50

color blue, very_high
color cyan, high
color yellow, medium
color red, low

# 신뢰도 낮은 영역 표시
show sticks, low
label low and name CA, "pLDDT=%4.1f" % b
```

#### AlphaFold3 복합체 ipTM 분석

```python
# AlphaFold3 복합체 (수용체 + 펩타이드)
load fold_test1_model_0.pdb, complex

# 체인별 pLDDT 확인
spectrum b, red_white_blue, chain A   # 펩타이드
spectrum b, red_white_blue, chain B   # 수용체

# 인터페이스 잔기만 하이라이트
select interface_A, chain A within 5 of chain B
select interface_B, chain B within 5 of chain A
show sticks, interface_A or interface_B

# pLDDT가 높은 인터페이스 = 신뢰할 수 있는 접촉
select confident_contacts, (interface_A or interface_B) and b > 70
color green, confident_contacts
```

### 배치 렌더링 스크립트

여러 PDB 파일을 자동으로 렌더링하여 비교 이미지를 생성합니다.

#### Python 배치 스크립트

```python
#!/usr/bin/env python3
"""batch_render.py -- 여러 PDB를 동일 뷰로 렌더링"""
import glob
import subprocess

pdbs = sorted(glob.glob("results/sstr2_docking/arm3_denovo/esmfold_*.pdb"))

for pdb in pdbs:
    name = pdb.replace(".pdb", "")
    cmd = f"""pymol -c -d "
        load {pdb};
        hide everything;
        show cartoon;
        spectrum b, red_white_blue, minimum=0, maximum=100;
        orient;
        set ray_opaque_background, 1;
        bg_color white;
        ray 1920, 1080;
        png {name}.png, dpi=300;
        quit
    " """
    subprocess.run(cmd, shell=True)
```

#### PML 배치 스크립트

```python
# batch_render.pml -- PyMOL 내부에서 실행
import glob, os

files = glob.glob("results/sstr2_docking/arm3_denovo/esmfold_*.pdb")
for f in files:
    name = os.path.basename(f).replace(".pdb", "")
    cmd.load(f, name)
    cmd.hide("everything", name)
    cmd.show("cartoon", name)
    cmd.spectrum("b", "red_white_blue", name, minimum=0, maximum=100)
    cmd.orient(name)
    cmd.ray(1920, 1080)
    cmd.png(f"renders/{name}.png", dpi=300)
    cmd.delete(name)
```

#### 비교 패널 (모든 포즈를 하나의 이미지로)

```python
# 모든 de novo 펩타이드를 한 뷰에 중첩
import glob

files = sorted(glob.glob("esmfold_bb*.pdb"))
colors = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "magenta",
          "salmon", "lime", "teal", "slate", "violet", "pink", "wheat", "olive"]

for i, f in enumerate(files):
    name = f"pep_{i}"
    cmd.load(f, name)
    cmd.show("cartoon", name)
    cmd.color(colors[i % len(colors)], name)
    if i > 0:
        cmd.align(name, "pep_0")

cmd.zoom("all", 5)
cmd.bg_color("white")
cmd.ray(2400, 1800)
cmd.png("all_peptides_overlay.png", dpi=300)
```

### Electrostatic Surface (APBS 연동)

바인딩 포켓의 정전기 표면을 계산하여 전하 분포를 분석합니다.

```python
# 1. PQR 파일 생성 (pdb2pqr 또는 PDB2PQR 웹서버)
# bash: pdb2pqr --ff=AMBER sstr2_receptor.pdb sstr2_receptor.pqr

# 2. APBS 실행
# bash: apbs apbs_input.in
# 출력: sstr2_receptor.dx (정전기 포텐셜 맵)

# 3. PyMOL에서 로드 및 표시
load sstr2_receptor.pdb, receptor
load sstr2_receptor.dx, emap

# 정전기 표면 색상 램프
ramp_new eramp, emap, [-5, 0, 5], [red, white, blue]

# 표면에 적용
show surface, receptor
set surface_color, eramp, receptor
set transparency, 0.1, receptor

# 리간드 포즈 위에 표면 표시
show sticks, chain A
zoom chain A, 10
```

#### PDB2PQR + APBS 자동화

```bash
#!/bin/bash
# electrostatics.sh -- 정전기 맵 자동 생성
PDB="sstr2_receptor.pdb"
PQR="${PDB%.pdb}.pqr"
DX="${PDB%.pdb}.dx"

# PQR 생성
pdb2pqr --ff=AMBER --apbs-input="apbs.in" "$PDB" "$PQR"

# APBS 실행
apbs apbs.in

# PyMOL 시각화
pymol -c -d "
load $PDB;
load $DX, emap;
ramp_new eramp, emap, [-5,0,5], [red,white,blue];
show surface;
set surface_color, eramp;
ray 1920, 1080;
png electrostatic_surface.png;
quit
"
```

### 펩타이드-수용체 인터페이스 분석

```python
# 인터페이스 상호작용 종합 분석
load sstr2_complex.pdb

# 1. 수소결합 네트워크
distance hbonds, chain A, chain B, mode=2
set dash_color, yellow, hbonds

# 2. 소수성 접촉
select hydrophobic_A, chain A and resn ALA+VAL+LEU+ILE+PHE+TRP+MET+PRO
select hydrophobic_B, chain B within 4 of hydrophobic_A
show sticks, hydrophobic_A or hydrophobic_B
color orange, hydrophobic_A
color tv_orange, hydrophobic_B

# 3. 염다리 (salt bridge)
select pos_A, chain A and (resn LYS and name NZ) or (resn ARG and name NH1+NH2+NE)
select neg_B, chain B and (resn ASP and name OD1+OD2) or (resn GLU and name OE1+OE2)
distance salt_bridges, pos_A, neg_B, mode=0, cutoff=4.0
set dash_color, cyan, salt_bridges
set dash_width, 3.0

# 4. 카이-파이 상호작용 (cation-pi)
select cation_A, chain A and (resn LYS and name NZ) or (resn ARG and name CZ)
select pi_B, chain B and resn PHE+TYR+TRP and name CG+CD1+CD2+CE1+CE2+CZ
distance cation_pi, cation_A, pi_B, mode=0, cutoff=6.0
set dash_color, magenta, cation_pi

# 5. 접촉 면적 (Buried Surface Area)
# PyMOL API
from pymol import cmd
cmd.get_area("chain A")                    # 총 SASA
cmd.get_area("chain A and interface_A")    # 인터페이스 SASA

# 6. 줌 + 렌더링
zoom chain A, 8
bg_color white
ray 2400, 1800
png interface_analysis.png, dpi=300
```

### PyMOL + Python API 자동화 예제

```python
#!/usr/bin/env python3
"""
analyze_docking_results.py
DiffDock 결과를 자동 분석하여 이미지 + 보고서 생성
"""
from pymol import cmd
import json
import os

def analyze_pose(receptor_pdb, ligand_sdf, output_dir, pose_name="pose"):
    """단일 도킹 포즈 분석 및 이미지 생성"""
    cmd.reinitialize()
    cmd.load(receptor_pdb, "receptor")
    cmd.load(ligand_sdf, "ligand")

    # 기본 표현
    cmd.hide("everything")
    cmd.show("cartoon", "receptor")
    cmd.color("gray80", "receptor")
    cmd.show("sticks", "ligand")
    cmd.util.cbay("ligand")

    # 바인딩 사이트 표시
    cmd.select("binding_site", "receptor within 5 of ligand")
    cmd.show("sticks", "binding_site")
    cmd.show("surface", "binding_site")
    cmd.set("transparency", 0.6, "binding_site")

    # 상호작용
    cmd.distance("hbonds", "ligand", "binding_site", mode=2)

    # 렌더링
    cmd.zoom("ligand", 8)
    cmd.bg_color("white")
    cmd.ray(1920, 1080)
    cmd.png(os.path.join(output_dir, f"{pose_name}.png"), dpi=300)

    # 정보 수집
    info = {
        "name": pose_name,
        "binding_residues": [],
        "hbond_count": 0,
    }

    # 바인딩 잔기 목록
    model = cmd.get_model("binding_site and name CA")
    for atom in model.atom:
        info["binding_residues"].append(f"{atom.chain}{atom.resi}({atom.resn})")

    return info

# 사용 예
if __name__ == "__main__":
    results = []
    for i, sdf in enumerate(sorted(os.listdir("arm1_smallmol/"))):
        if sdf.endswith(".sdf"):
            info = analyze_pose(
                "sstr2_receptor.pdb",
                f"arm1_smallmol/{sdf}",
                "renders/",
                f"arm1_pose_{i}"
            )
            results.append(info)

    with open("renders/analysis_report.json", "w") as f:
        json.dump(results, f, indent=2)
```

---

## 참고 자료

- **공식 문서**: https://pymol.org/dokuwiki/
- **명령어 레퍼런스**: https://pymol.org/pymol-command-ref.html
- **PyMOL Wiki**: https://pymolwiki.org/
- **GitHub**: https://github.com/schrodinger/pymol-open-source
- **APBS**: https://www.poissonboltzmann.org/
- **PDB2PQR**: https://pdb2pqr.readthedocs.io/
