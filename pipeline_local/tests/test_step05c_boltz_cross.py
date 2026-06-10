"""
test_step05c_boltz_cross.py
============================
Step 05c: Boltz-2 selectivity cross-validation 단위 테스트

테스트 목록:
  1. classify_tier — Tier 분류 경계값 검증
  2. compute_selectivity_margin — margin 및 best_receptor 산출
  3. tier delta redesign — Δ-기반 tier 회귀 검증
  4. _safe_id — 경로 안전 문자 검사
  5. BoltzSelectivityResult / Step05cOutput — 직렬화 라운드트립
  6. predict_pair mock — subprocess 호출·confidence 파싱 통합
  7. run_boltz_cross_validation mock — 전체 파이프라인 (subprocess 차단)
  8. _parse_confidence — 실제 파일 생성 후 iPTM 파싱
  9. download_alphafold_msa stub — 네트워크 없이 캐시 경로 반환
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from pipeline_local.schemas.io_schemas import (
    BoltzSelectivityResult,
    DockingResult,
    Step05cOutput,
)
from pipeline_local.steps.step05c_boltz_cross import (
    _parse_confidence,
    _safe_id,
    classify_tier,
    compute_selectivity_margin,
    DEFAULT_TIER_THRESHOLDS,
    download_alphafold_msa,
    predict_pair,
    run_boltz_cross_validation,
    SSTR_SEQUENCES,
    UNIPROT_MAP,
)


# ===========================================================================
# 1. classify_tier
# ===========================================================================

class TestClassifyTier:
    def test_t3_boundary(self):
        assert classify_tier(0.03) == "T3"

    def test_t3_above(self):
        assert classify_tier(0.10) == "T3"

    def test_t2_boundary(self):
        assert classify_tier(0.00) == "T2"

    def test_t2_below_t3(self):
        assert classify_tier(0.02) == "T2"

    def test_t1_boundary(self):
        assert classify_tier(-0.03) == "T1"

    def test_t1_inside(self):
        assert classify_tier(-0.01) == "T1"

    def test_t0_below(self):
        assert classify_tier(-0.04) == "T0"

    def test_t0_deep(self):
        assert classify_tier(-0.50) == "T0"

    def test_custom_thresholds(self):
        custom = {"T3": 0.10, "T2": 0.05, "T1": 0.00}
        assert classify_tier(0.11, custom) == "T3"
        assert classify_tier(0.07, custom) == "T2"
        assert classify_tier(0.02, custom) == "T1"
        assert classify_tier(-0.01, custom) == "T0"


# ===========================================================================
# 2. compute_selectivity_margin
# ===========================================================================

class TestComputeSelectivityMargin:
    def test_basic_margin(self):
        margin, best = compute_selectivity_margin(
            sstr2_iptm=0.95,
            offtarget_iptm={"SSTR1": 0.90, "SSTR3": 0.85},
        )
        assert abs(margin - 0.05) < 1e-9
        assert best == "SSTR1"

    def test_negative_margin(self):
        margin, best = compute_selectivity_margin(
            sstr2_iptm=0.80,
            offtarget_iptm={"SSTR1": 0.90},
        )
        assert abs(margin - (-0.10)) < 1e-9
        assert best == "SSTR1"

    def test_empty_offtarget(self):
        margin, best = compute_selectivity_margin(
            sstr2_iptm=0.90,
            offtarget_iptm={},
        )
        assert margin == 0.0
        assert best == "none"

    def test_all_receptors(self):
        offtarget = {
            "SSTR1": 0.975,
            "SSTR3": 0.958,
            "SSTR4": 0.956,
            "SSTR5": 0.913,
        }
        sstr2_iptm = 0.946
        margin, best = compute_selectivity_margin(sstr2_iptm, offtarget)
        # SSTR1이 가장 높음 → margin = 0.946 - 0.975 = -0.029
        assert abs(margin - (0.946 - 0.975)) < 1e-6
        assert best == "SSTR1"
        assert classify_tier(margin) == "T1"  # -0.03 ≤ margin < 0.0


# ===========================================================================
# 3. tier delta redesign
# ===========================================================================

class TestTierDeltaRedesign:
    def test_sst14_wild_measured_maps_to_t1(self):
        margin, best = compute_selectivity_margin(
            sstr2_iptm=0.946,
            offtarget_iptm={
                "SSTR1": 0.975,
                "SSTR3": 0.958,
                "SSTR4": 0.956,
                "SSTR5": 0.913,
            },
        )
        assert margin == pytest.approx(-0.029, abs=1e-9)
        assert best == "SSTR1"
        assert classify_tier(margin) == "T1"

    def test_clear_sstr2_selective_maps_to_t3(self):
        margin, best = compute_selectivity_margin(
            sstr2_iptm=0.98,
            offtarget_iptm={
                "SSTR1": 0.93,
                "SSTR3": 0.92,
                "SSTR4": 0.91,
                "SSTR5": 0.90,
            },
        )
        assert margin == pytest.approx(0.05, abs=1e-9)
        assert best == "SSTR1"
        assert classify_tier(margin) == "T3"

    def test_boundary_values(self):
        assert classify_tier(0.03) == "T3"
        assert classify_tier(0.029) == "T2"
        assert classify_tier(0.0) == "T2"
        assert classify_tier(-0.001) == "T1"

    def test_equal_iptm_values_map_to_t2(self):
        margin, best = compute_selectivity_margin(
            sstr2_iptm=0.95,
            offtarget_iptm={
                "SSTR1": 0.95,
                "SSTR3": 0.95,
                "SSTR4": 0.95,
                "SSTR5": 0.95,
            },
        )
        assert margin == pytest.approx(0.0, abs=1e-9)
        assert best == "SSTR1"
        assert classify_tier(margin) == "T2"

    def test_extreme_offtarget_dominance_maps_to_t0(self):
        margin, best = compute_selectivity_margin(
            sstr2_iptm=0.70,
            offtarget_iptm={
                "SSTR1": 0.95,
                "SSTR3": 0.94,
                "SSTR4": 0.93,
                "SSTR5": 0.92,
            },
        )
        assert margin == pytest.approx(-0.25, abs=1e-9)
        assert best == "SSTR1"
        assert classify_tier(margin) == "T0"


# ===========================================================================
# 4. _safe_id
# ===========================================================================

class TestSafeId:
    def test_valid(self):
        assert _safe_id("bb00_seq01") == "bb00_seq01"
        assert _safe_id("SSTR2") == "SSTR2"
        assert _safe_id("cand-01.v2") == "cand-01.v2"

    def test_invalid_slash(self):
        with pytest.raises(ValueError):
            _safe_id("bb00/seq01")

    def test_invalid_space(self):
        with pytest.raises(ValueError):
            _safe_id("bb 00")

    def test_invalid_semicolon(self):
        with pytest.raises(ValueError):
            _safe_id("seq;id")


# ===========================================================================
# 5. BoltzSelectivityResult / Step05cOutput 직렬화 라운드트립
# ===========================================================================

class TestSchemaSerialisation:
    def _make_result(self, tier: str = "T2") -> BoltzSelectivityResult:
        return BoltzSelectivityResult(
            seq_id="bb00_seq00",
            sequence="AGCKNFFWKTFTSC",
            sstr2_iptm=0.946,
            offtarget_iptm={"SSTR1": 0.975, "SSTR3": 0.958},
            selectivity_margin=-0.029,
            best_receptor="SSTR1",
            tier=tier,
        )

    def test_boltz_result_roundtrip(self):
        r = self._make_result()
        d = r.to_dict()
        r2 = BoltzSelectivityResult.from_dict(d)
        assert r2.seq_id == r.seq_id
        assert r2.tier == r.tier
        assert abs(r2.sstr2_iptm - r.sstr2_iptm) < 1e-9
        assert r2.offtarget_iptm == r.offtarget_iptm

    def test_step05c_output_roundtrip(self):
        r = self._make_result("T3")
        output = Step05cOutput(
            results=[r],
            passed_candidates=[r],
            n_total=1,
            n_passed=1,
        )
        d = output.to_dict()
        output2 = Step05cOutput.from_dict(d)
        assert output2.n_total == 1
        assert output2.n_passed == 1
        assert output2.results[0].tier == "T3"

    def test_get_tier_method(self):
        r_t3 = self._make_result("T3")
        r_t2 = self._make_result("T2")
        output = Step05cOutput(
            results=[r_t3, r_t2],
            passed_candidates=[r_t3, r_t2],
            n_total=2,
            n_passed=2,
        )
        assert len(output.get_tier("T3")) == 1
        assert len(output.get_tier("T2")) == 1
        assert len(output.get_tier("T0")) == 0


# ===========================================================================
# 6. _parse_confidence — 실제 파일 생성 후 파싱
# ===========================================================================

class TestParseConfidence:
    def test_known_path_pattern(self, tmp_path: Path):
        pair_id = "bb00_seq00__SSTR2"
        conf_dir = (
            tmp_path
            / f"boltz_results_{pair_id}"
            / "predictions"
            / pair_id
        )
        conf_dir.mkdir(parents=True)
        conf_file = conf_dir / f"confidence_{pair_id}_model_0.json"
        conf_file.write_text(
            json.dumps({"iptm": 0.954, "ptm": 0.869, "confidence_score": 0.859}),
            encoding="utf-8",
        )
        result = _parse_confidence(tmp_path, pair_id)
        assert result is not None
        assert abs(result - 0.954) < 1e-6

    def test_rglob_fallback(self, tmp_path: Path):
        nested = tmp_path / "some" / "nested" / "dir"
        nested.mkdir(parents=True)
        conf_file = nested / "confidence_other_model_0.json"
        conf_file.write_text(
            json.dumps({"iptm": 0.800}), encoding="utf-8"
        )
        result = _parse_confidence(tmp_path, "bb00_seq00__SSTR1")
        assert result is not None
        assert abs(result - 0.800) < 1e-6

    def test_pair_chains_iptm_fallback(self, tmp_path: Path):
        pair_id = "bb01_seq01__SSTR3"
        conf_dir = (
            tmp_path
            / f"boltz_results_{pair_id}"
            / "predictions"
            / pair_id
        )
        conf_dir.mkdir(parents=True)
        conf_file = conf_dir / f"confidence_{pair_id}_model_0.json"
        # iptm 키 없이 pair_chains_iptm만 있는 경우
        conf_file.write_text(
            json.dumps({"pair_chains_iptm": {"0": {"1": 0.750}}}),
            encoding="utf-8",
        )
        result = _parse_confidence(tmp_path, pair_id)
        assert result is not None
        assert abs(result - 0.750) < 1e-6

    def test_no_confidence_file(self, tmp_path: Path):
        result = _parse_confidence(tmp_path, "nonexistent__SSTR2")
        assert result is None


# ===========================================================================
# 7. download_alphafold_msa — 캐시 파일 존재 시 재다운로드 스킵
# ===========================================================================

class TestDownloadAlphafoldMsa:
    def test_cache_hit(self, tmp_path: Path):
        uniprot = "P30874"
        dest = tmp_path / f"AF-{uniprot}-F1-msa.a3m"
        # 더미 파일 (>1000 bytes) 생성
        dest.write_bytes(b"A" * 2000)
        result = download_alphafold_msa(uniprot, tmp_path)
        assert result == dest

    def test_missing_file_tries_network(self, tmp_path: Path):
        """네트워크 없이 실패해도 None 반환, 예외 없음을 보장."""
        with patch("urllib.request.urlopen", side_effect=OSError("no network")):
            result = download_alphafold_msa("P99999", tmp_path, timeout=1)
        assert result is None


# ===========================================================================
# 8. predict_pair — subprocess mock
# ===========================================================================

class TestPredictPair:
    def _make_conf_file(self, out_dir: Path, pair_id: str, iptm: float):
        conf_dir = (
            out_dir
            / f"boltz_results_{pair_id}"
            / "predictions"
            / pair_id
        )
        conf_dir.mkdir(parents=True)
        (conf_dir / f"confidence_{pair_id}_model_0.json").write_text(
            json.dumps({"iptm": iptm}), encoding="utf-8"
        )

    def test_success(self, tmp_path: Path):
        pair_id = "sst14__SSTR2"

        def fake_run(cmd, **kwargs):
            # out_dir 파싱
            out_dir_idx = cmd.index("--out_dir") + 1
            out_dir = Path(cmd[out_dir_idx])
            self._make_conf_file(out_dir, pair_id, 0.954)
            return MagicMock(returncode=0, stdout="", stderr="")

        # 수용체 MSA 더미 파일 생성
        rec_msa = tmp_path / "AF-P30874-F1-msa.a3m"
        rec_msa.write_bytes(b"A" * 2000)

        with patch("subprocess.run", side_effect=fake_run):
            result = predict_pair(
                seq_id="sst14",
                sequence="AGCKNFFWKTFTSC",
                receptor_name="SSTR2",
                receptor_seq=SSTR_SEQUENCES["SSTR2"],
                receptor_msa_path=rec_msa,
                work_dir=tmp_path,
                boltz_env="boltz",
                cuda_device=3,
                pair_timeout=600,
            )
        assert result is not None
        assert abs(result - 0.954) < 1e-6

    def test_timeout(self, tmp_path: Path):
        import subprocess as _sp
        rec_msa = tmp_path / "AF-P30874-F1-msa.a3m"
        rec_msa.write_bytes(b"A" * 2000)

        with patch("subprocess.run", side_effect=_sp.TimeoutExpired("cmd", 600)):
            result = predict_pair(
                seq_id="sst14",
                sequence="AGCKNFFWKTFTSC",
                receptor_name="SSTR2",
                receptor_seq=SSTR_SEQUENCES["SSTR2"],
                receptor_msa_path=rec_msa,
                work_dir=tmp_path,
                boltz_env="boltz",
                cuda_device=3,
                pair_timeout=600,
            )
        assert result is None

    def test_nonzero_returncode(self, tmp_path: Path):
        rec_msa = tmp_path / "AF-P30874-F1-msa.a3m"
        rec_msa.write_bytes(b"A" * 2000)

        with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="", stderr="error")):
            result = predict_pair(
                seq_id="sst14",
                sequence="AGCKNFFWKTFTSC",
                receptor_name="SSTR2",
                receptor_seq=SSTR_SEQUENCES["SSTR2"],
                receptor_msa_path=rec_msa,
                work_dir=tmp_path,
                boltz_env="boltz",
                cuda_device=3,
                pair_timeout=600,
            )
        assert result is None


# ===========================================================================
# 9. run_boltz_cross_validation — 전체 파이프라인 (predict_pair mock)
# ===========================================================================

class TestRunBoltzCrossValidation:
    """predict_pair 를 mock하여 subprocess 없이 전체 흐름 검증."""

    def _make_candidate(self, seq_id: str, sequence: str) -> DockingResult:
        return DockingResult(
            seq_id=seq_id,
            engine="boltz2",
            score=-5.0,
            confidence=0.9,
            pose_pdb="",
            rank=1,
        )

    def test_sst14_sstr2_single_pair_iptm_gte_09(self, tmp_path: Path):
        """SST-14 wild × SSTR2 단일 페어: mock iPTM ≥ 0.9 확인."""
        # DockingResult에 sequence 속성이 없으므로 patch로 주입
        candidate = self._make_candidate("sst14_wild", "AGCKNFFWKTFTSC")
        # sequence attribute 동적 주입
        candidate.__dict__["sequence"] = "AGCKNFFWKTFTSC"

        # predict_pair 호출 시 SSTR2=0.946, off-targets=0.90
        def mock_predict(seq_id, sequence, receptor_name, receptor_seq,
                         receptor_msa_path, work_dir, boltz_env, cuda_device, pair_timeout):
            iptm_map = {
                "SSTR1": 0.900, "SSTR2": 0.946,
                "SSTR3": 0.890, "SSTR4": 0.880, "SSTR5": 0.870,
            }
            return iptm_map.get(receptor_name, 0.85)

        sstr2_rec = {"name": "SSTR2", "uniprot": "P30874"}
        offtarget_recs = [
            {"name": "SSTR1", "uniprot": "P30872"},
            {"name": "SSTR3", "uniprot": "P32745"},
            {"name": "SSTR4", "uniprot": "P31391"},
            {"name": "SSTR5", "uniprot": "P35346"},
        ]
        config = {
            "alphafold_msa_dir": str(tmp_path / "msa"),
            "boltz_env": "boltz",
            "cuda_device": 3,
            "work_dir": str(tmp_path / "step05c"),
        }

        with patch(
            "pipeline_local.steps.step05c_boltz_cross._ensure_receptor_msa",
            side_effect=lambda uniprot_id, receptor_name, af_msa_dir: tmp_path / f"fake_{receptor_name}.a3m",
        ), patch(
            "pipeline_local.steps.step05c_boltz_cross.predict_pair",
            side_effect=mock_predict,
        ):
            output = run_boltz_cross_validation(
                candidates=[candidate],
                offtarget_receptors=offtarget_recs,
                sstr2_receptor=sstr2_rec,
                config=config,
            )

        assert output.n_total == 1
        result = output.results[0]
        assert result.sstr2_iptm >= 0.9, f"iPTM {result.sstr2_iptm} < 0.9"
        assert result.tier in ("T2", "T3"), f"예상치 못한 Tier: {result.tier}"

    def test_passed_candidates_filter(self, tmp_path: Path):
        """T0 후보는 passed_candidates에서 제외됨."""
        c1 = self._make_candidate("seq_t3", "AGCKNFFWKTFTSC")
        c2 = self._make_candidate("seq_t0", "AAAAAAAAAAAAA")
        c1.__dict__["sequence"] = "AGCKNFFWKTFTSC"
        c2.__dict__["sequence"] = "AAAAAAAAAAAAA"

        def mock_predict(seq_id, sequence, receptor_name, **kwargs):
            if seq_id == "seq_t3" and receptor_name == "SSTR2":
                return 0.98
            if seq_id == "seq_t3":
                return 0.90
            if seq_id == "seq_t0" and receptor_name == "SSTR2":
                return 0.70
            return 0.90  # seq_t0 off-target 높음 → negative margin

        sstr2_rec = {"name": "SSTR2", "uniprot": "P30874"}
        offtargets = [{"name": "SSTR1", "uniprot": "P30872"}]
        config = {
            "alphafold_msa_dir": str(tmp_path / "msa"),
            "work_dir": str(tmp_path / "step05c"),
        }

        with patch(
            "pipeline_local.steps.step05c_boltz_cross._ensure_receptor_msa",
            return_value=tmp_path / "fake.a3m",
        ), patch(
            "pipeline_local.steps.step05c_boltz_cross.predict_pair",
            side_effect=mock_predict,
        ):
            output = run_boltz_cross_validation(
                candidates=[c1, c2],
                offtarget_receptors=offtargets,
                sstr2_receptor=sstr2_rec,
                config=config,
            )

        assert output.n_total == 2
        # seq_t3: margin=0.08 → T3 (passed)
        # seq_t0: margin=-0.20 → T0 (failed)
        assert output.n_passed == 1
        assert output.passed_candidates[0].seq_id == "seq_t3"

    def test_checkpoint_created(self, tmp_path: Path):
        """checkpoint 파일이 생성되는지 확인."""
        c = self._make_candidate("sst14", "AGCKNFFWKTFTSC")
        c.__dict__["sequence"] = "AGCKNFFWKTFTSC"

        with patch(
            "pipeline_local.steps.step05c_boltz_cross._ensure_receptor_msa",
            return_value=tmp_path / "fake.a3m",
        ), patch(
            "pipeline_local.steps.step05c_boltz_cross.predict_pair",
            return_value=0.95,
        ):
            run_boltz_cross_validation(
                candidates=[c],
                offtarget_receptors=[{"name": "SSTR1", "uniprot": "P30872"}],
                sstr2_receptor={"name": "SSTR2", "uniprot": "P30874"},
                config={
                    "alphafold_msa_dir": str(tmp_path / "msa"),
                    "work_dir": str(tmp_path / "step05c"),
                },
            )

        cp = tmp_path / "step05c" / "partial_results.json"
        assert cp.exists(), "partial_results.json 생성되지 않음"
        data = json.loads(cp.read_text())
        assert len(data) > 0


# ===========================================================================
# 9. 상수 검증
# ===========================================================================

class TestConstants:
    def test_uniprot_map_complete(self):
        for name in ["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"]:
            assert name in UNIPROT_MAP, f"{name} UniProt 누락"

    def test_sstr_sequences_present(self):
        for name in ["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"]:
            assert name in SSTR_SEQUENCES
            assert len(SSTR_SEQUENCES[name]) > 100, f"{name} 시퀀스 너무 짧음"

    def test_sstr2_sequence_known_start(self):
        """SSTR2 시퀀스가 알려진 N-terminus로 시작하는지 확인."""
        assert SSTR_SEQUENCES["SSTR2"].startswith("MDMADEPLNG")


# ===========================================================================
# 10. F-06 회귀: config.sequence_map fallback (Issue #17)
# ===========================================================================

class TestF06SequenceMapFallback:
    """DockingResult가 sequence 필드를 가지지 않을 때 config.sequence_map으로 fallback.

    배경 (PR #14 dogfood 2026-05-12):
      orchestrator.py가 candidates=step05_out.docking_results를 step05c에 전달하나,
      DockingResult dataclass에 sequence 필드 없음 → step05c가 모든 후보를 skip →
      0/0 Boltz cross-validation. Issue #17 등록.

    Fix: step05c가 config.get("sequence_map", {}).get(seq_id)를 fallback으로 사용.
    """

    def _make_candidate(self, seq_id: str) -> DockingResult:
        """sequence 필드 없는 DockingResult (실 orchestrator 경로 재현)."""
        return DockingResult(
            seq_id=seq_id, engine="boltz2", score=-5.0,
            confidence=0.9, pose_pdb="", rank=1,
        )

    def test_sequence_map_fallback_resolves(self, tmp_path: Path):
        """sequence 동적 주입 없이 config.sequence_map만으로 후보 처리 가능."""
        candidate = self._make_candidate("var_026")
        # F-06 fix 이전이라면 여기서 candidate.__dict__["sequence"] 주입 필요했음.
        # fix 후: sequence_map만으로 충분.

        sequence_map = {"var_026": "AGCKNFFWKTFTSC"}

        captured_sequences: List[str] = []

        def mock_predict(seq_id, sequence, receptor_name, **kwargs):
            captured_sequences.append(sequence)
            return 0.95

        with patch(
            "pipeline_local.steps.step05c_boltz_cross._ensure_receptor_msa",
            return_value=tmp_path / "fake.a3m",
        ), patch(
            "pipeline_local.steps.step05c_boltz_cross.predict_pair",
            side_effect=mock_predict,
        ):
            output = run_boltz_cross_validation(
                candidates=[candidate],
                offtarget_receptors=[{"name": "SSTR1", "uniprot": "P30872"}],
                sstr2_receptor={"name": "SSTR2", "uniprot": "P30874"},
                config={
                    "alphafold_msa_dir": str(tmp_path / "msa"),
                    "work_dir": str(tmp_path / "step05c"),
                    "sequence_map": sequence_map,
                },
            )

        assert output.n_total == 1, (
            "F-06 fix 실패: sequence_map fallback이 작동하지 않아 후보가 스킵됨"
        )
        assert "AGCKNFFWKTFTSC" in captured_sequences, (
            "F-06 fix 실패: predict_pair에 sequence_map의 sequence 전달 안 됨"
        )

    def test_no_sequence_no_map_skips_gracefully(self, tmp_path: Path):
        """sequence 필드도 없고 sequence_map에도 없으면 fail-soft skip (기존 행위)."""
        candidate = self._make_candidate("var_999")  # sequence_map에 없음
        with patch(
            "pipeline_local.steps.step05c_boltz_cross._ensure_receptor_msa",
            return_value=tmp_path / "fake.a3m",
        ), patch(
            "pipeline_local.steps.step05c_boltz_cross.predict_pair",
            return_value=0.95,
        ):
            output = run_boltz_cross_validation(
                candidates=[candidate],
                offtarget_receptors=[{"name": "SSTR1", "uniprot": "P30872"}],
                sstr2_receptor={"name": "SSTR2", "uniprot": "P30874"},
                config={
                    "alphafold_msa_dir": str(tmp_path / "msa"),
                    "work_dir": str(tmp_path / "step05c"),
                    "sequence_map": {"var_026": "AGCKNFFWKTFTSC"},  # var_999 부재
                },
            )

        assert output.n_total == 0, "sequence 없는 후보는 결과에 포함되면 안 됨"

    def test_candidate_sequence_takes_precedence(self, tmp_path: Path):
        """candidate에 sequence 명시되면 sequence_map보다 우선."""
        candidate = self._make_candidate("var_026")
        candidate.__dict__["sequence"] = "EXPLICITSEQ___"  # 명시적 주입

        captured: List[str] = []

        def mock_predict(seq_id, sequence, receptor_name, **kwargs):
            captured.append(sequence)
            return 0.95

        with patch(
            "pipeline_local.steps.step05c_boltz_cross._ensure_receptor_msa",
            return_value=tmp_path / "fake.a3m",
        ), patch(
            "pipeline_local.steps.step05c_boltz_cross.predict_pair",
            side_effect=mock_predict,
        ):
            run_boltz_cross_validation(
                candidates=[candidate],
                offtarget_receptors=[{"name": "SSTR1", "uniprot": "P30872"}],
                sstr2_receptor={"name": "SSTR2", "uniprot": "P30874"},
                config={
                    "alphafold_msa_dir": str(tmp_path / "msa"),
                    "work_dir": str(tmp_path / "step05c"),
                    "sequence_map": {"var_026": "AGCKNFFWKTFTSC"},
                },
            )

        assert "EXPLICITSEQ___" in captured, "candidate.sequence가 우선되지 않음"
        assert "AGCKNFFWKTFTSC" not in captured, "sequence_map이 candidate.sequence보다 우선됨"

    def test_no_sequence_map_in_config_is_safe(self, tmp_path: Path):
        """config에 sequence_map 키가 없어도 KeyError/AttributeError 없이 동작."""
        candidate = self._make_candidate("var_026")
        candidate.__dict__["sequence"] = "AGCKNFFWKTFTSC"

        with patch(
            "pipeline_local.steps.step05c_boltz_cross._ensure_receptor_msa",
            return_value=tmp_path / "fake.a3m",
        ), patch(
            "pipeline_local.steps.step05c_boltz_cross.predict_pair",
            return_value=0.95,
        ):
            output = run_boltz_cross_validation(
                candidates=[candidate],
                offtarget_receptors=[{"name": "SSTR1", "uniprot": "P30872"}],
                sstr2_receptor={"name": "SSTR2", "uniprot": "P30874"},
                config={
                    "alphafold_msa_dir": str(tmp_path / "msa"),
                    "work_dir": str(tmp_path / "step05c"),
                    # sequence_map 키 의도적으로 부재
                },
            )

        assert output.n_total == 1, "sequence_map 키 부재 시에도 안전하게 동작해야 함"

    def test_default_tier_thresholds(self):
        assert DEFAULT_TIER_THRESHOLDS["T3"] == 0.03
        assert DEFAULT_TIER_THRESHOLDS["T2"] == 0.00
        assert DEFAULT_TIER_THRESHOLDS["T1"] == -0.03
