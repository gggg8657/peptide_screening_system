# 2026-05-28 회의 발표 narrative v3
> **작성일**: 2026-05-27  
> **작성자**: 김동주 (KAERI AI-RI Lab)  
> **원본 회의록**: `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf`  
> **회의 코드**: KAERI-AIRL-MOM-2026-003 (제3차 월간회의, 2026-04-06)  
> **목적**: 4월 회의에서 발생한 9개 Action Item의 수행 결과, 미충족 항목의 원인, 5월 28일 회의에서 결정이 필요한 사항을 정리한다.

---

## 1. 프로젝트의 현재 위치
SST-14 기반 SSTR2 표적 방사성의약품 후보를 계산 단계에서 선별하고, ¹⁷⁷Lu 표지와 Gate-2 실험으로 넘길 수 있는 3~4개 후보를 도출하는 것이 현재 파이프라인의 목적이다.
4월 회의는 이 목적을 위해 세 가지 병목을 명확히 했다.
첫째, SSTR1/3/4/5까지 포함한 site-directed docking과 selectivity 평가가 필요하다.
둘째, ΔG 단일 기준에서 벗어나 serum stability, ADMET, radiolysis, selectivity를 포함한 복합 스코어링으로 이동해야 한다.
셋째, diffusion docking과 고성능 GPU 인프라가 실제 병목을 줄이는지 별도 PoC가 필요하다.
회의록은 이를 다음과 같이 요약했다.
> "본 제3차 월간 회의에서는 지난 회의(2026-03-23, MOM-002) 이후 달성된 주요 진전 사항을 점검하고, 향후 파이프라인 고도화 방향을 논의하였다."
> — 회의록 §1
> "주요 이슈로는 ADMET/혈청 반감기 예측 모델의 정확도 한계, Top-K 후보 선정 기준의 체계화(현재 ΔG 과의존 문제), 디퓨전 모델 기반 도킹 가속화를 위한 고성능 GPU 인프라 확보 필요성이 논의되었다."
> — 회의록 §1
또한 4월 회의에서 다음 7단계 선별 체계가 확정되었다.
> "또한 서호성 박사의 제안으로 7단계 다단계 선별 체계(Specificity → Serum Stability → Toxicity → Lead 확정 → AA Modification → RI-MD simulation → 기타 예측)가 확정되었다."
> — 회의록 §1
이 7단계는 이번 발표의 기준 축이다.
1. SSTR2 specificity: Rosetta/FlexPepDock 및 selectivity 기반 1차 선별.
2. Serum stability: ProtParam 및 대체 도구, 이후 MD 기반 stability 검토.
3. Toxicity: pepADMET 또는 대체 ADMET 모델.
4. Lead compound 확정: WSS와 Pareto front 기반 최종 후보 도출.
5. Amino acid modification: radiolysis 민감 잔기 및 SS bond 안정성 중심 변형.
6. RI 표지 후 MD simulation: MM-GBSA, FEP/TI, 표지 후 구조 안정성.
7. 기타 예측: 제형 안정성, RCY/RCP, 실험 패키지 조건.
5월 회의의 핵심은 "어디까지 계산으로 닫혔는가"와 "어디부터 실측 또는 외부 도구가 필요한가"를 구분하는 것이다.

---

## 2. 4월 회의 원문 기준 주요 요구
4월 회의록 §3은 A-01부터 A-10까지의 Action Item을 제시했다. A-08은 회의 당일 삭제 처리되었으므로 실제 신규 과제는 9건이다.
이번 한 달의 수행 결과를 상태별로 먼저 요약하면 다음과 같다.
- 충족: A-01, A-04, A-05, A-06, A-09, A-10.
- 부분 충족: A-02, A-03.
- 외부 진행 대기: A-07.
- 삭제 정합: A-08.
부분 충족 항목 두 건은 모두 D-AA, cyclic peptide, DOTA 또는 비천연 AA가 기존 in silico ADMET/half-life 도구의 학습 범위 밖에 놓이는 문제와 연결된다.
따라서 5월 회의의 판단 지점은 "계산 결과를 신뢰한다/불신한다"가 아니라, 각 결과의 적용 범위를 어떻게 제한하고 어떤 실측을 병행할지이다.

---

## 3. 9개 Action Item별 수행 결과

### A-01 — SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹
**회의 원문**
> "SSTR1/3/4/5 위치 지정 도킹 좌표 확정 및 재도킹 수행 (SSTR3 에러 해결 포함). 담당: AI팀. 기한: 5월 회의 전. 상태: 신규."
> — 회의록 §3
> "블라인드 도킹은 전체 수용체 표면을 탐색하므로 연산 시간이 과도하다. SSTR2의 결합 포켓 위치가 cryo-EM 구조(7T10/7T11)에서 명확히 규정되어 있으므로, 다른 서브타입에서도 상동 위치를 지정하면 정확도와 속도를 동시에 개선할 수 있다."
> — 회의록 §4 A-01
**수행 내용**
SSTR2 기준 구조는 로컬 배치된 `7XNA`를 사용했다. 회의록 원문은 7T10/7T11을 언급하지만, 로컬 파이프라인 입력은 7XNA 기준으로 정리되어 있었다.
SSTR2 결합 포켓 중심 좌표를 추출해 `binding_pocket_SSTR2.json`에 고정했다.
좌표값은 (-5.595, -28.626, 52.210), 탐색 반경 13 Å, 박스 크기 26.1 Å이다.
SSTR1/3/4/5 구조는 SSTR2에 구조 정렬했다. 회의에서는 TM-align 또는 cealign을 제안했고, 현재 환경에서는 PyMOL cealign을 사용했다.
정렬 RMSD는 다음과 같다.
| 서브타입 | RMSD |
|---------|------|
| SSTR1 | 3.125 Å |
| SSTR3 | 3.086 Å |
| SSTR4 | 3.019 Å |
| SSTR5 | 2.770 Å |
모두 회의 KPI인 4 Å 이내에 들어온다.
SSTR3 도킹 에러는 A-10의 chain 선택 로직 수정과 연동하여 해결했다.
**산출물**
- PR #61 main merge.
- `binding_pocket_SSTR2.json`.
- SSTR1/3/4/5 aligned PDB.
- `selectivity_runner.py` 인터페이스 반영.
- 관련 테스트 38건 통과.
**현재 상태**
충족. 단, TM-align이 아니라 cealign을 사용한 점은 도구 변경으로 보고한다.

---

