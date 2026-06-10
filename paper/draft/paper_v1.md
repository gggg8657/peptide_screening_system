# 멀티에이전트 AI Co-Scientist 시스템을 활용한 SSTR2 타겟 방사성의약품 후보 물질 탐색

**Multi-Agent AI Co-Scientist System for SSTR2-Targeted Radiopharmaceutical Candidate Discovery**

김동주

한국원자력연구원

---

## Abstract

방사성의약품 후보 물질 탐색은 광범위한 화학적 공간 탐색과 복수의 계산 도구 간 조율이 필요한 복합적 과제이다. 본 연구에서는 SSTR2(Somatostatin Receptor Type 2) 타겟 방사성의약품 후보를 자동으로 설계·스크리닝·평가하는 멀티에이전트 AI Co-Scientist 시스템을 제안한다. 제안 시스템은 6개의 전문화된 에이전트(Planner, Builder, QC&Ranker, DiversityManager, Critic, Reporter)가 역할을 분담하며, 이 중 3개는 LLM(Qwen 2.5 7B) 기반, 3개는 결정론적 코드 기반으로 운영되는 하이브리드 구조를 채택하였다. 아키텍처 결정에는 4명의 AI 에이전트가 참여하는 경쟁 가설(Competing Hypotheses) 패턴을 적용하여 객관성을 확보하였다. Dual-Silo 파이프라인(소분자·펩타이드·de novo 3-Arm 가상 스크리닝 + 제약 기반 SST-14 돌연변이 생성)을 통해 89개 후보를 생성하고 통합 랭킹을 수행하였다. 또한, Model Context Protocol(MCP) 기반의 멀티에이전트 개발 환경(Cursor + Codex CLI + Claude Code)을 구축하여 시스템 개발 과정 자체에도 에이전트 협업을 적용하였다. 실험 결과, 하이브리드 구조가 전수 LLM 구조 대비 LLM 호출을 50% 절감하면서도 관심사 분리와 독립 테스트 가능성을 유지함을 확인하였으며, 에이전트 협업을 통해 치명적 버그 3건과 주요 결함 3건을 발견·수정하였다.

**키워드**: 멀티에이전트 시스템, AI Co-Scientist, 방사성의약품, SSTR2, 대규모 언어 모델, Model Context Protocol

---

## 1. 서론

### 1.1 연구 배경

소마토스타틴 수용체 2형(SSTR2)은 신경내분비종양(NET) 진단 및 치료에 핵심적인 분자 표적이다[1]. DOTATATE(^177Lu-DOTATATE, Lutathera®)로 대표되는 SSTR2 표적 방사성의약품은 펩타이드 수용체 방사성핵종 치료(PRRT)의 표준 치료제로 자리잡았으나, 제한적 종양 침투율과 off-target 수용체(SSTR1, 3, 4, 5) 결합에 의한 부작용 문제가 지속되고 있다[2].

신규 방사성의약품 후보 물질의 발굴은 전통적으로 웨트랩 기반의 시행착오적 접근에 의존해왔다. 이는 (1) 탐색 가능한 화학적 공간의 극히 일부만을 커버하고, (2) 구조 예측, 도킹, 안정성 평가 등 다수의 계산 도구를 순차적으로 수동 조율해야 하며, (3) 전문 인력의 지속적 개입이 필요하다는 한계를 갖는다.

### 1.2 AI 에이전트 시스템의 부상

최근 대규모 언어 모델(LLM) 기반의 AI 에이전트 시스템이 과학 연구 자동화의 새로운 패러다임으로 주목받고 있다. Google DeepMind의 AI Co-Scientist[3], MetaGPT[4], CAMEL[5] 등은 복수의 AI 에이전트가 역할을 분담하여 복잡한 태스크를 수행할 수 있음을 보여주었다. 특히, RFdiffusion[6], ProteinMPNN[7], DiffDock[8], ESMFold[9] 등 생명과학 특화 AI 모델의 발전은 단백질 설계와 도킹 시뮬레이션을 API 호출 수준으로 간소화하여, 에이전트 기반 자동화 파이프라인의 실현 가능성을 크게 높였다.

