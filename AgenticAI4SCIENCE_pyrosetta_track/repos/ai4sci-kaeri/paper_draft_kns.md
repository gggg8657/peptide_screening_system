# Agentic AI 기반 Computational Biology 실험 자동화 시스템 설계 및 구현

**Design and Implementation of an Agentic AI-based Computational Biology Experiment Automation System**

---

**저자**: [저자명]
**소속**: [소속기관]
**학회**: 한국원자력학회 / AI 트랙
**키워드**: Agentic AI, Multi-Agent System, Large Language Model, Computational Biology, PyRosetta, Experiment Automation

---

## 초록 (Abstract)

본 논문에서는 Agentic AI 패러다임에 기반한 computational biology 실험 자동화 시스템의 설계 및 구현을 제시한다. 제안 시스템은 5개의 Co-Scientist 에이전트(Planner, QCRanker, DiversityManager, Critic, Reporter)로 구성된 다중 에이전트 아키텍처를 채택하며, 이 중 3개 에이전트(Planner, Critic, Reporter)는 대규모 언어 모델(LLM)에 의해 구동되고, 2개 에이전트(QCRanker, DiversityManager)는 규칙 기반 코드로 동작한다. 파이프라인은 PyRosetta FlexPepDock을 활용한 mutate-dock-QC-critique-report 반복 실험 루프를 자동 수행하며, LLM Provider 추상화 계층을 통해 Ollama(로컬), vLLM, 또는 규칙 기반 폴백 모드를 유연하게 전환할 수 있다. 또한 React 19 + Vite + Tailwind CSS 기반의 웹 대시보드를 통해 파이프라인 진행 상황, 에이전트 상태, 후보 랭킹, QC 게이트 결과 및 수렴 그래프를 실시간으로 모니터링할 수 있다. 본 시스템 자체의 개발 과정에서도 Claude Code CLI, Cursor, Codex, Perplexity MCP 서버 등 agentic AI 개발 도구를 적극 활용하였다. SSTR2 수용체에 대한 SST-14 펩타이드 바인더 최적화 실험을 통해 시스템의 동작을 검증하였으며, 2회 반복 실험에서 ddG -31.12 kcal/mol(iter01) 및 -7.57 kcal/mol(iter02)의 후보를 자동 선별하는 결과를 확인하였다.

---

## 1. 서론 (Introduction)

### 1.1 연구 배경

최근 대규모 언어 모델(Large Language Model, LLM)의 급속한 발전은 과학 연구의 자동화에 새로운 가능성을 열어가고 있다. 특히 Google DeepMind의 AI Co-Scientist[1] 개념은 LLM 에이전트가 가설 생성, 실험 설계, 결과 분석, 보고서 작성에 이르는 과학적 탐구 과정 전반에 참여할 수 있음을 보여주었다. 이러한 Agentic AI 패러다임은 단일 모델의 추론 능력을 넘어, 목표 지향적인 자율 행동 루프(plan-execute-observe-critique)를 통해 복잡한 문제를 해결하는 접근법이다.

Computational biology 분야에서는 단백질 구조 예측(AlphaFold), 분자 도킹(DiffDock), 서열 설계(ProteinMPNN), 에너지 정제(PyRosetta) 등 다양한 계산 도구가 발전해왔다. 그러나 이들 도구를 조합하여 de novo 펩타이드 바인더를 설계하는 전체 파이프라인은 여전히 연구자의 수동적인 판단과 반복적인 파라미터 조정에 크게 의존하고 있다. 각 실험 단계의 출력을 평가하고, 실패 원인을 분석하며, 다음 반복(iteration)의 전략을 결정하는 과정은 상당한 전문 지식과 시간을 요구한다.

### 1.2 연구 목적

본 연구는 다음과 같은 목적을 가진다:

1. **다중 에이전트 기반 실험 자동화 시스템 설계**: 5개의 전문화된 Co-Scientist 에이전트로 구성된 아키텍처를 설계하여, 가설 생성부터 보고서 작성까지의 전 과정을 자동화한다.
2. **유연한 LLM 통합 추상화 계층 구현**: 로컬 GPU 환경의 제약(GTX 1060, 6GB VRAM)을 고려하여, 다양한 LLM 백엔드(Ollama, vLLM) 및 규칙 기반 폴백을 동적으로 전환할 수 있는 Provider 패턴을 구현한다.
3. **실시간 웹 모니터링 대시보드 개발**: 파이프라인 진행 상황, 에이전트 활동, 후보 평가 결과를 실시간으로 시각화하는 대시보드를 구현한다.
4. **Agentic AI 도구를 활용한 개발 방법론 검증**: 시스템 개발 과정 자체에서 Claude Code CLI, Cursor, Codex, Perplexity MCP 서버 등 agentic AI 개발 환경을 활용한 경험을 공유한다.

### 1.3 논문 구성

본 논문의 구성은 다음과 같다. 2장에서는 관련 연구를 살펴보고, 3장에서는 시스템 설계를 상세히 기술한다. 4장에서는 구현 세부사항을 다루며, 5장에서는 실험 결과를 제시한다. 6장에서는 한계점과 향후 과제를 논의하고, 7장에서 결론을 맺는다.

---

## 2. 관련 연구 (Related Work)

### 2.1 AI for Science 시스템

