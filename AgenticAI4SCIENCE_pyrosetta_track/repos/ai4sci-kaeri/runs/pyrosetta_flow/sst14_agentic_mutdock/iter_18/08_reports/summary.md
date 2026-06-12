# Iteration 18 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 18
            - **생성 시각**: 2026-06-12 11:18 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 18 of the SSTR2 peptide binder design campaign evaluated a single candidate, with only one passing all quality control (QC) gates. The low pass rate of 12.5% indicates a significant bottleneck in the design pipeline, likely due to overly stringent QC thresholds or limited structural diversity in the candidate pool. The top-performing candidate, iter18_cand005, exhibited a ΔG of -23.3 kcal/mol, which, while favorable, did not show substantial improvement over previous iterations. However, the pLDDT and docking scores were both reported as 0.0, suggesting potential issues with structural prediction or scoring reliability that warrant further investigation.

Structural failures were the primary mode of candidate rejection, highlighting the need for a more robust and diverse set of initial designs. The low yield of viable candidates underscores the importance of revisiting the QC criteria to ensure they are both rigorous and realistic for the current design space. While the selectivity pass rate could not be determined due to the small sample size, the overall performance of this iteration suggests a need for recalibration of the design and evaluation pipeline to enhance throughput and candidate quality.

            ## Recommendations

            - Reassess QC thresholds to ensure they are appropriately balanced between stringency and feasibility for the current design space.
- Increase the diversity of initial designs to improve the likelihood of generating high-quality candidates.
- Investigate the structural prediction and scoring methods for iter18_cand005 to address the reported pLDDT and docking score anomalies.
- Consider incorporating additional metrics or alternative scoring functions to improve selectivity and candidate ranking.