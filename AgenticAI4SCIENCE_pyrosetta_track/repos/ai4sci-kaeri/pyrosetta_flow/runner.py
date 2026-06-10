from __future__ import annotations

import json
import os
import random
import shutil
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

from AG_src.agents.critic import ScientistCriticAgent
from AG_src.agents.planner import PlannerAgent
from AG_src.agents.qc_ranker import Candidate, PYROSETTA_ONLY_WEIGHTS, QCRankerAgent
from AG_src.agents.reporter import ReporterAgent
from AG_src.llm import create_provider
from backend.status_emitter import StatusEmitter

from .adapter import (
    candidate_to_dict,
    choose_objective_mode,
    get_bandit_guidance,
    generate_guided_mutant,
    generate_random_mutant,
    notebook_mapping,
    validate_config,
)
from AG_src.pipeline.step07_analysis import generate_pymol_renders
from .ranking import (
    append_experiment_records,
    build_historical_candidates,
    extract_historical_sequences,
    load_experiment_records,
    summarize_top_hits,
)
from .convergence import ConvergenceDetector
from .schema import CandidateResult, FlowArtifacts, FlowConfig, IterationSummary

try:
    from .rcsb_sequence_search import search_similar_peptides, SequenceSearchResult
    _HAS_RCSB = True
except ImportError:  # pragma: no cover
    _HAS_RCSB = False

# 2026-06-09 P1: GNINA/Pareto 옵셔널 의존은 scoring_pipeline.py 로 이동 (거기서만 사용).

# 다목적 통합 (반감기 + ADMET + 선택성) cheap-objective 스칼라
_HAS_MO = False
try:
    from .multiobjective import multiobjective_scalar as _multiobjective_scalar
    _HAS_MO = True
except ImportError:  # pragma: no cover
    _multiobjective_scalar = None  # type: ignore[assignment]


def _mo_scalar(extra_scores: Dict[str, Any], ddg: float):
    """extra_scores + ddg 로 다목적 스칼라 점수 계산 (UI 표시용)."""
    if not _HAS_MO:
        return None
    cand = dict(extra_scores or {})
    cand["ddg"] = ddg
    try:
        return _multiobjective_scalar(cand)
    except Exception:
        return None

BayesianPeptideOptimizer = None  # type: ignore[assignment]
OneHotEmbedder = None  # type: ignore[assignment]
_HAS_BO = False
try:
    from .bayesian_optimizer import BayesianPeptideOptimizer, OneHotEmbedder  # type: ignore[assignment]
    _HAS_BO = True
except ImportError:  # pragma: no cover
    pass


_HAS_PHARMA = False
_PharmaProperties = None  # type: ignore[assignment]
try:
    from AG_src.pipeline.pharma_properties import PharmaProperties as _PharmaProperties  # type: ignore[assignment]
    _HAS_PHARMA = True
except ImportError:  # pragma: no cover
    pass

_HAS_CLUSTER = False
_batch_classify = None  # type: ignore[assignment]
try:
    from .cluster_report import batch_classify as _batch_classify  # type: ignore[assignment]
    _HAS_CLUSTER = True
except ImportError:  # pragma: no cover
    pass


PHARMACOPHORE_POSITIONS_1IDX = (7, 8, 9, 10)
PHARMACOPHORE_RETRY_LIMIT = 3


def _pharmacophore_slice(sequence: str) -> str:
    return sequence[PHARMACOPHORE_POSITIONS_1IDX[0] - 1 : PHARMACOPHORE_POSITIONS_1IDX[-1]]


def _preserves_pharmacophore(sequence: str, reference_sequence: str) -> bool:
    return _pharmacophore_slice(sequence) == _pharmacophore_slice(reference_sequence)


def _disulfide_cys_positions(sequence: str) -> tuple:
    """참조 서열의 Cys 위치(1-indexed) — SST-14 의 Cys3-Cys14 이황화결합 보존용."""
    return tuple(i + 1 for i, a in enumerate(sequence.upper()) if a == "C")


def _preserves_disulfide(sequence: str, reference_sequence: str) -> bool:
    """2026-06-10: 참조의 모든 Cys 위치가 sequence 에서도 Cys 여야 한다 (이황화결합 보존).
    이전엔 가드 부재로 C14→H 변이가 통과해 SS bond 가 깨졌다."""
    cys = _disulfide_cys_positions(reference_sequence)
    return all(pos <= len(sequence) and sequence[pos - 1] == "C" for pos in cys)


def _preserves_scaffold(sequence: str, reference_sequence: str) -> bool:
    """FWKT pharmacophore + Cys 이황화 둘 다 보존."""
    return (_preserves_pharmacophore(sequence, reference_sequence)
            and _preserves_disulfide(sequence, reference_sequence))


def _mutable_design_positions(config: "FlowConfig") -> List[int]:
    # 2026-06-10: FWKT(7-10) 뿐 아니라 Cys 위치(이황화결합)도 변이 대상에서 제외.
    cys = set(_disulfide_cys_positions(config.original_sequence))
    mutable_positions = [
        pos for pos in config.design_positions
        if pos not in PHARMACOPHORE_POSITIONS_1IDX and pos not in cys
    ]
    return mutable_positions or list(config.design_positions)


def _rcsb_check_candidates(
    sequences: Dict[str, str],
    identity_cutoff: float = 0.4,
    max_results: int = 5,
) -> Dict[str, list]:
    """RCSB PDB에서 후보 서열의 유사 구조를 검색합니다 (best-effort).

    네트워크 미연결 또는 rcsb_sequence_search 미설치 시 빈 결과 반환.

    Args:
        sequences: {candidate_id: amino_acid_sequence} 매핑
        identity_cutoff: 최소 서열 동일성 (0.0~1.0)
        max_results: 후보당 최대 히트 수

    Returns:
        {candidate_id: [{"pdb_id", "identity", "evalue"}, ...]}
    """
    if not _HAS_RCSB or not sequences:
        return {}

    results: Dict[str, list] = {}
    for cand_id, seq in sequences.items():
        if not seq or len(seq) < 5:
            continue
        try:
            search_result = search_similar_peptides(
                sequence=seq,
                identity_cutoff=identity_cutoff,
                max_results=max_results,
            )
            hits = []
            for hit in search_result.hits:
                hits.append({
                    "pdb_id": hit.pdb_id,
                    "identifier": hit.identifier,
                    "identity": hit.sequence_identity,
                    "evalue": hit.evalue,
                    "bitscore": hit.bitscore,
                })
            if hits:
                results[cand_id] = hits
        except Exception as exc:
            print(f"  [rcsb] {cand_id} search failed: {exc}", file=sys.stderr)
    return results


# 2026-06-09 P1 분해: 대안 스코어링 체인(GNINA/ECR/Pareto/BO + cheap objectives)을
# scoring_pipeline.py 로 추출. 하위호환: 기존 import 경로 보존을 위해 re-export.
from .scoring_pipeline import _apply_alternative_scoring  # noqa: E402,F401


# 2026-06-09 P1 분해: 도킹 subprocess 실행 레이어를 docking_executor.py 로 추출.
# 하위호환: 기존 `from pyrosetta_flow.runner import _run_script` 등을 위해 re-export.
from .docking_executor import _resolve_conda_python, _run_script  # noqa: E402,F401


def _read_pipeline_config(repo_root: Path) -> Dict[str, Any]:
    cfg_path = repo_root / "AG_src" / "config" / "pipeline_config.yaml"
    if not cfg_path.exists() or yaml is None:
        return {}
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}


def _resolve_llm_model(cli_model: str | None) -> str | None:
    """Resolve model name from CLI arg > LLM_MODEL env var > None (use config file).

    Priority: --llm-model CLI argument > LLM_MODEL env var > config file default.
    """
    if cli_model:
        return cli_model
    env_model = os.environ.get("LLM_MODEL")
    if env_model:
        return env_model
    return None


def _candidate_to_qc(candidate: CandidateResult, seq_id: int, objective_mode: str) -> Candidate:
    return Candidate(
        candidate_id=candidate.candidate_id,
        backbone_id=0,
        seq_id=seq_id,
        sequence=candidate.sequence,
        plddt_mean=0.0,     # Not available in PyRosetta-only mode
        plddt_interface=0.0, # Not available in PyRosetta-only mode
        dock_score=0.0,      # Not available in PyRosetta-only mode
        ddg=candidate.ddg,
        clash_count=int(candidate.clash_score),
        constraint_violations=0,
        lddt=0.0,            # Not available in PyRosetta-only mode
    )


