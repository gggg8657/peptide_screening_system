# Iteration 8 Summary: sst14_mutdock_17000

            - **Run ID**: `sst14_mutdock_17000`
            - **Iteration**: 8
            - **생성 시각**: 2026-06-11 17:03 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 8 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, with both passing all QC gates. However, the overall pass rate was low at 25%, indicating a significant issue with structural quality. The top candidates, iter08_cand006 and iter08_cand005, exhibited pLDDT values of 0.0, suggesting poor structural confidence. While iter08_cand006 showed the most favorable ddG value of -75.0 kcal/mol, its docking score of 0.00 indicates a lack of meaningful binding interaction. iter08_cand005 had a less favorable ddG of -26.1 kcal/mol but shared the same structural and docking limitations. The primary failure mode in this iteration was structural failures, which dominated the QC gate failures despite selectivity (Δmargin) being positive for the top candidates. This highlights the need to address structural prediction accuracy in future iterations.

            ## Recommendations

            - Improve structural prediction methods to increase pLDDT values and reduce structural failures.
- Investigate the root causes of poor docking scores and consider refining docking protocols.
- Focus on generating candidates with higher structural confidence to improve overall pass rates.
- Revisit selectivity metrics to ensure they align with structural and binding quality improvements.