### A-02 — 혈청 반감기 예측 도구 비교 조사
**회의 원문**
> "혈청 반감기 예측 도구 비교 조사 (벤치마크 세트 기반 정확도 평가). 담당: AI팀/RI팀. 기한: 5월 회의 전. 상태: 신규."
> — 회의록 §3
> "SST14 기반 펩타이드의 최대 약점은 극히 짧은 체내 반감기이다 (일반적으로 3분 이내에 분해). 전략 보고서의 KPI(TPP-B ≥24h, TPP-C ≥72h)를 계산 단계에서 선별하려면 신뢰할 수 있는 in silico 반감기 예측 도구가 필수이다."
> — 회의록 §4 A-02
> "[서호성 의견] 보다 정밀한 Serum Stability 혹은 인체 반감기 측정 프로그램을 찾아 사용할 필요가 있으며, 특히 D-Phe 등 변형된 아미노산을 분석할 수 있으면 더욱 바람직하다."
> — 회의록 §4 A-02
**수행 내용**
ProtParam, HLP, PlifePred, PeptideRanker, PeptideStability, pepMSND, CAMSOL 등 7종을 비교 대상으로 정리했다.
벤치마크 세트는 SST-14, Octreotide, Lanreotide, RC-160을 중심으로 구성했다.
회의 요구인 "5종 이상 비교"는 충족했다.
그러나 핵심 요구였던 D-AA 처리 가능성에서는 지원 도구가 확인되지 않았다.
Octreotide 테스트에서 D-AA 및 terminal modification을 제대로 반영하지 못하면 half-life가 4.83배 과대 추정될 수 있음을 확인했다.
D-AA는 protease recognition을 회피해 serum stability를 높이는 설계 축이지만, 서열 기반 도구가 이를 L-AA처럼 처리하면 이 효과를 반대로 왜곡하거나 과대평가할 수 있다.
**산출물**
- A-02 도구 비교 문서.
- `predict_halflife_pepmsnd.py` wrapper.
- `ENDPOINT_CONFIDENCE` 혈청 반감기 항목 7개 등록.
- D-AA 미지원 경고 반영.
**현재 상태**
도구 비교는 충족. D-AA half-life 예측 도구 확보는 미충족.
이 항목은 계산값을 합성 go/no-go 기준으로 쓰기 어렵고, wet-lab serum stability 측정을 병행해야 한다.

---

### A-03 — Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가
**회의 원문**
> "Fab-ADMET 정확도 검증 및 자체 학습 가능성 평가. 담당: AI팀. 기한: 5월 회의 전. 상태: 신규."
> — 회의록 §3
> "(추가적인 학습에 대한 김동주 선생님의 의견!!)"
> — 회의록 §2.2
**수행 내용**
회의록의 "Fab-ADMET" 표기는 실제 도구명 기준 pepADMET으로 정정했다.
pepADMET은 Tan et al. 2026 JCIM의 peptide ADMET 플랫폼이며, GitHub 저장소는 GPL-3.0, 웹 플랫폼은 CC BY-NC-SA 4.0 조건이다.
공개 정보 기준으로 29개 endpoint를 제공하며, toxicity endpoint는 AUC 0.949로 보고되어 있다. 다만 전문 접근과 endpoint별 재현은 별도 확인이 필요하다.
적용 가능성은 다음과 같이 나뉜다.
| 항목 | 판단 |
|------|------|
| SST-14 L-AA 서열 | 적용 가능 |
| cyclic peptide | 조건부 가능 |
| D-Phe/D-Trp/D-Nal 등 D-AA·비천연 AA | 공식 지원 미명시 |
| DOTA 결합 후보 | 적용 불가 또는 OOD 가능성 큼 |
| 자체 fine-tuning | 코드상 가능하나 데이터 필요 |
pepADMET REST API 자동 호출은 HTTP 403으로 차단되었다.
로컬 설치는 일부 진행되었으나, 최종 운영 수준의 자동화는 완료되지 않았다.
PRST 후보의 `binary_toxicity=1.00`은 절대 독성 판정으로 해석하지 않는다. D-AA, cyclic, DOTA가 포함된 후보는 학습 분포 밖(OOD)일 가능성이 크기 때문이다.
**산출물**
- A-03 조사 보고서.
- pepADMET 명칭 정정 기록.
- pepADMET 저자 문의 이메일 초안.
- ADMET 도구 신뢰도 등급 및 H-06 경고 반영.
**현재 상태**
명칭 정정과 적용 가능성 평가는 충족. PRST 후보의 ADMET 의사결정 모델 확보는 미충족.

---

### A-04 — Top-K 후보 선정 복합 스코어링 체계 설계
**회의 원문**
> "Top-K 후보 선정 복합 스코어링 체계 설계 (ΔG + 반감기 + 셀렉티비티 + ADMET 통합). 담당: AI팀/RI팀. 기한: 5월 회의 전. 상태: 신규."
> — 회의록 §3
> "현재 ΔG 단일 지표에 의존하는 후보 선정은 반감기가 극도로 짧거나 ADMET 프로파일이 불량한 후보를 통과시킬 위험이 있다. 전략 보고서의 13-metric panel에 기반한 복합 스코어가 필요하다."
> — 회의록 §4 A-04
> "Hard cutoff 통과 후보에 대해 가중 합산 스코어(weighted sum) 또는 Pareto front 방식으로 순위 결정. 가중치는 TPP별 우선순위에 따라 차등 적용."
> — 회의록 §4 A-04
**수행 내용**
Hard Cutoff 5개를 정의했다.
| 지표 | 기준 |
|------|------|
| ΔG | SST-14 reference ΔG 기준 |
| Selectivity | ≥100× |
| Radiolysis-sensitive residue | ≤3개 |
| ADMET toxicity | ≤0.3 |
| Instability Index | <40 |
Hard Cutoff 통과 후보에 대해 WSS와 Pareto front를 병행한다.
WSS 기본 가중치는 ΔG 0.35, selectivity 0.25, half-life 0.20, ADMET 0.10, radiolysis 0.10이다.
Tier 체계는 S/A/B/FAIL이다.
PR #62 commit 제목에 "S/A/B/C"가 들어간 적이 있으나, 실제 코드는 `Tier.S / Tier.A / Tier.B / Tier.FAIL`이다.
**산출물**
- `pipeline_local/scoring/composite_scorer.py`.
- `pipeline_local/scoring/radiolysis_scorer.py`.
- PR #62 main merge.
- 테스트 73건 통과.
**현재 상태**
충족.

---

