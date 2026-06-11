# Iteration 16 Summary: sst14_mutdock_7000

            - **Run ID**: `sst14_mutdock_7000`
            - **Iteration**: 16
            - **생성 시각**: 2026-06-10 23:25 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 16 evaluated a single candidate, with only one (100%) passing all quality control (QC) gates. The top candidate, iter16_cand006, exhibited a ddG of -16.3 kcal/mol, indicating strong binding affinity. However, the pLDDT and docking scores were both reported as 0.0, suggesting potential structural issues or incomplete modeling. Despite the strong binding energy, the overall pass rate was low (12.5%), and no improvement in selectivity was observed. The Critic analysis highlights persistent off-target binding, particularly at conserved pocket residues in SSTR3 and SSTR5, which may be contributing to the low selectivity and structural failures.

The primary failure mode in this iteration was structural failures, which could be due to modeling inaccuracies or suboptimal design features. While the best Δmargin remains strong at 8.69, the lack of progress in selectivity and the low pass rate indicate the need for a more focused design strategy. The next iteration should aim to address these structural issues and improve selectivity by refining the design around key residues in the SSTR2 binding pocket.

            ## Recommendations

            - Refine the design to address structural failures, particularly at conserved pocket residues in SSTR3/SSTR5.
- Implement additional selectivity filters in the QC pipeline to prioritize candidates with improved SSTR2 specificity.
- Consider incorporating experimental validation to better assess binding and selectivity in the next iteration.