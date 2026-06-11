# Iteration 17 Summary: sst14_mutdock_17000

            - **Run ID**: `sst14_mutdock_17000`
            - **Iteration**: 17
            - **생성 시각**: 2026-06-11 17:52 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 17 of the SSTR2 peptide binder design campaign evaluated a total of 8 candidates, with only 1 candidate passing all quality control (QC) gates. The low pass rate (12.5%) indicates a significant issue with structural quality, as the primary failure type was structural_failures. The single candidate that passed QC, iter17_cand008, demonstrated a ΔG of -18.4 kcal/mol, suggesting strong binding potential. However, the lack of structural confidence (pLDDT=0.0) and docking score (0.00) highlights the need for improved modeling and refinement strategies. The overall performance of this iteration underscores the importance of balancing binding affinity with structural reliability and selectivity.

            ## Recommendations

            - Improve structural modeling accuracy to increase the pass rate of candidates through QC gates.
- Refine the selection criteria to prioritize candidates with higher pLDDT scores and better docking performance.
- Investigate the root causes of structural failures to optimize the design pipeline for the next iteration.
- Consider incorporating additional selectivity metrics to ensure candidates are not only strong binders but also specific to the target.