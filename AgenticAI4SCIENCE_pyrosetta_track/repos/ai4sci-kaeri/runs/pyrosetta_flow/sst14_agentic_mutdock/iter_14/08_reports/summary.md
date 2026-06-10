# Iteration 14 Summary: sst14_mutdock_4000

            - **Run ID**: `sst14_mutdock_4000`
            - **Iteration**: 14
            - **생성 시각**: 2026-06-10 16:43 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            Iteration 14 evaluated three candidates for SSTR2 peptide binding, all of which passed quality control (QC) gates. While the candidates demonstrated strong binding affinity, as indicated by ddG values ranging from -17.0 to -23.9 kcal/mol, selectivity over off-targets remained a critical limitation. Only one candidate achieved a positive Δmargin, highlighting the need for improved selectivity in future designs. The primary failure mode was attributed to structural interactions that allowed off-target binding, likely due to conserved pocket residues. This suggests that current designs are not sufficiently optimized to avoid interactions with non-SSTR2 targets.

            ## Recommendations

            - Focus on modifying the peptide sequence to disrupt conserved interactions with off-target pockets while preserving SSTR2 binding.
- Incorporate selectivity metrics more explicitly into the design pipeline to prioritize candidates with higher Δmargin values.
- Perform additional molecular dynamics simulations to better understand the structural basis of off-target interactions and guide future design strategies.