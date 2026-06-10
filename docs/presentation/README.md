# 발표 자료 목차

SSTR2 타겟 방사성의약품 후보 스크리닝 AI 파이프라인 — 발표/보고 자료 통합 디렉토리.

---

## 메인 자료 (00_main/)

| 번호 | 파일 | 설명 |
|------|------|------|
| 1 | `01_ACTION_ITEMS_RESPONSE_REPORT.md/.pdf` | 액션 리스트 대응 보고서 — A-01~A-10 전체 대응 |
| 2 | `02_SILO_B_TECHNICAL_REPORT.md/.pdf` | Silo B 기술 보고서 — 파이프라인 상세 |
| 3 | `03_SILO_B_MASTER_PRESENTATION_REPORT.md/.pdf` | 통합 발표용 — Part I(액션) + Part II(기술) |
| 4 | `04_presentation_slides.md/.html/.pdf` | 발표 슬라이드 — Marp 12장 (HTML로 발표) |

---

## 부록 (01_appendix/)

| 파일 | 설명 |
|------|------|
| `system_architecture_guide.md` | 시스템 아키텍처 가이드 (→ ai4sci-kaeri/docs/reports/ symlink) |
| `system_overview_for_biologists.md` | 생명공학자용 시스템 개요 (→ ai4sci-kaeri/docs/reports/ symlink) |
| `action_items_mapping.md` | 액션 아이템 코드↔UI 매핑 |
| `silo_b_computational_definitions.md` | 필드별 수식 및 정의 |
| `silo_b_code_to_ui_pipeline_trace.md` | 파이프라인 추적 (코드 → UI) |
| `silo_b_dashboard_panels_methodology.md` | 대시보드 패널별 방법론 |
| `admet_alternative_plan.md` | pepADMET 대안 계획 |
| `pepadmet_reproduction_plan.md` | pepADMET 재현 계획 |
| `demo_scenario.md` | 시연 시나리오 (2026-04-03) |
| `system_architecture_guide.pdf` | 시스템 아키텍처 가이드 PDF |

> **참고**: `system_architecture_guide.md`, `system_overview_for_biologists.md`는
> `AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/docs/reports/` 의 symlink입니다.
> 원본을 수정하면 여기서도 반영됩니다.

---

## 스크린샷 (screenshots/)

UI 대시보드 캡처 이미지. `20260403/` 서브디렉토리에 최신본 포함.

---

## UI Walkthrough (03_ui_walkthrough/)

Silo B 대시보드 스크롤 캡처 (`assets/scroll_*.png`) 및 안내 문서.

---

## 빌드 스크립트 (_build/)

| 파일 | 설명 |
|------|------|
| `build_action_items_report.py` | 액션 아이템 보고서 PDF 빌드 |
| `build_silo_b_master_report.py` | 통합 발표 보고서 PDF 빌드 |
| `build_silo_b_technical_report.py` | Silo B 기술 보고서 PDF 빌드 |
| `_md_to_pdf_weasyprint.py` | Markdown → PDF 변환 유틸리티 |
| `resize_report_images.py` | 보고서 이미지 리사이즈 |

PDF 재빌드: `cd docs/presentation/_build && python build_silo_b_master_report.py`

---

## 아카이브 (_archive/)

이전 버전, 임시 파일, 구버전 슬라이드 등 보존용 디렉토리.
