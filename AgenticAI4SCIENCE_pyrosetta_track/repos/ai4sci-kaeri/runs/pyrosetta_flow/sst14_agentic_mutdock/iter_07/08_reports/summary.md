# Iteration 7 Summary: sst14_mutdock_5000

            - **Run ID**: `sst14_mutdock_5000`
            - **Iteration**: 7
            - **생성 시각**: 2026-06-10 17:51 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 7 evaluated four SSTR2 peptide binder candidates, all of which passed quality control (QC) gates. The designs exhibited strong binding affinity, as indicated by ddG values ranging from -21.5 to -27.3 kcal/mol. However, selectivity for SSTR2 over off-target receptors remained a significant challenge. Only one candidate (AECMNFFWKTFTSC) demonstrated selectivity with a Δmargin > 0, while the remaining candidates showed Δmargin ≤ 0, suggesting off-target interactions that compromise specificity. This highlights a critical bottleneck in the design process, with structural failures being the primary failure type. Despite the promising binding affinity, the low selectivity pass rate indicates a need for refinement in the design strategy to enhance SSTR2 specificity.

            ## Recommendations

            - Refine the design strategy to prioritize SSTR2 selectivity, focusing on minimizing off-target interactions.
- Incorporate additional constraints or scoring functions to better capture selectivity during the design phase.
- Revisit structural failures to identify common motifs or issues that may be addressed in future iterations.