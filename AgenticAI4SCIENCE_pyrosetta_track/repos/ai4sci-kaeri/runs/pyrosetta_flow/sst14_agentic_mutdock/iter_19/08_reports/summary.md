# Iteration 19 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 19
            - **생성 시각**: 2026-06-12 11:21 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 19 evaluated three candidate peptides for their binding affinity to the SSTR2 target. All candidates passed quality control (QC) gates, indicating structural and energetic feasibility. The candidates demonstrated strong ddG binding energies, with the best value of -28.3 kcal/mol for iter19_cand003. However, no significant improvement in selectivity over the native SST-14 was observed, as reflected in the modest Δmargin values. This highlights a critical bottleneck in the campaign: while binding affinity is robust, off-target interactions remain a concern. The Critic analysis identified structural failures as the primary failure mode, suggesting that further refinement is needed to optimize the balance between on-target binding and selectivity. The lack of pLDDT and docking score data for the candidates also indicates a need for more comprehensive structural validation in the next iteration.

            ## Recommendations

            - Prioritize the disruption of off-target interactions in the next iteration to improve selectivity.
- Incorporate structural validation tools to obtain pLDDT and docking scores for better assessment of candidate stability and binding modes.
- Refine the design strategy to balance strong on-target binding with reduced off-target activity, leveraging insights from the Critic analysis.