# A-03: Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가

**회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) | **담당**: AI팀 | **기한**: 5월 회의 전 | **상태**: 🟡 wrapper 완료, HTTP 403 차단

---

## ① 원본 요청 및 해석/분석

### 원문 (PDF §3 Action Items 표, p.5)
> "Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가"

### 회의록 §2.2 배경 (p.3)
> "ADMETlab 3.0 API 활용을 검토하였으나, 웹 기반 서비스로 현재 파이프라인과의 MCP 연동에 기술적 한계가 있다. 대안으로 Fab-ADMET을 논의하였는데, 독성 모델이 공개되어 있고 학습 코드가 GitHub에 공개되어 자체 학습이 가능하지만, 정확도 문제로 추가 검토가 필요하다. (추가적인 학습에 대한 김동주 선생님의 의견!!)"

### 회의록 §4 A-03 수행 가이드 (p.7)
1. Fab-ADMET GitHub 리포지토리에서 공개된 독성 모델과 학습 코드를 클론한다.
2. 원 논문에서 보고된 성능 지표(AUC, accuracy, F1)를 정리하고, 어떤 데이터셋/모달리티로 평가되었는지 확인한다.
3. SSTR2 타겟 펩타이드에 대한 적용 가능성을 평가한다 (환형 펩타이드, D-아미노산/비천연 아미노산 처리 가능 여부).
4. 자체 학습이 필요한 경우 데이터셋 규모, GPU 요구 사양, 예상 소요 시간을 산정한다.

### 후속 발견 (5/26 분석 파일 + audit)
- **Fab-ADMET = pepADMET 식별 확인** (2026-05-20, MASTER_INDEX A-03 비고)
- **HTTP 403 차단** — 외부 API 호출 시 차단됨 (audit)
- pepADMET 로컬 마이그레이션 진행됨 (`_workspace/pepadmet_local/pepADMET/`)

### 의도·범위·성공 기준
- **의도**: Toxicity 단계(7단계 §3) 도구 확보
- **성공 기준**: SSTR2 타겟 펩타이드에 적용 가능한 ADMET 도구 결정
- **요청 분류**: 연구·실험 + 기능

---

## ② 대응 방법 (Computer Science Method)

### 선택한 접근
- **로컬 마이그레이션**: pepADMET clone → 자체 GPU에서 추론
- **wrapper 통합**: `predict_admet_pepadmet.py` + `predict_admet_ai_wrapper.py` (ADMET-AI 보완)
- **OOD 가드**: `pipeline_local/pepadmet_ood/ood_detection.py` — 학습 도메인 밖 경고

### 알고리즘·파이프라인
1. ensemble_router가 후보를 도메인 분류 (L-AA, D-AA, cyclic, DOTA)
2. Layer 3 (DOTA): ADMET-AI MD proxy `[STUB]`
3. Layer 1/2: pepADMET 또는 ADMET-AI 라이브 호출
4. binary_toxicity, hemolysis, cytotoxicity 종합

### 대안 / Trade-off
- **ADMETlab 3.0**: 웹 기반, MCP 연동 어려움, **차단된 환경에서 사용 불가**
- **ADMET-AI** (Stanford Swansonk lab): 로컬 가능, `[추정]` 라이선스·정확도 §5 검증
- **자체 학습 (pepADMET fine-tuning)**: GPU 부담 ↑, 정확도 ↑ 가능

---

## ③ 현재 구현된 기능 (근거 필수)

### 동작 코드
- `pipeline_local/scripts/predict_admet_pepadmet.py` (pepADMET 래퍼)
- `pipeline_local/scripts/predict_admet_ai_wrapper.py` (ADMET-AI 래퍼)
- `pipeline_local/scoring/composite_scorer.py` (`layer3_dota_admet_ai_md_proxy_stub` 함수)
- `_workspace/pepadmet_local/pepADMET/` (vendored repo)

