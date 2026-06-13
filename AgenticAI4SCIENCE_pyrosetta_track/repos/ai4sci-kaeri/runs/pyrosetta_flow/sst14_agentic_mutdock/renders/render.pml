load '/home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/data/somatostatin_receptor/SSTR2_SST14_complex_boltz_1.pdb', receptor
bg_color white
hide everything
show cartoon, receptor
color slate, receptor
load '/home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/iter_20/cand_008.pdb', cand1
show cartoon, cand1
color red, cand1
load '/home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/iter_20/cand_002.pdb', cand2
show cartoon, cand2
color orange, cand2
orient
png /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/renders/overview.png, width=1200, height=900, dpi=150, ray=1
zoom polymer and (byres (receptor within 8 of cand1))
png /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/renders/closeup.png, width=1200, height=900, dpi=150, ray=1
show sticks, byres (receptor within 5 of cand1)
show sticks, byres (cand1 within 5 of receptor)
png /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/renders/interface.png, width=1200, height=900, dpi=150, ray=1
hide sticks
show surface, receptor
set transparency, 0.3, receptor
png /home/dongjukim/Documents/workspace/tmp/SST14-M_scr/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/renders/electrostatics.png, width=1200, height=900, dpi=150, ray=1
quit
