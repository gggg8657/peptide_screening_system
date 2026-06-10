# 회의 액션 아이템 대응 현황

---

## A-01: PepCalc/PeptideCutter → Step 8 혈청 t1/2 예측
| 항목 | 내용 |
|------|------|
| **담당** | AI팀 (김소연) |
| **기한** | 2주 내 |
| **현재 상태** | ⚠️ 부분 구현 |
| **구현 내용** | step08_stability.py에 반감기 예측 규칙 기반 모듈 존재. pepADMET conda env + 모델 설치됨. |
| **미완** | PepCalc/PeptideCutter 직접 통합 안 됨. 현재 규칙 기반(프로테아제 사이트 수 기반 추정). API 연동 또는 로컬 구현 필요. |
| **다음 단계** | ExPASy PeptideCutter API 연동 or BioPython ProtParam 통합 |

---

## A-02: ADMETlab 3.0 API → 상위 21개 후보 ADMET 프로파일
| 항목 | 내용 |
|------|------|
| **담당** | AI팀 |
| **기한** | 2주 내 |
| **현재 상태** | ✅ 구현됨 |
| **구현 내용** | Backend `/api/admet/batch` + `/api/pharmacology/batch` 엔드포인트. 14개 약리학 속성(GRAVY, pI, MW, 프로테아제 사이트 등) + ADMET 예측(nephrotox 포함). |
| **미완** | ADMETlab 3.0 외부 API 직접 연동은 안 됨 — 로컬 규칙 기반 예측. 외부 API 연동 시 정확도 향상 가능. |
| **다음 단계** | 최종 후보 확정 후 일괄 ADMET 생성 가능 |

---

## A-03: SSTR1/3/4/5 구조 + 선택성 스크리닝
| 항목 | 내용 |
|------|------|
| **담당** | AI팀 |
| **기한** | 즉시 |
| **현재 상태** | ✅ 구현됨 |
| **구현 내용** | - SSTR1~5 실험 구조 CIF 다운로드 완료 (cryo-EM/X-ray, AlphaFold 아님) |
| | - Selectivity 모듈: 5 API 엔드포인트 (receptors, run, status, results, jobs) |
| | - SelectivityRunner + offtarget_dock.py (PyRosetta FlexPepDock) |
| | - WSM/MSM/SR 스코어링 + Tier 분류 (Tier1 ≤-1.5, Tier2 ≤-2.0, Tier3 ≤-3.0) |
| | - SelectivityPage UI (Radar + Heatmap + 테이블) |
| **미완** | AutoDock Vina 배치는 미구현 — PyRosetta FlexPepDock으로 대체 (더 정밀). 실제 후보 대상 selectivity 분석 미실행 (파이프라인 정상화 후 진행). |
| **다음 단계** | 최종 후보 확정 → `/api/selectivity/run` 실행 |

---

## A-04: Critic Agent ClusterReport (A~E 분류) 추가
| 항목 | 내용 |
|------|------|
| **담당** | AI팀 (김소연) |
| **기한** | 1개월 내 |
| **현재 상태** | ❌ 미착수 |
| **분류 기준** | |
| | A – 결합 엘리트: ddG ≤ -8.0 + clash ≤ 5 + pLDDT ≥ 75 |
| | B – 선택성 특화: SSTR2 ddG 낮음 + off-target ddG ≥ -5.0 (차이 ≥ 3) |
| | C – 안정성 강화: Instability Index < 30 + BLOSUM62 높음 |
| | D – 방사화학 최적: GRAVY 중간 + 양전하 최소 + 킬레이터 최적 |
| | E – 탐색 후보: 비보존 치환, 새로운 접촉 패턴 |
| **현재 Critic** | 6가지 실패 유형만 분류 (LOW_PLDDT, GOOD_DOCK_BAD_DDG 등). A~E 클러스터 분류 없음. |
| **다음 단계** | Critic 확장 시 A~E 분류 로직 추가. 18개 메트릭 중 5개만 참조하는 문제도 동시 해결. |

---

