# Iteration 14 Summary: sst14_mutdock_13000

            - **Run ID**: `sst14_mutdock_13000`
            - **Iteration**: 14
            - **생성 시각**: 2026-06-11 10:30 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 14 (sst14_mutdock_13000) evaluated a total of 1 candidate, with only 1 passing all QC gates, resulting in a low pass rate of 100%. Despite the limited number of candidates, the single successful candidate, iter14_cand006, demonstrated a strong ddG value of -18.8, indicating favorable binding affinity. However, the absence of pLDDT and docking scores suggests potential issues with structural modeling or scoring completeness. The overall low yield of this iteration highlights inefficiencies in the current design space for generating structurally viable and selective SSTR2 peptide binders.

The primary failure mode observed was structural failures, which may be attributed to suboptimal design parameters or constraints that hinder the generation of stable and accurate structures. While the best Δmargin of 9.1021 indicates some level of selectivity, the lack of additional candidates limits the ability to explore this further. These findings suggest that the design strategy requires refinement to improve structural robustness and enhance the overall yield of high-quality candidates.

            ## Recommendations

            - Refine the design space parameters to enhance structural stability and reduce structural failures.
- Investigate the root causes of missing pLDDT and docking scores for the top candidate to ensure scoring completeness.
- Expand the candidate pool in the next iteration to improve statistical confidence in design performance.
- Consider integrating additional constraints or filters to improve selectivity and structural accuracy.