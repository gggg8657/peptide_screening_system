# Iteration 12 Summary: sst14_mutdock_13000

            - **Run ID**: `sst14_mutdock_13000`
            - **Iteration**: 12
            - **생성 시각**: 2026-06-11 10:22 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 12 evaluated three candidates for their potential as SSTR2 peptide binders. All three candidates passed the quality control (QC) gates, but none met the structural quality and docking score thresholds. The primary issue identified was structural failure, as all candidates exhibited a pLDDT of 0.0 and docking scores of 0.00, indicating poor structural confidence and docking performance. Despite this, the ddG binding scores were strong, with the best candidate (iter12_cand006) showing a ddG of -26.9 kcal/mol. Selectivity remained positive, suggesting that the candidates retain favorable binding specificity for the target. However, the structural failures prevent these candidates from progressing to the next stage of development.

            ## Recommendations

            - Revisit the structural modeling pipeline to improve pLDDT scores and docking performance in the next iteration.
- Investigate the root causes of structural failures, such as sequence design or modeling parameters.
- Maintain focus on ddG and selectivity as these metrics remain favorable, but prioritize structural quality improvements.