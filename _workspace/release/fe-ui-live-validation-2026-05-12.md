# FE UI Live 표시 검증 보고서

- **작성자**: reviewer-uiux (Task #5)
- **작성일**: 2026-05-12
- **대상**: `usePipelineStatus.ts` + `SiloBPage.tsx` 어제(T3) 수정 효과 검증
- **판정**: ✅ **PASS** (소스 기반 + BE API + status 파일 교차 검증)

---

## §1 사전 상태 (BE / FE / status 파일)

| 항목 | 결과 | 세부 |
|------|------|------|
| BE `/api/status` | ✅ 응답 정상 | HTTP 200, JSON 파싱 성공 |
| FE Vite Dev Server `localhost:5173` | ✅ 응답 정상 | HTTP 200 OK, `text/html`, React SPA 번들 확인 |
| `/tmp/ag_pipeline_status.json` | ✅ 존재·갱신 중 | 최초 확인 시 3,967 bytes, 실행 중 자동 갱신 확인 |
| FE SPA 라우트 `/silo-b` | ✅ SPA 응답 | `curl` HTML 응답 확인 (JS 번들 포함) |
| 브라우저 실측 | ⚠️ HEURISTIC-PARTIAL | CLI 환경 상 불가 — 사용자 측 확인 필요 (§6 참조) |

**초기 상태 요약** (최초 점검 시 `2026-05-12T02:03:01Z`):
- `run_id`: `local_20260512_0202_iter01`
- iteration: 1/3
- `step05` (DiffDock) 실행 중, step01·step03b·step04 완료

---

## §2 캡처된 step 시퀀스 (시간순)

### 이터레이션 1

| 시각(UTC) | `updated_at` | RUNNING | COMPLETED |
|-----------|--------------|---------|-----------|
| 02:03:19 | 02:03:01 | step05 | step01, step03b, step04 |
| 02:03:28 | 02:03:01 | step05 | step01, step03b, step04 |
| 02:03:42 | 02:03:01 | step05 | step01, step03b, step04 |
| 02:04:08 | 02:03:01 | step05 | step01, step03b, step04 |
| 02:04:28 | 02:03:01 | step05 | step01, step03b, step04 |
| 02:05:00 | 02:03:01 | step05 | step01, step03b, step04 |
| **02:06:19** | **02:06:12** | **step06** | **step01, step03b, step04, step05** |
| 02:06:55 | 02:06:12 | step06 | step01, step03b, step04, step05 |
| 02:07:05 | 02:06:12 | step06 | step01, step03b, step04, step05 |

**이터레이션 1 실행 시간**:

| step | duration |
|------|----------|
| step01 (Receptor Prep) | 0.0s |
| step03b (BLOSUM62 Mutation) | 0.0s |
| step04 (ESMFold QC) | 30.9s |
| step05 (DiffDock) | 190.7s |
| step06 (PyRosetta FlexPepDock) | 99.0s |
| step07 (Analysis/Reporter) | 5.0s |

> **step05 전환 확인**: poll 5 (02:06:07) → poll 6 (02:06:19) 구간에서 `step05 completed`, `step06 running` 전환 캡처. `updated_at` = 02:06:12.

### 이터레이션 2 진입 확인

| 시각(UTC) | `updated_at` | iteration | RUNNING | note |
|-----------|--------------|-----------|---------|------|
| 02:07:56 | 02:07:56 | **2/3** | step04 | 이터레이션 2 진입 확인 |

---

## §3 SILO_B_STEPS 매핑

`SiloBPage.tsx` Line 35-38에 정의된 화이트리스트:
```typescript
const SILO_B_STEPS = new Set([
  'step01', 'step03b', 'step03b_qc', 'silo_b',
  'step04', 'step05', 'step05b', 'step06', 'step07', 'step08', 'step09',
])
```

| step_id | SILO_B_STEPS | 이터레이션1 실제 상태 | 어제 추가 | 판정 |
|---------|-------------|---------------------|----------|------|
| `step01` | ✅ | completed (0.0s) | 기존 | ✅ PASS |
| `step02` | ❌ (Silo A 전용) | pending (필터됨) | N/A | ✅ 정상 제외 |
| `step03` | ❌ (Silo A 전용) | pending (필터됨) | N/A | ✅ 정상 제외 |
| `step03b` | ✅ | completed (0.0s) | 기존 | ✅ PASS |
| `step03b_qc` | ✅ | pending (미활성) | **신규** | ✅ 화이트리스트 포함 확인 |
| `step04` | ✅ | completed (30.9s) | **신규** | ✅ **ACTIVE — 실제 실행 확인** |
| `step05` | ✅ | completed (190.7s) | **신규** | ✅ **ACTIVE — 실제 실행 확인** |
| `step05b` | ✅ | pending (미활성) | **신규** | ✅ 화이트리스트 포함 확인 |
| `step06` | ✅ | completed (99.0s) | 기존 | ✅ PASS |
| `step07` | ✅ | completed (5.0s) | 기존 | ✅ PASS |
| `step08` | ✅ | pending (미활성) | **신규** | ✅ 화이트리스트 포함 확인 |
| `step09` | ✅ | pending (미활성) | **신규** | ✅ 화이트리스트 포함 확인 |

**어제 추가한 6개 step 중**:
- 실제 파이프라인에서 활성화 확인: `step04` ✅, `step05` ✅ (2개)
- 화이트리스트 등록은 확인되나 아직 미활성: `step03b_qc`, `step05b`, `step08`, `step09` (4개 — 파이프라인 설계상 pending 유지)

FE 필터 로직 (`SiloBPage.tsx:86`):
```typescript
const filteredLiveSteps = isLive ? live.steps.filter(s => SILO_B_STEPS.has(s.id)) : PIPELINE_STEPS
```
→ step02, step03 는 BE 응답에 포함되어 있으나 **FE에서 정상 필터 아웃**. 화이트리스트 필터 **정상 작동**.

---

## §4 status 갱신 빈도

| 구간 | `updated_at` 변화 | 실제 사유 |
|------|-------------------|---------|
| 02:03:01 ~ 02:06:12 | **약 3분 13초 고정** | step05 (DiffDock) 실행 중 — step 전환 없음 |
| 02:06:12 → 02:07:56 | 1분 44초 후 갱신 | step05→step06→step07 완료 + iter2 진입 |

> **분석**: BE는 step 전환 시점에만 `/tmp/ag_pipeline_status.json` 을 갱신. FE는 2,000ms마다 `/api/status`를 폴링하므로 **step 전환 후 최대 2초 이내** FE 반영 가능.
> 
> `updated_at` 고정이 FE 이상을 의미하지 않음 — 파이프라인이 동일 step에서 실행 중일 때 정상 동작.

---

## §5 어제 fix 효과 판정

### usePipelineStatus.ts — AbortController + mountedRef

| 수정 항목 | 소스 확인 | 효과 판정 |
|----------|---------|---------|
| `mountedRef = useRef(false)` | ✅ Line 246 | React StrictMode double-mount 방지 코드 존재 |
| `if (mountedRef.current) return` | ✅ Line 328-329 | 두 번째 마운트에서 interval 중복 생성 차단 |
| `mountedRef.current = false` (cleanup) | ✅ Line 346 | 클린업 후 재마운트 허용 |
| `fetchLiveStatus(signal?: AbortSignal)` | ✅ Line 258 | AbortSignal 파라미터 정의 |
| `AbortController` 생성 + cleanup | ✅ Lines 331-349 | 언마운트 시 진행 중 fetch 취소 |
| 폴링 중 archive 뷰 보호 | ✅ Lines 338-340 | `viewingArchiveRef` 확인 후 live fetch |

**판정**: ✅ **작동** (소스 기반 — 코드가 설계 의도대로 구현됨)

**한계**: React StrictMode 실 환경(브라우저)에서 double-mount 발생 여부, `fetch` abort 시 실제 네트워크 취소 동작은 브라우저 실측 없이 완전 검증 불가.

### SiloBPage.tsx — SILO_B_STEPS 화이트리스트 확장

| 수정 항목 | 소스 확인 | 실제 활성화 | 효과 판정 |
|----------|---------|-----------|---------|
| `step03b_qc` 추가 | ✅ Line 37 | 미활성 (pending) | ✅ 등록 확인 |
| `step04` 추가 | ✅ Line 37 | **completed (30.9s)** | ✅ **실 활성화 확인** |
| `step05` 추가 | ✅ Line 37 | **completed (190.7s)** | ✅ **실 활성화 확인** |
| `step05b` 추가 | ✅ Line 37 | 미활성 (pending) | ✅ 등록 확인 |
| `step08` 추가 | ✅ Line 37 | 미활성 (pending) | ✅ 등록 확인 |
| `step09` 추가 | ✅ Line 37 | 미활성 (pending) | ✅ 등록 확인 |

**판정**: ✅ **작동** — step04, step05 실제 실행 확인 + Silo A 전용 step02/step03 정상 필터 아웃

---

## §6 사용자 측 확인 권장 사항 (HEURISTIC-PARTIAL)

본 검증은 **BE API + 파일 기반 소스 검증**으로 수행. 다음 항목은 **실 브라우저에서 별도 확인 필요**:

| 검증 항목 | 이유 |
|----------|------|
| React StrictMode double-mount 실제 발생 여부 | 브라우저 개발 모드에서만 발생 |
| FE UI step 카드 실시간 갱신 (step05→step06 전환 시각적 반영) | 2초 폴링 반영 확인 필요 |
| step02/step03 실제로 FE UI에서 미표시 여부 | 필터 코드는 확인했으나 렌더 결과 미확인 |
| AbortController fetch 취소 네트워크 동작 | 브라우저 DevTools Network 탭 확인 필요 |
| 이터레이션 전환 시 UI 카운터 (`iter 1/3` → `iter 2/3`) 갱신 | 이터레이션 2 진입 확인됨 — UI 반영 브라우저 확인 필요 |

**권장 절차** (사용자 직접 확인):
1. `http://localhost:5173/silo-b` 접속 → 브라우저 개발자 도구(F12) 열기
2. Network 탭 → `/api/status` 요청 2초 간격 확인
3. Console 탭 → React StrictMode 경고 없는지 확인
4. UI에서 step 카드가 `step02`, `step03` 없이 표시되는지 확인
5. step 전환 시(예: step04→step05) 카드 색상 전환 확인

---

## 부록: 소스 검증 요약

### usePipelineStatus.ts 핵심 코드 확인

```typescript
// Line 246 — mountedRef 선언
const mountedRef = useRef(false)

// Line 258 — AbortSignal 파라미터
const fetchLiveStatus = useCallback(async (signal?: AbortSignal) => { ... }, [])

// Lines 325-351 — useEffect 생명주기
useEffect(() => {
  if (mountedRef.current) return  // double-mount 방지
  mountedRef.current = true
  const controller = new AbortController()
  abortRef.current = controller
  fetchLiveStatus(controller.signal)
  // ... interval 설정 ...
  return () => {
    mountedRef.current = false
    clearInterval(intervalRef.current)
    controller.abort()  // 언마운트 시 fetch 취소
  }
}, [...])
```

### SiloBPage.tsx SILO_B_STEPS 정의 확인

```typescript
// Lines 35-38 — 화이트리스트 (어제 추가분 포함)
const SILO_B_STEPS = new Set([
  'step01', 'step03b', 'step03b_qc', 'silo_b',
  'step04', 'step05', 'step05b', 'step06', 'step07', 'step08', 'step09',
])
// Line 86 — 필터 적용
const filteredLiveSteps = isLive ? live.steps.filter(s => SILO_B_STEPS.has(s.id)) : PIPELINE_STEPS
```

---

*작성: reviewer-uiux | Task #5 | 2026-05-12 02:08 UTC*