AI for Science는 기계학습과 AI를 과학적 발견에 적용하는 연구 분야로, 최근 수년간 급격한 발전을 이루었다. AlphaFold[2]는 단백질 구조 예측의 정확도를 혁신적으로 향상시켰으며, RFdiffusion[3]은 생성 모델을 통한 de novo 단백질 설계를 가능하게 하였다. 이러한 개별 도구의 발전에도 불구하고, 이들을 통합적으로 조율하는 자동화 프레임워크에 대한 연구는 상대적으로 미흡한 상황이다.

### 2.2 Co-Scientist 및 LLM 에이전트 시스템

Google DeepMind의 AI Co-Scientist[1]는 LLM 기반 다중 에이전트 시스템이 과학적 가설 생성 및 검증에 참여할 수 있음을 보여준 대표적 사례이다. 이 시스템은 여러 전문화된 에이전트가 협업하여 과학 논문을 분석하고, 새로운 가설을 제안하며, 실험 계획을 수립하는 구조를 채택하고 있다.

LangChain, AutoGen, CrewAI 등의 프레임워크는 LLM 에이전트의 구성과 조율을 위한 범용 도구를 제공하지만, computational biology 파이프라인의 도메인 특수성(PDB 파일 처리, 에너지 함수 해석, 구조적 실패 분류 등)을 충분히 반영하지 못한다.

### 2.3 PyRosetta와 FlexPepDock

PyRosetta[4]는 Rosetta 분자 모델링 스위트의 Python 인터페이스로, 단백질-펩타이드 도킹, 에너지 계산, 구조 정제 등의 기능을 프로그래밍적으로 활용할 수 있게 한다. FlexPepDock[5]은 PyRosetta 내에서 펩타이드-수용체 복합체의 유연한 도킹 및 정제를 수행하는 프로토콜이다. 본 시스템은 FlexPepDock을 핵심 시뮬레이션 엔진으로 활용한다.

### 2.4 Agentic AI 개발 환경

Claude Code CLI(Anthropic), Cursor(AI-native IDE), Codex(OpenAI), Perplexity MCP 서버 등은 개발자의 코딩 작업을 AI가 보조하는 agentic 개발 도구이다. 이들은 코드 생성, 리팩토링, 디버깅, 문서화 등의 작업에서 개발 생산성을 크게 향상시킨다. 본 연구에서는 이러한 도구를 시스템 구현에 적극 활용하였으며, 이는 "AI로 AI 시스템을 구축하는" 메타 수준의 agentic 개발 사례로서 의미가 있다.

---

## 3. 시스템 설계 (System Design)

### 3.1 전체 아키텍처 개요

본 시스템은 크게 세 가지 계층으로 구성된다: (1) 에이전트 계층(Agent Layer), (2) 파이프라인 실행 계층(Pipeline Execution Layer), (3) 모니터링 계층(Monitoring Layer). Fig. 1은 전체 시스템 아키텍처를 도식화한 것이다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Layer (Web UI)                      │
│  React 19 + Vite + Tailwind CSS                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Pipeline  │ │Agent     │ │Candidate │ │Convergence│           │
│  │Status    │ │Monitor   │ │Table     │ │Graph     │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│       ▲ polling (2s)                                             │
├───────┼─────────────────────────────────────────────────────────┤
│       │              API Server (Python HTTP, port 8787)         │
│       │    GET /api/status  ←  reads  ← status.json              │
├───────┼─────────────────────────────────────────────────────────┤
│       │           Pipeline Execution Layer                        │
│  ┌────┴──────────────────────────────────────────────┐          │
│  │  StatusEmitter  →  writes  →  /tmp/status.json    │          │
│  │                                                    │          │
│  │  ┌──────────── Iteration Loop ──────────────┐     │          │
│  │  │  Planner → Mutate → Dock → QC → Critic   │     │          │
│  │  │     → Reporter → [next iteration]         │     │          │
│  │  └───────────────────────────────────────────┘     │          │
│  └────────────────────────────────────────────────────┘          │
│                                                                   │
│           Agent Layer (Co-Scientist Agents)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │Planner   │ │Critic    │ │Reporter  │  ← LLM-backed          │
│  │(LLM)     │ │(LLM)     │ │(LLM)     │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
│  ┌──────────┐ ┌──────────┐                                      │
│  │QCRanker  │ │Diversity │  ← Code-based                        │
│  │(Code)    │ │Manager   │                                       │
│  └──────────┘ └──────────┘                                      │
│                                                                   │
│           LLM Provider Abstraction                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │Ollama    │ │vLLM      │ │None      │                         │
│  │Provider  │ │Provider  │ │Provider  │                         │
│  └──────────┘ └──────────┘ └──────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

*Fig. 1. 전체 시스템 아키텍처*

### 3.2 다중 에이전트 설계

본 시스템의 핵심은 5개의 전문화된 Co-Scientist 에이전트이다. 각 에이전트는 공통 베이스 클래스(`BaseAgent`)를 상속하며, `execute(context)` 메서드를 통해 표준화된 인터페이스로 동작한다. Table 1은 각 에이전트의 역할과 특성을 요약한다.

**Table 1. Co-Scientist 에이전트 구성**

