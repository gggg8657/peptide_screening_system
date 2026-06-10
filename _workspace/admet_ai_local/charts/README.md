# ADMET-AI charts (Layer 3) — PRST-001…004 + Octreotide

- **원천 데이터(단일 진실 원천 파일)**: `_workspace/admet_ai_local/layer3_prst001_004_octreotide_raw.json`  
  각 항목 `n_endpoints: 104` 예측 딕셔너리를 그대로 사용한다.
- **재현 스크립트**: `build_prst_admet_ai_charts.py` (`python3 build_prst_admet_ai_charts.py`)
- **H-06(외삽)**: 순환 펩티드 및 SS-bond 화합물은 ADMET-AI 학습 분포 밖일 수 있으며, 본 디렉터리 PNG의 영문 부제목에 동일 경고가 반복된다. 발표 한국어 캡션은 `docs/meet_log/2026-04-06_action_items/PRST_comprehensive_matrix_2026-05-21.md`를 사용한다.

| 산출물 | 내용 |
|--------|------|
| `admet_ai_heatmap_104x5.png` | 후보 순서(PRST-001→004→Oct) 열 × 104 키 행 열 지도 (행별 min-max 노멀라이즈) |
| `admet_ai_diff_prst001_vs_octreotide_top.png` | PRST-001 − Octreotide 차이 상위 32키 |
| `admet_ai_tier_scatter_toxicity_vs_absorption_proxy.png` | 티어( tier CSV 표기 ) vs 흡수·독성 proxy 산포 |
| `chart_metadata_minimal.json` | 산포도에 포함된 소수 필드 재현용 숫자 |

엔드포인트 카테고리(Absorption/Distribution/Metabolism/Excretion/Toxicity) 매핑은 스크립트 내 `category_for_key()` 규칙에 따른다(시각 분류 목적).
