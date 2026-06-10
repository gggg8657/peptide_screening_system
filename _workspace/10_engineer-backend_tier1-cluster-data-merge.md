# tier1-cluster-data BE candidate 머지 sprint 산출물
**날짜**: 2026-05-14
**담당**: engineer-backend
**Task**: #4 (completed) + #5 (completed)

---

## 1. 작업 요약

`GET /api/status` 응답의 candidates dict에 6개 필드 부재 → ClusterPanel 모두 'E' 분류 회귀 수정.

---

## 2. 변경 파일 목록

| 파일 | 유형 | 핵심 변경 |
|---|---|---|
| `backend/pharmacophore.py` | 신규 | `compute_fwkt_contact`, `compute_chelator_site`, `compute_pharmacophore_fields` |
| `backend/routers/status.py` | 수정 | `get_status()` + `_enrich_candidates()` (6-field on-the-fly 머지) |
| `pipeline_local/scripts/pharmacology_guards.py` | 수정 | `HEURISTIC_FUNCTION_DISCLAIMERS` 2개 항목 등록 |
| `pyrosetta_flow/runner.py` | 수정 | `candidate_entry` dict에 5개 필드 추가 |
| `backend/tests/test_pharmacophore.py` | 신규 | 34개 단위 테스트 |

---

## 3. 6 필드 데이터 흐름

```
[Pipeline 경로]
pharma_properties.calculate_all(seq)
  → pharma["gravy"], pharma["net_charge_ph74"]
cluster_report.classify_cluster(cluster_input)
  → criteria_met.A.fwkt_contact (항상 계산)
  → criteria_met.D.chelator_site_available (cluster D/E만)
entry.get("selectivity_margin") (step05b 결과)

↓ runner.py candidate_entry에 포함
↓ emitter.set_candidates(enriched_entries)
↓ /tmp/pipeline_local_status.json 저장

[API 서버 경로 — GET /api/status]
read_status() → status dict
_enrich_candidates():
  ① instability_index: pharma 없으면 backend.pharmacology.instability_index(seq)
  ② gravy: 없으면 backend.pharmacology.gravy(seq)
  ③ net_charge_ph74: 없으면 backend.admet.compute_admet(seq)["net_charge_ph74"]
  ④ selectivity_margin: selectivity._JOBS completed 결과 lookup
  ⑤ fwkt_contact: 없으면 pharmacophore.compute_fwkt_contact(candidate) [HEURISTIC]
  ⑥ chelator_site_available: 없으면 pharmacophore.compute_chelator_site(seq) [HEURISTIC]
```

---

## 4. reviewer-pharma 공식 정의 (2026-05-14)

### fwkt_contact
- **정의**: SST-14 FWKT pharmacophore(Phe6-Trp7-Lys8-Thr9, 1-indexed)가 SSTR2 binding pocket과 ≤4.5 Å 접촉 유지
- **SSTR2 pocket**: TM3(Asp122), TM5(Asn276), TM6(Phe294,Trp291), TM7(Tyr316) [PDB 7T11]
- **문헌**: Patel YC 1999, Reubi JC 2017 J Nucl Med (Ki ~1 nM with FWKT)
- **Pipeline 소스**: cluster_report._criteria_a().fwkt_contact (structural_rules.fwkt_pharmacophore.pass)
- **Fallback**: "FWKT" substring 존재 → True (Phase 1 heuristic)

### chelator_site_available
- **정의**: DOTA chelator를 N-terminus free amine 또는 Lys ε-NH2에 부착 가능한 site 존재
- **SST-14 검증**: N-term(Ala), K4, K8, Cys3-Cys14 SS-bond → True ✓
- **문헌**: Krenning 1992 Lancet, Maecke 2005 J Nucl Med (K8 ε-NH2 anchor)
- **Pipeline 소스**: cluster_report._criteria_d().chelator_site_available (n_strong ≥ 1)
  - ⚠️ 주의: n_strong이 SS-bond Cys 포함 → 과대계산 가능 (개선 예정)
- **Fallback**: N-term ≠ Pro → True; Pro+Lys → True; Pro+noLys → False

---

## 5. 테스트 결과

```
48 passed in 0.52s (2026-05-14)
  backend/tests/test_pharmacophore.py  : 34 passed
  backend/tests/test_experiment_router.py : 14 passed (기존, 회귀 없음)
```

---

## 6. 미해결 이슈 / Phase 2 TODO

| ID | 이슈 | 담당 | 우선순위 |
|---|---|---|---|
| P2-1 | chelator_site_available: n_strong의 SS-bond Cys 포함 문제 | engineer-backend + reviewer-pharma | 중 |
| P2-2 | fwkt_contact Phase 2: PDB 거리 기반 ≤4.5Å 구현 | engineer-backend | 낮 |
| P2-3 | selectivity_margin: _JOBS ephemeral → 영속 저장 필요 | engineer-backend | 중 |
| P2-4 | chelator_site: Pro N-term DOTA coupling 가능 여부 | reviewer-pharma | 낮 |

---

## 7. HEURISTIC_FUNCTION_DISCLAIMERS 등록 확인

```
pipeline_local/scripts/pharmacology_guards.py:
  + "backend.pharmacophore.compute_fwkt_contact": {confidence_grade: "HEURISTIC"}
  + "backend.pharmacophore.compute_chelator_site": {confidence_grade: "HEURISTIC"}
```

Stage 5 (약리학 환각 방지) 준수 완료.
