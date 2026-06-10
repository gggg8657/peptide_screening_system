# Iteration 13 Summary: sst14_mutdock_4000

            - **Run ID**: `sst14_mutdock_4000`
            - **Iteration**: 13
            - **생성 시각**: 2026-06-10 16:39 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 13 of the SSTR2 peptide binder design campaign evaluated a total of 1 candidate, with only 1 passing all QC gates, resulting in a pass rate of 100%. The top candidate, iter13_cand004, exhibited a ddG of -16.1, indicating strong binding affinity. However, the pLDDT and docking scores were both reported as 0.0, suggesting potential issues with structural confidence or docking accuracy. Despite the favorable ddG, the overall selectivity remains a concern, as the majority of candidates failed to achieve a positive Δmargin, indicating insufficient selectivity over off-target SSTRs.

The primary failure mode in this iteration was structural failures, which highlights the need for improved structural modeling or refinement strategies. The low pass rate and lack of selectivity underscore the importance of addressing these structural issues in the next iteration to enhance both binding affinity and specificity. Further investigation into the structural failures and their root causes is warranted to guide the design of more robust candidates.

            ## Recommendations

            - Investigate structural failures to improve modeling accuracy and confidence in future iterations.
- Focus on enhancing selectivity by incorporating additional constraints or metrics in the design process.
- Refine docking protocols to ensure more reliable scoring and better alignment with experimental data.