# Iteration 10 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 10
            - **생성 시각**: 2026-06-12 10:37 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 10 of the SSTR2 peptide binder design campaign evaluated three candidates, all of which passed the quality control (QC) gates. The designs demonstrated strong binding affinity as indicated by favorable ddG values, with the best candidate (iter10_cand003) achieving a ddG of -36.6 kcal/mol. However, the pLDDT and docking scores were not reported (0.0), suggesting potential limitations in structural confidence or docking evaluation. Despite the promising binding affinity, selectivity remains a critical challenge, as highlighted by the critic analysis. The best Δmargin is positive, but the overall pass rate for selectivity is low, indicating a need for targeted improvements in off-target discrimination.

The primary failure mode observed in this iteration was structural failures, underscoring the importance of refining structural stability and ensuring robustness in the design. The low selectivity pass rate necessitates a strategic shift in the next iteration to prioritize selectivity optimization alongside binding affinity. This will likely involve incorporating additional constraints or metrics to enhance discrimination against off-target receptors.

            ## Recommendations

            - Prioritize selectivity optimization in the next iteration by incorporating additional off-target screening metrics.
- Investigate the structural failures observed and refine the design constraints to improve stability.
- Consider integrating machine learning-based selectivity prediction models to guide the design process.
- Revisit the docking and pLDDT evaluation protocols to ensure they are providing meaningful insights into structural confidence.