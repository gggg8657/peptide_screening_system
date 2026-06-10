# Iteration 15 Summary: sst14_mutdock_4000

            - **Run ID**: `sst14_mutdock_4000`
            - **Iteration**: 15
            - **생성 시각**: 2026-06-10 16:47 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 15 of the SSTR2 peptide binder design campaign evaluated a single candidate, with one passing all QC gates. However, the overall pass rate was low at 12.5%, and the top candidate, iter15_cand003, exhibited structural and docking issues, as evidenced by a pLDDT of 0.0 and a dock score of 0.00. Despite a strong Δmargin of 8.6866 for this candidate, the majority of designs showed Δmargin values near or below 0, indicating poor selectivity. This suggests that the current design strategy may not be effectively balancing structural stability with functional selectivity.

The primary failure mode in this iteration was structural failures, highlighting the need for improved structural modeling or refinement strategies. The low pass rate and poor structural metrics underscore the importance of revisiting the design parameters and incorporating additional constraints to enhance structural integrity and binding specificity.

            ## Recommendations

            - Revisit the structural modeling pipeline to address the low pLDDT and dock score issues observed in this iteration.
- Incorporate additional constraints or refine the design parameters to improve structural stability and binding selectivity.
- Evaluate alternative docking protocols or scoring functions to better capture the binding interactions and improve selectivity metrics.