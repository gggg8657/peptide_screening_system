# Iteration 15 Summary: sst14_mutdock_27000

            - **Run ID**: `sst14_mutdock_27000`
            - **Iteration**: 15
            - **생성 시각**: 2026-06-12 11:03 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 15 of the SSTR2 peptide binder design campaign evaluated a single candidate, with one passing all quality control (QC) gates. The top candidate, iter15_cand008, exhibited a ddG of -32.8 kcal/mol, indicating strong binding affinity. However, the pLDDT and docking scores were both reported as 0.0, which suggests potential issues with structural prediction or docking reliability. The overall pass rate was 100% for this iteration, but the low number of candidates evaluated limits the statistical significance of this result. The Critic analysis highlights a concerning trend of decreasing Δmargin, which may indicate a decline in selectivity over recent iterations.

            ## Recommendations

            - Investigate the structural prediction and docking pipeline to address the zero pLDDT and docking scores observed for the top candidate.
- Expand the candidate pool in the next iteration to improve statistical confidence in QC pass rates and selectivity trends.
- Monitor the Δmargin closely in subsequent iterations to ensure selectivity is maintained and not compromised by binding affinity optimization.