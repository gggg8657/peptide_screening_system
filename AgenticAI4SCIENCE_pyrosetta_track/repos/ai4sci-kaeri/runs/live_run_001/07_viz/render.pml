load /Users/kimsoyeon/ai4sci_kaeri/PRST_N_FM/results/sstr2_docking/sstr2_receptor.pdb, receptor
bg_color white
hide everything
show cartoon, receptor
color slate, receptor
load /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/06_rosetta/refined_var_090.pdb, cand1
show cartoon, cand1
color red, cand1
load /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/06_rosetta/refined_var_111.pdb, cand2
show cartoon, cand2
color orange, cand2
load /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/06_rosetta/refined_var_102.pdb, cand3
show cartoon, cand3
color yellow, cand3
load /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/06_rosetta/refined_var_082.pdb, cand4
show cartoon, cand4
color green, cand4
load /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/06_rosetta/refined_var_115.pdb, cand5
show cartoon, cand5
color cyan, cand5
orient
png /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/07_viz/overview.png, width=1200, height=900, dpi=150, ray=1
zoom polymer and (byres (receptor within 8 of cand1))
png /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/07_viz/closeup.png, width=1200, height=900, dpi=150, ray=1
show sticks, byres (receptor within 5 of cand1)
show sticks, byres (cand1 within 5 of receptor)
png /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/07_viz/interface.png, width=1200, height=900, dpi=150, ray=1
hide sticks
show surface, receptor
set transparency, 0.3, receptor
png /Users/kimsoyeon/ai4sci_kaeri/runs/live_run_001/07_viz/electrostatics.png, width=1200, height=900, dpi=150, ray=1
quit
