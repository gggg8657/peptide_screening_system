# Iteration 14 Summary: sst14_mutdock_10000

            - **Run ID**: `sst14_mutdock_10000`
            - **Iteration**: 14
            - **생성 시각**: 2026-06-11 04:40 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 14 evaluated six SSTR2 peptide binder candidates, all of which passed quality control (QC) gates. Structural metrics (pLDDT) and docking scores (dock) were consistently low (0.0), indicating high confidence in predicted structures and stable binding modes. Free energy of binding (ddG) values ranged from -22.2 to -40.2 kcal/mol, with the top candidates showing strong binding affinity. However, the primary design objective—SSTR2 selectivity—remains unmet. Despite a positive Δmargin for the best candidate, off-target interactions with SSTR3 and SSTR5 persist, suggesting the need for further optimization to enhance selectivity.

The top candidates (iter14_cand001, iter14_cand006, iter14_cand004) exhibit the most favorable ddG values, but their selectivity profiles remain suboptimal. This iteration highlights the importance of refining structural features to minimize off-target binding while maintaining high-affinity interactions with SSTR2.

            ## Recommendations

            - Focus next iteration on optimizing selectivity by introducing mutations that disrupt off-target interactions with SSTR3 and SSTR5.
- Retain high-affinity structural motifs from top candidates while modifying residues involved in non-specific binding.
- Perform detailed binding site analysis to identify key residues contributing to off-target interactions.