# PyMOL 4-Panel Auto-Render: iter14_cand005
# 생성: 2026-06-10T16:43:23.534540
reinitialize

# --- 구조 로드 ---
load data/somatostatin_receptor/SSTR2_SST14_complex_boltz_1.pdb, receptor
load , peptide

# 기본 스타일
bg_color white
set ray_opaque_background, off
set antialias, 2
set ray_trace_mode, 1

# 수용체: 회색 cartoon
color gray70, receptor
show cartoon, receptor
hide lines, receptor

# 펩타이드: 청색 cartoon + stick
color marine, peptide
show cartoon, peptide
show sticks, peptide
set stick_radius, 0.15

# 수용체-펩타이드 정렬
align peptide, receptor

# ================================================================
# Panel 1: Overview (전체 복합체 cartoon)
# ================================================================
zoom all
set_view [\
    1.0, 0.0, 0.0, \
    0.0, 1.0, 0.0, \
    0.0, 0.0, 1.0, \
    0.0, 0.0, -80.0, \
    0.0, 0.0, 0.0, 40.0, 200.0, -20.0]
ray 1200, 900
png /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/iter_14/07_viz/iter14_cand005_1_overview.png, dpi=150

# ================================================================
# Panel 2: Closeup (결합 포켓 zoom)
# ================================================================
hide everything
show cartoon, receptor
show sticks, peptide
show cartoon, peptide
# 펩타이드 주변 8A 이내 수용체 residue 표시
select pocket_res, receptor within 8 of peptide
show sticks, pocket_res
color yellow, pocket_res
zoom peptide, 8
ray 1200, 900
png /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/iter_14/07_viz/iter14_cand005_2_closeup.png, dpi=150

# ================================================================
# Panel 3: Interface contacts (H-bond, salt bridge, hydrophobic)
# ================================================================
hide everything
show cartoon, receptor
show cartoon, peptide
show sticks, peptide
show sticks, pocket_res
# H-bonds
distance hbonds, receptor, peptide, 3.5, mode=2
color yellow, hbonds
# salt bridges
distance salt_bridges, receptor, peptide, 5.0, mode=1
color red, salt_bridges
set dash_width, 3.0
set label_size, 12
zoom peptide, 10
ray 1200, 900
png /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/iter_14/07_viz/iter14_cand005_3_interface.png, dpi=150

# ================================================================
# Panel 4: Electrostatics (APBS surface)
# ================================================================
hide everything
show surface, receptor
show cartoon, peptide
show sticks, peptide
# APBS 정전기 포텐셜 계산 (PyMOL APBS 플러그인 필요)
# apbs_run receptor
# ramp_new e_lvl, apbs_map, [-5, 0, 5], [red, white, blue]
# set surface_color, e_lvl, receptor
# --- APBS 미설치 환경 대안: 소수성 표면 ---
spectrum count, blue_white_red, receptor, minimum=0, maximum=10
set transparency, 0.3, receptor
zoom peptide, 12
ray 1200, 900
png /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/iter_14/07_viz/iter14_cand005_4_electrostatics.png, dpi=150

# ================================================================
# 세션 저장
# ================================================================
save /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/iter_14/07_viz/iter14_cand005.pse