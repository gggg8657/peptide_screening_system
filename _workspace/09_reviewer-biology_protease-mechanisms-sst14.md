# reviewer-biology: Serum Protease 분해 메커니즘 분석 요약

**Task**: S1 (id=10) | **날짜**: 2026-05-12  
**산출물**: `docs/wetlab/protease_mechanisms_sst14.md` (~480 줄)  
**생물학적 타당성 등급**: HIGH (문헌 근거) for NEP cleavage sites; MED (구조 일관) for 후보 비교

---

## 핵심 발견 요약

### 1. SST-14 1차 분해 효소 확인 (HIGH)

**Neprilysin (NEP, endopeptidase-24.11)**이 SST-14 분해의 1차 개시 효소.  
PubMed 1972574 (Matsas et al. 1985) 직접 확인:
- **Phe6↓Phe7** — NEP 1차 site
- **Thr10↓Phe11** — NEP 1차 site  
- Asn5↓Phe6 — NEP 2차 site

### 2. FWKT Pharmacophore의 집중 취약성

Trypsin (K4, K9), Chymotrypsin/NEP (F6, F7, W8, F11) 모두 **pharmacophore 인접 또는 직접 공격** → SST-14 t½ ~2분의 주원인.

### 3. 후보별 주요 위험도

| 후보 | 위험도 | 핵심 이유 |
|------|--------|---------|
| T3 #1 (ILCKKFFWKTFTSC) | 🔴 HIGH | K5 추가로 Trypsin site 3개 (K4, K5, K9) |
| var07_I2K (AKCKNFFWKTFTSC) | 🔴 CRITICAL | K2↓C3 절단 → SS bond 구조 붕괴 위험 |
| T3 #3 (AGCKNDFWKTLTSC) | 🟢 BEST | F6→D로 NEP 1차 site 제거 + F11→L |
| var12_T12dThr | 🟢 TARGETED | D-Thr12로 F11↓T12 chymotrypsin 차단 |

### 4. Octreotide 안정화 원리 → 적용 권고

D-Trp8 도입(octreotide의 핵심) → Chymotrypsin/NEP W8↓K9 차단 → t½ 30× 연장.  
**cand03 및 FWKT 보존 후보 모두에 D-Trp8 우선 도입 권고.**

---

## § 검증 필요 (6항목)

- §VB-01: HPLC-MS/MS human serum stability assay (wet lab)
- §VB-02: D-Trp8 후 SSTR2 결합 확인
- §VB-03: SS bond 환원 속도 측정
- §VB-04: T3 #3 F6→D SSTR2 affinity 영향
- §VB-05: NEP Leu vs Phe P1' kcat 비율 정량
- §VB-06: var07_I2K K2↓C3 절단 실제 발생 여부

---

## 관련 파일 경로

- 산출물: `docs/wetlab/protease_mechanisms_sst14.md`
- 기존 구현: `docs/presentation/01_appendix/a01_halflife_and_protease_detail.md`
- 가드: `pipeline_local/scripts/pharmacology_guards.py` (HEURISTIC_FUNCTION_DISCLAIMERS)
