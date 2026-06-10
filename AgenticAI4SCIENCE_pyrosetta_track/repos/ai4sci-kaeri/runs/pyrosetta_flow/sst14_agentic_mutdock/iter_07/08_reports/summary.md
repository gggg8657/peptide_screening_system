# Iteration 7 – sst14_mutdock_1000 Summary

            - **Run ID**: `sst14_mutdock_1000`
            - **Iteration**: 7
            - **생성 시각**: 2026-03-23 11:33 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            In this cycle we evaluated 11 designed sst14 variants, all of which satisfied the predefined quality control (QC) gates. The structural assessment revealed that the majority of candidates exhibit severe clashes, which is consistent with the observed high ddG penalties. The most promising designs, based on the most negative ddG values, are iter07_cand011 (−45.7 kcal mol⁻¹) and iter07_cand001 (−43.2 kcal mol⁻¹). Despite passing QC, the uniform pLDDT of 0.0 and docking scores of 0.00 indicate that the AlphaFold predictions and docking protocols are not yet discriminating between the variants. Consequently, the pipeline’s current selection criteria are insufficient to filter out structurally infeasible designs.

            ## Recommendations

            - Introduce a clash‑filtering step prior to docking to reduce structural_failures.
- Re‑evaluate the ddG threshold; consider a less stringent cutoff to allow more diverse candidates.
- Augment the docking protocol with a higher‑resolution scoring function to better discriminate binding modes.
- Incorporate an explicit pLDDT‑based confidence filter to avoid designs with uniformly low structural confidence.
- Generate a larger mutation library to increase sequence diversity and potentially improve binding affinity.