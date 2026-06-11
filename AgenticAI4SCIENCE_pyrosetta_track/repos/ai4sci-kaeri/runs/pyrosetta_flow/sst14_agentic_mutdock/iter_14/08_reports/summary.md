# Iteration 14 Summary: sst14_mutdock_7000

            - **Run ID**: `sst14_mutdock_7000`
            - **Iteration**: 14
            - **생성 시각**: 2026-06-10 23:17 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 14 evaluated three candidates, all of which passed the quality control (QC) gates. The candidates displayed a range of ddG values, with the best binder (iter14_cand001) showing a strong binding affinity (ddG = -50.5 kcal/mol). However, the pLDDT and docking scores were not reported, suggesting a lack of structural confidence or docking evaluation in this iteration. Critically, selectivity remains a major concern, as the Δmargin values indicate that most candidates do not significantly outperform native SST-14 in off-target discrimination. This highlights a key limitation in the current design strategy, where binding affinity is achieved but at the cost of poor selectivity.

The primary failure type observed in this iteration was structural failures, which may have implications for the stability or conformational accuracy of the designed peptides. While the best candidate shows promise in terms of binding strength, the lack of structural validation and poor selectivity suggest that further optimization is necessary. The next iteration should focus on improving selectivity while maintaining strong binding affinity and ensuring structural integrity of the designed peptides.

            ## Recommendations

            - Prioritize selectivity optimization in the next iteration to ensure off-target discrimination is significantly improved.
- Incorporate structural validation methods to address the structural failures observed in this iteration.
- Re-evaluate the docking and pLDDT metrics to ensure they are being calculated and reported for future iterations.