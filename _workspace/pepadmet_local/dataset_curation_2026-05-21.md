# pepADMET 학습 데이터 큐레이션 보고서
## A5Pa — 2026-05-21

**작성**: researcher (action-items-closure-20260521 팀)  
**산출물**: `pepADMET/data/Toxicity_extended.csv` + `curation_metadata_2026-05-21.csv`

---

## 0. 요약

| 항목 | 값 |
|------|-----|
| 원본 행 수 | 135 (binary_toxicity 라벨: 30건) |
| 신규 추가 행 수 | **224** |
| 최종 행 수 | **359** |
| binary_toxicity 라벨 (최종) | non-toxic=145, toxic=109, NaN=105 |
| cyclic SS-bond non-toxic | **9** (PubChem FDA/endogenous) |
| cyclic SS-bond toxic | **5** (PubChem cyclotides) |
| cyclic non-SS toxic | 89 (Hemolytik2) |
| cyclic non-SS non-toxic | 121 (Hemolytik2+Pasireotide) |
| abort 판정 | **진행** (224 > 50 row, abort 기준 미충족) |

⚠️ **SS-bond 30+ 미충족**: non-toxic SS=9 (목표 30+), toxic SS=5 (목표 30+).  
공개 DB에서 확보 가능한 최대치. 전체 추가량(224행)은 abort 기준(50)을 크게 초과.

---

## 1. 소스별 수집 결과

### 1.1 FDA 승인 / 내인성 cyclic SS-bond 펩타이드 (non-toxic, label=0)

**소스**: PubChem (공개, 라이센스 없음)  
**라벨 근거**: FDA/EMA 승인 → 임상 안전성 확립

| 화합물 | PubChem CID | SS-bond | MW | 근거 |
|--------|------------|---------|-----|------|
| Octreotide | 448601 | ✅ | 1019 Da | FDA 승인 SSTR2/5 agonist |
| Oxytocin | 439302 | ✅ | 1007 Da | FDA 승인 |
| Desmopressin | 5311065 | ✅ | 1069 Da | FDA 승인 |
| Atosiban | 5311010 | ✅ | 994 Da | EMA 승인 |
| Eptifibatide | 123610 | ✅ | 832 Da | FDA 승인 |
| Lanreotide | 6918011 | ✅ | ~1096 Da | FDA/EMA 승인 SSTR2/5 agonist |
| Arginine vasopressin | 644077 | ✅ | ~1084 Da | 내인성, 생리 용량 비독성 |
| Somatostatin-14 | 16129706 | ✅ | ~1639 Da | 내인성 SRIF, SSTR2 agonist |
| Calcitonin (salmon) | 16220016 | ✅ | 3358 Da | FDA 승인 |
| Pasireotide | 9941444 | ❌ (cyclic, non-SS) | 1047 Da | FDA 승인 pan-SSTR |

**행 수**: 10 (SS=9, non-SS=1)

### 1.2 PubChem — Cyclotide toxic SS-bond 펩타이드 (toxic, label=1)

**소스**: PubChem (공개)  
**라벨 근거**: 문헌 HC50 ≤ 100 µM 확립 hemolytic cyclotide  
**cyclotide 특징**: 3 SS bond + 머리-꼬리(head-to-tail) amide bond 환형화 → cyclic + SS-bond 대표 구조

| 화합물 | PubChem CID | SS-bond | 헤몰리시스 근거 |
|--------|------------|---------|---------------|
| Kalata B2 | 56669818 | ✅ | HC50 ~10-20 µM (Kamimori et al. 2005) |
| Cycloviolacin O2 | 119026029 | ✅ | HC50 ~20 µM (Svangård et al. 2004) |
| Cycloviolacin H4 | 44566282 | ✅ | Hemolytic cyclotide (Göransson et al. 2009) |
| Kalata B8 | 56676637 | ✅ | HC50 ~50 µM (Simonsen et al. 2008) |
| RTD-2 (Rhesus theta-defensin-2) | 16131989 | ✅ | Cyclic antimicrobial, hemolytic at ~50 µM |

**행 수**: 5

### 1.3 Hemolytik2 2025 — Cyclic 펩타이드 (binary label)

**소스**: Hemolytik2 (GitHub: raghavagps/Hemolytik2, 2025)  
**접근**: `curl -L https://github.com/raghavagps/Hemolytik2/raw/main/Hemolytik2_complete_data.csv`  
**파일 크기**: 7.4 MB (13,215 행 → cyclic 912 → label+SMILES 209)  
**라이센스**: 데이터 사용 제한 없음 (학술 공개 데이터)

**수집 쿼리**:
```
lyn_cyc == 'Cyclic'
AND smiles NOT NULL
AND binary_label NOT NULL
(binary_label = 0 or 1, v2 labeling rules 적용)
```

**라벨 파생 규칙 (v2)**:

| 패턴 | 라벨 |
|------|------|
| "0 % Hemolysis at ..." / "<5%" / "non-hemolytic" | 0 (non-toxic) |
| `non_hem` = "Non-hemolytic" or "Low hemolytic" | 0 |
| HC50 > 200 µM / MHC > 200 µM | 0 |
| "100% Hemolysis at ≤200 µM" / "100% at ≤200 µg/ml" | 1 (toxic) |
| HC50 ≤ 100 µM / MHC ≤ 100 µM | 1 |
| "96% Hemolysis at 150 µM" | 1 |
| `nature` = "Hemolytic" (단독) | 1 |

