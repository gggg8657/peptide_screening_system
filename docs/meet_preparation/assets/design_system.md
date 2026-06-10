# Design System — meet_preparation/ 산출물 공통 디자인 토큰
**적용 대상**: 본 디렉토리의 모든 .pptx / .md (보고서·메인 발표·부록 발표 3종)
**작성일**: 2026-06-01
**원칙**: 두 PPTX는 본 토큰을 **동일하게 상속**한다. 보고서 .md의 표·강조도 동일 의미 색을 따른다.

---

## 1. 컬러 팔레트 (Charcoal Minimal + Teal Trust)

### 1-1. 기본 톤
| 토큰 | HEX | 용도 |
|------|-----|------|
| `--bg` | `F2F2F2` | 콘텐츠 슬라이드 배경 (60-70% 비중) |
| `--bg-dark` | `1E2A36` | 타이틀·결론 슬라이드 배경 (sandwich) |
| `--bg-elev` | `FFFFFF` | 카드/패널 배경 |
| `--text` | `1E293B` | 본문 텍스트 |
| `--text-on-dark` | `FFFFFF` | 어두운 배경 위 텍스트 |
| `--muted` | `64748B` | 보조 텍스트·캡션 |
| `--border` | `CBD5E1` | 카드 경계선 |
| `--accent` | `028090` | 메인 액센트(teal) |
| `--accent-light` | `00A896` | 보조 액센트(seafoam) |

### 1-2. Status 색 (P0/P1/P2 일관 사용)
| 토큰 | HEX | 의미 |
|------|-----|------|
| `--good` | `27AE60` | 정상·완료·P3/안전 |
| `--warn` | `D68910` | 부분·P1·주의 |
| `--crit` | `C0392B` | 미달·P0·블로커 |
| `--info` | `2980B9` | 정보·검토 사항 |

### 1-3. 영역 색 (도식의 노드 색 코드, 두 PPT 공통)
| 영역 | HEX | 비고 |
|------|-----|------|
| Backend | `0E7C7B` | dark teal |
| Frontend | `7B2D8E` | violet |
| AI / LLM | `2E4D8F` | indigo |
| MCP | `B45309` | amber |
| Tools | `D97706` | orange |
| vLLM | `5B21B6` | purple |
| Docking | `0891B2` | cyan |
| Silo A | `1D4ED8` | blue |
| Silo B | `15803D` | green |
| Dual-silo | `BE123C` | red |

**규칙**: 도식에 영역 노드가 등장하면 위 색을 그대로 사용하고, 슬라이드 우측 또는 하단에 **범례(legend)** 를 둔다.

---

## 2. 타이포그래피

### 2-1. 폰트
| 용도 | 폰트 | Fallback |
|------|------|---------|
| 슬라이드 타이틀 (영문) | Cambria | Georgia, serif |
| 슬라이드 타이틀 (한글) | Pretendard | "Noto Sans CJK KR", "Malgun Gothic", sans-serif |
| 본문 (영문) | Calibri | Arial, sans-serif |
| 본문 (한글) | Pretendard | "Noto Sans CJK KR", "Malgun Gothic", sans-serif |
| 코드·로그 캡처 | Consolas | "Source Code Pro", monospace |

> **Fallback 메모**: 본 작업 환경에서 Pretendard 미설치 시 PPTX는 시스템 기본 한글 폰트로 표시될 수 있다. 발표용 머신에 Pretendard 또는 Noto Sans CJK KR 설치 권장. **본 산출물은 폰트 fallback 발생 가능성을 인지하고 글자 크기·여백을 보수적으로 설정**한다.

### 2-2. 크기
| 요소 | 크기 |
|------|------|
| 슬라이드 타이틀 | 26pt bold (Cambria) |
| 슬라이드 서브타이틀 | 13pt (Calibri, muted) |
| 섹션 헤더 (슬라이드 내) | 16-18pt bold |
| 본문 | 11-12pt |
| 코드·캡처 | 10-10.5pt (Consolas) |
| 표 본문 | 9.5-10pt |
| 캡션·footer | 9-10pt muted |

---

## 3. 레이아웃 그리드 (16:9 WIDE = 13.3 × 7.5 inch)

### 3-1. 공통 마진
- 외곽 마진: **0.4 inch** (좌우상하 통일)
- 타이틀 영역: y=0.3~1.3 inch (타이틀 0.3-1.0 + 서브타이틀 0.95-1.3)
- 콘텐츠 영역: y=1.4~6.9 inch
- Footer: y=7.05~7.35 inch

