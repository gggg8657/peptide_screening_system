# Iteration 13 Summary: sst14_mutdock_17000

            - **Run ID**: `sst14_mutdock_17000`
            - **Iteration**: 13
            - **생성 시각**: 2026-06-11 17:30 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 13 evaluated a total of 3 candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was to enhance binding affinity and selectivity for the SSTR2 peptide binder. While the candidates demonstrated strong binding affinity, as indicated by ddG values ranging from -21.0 to -40.4 kcal/mol, there was no improvement in selectivity over the native SST-14. The best ddG value of -40.4 kcal/mol was observed for iter13_cand007, but the Δmargin did not surpass the current best of 9.1021. The overall pass rate remained low at 37.5%, with structural failures being the primary cause of candidate rejection.

The top candidates, iter13_cand007, iter13_cand008, and iter13_cand005, exhibited strong binding affinities but lacked the desired selectivity improvements. The pLDDT and docking scores were not reported for these candidates, suggesting potential issues with structural modeling or scoring consistency. The results highlight the need to refine the design strategy to address structural stability and improve selectivity in future iterations.

            ## Recommendations

            - Refine the structural modeling approach to improve pLDDT and docking scores for better structural confidence.
- Incorporate additional selectivity metrics into the design pipeline to prioritize candidates with improved Δmargin.
- Investigate the structural failures to identify common issues and address them in the next iteration.
- Consider increasing the diversity of the candidate pool to enhance the likelihood of discovering high-affinity and selective binders.