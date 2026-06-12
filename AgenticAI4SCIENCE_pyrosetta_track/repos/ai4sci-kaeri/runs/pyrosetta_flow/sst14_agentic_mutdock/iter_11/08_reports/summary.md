# Iteration 11 Summary: sst14_mutdock_24000

            - **Run ID**: `sst14_mutdock_24000`
            - **Iteration**: 11
            - **생성 시각**: 2026-06-12 05:04 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 11 of the SSTR2 peptide binder design campaign evaluated a single candidate, with only one (100%) passing all QC gates. The sole candidate, iter11_cand008, exhibited a ΔG of -25.2 kcal/mol, indicating strong binding potential. However, the pLDDT and docking scores were both reported as 0.0, suggesting a lack of structural confidence or computational evaluation for these metrics. Despite the strong ddG, the low pass rate (12.5%) indicates significant structural failures, which may be due to design constraints or limitations in the current modeling approach.

The primary failure mode in this iteration was structural failures, which may point to issues in the design protocol or the stability of the generated structures. While the best Δmargin remains robust, the low yield of viable candidates suggests the need for further refinement of the design strategy. The results highlight the importance of improving structural modeling and ensuring that generated candidates are both energetically favorable and structurally sound.

            ## Recommendations

            - Investigate the structural modeling pipeline to address the lack of pLDDT and docking score data for candidates.
- Refine the design protocol to reduce structural failures and improve the pass rate through QC gates.
- Conduct a detailed analysis of iter11_cand008 to determine if it can serve as a template for future designs despite the missing structural metrics.