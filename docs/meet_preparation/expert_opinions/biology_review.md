# 생명공학 전문가 견해 — 구조·SS bond·GPCR 결합 메커니즘
**작성일**: 2026-06-01 | **작성자**: reviewer-biology
**검토 대상**: A-01 (SSTR1/3/4/5 위치 지정 도킹), A-05 (SST14 레퍼런스 ΔG), A-10 (SSTR3 도킹 에러)
**근거 원칙**: 검증된 출처만 인용. 미확인은 `[추정]` 명시. 할루시네이션 금지.

---

## 1. 총평 (생명공학·구조생물학 관점)

본 파이프라인은 SST-14 native 시퀀스(AGCKNFFWKTFTSC, 14aa, Cys3-Cys14 SS bond)를 기반으로 SSTR2 선택성 후보를 도출하는 구조를 취하고 있다. 생명공학 관점에서 핵심 쟁점은 세 가지다.

첫째, 파이프라인이 도킹 기준 구조로 사용하는 SSTR2_7XNA.pdb(`data/somatostatin_receptor/SSTR2_7XNA.pdb`)는 octreotide(8-mer cyclic, Cys2-Cys7 bridge) 복합체 구조이며, 회의록 §2.1이 명시한 SST-14 복합체 구조 7T10(SSTR2 + SST-14 14-mer native)과 다르다. 이 불일치는 결합 포켓 형태 해석과 pharmacophore 배치 검증의 신뢰성에 직접 영향을 준다.

둘째, Boltz 도킹이 생성한 SST-14/SSTR2 복합체 3종 모두에서 Cys3-Cys14 SS bond 형성은 확인되었으나, 펩타이드 중심(centroid)이 포켓 중심으로부터 66-80 Å 이탈한 상태다(`data/somatostatin_receptor/SSTR2_SST14_complex_metadata.json`). SS bond 형성과 포켓 배치가 동시에 충족된 모델이 없는 것은 현재 도킹 프로토콜의 구조적 한계를 드러낸다.

셋째, cealign 기반 SSTR 패밀리 정렬은 수행되었으며(alignment_summary.json, RMSD 2.77-3.13 Å), 네거티브 디자인 잔기 맵(ECL/TM 범위 77-314)도 등록되어 있다. 그러나 K-1/K-2 selectivity 결함(`_build_pdb_index` 정렬 오류·`candidate_pdb` 미전달)으로 현재 모든 off-target 결과가 동일한 값을 반환하므로, 셀렉티비티 KPI(≥100×) 수치의 신뢰성은 없는 상태다.

생물학적 타당성 등급: **MED** (구조 일관 — 7XNA 기반 포켓 정의는 구조적으로 타당하나 SST-14 복합체 7T10 부재로 pharmacophore 배치 검증이 불완전함)

---

## 2. Action Item별 상세 견해

### A-01: SSTR1/3/4/5 위치 지정 도킹

**구조 정렬 결과 평가**

`data/somatostatin_receptor/alignment_summary.json`에 따르면 SSTR2(7XNA)를 기준으로 한 cealign 결과는 SSTR5(2.77 Å) < SSTR4(3.019 Å) < SSTR3(3.086 Å) < SSTR1(3.125 Å) 순의 global RMSD를 보인다. GPCR 패밀리 내 구조 정렬에서 RMSD 3 Å 수준은 허용 범위이나, global RMSD가 낮다고 해서 결합 포켓 국소 RMSD가 낮은 것은 아니다. **TM5/TM6 포켓 잔기 국소 RMSD를 별도로 측정하는 것이 셀렉티비티 설계에 더 직접적인 근거**가 된다. `[추정]` — 국소 RMSD 측정은 현재 구현에 포함되지 않은 것으로 파악됨. §검증 필요.

**7T10 vs 7XNA 구조 ID 불일치의 결합 형태 해석 영향**

7XNA(PDB)는 SSTR2와 octreotide(D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Thr, 8-mer cyclic)의 cryo-EM 복합체로, chain B의 SSBOND 레코드에서 DCS-B3 ~ CYS-B8 간 SS bond(2.11 Å)가 확인된다(`data/somatostatin_receptor/SSTR2_7XNA.pdb:SSBOND B3-B8`). octreotide는 Phe7/Trp8/Lys9의 FWKT pharmacophore 핵심을 보존하면서 ring size를 14-mer에서 8-mer로 축소한 구조다.

