#
액션 아이템
담당
기한
우선순위
A-01
PepCalc/PeptideCutter를 AI 파이프라인 Step 8에 통합하고 SST-14 변형체 혈청 t1/2 예측값 산출
AI팀 (김소연)
2주 내
높음
A-02
ADMETlab 3.0 API를 활용하여 현재 상위 21개 후보 ADMET 프로파일 일괄 생성 (킬레이터 미부착 기준)
AI팀
2주 내
높음
A-03
SSTR1/3/4/5 AlphaFold 구조 다운로드 및 도킹 프로토콜(AutoDock Vina 배치) 구성. 선택성 스크리닝 파이프라인 연결
AI팀
2주 내
즉시
A-04
Critic Agent에 ClusterReport 기능(A~E 분류) 추가. 기존 실패 유형 분석은 로그 전용으로 전환
AI팀 (김소연)
1개월 내
높음
A-05
BLOSUM62 Tier 1 / 물리화학 필터 Tier 2 / 비제한 Tier 3 병렬 후보 생성 구조로 Step 3B 재설계
AI팀
1개월 내
높음
A-06
RI팀: Peptron, HLB PEP, Anygen에 DOTA-펩타이드 합성 견적 및 가능 여부 문의 (표준 DOTA-TATE 포함)
RI팀
2주 내
높음
A-07
RI팀: SST-14 상위 3개 후보의 Lys/N-말단 C18 부착 변형체 설계안 작성 후 AI팀과 구조 검토 미팅
RI팀
1개월 내
보통
A-08
13-메트릭 패널에 Selectivity Margin Index, Radiolysis Susceptibility, Chelator Binding Compatibility 추가
AI팀
2주 내
높음
A-09
아주대 김민규 교수팀 JCIM 논문 전문 검토 후 방법론 중 파이프라인 적용 가능 항목 정리 보고
AI팀 + RI팀
2주 내
보통
A-10
현재 RCP 안정성 예측 모듈(radiolysis risk 추정) 구현 여부 확인 및 없을 시 간이 구현
AI팀
1개월 내
보통

--- 
클러스터
유형명
분류 기준
우선순위 부여 방식
A – 결합 엘리트
High Affinity Core
ddG ≤ −8.0 kcal/mol + 클래시 ≤ 5 + pLDDT ≥ 75. FWKT 포켓 접촉 유지.
최우선 합성 대상. 표지(68Ga/177Lu) 후 재측정.
B – 선택성 특화
Subtype Selective
SSTR2 ddG 낮음 + SSTR1/3/4/5 ddG ≥ −5.0 (차이 ≥ 3 kcal/mol). ECL2 접촉 패턴 특이.
2순위. 선택성 >100× 목표 충족 가능성 높음.
C – 안정성 강화
Stability-First
Instability Index < 30 + BLOSUM62 누적 점수 높음 + 프로테아제 hotspot 감소. 혈청 t1/2 예측 상위.
3순위. 반감기 연장 후보(TPP-B/C) 공급원.
D – 방사화학 최적
Radiochem Friendly
GRAVY 중간(−1.0~+0.5) + 양전하 최소(신장 재흡수 리스크 저감) + 킬레이터 부착 위치 최적.
4순위. 표지 QC 통과 가능성 높음.
E – 탐색 후보
Novel Scaffold
비보존 치환 포함, Tier 3 출신. ddG 중간이나 구조적으로 새로운 접촉 패턴.
5순위. 리스크 높으나 혁신 가능성. MD 추가 검증 후 판단.
