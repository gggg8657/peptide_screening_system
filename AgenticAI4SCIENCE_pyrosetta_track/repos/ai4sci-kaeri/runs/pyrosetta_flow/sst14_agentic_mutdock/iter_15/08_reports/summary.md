# Iteration 15 Summary: sst14_mutdock_10000

            - **Run ID**: `sst14_mutdock_10000`
            - **Iteration**: 15
            - **생성 시각**: 2026-06-11 04:51 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 15 evaluated a total of 2 candidates, both of which passed all QC gates. Despite the small sample size, the iteration demonstrated high binding affinity as indicated by strong ddG values, with the best candidate (iter15_cand006) achieving a ddG of -34.0 kcal/mol. However, structural quality was severely compromised, as both candidates exhibited pLDDT scores of 0.0, indicating poor confidence in predicted structures. This highlights a critical issue in the design pipeline, where binding energy optimization appears to come at the expense of structural accuracy. Selectivity was maintained with a Δmargin > 0, but the overall pass rate of 25% suggests inefficiencies in the design process.

            ## Recommendations

            - Prioritize structural quality metrics (e.g., pLDDT) in the design pipeline to ensure that high ddG values are not achieved at the expense of structural confidence.
- Investigate the root causes of structural failures, including potential issues with template selection or sampling strategies.
- Consider incorporating additional constraints or filters to balance binding affinity and structural accuracy in future iterations.