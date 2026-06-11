# Iteration 1 Summary: sst14_mutdock_8000

            - **Run ID**: `sst14_mutdock_8000`
            - **Iteration**: 1
            - **생성 시각**: 2026-06-10 23:49 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 1 of the SSTR2 peptide binder design campaign evaluated a total of 8 candidate designs, of which only 2 passed all quality control (QC) gates, resulting in a low pass rate of 25%. The two successful candidates, iter01_cand008 and iter01_cand005, exhibited strong predicted binding affinities, with ddG values of -19.4 and -17.4 kcal/mol, respectively. However, both candidates reported pLDDT values of 0.0, indicating structural uncertainties that may compromise their reliability as viable designs. Additionally, the docking scores for both candidates were reported as 0.00, suggesting either an absence of meaningful docking data or a potential issue in the scoring pipeline. While the best Δmargin was positive (8.6866), the overall selectivity across the top candidates remains inconsistent, with off-target binding to SSTR3 and SSTR5 being a notable concern.

The primary failure mode observed in this iteration was structural failures, underscoring the need for improved structural modeling and validation strategies. The low pass rate and lack of consistent selectivity suggest that the current design parameters may not be sufficient to generate robust and specific SSTR2 binders. These findings highlight the importance of refining the design space and incorporating additional constraints to improve structural stability and target specificity in future iterations.

            ## Recommendations

            - Refine the structural modeling pipeline to improve pLDDT scores and reduce structural failures.
- Incorporate additional selectivity constraints to minimize off-target binding to SSTR3 and SSTR5.
- Evaluate and improve the docking scoring methodology to ensure meaningful and reliable docking scores.
- Expand the design space with more diverse sequence and structural features to increase the likelihood of generating high-quality candidates.