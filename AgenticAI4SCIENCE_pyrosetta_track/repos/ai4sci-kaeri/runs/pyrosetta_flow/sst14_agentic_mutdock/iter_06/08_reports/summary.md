# Iteration 6 – sst14_mutdock_1000 Summary

            - **Run ID**: `sst14_mutdock_1000`
            - **Iteration**: 6
            - **생성 시각**: 2026-03-23 11:27 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            In this iteration, eight candidate peptides were evaluated and all passed the initial QC gates. However, structural assessment revealed that none of the designs possess a reliable predicted fold, as indicated by a pLDDT of 0.0 for every candidate. Docking calculations returned a uniform score of 0.00, while the predicted binding free energy changes (ddG) were highly negative, ranging from –43.4 to –20.1 kcal mol⁻¹. The most favorable ddG value (–43.4 kcal mol⁻¹) is well below the acceptable threshold, suggesting that the models are likely over‑optimistic and structurally implausible. Consequently, the selectivity pass rate is effectively zero, reflecting the lack of meaningful structural or energetic discrimination among the candidates.

The top performers, ranked by ddG, are iter06_cand012, iter06_cand008, iter06_cand003, iter06_cand011, iter06_cand007, iter06_cand014, iter06_cand005, and iter06_cand002. All share identical pLDDT and docking scores, underscoring the need to revisit the modeling pipeline. The failure pattern points to a systemic issue in the structural prediction step rather than random noise, indicating that the current mutation‑generation and docking workflow is not producing viable peptide scaffolds for SSTR2 binding.

            ## Recommendations

            - Re‑evaluate the structural prediction pipeline; consider integrating AlphaFold2 or Rosetta relax steps to generate realistic backbone conformations before docking.
- Introduce a structural quality filter (e.g., pLDDT > 70) as an early QC gate to eliminate designs lacking a credible fold.
- Adjust the docking protocol to include receptor flexibility or use ensemble docking to better capture induced‑fit effects.
- Re‑define the ddG threshold to a less stringent value (e.g., > –10 kcal mol⁻¹) until structural reliability is restored.
- Implement a multi‑objective optimization that balances predicted stability, binding affinity, and structural confidence.
- Generate a larger mutation library with controlled diversity to increase the likelihood of obtaining viable scaffolds.