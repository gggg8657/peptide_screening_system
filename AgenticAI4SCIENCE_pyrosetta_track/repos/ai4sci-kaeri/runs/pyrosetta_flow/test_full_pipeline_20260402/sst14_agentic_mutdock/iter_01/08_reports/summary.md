# Iteration 1 Summary: sst14_mutdock_9999

            - **Run ID**: `sst14_mutdock_9999`
            - **Iteration**: 1
            - **생성 시각**: 2026-04-02 11:19 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated 7 candidate SSTR2 peptide binders, all of which passed QC gates. However, all candidates exhibited structural quality failures, with pLDDT=0.0 and docking scores=0.00, indicating poor model sampling and structural validity. While ddG values suggest favorable binding free energy, the structural metrics indicate unreliable predictions. The top candidates (iter01_cand002 to iter01_cand003) demonstrate a gradient of ddG values from -39.1 to -7.2, with iter01_cand002 showing the most favorable binding energy. Structural refinement and parameter adjustments are urgently required to improve model quality before progressing to subsequent iterations.

            ## Recommendations

            - Adjust sampling parameters to improve structural model quality
- Re-evaluate docking protocol for better energy landscape sampling
- Prioritize refinement of high-ddG candidates with structural validation