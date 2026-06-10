"""
planner.py
SSTR2 펩타이드 바인더 Co-Scientist - Planner 에이전트
Role: 연구 설계 / 실험 기획 (Research Design & Experiment Planning)

Planner는 Co-Scientist 루프의 첫 번째 에이전트로서,
실험 목표·제약·예산을 정의하고 각 iteration의 실행 계획(ExperimentPlan)을
생성·갱신하는 책임을 진다.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .base_agent import BaseAgent, MessageType
from ..llm.prompts import get_system_prompt, format_planner_prompt


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StepConfig:
    """단일 파이프라인 스텝 설정.

    Attributes:
        step_id: 스텝 식별자 (예: 'step01_openfold3')
        tool: 사용 도구 이름
        input_schema: 기대 입력 파일/필드 목록
        output_schema: 생성 출력 파일/필드 목록
        params: 도구별 실행 파라미터
        enabled: 이번 iteration에서 실행 여부
    """
    step_id: str
    tool: str
    input_schema: list[str]
    output_schema: list[str]
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class ExperimentPlan:
    """한 iteration의 완전한 실험 계획서.

    Attributes:
        run_id: 실행 고유 ID (형식: YYYYMMDD_HHMM_iterXX)
        iteration: 현재 반복 번호 (1부터 시작)
        parameters: 핵심 설계 파라미터 딕셔너리
            - n_backbone: RFdiffusion이 생성할 백본 수
            - k_seq: 백본당 MPNN 서열 수
            - contigs: RFdiffusion contig 문자열
            - hotspot_res: hotspot residue 목록
            - plddt_gate: ESMFold pLDDT 하한 임계값
            - dock_top_pct: 도킹 상위 통과 비율 (%)
            - rosetta_ddg_max: Rosetta ddG 상한 (kcal/mol)
        steps_config: Step01~07 StepConfig 목록
        gates: 각 스텝별 QC 게이트 조건 딕셔너리
        hypothesis: 이번 iteration의 과학적 가설 (자유 문자열)
        created_at: 계획 생성 시각 (ISO-8601)
        parent_run_id: 이전 iteration의 run_id (최초 iteration은 None)
        changes_from_prev: 이전 대비 변경 사항 목록 (원인-결과 추적용)
    """
    run_id: str
    iteration: int
    parameters: dict[str, Any]
    steps_config: list[StepConfig]
    gates: dict[str, Any]
    hypothesis: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    parent_run_id: Optional[str] = None
    changes_from_prev: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Default plan templates
# ---------------------------------------------------------------------------

_DEFAULT_PARAMETERS: dict[str, Any] = {
    "n_backbone": 50,           # RFdiffusion 백본 생성 수
    "k_seq": 8,                  # 백본당 MPNN 서열 수
    "contigs": "A1-350/0 10-30", # 수용체 체인 A 고정, 펩타이드 10~30 aa
    "hotspot_res": [],           # hotspot residue (예: ["A123", "A145"])
    "peptide_length_min": 10,
    "peptide_length_max": 30,
    "mpnn_temperature": 0.1,     # 서열 다양성 제어 (낮을수록 보수적)
    "mpnn_sampling_n": 8,
    "docking_engine": "diffdock",
    "rosetta_relax_cycles": 5,
    "seed": 42,
}

_DEFAULT_GATES: dict[str, Any] = {
    "esmfold_plddt_min": 75,
    "esmfold_interface_plddt_min": 70,
    "docking_top_pct": 20,
    "rosetta_ddg_max": -5.0,
    "rosetta_clash_max": 10,
    "rosetta_constraint_violations_max": 0,
    "foldmason_lddt_min": 0.6,
}

_DEFAULT_STEPS: list[dict[str, Any]] = [
    {
        "step_id": "step01_openfold3",
        "tool": "run_openfold3",
        "input_schema": ["receptor_id", "receptor_params"],
        "output_schema": ["receptor.pdb", "pocket_definition.json"],
    },
    {
        "step_id": "step02_rfdiffusion",
        "tool": "run_rfdiffusion",
        "input_schema": ["receptor.pdb", "pocket_definition.json"],
        "output_schema": ["backbone_{i}.pdb"],  # i = 0..n_backbone-1
    },
    {
        "step_id": "step03_proteinmpnn",
        "tool": "run_proteinmpnn",
        "input_schema": ["backbone_{i}.pdb"],
        "output_schema": ["seq_{i}_{j}.fasta"],  # j = 0..k_seq-1
    },
    {
        "step_id": "step04_esmfold",
        "tool": "run_esmfold",
        "input_schema": ["seq_{i}_{j}.fasta"],
        "output_schema": ["model_{i}_{j}.pdb", "plddt_summary.csv"],
    },
    {
        "step_id": "step05_docking",
        "tool": "run_docking",
        "input_schema": ["model_{i}_{j}.pdb", "receptor.pdb"],
        "output_schema": ["pose_{i}_{j}.pdb", "docking_scores.csv"],
    },
    {
        "step_id": "step06_pyrosetta",
        "tool": "run_pyrosetta_flexpep",
        "input_schema": ["pose_{i}_{j}.pdb"],
        "output_schema": ["refined_{i}_{j}.pdb", "ddg_table.csv"],
    },
    {
        "step_id": "step07_viz",
        "tool": "run_pymol_render",
        "input_schema": ["refined_{i}_{j}.pdb", "receptor.pdb"],
        "output_schema": [
            "overview.png", "closeup.png",
            "interface_contacts.png", "electrostatics.png",
            "interface_table.csv",
        ],
    },
]

_PYROSETTA_ONLY_STEPS: list[dict[str, Any]] = [
    {
        "step_id": "step06_mutate_dock",
        "tool": "run_pyrosetta_flexpep",
        "input_schema": ["template_complex.pdb", "target_sequence"],
        "output_schema": ["cand_{i}.pdb", "ddg_table.csv"],
    },
    {
        "step_id": "step06_qc",
        "tool": "run_qc_ranker",
        "input_schema": ["ddg_table.csv"],
        "output_schema": ["rank_table.csv", "qc_report.json"],
    },
    {
        "step_id": "step06_critic",
        "tool": "run_scientist_critic",
        "input_schema": ["rank_table.csv", "qc_report.json"],
        "output_schema": ["critic_feedback.json"],
    },
    {
        "step_id": "step06_reporter",
        "tool": "run_reporter",
        "input_schema": ["rank_table.csv", "critic_feedback.json"],
        "output_schema": ["summary.md"],
    },
    {
        "step_id": "step07_viz",
        "tool": "run_pymol_render",
        "input_schema": ["cand_{i}.pdb"],
        "output_schema": ["*_render.pml", "*.png"],
    },
]

_FORBIDDEN_KEYWORDS = (
    "rfdiffusion",
    "rf diffusion",
    "proteinmpnn",
    "protein mpnn",
    "mpnn",
    "esmfold",
    "esm fold",
    "esm-fold",
)


def _normalize_planner_mode(value: str) -> str:
    if value in {"pyrosetta_only", "pyrosetta-only"}:
        return "pyrosetta_only"
    return "default"


# ---------------------------------------------------------------------------
# Planner agent
# ---------------------------------------------------------------------------

class PlannerAgent(BaseAgent):
    """연구 설계 및 실험 기획 에이전트.

    역할:
        1. 실험 목표·제약·예산(시간/GPU)·스코어 기준 정의
        2. 각 step의 I/O 스키마 고정 (파일명/폴더 구조 포함)
        3. iteration별 실험 계획 생성
        4. 초기 파라미터 결정 (n_backbone, k_seq, contigs, hotspot_res 등)
        5. Scientist Critic의 피드백을 반영해 계획 갱신
    """

    def __init__(self, llm_provider: str = "claude", planner_mode: str = "default") -> None:
        super().__init__(
            name="Planner",
            role="연구 설계/실험 기획",
            description=(
                "실험 목표·제약·예산을 정의하고 iteration별 ExperimentPlan을 "
                "생성·갱신한다. Scientist Critic 피드백을 받아 파라미터를 조정하고 "
                "과학적 가설을 명시적으로 기록한다."
            ),
            llm_provider=llm_provider,
        )
        self._plans: list[ExperimentPlan] = []
        self.planner_mode = _normalize_planner_mode(planner_mode)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_initial_plan(
        self,
        receptor_config: dict[str, Any],
        constraints: dict[str, Any],
    ) -> ExperimentPlan:
        """최초 iteration을 위한 실험 계획을 생성한다.

        Args:
            receptor_config: 수용체 정보 딕셔너리
                - receptor_id: PDB ID 또는 파일 경로
                - chain: 분석 대상 체인 ID
                - pocket_residues: 포켓 residue 목록 (선택)
            constraints: 실험 제약 조건
                - max_gpu_hours: GPU 시간 예산
                - max_iterations: 최대 반복 횟수
                - target_top_k: 최종 보고할 후보 수
                - custom_gates: 사용자 정의 QC 임계값 (선택)

        Returns:
            ExperimentPlan: iteration 1 실험 계획
        """
        self.log("최초 실험 계획 생성 시작")

        # --- LLM 분기: LLM이 있으면 프롬프트 기반 계획 생성 시도 ---
        if self.has_llm:
            llm_plan = self._create_plan_via_llm(
                iteration=1,
                receptor_config=receptor_config,
                constraints=constraints,
            )
            if llm_plan is not None:
                if self.validate_plan(llm_plan):
                    self._plans.append(llm_plan)
                    self.log(f"LLM 기반 초기 계획 생성 완료: {llm_plan.run_id}")
                    return llm_plan
                self.log("LLM 계획 검증 실패, 규칙 기반 폴백", level="warning")
            else:
                self.log("LLM 응답 실패, 규칙 기반 폴백", level="warning")

        # --- 규칙 기반 폴백 (기존 로직) ---
        params = copy.deepcopy(_DEFAULT_PARAMETERS)
        gates = copy.deepcopy(_DEFAULT_GATES)

        # receptor config 반영
        if "pocket_residues" in receptor_config:
            params["hotspot_res"] = receptor_config["pocket_residues"]

        # 사용자 정의 게이트 덮어쓰기
        if "custom_gates" in constraints:
            gates.update(constraints["custom_gates"])

        # Default empty mutation guidance for rule-based fallback
        params["mutation_guidance"] = {
            "focus_positions": [],
            "suggested_mutations": {},
            "n_guided": 0,
            "strategy": "random",
        }

        steps = [
            StepConfig(
                step_id=s["step_id"],
                tool=s["tool"],
                input_schema=s["input_schema"],
                output_schema=s["output_schema"],
                params={},
                enabled=True,
            )
            for s in self._step_templates()
        ]

        run_id = self._make_run_id(iteration=1)
        plan = ExperimentPlan(
            run_id=run_id,
            iteration=1,
            parameters=params,
            steps_config=steps,
            gates=gates,
            hypothesis=self._sanitize_hypothesis(
                "초기 탐색: mutate -> dock -> QC -> critic -> reporter 경로로 "
                "PyRosetta 기반 기준선(baseline)을 확립한다."
            ),
            parent_run_id=None,
            changes_from_prev=[],
        )

        if self.validate_plan(plan):
            self._plans.append(plan)
            self.log(f"초기 계획 생성 완료: {run_id}")
        else:
            self.log("계획 검증 실패 - 기본값 재확인 필요", level="error")

        return plan

    def update_plan(
        self,
        iteration: int,
        critic_feedback: dict[str, Any],
        previous_results: dict[str, Any],
    ) -> ExperimentPlan:
        """Scientist Critic의 피드백을 반영해 다음 iteration 계획을 생성한다.

        최대 1-2개의 파라미터만 변경하여 원인-결과 추적 가능성을 유지한다.

        Args:
            iteration: 새로 생성할 iteration 번호
            critic_feedback: CriticAgent.analyze_results()의 반환값
                - proposed_changes: list[ParameterChange]
                - hypothesis: 새 가설 문자열
            previous_results: 이전 iteration 실행 결과 요약

        Returns:
            ExperimentPlan: 갱신된 실험 계획
        """
        self.log(f"Iteration {iteration} 계획 갱신 시작")

        # --- LLM 분기: LLM이 있으면 프롬프트 기반 계획 갱신 시도 ---
        if self.has_llm:
            llm_plan = self._create_plan_via_llm(
                iteration=iteration,
                receptor_config={"name": "SSTR2"},
                constraints={},
                previous_results=previous_results,
                critic_feedback=critic_feedback,
            )
            if llm_plan is not None:
                # parent_run_id 설정
                prev_plan = self._plans[-1] if self._plans else None
                if prev_plan:
                    llm_plan.parent_run_id = prev_plan.run_id
                if self.validate_plan(llm_plan):
                    self._plans.append(llm_plan)
                    self.log(f"LLM 기반 계획 갱신 완료: {llm_plan.run_id}")
                    return llm_plan
                self.log("LLM 갱신 계획 검증 실패, 규칙 기반 폴백", level="warning")
            else:
                self.log("LLM 응답 실패, 규칙 기반 폴백", level="warning")

        # --- 규칙 기반 폴백 (기존 로직) ---
        prev_plan = self._plans[-1] if self._plans else None
        params = copy.deepcopy(prev_plan.parameters if prev_plan else _DEFAULT_PARAMETERS)
        gates = copy.deepcopy(prev_plan.gates if prev_plan else _DEFAULT_GATES)
        changes_applied: list[str] = []

        # Default empty mutation guidance for rule-based fallback
        params["mutation_guidance"] = {
            "focus_positions": [],
            "suggested_mutations": {},
            "n_guided": 0,
            "strategy": "random",
        }

        # Critic 제안 변경사항 적용 (최대 2개 제한)
        proposed = critic_feedback.get("proposed_changes", [])
        for change in proposed[:2]:
            param_name = change.get("parameter_name", "")
            new_val = change.get("new_value")
            old_val = change.get("old_value")
            rationale = change.get("rationale", "")
            if param_name and new_val is not None:
                # gate 파라미터인지 확인
                if param_name in gates:
                    gates[param_name] = new_val
                else:
                    params[param_name] = new_val
                changes_applied.append(
                    f"{param_name}: {old_val} -> {new_val} ({rationale})"
                )
                self.log(f"  파라미터 변경: {param_name} {old_val} -> {new_val}")

        steps = [
            StepConfig(
                step_id=s["step_id"],
                tool=s["tool"],
                input_schema=s["input_schema"],
                output_schema=s["output_schema"],
                params={},
                enabled=True,
            )
            for s in self._step_templates()
        ]

        run_id = self._make_run_id(iteration=iteration)
        hypothesis = self._sanitize_hypothesis(
            critic_feedback.get(
                "hypothesis",
                f"Iteration {iteration}: mutate -> dock -> QC -> critic -> reporter 루프를 조정해 재실험",
            )
        )

        plan = ExperimentPlan(
            run_id=run_id,
            iteration=iteration,
            parameters=params,
            steps_config=steps,
            gates=gates,
            hypothesis=hypothesis,
            parent_run_id=prev_plan.run_id if prev_plan else None,
            changes_from_prev=changes_applied,
        )

        if self.validate_plan(plan):
            self._plans.append(plan)
            self.log(f"Iteration {iteration} 계획 갱신 완료: {run_id}")
        else:
            self.log("갱신된 계획 검증 실패", level="warning")

        return plan

    def validate_plan(self, plan: ExperimentPlan) -> bool:
        """실험 계획의 유효성을 검사한다.

        검사 항목:
        - run_id가 비어있지 않은지
        - n_backbone >= 1, k_seq >= 1
        - 모든 스텝이 정의되어 있는지
        - gates에 필수 키가 있는지

        Args:
            plan: 검사할 ExperimentPlan

        Returns:
            bool: 유효하면 True
        """
        errors: list[str] = []

        if not plan.run_id:
            errors.append("run_id가 비어 있음")

        n_backbone = plan.parameters.get("n_backbone", 0)
        if not isinstance(n_backbone, int) or n_backbone < 1:
            errors.append(f"n_backbone 유효하지 않음: {n_backbone}")

        k_seq = plan.parameters.get("k_seq", 0)
        if not isinstance(k_seq, int) or k_seq < 1:
            errors.append(f"k_seq 유효하지 않음: {k_seq}")

        if not plan.steps_config:
            errors.append("steps_config가 비어 있음")

        required_gate_keys = {"esmfold_plddt_min", "docking_top_pct", "rosetta_ddg_max"}
        missing_keys = required_gate_keys - set(plan.gates.keys())
        if missing_keys:
            errors.append(f"gates에 필수 키 누락: {missing_keys}")

        if errors:
            for e in errors:
                self.log(f"  [검증 실패] {e}", level="warning")
            return False

        return True

    def get_plan_history(self) -> list[ExperimentPlan]:
        """지금까지 생성된 모든 ExperimentPlan 목록을 반환한다."""
        return list(self._plans)

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """파이프라인 컨텍스트를 받아 실험 계획을 생성/갱신한다.

        context 키:
            - receptor_config (dict): 수용체 설정
            - constraints (dict): 실험 제약
            - iteration (int, optional): 현재 반복 번호 (없으면 1로 간주)
            - critic_feedback (dict, optional): Critic 피드백 (iteration > 1)
            - previous_results (dict, optional): 이전 결과 (iteration > 1)

        Returns:
            {'status': 'ok', 'plan': ExperimentPlan, 'run_id': str}
        """
        iteration = context.get("iteration", 1)
        if iteration == 1:
            plan = self.create_initial_plan(
                receptor_config=context.get("receptor_config", {}),
                constraints=context.get("constraints", {}),
            )
        else:
            plan = self.update_plan(
                iteration=iteration,
                critic_feedback=context.get("critic_feedback", {}),
                previous_results=context.get("previous_results", {}),
            )
        return {"status": "ok", "plan": plan, "run_id": plan.run_id}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_plan_via_llm(
        self,
        iteration: int,
        receptor_config: dict[str, Any],
        constraints: dict[str, Any],
        previous_results: Optional[dict[str, Any]] = None,
        critic_feedback: Optional[dict[str, Any]] = None,
    ) -> Optional[ExperimentPlan]:
        """LLM을 통해 ExperimentPlan을 생성한다. 실패 시 None 반환."""
        try:
            prompt = format_planner_prompt(
                iteration=iteration,
                receptor_config=receptor_config,
                constraints=constraints,
                previous_results=previous_results,
                critic_feedback=critic_feedback,
                planner_mode=self.planner_mode,
            )
            system = get_system_prompt("planner", planner_mode=self.planner_mode)
            result = self.llm_generate_json(prompt, system_prompt=system)
            if result is None:
                return None

            run_id = result.get("run_id") or self._make_run_id(iteration)
            params = copy.deepcopy(_DEFAULT_PARAMETERS)
            if "parameters" in result:
                params.update(result["parameters"])
            if "mutation_guidance" in result:
                params["mutation_guidance"] = result["mutation_guidance"]

            steps = [
                StepConfig(
                    step_id=s["step_id"], tool=s["tool"],
                    input_schema=s["input_schema"], output_schema=s["output_schema"],
                    params={}, enabled=True,
                )
                for s in self._step_templates()
            ]

            changes = [
                f"{c.get('parameter', '?')}: {c.get('old_value')} -> {c.get('new_value')} ({c.get('reason', '')})"
                for c in result.get("changes_from_prev", [])
            ]

            return ExperimentPlan(
                run_id=run_id,
                iteration=iteration,
                parameters=params,
                steps_config=steps,
                gates=copy.deepcopy(_DEFAULT_GATES),
                hypothesis=self._sanitize_hypothesis(
                    result.get("hypothesis", f"LLM-generated plan for iteration {iteration}")
                ),
                changes_from_prev=changes,
            )
        except Exception as exc:
            self.log(f"LLM 계획 생성 예외: {exc}", level="error")
            return None

    @staticmethod
    def _make_run_id(iteration: int) -> str:
        """run_id를 생성한다 (형식: YYYYMMDD_HHMM_iterXX_<uuid4 앞 4자>)."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
        uid = uuid.uuid4().hex[:4]
        return f"{ts}_iter{iteration:02d}_{uid}"

    def _step_templates(self) -> list[dict[str, Any]]:
        if self.planner_mode == "pyrosetta_only":
            return _PYROSETTA_ONLY_STEPS
        return _DEFAULT_STEPS

    def _sanitize_hypothesis(self, hypothesis: str) -> str:
        if self.planner_mode != "pyrosetta_only":
            return hypothesis
        lowered = hypothesis.lower()
        if any(token in lowered for token in _FORBIDDEN_KEYWORDS):
            return (
                "PyRosetta-only 모드 가설: mutate -> dock -> QC -> critic -> reporter "
                "루프에서 ddG/clash 기반 선택 전략을 개선한다."
            )
        return hypothesis
