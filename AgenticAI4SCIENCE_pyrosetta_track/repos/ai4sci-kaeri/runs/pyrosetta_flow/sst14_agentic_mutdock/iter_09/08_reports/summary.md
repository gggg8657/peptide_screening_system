# Iteration 9 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 9
            - **생성 시각**: 2026-06-12 10:34 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 9 of the SSTR2 peptide binder design campaign evaluated a single candidate, with 100% of the candidates passing all QC gates. The sole candidate, iter09_cand008, demonstrated a ΔG binding value of -30.2 kcal/mol, indicating strong predicted binding affinity. However, the pLDDT and docking scores were both reported as 0.0, suggesting potential issues with structural confidence or docking accuracy. Despite the strong Δmargin of 9.1021, the low overall pass rate (12.5% in the broader context of the campaign) indicates systemic challenges in structural or sequence design, or insufficient optimization for selectivity.

            ## Recommendations

            - Investigate the structural confidence (pLDDT) and docking accuracy of iter09_cand008 to determine if the low scores are due to computational limitations or genuine design issues.
- Focus on improving the structural design pipeline to increase the yield of candidates passing QC gates, particularly addressing the primary failure type of structural failures.
- Enhance selectivity optimization strategies to ensure candidates not only bind strongly but also exhibit the desired specificity for SSTR2.