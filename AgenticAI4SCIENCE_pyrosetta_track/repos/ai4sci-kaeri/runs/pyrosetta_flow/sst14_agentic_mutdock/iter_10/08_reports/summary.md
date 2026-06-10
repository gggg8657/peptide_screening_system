# Iteration 10 Summary: sst14_mutdock_7000

            - **Run ID**: `sst14_mutdock_7000`
            - **Iteration**: 10
            - **생성 시각**: 2026-02-25 10:10 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated 8 candidates for SSTR2 peptide binder design. All candidates passed QC gates, but exhibited critically low pLDDT (0.0) and docking scores (0.00), indicating severe structural instability despite meeting threshold criteria. The primary failure type was structural_failures, suggesting systematic issues in model generation. While ddG values ranged from -13.6 to -42.5, the lack of meaningful structural metrics raises concerns about the reliability of binding affinity predictions. Further investigation into the root causes of these failures is required before advancing to the next iteration.

            ## Recommendations

            - Investigate the root causes of structural failures in all candidates, prioritizing analysis of top ddG performers.
- Refine design parameters to improve pLDDT and docking score reliability, potentially revisiting backbone sampling strategies.
- Implement additional validation steps for candidates with extreme ddG values to ensure meaningful binding affinity predictions.
- Re-evaluate scoring function thresholds to better balance structural quality and binding affinity optimization.