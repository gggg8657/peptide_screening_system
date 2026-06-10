# 라이트 모드 가시성 전수 분석 — 2026-05-18

**작성**: reviewer-uiux  
**범위**: `frontend/src/` 전체 (컴포넌트 + 페이지 + tokens.css)  
**기준**: WCAG 2.1 AA (소형 텍스트 4.5:1 / 대형 텍스트·아이콘 3.0:1)  
**배경 기준**: `--bg: #fafaf9`, `--bg-elev: #ffffff`, `--bg-sunk: #f5f5f4`

---

## 판정: FAIL

라이트 모드에서 다음 3가지 구조적 문제가 확인됨.

1. OKLCH 토큰 4종이 소형 텍스트 AA 미달 (3.0~3.6:1)
2. slate-300/400 계열 131+163건 전부 라이트 bg에서 invisible 수준
3. color-300/400 계열 371건이 모두 라이트 bg에서 FAIL

---

## 1. OKLCH 토큰 권고 변경 (max 5건)

라이트 테마(`:root, [data-theme="light"]`) 적용 대상.  
다크 테마 값은 현행 유지.

| 토큰 | 현행값 | 현행 대비비 | 권고값 | 권고 대비비 | 근거 |
|------|--------|-----------|--------|-----------|------|
| `--warn` | `oklch(0.62 0.15 60)` | 3.05:1 FAIL | `oklch(0.50 0.16 60)` | 4.81:1 PASS | `#b45309` (amber-700) 동등치. `--warn-soft` 배경 위에서도 4.51:1로 AA 통과 |
| `--pos` | `oklch(0.55 0.13 145)` | 3.16:1 FAIL | `oklch(0.47 0.13 145)` | 4.80:1 PASS | `#15803d` (green-700) 동등치 |
| `--accent` | `oklch(0.58 0.13 200)` | 3.53:1 FAIL | `oklch(0.50 0.13 200)` | 5.13:1 PASS | `#0e7490` (cyan-700) 동등치 |
| `--teal` | `oklch(0.55 0.1 180)` | 3.59:1 FAIL | `oklch(0.47 0.1 180)` | 5.24:1 PASS | `#0f766e` (teal-700) 동등치 |
| `--accent-text` | `oklch(0.42 0.13 200)` | 현재 6.8:1 OK | 변경 불필요 | — | 이미 충분 |

**참고**: `--neg (0.55 0.2 25)` ≈ 4.62:1 (borderline PASS). `--violet (0.55 0.15 290)` ≈ 5.46:1 PASS. 두 토큰은 현행 유지 가능.

**주의**: 위 라이트 토큰 조정은 다크 모드에서 해당 시맨틱 토큰을 사용하는 컴포넌트에 영향 없음 (다크 섹션은 별도 `[data-theme="dark"]` 룰에서 재정의됨).

---

## 2. 하드코딩 잔재 완전 매핑표

### 2-A. 텍스트 색상 매핑

아래 매핑은 기계적 치환(sed/ESLint fix) 가능. 라이트 모드 우선 설계.

