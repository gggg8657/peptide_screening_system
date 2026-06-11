# Iteration 8 Summary: sst14_mutdock_11000

            - **Run ID**: `sst14_mutdock_11000`
            - **Iteration**: 8
            - **생성 시각**: 2026-06-11 06:09 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 8 evaluated five candidate peptides for their binding affinity and structural compatibility with the SSTR2 receptor. All candidates passed the quality control (QC) gates, indicating no immediate structural failures. The primary focus of this iteration was to improve SSTR2 selectivity over off-target receptors, but the results showed limited progress in this regard. While the binding affinities (ddG) of the candidates were strong, with the best candidate achieving a ddG of -25.7 kcal/mol, the selectivity margin remained comparable to native SST-14, indicating a lack of significant improvement in off-target discrimination. This suggests that the current design strategy is effective in enhancing binding affinity but insufficient in achieving the desired selectivity for SSTR2.

The top candidates, iter08_cand006, iter08_cand007, and iter08_cand002, demonstrated the strongest binding affinities. However, the absence of meaningful selectivity improvements highlights the need for a revised design approach. Future iterations should incorporate additional constraints or features that specifically enhance SSTR2 selectivity, such as targeted residue modifications or structural motifs known to confer receptor specificity.

            ## Recommendations

            - Revisit the design strategy to incorporate features that enhance SSTR2 selectivity, such as receptor-specific binding motifs or residue-level specificity constraints.
- Conduct a detailed analysis of the structural interactions of the top candidates to identify potential modifications that could improve selectivity.
- Consider incorporating additional computational tools or experimental validation to better assess selectivity against off-target receptors.