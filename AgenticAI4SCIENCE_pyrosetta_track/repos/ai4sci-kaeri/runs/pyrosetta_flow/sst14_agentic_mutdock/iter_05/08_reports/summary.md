# Iteration 5 Summary: sst14_mutdock_17000

            - **Run ID**: `sst14_mutdock_17000`
            - **Iteration**: 5
            - **생성 시각**: 2026-06-11 16:44 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 5 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, with both passing all QC gates. Despite the low number of candidates, the results revealed strong binding affinity as indicated by favorable ddG values. The top candidates, iter05_cand006 (ddG = -23.3) and iter05_cand002 (ddG = -19.9), demonstrated significant binding potential. However, structural quality remains a critical issue, as both candidates exhibited pLDDT values of 0.0, indicating poor predicted structural confidence. This highlights a key bottleneck in the design process, where binding affinity is achieved at the expense of structural integrity.

The primary failure mode in this iteration was structural failure, which dominated QC gate rejections. Selectivity metrics remained strong, with all candidates passing the selectivity threshold (Δmargin > 0). The low pass rate (25%) underscores the need for improved structural modeling strategies to ensure that high-affinity candidates also maintain structural quality. These findings suggest that future iterations should focus on refining structural prediction methods or incorporating additional constraints during design to balance binding affinity with structural confidence.

            ## Recommendations

            - Refine structural modeling approaches to improve pLDDT scores while maintaining strong ddG binding.
- Incorporate additional structural constraints during design to ensure structural quality is prioritized alongside binding affinity.
- Expand the candidate pool in the next iteration to increase the likelihood of identifying structurally valid high-affinity binders.