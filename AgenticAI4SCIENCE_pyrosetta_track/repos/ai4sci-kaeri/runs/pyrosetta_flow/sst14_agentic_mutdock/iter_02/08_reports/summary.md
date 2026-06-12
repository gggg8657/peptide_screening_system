# Iteration 2 Summary: sst14_mutdock_32000

            - **Run ID**: `sst14_mutdock_32000`
            - **Iteration**: 2
            - **생성 시각**: 2026-06-12 17:32 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 2 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, with both passing all QC gates. However, the structural and sequence quality of the top candidates remains a critical concern. Both top candidates, iter02_cand008 and iter02_cand007, exhibited pLDDT values of 0.0, indicating complete structural failure. Additionally, their docking scores were 0.00, suggesting poor docking quality despite favorable binding affinities (ddG of -31.6 and -30.4, respectively). These results highlight a significant gap between binding affinity and structural reliability in the current design pipeline.

The primary failure type observed in this iteration was structural failure, which underscores the need for improved structural modeling and validation strategies. While the binding affinity metrics are promising, the lack of reliable structural predictions limits the practical utility of these candidates. Future iterations should prioritize enhancing structural accuracy and ensuring that docking quality is not compromised in the pursuit of strong binding affinities.

            ## Recommendations

            - Improve structural modeling and validation to ensure reliable pLDDT values and docking quality.
- Investigate the root causes of structural failures in the current design pipeline.
- Balance the optimization of binding affinity with structural accuracy in future iterations.