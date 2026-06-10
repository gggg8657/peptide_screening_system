"""Tests for ranking.py: JSONL I/O, historical candidate aggregation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from pyrosetta_flow.ranking import (
    append_experiment_records,
    build_historical_candidates,
    extract_historical_sequences,
    load_experiment_records,
    summarize_top_hits,
)


# ===================================================================
# load_experiment_records tests  (Critical priority #3)
# ===================================================================

class TestLoadExperimentRecords:

    def test_missing_file(self, tmp_path):
        result = load_experiment_records(tmp_path / "nonexistent.jsonl")
        assert result == []

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert load_experiment_records(f) == []

    def test_valid_records(self, tmp_path):
        f = tmp_path / "log.jsonl"
        records = [
            {"record_type": "candidate", "sequence": "AAA", "ddg": -5.0},
            {"record_type": "candidate", "sequence": "BBB", "ddg": -10.0},
        ]
        f.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        loaded = load_experiment_records(f)
        assert len(loaded) == 2
        assert loaded[0]["sequence"] == "AAA"

    def test_malformed_json_tolerance(self, tmp_path):
        """Malformed lines should be silently skipped."""
        f = tmp_path / "log.jsonl"
        content = (
            '{"sequence": "AAA", "ddg": -5.0}\n'
            "THIS IS NOT JSON\n"
            '{"sequence": "BBB", "ddg": -10.0}\n'
        )
        f.write_text(content)
        loaded = load_experiment_records(f)
        assert len(loaded) == 2

    def test_blank_lines_skipped(self, tmp_path):
        f = tmp_path / "log.jsonl"
        content = (
            '{"a": 1}\n'
            "\n"
            "   \n"
            '{"b": 2}\n'
        )
        f.write_text(content)
        loaded = load_experiment_records(f)
        assert len(loaded) == 2


# ===================================================================
# append_experiment_records tests
# ===================================================================

class TestAppendExperimentRecords:

    def test_append_creates_file(self, tmp_path):
        f = tmp_path / "new_dir" / "log.jsonl"
        records = [{"seq": "AAA"}]
        append_experiment_records(f, records)
        assert f.exists()
        loaded = load_experiment_records(f)
        assert len(loaded) == 1

    def test_append_to_existing(self, tmp_path):
        f = tmp_path / "log.jsonl"
        append_experiment_records(f, [{"a": 1}])
        append_experiment_records(f, [{"b": 2}])
        loaded = load_experiment_records(f)
        assert len(loaded) == 2

    def test_append_empty_records(self, tmp_path):
        f = tmp_path / "log.jsonl"
        append_experiment_records(f, [])
        assert not f.exists()


# ===================================================================
# extract_historical_sequences tests
# ===================================================================

class TestExtractHistoricalSequences:

    def test_extract(self, sample_experiment_records):
        seqs = extract_historical_sequences(sample_experiment_records)
        assert isinstance(seqs, set)
        # All 4 candidate records have sequences
        assert len(seqs) == 4

    def test_non_candidate_records_ignored(self):
        records = [
            {"record_type": "summary", "sequence": "SHOULD_IGNORE"},
            {"record_type": "candidate", "sequence": "KEEP_ME"},
        ]
        seqs = extract_historical_sequences(records)
        assert seqs == {"KEEP_ME"}

    def test_empty_records(self):
        assert extract_historical_sequences([]) == set()


# ===================================================================
# summarize_top_hits tests  (Medium priority #10)
# ===================================================================

class TestSummarizeTopHits:

    def test_basic_top_hits(self, sample_experiment_records):
        hits = summarize_top_hits(sample_experiment_records, top_n=10)
        # Only records with status=success AND ddg < 0 qualify
        assert len(hits) == 2  # cand001 (ddg=-5.0), cand002 (ddg=-12.3)
        # Sorted by ddg ascending
        assert hits[0]["ddg"] <= hits[1]["ddg"]

    def test_top_n_limit(self, sample_experiment_records):
        hits = summarize_top_hits(sample_experiment_records, top_n=1)
        assert len(hits) == 1
        assert hits[0]["ddg"] == -12.3

    def test_no_successful_candidates(self):
        records = [
            {"record_type": "candidate", "status": "failed", "ddg": 999.0, "sequence": "X"},
        ]
        assert summarize_top_hits(records) == []

    def test_positive_ddg_excluded(self):
        records = [
            {"record_type": "candidate", "status": "success", "ddg": 5.0, "sequence": "X"},
        ]
        assert summarize_top_hits(records) == []


# ===================================================================
# build_historical_candidates tests  (Medium priority #10)
# ===================================================================

class TestBuildHistoricalCandidates:

    def test_basic_ranking(self, sample_experiment_records):
        result = build_historical_candidates(sample_experiment_records)
        assert len(result) == 4
        # rank 1 should be the best successful candidate
        assert result[0]["rank"] == 1
        assert result[0]["ddG"] == -12.3  # best ddg

    def test_success_before_failure(self, sample_experiment_records):
        result = build_historical_candidates(sample_experiment_records)
        # Successful candidates should rank before failed ones
        results = [r["result"] for r in result]
        # Find first FAIL index
        first_fail = results.index("FAIL") if "FAIL" in results else len(results)
        # All before first_fail should be PASS
        for i in range(first_fail):
            assert results[i] == "PASS"

    def test_limit(self, sample_experiment_records):
        result = build_historical_candidates(sample_experiment_records, limit=2)
        assert len(result) == 2

    def test_empty_records(self):
        assert build_historical_candidates([]) == []

    def test_final_score_calculation(self):
        records = [
            {
                "record_type": "candidate",
                "status": "success",
                "ddg": -10.0,
                "total_score": -100.0,
                "clash_score": 1.0,
                "candidate_id": "c1",
                "sequence": "AAA",
            },
        ]
        result = build_historical_candidates(records)
        assert result[0]["finalScore"] == round(10.0, 3)

    def test_positive_ddg_gets_zero_final_score(self):
        records = [
            {
                "record_type": "candidate",
                "status": "success",
                "ddg": 5.0,
                "total_score": -50.0,
                "clash_score": 2.0,
                "candidate_id": "c1",
                "sequence": "BBB",
            },
        ]
        result = build_historical_candidates(records)
        assert result[0]["finalScore"] == 0.0