def _summarize_iteration(
    iteration: int,
    run_id: str,
    hypothesis: str,
    objective_mode: str,
    selected: List[CandidateResult],
    report_paths: Dict[str, str],
    critic_hypothesis: str,
) -> IterationSummary:
    if selected:
        ddgs = [c.ddg for c in selected]
        best_ddg = min(ddgs)
        mean_ddg = statistics.mean(ddgs)
    else:
        best_ddg = 0.0
        mean_ddg = 0.0
    return IterationSummary(
        iteration=iteration,
        run_id=run_id,
        hypothesis=hypothesis,
        objective_mode=objective_mode,
        n_candidates=len(selected),
        best_ddg=round(best_ddg, 4),
        mean_ddg=round(mean_ddg, 4),
        selected_ids=[c.candidate_id for c in selected],
        critic_hypothesis=critic_hypothesis,
        report_paths=report_paths,
    )


def _emit_candidates(
    emitter: StatusEmitter,
    candidates: List[CandidateResult],
    ddg_threshold: float = -5.0,
    flow_dir: Path | None = None,
) -> None:
    emitter.set_candidates(
        [
            {
                "rank": idx + 1,
                "id": c.candidate_id,
                "sequence": c.sequence,
                "ddG": round(c.ddg, 3),
                "totalScore": round(c.total_score, 3),
                "clashScore": round(c.clash_score, 1),
                "finalScore": round(-c.ddg, 3),
                "result": (
                    "PASS" if c.selected else
                    "PASS" if (c.ddg <= ddg_threshold and c.ddg < 900) else
                    "FAIL"
                ),
                "failReason": c.fail_reason if c.fail_reason else "",
                **({"pdb_path": str(flow_dir / f"iter_{c.iteration:02d}" / f"cand_{int(c.candidate_id.split('cand')[1]):03d}.pdb")}
                   if flow_dir and "cand" in c.candidate_id else {}),
            }
            for idx, c in enumerate(sorted(candidates, key=lambda x: x.ddg))
        ]
    )


