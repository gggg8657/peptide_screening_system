# Iteration 1 Summary: sst14_mutdock_42

            - **Run ID**: `sst14_mutdock_42`
            - **Iteration**: 1
            - **생성 시각**: 2026-04-01 08:28 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated four SSTR2 peptide binder candidates, all of which passed QC gates. However, all candidates exhibited severe structural abnormalities, as indicated by pLDDT=0.0 and docking scores=0.00, despite achieving negative ddG values. These results suggest invalid structural predictions that require immediate investigation. The primary failure type was structural failures, undermining the reliability of binding affinity calculations. While ddG values show potential for favorable interactions, the invalid structures necessitate re-evaluation of conformational sampling methods.

The top candidate, iter01_cand002, demonstrated the most favorable ddG=-45.8, though its structural validity remains questionable. Other candidates showed progressively less favorable ddG values (-35.1, -27.9, -12.8). The lack of meaningful pLDDT and docking scores highlights a critical gap in structure prediction accuracy. These results emphasize the need to prioritize structural validation before advancing candidates to subsequent iterations.

            ## Recommendations

            - Prioritize refinement of structure prediction protocols to resolve pLDDT=0.0 failures
- Implement experimental validation (e.g., X-ray crystallography) for top candidates before proceeding
- Re-evaluate docking protocol parameters to ensure correlation with structural validity
- Focus iteration 2 on candidates with both negative ddG and non-zero pLDDT/docking scores