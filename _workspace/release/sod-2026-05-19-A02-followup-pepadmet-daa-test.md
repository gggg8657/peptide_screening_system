# A-02 follow-up — pepADMET D-AA 지원 실 테스트 (2026-05-19)

> **수행**: researcher (~9.5분, 실 웹서버 POST)
> **결과**: ⚠️ **D-AA half-life 예측 불가 확정 (HIGH-BLOCKER)** — pepADMET D-아미노산·환형 SS bond 모두 미지원

## 1. 핵심 결론 (3줄)

1. **Half-life D-AA 지원 불가 확정** — natural seq 전용 입력, modification 40종 중 D-AA 0개
2. **SST-14 예측 4.83× 과대** — pepADMET HBN 14.484 min vs 실측 3분 (Brazeau 1973)
3. **비표준 AA silent error** — 'B' 입력 시 경고 없이 처리 → 위험

## 2. 입력 형식 (실 테스트)

| 엔드포인트 | 입력 | SMILES | Modification 옵션 |
|----------|------|--------|------------------|
| `/calcpep/half-life/` | 서열 단독 | **없음** | 40종 (D-AA **0개**) |
| `/calcpep/bbb/` | SMILES + 서열 | 있음 | SMILES로 표현 |
| `/calcpep/tox/` | SMILES + 서열 | 있음 | SMILES로 표현 |
| `/calcpep/property/` | 서열 단독 | 없음 | 없음 |

## 3. 실 테스트 결과 (7건)

| 입력 서열 | 변형 | HBN (min) | HBM (min) | 비고 |
|---------|-----|----------|----------|------|
| AGCKNFFWKTFTSC (SST-14) | 없음 | **14.484** | 33.127 | 실측 3분, **4.83× 과대** |
| AGCKNFFWKTFTSC + CarboxymethylC3 | C3 mod | 31.421 | **433.350** | modified 모델 |
| FCFWKTCT (Octreotide L-seq) | 없음 | **84.008** | 142.585 | 실측 90분, **0.93× 우연 근접** |
| FCFWKTCT + Amidated@C-term | 위치9 | 88.160 | 23.613 | modified |
| FCYWKVCT + Amidated@C-term (Lanreotide 근사) | 위치8 | 315.267 | 89.887 | D-Nal 미지원 |
| EHWSYLLRP (Leuprolide) | pyroGlu+Amidated | 147.713 | 176.795 | modified |
| AGCBNFFWKTFTSC (비표준 'B') | 없음 | 23.121 | 1.052 | ⚠️ **silent error** (경고 없음) |

## 4. D-AA 지원 종합 등급

| 기능 | 지원 | 비고 |
|------|------|------|
| Half-life D-AA 직접 입력 | **NO** | 확정 |
| Half-life SS bond 지정 | **NO** | modification 0개 |
| Half-life 비표준 AA 처리 | **Silent error** | 위험 |
| BBB SMILES D-AA chirality | **조건부 가능** | linear만 |
| BBB/Tox 환형 SS bond | **NO** | 서버 에러 |
| D-AA modification 드롭다운 | **NO** | 40종 중 0개 |

## 5. ENDPOINT_CONFIDENCE 갱신 권고

```python
# pharmacology_guards.py admet_pepadmet 갱신
"admet_pepadmet": {
    "grade": "P2",
    "d_amino_acid_support": False,   # None → False (확정)
    "d_aa_support_detail": {
        "halflife_endpoint": False,
        "bbb_tox_smiles_linear": "conditional",
        "bbb_tox_smiles_cyclic_ss": False,
    },
    "cyclic_support": False,
    "silent_error_risk": True,
    "benchmark_sst14_HBN_min": 14.484,    # 실측 3분 대비 4.83× 과대
    "benchmark_octreotide_HBN_min": 84.008,
    "warnings": [
        "⚠️ D-AA half-life 예측 불가 — natural seq 전용",
        "⚠️ SS bond modification 없음",
        "⚠️ 비표준 AA silent error",
        "⚠️ SST-14 4.83× 과대 — 절대값 사용 금지",
        "⚠️ 환형 SMILES 서버 파싱 오류",
        "H-06: 웹 예측값을 in vitro 실측 대체 금지",
    ],
    "source": "pepADMET JCIM 2025 DOI:10.1021/acs.jcim.5c02518. 실 테스트 2026-05-19.",
},
```

## 6. 운영 도입 권고

### 권고 A: L-AA 선형 triage 제한적 도입 [MED]
- 대상: SST-14 계열 L-AA mutation (D-AA 치환 전) 후보
- 용도: BBB, 독성, bioavailability 1차 triage (29 endpoint)
- 제한: **반감기 절대값 금지 (4-5× 오차), 상대 순위만**

### 권고 B: D-AA 후보 pepADMET 적용 금지 [HIGH-BLOCKER]
- Octreotide/Lanreotide 등 D-AA 포함 후보는 pepADMET 출력 신뢰 불가
- pharmacology_guards에 `d_amino_acid_support: False` 확정 반영
- 비표준 AA silent error 방지: 입력 전 20종 표준 AA 검증 로직 필수

### 권고 C: 자체 D-AA 반감기 모델 개발 [HIGH, 중장기]
- 공개 도구 D-AA half-life 예측 가능 도구 **0개** 확정
- wet-lab LC-MS/MS 실측 후 fine-tuning

### 권고 D: BBB SMILES linear 경로 별도 평가 [LOW]
- linear D-AA 펩타이드 SMILES → BBB 예측 가능성 확인됨 (C2-9r BBB+ 0.525)
- 환형 SS bond 처리 시도 (p2smi로 재생성)

## 7. 우리 벤치마크 세트 × pepADMET

| 펩타이드 | 구조 | pepADMET 결과 | 신뢰 |
|---------|-----|------------|------|
| SST-14 | L-AA, SS bond | HBN 14.5 min (실측 3, 4.83×) | ❌ 상대 순위만 |
| SST-14 L-AA mutation | L-AA, SS bond | 적용 가능 | △ 상대 순위 |
| Octreotide | D-AA, SS bond | 84 min (우연 근접) | ❌ D-AA 무시 |
| Lanreotide | D-AA + 비천연 | 근사값만 | ❌ D-Nal 미지원 |
| DOTA-SST14 유사체 | D-AA + chelator | 적용 불가 | ❌ |

## 8. §검증 필요 처리

| # | 상태 | 결과 |
|---|------|------|
| V-02 논문 전문 (paywall) | 미해결 | ACS 403, 저자 직접 문의 필요 |
| V-03 D-AA 처리 방법 | **해결** | Half-life: 불가. BBB SMILES: linear만 |
| V-06 GitHub 소스 | 확인 | toxicity 모델만 공개, half-life 모델 미공개 |
| V-07 API 접근 | 확인 | REST API 없음. Django form POST 가능 |

## 9. §미해결

1. V-02 ACS 논문 전문 paywall — 저자 (jiedong@csu.edu.cn) 직접 문의
2. BBB SMILES 환형 에러 — RDKit macrocycle 한계? p2smi 재생성 후 재시도
3. Half-life 모델 GitHub 미공개 — 가중치·학습 데이터 비공개
4. Leuprolide 실측 t½ — Free peptide IV 조건 공개값 미확보

## 10. 참고
- Brazeau P 1973 Science 179:77 — SST-14 t½≈3분
- Bauer W 1982 Life Sci 31:1133 — Octreotide t½≈90분
- pepADMET JCIM 2025 DOI: 10.1021/acs.jcim.5c02518
- github.com/ifyoungnet/pepADMET (toxicity만 공개)
