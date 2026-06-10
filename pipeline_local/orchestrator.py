"""
orchestrator.py
===============
LOCAL MODE 파이프라인 오케스트레이터
SSTR2 Peptide Binder Pipeline Orchestrator — Local GPU Mode (no NIM API)

원본: AG_src/pipeline/orchestrator.py
변경 사항:
  - 파이프라인 스텝은 pipeline_local.steps에서 import
  - 스키마는 pipeline_local.schemas에서 import
  - 에이전트/LLM은 원본 AG_src에서 직접 import (sys.path 주입)
  - NIM API 참조 없음; 로컬 모델만 사용

동일하게 유지:
  - run_single_iteration() 전체 흐름
  - run() 반복 루프 + 수렴 판단 로직
  - 체크포인트 저장/로드
  - 에이전트 레지스트리 및 stub fallback
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# ---------------------------------------------------------------------------
# 상태 파일 경로 — frontend /api/status 폴링용
# ---------------------------------------------------------------------------
_STATUS_FILE = Path(
    os.environ.get("PIPELINE_STATUS_FILE", "/tmp/pipeline_local_status.json")
)

# ---------------------------------------------------------------------------
# 파이프라인 스텝 정의 — frontend steps[] 렌더링용
# ---------------------------------------------------------------------------
PIPELINE_STEPS: List[Dict[str, str]] = [
    {"id": "step01",  "label": "Receptor Preparation",              "shortLabel": "Receptor"},
    {"id": "silo_a",  "label": "Silo A (RFdiffusion+ProteinMPNN)", "shortLabel": "Silo-A"},
    {"id": "silo_b",  "label": "Silo B (BLOSUM62+FlexPepDock)",    "shortLabel": "Silo-B"},
    {"id": "step03b", "label": "BLOSUM62 Mutation",                "shortLabel": "Mutation"},
    {"id": "step04",  "label": "ESMFold QC",                       "shortLabel": "QC"},
    {"id": "step05",  "label": "Docking (Boltz-2)",                "shortLabel": "Docking"},
    {"id": "step06",  "label": "PyRosetta Refinement",             "shortLabel": "Rosetta"},
    {"id": "step07",  "label": "Analysis",                         "shortLabel": "Analysis"},
]

# ---------------------------------------------------------------------------
# 원본 AG_src를 sys.path에 주입 — 에이전트/LLM 모듈 공유
# ---------------------------------------------------------------------------
_AG_SRC_REPO = Path(os.environ.get(
    "AG_SRC_REPO",
    str(Path(__file__).resolve().parent.parent / "AgenticAI4SCIENCE_pyrosetta_track" / "repos" / "ai4sci-kaeri")
))
if str(_AG_SRC_REPO) not in sys.path:
    sys.path.insert(0, str(_AG_SRC_REPO))

# ---------------------------------------------------------------------------
# 스키마 import — 로컬 복사본 우선, 없으면 원본 AG_src 사용
# ---------------------------------------------------------------------------
try:
    from pipeline_local.schemas.io_schemas import (
        Step01Output,
        Step02Output,
        Step03Output,
        Step03bOutput,
        VariantEntry,
        DockingResult,
        Step04Output,
        Step05Output,
        Step05bOutput,
        Step05cOutput,
        BoltzSelectivityResult,
        SelectivityResult,
        Step06Output,
        RosettaResult,
        Step07Output,
        IterationRecord,
        RankTableRow,
        SequenceEntry,
    )
except ImportError:
    # 로컬 schemas 없으면 원본 사용
    from AG_src.schemas.io_schemas import (  # type: ignore[no-redef]
        Step01Output,
        Step02Output,
        Step03Output,
        Step03bOutput,
        VariantEntry,
        DockingResult,
        Step04Output,
        Step05Output,
        Step05bOutput,
        SelectivityResult,
        Step06Output,
        RosettaResult,
        Step07Output,
        IterationRecord,
        RankTableRow,
        SequenceEntry,
    )

# ---------------------------------------------------------------------------
# 파이프라인 스텝 import — pipeline_local.steps 우선, 없으면 원본 fallback
# ---------------------------------------------------------------------------
try:
    from pipeline_local import steps as _steps_module
    step01_receptor       = _steps_module.step01_receptor
    step02_backbone       = _steps_module.step02_backbone
    step03_sequence       = _steps_module.step03_sequence
    step03b_blosum_mutation = _steps_module.step03b_blosum_mutation
    step04_qc             = _steps_module.step04_qc
    step05_docking        = _steps_module.step05_docking
    step05b_selectivity   = _steps_module.step05b_selectivity
    step05c_boltz_cross   = _steps_module.step05c_boltz_cross
    step06_rosetta        = _steps_module.step06_rosetta
    step07_analysis       = _steps_module.step07_analysis
except (ImportError, AttributeError):
    # pipeline_local.steps 미구현 시 원본 AG_src 스텝 사용
    from AG_src.pipeline import (  # type: ignore[no-redef]
        step01_receptor,
        step02_backbone,
        step03_sequence,
        step03b_blosum_mutation,
        step04_qc,
        step05_docking,
        step05b_selectivity,
        step06_rosetta,
        step07_analysis,
    )

# ---------------------------------------------------------------------------
# 에이전트 import — 원본 AG_src에서 공유
# ---------------------------------------------------------------------------
from AG_src.agents.base_agent import BaseAgent
from AG_src.agents.planner import PlannerAgent, ExperimentPlan

# Tier 2 fix (F13/F14/F15): StatusEmitter 통합 — LOCAL MODE 진행을 UI에 노출
try:
    from backend.status_emitter import StatusEmitter  # type: ignore[import-not-found]
    _STATUS_EMITTER_AVAILABLE = True
except Exception:
    _STATUS_EMITTER_AVAILABLE = False
    StatusEmitter = None  # type: ignore[assignment,misc]
from AG_src.agents.qc_ranker import QCRankerAgent, Candidate, RankTable, QCReport
from AG_src.agents.diversity_manager import DiversityManagerAgent
from AG_src.agents.critic import ScientistCriticAgent, CriticAnalysis, ParameterChange
from AG_src.agents.reporter import ReporterAgent
from AG_src.pipeline.agent_output_validator import validate_agent_output
from AG_src.llm import create_provider  # Ollama 로컬 LLM provider

logger = logging.getLogger(__name__)

DEFAULT_REFERENCE_PEPTIDE_SEQUENCE = "AGCKNFFWKTFTSC"


# ---------------------------------------------------------------------------
# Result 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    """단일 파이프라인 단계 실행 결과 컨테이너."""
    step_name: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    elapsed_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.output and hasattr(self.output, "to_dict"):
            d["output"] = self.output.to_dict()
        return d


@dataclass
class IterationResult:
    """단일 반복(iteration) 전체 실행 결과."""
    iteration: int
    run_id: str
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    top_ddg: float = 0.0
    n_passed_final: int = 0
    hypothesis: str = ""
    next_actions: List[str] = field(default_factory=list)
    converged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "run_id": self.run_id,
            "step_results": {k: v.to_dict() for k, v in self.step_results.items()},
            "top_ddg": self.top_ddg,
            "n_passed_final": self.n_passed_final,
            "hypothesis": self.hypothesis,
            "next_actions": self.next_actions,
            "converged": self.converged,
        }


@dataclass
class AgentResponse:
    """에이전트 응답 컨테이너 (BaseAgent.execute() 위임 + stub fallback)."""
    agent_name: str
    content: Dict[str, Any]
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FinalResult:
    """전체 파이프라인 최종 결과."""
    run_id: str
    total_iterations: int
    iteration_records: List[IterationResult]
    best_candidates: List[Dict[str, Any]]
    converged: bool
    final_report_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "total_iterations": self.total_iterations,
            "iteration_records": [r.to_dict() for r in self.iteration_records],
            "best_candidates": self.best_candidates,
            "converged": self.converged,
            "final_report_path": self.final_report_path,
        }


@dataclass
class GateStats:
    """게이트 통과/실패 통계."""
    passed: int
    failed: int
    threshold: Any

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BranchOutputs:
    """분기 실행 후 후속 단계 입력."""
    step03_out: Step03Output
    step03b_out: Optional[Step03bOutput] = None
    silo_b_rosetta_results: List[Any] = field(default_factory=list)
    dual_mode: bool = False


@dataclass
class QCFilterResult:
    """Step04 QC 실행 결과와 통과 후보."""
    step04_out: Step04Output
    qc_passed: List[Any]


@dataclass
class DockingChainResult:
    """Step05/05b/05c 실행 결과."""
    step05_out: Step05Output
    top_docking: List[DockingResult]
    step05b_output: Optional[Step05bOutput]
    step05c_output: Optional[Step05cOutput]


@dataclass
class RosettaChainResult:
    """Step06 및 게이트 적용 결과."""
    step06_out: Step06Output
    rosetta_passed: List[RosettaResult]
    n_diverse: int
    silo_a_passed: int = 0
    silo_b_passed: int = 0


@dataclass
class AnalysisReportResult:
    """Step07 + Critic + Reporter 실행 결과."""
    step07_result: StepResult
    report_path: str


# ---------------------------------------------------------------------------
# LocalPipelineOrchestrator
# ---------------------------------------------------------------------------


class LocalPipelineOrchestrator:
    """LOCAL MODE SSTR2 펩타이드 바인더 설계 파이프라인 오케스트레이터.

    원본 PipelineOrchestrator와 동일한 로직을 유지하되,
    NIM API 의존성 없이 로컬 GPU 모델만 사용한다.

    Ollama → qwen3:8b (기본값, pipeline_config_local.yaml에서 변경 가능)
    ESMFold / RFdiffusion / ProteinMPNN → 로컬 weights 사용

    Attributes:
        config:          병합된 파이프라인 설정 (YAML 파일에서 로드)
        gate_thresholds: QC 게이트 임계값
        tool_registry:   툴 엔드포인트 레지스트리
        output_base:     루트 출력 디렉토리
        device:          사용할 CUDA 장치 (환경변수 CUDA_VISIBLE_DEVICES 기반)
    """

    def __init__(self, config_path: str) -> None:
        self._logger = logging.getLogger(f"{__name__}.LocalPipelineOrchestrator")
        self._configure_logging()

        config_path_obj = Path(config_path)
        config_dir = config_path_obj.parent

        self.config: Dict[str, Any] = self._load_yaml(config_path_obj)
        self.gate_thresholds: Dict[str, Any] = self._load_yaml(
            config_dir / "gate_thresholds_local.yaml",
            default=self._load_yaml(config_dir / "gate_thresholds.yaml", default={}),
        )
        self.tool_registry: Dict[str, Any] = self._load_yaml(
            config_dir / "tool_registry.yaml", default={}
        )

        self.config["gate_thresholds"] = self.gate_thresholds

        self.output_base: Path = Path(
            self.config.get("output_base_dir", "runs_local")
        )
        self._reference_peptide_sequence: str = str(
            self.config.get("reference_peptide", {}).get(
                "sequence",
                DEFAULT_REFERENCE_PEPTIDE_SEQUENCE,
            )
        )

        # 로컬 GPU 장치 설정
        self.device: str = self._resolve_device()
        self.config["device"] = self.device
        self._logger.info(
            "LocalPipelineOrchestrator 초기화 완료: config=%s, device=%s",
            config_path,
            self.device,
        )

        # 파이프라인 시작 시각 (elapsed_sec 계산용)
        self._pipeline_start_time: float = time.monotonic()
        # 현재 실행 파라미터 캐시 (status 파일에 기록)
        self._max_iterations: int = int(
            self.config.get("iteration", {}).get("max_iterations", 5)
        )

        # 에이전트 인스턴스 초기화
        self._init_agents()

        # ── Frontend 확장 상태 추적 필드 ──────────────────────────────────
        self._step_statuses: Dict[str, str] = {
            s["id"]: "pending" for s in PIPELINE_STEPS
        }
        self._step_start_times: Dict[str, float] = {}
        self._step_durations: Dict[str, str] = {}
        self._agent_messages: Dict[str, Any] = {}
        self._qc_gate_stats: Dict[str, Any] = {}
        self._passed_candidates: List[Dict[str, Any]] = []
        self._timeline: List[Dict[str, Any]] = []
        self._current_run_id: str = ""
        self._current_iteration: int = 0

    # ------------------------------------------------------------------
    # 메인 진입점
    # ------------------------------------------------------------------

    def run(
        self,
        max_iterations: Optional[int] = None,
        resume: bool = False,
        resume_run_id: Optional[str] = None,
    ) -> FinalResult:
        """파이프라인을 실행한다. 최대 max_iterations 반복.

        Args:
            max_iterations:  설정 파일의 max_iterations를 덮어쓰는 값.
            resume:          True면 마지막 체크포인트에서 재개.
            resume_run_id:   resume=True 시 사용할 run_id.

        Returns:
            FinalResult — 모든 반복 결과 및 최상위 후보 목록.
        """
        max_iter: int = max_iterations or int(
            self.config.get("iteration", {}).get("max_iterations", 5)
        )
        convergence_delta: float = float(
            self.config.get("convergence_ddg_delta", 0.5)
        )
        convergence_patience: int = int(
            self.config.get("convergence_patience", 2)
        )

        start_iteration = 1
        state: Dict[str, Any] = {}
        iteration_records: List[IterationResult] = []
        results_history: List[IterationResult] = []

        if resume and resume_run_id:
            state = self._load_state(resume_run_id)
            start_iteration = state.get("next_iteration", 1)
            iteration_records = [
                IterationResult(**r) for r in state.get("iteration_records", [])
            ]
            results_history = iteration_records.copy()
            self._logger.info(
                "체크포인트에서 재개: iteration=%d, run=%s",
                start_iteration,
                resume_run_id,
            )

        no_improvement_count = 0
        # 첫 반복이 항상 개선으로 인식되도록 inf로 초기화
        previous_best_ddg: float = float("inf")

        self._pipeline_start_time = time.monotonic()
        self._max_iterations = max_iter
        self._write_status(
            "start",
            "파이프라인 시작 중...",
            iteration=start_iteration,
            max_iterations=max_iter,
        )

        for iteration in range(start_iteration, max_iter + 1):
            run_id, out_dirs = self._setup_run(iteration)
            self.config["run_id"] = run_id
            self.config["output_dirs"] = out_dirs

            # iteration 시작 시 추적 필드 리셋
            self._current_run_id = run_id
            self._current_iteration = iteration
            self._step_statuses = {s["id"]: "pending" for s in PIPELINE_STEPS}
            self._step_start_times = {}
            self._step_durations = {}
            self._qc_gate_stats = {}
            self._passed_candidates = []

            # Tier 2 fix (F13/F14/F15): StatusEmitter — UI live progress + dashboard archive.
            # 첫 iteration일 때만 생성, 이후 iteration은 같은 emitter 재사용 (iteration field만 갱신).
            if _STATUS_EMITTER_AVAILABLE and not hasattr(self, "_emitter"):
                try:
                    self._emitter = StatusEmitter(
                        run_id=run_id,
                        total_iterations=max_iter,
                        llm_model=str(getattr(self, "_llm_provider", "rule-based")),
                    )
                except Exception as exc:
                    self._logger.warning("[F13] StatusEmitter 초기화 실패 (UI 노출 안 됨): %s", exc)
                    self._emitter = None
            elif _STATUS_EMITTER_AVAILABLE and getattr(self, "_emitter", None) is not None:
                # iteration 갱신
                self._emitter._state["iteration"] = iteration
                self._emitter._state["run_id"] = run_id
                self._emitter.flush()
            else:
                self._emitter = None

            self._write_status(
                "start",
                f"Iteration {iteration}/{max_iter} 준비 중...",
                iteration=iteration,
                max_iterations=max_iter,
            )

            self._logger.info(
                "=" * 60 + "\n  ITERATION %d/%d  run_id=%s\n" + "=" * 60,
                iteration, max_iter, run_id,
            )

            previous_results: Optional[IterationResult] = (
                results_history[-1] if results_history else None
            )

            try:
                iter_result = self.run_single_iteration(
                    iteration=iteration,
                    previous_results=previous_results,
                )
            except Exception as exc:
                self._logger.error(
                    "Iteration %d 처리 중 예외 발생: %s", iteration, exc,
                    exc_info=True,
                )
                self._write_status(
                    "error",
                    f"Iteration {iteration} 오류: {exc}",
                    iteration=iteration,
                    max_iterations=max_iter,
                    error=str(exc),
                )
                self._save_state(
                    run_id=run_id,
                    iteration=iteration,
                    state={
                        "error": str(exc),
                        "iteration_records": [r.to_dict() for r in iteration_records],
                        "next_iteration": iteration,
                    },
                )
                break

            iteration_records.append(iter_result)
            results_history.append(iter_result)

            self._write_status(
                "agents",
                f"Iteration {iteration}/{max_iter} 완료 — 최고 ddG: {iter_result.top_ddg:.2f}",
                iteration=iteration,
                max_iterations=max_iter,
                candidates_passed=iter_result.n_passed_final,
                top_ddg=iter_result.top_ddg,
            )

            # 수렴 판단
            ddg_improvement = abs(previous_best_ddg - iter_result.top_ddg)
            if previous_best_ddg != float("inf") and ddg_improvement < convergence_delta:
                no_improvement_count += 1
                self._logger.info(
                    "ddG 개선 없음 (delta=%.3f < %.3f). patience %d/%d",
                    ddg_improvement, convergence_delta,
                    no_improvement_count, convergence_patience,
                )
            else:
                no_improvement_count = 0
            previous_best_ddg = iter_result.top_ddg

            # 반복 후 상태 저장
            self._save_state(
                run_id=run_id,
                iteration=iteration,
                state={
                    "iteration_records": [r.to_dict() for r in iteration_records],
                    "next_iteration": iteration + 1,
                    "previous_best_ddg": previous_best_ddg,
                },
            )

            if self._check_convergence(results_history):
                self._logger.info("수렴 감지 — iteration %d에서 종료.", iteration)
                iter_result.converged = True
                break

            if no_improvement_count >= convergence_patience:
                self._logger.info(
                    "%d 반복 연속 개선 없음 — 조기 종료.", convergence_patience
                )
                break

        best_candidates = self._aggregate_best_candidates(iteration_records)
        final_report_path = self._write_final_report(
            iteration_records, best_candidates,
            run_id=self.config.get("run_id", "final"),
        )
        converged = any(r.converged for r in iteration_records)

        _best_ddg = best_candidates[0].get("ddg", 0.0) if best_candidates else 0.0
        self._write_status(
            "completed",
            "파이프라인 완료.",
            iteration=len(iteration_records),
            max_iterations=max_iter,
            candidates_passed=sum(r.n_passed_final for r in iteration_records),
            top_ddg=_best_ddg,
            converged=converged,
            final_report_path=final_report_path,
        )

        return FinalResult(
            run_id=self.config.get("run_id", "final"),
            total_iterations=len(iteration_records),
            iteration_records=iteration_records,
            best_candidates=best_candidates,
            converged=converged,
            final_report_path=final_report_path,
        )

    # ------------------------------------------------------------------
    # 단일 반복 실행
    # ------------------------------------------------------------------

    def run_single_iteration(
        self,
        iteration: int,
        previous_results: Optional[IterationResult] = None,
    ) -> IterationResult:
        """단일 반복을 실행하고 IterationResult를 반환한다.

        실행 순서:
          1. Planner   → 가설/계획 업데이트
          2. Builder   → Step01 .. Step07 실행
          3. QC&Ranker → 게이트 적용 및 랭킹
          4. Diversity → 구조 다양성 확보
          5. Critic    → 다음 반복을 위한 개선안 제시
          6. Reporter  → 반복 보고서 생성

        Args:
            iteration:        1-based 반복 번호.
            previous_results: 이전 반복의 IterationResult (첫 반복 시 None).

        Returns:
            모든 스텝 결과가 채워진 IterationResult.
        """
        run_id: str = self.config.get("run_id", "default_run")
        iter_result = IterationResult(iteration=iteration, run_id=run_id)
        previous_results_dict = previous_results.to_dict() if previous_results else {}

        planner_resp = self._invoke_agent(
            "planner",
            context={
                "iteration": iteration,
                "previous_results": previous_results_dict,
                "config": self.config,
            },
        )
        iter_result.hypothesis = planner_resp.content.get(
            "hypothesis", f"Iteration {iteration}: default hypothesis"
        )
        param_updates = planner_resp.content.get("parameter_updates", {})
        if param_updates:
            self._apply_parameter_updates(param_updates)
            self._logger.info("[Planner] 파라미터 업데이트 적용: %s", list(param_updates.keys()))

        self._write_status(
            "step01_receptor", "수용체 구조 준비 중...",
            iteration=iteration, max_iterations=self._max_iterations,
        )
        step01_result = self._execute_step(
            "step01_receptor",
            lambda: step01_receptor.prepare_receptor(self.config),
        )
        iter_result.step_results["step01"] = step01_result
        if not step01_result.success:
            self._logger.error("[Builder] Step01 실패 — 반복 중단.")
            iter_result.next_actions = ["Fix receptor preparation before next iteration."]
            return iter_result
        step01_out: Step01Output = step01_result.output

        branch_outputs = self._run_builder_branch(step01_out, iteration, iter_result)
        if branch_outputs is None:
            return iter_result

        dual_mode = branch_outputs.dual_mode
        step03_out = branch_outputs.step03_out
        step03b_out = branch_outputs.step03b_out
        silo_b_rosetta_results = branch_outputs.silo_b_rosetta_results

        self._write_status(
            "step04_qc", "ESMFold QC 실행 중...",
            iteration=iteration, max_iterations=self._max_iterations,
            candidates_generated=len(step03_out.sequences),
        )
        qc_filter_result = self._run_qc_filter(step03_out, iter_result)
        if qc_filter_result is None:
            if dual_mode and silo_b_rosetta_results:
                self._logger.warning(
                    "[Builder] Silo A Step04 실패 — Silo B 후보만으로 계속 진행."
                )
                qc_filter_result = QCFilterResult(
                    step04_out=Step04Output(qc_results=[]),
                    qc_passed=[],
                )
            else:
                return iter_result
        step04_out = qc_filter_result.step04_out
        qc_passed = qc_filter_result.qc_passed
        plddt_stats = self._compute_gate_stats(
            total=len(step04_out.qc_results),
            passed=len(qc_passed),
            threshold=float(self.gate_thresholds.get("esmfold_plddt_min", 60.0)),
        )
        self._qc_gate_stats["plddt"] = plddt_stats.to_dict()
        self._add_timeline(
            "step04_qc", "completed",
            f"{plddt_stats.passed}/{len(step04_out.qc_results)} 통과 "
            f"(pLDDT ≥ {plddt_stats.threshold})",
        )

        if not qc_passed:
            if dual_mode and silo_b_rosetta_results:
                self._logger.warning(
                    "[Dual] Silo A QC 게이트 통과 0/%d. Silo B %d 후보로 계속 진행.",
                    len(step04_out.qc_results),
                    len(silo_b_rosetta_results),
                )
            else:
                self._logger.warning(
                    "[QC&Ranker] QC 게이트 통과 0/%d. 반복 중단.",
                    len(step04_out.qc_results),
                )
                return iter_result

        _ = self._invoke_agent(
            "qc_ranker",
            context={
                "qc_results": [r.to_dict() for r in step04_out.qc_results],
                "passed": len(qc_passed),
                "failed": len(step04_out.qc_results) - len(qc_passed),
            },
        )
        self._logger.info(
            "[QC&Ranker] %d/%d 후보 ESMFold 게이트 통과.",
            len(qc_passed), len(step04_out.qc_results),
        )

        self._write_status(
            "step05_docking", "도킹 실행 중 (DiffDock / Boltz-2)...",
            iteration=iteration, max_iterations=self._max_iterations,
            candidates_generated=len(step03_out.sequences),
            candidates_passed=len(qc_passed),
        )
        docking_chain_result = self._run_docking(
            qc_passed=qc_passed,
            receptor_pdb=step01_out.receptor_pdb_path,
            step03_out=step03_out,
            step03b_out=step03b_out,
            iter_result=iter_result,
        )
        if docking_chain_result is None:
            return iter_result
        step05_out = docking_chain_result.step05_out
        top_docking = docking_chain_result.top_docking
        dock_pct = float(self.gate_thresholds.get("docking_top_pct", 20.0))
        docking_stats = self._compute_gate_stats(
            total=len(step05_out.docking_results)
            if hasattr(step05_out, "docking_results")
            else len(qc_passed),
            passed=len(top_docking),
            threshold=f"top {int(dock_pct)}%",
        )
        self._qc_gate_stats["docking"] = docking_stats.to_dict()
        self._add_timeline(
            "step05_docking", "completed",
            f"{docking_stats.passed}/{docking_stats.passed + docking_stats.failed} 통과 "
            f"(상위 {int(dock_pct)}%)",
        )

        if not top_docking:
            if dual_mode and silo_b_rosetta_results:
                self._logger.warning(
                    "[Dual] Silo A 도킹 게이트 통과 후보 없음. Silo B %d 후보로 계속 진행.",
                    len(silo_b_rosetta_results),
                )
            else:
                self._logger.warning("[QC&Ranker] 도킹 게이트 통과 후보 없음.")
                return iter_result

        if docking_chain_result.step05b_output is not None:
            self._logger.info(
                "[Step05b] %d/%d 선택성 게이트 통과",
                len(docking_chain_result.step05b_output.passed_candidates()),
                len(docking_chain_result.step05b_output.selectivity_results),
            )
        if docking_chain_result.step05c_output is not None:
            self._logger.info(
                "[Step05c] %d/%d Boltz-2 selectivity 통과 (T2 이상)",
                docking_chain_result.step05c_output.n_passed,
                docking_chain_result.step05c_output.n_total,
            )

        diverse_top = self._run_diversity_filter(top_docking)
        self._logger.info(
            "[Diversity] %d -> %d 후보 (다양성 필터 후).",
            len(top_docking), len(diverse_top),
        )

        self._write_status(
            "step06_rosetta", "Rosetta FlexPepDock 정제 중...",
            iteration=iteration, max_iterations=self._max_iterations,
            candidates_passed=len(
                [
                    c for c in diverse_top
                    if not (
                        getattr(c, "source", "") == "silo_a"
                        or str(getattr(c, "seq_id", "")).startswith("a_")
                    )
                ]
            ),
        )
        rosetta_chain_result = self._run_rosetta(
            candidates=diverse_top,
            sequence_map=self._build_sequence_map(step03_out, step03b_out),
            receptor_pdb=step01_out.receptor_pdb_path,
            iter_result=iter_result,
            dual_mode=dual_mode,
            silo_b_rosetta_results=silo_b_rosetta_results,
        )
        if rosetta_chain_result is None:
            return iter_result

        step06_out = rosetta_chain_result.step06_out
        self._finalize_rosetta_results(
            iter_result=iter_result,
            rosetta_chain_result=rosetta_chain_result,
            dual_mode=dual_mode,
            silo_b_total=len(silo_b_rosetta_results),
        )

        self._write_status(
            "step07_analysis", "분석 및 시각화 생성 중...",
            iteration=iteration, max_iterations=self._max_iterations,
            candidates_passed=iter_result.n_passed_final,
            top_ddg=iter_result.top_ddg,
        )
        analysis_result = self._run_analysis_reports(
            iteration=iteration, run_id=run_id, iter_result=iter_result,
            previous_results=previous_results_dict, receptor_pdb=step01_out.receptor_pdb_path,
            step06_out=step06_out,
        )
        self._logger.info("[Reporter] 반복 보고서: %s", analysis_result.report_path)
        return iter_result

    def _run_builder_branch(
        self,
        step01_out: Step01Output,
        iteration: int,
        iter_result: IterationResult,
    ) -> Optional[BranchOutputs]:
        """Step01 이후 branch selection을 처리한다."""
        dual_mode = bool(self.config.get("dual_silo", {}).get("enabled", False))
        approach_b_enabled = bool(self.config.get("approach_b", {}).get("enabled", False))

        if dual_mode:
            self._logger.info(
                "[Builder] 듀얼 사일로 모드 활성화: Silo A + Silo B 순차 실행."
            )
            self._write_status(
                "silo_a", "Silo A (RFdiffusion + ProteinMPNN) 실행 중...",
                iteration=iteration, max_iterations=self._max_iterations,
            )
            silo_a_seqs = self._run_silo_a(step01_out, iteration)
            self._logger.info("[Dual] Silo A → %d 서열 생성.", len(silo_a_seqs))
            self._write_status(
                "silo_b", "Silo B (BLOSUM62 씨드 + FlexPepDock) 실행 중...",
                iteration=iteration, max_iterations=self._max_iterations,
            )
            silo_b_rosetta_results = self._run_silo_b(step01_out, iteration)
            branch_outputs = self._run_dual_silo(silo_a_seqs, silo_b_rosetta_results)
            self._logger.info(
                "[Dual] Silo B → %d 후보 (FlexPepDock ddG 포함).",
                len(branch_outputs.silo_b_rosetta_results),
            )
            return branch_outputs

        if approach_b_enabled:
            self._logger.info("[Builder] Approach B 활성화: Step02/03 스킵, Step03b 실행.")
            self._write_status(
                "step03b_blosum", "BLOSUM62 돌연변이 생성 중 (Approach B)...",
                iteration=iteration, max_iterations=self._max_iterations,
            )
            branch_outputs = self._run_approach_b(iter_result)
            if branch_outputs is None:
                self._logger.error("[Builder] Step03b 실패 — 반복 중단.")
                return None
            if not branch_outputs.step03_out.sequences:
                self._logger.warning("[Builder] 변이체 없음 — 반복 중단.")
                return None
            if branch_outputs.step03b_out is not None and self.config.get("approach_b", {}).get(
                "stability_prescreen", True
            ):
                min_hl = float(
                    self.config.get("approach_b", {}).get(
                        "stability_prescreen_min_hours", 50.0
                    )
                )
                self._logger.info(
                    "[Step03b-QC] 안정성 사전 스크리닝: %d/%d 통과 (>= %.0fh)",
                    len(branch_outputs.step03_out.sequences),
                    len(branch_outputs.step03b_out.variants),
                    min_hl,
                )
            return branch_outputs

        self._write_status(
            "step02_backbone", "백본 구조 생성 중 (RFdiffusion)...",
            iteration=iteration, max_iterations=self._max_iterations,
        )
        step03_out = self._run_approach_a(step01_out, iteration, iter_result)
        if step03_out is None:
            if not iter_result.step_results["step02"].success:
                self._logger.error("[Builder] Step02 실패 — 반복 중단.")
            else:
                self._logger.warning("[Builder] 백본 없음 또는 Step03 실패 — 반복 중단.")
            return None
        return BranchOutputs(step03_out=step03_out)

    def _run_approach_a(
        self,
        step01_out: Step01Output,
        iteration: int,
        iter_result: IterationResult,
    ) -> Optional[Step03Output]:
        """단일 Approach A (RFdiffusion + ProteinMPNN)를 실행한다."""
        step02_result = self._execute_step(
            "step02_backbone",
            lambda: step02_backbone.generate_backbones(
                receptor_pdb=step01_out.receptor_pdb_path,
                pocket_info={"pocket_residues": step01_out.pocket_residues},
                config=self.config,
            ),
        )
        iter_result.step_results["step02"] = step02_result
        if not step02_result.success:
            return None

        step02_out: Step02Output = step02_result.output
        if not step02_out.backbone_pdbs:
            return None

        self._write_status(
            "step03_sequence", "서열 설계 중 (ProteinMPNN)...",
            iteration=iteration, max_iterations=self._max_iterations,
            candidates_generated=len(step02_out.backbone_pdbs),
        )
        step03_result = self._execute_step(
            "step03_sequence",
            lambda: step03_sequence.design_sequences(
                backbones=step02_out.backbone_pdbs,
                config=self.config,
            ),
        )
        iter_result.step_results["step03"] = step03_result
        if not step03_result.success:
            return None
        return step03_result.output

    def _run_approach_b(
        self,
        iter_result: IterationResult,
    ) -> Optional[BranchOutputs]:
        """단일 Approach B (BLOSUM mutation)를 실행한다."""
        step03b_result = self._execute_step(
            "step03b_blosum_mutation",
            lambda: step03b_blosum_mutation.run_approach_b(self.config),
        )
        iter_result.step_results["step03b"] = step03b_result
        if not step03b_result.success:
            return None

        step03b_out: Step03bOutput = step03b_result.output
        variants_to_use = step03b_out.variants
        approach_b_cfg = self.config.get("approach_b", {})
        if approach_b_cfg.get("stability_prescreen", True):
            from AG_src.pipeline.step08_stability import predict_half_life as _predict_hl

            min_hl = float(approach_b_cfg.get("stability_prescreen_min_hours", 50.0))
            variants_to_use = [
                v for v in step03b_out.variants
                if _predict_hl(v.sequence, []) >= min_hl
            ]

        step03_out = Step03Output(
            sequences=[
                SequenceEntry(
                    backbone_idx=0,
                    seq_idx=i,
                    sequence=v.sequence,
                    fasta_path="",
                    seq_id=v.variant_id,
                )
                for i, v in enumerate(variants_to_use)
            ]
        )
        return BranchOutputs(step03_out=step03_out, step03b_out=step03b_out)

    def _run_dual_silo(
        self,
        silo_a_seqs: List[Any],
        silo_b_rosetta_results: List[Any],
    ) -> BranchOutputs:
        """듀얼 사일로 실행 결과를 통합한다."""
        for seq in silo_a_seqs:
            seq.seq_id = f"a_{seq.seq_id}"
        return BranchOutputs(
            step03_out=Step03Output(sequences=silo_a_seqs),
            silo_b_rosetta_results=silo_b_rosetta_results,
            dual_mode=True,
        )

    def _run_qc_filter(
        self,
        step03_out: Step03Output,
        iter_result: IterationResult,
    ) -> Optional[QCFilterResult]:
        """Step04 QC를 실행하고 통과 후보를 반환한다."""
        step04_result = self._execute_step(
            "step04_qc",
            lambda: step04_qc.run_qc(
                sequences=step03_out.sequences,
                config=self.config,
            ),
        )
        iter_result.step_results["step04"] = step04_result
        if not step04_result.success:
            return None

        step04_out: Step04Output = step04_result.output
        return QCFilterResult(
            step04_out=step04_out,
            qc_passed=step04_out.passed(),
        )

    def _run_diversity_filter(self, top_docking: List[DockingResult]) -> List[DockingResult]:
        """Diversity manager 응답에 따라 도킹 후보를 재선택한다."""
        diversity_resp = self._invoke_agent(
            "diversity_manager",
            context={"docking_results": [r.to_dict() for r in top_docking]},
        )
        docking_by_sid = {r.seq_id: r for r in top_docking}
        return [
            docking_by_sid[sid]
            for sid in diversity_resp.content.get(
                "selected_seq_ids", [r.seq_id for r in top_docking]
            )
            if sid in docking_by_sid
        ]

    def _run_docking(
        self,
        qc_passed: List[Any],
        receptor_pdb: str,
        step03_out: Step03Output,
        step03b_out: Optional[Step03bOutput],
        iter_result: IterationResult,
    ) -> Optional[DockingChainResult]:
        """Step05 도킹과 selectivity 체인을 실행한다."""
        step05_result = self._execute_step(
            "step05_docking",
            lambda: step05_docking.run_docking(
                candidates=qc_passed,
                receptor_pdb=receptor_pdb,
                config=self.config,
            ),
        )
        iter_result.step_results["step05"] = step05_result
        if not step05_result.success:
            return None

        step05_out: Step05Output = step05_result.output
        step05b_output, step05c_output = self._run_selectivity_chain(
            step05_out=step05_out,
            step03_out=step03_out,
            step03b_out=step03b_out,
        )
        return DockingChainResult(
            step05_out=step05_out,
            top_docking=step05_out.top_pct(
                pct=float(self.gate_thresholds.get("docking_top_pct", 20.0))
            ),
            step05b_output=step05b_output,
            step05c_output=step05c_output,
        )

    def _run_selectivity_chain(
        self,
        step05_out: Step05Output,
        step03_out: Step03Output,
        step03b_out: Optional[Step03bOutput],
    ) -> Tuple[Optional[Step05bOutput], Optional[Step05cOutput]]:
        """Step05b/05c 선택성 체인을 실행한다."""
        step05b_output: Optional[Step05bOutput]
        try:
            selectivity_config = {
                **self.config.get("selectivity", {}),
                "selectivity_margin_min": self.gate_thresholds.get(
                    "selectivity_margin_min", -2.0
                ),
                "offtarget_max_allowed": self.gate_thresholds.get(
                    "offtarget_max_allowed", -3.0
                ),
            }
            step05b_output = step05b_selectivity.run_selectivity_screening(
                candidates=step05_out.docking_results
                if hasattr(step05_out, "docking_results") else [],
                offtarget_receptors=self.config.get("off_target_receptors", []),
                config=selectivity_config,
            )
        except Exception as exc:
            self._logger.warning(
                "Step 05b 선택성 스크리닝 실패: %s. 선택성 필터 없이 진행.", exc
            )
            step05b_output = None

        # Step 05b 결과 파일 저장
        if step05b_output is not None:
            _out_dirs = self.config.get("output_dirs", {})
            _05b_dir = Path(_out_dirs.get("05b_selectivity", "runs_local/05b_selectivity"))
            try:
                step05b_selectivity.save_selectivity_results(step05b_output, _05b_dir)
                self._logger.info("[Step05b] 선택성 결과 저장 완료: %s", _05b_dir)
            except Exception as _e:
                self._logger.warning("[Step05b] 선택성 결과 저장 실패 (비치명): %s", _e)

        # Step 05c: Boltz-2 Selectivity Cross-Validation
        step05c_output: Optional[Step05cOutput] = None
        boltz_cross_cfg = self.config.get("boltz_cross", {})
        if not boltz_cross_cfg.get("enabled", False):
            self._logger.debug("[Step05c] boltz_cross.enabled=false — 스킵")
            return step05b_output, step05c_output

        self._logger.warning(
            "[Step05c] iPTM 해석 한계 — iPTM은 geometry 신뢰도이며 결합 친화도/selectivity 순위 proxy 아님. "
            "SST-14 vs SSTR1~5 실측 검증에서 Ki↔iPTM 순위 일치 0/5. "
            "본 결과는 1차 스크리닝용. 정량 평가는 FEP/MM-GBSA/실측 Ki 필요. "
            "근거: _workspace/release/msa-routing-crosscheck-synthesis-2026-05-12.md"
        )
        try:
            step05c_output = step05c_boltz_cross.run_boltz_cross_validation(
                candidates=step05_out.docking_results
                if hasattr(step05_out, "docking_results") else [],
                offtarget_receptors=[
                    {"name": n, "uniprot": u}
                    for n, u in [
                        ("SSTR1", "P30872"),
                        ("SSTR3", "P32745"),
                        ("SSTR4", "P31391"),
                        ("SSTR5", "P35346"),
                    ]
                ],
                sstr2_receptor={"name": "SSTR2", "uniprot": "P30874"},
                config={
                    **boltz_cross_cfg,
                    "work_dir": str(
                        Path(self.config.get("output_dir", "runs_local"))
                        / "step05c_boltz_cross"
                    ),
                    "sequence_map": self._build_sequence_map(step03_out, step03b_out),
                },
            )
        except Exception as exc:
            self._logger.warning(
                "Step 05c Boltz-2 cross-validation 실패: %s. 스킵 후 진행.", exc
            )
            step05c_output = None

        # Step 05c 결과 파일 저장
        if step05c_output is not None:
            _out_dirs = self.config.get("output_dirs", {})
            _05c_dir = Path(
                _out_dirs.get(
                    "05c_boltz_cross",
                    str(Path(_out_dirs.get("05b_selectivity", "runs_local/05b_selectivity")).parent / "05c_boltz_cross"),
                )
            )
            try:
                step05c_boltz_cross.save_step05c_results(step05c_output, _05c_dir)
                self._logger.info("[Step05c] Boltz-2 결과 저장 완료: %s", _05c_dir)
            except Exception as _e:
                self._logger.warning("[Step05c] Boltz-2 결과 저장 실패 (비치명): %s", _e)

        return step05b_output, step05c_output

    def _run_rosetta(
        self,
        candidates: List[Any],
        sequence_map: Dict[str, str],
        receptor_pdb: str,
        iter_result: IterationResult,
        dual_mode: bool,
        silo_b_rosetta_results: List[Any],
    ) -> Optional[RosettaChainResult]:
        """Step06 Rosetta 실행과 듀얼 사일로 병합을 처리한다."""
        silo_a_diverse = [
            c
            for c in candidates
            if getattr(c, "source", "") == "silo_a"
            or str(getattr(c, "seq_id", "")).startswith("a_")
        ]
        silo_other = [c for c in candidates if c not in silo_a_diverse]

        if silo_other:
            step06_result = self._execute_step(
                "step06_rosetta",
                lambda: step06_rosetta.run_rosetta_refinement(
                    candidates=silo_other,
                    receptor_pdb=receptor_pdb,
                    config={**self.config, "sequence_map": sequence_map},
                ),
            )
        else:
            step06_result = StepResult(
                step_name="step06_rosetta",
                success=True,
                output=Step06Output(rosetta_results=[]),
            )
            self._step_statuses["step06"] = "completed"

        iter_result.step_results["step06"] = step06_result
        if not step06_result.success:
            if not (dual_mode and silo_b_rosetta_results):
                return None
            step06_out = Step06Output(rosetta_results=[])
        else:
            step06_out = step06_result.output

        rosetta_thresh = float(self.gate_thresholds.get("rosetta_ddg_max", 498.4713))
        rosetta_passed, _ = step06_rosetta.apply_rosetta_gate(
            step06_out.rosetta_results,
            ddg_threshold=rosetta_thresh,
            clash_max=int(self.gate_thresholds.get("rosetta_clash_max", 0)),
        )
        for candidate in silo_a_diverse:
            rosetta_passed.append(
                RosettaResult(
                    seq_id=getattr(
                        candidate, "seq_id", str(getattr(candidate, "candidate_id", ""))
                    ),
                    ddg=getattr(candidate, "dock_score", 0.0),
                    total_score=0.0,
                    clash_score=0.0,
                    constraint_violations=0,
                    refined_pdb="",
                    source="silo_a",
                )
            )

        n_diverse = len(candidates)
        silo_b_passed_count = 0
        if dual_mode and silo_b_rosetta_results:
            silo_b_passed, _ = step06_rosetta.apply_rosetta_gate(
                silo_b_rosetta_results,
                ddg_threshold=rosetta_thresh,
                clash_max=int(self.gate_thresholds.get("rosetta_clash_max", 0)),
            )
            silo_b_passed_count = len(silo_b_passed)
            rosetta_passed = list(rosetta_passed) + list(silo_b_passed)
            step06_out = Step06Output(
                rosetta_results=step06_out.rosetta_results + silo_b_rosetta_results
            )
            n_diverse += len(silo_b_rosetta_results)

        return RosettaChainResult(
            step06_out=step06_out,
            rosetta_passed=list(rosetta_passed),
            n_diverse=n_diverse,
            silo_a_passed=sum(
                1 for r in rosetta_passed if getattr(r, "source", "silo_a") == "silo_a"
            ),
            silo_b_passed=silo_b_passed_count,
        )

    def _finalize_rosetta_results(
        self,
        iter_result: IterationResult,
        rosetta_chain_result: RosettaChainResult,
        dual_mode: bool,
        silo_b_total: int,
    ) -> None:
        """Rosetta 게이트 결과를 iteration 상태에 반영한다."""
        rosetta_passed = rosetta_chain_result.rosetta_passed
        rosetta_thresh = float(self.gate_thresholds.get("rosetta_ddg_max", 498.4713))
        if dual_mode and silo_b_total:
            self._logger.info(
                "[Dual] Silo B 게이트 결과: %d 통과 / %d 실패",
                rosetta_chain_result.silo_b_passed,
                silo_b_total - rosetta_chain_result.silo_b_passed,
            )
            self._logger.info(
                "[Dual] 최종 병합 후보: Silo A + Silo B = %d 통과",
                len(rosetta_passed),
            )

        rosetta_stats = self._compute_gate_stats(
            total=rosetta_chain_result.n_diverse,
            passed=len(rosetta_passed),
            threshold=rosetta_thresh,
        )
        self._qc_gate_stats["rosetta"] = rosetta_stats.to_dict()
        if not rosetta_passed:
            self._logger.warning("[QC&Ranker] Rosetta 게이트 통과 후보 없음.")
            return

        iter_result.top_ddg = min(r.ddg for r in rosetta_passed)
        iter_result.n_passed_final = len(rosetta_passed)
        self._logger.info(
            "[QC&Ranker] %d 후보 Rosetta 게이트 통과. 최고 ddG=%.2f.",
            len(rosetta_passed), iter_result.top_ddg,
        )
        self._passed_candidates = [
            {
                "id": r.seq_id,
                "sequence": getattr(r, "sequence", ""),
                "plddt": float(getattr(r, "plddt_mean", 0.0)),
                "ddG": float(r.ddg),
                "source": getattr(r, "source", "silo_a"),
                "status": "passed",
            }
            for r in rosetta_passed
        ]
        if dual_mode:
            self._logger.info(
                "[Dual] 통과 후보 소스별 통계 — Silo A: %d, Silo B: %d",
                rosetta_chain_result.silo_a_passed,
                rosetta_chain_result.silo_b_passed,
            )
            self._qc_gate_stats["rosetta"]["silo_a_passed"] = rosetta_chain_result.silo_a_passed
            self._qc_gate_stats["rosetta"]["silo_b_passed"] = rosetta_chain_result.silo_b_passed
        self._add_timeline(
            "step06_rosetta", "completed",
            f"{len(rosetta_passed)}/{rosetta_chain_result.n_diverse} 통과 "
            f"(ddG ≤ {rosetta_thresh})",
        )

    def _run_analysis_reports(
        self,
        iteration: int,
        run_id: str,
        iter_result: IterationResult,
        previous_results: Dict[str, Any],
        receptor_pdb: str,
        step06_out: Step06Output,
    ) -> AnalysisReportResult:
        """Step07 분석과 Critic/Reporter 에이전트 호출을 수행한다."""
        step07_result = self._execute_step(
            "step07_analysis",
            lambda: step07_analysis.run_analysis(
                candidates=step06_out.rosetta_results,
                receptor_pdb=receptor_pdb,
                config=self.config,
            ),
        )
        iter_result.step_results["step07"] = step07_result

        critic_resp = self._invoke_agent(
            "critic",
            context={
                "iteration": iteration,
                "hypothesis": iter_result.hypothesis,
                "top_ddg": iter_result.top_ddg,
                "n_passed_final": iter_result.n_passed_final,
                "step_results": {k: v.to_dict() for k, v in iter_result.step_results.items()},
                "previous_results": previous_results,
            },
        )
        iter_result.next_actions = critic_resp.content.get("next_actions", [])[:2]

        reporter_resp = self._invoke_agent(
            "reporter",
            context={
                "iteration": iteration,
                "run_id": run_id,
                "iter_result": iter_result.to_dict(),
            },
        )
        return AnalysisReportResult(
            step07_result=step07_result,
            report_path=reporter_resp.content.get("report_path", ""),
        )

    @staticmethod
    def _compute_gate_stats(total: int, passed: int, threshold: Any) -> GateStats:
        """게이트 통계 계산."""
        return GateStats(
            passed=passed,
            failed=max(0, total - passed),
            threshold=threshold,
        )

    @staticmethod
    def _build_sequence_map(
        step03_out: Step03Output,
        step03b_out: Optional[Step03bOutput],
    ) -> Dict[str, str]:
        """Step03/03b 출력에서 seq_id→sequence 매핑을 구성한다."""
        sequence_map: Dict[str, str] = {}
        if step03b_out is not None and hasattr(step03b_out, "variants"):
            for variant in step03b_out.variants:
                if getattr(variant, "seq_id", None) and getattr(variant, "sequence", None):
                    sequence_map[variant.seq_id] = variant.sequence
        if hasattr(step03_out, "sequences"):
            for seq_entry in step03_out.sequences:
                if getattr(seq_entry, "seq_id", None) and getattr(seq_entry, "sequence", None):
                    sequence_map.setdefault(seq_entry.seq_id, seq_entry.sequence)
        return sequence_map

    # ------------------------------------------------------------------
    # 듀얼 사일로 헬퍼 메서드
    # ------------------------------------------------------------------

    def _run_silo_a(
        self,
        step01_out: Any,
        iteration: int,
    ) -> List[Any]:
        """Silo A: de novo 백본 설계 → 서열 설계.

        Step02 (RFdiffusion) + Step03 (ProteinMPNN) 를 실행하고
        SequenceEntry 리스트를 반환한다.

        Silo A 실패 시 빈 리스트를 반환하여 Silo B만으로 진행할 수 있게 한다.

        Args:
            step01_out: Step01Output (receptor_pdb_path, pocket_residues).
            iteration:  현재 반복 번호.

        Returns:
            List[SequenceEntry] — 생성된 서열 항목 (실패 시 []).
        """
        dual_cfg = self.config.get("dual_silo", {})
        silo_a_cfg = dual_cfg.get("silo_a", {})
        gpu_device: int = int(silo_a_cfg.get("gpu_device", 2))

        # 듀얼 모드 전용 파라미터 덮어쓰기 (선택)
        silo_config = dict(self.config)
        iter_cfg = dict(silo_config.get("iteration", {}))
        if "n_backbone" in silo_a_cfg:
            iter_cfg["n_backbone"] = int(silo_a_cfg["n_backbone"])
        if "k_seq_per_backbone" in silo_a_cfg:
            iter_cfg["k_seq_per_backbone"] = int(silo_a_cfg["k_seq_per_backbone"])
        silo_config["iteration"] = iter_cfg
        silo_config["device"] = f"cuda:{gpu_device}"

        step02_result = self._execute_step(
            "silo_a_step02_backbone",
            lambda: step02_backbone.generate_backbones(
                receptor_pdb=step01_out.receptor_pdb_path,
                pocket_info={"pocket_residues": step01_out.pocket_residues},
                config=silo_config,
            ),
        )
        if not step02_result.success or not step02_result.output.backbone_pdbs:
            self._logger.warning("[Silo A] Step02 실패 또는 백본 없음 — Silo A 후보 0개.")
            return []

        step02_out: Any = step02_result.output
        step03_result = self._execute_step(
            "silo_a_step03_sequence",
            lambda: step03_sequence.design_sequences(
                backbones=step02_out.backbone_pdbs,
                config=silo_config,
            ),
        )
        if not step03_result.success:
            self._logger.warning("[Silo A] Step03 실패 — Silo A 후보 0개.")
            return []

        seqs: List[Any] = step03_result.output.sequences
        self._logger.info("[Silo A] %d 서열 생성 완료.", len(seqs))
        return seqs

    def _run_silo_b(
        self,
        step01_out: Any,
        iteration: int,
    ) -> List[Any]:
        """Silo B: PyRosetta mutation+dock flow 실행.

        pyrosetta_flow/runner.py의 run_pyrosetta_agentic_mutdock_flow()를 호출한다.
        이 함수가 자체적으로 mutation → FlexPepDock → ddG → Planner → Critic →
        Reporter 루프를 처리하므로, orchestrator는 설정만 전달하면 된다.

        반환된 후보는 이미 ddG/clashScore/totalScore를 포함하므로
        통합 Step05(Boltz)/Step06(Rosetta) 단계를 건너뛰고 게이트만 적용한다.

        각 후보의 seq_id에 "b_" 접두어를 붙여 Silo A seq_id와 충돌을 방지한다.

        Args:
            step01_out: Step01Output (receptor_pdb_path).
            iteration:  현재 반복 번호.

        Returns:
            List[RosettaResult-compatible dict] — FlexPepDock 결과 (실패 시 []).
        """
        from pyrosetta_flow.runner import run_pyrosetta_agentic_mutdock_flow
        from pyrosetta_flow.schema import FlowConfig

        dual_cfg = self.config.get("dual_silo", {})
        silo_b_cfg = dual_cfg.get("silo_b", {})

        # Silo B는 receptor+peptide 복합체 PDB가 필요 (FlexPepDock 입력).
        # CIF→PDB 변환본은 chain ID가 깨지므로, 원본 복합체 PDB 우선 사용.
        # 절대경로로 변환 — runner.py의 cwd와 orchestrator의 cwd가 다름.
        receptor_cfg = self.config.get("receptor", {})
        receptor_pdb: str = str(Path(
            silo_b_cfg.get("template_pdb")
            or receptor_cfg.get("existing_pdb")
            or step01_out.receptor_pdb_path
        ).resolve())
        run_id: str = self.config.get("run_id", f"silo_b_iter{iteration:02d}")
        silo_b_output_dir: str = str(
            (self.output_base / run_id / "silo_b").resolve()
        )
        n_candidates: int = int(
            silo_b_cfg.get(
                "n_mutations",
                self.config.get("iteration", {}).get("n_candidates", 8),
            )
        )

        flow_config = FlowConfig(
            template_pdb=receptor_pdb,
            output_dir=silo_b_output_dir,
            max_iterations=1,  # orchestrator가 iteration을 관리하므로 내부는 1회
            n_candidates=n_candidates,
            original_sequence=self._reference_peptide_sequence,
            peptide_chain=1,  # Chain index (int): 1 = 펩타이드 체인
            conda_env=str(silo_b_cfg.get("conda_env", "bio-tools")),
            seed_base=iteration * 100,
            llm_model_override=str(
                self.config.get("llm", {}).get("model", "qwen3:8b")
            ),
            llm_provider=str(
                self.config.get("llm", {}).get("provider", "ollama")
            ),
            llm_base_url=str(
                self.config.get("llm", {}).get("base_url", "http://localhost:11434")
            ),
            rosetta_ddg_max=float(
                self.gate_thresholds.get("rosetta_ddg_max", 498.4713)
            ),
        )

        self._logger.info(
            "[Silo B] run_pyrosetta_agentic_mutdock_flow 호출: "
            "template_pdb=%s, n_candidates=%d, seed_base=%d",
            receptor_pdb, n_candidates, flow_config.seed_base,
        )

        try:
            artifacts = run_pyrosetta_agentic_mutdock_flow(flow_config)
        except Exception as exc:  # noqa: BLE001
            self._logger.warning("[Silo B] run_pyrosetta_agentic_mutdock_flow 실패: %s", exc)
            return []

        # FlowArtifacts.final_candidates 우선 사용, 없으면 iterations에서 취합
        raw_candidates: List[Any] = list(artifacts.final_candidates)
        if not raw_candidates:
            for iter_rec in artifacts.iterations:
                raw_candidates.extend(iter_rec.get("candidates", []))

        if not raw_candidates:
            self._logger.warning("[Silo B] FlowArtifacts에 후보 없음 — 0개 반환.")
            return []

        # RosettaResult 인스턴스로 변환하여 apply_rosetta_gate / step07과 타입 통일
        rosetta_results: List[RosettaResult] = []
        for cand in raw_candidates:
            # dict 또는 dataclass 양쪽 지원
            if isinstance(cand, dict):
                seq_id_raw: str = str(cand.get("candidate_id", cand.get("id", "")))
                ddg: float = float(cand.get("ddg", cand.get("ddG", 0.0)))
                clash: float = float(cand.get("clash_score", cand.get("clashScore", 0.0)))
                total: float = float(cand.get("total_score", cand.get("totalScore", 0.0)))
                constraint_viol: int = int(cand.get("constraint_violations", 0))
                refined_pdb: str = str(cand.get("pdb", cand.get("refined_pdb", "")))
            else:
                seq_id_raw = str(getattr(cand, "candidate_id", getattr(cand, "id", "")))
                ddg = float(getattr(cand, "ddg", 0.0))
                clash = float(getattr(cand, "clash_score", 0.0))
                total = float(getattr(cand, "total_score", 0.0))
                constraint_viol = int(getattr(cand, "constraint_violations", 0))
                refined_pdb = str(getattr(cand, "pdb", getattr(cand, "refined_pdb", "")))

            # "b_" 접두어 중복 방지
            seq_id = seq_id_raw if seq_id_raw.startswith("b_") else f"b_{seq_id_raw}"

            result = RosettaResult(
                seq_id=seq_id,
                ddg=ddg,
                total_score=total,
                clash_score=clash,
                constraint_violations=constraint_viol,
                refined_pdb=refined_pdb,
                source="silo_b",
            )
            rosetta_results.append(result)

        self._logger.info(
            "[Silo B] PyRosetta mutdock flow 완료: %d 후보 (ddG 포함).",
            len(rosetta_results),
        )
        return rosetta_results

    # ------------------------------------------------------------------
    # 실행 환경 설정
    # ------------------------------------------------------------------

    def _resolve_device(self) -> str:
        """CUDA_VISIBLE_DEVICES 환경변수에서 장치를 결정한다.

        CUDA_VISIBLE_DEVICES 설정 시 PyTorch는 항상 cuda:0이 첫 번째 가시 GPU.
        예: CUDA_VISIBLE_DEVICES=2,3 → cuda:0 = 물리 GPU 2
        """
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda:0"
        except ImportError:
            pass
        return "cpu"

    def _setup_run(self, iteration: int) -> Tuple[str, Dict[str, str]]:
        """실행 ID와 출력 디렉토리 구조를 생성한다."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        run_id = f"local_{timestamp}_iter{iteration:02d}"

        out_base = self.output_base / run_id
        step_dirs = {
            "00_config": "00_config",
            "01_receptor": "01_receptor",
            "02_backbone": "02_backbone",
            "03_sequence": "03_sequence",
            "03b_blosum": "03b_blosum",
            "04_qc": "04_qc",
            "05_docking": "05_docking",
            "05b_selectivity": "05b_selectivity",
            "06_rosetta": "06_rosetta",
            "07_viz": "07_viz",
            "08_reports": "08_reports",
        }
        out_dirs: Dict[str, str] = {}
        for key, sub in step_dirs.items():
            d = out_base / sub
            d.mkdir(parents=True, exist_ok=True)
            out_dirs[key] = str(d)

        # 설정 파일을 00_config에 복사
        config_src = Path(__file__).parent / "config"
        config_dst = out_base / "00_config"
        for fname in (
            "pipeline_config_local.yaml",
            "gate_thresholds.yaml",
            "gate_thresholds_local.yaml",
            "tool_registry.yaml",
        ):
            src = config_src / fname
            if src.exists():
                shutil.copy(src, config_dst / fname)

        self._logger.info("[Setup] Run %s 초기화 완료: %s", run_id, out_base)
        return run_id, out_dirs

    # ------------------------------------------------------------------
    # 스텝 실행 (에러 처리 포함)
    # ------------------------------------------------------------------

    def _execute_step(
        self,
        step_name: str,
        step_fn: Any,
        max_retries: int = 1,
    ) -> StepResult:
        """파이프라인 단계를 실행하고 StepResult로 래핑한다."""
        self._logger.info("[Step] %s 시작 ...", step_name)
        t0 = time.monotonic()

        # ── step status 추적 ──────────────────────────────────────────────
        step_id = self._get_step_id(step_name)
        if step_id:
            self._step_statuses[step_id] = "running"
            self._step_start_times[step_id] = t0
            # F13 fix: StatusEmitter로 UI 노출
            emitter = getattr(self, "_emitter", None)
            if emitter is not None:
                try:
                    emitter.update_step(step_id, "running")
                except Exception as exc:
                    self._logger.debug("[F13] emitter.update_step running 실패: %s", exc)

        last_exc: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                output = step_fn()
                elapsed = time.monotonic() - t0
                self._logger.info("[Step] %s 완료 (%.1fs).", step_name, elapsed)
                if step_id:
                    self._step_durations[step_id] = f"{elapsed:.1f}s"
                    self._step_statuses[step_id] = "completed"
                    # F13 fix: completed 신호
                    emitter = getattr(self, "_emitter", None)
                    if emitter is not None:
                        try:
                            emitter.update_step(step_id, "completed", duration=f"{elapsed:.1f}s")
                        except Exception as exc:
                            self._logger.debug("[F13] emitter.update_step completed 실패: %s", exc)
                return StepResult(
                    step_name=step_name,
                    success=True,
                    output=output,
                    elapsed_sec=round(elapsed, 2),
                )
            except Exception as exc:
                last_exc = exc
                elapsed = time.monotonic() - t0
                if attempt < max_retries:
                    wait = 2 ** attempt
                    self._logger.warning(
                        "[Step] %s 시도 %d/%d 실패 (%s). %ds 후 재시도.",
                        step_name, attempt + 1, max_retries + 1, exc, wait,
                    )
                    time.sleep(wait)
                else:
                    self._logger.error(
                        "[Step] %s %d회 시도 후 실패: %s",
                        step_name, max_retries + 1, exc, exc_info=True,
                    )

        if step_id:
            self._step_statuses[step_id] = "failed"
        return StepResult(
            step_name=step_name,
            success=False,
            error=str(last_exc),
            elapsed_sec=round(time.monotonic() - t0, 2),
        )

    # ------------------------------------------------------------------
    # 에이전트 레지스트리 초기화
    # ------------------------------------------------------------------

    def _init_agents(self) -> None:
        """에이전트 인스턴스를 초기화하고 레지스트리에 등록한다.

        로컬 모드에서는 Ollama (OLLAMA_HOST에 지정된 포트)를 LLM provider로 사용한다.
        """
        self._agents: Dict[str, BaseAgent] = {}
        self._last_critic_analysis: Optional[CriticAnalysis] = None
        self._last_rank_table: Optional[RankTable] = None
        self._last_qc_report: Optional[QCReport] = None

        # 로컬 Ollama LLM provider 생성
        self._llm_provider = create_provider(self.config)
        llm = self._llm_provider

        try:
            self._agents["planner"] = PlannerAgent(llm_provider=llm)
            self._agents["qc_ranker"] = QCRankerAgent(llm_provider=llm)
            self._agents["diversity_manager"] = DiversityManagerAgent(llm_provider=llm)
            self._agents["critic"] = ScientistCriticAgent(llm_provider=llm)
            self._agents["reporter"] = ReporterAgent(
                llm_provider=llm,
                runs_base_dir=str(self.output_base),
            )
            self._logger.info(
                "에이전트 레지스트리 초기화 완료: %s (LLM: %s)",
                list(self._agents.keys()), llm,
            )
        except Exception as e:
            self._logger.warning(
                "에이전트 초기화 실패: %s. Rule-based stub 사용.", e
            )
            self._agents = {}

    # ------------------------------------------------------------------
    # 에이전트 호출 — 실제 위임 + stub fallback
    # ------------------------------------------------------------------

    def _invoke_agent(
        self,
        agent_name: str,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """지정된 에이전트를 BaseAgent.execute()로 호출한다.

        실패 시 rule-based stub으로 fallback한다.
        """
        self._logger.debug(
            "[Agent] '%s' 호출, context keys: %s",
            agent_name, list(context.keys()),
        )

        agent = self._agents.get(agent_name)
        if agent is None:
            stub_resp = self._invoke_agent_stub(agent_name, context)
            self._capture_agent_message(agent_name, stub_resp.content)
            return stub_resp

        try:
            adapted_ctx = self._adapt_agent_context(agent_name, context)
            result = agent.execute(adapted_ctx)

            # 에이전트 출력 스키마 검증
            valid, validation_errors = validate_agent_output(agent_name, result)
            if not valid:
                self._logger.warning(
                    "[Agent] '%s' 출력 스키마 검증 실패 — stub fallback. 오류: %s",
                    agent_name, "; ".join(validation_errors),
                )
                stub_resp = self._invoke_agent_stub(agent_name, context)
                self._capture_agent_message(agent_name, stub_resp.content)
                return stub_resp

            content = self._map_agent_result(agent_name, result, context)
            self._capture_agent_message(agent_name, content)
            self._logger.info("[Agent] '%s' 실행 완료.", agent_name)
            return AgentResponse(agent_name=agent_name, content=content)
        except Exception as e:
            self._logger.warning(
                "[Agent] '%s' 실행 실패: %s. stub fallback.", agent_name, e
            )
            stub_resp = self._invoke_agent_stub(agent_name, context)
            self._capture_agent_message(agent_name, stub_resp.content)
            return stub_resp

    # ------------------------------------------------------------------
    # 컨텍스트 어댑터 — 오케스트레이터 dict → 에이전트별 포맷
    # ------------------------------------------------------------------

    def _adapt_agent_context(
        self, agent_name: str, context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """오케스트레이터 컨텍스트를 각 에이전트 입력 포맷으로 변환한다."""
        if agent_name == "planner":
            cfg = context.get("config", {})
            prev = context.get("previous_results", {})
            critic_fb = None
            if self._last_critic_analysis is not None:
                critic_fb = {
                    "proposed_changes": [
                        {
                            "parameter_name": pc.parameter_name,
                            "new_value": pc.new_value,
                            "rationale": pc.rationale,
                        }
                        for pc in self._last_critic_analysis.proposed_changes
                    ],
                    "hypothesis": self._last_critic_analysis.hypothesis,
                }
            return {
                "iteration": context.get("iteration", 1),
                "receptor_config": cfg.get("receptor", {}),
                "constraints": cfg.get("constraints", {}),
                "critic_feedback": critic_fb,
                "previous_results": prev,
            }

        if agent_name == "qc_ranker":
            candidates = self._candidates_from_dicts(context.get("qc_results", []))
            return {
                "candidates": candidates,
                "thresholds": self.gate_thresholds,
                "run_id": self.config.get("run_id", "default"),
                "iteration": context.get("iteration", 1),
            }

        if agent_name == "diversity_manager":
            candidates = self._candidates_from_dicts(context.get("docking_results", []))
            n_select = int(
                self.config.get("iteration", {}).get("diversity_top_n", 20)
            )
            return {"candidates": candidates, "n_select": n_select}

        if agent_name == "critic":
            rank_table = self._last_rank_table or self._build_empty_rank_table(context)
            qc_report = self._last_qc_report or self._build_empty_qc_report(context)
            return {
                "rank_table": rank_table,
                "qc_report": qc_report,
                "iteration": context.get("iteration", 1),
                "current_params": self.config.get("iteration", {}),
            }

        if agent_name == "reporter":
            return {
                "run_id": context.get("run_id", "default"),
                "iteration": context.get("iteration", 1),
                "rank_table": self._last_rank_table or self._build_empty_rank_table(context),
                "top_candidates": [],
                "receptor_pdb": self.config.get("receptor", {}).get("pdb_path", ""),
                "output_dir": str(self.output_base / context.get("run_id", "default")),
                "critic_analysis": self._last_critic_analysis,
            }

        return context

    # ------------------------------------------------------------------
    # 응답 매퍼 — 에이전트 결과 → 오케스트레이터 content dict
    # ------------------------------------------------------------------

    def _map_agent_result(
        self,
        agent_name: str,
        result: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """agent.execute() 결과를 오케스트레이터가 기대하는 content dict로 매핑한다."""
        if agent_name == "planner":
            plan: Optional[ExperimentPlan] = result.get("plan")
            if plan is None:
                raise ValueError("Planner가 plan을 반환하지 않았습니다.")
            param_updates: Dict[str, Any] = {}
            if plan.changes_from_prev:
                param_updates = {
                    f"iteration.{k}": v for k, v in plan.parameters.items()
                }
            return {"hypothesis": plan.hypothesis, "parameter_updates": param_updates}

        if agent_name == "qc_ranker":
            rank_table = result.get("rank_table")
            qc_report = result.get("qc_report")
            if rank_table is not None:
                self._last_rank_table = rank_table
            if qc_report is not None:
                self._last_qc_report = qc_report
            passed = qc_report.passed_count if qc_report else context.get("passed", 0)
            failed = qc_report.failed_count if qc_report else context.get("failed", 0)
            return {"ranking_comment": f"QC gate: {passed} passed, {failed} failed."}

        if agent_name == "diversity_manager":
            diverse = result.get("diverse_candidates", [])
            if diverse:
                # candidate_id (문자열)를 사용 — seq_id는 int로 변환되어 키 불일치
                return {"selected_seq_ids": [c.candidate_id for c in diverse]}
            fallback = context.get("docking_results", [])
            return {"selected_seq_ids": [r.get("candidate_id", r.get("seq_id", "")) for r in fallback]}

        if agent_name == "critic":
            analysis: Optional[CriticAnalysis] = result.get("critic_analysis")
            if analysis is None:
                raise ValueError("Critic이 analysis를 반환하지 않았습니다.")
            self._last_critic_analysis = analysis
            next_actions = [
                f"{pc.parameter_name}: {pc.old_value} -> {pc.new_value} ({pc.rationale})"
                for pc in analysis.proposed_changes
            ]
            if not next_actions:
                next_actions = [analysis.hypothesis]
            return {"next_actions": next_actions[:2]}

        if agent_name == "reporter":
            report_paths = result.get("report_paths", {})
            first_path = next(iter(report_paths.values()), "") if report_paths else ""
            return {"report_path": first_path}

        return result

    # ------------------------------------------------------------------
    # 헬퍼 — dict 리스트 → typed 객체
    # ------------------------------------------------------------------

    @staticmethod
    def _candidates_from_dicts(records: List[Dict[str, Any]]) -> List[Candidate]:
        """dict 리스트에서 최소한의 Candidate 객체를 생성한다."""
        candidates: List[Candidate] = []
        for r in records:
            candidates.append(Candidate(
                candidate_id=str(r.get("candidate_id", r.get("seq_id", "unknown"))),
                backbone_id=int(r.get("backbone_id", 0)),
                seq_id=int(r.get("seq_id", 0))
                    if str(r.get("seq_id", "0")).isdigit()
                    else hash(str(r.get("seq_id", ""))) % 10000,
                sequence=str(r.get("sequence", "")),
                pdb_path=str(r.get("pdb_path", "")),
                plddt_mean=float(r.get("plddt_mean", 0.0)),
                plddt_interface=float(r.get("plddt_interface", 0.0)),
                dock_score=float(r.get("dock_score", r.get("score", 0.0))),
                ddg=float(r.get("ddg", 0.0)),
                lddt=float(r.get("lddt", 0.0)),
            ))
        return candidates

    def _build_empty_rank_table(self, context: Dict[str, Any]) -> RankTable:
        return RankTable(
            run_id=self.config.get("run_id", context.get("run_id", "default")),
            iteration=context.get("iteration", 1),
            ranked_candidates=[],
            weights=dict(self.gate_thresholds.get("final_score_weights", {})),
        )

    def _build_empty_qc_report(self, context: Dict[str, Any]) -> QCReport:
        n_passed = context.get("n_passed_final", 0)
        step_results = context.get("step_results", {})
        total = n_passed
        for sr in step_results.values():
            if sr.get("output") and isinstance(sr["output"], dict):
                total = max(total, sr["output"].get("total_count", total))
        return QCReport(
            run_id=self.config.get("run_id", "default"),
            total_input=total,
            passed_count=n_passed,
            failed_count=max(0, total - n_passed),
            failure_breakdown={},
            gates_applied=dict(self.gate_thresholds),
            pass_rate=n_passed / total if total > 0 else 0.0,
        )

    # ------------------------------------------------------------------
    # Rule-based stub (에이전트 실패 시 fallback)
    # ------------------------------------------------------------------

    def _invoke_agent_stub(
        self,
        agent_name: str,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """에이전트 호출 실패 시 사용하는 rule-based stub."""
        content: Dict[str, Any] = {}

        if agent_name == "planner":
            iteration = context.get("iteration", 1)
            prev = context.get("previous_results", {})
            prev_actions = prev.get("next_actions", []) if prev else []
            hypothesis = (
                f"Iteration {iteration}: "
                + (prev_actions[0] if prev_actions
                   else "Initial de-novo binder design for SSTR2.")
            )
            content = {"hypothesis": hypothesis, "parameter_updates": {}}

        elif agent_name == "qc_ranker":
            content = {
                "ranking_comment": (
                    f"QC gate: {context.get('passed', 0)} passed, "
                    f"{context.get('failed', 0)} failed."
                )
            }

        elif agent_name == "diversity_manager":
            results = context.get("docking_results", [])
            content = {"selected_seq_ids": [r["seq_id"] for r in results]}

        elif agent_name == "critic":
            top_ddg = context.get("top_ddg", 0.0)
            next_actions: List[str] = []
            if top_ddg >= 0:
                next_actions.append(
                    "Increase diffusion steps to 100 and hotspot weight to improve binding."
                )
            elif top_ddg > -5.0:
                next_actions.append(
                    "Tighten contigs to focus on TM2-TM5 pocket; reduce binder length to 15-20."
                )
            else:
                next_actions.append(
                    "Results look promising. Consider expanding to 15 backbones."
                )
            content = {"next_actions": next_actions[:2]}

        elif agent_name == "reporter":
            run_id = context.get("run_id", "unknown")
            iteration = context.get("iteration", 1)
            report_dir = self.output_base / run_id / "08_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"lab_notebook_iter{iteration:02d}.md"
            iter_result_dict = context.get("iter_result", {})
            top_ddg = iter_result_dict.get("top_ddg", 0.0)
            n_passed = iter_result_dict.get("n_passed_final", 0)
            report_lines = [
                f"# Lab Notebook – Iteration {iteration:02d} [LOCAL MODE]",
                f"**Run ID:** {run_id}",
                f"**Device:** {self.device}",
                f"**Hypothesis:** {iter_result_dict.get('hypothesis', '')}",
                "",
                f"**Best ddG:** {top_ddg:.2f} kcal/mol",
                f"**Candidates passing all gates:** {n_passed}",
                "",
                "## Next Actions",
            ]
            for action in iter_result_dict.get("next_actions", []):
                report_lines.append(f"- {action}")
            report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
            content = {"report_path": str(report_path)}

        else:
            self._logger.warning("[Agent] 알 수 없는 에이전트 '%s'; 빈 응답 반환.", agent_name)

        return AgentResponse(agent_name=agent_name, content=content)

    # ------------------------------------------------------------------
    # 상태 파일 기록 — frontend /api/status 폴링용
    # ------------------------------------------------------------------

    def _write_status(
        self,
        phase: str,
        message: str,
        **extra: Any,
    ) -> None:
        """파이프라인 현재 상태를 /tmp/pipeline_local_status.json 에 기록한다.

        frontend는 GET /api/status 를 2초 간격으로 폴링하여 이 파일을 읽는다.

        Args:
            phase:   현재 단계 식별자 (예: "step02_backbone", "completed", "error").
            message: 사람이 읽을 수 있는 진행 메시지.
            **extra: 추가 필드 (iteration, candidates_generated 등).
        """
        elapsed = round(time.monotonic() - self._pipeline_start_time, 1)
        iteration: int = int(extra.pop("iteration", 0))
        max_iterations: int = int(extra.pop("max_iterations", self._max_iterations))

        # 진행률 계산: 반복 기반 + 단계 보정
        _STEP_PROGRESS: Dict[str, float] = {
            "start":            0.0,
            "step01_receptor":  5.0,
            "step02_backbone":  15.0,
            "step03_sequence":  30.0,
            "step03b_blosum":   30.0,
            # 듀얼 사일로 단계 진행률
            "silo_a":           15.0,   # Silo A (RFdiffusion+MPNN)
            "silo_b":           30.0,   # Silo B (BLOSUM62+FlexPepDock)
            "step04_qc":        50.0,
            "step05_docking":   65.0,
            "step05b_select":   70.0,
            "step06_rosetta":   80.0,
            "step07_analysis":  90.0,
            "agents":           95.0,
            "completed":        100.0,
            "error":            100.0,
        }
        step_pct = _STEP_PROGRESS.get(phase, 50.0)
        if max_iterations > 0 and iteration > 0:
            iter_base = (iteration - 1) / max_iterations * 100.0
            iter_span = 1.0 / max_iterations * 100.0
            progress_pct = round(iter_base + (step_pct / 100.0) * iter_span, 1)
        else:
            progress_pct = round(step_pct, 1)

        # ── 기존 단순 필드 ─────────────────────────────────────────────────
        payload: Dict[str, Any] = {
            "phase":               phase,
            "iteration":           iteration,
            "max_iterations":      max_iterations,
            "progress_pct":        progress_pct,
            "current_step":        message,
            "candidates_generated": int(extra.pop("candidates_generated", 0)),
            "candidates_passed":    int(extra.pop("candidates_passed", 0)),
            "elapsed_sec":          elapsed,
            "connected":            True,
            **extra,
        }

        # ── Frontend 확장 필드 ──────────────────────────────────────────────
        # run_id / iteration 헤더
        payload["run_id"] = self._current_run_id or self.config.get("run_id", "")
        payload["total_iterations"] = max_iterations

        # steps[]
        steps_list = []
        for step_def in PIPELINE_STEPS:
            sid = step_def["id"]
            entry: Dict[str, Any] = {
                "id": sid,
                "label": step_def["label"],
                "shortLabel": step_def["shortLabel"],
                "status": self._step_statuses.get(sid, "pending"),
            }
            if sid in self._step_durations:
                entry["duration"] = self._step_durations[sid]
            steps_list.append(entry)
        payload["steps"] = steps_list

        # agents[]
        payload["agents"] = [
            {
                "id": "planner",
                "name": "Planner",
                "type": "LLM",
                "status": "idle",
                "lastMessage": self._agent_messages.get("planner", {}).get("lastMessage", ""),
                "isRuntimeActive": False,
            },
            {
                "id": "critic",
                "name": "Critic",
                "type": "LLM",
                "status": "idle",
                "lastMessage": self._agent_messages.get("critic", {}).get("lastMessage", ""),
                "isRuntimeActive": False,
            },
            {
                "id": "reporter",
                "name": "Reporter",
                "type": "LLM",
                "status": "idle",
                "lastMessage": self._agent_messages.get("reporter", {}).get("lastMessage", "보고서 작성 완료"),
                "isRuntimeActive": False,
            },
        ]

        # candidates[]
        payload["candidates"] = list(self._passed_candidates)

        # timeline[]
        payload["timeline"] = list(self._timeline)

        # qc_gates[]
        _GATE_LABEL = {
            "plddt": "pLDDT Gate",
            "docking": "Docking Gate",
            "rosetta": "Rosetta Gate",
        }
        payload["qc_gates"] = [
            {
                "name": _GATE_LABEL.get(k, k),
                "passed": v.get("passed", 0),
                "failed": v.get("failed", 0),
                "threshold": v.get("threshold", ""),
            }
            for k, v in self._qc_gate_stats.items()
        ]

        try:
            _STATUS_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except OSError as exc:
            self._logger.warning("[Status] 상태 파일 쓰기 실패: %s", exc)

    # ------------------------------------------------------------------
    # 수렴 감지
    # ------------------------------------------------------------------

    def _check_convergence(self, results_history: List[IterationResult]) -> bool:
        """수렴 기준을 평가한다.

        최근 두 반복에서 최상위 ddG 개선폭이 convergence_ddg_delta 미만이면 수렴으로 판단.
        """
        patience: int = int(self.config.get("convergence_patience", 2))
        delta: float = float(self.config.get("convergence_ddg_delta", 0.5))

        if len(results_history) < patience + 1:
            return False

        recent = results_history[-(patience + 1):]
        ddg_values = [r.top_ddg for r in recent if r.top_ddg < 0]
        if len(ddg_values) < patience:
            return False

        improvements = [
            abs(ddg_values[i] - ddg_values[i + 1]) for i in range(len(ddg_values) - 1)
        ]
        converged = all(imp < delta for imp in improvements)
        if converged:
            self._logger.info(
                "수렴 감지: improvements=%s, 모두 < %.3f -> CONVERGED",
                [round(x, 3) for x in improvements], delta,
            )
        return converged

    # ------------------------------------------------------------------
    # 상태 저장/로드 (체크포인트)
    # ------------------------------------------------------------------

    def _save_state(
        self,
        run_id: str,
        iteration: int,
        state: Dict[str, Any],
    ) -> str:
        """파이프라인 상태를 JSON 체크포인트 파일로 저장한다."""
        state_dir = self.output_base / run_id / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / f"checkpoint_iter{iteration:02d}.json"
        full_state = {
            "run_id": run_id,
            "iteration": iteration,
            "saved_at": datetime.utcnow().isoformat(),
            "mode": "local",
            "device": self.device,
            **state,
        }
        state_path.write_text(
            json.dumps(full_state, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        self._logger.info("[State] 체크포인트 저장 -> %s", state_path)
        return str(state_path)

    def _load_state(self, run_id: str) -> Dict[str, Any]:
        """가장 최근 체크포인트에서 상태를 로드한다."""
        state_dir = self.output_base / run_id / "state"
        checkpoints = sorted(state_dir.glob("checkpoint_iter*.json"))
        if not checkpoints:
            raise FileNotFoundError(
                f"run_id='{run_id}' 체크포인트 없음: {state_dir}"
            )
        latest = checkpoints[-1]
        self._logger.info("[State] 체크포인트 로드: %s", latest)
        return json.loads(latest.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Planner 파라미터 업데이트 (화이트리스트 적용)
    # ------------------------------------------------------------------

    _ALLOWED_PARAM_KEYS: frozenset = frozenset({
        "iteration.n_backbone", "iteration.k_seq", "iteration.contigs",
        "iteration.hotspot_res", "iteration.peptide_length_min",
        "iteration.peptide_length_max", "iteration.mpnn_temperature",
        "iteration.mpnn_sampling_n", "iteration.docking_engine",
        "iteration.rosetta_relax_cycles", "iteration.seed",
        "iteration.diversity_top_n",
    })

    def _apply_parameter_updates(self, updates: Dict[str, Any]) -> None:
        """Planner 에이전트가 제안한 파라미터를 화이트리스트 검증 후 config에 적용한다."""
        for key, value in updates.items():
            if key not in self._ALLOWED_PARAM_KEYS:
                self._logger.warning(
                    "[Config] 허용되지 않은 파라미터 업데이트 차단: %s = %s", key, value
                )
                continue
            if "." in key:
                section, sub_key = key.split(".", 1)
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][sub_key] = value
                self._logger.info("[Config] 업데이트: %s.%s = %s", section, sub_key, value)
            else:
                self.config[key] = value
                self._logger.info("[Config] 업데이트: %s = %s", key, value)

    # ------------------------------------------------------------------
    # 최종 결과 집계
    # ------------------------------------------------------------------

    def _aggregate_best_candidates(
        self, iteration_records: List[IterationResult]
    ) -> List[Dict[str, Any]]:
        """모든 반복에서 최상위 후보를 ddG 기준으로 정렬하여 반환한다."""
        best: List[Dict[str, Any]] = []
        for record in iteration_records:
            step06 = record.step_results.get("step06")
            if not step06 or not step06.success or not step06.output:
                continue
            step06_out = step06.output
            if not hasattr(step06_out, "rosetta_results"):
                continue
            for r in step06_out.rosetta_results:
                best.append({
                    "iteration": record.iteration,
                    "seq_id": r.seq_id,
                    "ddg": r.ddg,
                    "total_score": r.total_score,
                    "clash_score": r.clash_score,
                    "refined_pdb": r.refined_pdb,
                })
        return sorted(best, key=lambda x: x.get("ddg", 0.0))[:10]

    def _write_final_report(
        self,
        iteration_records: List[IterationResult],
        best_candidates: List[Dict[str, Any]],
        run_id: str,
    ) -> str:
        """전체 실험 최종 보고서를 마크다운으로 생성한다."""
        report_dir = self.output_base / run_id / "08_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "final_report.md"

        lines = [
            "# SSTR2 Peptide Binder Design – Final Report [LOCAL MODE]",
            f"**Run ID:** {run_id}",
            f"**Device:** {self.device}",
            f"**Total Iterations:** {len(iteration_records)}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Summary",
            f"Completed {len(iteration_records)} iteration(s).",
            (
                f"Best ddG: {best_candidates[0]['ddg']:.2f} kcal/mol"
                f" ({best_candidates[0]['seq_id']})"
            ) if best_candidates else "No passing candidates found.",
            "",
            "## Top Candidates",
            "",
            "| Rank | seq_id | ddG (kcal/mol) | Iteration | refined_pdb |",
            "|------|--------|---------------|-----------|-------------|",
        ]
        for rank, c in enumerate(best_candidates, 1):
            pdb_name = Path(c["refined_pdb"]).name if c.get("refined_pdb") else "N/A"
            lines.append(
                f"| {rank} | {c['seq_id']} | {c['ddg']:.2f}"
                f" | {c['iteration']} | `{pdb_name}` |"
            )

        lines += ["", "## Iteration History", ""]
        for record in iteration_records:
            lines.append(
                f"- **Iteration {record.iteration}**: "
                f"hypothesis='{record.hypothesis}', "
                f"best ddG={record.top_ddg:.2f}, "
                f"n_passed={record.n_passed_final}"
            )

        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self._logger.info("[Reporter] 최종 보고서 작성 -> %s", report_path)
        return str(report_path)

    # ------------------------------------------------------------------
    # Frontend 상태 추적 헬퍼
    # ------------------------------------------------------------------

    def _get_step_id(self, step_name: str) -> Optional[str]:
        """step_name (예: 'step04_qc') → PIPELINE_STEPS id (예: 'step04')."""
        for step in PIPELINE_STEPS:
            if step_name.startswith(step["id"]):
                return step["id"]
        return None

    def _add_timeline(self, stage: str, status: str, message: str) -> None:
        """타임라인 이벤트를 추가한다."""
        self._timeline.append({
            "iteration": self._current_iteration,
            "stage": stage,
            "status": status,
            "message": message,
            "ts": datetime.utcnow().isoformat(),
        })

    def _capture_agent_message(
        self, agent_name: str, content: Dict[str, Any]
    ) -> None:
        """에이전트 호출 결과를 _agent_messages에 캐싱하고 타임라인에 기록한다."""
        if agent_name == "planner":
            hypothesis = content.get("hypothesis", "")
            self._agent_messages["planner"] = {
                "lastMessage": hypothesis,
                "isRuntimeActive": False,
            }
            self._add_timeline(
                "planner", "completed",
                f"가설: {hypothesis[:100]}" if hypothesis else "Planner 완료",
            )
        elif agent_name == "critic":
            next_actions = content.get("next_actions", [])
            msg = next_actions[0] if next_actions else "Critic 완료"
            self._agent_messages["critic"] = {
                "lastMessage": msg,
                "isRuntimeActive": False,
            }
            self._add_timeline("critic", "completed", msg[:100])
        elif agent_name == "reporter":
            self._agent_messages["reporter"] = {
                "lastMessage": "보고서 작성 완료",
                "isRuntimeActive": False,
            }
            self._add_timeline("reporter", "completed", "보고서 작성 완료")

    # ------------------------------------------------------------------
    # 로깅 설정
    # ------------------------------------------------------------------

    @staticmethod
    def _configure_logging() -> None:
        """루트 로거에 콘솔 핸들러를 설정한다 (중복 방지)."""
        root = logging.getLogger()
        if not root.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s][%(name)s] %(levelname)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            root.addHandler(handler)
            root.setLevel(logging.INFO)

    # ------------------------------------------------------------------
    # YAML 헬퍼
    # ------------------------------------------------------------------

    @staticmethod
    def _load_yaml(
        path: Path, default: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """YAML 파일을 로드하고 dict를 반환한다. 파일 없으면 default 반환."""
        if not path.exists():
            logger.warning("설정 파일 없음: %s. 기본값 사용.", path)
            return default or {}
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else (default or {})
