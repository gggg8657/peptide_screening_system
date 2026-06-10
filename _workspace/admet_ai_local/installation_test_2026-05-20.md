# ADMET-AI Layer 3 installation/inference test (2026-05-20)

## Summary

- Status: SUCCESS for isolated install/import and CPU inference.
- No local training was performed. The run used the learned ADMET-AI package/model only.
- Isolation directory: `_workspace/admet_ai_local/`.
- Environment: `_workspace/admet_ai_local/.conda_env` (Python 3.11).
- ADMET-AI package path: `/home/dongjukim/Documents/workspace/repos/SST14-M_scr/_workspace/admet_ai_local/admet_ai/admet_ai`.
- Model init time: `0.14` seconds.
- Raw full endpoint JSON: `_workspace/admet_ai_local/layer3_prst001_004_octreotide_raw.json`.
- Provider stderr/log: `_workspace/admet_ai_local/layer3_prst001_004_octreotide_stderr.txt`.
- CUDA collision avoidance: inference command used `CUDA_VISIBLE_DEVICES=""`; provider log reported `GPU available: False, used: False`.

## Mandatory Guard

- H-06 extrapolation warning: ADMET-AI is a learned small-molecule ADMET model. PRST cyclic peptides, large peptides, Octreotide-like cyclic peptides, and DOTA/radiometal-chelator conjugates are outside the validated decision domain. All outputs below are raw ADMET-AI endpoint outputs for triage only; recommended_for_decision=False.
- `extrapolation_warning=True` for every compound.
- `recommended_for_decision=False` for every compound.
- DOTA handling remains OOD. This report does not upgrade DOTA-conjugate decision confidence.

## Inputs

- PRST-001: AGCKNIIWKTITSC
- PRST-002: AGCKNFIWKTITSC
- PRST-003: AGCRNFIWKTITSC
- PRST-004: AICKNFIWKTITSC
- Octreotide: PubChem CID 448601 SMILES supplied in task

SMILES notes: PRST-001~004 SMILES were generated in the ADMET-AI conda env with `pyrosetta_flow.smiles_converter.sequence_to_smiles()` from `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/pyrosetta_flow/smiles_converter.py`. Octreotide used the PubChem CID 448601 SMILES supplied in the task.

## Run Status

| compound | ok | endpoints | predict_sec | error |
|---|---:|---:|---:|---|
| PRST-001 | True | 104 | 0.301 |  |
| PRST-002 | True | 104 | 0.239 |  |
| PRST-003 | True | 104 | 0.278 |  |
| PRST-004 | True | 104 | 0.285 |  |
| Octreotide | True | 104 | 0.201 |  |

## All Raw Endpoint Outputs

### PRST-001

- extrapolation_warning: `True`
- recommended_for_decision: `False`

