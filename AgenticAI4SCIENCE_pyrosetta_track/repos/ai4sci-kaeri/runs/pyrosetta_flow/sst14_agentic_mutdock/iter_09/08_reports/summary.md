# Iteration 9 – sst14_mutdock_1000 – Structural Viability Assessment

            - **Run ID**: `sst14_mutdock_1000`
            - **Iteration**: 9
            - **생성 시각**: 2026-03-23 11:44 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            In this iteration, nine candidate peptides were generated and all passed the initial QC gates. However, the structural assessment revealed a systemic failure: every candidate exhibited a pLDDT of 0.0 and a docking score of 0.00, indicating that AlphaFold predictions could not converge on a stable structure and that the docking protocol failed to produce a meaningful binding pose. The ddG values, while numerically large in magnitude, are not indicative of true binding affinity due to the lack of structural context. Consequently, the pipeline failed to produce any viable designs, and the selectivity pass rate is effectively zero despite the nominal QC pass.

The most promising candidates, based on ddG alone, are iter09_cand001 (−41.8 kcal mol⁻¹) and iter09_cand012 (−41.0 kcal mol⁻¹). Nonetheless, without credible structural predictions, these values cannot be trusted. The next iteration must prioritize structural integrity, incorporating stricter constraints and alternative modeling strategies to ensure that candidates can fold and bind to SSTR2 in a physically realistic manner.

            ## Recommendations

            - Integrate a structural feasibility filter prior to docking, such as a minimum pLDDT threshold (e.g., >70) to ensure that only foldable designs proceed.
- Employ an alternative protein‑structure prediction engine (e.g., RoseTTAFold) to cross‑validate AlphaFold outputs and identify candidates with consistent high confidence scores.
- Introduce explicit backbone constraints or use Rosetta’s FastRelax protocol to refine candidate structures before docking.
- Re‑evaluate the docking protocol parameters; consider using a more flexible receptor model or a different scoring function that can handle low‑confidence structures.
- Add a secondary QC gate that flags candidates with pLDDT or docking scores below a defined cutoff, preventing them from being reported as top candidates.
- Iteratively test a smaller, focused library (e.g., 20–30 candidates) with enriched diversity to reduce computational burden while improving hit quality.