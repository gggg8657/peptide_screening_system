# Iteration 6 Summary: sst14_mutdock_39000

            - **Run ID**: `sst14_mutdock_39000`
            - **Iteration**: 6
            - **생성 시각**: 2026-06-13 05:42 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 6 evaluated a total of 2 candidates, both of which passed all QC gates. Despite the 100% pass rate, the structural quality of the candidates remains a concern, as evidenced by pLDDT and docking scores of 0.0, indicating structural failures. The ddG values, however, show strong binding affinity, with the top candidate (iter06_cand004) achieving a ddG of -37.9 kcal/mol and the second candidate (iter06_cand007) at -28.6 kcal/mol. While these values are promising, there is no notable improvement in selectivity over the best Δmargin from previous iterations. This suggests that the current design strategy is not effectively balancing structural quality with functional performance. The primary failure mode in this iteration is structural, which must be addressed to ensure the production of viable binder candidates.

            ## Recommendations

            - Refine the structural modeling pipeline to improve pLDDT and docking scores.
- Incorporate additional constraints or filters to ensure structural quality is prioritized alongside binding affinity.
- Revisit the selectivity criteria and consider alternative metrics or benchmarks to better assess functional performance.