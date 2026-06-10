# FE UX 패치 리뷰 보고서 — P14 + P05 + P15

**작성일**: 2026-05-14  
**작성자**: reviewer-uiux  
**대상**: dag-v21-tier0 LiveRun 통합 분석 v2.1  
**태스크**: #4 (P05+P14+P15: FE UX 패치 3건)

---

## 요약: PASS (3건 적용 완료)

| 패치 | 상태 | 변경 파일 | 비고 |
|------|------|-----------|------|
| P14 worst off-target hotfix | ✅ PASS | `useSelectivity.ts` | 데이터 오류 수정 |
| P05 ClusterPanel payload 확장 | ✅ PASS | `types/index.ts`, `usePipelineStatus.ts`, `ClusterPanel.tsx` | BE 스키마 누락 발견 → 보고 |
| P15 Skipped 뱃지 dot 추가 | ✅ PASS | `ValidationPanel.tsx` | WCAG 1.4.11 충족 |
| **빌드** | ✅ 무에러 | — | `npm run build` |
| **린트** | ✅ 무에러 | — | `npm run lint` |
| **테스트** | ✅ 60/60 | — | `npm test` |

---

## P14 — worst off-target FE 데이터 오류 hotfix

### 문제
`useSelectivity.ts` `_mapCandidates`가 `offtarget_ddg`에서 **max** (가장 덜 음수)를 worst로 계산.  
BE는 `min(scores)` (가장 음수 = 가장 강한 결합 = 가장 위험) 기준으로 `offtarget_max_receptor`, `offtarget_max_score` 응답.  
→ 사용자에게 표시된 "가장 위험한 off-target"이 실제와 반대.

### 수정
```diff
- const otEntries = Object.entries(ot)
- const worstEntry = otEntries.reduce(
-   (max, [k, v]) => (v > (max[1] as number) ? [k, v] : max),
-   ['', -Infinity] as [string, number],
- )
...
- offtarget_max_receptor: worstEntry[0],
- offtarget_max_score: worstEntry[1] === -Infinity ? 0 : worstEntry[1],
+ // P14: BE가 min(scores) 기준으로 계산한 worst off-target 사용
+ offtarget_max_receptor: (c.offtarget_max_receptor as string) ?? '',
+ offtarget_max_score: (c.offtarget_max_score as number) ?? 0,
```

### BE 확인
`backend/routers/selectivity.py:266, 273-274`:
```python
worst_receptor = min(offtarget_scores, key=offtarget_scores.get)
"offtarget_max_receptor": worst_receptor,
"offtarget_max_score": round(worst_ot, 2),
```
BE가 올바른 값을 이미 응답 — FE에서 재계산 불필요함을 확인.

---

## P05 — ClusterPanel payload 확장

### 순서 (완료)
1. ✅ `types/index.ts` — `Candidate` 인터페이스에 6 optional 필드 추가
2. ✅ `usePipelineStatus.ts` — `mapCandidate`에서 6필드 매핑
3. ✅ `ClusterPanel.tsx` — payload에 6필드 포함

### 타입 충돌 수정
`CandidateCompareModal.tsx`의 `ExtendedCandidate`가 `instability_index?: number | null`로 선언되어 있었으나, 새 베이스 타입이 `number`만 허용해 TypeScript 오류 발생.  
→ `Candidate.instability_index`를 `number | null`로 변경 (근거: `stability.py:124`에서 NaN → None 반환).  
→ `ExtendedCandidate`의 중복 선언 제거.

### ⚠️ BE 스키마 누락 — 팀 리더 보고 필요

| 필드 | BE 위치 | `/api/status` candidates 포함? |
|------|---------|-------------------------------|
| `selectivity_margin` | `routers/selectivity.py` | ❌ 없음 (selectivity 전용 endpoint만) |
| `instability_index` | `pharmacology.py`, `stability.py` | ❌ 없음 |
| `gravy` | `pharmacology.py` | ❌ 없음 |
| `net_charge_ph74` | `admet.py` | ❌ 없음 |
| `fwkt_contact` | **코드베이스 전체 없음** | ❌ 미구현 |
| `chelator_site_available` | **코드베이스 전체 없음** | ❌ 미구현 |

