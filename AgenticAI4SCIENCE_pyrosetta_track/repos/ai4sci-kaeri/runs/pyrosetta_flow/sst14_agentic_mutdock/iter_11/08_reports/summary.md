# Iteration 11 Summary: sst14_mutdock_31000

            - **Run ID**: `sst14_mutdock_31000`
            - **Iteration**: 11
            - **생성 시각**: 2026-06-12 16:49 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 11 evaluated a total of 3 candidates, all of which passed the quality control (QC) gates. The primary focus of this iteration was to improve binding affinity and selectivity for the SSTR2 target. While the binding free energy (ddG) values showed strong performance, with the best candidate (iter11_cand005) achieving a ddG of -39.1 kcal/mol, selectivity remains a significant challenge. The best selectivity margin (Δmargin) was positive, but the overall pass rate for selectivity was low, indicating that most candidates still fail to meet the required threshold for target specificity. This suggests that structural features may not be sufficiently optimized to ensure high selectivity across the target landscape.

Structural failures were the primary mode of failure in this iteration, highlighting the need for further refinement of the peptide binder designs. The pLDDT and docking scores for all candidates were reported as 0.0, which may indicate limitations in the structural modeling or docking protocols used. These findings suggest that future iterations should prioritize strategies to enhance structural stability and improve selectivity metrics. Optimization of key residues and exploration of alternative binding modes may be necessary to achieve the desired balance between affinity and specificity.

            ## Recommendations

            - Focus on improving selectivity by optimizing key residues involved in target-specific interactions.
- Investigate the structural failures to identify common motifs or issues affecting stability and binding.
- Consider refining the docking and modeling protocols to better capture structural features and improve pLDDT and docking scores.
- Explore alternative binding modes or conformations that may enhance selectivity while maintaining strong binding affinity.