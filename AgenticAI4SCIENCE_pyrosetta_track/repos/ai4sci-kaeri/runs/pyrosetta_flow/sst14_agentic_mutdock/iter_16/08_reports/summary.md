# Iteration 16 Summary: sst14_mutdock_10000

            - **Run ID**: `sst14_mutdock_10000`
            - **Iteration**: 16
            - **생성 시각**: 2026-06-11 04:59 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 16 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, both of which passed all QC gates. While the selectivity margin showed improvement (Δmargin > 0), the overall pass rate remained low at 25%, consistent with prior iterations. The primary failure mode was structural failures, as evidenced by the absence of meaningful pLDDT values (pLDDT=0.0) for the top candidates, indicating that structural quality remains a critical bottleneck in the design pipeline. Despite this, the top candidates exhibited strong binding affinity, as reflected by their ddG values of -41.3 and -30.9 kcal/mol, respectively. These results suggest that the current design strategy is generating binders with favorable energetics but is struggling to produce structurally viable candidates.

            ## Recommendations

            - Prioritize structural refinement strategies to improve pLDDT scores and reduce structural failures.
- Investigate the root causes of structural failures, such as backbone clashes or poor secondary structure predictions.
- Consider incorporating additional structural constraints or using higher-resolution modeling techniques in the next iteration.
- Continue to monitor selectivity improvements and refine the scoring function to better align with structural quality metrics.