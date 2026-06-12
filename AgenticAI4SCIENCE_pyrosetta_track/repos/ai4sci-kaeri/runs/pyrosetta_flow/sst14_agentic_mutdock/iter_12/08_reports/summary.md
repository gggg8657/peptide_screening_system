# Iteration 12 Summary: sst14_mutdock_31000

            - **Run ID**: `sst14_mutdock_31000`
            - **Iteration**: 12
            - **생성 시각**: 2026-06-12 16:53 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 12 evaluated a single candidate, which passed all QC gates. Despite the low number of candidates, the pass rate was 100%, but the overall pass rate for the iteration was only 12.5% due to the limited input size. The top candidate, iter12_cand001, exhibited a strong ddG value of -30.1, indicating favorable binding affinity. However, the pLDDT of 0.0 and docking score of 0.00 suggest significant structural and docking failures, which are the primary reasons for QC gate failures in this iteration. The positive selectivity margin for the top candidate is a promising sign, but structural quality remains a critical issue that needs to be addressed.

            ## Recommendations

            - Focus on improving structural modeling quality to address the low pLDDT values and docking failures.
- Investigate the root causes of structural failures to refine the design pipeline.
- Consider increasing the number of candidates in the next iteration to better assess pass rates and identify robust binders.