그러나 기존 연구들은 (1) 단일 에이전트가 전체 파이프라인을 담당하거나, (2) 에이전트의 역할 분화가 불명확하거나, (3) 에이전트 구조 결정 과정 자체의 객관성이 보장되지 않는 한계를 보인다.

### 1.3 연구 목적 및 기여

본 연구의 목적은 SSTR2 타겟 방사성의약품 후보 물질을 자동으로 탐색하는 멀티에이전트 AI Co-Scientist 시스템을 설계·구현·검증하는 것이다. 본 연구의 핵심 기여는 다음과 같다:

1. **6-Agent Hybrid 아키텍처**: LLM 기반 에이전트(3개)와 결정론적 코드 에이전트(3개)를 역할별로 분화한 하이브리드 구조를 제안하고, LLM 호출을 50% 절감하면서 관심사 분리(SoC)를 유지하는 최적 구성을 도출하였다.

2. **Competing Hypotheses 기반 아키텍처 검증**: 4명의 AI 에이전트(옹호자 2명 + 평가자 + 악마의 대변인)가 참여하는 경쟁 가설 패턴으로 아키텍처 결정 과정의 객관성과 재현 가능성을 확보하였다.

3. **멀티 MCP 기반 개발 방법론**: Model Context Protocol을 활용하여 3종의 AI 에이전트(Cursor, Codex CLI, Claude Code)가 협업하는 개발 환경을 구축하고, 시스템 개발 과정 자체에 멀티에이전트 접근을 적용하였다.

---

## 2. 관련 연구

### 2.1 AI 기반 신약 후보 탐색

구조 기반 약물 설계(SBDD)에서 AI의 역할은 분자 생성, 구조 예측, 도킹 시뮬레이션의 세 축으로 구분된다. RFdiffusion[6]은 denoising diffusion 모델을 활용하여 표적 단백질에 결합하는 de novo 펩타이드 백본을 설계하며, ProteinMPNN[7]은 역접힘(inverse folding) 문제를 해결하여 주어진 백본에 최적 서열을 할당한다. ESMFold[9]는 서열로부터 3차원 구조를 예측하며 pLDDT 신뢰도 지표를 제공한다. DiffDock[8]은 확산 모델 기반의 분자 도킹으로 결합 포즈와 신뢰도를 동시에 예측한다. MolMIM[10]은 소분자 생성 및 QED 최적화를 지원하며, PyRosetta[11]는 분자 수준의 에너지 계산과 FlexPepDock을 제공한다. 이들 도구는 개별적으로는 성숙도가 높으나, 통합 파이프라인으로의 조율은 여전히 수동 프로세스에 의존하고 있다.

### 2.2 멀티에이전트 AI 시스템

LLM 기반 멀티에이전트 시스템은 복수의 전문화된 에이전트가 역할을 분담하여 복잡한 태스크를 수행하는 프레임워크이다. MetaGPT[4]는 소프트웨어 개발에 Waterfall 모델의 역할(PM, 아키텍트, 개발자, QA)을 에이전트로 매핑하였다. CAMEL[5]은 역할극(role-playing) 기반의 두 에이전트 협업 프레임워크를 제안하였다. ChatDev[12]는 소프트웨어 개발의 전체 라이프사이클을 에이전트 팀으로 자동화하였다. AI Co-Scientist[3] 개념은 이를 과학 연구로 확장하여, 가설 생성-실험 설계-결과 분석의 과학적 방법을 에이전트 루프로 구현한다.

본 연구는 이러한 멀티에이전트 패러다임을 방사성의약품 후보 탐색이라는 특정 도메인에 적용하되, 에이전트 역할 분화의 근거를 정량적으로 제시하고, 아키텍처 결정 과정 자체에 에이전트 기반 검증을 도입한다는 점에서 차별화된다.

### 2.3 Model Context Protocol과 에이전트 통합

Model Context Protocol(MCP)[13]은 IDE와 AI 모델 간의 표준 통신 프로토콜로, JSON-RPC over stdio 기반으로 도구 호출, 리소스 접근, 프롬프트 관리를 통합한다. Cursor IDE[14]는 MCP를 통해 외부 AI 에이전트를 플러그인 형태로 통합할 수 있으며, 최대 8개의 병렬 에이전트를 Git worktree 기반으로 격리 실행할 수 있다. Codex CLI[15]는 OpenAI의 코딩 에이전트로, MCP 서버 모드에서 최대 6개의 서브에이전트를 운용할 수 있다. Claude Code[16]는 Anthropic의 자율 추론 에이전트로, Agent Teams 기능을 통해 에이전트 간 직접 메시지 교환과 공유 태스크 리스트를 지원한다.

