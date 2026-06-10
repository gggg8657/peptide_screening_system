# Iteration 8 – sst14_mutdock_1000 Summary

            - **Run ID**: `sst14_mutdock_1000`
            - **Iteration**: 8
            - **생성 시각**: 2026-03-23 11:38 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            In this cycle we evaluated 11 designed sst14 variants using AlphaFold‑2 for structural confidence (pLDDT) and Rosetta docking for binding affinity (dock score) and stability (ddG). All candidates passed the automated QC gates, yielding a 100 % QC pass rate. However, the ddG values are highly negative (−16.8 to −43.4 kcal mol⁻¹), suggesting that the current stability threshold may be too stringent and that many designs could be intrinsically unstable. The docking scores are uniformly zero, indicating that the scoring function did not discriminate binding quality in this set. No selectivity data were collected, so the selectivity pass rate is reported as 0.0.

The top performers by ddG are iter08_cand010, iter08_cand007, and iter08_cand001, all achieving ddG values below −42 kcal mol⁻¹. Despite their favorable ddG, the lack of structural confidence (pLDDT = 0.0) and identical docking scores raise concerns about the reliability of these predictions. Future iterations should incorporate stricter structural validation and alternative docking protocols to better capture binding nuances.

            ## Recommendations

            - Re‑evaluate the ddG stability threshold; consider a less stringent cutoff or incorporate additional stability metrics (e.g., Rosetta energy terms).
- Integrate a secondary docking protocol (e.g., HADDOCK or AutoDock Vina) to provide complementary binding scores and reduce reliance on a single scoring function.
- Add structural confidence checks beyond pLDDT, such as Ramachandran plot analysis or predicted solvent accessibility, to filter out designs with low confidence.
- Collect selectivity data against off‑target receptors (e.g., SSTR1, SSTR3) to enable a meaningful selectivity pass rate.
- Generate a larger design pool (≥ 200 candidates) to increase the likelihood of discovering high‑confidence binders.