# Iteration 13 Summary: sst14_mutdock_35000

            - **Run ID**: `sst14_mutdock_35000`
            - **Iteration**: 13
            - **생성 시각**: 2026-06-12 23:20 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 13 evaluated a total of 2 candidates, both of which passed all QC gates. Despite the small candidate pool, the iteration demonstrated strong binding affinity, as evidenced by high ddG values. The top candidates, iter13_cand008 and iter13_cand005, exhibited ddG scores of -30.8 and -19.8 kcal/mol, respectively. However, the structural quality of the designs was poor, as indicated by pLDDT scores of 0.0 for both candidates, and docking scores were not informative (0.00). Selectivity remained favorable, with a Δmargin > 0 for all candidates, but the lack of structural confidence limits the utility of these designs for downstream applications.

The primary failure mode in this iteration was structural failures, which suggests that the design algorithm may be prioritizing binding affinity at the expense of structural stability. While selectivity is maintained, the campaign has not yet reached convergence due to the poor structural quality of the designs. Further refinement of the design process is necessary to balance affinity with structural integrity.

            ## Recommendations

            - Refine the design algorithm to prioritize structural quality (e.g., pLDDT) alongside binding affinity (ddG).
- Investigate the root cause of structural failures and consider incorporating additional constraints or validation steps.
- Expand the candidate pool in the next iteration to increase the likelihood of identifying structurally sound, high-affinity binders.
- Maintain focus on selectivity metrics to ensure that new designs retain favorable SSTR2 specificity.