| endpoint | value |
|---|---:|
| `molecular_weight` | 1535.858 |
| `logP` | -5.5034 |
| `hydrogen_bond_acceptors` | 23 |
| `hydrogen_bond_donors` | 22 |
| `Lipinski` | 1 |
| `QED` | 0.0308572486957 |
| `stereo_centers` | 18 |
| `tpsa` | 613.23 |
| `PAINS_alert` | 0 |
| `BRENK_alert` | 2 |
| `NIH_alert` | 0 |
| `AMES` | 0.46702259779 |
| `BBB_Martins` | 0.00047808457748 |
| `Bioavailability_Ma` | 0.00988911278546 |
| `CYP1A2_Veith` | 1.8690076331e-07 |
| `CYP2C19_Veith` | 0.0521029904485 |
| `CYP2C9_Substrate_CarbonMangels` | 2.88525575343e-06 |
| `CYP2C9_Veith` | 0.00987055152655 |
| `CYP2D6_Substrate_CarbonMangels` | 0.000116549897939 |
| `CYP2D6_Veith` | 0.108343079686 |
| `CYP3A4_Substrate_CarbonMangels` | 0.0997751131654 |
| `CYP3A4_Veith` | 0.319798856974 |
| `Carcinogens_Lagunin` | 0.00278102001175 |
| `ClinTox` | 0.0781800746918 |
| `DILI` | 0.115503452718 |
| `HIA_Hou` | 9.52253612923e-05 |
| `NR-AR-LBD` | 0.0159715861082 |
| `NR-AR` | 0.0838420763612 |
| `NR-AhR` | 3.02392818412e-05 |
| `NR-Aromatase` | 0.00982082728297 |
| `NR-ER-LBD` | 0.291745483875 |
| `NR-ER` | 0.375054270029 |
| `NR-PPAR-gamma` | 0.000462622701889 |
| `PAMPA_NCATS` | 2.42347396124e-05 |
| `Pgp_Broccatelli` | 0.0248076356947 |
| `SR-ARE` | 0.198220640421 |
| `SR-ATAD5` | 0.0742458701134 |
| `SR-HSE` | 0.000537652056664 |
| `SR-MMP` | 0.00333082443103 |
| `SR-p53` | 0.298776805401 |
| `Skin_Reaction` | 0.167309850454 |
| `hERG` | 0.484513372183 |
| `Caco2_Wang` | -9.80484008789 |
| `Clearance_Hepatocyte_AZ` | -31.2010097504 |
| `Clearance_Microsome_AZ` | 156.153335571 |
| `Half_Life_Obach` | -11.3150987625 |
| `HydrationFreeEnergy_FreeSolv` | -63.671459198 |
| `LD50_Zhu` | 3.89699864388 |
| `Lipophilicity_AstraZeneca` | -0.20486882329 |
| `PPBR_AZ` | 67.0242385864 |
| `Solubility_AqSolDB` | -3.16210508347 |
| `VDss_Lombardo` | -3.71293115616 |
| `molecular_weight_drugbank_approved_percentile` | 98.9455184534 |
| `logP_drugbank_approved_percentile` | 4.49912126538 |
| `hydrogen_bond_acceptors_drugbank_approved_percentile` | 98.7873462214 |
| `hydrogen_bond_donors_drugbank_approved_percentile` | 99.3673110721 |
| `Lipinski_drugbank_approved_percentile` | 2.54833040422 |
| `QED_drugbank_approved_percentile` | 1.93321616872 |
| `stereo_centers_drugbank_approved_percentile` | 98.8400702988 |
| `tpsa_drugbank_approved_percentile` | 99.1212653779 |
| `PAINS_alert_drugbank_approved_percentile` | 47.5922671353 |
| `BRENK_alert_drugbank_approved_percentile` | 87.9261862917 |
| `NIH_alert_drugbank_approved_percentile` | 37.1880492091 |
| `AMES_drugbank_approved_percentile` | 76.2741652021 |
| `BBB_Martins_drugbank_approved_percentile` | 0.738137082601 |
| `Bioavailability_Ma_drugbank_approved_percentile` | 1.4762741652 |
| `CYP1A2_Veith_drugbank_approved_percentile` | 1.68717047452 |
| `CYP2C19_Veith_drugbank_approved_percentile` | 40.5975395431 |
| `CYP2C9_Substrate_CarbonMangels_drugbank_approved_percentile` | 1.26537785589 |
| `CYP2C9_Veith_drugbank_approved_percentile` | 31.6344463972 |
| `CYP2D6_Substrate_CarbonMangels_drugbank_approved_percentile` | 1.9683655536 |
| `CYP2D6_Veith_drugbank_approved_percentile` | 61.7574692443 |
| `CYP3A4_Substrate_CarbonMangels_drugbank_approved_percentile` | 15.2548330404 |
| `CYP3A4_Veith_drugbank_approved_percentile` | 75.1493848858 |
| `Carcinogens_Lagunin_drugbank_approved_percentile` | 2.67135325132 |
| `ClinTox_drugbank_approved_percentile` | 43.6203866432 |
| `DILI_drugbank_approved_percentile` | 21.4059753954 |
| `HIA_Hou_drugbank_approved_percentile` | 1.40597539543 |
| `NR-AR-LBD_drugbank_approved_percentile` | 60.3866432337 |
| `NR-AR_drugbank_approved_percentile` | 88.7170474517 |
| `NR-AhR_drugbank_approved_percentile` | 2.24956063269 |
| `NR-Aromatase_drugbank_approved_percentile` | 40.1054481547 |
| `NR-ER-LBD_drugbank_approved_percentile` | 95.3602811951 |
| `NR-ER_drugbank_approved_percentile` | 93.4270650264 |
| `NR-PPAR-gamma_drugbank_approved_percentile` | 11.9507908612 |
| `PAMPA_NCATS_drugbank_approved_percentile` | 1.230228471 |
| `Pgp_Broccatelli_drugbank_approved_percentile` | 40.0351493849 |
| `SR-ARE_drugbank_approved_percentile` | 61.3005272408 |
| `SR-ATAD5_drugbank_approved_percentile` | 82.0386643234 |
| `SR-HSE_drugbank_approved_percentile` | 6.53778558875 |
| `SR-MMP_drugbank_approved_percentile` | 23.9367311072 |
| `SR-p53_drugbank_approved_percentile` | 90.3339191564 |
| `Skin_Reaction_drugbank_approved_percentile` | 8.6467486819 |
| `hERG_drugbank_approved_percentile` | 61.8980667838 |
| `Caco2_Wang_drugbank_approved_percentile` | 1.12478031634 |
| `Clearance_Hepatocyte_AZ_drugbank_approved_percentile` | 3.1985940246 |
| `Clearance_Microsome_AZ_drugbank_approved_percentile` | 97.8207381371 |
| `Half_Life_Obach_drugbank_approved_percentile` | 6.95957820738 |
| `HydrationFreeEnergy_FreeSolv_drugbank_approved_percentile` | 1.12478031634 |
| `LD50_Zhu_drugbank_approved_percentile` | 97.8207381371 |
| `Lipophilicity_AstraZeneca_drugbank_approved_percentile` | 27.3462214411 |
| `PPBR_AZ_drugbank_approved_percentile` | 43.0931458699 |
| `Solubility_AqSolDB_drugbank_approved_percentile` | 49.0333919156 |
| `VDss_Lombardo_drugbank_approved_percentile` | 6.60808435852 |

