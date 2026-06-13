# Iteration 15 Summary: sst14_mutdock_42000

            - **Run ID**: `sst14_mutdock_42000`
            - **Iteration**: 15
            - **생성 시각**: 2026-06-13 11:13 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 15 evaluated four candidates, all of which passed quality control (QC) gates. The primary focus of this iteration was to improve binding affinity and selectivity for the SSTR2 receptor. While the ddG values indicate strong binding (ranging from -19.8 to -42.6 kcal/mol), the selectivity margin (Δmargin) remains suboptimal, with the best Δmargin being positive but not robust enough to ensure consistent SSTR2 selectivity over off-targets. This suggests that while the candidates exhibit favorable binding affinities, further optimization is needed to enhance their selectivity profile.

The top-performing candidate, iter15_cand007, demonstrated the lowest ddG of -42.6 kcal/mol, indicating the strongest binding affinity among the four. However, the lack of pLDDT and docking score data raises questions about the structural reliability of the predicted models. Structural failures were identified as the primary failure type, highlighting the need for improved structural modeling in the next iteration to ensure both strong binding and structural integrity.

            ## Recommendations

            - Prioritize structural modeling improvements to ensure reliable pLDDT and docking scores for future candidates.
- Focus on enhancing selectivity margins (Δmargin) to achieve robust SSTR2 selectivity over off-targets.
- Consider incorporating additional selectivity filters in the design pipeline to preemptively eliminate candidates with low selectivity potential.