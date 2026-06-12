# Iteration 10 Summary: sst14_mutdock_21000

            - **Run ID**: `sst14_mutdock_21000`
            - **Iteration**: 10
            - **생성 시각**: 2026-06-12 00:08 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 10 of the SSTR2 peptide binder design campaign evaluated a total of 2 candidates, with both passing all QC gates. However, the structural quality of the candidates was poor, as evidenced by pLDDT scores of 0.0 for all designs. The binding affinity, as measured by ddG, ranged from -31.8 to -39.6 kcal/mol, with the most favorable value observed for iter10_cand001. Despite moderate selectivity (Δmargin > 0), the low pass rate (25%) and lack of structural confidence highlight limitations in the current design strategy. These results suggest that the structural sampling process may be insufficient, and the mutagenesis approach could benefit from greater specificity to preserve the pharmacophore while enhancing selectivity.

            ## Recommendations

            - Improve structural sampling by refining the modeling protocol to increase pLDDT scores and ensure better structural confidence.
- Refine mutagenesis strategies to focus on residues critical for selectivity and pharmacophore integrity.
- Incorporate additional constraints or scoring functions to guide the design process toward higher-quality, more selective candidates.
- Consider increasing the diversity of the candidate pool to improve the pass rate and identify more promising leads.