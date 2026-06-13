# Iteration 6 Summary: sst14_mutdock_35000

            - **Run ID**: `sst14_mutdock_35000`
            - **Iteration**: 6
            - **생성 시각**: 2026-06-12 22:49 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 6 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, with both passing all QC gates. Despite the small number of candidates, the results showed strong binding affinities as indicated by ddG values, with the best candidate (iter06_cand001) exhibiting a ddG of -28.7 kcal/mol. However, the pLDDT and docking scores for both candidates were not available (0.0), raising concerns about the structural quality of the predicted models. The low pass rate (25%) suggests potential issues with structural modeling or sequence design, despite the strong selectivity (Δmargin > 0) observed in this iteration.

The primary failure type identified was structural failures, indicating a need to refine the modeling pipeline or improve the sequence design criteria to ensure higher structural accuracy. The strong binding affinities observed are promising, but they must be supported by reliable structural predictions to ensure the candidates are viable for further development.

            ## Recommendations

            - Investigate the structural modeling pipeline to address the lack of pLDDT and docking scores for the candidates.
- Refine the sequence design criteria to improve structural quality while maintaining strong binding affinities.
- Increase the number of candidates in the next iteration to better assess the impact of structural improvements on overall performance.