load '/home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/sst14_agentic_mutdock/baseline_refined.pdb', receptor
bg_color white
hide everything
show cartoon, receptor
color slate, receptor
load '/home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle/sst14_agentic_mutdock/iter_05/cand_002.pdb', cand1
show cartoon, cand1
color red, cand1
orient
png /home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle/sst14_agentic_mutdock/renders/overview.png, width=1200, height=900, dpi=150, ray=1
zoom polymer and (byres (receptor within 8 of cand1))
png /home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle/sst14_agentic_mutdock/renders/closeup.png, width=1200, height=900, dpi=150, ray=1
show sticks, byres (receptor within 5 of cand1)
show sticks, byres (cand1 within 5 of receptor)
png /home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle/sst14_agentic_mutdock/renders/interface.png, width=1200, height=900, dpi=150, ray=1
hide sticks
show surface, receptor
set transparency, 0.3, receptor
png /home/helloworld/Documents/workspace/repos/PRST_N_FM/AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/runs/pyrosetta_flow/demo_5cycle/sst14_agentic_mutdock/renders/electrostatics.png, width=1200, height=900, dpi=150, ray=1
quit
