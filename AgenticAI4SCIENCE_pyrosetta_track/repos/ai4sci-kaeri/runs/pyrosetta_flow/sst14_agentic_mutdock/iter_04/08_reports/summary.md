# Iteration 4 Summary: sst14_mutdock_21000

            - **Run ID**: `sst14_mutdock_21000`
            - **Iteration**: 4
            - **생성 시각**: 2026-06-11 23:43 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 4 of the SSTR2 peptide binder design campaign evaluated four candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was on stability and binding affinity, as evidenced by strong ddG values ranging from -16.8 to -46.7 kcal/mol. However, selectivity remains a critical challenge, with a wide range of selectivity scores observed among the top candidates. The best Δmargin is positive, but the overall selectivity pass rate is low, indicating that further optimization is necessary to improve target specificity. Structural failures were the primary cause of QC gate failures in previous iterations, but this iteration saw no such issues, suggesting that structural stability has been effectively addressed.

            ## Recommendations

            - Focus on improving selectivity in the next iteration by incorporating additional constraints or redesigning the binding interface to enhance specificity for SSTR2 over off-target receptors.
- Explore the top candidates (iter04_cand001, iter04_cand006, iter04_cand002) further for their strong ddG values, as they represent the most stable and potentially effective binders.
- Consider using experimental validation methods, such as SPR or ITC, to assess the binding affinity and selectivity of the top candidates in vitro.
- Refine the docking and scoring protocols to better capture selectivity metrics, potentially by integrating machine learning-based scoring functions.