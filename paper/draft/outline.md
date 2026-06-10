# 논문 아웃라인: Multi-Agent AI Co-Scientist for Radiopharmaceutical Discovery

**제목안 (한국어)**: 멀티에이전트 AI Co-Scientist 시스템 기반 방사성의약품 후보 물질 탐색 — SSTR2 타겟 사례 연구
**제목안 (영문)**: Multi-Agent AI Co-Scientist System for Radiopharmaceutical Candidate Discovery: A Case Study on SSTR2 Targeting

**마감**: 2026-02-26
**학회**: (확인 필요)

---

## 논문 포커스

핵심 주장: **멀티에이전트 AI 시스템이 방사성의약품 후보 탐색의 전체 워크플로우를 자동화할 수 있으며, 특히 에이전트 간 역할 분화와 협업 구조가 전통적 단일 파이프라인 대비 품질·확장성에서 우위를 가진다.**

차별점:
1. 에이전트 시스템 자체가 연구 대상 (약물이 아닌 AI 시스템이 주인공)
2. 멀티 MCP (Cursor + Codex + Claude Code) 기반의 실제 개발 방법론
3. Competing Hypotheses Pattern으로 아키텍처 결정을 검증

---

## 섹션 구조

### 1. Introduction (서론) — 1~1.5페이지
- 방사성의약품의 중요성과 후보 탐색의 어려움
  - SSTR2 타겟: 신경내분비종양 진단/치료 핵심 수용체
  - 기존 웨트랩 기반 탐색의 한계: 시간, 비용, 인력
- AI for Drug Discovery의 최근 동향
  - 생성형 AI + 구조 예측 (AlphaFold, ESMFold)
  - 에이전트 기반 AI 시스템의 부상 (AI Co-Scientist)
- 연구 동기
  - 단일 모델이 아닌 **멀티에이전트 협업** 시스템의 필요성
  - 웨트랩에 제안할 후보군을 자동으로 도출하는 end-to-end 파이프라인
- 핵심 기여 3가지 미리 제시

### 2. Related Work (관련 연구) — 1~1.5페이지
- **2.1 AI-Driven Drug Discovery**
  - RFdiffusion, ProteinMPNN, DiffDock, MolMIM
  - NVIDIA NIM API 기반 클라우드 추론
- **2.2 Multi-Agent AI Systems**
  - LLM 기반 에이전트 시스템 (AutoGPT, MetaGPT, CAMEL)
  - AI Co-Scientist 개념 (Google DeepMind)
  - Agent 역할 분화: Planner-Executor-Critic 패턴
- **2.3 Model Context Protocol (MCP) 기반 개발**
  - MCP 표준과 에이전트 통합
  - Cursor + Codex CLI + Claude Code 멀티 MCP 아키텍처

### 3. System Architecture (시스템 아키텍처) — 2~2.5페이지 ★핵심
- **3.1 전체 구조: Dual-Silo 파이프라인**
  - Silo A: 3-Arm Virtual Screening (소분자, 펩타이드, de novo)
  - Silo B: HIL SST-14 Mutant Generation (제약 기반 돌연변이)
  - [Figure 1: 전체 아키텍처 다이어그램]
- **3.2 6-Agent + Hybrid (3 LLM + 3 Code) 구조**
  - 에이전트 역할 분화 근거
  - LLM vs Code 에이전트 분류 기준 (LLM Necessity Score)
  - [Table 1: 에이전트별 역할, 실행 모드, 근거]
  - [Figure 2: 에이전트 협업 플로우 다이어그램]
