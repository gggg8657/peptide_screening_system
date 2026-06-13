# Iteration 12 Summary: sst14_mutdock_35000

            - **Run ID**: `sst14_mutdock_35000`
            - **Iteration**: 12
            - **생성 시각**: 2026-06-12 23:16 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 12 of the SSTR2 peptide binder design campaign evaluated a single candidate, with only one passing all quality control (QC) gates. The low pass rate of 12.5% indicates a significant bottleneck in the design process, primarily attributed to structural failures. The top candidate, iter12_cand005, exhibited a strong binding affinity with a ddG of -24.6 kcal/mol, but its pLDDT and docking scores were both zero, suggesting potential issues with structural confidence and binding mode prediction. These results highlight the need for a more balanced optimization strategy that prioritizes structural stability alongside binding affinity.

The primary failure mode in this iteration was structural instability, likely due to overly aggressive ddG filtering criteria that may have excluded structurally viable candidates. This suggests that the current design parameters may be too stringent for the target system. To improve the yield of high-quality candidates in the next iteration, it is recommended to revisit the filtering thresholds and incorporate additional metrics for structural validation.

            ## Recommendations

            - Reassess the ddG filtering criteria to avoid overly aggressive exclusion of structurally viable candidates.
- Incorporate additional structural validation metrics to improve the pass rate while maintaining selectivity.
- Consider relaxing QC thresholds temporarily to explore a broader design space in the next iteration.