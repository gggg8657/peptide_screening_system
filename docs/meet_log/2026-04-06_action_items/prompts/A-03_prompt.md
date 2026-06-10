# Claude Code 실행 프롬프트 — A-03: Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가

> **📌 명칭 정정 (2026-05-20)**: 회의록 "Fab-ADMET"의 실제 도구는 **[pepADMET](https://github.com/ifyoungnet/pepADMET)** (GPL-3.0, Tan et al. 2026 JCIM, DOI: `10.1021/acs.jcim.5c02518`). 본 프롬프트의 "Fab-ADMET"은 pepADMET을 지칭하며, GitHub URL 검색 단계는 **완료 처리**. 후속 작업은 V-02~V-04(설치/D-AA 테스트/법무 검토)부터 진행. 상세: [`A-03_research_fab_admet.md`](../A-03_research_fab_admet.md).

## 사용 방법

```bash
# Claude Code CLI에서 이 파일을 컨텍스트로 로드하여 실행
# 방법 1: 직접 프롬프트 붙여넣기 (아래 "작업 정의" 섹션 내용)
# 방법 2: researcher에게 위임 (GitHub/논문 문헌 수집) + reviewer-pharma (검증)
```

---

## 컨텍스트

- `@CLAUDE.md` — 프로젝트 행동 규칙 및 위임 트리
- `@docs/meet_log/2026-04-06_action_items/A-03_Fab-ADMET_validation.md` — 액션 아이템 상세 정의
- `@docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성\ V2.pdf` — 원본 회의록
- `@pipeline_local/scripts/pharmacology_guards.py` — Stage 5 약리학 가드 (ENDPOINT_CONFIDENCE, HEURISTIC_FUNCTION_DISCLAIMERS)

---

## 작업 정의

**목표**: Fab-ADMET 도구의 정확도를 원 논문 기준으로 정리하고, SSTR2 타겟 환형 펩타이드(D-아미노산/비천연 AA/DOTA 킬레이터)에 대한 적용 가능성을 평가한다. 적용 불가 시 자체 학습 로드맵을 제시한다.

**핵심 제약**:
1. Fab-ADMET GitHub URL 확인이 최우선 (회의록에 URL 미명시 — 검색 필요)
2. 원 논문에 보고된 성능 지표(AUC, Accuracy, F1)는 **문헌 원문에서 직접 인용** (추측 금지)
3. 적용 가능성 평가는 "가능/불가능/미확인" 3단계로만 명시 (H-06 가드)
4. 자체 학습 요구사항은 프로젝트 GPU 자원 기준 (H100 NVL ×4, CUDA_VISIBLE_DEVICES=2)

---

## 입력 (Input Spec)

### 평가 대상 도구
```
도구명: Fab-ADMET
- GitHub: (URL 미확인 — researcher 에이전트로 검색 필요)
- 원 논문: (미확인 — researcher 에이전트로 검색 필요)
- 유사 키워드: "Fab-ADMET", "peptide ADMET prediction", "cyclic peptide toxicity ML"
```

### 벤치마크 입력 펩타이드 (A-02와 공유)

| 펩타이드 | 서열 | 특수성 |
|---------|------|--------|
| SST14 | AGCKNFFWKTFTSC | SS bond, 표준 L-아미노산 |
| Octreotide | D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr(ol) | D-아미노산, 고리형 |
| Lanreotide | D-Nal-Cys-Tyr-D-Trp-Lys-Val-Cys-Thr | D-Nal (비천연), D-아미노산 |
| SSTR2 신규 후보 (예시) | SST14 파생 + DOTA | DOTA 킬레이터 결합 |

### 프로젝트 GPU 자원
```
GPU: H100 NVL ×4
기본 설정: CUDA_VISIBLE_DEVICES=2
학습 가용: CUDA_VISIBLE_DEVICES=0,1,3 (필요 시 조정)
```

---

## 출력 (Output Spec)

### 1. Fab-ADMET 정보 요약 (Markdown)

```markdown
## Fab-ADMET 기본 정보
- GitHub URL: <URL 또는 "미확인">
- 원 논문: <저자 연도 저널 DOI>
- 라이선스: <MIT/Apache/기타/미확인>

## 원 논문 성능 지표
| 지표 | 값 | 데이터셋 | 모달리티 |
|-----|---|---------|---------|
| AUC | ? | ? | ? |
| Accuracy | ? | ? | ? |
| F1 | ? | ? | ? |

출처: <논문 원문 직접 인용>
```

### 2. SSTR2 펩타이드 적용 가능성 표 (Markdown)

```markdown
| 특성 | Fab-ADMET 지원 여부 | 근거 |
|-----|-----------------|------|
| 표준 L-아미노산 펩타이드 | 가능/불가능/미확인 | |
| 환형 펩타이드 (SS bond) | 가능/불가능/미확인 | |
| D-아미노산 | 가능/불가능/미확인 | |
| 비천연 아미노산 (D-Nal) | 가능/불가능/미확인 | |
| DOTA 킬레이터 결합 구조 | 가능/불가능/미확인 | |
```

### 3. 자체 학습 요구사항 표 (해당 시)

```markdown
| 항목 | 값 | 근거/산정 방법 |
|-----|---|--------------|
| 필요 학습 데이터 규모 | ? samples | 논문 스케일링 법칙 참조 |
| GPU VRAM | ? GB | 모델 파라미터 수 기반 |
| 학습 시간 (H100 NVL 기준) | ?시간 | |
| Fine-tuning 가능 여부 | 가능/불가능 | |
| 학습 데이터 소스 후보 | ChEMBL, PubChem BioAssay, ... | |
```

### 4. ENDPOINT_CONFIDENCE 등록 코드 스니펫

```python
# pharmacology_guards.py 추가용 (실제 추가는 engineer-backend 검토 후)
ENDPOINT_CONFIDENCE["fab_admet_toxicity"] = {
    "tool": "Fab-ADMET",
    "grade": "P?",           # P1=high / P2=moderate / P3=low / P4=heuristic
    "d_amino_acid_support": False,     # 검증 후 갱신
    "cyclic_peptide_support": False,   # 검증 후 갱신
    "dota_support": False,             # 검증 후 갱신
    "local_executable": True,
    "reported_auc": 0.0,               # 원 논문 값
    "disclaimer": (
        "Fab-ADMET는 표준 아미노산 학습 데이터 기반. "
        "D-아미노산·비천연 AA·DOTA 결합 구조는 도메인 외 예측이므로 신뢰도 낮음. "
        "wet-lab ADMET 실측 병행 필수."
    ),
    "source": "<논문 DOI>",
}
```

### 5. 권고사항 (Markdown)
- 통합 권고 / 조건부 통합 / 미권고 + 대안 중 하나 선택
- 대안 도구 후보 (해당 시)

---

## 검증 기준 (Acceptance Criteria)

- [ ] Fab-ADMET GitHub URL 확인 완료 (미발견 시 "확인 불가" 명시)
- [ ] 원 논문 AUC / Accuracy / F1 수집 완료 (논문 원문 직접 인용, 없으면 "미보고" 명시)
- [ ] SSTR2 벤치마크 세트 4종 적용 가능성 평가 완료 (가능/불가능/미확인 3단계)
- [ ] D-아미노산 처리 가능 여부 명확히 확인 (미확인 상태 허용 — 단, "미확인" 명시 필수)
- [ ] 자체 학습 시 H100 NVL 기준 요구사항 산정 완료 (불가 시 근거 명시)
- [ ] `ENDPOINT_CONFIDENCE` 등록 형식 준수
- [ ] H-06 가드 준수: 확인되지 않은 항목은 "미확인" 명시, 추측 금지

---

## 추천 위임 경로

```
researcher         ← Fab-ADMET GitHub/논문 URL 검색, 성능 지표 수집
reviewer-pharma    ← 원 논문 AUC/F1 지표의 약리학적 타당성 검증
                      D-아미노산 ADMET 예측 신뢰도 검토
reviewer-chemistry ← D-아미노산/비천연 AA/DOTA 구조 입력 가능 여부 검증
                      SMILES 표현 적합성 검토
engineer-backend   ← ENDPOINT_CONFIDENCE 테이블 등록 코드 구현
                      Fab-ADMET 로컬 실행 환경 설정 (conda, 의존성)
                      pharmacology_guards.py 연동 테스트 작성
engineer-infra     ← 자체 학습 시 GPU 환경 구성 (H100 NVL ×4 설정)
```

**실행 예시 (단계별)**:
```bash
# Step 1: researcher로 GitHub/논문 정보 수집
# (Claude Code에서 researcher 에이전트 호출)
"Fab-ADMET 도구 GitHub 리포지토리와 원 논문을 찾아주세요. 
 키워드: Fab-ADMET, peptide ADMET prediction, cyclic peptide toxicity ML"

# Step 2: 수집된 정보로 적용 가능성 평가
# (reviewer-pharma + reviewer-chemistry 병렬 호출)
"수집된 Fab-ADMET 정보로 SSTR2 타겟 환형 펩타이드(D-아미노산/DOTA 포함) 
 적용 가능성을 평가하세요. A-03_Fab-ADMET_validation.md 참조."
```

---

## 에러 처리

| 에러 상황 | 대응 |
|---------|------|
| Fab-ADMET GitHub 미발견 | "Fab-ADMET" 대안 키워드로 재검색, 미발견 시 유사 도구(Chemprop, DeepADMET 등) 제안 |
| 원 논문 AUC 미보고 | "성능 지표 미보고" 명시, 독립 벤치마크로 자체 평가 제안 |
| D-아미노산 입력 오류 | SMILES 형식으로 재시도, 실패 시 "D-AA 미지원 확인" |
| DOTA 구조 파싱 실패 | "DOTA 킬레이터 미지원" 명시 (C-07 DOTA stoichiometry 규칙과 연계) |
| 라이선스 상업 이용 불가 | 라이선스 이슈 명시, 대안 오픈소스 도구 제안 |
| 자체 학습 데이터 부족 | 필요 데이터 규모 추정 + 공개 데이터셋(ChEMBL, BindingDB) 활용 방안 제시 |

---

## 참고 자료

- ChEMBL (학습 데이터 소스 후보): https://www.ebi.ac.uk/chembl/
- PubChem BioAssay: https://pubchem.ncbi.nlm.nih.gov/
- DeepADMET (대안 도구 후보): https://github.com/chaoszhang/DeepADMET
- Chemprop (그래프 신경망 기반): https://github.com/chemprop/chemprop
- `pipeline_local/scripts/pharmacology_guards.py` — Stage 5 가드 및 ENDPOINT_CONFIDENCE / HEURISTIC_FUNCTION_DISCLAIMERS 구조 참조
- `tools/harness-adaptation/PROMPT_PRST_N_FM_EXAMPLE.md §3` — H-06 가드 ("계산 불가능을 계산 가능한 척" 방지)
- `pipeline_local/scripts/modification_conflict.py` — C-07 DOTA stoichiometry 규칙 참조
