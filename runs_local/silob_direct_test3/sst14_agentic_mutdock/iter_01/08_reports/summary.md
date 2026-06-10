# Iteration 1 Summary: sst14_mutdock_42

            - **Run ID**: `sst14_mutdock_42`
            - **Iteration**: 1
            - **생성 시각**: 2026-04-01 08:32 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated four SSTR2 peptide binder candidates, all of which passed QC gates. However, all candidates exhibited critically low pLDDT (0.0) and docking scores (0.00), indicating severe structural abnormalities despite meeting basic validity criteria. The ddG values ranged from -19.7 to -38.9, suggesting varying degrees of binding affinity potential. The primary failure type was structural failures, which likely compromise the feasibility of these candidates for further development. While the QC pipeline successfully filtered out invalid structures, the results highlight the need for targeted refinements to improve structural integrity and docking accuracy.

The top candidates based on ddG are iter01_cand002 (-38.9), iter01_cand001 (-34.8), iter01_cand004 (-20.9), and iter01_cand003 (-19.7). These candidates demonstrate the highest binding affinity potential among the group, but their structural validity remains questionable. The uniformly low pLDDT and docking scores suggest a systemic issue in the design process that requires investigation. Further analysis of the structural failures is critical to refine the design strategy for subsequent iterations.

The results underscore the necessity of addressing structural failures while maintaining binding affinity. The next iteration should prioritize optimizing the peptide backbone and interactions to improve pLDDT and docking scores. Additionally, re-evaluating the scoring functions or incorporating constraints to avoid structural abnormalities may enhance the quality of generated candidates.

            ## Recommendations

            - Refine the design process to address systemic structural failures while preserving binding affinity
- Prioritize optimization of peptide backbone and interaction patterns to improve pLDDT and docking scores
- Re-evaluate scoring functions or incorporate structural constraints to avoid abnormal configurations