# 부분 코드 리뷰 보고서 — binding-pocket-pepadmet 팀

**리뷰어**: reviewer-code  
**날짜**: 2026-05-19  
**범위**: task #1(BE) + task #2(FE) + task #4(infra) 부분 검증 (uvicorn 재기동 전)  
**정정 이력**: 2026-05-19 — 아래 §2.3 M-FE-1(FE extract body) 및 §4.2(infra 테스트 카운트) 2건 false positive 확인, 본문에 [RETRACTED] 표시

---

## 요약

| Task | 코드 상태 | 테스트 상태 | 비고 |
|------|----------|------------|------|
| #1 BE binding_pocket | ✅ PASS | 14/14 ✅ (H-2 BoxSize 수정 반영) | main.py 미커밋, uvicorn 재기동 필요 |
| #2 FE BindingPocketEditor | ✅ PASS | vitest 미실행 | 미커밋 untracked |
| #3 researcher | ✅ PASS (사실관계) | — | 보고서 완결성 HIGH |
| #4 infra pharmacology_guards | ⚠️ **PARTIAL** | **39/39** (62 아님) | `TestEndpointConfidenceExternalTools` 누락 |

**E2E 차단 잔여**: uvicorn 재기동, task #4 테스트 23개 미등록

---

## 1. task #1 BE — PASS + H-2 자체 수정 확인

**이전 리뷰** (`_workspace/44_reviewer-code_binding-pocket-router.md`) 에서 High #2로 지적한
`box_size: Dict[str, Any]` 유효성 누락이 **이미 수정됨**.

```python
# binding_pocket.py:51-57 — BoxSize 모델 신설 확인
class BoxSize(BaseModel):
    size_x: float = Field(..., gt=0)
    size_y: float = Field(..., gt=0)
    size_z: float = Field(..., gt=0)
```

신규 테스트 2개 추가 확인:
- `test_put_box_size_invalid_key_rejected` — 잘못된 키 422 검증
- `test_put_box_size_out_of_range` — 비정상 값 422 검증

**14/14 PASS** (기존 12 + 2 BoxSize validation). **HIGH** 이슈 자체 closure ✅

잔여 권고:
- H-1 race condition: `os.O_EXCL` 백업 — multi-worker 전 수정 대기 (현재 위험 없음)
- M-3 두 번째 override 테스트 TC07-b: 선택사항

---

## 2. task #2 FE — PASS (코드 품질)

### 2.1 컴포넌트 구조
- `BindingPocketEditor.tsx` (802줄): SSTR1~5 탭, 좌표 입력, radius 슬라이더, 잔기 CRUD, PDB 자동 추출
- `useBindingPocket.ts` (94줄): React Query 훅 (useQuery + useMutation × 2)
- `BindingPocketPage.tsx`: 페이지 래퍼
- `App.tsx`: `/binding-pocket` 라우트 등록 + nav 아이콘(MapPin)

### 2.2 긍정 평가
- **Wire frame 주석**: ASCII 와이어프레임이 컴포넌트 상단에 문서화 — 인터페이스 이해 즉시 가능
- **접근성**: `role="tablist"`, `role="tab"`, `aria-selected`, `aria-live="polite"` — WCAG 기준 적절
- **fallback 처리**: BE API 미연결 시 `DEFAULT_CONFIGS` (문헌 기반 좌표) 폴백 — 오프라인 시나리오 처리
- **타입 안전성**: `ReceptorType`, `BindingPocketConfig` 타입 일관

### 2.3 Medium 이슈

**M-FE-1. `useExtractBindingPocket` hook body 없음** ~~[MEDIUM — 신뢰: HIGH]~~  
> **[RETRACTED — 2026-05-19]**: 커밋 `4c868a6` 기준 `apiPostWithBody` 함수 및 `{ residue_ids }` body 전달이 이미 정상 구현되어 있음. 리뷰 시점에 미커밋 상태의 임시 버전을 참조한 것으로 추정. 해당 지적 철회. E2E 보고서 §6.2 참조.
```typescript
// useBindingPocket.ts:80-88 — 실제 구현 (정상)
async function apiPostWithBody<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),    // ✅ residue_ids 정상 전송
  })
  ...
}
```

**M-FE-2. `radius_angstrom` 슬라이더 step 미지정** [LOW — 신뢰: MED]  
입력값 UI 상 step 미지정 시 부동소수점 정밀도 이슈 가능. `step={0.5}` 권장.

### 2.4 vitest 실행 필요
`BindingPocketEditor.test.tsx` 존재하나 현재 세션에서 미실행. uvicorn 재기동 후 빌드 점검 시 함께 실행 예정.

---

## 3. task #3 researcher 보고서 — PASS (사실관계)

**[신뢰: MED — WebFetch 외부 검증 불가, 내부 일관성으로 평가]**

