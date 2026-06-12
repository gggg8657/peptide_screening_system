# Iteration 20 Summary: sst14_mutdock_24000

            - **Run ID**: `sst14_mutdock_24000`
            - **Iteration**: 20
            - **생성 시각**: 2026-06-12 06:05 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 20 evaluated four candidate peptides for SSTR2 binding, all of which passed the defined quality control (QC) gates. While the pass rate of 100% is encouraging, the overall structural quality metrics, including pLDDT and docking scores, remain at baseline values (0.0), indicating a lack of structural refinement. The ddG values show moderate improvements, with the best candidate (iter20_cand008) achieving a binding energy of -46.6 kcal/mol. However, the selectivity pass rate remains low, and no significant gains in off-target discrimination were observed compared to native SST-14. This suggests that while binding affinity is improving, the designs have not yet effectively addressed off-target interactions.

The primary failure mode in this iteration was structural failures, which may be linked to the lack of meaningful pLDDT improvements. The Critic analysis highlights the need to focus on disrupting off-target contacts while preserving key pharmacophore residues. The next iteration should prioritize strategies to enhance structural stability and specificity, particularly by refining the peptide backbone and side-chain interactions at the SSTR2 interface.

            ## Recommendations

            - Focus on structural refinement to improve pLDDT and stabilize key interactions.
- Incorporate explicit strategies to disrupt off-target contacts while maintaining SSTR2 binding.
- Evaluate the impact of backbone modifications on selectivity and affinity.
- Consider targeted mutagenesis of residues involved in off-target interactions.