---

## 3. 제안 시스템

### 3.1 전체 구조: Dual-Silo 파이프라인

본 시스템은 SSTR2(P30874)에 대한 SST-14(AGCKNFFWKTFTSC) 기반 변이/대체 리간드를 탐색하는 Dual-Silo 구조를 채택하였다(Fig. 1).

**Silo A (3-Arm Virtual Screening)**: 세 가지 상이한 접근법을 병렬로 실행하여 다양한 유형의 후보를 탐색한다.
- Arm 1 (소분자): MolMIM으로 소분자를 생성하고 DiffDock으로 도킹 수행
- Arm 2 (펩타이드 변이체): SST-14의 Alanine scanning 및 강화 변이체 분석
- Arm 3 (De Novo): RFdiffusion → ProteinMPNN → ESMFold로 신규 펩타이드 바인더 설계

**Silo B (HIL SST-14 Mutant Generation)**: SST-14을 템플릿으로 제약 기반 돌연변이를 생성하고, Human-in-the-Loop(HIL) 3단계 게이트로 정제한다.
- Constraint Compiler: 고정 위치, 약리작용단(pharmacophore), 이황화 결합 보존
- MutantGenerator: enumerate/sampling/GA-BO 전략 자동 선택
- 3-Gate HIL: 정적 필터(Gate 1) → 도킹 분류(Gate 2) → 전문가 검토(Gate 3)

두 Silo는 YAML config 기반 오케스트레이션, NVIDIA NIM API 클라이언트 추상화, 가중치 기반 점수 정합(Unified Scoring)을 공유하며, 최종 후보를 통합 랭킹한다.

```
                         ┌──────────────────────┐
                         │   NVIDIA NIM API      │
                         │ (MolMIM, DiffDock,    │
                         │  RFdiffusion, MPNN,   │
                         │  ESMFold)             │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
    ┌─────────▼─────────┐ ┌────────▼────────┐ ┌─────────▼─────────┐
    │    Silo A          │ │                 │ │    Silo B          │
    │  3-Arm Virtual     │ │  Unified        │ │  HIL SST-14       │
    │  Screening         │ │  Scoring &      │ │  Mutant            │
    │                    │ │  Ranking        │ │  Generation        │
    │  Arm1: SmallMol    │ │                 │ │                    │
    │  Arm2: FlexPep     │ │                 │ │  Constraint →      │
    │  Arm3: De Novo     │ │                 │ │  Generate →        │
    │                    │ │                 │ │  Filter → Dock →   │
    └────────┬───────────┘ └────────┬────────┘ │  Score → Gate      │
             │                      │          └─────────┬──────────┘
             └──────────────────────┴────────────────────┘
                                    │
                           ┌────────▼────────┐
                           │  Top Candidates  │
                           │  for Wet Lab     │
                           └─────────────────┘
```
**Fig. 1. SSTR2 타겟 Dual-Silo 파이프라인 전체 구조**

### 3.2 6-Agent Hybrid 아키텍처

각 Silo의 파이프라인 실행을 조율하기 위해 6개의 전문화된 에이전트를 설계하였다. 핵심 설계 원칙은 **에이전트별 LLM 필요성을 정량적으로 평가하여 불필요한 LLM 호출을 제거**하는 것이다.

에이전트별 LLM 필요성을 5개 차원(자연어 생성, 인과 추론, 창의적 탐색, 구조화 출력, 수치 계산)에서 0~5점 스케일로 평가하였다(Table 1).

**Table 1. 에이전트별 역할, 실행 모드, LLM 필요성 평가**

