# Iteration 18 Summary: sst14_mutdock_42000

            - **Run ID**: `sst14_mutdock_42000`
            - **Iteration**: 18
            - **생성 시각**: 2026-06-13 11:33 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 18 evaluated a total of 2 candidates, both of which passed all quality control (QC) gates. The primary focus of this iteration was to assess binding affinity and structural stability. While the candidates demonstrated strong binding affinities, as indicated by ddG values of -24.6 and -18.2 kcal/mol for iter18_cand002 and iter18_cand003, respectively, structural failures were identified as a major limitation. Notably, the pLDDT and docking scores were not available for these candidates, suggesting potential issues with structural modeling or docking accuracy. Despite the strong binding affinity, the absence of structural confidence highlights the need for improved modeling strategies to ensure both high affinity and structural integrity in future designs.

            ## Recommendations

            - Investigate the structural modeling pipeline to address the lack of pLDDT and docking scores, which may indicate modeling inaccuracies.
- Optimize the balance between binding affinity and structural stability in the design process.
- Consider incorporating additional structural validation metrics to ensure robustness in future iterations.