**결론**: FE 타입/매핑/payload는 준비 완료. BE가 `/api/status` candidates dict에 위 필드를 포함시켜야 ClusterPanel에 실데이터가 전달됨.  
`fwkt_contact`, `chelator_site_available`은 BE 신규 구현 필요 (후속 작업).

---

## P15 — Validation Skipped 뱃지 + dot

### 변경
```diff
- {r.checks.filter(c => !c.skipped).map(c => (
-   <div key={c.id} title={...} className={cn('w-2 h-2 rounded-full', ...)} />
- ))}
+ {r.checks.map(c => (
+   c.skipped ? (
+     <div key={c.id}
+       aria-label="skipped"
+       title="이 검증은 데이터 부족으로 스킵됨"
+       className="w-2 h-2 rounded-full bg-slate-500"
+     />
+   ) : (
+     <div key={c.id}
+       title={`${c.label}: ${c.value} ${c.unit} — ${c.passed ? 'PASS' : 'FAIL'}`}
+       aria-label={c.passed ? 'passed' : 'failed'}
+       className={cn('w-2 h-2 rounded-full', c.passed ? 'bg-green-500' : 'bg-red-500')}
+     />
+   )
+ ))}
```

### ASCII 와이어프레임 Before/After

**Before** (skipped 제외):
```
SEQ_001  AGCKNFF...  CAUTION(80%)  [●●●●○●○●]  [Detail]
                                    ↑ pass/fail dots only, skipped hidden
```

**After** (skipped 회색 dot 포함):
```
SEQ_001  AGCKNFF...  CAUTION(80%)  [●●●●○●◉●]  [Detail]
                                             ↑ 회색 dot = skipped
                                    ● green=pass  ○ red=fail  ◉ gray=skipped
```

### WCAG 접근성 검증

| 항목 | 기준 | 결과 |
|------|------|------|
| skipped dot `aria-label` | WCAG 1.1.1 | ✅ `aria-label="skipped"` |
| skipped dot `title` | 툴팁 보조 | ✅ "이 검증은 데이터 부족으로 스킵됨" |
| pass/fail dot `aria-label` | WCAG 1.1.1 | ✅ `aria-label="passed"/"failed"` 추가 |
| bg-slate-500 (#64748b) on bg-slate-900 (#0f172a) | WCAG 1.4.11 비텍스트 ≥3:1 | ✅ ~3.75:1 충족 |
| 사용자 멘탈 모델 | "skipped ≠ 실패" | ✅ neutral gray (amber/red와 명확 구분) |

> **주의**: 2px 상태 dot는 WCAG 1.4.3(텍스트 4.5:1)이 아닌 1.4.11(비텍스트 UI 컴포넌트 3:1) 기준 적용.  
> bg-slate-500 선택은 task 지시 + 3:1 비텍스트 기준 충족으로 유효.

---

## 변경 파일 목록

| 파일 | 변경 |
|------|------|
| `frontend/src/hooks/useSelectivity.ts` | P14: reduce 블록 제거, BE 값 직접 사용 |
| `frontend/src/types/index.ts` | P05: Candidate 6 optional 필드, instability_index null 허용 |
| `frontend/src/hooks/usePipelineStatus.ts` | P05: mapCandidate 6필드 매핑 |
| `frontend/src/components/ClusterPanel.tsx` | P05: payload 6필드 포함 |
| `frontend/src/components/ValidationPanel.tsx` | P15: skipped dot + aria-label |
| `frontend/src/components/CandidateCompareModal.tsx` | P05 부수: ExtendedCandidate 중복 필드 제거 |

---

## 후속 작업 (BE 팀 필요)

1. **[Critical] BE `selectivity_margin` 파이프라인 연동**: `/api/status` candidates에 `selectivity_margin` 포함
2. **[Medium] BE `instability_index`, `gravy`, `net_charge_ph74`**: pharmacology/admet 결과를 pipeline status candidates에 머지
3. **[New] BE `fwkt_contact`, `chelator_site_available`**: 신규 구현 필요 (현재 코드베이스에 없음)