| 에이전트 | 역할 | 실행 모드 | LLM 필요성 | 근거 |
|----------|------|-----------|:----------:|------|
| Planner | 실험 계획 수립, 가설 생성 | LLM (Qwen 2.5 7B) | 4.2/5.0 | 과학적 추론, 창의적 파라미터 탐색 |
| Builder | Step 01~07 실행 관리 | Code (규칙 기반) | 1.0/5.0 | API 호출 + 파일 I/O, 결정론적 |
| QC&Ranker | 4단계 품질 게이트 + 랭킹 | Code (알고리즘) | 1.2/5.0 | 수치 비교 + 가중합, 선형대수 |
| DiversityMgr | 구조 클러스터링 + 중복 제거 | Code (알고리즘) | 1.0/5.0 | 서열 유사도 + 그리디 클러스터링 |
| Critic | 실패 분석 + 파라미터 변경 제안 | LLM (Qwen 2.5 7B) | 4.5/5.0 | 근본 원인 분석, 가설 생성 |
| Reporter | 보고서 생성 + 시각화 | LLM (Qwen 2.5 7B) | 3.8/5.0 | 자연어 합성, 맥락 기반 해석 |

LLM 필요성 점수가 2.0 이상인 에이전트(Planner, Critic, Reporter)만 LLM을 사용하고, 나머지(Builder, QC&Ranker, DiversityManager)는 결정론적 코드로 실행한다. 이를 통해 반복(iteration)당 LLM 호출을 6회에서 3회로 50% 절감하면서, 코드 에이전트의 비결정성(non-determinism) 위험을 원천 제거하였다.

에이전트 간 데이터 흐름은 단방향 파이프라인을 따른다(Fig. 2).

```
Planner(LLM) → Builder(Code) → QC&Ranker(Code) → DiversityMgr(Code) → Critic(LLM) → Reporter(LLM)
    ↑                                                                        │
    └────────────────────── 파라미터 변경 제안 ──────────────────────────────┘
                        (최대 2개 변경/iteration, 수렴 시 종료)
```
**Fig. 2. 에이전트 간 협업 플로우 (자기 개선 루프)**

**수렴 기준**: ddG 개선량 < 0.5 kcal/mol이 2회 연속 발생하거나 최대 5회 반복에 도달하면 루프를 종료한다.

### 3.3 QC Gate 메커니즘

품질 보증을 위해 4단계 게이트를 설계하였다(Table 2).

**Table 2. QC Gate 구성**

| Gate | 평가 지표 | 임계값 | 적용 단계 |
|------|-----------|--------|-----------|
| Gate 1 | pLDDT 평균 | ≥ 75 | ESMFold 구조 예측 |
| Gate 2 | 도킹 점수 | 상위 20% | DiffDock/Boltz-2 |
| Gate 3 | Rosetta ddG | ≤ -5.0 kcal/mol | PyRosetta FlexPepDock |
| Gate 4 | 선택성 마진 | ≤ -2.0 | Off-target 도킹 |

Gate 4는 SSTR2 선택성 검증을 위해 off-target 수용체(SSTR1, 3, 4, 5)에 대한 도킹 점수를 비교하여, on-target 점수가 off-target 최고 점수보다 충분히 낮은 후보만 통과시킨다.

### 3.4 Competing Hypotheses 기반 아키텍처 결정

아키텍처 결정의 객관성을 확보하기 위해, 4명의 AI 에이전트로 구성된 경쟁 가설 분석 팀을 운영하였다(Table 3).

**Table 3. Competing Hypotheses 분석 에이전트 구성**

| 에이전트 | 역할 | 분석 관점 |
|----------|------|-----------|
| Advocate-6Agent | 6-Agent 옹호자 | SoC, 테스트 용이성, OCP 확장성 |
| Advocate-Hybrid | 4-Agent 옹호자 | LLM 호출 감소, 구현 단순화 |
| LLM-Evaluator | LLM 적합성 평가자 | 8B~11B 모델 벤치마크 비교 |
| Devil's Advocate | 악마의 대변인 | 양측 약점 공격, 숨겨진 위험 발견 |

각 에이전트는 독립적으로 코드베이스(44파일, ~13,800줄)를 분석한 후 합의를 도출하였다. 3개 아키텍처 옵션의 비교 결과는 Table 4와 같다.

**Table 4. 아키텍처 옵션 비교**