### A-05 — SST14 레퍼런스 ΔG 기준선 확립
**회의 원문**
> "SST14 레퍼런스 ΔG 기준선 확립 및 가변 임계값 적용 (n회 반복 Mean 값 기준). 담당: AI팀. 기한: 5월 회의 전. 상태: 신규."
> — 회의록 §3
> "SST14 원형(native sequence)을 SSTR2(7T10)에 동일 도킹 프로토콜로 도킹하여 ΔG 레퍼런스 값을 확보한다. 현재 하드코딩된 -5 기준선 대신, SST14 ΔG × 0.9(10% 허용) 등의 가변 임계값을 적용하여 실험 조건 변화에 강건한 필터를 구현한다."
> — 회의록 §4 A-05
> "[서호성 의견] Docking simulation을 n회 반복 수행하여 Mean 값을 기준으로 하는 것이 좋다."
> — 회의록 §4 A-05
**수행 내용**
SST-14 원형을 SSTR2에 동일 프로토콜로 반복 도킹했다.
FlexPepDock 기준 평균 ΔG는 **553.857 REU**, 표준편차는 **σ=4.024 REU**이다.
KPI인 σ<5를 충족했다.
Boltz-2 비교 실행에서는 ΔG **-95.024 REU**가 산출되었다.
FlexPepDock REU와 Boltz-2 값은 단위와 스케일이 다르므로 직접 비교하지 않는다.
`gate_thresholds.yaml`에는 `rosetta_ddg_max = 498.4713`이 반영되었다 (553.857 × 0.9, 회의에서 제안된 10% 허용 가변 임계값).
**산출물**
- main commit `8e7e1cc`.
- `pharmacology_guards.py::LITERATURE_VALUES` 등록.
- tool-specific reference ΔG 적용.
**현재 상태**
충족. 단, SST-14:SSTR2 복합체 cryo-EM ground truth가 공개되어 있지 않아 absolute pose validation에는 한계가 있다.

---

### A-06 — 디퓨전 모델 기반 도킹 가속화 PoC
**회의 원문**
> "디퓨전 모델 기반 도킹 가속화 PoC 수행 (정확도 vs Rosetta 비교). 담당: AI팀. 기한: 5월 회의 전. 상태: 신규."
> — 회의록 §3
> "Rosetta 대비 약 10배 빠른 속도가 기대되나, 정확도 및 신뢰도 검증이 선행되어야 한다. GPU VRAM 120GB 이상 사양이 필요하여 DGX 전용 서버 구매 또는 기존 PC 업그레이드 방안이 검토되었다."
> — 회의록 §2.4
> "RMSD 2.0Å 이내 재현율이 80% 이상이면 파이프라인 1차 필터로 도입을 검토한다."
> — 회의록 §4 A-06
**수행 내용**
DiffPepDock을 검토 대상으로 두었다.
SSTR2-SST14 복합체의 실험 ground truth 부재로, 내부 reference pose와 비교하는 방식으로 평가했다.
핵심 한계는 SS bond 처리였다.
SST-14 및 PRST 후보는 Cys3-Cys14 SS bond가 구조의 기본 제약인데, DiffPepDock 입력 처리는 이 제약을 안정적으로 유지하지 못했다.
속도 측면의 이점은 있으나, 회의 KPI인 RMSD 2.0 Å 이내 재현율 80% 판단 기준을 충족하지 못했다.
GPU VRAM 120 GB 이상 요구도 A-07과 연결되는 병목으로 남았다.
**산출물**
- DiffPepDock 평가 보고.
- `HEURISTIC_FUNCTION_DISCLAIMERS`에 NOT_RECOMMENDED 사유 반영.
**현재 상태**
평가 완료. 현 단계 도입은 NOT_RECOMMENDED.

---

### A-07 — DGX/고성능 GPU 서버 구매 사양 및 비용 견적 수집
**회의 원문**
> "DGX/고성능 GPU 서버 구매 사양 및 비용 견적 수집. 담당: 서호성/안기범. 기한: 5월 회의 전. 상태: 신규."
> — 회의록 §3
> "NVIDIA DGX H100(80GB×8) 또는 DGX B200 등 옵션의 견적을 최소 2개 벤더로부터 수집한다. 비교 항목: VRAM 총량, NVLink 대역폭, 전력/냉각 요구사항, 납기, 유지보수 계약."
> — 회의록 §4 A-07
**수행 내용**
비교 매트릭스와 점검 양식은 작성했다.
비교 항목은 VRAM 총량, NVLink, 전력/냉각, 납기, 유지보수 계약, Desmond/FEP+/diffusion docking 연동 가능성으로 정리했다.
외부 벤더 견적 수집은 담당자 영역으로 남아 있다.
**현재 상태**
양식은 완료. 견적 수집은 회의에서 진행 상황 확인 필요.

---

### A-08 — 서버 마이그레이션
**회의 원문**
> "라이브러리 서버 마이그레이션 완료 및 검증. 상태: 삭제. 비고: 완료/불요."
> — 회의록 §3
> "외부망 서버 배포 완료로 본 항목은 삭제 처리한다."
> — 회의록 §4 A-08
**현재 상태**
회의록 결정과 정합. 별도 수행 없음.

---

### A-09 — 최종 후보 3~4개 도출 및 합성 의뢰 준비
**회의 원문**
> "최종 후보 3-4개 도출 및 합성 의뢰 준비 (파이프라인 1차 완전 실행). 담당: 전체. 기한: 연속. 상태: 신규."
> — 회의록 §3
> "회의에서 최종 후보 3-4개를 빠르게 도출하여 합성 및 실험 진행 필요성이 강조되었다. 전략 보고서의 Gate-1(계산) → Gate-2(표지/제조) 진행을 위한 핵심 마일스톤이다."
> — 회의록 §4 A-09
**수행 내용**
A-04 scoring을 전체 후보 라이브러리에 적용했다.
최종 후보는 PRST-001~004 네 개로 정리했다.
| 후보 | Tier | 핵심 정보 |
|------|------|----------|
| PRST-001 | S | AGCKNIIWKTITSC, WSS=1.000, ΔG=-105.5 REU, II=28.5 |
| PRST-002 | B | 합성 의뢰서 작성 |
| PRST-003 | B | 합성 의뢰서 작성 |
| PRST-004 | B | 합성 의뢰서 작성 |
후보 4개의 sequence identity는 86~93%로, 권장 기준 80% 이하를 충족하지 못한다.
이는 14 aa 길이, Cys3-Cys14 SS bond, FWKT pharmacophore 보존, Hard Cutoff 5개를 동시에 적용했을 때 발생한 수렴이다.
후보 다양성 부족은 WARN으로 기록했다.
합성 의뢰서에는 selectivity, half-life, ADMET 항목의 신뢰도 한계를 명시했다.
특히 ADMET `binary_toxicity=1.00` 정정 및 OOD 외삽 가능성을 포함했다.
**산출물**
- `runs_local/final_candidates/synthesis_orders/PRST-001.md` ~ `PRST-004.md`.
- `tier_s_candidates.csv`.
- `tier_b_candidates.csv`.
- PR #63 main merge.
**현재 상태**
충족. Gate-2 진입 결정은 회의에서 필요하다.