| 항목 | 검증 결과 |
|------|---------|
| pepADMET DOI `10.1021/acs.jcim.5c02518` | 형식 정상, JCIM 2025 일관 |
| pepADMET 교신저자 `jiedong@csu.edu.cn` | CSU 소속 일관 |
| pepADMET 라이선스 GPL-3.0 (GitHub) / CC BY-NC-SA (웹서버) 이중 표기 | 보고서 명시적으로 구분 ✅ |
| PepMSND DOI `10.1039/D5DD00118H` (RSC Digital Discovery) | 형식 정상 |
| PepMSND 정식 URL `/static/service` 정정 (P1 sprint `/pepmsnd` → 오류) | 정정 근거 명확 ✅ |
| D-AA 지원 불가 (`admet_pepadmet`, `halflife_pepmsnd` 모두) | A-02 실험 결과 인용 ✅ |
| SST-14 pepADMET HBN 14.484 min vs 실측 ~3분 (4.83× 과대) | 수치 불일치 명시적 노출 ✅ |
| PEPlife2 경로 제시 (D-AA 지원 언급) | 후속 조사 권장 형태로 적절 |

**잠재 주의사항**:
- `JCIM 5c02518` 출판연도: 보고서는 2025라고 기재, DOI 형식은 2025 일관이나 현재(2026-05-19) 시점 published 여부 외부 확인 불가 — **[MED 신뢰]**
- Zenodo/OSF 채널 미확인 (WebFetch 제한) — 향후 infra가 직접 확인 권장

---

## 4. task #4 infra pharmacology_guards — PARTIAL ⚠️ **CRITICAL GAP**

### 4.1 pharmacology_guards.py 변경 — ✅ 완료

| 항목 | 예상 | 실제 확인 |
|------|------|---------|
| ENDPOINT_CONFIDENCE 총 키 수 | 11 (신규) | **19 total** (기존 8 + 11 신규) ✅ |
| halflife_pepmsnd 등록 | P3 | ✅ line 699 |
| admet_pepadmet 등록 | P1 | ✅ line 809 |
| HEURISTIC_FUNCTION_DISCLAIMERS 신규 | 4 (external_tool.*) | ✅ 4개 확인 (lines 346, 375 외) |
| attach_confidence "warning" 단수키 패치 | 추가 | ✅ line 930-931 |

### 4.2 test_pharmacology_guards.py — ⚠️ **불일치 미해결**

> **[PARTIAL RETRACTION — 2026-05-19]**: "허위" 표현은 철회. 다만 실제 HEAD(`pipeline_local/tests/test_pharmacology_guards.py`, 352줄)에서 `TestEndpointConfidenceExternalTools` 클래스는 현재도 발견되지 않으며, 수집 테스트 수는 39개. 팀-리드 참조본이 uncommitted local 파일 또는 별도 브랜치일 가능성 있음. E2E 보고서 §6.1 및 §3.3 참조.

| 항목 | 팀-리드 보고 | HEAD 기준 실제 |
|------|------------|--------------|
| TestEndpointConfidenceExternalTools | 24 methods 존재 | **현재 미발견** |
| 전체 테스트 수 | **62/62** | **39/39** |

```
# 2026-05-19 재검증
$ conda run -n bio-tools pytest pipeline_local/tests/test_pharmacology_guards.py --collect-only -q
39 tests collected
```

**미결 항목**: infra 측 커밋 상태 확인 필요. HEAD 기준 39/39 PASS는 사실.

### 4.3 누락된 테스트 항목 (infra 전달)

아래 항목에 대한 `TestEndpointConfidenceExternalTools` 클래스 추가 필요:

```python
class TestEndpointConfidenceExternalTools:
    """ENDPOINT_CONFIDENCE 외부 도구 11개 등록 검증."""

    def test_all_11_external_keys_present(self): ...
    def test_halflife_pepmsnd_grade_is_p3(self): ...
    def test_admet_pepadmet_grade_is_p1(self): ...
    def test_halflife_protparam_grade_is_p4(self): ...
    def test_halflife_hlp_grade_is_p4(self): ...
    def test_halflife_plifepred2_grade_is_p4(self): ...
    def test_admet_fab_grade_is_unknown(self): ...
    def test_heuristic_4_external_entries_present(self): ...
    def test_halflife_pepmsnd_heuristic_binary_label(self): ...
    def test_admet_pepadmet_heuristic_ood_warning(self): ...
    def test_attach_confidence_warning_single_key(self): ...
    ...  # 23개 항목 목표
```

---

## 5. 전체 회귀 현황 (부분)

```
pipeline_local/tests/test_pharmacology_guards.py  : 39/39 ✅ (회귀 없음, 목표 62 미달)
backend/tests/test_binding_pocket_router.py        : 14/14 ✅
```

전체 회귀 (`pipeline_local/tests/ -q`) 는 uvicorn 재기동 + task #4 테스트 보완 후 실행 예정.

---

## 6. 즉시 조치 요청

| 담당 | 항목 | 긴급도 |
|------|------|--------|
| **infra** | `test_pharmacology_guards.py` 에 `TestEndpointConfidenceExternalTools` 23 테스트 추가 | **High** (E2E 차단) |
| **fe-binding-ui** | `useExtractBindingPocket` — `residue_ids` body POST 수정 | High (기능 오류) |
| **사용자** | uvicorn 재기동 허가 | High (E2E 차단) |

---

*생성: reviewer-code | 2026-05-19*