반면 7T10은 SSTR2와 SST-14(native 14-mer, Cys3-Cys14 SS bond) 복합체로, ring conformation과 N/C-terminal flanking region의 배치가 7XNA와 다르다. SST-14의 Cys3-Cys14 고리는 octreotide의 Cys2-Cys7 고리보다 ring span이 크며(12-잔기 루프 vs 6-잔기 루프), 이로 인해 ECL2와의 접촉 기하학이 달라진다. 회의록 §2.1이 7T10을 명시적으로 인용한 것은 이 차이를 반영하기 위한 것으로 해석된다.

**결합 형태 해석 영향 요약**: 7XNA 기반 포켓 중심 좌표(-4.956, -27.489, 50.277 — `binding_pocket_SSTR2.json`)는 octreotide 결합 형태에 최적화된 값이다. SST-14 유사체를 이 좌표 기준으로 도킹할 경우, 14-mer ring의 부피·ECL2 접촉이 과소 또는 오평가될 수 있다. 7T10 기반 포켓 좌표로 보정하거나, 7T10 구조로 별도 도킹을 수행하여 결과를 비교하는 것이 타당하다.

**R-20 조치 권고**: 7T10 PDB 취득 + 7XNA와 binding pocket 좌표 비교 → 편차가 5 Å 이상이면 7T10 기준으로 전환 또는 dual-pocket 앙상블 도킹. 이는 `reflection_plan/00_master_plan.md`의 R-20 항목과 직결된다.

생물학적 타당성 등급: **MED** (7XNA 포켓 정의는 구조적으로 합리적이나 7T10 미검증으로 인한 pharmacophore 배치 불확실성 잔존)

**회의록 §2.1 ECL/TM 잔기 표의 네거티브 디자인 활용**

`data/somatostatin_receptor/negative_design_residues_SSTR2.json`에 등록된 SSTR2 선택성 잔기(ECL2: 192/193/195/197; ECL3: 284/286; TM5: 205/208/209/212; TM6: 272/273/276/279)는 Gervasoni 2024 CSBJ(DOI: 10.1016/j.csbj.2024.03.005)의 SSTR 패밀리 MD 비교 분석과 구조적으로 일관된다. 동 논문은 SSTR2 선택성이 TM5/TM6 경계의 소수성 서브포켓 상호작용에서 기인함을 보고하고 있으며, W8 변형으로 SSTR4 선택성이 향상된다는 관찰은 FWKT pharmacophore에서 Trp(W8 = SST-14 Trp8)의 역할을 직접 지지한다.

네거티브 디자인 활용 방안: ECL2(178-201)와 ECL3(282-287) 잔기 차이를 SSTR1/3/4/5 구조에서 추출하여 **서브타입별 "불허 접촉 지도(forbidden contact map)"**를 구성하고, 후보 펩타이드의 off-target 잔기 접촉 에너지가 SSTR2 접촉보다 불리할 조건(양수 ΔΔG)을 필터 기준으로 정량화하는 것이 서호성 박사 의견(회의록 §2.1)의 핵심 의도다. 현재 구현(`selectivity_runner.py`)은 ΔG 배수 비교만 수행하고 있어, 잔기 수준의 에너지 분해(per-residue energy decomposition)는 포함되지 않은 것으로 파악된다. `[추정]` §검증 필요.

---

### A-05: SST14 레퍼런스 ΔG 기준선

**SS bond 형성 상태 및 결합 형태 평가**

`data/somatostatin_receptor/SSTR2_SST14_complex_metadata.json`의 Boltz 도킹 결과를 분석하면:

- Boltz_1: CYS A3 SG(-45.823, 9.836, -10.362) — CYS A14 SG(-44.424, 8.555, -10.646) 간 SG-SG 거리 = 1.918 Å. 표준 SS bond(2.03±0.05 Å)보다 압축되어 있으나, Boltz CIF→PDB 변환 아티팩트 또는 예측 오차 범위 내일 수 있다. `[추정]` — 1.918 Å는 생리적 조건에서 약간 단축된 거리로, 단독으로는 SS bond 형성 부정의 근거가 되지 않는다.
- Boltz_2: SG-SG 0.712 Å — 이 값은 물리적으로 불가능하다. 두 황 원자가 동일 위치에 가까이 있는 충돌(clash) 상태이며, 이 모델의 SS bond 기하학은 타당하지 않다. `data/somatostatin_receptor/SSTR2_SST14_complex_boltz_2.pdb` 모델은 SS bond geometry 검증 실패.
- Boltz_3: SG-SG 1.284 Å — Boltz_2보다는 완화되었으나 역시 표준 SS bond 거리보다 현저히 짧다. 동일한 clash 우려가 있다.

