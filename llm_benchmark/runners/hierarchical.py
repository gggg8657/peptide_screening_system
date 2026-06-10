"""Hierarchical flow runner — Orchestrator delegates to sub-agents."""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AgentTurn, ExperimentConfig, SequentialFlowRunner, REPO_ROOT

logger = logging.getLogger(__name__)

sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Orchestrator system prompt template
# ---------------------------------------------------------------------------

_ORCHESTRATOR_SYSTEM_PROMPT = """\
You are the Orchestrator for an SSTR2 peptide binder screening experiment.
You maintain the global experimental strategy across all iterations.

Your responsibilities:
1. Set high-level direction for each iteration
2. Approve or modify the Planner's strategy
3. Synthesize the Critic's feedback with your global view
4. Decide when to explore new regions vs exploit known good positions

Current experiment state:
- Iteration: {iteration}/{max_iterations}
- Best ddG so far: {best_ddg}
- FWKT conservation rate: {fwkt_rate}
- Explored positions: {explored_positions}
"""

_DIRECTION_PROMPT = """\
Based on the experiment history, provide strategic direction for iteration {iteration}:
Respond in JSON: {{
  "strategy": "explore" | "exploit" | "diversify",
  "priority_positions": [...],
  "rationale": "...",
  "constraints": {{"avoid_positions": [...], "prefer_mutations": [...]}}
}}
"""

_APPROVAL_PROMPT = """\
The Planner proposes: {plan_summary}
Do you approve this plan given the global strategy of "{strategy}"?
Respond in JSON: {{"approved": bool, "modifications": {{}} or null, "rationale": "..."}}
"""


# ---------------------------------------------------------------------------
# OrchestratorAgent
# ---------------------------------------------------------------------------

