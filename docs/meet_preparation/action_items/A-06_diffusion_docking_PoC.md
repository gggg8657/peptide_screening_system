# A-06: 디퓨전 모델 기반 도킹 가속화 PoC 수행 (정확도 vs Rosetta 비교)

**회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) | **담당**: AI팀 | **기한**: 5월 회의 전 | **상태**: 🟡 스크립트 존재, 완성도 미확인

---

## ① 원본 요청 및 해석/분석

### 원문 (PDF §3 Action Items 표, p.5)
> "디퓨전 모델 기반 도킹 가속화 PoC 수행 (정확도 vs Rosetta 비교)"

### 회의록 §2.4 배경 (p.4)
> "생성형 AI(디퓨전 모델)를 활용한 도킹 시뮬레이션 속도 개선 가능성이 논의되었다. **Rosetta 대비 약 10배 빠른 속도가 기대되나, 정확도 및 신뢰도 검증이 선행되어야 한다.** GPU VRAM 120GB 이상 사양이 필요하여 DGX 전용 서버 구매 또는 기존 PC 업그레이드 방안이 검토되었다."

### 회의록 §4 A-06 수행 가이드 (p.8-9)
1. DiffDock 또는 유사 디퓨전 기반 도킹 모델을 선정한다.
2. SSTR2-SST14 복합체(7T10)를 ground truth로 두고, 디퓨전 모델의 예측 포즈 vs cryo-EM 포즈의 RMSD를 비교한다.
3. Rosetta FlexPepDock 과의 속도 비교(wall-clock time per candidate)를 수행한다.
4. RMSD 2.0Å 이내 재현율이 80% 이상이면 파이프라인 1차 필터로 도입을 검토한다.
> **GPU 요구사항**: VRAM 120GB 이상 필요. 현재 H100 8장 서버에서 가능 여부를 먼저 확인하고, 불가 시 A-07의 DGX 검토와 연동한다.

### 의도·범위·성공 기준
- **의도**: Step05 Boltz 25분 SLA 미완(본 점검 발견)의 근본 해결
- **성공 기준**: RMSD 2.0Å 재현율 ≥80% + 속도 10배 개선 확인
- **요청 분류**: 연구·실험 + 기능

---

## ② 대응 방법 (Computer Science Method)

### 선택한 접근
- **DiffDock**(`[추정]` Corso et al. 2023 — §5 검증 필수)
- **AlphaFold3-style docking** 가능성 검토 (`[추정]` Boltz-2가 이미 일부 역할)
- **RMSD ≤2.0Å 재현율** 표준 평가 지표

### 알고리즘·파이프라인
1. SSTR2-SST14(7T10) ground truth 확보
2. DiffDock 또는 Boltz-2 docking → 예측 pose
3. PyMOL/PyRosetta RMSD 계산
4. Rosetta FlexPepDock와 wall-clock time 비교
5. RMSD ≤2.0Å 80% 충족 시 1차 필터 후보

### 대안 / Trade-off
- **DiffPepBuilder**: 본 점검에서 비활성(`step05_docking.py:144`) — Boltz-2 단독으로 대체된 상태
- **Boltz-2**: 이미 primary 엔진 — A-06의 "디퓨전" 정의에 부합 가능 `[추정]`
- **GNINA**: AutoDock 기반, 디퓨전 아님

---

## ③ 현재 구현된 기능 (근거 필수)

### 동작 코드
- `pipeline_local/wrapper_scripts/run_diffpepbuilder.py` (스크립트 존재)
- `pipeline_local/wrapper_scripts/run_boltz.py` (Boltz-2 — 실제 운영)
- `pipeline_local/steps/step05c_boltz_cross.py` (cross-validation)

### 라이브 검증
- Boltz-2 모델 4.4 GB 로드 가능 ([확인])
- `step05_docking.py:144` DiffPepBuilder 주석 처리 ([확인] 본 점검 silo_b_docking 에이전트 발견)

### 한계 (정직 명시)
- 🔴 **DiffDock 본격 PoC 미수행** — RMSD·속도 비교 보고서 부재
- 🔴 **DiffPepBuilder 비활성화** (step05:144) — 디퓨전 엔진은 사실상 Boltz-2 단독
- 🟡 **GPU VRAM 120GB 충족 여부** — 현재 H100×8 (NVL 95GB×4) 환경에서 본격 학습·추론 가능성 미확인
- 🟡 회의록의 "디퓨전" 정의에 Boltz-2를 포함시킬 수 있는지 `확인 필요`

### 데모 가능 여부
- 🟢 Boltz-2 단건 도킹 라이브 시연 (~10초, demo scenario §Step 3)
- 🔴 **DiffDock vs Rosetta PoC 결과 시연 불가**

---

## ④ AI Scientist 관점 결과 · 향후 방향 · 단기 목표

### 연구 관점 의미
- Step05 Boltz 25분 SLA 미완(audit) → 디퓨전 가속화는 **E2E pipeline 라이브 시연 가능성을 결정하는 핵심 요인**
- RMSD ≤2.0Å는 약물 디자인 공인 기준 — 충족 시 신뢰 가능

### 향후 방향 (§5 웹 검증 필수)
- **DiffDock** — `[추정]` Corso et al. 2023 arXiv:2210.01776 (§5 검증)
- **Boltz-2** — `[확인]` 이미 운영 중
- **AlphaFold3** — `[추정]` Deepmind 최신 모델, 라이선스 검토 (§5 검증)

### 단기 목표 (다음 회의까지)
1. **DiffDock 본격 PoC 1회 실행** — SSTR2-SST14 RMSD 계산
2. Rosetta vs DiffDock wall-clock time 측정 → 회의 자료
3. A-07 GPU 견적과 연동: VRAM 120GB 충족 여부 결정

### `[확인]` vs `[추정]` 분리
- `[확인]` Boltz-2 운영, DiffPepBuilder 비활성
- `[추정]` DiffDock 10배 속도 — `확인 필요` (실제 측정 부재)
- `[추정]` Boltz-2가 회의록의 "디퓨전 모델" 정의를 충족하는지

---

## ⑤ 한 줄 보고 요약
> 디퓨전 도킹 PoC는 **DiffDock 본격 실행이 미완**이며 DiffPepBuilder가 비활성화되어 사실상 Boltz-2 단독 운영 중이라, 회의록 KPI(RMSD ≤2.0Å 80%, 10배 가속) 미충족 — 6월 회의 전 1회 본 PoC가 필요하다.

---

## 추적성 매핑
- 머지 PR: — (PoC 미완)
- 핵심 파일: `pipeline_local/wrapper_scripts/run_diffpepbuilder.py` (보류), `run_boltz.py` (운영)
- 점검 증거: `inspect_evidence/silo_b_docking.md` §3 (DiffPepBuilder 비활성)
- 회의록 출처: PDF p.4 §2.4, p.8-9 §4 A-06
- 관련 Action Item: A-07 (GPU), A-01 (위치 지정 도킹의 가속화)
