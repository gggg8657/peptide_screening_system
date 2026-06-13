# Iteration 8 Summary: sst14_mutdock_35000

            - **Run ID**: `sst14_mutdock_35000`
            - **Iteration**: 8
            - **생성 시각**: 2026-06-12 22:56 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 8 of the SSTR2 peptide binder design campaign evaluated a total of 1 candidate, with only 1 passing all QC gates. The top candidate, iter08_cand002, exhibited a pLDDT of 0.0 and a docking score of 0.00, indicating significant structural and docking failures. Despite a favorable ddG of -18.6 kcal/mol and strong selectivity (Δmargin > 0), the lack of structural integrity and docking accuracy severely limits its viability as a candidate for further development. The low pass rate of 12.5% underscores the challenges in generating structurally sound and functionally effective designs in this iteration.

The primary failure mode observed was structural failure, suggesting that the design process may need to be refined to better ensure structural stability and accurate docking predictions. While selectivity remains a strength, the inability to pass structural and docking criteria is a critical bottleneck. Future iterations should focus on addressing these issues to improve the overall quality and robustness of the generated candidates.

            ## Recommendations

            - Refine the design protocol to improve structural stability and docking accuracy.
- Incorporate additional constraints or scoring terms to prioritize candidates with higher pLDDT and docking scores.
- Reassess the balance between selectivity and structural/docking criteria to ensure a more robust set of viable candidates.
- Consider increasing the diversity of the design space to explore alternative structural solutions.