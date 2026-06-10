# Claude Code 실행 프롬프트 — A-02: 혈청 반감기 예측 도구 비교 조사

## 사용 방법

```bash
# Claude Code CLI에서 이 파일을 컨텍스트로 로드하여 실행
# 방법 1: 직접 프롬프트 붙여넣기 (아래 "작업 정의" 섹션 내용)
# 방법 2: /subagent-dev 스킬로 engineer-backend에 위임
```

---

## 컨텍스트

- `@CLAUDE.md` — 프로젝트 행동 규칙 및 위임 트리
- `@docs/meet_log/2026-04-06_action_items/A-02_serum_halflife_tools.md` — 액션 아이템 상세 정의
- `@docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성\ V2.pdf` — 원본 회의록
- `@pipeline_local/scripts/pharmacology_guards.py` — Stage 5 약리학 가드 (반감기 관련 검증 로직)

---

## 작업 정의

**목표**: 혈청 반감기 예측 도구 5종 이상을 벤치마크 세트(SST14, Octreotide, Lanreotide, RC-160)에 적용하여 정확도와 파이프라인 통합 가능성을 평가한다.

**핵심 제약**:
1. D-아미노산 처리 가능 도구 ≥1개 반드시 확보 (없으면 자체 ML 모델 로드맵 제시)
2. 평가 결과는 `pharmacology_guards.py`의 `ENDPOINT_CONFIDENCE` 테이블에 통합 가능한 형식으로 출력
3. 계산 불가능한 항목은 "계산 불가능"으로 명시 (H-06 가드 — 추측 금지)
4. 모든 도구 평가 결과에 **문헌 출처** 명시 (pharmacology_guards.py 스타일)

---

## 입력 (Input Spec)

### 벤치마크 세트

```python
BENCHMARK_SET = {
    "SST14": {
        "sequence": "AGCKNFFWKTFTSC",
        "known_t_half_min": 3.0,       # 혈청 반감기 (분), 문헌 실측
        "ss_bond": (3, 14),             # Cys3-Cys14
        "aa_type": "standard_L",
        "source": "Brazeau 1973 Science 179:77"
    },
    "Octreotide": {
        "sequence": "D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr(ol)",
        "known_t_half_min": 100.0,      # ~100분
        "aa_type": "d_amino_acid",
        "source": "Lamberts 1996 NEJM 334:246"
    },
    "Lanreotide": {
        "sequence": "D-Nal-Cys-Tyr-D-Trp-Lys-Val-Cys-Thr",
        "known_t_half_min": None,       # 제형에 따라 수 시간~수일 (IP/SC 제형 차이)
        "aa_type": "unnatural_aa",
        "note": "D-Nal = D-2-Naphthylalanine (비천연 아미노산)"
    },
    "RC160_Vapreotide": {
        "sequence": "D-Phe-Cys-Phe-Trp-Lys-Val-Cys-Thr",
        "known_t_half_min": None,       # RC-160은 serum stability ↑ 정성 정보만 있음
        "aa_type": "d_amino_acid",
        "note": "Val 소수성 측쇄로 serum stability ↑, specificity ↓"
    }
}
```

### 평가 대상 도구 리스트

```python
TOOLS_TO_EVALUATE = [
    {"name": "ProtParam", "url": "https://web.expasy.org/protparam/",       "method": "N-end rule 기반"},
    {"name": "HLP",        "url": "확인 필요",                               "method": "ML 기반 혈청 반감기"},
    {"name": "PlifePred",  "url": "http://crdd.osdd.net/raghava/plifepred/", "method": "서열 기반 예측"},
    {"name": "PeptideStability", "url": "GitHub — 확인 필요",               "method": "ML/AI 모델"},
    {"name": "PeptideRanker",    "url": "http://www.moult.umbi.umd.edu/",   "method": "생물활성 순위화"},
]
```

---

## 출력 (Output Spec)

### 1. 도구별 평가 매트릭스 (Markdown 표)

```markdown
| 도구 | SST14 예측(min) | Octreotide 예측(min) | D-AA 지원 | API | 로컬 | R² | ρ | 비고 |
```

