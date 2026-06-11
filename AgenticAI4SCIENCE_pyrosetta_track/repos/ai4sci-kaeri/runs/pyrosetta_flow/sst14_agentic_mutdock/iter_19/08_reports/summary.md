# Iteration 19 Summary: sst14_mutdock_7000

            - **Run ID**: `sst14_mutdock_7000`
            - **Iteration**: 19
            - **생성 시각**: 2026-06-10 23:40 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 19 evaluated three candidate peptides for their binding affinity and selectivity toward the SSTR2 receptor. All three candidates passed the quality control (QC) gates, indicating structural and energetic feasibility. The top candidates demonstrated strong binding affinities, as indicated by ddG values ranging from -16.4 to -31.4 kcal/mol. However, the selectivity of these candidates over off-target receptors was limited, with Δmargin values comparable to the native SST-14 ligand. This suggests that while the candidates exhibit favorable binding energies, they have not achieved the desired level of specificity for SSTR2, which is a critical design objective.

The primary failure mode in this iteration was structural failures, indicating that further refinement of the peptide structures is necessary to improve both stability and selectivity. The lack of significant improvement in selectivity highlights the need for additional design strategies focused on optimizing interactions specific to the SSTR2 binding pocket.

            ## Recommendations

            - Focus the next iteration on structural refinement to address the observed structural failures and improve selectivity for SSTR2.
- Incorporate additional constraints or design rules that prioritize interactions unique to the SSTR2 binding site.
- Re-evaluate the scoring metrics to ensure that selectivity is adequately weighted in the candidate ranking.