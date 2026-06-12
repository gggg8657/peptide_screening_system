# Iteration 5 Summary: sst14_mutdock_21000

            - **Run ID**: `sst14_mutdock_21000`
            - **Iteration**: 5
            - **생성 시각**: 2026-06-11 23:46 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 5 of the SSTR2 peptide binder design campaign evaluated four candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was to improve SSTR2 selectivity while maintaining strong binding affinity. While the candidates demonstrated strong ddG binding scores, ranging from -15.1 to -28.7 kcal/mol, selectivity over the native SST-14 remained a challenge. Notably, no significant improvements in selectivity were observed, indicating that the current design strategy may not be sufficient to achieve the desired specificity.

The top-performing candidates, iter05_cand004 and iter05_cand005, exhibited the most favorable ddG values of -28.7 and -28.0 kcal/mol, respectively. However, the lack of structural data (pLDDT and docking scores remain at default values) suggests potential limitations in structural accuracy or docking reliability. The primary failure mode observed in this iteration was structural failures, which may have hindered the ability to optimize selectivity. These findings highlight the need for a revised design approach to address structural limitations and enhance SSTR2 selectivity.

            ## Recommendations

            - Revisit the structural modeling pipeline to improve pLDDT and docking accuracy for better selectivity prediction.
- Incorporate additional selectivity filters or constraints in the design process to prioritize SSTR2-specific interactions.
- Consider exploring alternative scaffold designs or mutations that may enhance both binding affinity and selectivity.
- Perform a more detailed analysis of structural failure modes to identify and address underlying issues in the design workflow.