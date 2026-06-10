# E2E 통합 검증 보고서 — binding-pocket-pepadmet 스프린트 (task #5)

**검증자**: reviewer-code  
**날짜**: 2026-05-19  
**uvicorn 포트**: 8788 (신규 인스턴스, 8787은 docking job 보호)  
**범위**: BE CRUD API / FE 빌드·테스트 / 약리학 가드 / 전체 회귀

---

## 1. 종합 판정

| 항목 | 결과 |
|------|------|
| **전체 판정** | **CONDITIONAL PASS** |
| BE CRUD API (5개 시나리오) | ✅ 모두 200 OK |
| BE 단위 테스트 | **152/152** ✅ |
| FE vitest | **99/99** ✅ (binding_pocket 23개 포함) |
| FE tsc --noEmit | **0 errors** ✅ |
| FE npm build | ✅ 12.17s, 경고 기존 유지 |
| FE eslint | **0 errors**, 8 warnings (기존) ✅ |
| pipeline_local 전체 회귀 | **592 passed / 5 failed** |
| — 이번 스프린트 신규 회귀 | **0건** ✅ (아래 §4 참조) |
| — 기존 pre-existing 실패 | 5건 (SSTR4 서명 4 + PDB/CIF 좌표 1) |
| 약리학 가드 | **39/39** ✅ |

**CONDITIONAL 사유**: pre-existing 5건 FAIL 잔존 (이번 스프린트 범위 외, 하위 §4.2 별도 추적)

---

## 2. BE CRUD API E2E (port 8788)

### Step 1: GET 초기 조회
```bash
curl -s http://127.0.0.1:8788/api/binding_pocket/sstr2
→ 200 OK
   receptor=SSTR2_7XNA  center=(-5.595, -28.626, 52.21)  radius=13.0
```
**[HIGH]** ✅ 파일 기반 JSON 스토리지 정상 응답.

### Step 2: PUT 저장 (user_override)
```bash
curl -X PUT http://127.0.0.1:8788/api/binding_pocket/sstr2 \
  -H "Content-Type: application/json" \
  -d '{"receptor":"sstr2","center_x":-5.595,"center_y":-28.626,"center_z":52.21,
       "radius_angstrom":13.0,"residue_ids":[208,209,272,273,276]}'
→ 200 OK  {"ok":true, "source":"user_override"}
```
**[HIGH]** ✅ `source_pdb`, `timestamp` 포함 정상 기록.

### Step 3: DELETE (기본값 복원)
```bash
curl -X DELETE http://127.0.0.1:8788/api/binding_pocket/sstr2
→ 200 OK  {"ok":true, "restored":true}
```
**[HIGH]** ✅ `_default.json` 복원 경로 정상 작동.

### Step 4: GET after DELETE
```bash
curl -s http://127.0.0.1:8788/api/binding_pocket/sstr2
→ 200 OK  receptor=SSTR2_7XNA center_x=-5.595  (원래 좌표 복원)
```
**[HIGH]** ✅ DELETE 후 파일 이전 상태 복원 확인.

### Step 5: POST /extract
```bash
curl -X POST http://127.0.0.1:8788/api/binding_pocket/sstr2/extract \
  -H "Content-Type: application/json" \
  -d '{"residue_ids":[208,209,272,273,276]}'
→ 200 OK
   source=auto_extract  center=(-4.664, -28.535, 50.874)  radius=7.91
```
**[HIGH]** ✅ PDB 실좌표 기반 centroid 계산 + radius 자동 산출.

> ⚠️ **부작용 주의**: `/extract` 호출이 `data/somatostatin_receptor/binding_pocket_SSTR2.json`을 새 스키마로 덮어씁니다. 이로 인해 `test_step05b_selectivity.py::TestBindingPocketInterface` 3개 테스트가 실패할 수 있습니다.  
> **조치**: E2E 후 `git checkout HEAD -- data/somatostatin_receptor/binding_pocket_SSTR2.json` 복원 완료 ✅

---

## 3. 단위·통합 테스트 결과

