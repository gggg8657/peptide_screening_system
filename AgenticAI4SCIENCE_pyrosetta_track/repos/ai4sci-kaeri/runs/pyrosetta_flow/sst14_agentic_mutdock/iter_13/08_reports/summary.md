# Iteration 13 Summary: sst14_mutdock_24000

            - **Run ID**: `sst14_mutdock_24000`
            - **Iteration**: 13
            - **생성 시각**: 2026-06-12 05:20 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 13 evaluated a total of 3 candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was to improve binding affinity, as evidenced by strong ddG values ranging from -18.0 to -33.0 kcal/mol. However, the structural quality of the designs remains a significant concern, with all candidates reporting pLDDT scores of 0.0, indicating poor confidence in their predicted structures. Selectivity metrics did not show improvement, with the best Δmargin remaining at 9.1021. The low pass rate of 37.5% suggests that the overall design space is still suboptimal for generating structurally viable SSTR2 binders.

The top candidates in this iteration are iter13_cand001 (ddG=-33.0), iter13_cand007 (ddG=-26.7), and iter13_cand002 (ddG=-18.0). Despite their strong binding affinities, the lack of structural confidence limits their potential for further development. The primary failure mode is attributed to structural failures, highlighting the need for improved structural modeling in the next iteration.

            ## Recommendations

            - Prioritize improvements in structural modeling to increase pLDDT scores and overall structural confidence.
- Incorporate additional constraints or filters to enhance selectivity metrics beyond the current Δmargin threshold.
- Expand the design space to increase the pass rate and generate a larger pool of viable candidates for evaluation.