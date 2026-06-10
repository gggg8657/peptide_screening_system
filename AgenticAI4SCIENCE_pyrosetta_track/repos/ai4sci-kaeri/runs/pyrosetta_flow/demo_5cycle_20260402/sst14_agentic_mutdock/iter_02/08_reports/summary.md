# Iteration 2 Summary: sst14_mutdock_2026

            - **Run ID**: `sst14_mutdock_2026`
            - **Iteration**: 2
            - **생성 시각**: 2026-04-02 06:17 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated 7 candidate peptide binders for SSTR2 targeting. All candidates passed QC gates, but structural anomalies were observed in top performers. Notably, all top candidates exhibited pLDDT=0.0 and dock=0.00 scores, which deviate from expected structural validity. The highest ddG value of -40.9 kcal/mol (iter02_cand006) suggests strong binding potential, though structural concerns require validation. The 87.5% QC pass rate indicates minimal filtering issues, but the abnormal metrics necessitate further investigation into docking protocol reliability and structural modeling accuracy.

            ## Recommendations

            - Investigate structural validity of top candidates with abnormal pLDDT/dock scores using independent modeling tools
- Refine docking protocol parameters to resolve persistent zero-score artifacts
- Prioritize candidates with highest ddG values for experimental validation while addressing structural concerns
- Implement additional selectivity checks for off-target binding risks