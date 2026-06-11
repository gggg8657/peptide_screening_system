# Iteration 1 Summary: sst14_mutdock_17000

            - **Run ID**: `sst14_mutdock_17000`
            - **Iteration**: 1
            - **생성 시각**: 2026-06-11 16:30 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 1 of the SSTR2 peptide binder design campaign evaluated a total of 5 candidates, all of which passed the quality control (QC) gates. The candidates demonstrated strong binding affinities to SSTR2, as indicated by favorable ddG values ranging from -17.5 to -30.1 kcal/mol. However, the primary limitation identified was the lack of sufficient selectivity, particularly against SSTR3 and SSTR5. While the best Δmargin values were positive, they remained relatively low (4.25–9.10), indicating a need for improved off-target discrimination. Structural failures were noted as the primary failure type, suggesting that further refinement of structural features is necessary to enhance both binding and selectivity.

The top-performing candidates in this iteration were iter01_cand001 (ddG = -30.1), iter01_cand007 (ddG = -28.9), and iter01_cand002 (ddG = -27.8). Despite their strong binding potential, the overall selectivity profile remains suboptimal for clinical application. The next iteration should focus on optimizing structural elements to improve selectivity while maintaining strong SSTR2 binding.

            ## Recommendations

            - Focus on structural modifications to enhance selectivity against SSTR3 and SSTR5.
- Incorporate additional constraints in the design pipeline to prioritize off-target discrimination.
- Revisit the scoring function to better reflect selectivity in candidate prioritization.