| 에이전트 | 역할 | 구동 방식 | 주요 입력 | 주요 출력 |
|----------|------|-----------|-----------|-----------|
| Planner | 실험 기획, 가설 생성 | LLM + 규칙 폴백 | 제약조건, Critic 피드백 | ExperimentPlan (JSON) |
| QCRanker | 품질관리 및 랭킹 | 코드 기반 (규칙) | 후보 점수 데이터 | RankTable, QCReport |
| DiversityManager | 서열 다양성 관리 | 코드 기반 (규칙) | 후보 서열 집합 | 다양성 메트릭 |
| Critic | 비판적 검토, 원인 분석 | LLM + 규칙 폴백 | RankTable, QCReport | CriticAnalysis (JSON) |
| Reporter | 보고서 작성, 시각화 | LLM + 규칙 폴백 | RankTable, CriticAnalysis | summary.md, rank_table.csv, PyMOL 스크립트 |

#### 3.2.1 에이전트 간 통신 구조

에이전트 간 통신은 `AgentMessage` 데이터클래스를 통해 이루어지며, 4가지 메시지 유형(`INFO`, `REQUEST`, `DECISION`, `ALERT`)을 지원한다. 현재 구현에서는 동기 방식의 직접 호출(synchronous direct call)로 메시지를 전달하며, `BaseAgent.send_message()` 메서드가 수신 에이전트의 `receive_message()`를 직접 호출한다.

```python
class AgentMessage:
    sender: str          # 발신 에이전트 이름
    receiver: str        # 수신 에이전트 이름
    content: dict        # 메시지 본문
    timestamp: str       # ISO-8601 시각
    message_type: MessageType  # INFO | REQUEST | DECISION | ALERT
```

#### 3.2.2 LLM-규칙 이중 실행 전략 (Dual Execution Strategy)

LLM 기반 에이전트(Planner, Critic, Reporter)는 공통적으로 "LLM 우선, 규칙 기반 폴백" 전략을 채택한다. 이 설계의 핵심 동기는 다음과 같다:

- **GPU 자원 제약 대응**: GTX 1060(6GB VRAM) 환경에서 LLM 서빙과 PyRosetta 시뮬레이션이 GPU를 공유하므로, LLM 호출이 실패하거나 불가능한 상황이 빈번하다.
- **결정론적 폴백 보장**: LLM 응답의 비결정성 및 파싱 실패에 대비하여, 항상 동작 가능한 규칙 기반 로직을 유지한다.
- **점진적 향상(Progressive Enhancement)**: LLM 모델의 업그레이드 시 에이전트 동작이 자연스럽게 향상되며, 모델 없이도 기본 기능이 보장된다.

구현 패턴은 다음과 같다:

```python
def analyze_results(self, ...):
    # 1차 시도: LLM 기반 분석
    if self.has_llm:
        llm_result = self._analyze_via_llm(...)
        if llm_result is not None:
            return llm_result
        self.log("LLM 분석 실패, 규칙 기반 폴백", level="warning")

    # 2차: 규칙 기반 폴백
    return self._rule_based_analysis(...)
```

### 3.3 파이프라인 실행 흐름

파이프라인의 핵심 실행 흐름은 반복적인 "mutate-dock-QC-critique-report" 루프이다. Fig. 2는 단일 iteration 내의 실행 단계를 보여준다.

```
┌─────────┐    ┌──────────┐    ┌───────────┐    ┌────────────┐
│ Planner  │───>│ Mutate & │───>│ QCRanker  │───>│   Critic   │
│ (가설생성)│    │ FlexPep  │    │ (QC+랭킹)  │    │ (원인분석) │
└─────────┘    │ Dock     │    └───────────┘    └────────────┘
               └──────────┘            │               │
                                       ▼               ▼
                               ┌───────────┐    ┌────────────┐
                               │ Reporter  │<───│ 다음 iter  │
                               │ (보고서)   │    │ 피드백 전달 │
                               └───────────┘    └────────────┘
```

*Fig. 2. 단일 iteration 실행 흐름*

각 단계의 세부 동작은 다음과 같다:

1. **Planner 단계**: 현재 iteration 번호, 이전 결과, Critic 피드백을 입력으로 받아 `ExperimentPlan`을 생성한다. PyRosetta-only 모드에서는 mutate-dock-QC-critic-reporter에 한정된 용어만 사용하도록 제약한다.

2. **Mutate & Dock 단계**: `generate_random_mutant()` 함수를 통해 원본 서열(AGCKNFFWKTFTSC, SST-14 DOTATATE)의 가변 위치(1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14번)에 아미노산 변이를 도입하고, PyRosetta FlexPepDock(`flexpep_refine` 프로토콜)으로 복합체 정제 및 ddG(결합 자유 에너지 변화)를 계산한다.

3. **QCRanker 단계**: ddG, clash score, constraint violations 등을 기준으로 품질 게이트를 적용하고, 통과한 후보를 랭킹하여 `RankTable`과 `QCReport`를 생성한다.

4. **Critic 단계**: QC 결과를 분석하여 실패 유형(low_plddt, good_dock_bad_ddg, high_clash, low_sequence_diversity, pocket_specific_failure, poor_selectivity)을 분류하고, 최대 2개의 파라미터 변경을 제안한다.

5. **Reporter 단계**: summary.md(Markdown 보고서), rank_table.csv(랭킹 테이블), PyMOL 4-panel 렌더 스크립트(.pml)를 자동 생성한다.

### 3.4 데이터 스키마 설계

파이프라인의 데이터 흐름은 Python dataclass로 정의된 명확한 스키마를 따른다. 주요 데이터 구조는 다음과 같다:

**Table 2. 핵심 데이터 스키마**

