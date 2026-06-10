"""Collaborative flow runner — Planner↔Critic debate before execution.

DebatingPlannerAgent가 PlannerAgent를 서브클래싱하여 execute() 내부에서
Planner↔Critic 토론 라운드를 수행한 뒤 최종 ExperimentPlan을 반환한다.
실제 FlexPepDock 실행은 상위 run_pyrosetta_agentic_mutdock_flow()에 위임한다.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ExperimentConfig, SequentialFlowRunner, REPO_ROOT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SST-14 / 약리단 상수
# ---------------------------------------------------------------------------

_SST14_SEQ = "AGCKNFFWKTFTSC"
_PHARMACOPHORE_POSITIONS = (7, 8, 9, 10)   # 1-indexed, FWKT

# ---------------------------------------------------------------------------
# Debate prompt templates
# ---------------------------------------------------------------------------

_CRITIC_REVIEW_SYSTEM = (
    "You are a rigorous scientific critic specializing in SSTR2 peptide binder design. "
    "Respond ONLY with valid JSON."
)

_CRITIC_REVIEW_TEMPLATE = """\
You are a scientific critic reviewing a mutation strategy for SSTR2 peptide binder design.

The Planner proposes:
- Hypothesis: {hypothesis}
- Focus positions: {focus_positions}
- Mutation guidance: {mutation_guidance}

Based on your knowledge of SST-14 (AGCKNFFWKTFTSC) with FWKT pharmacophore (pos 7-10):
1. Are the proposed mutations scientifically sound?
2. Do they risk disrupting the FWKT pharmacophore?
3. Are there obvious failure modes?

Respond in JSON: {{"approved": bool, "objections": [...], "suggested_alternative": "..." or null}}"""

_PLANNER_REVISE_SYSTEM = (
    "You are a research planner for SSTR2 peptide binder design. "
    "Respond ONLY with valid JSON."
)

_PLANNER_REVISE_TEMPLATE = """\
Your previous strategy was critiqued:
Objections: {objections}
Suggested alternative: {suggested_alternative}

