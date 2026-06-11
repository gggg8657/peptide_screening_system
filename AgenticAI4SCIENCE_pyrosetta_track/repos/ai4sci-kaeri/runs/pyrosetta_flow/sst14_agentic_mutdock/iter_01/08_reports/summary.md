# Iteration 1 Summary: sst14_mutdock_11000

            - **Run ID**: `sst14_mutdock_11000`
            - **Iteration**: 1
            - **생성 시각**: 2026-06-11 05:38 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 1 of the SSTR2 peptide binder design campaign evaluated a total of 3 candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was to assess binding affinity (ddG) and selectivity (Δmargin > 0). While all candidates demonstrated strong ddG values, indicating favorable binding to SSTR2, the structural quality metrics (pLDDT) were uniformly low (pLDDT=0.0), raising concerns about the reliability of the predicted structures. This suggests that the current design approach may not be generating structurally plausible candidates, despite favorable binding energy predictions.

The top candidates, iter01_cand007, iter01_cand004, and iter01_cand005, exhibited ddG values of -28.1, -25.1, and -20.3 kcal/mol, respectively. However, the absence of meaningful pLDDT and docking scores indicates a need for refinement in the structural modeling pipeline. The selectivity criterion was met by all candidates, but the overall pass rate was low (37.5%), underscoring the need for improvements in structural accuracy.

            ## Recommendations

            - Investigate the structural modeling pipeline to improve pLDDT scores and overall structural quality.
- Refine the design strategy to ensure that structural accuracy is prioritized alongside binding affinity.
- Consider incorporating additional constraints or validation steps to enhance the reliability of predicted structures.
- Evaluate the impact of sequence design on structural plausibility in subsequent iterations.