### PRST-002

- extrapolation_warning: `True`
- recommended_for_decision: `False`

| endpoint | value |
|---|---:|
| `molecular_weight` | 1569.875 |
| `logP` | -5.3068 |
| `hydrogen_bond_acceptors` | 23 |
| `hydrogen_bond_donors` | 22 |
| `Lipinski` | 1 |
| `QED` | 0.0263629026016 |
| `stereo_centers` | 17 |
| `tpsa` | 613.23 |
| `PAINS_alert` | 0 |
| `BRENK_alert` | 2 |
| `NIH_alert` | 0 |
| `AMES` | 0.460692346096 |
| `BBB_Martins` | 0.000635788834188 |
| `Bioavailability_Ma` | 0.0121765229851 |
| `CYP1A2_Veith` | 3.30719728936e-07 |
| `CYP2C19_Veith` | 0.0416065566242 |
| `CYP2C9_Substrate_CarbonMangels` | 6.07727997703e-06 |
| `CYP2C9_Veith` | 0.00910662300885 |
| `CYP2D6_Substrate_CarbonMangels` | 0.000126352097141 |
| `CYP2D6_Veith` | 0.155784651637 |
| `CYP3A4_Substrate_CarbonMangels` | 0.125806599855 |
| `CYP3A4_Veith` | 0.384299129248 |
| `Carcinogens_Lagunin` | 0.00354033941403 |
| `ClinTox` | 0.106651164591 |
| `DILI` | 0.176677197218 |
| `HIA_Hou` | 0.000241537840338 |
| `NR-AR-LBD` | 0.0167282037437 |
| `NR-AR` | 0.0886437520385 |
| `NR-AhR` | 4.77637149743e-05 |
| `NR-Aromatase` | 0.0142042562366 |
| `NR-ER-LBD` | 0.25006878376 |
| `NR-ER` | 0.346420347691 |
| `NR-PPAR-gamma` | 0.00131892855279 |
| `PAMPA_NCATS` | 3.26569570461e-05 |
| `Pgp_Broccatelli` | 0.0601649172604 |
| `SR-ARE` | 0.189612656832 |
| `SR-ATAD5` | 0.0730998143554 |
| `SR-HSE` | 0.000898164114915 |
| `SR-MMP` | 0.00384702952579 |
| `SR-p53` | 0.290136903524 |
| `Skin_Reaction` | 0.149569317698 |
| `hERG` | 0.577107906342 |
| `Caco2_Wang` | -9.87022686005 |
| `Clearance_Hepatocyte_AZ` | -30.0494384766 |
| `Clearance_Microsome_AZ` | 156.072845459 |
| `Half_Life_Obach` | -5.86430549622 |
| `HydrationFreeEnergy_FreeSolv` | -64.1716079712 |
| `LD50_Zhu` | 3.79651641846 |
| `Lipophilicity_AstraZeneca` | -0.0855080112815 |
| `PPBR_AZ` | 71.6366271973 |
| `Solubility_AqSolDB` | -3.16706514359 |
| `VDss_Lombardo` | -5.21626424789 |
| `molecular_weight_drugbank_approved_percentile` | 99.0158172232 |
| `logP_drugbank_approved_percentile` | 4.67486818981 |
| `hydrogen_bond_acceptors_drugbank_approved_percentile` | 98.7873462214 |
| `hydrogen_bond_donors_drugbank_approved_percentile` | 99.3673110721 |
| `Lipinski_drugbank_approved_percentile` | 2.54833040422 |
| `QED_drugbank_approved_percentile` | 1.61687170475 |
| `stereo_centers_drugbank_approved_percentile` | 98.6643233743 |
| `tpsa_drugbank_approved_percentile` | 99.1212653779 |
| `PAINS_alert_drugbank_approved_percentile` | 47.5922671353 |
| `BRENK_alert_drugbank_approved_percentile` | 87.9261862917 |
| `NIH_alert_drugbank_approved_percentile` | 37.1880492091 |
| `AMES_drugbank_approved_percentile` | 75.6414762742 |
| `BBB_Martins_drugbank_approved_percentile` | 0.773286467487 |
| `Bioavailability_Ma_drugbank_approved_percentile` | 1.61687170475 |
| `CYP1A2_Veith_drugbank_approved_percentile` | 1.93321616872 |
| `CYP2C19_Veith_drugbank_approved_percentile` | 37.3989455185 |
| `CYP2C9_Substrate_CarbonMangels_drugbank_approved_percentile` | 1.44112478032 |
| `CYP2C9_Veith_drugbank_approved_percentile` | 30.158172232 |
| `CYP2D6_Substrate_CarbonMangels_drugbank_approved_percentile` | 2.00351493849 |
| `CYP2D6_Veith_drugbank_approved_percentile` | 68.0843585237 |
| `CYP3A4_Substrate_CarbonMangels_drugbank_approved_percentile` | 18.9455184534 |
| `CYP3A4_Veith_drugbank_approved_percentile` | 78.1370826011 |
| `Carcinogens_Lagunin_drugbank_approved_percentile` | 3.26889279438 |
| `ClinTox_drugbank_approved_percentile` | 52.5834797891 |
| `DILI_drugbank_approved_percentile` | 31.5992970123 |
| `HIA_Hou_drugbank_approved_percentile` | 1.86291739895 |
| `NR-AR-LBD_drugbank_approved_percentile` | 61.6168717047 |
| `NR-AR_drugbank_approved_percentile` | 89.5957820738 |
| `NR-AhR_drugbank_approved_percentile` | 2.74165202109 |
| `NR-Aromatase_drugbank_approved_percentile` | 45.3778558875 |
| `NR-ER-LBD_drugbank_approved_percentile` | 94.6572934974 |
| `NR-ER_drugbank_approved_percentile` | 92.6889279438 |
| `NR-PPAR-gamma_drugbank_approved_percentile` | 22.460456942 |
| `PAMPA_NCATS_drugbank_approved_percentile` | 1.33567662566 |
| `Pgp_Broccatelli_drugbank_approved_percentile` | 47.7680140598 |
| `SR-ARE_drugbank_approved_percentile` | 60.1054481547 |
| `SR-ATAD5_drugbank_approved_percentile` | 81.7926186292 |
| `SR-HSE_drugbank_approved_percentile` | 8.61159929701 |
| `SR-MMP_drugbank_approved_percentile` | 25.9050966608 |
| `SR-p53_drugbank_approved_percentile` | 90.0878734622 |
| `Skin_Reaction_drugbank_approved_percentile` | 7.48681898067 |
| `hERG_drugbank_approved_percentile` | 66.6080843585 |
| `Caco2_Wang_drugbank_approved_percentile` | 1.12478031634 |
| `Clearance_Hepatocyte_AZ_drugbank_approved_percentile` | 3.30404217926 |
| `Clearance_Microsome_AZ_drugbank_approved_percentile` | 97.8207381371 |
| `Half_Life_Obach_drugbank_approved_percentile` | 12.6537785589 |
| `HydrationFreeEnergy_FreeSolv_drugbank_approved_percentile` | 1.12478031634 |
| `LD50_Zhu_drugbank_approved_percentile` | 97.4692442882 |
| `Lipophilicity_AstraZeneca_drugbank_approved_percentile` | 29.2091388401 |
| `PPBR_AZ_drugbank_approved_percentile` | 47.7680140598 |
| `Solubility_AqSolDB_drugbank_approved_percentile` | 48.8224956063 |
| `VDss_Lombardo_drugbank_approved_percentile` | 3.05799648506 |