class OrchestratorAgent:
    """LLM 기반 오케스트레이터 에이전트.

    direct()  — iteration 시작 전 전략적 방향 설정
    approve() — Planner 계획 승인/수정
    synthesize() — Critic 피드백과 글로벌 관점 통합

    Args:
        llm_provider: LLMProvider 인스턴스
        max_iterations: 전체 실험 반복 횟수
        log_dir: agent_log 디렉토리 경로
    """

    def __init__(
        self,
        llm_provider: Any,
        max_iterations: int,
        log_dir: Path,
    ) -> None:
        self._llm = llm_provider
        self._max_iterations = max_iterations
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        # 글로벌 컨텍스트: 이터레이션 간 누적 상태
        self._global_history: List[Dict[str, Any]] = []
        self._best_ddg: float = float("inf")
        self._explored_positions: List[int] = []
        self._fwkt_rate: float = 1.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def direct(
        self,
        iteration: int,
        experiment_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """iteration 시작 전 오케스트레이터가 전략적 방향을 결정한다.

        Args:
            iteration: 현재 이터레이션 번호
            experiment_state: 현재 실험 상태 요약

        Returns:
            {"strategy": str, "priority_positions": list, "rationale": str, "constraints": dict}
        """
        self._update_global_state(experiment_state)
        system = self._build_system_prompt(iteration)
        prompt = _DIRECTION_PROMPT.format(iteration=iteration)

        t0 = time.time()
        raw = self._llm.generate(
            prompt,
            system_prompt=system,
            json_mode=True,
            temperature=0.3,
        )
        latency_ms = (time.time() - t0) * 1000

        direction = self._parse_json_safe(raw, default={
            "strategy": "explore",
            "priority_positions": [],
            "rationale": "LLM unavailable — default explore strategy",
            "constraints": {"avoid_positions": [], "prefer_mutations": []},
        })

        self._log_turn(
            iteration=iteration,
            step="direct",
            input_prompt=prompt,
            system_prompt=system,
            raw_response=raw or "",
            parsed=direction,
            latency_ms=latency_ms,
        )
        logger.debug(
            "[Orchestrator] iter=%d direction strategy=%s positions=%s",
            iteration,
            direction.get("strategy"),
            direction.get("priority_positions"),
        )
        return direction

    def approve(
        self,
        iteration: int,
        plan_summary: str,
        strategy: str,
    ) -> Dict[str, Any]:
        """Planner가 제안한 계획을 승인하거나 수정 지침을 반환한다.

        Args:
            iteration: 현재 이터레이션 번호
            plan_summary: Planner 계획 요약 문자열
            strategy: direct()가 결정한 전략 ("explore"|"exploit"|"diversify")

        Returns:
            {"approved": bool, "modifications": dict|None, "rationale": str}
        """
        system = self._build_system_prompt(iteration)
        prompt = _APPROVAL_PROMPT.format(
            plan_summary=plan_summary,
            strategy=strategy,
        )

        t0 = time.time()
        raw = self._llm.generate(
            prompt,
            system_prompt=system,
            json_mode=True,
            temperature=0.2,
        )
        latency_ms = (time.time() - t0) * 1000

        approval = self._parse_json_safe(raw, default={
            "approved": True,
            "modifications": None,
            "rationale": "LLM unavailable — auto-approved",
        })

        self._log_turn(
            iteration=iteration,
            step="approve",
            input_prompt=prompt,
            system_prompt=system,
            raw_response=raw or "",
            parsed=approval,
            latency_ms=latency_ms,
        )
        logger.debug(
            "[Orchestrator] iter=%d approval=%s rationale=%s",
            iteration,
            approval.get("approved"),
            approval.get("rationale", "")[:80],
        )
        return approval

    def synthesize(
        self,
        iteration: int,
        critic_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Critic 피드백과 오케스트레이터 글로벌 관점을 통합한다.

        Args:
            iteration: 현재 이터레이션 번호
            critic_analysis: ScientistCriticAgent의 분석 결과

        Returns:
            {"synthesized_feedback": dict, "next_iter_priority": str, "rationale": str}
        """
        system = self._build_system_prompt(iteration)
        critic_summary = json.dumps(critic_analysis, ensure_ascii=False)[:800]
        prompt = (
            f"Critic feedback for iteration {iteration}:\n{critic_summary}\n\n"
            "Synthesize this with the global experiment context. "
            "Respond in JSON: {\"synthesized_feedback\": {}, "
            "\"next_iter_priority\": \"...\", \"rationale\": \"...\"}"
        )

        t0 = time.time()
        raw = self._llm.generate(
            prompt,
            system_prompt=system,
            json_mode=True,
            temperature=0.3,
        )
        latency_ms = (time.time() - t0) * 1000

        synthesis = self._parse_json_safe(raw, default={
            "synthesized_feedback": critic_analysis,
            "next_iter_priority": "continue",
            "rationale": "LLM unavailable — passed critic feedback unchanged",
        })

        self._log_turn(
            iteration=iteration,
            step="synthesize",
            input_prompt=prompt,
            system_prompt=system,
            raw_response=raw or "",
            parsed=synthesis,
            latency_ms=latency_ms,
        )
        return synthesis

    def update_state(
        self,
        iteration: int,
        selected_candidates: List[Dict[str, Any]],
        direction: Dict[str, Any],
    ) -> None:
        """이터레이션 결과로 글로벌 상태를 갱신한다."""
        if selected_candidates:
            iter_best = min(c.get("ddg", float("inf")) for c in selected_candidates)
            if iter_best < self._best_ddg:
                self._best_ddg = iter_best

        # 이 이터레이션에서 탐색된 우선순위 포지션 누적
        new_pos: List[int] = direction.get("priority_positions", [])
        for p in new_pos:
            if p not in self._explored_positions:
                self._explored_positions.append(p)

        self._global_history.append({
            "iteration": iteration,
            "best_ddg_snapshot": self._best_ddg,
            "strategy": direction.get("strategy"),
            "priority_positions": new_pos,
        })

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self, iteration: int) -> str:
        explored_str = str(self._explored_positions) if self._explored_positions else "none yet"
        best_ddg_str = f"{self._best_ddg:.3f}" if self._best_ddg != float("inf") else "N/A"
        return _ORCHESTRATOR_SYSTEM_PROMPT.format(
            iteration=iteration,
            max_iterations=self._max_iterations,
            best_ddg=best_ddg_str,
            fwkt_rate=f"{self._fwkt_rate:.2f}",
            explored_positions=explored_str,
        )

    def _update_global_state(self, experiment_state: Dict[str, Any]) -> None:
        best = experiment_state.get("best_ddg")
        if best is not None and float(best) < self._best_ddg:
            self._best_ddg = float(best)
        fwkt = experiment_state.get("fwkt_rate")
        if fwkt is not None:
            self._fwkt_rate = float(fwkt)

    @staticmethod
    def _parse_json_safe(
        raw: Optional[str],
        default: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not raw:
            return default
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        # ```json ... ``` 블록 추출 시도
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            parsed = json.loads(raw[start:end])
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, json.JSONDecodeError):
            pass
        return default

    def _log_turn(
        self,
        iteration: int,
        step: str,
        input_prompt: str,
        system_prompt: str,
        raw_response: str,
        parsed: Dict[str, Any],
        latency_ms: float,
    ) -> None:
        log_path = self._log_dir / f"iter_{iteration:02d}_orchestrator.jsonl"
        record = {
            "iteration": iteration,
            "step": step,
            "agent": "orchestrator",
            "input_prompt": input_prompt,
            "system_prompt": system_prompt,
            "raw_response": raw_response,
            "parsed_output": parsed,
            "parse_success": bool(parsed),
            "latency_ms": round(latency_ms, 1),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# OrchestratedPlannerAgent — PlannerAgent 서브클래스
# ---------------------------------------------------------------------------

class OrchestratedPlannerAgent:
    """PlannerAgent를 감싸 오케스트레이터 감독을 추가한다.

    execute() 호출 시:
      1. Orchestrator.direct() — 전략적 방향 획득
      2. PlannerAgent.execute()  — 기존 계획 생성
      3. Orchestrator.approve()  — 계획 승인/수정
      4. 수정이 있으면 계획 파라미터에 반영

    Args:
        inner_planner: 기존 PlannerAgent 인스턴스
        orchestrator: OrchestratorAgent 인스턴스
        experiment_state_fn: () -> Dict 형태의 콜백,
            현재 실험 상태(best_ddg 등)를 반환
    """

    def __init__(
        self,
        inner_planner: Any,
        orchestrator: OrchestratorAgent,
        experiment_state_fn: Optional[Any] = None,
    ) -> None:
        self._inner = inner_planner
        self._orchestrator = orchestrator
        self._state_fn = experiment_state_fn or (lambda: {})
        # PlannerAgent의 공개 속성 위임
        self.planner_mode = getattr(inner_planner, "planner_mode", "pyrosetta_only")
        self._last_direction: Dict[str, Any] = {}

    # delegate attribute access to inner planner for duck-typing compatibility
    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """오케스트레이터 감독 하에 기획을 실행한다."""
        iteration = context.get("iteration", 1)
        experiment_state = self._state_fn()

        # ---- Step 1: 오케스트레이터 방향 설정 ----
        direction = self._orchestrator.direct(iteration, experiment_state)
        self._last_direction = direction
        strategy = direction.get("strategy", "explore")

        # 오케스트레이터가 제시한 priority_positions를 critic_feedback에 주입
        # → 기존 PlannerAgent가 mutation_guidance.focus_positions로 활용
        enriched_context = dict(context)
        existing_feedback = dict(context.get("critic_feedback", {}))
        orchestrator_guidance = {
            "orchestrator_strategy": strategy,
            "orchestrator_positions": direction.get("priority_positions", []),
            "orchestrator_constraints": direction.get("constraints", {}),
            "orchestrator_rationale": direction.get("rationale", ""),
        }
        existing_feedback["orchestrator_guidance"] = orchestrator_guidance
        enriched_context["critic_feedback"] = existing_feedback

        # ---- Step 2: 기존 PlannerAgent 실행 ----
        result = self._inner.execute(enriched_context)
        plan = result.get("plan")

        # ---- Step 3: 오케스트레이터 승인 ----
        plan_summary = self._build_plan_summary(plan, iteration, strategy)
        approval = self._orchestrator.approve(iteration, plan_summary, strategy)

        # ---- Step 4: 수정 지침 반영 ----
        if plan is not None and not approval.get("approved", True):
            modifications = approval.get("modifications") or {}
            self._apply_modifications(plan, modifications)
            logger.info(
                "[OrchestratedPlanner] iter=%d plan modified by orchestrator: %s",
                iteration,
                approval.get("rationale", "")[:100],
            )
        else:
            logger.debug(
                "[OrchestratedPlanner] iter=%d plan approved: %s",
                iteration,
                approval.get("rationale", "")[:80],
            )

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_plan_summary(plan: Any, iteration: int, strategy: str) -> str:
        if plan is None:
            return f"iter={iteration} strategy={strategy} (no plan object)"
        hypothesis = getattr(plan, "hypothesis", "")
        params = getattr(plan, "parameters", {})
        guidance = params.get("mutation_guidance", {})
        return (
            f"iter={iteration} strategy={strategy} "
            f"hypothesis='{hypothesis[:120]}' "
            f"focus_positions={guidance.get('focus_positions', [])} "
            f"n_guided={guidance.get('n_guided', 0)}"
        )

    @staticmethod
    def _apply_modifications(plan: Any, modifications: Dict[str, Any]) -> None:
        """오케스트레이터 수정 지침을 plan 파라미터에 반영한다."""
        if not modifications or not hasattr(plan, "parameters"):
            return
        params = plan.parameters
        guidance = params.setdefault("mutation_guidance", {})

        # focus_positions 덮어쓰기
        if "focus_positions" in modifications:
            guidance["focus_positions"] = modifications["focus_positions"]
        if "priority_positions" in modifications:
            guidance["focus_positions"] = modifications["priority_positions"]

        # suggested_mutations 병합
        if "prefer_mutations" in modifications:
            existing = guidance.get("suggested_mutations", {})
            existing.update(modifications["prefer_mutations"])
            guidance["suggested_mutations"] = existing

        # avoid_positions: guidance에 기록 (실제 필터는 runner에서 적용)
        if "avoid_positions" in modifications:
            guidance["avoid_positions"] = modifications["avoid_positions"]


# ---------------------------------------------------------------------------
# HierarchicalFlowRunner
# ---------------------------------------------------------------------------

class HierarchicalFlowRunner(SequentialFlowRunner):
    """Extends sequential flow with a central Orchestrator agent.

    The Orchestrator:
      - Maintains global experiment context across iterations
      - Assigns tasks to Planner, Critic, Reporter
      - Resolves conflicts between agent outputs
      - Makes final strategic decisions

    Sub-variable: orchestrator_model
      - "same": Orchestrator uses the same model as other agents
      - "cross": Orchestrator uses a different (potentially larger) model,
        stored in config.extra["orchestrator_cross_model"]
    """

    def __init__(self, config: ExperimentConfig) -> None:
        super().__init__(config)
        self.orchestrator_model: str = config.extra.get("orchestrator_model", "same")

    def run(self) -> Dict[str, Any]:
        """오케스트레이터 감독 하에 계층적 흐름을 실행한다."""
        from pyrosetta_flow.schema import FlowConfig
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow
        from AG_src.agents.planner import PlannerAgent
        from AG_src.llm import create_provider

        # ---- LLM 프로바이더 생성 ----
        llm_cfg = self._build_llm_cfg()
        base_llm = create_provider(llm_cfg, model_override=self.config.model_hf_id)
        orchestrator_llm = self._build_orchestrator_llm(llm_cfg, base_llm)

        # ---- OrchestratorAgent 생성 ----
        orchestrator = OrchestratorAgent(
            llm_provider=orchestrator_llm,
            max_iterations=self.config.max_iterations,
            log_dir=self._agent_log_dir,
        )

        # ---- OrchestratedPlannerAgent 생성 ----
        inner_planner = PlannerAgent(
            llm_provider=base_llm,
            planner_mode="pyrosetta_only",
        )
        orchestrated_planner = OrchestratedPlannerAgent(
            inner_planner=inner_planner,
            orchestrator=orchestrator,
            experiment_state_fn=lambda: orchestrator._global_history[-1]
            if orchestrator._global_history
            else {},
        )

        # ---- FlowConfig 구성 ----
        flow_config = FlowConfig(
            template_pdb=str(REPO_ROOT / "data" / "fold_test1_model_0.pdb"),
            output_dir=str(self._output_dir / "pyrosetta_flow"),
            max_iterations=self.config.max_iterations,
            n_candidates=self.config.n_candidates,
            top_k=self.config.top_k,
            original_sequence="AGCKNFFWKTFTSC",
            peptide_chain=1,
            conda_env="bio-tools",
            seed_base=self.config.seed,
            llm_model_override=self.config.model_hf_id,
            llm_provider="vllm",
            llm_base_url="http://localhost:8002",
            planner_mode="pyrosetta_only",
            validation_n_trials=1,
        )

        self._write_config_snapshot(flow_config)
        self._write_orchestrator_meta(orchestrator_llm)

        # ---- 오케스트레이터 주입 실행 ----
        # 업스트림 runner가 내부적으로 PlannerAgent를 생성하므로,
        # monkey-patch 방식으로 PlannerAgent 클래스를 대체한다.
        # 이 패턴은 collaborative.py와 동일한 접근법이다.
        import pyrosetta_flow.runner as _upstream_runner
        import AG_src.agents.planner as _planner_module

        _original_planner_cls = _planner_module.PlannerAgent

        class _PatchedPlannerAgent(_original_planner_cls):  # type: ignore[valid-type]
            """오케스트레이터 감독을 주입한 PlannerAgent 패치."""

            def __init__(self_, *args: Any, **kwargs: Any) -> None:  # noqa: N805
                super().__init__(*args, **kwargs)
                self_._orchestrated = OrchestratedPlannerAgent(
                    inner_planner=self_,
                    orchestrator=orchestrator,
                    experiment_state_fn=lambda: orchestrator._global_history[-1]
                    if orchestrator._global_history
                    else {},
                )

            def execute(self_, context: Dict[str, Any]) -> Dict[str, Any]:  # noqa: N805
                return self_._orchestrated.execute(context)

        start = time.time()
        _planner_module.PlannerAgent = _PatchedPlannerAgent  # type: ignore[misc]
        try:
            result = run_pyrosetta_agentic_mutdock_flow(flow_config)
            elapsed = time.time() - start
            self._write_status("done", elapsed)
            return {
                "success": True,
                "result": result,
                "elapsed_s": elapsed,
                "orchestrator_model": self.orchestrator_model,
                "orchestrator_iterations": len(orchestrator._global_history),
            }
        except Exception as exc:
            elapsed = time.time() - start
            self._write_status("failed", elapsed, str(exc))
            logger.error(
                "[Hierarchical] Experiment %s failed: %s",
                self.config.experiment_id,
                exc,
            )
            return {
                "success": False,
                "error": str(exc),
                "elapsed_s": elapsed,
                "orchestrator_model": self.orchestrator_model,
            }
        finally:
            # monkey-patch 복구
            _planner_module.PlannerAgent = _original_planner_cls  # type: ignore[misc]
            self._write_orchestrator_summary(orchestrator)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_llm_cfg(self) -> Dict[str, Any]:
        return {
            "llm": {
                "provider": "vllm",
                "model": self.config.model_hf_id,
                "base_url": "http://localhost:8002",
            }
        }

    def _build_orchestrator_llm(
        self,
        base_llm_cfg: Dict[str, Any],
        base_llm: Any,
    ) -> Any:
        """orchestrator_model 설정에 따라 LLM 인스턴스를 반환한다."""
        from AG_src.llm import create_provider

        if self.orchestrator_model == "cross":
            cross_model = self.config.extra.get("orchestrator_cross_model")
            if cross_model:
                cross_cfg: Dict[str, Any] = {
                    "llm": dict(base_llm_cfg["llm"], model=cross_model)
                }
                logger.info(
                    "[Hierarchical] Orchestrator using cross-model: %s", cross_model
                )
                return create_provider(cross_cfg, model_override=cross_model)
            else:
                logger.warning(
                    "[Hierarchical] orchestrator_model='cross' but "
                    "orchestrator_cross_model not set — falling back to same model."
                )
        # "same" 또는 fallback
        return base_llm

    def _write_orchestrator_meta(self, orchestrator_llm: Any) -> None:
        meta = {
            "orchestrator_model_mode": self.orchestrator_model,
            "orchestrator_llm": repr(orchestrator_llm),
            "flow": "hierarchical",
        }
        (self._output_dir / "orchestrator_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _write_orchestrator_summary(self, orchestrator: OrchestratorAgent) -> None:
        summary = {
            "best_ddg": orchestrator._best_ddg
            if orchestrator._best_ddg != float("inf")
            else None,
            "fwkt_rate": orchestrator._fwkt_rate,
            "explored_positions": orchestrator._explored_positions,
            "iterations_logged": len(orchestrator._global_history),
            "history": orchestrator._global_history,
        }
        (self._output_dir / "orchestrator_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
