# Iteration 13 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 13
            - **생성 시각**: 2026-06-12 10:48 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 13 evaluated three candidates, all of which passed the quality control (QC) gates. However, the structural quality of the top candidates was poor, as indicated by pLDDT values of 0.0 for all three. Despite this limitation, the candidates exhibited strong binding affinities, with ddG values ranging from -17.1 to -34.7 kcal/mol. Docking scores were not informative (0.00), and while selectivity margins were positive, the designs have not yet consistently outperformed native SST-14 in this regard. The primary failure mode in this iteration was structural instability, suggesting a need for improved structural modeling or refinement strategies.

The top candidates, iter13_cand005, iter13_cand006, and iter13_cand007, show promise in terms of binding energy but require structural validation and optimization. The lack of structural confidence highlights the importance of integrating structural refinement techniques in the next iteration to ensure both strong binding and high structural quality. Overall, while the iteration demonstrates progress in binding affinity, structural improvements are critical for advancing viable candidates.

            ## Recommendations

            - Implement structural refinement techniques to improve pLDDT scores and overall structural quality.
- Focus on balancing binding affinity (ddG) with structural stability in the next iteration.
- Revisit the selectivity criteria to ensure designs consistently outperform native SST-14.