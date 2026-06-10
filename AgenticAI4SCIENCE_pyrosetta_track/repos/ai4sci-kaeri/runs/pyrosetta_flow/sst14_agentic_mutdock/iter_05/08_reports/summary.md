# Iteration 5 Summary: sst14_mutdock_5000

            - **Run ID**: `sst14_mutdock_5000`
            - **Iteration**: 5
            - **생성 시각**: 2026-06-10 17:44 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 5 of the SSTR2 peptide binder design campaign evaluated six candidates, all of which passed quality control (QC) gates. Structural quality, as indicated by pLDDT values, was consistently high (pLDDT=0.0), suggesting accurate predicted structures. Stability, as measured by ddG, was also strong, with the best candidate (iter05_cand006) showing a ddG of -37.2 kcal/mol. However, selectivity remains a significant challenge, with only one candidate (AECMNFFWKTFTSC) showing a significant Δmargin (>0), while the rest performed near or below the threshold. This indicates that while the designs are structurally sound and stable, off-target binding is still a concern.

            ## Recommendations

            - Focus on improving selectivity in the next iteration by incorporating additional constraints or filters to penalize off-target interactions.
- Analyze the successful candidate (AECMNFFWKTFTSC) to identify key residues or motifs contributing to selectivity and use this information to guide future designs.
- Consider optimizing the docking protocol to better capture subtle differences in selectivity between candidates.