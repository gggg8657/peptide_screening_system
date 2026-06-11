# Iteration 19 Summary: sst14_mutdock_16000

            - **Run ID**: `sst14_mutdock_16000`
            - **Iteration**: 19
            - **생성 시각**: 2026-06-11 16:18 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 19 evaluated four candidate peptides for their binding affinity and structural compatibility with the SSTR2 target. All four candidates passed the quality control (QC) gates, indicating that they met the baseline structural and energetic criteria. The top candidates demonstrated strong binding affinities, with the best ΔG of binding (ddG) reaching -28.8 kcal/mol for iter19_cand007. However, the primary limitation of this iteration was the lack of significant selectivity improvement over the native SST-14 ligand. While the best Δmargin was positive, it was not sufficiently large to ensure high selectivity, and several candidates exhibited weak selectivity profiles. This suggests that the current design strategy may not be effectively addressing the structural determinants of selectivity.

            ## Recommendations

            - Refine the design strategy to prioritize selectivity metrics alongside binding affinity in the next iteration.
- Investigate the structural basis of the weak selectivity observed in this iteration using detailed binding mode analysis.
- Consider incorporating additional constraints or descriptors that better capture selectivity determinants during candidate generation.