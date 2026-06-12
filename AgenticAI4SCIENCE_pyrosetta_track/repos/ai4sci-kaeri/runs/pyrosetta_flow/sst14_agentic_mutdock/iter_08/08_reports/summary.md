# Iteration 8 Summary: sst14_mutdock_24000

            - **Run ID**: `sst14_mutdock_24000`
            - **Iteration**: 8
            - **생성 시각**: 2026-06-12 04:53 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 8 evaluated a total of 2 candidates, with both passing all QC gates. However, the structural and docking metrics (pLDDT=0.0 and dock=0.00) suggest that these candidates likely represent structural failures, potentially due to poor backbone geometry or steric clashes. Despite this, the selectivity (Δmargin) remains strong, indicating that the binding specificity is preserved. The low pass rate (25%) highlights a need to address structural stability in the design pipeline to ensure robust and viable candidates.

The top candidates, iter08_cand006 and iter08_cand001, exhibited ddG values of -28.2 and -15.5 kcal/mol, respectively. These values suggest strong binding affinity, but the lack of structural confidence limits their utility. The primary failure mode in this iteration is structural instability, which must be addressed in future rounds to improve the overall quality and reliability of the designed peptides.

            ## Recommendations

            - Improve structural modeling protocols to enhance backbone geometry and reduce steric clashes.
- Incorporate additional structural validation steps to filter out candidates with poor pLDDT and docking scores.
- Focus on optimizing structural stability while maintaining strong selectivity and binding affinity in the next iteration.