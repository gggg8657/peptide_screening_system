# Iteration 2 Summary: sst14_mutdock_43000

            - **Run ID**: `sst14_mutdock_43000`
            - **Iteration**: 2
            - **생성 시각**: 2026-06-13 12:00 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 2 of the SSTR2 peptide binder design campaign evaluated a total of 3 candidates, all of which passed the quality control (QC) gates. Despite this 100% pass rate, the overall progress toward the primary objective of achieving SSTR2 selectivity remains limited. The best candidate, iter02_cand004, exhibited a favorable ddG of -29.4 kcal/mol, indicating strong binding affinity. However, the pLDDT and docking scores remain at default values (0.0), suggesting that structural predictions or docking simulations may not have been fully implemented or validated in this iteration. The selectivity margin relative to native SST-14 is positive but not significantly higher, and off-target interactions with SSTR3 and SSTR5 remain a concern.

The primary failure mode in this iteration was structural failures, which may have impacted the ability to assess true selectivity and binding behavior. While the ddG scores of the top candidates are promising, the lack of meaningful pLDDT and docking data limits the confidence in their structural accuracy and binding modes. The next iteration should focus on refining the structural modeling pipeline and incorporating more rigorous selectivity assessments to address the off-target interactions.

            ## Recommendations

            - Improve the structural modeling pipeline to ensure accurate pLDDT and docking scores for better candidate evaluation.
- Incorporate more detailed selectivity assessments, particularly against SSTR3 and SSTR5, to reduce off-target interactions.
- Expand the design space to increase the likelihood of identifying candidates with significantly improved SSTR2 selectivity.