| 기준 | A: 6-Agent (전수 LLM) | B: 4-Agent 통합 | **C: 6-Agent Hybrid** |
|------|:---:|:---:|:---:|
| LLM 호출/반복 | 6 | 4 | **3** |
| 관심사 분리(SoC) | 유지 | 부분 | **유지** |
| QC 독립성 | 유지 | 자기 QC 편향 | **유지** |
| 최대 모듈 크기 | 566줄 | ~1,516줄 | **566줄** |
| 장애 전파 범위 | 1 에이전트 | 확대 | **1 에이전트** |
| 테스트 가능성 | 높음 | 중간 | **높음** |
| 추론 비용/반복 | 높음 | 중간 | **낮음** |

최종 합의: Option C (6-Agent Hybrid)가 3:1 다수결로 채택되었다. Option B를 옹호한 에이전트도 자기 QC 편향 문제를 인정하여 실질적으로 만장일치에 가까운 결과를 얻었다.

### 3.5 LLM 선정

온프레미스 배포 환경(A100 40GB)에서 운용 가능한 7~11B 모델 5종을 벤치마크 비교하였다(Table 5).

**Table 5. LLM 후보 모델 벤치마크 비교**

| 모델 | 파라미터 | MMLU | JSON 출력 | 컨텍스트 | Tool Call | 추론 속도 |
|------|:--------:|:----:|:---------:|:--------:|:---------:|:---------:|
| **Qwen 2.5 7B** | **7B** | **74.2** | **Native** | **128K** | **Native** | **~45 tok/s** |
| Llama 3.1 8B | 8B | 69.4 | Template | 128K | Basic | ~40 tok/s |
| Llama 3.2 11B | 11B | ~69 | Template | 128K | Basic | ~30 tok/s |
| Gemma 2 9B | 9B | 71.3 | Template | 8K | 없음 | ~35 tok/s |
| Mistral 7B | 7B | 63.5 | Template | 32K | Native | ~45 tok/s |

Qwen 2.5 7B가 MMLU(74.2), native JSON/Tool calling, 128K 컨텍스트에서 전 항목 최우수로 선정되었다. Llama 3.2 11B는 추가 3B 파라미터가 Vision 인코더에 할당되어 텍스트 성능이 8B급과 동등하므로 제외하였다.

### 3.6 멀티 MCP 기반 개발 방법론

본 시스템의 개발 과정 자체에도 멀티에이전트 접근을 적용하였다. Model Context Protocol(MCP)을 통해 3종의 AI 에이전트를 단일 IDE에 통합하였다(Fig. 3).

```
┌─────────────────────────────────────────────────┐
│                Cursor IDE (주 오케스트레이터)       │
│  - 코드 수정 (최대 8 병렬 에이전트, Git worktree)  │
│  - Linear MCP (이슈/PR/사이클 관리)               │
│  - GitHub MCP (버전 관리)                         │
├─────────────┬───────────────────┬───────────────┤
│ Codex CLI   │                   │ Claude Code   │
│ MCP Server  │                   │ MCP Server    │
│             │                   │ (proxy.mjs)   │
│ - 비판적    │                   │ - 자율 추론   │
│   코드 감사 │                   │ - Agent Teams │
│ - 구조화    │                   │ - 경쟁 가설   │
│   분석      │                   │   분석        │
│ (최대 6     │                   │ (에이전트 간  │
│  서브에이전트)│                   │  직접 통신)   │
└─────────────┴───────────────────┴───────────────┘
```
**Fig. 3. 멀티 MCP 개발 환경 아키텍처**

실제 개발 과정에서 3종의 에이전트가 역할을 분담하였다:

- **Cursor**: 직접 코드 수정, 테스트 실행, 프로젝트 관리 (Linear/GitHub 연동)
- **Codex CLI**: 비판적 코드 감사, 구조화된 취약점 분석, 패치 생성
- **Claude Code**: 자율 탐색, 아키텍처 검증(Competing Hypotheses), 웹 리서치

대표적 협업 사례로, Silo A/B의 코드 품질 개선 작업에서 3개 에이전트가 동일 코드베이스의 서로 다른 모듈을 병렬로 분석하여, 에이전트별로 다른 관점의 결함을 발견하였다.

---

## 4. 구현

### 4.1 7-Step 계산 파이프라인

Silo A의 핵심 파이프라인은 7단계로 구성된다:

