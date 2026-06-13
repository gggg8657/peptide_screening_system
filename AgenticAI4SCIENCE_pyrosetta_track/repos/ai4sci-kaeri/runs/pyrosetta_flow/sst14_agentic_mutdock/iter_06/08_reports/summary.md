# Iteration 6 Summary: sst14_mutdock_43000

            - **Run ID**: `sst14_mutdock_43000`
            - **Iteration**: 6
            - **생성 시각**: 2026-06-13 12:14 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 6 evaluated three candidates, all of which passed the quality control (QC) gates. Despite the small number of candidates, the results showed strong binding affinities as indicated by ddG values ranging from -16.3 to -26.9 kcal/mol. However, the structural quality of the top candidates remains a concern, as all candidates exhibited a pLDDT score of 0.0, suggesting significant structural inaccuracies. The pass rate for this iteration was 37.5%, which is relatively low given the small cohort size. Selectivity metrics were above zero, but the Δmargin did not show significant improvement, indicating a lack of progress in distinguishing high-affinity binders from lower-affinity ones.

            ## Recommendations

            - Prioritize structural refinement of top candidates to improve pLDDT scores and overall model quality.
- Investigate the source of structural failures to determine if adjustments in modeling protocols or constraints are needed.
- Consider increasing the cohort size in the next iteration to better assess selectivity and improve the pass rate.
- Monitor the Δmargin more closely to ensure progress in differentiating high-affinity binders from lower-affinity ones.