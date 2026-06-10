# P1-4 — HEURISTIC API 자동 주입 구현 보고서

> **작성**: reviewer-pharma · 2026-05-13  
> **범위**: backend API 응답 confidence_grade 자동 주입 + pharmacology_guards 문서 갱신  
> **회귀 테스트**: ✅ **39/39 PASS** (변경 후 재실행 확인)

---

## 1. 구현 요약

### 1.1 변경 파일 목록

| 파일 | 변경 내용 | 라인 수 (변경) |
|------|----------|-------------|
| `pipeline_local/scripts/pharmacology_guards.py` | §5 API 신뢰도 메타데이터 추가 + docstring 갱신 | +107 |
| `pipeline_local/backend/routers/admet.py` | attach_confidence 적용 (3 엔드포인트) | +31 |
| `pipeline_local/backend/routers/validation.py` | attach_confidence 적용 (3 엔드포인트) | +25 |
| `pipeline_local/backend/routers/selectivity.py` | attach_confidence 적용 (2 엔드포인트) + 모듈 docstring | +22 |
| `CLAUDE.md` | 33→39 회귀 테스트 수 갱신 (M5-P6) | +1 |

---

## 2. pharmacology_guards.py 신규 섹션 5 구조

### 2.1 ENDPOINT_CONFIDENCE (등록 8개 엔드포인트)

| 엔드포인트 | grade | 핵심 warnings |
|-----------|-------|-------------|
| `/admet/{sequence}` | **C** | DLscore 포화 (G-05/M5-P3), 소분자 모델 적합성 미검증 |
| `/admet/batch` | **C** | 위와 동일 |
| `/pharmacology/batch` | **B** | Biopython ProtParam in-silico, D-AA Instability 한계 (M5-P1) |
| `/selectivity/results/{job_id}` | **C** | selectivity_margin ≠ Ki (M5-P4), iPTM ≠ Ki proxy (ρ≈-0.3) |
| `/selectivity/status/{job_id}` | **C** | selectivity_margin 해석 주의 (M5-P4) |
| `/validate/selected` | **B** | ddG PyRosetta ref2015 ideal coord 한계 (VR-cycle-08) |
| `/validation/run` | **B** | in-silico 추정, 임상 결과 대체 불가 |
| `/validate/unified` | **B** | 복합 검증, 임상 결과 대체 불가 |

미등록 경로 → 기본값 `grade="B"`, `warning="⚠️ in-silico 추정값"` 적용.

### 2.2 attach_confidence() API

```python
from pipeline_local.scripts.pharmacology_guards import attach_confidence

# 단순 사용
result = attach_confidence(raw_dict, "/admet/{sequence}")
# → result["confidence_grade"] == "C"
# → result["confidence_warnings"] == ["⚠️⚠️ DLscore 포화...", ...]
# → result["confidence_metadata"] == {"grade": "C", "affected_metrics": [...], ...}

# HEURISTIC 함수 사용 추가 경고
result = attach_confidence(raw_dict, "/pharmacology/batch",
    heuristic_functions_used=["pipeline_local.steps.step08_stability.predict_half_life"])
# → confidence_warnings에 HEURISTIC 경고 자동 추가
```

**설계 원칙**:
- **원본 불변**: `dict(response)` 복사 후 필드 주입 → 원본 dict 변경 없음 ✅
- **테이블 기반**: 등급·경고 모두 `ENDPOINT_CONFIDENCE`에서 관리 → 한 곳에서 제어 ✅
- **확장 용이**: 새 엔드포인트 추가 시 `ENDPOINT_CONFIDENCE`에 1 항목 추가만 필요 ✅

---

## 3. 응답 형식 변경

### 3.1 이전 vs 이후 비교

**이전 (GET /admet/AGCKNFFWKTFTSC)**:
```json
{
  "sequence": "AGCKNFFWKTFTSC",
  "dlscore": 100,
  "nephrotox_risk": "High",
  "bbb_risk": "Low"
}
```

