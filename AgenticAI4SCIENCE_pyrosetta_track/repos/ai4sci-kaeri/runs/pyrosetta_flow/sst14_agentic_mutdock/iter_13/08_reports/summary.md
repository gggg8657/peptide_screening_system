# Iteration 13 Summary: sst14_mutdock_31000

            - **Run ID**: `sst14_mutdock_31000`
            - **Iteration**: 13
            - **생성 시각**: 2026-06-12 16:56 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 13 evaluated four peptide binder candidates for SSTR2, all of which passed the quality control (QC) gates. The designs demonstrated strong binding affinity, as evidenced by favorable ddG values ranging from -16.8 to -25.6 kcal/mol. However, the pLDDT and docking scores remained at 0.0 for all candidates, indicating a lack of structural confidence and docking performance. While the best Δmargin is positive, the overall pass rate for selectivity remains low, suggesting that off-target interactions are still a concern. The primary failure mode was structural failures, which highlights the need for improved structural stability and selectivity in future designs.

The top-performing candidate, iter13_cand008, exhibited the most favorable ddG of -25.6 kcal/mol, followed closely by iter13_cand007 with a ddG of -25.0 kcal/mol. These candidates should be prioritized for further analysis and experimental validation. However, the marginal improvements in selectivity suggest that the design strategy should be adjusted to focus on disrupting off-target contacts and enhancing structural integrity.

            ## Recommendations

            - Refine the design strategy to prioritize structural stability and selectivity over binding affinity alone.
- Focus on disrupting off-target contacts to improve the selectivity pass rate.
- Incorporate additional constraints or scoring terms to enhance pLDDT and docking performance.
- Conduct experimental validation of top candidates to confirm predicted binding and selectivity.