# Iteration 7 Summary: sst14_mutdock_14000

            - **Run ID**: `sst14_mutdock_14000`
            - **Iteration**: 7
            - **생성 시각**: 2026-06-11 11:47 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 7 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, with both passing all QC gates. However, the overall pass rate was low at 25%, and no candidates achieved a Δmargin ≤ 0, indicating that selectivity remains a significant challenge. The top candidates, iter07_cand007 and iter07_cand005, exhibited strong ddG values of -27.6 and -18.9, respectively, but lacked structural and docking quality, as indicated by pLDDT and docking scores of 0.0. These results suggest that while binding affinity is being achieved, structural reliability and selectivity are not yet optimized.

The primary failure mode observed in this iteration was structural failures, highlighting the need to improve the structural quality of the designed peptides. The absence of meaningful pLDDT and docking scores indicates a need for refinement in the modeling pipeline to ensure that candidates not only bind strongly but also maintain structural integrity. Future iterations should focus on addressing these structural shortcomings while also improving selectivity to enhance the overall quality of the binder candidates.

            ## Recommendations

            - Improve the structural modeling pipeline to ensure higher pLDDT and docking scores for future candidates.
- Incorporate additional selectivity constraints in the design process to address the current lack of selectivity.
- Evaluate alternative scoring functions or design strategies that prioritize both affinity and structural quality.