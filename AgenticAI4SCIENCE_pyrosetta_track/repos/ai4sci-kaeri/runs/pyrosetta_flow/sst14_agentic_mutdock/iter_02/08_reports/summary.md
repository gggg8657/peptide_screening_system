# Iteration 2 Summary: sst14_mutdock_17000

            - **Run ID**: `sst14_mutdock_17000`
            - **Iteration**: 2
            - **생성 시각**: 2026-06-11 16:34 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 2 of the sst14_mutdock_17000 campaign evaluated four candidate peptides for their binding affinity and structural stability. All four candidates passed the quality control (QC) gates, indicating no immediate structural failures. The primary focus of this iteration was to assess improvements in stability (as measured by ddG) and selectivity over the native SST-14 ligand. While the candidates demonstrated strong stability, with ddG values ranging from -21.0 to -44.4 kcal/mol, selectivity gains were limited. Notably, the top candidates did not consistently surpass the native SST-14 selectivity threshold, suggesting that further optimization is required to achieve the desired specificity.

The top-performing candidate, iter02_cand003, exhibited the most favorable ddG value of -44.4 kcal/mol, indicating high stability. However, the pLDDT and docking scores remained at baseline values (0.0), which may suggest limitations in the current design or scoring methods. The lack of improvement in these metrics highlights the need for a more refined approach to structural modeling and docking accuracy in future iterations.

            ## Recommendations

            - Refine the structural modeling pipeline to improve pLDDT and docking score predictions.
- Incorporate additional selectivity metrics or experimental validation to better assess performance relative to native SST-14.
- Focus on optimizing the binding interface to enhance both stability and specificity in the next iteration.