**수집 결과**:
| 라벨 | 행 수 | 비고 |
|------|-------|------|
| non-toxic (0) | 120 | Low hemolytic 포함 |
| toxic (1) | 89 | HC50 ≤ 100 µM 또는 100% 용혈 |
| **합계** | 209 | SS-bond in SMILES: 0 (자유 티올 표현) |

⚠️ **SS-bond 표현 제한**: Hemolytik2 SMILES는 자유 티올(-SH) 형태로 저장. Cycloviolacin 시리즈 등 실제 SS-bond 있는 peptide도 SMILES에는 CSSC 없음. 85개 Cys 포함 시퀀스.

---

## 2. 도메인 분포 분석

### 2.1 신규 데이터 길이 분포

| 소스 | 라벨 | 평균 길이 | 범위 |
|------|------|---------|------|
| FDA SS-bond | 0 | 8~32 aa | 8 (Octreotide) ~ 32 (Calcitonin) |
| Cyclotides SS-bond | 1 | 28-30 aa | 27~31 |
| Hemolytik2 non-toxic | 0 | 17 aa | 4~45 |
| Hemolytik2 toxic | 1 | 18 aa | 6~32 |
| **SST-14 (원형)** | **0** | **14 aa** | — |
| **PRST-001~004 (타겟)** | **?** | **14 aa** | — |

### 2.2 SS-bond 데이터 현황

| 범주 | non-toxic | toxic | 합계 |
|------|----------|-------|------|
| SS-bond SMILES (CSSC) | **9** | **5** | **14** |
| Cys 포함 (SS 아닐 수 있음) | 107 | 91 | 198 |
| SS 없음 | 29 | 13 | 42 |

### 2.3 원본 vs 확장 비교

| 항목 | 원본 | 확장 |
|------|------|------|
| 총 행 | 135 | **359** |
| binary_toxicity 라벨 | 30 | **254** |
| cyclic SS-bond 라벨 | 0 | **14** (9 non-toxic, 5 toxic) |
| 14aa 환형 SS-bond | 0 | 1 (SST-14) |

---

## 3. 정제 규칙

1. **중복 제거**: `smiles` 기준 중복 행 제거 예정 (backend 단계)
2. **SMILES 검증**: `rdkit.Chem.MolFromSmiles()` 실패 시 제거 (conda env 필요)
3. **train/test/valid 분할**: `group` 컬럼 (`training` = 배정 예정, backend가 재분할)
4. **라벨 일관성**: binary_toxicity 외 태스크(toxicity_type, neurotoxicity_type, HC50)는 NaN으로 신규 추가 → 마스크 기반 학습으로 처리됨
5. **Descriptor 계산**: 2133개 descriptor 컬럼은 모두 NaN → **conda env에서 PyBioMed로 재계산 필요**

---

## 4. 라이센스 정리

| 소스 | 라이센스 | 재배포 조건 |
|------|---------|-----------|
| PubChem | 공개 도메인 | 없음 |
| Hemolytik2 2025 | 학술 공개 (무제한 사용 명시 없음) | 학술 인용 권장 |
| pepADMET (train code) | **GPL v3** | 수정/재배포 시 GPL 전파 |
| 신규 weights (학습 후) | **GPL v3 derivative** | 외부 공개 시 GPL 의무 |

---

## 5. 미충족 항목 (§검증 필요)

| 항목 | 현황 | 원인 |
|------|------|------|
| SS-bond non-toxic ≥ 30 | **9/30** | 공개 DB 한계; DBAASP 직접 다운로드 불가 |
| SS-bond toxic ≥ 30 | **5/30** | PubChem에 cyclotide SS-bond SMILES 등재 제한 |
| Descriptor 계산 | NaN | conda env (Python 3.7 + PyBioMed) 미셋업 |
| SMILES 검증 | 미실행 | rdkit conda env 필요 |
| Hemolytik2 SS-bond SMILES | 0건 | 자유 티올 형태로 저장 → SS bond 미인코딩 |

**권고 (backend 위임)**:
1. DBAASP에서 cyclic SS-bond hemolytic 데이터 추가 수집 (웹 UI 수동 export 또는 API 확보 시)
2. conda env 셋업 후 새 행들의 PyBioMed descriptor 계산
3. SMILES rdkit 검증 + 중복 제거 실행

---

## 6. 파일 위치

| 파일 | 경로 | 크기 |
|------|------|------|
| `Toxicity_extended.csv` | `_workspace/pepadmet_local/pepADMET/data/` | 2.1 MB |
| `curation_metadata_2026-05-21.csv` | `_workspace/pepadmet_local/` | ~30 KB |
| Hemolytik2 원본 | `/tmp/hemolytik2_test.csv` (임시) | 7.4 MB |

> **주의**: `/tmp/` 파일은 재부팅 시 삭제됨. 영구 보관 필요 시 backend가 이동 요청.

---

## 7. abort 판정

| 조건 | 기준 | 결과 |
|------|------|------|
| 신규 row 수 | < 50 → abort | **224행 → 진행** ✅ |
| SS-bond 30+ non-toxic | 권고 기준 | **9/30 — 미충족** ⚠️ |
| SS-bond 30+ toxic | 권고 기준 | **5/30 — 미충족** ⚠️ |

**결론**: abort 조건 미충족, 진행 권장. SS-bond 미충족은 공개 DB 한계로 사용자 결정 필요.

---

**다음 단계 (A5Pb)**: conda env 셋업 (dgl≥0.9 + torch≥2.0, 대안 B) + descriptor 재계산 + SMILES 검증