- **3.3 LLM 선정: Competing Hypotheses Pattern**
  - 4명의 경쟁 분석 에이전트 (Advocate-6Agent, Advocate-Hybrid, LLM-Evaluator, Devil's Advocate)
  - [Table 2: LLM 후보 벤치마크 비교]
  - Qwen 2.5 7B 선정 근거
- **3.4 QC Gate 메커니즘**
  - 4-Stage Gate (pLDDT, Docking, Rosetta, Selectivity)
  - 수렴 기준: ddG 개선 < 0.5 kcal/mol × 2회 연속

### 4. Multi-MCP 기반 개발 방법론 — 1~1.5페이지 ★차별점
- **4.1 멀티 MCP 오케스트레이션 아키텍처**
  - Cursor (IDE 통합, 코드 수정, Linear/GitHub 연동)
  - Codex CLI (비판적 코드 감사, 멀티에이전트 분석)
  - Claude Code (자율 추론, Agent Teams, 웹 리서치)
  - [Figure 3: 멀티 MCP 협업 아키텍처]
- **4.2 에이전트 협업 사례**
  - 3-way 병렬 분석: CHA-78 (Codex) + CHA-79 (Claude) + CHA-86 (Cursor)
  - Competing Hypotheses: 4명 Agent Team이 아키텍처 결정
- **4.3 MCP 통합 기술적 과제 및 해결**
  - proxy.mjs를 통한 스키마 호환성 해결
  - 멀티에이전트 파일 충돌 방지 전략

### 5. Implementation (구현) — 1~1.5페이지
- **5.1 7-Step 계산 파이프라인**
  - Step01 (Receptor) → Step07 (Analysis) 흐름
  - NVIDIA NIM API 통합
- **5.2 에이전트 구현 상세**
  - BaseAgent 인터페이스 + execute() 패턴
  - Critic의 FAILURE_ACTION_MAP (6 실패 유형 × 13 교정 액션)
  - ParameterValidator 보안 메커니즘
- **5.3 Silo B: 제약 기반 돌연변이 생성**
  - ConstraintCompiler + MutantGenerator
  - 3단계 HIL Gate

### 6. Results & Evaluation (결과) — 1.5~2페이지
- **6.1 아키텍처 검증 결과**
  - Option A vs B vs C 비교 (Table: 8개 기준)
  - 합의: 3:1로 Option C 채택
- **6.2 에이전트 협업 성과**
  - P0 치명적 버그 3건 발견 + 수정 (_invoke_agent 스텁, Schema 검증, Step05b)
  - P1 중요 버그 3건 발견 + 수정
  - LLM 호출 50% 절감 (6→3 calls/iteration)
- **6.3 파이프라인 실행 결과**
  - Silo A: 3-Arm 후보 89개 생성, 통합 랭킹 완료
  - Silo B: 33개 테스트 통과 (9 + 24)
  - [Table 3: Silo A 결과 요약]
  - [Table 4: 에이전트 기여도 분석]
- **6.4 멀티 MCP 개발 효율성**
  - 병렬 에이전트 활용 시 개발 속도 향상
  - 비판적 분석의 품질 기여

### 7. Discussion (논의) — 0.5~1페이지
- AI 에이전트의 과학적 추론 신뢰성 한계
- 8B 모델의 Critic 역할 수행 능력과 한계
- 멀티 MCP 시스템의 비용-효과 트레이드오프
- 실제 웨트랩 검증까지의 갭

### 8. Conclusion (결론) — 0.5페이지
- **기여 1**: 방사성의약품 후보 탐색을 위한 6-Agent Hybrid AI Co-Scientist 시스템 설계 및 검증
- **기여 2**: Competing Hypotheses Pattern을 활용한 객관적 아키텍처 결정 방법론 제시
- **기여 3**: 멀티 MCP 기반 AI 에이전트 개발 워크플로우의 실용성 입증

---

## Figure 목록 (예상 5~6개)
1. **Fig 1**: 전체 시스템 아키텍처 (Dual-Silo + 6-Agent)
2. **Fig 2**: 에이전트 협업 플로우 다이어그램
3. **Fig 3**: 멀티 MCP 오케스트레이션 아키텍처
4. **Fig 4**: QC Gate 흐름도
5. **Fig 5**: Competing Hypotheses 분석 프로세스
6. **Fig 6**: 파이프라인 실행 결과 시각화

## Table 목록 (예상 4~5개)
1. **Table 1**: 에이전트별 역할, 실행 모드, LLM Necessity Score
2. **Table 2**: LLM 후보 모델 벤치마크 비교 (MMLU, JSON, Context)
3. **Table 3**: 아키텍처 옵션 비교 (8개 기준)
4. **Table 4**: Silo A 실행 결과 요약
5. **Table 5**: 발견된 버그/개선사항 분류

---

## 핵심 참고문헌 (초안)
1. Gottwalt et al. "AI Co-Scientist" — Google DeepMind, 2024
2. Watson et al. "RFdiffusion" — Nature, 2023
3. Dauparas et al. "ProteinMPNN" — Science, 2022
4. Corso et al. "DiffDock" — ICLR, 2023
5. Lin et al. "ESMFold" — Science, 2023
6. Qwen Team. "Qwen 2.5 Technical Report" — 2024
7. Hong et al. "MetaGPT" — ICLR, 2024
8. Li et al. "CAMEL" — NeurIPS, 2023
9. MCP Specification — Anthropic, 2024
10. Cursor IDE Documentation — 2025