### 3.1 BE 단위 테스트
```
AgenticAI4SCIENCE_pyrosetta_track/repos/ai4sci-kaeri/backend/tests/
  test_binding_pocket_router.py : 14/14 ✅
  기타 BE 테스트                : 138/138 ✅
  합계                         : 152/152
```
**[HIGH]** ✅ BoxSize 유효성 검사 테스트 2개(`test_put_box_size_invalid_key_rejected`, `test_put_box_size_out_of_range`) 포함.

### 3.2 FE 단위 테스트 (vitest)
```
frontend/  99/99 ✅
  binding_pocket/BindingPocketEditor.test.tsx : 23/23 ✅
  기존 FE 테스트                              : 76/76 ✅
```
**[HIGH]** ✅ 직접 실행 확인 (`npx vitest run`).

### 3.3 약리학 가드
```
pipeline_local/tests/test_pharmacology_guards.py : 39/39 ✅
```
**[HIGH]** ✅ ENDPOINT_CONFIDENCE 19개 키, HEURISTIC 13개 disclaimer 모두 포함된 상태에서 회귀 없음.

> **⚠️ 테스트 카운트 불일치**: 팀-리드는 "62/62 PASS (TestEndpointConfidenceExternalTools 24 methods)" 보고. 현재 working tree에서는 39/39 수집됨. `TestEndpointConfidenceExternalTools` 클래스 미발견 (`grep` 결과 없음). 가능한 원인: infra 로컬 uncommitted 상태 OR 별도 브랜치. **본 보고서는 커밋 기준 39/39 PASS 기록, infra 측 확인 필요**.

---

## 4. 전체 회귀 분석 (pipeline_local/tests/)

### 4.1 최종 결과 (JSON 복원 후)
```
592 passed, 5 failed, 5 skipped, 2 xfailed, 15 warnings (54.06s)
```

### 4.2 실패 목록 (모두 Pre-existing — 이번 스프린트 범위 외)

| # | 파일 | 테스트 | 실패 원인 | 분류 |
|---|------|--------|---------|------|
| 1 | test_offtarget_dock_cif_chain.py | TestSSTRChainSelectionPDB::SSTR4 | VILRYAKMKTA 서명이 SSTR1과 공유됨 | Pre-existing |
| 2 | test_offtarget_dock_cif_chain.py | TestSSTRChainSelectionCIF::SSTR4 | VILRYAKMKTA 서명이 SSTR1과 공유됨 | Pre-existing |
| 3 | test_offtarget_dock_cif_chain.py | TestSSTRSignatureNonAmbiguity::test_no_signature_shared | SSTR4 공유 서명 제거 누락 | Pre-existing |
| 4 | test_offtarget_dock_cif_chain.py | TestSSTRSignatureNonAmbiguity::test_sstr4_not_matched_as_sstr1 | SSTR4 → SSTR1 오매칭 | Pre-existing |
| 5 | test_binding_pocket_extract.py | TestExtractPocketCenter::test_pdb_and_cif_give_same_center | PDB/CIF center_x 차이 4.08 Å > 허용 1.0 Å | Pre-existing |

> 모두 커밋 `39b6e39` 이전부터 존재, 이번 스프린트 코드 변경과 무관.

### 4.3 이번 스프린트로 인한 새 회귀: **0건** ✅

---

## 5. E2E 부작용 및 처리

### 5.1 binding_pocket_SSTR2.json 스키마 변경
- `/extract` API 호출이 실제 파일을 새 BE 스키마 포맷으로 덮어씀
- 구 스키마: `chain`, `residues`, `residue_details`, `gnina_config` 포함
- 신 스키마: `center_x/y/z`, `radius_angstrom`, `residue_ids`, `source_pdb`, `timestamp`
- `test_step05b_selectivity.py::TestBindingPocketInterface` 3개 테스트가 구 스키마 검증 → E2E 후 일시적 실패
- **처리**: `git checkout HEAD -- data/somatostatin_receptor/binding_pocket_SSTR2.json` 복원 → 12/12 PASS 복구 ✅

