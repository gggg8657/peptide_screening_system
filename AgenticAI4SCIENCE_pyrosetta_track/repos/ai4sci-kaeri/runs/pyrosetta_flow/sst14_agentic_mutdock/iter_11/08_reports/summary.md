# Iteration 11 Summary: sst14_mutdock_14000

            - **Run ID**: `sst14_mutdock_14000`
            - **Iteration**: 11
            - **생성 시각**: 2026-06-11 12:10 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 11 evaluated three SSTR2 peptide binder candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was to improve binding affinity and selectivity. While the candidates demonstrated strong binding affinities, as indicated by ddG values ranging from -16.6 to -35.7 kcal/mol, improvements in selectivity were marginal. The top candidates, iter11_cand007, iter11_cand003, and iter11_cand006, showed promising ddG scores but lacked significant enhancements in structural stability or sequence diversity. Notably, all candidates had pLDDT and docking scores of 0.00, suggesting potential issues with structural modeling or scoring accuracy. The primary failure type observed was structural failures, indicating that the current designs may not be structurally robust enough to meet the desired criteria. This highlights the need for further refinement in the structural design process to improve both stability and selectivity.

            ## Recommendations

            - Refine structural modeling to improve pLDDT and docking scores, which are currently at baseline values.
- Incorporate additional constraints or diversity in the sequence design to enhance selectivity.
- Investigate the structural failures in more detail to identify common issues and address them in the next iteration.
- Consider using alternative scoring functions or validation methods to better assess structural stability and binding affinity.