---

### A-10 — SSTR3 도킹 에러 원인 분석 및 해결
**회의 원문**
> "SSTR3 도킹 에러 원인 분석 및 해결. 담당: AI팀. 기한: 5월 회의 전. 상태: 신규 A-01과 연동."
> — 회의록 §3
> "SSTR3 PDB 구조의 전처리 상태를 점검한다: 누락 잔기(missing residues), 충돌 원자(clashes), 비정상 B-factor 등을 확인한다. 필요 시 Modeller 또는 SWISS-MODEL로 누락 루프를 재구축한 뒤 에너지 최소화를 수행한다."
> — 회의록 §4 A-10
**수행 내용**
SSTR3 PDB(`8XIR`)에서 다중 chain 처리 로직이 문제였다.
`offtarget_dock.py`에 chain 선택 로직을 추가했다.
smoke test 결과 ddg=-92.09로 정상 실행되었다.
후속 분석에서 SSTR1/SSTR4 공유 signature로 인한 subtype mapping 위험도 확인했고, 고유 signature만 사용하는 방식으로 수정했다.
**산출물**
- PR #60 main merge.
- `pipeline_local/tests/test_offtarget_dock_cif_chain.py`.
- `pipeline_local/tests/test_offtarget_dock_boltz.py`.
- 관련 테스트 48건 통과.
**현재 상태**
충족.

---

## 4. 9개 Action Item 요약
| 번호 | 회의 요구 | 수행 결과 | 상태 |
|------|----------|----------|------|
| A-01 | SSTR1/3/4/5 위치 지정 도킹 좌표 + 재도킹 | SSTR2 좌표 추출, cealign 정렬, RMSD 2.77~3.13 Å, 인터페이스 구현 | 충족 |
| A-02 | 반감기 도구 5종 이상 비교 + 정확도 평가 | 7종 비교, D-AA 지원 도구 0개, Octreotide 4.83× 과대 추정 확인 | 부분 |
| A-03 | Fab-ADMET 정확도 + 자체 학습 가능성 | Fab-ADMET=pepADMET 오기재 정정, D-AA/DOTA OOD 한계 확인 | 부분 |
| A-04 | ΔG+반감기+selectivity+ADMET 복합 스코어링 | Hard Cutoff, WSS, Pareto front, Tier S/A/B/FAIL 구현 | 충족 |
| A-05 | SST14 reference ΔG n회 평균 | FlexPepDock mean 553.857 REU, σ=4.024 | 충족 |
| A-06 | diffusion docking PoC | DiffPepDock SS bond 처리 한계, NOT_RECOMMENDED | 충족 |
| A-07 | GPU 서버 2벤더 견적 | 비교 매트릭스 작성, 외부 견적 대기 | 부분 |
| A-08 | 서버 마이그레이션 | 회의 당일 삭제 항목과 정합 | 삭제 |
| A-09 | 최종 후보 3~4개 + 합성 의뢰 | PRST-001~004 및 의뢰서 4건 작성 | 충족 |
| A-10 | SSTR3 도킹 에러 해결 | chain 선택 로직 및 subtype signature 수정 | 충족 |
회의 KPI 기준으로는 신규 8건 중 6건 충족, 2건 부분 충족이다. A-07은 외부 견적 영역이고, A-08은 삭제 항목이다.

---

## 5. 3-Layer Ensemble과 serum stability/ADMET 병목

### 5.1 문제 재정의
A-02와 A-03의 공통 병목은 "도구를 못 찾았다"가 아니라 "후보의 화학 공간이 기존 도구의 학습 범위 밖에 있다"는 점이다.
PRST 후보는 다음 특성을 동시에 가진다.
- SST-14 유사 14 aa peptide.
- Cys3-Cys14 SS bond 기반 cyclic constraint.
- D-AA 또는 비천연 AA 치환 가능성.
- DOTA 등 chelator 결합 가능성.
- SSTR2 selectivity와 radiolysis stability를 동시에 만족해야 하는 다목적 조건.
일반 L-AA peptide 또는 small molecule ADMET 모델은 이 조합에 대해 절대값 보정을 제공하지 못한다.
따라서 serum stability와 ADMET 문제는 단일 모델로 닫히지 않는다.

