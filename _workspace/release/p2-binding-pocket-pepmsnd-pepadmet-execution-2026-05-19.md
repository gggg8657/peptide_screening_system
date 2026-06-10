# P2 실행 보고서: ENDPOINT_CONFIDENCE 복구 + 외부 도구 통합
**날짜**: 2026-05-19  
**담당**: engineer-infra  
**Task**: #4 infra + reviewer — PepMSND + pepADMET 새 접근 + ENDPOINT_CONFIDENCE 통합  

---

## 실행 요약

| Step | 상태 | 비고 |
|------|------|------|
| Step 1 — researcher 보고서 수신 | ⏳ 대기 | `p2-pepmsnd-pepadmet-retry-2026-05-19.md` 미도착 (task #3 in_progress) |
| Step 2 — 새 접근 환경 구축 | ⏳ researcher 차단 | 새 채널 확인 후 진행 |
| Step 3 — wrapper 갱신 | ⏳ researcher 차단 | predict_halflife_pepmsnd.py / predict_admet_pepadmet.py |
| Step 4 — ENDPOINT_CONFIDENCE 재등록 | ✅ 완료 | 11 도구 (7 halflife + 4 admet) |
| Step 5 — HEURISTIC disclaimers 4항목 | ✅ 완료 | external_tool.* 4개 |
| Step 6 — TestEndpointConfidenceExternalTools | ✅ 완료 | 23 테스트 신규 |
| Step 7 — attach_confidence warning 단수키 호환 | ✅ 완료 | |
| Step 8 — 회귀 검증 | ✅ 62/62 PASS | 39 → 62 (기존 39개 회귀 유지) |

**현재 차단**: researcher task #3 미완료 → Step 2, 3, 5(벤치마크) 대기

---

## 1. ENDPOINT_CONFIDENCE 재등록 (P1 손실 복구)

### 1.1 혈청 반감기 도구 (7개)

| 키 | 등급 | 도구 | 핵심 근거 | 강등 사유 |
|----|------|------|-----------|-----------|
| `halflife_pepmsnd` | **P3** | PepMSND | Wang 2025 DOI:10.1039/D5DD00118H | P1→P3: 이진 분류, 연속 t½ 없음 |
| `halflife_plifepred` | P2 | PlifePred | Mathur 2018 PLOS ONE, R²=0.552 | — |
| `halflife_plifepred2` | **P4** | PlifePred2 | §V-infra-01 단위 미명시 | 절대값 사용 금지 |
| `halflife_ml_peptide` | P3 | ML_Peptide | peer-review 미확보 | — |
| `halflife_protparam` | **P4** | ProtParam | Varshavsky 1996; N-end rule = 세포내 | P3→P4: 혈청 메커니즘 완전 불일치 |
| `halflife_hlp` | P4 | HLP | Sharma 2014; GI 전용 | 혈청 절대 금지 + 1.6초 오적용 |
| `halflife_peptiderranker` | P4 | PeptideRanker | 생물활성 ranking 전용 | — |

### 1.2 ADMET 도구 (4개)

| 키 | 등급 | 도구 | 핵심 근거 | 비고 |
|----|------|------|-----------|------|
| `admet_pepadmet` | **P1** | pepADMET | Wang 2026 JCIM, R²=0.84-0.90 | HTTP 403 = infra 문제 (등급 ≠ 인프라 상태) |
| `admet_modlamp` | P3 | modlamp | 물리화학 디스크립터 | ADMET 예측 아님 |
| `admet_ai` | P2 | ADMET-AI | 소분자 중심, 펩타이드 감점 | — |
| `admet_fab` | **UNKNOWN** | Fab-ADMET | 원출처 미식별 | 5월 회의 Fab-ADMET=pepADMET 정정 |

---

## 2. HEURISTIC_FUNCTION_DISCLAIMERS 4항목 신규 등록

| qualname | surface_unit | 핵심 한계 |
|----------|-------------|-----------|
| `external_tool.halflife_pepmsnd` | binary label | 연속 t½ 오용 방지; D-AA 미지원 |
| `external_tool.halflife_hlp` | time (GI env) | 혈청 절대 금지; 1.6초 오적용 traceback |
| `external_tool.admet_pepadmet` | 29 ADMET endpoints | DOTA OOD; D-AA 미확인; web-only |
| `external_tool.halflife_plifepred2` | probability score (단위 미명시) | §V-infra-01; 절대값 금지 |

모든 항목 `confidence_grade = "HEURISTIC"` ✅

---

## 3. attach_confidence() 패치

```python
# 기존 (P1 손실 전)
warnings: List[str] = list(info.get("warnings", []))

# 복구 후 — "warning" 단수 키 호환
warnings: List[str] = list(info.get("warnings", []))
if "warning" in info and info["warning"] not in warnings:
    warnings.append(info["warning"])
```

- `halflife_protparam`, `halflife_hlp`, `halflife_plifepred2`, `admet_fab` 등
  단수 `"warning"` 키 사용 엔트리가 attach_confidence에서 누락 없이 포함됨

---

## 4. 테스트 결과

| 항목 | 이전 | 이후 |
|------|------|------|
| 기존 회귀 | 39/39 PASS | 39/39 PASS ✅ |
| TestEndpointConfidenceExternalTools (신규) | — | **23/23 PASS** |
| **합계** | 39 | **62/62 PASS** |

```
62 passed in 0.20s
```

---

## 5. 차단 항목 (researcher #3 의존)

| 항목 | 차단 원인 |
|------|----------|
| Step 2: 새 접근 환경 (새 conda env / Docker / HF) | researcher가 새 채널 식별해야 함 |
| Step 3: wrapper 갱신 (새 접근 방식 통합) | 위 동일 |
| SST14/Octreotide/Lanreotide 벤치마크 | 도구 접근 가능해야 실행 가능 |

researcher 보고서 수신 즉시 Step 2-3 착수 가능.

---

## 6. 변경 파일 요약

| 파일 | 변경 내용 |
|------|----------|
| `pipeline_local/scripts/pharmacology_guards.py` | ENDPOINT_CONFIDENCE: 11 외부 도구 추가; HEURISTIC_FUNCTION_DISCLAIMERS: 4개 추가; attach_confidence: "warning" 단수키 호환 패치 |
| `pipeline_local/tests/test_pharmacology_guards.py` | ENDPOINT_CONFIDENCE, attach_confidence import 추가; TestEndpointConfidenceExternalTools 23 테스트 신규 |

---

## 7. reviewer-code 인계 항목

- `pharmacology_guards.py` 변경: ENDPOINT_CONFIDENCE 11 + HEURISTIC 4 + attach_confidence 패치
- 테스트 62/62 PASS 확인 (기존 39 회귀 무)
- Step 2-3 (researcher 의존) 완료 후 추가 회귀 필요
- 인계 가능 시점: **즉시** (Step 2-3은 별도로 인계)
