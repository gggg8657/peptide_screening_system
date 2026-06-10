# A-09: 최종 후보 3-4개 도출 및 합성 의뢰 준비 (파이프라인 1차 완전 실행)

**회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) | **담당**: 전체 | **기한**: 연속 | **상태**: ✅ PR #63 머지 (PRST-001~004)

---

## ① 원본 요청 및 해석/분석

### 원문 (PDF §3 Action Items 표, p.5)
> "최종 후보 3-4개 도출 및 합성 의뢰 준비 (파이프라인 1차 완전 실행)"

### 회의록 §4 A-09 수행 가이드 (p.9)
1. A-04의 복합 스코어링 체계가 확립되면, 현재까지 생성된 전체 후보 라이브러리에 적용하여 Top-K를 선정한다.
2. Top-K 중 합성 가능성(비천연 아미노산 조달, 고리화 전략, 예상 합성 수율)을 RI 팀과 협의하여 최종 3-4개를 확정한다.
3. 합성 의뢰서(서열, 수식 위치, 순도 기준, 납기)를 작성한다. 국내 DOTA/DFO 킬레이터 합성 벤더 선정(MOM-002 A-10)과 연동한다.

### 의도·범위·성공 기준
- **의도**: in silico → wet lab 첫 닫힌 사이클
- **성공 기준**: 3-4개 후보 + 합성 의뢰서 + 벤더 확정
- **요청 분류**: 기능 + 연구·실험 + 운영

---

## ② 대응 방법 (Computer Science Method)

### 선택한 접근
- A-04 Tier 시스템(S/A/B/FAIL) 적용 → Tier S 후보 선별
- PRST-001~004 (4종) 합성 의뢰서 작성

### 알고리즘·파이프라인
1. `runs_local/dual_final_03/local_20260402_1055_iter01/` 운영
2. composite_scorer Tier S 선별 → 4종 후보
3. RI 팀 협의 → 합성 가능성 확인
4. 합성 의뢰서: 서열·수식 위치·순도·납기·DOTA 킬레이터

### 대안 / Trade-off
- 후보 수 3 vs 4 vs 5: 실험 부담 vs 다양성
- **Tier S만 vs Tier S+A**: 보수성 vs 발견 확률

---

## ③ 현재 구현된 기능 (근거 필수)

### 동작 결과
- **PRST-001~004 도출 완료** ([확인] PR #63 머지)
  - PRST-001 Tier S, AGCKNIIWKTITSC, WSS=1.000, ⊿G=-105.5 REU
  - PRST-002~004 동일 디렉토리 (`runs_local/dual_final_03/`)
- **합성 의뢰서 작성 완료** ([확인])

### 라이브 검증
- FE `/candidate/:id` (PRST-001~004) 라이브 페이지 ([확인] 본 점검 §4.2)
- Mol* 3D 표시 + Selectivity Explorer SSTR1/3/4/5 ⊿G 비교

### 한계 (정직 명시)
- 🔴 **wet-lab 미시작** — 합성 의뢰서는 작성되었으나 실제 합성·assay는 진행 전
- 🔴 **ADMET=1.00 OOD 위험**: 모든 PRST 후보의 binary_toxicity=1.00은 절대 독성 판정이 아니며 OOD 외삽 가능성. **in vitro 실측만이 확정** (audit §1.1 ④, 서호성 의견)
- 🟡 **K-1/K-2 selectivity 결함** 영향 — 모든 후보가 동일 off-target → ranking 재검증 필요 (본 점검 신규 발견)
- 🟡 **Layer 3 STUB**으로 DOTA 종합 평가 공백

### 데모 가능 여부
- 🟢 PRST-001~004 화면 시연 가능 (Mol* + selectivity matrix)
- 🟡 "한계 명시" 화면 제공 권장 (서호성 의견의 framework)

---

## ④ AI Scientist 관점 결과 · 향후 방향 · 단기 목표

### 연구 관점 의미
- 본 프로젝트의 **첫 in silico → wet lab 사이클 도달** — 단, 본 보고는 후보 도출까지이고 KPI는 wet lab 결과
- ADMET=1.00은 framework가 "한계 노출"한 결과 — 단일 모델 출력 과신 방지

### 향후 방향
- **wet-lab 실측**: 합성 + binding affinity (Ki) + Selectivity + Serum Stability + Hemolysis
- **K-1/K-2 정정 후 ranking 재검증** → 가능한 경우 PRST-005~XXX 추가 후보 도출
- **RI 표지(¹⁷⁷Lu) 후 Radiolysis assay**: 회의록 §A-04 Radiolysis Quencher DOE 활용 (서호성 의견)

### 단기 목표 (다음 회의까지)
1. 합성 ETA 확정 (KAERI 자체 합성 vs 벤더)
2. binding affinity assay 설계 (Ki 측정 프로토콜)
3. K-1/K-2 selectivity 정정 후 PRST ranking 재검증
4. wet-lab 결과 보고 시점 합의

### `[확인]` vs `[추정]` 분리
- `[확인]` PRST-001~004 도출, 합성 의뢰서 작성
- `[확인]` PRST 후보 화면 시연 가능
- `[추정]` wet-lab 결과 — 미실시
- `[추정]` ADMET=1.00의 실제 독성 — `in vitro 실측 필요`

---

## ⑤ 한 줄 보고 요약
> PRST-001~004 후보 + 합성 의뢰서는 PR #63으로 완료되었으나, **wet-lab 미시작 + K-1/K-2 selectivity 결함이 ranking 신뢰성 위협 + ADMET=1.00 OOD 위험**으로 in vitro 병행 + ranking 정정이 6월 회의 안건이다.

---

## 추적성 매핑
- 머지 PR: **#63** (PRST-001~004)
- 핵심 자료: `runs_local/dual_final_03/local_20260402_1055_iter01/`, 합성 의뢰서
- 점검 증거: `inspect_evidence/silo_b_docking.md` §최근 실행 흔적, `daily_system_inspection_report_20260601.md` §4.10
- 회의록 출처: PDF p.5 §3 A-09, p.9 §4 A-09
- 관련 Action Item: A-04 (Top-K 스코어링), A-02·A-03 (ADMET/반감기 입력)
