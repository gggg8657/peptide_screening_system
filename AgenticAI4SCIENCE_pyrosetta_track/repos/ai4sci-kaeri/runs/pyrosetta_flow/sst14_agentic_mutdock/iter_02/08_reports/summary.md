# Iteration 2 Summary: sst14_mutdock_1000

            - **Run ID**: `sst14_mutdock_1000`
            - **Iteration**: 2
            - **생성 시각**: 2026-06-10 07:17 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 2 of the SSTR2 peptide binder design campaign evaluated a total of 3 candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was to assess binding affinity and selectivity for SSTR2. While the candidates demonstrated strong binding affinities, as indicated by ddG values ranging from -23.8 to -32.7 kcal/mol, none achieved the desired selectivity threshold for SSTR2 over off-target receptors such as SSTR3 and SSTR5. This lack of selectivity is attributed to conserved pocket contacts that promote off-target binding.

The top-performing candidates, iter02_cand004, iter02_cand003, and iter02_cand007, exhibited the lowest ddG values, suggesting high binding affinity. However, the absence of selectivity remains a critical limitation. The structural failure type identified in the Critic analysis suggests that the design strategy should be refined to avoid conserved interaction motifs that contribute to off-target binding. Future iterations should prioritize structural modifications that enhance SSTR2 specificity.

            ## Recommendations

            - Refine the design strategy to avoid conserved interaction motifs that promote off-target binding to SSTR3 and SSTR5.
- Incorporate structural constraints or modifications that enhance SSTR2 specificity.
- Consider introducing steric or electrostatic features that differentiate the SSTR2 binding pocket from other SSTR subtypes.