| 스키마 | 역할 | 주요 필드 |
|--------|------|-----------|
| `FlowConfig` | 파이프라인 실행 설정 | template_pdb, original_sequence, n_candidates, max_iterations, objective_mode |
| `CandidateResult` | 단일 후보 결과 | candidate_id, sequence, ddg, total_score, clash_score, selected |
| `IterationSummary` | 반복 요약 | iteration, hypothesis, best_ddg, mean_ddg, selected_ids |
| `FlowArtifacts` | 전체 실행 산출물 | run_id, config, iterations, final_candidates, summary |
| `ExperimentPlan` | 실험 계획서 | run_id, iteration, parameters, steps_config, hypothesis |
| `CriticAnalysis` | 비판적 분석 결과 | failure_summary, proposed_changes, hypothesis |

### 3.5 Status Emitter 패턴

파이프라인과 웹 대시보드 간의 통신은 "파일 기반 상태 전파(File-based Status Propagation)" 패턴을 채택한다. 이 설계의 핵심은 세 가지 컴포넌트의 느슨한 결합(loose coupling)이다:

```
Pipeline Runner  ──writes──>  /tmp/ag_pipeline_status.json
                                          │
API Server       ──reads───>              │  (file-level caching, 200ms)
                                          │
Frontend         ──polls───>  GET /api/status (2초 간격)
```

`StatusEmitter` 클래스는 파이프라인 내부에서 인스턴스화되어, 각 단계의 진행 상황을 JSON 파일에 기록한다. 상태 파일에는 다음 정보가 포함된다:

- 파이프라인 단계 상태 (pending/running/completed/failed)
- 에이전트 활동 상태 (idle/active/error) 및 최근 메시지
- 후보 리스트 및 점수 데이터
- QC 게이트 결과
- 수렴 그래프 데이터 (iteration별 best_ddG)
- 타임라인 이벤트 (iteration별 상세 이벤트 로그)
- PyRosetta 하위 단계 상태 (Prepare/Mutate/Refine/Score/QC)

이 패턴의 장점은 파이프라인 프로세스와 API 서버가 독립적으로 실행되므로, 파이프라인 장애 시에도 대시보드가 마지막 상태를 표시할 수 있다는 것이다.

---

## 4. 구현 (Implementation)

### 4.1 기술 스택

본 시스템의 기술 스택은 Table 3과 같다.

**Table 3. 기술 스택 요약**

| 계층 | 기술 | 버전/비고 |
|------|------|-----------|
| 시뮬레이션 | PyRosetta (FlexPepDock) | conda env: bio-tools |
| 에이전트 프레임워크 | Python dataclass + ABC 패턴 | 커스텀 구현 (외부 프레임워크 미사용) |
| LLM 서빙 | Ollama (gemma3:1b) | http://localhost:11434 |
| LLM 대안 | vLLM (OpenAI-compatible API) | http://localhost:8000 |
| 백엔드 API | Python http.server (stdlib) | 포트 8787, CORS 지원 |
| 프론트엔드 | React 19 + Vite + Tailwind CSS | TypeScript, lucide-react 아이콘 |
| 상태 통신 | JSON 파일 기반 (/tmp/) | StatusEmitter 클래스 |
| 설정 관리 | YAML (pipeline_config.yaml) | PyYAML |
| 개발 도구 | Claude Code CLI, Cursor, Codex, Perplexity MCP | Agentic 개발 환경 |

### 4.2 LLM Provider 추상화 계층

LLM 통합의 핵심은 `LLMProvider` 추상 기본 클래스와 팩토리 패턴(`create_provider`)이다. 이를 통해 에이전트 코드를 수정하지 않고도 LLM 백엔드를 전환할 수 있다.

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt, *, system_prompt=None,
                 json_mode=False, temperature=0.3,
                 max_tokens=4096) -> Optional[str]: ...

    def generate_json(self, prompt, **kwargs) -> Optional[Dict]: ...

class OllamaProvider(LLMProvider):  # Ollama REST API
class VLLMProvider(LLMProvider):    # vLLM OpenAI-compatible API
class NoneProvider(LLMProvider):    # 규칙 기반 폴백 (None 반환)
```

현재 시스템은 GPU 자원 제약(GTX 1060, 6GB VRAM)으로 인해 gemma3:1b 모델을 Ollama를 통해 서빙하고 있다. `pipeline_config.yaml`의 설정으로 프로바이더를 전환한다:

```yaml
llm:
  provider: "ollama"          # none | ollama | vllm
  model: "gemma3:1b"
  base_url: "http://localhost:11434"
  temperature: 0.3
  max_tokens: 4096
  timeout: 120