### 3-2. 디자인 모티프 (재사용 강제)
- **좌측 0.08 inch 세로 액센트 바**: 모든 콘텐츠 슬라이드 좌측에 y=0.6~6.9 범위로 액센트 컬러 바를 둔다. P0 강조 슬라이드는 `--crit` 색으로 변경.
- **카드 좌측 0.08 inch 컬러 인디케이터**: 모든 카드/패널 좌측에 의미 색(영역색 또는 status색) 인디케이터 바.
- **번호 원형 뱃지**: 단계/우선순위 표시 시 0.55 inch 원형 + Cambria 18-24pt 흰색 숫자.

### 3-3. 타이틀 슬라이드 레이아웃
- 배경: `--bg-dark`
- 우측 0.6 inch 세로 액센트 바 (`--accent`)
- 타이틀: 큰 글씨 (48pt) + 서브타이틀 (32pt accent-light)
- 메타 라인: "초안 보고 / 현재 상태 공유 · 최종 성과 발표 아님" (warn 색 italic)
- 발표자·날짜 footer

### 3-4. 콘텐츠 슬라이드 레이아웃
- 배경: `--bg`
- 좌측 액센트 바 + 타이틀 + 서브타이틀 + 콘텐츠 + footer
- footer 형식: `{LABEL} · 2026-06-01 · 초안 보고        {N} / {TOTAL}`

### 3-5. 클로징/결론 슬라이드 레이아웃
- 배경: `--bg-dark` (sandwich 마감)
- 큰 결론 5줄 또는 종합 의견 박스

---

## 4. "초안/DRAFT" 표기 의무
- 모든 타이틀 슬라이드: 명시적 "초안 보고 / 현재 상태 공유" 텍스트
- 모든 콘텐츠 슬라이드 footer: "초안 보고" 포함
- 보고서 .md: 헤더에 `**상태**: 초안 / 현재 상태 공유 (최종 성과 발표 아님)`

---

## 5. 캡처·로그 표시 규칙
- 캡처는 원본 해상도 유지 (저해상도 확대 금지)
- 코드·로그 블록: 배경 `263238` (dark), 텍스트 `B2DFDB` (mint-on-dark), Consolas 10pt
- 라이브 응답 캡처는 실제 명령어 + 출력 동시 표시

---

## 6. 표 스타일
- 헤더 행: 배경 `--bg-dark`, 텍스트 `--text-on-dark`, bold
- 본문 행: 배경 `--bg-elev` (홀수) / `F8FAFC` (짝수 — 가독성)
- 경계선: 0.5pt `--border`
- 의미 셀: status 색 직접 적용 (예: 미달 셀 `--crit` 텍스트)
- 폰트: Calibri 9.5-10pt

---

## 7. 도식 (Mermaid / PPT 도형) 일관성
- 노드 색은 §1-3 영역 색을 그대로 사용
- 화살표·라인: `--muted` 1pt
- 강조 화살표 (분기·합류): `--accent` 또는 status 색
- 범례 의무: 도식 슬라이드 우측/하단에 영역 색 ↔ 의미 매핑 5-7개 표시

---

## 8. 기본 금지 사항
- Office 기본 테마·클립아트·워드아트·3D 그라데이션 ❌
- 과밀 텍스트(한 슬라이드 8 bullet 이상) ❌
- 색 5종 이상 동시 사용 (Status 3 + 영역 색 ≤ 5) ❌
- 타이틀 아래 액센트 라인 (AI 생성 슬라이드의 전형적 결함) ❌
- 한글 깨짐 가능 폰트 단독 사용 ❌ (반드시 fallback 명시)

---

## 9. 두 PPTX의 디자인 동기화
- 두 PPTX는 본 토큰을 헬퍼 함수 `addTitle()`, `addSideBar()`, `statusBadge()`, `addFooter()` 형태로 공유한다.
- 모든 슬라이드 타이틀 y=0.3, 서브타이틀 y=0.95, 콘텐츠 시작 y=1.4 — 두 PPTX 동일.
- footer 형식·위치 동일.

---

*본 디자인 시스템은 `pptx/build_pptx.js` 빌드 스크립트와 동기화되며, 변경 시 양쪽을 함께 갱신한다.*
