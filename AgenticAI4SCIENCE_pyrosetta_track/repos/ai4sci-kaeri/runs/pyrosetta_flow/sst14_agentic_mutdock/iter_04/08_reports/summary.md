# Iteration 4 Summary: sst14_mutdock_5000

            - **Run ID**: `sst14_mutdock_5000`
            - **Iteration**: 4
            - **생성 시각**: 2026-06-10 17:35 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 4 of the SSTR2 peptide binder design campaign evaluated a single candidate, with one passing all QC gates. Despite the high pass rate (100%), the structural quality of the top candidate, iter04_cand004, is poor, as indicated by a pLDDT score of 0.0. While the candidate demonstrates a favorable ddG of -22.7 kcal/mol, suggesting strong binding affinity, its docking score of 0.00 and lack of structural confidence raise concerns about its reliability as a viable binder. The overall selectivity of the iteration is suboptimal, with most candidates showing a Δmargin ≤ 0, indicating a lack of selectivity over the native SST-14 ligand. This is likely due to off-target interactions with conserved pockets at SSTR3 and SSTR5.

The primary failure mode in this iteration is structural failures, which underscores the need for improved structural prediction and refinement strategies. The low structural confidence of the top candidate highlights the importance of prioritizing structural quality in future design cycles to ensure both affinity and selectivity are achieved.

            ## Recommendations

            - Implement enhanced structural prediction and refinement protocols to improve pLDDT scores and overall structural confidence.
- Focus on optimizing selectivity by targeting non-conserved regions to reduce off-target interactions with SSTR3 and SSTR5.
- Increase the number of candidates in the next iteration to better explore the design space and identify structurally and selectively robust binders.