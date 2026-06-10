# Iteration 8 Summary: sst14_mutdock_5000

            - **Run ID**: `sst14_mutdock_5000`
            - **Iteration**: 8
            - **생성 시각**: 2026-06-10 17:59 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 8 of the SSTR2 peptide binder design campaign evaluated a total of 3 candidates, all of which passed the quality control (QC) gates. Despite the small number of candidates, the iteration yielded some promising ddG values, with the most favorable being -46.9 kcal/mol for iter08_cand006. However, structural metrics such as pLDDT and docking scores were not available (0.0), indicating potential limitations in structural modeling or docking reliability. Selectivity remains a significant challenge, with only one candidate (AECMNFFWKTFTSC) showing a Δmargin > 0. None of the candidates surpassed native SST-14 in selectivity, underscoring the need for further optimization in this area.

The low pass rate (37.5%) and structural failures observed in this iteration suggest that the design space may be constrained or that the current modeling approaches are not capturing structural nuances effectively. The primary failure type was structural_failures, which may be attributed to poor backbone modeling or inadequate sampling of conformational space. These findings highlight the importance of refining the design strategy and exploring alternative modeling techniques to improve structural accuracy and selectivity in the next iteration.

            ## Recommendations

            - Expand the design space to include more diverse sequences and structural motifs to improve selectivity and structural stability.
- Investigate alternative modeling approaches or refine current protocols to address structural failures and improve pLDDT and docking score accuracy.
- Focus on optimizing candidates with the most favorable ddG values while ensuring they meet selectivity criteria.
- Revisit the native SST-14 benchmark to identify key interactions that could be mimicked or enhanced in the designed peptides.