"""
backend/tests/test_selectivity_pdb_index.py
=============================================
G-1 fix — _build_pdb_index candidate_id format mismatch 단위 테스트 (2026-05-20).

be-fe-trace 분석: FE 가 실제로 보내는 candidate_id 형식은 "iter04_cand004"
(iter prefix 포함, 4자리 zero-pad). 기존 코드는 "001"/"1"/"var001" 만 등록해
항상 estimation fallback 으로 빠졌음.

커버리지 항목:
  G-1. FE 형식 "iter04_cand004" → 인덱스 hit
  G-2. 기존 레거시 형식 "001", "1", "var001" → 여전히 hit (회귀)
  G-3. "cand001", "cand_001" 변형 → hit
  G-4. 존재하지 않는 cid "iter99_cand999" → miss (estimation fallback 트리거 확인)
  G-5. iter_01 / iter_02 복수 iter → 각각 다른 iter 키로 등록
  G-6. cand_007.val1.pdb 처럼 stem 에 점 포함 → "007" 정상 파싱
  G-7. 가장 최근(reverse sorted) run 만 사용 → 오래된 run 파일 무시
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ──────────────────────────────────────────────
# sys.path 설정
# ──────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # ai4sci-kaeri
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ──────────────────────────────────────────────
# 헬퍼: 가짜 runs 디렉토리 구조 생성
# ──────────────────────────────────────────────
def _make_run_structure(
    base: Path,
    run_name: str,
    iters: dict[str, list[str]],  # {"iter_04": ["cand_001.pdb", "cand_004.pdb"], ...}
    with_baseline: bool = True,
) -> Path:
    """runs_dir/run_name/sst14_agentic_mutdock/iter_XX/cand_YYY.pdb 구조 생성."""
    mutdock = base / run_name / "sst14_agentic_mutdock"
    for iter_name, pdb_files in iters.items():
        iter_dir = mutdock / iter_name
        iter_dir.mkdir(parents=True, exist_ok=True)
        for fname in pdb_files:
            (iter_dir / fname).write_text(f"ATOM dummy {fname}")
    if with_baseline:
        (mutdock / "baseline_refined.pdb").write_text("ATOM baseline")
    return base


# ──────────────────────────────────────────────
# G-1: FE 형식 "iter04_cand004" → hit
# ──────────────────────────────────────────────
def test_g1_iter_cand_format_matches(tmp_path: Path) -> None:
    """FE 가 실제로 보내는 'iter04_cand004' 형식이 인덱스에서 hit 해야 한다."""
    runs_dir = _make_run_structure(
        tmp_path,
        run_name="run_20260520",
        iters={
            "iter_04": ["cand_004.pdb"],
            "iter_03": ["cand_003.pdb"],
        },
    )

    from backend.routers.selectivity import _build_pdb_index
    index, _ = _build_pdb_index(runs_dir)

    # FE 형식 확인
    assert "iter04_cand004" in index, f"FE 형식 키 누락. 등록된 키: {sorted(index.keys())}"
    assert "iter03_cand003" in index, f"iter03 형식 키 누락."

    # 경로가 실제 pdb 파일을 가리켜야 함
    assert index["iter04_cand004"].endswith("cand_004.pdb")
    assert index["iter03_cand003"].endswith("cand_003.pdb")


# ──────────────────────────────────────────────
# G-2: 레거시 형식 "001", "1", "var001" → 회귀
# ──────────────────────────────────────────────
def test_g2_legacy_3digit_still_matches(tmp_path: Path) -> None:
    """기존 '001', '1', 'var001' 키가 여전히 인덱스에 등록되어야 한다 (회귀)."""
    runs_dir = _make_run_structure(
        tmp_path,
        run_name="run_20260520",
        iters={"iter_01": ["cand_001.pdb"]},
    )

    from backend.routers.selectivity import _build_pdb_index
    index, _ = _build_pdb_index(runs_dir)

    assert "001" in index, "레거시 '001' 키 누락"
    assert "1" in index, "레거시 '1' (lstrip 0) 키 누락"
    assert "var001" in index, "레거시 'var001' 키 누락"


# ──────────────────────────────────────────────
# G-3: "cand001", "cand_001" 변형 → hit
# ──────────────────────────────────────────────
def test_g3_cand_variants_match(tmp_path: Path) -> None:
    """'cand001' 및 'cand_001' 변형 키가 등록되어야 한다."""
    runs_dir = _make_run_structure(
        tmp_path,
        run_name="run_20260520",
        iters={"iter_02": ["cand_007.pdb"]},
    )

    from backend.routers.selectivity import _build_pdb_index
    index, _ = _build_pdb_index(runs_dir)

    assert "cand007" in index, "'cand007' 변형 키 누락"
    assert "cand_007" in index, "'cand_007' 변형 키 누락"


# ──────────────────────────────────────────────
# G-4: 없는 cid → miss (estimation fallback 확인)
# ──────────────────────────────────────────────
def test_g4_missing_cid_returns_empty(tmp_path: Path) -> None:
    """존재하지 않는 cid 는 인덱스에서 miss → estimation fallback 으로 빠진다."""
    runs_dir = _make_run_structure(
        tmp_path,
        run_name="run_20260520",
        iters={"iter_01": ["cand_001.pdb"]},
    )

    from backend.routers.selectivity import _build_pdb_index
    index, _ = _build_pdb_index(runs_dir)

    assert "iter99_cand999" not in index
    assert index.get("iter99_cand999", "") == ""


# ──────────────────────────────────────────────
# G-5: 복수 iter → 각각 iter 키 등록
# ──────────────────────────────────────────────
def test_g5_multiple_iters_all_registered(tmp_path: Path) -> None:
    """iter_01/iter_02/iter_03 각각의 cand 가 iter 키로 독립 등록되어야 한다."""
    runs_dir = _make_run_structure(
        tmp_path,
        run_name="run_20260520",
        iters={
            "iter_01": ["cand_001.pdb"],
            "iter_02": ["cand_002.pdb"],
            "iter_03": ["cand_003.pdb"],
        },
    )

    from backend.routers.selectivity import _build_pdb_index
    index, _ = _build_pdb_index(runs_dir)

    assert "iter01_cand001" in index
    assert "iter02_cand002" in index
    assert "iter03_cand003" in index
    # 각각 다른 PDB 파일
    assert index["iter01_cand001"].endswith("cand_001.pdb")
    assert index["iter02_cand002"].endswith("cand_002.pdb")
    assert index["iter03_cand003"].endswith("cand_003.pdb")


# ──────────────────────────────────────────────
# G-6: stem 에 점 포함 — "cand_007.val1" → "007" 정상 파싱
# ──────────────────────────────────────────────
def test_g6_stem_with_dot_parsed_correctly(tmp_path: Path) -> None:
    """cand_007.val1.pdb 처럼 stem 에 점이 포함돼도 '007' 로 올바르게 파싱된다."""
    mutdock = tmp_path / "run_20260520" / "sst14_agentic_mutdock"
    iter_dir = mutdock / "iter_01"
    iter_dir.mkdir(parents=True)
    # 점 포함 파일명: pdb.stem = "cand_007.val1"
    (iter_dir / "cand_007.val1.pdb").write_text("ATOM dummy")

    from backend.routers.selectivity import _build_pdb_index
    index, _ = _build_pdb_index(tmp_path)

    assert "007" in index, "점 포함 stem '007' 파싱 실패"
    assert "iter01_cand007" in index, "iter 키 생성 실패 (점 포함 stem)"


# ──────────────────────────────────────────────
# G-7: 가장 최근 run 만 사용 — 오래된 run 무시
# ──────────────────────────────────────────────
def test_g7_only_most_recent_run_used(tmp_path: Path) -> None:
    """runs_dir 에 2개 run 이 있을 때 reverse sorted 기준 가장 최근 run 만 사용."""
    # 오래된 run: cand_099.pdb
    _make_run_structure(
        tmp_path,
        run_name="run_20260101",
        iters={"iter_01": ["cand_099.pdb"]},
        with_baseline=False,
    )
    # 최신 run: cand_001.pdb
    _make_run_structure(
        tmp_path,
        run_name="run_20260520",
        iters={"iter_01": ["cand_001.pdb"]},
        with_baseline=True,
    )

    from backend.routers.selectivity import _build_pdb_index
    index, baseline = _build_pdb_index(tmp_path)

    # 최신 run 의 cand_001 이 등록되어야 함
    assert "001" in index
    # 오래된 run 의 cand_099 는 등록되지 않아야 함
    assert "099" not in index, "오래된 run 의 cand_099 가 등록됨 — 최신 run 만 사용해야 함"
    # baseline 은 최신 run 에서 찾아야 함
    assert "run_20260520" in baseline


# ──────────────────────────────────────────────
# K-1: iter 자연 정렬 회귀 — "iter_2" vs "iter_10" alphabet 정렬 버그
# ──────────────────────────────────────────────
def test_k1_iter_natural_sort_iter10_preferred(tmp_path: Path) -> None:
    """K-1 fix: iter_10 이 iter_2 보다 최신이지만 alphabet 정렬에서는 'iter_10' < 'iter_2'.

    기존 sorted(..., reverse=True) 만 사용 시 iter_2 가 먼저 와서
    setdefault 가 iter_2 의 PDB 를 cand 키에 등록 → 잘못된 PDB 사용.

    fix: key=int(parts[1]) 자연 정렬로 iter_10 우선.
    """
    runs_dir = _make_run_structure(
        tmp_path,
        run_name="run_20260526",
        iters={
            "iter_2": ["cand_005.pdb"],   # 오래된 iter 의 cand_005
            "iter_10": ["cand_005.pdb"],  # 최신 iter 의 cand_005 (이게 선택되어야 함)
        },
    )

    from backend.routers.selectivity import _build_pdb_index
    index, _ = _build_pdb_index(runs_dir)

    # K-1: iter_10 의 cand_005 가 우선 등록되어야 함 (자연 정렬, 최신 iter 우선)
    assert "iter10_cand005" in index, f"iter10 키 누락. 등록 키: {sorted(index.keys())[:10]}"
    # "005" 같은 일반 키는 iter_10 의 경로를 가리켜야 함 (가장 최근 iter)
    assert "iter_10" in index["005"], (
        f"K-1 회귀: '005' 일반 키가 iter_10 가 아닌 iter_2 의 PDB 를 가리킴 → 자연 정렬 적용 필요. "
        f"실제 경로: {index['005']}"
    )


def test_k1_many_iters_natural_sort(tmp_path: Path) -> None:
    """K-1 fix: iter_1, iter_2, ..., iter_15 mix 에서 iter_15 가 최신."""
    iters_dict = {f"iter_{i}": [f"cand_{i:03d}.pdb"] for i in [1, 2, 5, 9, 10, 15]}
    runs_dir = _make_run_structure(tmp_path, run_name="run_2026", iters=iters_dict)

    from backend.routers.selectivity import _build_pdb_index
    index, _ = _build_pdb_index(runs_dir)

    # 모든 iter 키 등록
    for i in [1, 2, 5, 9, 10, 15]:
        key = f"iter{i}_cand{i:03d}"
        assert key in index, f"iter{i} 키 누락. 등록 키: {sorted(index.keys())[:15]}"
