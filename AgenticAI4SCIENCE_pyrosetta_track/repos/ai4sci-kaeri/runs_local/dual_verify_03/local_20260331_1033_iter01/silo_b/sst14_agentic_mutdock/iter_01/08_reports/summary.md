# Iteration 1 Summary: sst14_mutdock_100 - QC Gate Failures

            - **Run ID**: `sst14_mutdock_100`
            - **Iteration**: 1
            - **생성 시각**: 2026-03-31 10:36 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated 0 candidates, all of which failed QC gates due to excessively strict ddG and clash threshold parameters. The primary failure type was structural_failures, indicating the current design space may not meet the imposed criteria. No valid candidates were generated, necessitating parameter adjustments for subsequent iterations.

            ## Recommendations

            - Relax ddG and clash thresholds to accommodate the current design space
- Refine scoring function parameters to balance stringency and design feasibility
- Increase diversity in the initial design space to improve QC gate pass rates