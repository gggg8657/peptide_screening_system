# Iteration 1 Summary: sst14_mutdock_100

            - **Run ID**: `sst14_mutdock_100`
            - **Iteration**: 1
            - **생성 시각**: 2026-04-01 09:47 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated 102 candidates for SSTR2 peptide binder design, with all passing QC gates. The top candidates exhibit highly negative ddG values (-43.8 to -51.6), indicating strong predicted binding affinity. However, all top candidates display pLDDT=0.0 and dock=0.00, suggesting structural validity concerns. These metrics indicate potential over-optimization of energy terms without corresponding structural quality, raising alarms about the reliability of high ddG scores. Further analysis is required to validate these candidates experimentally.

Critic analysis highlights a critical correlation between high ddG scores and structural failures, implying that current optimization prioritizes energy minimization over structural accuracy. While selectivity metrics were not explicitly reported, the QC pass rate suggests no immediate filtering issues. The next iteration must address this structural validity gap while maintaining binding affinity optimization.

            ## Recommendations

            - Refine scoring function to prioritize structural validity metrics (pLDDT, dock score) alongside ddG optimization
- Implement additional QC gates to filter candidates with structural failures
- Increase sampling diversity to avoid overfitting to energy-based metrics
- Validate selectivity profiles experimentally for top candidates in next iteration