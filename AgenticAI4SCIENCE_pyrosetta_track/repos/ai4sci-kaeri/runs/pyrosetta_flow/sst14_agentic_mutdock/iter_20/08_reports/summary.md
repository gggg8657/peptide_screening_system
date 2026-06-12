# Iteration 20 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 20
            - **생성 시각**: 2026-06-12 11:25 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 20 evaluated a total of 2 candidates, both of which passed all QC gates. Despite the small number of candidates, the iteration demonstrated strong binding affinity as indicated by favorable ddG values, with the best candidate achieving a ddG of -27.1 kcal/mol. However, the absence of pLDDT and docking scores suggests that structural quality and docking reliability remain significant challenges. The top candidates, iter20_cand008 and iter20_cand007, showed promising ddG values of -27.1 and -21.9 kcal/mol, respectively, but lacked structural validation metrics. Selectivity was strong, with a Δmargin of 9.1021, indicating potential for improved target specificity. However, the primary failure mode was structural instability, which highlights the need for enhanced structural modeling and validation in future iterations.

            ## Recommendations

            - Prioritize structural modeling improvements to address instability and ensure reliable pLDDT and docking scores.
- Incorporate additional QC checks focused on structural quality to filter out candidates with poor geometry.
- Explore design strategies that enhance both binding affinity and structural stability simultaneously.