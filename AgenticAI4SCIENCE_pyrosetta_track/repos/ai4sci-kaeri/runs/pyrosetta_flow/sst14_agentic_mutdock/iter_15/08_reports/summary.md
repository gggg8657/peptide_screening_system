# Iteration 15 Summary: sst14_mutdock_7000

            - **Run ID**: `sst14_mutdock_7000`
            - **Iteration**: 15
            - **생성 시각**: 2026-06-10 23:22 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 15 of the SSTR2 peptide binder design campaign evaluated a single candidate, with one passing all QC gates. The top candidate, iter15_cand008, exhibited a ddG of -21.7 kcal/mol, indicating strong binding affinity. However, the pLDDT and docking scores were both reported as 0.0, suggesting potential issues with structural confidence or docking accuracy. Despite this, the candidate passed QC, likely due to its favorable ddG value. The overall pass rate for this iteration was 100%, but the low number of candidates evaluated limits the statistical significance of these results.

The primary challenge identified in this iteration is the lack of selectivity improvement over native SST-14. The Critic analysis highlights that most candidates, including the top performer, have not achieved a sufficient Δmargin to demonstrate enhanced selectivity. This suggests that the current design strategy may not be effectively addressing the key residues or interactions necessary for selectivity. The low pass rate in the broader context of the campaign (12.5%) indicates a need for a more focused and refined design approach.

            ## Recommendations

            - Refine the design strategy to focus on residues and interactions that are critical for selectivity over native SST-14.
- Increase the number of candidates evaluated in the next iteration to improve statistical confidence and identify more diverse high-performing designs.
- Investigate the structural and docking issues observed in iter15_cand008 to ensure that the low pLDDT and docking scores do not compromise the reliability of the ddG value.