# Iteration 3 Summary: sst14_mutdock_1000

            - **Run ID**: `sst14_mutdock_1000`
            - **Iteration**: 3
            - **생성 시각**: 2026-06-10 07:30 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 3 of the sst14_mutdock_1000 design campaign evaluated five peptide binder candidates for SSTR2 binding. All candidates passed quality control (QC) gates, indicating structural and design consistency. However, despite favorable binding affinities (ddG values ranging from -12.5 to -45.2 kcal/mol), none achieved SSTR2 selectivity, as all displayed Δmargin ≤ 0. This suggests that the current designs are not distinguishing between SSTR2 and off-target receptors such as SSTR3 and SSTR5, likely due to conserved interaction motifs in the binding pocket. The primary failure mode was structural_failures, indicating a need for improved specificity through structural modifications.

            ## Recommendations

            - Introduce structural modifications to disrupt conserved interactions in the binding pocket, particularly those that may be shared with SSTR3 and SSTR5.
- Incorporate selectivity screening early in the design pipeline to prioritize candidates with distinct SSTR2-specific interactions.
- Revisit the docking and scoring protocols to better capture selectivity-related metrics in addition to binding affinity.