# Iteration 6 Summary: sst14_mutdock_11000

            - **Run ID**: `sst14_mutdock_11000`
            - **Iteration**: 6
            - **생성 시각**: 2026-06-11 05:57 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 6 evaluated four candidates for their potential as SSTR2 peptide binders. All candidates passed the quality control (QC) gates, indicating structural and design integrity. The primary focus of this iteration was to improve binding affinity and SSTR2 selectivity. While the candidates demonstrated strong binding affinities, as indicated by ddG values ranging from -20.2 to -27.6 kcal/mol, the selectivity over the native SST-14 baseline remained suboptimal. None of the candidates achieved a significant Δmargin, highlighting selectivity as the primary limitation for this iteration. The pLDDT and docking scores were not informative, as they were uniformly reported as 0.0, suggesting a potential issue with the scoring methodology or data reporting for these metrics.

The top-performing candidates in terms of binding affinity were iter06_cand002 (ddG=-27.6) and iter06_cand006 (ddG=-27.0). These candidates represent the most promising leads for further optimization. However, the lack of selectivity improvement suggests that the design strategy needs refinement to better target SSTR2-specific interactions. Structural failures were noted as the primary failure mode, indicating that future iterations should focus on enhancing structural compatibility and specificity.

            ## Recommendations

            - Refine the design strategy to enhance SSTR2 selectivity, focusing on interactions unique to the SSTR2 receptor.
- Investigate the structural failures to identify common issues and improve structural compatibility.
- Re-evaluate the scoring methodology for pLDDT and docking scores to ensure accurate and informative metrics.
- Conduct a more detailed analysis of the top candidates to identify features that may contribute to improved selectivity.