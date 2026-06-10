# 2026-03-30 내부 미팅 — 발표 자료 (단일 묶음)

이 폴더에 **오늘 발표에 필요한 Marp 원고·HTML·아젠다·도식 원본**을 모두 모아 두었습니다.  
상위 레포의 다른 문서(`../progress_report_*.md`, `../action_items_tracker.md` 등)는 **참고 링크**로만 쓰입니다.

---

## 빠른 선택 가이드

| 상황 | 열 파일 |
|------|---------|
| **회의 진행 순서·시간 배분만 본다** | [`agenda.md`](agenda.md) |
| **프로젝터 / 다크 테마 슬라이드** | [`marp_meeting_dark.md`](marp_meeting_dark.md) 또는 [`html/marp_meeting_dark.html`](html/marp_meeting_dark.html) |
| **인쇄·밝은 배경 (v2 통합본)** | [`marp_meeting_print.md`](marp_meeting_print.md) 또는 [`html/marp_meeting_print.html`](html/marp_meeting_print.html) |
| **NIM → 로컬 파이프라인 마이그레이션만** | [`marp_migration.md`](marp_migration.md) 또는 [`html/marp_migration.html`](html/marp_migration.html) |

---

## 디렉터리 구조

```
presentation_20260330/
├── README.md                 ← 이 파일 (목차·용도)
├── agenda.md                 ← 아젠다·핵심 숫자·협의 사항
├── marp_meeting_dark.md      ← 내부 미팅 본편 (다크 테마, ~44슬라이드)
├── marp_meeting_print.md     ← 인쇄용 v2 (밝은 테마, 아젠다·인프라·Critic 융합)
├── marp_migration.md         ← 서버 마이그레이션 전용 (~15슬라이드)
├── html/                     ← 브라우저 미리보기용 (Marp 내보내기 산출물)
│   ├── marp_meeting_dark.html
│   ├── marp_meeting_print.html
│   └── marp_migration.html
└── figures/                  ← Mermaid 소스 (.mmd) + 도식 README
```

---

## Marp HTML 다시 만들기

레포 루트가 아니라 **이 폴더를 기준**으로 실행합니다 (`--no-stdin` 필수).

```bash
cd docs/presentation_20260330
npx --yes @marp-team/marp-cli@latest --no-stdin marp_meeting_dark.md   -o html/marp_meeting_dark.html
npx --yes @marp-team/marp-cli@latest --no-stdin marp_meeting_print.md  -o html/marp_meeting_print.html
npx --yes @marp-team/marp-cli@latest --no-stdin marp_migration.md    -o html/marp_migration.html
```

PDF가 필요하면 `-o 파일명.pdf`로 동일하게 지정하면 됩니다.

---

## 도식 (Mermaid)

[`figures/README.md`](figures/README.md)에 `mmdc`로 PNG/SVG 뽑는 방법이 있습니다. 슬라이드에 넣을 때는 생성한 이미지를 Marp에 `![](figures/xxx.png)` 형태로 넣으면 됩니다.

---

## 관련 문서 (레포 기타 경로)

| 문서 | 경로 |
|------|------|
| 진행 보고 | `../progress_report_20260323.md` |
| 액션 65건 | `../action_items_tracker.md` |
| meet_log | `../../meet_log.md` (레포 루트) |
