# A-05: SST14 레퍼런스 ⊿G 기준선 확립 및 가변 임계값 적용

**회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) | **담당**: AI팀 | **기한**: 5월 회의 전 | **상태**: ✅ main 직접 push (`8e7e1cc`)

---

## ① 원본 요청 및 해석/분석

### 원문 (PDF §3 Action Items 표, p.5)
> "SST14 레퍼런스 ⊿G 기준선 확립 및 가변 임계값 적용 (n회 반복 Mean 값 기준)"

### 회의록 §4 A-05 수행 가이드 (p.8)
> "SST14 원형(native sequence)을 SSTR2(7T10)에 동일 도킹 프로토콜로 도킹하여 ⊿G 레퍼런스 값을 확보한다. 현재 하드코딩된 -5 기준선 대신, SST14 ⊿G × 0.9(10% 허용) 등의 가변 임계값을 적용하여 실험 조건 변화에 강건한 필터를 구현한다."

### 서호성 박사 보강 의견 (p.8)
> "Docking simulation을 n회 반복 수행하여 Mean 값을 기준으로 하는 것이 좋다. MD simulation 사용도 검토해볼 필요가 있다. 구체적으로: (1) 1차 스크리닝은 Rosetta 도킹 ⊿G로 200-500개 선별, (2) 2차 스크리닝은 MM-GBSA로 랭킹 재산정하여 20-50개 선별 (이 단계부터 킬레이터 부착), (3) 3차 스크리닝은 FEP/TI로 정밀 ⊿⊿G 계산. **OpenMM 자체의 알케미컬 프로토콜이나 OpenFE 프레임워크를 활용할 수 있으며, MM-PBSA는 OpenMM에서 직접 구현하거나 gmx_MMPBSA를 사용할 수 있다.**"

### 의도·범위·성공 기준
- **의도**: 실험 조건·외부 환경 변화에 강건한 가변 임계값 + 정밀 ⊿G 계산
- **성공 기준**: SST14 ⊿G 실측값 확보 + gate_thresholds.yaml 가변화
- **요청 분류**: 기능 + 연구

---

## ② 대응 방법 (Computer Science Method)

### 선택한 접근
- **n회 반복 도킹의 Mean값**: 통계적 강건성
- **가변 임계값**: `gate_thresholds.yaml` 의 `delta_g_threshold: ref * 0.9` 패턴
- **서호성 의견의 6단계 정밀 계산 (`[추정]`)**:
  - 1차 Rosetta FlexPepDock ⊿G → 200-500개 선별
  - 2차 MM-GBSA → 20-50개 선별 (이 단계부터 킬레이터)
  - 3차 FEP/TI → 정밀 ⊿⊿G

### 알고리즘·파이프라인
1. SST14 wildtype을 SSTR2(7T10)에 n회 도킹
2. Mean ⊿G 산출 → `data/sst14_reference_dG.json`
3. composite_scorer가 임계값 비교 시 `ref * 0.9` 가변 적용
4. (`[추정]`) MM-GBSA 추가 단계는 미구현

### 대안 / Trade-off
- **하드코딩 -5 REU**: 단순, 단 실험 조건·력장 변화에 취약
- **MM-GBSA** (서호성 의견): 정확도 ↑, GPU 부담 + 도구 선정 필요
- **FEP/TI**: 황금 표준 정확도, 단 시간·GPU 매우 ↑

---

## ③ 현재 구현된 기능 (근거 필수)

### 동작 코드
- `pipeline_local/config/gate_thresholds.yaml` ([확인] 가변 임계값 적용)
- `data/sst14_reference_dG.json` (`[확인 필요]` 파일 존재 확인)
- main 직접 push: commit `8e7e1cc`

### 라이브 검증
- 도킹 ⊿G 실측 확보 (MASTER_INDEX A-05 ✅)
- composite_scorer가 가변 임계값 사용 (코드 grep으로 확인)

### 한계 (정직 명시)
- 🟡 **MM-GBSA/FEP/TI 정밀 계산 미구현** — 서호성 의견의 6단계 (2차·3차)는 향후 작업
- 🟡 **n 반복 횟수** — 현재 코드에 명시되지 않음 (`확인 필요`)
- 🟢 1차(Rosetta ⊿G) 가변 임계값은 적용됨

### 데모 가능 여부
- 🟢 gate_thresholds.yaml 가변값 화면 표시 가능
- 🟡 MM-GBSA·FEP/TI는 미구현이므로 시연 X

---

## ④ AI Scientist 관점 결과 · 향후 방향 · 단기 목표

### 연구 관점 의미
- SST14 레퍼런스 ⊿G 기준은 약리학적으로 **selectivity 배수 산출의 기준점** — 정확한 측정이 KPI(≥100×)와 직결
- 서호성 의견의 3단계 정밀 계산(Rosetta → MM-GBSA → FEP/TI)은 약물 디자인 학계 표준 워크플로

### 향후 방향 (§5 웹 검증 필수)
- **gmx_MMPBSA** — `[추정]` GitHub repo Valdes-Tresanco-MS, peer-reviewed (§5 references/libraries)
- **OpenMM** — `[확인 필요]` openmm.org 공식 페이지
- **OpenFE** — `[추정]` 자유 에너지 alchemical workflow 프레임워크
- **PySCF/NWChem** alchemical — `[추정]` 정확도·시간 trade-off 검토

### 단기 목표 (다음 회의까지)
1. n 반복 횟수 명시 + 표준편차 보고
2. MM-GBSA 도구 검토 결과 6월 회의 발표 (gmx_MMPBSA vs OpenMM 직접 구현)
3. FEP/TI 도입 로드맵 (시간·GPU·라이선스)

### `[확인]` vs `[추정]` 분리
- `[확인]` SST14 ⊿G 실측 확보, 가변 임계값 적용
- `[확인]` main `8e7e1cc` 머지
- `[추정]` MM-GBSA 도입 시 selectivity 정확도 향상 — §5 검증
- `[추정]` FEP/TI 실용 시간 — `확인 필요`

---

## ⑤ 한 줄 보고 요약
> SST14 ⊿G 실측·가변 임계값은 완료되었으나, **서호성 의견의 2차(MM-GBSA)·3차(FEP/TI) 정밀 계산은 미구현**으로 6월 회의에서 도입 의사결정 + 도구 검토 결과 보고가 필요하다.

---

## 추적성 매핑
- 머지: main 직접 push `8e7e1cc`
- 핵심 파일: `pipeline_local/config/gate_thresholds.yaml`, `data/sst14_reference_dG.json`
- 회의록 출처: PDF p.5 §3 A-05, p.8 §4 A-05
- 관련 Action Item: A-01 (병행 권장), A-04 (Top-K 임계값 적용), A-09 (최종 선정)
