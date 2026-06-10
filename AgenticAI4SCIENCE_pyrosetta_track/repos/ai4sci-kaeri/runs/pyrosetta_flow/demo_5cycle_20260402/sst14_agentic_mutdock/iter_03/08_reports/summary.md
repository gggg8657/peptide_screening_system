# Iteration 3 Summary: sst14_mutdock_2026

            - **Run ID**: `sst14_mutdock_2026`
            - **Iteration**: 3
            - **생성 시각**: 2026-04-02 06:20 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated 5 candidate peptide binders for SSTR2 targeting. While all candidates passed QC gates, structural integrity metrics revealed critical issues. All top candidates exhibited pLDDT=0.0, indicating severe structural failures, and docking scores of 0.00 suggest computational pipeline inconsistencies. The most energetically favorable candidate (iter03_cand003) achieved ddG=-43.6, but this was accompanied by complete structural collapse. The low selectivity pass rate (62.5%) highlights challenges in balancing binding affinity with structural stability. These results underscore the need for recalibrating scoring thresholds and refining structural constraints in subsequent iterations.

            ## Recommendations

            - Re-evaluate ddG/clash thresholds to avoid overly restrictive criteria
- Prioritize structural validation protocols to address pLDDT=0.0 failures
- Implement hybrid scoring functions balancing energetic and structural metrics
- Validate top candidates with experimental binding assays to confirm functional relevance