### 2. 통합 후보 도구 추천 (Markdown)
- 기준: R² ≥ 0.5 AND Spearman ρ ≥ 0.7 AND 로컬 실행 가능

### 3. ENDPOINT_CONFIDENCE 등록 코드 스니펫

```python
# pharmacology_guards.py 추가용 코드 (실제 추가는 engineer-backend 검토 후)
ENDPOINT_CONFIDENCE["halflife_<tool_name>"] = {
    "tool": "<tool_name>",
    "grade": "P?",   # P1=high / P2=moderate / P3=low / P4=heuristic
    "d_amino_acid_support": False,
    "local_executable": True,
    "benchmark_r2": 0.0,
    "benchmark_spearman_rho": 0.0,
    "disclaimer": "...",  # H-06 가드 준수
    "source": "...",      # 문헌 인용
}
```

### 4. D-아미노산 지원 부재 시 자체 ML 모델 로드맵 (있으면)
- 필요 데이터 규모, 학습 전략, 예상 기간

---

## 검증 기준 (Acceptance Criteria)

- [ ] 벤치마크 세트 4종 모두에 대해 각 도구 예측값 수집 완료 (지원 불가 시 "N/A" 명시)
- [ ] R² ≥ 0.5 AND Spearman ρ ≥ 0.7 이상 도구 ≥1개 확인 (미달 시 전체 미달 명시)
- [ ] D-아미노산 처리 가능 도구 ≥1개 확보 또는 자체 모델 로드맵 제시
- [ ] 모든 예측값에 문헌 출처 또는 도구 출처 명시
- [ ] `ENDPOINT_CONFIDENCE` 등록 형식 준수 (pharmacology_guards.py 스타일)
- [ ] H-06 가드 준수: 예측 불가능한 항목은 "지원 불가" 명시, 추측 금지

---

## 추천 위임 경로

```
reviewer-pharma    ← 반감기 예측값 약리학 검증, 문헌 실측값 정합성
reviewer-chemistry ← D-아미노산/비천연 AA 처리 가능 여부 검증
engineer-backend   ← ENDPOINT_CONFIDENCE 테이블 등록 코드 구현
                     pharmacology_guards.py 연동 테스트 작성
```

**실행 예시**:
```bash
# 서브에이전트 위임
/subagent-dev "A-02 혈청 반감기 도구 평가 — docs/meet_log/2026-04-06_action_items/prompts/A-02_prompt.md 참조"
```

---

## 에러 처리

| 에러 상황 | 대응 |
|---------|------|
| HLP 1.6초 예측 재현 | 재현 확인 후 신뢰도 P4(heuristic/unreliable)로 등급화 |
| 도구 API 접근 불가 | "API 접근 불가" 명시, 로컬 대안 탐색 |
| D-아미노산 입력 오류 | SMILES 형식으로 재시도, 실패 시 "D-AA 미지원" 명시 |
| Lanreotide D-Nal 처리 불가 | "비천연 AA 미지원" 명시, 자체 모델 로드맵 트리거 |
| 문헌 실측값 불명확 (Lanreotide, RC-160) | 제형별 t½ 범위 명시 + Spearman ρ 계산 제외 |

---

## 참고 자료

- ExPASy ProtParam: https://web.expasy.org/protparam/
- PlifePred: http://crdd.osdd.net/raghava/plifepred/
- Varshavsky 1996 PNAS 93:12142 — N-end rule mammalian half-life (pharmacology_guards.py 인용)
- Lamberts SWJ et al. 1996 NEJM 334:246 — Octreotide pharmacology
- Brazeau P et al. 1973 Science 179:77-79 — SST14 원본 논문
- `pipeline_local/scripts/pharmacology_guards.py` — Stage 5 가드 및 ENDPOINT_CONFIDENCE 구조 참조
- `tools/harness-adaptation/PROMPT_PRST_N_FM_EXAMPLE.md §3` — H-06 가드 ("계산 불가능을 계산 가능한 척" 방지)
