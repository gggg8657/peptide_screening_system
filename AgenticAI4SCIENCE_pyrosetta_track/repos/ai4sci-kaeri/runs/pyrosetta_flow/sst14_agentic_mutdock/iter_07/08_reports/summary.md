# Iteration 7 Summary: sst14_mutdock_39000

            - **Run ID**: `sst14_mutdock_39000`
            - **Iteration**: 7
            - **생성 시각**: 2026-06-13 05:51 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 7 evaluated five candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was on stability, as reflected in the ddG values, which ranged from -20.8 to -37.6 kcal/mol. These results indicate strong binding stability for the top candidates. However, the selectivity (Δmargin) remains a significant concern, with the best Δmargin being positive but some candidates only marginally above zero. This suggests that while the designs are stable, off-target binding is still a challenge that requires further optimization.

The top candidates, iter07_cand004, iter07_cand003, and iter07_cand007, showed the most favorable ddG values, but the lack of meaningful pLDDT and docking scores indicates a potential issue with structural modeling or scoring accuracy. The primary failure type observed was structural failures, which may be linked to the low pLDDT and docking scores. These findings highlight the need for improved structural modeling and more accurate scoring methods to enhance selectivity and ensure robust target specificity.

            ## Recommendations

            - Improve structural modeling and scoring accuracy to obtain meaningful pLDDT and docking scores.
- Focus on enhancing selectivity by optimizing the Δmargin to ensure robust target specificity.
- Investigate the structural failures observed in this iteration to refine the design process.