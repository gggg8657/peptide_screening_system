# A-10: SSTR3 도킹 에러 원인 분석 및 해결

**회의**: KAERI-AIRL-MOM-2026-003 (2026-04-06) | **담당**: AI팀 | **기한**: 5월 회의 전 | **상태**: ✅ PR #60 머지 (fix `5f5f7af`)

---

## ① 원본 요청 및 해석/분석

### 원문 (PDF §3 Action Items 표, p.5)
> "SSTR3 도킹 에러 원인 분석 및 해결" (A-01과 연동)

### 회의록 §4 A-10 수행 가이드 (p.9)
> "SSTR3 PDB 구조의 전처리 상태를 점검한다: 누락 잔기(missing residues), 충돌 원자(clashes), 비정상 B-factor 등을 확인한다. 필요 시 Modeller 또는 SWISS-MODEL로 누락 루프를 재구축한 뒤 에너지 최소화를 수행한다. 전처리 완료 후 SSTR2와 동일 프로토콜로 도킹을 재실행하여 결과를 확보한다."

### 회의록 §2.1 (p.2)
> "**기술적 이슈**: SSTR1/3/4번 병렬 처리 시도 중 시스템 오류가 발생하였으나 롤백 후 정상 진행 가능한 상태이다."

### 의도·범위·성공 기준
- **의도**: A-01 (위치 지정 도킹) 선행 조건 해소
- **성공 기준**: SSTR3 도킹 결과 확보
- **요청 분류**: 기능 + 운영

---

## ② 대응 방법 (Computer Science Method)

### 선택한 접근
- SSTR3 PDB 전처리 점검 (누락 잔기·충돌·B-factor)
- 필요시 Modeller / SWISS-MODEL 누락 루프 재구축
- 에너지 최소화 후 도킹 재실행

### 알고리즘·파이프라인
1. SSTR3 PDB 진단 (`pipeline_local/scripts/structure_io.py`)
2. 누락 잔기·충돌 원자 식별
3. 재구축 후 SSTR2 동일 프로토콜 도킹

### 대안 / Trade-off
- **Modeller** (licensed academic): 잘 알려진 도구, 라이선스
- **SWISS-MODEL** (free web): GUI, 자동
- **PyRosetta cleanup**: 우리 환경 내장, 신뢰

---

## ③ 현재 구현된 기능 (근거 필수)

### 동작 코드
- `pipeline_local/scripts/structure_io.py` (CIF/PDB 자동 감지 + sanitize)
- SSTR3 PDB 전처리 완료
- 도킹 재실행 결과 ([확인] MASTER_INDEX A-10 ✅)

### 라이브 검증
- PR #60 머지 (fix `5f5f7af`)
- 별건 회귀 BUG: **SSTR4 시그니처 `VILRYAKMKTA` SSTR1/SSTR4 중복 등록** — `_SSTR_SIGNATURES`에서 공유 모티프 제거되어 회귀 테스트 통과 (MASTER_INDEX 비고)

### 한계 (정직 명시)
- 🟢 거의 없음 — 머지·검증·회귀 테스트 모두 PASS
- 🟡 회귀 테스트 유지 필요

### 데모 가능 여부
- 🟢 SSTR3 도킹 결과 화면 시연 가능

---

## ④ AI Scientist 관점 결과 · 향후 방향 · 단기 목표

### 연구 관점 의미
- A-01 위치 지정 도킹 + selectivity 평가의 선행 조건 해소
- SSTR1/3/4/5 모두 정상 도킹 가능 상태 달성

### 향후 방향
- 회귀 테스트 유지 (`_SSTR_SIGNATURES` 검증 + SSTR3 PDB sanitize 검증)
- 다른 SSTR receptor PDB의 유사 결함 점검 (`확인 필요`)

### 단기 목표
- 특별한 추가 작업 없음 (유지 모드)

### `[확인]` vs `[추정]` 분리
- `[확인]` PR #60 머지, fix 검증
- `[확인]` SSTR4 회귀 별건 해결

---

## ⑤ 한 줄 보고 요약
> SSTR3 도킹 에러는 PR #60(fix `5f5f7af`)로 해결되었고, 별건 SSTR4 시그니처 중복 회귀도 해소되어 A-01의 위치 지정 도킹 선행 조건이 충족되었다.

---

## 추적성 매핑
- 머지 PR: **#60** (fix `5f5f7af`)
- 핵심 파일: `pipeline_local/scripts/structure_io.py`, `_SSTR_SIGNATURES` 정의 파일
- 회의록 출처: PDF p.5 §3 A-10, p.9 §4 A-10
- 관련 Action Item: A-01 (선행)