**핵심 문제**: 세 모델 모두 포켓 배치(pocket placement)가 실패(centroid-pocket 거리 66-80 Å). SS bond 형성 여부와 무관하게, SST-14 펩타이드가 SSTR2 결합 포켓 내에 배치되지 못한 상태로 계산된 ΔG이다. 따라서 `SST14_SSTR2_reference_dG.json`의 Mean ΔG = 553.857 REU(PyRosetta FlexPepDock, 양수값)는 **결합 상태가 아닌 비결합·연장 conformation에서의 에너지**를 반영하고 있을 가능성이 높다. 이 값을 결합 기준선으로 사용하는 것은 생물학적으로 타당하지 않다.

FlexPepDock 주석(`note: "Fallback 모드 — SSTR2_7XNA_complex.pdb reference complex 부재 — 확장 conformation 초기화"`)이 이 한계를 내부적으로 명시하고 있으며, 이는 구현팀이 인식하고 있는 사실이다. 그러나 이 값이 `composite_scorer.ddg_score` 정규화 기준으로 실제 사용되고 있다면, A-04 Top-K 스코어링과 A-09 PRST-001~004 최종 선정 결과의 신뢰성도 함께 의문시된다.

**생물학적 타당성 등급**: **LOW** (포켓 외부 conformation 기반 ΔG 사용 — 결합 상태 에너지 기준 아님)

**개선 방향**: 7T10 기반 SST-14 복합체 구조를 초기 conformation으로 사용하거나, 포켓 내부에 SST-14를 배치한 상태에서 FlexPepDock 재실행이 필요하다. 서호성 박사 의견의 2단계(MM-GBSA)는 이 선행 조건이 충족된 후에야 의미있다.

---

### A-10: SSTR3 도킹 에러

**PDB 전처리 관점 평가**

A-10은 PR #60(fix `5f5f7af`)으로 구현 완료 판정을 받았다. `pipeline_local/scripts/structure_io.py`가 CIF/PDB 자동 감지 및 sanitize를 수행하며, SSTR3(8XIR.pdb)의 누락 잔기 재구축이 수행된 것으로 보고되어 있다.

별건으로 발견된 SSTR4 시그니처 중복(`_SSTR_SIGNATURES`에서 VILRYAKMKTA가 SSTR1/SSTR4 공유)이 해소된 점은 중요하다. GPCR 서브타입 간 signature peptide를 결합 포켓 인근 잔기가 아닌 전체 서열 기반으로 정의할 경우, 보존된 TM helix 모티프가 여러 서브타입에 공유되어 이런 중복이 발생한다. 향후 시그니처를 TM5/TM6 포켓 잔기 기반으로 재정의하는 것이 구조생물학적으로 더 정확하다.

`data/somatostatin_receptor/SSTR3_8XIR.pdb`의 chain A 잔기 범위는 40-328로 확인되며, 이는 7XNA(41-333), SSTR4 7XMT(40-?), SSTR5 8ZBJ(40-?) 와 유사한 패턴을 보인다. SSTR3 구조의 residue numbering gap(missing residues) 위치에 대한 구체적 기록이 현재 action item 카드에 없는 점이 아쉽다. 향후 Modeller/SWISS-MODEL 재구축 시 어느 루프가 재구축되었는지 PDB REMARK에 기록하는 것을 권고한다.

**생물학적 타당성 등급**: **HIGH** (PR 완료·회귀 테스트 통과 — 절차상 신뢰 가능)

---

## 3. (보조) Silo A 이중 구현의 구조생물학적 의미

Silo A의 de novo 경로(`pipelines/silo_a/` 3-Arm — NIM 키 부재로 실행 0건)가 관련된 de novo peptide 생성 모델(DiffDock, RFdiffusion, ProteinMPNN)은 구조적 prior 없이 sequence-only 또는 backbone-only 기반으로 후보를 생성한다. 이 후보들이 Cys3-Cys14 SS bond topology를 자동으로 보존할 보장이 없다. SST-14의 생물활성이 SS bond에 의한 ring conformation 제약과 FWKT pharmacophore의 상대적 3D 배향에 강하게 의존한다는 점에서(Gervasoni 2023 JCIM, DOI: 10.1021/acs.jcim.3c00712), de novo 경로 후보에 대해서는 SS bond topology와 pharmacophore 유지 여부를 별도 검증 단계로 삽입해야 한다. 현재 1-Arm 축약판(`pipeline_local/_run_silo_a()`)도 RFdiffusion+ProteinMPNN만 사용하므로 동일한 검증 필요성이 있다.

---

## 4. 도메인 간 권고