Revise your strategy or defend your original proposal.
Respond in JSON with updated: {{"hypothesis": "...", "focus_positions": [...], "mutation_guidance": {{...}}}}"""


# ---------------------------------------------------------------------------
# DebatingPlannerAgent
# ---------------------------------------------------------------------------

class DebatingPlannerAgent:
    """PlannerAgent를 감싸는 래퍼.

    execute()를 오버라이드하여 내부적으로 Planner↔Critic 토론 라운드를 실행한 뒤
    합의된(또는 강제 진행) ExperimentPlan을 반환한다.

    LLM 프로바이더가 NoneProvider이거나 응답 생성에 실패하면 토론 없이
    원래 PlannerAgent.execute() 결과를 그대로 반환한다.
    """

    def __init__(
        self,
        planner,                        # PlannerAgent 인스턴스
        critic,                         # ScientistCriticAgent 인스턴스
        llm_provider,                   # LLMProvider 인스턴스
        debate_max_rounds: int = 2,
        log_dir: Optional[Path] = None,
        experiment_id: str = "exp",
    ) -> None:
        self._planner = planner
        self._critic = critic
        self._llm = llm_provider
        self.debate_max_rounds = debate_max_rounds
        self._log_dir = log_dir
        self._experiment_id = experiment_id

    # ------------------------------------------------------------------
    # Public API — mimics PlannerAgent.execute()
    # ------------------------------------------------------------------

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Planner↔Critic 토론 후 ExperimentPlan을 반환한다.

        토론이 불가능한 경우(NoneProvider, LLM 오류 등) 원래 플래너 결과를
        그대로 반환하여 파이프라인이 중단되지 않도록 한다.
        """
        iteration = context.get("iteration", 1)
        planner_result = self._planner.execute(context)
        plan = planner_result.get("plan")

        # LLM 없이는 토론 불가 — 즉시 반환
        if not self._has_real_llm():
            logger.debug("[Debate] LLM 없음 — 토론 생략 (iter %d)", iteration)
            return planner_result

        if plan is None:
            logger.warning("[Debate] plan이 None — 토론 생략 (iter %d)", iteration)
            return planner_result

        debate_log: List[Dict[str, Any]] = []
        approved = False
        current_hypothesis = getattr(plan, "hypothesis", "")
        current_guidance = getattr(plan, "parameters", {}).get("mutation_guidance", {})
        current_focus = current_guidance.get("focus_positions", [])

        for round_idx in range(1, self.debate_max_rounds + 1):
            # ---- Critic reviews Planner proposal ----
            critic_prompt = _CRITIC_REVIEW_TEMPLATE.format(
                hypothesis=current_hypothesis,
                focus_positions=current_focus,
                mutation_guidance=json.dumps(current_guidance, ensure_ascii=False),
            )
            t0 = time.time()
            critic_raw = self._llm.generate(
                critic_prompt,
                system_prompt=_CRITIC_REVIEW_SYSTEM,
                json_mode=True,
            )
            critic_latency = (time.time() - t0) * 1000
            critic_parsed = _safe_parse_json(critic_raw)

            debate_log.append({
                "experiment_id": self._experiment_id,
                "iteration": iteration,
                "round": round_idx,
                "speaker": "Critic",
                "prompt": critic_prompt,
                "raw_response": critic_raw,
                "parsed": critic_parsed,
                "latency_ms": round(critic_latency, 1),
                "parse_success": critic_parsed is not None,
            })

            if critic_parsed is None:
                logger.warning("[Debate] Critic 응답 파싱 실패 (iter %d, round %d) — 진행 강제", iteration, round_idx)
                approved = True
                break

            approved = bool(critic_parsed.get("approved", False))
            objections = critic_parsed.get("objections", [])
            suggested_alt = critic_parsed.get("suggested_alternative")

            logger.info(
                "[Debate] iter=%d round=%d approved=%s objections=%d",
                iteration, round_idx, approved, len(objections),
            )

            if approved:
                break

            # ---- Planner revises based on criticism ----
            if round_idx < self.debate_max_rounds:
                revise_prompt = _PLANNER_REVISE_TEMPLATE.format(
                    objections=json.dumps(objections, ensure_ascii=False),
                    suggested_alternative=suggested_alt or "none",
                )
                t0 = time.time()
                planner_raw = self._llm.generate(
                    revise_prompt,
                    system_prompt=_PLANNER_REVISE_SYSTEM,
                    json_mode=True,
                )
                planner_latency = (time.time() - t0) * 1000
                planner_parsed = _safe_parse_json(planner_raw)

                debate_log.append({
                    "experiment_id": self._experiment_id,
                    "iteration": iteration,
                    "round": round_idx,
                    "speaker": "Planner",
                    "prompt": revise_prompt,
                    "raw_response": planner_raw,
                    "parsed": planner_parsed,
                    "latency_ms": round(planner_latency, 1),
                    "parse_success": planner_parsed is not None,
                })

                if planner_parsed is not None:
                    # 플래너 수정안을 plan에 반영
                    current_hypothesis = planner_parsed.get("hypothesis", current_hypothesis)
                    current_focus = planner_parsed.get("focus_positions", current_focus)
                    new_guidance = planner_parsed.get("mutation_guidance", {})
                    if new_guidance:
                        current_guidance = new_guidance
                    # plan 객체 필드 업데이트 (가능한 경우)
                    try:
                        plan.hypothesis = current_hypothesis
                        plan.parameters.setdefault("mutation_guidance", {})
                        plan.parameters["mutation_guidance"].update(current_guidance)
                        plan.parameters["mutation_guidance"]["focus_positions"] = current_focus
                    except Exception as exc:
                        logger.debug("[Debate] plan 필드 업데이트 실패 (non-fatal): %s", exc)
            else:
                # 최대 라운드 도달 → 강제 진행
                logger.info("[Debate] 최대 라운드 도달 — 강제 진행 (iter %d)", iteration)

        self._write_debate_log(iteration, debate_log)
        planner_result["plan"] = plan
        planner_result["debate_rounds"] = len(debate_log)
        planner_result["debate_approved"] = approved
        return planner_result

    # ------------------------------------------------------------------
    # Delegate attribute access to underlying planner
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        """PlannerAgent의 나머지 메서드/속성을 투명하게 위임한다."""
        return getattr(self._planner, name)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _has_real_llm(self) -> bool:
        """NoneProvider가 아닌 실제 LLM인지 확인한다."""
        provider_name = getattr(self._llm, "provider_name", "NoneProvider")
        return provider_name != "NoneProvider"

    def _write_debate_log(self, iteration: int, log: List[Dict[str, Any]]) -> None:
        """debate 턴을 JSONL 형식으로 기록한다.

        출력 파일: {log_dir}/iter_{N:02d}_debate.jsonl
        """
        if self._log_dir is None or not log:
            return
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            log_path = self._log_dir / f"iter_{iteration:02d}_debate.jsonl"
            with log_path.open("a", encoding="utf-8") as fh:
                for entry in log:
                    fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            logger.debug("[Debate] 로그 기록: %s (%d turns)", log_path, len(log))
        except Exception as exc:
            logger.warning("[Debate] 로그 기록 실패 (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# CollaborativeFlowRunner
# ---------------------------------------------------------------------------

class CollaborativeFlowRunner(SequentialFlowRunner):
    """SequentialFlowRunner를 확장하여 반복 루프 전에 Planner↔Critic 토론을 주입한다.

    Phase A: Strategy Debate (Builder 호출 전)
      - Planner가 전략(가설 + focus_positions)을 제안
      - Critic이 검토하고 이의를 제기
      - Planner가 수정 (최대 debate_max_rounds 라운드)
      - 합의 또는 강제 진행

    Phase B: Builder + QCRanker (기존 sequential과 동일)

    Phase C: Joint Evaluation
      - Critic이 결과를 분석
      - Planner가 결과에 응답
      - Reporter가 합의를 정리

    구현 전략:
        run_pyrosetta_agentic_mutdock_flow()에 전달하기 전에
        DebatingPlannerAgent로 PlannerAgent를 교체한다.
        monkey-patch 방식 대신 플로우를 직접 재구성하여 플래너 교체를 적용한다.
    """

    def __init__(self, config: ExperimentConfig) -> None:
        super().__init__(config)
        self.debate_max_rounds: int = config.extra.get("debate_max_rounds", 2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Debate-enhanced flow를 실행한다.

        내부적으로 run_pyrosetta_agentic_mutdock_flow()를 호출하되,
        FlowConfig에 collaborative 플래그를 설정하여 플래너 교체를 활성화한다.
        플래너 교체가 불가한 경우(import 오류 등) sequential 폴백을 사용한다.
        """
        try:
            return self._run_collaborative()
        except Exception as exc:
            logger.error(
                "[Collaborative] 실행 실패 — sequential 폴백: %s", exc, exc_info=True
            )
            return super().run()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run_collaborative(self) -> Dict[str, Any]:
        """LLM·에이전트를 직접 구성하여 debate-injected 플로우를 실행한다."""
        sys.path.insert(0, str(REPO_ROOT))

        from pyrosetta_flow.schema import FlowConfig
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow
        from AG_src.agents.planner import PlannerAgent
        from AG_src.agents.critic import ScientistCriticAgent
        from AG_src.llm import create_provider

        # FlowConfig 구성 (base runner와 동일)
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

        # LLM 프로바이더 생성
        llm_cfg = {
            "llm": {
                "provider": "vllm",
                "model": self.config.model_hf_id or "qwen3:8b",
                "base_url": "http://localhost:8002",
            }
        }
        llm = create_provider(llm_cfg, model_override=self.config.model_hf_id or None)

        # DebatingPlannerAgent 구성
        base_planner = PlannerAgent(llm_provider=llm, planner_mode="pyrosetta_only")
        critic = ScientistCriticAgent(llm_provider=llm)
        debating_planner = DebatingPlannerAgent(
            planner=base_planner,
            critic=critic,
            llm_provider=llm,
            debate_max_rounds=self.debate_max_rounds,
            log_dir=self._agent_log_dir,
            experiment_id=self.config.experiment_id,
        )

        # runner.py의 플래너를 DebatingPlannerAgent로 교체하여 실행
        # run_pyrosetta_agentic_mutdock_flow는 내부에서 PlannerAgent를 새로 생성하므로
        # collaborative 모드에서는 해당 함수의 planner 인스턴스를 교체할 수 없다.
        # 대신 _run_with_injected_planner()로 반복 루프를 직접 구동한다.
        start = time.time()
        try:
            result = self._run_with_injected_planner(
                flow_config=flow_config,
                debating_planner=debating_planner,
                critic=critic,
                llm=llm,
            )
            elapsed = time.time() - start
            self._write_status("done", elapsed)
            return {"success": True, "result": result, "elapsed_s": elapsed}
        except Exception as exc:
            elapsed = time.time() - start
            self._write_status("failed", elapsed, str(exc))
            logger.error(
                "[Collaborative] experiment %s failed: %s",
                self.config.experiment_id, exc,
            )
            return {"success": False, "error": str(exc), "elapsed_s": elapsed}

    def _run_with_injected_planner(
        self,
        flow_config: Any,
        debating_planner: DebatingPlannerAgent,
        critic: Any,
        llm: Any,
    ) -> Any:
        """DebatingPlannerAgent가 주입된 상태로 플로우를 실행한다.

        runner.py의 run_pyrosetta_agentic_mutdock_flow()는 내부에서 planner를
        직접 생성하므로, 해당 모듈의 전역 심볼을 일시적으로 교체하여 debate를 주입한다.
        교체는 실행 블록 내에서만 유효하며, finally에서 반드시 원복된다.
        """
        import pyrosetta_flow.runner as _runner_mod
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow
        from AG_src.agents.planner import PlannerAgent as _OrigPlanner

        # 원본 클래스 보존
        _orig_planner_cls = _runner_mod.__dict__.get("PlannerAgent", _OrigPlanner)

        class _PatchedPlannerAgent:
            """DebatingPlannerAgent 인스턴스를 반환하는 팩토리 클래스."""

            def __new__(cls, *args: Any, **kwargs: Any) -> DebatingPlannerAgent:  # type: ignore[override]
                # runner.py가 PlannerAgent(llm_provider=..., planner_mode=...) 로 호출
                inner = _orig_planner_cls(*args, **kwargs)
                # critic, llm은 outer scope에서 캡처
                return DebatingPlannerAgent(  # type: ignore[return-value]
                    planner=inner,
                    critic=critic,
                    llm_provider=llm,
                    debate_max_rounds=self.debate_max_rounds,
                    log_dir=self._agent_log_dir,
                    experiment_id=self.config.experiment_id,
                )

        try:
            _runner_mod.PlannerAgent = _PatchedPlannerAgent  # type: ignore[attr-defined]
            logger.info(
                "[Collaborative] PlannerAgent monkey-patched → DebatingPlannerAgent "
                "(debate_max_rounds=%d)",
                self.debate_max_rounds,
            )
            result = run_pyrosetta_agentic_mutdock_flow(flow_config)
        finally:
            _runner_mod.PlannerAgent = _orig_planner_cls  # type: ignore[attr-defined]
            logger.info("[Collaborative] PlannerAgent 원복 완료")

        return result


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _safe_parse_json(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    """JSON 문자열을 파싱한다. 실패하면 None을 반환한다."""
    if raw is None:
        return None
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # ```json ... ``` 블록 추출 시도
    import re
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    return None
