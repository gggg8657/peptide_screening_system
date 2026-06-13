# Iteration 18 Summary: sst14_mutdock_38000

            - **Run ID**: `sst14_mutdock_38000`
            - **Iteration**: 18
            - **생성 시각**: 2026-06-13 04:56 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 18 evaluated three candidate peptides for SSTR2 binding. All candidates passed quality control (QC) gates, but structural and docking quality metrics were severely compromised, with all candidates reporting pLDDT and docking scores of 0.0. Despite this, binding affinity, as measured by ddG, was strong, with the best candidate (iter18_cand006) achieving a ddG of -39.3 kcal/mol. Selectivity metrics indicated a positive Δmargin, but the improvement over the native SST-14 ligand was not substantial. The primary failure mode was structural modeling inaccuracies, which may have impacted the reliability of predicted binding modes and overall design quality.

The top three candidates (iter18_cand006, iter18_cand005, and iter18_cand002) showed progressively weaker ddG values, but all lacked structural confidence. These results highlight the need to improve structural modeling accuracy in future iterations to ensure that high-affinity candidates are also structurally plausible and dockable. The next iteration should focus on refining structural prediction methods and validating binding modes through higher-resolution modeling or experimental validation.

            ## Recommendations

            - Improve structural modeling accuracy to enhance pLDDT and docking scores.
- Validate top candidates using higher-resolution modeling or experimental techniques.
- Focus on achieving a balance between strong ddG values and structural reliability in future iterations.