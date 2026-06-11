# Iteration 6 Summary: sst14_mutdock_17000

            - **Run ID**: `sst14_mutdock_17000`
            - **Iteration**: 6
            - **생성 시각**: 2026-06-11 16:52 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 6 evaluated three candidate peptides for their potential as SSTR2 binders. All candidates passed quality control (QC) gates, but structural quality, as indicated by pLDDT scores, was uniformly poor (pLDDT=0.0 across all candidates). Despite this limitation, the candidates demonstrated strong binding affinities, with ddG values ranging from -23.8 to -38.4 kcal/mol. The docking scores were not informative (0.00), likely due to structural uncertainties. Selectivity improvements were noted (Δmargin > 0), but the margin remains insufficient to guarantee SSTR2 specificity over off-target receptors.

The top performer, iter06_cand004, exhibited the lowest ddG (-38.4 kcal/mol), suggesting strong binding potential. However, the lack of structural confidence (pLDDT=0.0) raises concerns about its feasibility for experimental validation. The primary failure mode in this iteration was structural failure, indicating a need to prioritize structural quality in future design cycles.

            ## Recommendations

            - Prioritize structural quality (pLDDT) in the next iteration to ensure reliable candidate designs.
- Incorporate additional selectivity constraints to improve the margin over off-target receptors.
- Revisit the docking protocol to ensure it is robust and informative for future iterations.