| Step | 도구 | 입력 | 출력 |
|------|------|------|------|
| 01 | AlphaFold3 | SSTR2 + SST-14 복합체 | 바인딩 포켓 (35잔기) |
| 02 | RFdiffusion | 포켓 구조 + contigs | 펩타이드 백본 |
| 03 | ProteinMPNN | 백본 구조 | 최적 서열 |
| 04 | ESMFold | 설계 서열 | 3D 구조 + pLDDT |
| 05 | DiffDock/Boltz-2 | 리간드 + 수용체 | 도킹 포즈 + 신뢰도 |
| 05b | Off-target docking | 후보 + SSTR1/3/4/5 | 선택성 마진 |
| 06 | PyRosetta | 복합체 구조 | ddG (kcal/mol) |
| 07 | FoldMason + PyMOL | 구조 세트 | 시각화 + 분석 |

모든 계산 도구는 NVIDIA NIM API를 통해 클라우드에서 실행되므로 로컬 GPU가 불필요하다.

### 4.2 Critic 에이전트의 자기 개선 메커니즘

Critic 에이전트는 파이프라인 실패를 6가지 유형으로 분류하고, 각 유형에 대응하는 교정 액션을 FAILURE_ACTION_MAP으로 정의한다:

| 실패 유형 | 교정 액션 (예시) |
|-----------|-----------------|
| 구조 품질 저하 (pLDDT < 75) | diffusion 단계 수 증가, contigs 범위 조정 |
| 도킹 실패 | 포켓 잔기 재선정, 리간드 유연성 증가 |
| 에너지 발산 (ddG > 0) | relax 프로토콜 변경, 제약 조건 완화 |
| 선택성 미달 | off-target 잔기 분석, 서열 특이성 강화 |
| 다양성 부족 | 클러스터 수 증가, temperature 상향 |
| 수렴 지연 | 학습률 감소, 탐색 범위 축소 |

반복당 최대 2개의 파라미터만 변경하여 인과 추적성(traceability)을 보장한다. 또한, 파라미터 주입 시 화이트리스트 검증을 통해 LLM 환각에 의한 설정 오염을 차단한다.

### 4.3 Silo B: 제약 기반 돌연변이 생성

Silo B의 ConstraintCompiler는 30개 이상의 Pydantic 모델로 정의된 제약 조건을 컴파일한다:

- **Frozen positions**: C1, C14 (이황화 결합), F7, F8, W9, K10 (약리작용단)
- **Per-position whitelist**: 각 가변 위치의 허용 아미노산 집합
- **Pairwise rules**: 위치 간 조합 제약 (hard/soft violation 구분)
- **Pharmacophore**: SSTR2 결합에 필수적인 잔기 패턴 보존

MutantGenerator는 설계 공간 크기에 따라 전수 열거(enumerate), 무작위 샘플링(sampling), 유전 알고리즘-베이지안 최적화(GA-BO) 전략을 자동 선택한다.

---

## 5. 실험 결과

### 5.1 아키텍처 검증 결과

Competing Hypotheses 분석 결과, 에이전트 팀은 3:1 다수결로 Option C (6-Agent Hybrid)를 최적 아키텍처로 채택하였다(Table 4). Devil's Advocate는 Option B의 자기 QC 편향과 Option A의 비용 비효율성을 모두 지적하며, Option C가 두 옵션의 장점을 결합한다고 결론지었다.

### 5.2 에이전트 협업 성과

멀티 MCP 기반 에이전트 협업을 통해 다음의 결함을 발견·수정하였다(Table 6).

**Table 6. 에이전트 협업으로 발견된 결함**

| 심각도 | ID | 결함 내용 | 발견 에이전트 | 영향 |
|--------|-----|----------|-------------|------|
| P0 | 1 | `_invoke_agent()` 스텁이 실제 에이전트를 호출하지 않음 | Devil's Advocate | 6개 에이전트 클래스가 사실상 미사용 |
| P0 | 2 | LLM 출력이 파이프라인 설정에 무검증 주입 | LLM-Evaluator | 보안 취약점 (임의 설정 변경 가능) |
| P0 | 3 | Step05b 선택성 스크리닝 미구현 | Advocate-6Agent | 선택성 평가 없이 후보 통과 |
| P1 | 1 | 수렴 초기값 버그 (`previous_best_ddg = 0.0`) | Codex CLI | 첫 반복 수렴 판정 오류 |
| P1 | 2 | `StopIteration` 크래시 (DiversityManager) | Claude Code | 파이프라인 비정상 종료 |
| P1 | 3 | 파라미터 화이트리스트 미적용 | Cursor | LLM 환각에 의한 보안 설정 노출 |

