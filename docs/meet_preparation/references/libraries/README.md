# Libraries — 도구 매트릭스

접근 확인일: 2026-06-01

## 반감기 / 안정성 예측 도구

| 도구 | URL | 환경 | 라이선스 | 펩타이드 지원 | 혈중 반감기 | 장내 반감기 | 검증 상태 |
|------|-----|------|---------|------------|-----------|-----------|---------|
| ProtParam | https://web.expasy.org/protparam/ | 웹 | 공개 | O (선형 제한) | 추정값 (ProtParam 공식) | X | 통과 |
| PlifePred | https://webs.iiitd.edu.in/raghava/plifepred/ | 웹 | 공개 | O | O (실험 기반) | X | 통과 |
| HLP | https://webs.iiitd.edu.in/raghava/hlp/ | 웹 | 공개 | O | X | O | 통과 |
| PeptideRanker | http://distilldeep.ucd.ie/PeptideRanker/ | 웹 | 공개 | O | X (bioactivity) | X | 통과 (서버 불안정) |

## ADMET 예측 도구

| 도구 | URL | 환경 | 라이선스 | 펩타이드 전용 | 엔드포인트 수 | 검증 상태 |
|------|-----|------|---------|------------|------------|---------|
| pepADMET | https://github.com/ifyoungnet/pepADMET | GitHub + 웹 | GPL-3.0 | O (전용) | 19 | 통과 |
| ADMET-AI | https://github.com/swansonk14/admet_ai | GitHub + 웹 | MIT | 소분자 중심 | TDC 기준 | 통과 |
| ADMETlab 3.0 | https://admetlab3.scbdd.com/ | 웹 (API 제공) | 공개 API | 일부 | 119 | 통과 |

## 자유에너지 / 도킹 도구

| 도구 | URL | 환경 | 라이선스 | GPU 필요 | 최신 버전 | 검증 상태 |
|------|-----|------|---------|---------|---------|---------|
| DiffDock | https://github.com/gcorso/DiffDock | GitHub | MIT | O | v1.1.3 (2024-09-04) | 통과 |
| Boltz-2 | https://github.com/jwohlwend/boltz | GitHub | MIT | O | v2.2.1 (2025-09-08) | 통과 |
| gmx_MMPBSA | https://github.com/Valdes-Tresanco-MS/gmx_MMPBSA | GitHub | GPL-3.0 | 선택 | v1.6.5 (2026-05-23) | 통과 |
| OpenMM | https://openmm.org/ | Python | MIT/LGPL | O (GPU 가속) | 8.x | 통과 |
| OpenFE | https://openfree.energy/ | Python | MIT | 선택 | v1.0+ (2024-05 stable) | 통과 |

## 최적화 도구

| 도구 | URL | 환경 | 라이선스 | NSGA-II | 검증 상태 |
|------|-----|------|---------|---------|---------|
| pymoo | https://pymoo.org/ | Python | Apache-2.0 | O | 통과 |

## 우선 권고 조합 (본 프로젝트 SSTR2 펩타이드)

```
A-02 (반감기):   PlifePred (혈중) + HLP (장내) → ProtParam (보조)
A-03 (ADMET):   pepADMET (펩타이드 전용) → ADMETlab 3.0 (추가 확인)
A-05 (재채점):  gmx_MMPBSA (MM-GBSA) + OpenFE (alchemical FEP)
A-06 (도킹):    Boltz-2 (구조+친화도 통합) → DiffDock (소분자 보조)
A-04 (최적화):  pymoo (NSGA-II Pareto)
```