| 수신자 | 권고 내용 |
|--------|-----------|
| engineer-backend | R-20: 7T10 PDB 취득 후 7XNA 포켓 좌표와 비교(TM5/TM6 중심 편차 측정). 편차 ≥5 Å이면 7T10 기반 재도킹 |
| engineer-backend | Boltz_2 모델(SG-SG 0.712 Å) 폐기 및 재실행 시 SS bond 거리 필터를 1.8-2.2 Å로 강화 |
| engineer-backend | SST14 레퍼런스 ΔG 산출 시 포켓 배치 성공(centroid-pocket 거리 ≤ 포켓 반경) 조건을 필수 전제로 추가 |
| reviewer-chemistry | Cys3-Cys14 SS bond 보존이 전제인 modification 전략의 ring size 영향 검토 권고 [다른 전문가 의견 권장] |
| reviewer-pharma | FlexPepDock Fallback 모드 ΔG(553.857 REU, 포켓 외부 추정)를 ADMET 스코어링 기준으로 사용 중인지 확인 후 격리 요청 [다른 전문가 의견 권장] |
| reviewer-math | Boltz iptm 0.93-0.95 (3종 모두 iptm_pass: true)인데 pocket_placement가 전부 실패인 조합 — iptm이 포켓 배치 정확도를 보장하지 않는다는 통계적 경고 추가 권고 [다른 전문가 의견 권장] |

---

## 5. 의사결정 권고 (6월 회의 안건)

**D-1 (즉시 결정 필요)**

7T10 구조 취득 및 7XNA 포켓 좌표 비교를 R-20 조치로 수행한 후, 그 결과를 회의 전까지 공유하여 도킹 기준 구조 결정을 안건화할 것을 권고한다. 기준 구조 변경은 A-01/A-05/A-09 모든 산출물에 파급되므로, **이 결정이 선행되어야** MM-GBSA 도입(R-11) 로드맵도 의미가 생긴다.

**D-2 (방향 확인)**

SST14 레퍼런스 ΔG 재산출 — 포켓 내부 배치가 성공한 FlexPepDock 결과가 현재 없으므로, 7T10 기반 초기 구조 또는 HADDOCK/ZDOCK 수동 배치 후 재산출을 결정할 필요가 있다. 현재 553.857 REU 값은 Fallback conformation 기반으로, PRST ranking의 ddg_score 정규화 기준으로 사용되어서는 안 된다.

**D-3 (중기 계획)**

네거티브 디자인의 정량화 수준 향상을 위해, 잔기별 에너지 분해(PyRosetta `per_residue_energies` 또는 MM-GBSA residue decomposition)를 selectivity scoring에 통합하는 방안을 Q3 작업으로 검토할 것을 권고한다. Gervasoni 2024 CSBJ(DOI: 10.1016/j.csbj.2024.03.005)의 MD 기반 서브타입 잔기 기여 분석이 설계 근거로 활용 가능하다.

---

## 6. 한 줄 핵심 메시지

7XNA(octreotide 복합체) 기반 포켓 정의는 7T10(SST-14 복합체) 미검증으로 pharmacophore 배치 해석이 불완전하고, Boltz 도킹 3종 모두 포켓 외부 배치로 산출된 ΔG 기준선(553.857 REU)은 결합 상태 에너지를 반영하지 않아 PRST ranking 신뢰성의 구조생물학적 선결 조건이 충족되지 않은 상태다.

---

## §검증 필요 항목

| ID | 항목 | 검증 방법 |
|----|------|----------|
| BV-01 | 7T10 vs 7XNA TM5/TM6 포켓 잔기 국소 RMSD | 7T10 PDB 취득 후 PyMOL cealign + per-residue distance |
| BV-02 | Boltz_2 SG-SG 0.712 Å의 원인(CIF→PDB 변환 오류 또는 모델 오류) | `SSTR2_SST14_complex_boltz_2.pdb` CYS SG 좌표 직접 확인 |
| BV-03 | `selectivity_runner.py` 잔기 수준 에너지 분해 구현 여부 | grep per_residue selectivity_runner.py |
| BV-04 | de novo 경로(RFdiffusion/ProteinMPNN) 출력물의 Cys3-Cys14 SS bond 자동 검증 단계 유무 | Silo A 파이프라인 코드 점검 |
| BV-05 | 포켓 배치 실패 조건에서의 ΔG가 composite_scorer 정규화에 실제 사용되는지 | `composite_scorer.py` ddg_score 입력 경로 추적 |

---

*reviewer-biology | 2026-06-01 | 구조·SS bond·GPCR 결합 메커니즘 도메인*