### 라이브 검증
- BE `/api/admet/batch` 200 응답 ([확인] 본 점검 §4.1)
- 단위 테스트 `test_layer3_admet_ai.py` PASS

### 한계 (정직 명시)
- 🔴 **HTTP 403 차단**: 외부 ADMET 서비스 호출 시 차단됨 → 자체 모델 의존 강화 필요
- 🔴 **Layer 3 STUB**: 함수명 그대로 `layer3_dota_admet_ai_md_proxy_stub` → DOTA 라벨링 후보 평가 공백 (본 점검 P0)
- 🟡 **ADMET=1.00 OOD 위험** (audit §1.1 ④): PRST-001~004 ADMET binary_toxicity=1.00 — 절대 독성 판정 아닌 OOD 외삽 가능성. **in vitro 실측만이 확정 가능**
- 🟡 **pepADMET 자체 학습 평가 미완** — 데이터셋 규모·GPU·시간 산정 진행 중

### 데모 가능 여부
- 🟢 Tier 산정 + binary_toxicity 표시 가능
- 🔴 **Layer 3 STUB은 시연 시 명시적 경고 화면 권장** (서호성 의견의 "한계 노출 framework")

---

## ④ AI Scientist 관점 결과 · 향후 방향 · 단기 목표

### 연구 관점 의미
- 7단계 §3 Toxicity 필터의 **유일한 in silico 도구** — 부재 시 wet-lab 실측 의존
- ADMET=1.00 수치를 **약리학적 절대 판정으로 해석하지 않는 framework** 가 narrative v3 §5의 핵심 (audit §1.1 ④ 3 reviewer 공통 결론)

### 향후 방향 (§5 웹 검증 필요)
- **pepADMET** — `[추정]` GitHub repo 검증 + 학습 코드 평가 (§5 references/repos/)
- **ADMET-AI** (Stanford) — `[추정]` 공식 repo·논문 검증
- **ADMETlab 3.0** API — 차단 환경에서는 운영 불가 (정직 명시)
- **자체 학습 로드맵**: D-AA 데이터 ~수천 개 확보 시 fine-tuning 검토

### 단기 목표 (다음 회의까지)
1. pepADMET 자체 학습 데이터 요구사항·GPU·시간 산정 완료 (회의록 §4 A-03 단계 4)
2. Layer 3 STUB → 최소 구현 (DOTA 후보 OOD 경고만이라도 발행)
3. **AI 모델 출력이 in vitro 실측으로 정정되어야 함을 의뢰서·발표 자료에 명시**

### `[확인]` vs `[추정]` 분리
- `[확인]` pepADMET wrapper 동작, BE 응답
- `[확인]` Layer 3 STUB 코드 위치
- `[추정]` pepADMET 자체 학습 시 정확도 향상 — §5 검증
- `[추정]` ADMET-AI 라이선스·D-AA 처리 가능성 — `확인 필요`

---

## ⑤ 한 줄 보고 요약
> pepADMET wrapper는 완성되었으나 **외부 API HTTP 403 차단** + **Layer 3 (DOTA proxy) STUB**으로 자체 학습 의사결정과 OOD 경고 framework 강화가 6월 회의 안건이다.

---

## 추적성 매핑
- 머지 PR: (wrapper) — 자체 학습 진행은 미커밋
- 핵심 파일: `pipeline_local/scripts/predict_admet_pepadmet.py`, `scoring/composite_scorer.py`
- 점검 증거: `inspect_evidence/silo_b_docking.md` §Layer3 STUB, `inspect_evidence/backend.md` §/api/admet
- 회의록 출처: PDF p.3 §2.2, p.7 §4 A-03
- 관련 Action Item: A-02 (Serum Stability — 단계 §2 인접), A-04 (Top-K 통합)
- 추가 자료: `docs/meet_log/2026-04-06_action_items/A-03_research_pepadmet_environment.md`, `A-03_pepadmet_author_email_draft.md`
