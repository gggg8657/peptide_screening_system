# Iteration 20 Summary: sst14_mutdock_10000

            - **Run ID**: `sst14_mutdock_10000`
            - **Iteration**: 20
            - **생성 시각**: 2026-06-11 05:28 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 20 evaluated three candidates, all of which passed quality control (QC) gates. Despite the structural quality metric (pLDDT) being uniformly zero across all candidates, indicating structural failures, the binding affinity (ddG) values were strong, with the best candidate (iter20_cand007) achieving a ddG of -32.7 kcal/mol. Docking scores were not informative (0.00) for all candidates, suggesting a lack of meaningful docking evaluation or data availability. Selectivity metrics showed a positive margin (Δmargin > 0), but no candidate surpassed the native SST-14 ligand in all aspects.

The primary failure mode in this iteration was structural, highlighting the need for improved structural modeling or refinement strategies. The strong ddG values suggest that the binding affinity is being captured effectively, but structural accuracy remains a critical bottleneck. Future iterations should prioritize enhancing structural quality while maintaining strong binding performance.

            ## Recommendations

            - Implement structural refinement strategies to address the structural failure mode observed in this iteration.
- Investigate the reasons for the lack of informative docking scores and consider alternative evaluation methods.
- Continue to prioritize candidates with strong ddG values while improving structural quality metrics.