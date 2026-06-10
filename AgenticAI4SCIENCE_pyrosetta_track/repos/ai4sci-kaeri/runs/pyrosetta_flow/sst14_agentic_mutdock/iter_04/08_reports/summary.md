# Iteration 4 Summary: sst14_mutdock_1000

            - **Run ID**: `sst14_mutdock_1000`
            - **Iteration**: 4
            - **생성 시각**: 2026-06-10 07:33 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 4 of the SSTR2 peptide binder design campaign evaluated five candidates, all of which passed quality control (QC) gates. The designs demonstrated strong binding affinity to the target, with ddG values ranging from -5.4 to -22.1 kcal/mol. The most favorable binder, iter04_cand002, exhibited the lowest ddG of -22.1 kcal/mol. However, the primary limitation of this iteration was a lack of selectivity for SSTR2 over other somatostatin receptor subtypes, particularly SSTR3 and SSTR5, as all candidates failed to achieve a Δmargin > 0. This off-target binding represents a critical barrier to advancing these designs toward experimental validation.

Structural failures were identified as the main cause of selectivity issues, suggesting that the current designs may not adequately differentiate the SSTR2 binding pocket from those of other subtypes. While the binding affinity is promising, the absence of selectivity indicates a need for targeted modifications to enhance specificity. The next iteration should focus on structural optimization strategies to improve selectivity while maintaining strong binding affinity.

            ## Recommendations

            - Focus on structural modifications to enhance SSTR2 selectivity, particularly by targeting residues that differentiate the SSTR2 binding pocket from SSTR3 and SSTR5.
- Incorporate selectivity constraints into the design pipeline to prioritize candidates with favorable Δmargin values.
- Revisit the docking and scoring protocols to better capture selectivity-related interactions.
- Conduct a detailed analysis of the structural failures to identify common motifs or interactions contributing to off-target binding.