### PRST-003

- extrapolation_warning: `True`
- recommended_for_decision: `False`

| endpoint | value |
|---|---:|
| `molecular_weight` | 1597.889 |
| `logP` | -6.17253 |
| `hydrogen_bond_acceptors` | 23 |
| `hydrogen_bond_donors` | 24 |
| `Lipinski` | 1 |
| `QED` | 0.0153883695257 |
| `stereo_centers` | 17 |
| `tpsa` | 649.11 |
| `PAINS_alert` | 0 |
| `BRENK_alert` | 4 |
| `NIH_alert` | 0 |
| `AMES` | 0.462139546871 |
| `BBB_Martins` | 0.000274709193036 |
| `Bioavailability_Ma` | 0.00410112086684 |
| `CYP1A2_Veith` | 1.44454887163e-07 |
| `CYP2C19_Veith` | 0.0655547454953 |
| `CYP2C9_Substrate_CarbonMangels` | 1.07626135559e-06 |
| `CYP2C9_Veith` | 0.00927775166929 |
| `CYP2D6_Substrate_CarbonMangels` | 7.05754282535e-05 |
| `CYP2D6_Veith` | 0.134767025709 |
| `CYP3A4_Substrate_CarbonMangels` | 0.0478975772858 |
| `CYP3A4_Veith` | 0.27201372385 |
| `Carcinogens_Lagunin` | 0.00268511637114 |
| `ClinTox` | 0.055506773293 |
| `DILI` | 0.0572036914527 |
| `HIA_Hou` | 7.66202992963e-06 |
| `NR-AR-LBD` | 0.0108780842274 |
| `NR-AR` | 0.112958028913 |
| `NR-AhR` | 3.31417722919e-05 |
| `NR-Aromatase` | 0.00703904032707 |
| `NR-ER-LBD` | 0.299931108952 |
| `NR-ER` | 0.429896920919 |
| `NR-PPAR-gamma` | 0.000170736806467 |
| `PAMPA_NCATS` | 6.68807706461e-06 |
| `Pgp_Broccatelli` | 0.00762299448252 |
| `SR-ARE` | 0.0891193002462 |
| `SR-ATAD5` | 0.0484589934349 |
| `SR-HSE` | 0.000177854817593 |
| `SR-MMP` | 0.00106053811032 |
| `SR-p53` | 0.148188561201 |
| `Skin_Reaction` | 0.191393196583 |
| `hERG` | 0.518608212471 |
| `Caco2_Wang` | -10.9343738556 |
| `Clearance_Hepatocyte_AZ` | -30.1387901306 |
| `Clearance_Microsome_AZ` | 178.160827637 |
| `Half_Life_Obach` | -18.4860572815 |
| `HydrationFreeEnergy_FreeSolv` | -74.7023773193 |
| `LD50_Zhu` | 3.68509244919 |
| `Lipophilicity_AstraZeneca` | -0.661317706108 |
| `PPBR_AZ` | 54.7455825806 |
| `Solubility_AqSolDB` | -3.1970717907 |
| `VDss_Lombardo` | -5.88364553452 |
| `molecular_weight_drugbank_approved_percentile` | 99.086115993 |
| `logP_drugbank_approved_percentile` | 3.72583479789 |
| `hydrogen_bond_acceptors_drugbank_approved_percentile` | 98.7873462214 |
| `hydrogen_bond_donors_drugbank_approved_percentile` | 99.5782073814 |
| `Lipinski_drugbank_approved_percentile` | 2.54833040422 |
| `QED_drugbank_approved_percentile` | 0.632688927944 |
| `stereo_centers_drugbank_approved_percentile` | 98.6643233743 |
| `tpsa_drugbank_approved_percentile` | 99.2267135325 |
| `PAINS_alert_drugbank_approved_percentile` | 47.5922671353 |
| `BRENK_alert_drugbank_approved_percentile` | 99.2794376098 |
| `NIH_alert_drugbank_approved_percentile` | 37.1880492091 |
| `AMES_drugbank_approved_percentile` | 75.7820738137 |
| `BBB_Martins_drugbank_approved_percentile` | 0.597539543058 |
| `Bioavailability_Ma_drugbank_approved_percentile` | 0.843585237258 |
| `CYP1A2_Veith_drugbank_approved_percentile` | 1.65202108963 |
| `CYP2C19_Veith_drugbank_approved_percentile` | 44.6397188049 |
| `CYP2C9_Substrate_CarbonMangels_drugbank_approved_percentile` | 1.05448154657 |
| `CYP2C9_Veith_drugbank_approved_percentile` | 30.4042179262 |
| `CYP2D6_Substrate_CarbonMangels_drugbank_approved_percentile` | 1.61687170475 |
| `CYP2D6_Veith_drugbank_approved_percentile` | 65.6239015817 |
| `CYP3A4_Substrate_CarbonMangels_drugbank_approved_percentile` | 8.4007029877 |
| `CYP3A4_Veith_drugbank_approved_percentile` | 72.4077328647 |
| `Carcinogens_Lagunin_drugbank_approved_percentile` | 2.63620386643 |
| `ClinTox_drugbank_approved_percentile` | 34.446397188 |
| `DILI_drugbank_approved_percentile` | 11.0017574692 |
| `HIA_Hou_drugbank_approved_percentile` | 0.843585237258 |
| `NR-AR-LBD_drugbank_approved_percentile` | 49.6309314587 |
| `NR-AR_drugbank_approved_percentile` | 92.1968365554 |
| `NR-AhR_drugbank_approved_percentile` | 2.24956063269 |
| `NR-Aromatase_drugbank_approved_percentile` | 34.8330404218 |
| `NR-ER-LBD_drugbank_approved_percentile` | 95.4305799649 |
| `NR-ER_drugbank_approved_percentile` | 94.3057996485 |
| `NR-PPAR-gamma_drugbank_approved_percentile` | 6.81898066784 |
| `PAMPA_NCATS_drugbank_approved_percentile` | 0.984182776801 |
| `Pgp_Broccatelli_drugbank_approved_percentile` | 31.072056239 |
| `SR-ARE_drugbank_approved_percentile` | 40.8435852373 |
| `SR-ATAD5_drugbank_approved_percentile` | 77.0123022847 |
| `SR-HSE_drugbank_approved_percentile` | 3.90158172232 |
| `SR-MMP_drugbank_approved_percentile` | 13.2513181019 |
| `SR-p53_drugbank_approved_percentile` | 79.683655536 |
| `Skin_Reaction_drugbank_approved_percentile` | 10.5448154657 |
| `hERG_drugbank_approved_percentile` | 63.8664323374 |
| `Caco2_Wang_drugbank_approved_percentile` | 0.632688927944 |
| `Clearance_Hepatocyte_AZ_drugbank_approved_percentile` | 3.30404217926 |
| `Clearance_Microsome_AZ_drugbank_approved_percentile` | 98.5588752197 |
| `Half_Life_Obach_drugbank_approved_percentile` | 2.42530755712 |
| `HydrationFreeEnergy_FreeSolv_drugbank_approved_percentile` | 0.632688927944 |
| `LD50_Zhu_drugbank_approved_percentile` | 96.4850615114 |
| `Lipophilicity_AstraZeneca_drugbank_approved_percentile` | 21.4762741652 |
| `PPBR_AZ_drugbank_approved_percentile` | 32.0210896309 |
| `Solubility_AqSolDB_drugbank_approved_percentile` | 47.9437609842 |
| `VDss_Lombardo_drugbank_approved_percentile` | 2.2144112478 |

