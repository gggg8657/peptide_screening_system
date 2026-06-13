# Iteration 14 Summary: sst14_mutdock_35000

            - **Run ID**: `sst14_mutdock_35000`
            - **Iteration**: 14
            - **생성 시각**: 2026-06-12 23:24 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 14 of the SSTR2 peptide binder design campaign evaluated a single candidate, with only one passing all QC gates. Despite the low pass rate (12.5%), the sole candidate that passed, iter14_cand008, exhibited a favorable ddG value of -19.0, indicating strong binding affinity. However, the structural quality of the candidate was poor, as evidenced by a pLDDT of 0.0 and a docking score of 0.00, suggesting that structural failures were the primary cause of QC gate rejection. This highlights a critical bottleneck in the design process, where structural accuracy remains a limiting factor for candidate progression.

The low structural quality observed in this iteration underscores the need for improvements in modeling and refinement strategies. While selectivity (Δmargin) remains positive for the best candidates, the lack of structural confidence limits the reliability of predicted performance. Future iterations should focus on enhancing structural prediction accuracy and exploring alternative design strategies to improve the overall quality of generated candidates.

            ## Recommendations

            - Enhance structural prediction methods to improve pLDDT and docking scores in future iterations.
- Investigate alternative design strategies to increase the diversity and structural quality of candidates.
- Implement additional QC checks focused on structural validation to preemptively filter out poor-quality candidates.