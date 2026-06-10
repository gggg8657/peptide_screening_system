load '/home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pos5_6_11_optimization/p5F_p6D_p11S_AGCKFDFWKTSTSC/refined.pdb', receptor
bg_color white
hide everything
show cartoon, receptor
color slate, receptor
load '/home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle_20260402/sst14_agentic_mutdock/iter_05/cand_002.pdb', cand1
show cartoon, cand1
color red, cand1
load '/home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle_20260402/sst14_agentic_mutdock/iter_05/cand_005.pdb', cand2
show cartoon, cand2
color orange, cand2
load '/home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle_20260402/sst14_agentic_mutdock/iter_05/cand_003.pdb', cand3
show cartoon, cand3
color yellow, cand3
orient
png /home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle_20260402/sst14_agentic_mutdock/renders/overview.png, width=1200, height=900, dpi=150, ray=1
zoom polymer and (byres (receptor within 8 of cand1))
png /home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle_20260402/sst14_agentic_mutdock/renders/closeup.png, width=1200, height=900, dpi=150, ray=1
show sticks, byres (receptor within 5 of cand1)
show sticks, byres (cand1 within 5 of receptor)
png /home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle_20260402/sst14_agentic_mutdock/renders/interface.png, width=1200, height=900, dpi=150, ray=1
hide sticks
show surface, receptor
set transparency, 0.3, receptor
png /home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle_20260402/sst14_agentic_mutdock/renders/electrostatics.png, width=1200, height=900, dpi=150, ray=1
quit