def run_pyrosetta_agentic_mutdock_flow(config: FlowConfig) -> FlowArtifacts:
    validate_config(config)
    repo_root = Path(__file__).resolve().parent.parent
    flow_dir = repo_root / config.output_dir / "sst14_agentic_mutdock"
    flow_dir.mkdir(parents=True, exist_ok=True)
    flexpep_script = repo_root / "AG_src" / "scripts" / "flexpep_dock.py"
    run_id = f"sst14_mutdock_{config.seed_base}"
    exp_log_path = repo_root / config.output_dir / "experiment_log.jsonl"
    run_status = "success"
    run_failure_stage = ""
    run_error_summary = ""
    run_records: List[Dict[str, Any]] = []

    model_override = _resolve_llm_model(config.llm_model_override)
    # FlowConfig에 llm_provider/llm_base_url가 지정되면 pipeline_config 대신 사용
    if getattr(config, 'llm_provider', None) and getattr(config, 'llm_base_url', None):
        _llm_cfg = {
            "llm": {
                "provider": config.llm_provider,
                "model": model_override or config.llm_model_override or "qwen3:8b",
                "base_url": config.llm_base_url,
            }
        }
        llm = create_provider(_llm_cfg, model_override=model_override)
    else:
        llm = create_provider(_read_pipeline_config(repo_root), model_override=model_override)
    emitter = StatusEmitter(run_id=run_id, total_iterations=config.max_iterations, llm_model=str(llm))
    # PyRosetta-only flow는 step01~05/05b를 건너뜀 — "pending" 채로 방치하면 UI 혼란
    for _skip_id in ["step01", "step02", "step03", "step03b", "step04", "step05", "step05b"]:
        emitter.update_step(_skip_id, "skipped")
    planner = PlannerAgent(llm_provider=llm, planner_mode=config.planner_mode)
    critic = ScientistCriticAgent(llm_provider=llm)
    reporter = ReporterAgent(runs_base_dir=str(repo_root / config.output_dir), llm_provider=llm)
    qcranker = QCRankerAgent(weights=PYROSETTA_ONLY_WEIGHTS, llm_provider="none")
    prior_records = load_experiment_records(exp_log_path)
    emitter.set_historical_candidates(build_historical_candidates(prior_records))
    # Cross-run dedup: seed seen_sequences with all historically tried sequences
    historical_sequences = extract_historical_sequences(prior_records)
    historical_top_hits = summarize_top_hits(prior_records, top_n=10)
    n_prior = len(historical_sequences)
    if n_prior:
        print(f"  [history] Loaded {n_prior} unique sequences from prior runs (dedup enabled)", file=sys.stderr)
        print(f"  [history] Top prior hit: {historical_top_hits[0]['sequence']} ddG={historical_top_hits[0]['ddg']}" if historical_top_hits else "  [history] No successful prior candidates", file=sys.stderr)

    t_baseline = emitter.start_step("step06_baseline")
    t_prepare0 = emitter.start_rosetta_substep("step06_prepare")
    n_baseline_trials = config.n_baseline_trials
    emitter.append_timeline_event(0, "rosetta.prepare", "running", f"Preparing baseline ({n_baseline_trials} trials, best-of)")
    baseline_out = flow_dir / "baseline_refined.pdb"
    baseline: Dict[str, Any] = {}
    # 무한 엔진: native SST-14 baseline 을 epoch 간 캐시 (첫 도킹만 측정, 이후 재사용).
    # 변이는 template_pdb 에서 시작 → baseline 은 비교 기준값일 뿐이라 재도킹 불필요.
    _baseline_cache = repo_root / config.output_dir / "baseline_cache.json"
    _baseline_cache_pdb = repo_root / config.output_dir / "baseline_cached.pdb"
    _cached = None
    if getattr(config, "reuse_baseline", False) and _baseline_cache.exists():
        try:
            _c = json.loads(_baseline_cache.read_text(encoding="utf-8"))
            # 같은 template + 같은 native 서열일 때만 재사용 (안전)
            if _c.get("template_pdb") == config.template_pdb and _c.get("sequence") == config.original_sequence:
                _cached = _c
        except Exception as exc:
            print(f"  [baseline] 캐시 로드 실패(재도킹): {exc}", file=sys.stderr)
    try:
        if _cached is not None:
            # 캐시 재사용 — 재도킹 생략, 비교용 PDB 만 현재 epoch 경로로 복사
            if _baseline_cache_pdb.exists():
                shutil.copy2(str(_baseline_cache_pdb), str(baseline_out))
            best_baseline_ddg = float(_cached.get("ddg", 0.0))
            baseline = {"ddg": best_baseline_ddg,
                        "total_score": float(_cached.get("total_score", 0.0)),
                        "clash_score": float(_cached.get("clash_score", 0.0))}
            print(f"  [baseline] 캐시 재사용 (native SST-14 재도킹 생략): ddG={best_baseline_ddg:.3f}", file=sys.stderr)
        else:
            # Run multiple baseline refinements and pick best by ddG
            best_baseline: Dict[str, Any] = {}
            best_baseline_ddg = float("inf")
            for trial_idx in range(n_baseline_trials):
                trial_out = flow_dir / f"baseline_trial_{trial_idx}.pdb"
                trial_result = _run_script(
                    flexpep_script,
                    [
                        "--input", config.template_pdb,
                        "--output", str(trial_out),
                        "--protocol", "flexpep_refine",
                        "--peptide-chain", str(config.peptide_chain),
                    ],
                    config.conda_env,
                    repo_root,
                    timeout=config.script_timeout,
                )
                trial_ddg = float(trial_result.get("ddg", 999.0))
                print(f"  [baseline] trial {trial_idx + 1}/{n_baseline_trials}: ddG={trial_ddg:.3f} total={float(trial_result.get('total_score', 0)):.3f}", file=sys.stderr)
                if trial_ddg < best_baseline_ddg:
                    best_baseline_ddg = trial_ddg
                    best_baseline = trial_result
                    # Copy best trial PDB to canonical baseline path
                    shutil.copy2(str(trial_out), str(baseline_out))
            baseline = best_baseline
            # 캐시 저장 (다음 epoch 재사용용) — reuse_baseline 일 때만
            if getattr(config, "reuse_baseline", False) and best_baseline:
                try:
                    _baseline_cache.parent.mkdir(parents=True, exist_ok=True)
                    _baseline_cache.write_text(json.dumps({
                        "template_pdb": config.template_pdb,
                        "sequence": config.original_sequence,
                        "ddg": best_baseline_ddg,
                        "total_score": float(baseline.get("total_score", 0.0)),
                        "clash_score": float(baseline.get("clash_score", 0.0)),
                    }, indent=2, ensure_ascii=False), encoding="utf-8")
                    if baseline_out.exists():
                        shutil.copy2(str(baseline_out), str(_baseline_cache_pdb))
                    print(f"  [baseline] 캐시 저장 (이후 epoch 재사용): {_baseline_cache.name}", file=sys.stderr)
                except Exception as exc:
                    print(f"  [baseline] 캐시 저장 실패(non-fatal): {exc}", file=sys.stderr)
        emitter.complete_rosetta_substep("step06_prepare", t_prepare0)
        emitter.append_timeline_event(0, "rosetta.prepare", "completed", f"Baseline ready (best of {n_baseline_trials}: ddG={best_baseline_ddg:.1f})")
        baseline_ddg = float(baseline.get("ddg", 0.0))
        baseline_total = float(baseline.get("total_score", 0.0))
        baseline_clash = float(baseline.get("clash_score", 0.0))

        # Adaptive gate: set initial thresholds relative to baseline
        if getattr(config, "gate_mode", "static") == "adaptive" and baseline_ddg < 0:
            # Initial gate = 10% of baseline ddG (e.g., baseline=-48 → gate=-4.8)
            initial_ddg_gate = round(baseline_ddg * 0.1, 1)
            initial_clash_gate = max(int(baseline_clash * 2), 10)
            config.rosetta_ddg_max = initial_ddg_gate
            config.rosetta_clash_max = initial_clash_gate
            print(f"  [adaptive] Initial gates from baseline: ddG≤{initial_ddg_gate} clash≤{initial_clash_gate}", file=sys.stderr)

        emitter.set_baseline({
            "sequence": config.original_sequence,
            "pdb": str(baseline_out),
            "ddg": baseline_ddg,
            "total_score": baseline_total,
            "clash_score": baseline_clash,
        })
        # Add baseline as reference candidate in the ranking table
        emitter.set_candidates([{
            "rank": 0,
            "id": "baseline_SST14",
            "sequence": config.original_sequence,
            "ddG": round(baseline_ddg, 3),
            "totalScore": round(baseline_total, 3),
            "clashScore": round(baseline_clash, 1),
            "finalScore": round(-baseline_ddg, 3),
            "result": "REF",
            "failReason": "",
        }])
        emitter.complete_step("step06_baseline", t_baseline)
    except Exception as exc:
        emitter.fail_rosetta_substep("step06_prepare", t_prepare0)
        emitter.append_timeline_event(0, "rosetta.prepare", "failed", f"Baseline preparation failed: {exc}")
        emitter.fail_step("step06_baseline", t_baseline)
        run_status = "completed_with_warnings"
        run_failure_stage = "baseline_prepare"
        run_error_summary = str(exc)
        # Fail-open: keep loop alive to produce candidates/ranking from iterations.
        emitter.append_timeline_event(0, "runner", "running", "Fail-open enabled: continue without baseline pose")

    iterations_out: List[Dict[str, Any]] = []
    final_selected: List[CandidateResult] = []
    # Only dedup within current run — cross-run history excluded to preserve
    # search space. Native sequence is always excluded to prevent fallback.
    seen_sequences = {config.original_sequence}
    critic_feedback: Dict[str, Any] = {}

    # Multi-Armed Bandit: data-driven fallback for focus_positions
    bandit_guidance: Dict[str, Any] = {}
    if prior_records:
        try:
            bandit_guidance = get_bandit_guidance(prior_records, n_focus=config.bandit_n_focus)
            print(f"  [bandit] Thompson sampling focus: {bandit_guidance.get('focus_positions', [])}", file=sys.stderr)
        except Exception as exc:
            print(f"  [bandit] Initialization failed (non-fatal): {exc}", file=sys.stderr)
    convergence_detector = ConvergenceDetector(
        window_size=config.convergence_window_size,
        significance_level=config.convergence_significance,
    )

    # BO optimizer: iteration 간 공유 (fit은 매 iteration 내에서 수행)
    _bo_optimizer: Optional[Any] = None
    if _HAS_BO:
        try:
            _bo_optimizer = BayesianPeptideOptimizer(
                embedder=OneHotEmbedder(max_len=len(config.original_sequence)),
                objectives=["ddg", "ecr_score"],
                maximize=[False, True],  # ddg 최소화, ecr_score 최대화
            )
            print("  [bo] BayesianPeptideOptimizer initialized", file=sys.stderr)
        except Exception as exc:
            print(f"  [bo] Initialization failed (non-fatal): {exc}", file=sys.stderr)
            _bo_optimizer = None

    # 2026-06-10: in-loop 선택성 리더보드 (조건부 게이트). config.inloop_selectivity 시 매 iteration
    # 유망(ddG 강한) 후보만 off-target 도킹 → Δmargin(native 보정) → Planner/Critic 피드백.
    _sel_leaderboard = None
    _global_lb = None
    _global_lb_path = repo_root / config.output_dir / "global_selectivity_leaderboard.json"
    if getattr(config, "inloop_selectivity", False):
        try:
            from .selectivity_loop import SelectivityLeaderboard
            from .global_leaderboard import GlobalSelectivityLeaderboard
            _sel_leaderboard = SelectivityLeaderboard(capacity=config.top_k)
            # 무한 엔진: 글로벌 리더보드로 warm-start (역대 도킹 서열 dedup + 게이트 기준선)
            _global_lb = GlobalSelectivityLeaderboard.load(_global_lb_path)
            if _global_lb.entries or _global_lb.screened_seqs:
                _sel_leaderboard.seed_from_global(_global_lb.warm_start_payload())
                print(f"  [sel-loop] 글로벌 warm-start: {len(_global_lb.screened_seqs)} 서열 기측정, "
                      f"역대 best Δ={_global_lb.best_delta()}", file=sys.stderr)
            print("  [sel-loop] in-loop selectivity 활성화 (조건부 게이트)", file=sys.stderr)
        except Exception as exc:
            print(f"  [sel-loop] init 실패(non-fatal): {exc}", file=sys.stderr)

    for iteration in range(1, config.max_iterations + 1):
        emitter.set_iteration(iteration)
        emitter.reset_rosetta_substeps()
        objective_mode = choose_objective_mode(config.objective_mode, iteration)

        emitter.append_timeline_event(iteration, "planner", "running", "Planner generating hypothesis")
        emitter.update_agent("planner", status="active", message=f"Iteration {iteration} planning")
        prev_results: Dict[str, Any] = {"objective_mode": objective_mode}
        if final_selected:
            prev_results["top_candidates"] = [
                {"sequence": c.sequence, "ddg": c.ddg, "id": c.candidate_id}
                for c in sorted(final_selected, key=lambda x: x.ddg)[:5]
            ]
            prev_results["best_ddg"] = min(c.ddg for c in final_selected)
        # 2026-06-10: in-loop 선택성 리더보드를 Planner 에 피드백 (Δmargin>0 = native 초과 선택성)
        if _sel_leaderboard is not None and _sel_leaderboard.entries:
            prev_results["selectivity_leaderboard"] = _sel_leaderboard.summary()
            prev_results["best_delta_margin"] = _sel_leaderboard.best_delta()
        if historical_top_hits:
            prev_results["historical_top_hits"] = historical_top_hits
            prev_results["n_historical_sequences"] = n_prior
        plan = planner.execute(
            {
                "iteration": iteration,
                "receptor_config": {"name": "SSTR2", "chain": "A"},
                "constraints": {
                    "max_iterations": config.max_iterations,
                    "reference_sequence": config.original_sequence,
                    "design_positions": config.design_positions,
                },
                "critic_feedback": critic_feedback,
                "previous_results": prev_results,
            }
        ).get("plan")
        hypothesis = getattr(plan, "hypothesis", f"Iteration {iteration} mutate->dock optimization")
        emitter.update_agent(
            "planner",
            status="idle",
            message=hypothesis[:80],
            task_count_delta=1,
            report={
                "type": "plan",
                "iteration": iteration,
                "run_id": run_id,
                "hypothesis": hypothesis,
                "strategy": objective_mode,
            },
        )
        emitter.append_timeline_event(iteration, "planner", "completed", hypothesis[:120])

        iter_dir = flow_dir / f"iter_{iteration:02d}"
        iter_dir.mkdir(parents=True, exist_ok=True)
        reports_dir = iter_dir / "08_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # -- persist planner report per iteration --
        planner_report = {
            "type": "planner",
            "iteration": iteration,
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hypothesis": hypothesis,
            "strategy": objective_mode,
            "critic_feedback_used": critic_feedback or None,
            "previous_best_ddg": prev_results.get("best_ddg"),
        }
        (reports_dir / "planner_report.json").write_text(
            json.dumps(planner_report, indent=2, ensure_ascii=False), encoding="utf-8",
        )

        candidates: List[CandidateResult] = []
        t_prepare = emitter.start_rosetta_substep("step06_prepare")
        emitter.append_timeline_event(iteration, "rosetta.prepare", "running", "Iteration directory and run context prepared")
        emitter.complete_rosetta_substep("step06_prepare", t_prepare)
        emitter.append_timeline_event(iteration, "rosetta.prepare", "completed", "Ready for mutation and docking")

        t_step06 = emitter.start_step("step06")
        t_mutate = emitter.start_rosetta_substep("step06_mutate")
        emitter.append_timeline_event(iteration, "rosetta.mutate", "running", "Generating peptide mutants")
        try:
            candidate_jobs: List[Dict[str, Any]] = []
            guidance = getattr(plan, "parameters", {}).get("mutation_guidance", {})
            # Merge bandit guidance: use bandit focus_positions as fallback
            # when the LLM planner did not provide focus_positions
            if bandit_guidance and not guidance.get("focus_positions"):
                guidance.setdefault("focus_positions", bandit_guidance.get("focus_positions", []))
            n_guided = min(guidance.get("n_guided", config.n_candidates), config.n_candidates)

            mutation_positions = _mutable_design_positions(config)
            for idx in range(1, config.n_candidates + 1):
                mutant = None
                fail_reason = ""
                last_proposal = config.original_sequence
                for pharmacophore_attempt in range(PHARMACOPHORE_RETRY_LIMIT + 1):
                    max_trials = config.max_dedup_trials
                    for trial in range(max_trials):
                        # Escalate mutation count on repeated dedup failures
                        force_n_mutations = None
                        if trial >= max_trials * 3 // 5:
                            force_n_mutations = min(len(mutation_positions), config.max_random_mutations + 1)
                        elif trial >= max_trials * 2 // 5:
                            force_n_mutations = config.max_random_mutations
                        elif trial >= max_trials // 5:
                            force_n_mutations = 2

                        if idx <= n_guided and guidance.get("focus_positions") and trial < max_trials * 2 // 5:
                            proposal = generate_guided_mutant(
                                config.original_sequence,
                                mutation_positions,
                                guidance,
                                rng=random.Random(
                                    config.seed_base
                                    + iteration * 1000
                                    + idx * 100
                                    + pharmacophore_attempt * max_trials
                                    + trial
                                ),
                            )
                        else:
                            proposal = generate_random_mutant(
                                config.original_sequence,
                                mutation_positions,
                                rng=random.Random(
                                    config.seed_base
                                    + iteration * 1000
                                    + idx * 100
                                    + pharmacophore_attempt * max_trials
                                    + trial
                                ),
                                n_mutations=force_n_mutations,
                            )
                        last_proposal = proposal
                        if proposal == config.original_sequence or proposal in seen_sequences:
                            continue
                        if not _preserves_scaffold(proposal, config.original_sequence):
                            break
                        mutant = proposal
                        seen_sequences.add(proposal)
                        break
                    if mutant is not None:
                        break
                    if not _preserves_scaffold(last_proposal, config.original_sequence):
                        continue
                    # Guaranteed: never submit native sequence as candidate
                    fallback = generate_random_mutant(
                        config.original_sequence,
                        mutation_positions,
                        rng=random.Random(
                            config.seed_base
                            + iteration * 1000
                            + idx * 100
                            + pharmacophore_attempt * max_trials
                            + 99
                        ),
                        n_mutations=max(2, len(mutation_positions) // 2),
                    )
                    last_proposal = fallback
                    if (
                        fallback != config.original_sequence
                        and fallback not in seen_sequences
                        and _preserves_scaffold(fallback, config.original_sequence)
                    ):
                        mutant = fallback
                        seen_sequences.add(fallback)
                        break

                if mutant is None:
                    fail_reason = (
                        "FWKT pharmacophore gate failed after "
                        f"{PHARMACOPHORE_RETRY_LIMIT} retries"
                    )
                    mutant = last_proposal
                candidate_jobs.append(
                    {
                        "idx": idx,
                        "mutant": mutant,
                        "out_pdb": iter_dir / f"cand_{idx:03d}.pdb",
                        "fail_reason": fail_reason,
                    }
                )

            emitter.complete_rosetta_substep("step06_mutate", t_mutate)
            emitter.append_timeline_event(
                iteration,
                "rosetta.mutate",
                "completed",
                "Mutants generated" if candidate_jobs else "No candidates to mutate",
            )

            t_refine = emitter.start_rosetta_substep("step06_refine")
            n_jobs = len(candidate_jobs)
            max_workers = min(n_jobs, config.max_parallel_workers, os.cpu_count() or 4)
            emitter.append_timeline_event(
                iteration, "rosetta.refine", "running",
                f"Running FlexPepDock refinement ({n_jobs} candidates, {max_workers} parallel workers)",
            )

            # Emit per-candidate "running" events
            for job in candidate_jobs:
                cid = f"iter{iteration:02d}_cand{int(job['idx']):03d}"
                emitter.append_timeline_event(
                    iteration, f"rosetta.refine.{cid}", "running",
                    f"{cid}: {job['mutant']}",
                )

            iteration_failures: List[str] = []
            completed_count = 0

            def _dock_one(job: Dict[str, Any]) -> CandidateResult:
                idx = int(job["idx"])
                mutant = str(job["mutant"])
                out_pdb = Path(job["out_pdb"])
                candidate_id = f"iter{iteration:02d}_cand{idx:03d}"
                fail_reason = str(job.get("fail_reason", ""))
                if fail_reason:
                    return CandidateResult(
                        iteration=iteration,
                        candidate_id=candidate_id,
                        sequence=mutant,
                        ddg=999.0,
                        total_score=999.0,
                        clash_score=999.0,
                        objective_mode=objective_mode,
                        fail_reason=fail_reason,
                    )
                try:
                    result = _run_script(
                        flexpep_script,
                        [
                            "--input", config.template_pdb,
                            "--output", str(out_pdb),
                            "--protocol", "flexpep_refine",
                            "--reference-complex", config.template_pdb,
                            "--target-sequence", mutant,
                            "--peptide-chain", str(config.peptide_chain),
                        ],
                        config.conda_env,
                        repo_root,
                        timeout=config.script_timeout,
                    )
                    return CandidateResult(
                        iteration=iteration,
                        candidate_id=candidate_id,
                        sequence=mutant,
                        ddg=float(result.get("ddg", 0.0)),
                        total_score=float(result.get("total_score", 0.0)),
                        clash_score=float(result.get("clash_score", 0.0)),
                        objective_mode=objective_mode,
                    )
                except Exception as cand_exc:
                    return CandidateResult(
                        iteration=iteration,
                        candidate_id=candidate_id,
                        sequence=mutant,
                        ddg=999.0,
                        total_score=999.0,
                        clash_score=999.0,
                        objective_mode=objective_mode,
                        fail_reason=str(cand_exc),
                    )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_job = {
                    executor.submit(_dock_one, job): job for job in candidate_jobs
                }
                for future in as_completed(future_to_job):
                    cand_result = future.result()
                    candidates.append(cand_result)
                    completed_count += 1
                    cid = cand_result.candidate_id

                    if cand_result.fail_reason:
                        failure_msg = f"{cid} refine failed: {cand_result.fail_reason}"
                        iteration_failures.append(failure_msg)
                        emitter.append_timeline_event(
                            iteration, f"rosetta.refine.{cid}", "failed",
                            f"{cid}: FAILED ({cand_result.fail_reason[:120]})",
                        )
                    else:
                        emitter.append_timeline_event(
                            iteration, f"rosetta.refine.{cid}", "completed",
                            f"{cid}: ddG={cand_result.ddg:.2f} seq={cand_result.sequence}",
                        )

                    # Stream completed candidate to UI immediately
                    _emit_candidates(emitter, candidates, ddg_threshold=config.rosetta_ddg_max, flow_dir=flow_dir)

            emitter.complete_rosetta_substep("step06_refine", t_refine)
            if iteration_failures:
                run_status = "completed_with_warnings"
                if not run_failure_stage:
                    run_failure_stage = f"iteration_{iteration}_rosetta_partial"
                run_error_summary = f"{len(iteration_failures)} candidate refine failures (latest iteration={iteration})"
                emitter.append_timeline_event(
                    iteration,
                    "rosetta.refine",
                    "completed",
                    f"Docking refinement completed with {len(iteration_failures)} failures",
                )
                if iteration < config.max_iterations:
                    emitter.append_timeline_event(
                        iteration,
                        "continue_to_next_iteration",
                        "running",
                        "Partial failures recorded; continuing to next iteration",
                    )
            else:
                emitter.append_timeline_event(iteration, "rosetta.refine", "completed", "Docking refinement completed")
            t_score = emitter.start_rosetta_substep("step06_score")
            emitter.append_timeline_event(iteration, "rosetta.score", "running", "Aggregating ddG/score/clash metrics")
            _ = {
                "mean_ddg": statistics.mean([c.ddg for c in candidates]) if candidates else 0.0,
                "best_ddg": min([c.ddg for c in candidates]) if candidates else 0.0,
            }
            emitter.complete_rosetta_substep("step06_score", t_score)
            emitter.append_timeline_event(iteration, "rosetta.score", "completed", "Rosetta scoring metrics ready")
        except Exception as exc:
            # Keep sub-step status truthful in failure scenarios.
            try:
                emitter.fail_rosetta_substep("step06_refine", t_refine)  # type: ignore[name-defined]
                emitter.append_timeline_event(iteration, "rosetta.refine", "failed", f"Refinement failed: {exc}")
            except Exception:
                emitter.fail_rosetta_substep("step06_mutate", t_mutate)
                emitter.append_timeline_event(iteration, "rosetta.mutate", "failed", f"Mutation stage failed: {exc}")
            emitter.fail_step("step06", t_step06)
            run_status = "completed_with_warnings"
            run_failure_stage = f"iteration_{iteration}_rosetta"
            run_error_summary = str(exc)
            # Keep historical ranking update path reachable for later iterations.
            if iteration < config.max_iterations:
                emitter.append_timeline_event(
                    iteration,
                    "continue_to_next_iteration",
                    "running",
                    "Iteration-level Rosetta failure captured; continuing",
                )
                continue

        qc_candidates = [_candidate_to_qc(c, i + 1, objective_mode) for i, c in enumerate(candidates)]
        thresholds = {
            "gates_enabled": {
                "plddt": False,       # ESMFold 필요 → OFF
                "docking": False,     # DiffDock/Boltz2 필요 → OFF
                "rosetta": True,      # 로컬 PyRosetta → ON
                "selectivity": False, # off-target 구조 필요 → OFF
            },
            "rosetta_ddg_max": config.rosetta_ddg_max,
            "rosetta_clash_max": config.rosetta_clash_max,
            "rosetta_constraint_violations_max": 0,
            "ranking_mode": "ddg_primary",
            "top_k_by_ddg": config.top_k,
        }
        t_qc = emitter.start_rosetta_substep("step06_qc")
        emitter.append_timeline_event(iteration, "qc", "running", "Applying QC gates and ranking")
        emitter.update_agent("qc-ranker", status="active", message="Ranking candidates")
        qc_result = qcranker.execute(
            {
                "candidates": qc_candidates,
                "thresholds": thresholds,
                "run_id": run_id,
                "iteration": iteration,
                "top_k": config.top_k,
            }
        )
        emitter.update_agent("qc-ranker", status="idle", message="Ranking done", task_count_delta=1)
        emitter.complete_rosetta_substep("step06_qc", t_qc)
        emitter.append_timeline_event(iteration, "qc", "completed", "QC ranking completed")

        selected_ids = {c.candidate_id for c in qc_result["top_candidates"]}
        selected: List[CandidateResult] = []
        for c in candidates:
            if c.candidate_id in selected_ids:
                c.selected = True
                selected.append(c)

        _emit_candidates(emitter, candidates, ddg_threshold=config.rosetta_ddg_max, flow_dir=flow_dir)

        # -- In-loop 선택성 (조건부 게이트): 유망(ddG 강한) 후보만 off-target 도킹 → Δmargin --
        if _sel_leaderboard is not None:
            try:
                from .selectivity_loop import screen_iteration_candidates
                emitter.append_timeline_event(iteration, "selectivity", "running", "In-loop selectivity 게이트 평가")
                screened = screen_iteration_candidates(
                    candidates, iter_dir, _sel_leaderboard,
                    original_sequence=config.original_sequence,
                    conda_env=config.conda_env,
                    max_screen_per_iter=getattr(config, "selectivity_max_per_iter", 2),
                    clash_max=float(config.rosetta_clash_max),
                    timeout=config.script_timeout,
                )
                emitter.append_timeline_event(
                    iteration, "selectivity", "completed",
                    f"In-loop selectivity: {len(screened)}건 도킹, leaderboard best Δ={_sel_leaderboard.best_delta()}",
                )
            except Exception as exc:
                print(f"  [sel-loop] iteration screening 실패(non-fatal): {exc}", file=sys.stderr)

        # -- Convergence detection --
        if selected:
            convergence_detector.add_iteration(iteration, [c.ddg for c in selected])
            conv_flag, conv_details = convergence_detector.is_converged()
            emitter.set_convergence({
                "converged": conv_flag,
                "p_value": conv_details.get("p_value"),
                "cv": conv_details.get("cv"),
                "recommendation": conv_details.get("recommendation", ""),
            })
            if conv_flag:
                emitter.append_timeline_event(
                    iteration, "convergence", "completed",
                    f"Converged: p={conv_details['p_value']:.4f}, CV={conv_details['cv']:.4f}",
                )
                print(
                    f"  [convergence] iter {iteration}: CONVERGED "
                    f"(p={conv_details['p_value']:.4f}, CV={conv_details['cv']:.4f})",
                    file=sys.stderr,
                )
            else:
                print(
                    f"  [convergence] iter {iteration}: not converged "
                    f"({conv_details.get('recommendation', '')})",
                    file=sys.stderr,
                )

        now_iso = datetime.now(timezone.utc).isoformat()
        run_records.extend(
            [
                {
                    "record_type": "candidate",
                    "status": "failed" if c.fail_reason else "success",
                    "run_id": run_id,
                    "iteration": iteration,
                    "candidate_id": c.candidate_id,
                    "sequence": c.sequence,
                    "ddg": c.ddg,
                    "total_score": c.total_score,
                    "clash": c.clash_score,
                    "selected": c.selected,
                    "final_score": round(-c.ddg, 3),
                    "error_summary": c.fail_reason,
                    "ts": now_iso,
                }
                for c in candidates
            ]
        )
        emitter.set_qc_gates(
            [
                {
                    "name": "RosettaGate",
                    "criterion": f"ddG <= {config.rosetta_ddg_max}",
                    "passed": len(selected),
                    "failed": max(0, len(candidates) - len(selected)),
                    "total": len(candidates),
                }
            ]
        )

        t_critic = emitter.start_rosetta_substep("step06_critic")
        emitter.append_timeline_event(iteration, "critic", "running", "Critic analyzing candidate outcomes")
        emitter.update_agent("critic", status="active", message="Analyzing results")
        critic_analysis = critic.execute(
            {
                "rank_table": qc_result["rank_table"],
                "qc_report": qc_result["qc_report"],
                "iteration": iteration,
                "current_params": {
                    "n_candidates": config.n_candidates,
                    "objective_mode": objective_mode,
                    "rosetta_ddg_max": config.rosetta_ddg_max,
                    "rosetta_clash_max": config.rosetta_clash_max,
                },
                # 2026-06-10: 선택성 리더보드를 Critic 에 제공 (Δmargin>0 = native 초과 선택성)
                "selectivity_leaderboard": (_sel_leaderboard.summary() if _sel_leaderboard else []),
                "best_delta_margin": (_sel_leaderboard.best_delta() if _sel_leaderboard else None),
            }
        ).get("critic_analysis")
        emitter.update_agent(
            "critic",
            status="idle",
            message=(getattr(critic_analysis, "hypothesis", "") or "" or "")[:80],
            task_count_delta=1,
            report={
                "type": "critic",
                "iteration": iteration,
                "hypothesis": getattr(critic_analysis, "hypothesis", "") or "",
                "proposed_changes": [
                    {
                        "parameter": c.parameter_name,
                        "old": str(c.old_value),
                        "new": str(c.new_value),
                        "rationale": c.rationale,
                    }
                    for c in getattr(critic_analysis, "proposed_changes", [])
                ],
            },
        )
        emitter.complete_rosetta_substep("step06_critic", t_critic)
        emitter.append_timeline_event(
            iteration,
            "critic",
            "completed",
            (getattr(critic_analysis, "hypothesis", "") or "" or "")[:120],
        )
        critic_feedback = {
            "hypothesis": getattr(critic_analysis, "hypothesis", "") or "",
            "proposed_changes": [
                {
                    "parameter_name": c.parameter_name,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "rationale": c.rationale,
                }
                for c in getattr(critic_analysis, "proposed_changes", [])
            ],
        }

        # -- Adaptive gate: apply Critic's proposed threshold changes --
        if getattr(config, "gate_mode", "static") == "adaptive":
            for change in critic_feedback["proposed_changes"]:
                pname = change["parameter_name"]
                new_val = change["new_value"]
                if pname == "rosetta_ddg_max" and isinstance(new_val, (int, float)):
                    old = config.rosetta_ddg_max
                    config.rosetta_ddg_max = float(new_val)
                    print(f"  [adaptive] rosetta_ddg_max: {old} → {config.rosetta_ddg_max} (Critic)", file=sys.stderr)
                elif pname == "rosetta_clash_max" and isinstance(new_val, (int, float)):
                    old = config.rosetta_clash_max
                    config.rosetta_clash_max = int(new_val)
                    print(f"  [adaptive] rosetta_clash_max: {old} → {config.rosetta_clash_max} (Critic)", file=sys.stderr)

        # -- persist critic report per iteration --
        # collect PDB paths for this iteration's candidates
        iter_pdb_paths = sorted(str(p) for p in iter_dir.glob("cand_*.pdb"))
        critic_report = {
            "type": "critic",
            "iteration": iteration,
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hypothesis": critic_feedback["hypothesis"],
            "proposed_changes": critic_feedback["proposed_changes"],
            "current_params": {
                "n_candidates": config.n_candidates,
                "objective_mode": objective_mode,
                "rosetta_ddg_max": config.rosetta_ddg_max,
                "rosetta_clash_max": config.rosetta_clash_max,
            },
            "candidate_pdbs": iter_pdb_paths,
            "receptor_pdb": config.template_pdb,
        }
        (reports_dir / "critic_report.json").write_text(
            json.dumps(critic_report, indent=2, ensure_ascii=False), encoding="utf-8",
        )

        t_reporter = emitter.start_rosetta_substep("step06_reporter")
        emitter.append_timeline_event(iteration, "reporter", "running", "Reporter writing iteration artifacts")
        emitter.update_agent("reporter", status="active", message="Writing reports")
        report_paths = reporter.execute(
            {
                "run_id": run_id,
                "iteration": iteration,
                "rank_table": qc_result["rank_table"],
                "top_candidates": qc_result["top_candidates"],
                "receptor_pdb": config.template_pdb,
                "output_dir": str(iter_dir),
                "critic_analysis": critic_analysis,
            }
        ).get("report_paths", {})
        emitter.update_agent(
            "reporter",
            status="idle",
            message="Reports saved",
            task_count_delta=1,
            report={
                "type": "reporter",
                "iteration": iteration,
                "summary": str(report_paths.get("summary_md", "")),
            },
        )
        # -- persist iteration manifest (reporter meta + PDB paths) --
        rank_table_obj = qc_result.get("rank_table")
        # RankTable object → extract ranked_candidates list
        if hasattr(rank_table_obj, "ranked_candidates"):
            rank_rows = [
                {
                    "candidate_id": c.candidate_id,
                    "sequence": c.sequence,
                    "ddg": c.ddg,
                    "clash_count": c.clash_count,
                    "pass_gates": c.pass_gates,
                    "fail_reasons": c.fail_reasons,
                    "final_score": c.final_score,
                    "pdb_path": c.pdb_path,
                }
                for c in rank_table_obj.ranked_candidates
            ]
        elif isinstance(rank_table_obj, list):
            rank_rows = rank_table_obj
        else:
            rank_rows = []
        candidate_manifest = []
        for row in rank_rows:
            cid = row.get("candidate_id", "")
            # derive PDB path: iter_XX/cand_NNN.pdb
            cand_num = cid.split("cand")[-1] if "cand" in cid else ""
            pdb_file = iter_dir / f"cand_{int(cand_num):03d}.pdb" if cand_num.isdigit() else None
            candidate_manifest.append({
                "candidate_id": cid,
                "sequence": row.get("sequence", ""),
                "ddg": row.get("ddg"),
                "clash_count": row.get("clash_count"),
                "pass_gates": row.get("pass_gates"),
                "fail_reasons": row.get("fail_reasons", ""),
                "pdb_path": str(pdb_file) if pdb_file and pdb_file.exists() else None,
            })
        # -- Alternative scoring chain: GNINA → ECR → Pareto → BO --
        candidates = _apply_alternative_scoring(
            candidates,
            iter_dir=iter_dir,
            iteration=iteration,
            bo_optimizer=_bo_optimizer,
        )

        # -- RCSB PDB sequence similarity check (best-effort) --
        rcsb_matches: Dict[str, list] = {}
        selected_seqs = {c.candidate_id: c.sequence for c in selected if c.sequence}
        if selected_seqs and _HAS_RCSB:
            print(f"  [rcsb] Checking {len(selected_seqs)} selected candidates against RCSB PDB...", file=sys.stderr)
            rcsb_matches = _rcsb_check_candidates(selected_seqs, identity_cutoff=0.4, max_results=5)
            if rcsb_matches:
                print(f"  [rcsb] Found PDB matches for {len(rcsb_matches)} candidates", file=sys.stderr)
            else:
                print("  [rcsb] No PDB matches found (or network unavailable)", file=sys.stderr)
        # Enrich candidate_manifest with RCSB hits
        for entry in candidate_manifest:
            cid = entry["candidate_id"]
            if cid in rcsb_matches:
                entry["rcsb_hits"] = rcsb_matches[cid]

        # -- Pharma properties enrichment (best-effort) --
        if _HAS_PHARMA:
            try:
                pp = _PharmaProperties(reference_seq=config.original_sequence)
                for entry in candidate_manifest:
                    seq = entry.get("sequence", "")
                    if seq and len(seq) >= 5:
                        try:
                            pharma = pp.calculate_all(seq)
                            entry["pharma"] = pharma
                        except Exception:
                            pass
                print(f"  [pharma] Enriched {sum(1 for e in candidate_manifest if 'pharma' in e)} candidates", file=sys.stderr)
            except Exception as exc:
                print(f"  [pharma] Failed: {exc}", file=sys.stderr)

        # -- Cluster A~E classification (best-effort) --
        if _HAS_CLUSTER and _HAS_PHARMA:
            try:
                cluster_input = []
                for entry in candidate_manifest:
                    pharma = entry.get("pharma", {})
                    cluster_input.append({
                        "sequence": entry.get("sequence", ""),  # chelator_site sequence-based 판정용
                        "ddG": entry.get("ddG", 0),
                        "clash_score": entry.get("clashScore", entry.get("clash_score", 99)),
                        "pLDDT": entry.get("pLDDT"),
                        "structural_rules": pharma.get("structural_rules", {}),
                        "instability_index": pharma.get("instability_index", 99),
                        "blosum62": pharma.get("blosum62", {}),
                        "protease_sites": pharma.get("protease_sites", {}),
                        "gravy": pharma.get("gravy", 0),
                        "net_charge_ph74": pharma.get("net_charge_ph74", 0),
                        "metal_coordination": pharma.get("metal_coordination", {}),
                        "selectivity_margin": entry.get("selectivity_margin"),
                    })
                cluster_result = _batch_classify(cluster_input)
                for i, entry in enumerate(candidate_manifest):
                    if i < len(cluster_result.get("results", [])):
                        entry["cluster"] = cluster_result["results"][i].get("classification", {})
                print(f"  [cluster] Classified {len(candidate_manifest)} candidates into A~E", file=sys.stderr)
            except Exception as exc:
                print(f"  [cluster] Failed: {exc}", file=sys.stderr)

        # -- Dashboard enrichment: pharma/cluster 값 포함한 최종 candidate 상태 push --
        if _HAS_PHARMA or _HAS_CLUSTER:
            try:
                manifest_by_cid = {e["candidate_id"]: e for e in candidate_manifest}
                enriched_entries = []
                for idx, c in enumerate(sorted(candidates, key=lambda x: x.ddg)):
                    entry = manifest_by_cid.get(c.candidate_id, {})
                    pharma = entry.get("pharma", {})
                    cluster_info = entry.get("cluster", {})
                    candidate_entry: Dict[str, Any] = {
                        "rank": idx + 1,
                        "id": c.candidate_id,
                        "sequence": c.sequence,
                        "ddG": round(c.ddg, 3),
                        "totalScore": round(c.total_score, 3),
                        "clashScore": round(c.clash_score, 1),
                        "finalScore": round(-c.ddg, 3),
                        "result": (
                            "PASS" if c.selected else
                            "PASS" if (c.ddg <= config.rosetta_ddg_max and c.ddg < 900) else
                            "FAIL"
                        ),
                        "failReason": c.fail_reason if c.fail_reason else "",
                        "mw": pharma.get("molecular_weight", {}).get("mw_average"),
                        "instability_index": pharma.get("instability_index"),
                        "radiolysis_score": pharma.get("radiolysis_susceptibility", {}).get("total_score"),
                        "cluster": cluster_info.get("cluster"),
                        # reviewer-pharma 2026-05-14 — tier1-cluster-data 머지 sprint
                        # gravy / net_charge_ph74 : pharma_properties.calculate_all() 직접 키
                        "gravy": pharma.get("gravy"),
                        "net_charge_ph74": pharma.get("net_charge_ph74"),
                        # selectivity_margin: step05b 결과가 manifest entry에 있으면 포함
                        "selectivity_margin": entry.get("selectivity_margin", c.extra_scores.get("selectivity_margin")),
                        # 다목적 cheap-objectives (Step 0 enrichment): 반감기 + ADMET surrogate + 통합 점수
                        "half_life_h": c.extra_scores.get("half_life_h"),
                        "admet_score": c.extra_scores.get("admet_score"),
                        "boman_index": c.extra_scores.get("boman_index"),
                        "pi": c.extra_scores.get("pi"),
                        "mo_score": _mo_scalar(c.extra_scores, c.ddg) if _HAS_MO else None,
                        # fwkt_contact: _criteria_a()가 항상 계산 → 모든 cluster에서 존재
                        "fwkt_contact": cluster_info.get("criteria_met", {}).get("A", {}).get("fwkt_contact"),
                        # chelator_site_available: _criteria_d()는 cluster D/E에서만 포함
                        # cluster A/B/C 후보는 status._enrich_candidates() fallback으로 채워짐
                        "chelator_site_available": cluster_info.get("criteria_met", {}).get("D", {}).get("chelator_site_available"),
                    }
                    if "cand" in c.candidate_id:
                        candidate_entry["pdb_path"] = str(
                            flow_dir / f"iter_{c.iteration:02d}" / f"cand_{int(c.candidate_id.split('cand')[1]):03d}.pdb"
                        )
                    enriched_entries.append(candidate_entry)
                emitter.set_candidates(enriched_entries)
                print(f"  [dashboard-enrich] Pushed {len(enriched_entries)} enriched candidates", file=sys.stderr)
            except Exception as exc:
                print(f"  [dashboard-enrich] Failed: {exc}", file=sys.stderr)

        iteration_manifest = {
            "type": "iteration_manifest",
            "iteration": iteration,
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "receptor_pdb": config.template_pdb,
            "baseline_pdb": str(flow_dir / "baseline_refined.pdb"),
            "candidates": candidate_manifest,
            "rcsb_match_summary": {
                "checked": len(selected_seqs),
                "matched": len(rcsb_matches),
                "identity_cutoff": 0.4,
            },
            "report_paths": {k: str(v) for k, v in report_paths.items()},
            "planner_report": str(reports_dir / "planner_report.json"),
            "critic_report": str(reports_dir / "critic_report.json"),
        }
        (reports_dir / "iteration_manifest.json").write_text(
            json.dumps(iteration_manifest, indent=2, ensure_ascii=False), encoding="utf-8",
        )

        emitter.complete_rosetta_substep("step06_reporter", t_reporter)
        emitter.append_timeline_event(
            iteration,
            "reporter",
            "completed",
            str(report_paths.get("summary_md", "")),
        )
        emitter.complete_step("step06", t_step06)

        iter_summary = _summarize_iteration(
            iteration,
            run_id,
            hypothesis,
            objective_mode,
            selected,
            report_paths,
            getattr(critic_analysis, "hypothesis", "") or "" or "",
        )
        iterations_out.append(
            {"summary": iter_summary.__dict__, "candidates": [candidate_to_dict(c) for c in candidates]}
        )
        _conv_flag, _ = convergence_detector.is_converged() if selected else (False, {})
        emitter.add_convergence_point(
            iteration=iteration,
            best_ddg=min((c.ddg for c in selected), default=0.0),
            top_candidates=len(selected),
            converged=_conv_flag,
        )
        final_selected = selected

        # Update running best candidate after each iteration
        if final_selected:
            iter_best = min(final_selected, key=lambda x: x.ddg)
            emitter.set_best_candidate(
                {
                    "id": iter_best.candidate_id,
                    "sequence": iter_best.sequence,
                    "ddG": round(iter_best.ddg, 3),
                    "totalScore": round(iter_best.total_score, 3),
                }
            )

    # -- Optional: multi-trial validation for final candidates --
    validation_stats: Dict[str, Any] = {}
    if config.validation_n_trials > 1 and final_selected:
        print(
            f"\n{'='*60}\n"
            f"  Multi-trial validation: {config.validation_n_trials} trials × "
            f"{len(final_selected)} candidates\n"
            f"{'='*60}",
            file=sys.stderr,
        )
        emitter.append_timeline_event(
            config.max_iterations, "validation", "running",
            f"Running {config.validation_n_trials}-trial validation for {len(final_selected)} candidates",
        )
        for cand in final_selected:
            trial_ddgs: List[float] = [cand.ddg]  # trial 0 = existing result
            cand_pdb = flow_dir / f"iter_{cand.iteration:02d}" / f"cand_{int(cand.candidate_id.split('cand')[1]):03d}.pdb"

            def _run_validation_trial(trial_idx: int) -> float:
                try:
                    result = _run_script(
                        flexpep_script,
                        [
                            "--input", config.template_pdb,
                            "--output", str(cand_pdb.with_suffix(f".val{trial_idx}.pdb")),
                            "--protocol", "flexpep_refine",
                            "--reference-complex", config.template_pdb,
                            "--target-sequence", cand.sequence,
                            "--peptide-chain", str(config.peptide_chain),
                        ],
                        config.conda_env,
                        repo_root,
                        timeout=config.script_timeout,
                    )
                    return float(result.get("ddg", 999.0))
                except Exception:
                    return 999.0

            remaining_trials = config.validation_n_trials - 1
            workers = min(remaining_trials, config.validation_max_workers, os.cpu_count() or 4)
            early_stopped = False

            with ThreadPoolExecutor(max_workers=workers) as pool:
                # Submit trials in batches to allow early stopping
                batch_size = max(workers, 4)
                trial_idx = 1
                while trial_idx <= remaining_trials:
                    batch_end = min(trial_idx + batch_size, remaining_trials + 1)
                    futures = {
                        pool.submit(_run_validation_trial, t): t
                        for t in range(trial_idx, batch_end)
                    }
                    for fut in as_completed(futures):
                        ddg = fut.result()
                        if ddg < 900:  # filter catastrophic failures
                            trial_ddgs.append(ddg)
                    trial_idx = batch_end

                    # Early stopping: check CV after ≥5 valid trials
                    if (
                        config.validation_early_stop_cv > 0
                        and len(trial_ddgs) >= 5
                    ):
                        sane = [d for d in trial_ddgs if d <= 0]
                        if len(sane) >= 4:
                            cv = abs(statistics.stdev(sane) / statistics.mean(sane)) if statistics.mean(sane) != 0 else 999
                            if cv < config.validation_early_stop_cv:
                                early_stopped = True
                                break

            # Compute stats from sane trials (ddG ≤ 0)
            sane_ddgs = sorted([d for d in trial_ddgs if d <= 0])
            if not sane_ddgs:
                sane_ddgs = sorted(trial_ddgs)  # fallback
            top3_mean = statistics.mean(sane_ddgs[:3]) if len(sane_ddgs) >= 3 else statistics.mean(sane_ddgs)
            cand_stats = {
                "n_trials": len(trial_ddgs),
                "n_sane": len(sane_ddgs),
                "top3_mean": round(top3_mean, 4),
                "median": round(statistics.median(sane_ddgs), 4),
                "mean": round(statistics.mean(sane_ddgs), 4),
                "stdev": round(statistics.stdev(sane_ddgs), 4) if len(sane_ddgs) > 1 else 0.0,
                "best": round(min(sane_ddgs), 4),
                "early_stopped": early_stopped,
            }
            validation_stats[cand.candidate_id] = cand_stats
            # Update candidate ddG to top-3 mean for downstream ranking
            cand.ddg = top3_mean
            es_tag = " [early-stop]" if early_stopped else ""
            print(
                f"  {cand.candidate_id}: top3_mean={top3_mean:.2f} "
                f"stdev={cand_stats['stdev']:.2f} "
                f"({cand_stats['n_sane']}/{cand_stats['n_trials']} ok){es_tag}",
                file=sys.stderr,
            )

        emitter.append_timeline_event(
            config.max_iterations, "validation", "completed",
            f"Validation complete: {len(validation_stats)} candidates validated",
        )

    # ------------------------------------------------------------------
    # 최종 단계: 선택성(off-target SSTR1/3/4/5 실제 도킹) — config-gated, 비쌈
    #   top-K 후보를 SSTR2 정렬 큐레이션 수용체에 transplant+relax+dock 하여
    #   selectivity_margin = min(offtarget_ddg) - sstr2_ddg 산출 (양수=SSTR2 선택적).
    # ------------------------------------------------------------------
    if getattr(config, "enable_selectivity", False) and final_selected:
        try:
            from .multiobjective import screen_selectivity
            sel_k = getattr(config, "selectivity_top_k", 3)
            sel_targets = sorted(final_selected, key=lambda c: c.ddg)[:sel_k]
            print(f"  [selectivity] off-target screening for top-{len(sel_targets)} candidates",
                  file=sys.stderr)
            emitter.append_timeline_event(
                config.max_iterations, "selectivity", "running",
                f"Off-target docking (SSTR1/3/4/5) for top-{len(sel_targets)}",
            )
            for cand in sel_targets:
                try:
                    cid = cand.candidate_id
                    pdb = str(flow_dir / f"iter_{cand.iteration:02d}" /
                              f"cand_{int(cid.split('cand')[1]):03d}.pdb") if "cand" in cid else None
                    if not pdb or not Path(pdb).exists():
                        continue
                    sel = screen_selectivity(
                        sstr2_complex_pdb=pdb,
                        on_target_ddg=cand.ddg,
                        conda_env=config.conda_env,
                        timeout=config.script_timeout,
                    )
                    if sel.get("selectivity_margin") is not None:
                        cand.extra_scores["selectivity_margin"] = sel["selectivity_margin"]
                        cand.extra_scores["offtarget_ddg"] = sel.get("offtarget_ddg")
                        print(f"  [selectivity] {cand.sequence}: margin={sel['selectivity_margin']:.2f} "
                              f"(off-target {sel.get('offtarget_ddg')})", file=sys.stderr)
                except Exception as _se:
                    print(f"  [selectivity] {cand.candidate_id} failed (non-fatal): {_se}",
                          file=sys.stderr)
            emitter.append_timeline_event(
                config.max_iterations, "selectivity", "completed",
                "Off-target selectivity screening complete",
            )
        except Exception as exc:
            print(f"  [selectivity] stage failed (non-fatal): {exc}", file=sys.stderr)

    summary = {
        "mode": "agentic_mutate_then_dock",
        "objective_mode_requested": config.objective_mode,
        "iterations": config.max_iterations,
        "best_final_ddg": min((c.ddg for c in final_selected), default=0.0),
        "run_status": run_status,
        "failure_stage": run_failure_stage,
        "error_summary": run_error_summary,
        "validation_stats": validation_stats if validation_stats else None,
    }
    if run_status == "failed":
        run_records.append(
            {
                "record_type": "candidate",
                "status": "failed",
                "run_id": run_id,
                "iteration": int(summary["iterations"]),
                "candidate_id": f"{run_id}_failed",
                "sequence": config.original_sequence,
                "ddg": 999.0,
                "clash": 999.0,
                "selected": False,
                "plddt": 0.0,
                "dock_score": 0.0,
                "lddt": 0.0,
                "selectivity": 0.0,
                "final_score": -999.0,
                "error_summary": run_error_summary or run_failure_stage or "run failed",
                "failure_stage": run_failure_stage or "unknown",
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        )
    append_experiment_records(exp_log_path, run_records)
    historical = build_historical_candidates(load_experiment_records(exp_log_path))
    emitter.set_historical_candidates(historical)
    if final_selected:
        best = min(final_selected, key=lambda x: x.ddg)
        emitter.set_best_candidate(
            {
                "id": best.candidate_id,
                "sequence": best.sequence,
                "ddG": round(best.ddg, 3),
                "totalScore": round(best.total_score, 3),
            }
        )
    # -- Optional: generate PyMOL visualization renders --
    try:
        if final_selected:
            viz_dir = flow_dir / "renders"
            top_pdbs = [
                str(flow_dir / f"iter_{c.iteration:02d}" / f"cand_{int(c.candidate_id.split('cand')[1]):03d}.pdb")
                for c in sorted(final_selected, key=lambda x: x.ddg)[:3]
            ]
            render_paths = generate_pymol_renders(
                top_candidates=top_pdbs,
                receptor_pdb=config.template_pdb,
                output_dir=viz_dir,
            )
            if render_paths:
                view_labels = {
                    "overview": "Overview",
                    "closeup": "Close-up",
                    "interface": "Interface",
                    "electrostatics": "Electrostatics",
                }
                viz_images = [
                    {
                        "type": view,
                        "label": view_labels.get(view, view),
                        "url": f"/api/images/{Path(png_path).relative_to(repo_root / 'runs')}",
                    }
                    for view, png_path in render_paths.items()
                ]
                emitter.set_visualization_images(viz_images)
    except Exception as viz_exc:
        print(f"  [viz] PyMOL render skipped: {viz_exc}", file=sys.stderr)

    emitter.set_completed()

    artifacts = FlowArtifacts.from_parts(
        run_id=run_id,
        config=config,
        notebook_mapping=notebook_mapping(),
        baseline=baseline,
        iterations=iterations_out,
        final_candidates=[candidate_to_dict(c) for c in final_selected],
        summary=summary,
    )

    # 무한 엔진: 이번 run 의 선택성 측정을 글로벌 리더보드에 누적·영속 (다음 epoch warm-start 용)
    if _global_lb is not None:
        try:
            ing = _global_lb.ingest_artifacts(artifacts.to_dict())
            _global_lb.save(_global_lb_path)
            print(f"  [global-lb] +{ing['n_measurements']} 측정, 역대 best Δ={ing['best_delta_margin']}, "
                  f"unique={ing['n_unique']}, improved={ing['improved_best']}", file=sys.stderr)
        except Exception as exc:
            print(f"  [global-lb] 영속 실패(non-fatal): {exc}", file=sys.stderr)

    return artifacts


def run_pyrosetta_notebook_flow(config: FlowConfig) -> FlowArtifacts:
    """Backward compatibility wrapper."""
    return run_pyrosetta_agentic_mutdock_flow(config)