## A-05: Step 3B 재설계 (BLOSUM62 Tier 1/2/3 병렬)
| 항목 | 내용 |
|------|------|
| **담당** | AI팀 |
| **기한** | 1개월 내 |
| **현재 상태** | ⚠️ 부분 |
| **구현 내용** | 현재 step03b는 BLOSUM62 단일 전략. Silo B에서 PyRosetta flow가 mutation+dock을 처리. |
| **미완** | Tier 1(BLOSUM62 보존)/Tier 2(물리화학 필터)/Tier 3(비제한) 병렬 구조 미구현. 현재는 BLOSUM62 씨드 → FlexPepDock 단일 경로. |
| **다음 단계** | step03b에 3개 Tier 분기 추가 + 각 Tier별 후보 수 config화 |

---

## A-06: 합성 견적 문의 (RI팀)
| 항목 | 내용 |
|------|------|
| **담당** | RI팀 |
| **현재 상태** | AI팀 범위 밖 (RI팀 액션) |

---

## A-07: C18 부착 변형체 설계 (RI팀)
| 항목 | 내용 |
|------|------|
| **담당** | RI팀 |
| **현재 상태** | AI팀 범위 밖 (RI팀 액션) |

---

## A-08: 13-메트릭 패널 확장 (+3 메트릭)
| 항목 | 내용 |
|------|------|
| **담당** | AI팀 |
| **기한** | 2주 내 |
| **현재 상태** | ⚠️ 부분 |
| **추가 필요** | |
| | - Selectivity Margin Index: ✅ WSM/MSM 구현됨 (selectivity_runner.py) |
| | - Radiolysis Susceptibility: ⚠️ step08에 간이 추정 있으나 정밀 모듈 미구현 |
| | - Chelator Binding Compatibility: ❌ 미구현 (Lys/N-말단 킬레이터 부착 적합성 평가) |
| **다음 단계** | Critic 확장(A-04) 시 3개 메트릭 동시 추가 |

---

## A-09: 아주대 JCIM 논문 검토
| 항목 | 내용 |
|------|------|
| **담당** | AI팀 + RI팀 |
| **현재 상태** | ❌ 미착수 (논문 검토 필요) |

---

## A-10: RCP 안정성 예측 모듈 (radiolysis risk)
| 항목 | 내용 |
|------|------|
| **담당** | AI팀 |
| **기한** | 1개월 내 |
| **현재 상태** | ⚠️ 간이 구현 |
| **구현 내용** | step08에 아미노산별 방사선분해 감수성 점수 기반 간이 추정 존재. |
| **미완** | 정밀 RCP 안정성 모델 미구현. 실험 데이터 기반 보정 필요. |

---

## A~E 클러스터 분류 대응

| 클러스터 | 현재 시스템에서 판별 가능? | 필요 메트릭 | 상태 |
|---------|-------------------------|-----------|------|
| **A – 결합 엘리트** | ⚠️ | ddG, clash, pLDDT, FWKT 접촉 | ddG+clash+pLDDT 있음. FWKT 접촉 분석 미구현. |
| **B – 선택성 특화** | ✅ | SSTR2 ddG + off-target ddG | Selectivity 모듈 구현됨 (WSM, SR) |
| **C – 안정성 강화** | ⚠️ | Instability Index, BLOSUM62, 프로테아제 | 약리학 패널에 부분 포함. Instability Index 직접 계산 필요. |
| **D – 방사화학 최적** | ⚠️ | GRAVY, 전하, 킬레이터 위치 | GRAVY/pI 있음. 킬레이터 호환성 미구현. |
| **E – 탐색 후보** | ❌ | 비보존 치환, 구조 패턴 | 자동 분류 로직 없음. |

---

## 요약

| 상태 | 액션 수 |
|------|---------|
| ✅ 완료 | 2 (A-02, A-03) |
| ⚠️ 부분 | 5 (A-01, A-05, A-08, A-10, 클러스터) |
| ❌ 미착수 | 2 (A-04, A-09) |
| RI팀 | 2 (A-06, A-07) |
