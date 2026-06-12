# Iteration 16 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 16
            - **생성 시각**: 2026-06-12 11:06 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 16 evaluated a total of three candidates, all of which passed the quality control (QC) gates. Despite the complete QC pass rate, the structural and docking quality metrics were severely compromised, with all candidates reporting pLDDT and docking scores of 0.00. This indicates a failure in structural modeling during the design process. However, the binding affinity, as measured by ddG, was strong, with the best value of -41.8 kcal/mol for iter16_cand006. Selectivity was also favorable, with a Δmargin of 9.10, suggesting that the candidates maintain good target specificity despite structural limitations.

The primary failure mode in this iteration was structural modeling inaccuracies, which significantly limit the viability of the candidates for downstream experimental validation. While the binding energy and selectivity are promising, the lack of structural confidence necessitates a reevaluation of the modeling pipeline. The top candidates, iter16_cand006, iter16_cand003, and iter16_cand002, should be revisited in the next iteration with improved structural modeling approaches.

            ## Recommendations

            - Investigate and refine the structural modeling pipeline to address the recurring structural failure mode.
- Reevaluate the top candidates in the next iteration using improved modeling techniques to restore confidence in pLDDT and docking scores.
- Maintain focus on optimizing binding affinity and selectivity while addressing structural modeling limitations.