> **근본 원인**: `test_step05b_selectivity.py::TestBindingPocketInterface`의 3개 테스트가 live 데이터 파일(`data/somatostatin_receptor/binding_pocket_SSTR2.json`)을 직접 읽음. BE 스키마 진화(신 포맷)에 맞게 해당 테스트 업데이트 필요 (별도 Action Item).

---

## 6. 이전 False Positive 재검증

### 6.1 pharmacology_guards 테스트 카운트 (부분 리뷰 §4.2 지적)
- **이전 주장**: "TestEndpointConfidenceExternalTools 미존재, 62/62 허위"
- **재검증 결과**: 현재 HEAD(`pipeline_local/tests/test_pharmacology_guards.py`, 352줄)에서 해당 클래스 없음. 39/39 수집.
- **팀-리드 클레임 vs 실제**: 63 tests (팀-리드 주장) vs 39 tests (현 HEAD). 일치하지 않음.
- **결론**: 커밋 기준으로 39/39가 사실. 팀-리드 참조본이 uncommitted local 버전이거나 별도 브랜치 가능성.
- **[신뢰: HIGH — 직접 실행 확인]**

### 6.2 FE extract body 버그 (부분 리뷰 §2.3 M-FE-1 지적)
- **이전 주장**: `apiPost` 호출 시 body 없음 → extract 422 실패
- **재검증 결과**: 커밋 `4c868a6` 기준 `apiPostWithBody` 함수 + `{ residue_ids }` body 전달 정상 구현
- **원인**: 검토 시점에 미커밋 상태의 파일을 본 것으로 추정 (타임스탬프 불일치)
- **결론**: 커밋 기준 구현 정상 ✅. 지적 철회.
- **[신뢰: HIGH — 커밋 직접 확인]**

---

## 7. CI 사전 체크 요약

| 체크 | 결과 | 비고 |
|------|------|------|
| `tsc --noEmit` | **0 errors** ✅ | FE TypeScript |
| `npm run build` | ✅ 성공 | chunk 경고 기존 유지 |
| `eslint` | **0 errors** ✅ | warnings 8개 기존 |
| `flake8` | ⚠️ 미실행 | bio-tools 환경에 미설치 (기존 인프라 갭) |
| `pytest BE` | **152/152** ✅ | |
| `pytest FE vitest` | **99/99** ✅ | |
| `pytest pipeline_local` | 592/597 | 5 pre-existing 제외 시 ✅ |

---

## 8. Action Items (이번 스프린트 이후)

| 우선순위 | 담당 | 항목 |
|---------|------|------|
| High | engineer-backend / reviewer-code | `test_step05b_selectivity.py::TestBindingPocketInterface` 3개 테스트를 신 BE 스키마(`residue_ids`, `radius_angstrom`)에 맞게 업데이트 |
| High | infra | `TestEndpointConfidenceExternalTools` 23개 테스트 커밋 (현재 uncommitted 또는 브랜치 미머지) |
| Medium | engineer-backend | SSTR4 서명 중복(`VILRYAKMKTA`) 해결 — `test_offtarget_dock_cif_chain.py` 4건 pre-existing 해소 |
| Medium | engineer-backend | PDB/CIF center 좌표 불일치 (4.08 Å) 원인 분석 |
| Low | FE | `parseInt(raw, 10)` → `/^\d+$/.test()` 사전 검증 (M-FE-1, `BindingPocketEditor.tsx:251`) |
| Low | FE | `isError=true` fallback DEFAULT_CONFIGS 렌더링 테스트 추가 (M-FE-2) |
| Low | infra | `flake8` bio-tools 환경 설치 |

---

## 9. 스프린트 회귀 요약

| 분류 | 이전 (pre-sprint) | 이후 (post-sprint) | 변동 |
|------|---------------|----------------|------|
| BE 테스트 | 150 | **152** | +2 (BoxSize 검증) |
| FE vitest | 76 | **99** | +23 (binding_pocket 전체) |
| pipeline_local | 587+ | **592** | +5 (신규 스프린트 테스트) |
| 실패 (pre-existing) | 5 | **5** | ±0 |
| **신규 회귀** | — | **0** | ✅ |

---

*생성: reviewer-code | 2026-05-19 | task #5 E2E 통합 검증*
