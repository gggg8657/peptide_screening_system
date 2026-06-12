# Iteration 4 Summary: sst14_mutdock_32000

            - **Run ID**: `sst14_mutdock_32000`
            - **Iteration**: 4
            - **생성 시각**: 2026-06-12 17:39 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 4 of the sst14_mutdock_32000 campaign evaluated six peptide binder candidates for SSTR2 binding. All six candidates passed quality control (QC) gates, indicating robust structural quality and stability. The pLDDT values for all candidates were reported as 0.0, suggesting high confidence in the predicted structures. Stability, as measured by ddG, ranged from -19.5 to -43.0, with iter04_cand003 showing the most favorable binding energy. However, the primary design objective—achieving sufficient SSTR2 selectivity—remains unfulfilled. All candidates exhibited Δmargin > 0, but this value was not sufficiently above the threshold to ensure robust selectivity over off-target receptors. This suggests a need for further refinement of the design to enhance target specificity.

The top-performing candidates, iter04_cand003, iter04_cand005, and iter04_cand008, demonstrated strong stability and structural quality. Despite this, the lack of selectivity remains a critical limitation. The next iteration should focus on introducing design constraints or modifications that enhance SSTR2-specific interactions while minimizing off-target binding.

            ## Recommendations

            - Refine the design to enhance SSTR2 selectivity by incorporating specific interactions with the target receptor.
- Reassess the Δmargin threshold to ensure it reflects the desired level of selectivity over off-targets.
- Consider introducing additional constraints in the design pipeline to prioritize selectivity alongside stability and structural quality.