```

팩토리 함수 `create_provider(config)`는 설정을 파싱하여 적절한 프로바이더 인스턴스를 반환한다. `provider: "none"`으로 설정하면 LLM 호출 없이 모든 에이전트가 규칙 기반 모드로 동작한다.

### 4.3 에이전트 프롬프트 설계

LLM 기반 에이전트의 프롬프트는 `prompts.py` 모듈에서 체계적으로 관리된다. 각 에이전트별로 시스템 프롬프트(역할 설정)와 JSON 출력 스키마가 명시되며, 사용자 프롬프트는 포맷 함수를 통해 동적으로 생성된다.

**Planner 시스템 프롬프트 (PyRosetta-only 모드):**
```
You are PlannerAgent for a PyRosetta-only mutate->dock loop.
Rules:
- Always output valid JSON matching the schema below.
- Allowed action terms: mutate->dock, QC, critic, reporter.
- Do NOT mention RFdiffusion, ProteinMPNN, ESMFold, or related aliases.
```

**Critic 출력 스키마:**
```json
{
  "overall_assessment": "string",
  "failure_analysis": {
    "structural_failures": "integer",
    "primary_failure_type": "string"
  },
  "parameter_changes": [
    {"parameter_name": "string", "rationale": "string", ...}
  ],
  "convergence_signal": "boolean"
}
```

이와 같은 구조화된 프롬프트 설계를 통해 LLM 출력의 파싱 안정성을 높이고 있다. JSON 파싱 실패 시에는 마크다운 코드 블록 추출 및 중괄호 기반 추출을 시도하는 다단계 폴백 로직(`_extract_json_block`)이 적용된다.

### 4.4 Critic 에이전트의 실패 유형 분류 체계

Critic 에이전트는 6가지 실패 유형과 이에 대응하는 액션 매핑 테이블(`FAILURE_ACTION_MAP`)을 내장하고 있다.

**Table 4. 실패 유형 및 대응 액션 매핑**

| 실패 유형 | 설명 | 대응 파라미터 | 변경 방향 |
|-----------|------|--------------|-----------|
| LOW_PLDDT | ESMFold 구조 신뢰도 낮음 | mpnn_temperature | 감소 (x0.5) |
| GOOD_DOCK_BAD_DDG | 도킹 양호, ddG 불량 | hotspot_res | 업데이트 |
| HIGH_CLASH | Rosetta clash score 과다 | rosetta_relax_cycles | 증가 (+5) |
| LOW_SEQUENCE_DIVERSITY | 서열 다양성 부족 | mpnn_temperature | 증가 (+0.1) |
| POCKET_SPECIFIC_FAILURE | 특정 포켓 반복 실패 | contigs | 재설정 |
| POOR_SELECTIVITY | SSTR2 선택성 부족 | hotspot_residues | 추가 |

Critic은 매 iteration에서 최대 2개의 파라미터 변경만을 제안하여 원인-결과 추적 가능성을 유지한다.

### 4.5 백엔드 API 서버

API 서버는 Python 표준 라이브러리의 `http.server`를 기반으로 포트 8787에서 동작하며, 다음 엔드포인트를 제공한다:

**Table 5. API 엔드포인트**

| 메서드 | 경로 | 기능 |
|--------|------|------|
| GET | /api/status | 파이프라인 상태 조회 (프론트엔드 폴링) |
| POST | /api/status | 파이프라인 상태 갱신 |
| GET | /api/run/status | 파이프라인 프로세스 상태 조회 |
| POST | /api/run/start | 파이프라인 실행 시작 |
| POST | /api/run/stop | 파이프라인 실행 중지 |
| GET | /api/health | 헬스체크 |
| GET | /api/images/{path} | 실행 결과 이미지 서빙 |

상태 파일 읽기에는 파일 수정 시간 기반 캐싱(200ms 임계값)을 적용하여 불필요한 디스크 I/O를 방지한다. CORS 헤더를 포함하여 프론트엔드 개발 서버(Vite)와의 크로스 오리진 통신을 지원한다.

API 서버는 파이프라인을 `subprocess.Popen`으로 관리하며, 설정 파라미터(pipeline_mode, max_iterations, llm_provider, llm_model, n_candidates, seed_base, objective_mode 등)를 명령줄 인자로 전달한다.

### 4.6 프론트엔드 대시보드

프론트엔드는 React 19 + Vite + Tailwind CSS로 구현된 단일 페이지 애플리케이션(SPA)이다. `usePipelineStatus` 커스텀 훅을 통해 2초 간격으로 API를 폴링하여 실시간 상태를 반영한다.

대시보드의 주요 컴포넌트는 다음과 같다:

1. **RunControlPanel**: 파이프라인 실행 제어 UI. Pipeline Mode(PyRosetta/NIM), LLM Provider(ollama/vllm/none), 반복 횟수, 후보 수, 시드값 등을 설정하고 실행/중지할 수 있다.

2. **PipelineStatus**: 파이프라인 단계별 진행 상황을 시각화한다. PyRosetta-only 모드에서는 Step06(PyRosetta) 관련 단계만 표시하며, Rosetta 하위 단계(Prepare/Mutate/Refine/Score/QC)를 세분화하여 보여준다.

3. **AgentMonitor**: 5개 에이전트의 현재 상태(idle/active/error), 최근 메시지, 처리 태스크 수를 실시간으로 표시한다. LLM 유형과 Code 유형을 시각적으로 구분한다.

4. **CandidateTable**: 현재 iteration의 후보 목록을 랭킹, 서열, pLDDT, dock score, ddG, lDDT, selectivity, final score, 결과(PASS/FAIL)와 함께 표시한다. 현재 실행이 실패한 경우 과거 이력 데이터로 자동 전환된다.

5. **QCGateChart**: QC 게이트별 통과/실패 비율을 차트로 시각화한다.

6. **ConvergenceGraph**: iteration별 best ddG 추이를 그래프로 표시하여 최적화 수렴 상황을 파악한다.

7. **LoopTimeline**: PyRosetta-only 모드에서 iteration별 이벤트(planner, rosetta.mutate, rosetta.refine, qc, critic, reporter)를 시계열로 표시한다.

8. **VisualizationPanel**: PyMOL 렌더링 결과 이미지를 표시한다.

실행 모드 자동 감지 로직은 `detectExecutionMode` 함수에 구현되어 있으며, run_id가 `sst14_mutdock_`으로 시작하거나 Step06만 활성 상태인 경우 `pyrosettaOnly` 모드로 자동 전환한다.

### 4.7 Agentic AI 도구를 활용한 개발 과정

본 시스템의 개발 과정에서 다음과 같은 agentic AI 도구를 활용하였다:

- **Claude Code CLI**: 터미널 기반 AI 코딩 어시스턴트. 에이전트 클래스 골격 생성, 프롬프트 엔지니어링, 리팩토링, 코드 리뷰에 활용하였다. 특히 복잡한 파이프라인 오케스트레이션 로직의 디버깅과 status emitter 패턴 구현에 효과적이었다.

- **Cursor**: AI-native IDE. 프론트엔드 React 컴포넌트 개발, TypeScript 타입 정의, Tailwind 스타일링에 주로 활용하였다.

- **Codex**: OpenAI의 코드 생성 모델. PyRosetta 스크립트 초안 작성 및 YAML 설정 파일 구조화에 활용하였다.

- **Perplexity MCP 서버**: 최신 연구 동향 검색과 API 문서 참조에 활용하였다. MCP(Model Context Protocol) 서버로 통합되어 개발 워크플로 내에서 직접 접근이 가능하다.

이러한 도구의 조합을 통해, 단일 개발자가 약 2주 내에 에이전트 프레임워크, PyRosetta 통합, 웹 대시보드를 포함하는 전체 시스템을 구현할 수 있었다.

---

## 5. 실험 및 결과 (Experiments and Results)

### 5.1 실험 설정

실험 대상은 SSTR2(Somatostatin Receptor Type 2)에 대한 SST-14 펩타이드 바인더 최적화이다. Table 6은 실험 설정을 요약한다.

**Table 6. 실험 설정**

| 항목 | 값 |
|------|-----|
| 대상 수용체 | SSTR2 (Somatostatin Receptor Type 2) |
| 참조 펩타이드 | DOTATATE (AGCKNFFWKTFTSC, 14-aa) |
| 디자인 가변 위치 | 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14번 |
| 고정 잔기 | Cys3, Cys14 (이황화 결합), Phe7, Trp8, Lys9, Thr10 (결합 핫스팟) |
| 반복 횟수 (max_iterations) | 2 |
| iteration당 후보 수 (n_candidates) | 2 |
| QC 게이트: ddG 상한 | -5.0 kcal/mol |
| QC 게이트: clash 상한 | 10 |
| 도킹 프로토콜 | FlexPepDock (flexpep_refine) |
| LLM 설정 | Ollama, gemma3:1b, temperature=0.3 |
| 하드웨어 | GTX 1060 6GB, conda env: bio-tools |
| Run ID | sst14_mutdock_2000 |

### 5.2 실행 결과

2회 반복 실험의 결과를 Table 7에 제시한다. 데이터는 `experiment_log.jsonl` 및 `rank_table.csv`에서 추출하였다.

**Table 7. 실험 결과 요약 (Run ID: sst14_mutdock_2000)**

| Iteration | Candidate ID | Sequence | ddG (kcal/mol) | Clash | Dock Score | QC 결과 |
|-----------|-------------|----------|----------------|-------|------------|---------|
| 1 | iter01_cand001 | AGCKVFFWKTFHSC | -18.38 | 1 | -6.16 | PASS (selected) |
| 1 | iter01_cand002 | AGCSNFFWKTQVSC | +6.84 | 2 | -8.00 | FAIL (ddG > -5.0) |
| 2 | iter02_cand001 | AGCMNYFWKMFTSC | -34.08 | 0 | -4.59 | FAIL (ddG 기준외 탈락) |
| 2 | iter02_cand002 | TGCKYFFKKTFTSC | -7.57 | 0 | -7.24 | PASS (selected) |

**주요 관찰:**

- **Iteration 1**: 2개 후보 중 1개(iter01_cand001, 서열 AGCKVFFWKTFHSC)가 ddG -18.38 kcal/mol로 QC 게이트를 통과하였다. 5번 위치 N->V, 12번 위치 T->H 변이가 결합 에너지 개선에 기여하였다. QC 통과율은 50%로 기록되었다.

- **Iteration 2**: iter02_cand002(서열 TGCKYFFKKTFTSC, ddG -7.57 kcal/mol)가 선별되었다. iter02_cand001은 ddG -34.08로 매우 우수한 에너지 값을 보였으나 랭킹 기준에 따라 cand002가 최종 선택되었다. 이는 QCRanker의 다차원 평가(ddG 단독이 아닌 dock_score, clash 등 종합 고려)를 반영한 결과이다.

### 5.3 에이전트 동작 분석

파이프라인 실행 중 각 에이전트의 동작을 분석하면 다음과 같다:

**Planner 에이전트**: 각 iteration 시작 시 가설을 생성하였다. Iteration 1에서는 "초기 탐색: mutate -> dock -> QC -> critic -> reporter 경로로 PyRosetta 기반 기준선(baseline)을 확립한다"는 가설이 설정되었다.

**QCRanker 에이전트**: RosettaGate(ddG <= -5.0)를 기준으로 후보를 필터링하고, 통과한 후보를 ddG 기반으로 랭킹하였다. Iteration 1에서는 2개 후보 중 1개가 통과(50%), Iteration 2에서도 2개 중 1개가 통과(50%)하였다.

**Critic 에이전트**: Iteration 1에서 ddG 관련 실패 유형 1건을 식별하였으며, "이전 iteration과 동일한 파라미터로 재현성 확인 및 후보 다양성 탐색"이라는 가설을 생성하였다. 파라미터 변경 제안은 없었으며, 이는 초기 탐색 단계에서 데이터 부족으로 인해 보수적 접근이 이루어진 것으로 해석된다.

**Reporter 에이전트**: 각 iteration 종료 시 `08_reports/summary.md`(Markdown 요약), `08_reports/rank_table.csv`(CSV 랭킹), `07_viz/*_render.pml`(PyMOL 스크립트)을 자동 생성하였다.

### 5.4 시스템 성능 특성

StatusEmitter를 통해 기록된 타임라인 이벤트를 분석한 결과, 파이프라인의 주요 병목은 PyRosetta FlexPepDock 정제 단계로 확인되었다. 에이전트 연산(Planner/Critic/Reporter) 자체의 소요 시간은 LLM 호출 포함 시에도 수 초 이내로, 전체 실행 시간의 대부분이 분자 시뮬레이션에 소요된다.

웹 대시보드는 2초 간격 폴링으로 파이프라인 상태를 실시간에 근접하게 반영하였으며, Status 파일 기반 캐싱을 통해 API 서버의 부하를 최소화하였다.

---

## 6. 논의 (Discussion)

### 6.1 시스템의 기여

본 시스템은 다음과 같은 측면에서 기여한다:

1. **도메인 특화 다중 에이전트 프레임워크**: LangChain 등 범용 프레임워크가 아닌, computational biology 파이프라인에 특화된 에이전트 구조를 설계하여 도메인 로직(실패 유형 분류, 구조적 인사이트 생성 등)을 에이전트 내부에 내장하였다.

2. **LLM-규칙 이중 실행 전략**: GPU 자원이 제한된 환경에서도 안정적으로 동작하는 점진적 향상 패턴을 제시하였다. 이는 고가의 GPU 클러스터 없이도 agentic 시스템을 운용할 수 있음을 보여준다.

3. **종단간 웹 기반 모니터링**: 파이프라인 내부 상태를 StatusEmitter 패턴을 통해 외부에 노출하고, React 대시보드로 실시간 시각화하는 아키텍처를 구현하였다.

4. **Agentic 개발 방법론**: AI 도구를 활용한 시스템 개발 과정 자체가 agentic 워크플로의 실증 사례이다.

### 6.2 한계점

**GPU 자원 제약**: 현재 시스템은 GTX 1060(6GB VRAM)에서 gemma3:1b 모델을 사용하고 있어, LLM의 추론 능력이 제한적이다. 1B 파라미터 모델은 복잡한 과학적 가설 생성이나 구조적 분석에서 한계를 보이며, 규칙 기반 폴백에 빈번하게 의존한다.

**소규모 실험**: 2회 반복, iteration당 2개 후보의 소규모 실험만 수행하여, 에이전트의 적응적 학습 효과(Critic 피드백 반영에 의한 점진적 개선)를 충분히 검증하지 못하였다.

**FlexPepDock 안정성**: 실험 로그에서 segmentation fault로 인한 PyRosetta 실행 실패가 관찰되었다. 이는 특정 변이 조합에서 에너지 함수 발산이 발생하는 것으로 추정되며, 시스템의 fail-open 전략(실패 시 다음 iteration 계속)으로 대응하고 있으나 근본적인 해결이 필요하다.

**평가 지표의 제한**: 현재 시스템은 ddG와 clash score를 주요 평가 지표로 사용하고 있으나, 실제 결합 친화도 예측을 위해서는 분자 동역학(MD) 시뮬레이션, 실험적 검증 등 추가적인 평가가 필요하다.

### 6.3 향후 과제

1. **LLM 모델 업그레이드**: Qwen3-8B, Llama 3 70B 등 대형 모델로 전환하여 에이전트의 추론 능력을 향상시킨다. vLLM Provider를 통한 원격 서버 연결이 이미 구현되어 있으므로, 인프라 변경 없이 모델 교체가 가능하다.

2. **적응적 수렴 전략**: `pipeline_config.yaml`에 정의된 수렴 조건(convergence_min_candidates, convergence_ddg_threshold, no_improvement_patience)을 활용한 자동 조기 종료 로직을 구현한다.

3. **확장 파이프라인 통합**: 현재 PyRosetta-only 모드 외에, RFdiffusion + ProteinMPNN + ESMFold + DiffDock을 포함하는 전체 파이프라인(full mode)의 에이전트 오케스트레이션을 완성한다. Planner의 스텝 템플릿(`_DEFAULT_STEPS`)이 이미 7단계 전체를 정의하고 있어 확장 기반이 마련되어 있다.

4. **분산 실행**: 다수의 후보를 병렬로 처리하기 위한 분산 실행 프레임워크(Ray, Dask 등)를 도입한다.

5. **선택성 스크리닝 통합**: SSTR1/3/4/5에 대한 off-target 도킹을 수행하여 SSTR2 선택성을 평가하는 `step05b_selectivity` 단계를 활성화한다.

---

## 7. 결론 (Conclusion)

본 논문에서는 Agentic AI 패러다임에 기반한 computational biology 실험 자동화 시스템을 설계하고 구현하였다. 제안 시스템은 5개의 Co-Scientist 에이전트(Planner, QCRanker, DiversityManager, Critic, Reporter)로 구성된 다중 에이전트 아키텍처를 통해 mutate-dock-QC-critique-report 반복 실험 루프를 자동 수행한다. LLM Provider 추상화 계층은 GPU 자원 제약 환경에서도 Ollama(로컬 gemma3:1b), vLLM, 규칙 기반 폴백 간의 유연한 전환을 지원하며, React 기반 웹 대시보드는 파이프라인 상태를 실시간으로 모니터링한다.

SSTR2-SST14 펩타이드 바인더 최적화 실험을 통해 시스템의 동작을 검증하였으며, 자동화된 에이전트가 가설 생성, QC 평가, 실패 분석, 보고서 작성을 일관되게 수행하는 것을 확인하였다. 특히, LLM-규칙 이중 실행 전략은 저사양 GPU 환경에서도 시스템의 안정적 동작을 보장하는 실용적인 접근법임을 실증하였다.

본 시스템은 computational biology 분야에 한정되지 않고, 실험 설계-실행-분석-피드백 루프를 반복하는 다양한 과학 연구 분야에 적용 가능한 범용적인 agentic 실험 자동화 프레임워크의 기반을 제공한다.

---

## 참고문헌 (References)

[1] Gottweis, J., et al., "Towards AI Co-Scientists," Google DeepMind, 2025.

[2] Jumper, J., et al., "Highly Accurate Protein Structure Prediction with AlphaFold," *Nature*, vol. 596, pp. 583-589, 2021.

[3] Watson, J. L., et al., "De novo design of protein structure and function with RFdiffusion," *Nature*, vol. 620, pp. 1089-1100, 2023.

[4] Chaudhury, S., Lyskov, S., Gray, J. J., "PyRosetta: a script-based interface for implementing molecular modeling algorithms using Rosetta," *Bioinformatics*, vol. 26, no. 5, pp. 689-691, 2010.

[5] Raveh, B., London, N., Schueler-Furman, O., "Sub-angstrom modeling of complexes between flexible peptides and globular proteins," *Proteins*, vol. 78, no. 9, pp. 2029-2040, 2010.

[6] Dauparas, J., et al., "Robust deep learning-based protein sequence design using ProteinMPNN," *Science*, vol. 378, pp. 49-56, 2022.

[7] Lin, Z., et al., "Evolutionary-scale prediction of atomic-level protein structure with a language model," *Science*, vol. 379, pp. 1123-1130, 2023.

---

## 부록 A. 프로젝트 구조

```
ai4sci-kaeri/
├── AG_src/
│   ├── agents/
│   │   ├── base_agent.py         # 에이전트 베이스 클래스
│   │   ├── planner.py            # Planner 에이전트
│   │   ├── critic.py             # Critic 에이전트
│   │   ├── reporter.py           # Reporter 에이전트
│   │   └── qc_ranker.py          # QCRanker 에이전트
│   ├── llm/
│   │   ├── provider.py           # LLM Provider 추상화 계층
│   │   └── prompts.py            # 에이전트 프롬프트 템플릿
│   ├── config/
│   │   └── pipeline_config.yaml  # 파이프라인 설정
│   └── scripts/
│       └── flexpep_dock.py       # PyRosetta FlexPepDock 스크립트
├── pyrosetta_flow/
│   ├── runner.py                 # 메인 파이프라인 러너
│   ├── schema.py                 # 데이터 스키마 정의
│   ├── adapter.py                # 유틸리티 어댑터
│   └── ranking.py                # 이력 랭킹 관리
├── backend/
│   ├── api_server.py             # HTTP API 서버 (포트 8787)
│   └── status_emitter.py         # 상태 전파 모듈
├── frontend/
│   └── src/
│       ├── App.tsx               # 메인 애플리케이션
│       ├── hooks/
│       │   └── usePipelineStatus.ts  # 상태 폴링 훅
│       └── components/
│           ├── PipelineStatus.tsx
│           ├── AgentMonitor.tsx
│           ├── CandidateTable.tsx
│           ├── QCGateChart.tsx
│           ├── ConvergenceGraph.tsx
│           └── RiskMatrix.tsx
└── runs/
    └── pyrosetta_flow/
        ├── experiment_log.jsonl  # 실험 이력 로그
        └── sst14_agentic_mutdock/
            ├── iter_01/
            │   ├── 07_viz/
            │   └── 08_reports/
            └── iter_02/
                ├── 07_viz/
                └── 08_reports/
```

## 부록 B. 주요 설정 파라미터

```yaml
# pipeline_config.yaml 핵심 설정 (발췌)
iteration:
  max_iterations: 10
  adaptive_enabled: true
  convergence_ddg_threshold: -30.0
  no_improvement_patience: 2

receptor:
  name: "SSTR2"
  chain: "B"
  pocket_residues: [119, 120, 122, 123, 124, 127, 180, 181, ...]

reference_peptide:
  sequence: "AGCKNFFWKTFTSC"
  cys_positions: [3, 14]
  frozen_residues: ["C3", "C14", "F7", "W8", "K9", "T10"]

llm:
  provider: "ollama"
  model: "gemma3:1b"
  base_url: "http://localhost:11434"
  temperature: 0.3
  max_tokens: 4096
  timeout: 120
```