**이후 (P1-4 적용)**:
```json
{
  "sequence": "AGCKNFFWKTFTSC",
  "dlscore": 100,
  "nephrotox_risk": "High",
  "bbb_risk": "Low",
  "confidence_grade": "C",
  "confidence_warnings": [
    "⚠️⚠️ compute_admet DLscore 100/100 포화 — 변별력 부족 (§검증 필요 G-05/M5-P3)",
    "⚠️ 소분자 기반 ADMET 모델 — 펩타이드 적합성 미검증"
  ],
  "confidence_metadata": {
    "grade": "C",
    "affected_metrics": ["dlscore", "nephrotox_risk", "bbb_risk", "herg_risk", "cyp450"],
    "source": "M5_reviewer-pharma_module-spec-2026-05-13.md §1.11",
    "heuristic_functions": [],
    "guard_version": "pharmacology_guards.py P1-4 (2026-05-13)"
  }
}
```

### 3.2 /selectivity/results 이후

```json
{
  "job_id": "sel_...",
  "candidates": [...],
  "summary": {...},
  "confidence_grade": "C",
  "confidence_warnings": [
    "⚠️⚠️ selectivity_margin은 dock_score 차이 기반 — 실측 Ki selectivity 상관 미검증 (M5-P4)",
    "⚠️⚠️ Boltz iPTM ≠ Ki proxy (Spearman ρ≈-0.3, 순위 일치 0/5 실증) — 정량 선택성은 FEP/Ki assay 필요"
  ],
  "confidence_metadata": {
    "grade": "C",
    "affected_metrics": ["selectivity_margin", "wsm", "msm", "tier", "passed", ...],
    ...
  }
}
```

---

## 4. 테스트 결과

### 4.1 기존 회귀 테스트

```
pytest pipeline_local/tests/test_pharmacology_guards.py -v
============================== 39 passed in 0.13s ==============================
```

### 4.2 신규 attach_confidence 검증 (python -c 직접 실행)

| 테스트 | 결과 |
|--------|------|
| `/pharmacology/batch` → grade B | ✅ |
| `/admet/{sequence}` → grade C | ✅ |
| `/selectivity/results/{job_id}` → grade C | ✅ |
| HEURISTIC 함수 경고 자동 생성 | ✅ |
| 미등록 경로 기본 grade B | ✅ |
| 원본 dict 불변 확인 | ✅ |

---

## 5. UI 노출 권장 (미구현, 후속 작업)

현재 구현은 **API 응답 레벨** confidence 주입까지 완료. 프론트엔드 표시는 별도 작업 필요.

| 등급 | 권장 UI 표시 | 색상 |
|------|------------|------|
| **A** | ✅ 실측 데이터 | 녹색 |
| **B** | ⚠️ in-silico 추정값 | 노랑 |
| **C** | ⚠️⚠️ 검증 부족 — 절대값 해석 주의 | 주황 |
| **HEURISTIC** | 🔴 HEURISTIC — ranking 전용 (임상 값 아님) | 빨강 |

**Action Item**: `frontend/src/components/` 에 `ConfidenceBadge` 컴포넌트 추가하여 `confidence_grade` 필드 기반 배지 표시. (P1-5 UI 팀 작업과 연계 권장)

---

## 6. CLAUDE.md 갱신 (M5-P6)

```diff
- | 2026-05-11 | Stage 5 | ... + 33 회귀 테스트 | ...
+ | 2026-05-11 | Stage 5 | ... + 33 회귀 테스트 (2026-05-13 현재 39개) | ...
```

---

## 7. 미완료 항목 (후속 작업)

| 항목 | 이유 | 담당 |
|------|------|------|
| M5-P1: D-AA Instability pepADMET | 도구 도입 필요 | researcher |
| M5-P3: DLscore 포화 규칙 재정의 | backend.admet.py 수정 필요 | engineer-backend |
| UI ConfidenceBadge 컴포넌트 | 프론트엔드 | reviewer-uiux / P1-5 |
| `/api/stability/*` 신규 엔드포인트 | 현재 stability 전용 라우터 없음 | engineer-backend |

---

*Reviewer-pharma · P1-4 완료 · 39/39 guards PASS · 2026-05-13*
