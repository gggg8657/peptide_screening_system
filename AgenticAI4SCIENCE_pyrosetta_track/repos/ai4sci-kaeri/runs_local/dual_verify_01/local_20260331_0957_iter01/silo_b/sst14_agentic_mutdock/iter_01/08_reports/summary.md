# Iteration 1 Summary: sst14_mutdock_100 - Structural Failures Due to Stringent QC Thresholds

            - **Run ID**: `sst14_mutdock_100`
            - **Iteration**: 1
            - **생성 시각**: 2026-03-31 10:00 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration yielded no valid candidates due to overly stringent ddG and clash thresholds, resulting in all candidates failing structural quality checks. The QC gates were configured to reject any binding pose with non-optimal energy landscapes or steric clashes, which inadvertently excluded all generated models. Key metrics such as pLDDT, docking scores, and selectivity could not be evaluated due to the absence of passing candidates. The primary failure type was structural_failures, indicating a need to recalibrate energy thresholds and clash detection parameters to balance stringency with model viability.

            ## Recommendations

            - Adjust ddG and clash threshold parameters to reduce false negatives in structural validation
- Implement tiered QC gating to prioritize structural integrity without excessive filtering
- Validate parameter settings against benchmark datasets to optimize balance between stringency and model diversity