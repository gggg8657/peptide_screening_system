# Iteration 14 Summary: sst14_mutdock_20000

            - **Run ID**: `sst14_mutdock_20000`
            - **Iteration**: 14
            - **생성 시각**: 2026-06-11 22:47 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 14 of the SSTR2 peptide binder design campaign evaluated a single candidate, with one successfully passing all QC gates. The top candidate, iter14_cand004, demonstrated a ddG of -36.3 kcal/mol, indicating strong binding affinity. However, the pLDDT and docking scores for this candidate were both reported as 0.0, suggesting potential issues with structural confidence or docking accuracy. Despite the positive Δmargin of 9.10, the overall selectivity remains inconsistent, with many candidates exhibiting weak or no selectivity (Δmargin ≤ 0).

The low pass rate of 12.5% highlights a significant challenge in this iteration, primarily attributed to structural failures. These failures may stem from suboptimal backbone conformations or inadequate sampling during design. To address this, the next iteration should focus on refining structural sampling and improving the robustness of design protocols to enhance the likelihood of generating high-quality candidates that pass all QC gates.

            ## Recommendations

            - Refine structural sampling protocols to reduce structural failures.
- Investigate the root cause of the zero pLDDT and docking scores for iter14_cand004.
- Enhance selectivity screening to ensure consistent Δmargin across all candidates.