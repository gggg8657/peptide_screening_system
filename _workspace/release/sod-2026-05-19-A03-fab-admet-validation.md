# A-03 — pepADMET 정확도 검증 + 자체 학습 가능성

> **수행**: researcher (2026-05-19, ~5.5분)
> **갱신**: 2026-05-19 V-01 해결 — **사용자 확인: "Fab-ADMET"는 오기재, 실제 도구는 pepADMET**
> **분류**: Phase 1, 즉시 병렬

## 핵심 발견

**회의록의 "Fab-ADMET" 표기는 오기재** — 실제 평가 대상 도구는 **pepADMET** (2025 JCIM, 펩타이드 전용 ADMET 플랫폼). 사용자가 V-01 직접 확인 (2026-05-19).

> 참고: researcher 1차 조사에서 학술 DB·GitHub 어디에도 "Fab-ADMET" 이름 도구 미확인. FP-ADMET (소분자, GPL v3) 가능성도 검토했으나, **pepADMET이 정확한 대상**으로 확정.

## 표 1 — 도구별 원 논문 성능

| 도구 | endpoint | AUC | 학습 규모 | 입력 | 라이선스 |
|------|---------|-----|---------|-----|---------|
| FP-ADMET | 56 | BBB 0.92, DILI ~0.74 | 88~59K /endpoint | SMILES | GPL v3 |
| pepADMET | 29 | 독성 0.949, 생체이용률 0.90, BBB 0.889 | 36,643 펩타이드 | 미확인 (서열 추정) | CC BY-NC-SA |
| ADMET-AI | 41 | 20/31 AUROC>0.85 | TDC | SMILES | CC-BY |
| ADMETlab 3.0 | 119 | DMPNN-Des | >400K | SMILES/API | 상업 |
| CAPTP | 독성 binary | 0.959 CV / 0.901 test | 7,513 펩타이드 | 서열 | CC-BY |
| ToxTeller | 독성 binary | 0.930 | 4,129 | 서열 | CC-BY |
| CycPeptMP | 막 투과성 | R=0.87 | ~1,000 환형 | 구조 | 미확인 |

## 표 2 — SSTR2 환형 펩타이드 (D-AA, DOTA) 적용 가능성

| 특성 | FP-ADMET | pepADMET | ADMET-AI | CAPTP/ToxTeller |
|------|----------|----------|----------|----------------|
| 표준 L-AA 선형 | 미확인 | **가능** | 미확인 | 가능 |
| 환형 (SS bond) | 미확인 | **가능** | 미확인 | **불가능** |
| D-AA (Octreotide) | 미확인 | 미확인 | 미확인 | **불가능** |
| 비천연 (D-Nal) | 미확인 | 미확인 | 미확인 | **불가능** |
| DOTA 결합 | **불가능** | 미확인 | **불가능** | **불가능** |
| 로컬 실행 | 가능 | **불가능 (웹 전용)** | 가능 | 가능 |

## 표 3 — 자체 fine-tuning 가능성

| 항목 | 추정 | 신뢰 |
|------|------|------|
| 목표 도구 | ToxTeller (서열 기반) 또는 CAPTP | MED |
| 필요 데이터 | D-AA 환형 ≥500-2000 samples | LOW |
| 학습 시간 (H100 1장) | 1-4시간 | LOW |
| Fine-tuning 가능 | **가능** (CC-BY 라이선스) | HIGH |
| 주요 병목 | **D-AA 환형 ADMET 레이블 데이터 부족** | HIGH |

## ENDPOINT_CONFIDENCE 등록 코드 (pharmacology_guards.py 추가 권고)

```python
ENDPOINT_CONFIDENCE["fab_admet_toxicity"] = {
    "tool": "FP-ADMET (Venkatraman 2021) 또는 pepADMET — 회의록 'Fab-ADMET' 도구 정체 미확인",
    "grade": "P3",  # low confidence
    "d_amino_acid_support": None,     # 미확인
    "cyclic_peptide_support": None,
    "dota_support": False,
    "local_executable": True,         # FP-ADMET 기준
    "reported_auc": 0.92,             # BBB endpoint
    "disclaimer": (
        "SSTR2 환형 펩타이드(D-Phe, D-Trp, D-Nal, DOTA)는 학습 도메인 외(OOD) 예측. "
        "신뢰도 매우 낮음. wet-lab ADMET 실측 병행 필수."
    ),
    "source": "Venkatraman 2021 J Cheminform 13:56",
}
```

## 권고

| 시나리오 | 권고 | 등급 |
|---------|------|------|
| FP-ADMET를 SSTR2 환형에 직접 적용 | **미권고** | LOW |
| pepADMET로 SST14(L-AA) 사전 스크리닝 | 조건부 도입 (비상업, 웹 전용) | MED |
| ToxTeller/CAPTP로 독성 스크리닝 | 조건부 (D-AA/환형 미지원) | MED |
| CycPeptMP로 환형 투과성 예측 | 조건부 (투과성만) | MED |
| 자체 fine-tuning (ToxTeller 기반) | **중장기 권고** (6개월+) | MED |

### 신뢰 가능 endpoint (SSTR2 컨텍스트)

| Endpoint | 권장 도구 | 조건 |
|---------|---------|------|
| 독성 | pepADMET (L-AA만), ToxTeller | L-AA 선형 한정 |
| 생체이용률 | pepADMET | SST14만 신뢰 |
| BBB 투과성 | pepADMET | 참고용 |
| 막 투과성 | CycPeptMP | 환형 구조 특화 |
| **D-AA 후보 독성** | **신뢰 가능한 도구 없음** | wet-lab 필수 |
| **DOTA 결합 후보** | **신뢰 가능한 도구 없음** | wet-lab 필수 |

## §검증 필요 (V-01~V-08)

| # | 사항 | 우선 | 담당 |
|---|------|------|------|
| V-01 | ~~회의록 PDF의 "Fab-ADMET" 원본 표기 확인~~ — **RESOLVED 2026-05-19: pepADMET 오기재 확정** | DONE | 사용자 (확인 완료) |
| V-02 | pepADMET 논문 전문 접근 (DOI: 10.1021/acs.jcim.5c02518, paywall) | HIGH | reviewer-pharma |
| V-03 | pepADMET D-AA 처리 방법 — Octreotide SMILES 테스트 | HIGH | reviewer-chemistry |
| V-04 | FP-ADMET 학습 데이터 펩타이드 포함 여부 | MED | engineer-backend |
| V-05 | ChEMBL D-AA 환형 ADMET 데이터 수 | MED | engineer-backend |
| V-06 | pepADMET 로컬 설치 가능성 | MED | engineer-infra |
| V-07 | CycPeptMP D-AA monomer-level 처리 | LOW | engineer-backend |
| V-08 | ADMETlab 3.0 상업 라이선스 KAERI 적용 | LOW | 사용자/법무 |

## 결론

> SSTR2 theranostic 후보의 핵심 특성인 **D-아미노산·DOTA 킬레이터 결합 구조에 대한 신뢰할 수 있는 ADMET 예측 도구는 현재 존재하지 않는다.** pepADMET가 가장 근접하지만 웹 전용·비상업 라이선스 제약과 D-AA 미명시 한계가 있다. 자체 fine-tuning은 기술적으로 가능하나(ToxTeller/CAPTP, CC-BY) D-AA 환형 ADMET 데이터 확보가 실질 병목이다.
