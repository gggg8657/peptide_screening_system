# Iteration 13 Summary: sst14_mutdock_20000

            - **Run ID**: `sst14_mutdock_20000`
            - **Iteration**: 13
            - **생성 시각**: 2026-06-11 22:43 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 13 evaluated three candidates for SSTR2 binding, all of which passed quality control (QC) gates. The top candidates demonstrated strong binding affinities as indicated by their ddG values, with iter13_cand006 showing the most favorable ddG of -48.9 kcal/mol. However, the selectivity metrics (Δmargin) for off-targets SSTR3 and SSTR5 remain suboptimal, with values not significantly higher than those of the native SST-14. This suggests that while the current designs exhibit strong binding to the target receptor, further optimization is necessary to enhance selectivity and reduce potential cross-reactivity. The primary failure type observed in this iteration was structural failures, indicating a need to refine structural stability and specificity in the next round of design.

            ## Recommendations

            - Focus on improving selectivity for SSTR3 and SSTR5 in the next iteration by incorporating additional constraints or features into the design process.
- Investigate the structural failures observed in this iteration to identify common motifs or weaknesses that can be addressed in future designs.
- Consider using higher-resolution modeling or additional validation methods to refine the predicted structures and improve pLDDT scores.