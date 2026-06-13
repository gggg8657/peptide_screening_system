# Iteration 3 Summary: sst14_mutdock_36000

            - **Run ID**: `sst14_mutdock_36000`
            - **Iteration**: 3
            - **생성 시각**: 2026-06-13 00:00 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 3 of the sst14_mutdock_36000 campaign evaluated five peptide binder candidates, all of which passed quality control (QC) gates. The primary focus of this iteration was to improve binding affinity as measured by ddG, and the results showed strong performance in this metric, with the top candidate (iter03_cand004) achieving a ddG of -43.1 kcal/mol. However, structural and docking data were not available for any of the candidates, as indicated by the pLDDT and docking score values of 0.0, suggesting incomplete modeling and a lack of structural validation. This highlights a critical gap in the evaluation process, as structural confidence is essential for reliable candidate selection.

            ## Recommendations

            - Prioritize the generation of structural and docking data for the top candidates in the next iteration to ensure a more complete evaluation.
- Investigate the reasons for the lack of selectivity improvement and consider incorporating additional selectivity metrics or constraints into the design process.
- Refine the modeling pipeline to address structural failures and ensure that pLDDT and docking scores are reliably computed for all candidates.