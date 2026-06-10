# Iteration 2 Summary: sst14_mutdock_4002

            - **Run ID**: `sst14_mutdock_4002`
            - **Iteration**: 2
            - **생성 시각**: 2026-04-02 06:58 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated six SSTR2 peptide binder candidates, all of which passed QC gates. However, all candidates exhibited critically low pLDDT (0.0) and docking scores (0.00), indicating potential scoring artifacts rather than structural failures. The primary failure type was structural_failures, suggesting systematic issues in model quality or scoring function calibration. While ddG values ranged from -21.8 to -47.7, the lack of meaningful pLDDT and docking score variation raises concerns about the reliability of these metrics for ranking candidates. Further investigation into scoring artifacts and structural refinement is required before progressing to the next iteration.

            ## Recommendations

            - Investigate scoring artifacts in pLDDT and docking calculations to ensure metric reliability.
- Prioritize structural refinement for candidates with the highest ddG values (-47.7 to -42.4) to validate binding affinity predictions.
- Re-evaluate model sampling strategies to improve conformational diversity and scoring accuracy.