### PRST-004

- extrapolation_warning: `True`
- recommended_for_decision: `False`

| endpoint | value |
|---|---:|
| `molecular_weight` | 1625.983 |
| `logP` | -3.8921 |
| `hydrogen_bond_acceptors` | 23 |
| `hydrogen_bond_donors` | 22 |
| `Lipinski` | 1 |
| `QED` | 0.0244105539636 |
| `stereo_centers` | 19 |
| `tpsa` | 613.23 |
| `PAINS_alert` | 0 |
| `BRENK_alert` | 2 |
| `NIH_alert` | 0 |
| `AMES` | 0.414451897144 |
| `BBB_Martins` | 0.000407241343055 |
| `Bioavailability_Ma` | 0.015079177916 |
| `CYP1A2_Veith` | 6.39006088932e-07 |
| `CYP2C19_Veith` | 0.0520767383277 |
| `CYP2C9_Substrate_CarbonMangels` | 7.46773821447e-06 |
| `CYP2C9_Veith` | 0.0126593131572 |
| `CYP2D6_Substrate_CarbonMangels` | 0.00015899274149 |
| `CYP2D6_Veith` | 0.18376968801 |
| `CYP3A4_Substrate_CarbonMangels` | 0.208461761475 |
| `CYP3A4_Veith` | 0.492127984762 |
| `Carcinogens_Lagunin` | 0.00256836926565 |
| `ClinTox` | 0.14845213294 |
| `DILI` | 0.244249299169 |
| `HIA_Hou` | 0.00103996857069 |
| `NR-AR-LBD` | 0.0197174362838 |
| `NR-AR` | 0.0783037766814 |
| `NR-AhR` | 5.24959541508e-05 |
| `NR-Aromatase` | 0.0203737281263 |
| `NR-ER-LBD` | 0.26060166955 |
| `NR-ER` | 0.313961178064 |
| `NR-PPAR-gamma` | 0.00327630038373 |
| `PAMPA_NCATS` | 4.68939106213e-05 |
| `Pgp_Broccatelli` | 0.170438855886 |
| `SR-ARE` | 0.263989120722 |
| `SR-ATAD5` | 0.120866082609 |
| `SR-HSE` | 0.00172353372909 |
| `SR-MMP` | 0.0118394363672 |
| `SR-p53` | 0.383061468601 |
| `Skin_Reaction` | 0.10432741791 |
| `hERG` | 0.672606289387 |
| `Caco2_Wang` | -9.60108566284 |
| `Clearance_Hepatocyte_AZ` | -25.0043735504 |
| `Clearance_Microsome_AZ` | 164.386291504 |
| `Half_Life_Obach` | -7.16286325455 |
| `HydrationFreeEnergy_FreeSolv` | -62.9356079102 |
| `LD50_Zhu` | 3.89753103256 |
| `Lipophilicity_AstraZeneca` | 0.536849856377 |
| `PPBR_AZ` | 80.3767852783 |
| `Solubility_AqSolDB` | -3.22523355484 |
| `VDss_Lombardo` | -5.58162689209 |
| `molecular_weight_drugbank_approved_percentile` | 99.1564147627 |
| `logP_drugbank_approved_percentile` | 6.08084358524 |
| `hydrogen_bond_acceptors_drugbank_approved_percentile` | 98.7873462214 |
| `hydrogen_bond_donors_drugbank_approved_percentile` | 99.3673110721 |
| `Lipinski_drugbank_approved_percentile` | 2.54833040422 |
| `QED_drugbank_approved_percentile` | 1.40597539543 |
| `stereo_centers_drugbank_approved_percentile` | 99.1564147627 |
| `tpsa_drugbank_approved_percentile` | 99.1212653779 |
| `PAINS_alert_drugbank_approved_percentile` | 47.5922671353 |
| `BRENK_alert_drugbank_approved_percentile` | 87.9261862917 |
| `NIH_alert_drugbank_approved_percentile` | 37.1880492091 |
| `AMES_drugbank_approved_percentile` | 71.6344463972 |
| `BBB_Martins_drugbank_approved_percentile` | 0.66783831283 |
| `Bioavailability_Ma_drugbank_approved_percentile` | 1.79261862917 |
| `CYP1A2_Veith_drugbank_approved_percentile` | 2.2144112478 |
| `CYP2C19_Veith_drugbank_approved_percentile` | 40.5975395431 |
| `CYP2C9_Substrate_CarbonMangels_drugbank_approved_percentile` | 1.54657293497 |
| `CYP2C9_Veith_drugbank_approved_percentile` | 35.3251318102 |
| `CYP2D6_Substrate_CarbonMangels_drugbank_approved_percentile` | 2.28471001757 |
| `CYP2D6_Veith_drugbank_approved_percentile` | 70.4042179262 |
| `CYP3A4_Substrate_CarbonMangels_drugbank_approved_percentile` | 27.5219683656 |
| `CYP3A4_Veith_drugbank_approved_percentile` | 82.2847100176 |
| `Carcinogens_Lagunin_drugbank_approved_percentile` | 2.49560632689 |
| `ClinTox_drugbank_approved_percentile` | 61.7926186292 |
| `DILI_drugbank_approved_percentile` | 38.8049209139 |
| `HIA_Hou_drugbank_approved_percentile` | 2.63620386643 |
| `NR-AR-LBD_drugbank_approved_percentile` | 65.6590509666 |
| `NR-AR_drugbank_approved_percentile` | 87.5922671353 |
| `NR-AhR_drugbank_approved_percentile` | 2.81195079086 |
| `NR-Aromatase_drugbank_approved_percentile` | 50.5096660808 |
| `NR-ER-LBD_drugbank_approved_percentile` | 94.7275922671 |
| `NR-ER_drugbank_approved_percentile` | 91.2126537786 |
| `NR-PPAR-gamma_drugbank_approved_percentile` | 37.855887522 |
| `PAMPA_NCATS_drugbank_approved_percentile` | 1.54657293497 |
| `Pgp_Broccatelli_drugbank_approved_percentile` | 59.8242530756 |
| `SR-ARE_drugbank_approved_percentile` | 67.8031634446 |
| `SR-ATAD5_drugbank_approved_percentile` | 88.4710017575 |
| `SR-HSE_drugbank_approved_percentile` | 13.0404217926 |
| `SR-MMP_drugbank_approved_percentile` | 37.1177504394 |
| `SR-p53_drugbank_approved_percentile` | 93.4622144112 |
| `Skin_Reaction_drugbank_approved_percentile` | 3.83128295255 |
| `hERG_drugbank_approved_percentile` | 70.755711775 |
| `Caco2_Wang_drugbank_approved_percentile` | 1.37082601054 |
| `Clearance_Hepatocyte_AZ_drugbank_approved_percentile` | 4.28822495606 |
| `Clearance_Microsome_AZ_drugbank_approved_percentile` | 98.1370826011 |
| `Half_Life_Obach_drugbank_approved_percentile` | 10.8260105448 |
| `HydrationFreeEnergy_FreeSolv_drugbank_approved_percentile` | 1.15992970123 |
| `LD50_Zhu_drugbank_approved_percentile` | 97.855887522 |
| `Lipophilicity_AstraZeneca_drugbank_approved_percentile` | 39.2618629174 |
| `PPBR_AZ_drugbank_approved_percentile` | 56.0984182777 |
| `Solubility_AqSolDB_drugbank_approved_percentile` | 47.3462214411 |
| `VDss_Lombardo_drugbank_approved_percentile` | 2.56590509666 |

