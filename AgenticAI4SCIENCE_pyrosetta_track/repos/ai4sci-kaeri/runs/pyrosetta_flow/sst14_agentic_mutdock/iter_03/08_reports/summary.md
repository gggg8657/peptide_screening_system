# Iteration 3 Summary: sst14_mutdock_14000

            - **Run ID**: `sst14_mutdock_14000`
            - **Iteration**: 3
            - **생성 시각**: 2026-06-11 11:33 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 3 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, with both passing all QC gates. However, the structural quality of the designs was notably poor, as indicated by pLDDT values of 0.0 for both candidates, suggesting significant structural failures. The docking scores were also suboptimal (0.00), and while the ddG values indicated favorable binding affinities (ranging from -18.4 to -44.1), the overall design quality remains a concern. The best candidate, iter03_cand007, exhibited the lowest ddG of -44.1, but its structural reliability is questionable due to the absence of meaningful pLDDT values. Selectivity (Δmargin) was positive for the top candidates, but this was not sufficient to offset the structural and docking shortcomings.

The low pass rate (25%) and poor structural quality highlight the need for improvements in the design pipeline, particularly in ensuring structural accuracy and stability. The current results suggest that the design process may not be effectively balancing binding affinity with structural integrity, necessitating a re-evaluation of the design parameters and constraints.

            ## Recommendations

            - Revisit the structural modeling pipeline to improve pLDDT scores and reduce structural failures.
- Incorporate additional constraints or scoring terms to enhance docking performance and structural accuracy.
- Evaluate the role of sequence design in stabilizing the predicted structures.
- Consider increasing the diversity of the design space to explore alternative binding modes with better structural quality.