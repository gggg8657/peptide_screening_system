# Iteration 17 Summary: sst14_mutdock_24000

            - **Run ID**: `sst14_mutdock_24000`
            - **Iteration**: 17
            - **생성 시각**: 2026-06-12 05:35 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 17 of the SSTR2 peptide binder design campaign evaluated a total of 1 candidate, with only 1 passing all QC gates, resulting in a pass rate of 100%. Despite the low number of candidates, the top candidate, iter17_cand006, exhibited a strong ddG value of -27.6, indicating favorable binding affinity. However, the pLDDT and docking scores were both reported as 0.0, suggesting potential issues with structural prediction or docking accuracy. The overall low pass rate and structural failures observed in this iteration highlight the need for further optimization of both sequence and structural design parameters to improve yield and reliability.

The primary failure mode in this iteration was attributed to structural failures, which may stem from suboptimal sequence-structure compatibility or limitations in the current modeling pipeline. While the single candidate that passed QC shows promise in terms of binding energy, the lack of structural confidence metrics raises concerns about its overall viability as a lead candidate. These findings underscore the importance of refining the design strategy to address structural stability and ensure robust performance across all QC metrics.

            ## Recommendations

            - Investigate the structural failures observed in this iteration to identify root causes and refine the design pipeline accordingly.
- Improve the modeling and docking protocols to enhance the accuracy of pLDDT and docking scores for better candidate evaluation.
- Expand the candidate pool in the next iteration to increase the likelihood of identifying structurally and functionally robust binders.
- Focus on optimizing sequence-structure compatibility to improve the overall pass rate and reduce structural failure rates.