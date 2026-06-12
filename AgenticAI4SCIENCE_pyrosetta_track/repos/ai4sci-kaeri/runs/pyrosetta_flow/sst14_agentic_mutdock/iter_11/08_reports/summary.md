# Iteration 11 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 11
            - **생성 시각**: 2026-06-12 10:41 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 11 evaluated five candidate peptides for SSTR2 binding, all of which passed quality control (QC) gates. The primary focus of this iteration was to improve binding affinity, as reflected by the ddG values, which ranged from -19.0 to -34.3 kcal/mol. The top candidates demonstrated strong binding potential, with iter11_cand001 achieving the lowest ddG of -34.3 kcal/mol. However, the pLDDT and docking scores remained at 0.0 for all candidates, indicating that structural confidence and docking accuracy were not assessed or were not available for this iteration. Selectivity remains a key challenge, as several candidates exhibited lower Δmargin values, suggesting potential off-target binding.

            ## Recommendations

            - Prioritize candidates with the lowest ddG values (e.g., iter11_cand001) for further evaluation and experimental validation.
- Address selectivity concerns by incorporating additional selectivity filters or off-target binding assessments in the next iteration.
- Investigate the structural failures noted in the Critic analysis to improve structural confidence and docking accuracy in future designs.