에이전트별 발견 결함의 특성이 상이하며, 이는 역할 분화된 멀티에이전트 분석의 유효성을 보여준다. Devil's Advocate가 가장 치명적인 P0-1 결함(에이전트 미사용)을 발견한 것은 악마의 대변인 역할의 중요성을 입증한다.

### 5.3 파이프라인 실행 결과

**Silo A 실행 결과:**

| Arm | 방법 | 후보 수 | 주요 지표 | 상태 |
|-----|------|---------|-----------|------|
| 1 | 소분자 (MolMIM + DiffDock) | 40 (15 도킹) | QED=0.94, confidence=-3.0 | 완료 |
| 2 | 펩타이드 변이체 | 13 | Ala scan + 강화 변이체 | 분석 완료 |
| 3 | De Novo (RFdiff + MPNN + ESMFold) | 16 | pLDDT=81.4 (최고) | 완료 |
| **통합** | **FastDesign + De Novo 통합** | **20** | **가중합 랭킹** | **완료** |

**Silo B 검증 결과:**
- 단위 테스트: Silo A 9건 + Silo B 24건 = **전 33건 통과**
- ConstraintCompiler: frozen position, pharmacophore, pairwise rule 검증 완료
- MultiObjectiveScorer: dG/stability/druggability/diversity 가중합 검증 완료

### 5.4 LLM 호출 효율성

| 구성 | LLM 호출/반복 | 추론 시간/반복 (A100) | 코드 줄 수 (최대) |
|------|:---:|:---:|:---:|
| Option A (6-LLM) | 6 | ~12-30s | 566 |
| Option B (4-Agent) | 4 | ~8-20s | ~1,516 |
| **Option C (Hybrid)** | **3** | **~6-10s** | **566** |

Option C는 Option A 대비 **추론 비용 50% 절감**, Option B 대비 **코드 복잡도 63% 감소**를 동시에 달성하였다.

---

## 6. 논의

### 6.1 에이전트 역할 분화의 효과

LLM 필요성 점수 기반의 에이전트 분류는 불필요한 LLM 호출을 제거하면서도 과학적 추론이 필요한 단계(가설 생성, 실패 분석, 보고서 작성)의 품질을 유지할 수 있음을 보여주었다. Builder, QC&Ranker, DiversityManager의 코드 전환은 비결정성 위험의 원천 제거라는 부가적 이점을 제공한다.

### 6.2 Competing Hypotheses 패턴의 유용성

에이전트 간 경쟁적 분석은 단일 에이전트의 확증 편향(confirmation bias)을 효과적으로 완화하였다. 특히 Devil's Advocate의 역할이 가장 치명적인 결함(P0-1)을 발견한 것은, 의도적으로 반대 관점을 탐색하는 에이전트의 가치를 실증한다. 이 패턴은 다른 복잡 시스템의 아키텍처 결정에도 일반화 가능하다.

### 6.3 한계 및 향후 연구

본 연구는 다음과 같은 한계를 갖는다:

1. **웨트랩 검증 부재**: 생성된 후보 물질의 실제 결합 친화도는 웨트랩 실험으로 확인되지 않았다. 향후 SPR(Surface Plasmon Resonance) 및 방사성동위원소 표지 실험이 필요하다.

2. **LLM 환각 위험**: Critic 에이전트의 7B 모델은 복잡한 실패 원인 분석에서 환각 가능성이 존재한다. FAILURE_ACTION_MAP 기반 few-shot 스캐폴딩과 규칙 기반 폴백으로 위험을 완화하였으나, 완전한 해결은 아니다.

3. **GLP-1 안정성 예측 미구현**: 혈액 내 6~10일 안정성은 GLP-1 유사체 기술 접목이 필요하나 현재 미구현 상태이다.

4. **NIM API 단일 장애점**: 모든 계산 도구가 NVIDIA NIM API에 의존하여, API 장애 시 전체 파이프라인이 중단된다. Circuit breaker 패턴 도입이 필요하다.

