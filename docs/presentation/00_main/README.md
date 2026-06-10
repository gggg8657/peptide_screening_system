# 00_main 발표 자료 인덱스

SSTR2 타겟 방사성의약품 AI Co-Scientist — 2026-04-05 내부 보고 발표자료

---

## 발표 슬라이드 (5개 버전)

| 파일 | 버전 | 장수 | 용도 | 인쇄 |
|------|------|:----:|------|:----:|
| `04_v_a_demo_first` | A 데모 퍼스트 | 13장 | 데모를 먼저 보여주고 설명하는 구조 | 선택 |
| `04_v_b_action_order` | **B 액션 순서** | 27장 | **메인 발표용** — A-03 등은 two-col 단일 슬라이드로 압축 가능 | **필수** (청중 배포) |
| `04_v_c_formal` | C 격식적 | 12장 | KAERI 공식 보고 형식 (문서번호, 경어체) | 선택 |
| `04_v_d_compact` | **D 압축** | 6장 | **5분 요약** — 바쁜 상급자/PI용 | **권장** (3부) |
| `04_v_e_detailed` | E 디테일 | 19장 | 기술 심층 보고 (수식, 커밋 이력, 알고리즘 포함) | 선택 |

각 **발표 버전**은 `.md` (Marp 소스) + `.html` (브라우저 발표용) + `.pdf` (인쇄용) 3종 세트를 권장합니다.

---

## 부록 및 보충 자료 (일반 마크다운)

| 파일 | 형식 | 내용 |
|------|------|------|
| `05_unified_appendix.md` | **Marp 비사용** | 통합 부록 §A~§J + §E-2, 표지에 §별 목차 |
| `06_selectivity_supplementary.md` | **Marp 비사용** | SSTR1/3/4/5 Off-target Selectivity 추가 보고 |

동봉·갱신 산출물: **`05_unified_appendix.html` / `.pdf`**, **`06_selectivity_supplementary.html` / `.pdf`** (pandoc + Chrome headless로 생성, 아래 스크립트).

### 부록 섹션 목차

| 섹션 | 내용 |
|------|------|
| §A | A-01 도구 전수 조사 결과 (18개 도구 실태) |
| §B | pharma_properties 15메서드 수식 + 78케이스 검증 |
| §C | SS bond Cys pI 보정 상세 (9.04→10.62) |
| §D | DIWV Lookup Table 16건 버그 상세 |
| §E | pepADMET 논문 요약 + ADMETlab 부적합 사유 |
| §E-2 | **pepADMET MGA 아키텍처 상세** (딥러닝 구조, HC50 R²=0.474 해설) |
| §F-0 | Tier 1/2/3 병렬 후보 생성·파레토·BO 맥락 |
| §F | A~E 클러스터 분류 기준 (II<30 보수적 운용 근거) |
| §G | Selectivity 상세 (CIF 5종, WSM/MSM/SR, Tier T0~T3) |
| §H | 반감기 예측 모델 (5종 수정 보너스, 20AA 취약성 스코어) |
| §I | 13-메트릭 우선순위 (★5~★1) |
| §J | Q&A 예상 질문 대응표 (10개) |

---

## 보고서 (기존)

| 파일 | 내용 |
|------|------|
| `01_ACTION_ITEMS_RESPONSE_REPORT` | 액션 리스트 A-01~A-10 대응 보고서 (도구 조사 표 포함) |
| `02_SILO_B_TECHNICAL_REPORT` | Silo B 파이프라인 기술 보고서 |
| `03_SILO_B_MASTER_PRESENTATION_REPORT` | 통합 발표용 (Part I 액션 + Part II 기술) |
| `04_presentation_slides` | 기존 슬라이드 12장 (원본, 수정 전) |
| `05_presentation_script` | 기존 발표 스크립트 (원본) |

---

## 공통 반영 사항 (모든 버전)

- **RI팀 내용 제거**: A-06(합성 견적), A-07(C18 변형체) 관련 내용 전부 삭제
- **Selectivity 상태**: "시스템 구축완료, 시뮬레이션 진행가능"
- **pepADMET 구분**: 코드 공개(재학습 가능) / 모델 공개(추론 성공) / descriptor 진행중
- **Instability Index**: < 30 "(논문 기준 40, 보수적 운용)"
- **selectivity_margin**: `margin = ddG(off-target) − ddG(SSTR2)`, Gate ≥ 3.0 REU
- **ddG 단위**: REU (Rosetta Energy Unit) 명시
- **CSS 수정**: `.small` #444, `.ref` #666 (WCAG 대비 개선)
- **청중**: 방사성의약품/생명공학 연구원 (CS 비전공), 발표자: CS 전공

---

## 빌드 방법

```bash
# 메인 발표 덱만 Marp (HTML / PDF)
npx @marp-team/marp-cli 04_v_b_action_order.md --no-stdin -o 04_v_b_action_order.html
npx @marp-team/marp-cli 04_v_b_action_order.md --no-stdin --pdf --allow-local-files -o 04_v_b_action_order.pdf

# 나머지 발표 버전 일괄
for f in 04_v_*.md; do
  npx @marp-team/marp-cli "$f" --no-stdin -o "${f%.md}.html"
done
```

`05_unified_appendix.md`, `06_selectivity_supplementary.md`는 **Marp로 빌드하지 않습니다.** 대신 아래로 HTML·PDF를 만듭니다.

**요구**: [Pandoc](https://pandoc.org/) · macOS **Google Chrome**(또는 Chromium) — PDF는 Chrome headless `print-to-pdf`.

```bash
cd docs/presentation/00_main
./build_appendix_supplementary.sh
```

수동 예시:

```bash
cd docs/presentation/00_main
pandoc 05_unified_appendix.md -s --toc \
  --metadata title="통합 부록 — SSTR2 방사성의약품 AI Co-Scientist" \
  --css=_md_doc_style.css -o 05_unified_appendix.html
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$(pwd)/05_unified_appendix.pdf" \
  "file://$(pwd)/05_unified_appendix.html"
# 06_selectivity_supplementary 동일 패턴
```

스타일은 `_md_doc_style.css` (pandoc HTML에 링크).

---

## 인쇄 가이드

| 우선순위 | 파일 | 부수 | 비고 |
|:--------:|------|:----:|------|
| 필수 | `04_v_b_action_order.pdf` | 청중 인원수 | Marp PDF, 양면 1-up 또는 2-up |
| 권장 | `04_v_d_compact.pdf` | 3부 | Marp PDF |
| 발표자 | `05_unified_appendix.pdf` (또는 `.html`) | 1부 | 연속 문서 PDF — 4-up 축소 가능 |
| 발표자 | `06_selectivity_supplementary.pdf` | 1부 | 짧은 보충 자료 |
