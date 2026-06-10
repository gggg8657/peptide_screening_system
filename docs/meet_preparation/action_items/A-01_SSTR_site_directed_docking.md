# A-01: SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹

**회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) | **담당**: AI팀 | **기한**: 5월 회의 전 | **상태**: ✅ PR #61 머지

---

## ① 원본 요청 및 해석/분석

### 원문 (PDF §3 Action Items 표, p.5)
> "SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹 수행 (SSTR3 에러 해결 포함)"

### 회의록 §2.1 배경 (p.2)
> "블라인드 도킹의 과도한 연산 시간 문제로 위치 지정(site-directed) 결합 방식 도입이 논의되었다. SSTR2의 결합 포켓 위치가 cryo-EM 구조(7T10/7T11)에서 명확히 규정되어 있으므로, 다른 서브타입에서도 상동 위치를 지정하면 정확도와 속도를 동시에 개선할 수 있다."

### 의도·범위·전제·성공 기준
- **의도**: 블라인드 → 위치 지정으로 docking 정확도·속도 동시 개선
- **전제**: SSTR2(7T10/7T11) cryo-EM 결합 포켓을 4종 서브타입(SSTR1/3/4/5)에 구조 정렬로 전사 가능
- **성공 기준**: 셀렉티비티 ≥100× 최소 / ≥300× 권장 (전략 보고서 KPI)
- **요청 분류**: 기능 + 연구·실험

### 서호성 박사 보강 의견 (p.2, §2.1)
> "SSTR2 결합 영역은 2.1절의 ECL/TM 핵심 잔기 표를 기준으로 설정하되, 77-314 범위로 한정하는 것이 합리적이다. 핵심 잔기 정보를 네거티브 디자인의 정량적 근거로 활용한다."

---

## ② 대응 방법 (Computer Science Method)

### 선택한 접근
- **구조 정렬(structural alignment)** + **포켓 중심 좌표 추출**
- PyMOL `cealign` 또는 TM-align 활용
- 결합 포켓 중심 ± **15-20Å 범위**를 도킹 검색 영역으로 설정

### 알고리즘·파이프라인
1. SSTR2(7T10/7XNA) 결합 포켓 중심 좌표 추출 (Trp-Lys 모티프 인접 영역)
2. SSTR1/3/4/5의 cryo-EM/AlphaFold 구조를 SSTR2에 cealign
3. 상동 포켓 좌표 결정 → `binding_pocket_<SSTR>.json` 저장
4. SSTR3 에러(A-10 선행) 해결 후 재도킹
5. SSTR2 레퍼런스 ΔG 대비 셀렉티비티 배수 산출

### 대안 / Trade-off
- **블라인드 도킹**: 정확도 ↑ 가능성, 속도 ↓ (현 25분 SLA 미완의 원인)
- **AutoDock-GPU**: GNINA, 라이선스·재현성 검토 필요 (`[추정]` — §5 검증 대상)
- **Boltz-2 자동 포켓**: 수동 좌표 불필요, 단 FlexPepDock legacy 미지원

---

## ③ 현재 구현된 기능 (근거 필수)

### 동작 코드
- `pipeline_local/scripts/extract_binding_pocket.py` (포켓 추출)
- `pipeline_local/core/selectivity_runner.py` (셀렉티비티 러너)
- `pipeline_local/scoring/composite_scorer.py` (Tier 시스템 + 셀렉티비티 통합)
- `data/somatostatin_receptor/binding_pocket_SSTR{1,2,3,4,5}.json` (좌표 파일)

### 라이브 검증
- BE 라우터 `GET /api/binding_pocket/{receptor}` 등록·응답 확인 (본 점검 §4.1)
- FE `BindingPocketPage` 통해 좌표 시각·편집 가능 (본 점검 §4.2)

### 한계 (정직 명시)
- **로컬 PDB ID와 회의록 PDB ID 불일치** — 회의록은 7T10 명시하나 로컬은 `SSTR2_7XNA.pdb`. 도킹 자체는 7XNA로 수행되어 KPI 셀렉티비티 배수 해석에 영향 가능
- **본 점검에서 발견된 K-1/K-2 selectivity 결함**(`_build_pdb_index` 정렬 + `candidate_pdb` 미전달) — 모든 후보가 동일 off-target 결과 → A-01의 출력 신뢰성 위협

### 데모 가능 여부
- 🟢 **정적 시연 가능**: 좌표 JSON + Mol* 3D 표시
- 🟡 **라이브 도킹**: Step05 Boltz가 후보당 30~40s → demo subset(작은 N)만 가능

---

## ④ AI Scientist 관점 결과 · 향후 방향 · 단기 목표

### 연구 관점 의미
- 위치 지정 도킹은 **네거티브 디자인**(off-target 회피)의 정량 기반. 셀렉티비티 ≥100× KPI 달성은 약리학적으로 유의미.
- 회의록 §2.1 인용 논문 2종 (`[확인 필요]` §5 웹 검증):
  - "Interaction of Radiopharmaceuticals with Somatostatin Receptor 2 Revealed by Molecular Dynamics Simulations" (2023, JCIM)
  - "Exploring key features of selectivity in somatostatin receptors through molecular dynamics simulations" (2024, CSBJ)

### 단기 목표 (다음 회의까지)
1. 회의록의 7T10 vs 로컬 7XNA 구조 ID 정합 결정
2. **K-1/K-2 selectivity 결함 정정** (본 점검 신규 P0 발견)
3. 셀렉티비티 ≥100× KPI 충족 후보 데이터 정리

### `[확인]` vs `[추정]` 분리
- `[확인]` PR #61 머지, binding_pocket JSON 5종 존재
- `[추정]` 7T10/7XNA 차이가 KPI 해석에 미치는 영향 크기 — `확인 필요`
- `[추정]` MD 보정 시 정확도 향상 정도 — §5 references/papers 검증 대상

---

## ⑤ 한 줄 보고 요약
> SSTR1/3/4/5 위치 지정 도킹은 PR #61로 머지 완료되었으나, **회의록 7T10 vs 로컬 7XNA 구조 ID 불일치**와 **본 점검 신규 발견 K-1/K-2 selectivity 결함**으로 출력 신뢰성 정정이 6월 회의 전 필요하다.

---

## 추적성 매핑
- 머지 PR: **#61** (10 files, +43K)
- 핵심 파일: `pipeline_local/scripts/extract_binding_pocket.py`, `core/selectivity_runner.py`
- 점검 증거: `inspect_evidence/backend.md` §라우터, `inspect_evidence/silo_b_docking.md`
- 회의록 출처: PDF p.2 §2.1, p.5 §3 A-01
- 관련 Action Item: A-05 (레퍼런스 ΔG), A-10 (SSTR3 에러 — 선행)