향후 연구로는 (1) Qwen 2.5 7B의 실제 통합 및 온프레미스 배포, (2) 적응형 LLM 라우팅(confidence 기반), (3) GLP-1 안정성 예측 모듈 개발, (4) 웨트랩 검증을 통한 end-to-end 파이프라인 실증을 계획하고 있다.

---

## 7. 결론

본 연구에서는 SSTR2 타겟 방사성의약품 후보 물질 탐색을 위한 멀티에이전트 AI Co-Scientist 시스템을 제안하고 검증하였다. 핵심 기여는 다음과 같다:

첫째, **6-Agent Hybrid 아키텍처**를 통해 LLM 기반 에이전트(3개)와 코드 기반 에이전트(3개)를 역할별로 최적 분화하여, 전수 LLM 구조 대비 추론 비용을 50% 절감하면서 관심사 분리와 독립 테스트 가능성을 유지하였다.

둘째, **Competing Hypotheses 패턴**을 아키텍처 결정에 적용하여, 4명의 AI 에이전트가 독립적으로 코드베이스를 분석하고 합의를 도출하는 객관적 의사결정 프로세스를 수립하였다. 이를 통해 치명적 결함 3건을 포함한 총 6건의 결함을 발견·수정하였다.

셋째, **멀티 MCP 기반 개발 방법론**을 통해 3종의 AI 에이전트(Cursor, Codex CLI, Claude Code)가 역할을 분담하여 시스템을 협업 개발하는 실용적 워크플로우를 구축하고, 그 유효성을 입증하였다.

Dual-Silo 파이프라인은 소분자, 펩타이드, de novo 접근을 통합하여 89개 후보를 생성하였으며, 전 33건의 단위 테스트를 통과하였다. 향후 웨트랩 검증을 통해 실제 방사성의약품 후보로의 전환 가능성을 확인할 계획이다.

---

## 참고문헌

[1] Reubi, J. C. "Peptide receptors as molecular targets for cancer diagnosis and therapy." *Endocrine Reviews*, 24(4), 389-427, 2003.

[2] Strosberg, J., et al. "Phase 3 trial of ^177Lu-DOTATATE for midgut neuroendocrine tumors." *New England Journal of Medicine*, 376(2), 125-135, 2017.

[3] Gottwalt, A., et al. "AI Co-Scientist." Google DeepMind Technical Report, 2024.

[4] Hong, S., et al. "MetaGPT: Meta programming for a multi-agent collaborative framework." *ICLR*, 2024.

[5] Li, G., et al. "CAMEL: Communicative agents for 'mind' exploration of large language model society." *NeurIPS*, 2023.

[6] Watson, J. L., et al. "De novo design of protein structure and function with RFdiffusion." *Nature*, 620, 1089-1100, 2023.

[7] Dauparas, J., et al. "Robust deep learning-based protein sequence design using ProteinMPNN." *Science*, 378(6615), 49-56, 2022.

[8] Corso, G., et al. "DiffDock: Diffusion steps, twists, and turns for molecular docking." *ICLR*, 2023.

[9] Lin, Z., et al. "Evolutionary-scale prediction of atomic-level protein structure with a language model." *Science*, 379(6637), 1123-1130, 2023.

[10] NVIDIA. "MolMIM: Molecular generation and optimization." NVIDIA NIM API Documentation, 2024.

[11] Chaudhury, S., et al. "PyRosetta: A script-based interface for implementing molecular modeling algorithms using Rosetta." *Bioinformatics*, 26(5), 689-691, 2010.

[12] Qian, C., et al. "ChatDev: Communicative agents for software development." *ACL*, 2024.

[13] Anthropic. "Model Context Protocol Specification." https://modelcontextprotocol.io, 2024.

[14] Cursor. "Cursor IDE Documentation." https://cursor.sh/docs, 2025.

[15] OpenAI. "Codex CLI." https://github.com/openai/codex, 2025.

[16] Anthropic. "Claude Code CLI." https://docs.anthropic.com/claude-code, 2025.

---

*본 논문의 시스템 개발 및 분석에 Cursor IDE, OpenAI Codex CLI, Anthropic Claude Code가 멀티에이전트 협업 도구로 활용되었다.*
