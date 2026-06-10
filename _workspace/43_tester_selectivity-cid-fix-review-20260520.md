# 코드 리뷰 보고서 — selectivity-cid-fix-20260520 (PR #71)

**판정: APPROVE**
**작성일**: 2026-05-20
**리뷰 대상**: `chore/selectivity-cid-fix-20260520` @ `b11d6a0` (PR #71)
**검토 파일**:
- `backend/routers/selectivity.py` (+10줄, `_build_pdb_index` G-1 fix)
- `backend/tests/test_selectivity_pdb_index.py` (신규 7개)

---

## 1. 요약

| 항목 | 상태 |
|------|------|
| Critical 이슈 | 없음 |
| FE format 일치 | ✓ |
| 기존 키 회귀 | 없음 |
| 다른 세션 충돌 | 없음 |
| 테스트 결과 | 162/162 PASS |
| 권고 | 머지 가능 |

---

## 2. 핵심 검증 — 확인 포인트 3개

### 확인 포인트 1: iter_str 추출 → FE 형식 일치 여부

**코드** (selectivity.py:179-195):
```python
iter_parts = iter_dir.name.split("_", 1)
iter_str = iter_parts[1] if len(iter_parts) == 2 else iter_dir.name
pdb_index.setdefault(f"iter{iter_str}_cand{cid_raw}", pdb_path_str)
```

**FE 실제 형식** (runner.py:856, 869):
```python
cid = f"iter{iteration:02d}_cand{int(job['idx']):03d}"   # 라인 856
candidate_id = f"iter{iteration:02d}_cand{idx:03d}"       # 라인 869
```

**디렉토리 생성** (runner.py:707):
```python
iter_dir = flow_dir / f"iter_{iteration:02d}"  # 항상 2자리 zero-pad
```

검증:
- `iter_dir.name = "iter_04"` → `split("_", 1)[1]` = `"04"` → `f"iter04_cand001"` ✓
- FE가 보내는 `iter04_cand001` 와 정확히 일치 [HIGH]

---

### 확인 포인트 2: `iter_dir.name`이 `"iter_4"` (1자리)인 경우 miss 가능성

**결론: 해당 없음.**

runner.py:707이 **항상** `f"iter_{iteration:02d}"` (2자리) 로 디렉토리를 생성함. 운영 환경에서 `iter_4` (1자리) 디렉토리는 존재하지 않음. [HIGH]

---

### 확인 포인트 3: setdefault — 같은 숫자의 여러 iter 처리

```python
for iter_dir in sorted(run_dir.glob("iter_*"), reverse=True):  # iter_04, iter_03, ... 순
    for pdb in iter_dir.glob("cand_*.pdb"):
        pdb_index.setdefault("001", ...)           # 처음 보이는 값 (최신 iter)
        pdb_index.setdefault("iter04_cand001", ...)  # iter04용 독립 키
        pdb_index.setdefault("iter03_cand001", ...)  # iter03용 독립 키
```

- `"001"` 키: 역정렬 기준 가장 최신 iter(iter_04) 파일 → 기존 동작과 일관성 있음 ✓
- `"iter04_cand001"`, `"iter03_cand001"`: 각각 독립 키 → FE의 cid별 정확한 PDB 조회 가능 ✓
- 의도된 동작 확인 [HIGH]

---

## 3. 추가 검토 항목

### 기존 키 회귀
| 키 | 여전히 존재? |
|----|------------|
| `"001"` (숫자 raw) | ✓ |
| `"1"` (lstrip 0) | ✓ |
| `"var001"` | ✓ |

### 신규 키 6종 (per cand_*.pdb)
| 키 형식 | 예시 | 비고 |
|---------|------|------|
| `iter{str}_cand{raw}` | `iter04_cand001` | FE 실제 형식 |
| `cand{raw}` | `cand001` | underscore 없는 변형 |
| `cand_{raw}` | `cand_001` | underscore 있는 변형 |

### 클린코드
- 주석: G-1 fix 일자, 목적, 등록 키 6종 명시 [HIGH]
- magic number 없음 ✓
- `setdefault` 사용: 중복 등록 방지, 최신 우선 보장 ✓

---

## 4. 지적 사항 (블로커 아님)

### [LOW] 커밋 메시지 오표현

커밋 메시지에 "4자리 zero-pad"라고 기재됐으나 실제 형식은 **iter=2자리, cand=3자리**. runner.py:707/856/869 모두 `%02d`/`%03d` 형식. 코드 동작에는 영향 없음. 히스토리 가독성 위해 다음 PR 설명 시 정정 권장.

---

## 5. 테스트 품질

| 테스트 | 검증 대상 | 품질 |
|--------|---------|------|
| G-1 | `iter04_cand004` 형식 hit | ✓ 실제 파일 경로까지 확인 |
| G-2 | 레거시 "001"/"1"/"var001" 회귀 | ✓ |
| G-3 | "cand001"/"cand_001" 변형 | ✓ |
| G-4 | 없는 cid → miss (estimation fallback) | ✓ |
| G-5 | 복수 iter 독립 키 등록 | ✓ cand_001/002/003 각각 다른 파일 경로 검증 |
| G-6 | `cand_007.val1.pdb` stem 점 포함 파싱 | ✓ |
| G-7 | 최근 run만 사용, 오래된 run 무시 | ✓ |

---

## 6. 회귀 테스트 결과

```
pytest backend/tests/ (aiofiles 의존 제외) — 162/162 PASS (1.60s)
  신규 test_selectivity_pdb_index.py: 7/7 PASS
  회귀 test_selectivity_guard.py: 10/10 PASS
  회귀 기타: 145/145 PASS
```

---

## 7. 판정

**APPROVE** — 머지 가능.

FE format 검증 완료 (runner.py:707/856/869 크로스체크). setdefault 동작 의도 확인. 162/162 PASS. 커밋 메시지 표현 오류(LOW, 기능 무관)만 존재.
