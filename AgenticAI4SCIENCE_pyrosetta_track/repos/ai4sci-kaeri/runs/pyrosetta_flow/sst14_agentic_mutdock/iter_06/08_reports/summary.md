# Iteration 6 Summary: sst14_mutdock_8000

            - **Run ID**: `sst14_mutdock_8000`
            - **Iteration**: 6
            - **생성 시각**: 2026-06-11 00:07 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 6 of the SSTR2 peptide binder design campaign evaluated a single candidate, with only one passing all QC gates. The top candidate, iter06_cand004, exhibited a ddG of -21.1 kcal/mol, indicating strong binding affinity. However, the structural quality of the candidate was poor, as evidenced by a pLDDT score of 0.0, suggesting significant structural inaccuracies or failures in modeling. The docking score of 0.00 further highlights the lack of reliable interaction predictions. While selectivity showed some improvement, the Δmargin of the top candidate was insufficient to outperform the native SST-14 margin, primarily due to off-target interactions with SSTR3 and SSTR5. This highlights the need for strategies to enhance SSTR2-specific interactions and reduce cross-reactivity with other subtypes.

The low pass rate (12.5%) in this iteration underscores the challenges in generating structurally viable candidates. The primary failure mode was structural failures, which must be addressed in future rounds. Given the current limitations, the design pipeline may benefit from incorporating additional structural constraints or refining the modeling protocol to improve pLDDT scores and overall structural reliability.

            ## Recommendations

            - Refine the structural modeling protocol to improve pLDDT scores and overall structural accuracy.
- Incorporate additional constraints or filters to enhance SSTR2-specific interactions and reduce off-target binding to SSTR3/SSTR5.
- Expand the candidate pool in the next iteration to increase the likelihood of identifying structurally and functionally viable binders.
- Re-evaluate the docking and scoring functions to better capture the specificity and affinity landscape.