### 5.2 PR #85 3-Layer Ensemble 구조
PR #85의 3-Layer Ensemble 모듈은 main에 반영되었다. 단, §5.4에서 다루듯이 main 반영은 모듈 존재만 의미하며 표준 후보 enrichment 경로와는 분리되어 있다.
Layer 1은 휴리스틱 계층이다.
ProtParam, Instability Index, radiolysis-sensitive residue count, N-end rule 계열 값처럼 빠르게 산출 가능한 지표를 모은다.
Layer 1의 장점은 해석 가능성과 속도이다. 단점은 D-AA, cyclic constraint, DOTA를 물리적으로 직접 다루지 못한다는 점이다.
Layer 2는 ML regression 계층이다.
half-life 같은 연속값을 예측하는 계층이며, PEPlife2-GAT 재학습을 포함해 검토했다.
초기 학습 결과는 R²=-0.028, Spearman ρ=-0.119, MAE=33.12 h였다.
이후 실험 브랜치(`experiment/layer2-pepmsnd-retrain-20260521`, PR #112)에서 R²=0.022, Spearman ρ=0.571로 재학습된 결과가 보고되었으나, seed/셔플에 따라 부호가 흔들리고 main에 머지되지 않았다.
두 결과 모두 평균 baseline 수준이며, 절대 t½ 보고용으로 신뢰할 수 없다.
Layer 3은 ML classification 계층이다.
toxicity, binary ADMET flag, OOD guard를 포함한다.
PRST 후보의 ADMET=1.00은 이 계층에서 나온 값이지만, D-AA·cyclic·DOTA 조합에 대해 외삽 가능성이 크다.
따라서 `recommended_for_decision=False` 성격의 guard가 필요하다.

### 5.3 3-Layer는 타개책인가
현실적 판단은 다음과 같다.
3-Layer Ensemble은 serum stability와 ADMET 문제의 해결책이 아니다.
다만 현재 한계를 수치와 상태 플래그로 노출하고, 단일 도구 출력이 합성 결정으로 직행하지 못하게 막는 framework이다.
즉, 3-Layer의 의미는 "예측 정확도 확보"보다 "의사결정 오류 억제"에 있다.
Layer 1은 빠른 제외 기준을 제공한다.
Layer 2는 현재 실패를 계량화한다.
Layer 3은 OOD와 binary toxicity 경고를 부착한다.
이 세 층이 동시에 작동하면, PRST 후보는 계산상 우선순위 후보로 남을 수 있지만 ADMET/half-life 실측 없이 통과 판정을 받지는 않는다.

### 5.4 코드 실태와 narrative의 격차
이 항목은 발표에서 부풀리지 말아야 할 부분이다. 5월 코드 조사(`_workspace/release/3layer-admet-serum-impact-analysis.md`) 결과를 그대로 옮긴다.
"PR #85가 main에 들어갔다"와 "표준 후보 enrichment가 3-Layer를 호출한다"는 동치가 아니다.
현재 브랜치(`docs/schrodinger-proposal-d2-20260526`) 워킹 트리 기준 사실은 다음과 같다.
- 표준 enrichment 함수 `enrich_candidates_from_wrappers`는 `run_routed_halflife` / `compute_layer1_halflife` / `predict_admet_layer3`를 호출하지 않는다. 즉 PRST 의뢰서 산출 경로는 여전히 단일 wrapper(`predict_halflife_pepmsnd.py`, `predict_admet_pepadmet.py`) 기반이다.
- `run_routed_halflife`는 Layer 2(`layer2_daa_cyclic_pepmsnd`)만 실구현이고, Layer 1·3 반감기 경로는 스텁 메시지와 경고만 반환한다(`pipeline_local/scoring/ensemble_router.py:61-76`).
- D-AA 표기 후보는 enrichment 진입 단계에서 통째로 스킵 처리되어 `halflife_confidence_grade=UNAVAILABLE`, `admet_confidence_grade=UNAVAILABLE`만 남는다(`composite_scorer.py:400-408`). Layer 2 라우팅도 받지 않는다.
- `recommended_for_decision` 문자열은 `predict_admet_ai_wrapper.py`에서만 항상 `False`로 고정 출력되며, Tier 결정 또는 Hard Cutoff 분기와 자동 결합되어 있지 않다.
- PR #117(ADMET divergence guard, commit `e3a5413`)은 현재 브랜치 및 main 양쪽 모두에 포함되어 있지 않다. `docs/eod-2026-05-26-vram-pcap-dpep`와 `fix/fe-stale-runid-20260526` 브랜치에만 존재한다. 발표에서 #117을 main 반영 항목으로 언급해서는 안 된다.
- PR #112(pepMSND Layer 2 재학습)는 2026-05-21부터 OPEN 상태이며 main 머지 commit이 없다. 후속 PR #115의 5/28 deck D-6 갱신 commit은 PR #112 산출물을 "부록 반영"으로만 포함했다. 즉 발표에서 "PR #112가 main에 들어갔다"는 표현은 사실과 다르며, 현재 형태는 "별도 브랜치의 실험 결과를 부록 자료로 가져왔다"가 정확하다.
- 합성 의뢰서 `runs_local/final_candidates/synthesis_orders/PRST-00{1,2,3,4}.md`에 "Layer 1/2/3", "ensemble_halflife_hours", "ADMET-AI Layer 3" 표기는 없다. 사람이 작성한 H-06 disclaimer와 "pepADMET 1.00 + OOD 해석 가능성" 문장으로 같은 정책을 흡수했다.

| 항목 | PRST 의뢰서 표현 | 동일 명칭 코드 산출 | 정합 여부 |
|------|-----------------|-------------------|----------|
| 반감기 수치 근거 | `step08_stability.py::predict_half_life`, HEURISTIC | enrichment 선택 시 `predict_halflife_pepmsnd`; Layer 모듈은 비호출 | 부분 불일치 |
| 독성 1.00 | pepADMET 로컬 재검증 + OOD 문구 | 재훈련 GNN 출력 + 레지스트리 경고 정합 | 의미상 일치 |
| 3-Layer 용어 | 미사용 | 모듈·테스트 존재 | 문서 간 갭 |
| `recommended_for_decision` | 없음 | ADMET-AI wrapper에만 `False` 고정 | 서로 무관 레이어 |

결과적으로 5월의 변화는 "코드베이스에 더 엄격한 실험 모듈이 병렬로 생긴 상태"이고, 합성 패키지 양식 자체는 4월 회의 이후 거의 고정되어 있다.
6월 회의까지 진행해야 할 항목은 "어느 엔진이 canonical인가"의 합의이며, 이것이 정리되어야 narrative와 코드 사이의 격차가 닫힌다.

### 5.5 의사결정 루프 — 의도와 현실
3-Layer Ensemble이 의도한 루프는 다음과 같다.
1. Hard Cutoff와 WSS/Pareto로 후보를 좁힌다.
2. Layer 1에서 즉시 산출 가능한 stability/radiolysis 지표를 붙인다.
3. Layer 2 regression이 유효하지 않으면 그 상태를 수치로 남긴다.
4. Layer 3 classification 결과가 OOD이면 절대값 대신 risk flag로 전환한다.
5. 합성 의뢰서에 Ki, serum stability, ADMET, hemolysis, cytotoxicity 실측 항목을 포함한다.
6. 실측값으로 다음 후보 생성과 scoring weight를 보정한다.
이 가운데 §5.4의 코드 실태를 반영하면, 1·5·6은 현재도 작동한다. 2·3·4는 모듈은 존재하지만 표준 후보 enrichment 경로와 분리되어 있어, 사람이 H-06 disclaimer 문장과 OOD 해석으로 같은 기능을 수동으로 수행하고 있다.
PRST-001은 Tier S로 합성 우선 후보로 유지된다.
PRST-002~004는 Tier B로 남고, 실측 패키지 없이 "백업 lead"로 승격하지 않는다.
이 결정 자체는 ADMET=1.00 또는 half-life heuristic score의 절대값에 근거하지 않는다.

### 5.6 wet-lab 병행의 위치
A-02와 A-03 결과를 반영하면 wet-lab 병행은 선택 항목이 아니라 Gate-2 판단 조건이다.
최소 실측 항목은 다음과 같다.
- SSTR2 Ki 또는 기능적 binding assay.
- SSTR1/3/4/5 selectivity.
- Serum stability t½.
- Hemolysis 또는 cytotoxicity.
- ¹⁷⁷Lu 표지 후 RCP/Radiochemical stability.
- 72 h RCP ≥90% 여부.
3-Layer Ensemble은 이 실측 항목을 줄여 주는 도구가 아니다.
우선순위를 정하고, 어떤 계산값을 신뢰하지 말아야 하는지 표시하는 장치이다.

### 5.7 파급효과
첫째, 합성 후보 선정의 근거가 ΔG 중심에서 다중 조건 중심으로 이동한다. 단, §5.4의 격차가 닫혀야 자동화된 다중 조건이 된다.
둘째, OOD 경고가 있는 후보도 폐기하지 않고 실측 패키지로 넘기는 경로가 생긴다. 현재는 사람이 H-06 disclaimer 문장을 의뢰서에 추가하는 방식으로 동일 정책이 적용되고 있다.
셋째, 실패 결과가 다음 모델 학습 데이터가 된다. wet-lab 측정값이 들어오기 전까지는 누적이 시작되지 않는다.
넷째, 6월 회의부터는 "예측값 보고"가 아니라 "예측값과 실측값의 불일치 보고"가 중요해진다.
다섯째, 자체 ML 모델 학습의 필요성이 더 명확해진다. 다만 현재 Layer 2의 R²=-0.028 상태에서는 자체 모델을 즉시 의사결정용으로 쓰지 않는다.
여섯째, 운영상 가장 시급한 보고 항목은 "어느 엔진이 canonical 후보 보강 경로인가"의 합의이다. 이 합의 없이 6월 회의로 가면, 발표 narrative와 실제 의뢰서 산출 코드 사이의 격차가 계속 누적된다.

---

## 6. 슈뢰딩거 도입 검토

### 6.1 검토 전제
KAERI가 현재 Schrödinger 라이센스를 보유하지 않는 것으로 확인되어 있다.
Schrödinger Korea 영업 연락과 라이센스 조건 확인도 아직 진행되지 않았다.
따라서 아래 내용은 실제 적용 결과가 아니라 일반 문헌 벤치마크와 Schrödinger 공식 자료 기반의 예상이다.
6월 회의 전까지 도입 검토를 승인받는다면, 실제 비용, 모듈 범위, 서버 연동, 첫 산출물의 형식은 별도 정량화해야 한다.

### 6.2 현재 자체 도구 한계
현재 도구 한계는 다섯 축으로 정리된다.
1. PRST 후보 ADMET=1.00은 Layer 3 OOD 외삽 가능성이 크다.
2. Layer 2 half-life regression은 R²=-0.028로 의사결정용이 아니다.
3. Layer 1은 시간 단위 half-life 합의값을 제공하지 못한다.
4. DiffPepDock은 SS bond 처리 한계로 NOT_RECOMMENDED이다.
5. OpenMM/OpenFE/FlexPepDock/Boltz-2 조합은 단위와 스케일이 달라 cross-tool calibration이 필요하다.
Schrödinger 검토는 이 다섯 한계 중 일부를 상용 통합 워크플로우로 줄일 수 있는지 확인하는 작업이다.

### 6.3 모듈별 예상 효과
| 모듈 | 일반 벤치마크/공식 자료 기반 | SST-14/SSTR2 적용 시 기대 |
|------|-----------------------------|---------------------------|
| Glide SP/XP | peptide docking protocol에서 enhanced sampling+MM-GBSA rescoring 시 RMSD ≤2 Å 성공률 58%, FlexPepDock 63%에 근접한 벤치마크 보고 | cyclic SST-14 계열 pose generation의 비교 축. 단, SS bond와 DOTA 처리 확인 필요 |
| FEP+ | large-scale benchmark에서 FEP+ pairwise RMSE 약 1.25 kcal/mol, edgewise RMSE 약 1.17 kcal/mol 보고. 공식 자료는 ~1 kcal/mol 수준을 제시 | A-05 ΔG reference와 A-04 modification 후보의 ΔΔG 우선순위 판단 보조 |
| Desmond | GPU 기반 MD 엔진. 공식 성능표는 GPU별 ns/day를 제시하며, 성능은 system size와 GPU에 의존 | SS bond 유지, DOTA 결합 전후, RI 표지 후 stability MD의 처리량 개선 가능성 |
| Prime MM-GBSA | Glide pose rescoring과 relative binding free energy estimate에 사용. docking score 단독보다 pose filtering에 유리하나 절대 affinity 모델은 아님 | PRST-001~004 재랭킹 및 A-05 이후 20~50개 후보 압축 보조 |
| WaterMap | binding pocket의 물 위치와 에너지, high-energy displaceable water 분석 제공 | SSTR subtype pocket의 물 네트워크 차이를 selectivity 해석에 연결 가능 |
| BioLuminate | biopolymer modeling, peptide/protein engineering 워크플로우 | cyclic peptide, D-AA, DOTA parameterization 검토 및 Layer 3 OOD ML 보완재 |
Glide의 peptide benchmark는 19개 peptide set에서 default SP 대비 enhanced peptide protocol의 pose prediction을 개선한 결과다.
우리 시스템에 그대로 58%가 재현된다는 뜻은 아니다.
SST-14는 cyclic SS bond를 갖고 있고, 후보군에는 D-AA와 chelator가 들어갈 수 있으므로 별도 validation이 필요하다.
FEP+는 가장 직접적인 의사결정 보조 가능성이 있다.
A-04 7단계 중 amino acid modification 후보를 고를 때, 변이 전후 ΔΔG의 방향성과 크기를 기존 Rosetta/Boltz 값과 비교할 수 있다.
단, FEP+가 신뢰도를 가지려면 congeneric series, 명확한 binding pose, parameterization 가능성, 충분한 sampling이 필요하다.
Desmond는 A-06 diffusion docking의 대체재가 아니라 MD 검증 축이다.
즉, 빠른 docking이 아니라 SS bond, cyclic conformation, RI 표지 후 구조 안정성, solvent exposure를 시간축에서 확인하는 역할이다.
Prime MM-GBSA는 A-05와 A-09 사이의 rescoring에 위치한다.
정확도는 system-dependent이며, 단독 go/no-go 기준이 아니라 pose filtering과 ranking stability 확인용이다.
WaterMap은 직접 ADMET을 해결하지 않는다.
다만 SSTR2와 off-target subtype pocket의 hydration pattern 차이를 selectivity 해석에 연결할 수 있다.
BioLuminate는 3-Layer의 Layer 3 OOD 문제를 직접 없애지는 않는다.
하지만 D-AA, cyclic peptide, chelator 포함 구조를 명시적으로 세팅하고, 이후 Glide/Desmond/FEP+로 넘기는 전처리 축이 될 수 있다.

### 6.4 6월 회의까지 가능한 산출물
도입 검토를 승인받고 라이센스 평가판 또는 기관 사용권을 확보할 수 있다는 가정에서, 6월 회의까지 가능한 산출물은 제한적으로 잡아야 한다.
일반적인 순서는 다음과 같다.
1. 라이센스 조건 확인: 학술/비상업/기관 과제 사용 가능 범위, 모듈별 포함 여부.
2. 설치 및 환경 셋업: Maestro, Glide, Prime, Desmond, FEP+, BioLuminate, WaterMap 중 대상 모듈 확인.
3. GPU/CPU 연동 확인: Desmond와 FEP+ job scheduler, A-07 GPU 견적과 연동.
4. 입력 구조 준비: SSTR2, PRST-001, SST-14 reference, SS bond, DOTA 여부.
5. 첫 산출물: PRST-001 또는 SST-14 기준 docking pose, Prime MM-GBSA rescoring, 짧은 Desmond sanity MD.
라이센스 접근이 빠르게 열리면 첫 sanity output은 수일~2주 범위에서 가능할 수 있다.
그러나 실제 의사결정용 validation은 1~3개월 학습 곡선을 별도로 봐야 한다.
1개월 평가는 설치 안정성, 입력 구조 처리, SS bond/D-AA/DOTA parameterization 가능성, job failure rate를 본다.
2개월 평가는 PRST-001~004 재랭킹, A-05 reference와의 일관성, Desmond trajectory 품질을 본다.
3개월 평가는 FEP+ ΔΔG와 wet-lab Ki 또는 stability 실측값의 상관을 본다.

### 6.5 GPU 연계
Desmond와 FEP+는 GPU 연계 여부가 처리량을 좌우한다.
A-07의 DGX/B200 견적은 diffusion docking만을 위한 것이 아니라, Schrödinger 도입 시 MD/FEP throughput 평가와도 연결된다.
견적 비교에는 다음 항목을 추가해야 한다.
- Desmond GPU support와 ns/day 예상.
- FEP+ job 병렬화 단위.
- NVLink 필요성.
- 라이센스 token과 GPU 수의 병목 관계.
- 온프레미스 서버와 외부망 서버 배포 제약.

### 6.6 도입하지 않을 경우의 대안
Schrödinger를 도입하지 않으면 자체 ML 및 오픈소스 물리 계산을 강화하는 경로로 간다.
대안 경로는 다음과 같다.
| 항목 | Schrödinger 도입 | 자체 ML/오픈소스 경로 |
|------|------------------|----------------------|
| 비용 | 라이센스 비용 및 모듈별 견적 필요 | 직접 라이센스 비용은 낮으나 인력 시간이 큼 |
| 일정 | 설치 후 sanity output은 빠를 수 있으나 계약 리드타임 존재 | 즉시 착수 가능하나 안정화와 검증 시간이 길다 |
| 정확도 | FEP+ 등 벤치마크가 존재하나 system validation 필요 | 현재 Layer 2 R²=-0.028로 출발점 낮음 |
| 인력 | 상용 workflow 학습 필요 | 모델 학습, 데이터 큐레이션, force field 세팅 역량 필요 |
| 재현성 | Maestro project/job 중심 관리 | 코드 기반 재현성은 높일 수 있으나 운영 부담 큼 |
| D-AA/DOTA | parameterization 확인 필요 | 직접 parameterization 및 검증 필요 |
자체 ML 경로의 장점은 장기적으로 내부 데이터와 실측값을 축적해 도메인 특화 모델을 만들 수 있다는 점이다.
단기적으로는 R²=-0.028 상태에서 바로 의사결정 품질을 만들기 어렵다.
Schrödinger 경로의 장점은 pose generation, rescoring, MD, FEP, hydration analysis가 하나의 workflow로 묶인다는 점이다.
단점은 비용, 라이센스, 내부 승인, 실제 SST-14/SSTR2 system validation이 남는다는 점이다.

### 6.7 5월 회의에서의 요청
5월 회의에서 필요한 결정은 구매가 아니다.
6월 회의까지 다음 검토를 진행할지 여부이다.
- Schrödinger Korea 또는 공급사 연락 승인.
- 평가판 또는 기관 라이센스 가능성 확인.
- 대상 모듈 범위 지정: Glide, Prime MM-GBSA, Desmond, FEP+, WaterMap, BioLuminate.
- A-07 GPU 견적표에 Schrödinger job throughput 항목 추가.
- PRST-001/SST-14 기준 sanity workflow 정의.
결정은 6월 회의에서 정량화 후 진행한다.

---

## 7. 5월 28일 회의 의사결정 항목

### 7.1 PRST-001~004 합성 진행 범위 — 결정 주체: 서호성 박사 + RI팀
결정해야 할 것은 네 후보 전체를 보낼지, PRST-001 우선으로 줄일지이다.
PRST-001은 Tier S이지만, ADMET/half-life 계산값은 절대 근거가 아니다.
따라서 합성 진행 시 serum stability, hemolysis/cytotoxicity, selectivity, RCP/Radiochemical stability를 실험 패키지에 포함해야 한다.

### 7.2 pepADMET 라이센스 및 저자 문의 — 결정 주체: KAERI 행정·법무 + AI팀
pepADMET GitHub GPL-3.0, 웹 CC BY-NC-SA 4.0 조건을 KAERI 과제와 상업화 가능성 관점에서 법무 검토해야 한다.
저자 문의는 공개되지 않은 half-life endpoint weight 또는 training data 접근 가능성을 확인하는 방향이다.

### 7.3 A-07 GPU 견적 — 결정 주체: 서호성 박사 + 안기범 박사
DGX H100, DGX B200 또는 기존 외부망 서버 확장 여부를 비교해야 한다.
DiffPepDock 도입은 보류지만, Desmond/FEP+와 자체 ML 학습을 고려하면 GPU 의사결정은 여전히 필요하다.
견적 결정은 §7.4 Schrödinger 검토 결과와 §7.5 6월 산출물 범위에 직접 영향을 준다.

### 7.4 Schrödinger 도입 검토 — 결정 주체: 회의 참석 전원 (검토 승인 여부)
5월 회의 결정은 "6월까지 검토를 진행할지"이다.
구매 결정은 비용, 라이센스, 모듈 범위, GPU 연동, 첫 sanity 결과를 보고 6월 회의에서 판단한다.

### 7.5 6월 회의 기준 산출물 — 결정 주체: 본 발표 후 회의 합의
6월 회의의 기준 산출물은 다음으로 제한한다.
§7.1 합성 발주 결정이 선행되어야 실측 항목 4~6가 의미를 갖는다.
- PRST-001~004 합성 진행 상태 또는 발주 결정 결과.
- pepADMET 법무/저자 문의 진행 상태.
- Layer 2 half-life 개선 여부 또는 실패 원인.
- Schrödinger 도입 검토 결과.
- A-07 GPU 견적 비교표.
- 실측 데이터가 확보되면 계산값과의 불일치 분석.

---

## 8. 발표 마지막 메시지
4월 회의에서 받은 신규 Action Item 8건 중 6건은 충족했고, A-02/A-03은 D-AA·cyclic·DOTA 조합의 도구 부재로 부분 충족에 머물렀다.
최종 후보 PRST-001~004는 도출되었고 합성 의뢰서도 작성되었다.
다만 이 후보들은 ADMET과 serum stability 계산값만으로 통과 판정을 받을 수 없다.
PR #85의 3-Layer Ensemble 모듈은 이 한계를 해결하지 않는다.
대신 한계를 수치와 경고 플래그로 노출하고, 단일 도구 출력의 과신을 막고, wet-lab 실측의 필요성을 명시하는 framework이다.
현재 표준 enrichment 경로가 이 framework를 호출하지 않는 상태이므로, 6월 회의까지 enrichment 정합 작업이 함께 진행되어야 narrative와 코드 사이의 격차가 닫힌다.
Schrödinger 도입 검토는 이 한계 중 docking, rescoring, MD, FEP, hydration analysis를 상용 workflow로 줄일 수 있는지 확인하는 선택지이다.
현재는 라이센스와 비용이 확인되지 않았으므로 결정 사항이 아니라 검토 사항이다.
5월 28일 회의에서 필요한 결정은 합성 범위, 실측 패키지, pepADMET 법무/저자 문의, GPU 견적 진행, Schrödinger 도입 검토 승인이다.

---

## 부록 A. 축약 용어
| 용어 | 본 문서에서의 의미 |
|------|-------------------|
| WSS | Weighted Sum Score. 여러 지표를 정규화해 가중 합산한 후보 점수 |
| Pareto front | 여러 목적 함수에서 다른 후보가 모든 지표를 동시에 압도하지 못하는 후보 집합 |
| Tier S/A/B/FAIL | S=합성 우선, A=2순위, B=보류, FAIL=Hard Cutoff 미통과 |
| OOD | Out-of-distribution. 모델 학습 분포 밖의 입력 |
| R²<0 | 평균값 예측보다 낮은 설명력 |
| Spearman ρ | 예측 순위와 실측 순위의 일치도 |
| MAE | 평균 절대 오차 |
| REU | Rosetta Energy Unit. Rosetta 계열 도구의 내부 에너지 단위 |
| RCY/RCP | Radiochemical Yield / Radiochemical Purity |
| H-06 guard | 계산 불가능 또는 OOD 값을 결정 근거로 쓰지 않도록 붙인 경고/차단 규칙 |
| FEP+ ΔΔG | 변이 또는 치환 전후 상대 결합 자유에너지 차이 |

---

## 부록 B. 근거 문서
| 문서 | 위치 |
|------|------|
| 회의록 원본 PDF | `docs/meet_log/AI-RI_Scientist_회의록_20260406_서호성 V2.pdf` |
| 회의 준비 및 Q&A | `docs/meet_log/2026-04-06_action_items/MEETING_PREP_2026-05-28.md` |
| 5/20 STATUS | `docs/meet_log/2026-04-06_action_items/STATUS_2026-05-20.md` |
| A-01~A-10 action item 문서 | `docs/meet_log/2026-04-06_action_items/A-*.md` |
| v1 narrative | `_workspace/release/meeting-2026-05-28-narrative.md` |

---

## 부록 C. Schrödinger 벤치마크 참고
아래 수치는 우리 SST-14/SSTR2 실측값이 아니라 일반 문헌 및 공식 자료 기반 참고값이다.
| 항목 | 참고 |
|------|------|
| Glide peptide docking | Tubert-Brohman et al., 2013 JCIM: enhanced peptide protocol에서 top-10 pose 기준 RMSD ≤2 Å 성공률 58%, FlexPepDock 63%와 비교 |
| FEP+ | large-scale FEP+ benchmark: pairwise RMSE 1.25 kcal/mol, edgewise RMSE 1.17 kcal/mol; Schrödinger 공식 자료는 ~1 kcal/mol 수준 제시 |
| Desmond | Schrödinger 공식 GPU performance table은 GPU별 ns/day 성능을 제시하나 system size 의존성이 큼 |
| Prime MM-GBSA | Glide pose 후처리 및 relative free energy estimate에 사용. docking score 단독의 affinity 한계를 보완하나 절대값 모델은 아님 |
| WaterMap | binding pocket water location/energetics 및 high-energy displaceable water 분석 |
| BioLuminate | biopolymer/peptide modeling workflow. D-AA·DOTA 처리는 실제 parameterization 검토 필요 |
참고 URL: Schrödinger FEP+ `https://www.schrodinger.com/platform/products/fep/`, Schrödinger WaterMap `https://www.schrodinger.com/platform/products/watermap/`, Schrödinger Desmond GPU performance table `https://learn.schrodinger.com/public/getting-started/2025-1/system_requirements/Content/desmond/desmond_user_manual/gpu_performance.htm`, Glide docking white paper `https://www.schrodinger.com/life-science/learn/white-papers/docking-and-scoring/`, FEP+ benchmark `https://pmc.ncbi.nlm.nih.gov/articles/PMC10576784/`, Glide peptide docking paper `https://pubs.acs.org/doi/10.1021/ci400128m`.

---

## 부록 D. 시간선
| 날짜 | 사건 |
|------|------|
| 2026-03-23 | MOM-002 |
| 2026-04-06 | MOM-003. 9개 Action Item 발생 |
| 2026-04-12 | 회의록 작성 완료 |
| 2026-05-19 | Action Item audit 및 PR #60~#63 계열 정리 |
| 2026-05-20 | Fab-ADMET=pepADMET 명칭 정정, STATUS 문서 작성 |
| 2026-05-21 | PR #85 3-Layer framework, PR #90 binding pocket fix 반영 |
| 2026-05-27 | narrative v2 작성 |
| 2026-05-28 | 회의 |
| 2026년 6월 | 다음 회의. 일자 미정 |