| 기존 클래스 | 대비비 on #fafaf9 | 치환 대상 | 비고 |
|------------|-----------------|---------|------|
| `text-slate-100` | 1.10:1 FAIL | `text-[var(--text)]` | 거의 흰색, 완전 invisible |
| `text-slate-200` | 1.18:1 FAIL | `text-[var(--text)]` | 동일 |
| `text-slate-300` | 1.42:1 FAIL | `text-[var(--text-mute)]` | 120건. 가장 빈도 높은 위험 패턴 |
| `text-slate-400` | 2.46:1 FAIL | `text-[var(--text-dim)]` | 131건. `--text-dim` (#78716c) = 4.59:1 PASS |
| `text-slate-500` | 4.56:1 PASS | 유지 가능 (borderline) | — |
| `text-slate-600` | 7.0:1+ PASS | 유지 가능 | — |
| `text-green-300` | 1.34:1 FAIL | `text-[var(--pos)]` | 12건 |
| `text-green-400` | 1.67:1 FAIL | `text-[var(--pos)]` | 87건 |
| `text-red-300` | 1.82:1 FAIL | `text-[var(--neg)]` | 18건 |
| `text-red-400` | 2.65:1 FAIL | `text-[var(--neg)]` | 65건 |
| `text-amber-300` | 1.38:1 FAIL | `text-[var(--warn)]` | 10건 |
| `text-amber-400` | 1.60:1 FAIL | `text-[var(--warn)]` | 49건 |
| `text-yellow-300/400` | 1.3~1.5:1 FAIL | `text-[var(--warn)]` | — |
| `text-cyan-300` | 1.39:1 FAIL | `text-[var(--accent)]` | 40건 |
| `text-cyan-400` | 1.73:1 FAIL | `text-[var(--accent)]` | 43건 |
| `text-blue-300` | 1.73:1 FAIL | `text-[var(--accent)]` | 14건 |
| `text-blue-400` | 2.43:1 FAIL | `text-[var(--accent)]` | 22건 |
| `text-purple-300` | 1.69:1 FAIL | `text-[var(--violet)]` | 9건 |
| `text-purple-400` | 2.53:1 FAIL | `text-[var(--violet)]` | 9건 |
| `text-teal-400` | ~3.0:1 FAIL | `text-[var(--teal)]` | 7건 |
| `text-orange-400` | ~2.9:1 FAIL | `text-[var(--warn)]` | 5건 |
| `text-violet-400` | — FAIL | `text-[var(--violet)]` | 5건 |

### 2-B. 배경 색상 매핑

| 기존 클래스 | 라이트 모드 합성 결과 | 치환 대상 | 비고 |
|------------|------------------|---------|------|
| `bg-slate-700/50`, `bg-slate-700/40` 등 | 중간 회색 패널 | `bg-[var(--bg-sunk)]` | 카드 배경 역할 |
| `bg-slate-800`, `bg-slate-800/60` 등 | 어두운 회색 박스 (~rgb(118,124,135)) | `bg-[var(--bg-elev)]` | 부유 패널 역할 |
| `bg-slate-900`, `bg-slate-900/90` 등 | 진한 회색 박스 | `bg-[var(--bg)]` | 페이지 배경 역할 |
| `bg-green-500/15` | 연두색 tint | `bg-[var(--pos-soft)]` | soft tint용 토큰 이미 존재 |
| `bg-green-500/20`, `/30` | 중간 tint | `bg-[var(--pos-soft)]` | opacity 조정 불필요 |
| `bg-red-500/10`, `/15`, `/20`, `/30` | 연분홍 tint | `bg-[var(--neg-soft)]` | — |
| `bg-amber-500/10`, `/15`, `/20` | 연황색 tint | `bg-[var(--warn-soft)]` | — |
| `bg-yellow-500/10`, `/20` | 연노랑 tint | `bg-[var(--warn-soft)]` | — |
| `bg-cyan-500/10`, `/15`, `/20` | 연시안 tint | `bg-[var(--accent-soft)]` | — |
| `bg-blue-500/10`, `/15`, `/20` | 연파랑 tint | `bg-[var(--accent-soft)]` | — |
| `bg-violet-500/10`, `/20` | 연보라 tint | `bg-[var(--violet-soft)]` | — |
| `bg-purple-500/10`, `/20` | 연보라 tint | `bg-[var(--violet-soft)]` | — |

### 2-C. 경계(border) 색상 매핑

| 기존 클래스 | 치환 대상 |
|------------|---------|
| `border-slate-700`, `border-slate-700/50` 등 | `border-[var(--border)]` |
| `border-slate-800` | `border-[var(--border-strong)]` |
| `border-green-500/30`, `/40` | `border-[var(--pos)]` with opacity 클래스 유지 OR `border-[var(--pos-soft)]` |
| `border-red-500/30`, `/40` | `border-[var(--neg)]` with opacity |
| `border-amber-500/30`, `/40` | `border-[var(--warn)]` with opacity |
| `border-cyan-500/30`, `/40` | `border-[var(--accent)]` with opacity |
| `border-blue-500/30` | `border-[var(--accent)]` with opacity |

---

## 3. 케이스별 예외 (기계적 치환 불가)

### 예외 A — `AgentFlowDiagram.tsx` SVG 인라인 hex

**파일**: `src/components/AgentFlowDiagram.tsx`  
**문제**: SVG 노드 배경에 하드코딩된 어두운 hex:
- `fillColor = '#0c1929'` (active node bg), `'#0f172a'` (idle), `'#0a1a12'` (completed), `'#1e1115'` (error)
- 이 색상들은 **다크 테마 전용 SVG 캔버스**를 가정. 라이트에서는 어두운 박스 안에 밝은 텍스트가 생겨 오히려 역전 가독성 문제 발생.
- edge/arrow hex (`#3b82f6`, `#8b5cf6`, `#f59e0b`)는 라이트 bg에서 FAIL 수준 대비비.

**처리 방안**: JS 코드 내 CSS 변수 참조 필요. 예:
```tsx
const fillColor = isError ? 'var(--neg-soft)' : isActive ? 'var(--accent-soft)' : 'var(--bg-elev)'
const strokeColor = isError ? 'var(--neg)' : isActive ? 'var(--accent)' : 'var(--border)'
```
SVG `fill`/`stroke` props에 `var()` 직접 사용 가능 (현대 브라우저 지원). 기계적 치환 스크립트로는 처리 불가 — **수동 처리 필요**.

### 예외 B — `CombinedPage.tsx` Recharts contentStyle

**파일**: `src/pages/CombinedPage.tsx` L416, L458  
**문제**: Recharts `<Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }}>` — 다크 툴팁이 라이트 모드에서 그대로 렌더링됨.  
**처리 방안**:
```tsx
contentStyle={{ 
  background: 'var(--bg-elev)', 
  border: '1px solid var(--border)', 
  color: 'var(--text)' 
}}
```
기계적 치환: `sed` 패턴으로 처리 가능하나 문자열 내부라 복잡. **수동 수정 권장 (2군데)**.

### 예외 C — `RiskMatrix.tsx` CELL_BG (`bg-red-950/60`, `bg-yellow-950/40`)

**파일**: `src/components/RiskMatrix.tsx` L39–L45  
**문제**: `bg-red-950/60` = 라이트 배경에서 합성 시 어두운 적갈색 (~rgb(141,106,105)) 패널 생성. 그 위에 배지 텍스트를 `text-[var(--neg)]`(토큰 사용)로 출력하지만, 배지 bg인 `bg-red-500/20`도 라이트에서 불충분.  
**처리 방안**: `bg-red-950/60` → `bg-[var(--neg-soft)]`. `bg-yellow-950/40` → `bg-[var(--warn-soft)]`. 단, 매트릭스 셀의 "심각도를 색상 강도로 표현"하는 시각 계층구조를 유지하려면 토큰 soft 레벨로는 구분이 약해질 수 있음 — 다크/라이트 테마별 분기 처리 또는 `opacity` 조정 고려.

### 예외 D — `HeuristicBanner.tsx` `bg-*-900/20`

**파일**: `src/components/HeuristicBanner.tsx` L39,47,63  
**문제**: `bg-green-900/20` = 라이트에서 연초록 (rgb≈204,216,205). 그 위 `text-green-400` = 대비비 1.18:1 (사실상 invisible). 단, `labelColor: 'text-green-400'`은 바로 위 기계적 치환 대상(`→ text-[var(--pos)]`)으로 해결됨.  
**처리 방안**: `bg-green-900/20` → `bg-[var(--pos-soft)]`. 배너 bgColor를 토큰으로 교체하면 라이트/다크 동시 해결.

### 예외 E — `QCGateChart.tsx` / `ExperimentControl.tsx` 대규모 미마이그레이션

**파일**: `src/components/QCGateChart.tsx` (slate-200/300/700 다수), `ExperimentControl.tsx` (slate-300/400/800 다수)  
**문제**: 두 파일 모두 헤더(`text-slate-300 uppercase tracking-widest`), 입력 필드(`bg-slate-800 border border-slate-700 ... text-cyan-300`), 툴팁(`bg-slate-800 border border-slate-700 text-xs`)에서 다크 전용 패턴이 방치됨.  
**처리 방안**: 기계적 치환 스크립트 적용 후 토큰 클래스로 교체. `<input>`/`<select>` 요소의 `bg-slate-800` → `bg-[var(--bg-elev)]` 로 처리.

### 예외 F — `SARHeatmap.tsx` (안전한 예외)

**파일**: `src/components/SARHeatmap.tsx`  
**상태**: 전부 `var(--*)` 토큰 사용 (`fill="var(--warn)"`, `fill="var(--text)"` 등). 기계적 치환 스크립트 **적용 제외** 대상. 이미 올바르게 토큰화됨. `color-mix(in oklch, var(--bg-sunk) ... var(--accent) ...)` 패턴도 라이트/다크 자동 대응.

### 예외 G — `text-white` 5건

| 파일 | 컨텍스트 | 처리 |
|------|---------|------|
| `CandidatePage.tsx:412` | `bg-pos` (filled button) 위 흰 텍스트 | 유지 — filled button에서 white는 정상 |
| `RunLauncherPage.tsx:164` | 동일 패턴 | 유지 |
| `RunLauncherPage.tsx:456` | `bg-accent` 위 white | 유지 |
| `SelectivityExplorerPage.tsx:187` | `value > 0.93 ? 'text-white'` (dense cell) | 유지 — 고채도 셀 위 white는 의도적 |
| `HeatmapCell.tsx:46` | `value > 0.92 ? 'text-white'` | 유지 — 동일 이유 |

모두 **filled 배경 위 white** 패턴 → 라이트 모드에서 배경이 color 토큰 기반이면 충분히 어두워 허용 가능. **예외 처리**.

---

## 4. 우선순위별 개선 로드맵

### P0 — 즉시 수정 (Token 자체, 5건, tokens.css 단일 파일)

`src/styles/tokens.css`의 `:root, [data-theme="light"]` 블록에서:

```diff
-  --warn: oklch(0.62 0.15 60);
+  --warn: oklch(0.50 0.16 60);
-  --pos: oklch(0.55 0.13 var(--pos-hue));
+  --pos: oklch(0.47 0.13 var(--pos-hue));
-  --accent: oklch(0.58 0.13 var(--accent-hue));
+  --accent: oklch(0.50 0.13 var(--accent-hue));
-  --teal: oklch(0.55 0.1 var(--teal-hue));
+  --teal: oklch(0.47 0.1 var(--teal-hue));
```

효과: 토큰을 직접 사용하는 `dashboard/TierBadge`, `dashboard/PipelineFlow`, `dashboard/Sequence`, `RiskMatrix` 등 ~90개 토큰 참조가 자동 수정됨.

### P1 — 기계적 치환 스크립트 (색상 토큰 일괄 적용)

대상 파일: `src/components/*.tsx`, `src/pages/*.tsx`  
제외: `src/components/SARHeatmap.tsx` (이미 토큰화됨)  
수동 처리: `AgentFlowDiagram.tsx`, `CombinedPage.tsx` (Recharts contentStyle)

**sed 스크립트 예시** (검증 후 사용):
```bash
# text-slate-300/400 → token
find src -name "*.tsx" ! -name "SARHeatmap.tsx" -exec sed -i \
  -e 's/text-slate-300/text-\[var(--text-mute)\]/g' \
  -e 's/text-slate-400/text-\[var(--text-dim)\]/g' \
  -e 's/text-green-[34]00/text-\[var(--pos)\]/g' \
  -e 's/text-red-[34]00/text-\[var(--neg)\]/g' \
  -e 's/text-amber-[34]00/text-\[var(--warn)\]/g' \
  -e 's/text-cyan-[34]00/text-\[var(--accent)\]/g' \
  -e 's/text-blue-[34]00/text-\[var(--accent)\]/g' \
  -e 's/text-purple-[34]00/text-\[var(--violet)\]/g' \
  -e 's/text-violet-[34]00/text-\[var(--violet)\]/g' \
  -e 's/text-teal-400/text-\[var(--teal)\]/g' \
  {} +
```

**bg 치환**:
```bash
find src -name "*.tsx" ! -name "SARHeatmap.tsx" -exec sed -i \
  -e 's/bg-slate-800[^,")> ]*/bg-\[var(--bg-elev)\]/g' \
  -e 's/bg-slate-900[^,")> ]*/bg-\[var(--bg)\]/g' \
  -e 's/bg-green-[5-9][0-9][0-9]\/[0-9]*/bg-\[var(--pos-soft)\]/g' \
  -e 's/bg-red-[5-9][0-9][0-9]\/[0-9]*/bg-\[var(--neg-soft)\]/g' \
  -e 's/bg-amber-[5-9][0-9][0-9]\/[0-9]*/bg-\[var(--warn-soft)\]/g' \
  -e 's/bg-yellow-[5-9][0-9][0-9]\/[0-9]*/bg-\[var(--warn-soft)\]/g' \
  -e 's/bg-cyan-[5-9][0-9][0-9]\/[0-9]*/bg-\[var(--accent-soft)\]/g' \
  -e 's/bg-blue-[5-9][0-9][0-9]\/[0-9]*/bg-\[var(--accent-soft)\]/g' \
  -e 's/bg-violet-[5-9][0-9][0-9]\/[0-9]*/bg-\[var(--violet-soft)\]/g' \
  -e 's/bg-purple-[5-9][0-9][0-9]\/[0-9]*/bg-\[var(--violet-soft)\]/g' \
  -e 's/bg-green-[89][0-9][0-9]\/[0-9]*/bg-\[var(--pos-soft)\]/g' \
  -e 's/bg-red-[89][0-9][0-9]\/[0-9]*/bg-\[var(--neg-soft)\]/g' \
  {} +
```

**경고**: `bg-slate-800/60` 등 opacity suffix 치환은 Tailwind v4 임의값 문법과 혼재 주의. 치환 후 반드시 `npm run build` 및 `vite preview`로 시각 확인 필요.

### P2 — 수동 수정 (4건, 복잡 케이스)

1. `AgentFlowDiagram.tsx` — SVG 인라인 hex → CSS 변수 (예외 A)
2. `CombinedPage.tsx` L416, L458 — Recharts contentStyle → 토큰 (예외 B)
3. `HeuristicBanner.tsx` — `bg-*-900/20` → `bg-[var(--pos/neg/warn-soft)]` (예외 D)
4. `RiskMatrix.tsx` CELL_BG — `bg-red-950/60`, `bg-yellow-950/40` → 토큰 or 테마 분기 (예외 C)

### P3 — 잔여 slate 계열 (slate-500 이하, 저위험)

`text-slate-500` (4.56:1 borderline PASS) — 치환 불필요하나 `text-[var(--text-dim)]` 로 통일 가능.  
`border-slate-700` 계열 — `border-[var(--border)]` 로 기계적 치환 권장.

---

## 5. 수치 요약

| 위험 범주 | 건수 | WCAG 위반 | 치환 방식 |
|---------|-----|---------|---------|
| text-slate-100/200/300 | 163건 | FAIL (1.1~1.4:1) | 기계적 |
| text-slate-400 | 131건 | FAIL (2.46:1) | 기계적 |
| text-{hue}-300/400 | 371건 | FAIL (1.3~2.7:1) | 기계적 |
| bg-slate-700~950 (dark card) | 96건 | 구조 파괴 | 기계적 |
| bg-{hue}-500+/opacity (soft bg) | 179건 | soft bg 자체는 무해하나 위 텍스트가 FAIL | 기계적 |
| bg-{hue}-900/950 (near-black) | 12건 | 라이트서 이질적 어두운 박스 | 수동 |
| inline hex (AgentFlowDiagram, CombinedPage) | 65건 | 다크 전용 | 수동 |
| OKLCH 토큰 직접 적용 (~90 refs) | — | 3.0~3.6:1 FAIL | tokens.css 단일 수정 |

**총 대응 필요 건수**: ~1,017건 (기계적 940건 + 수동 ~77건)  
**기계적 일괄 처리 비율**: ~93%

---

## 6. 검증 필요 사항

- [ ] P0 토큰 조정 후 다크 모드 시각 회귀 여부 (`[data-theme="dark"]`는 별도 값이므로 영향 없지만 확인)
- [ ] `AgentFlowDiagram` SVG: CSS 변수로 교체 후 크로스 브라우저(Safari) 테스트
- [ ] Recharts tooltip: `contentStyle` 교체 후 hover 시각 확인
- [ ] sed 치환 스크립트: `npm run build` 에러 없음 + `vite preview` 라이트/다크 전환 테스트
- [ ] `HeatmapCell` / `SelectivityExplorerPage` text-white 유지 케이스: filled cell 배경색이 충분히 어두운지 재확인
