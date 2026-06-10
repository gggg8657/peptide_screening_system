# Stability Predictor — 8 후보 평가 결과

> ⚠️ hl_score_heuristic은 ranking score (NOT clinical half-life)

| seq_id     | sequence        | MW (Da) | GRAVY | Instab. | pI   | Boman | Aliphatic | HL score* | Nephrotox | Tryp sites | Chymo sites         |
| ---------- | --------------- | ------- | ----- | ------- | ---- | ----- | --------- | --------- | --------- | ---------- | ------------------- |
| SST14_ref  | AGCKNFFWKTFTSC  | 1640    | 0.03  | 30.6    | 8.91 | 0.69  | 7.1       | 40.6      | High      | [4, 9]     | [6, 7, 8, 11]       |
| cand03     | AICKNFFWKTFTSC  | 1696    | 0.38  | 30.6    | 8.91 | 0.41  | 35.0      | 40.6      | High      | [4, 9]     | [6, 7, 8, 11]       |
| T3_1       | ILCKKFFWKTFTSC  | 1752    | 0.49  | 55.1    | 9.39 | 0.11  | 55.7      | 36.8      | High      | [4, 5, 9]  | [6, 7, 8, 11]       |
| T3_2       | IGCWWFFWKTFTSC  | 1812    | 0.62  | 58.3    | 8.06 | -0.73 | 27.9      | 43.3      | Moderate  | [9]        | [4, 5, 6, 7, 8, 11] |
| T3_3       | AGCKNDFWKTLTSC  | 1574    | -0.35 | 27.2    | 8.09 | 1.39  | 35.0      | 41.9      | Moderate  | [4, 9]     | [7, 8]              |
| T3_4       | QTCKNFFWKTFTSC  | 1741    | -0.37 | 30.6    | 8.90 | 1.47  | 0.0       | 40.8      | High      | [4, 9]     | [6, 7, 8, 11]       |
| T3_5       | AGCKWEFWKTLTSC  | 1660    | -0.16 | 32.6    | 8.09 | 0.61  | 35.0      | 41.2      | Moderate  | [4, 9]     | [5, 7, 8]           |
| var12_dThr | AICKNFFWKTFT[d… | 1710    | 0.39  | 7.4     | 8.91 | 0.35  | 35.0      | 88.6      | High      | [4, 9]     | [6, 7, 8, 11]       |

\* hl_score_heuristic = ranking score (NOT clinical half-life). HEURISTIC 신뢰등급.
