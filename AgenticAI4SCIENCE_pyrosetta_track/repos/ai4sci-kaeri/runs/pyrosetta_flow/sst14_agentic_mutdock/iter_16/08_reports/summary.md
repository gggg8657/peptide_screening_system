# Iteration 16 Summary: sst14_mutdock_31000

            - **Run ID**: `sst14_mutdock_31000`
            - **Iteration**: 16
            - **생성 시각**: 2026-06-12 17:07 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 16 of the SSTR2 peptide binder design campaign evaluated four candidates, all of which passed the quality control (QC) gates. The designs demonstrated strong binding affinity, as indicated by ddG values ranging from -20.2 to -37.2 kcal/mol. However, the primary objective of achieving SSTR2 selectivity over off-target receptors remains unmet. Critically, the best Δmargin for selectivity was positive but not significantly above the native SST-14 baseline, indicating that the current designs lack the necessary specificity to distinguish SSTR2 from other targets. This failure is categorized under structural_failures, suggesting that the binding mode or structural features may not be optimized for selectivity.

            ## Recommendations

            - Refine the structural design to enhance SSTR2 selectivity, focusing on key residues or interactions that differentiate SSTR2 from off-target receptors.
- Incorporate selectivity metrics more explicitly into the design and scoring framework to prioritize candidates with improved specificity.
- Conduct a detailed analysis of the binding modes of the top candidates to identify structural features that may be contributing to the lack of selectivity.
- Consider introducing additional constraints or penalties in the design process to favor selectivity over affinity when the two conflict.