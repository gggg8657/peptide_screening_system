# Iteration 14 Summary: sst14_mutdock_42000

            - **Run ID**: `sst14_mutdock_42000`
            - **Iteration**: 14
            - **생성 시각**: 2026-06-13 11:05 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 14 (sst14_mutdock_42000) evaluated a total of 2 candidates, with both passing all QC gates. However, the structural quality of the candidates was poor, as indicated by pLDDT values of 0.0 for both iter14_cand001 and iter14_cand002. The docking scores were not computed (0.00), and the ddG values ranged from -15.6 to -34.0, with iter14_cand001 showing the most favorable binding energy. Despite moderate selectivity (Δmargin > 0), the low pass rate (25%) and structural failures suggest a need for improved structural modeling in the next iteration. The primary failure mode was structural, indicating that the design process should focus on enhancing structural accuracy to improve overall candidate quality.

            ## Recommendations

            - Improve structural modeling to increase pLDDT values and reduce structural failures.
- Investigate the cause of the low pass rate and optimize the design pipeline to enhance candidate quality.
- Focus on refining the binding interface to improve both ddG and selectivity metrics.