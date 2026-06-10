# PRST 종합 매트릭스 + ADMET-AI 시각 묶음 — 세션 종료 로그

**작업일시**: 2026-05-21  
**Git**: 사용자 지시대로 **commit 없음** (작업 트리에 문서만 추가·갱신).  
**스코프**: PRST-001…004 종합 패널 및 Layer3 차트 생성만 (다른 세션 코드 디렉터리 비터치 원칙 유지 시도).

## 완료한 산출물

| # | 결과 | 비고 |
|---|------|------|
| 1 | `docs/meet_log/2026-04-06_action_items/PRST_comprehensive_matrix_2026-05-21.md` | tier CSV·의뢰서·재검증 MD·Boltz값·radiolysis·ADMET 교차 근거; **CSV hard_pass vs 재측 1.00 모순** 문서만 |
| 2 | `_workspace/admet_ai_local/charts/` 신규 | `build_prst_admet_ai_charts.py`, 삼중 PNG 산물, `chart_metadata_minimal.json`, KO `README.md` |
| 3 | `docs/meet_log/2026-04-06_action_items/PRST_one_page_summary_2026-05-21.md` | D-7 브리프용 한 장 레퍼런스 |

## 차트 종류 확인

| ID | 파일 | 근거 |
|----|------|------|
| (a) | `admet_ai_heatmap_104x5.png` | 레이아웃 카테고리 정렬 후 min-max 노멀 |
| (b) | `admet_ai_diff_prst001_vs_octreotide_top.png` | PRST-001 − Octreotide 상위 32 차이키 |
| (c) | `admet_ai_tier_scatter_toxicity_vs_absorption_proxy.png` | tier 라벨( tier CSV 규격 ) vs proxy 축(raw Layer3) |

영어 축 문자는 DejaVuSans 글립 한계 때문에 사용. 한글 H-06 본문은 KR 문서 참조하도록 `README.md`에 교차 링크.

## 품질·금지 규약 준수 체크

- **실측만**: 레포 내 위에서 열린 경로 문자열만 인용했다. 새 수치 역산 거의 없음(차트 min-max 규격 제외)·수치 교차 검증 가능.
- **H-06 차트 디스크로저**: PNG 타이틀 & 스크립트 상수 문자열 포함.
- **Tier**: `tier_*` CSV + `composite_scorer.py` 헤더 주석에 정렬했다.
- **Layer1/2**: 사용자 지정 read-only 디렉터리에 시간 산물 없음 명시했다. 라우팅 라인은 코드 인용 문자열뿐이다.

## 남긴 FOLLOW-UPS (외부 과제 · 이번 PR 범위 밖)

| 항목 | 주체 |
|------|------|
| `hard_cutoff_pass` 업데이트 vs 재측 1.00 정합 재현성 | scorer 파이프라인 책임 |
| Layer2 PEPlife2 결과를 별도 JSON으로 귀속 | infra / backend 향후 |
| HTML 대체 차트 필요 시(plotly)·서체 통합 브라우저 프리즈 | 디자인/FE |

## 검증 명령(재실행 안내)

```
python3 _workspace/admet_ai_local/charts/build_prst_admet_ai_charts.py
```

`matplotlib Agg` 헤드리스 패스 확인됨(Ubuntu 6.x).
