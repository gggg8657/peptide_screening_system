# Iteration 1 Summary: sst14_mutdock_1000

            - **Run ID**: `sst14_mutdock_1000`
            - **Iteration**: 1
            - **생성 시각**: 2026-03-23 09:18 UTC
            - **생성 방식**: LLM (Qwen 2.5 7B)

            ## Summary

            This iteration evaluated a single candidate (iter01_cand001) with pLDDT=0.0, dock score=0.00, and ddG=-37.2. All candidates passed QC gates, but the low pLDDT and dock score suggest significant structural and docking challenges. The critic analysis highlights overly restrictive ddG thresholds and potential structural failures in top candidates, which may have contributed to the low pass rate despite passing QC gates. Further investigation is required to resolve structural inconsistencies and optimize scoring parameters.

            ## Recommendations

            - Adjust ddG threshold criteria to balance stringency with candidate viability
- Refine structural modeling protocols to improve pLDDT and dock score reliability
- Validate structural integrity of top candidates using experimental or high-resolution data