### Octreotide

- extrapolation_warning: `True`
- recommended_for_decision: `False`

| endpoint | value |
|---|---:|
| `molecular_weight` | 1019.261 |
| `logP` | -0.8054 |
| `hydrogen_bond_acceptors` | 14 |
| `hydrogen_bond_donors` | 13 |
| `Lipinski` | 1 |
| `QED` | 0.0455175534847 |
| `stereo_centers` | 10 |
| `tpsa` | 332.22 |
| `PAINS_alert` | 0 |
| `BRENK_alert` | 2 |
| `NIH_alert` | 0 |
| `AMES` | 0.562331616879 |
| `BBB_Martins` | 0.0288035664707 |
| `Bioavailability_Ma` | 0.204338312149 |
| `CYP1A2_Veith` | 0.00148352375254 |
| `CYP2C19_Veith` | 0.0622699744999 |
| `CYP2C9_Substrate_CarbonMangels` | 0.00767167657614 |
| `CYP2C9_Veith` | 0.0457151792943 |
| `CYP2D6_Substrate_CarbonMangels` | 0.0287741608918 |
| `CYP2D6_Veith` | 0.338901102543 |
| `CYP3A4_Substrate_CarbonMangels` | 0.534392416477 |
| `CYP3A4_Veith` | 0.72695505619 |
| `Carcinogens_Lagunin` | 0.0521945469081 |
| `ClinTox` | 0.414185345173 |
| `DILI` | 0.396473884583 |
| `HIA_Hou` | 0.348968833685 |
| `NR-AR-LBD` | 0.0498852133751 |
| `NR-AR` | 0.0826335847378 |
| `NR-AhR` | 0.0145236458629 |
| `NR-Aromatase` | 0.0788207873702 |
| `NR-ER-LBD` | 0.0980829149485 |
| `NR-ER` | 0.185189753771 |
| `NR-PPAR-gamma` | 0.0457830354571 |
| `PAMPA_NCATS` | 0.0167645663023 |
| `Pgp_Broccatelli` | 0.524663805962 |
| `SR-ARE` | 0.276923596859 |
| `SR-ATAD5` | 0.128107234836 |
| `SR-HSE` | 0.0331030152738 |
| `SR-MMP` | 0.0664442628622 |
| `SR-p53` | 0.287224203348 |
| `Skin_Reaction` | 0.254321753979 |
| `hERG` | 0.923535525799 |
| `Caco2_Wang` | -7.53591156006 |
| `Clearance_Hepatocyte_AZ` | -8.04766273499 |
| `Clearance_Microsome_AZ` | 103.636795044 |
| `Half_Life_Obach` | -1.4003225565 |
| `HydrationFreeEnergy_FreeSolv` | -40.4666366577 |
| `LD50_Zhu` | 3.78221130371 |
| `Lipophilicity_AstraZeneca` | 1.867639184 |
| `PPBR_AZ` | 87.9293212891 |
| `Solubility_AqSolDB` | -3.23949432373 |
| `VDss_Lombardo` | -1.15116560459 |
| `molecular_weight_drugbank_approved_percentile` | 96.8717047452 |
| `logP_drugbank_approved_percentile` | 15.9578207381 |
| `hydrogen_bond_acceptors_drugbank_approved_percentile` | 95.2548330404 |
| `hydrogen_bond_donors_drugbank_approved_percentile` | 97.855887522 |
| `Lipinski_drugbank_approved_percentile` | 2.54833040422 |
| `QED_drugbank_approved_percentile` | 2.56590509666 |
| `stereo_centers_drugbank_approved_percentile` | 95.9578207381 |
| `tpsa_drugbank_approved_percentile` | 96.5905096661 |
| `PAINS_alert_drugbank_approved_percentile` | 47.5922671353 |
| `BRENK_alert_drugbank_approved_percentile` | 87.9261862917 |
| `NIH_alert_drugbank_approved_percentile` | 37.1880492091 |
| `AMES_drugbank_approved_percentile` | 83.8312829525 |
| `BBB_Martins_drugbank_approved_percentile` | 3.72583479789 |
| `Bioavailability_Ma_drugbank_approved_percentile` | 7.34622144112 |
| `CYP1A2_Veith_drugbank_approved_percentile` | 16.2741652021 |
| `CYP2C19_Veith_drugbank_approved_percentile` | 43.7258347979 |
| `CYP2C9_Substrate_CarbonMangels_drugbank_approved_percentile` | 8.78734622144 |
| `CYP2C9_Veith_drugbank_approved_percentile` | 54.3409490334 |
| `CYP2D6_Substrate_CarbonMangels_drugbank_approved_percentile` | 22.1792618629 |
| `CYP2D6_Veith_drugbank_approved_percentile` | 79.2970123023 |
| `CYP3A4_Substrate_CarbonMangels_drugbank_approved_percentile` | 59.4727592267 |
| `CYP3A4_Veith_drugbank_approved_percentile` | 89.1388400703 |
| `Carcinogens_Lagunin_drugbank_approved_percentile` | 17.0474516696 |
| `ClinTox_drugbank_approved_percentile` | 87.3110720562 |
| `DILI_drugbank_approved_percentile` | 49.5606326889 |
| `HIA_Hou_drugbank_approved_percentile` | 13.0755711775 |
| `NR-AR-LBD_drugbank_approved_percentile` | 83.6203866432 |
| `NR-AR_drugbank_approved_percentile` | 88.4710017575 |
| `NR-AhR_drugbank_approved_percentile` | 45.1669595782 |
| `NR-Aromatase_drugbank_approved_percentile` | 71.5641476274 |
| `NR-ER-LBD_drugbank_approved_percentile` | 86.4323374341 |
| `NR-ER_drugbank_approved_percentile` | 81.6520210896 |
| `NR-PPAR-gamma_drugbank_approved_percentile` | 78.8752196837 |
| `PAMPA_NCATS_drugbank_approved_percentile` | 9.3848857645 |
| `Pgp_Broccatelli_drugbank_approved_percentile` | 78.8400702988 |
| `SR-ARE_drugbank_approved_percentile` | 68.8927943761 |
| `SR-ATAD5_drugbank_approved_percentile` | 89.0685413005 |
| `SR-HSE_drugbank_approved_percentile` | 63.5852372583 |
| `SR-MMP_drugbank_approved_percentile` | 58.7346221441 |
| `SR-p53_drugbank_approved_percentile` | 89.9472759227 |
| `Skin_Reaction_drugbank_approved_percentile` | 15.992970123 |
| `hERG_drugbank_approved_percentile` | 88.8576449912 |
| `Caco2_Wang_drugbank_approved_percentile` | 4.14762741652 |
| `Clearance_Hepatocyte_AZ_drugbank_approved_percentile` | 9.91212653779 |
| `Clearance_Microsome_AZ_drugbank_approved_percentile` | 90.7205623902 |
| `Half_Life_Obach_drugbank_approved_percentile` | 19.8594024605 |
| `HydrationFreeEnergy_FreeSolv_drugbank_approved_percentile` | 3.51493848858 |
| `LD50_Zhu_drugbank_approved_percentile` | 97.3286467487 |
| `Lipophilicity_AstraZeneca_drugbank_approved_percentile` | 59.5782073814 |
| `PPBR_AZ_drugbank_approved_percentile` | 66.0456942004 |
| `Solubility_AqSolDB_drugbank_approved_percentile` | 47.065026362 |
| `VDss_Lombardo_drugbank_approved_percentile` | 24.6748681898 |

## Honest Failure/Dependency Notes

- No provider error occurred for PRST-001~004 or Octreotide in this run.
- ADMET-AI emitted Lightning/tqdm progress and batch-normalization warnings in stderr; raw endpoint JSON was still produced for every input.
- These values are not validated peptide/DOTA ADMET estimates. They are raw model outputs under an explicit extrapolation guard.

