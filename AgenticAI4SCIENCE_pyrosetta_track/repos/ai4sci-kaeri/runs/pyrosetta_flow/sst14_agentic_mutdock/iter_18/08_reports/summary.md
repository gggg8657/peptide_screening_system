# Iteration 18 Summary: sst14_mutdock_13000

            - **Run ID**: `sst14_mutdock_13000`
            - **Iteration**: 18
            - **생성 시각**: 2026-06-11 11:04 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 18 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, both of which passed all quality control (QC) gates. Despite this, the structural quality of the designs was poor, as indicated by pLDDT values of 0.0 for both candidates. The binding affinity, as measured by ddG, was strong, with the best candidate (iter18_cand008) achieving a ddG of -37.5 kcal/mol. However, the lack of structural confidence and the low pass rate (25%) suggest that the designs are not yet suitable for experimental validation. The docking scores were not informative (0.00), and no selectivity data were provided, though the critic analysis noted that selectivity remains positive. Overall, the iteration highlights the need to improve structural prediction accuracy while maintaining favorable binding energetics.

The primary failure mode in this iteration was structural failures, indicating that the current design approach may not be generating sufficiently accurate or stable structures. This is a critical barrier to advancing candidates to the next stage of the design campaign.

            ## Recommendations

            - Prioritize improvements in structural prediction accuracy to ensure viable candidates for experimental validation.
- Investigate the root causes of structural failures, including potential limitations in the modeling pipeline.
- Maintain focus on optimizing binding affinity (ddG) while addressing structural quality issues.
- Consider incorporating additional constraints or validation steps to enhance the robustness of the designs.