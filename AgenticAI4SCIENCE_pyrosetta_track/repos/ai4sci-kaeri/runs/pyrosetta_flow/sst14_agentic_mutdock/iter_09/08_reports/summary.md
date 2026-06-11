# Iteration 9 Summary: sst14_mutdock_14000

            - **Run ID**: `sst14_mutdock_14000`
            - **Iteration**: 9
            - **생성 시각**: 2026-06-11 11:58 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 9 evaluated four candidates for their potential as SSTR2 peptide binders. All candidates passed the quality control (QC) gates, indicating structural integrity and general stability. However, while the designs demonstrated strong binding affinity to the target receptor, as indicated by ddG values ranging from -28.0 to -35.2 kcal/mol, the primary objective of achieving SSTR2 selectivity remains a significant challenge. The best Δmargin is still positive, but the overall pass rate for selectivity is low, with structural failures being the main cause of non-compliance. This suggests that while the binding affinity is promising, further optimization is needed to enhance receptor specificity and reduce off-target interactions.

The top-performing candidate, iter09_cand001, exhibited the lowest ddG (-35.2 kcal/mol), indicating the strongest predicted binding affinity. However, the lack of pLDDT and docking score data raises concerns about the structural confidence and docking accuracy of the designs. This highlights the need for improved modeling and scoring methods to ensure both affinity and structural reliability. Overall, the iteration underscores the importance of balancing binding strength with selectivity in the design of effective SSTR2 binders.

            ## Recommendations

            - Focus on improving SSTR2 selectivity by incorporating additional constraints or filters during the design phase.
- Investigate the structural failures identified in the Critic analysis to better understand the underlying causes and refine the modeling pipeline.
- Enhance the scoring and modeling methods to obtain reliable pLDDT and docking scores for future candidates.
- Consider retraining or fine-tuning the design model with a focus on selectivity metrics to improve the pass rate in subsequent iterations.