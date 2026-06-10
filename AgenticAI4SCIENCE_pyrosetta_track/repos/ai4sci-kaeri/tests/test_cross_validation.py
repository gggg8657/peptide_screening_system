"""
pharma_properties.py 3자+ 교차 검증 테스트
==========================================

우리 구현(pharma_properties.py)의 계산 결과를 **서로 다른 코드베이스**의
외부 패키지들과 교차 비교하여, "이름만 같고 결과가 다른 것"이 아닌지 검증합니다.

검증 구조
---------
    pharma_properties.py (우리 코드)
          ↕
    peptides v0.5.0      (GT, 이미 검증 완료)
          ↕
    modlAMP              (독립 코드베이스 — 3자 검증의 핵심)
          ↕
    Biopython            (ExPASy ProtParam 로컬 구현)
          ↕
    Pyteomics            (질량분석 기반 — MW/protease 고정밀)

각 외부 패키지가 미설치면 해당 테스트만 skip됩니다.
"pip install modlamp peptides pyteomics"로 전체 검증 가능.

실행 방법
---------
    # 전체 실행 (설치된 패키지만 테스트)
    pytest tests/test_cross_validation.py -v

    # 특정 어댑터만
    pytest tests/test_cross_validation.py -v -k "modlamp"

    # 상세 비교 테이블 출력
    pytest tests/test_cross_validation.py -v -s
"""

from __future__ import annotations

import math
import os
import sys
import unittest

# 프로젝트 경로 설정
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

from AG_src.pipeline.pharma_properties import PharmaProperties

# 어댑터 import
from tests.cross_validators import (
    biopython_adapter,
    modlamp_adapter,
    peptides_adapter,
    pyteomics_adapter,
)

# ─── 테스트 서열 ────────────────────────────────────────────────────────

# SST-14 native (Cys3-Cys14 이황화결합, FWKT 약리단 pos 7-10)
SST14 = "AGCKNFFWKTFTSC"

# 추가 검증 서열 — 다양한 아미노산 조성
TEST_SEQS = {
    "SST14":      "AGCKNFFWKTFTSC",   # 타겟 펩타이드
    "AllAla":     "AAAAAAAAAA",       # 균일 서열 (에지 케이스)
    "Charged":    "KKKKDDDDEE",       # 극성 잔기 풍부
    "Hydrophobic": "ILLLVVFFWW",      # 소수성 잔기 풍부
    "Short":      "ACDEF",            # 최소 길이
}

# ─── 허용 오차 정의 ──────────────────────────────────────────────────────

# 메서드별 허용 오차 (문헌·패키지 간 미세 구현 차이 반영)
TOLERANCES = {
    "gravy":              {"abs": 0.05,  "pct": 5.0},
    "boman_index":        {"abs": 0.15,  "pct": 15.0},  # RW 테이블 버전 차이
    "instability_index":  {"abs": 1.0,   "pct": 5.0},
    "aliphatic_index":    {"abs": 0.5,   "pct": 1.0},
    "pi":                 {"abs": 1.0,   "pct": None},   # pH 단위, pKa 스케일 차이
    "mw":                 {"abs": 5.0,   "pct": 0.5},    # Da 단위
    "net_charge":         {"abs": 0.5,   "pct": None},   # charge 단위
    "hydrophobic_moment": {"abs": 0.1,   "pct": 20.0},   # 윈도우/스케일 차이
    "extinction_coeff":   {"abs": 200,   "pct": 5.0},
}


def _within_tolerance(ours: float, theirs: float, metric: str) -> bool:
    """허용 오차 내 일치 여부 판단."""
    tol = TOLERANCES.get(metric, {"abs": 1.0, "pct": 10.0})
    abs_tol = tol.get("abs")
    pct_tol = tol.get("pct")

    if abs_tol is not None and abs(ours - theirs) <= abs_tol:
        return True
    if pct_tol is not None and theirs != 0:
        pct_diff = abs(ours - theirs) / abs(theirs) * 100
        if pct_diff <= pct_tol:
            return True
    return False


def _comparison_line(metric: str, ours: float, theirs: float, source: str) -> str:
    """비교 결과를 한 줄로 포맷."""
    delta = ours - theirs
    ok = "✅" if _within_tolerance(ours, theirs, metric) else "❌"
    return f"  {metric:<25s} | ours={ours:>10.4f} | {source}={theirs:>10.4f} | Δ={delta:+.4f} | {ok}"


# ─── 우리 코드 래퍼 ─────────────────────────────────────────────────────

_PP = PharmaProperties()


def _our_values(seq: str) -> dict:
    """pharma_properties.py에서 전체 계산 결과를 딕셔너리로 반환."""
    return {
        "gravy": _PP.calculate_gravy(seq),
        "boman_index": _PP.calculate_boman_index(seq),
        "instability_index": _PP.calculate_instability_index(seq),
        "aliphatic_index": _PP.calculate_aliphatic_index(seq),
        "pi": _PP.calculate_pi(seq),
        "mw": _PP.calculate_mw(seq).get("mw_average", 0.0),
        "net_charge": _PP.calculate_net_charge(seq, ph=7.4),
        "hydrophobic_moment": _PP.calculate_hydrophobic_moment(seq, angle=100.0, window=min(11, len(seq))),
        "extinction_coeff": _PP.calculate_extinction_coefficient(seq, n_disulfide=0),
    }


# ═══════════════════════════════════════════════════════════════════════
#  Biopython ProteinAnalysis 교차 검증
# ═══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(biopython_adapter.is_available(), "biopython 미설치")
class TestVsBiopython(unittest.TestCase):
    """Biopython ProteinAnalysis(ExPASy ProtParam 로컬 구현)와 비교."""

    def _compare(self, seq: str, metric: str):
        ours = _our_values(seq)
        theirs = biopython_adapter.compute(seq)
        self.assertIsNotNone(theirs, "Biopython 계산 실패")
        o, t = ours[metric], theirs[metric]
        print(_comparison_line(metric, o, t, "biopython"))
        self.assertTrue(
            _within_tolerance(o, t, metric),
            f"{metric}: ours={o:.4f}, biopython={t:.4f}"
        )

    def test_gravy_sst14(self):
        """GRAVY (Kyte-Doolittle) — SST-14"""
        self._compare(SST14, "gravy")

    def test_instability_index_sst14(self):
        """Instability Index (Guruprasad) — SST-14"""
        self._compare(SST14, "instability_index")

    def test_pi_sst14(self):
        """Isoelectric Point — SST-14"""
        self._compare(SST14, "pi")

    def test_mw_sst14(self):
        """Molecular Weight — SST-14"""
        self._compare(SST14, "mw")

    def test_extinction_coefficient_sst14(self):
        """ε₂₈₀ — SST-14 (reduced Cys 기준)"""
        ours = _our_values(SST14)["extinction_coeff"]
        theirs = biopython_adapter.compute(SST14)["extinction_coeff_reduced"]
        print(_comparison_line("extinction_coeff", ours, theirs, "biopython"))
        self.assertTrue(
            _within_tolerance(ours, theirs, "extinction_coeff"),
            f"ε₂₈₀: ours={ours}, biopython={theirs}"
        )

    def test_multi_sequences(self):
        """여러 서열에 대해 GRAVY 교차 검증."""
        for name, seq in TEST_SEQS.items():
            with self.subTest(seq=name):
                self._compare(seq, "gravy")


# ═══════════════════════════════════════════════════════════════════════
#  modlAMP 교차 검증 (3자 검증의 핵심)
# ═══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(modlamp_adapter.is_available(), "modlamp 미설치")
class TestVsModlAMP(unittest.TestCase):
    """modlAMP(AMP descriptor 패키지) — peptides와 완전히 독립된 코드베이스."""

    def _compare(self, seq: str, metric: str):
        ours = _our_values(seq)
        theirs = modlamp_adapter.compute(seq)
        self.assertIsNotNone(theirs, "modlAMP 계산 실패")
        o, t = ours[metric], theirs[metric]
        print(_comparison_line(metric, o, t, "modlamp"))
        self.assertTrue(
            _within_tolerance(o, t, metric),
            f"{metric}: ours={o:.4f}, modlamp={t:.4f}"
        )

    def test_gravy_sst14(self):
        self._compare(SST14, "gravy")

    def test_boman_index_sst14(self):
        self._compare(SST14, "boman_index")

    def test_instability_index_sst14(self):
        self._compare(SST14, "instability_index")

    def test_aliphatic_index_sst14(self):
        self._compare(SST14, "aliphatic_index")

    def test_pi_sst14(self):
        self._compare(SST14, "pi")

    def test_mw_sst14(self):
        self._compare(SST14, "mw")

    def test_net_charge_sst14(self):
        self._compare(SST14, "net_charge")

    def test_hydrophobic_moment_sst14(self):
        self._compare(SST14, "hydrophobic_moment")

    def test_multi_sequences_gravy(self):
        """여러 서열에 대해 GRAVY 3자 검증."""
        for name, seq in TEST_SEQS.items():
            with self.subTest(seq=name):
                self._compare(seq, "gravy")

    def test_multi_sequences_pi(self):
        """여러 서열에 대해 pI 3자 검증."""
        for name, seq in TEST_SEQS.items():
            with self.subTest(seq=name):
                self._compare(seq, "pi")


# ═══════════════════════════════════════════════════════════════════════
#  peptides PyPI 교차 검증 (기존 GT 재확인)
# ═══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(peptides_adapter.is_available(), "peptides 미설치")
class TestVsPeptides(unittest.TestCase):
    """peptides v0.5.0 — 기존 GT. 어댑터 인터페이스 통일 확인."""

    def _compare(self, seq: str, metric: str):
        ours = _our_values(seq)
        theirs = peptides_adapter.compute(seq)
        self.assertIsNotNone(theirs, "peptides 계산 실패")
        o, t = ours[metric], theirs[metric]
        print(_comparison_line(metric, o, t, "peptides"))
        self.assertTrue(
            _within_tolerance(o, t, metric),
            f"{metric}: ours={o:.4f}, peptides={t:.4f}"
        )

    def test_gravy_sst14(self):
        self._compare(SST14, "gravy")

    def test_boman_index_sst14(self):
        self._compare(SST14, "boman_index")

    def test_instability_index_sst14(self):
        self._compare(SST14, "instability_index")

    def test_aliphatic_index_sst14(self):
        self._compare(SST14, "aliphatic_index")

    def test_pi_sst14(self):
        self._compare(SST14, "pi")

    def test_mw_sst14(self):
        self._compare(SST14, "mw")

    def test_net_charge_sst14(self):
        self._compare(SST14, "net_charge")

    def test_hydrophobic_moment_sst14(self):
        self._compare(SST14, "hydrophobic_moment")


# ═══════════════════════════════════════════════════════════════════════
#  Pyteomics 교차 검증 (MW 고정밀 + Protease Sites)
# ═══════════════════════════════════════════════════════════════════════

@unittest.skipUnless(pyteomics_adapter.is_available(), "pyteomics 미설치")
class TestVsPyteomics(unittest.TestCase):
    """Pyteomics — MW 고정밀 계산 + 프로테아제 절단 사이트."""

    def test_mw_sst14(self):
        """MW (평균 동위원소 질량) — SST-14"""
        ours = _our_values(SST14)["mw"]
        theirs = pyteomics_adapter.compute(SST14)
        self.assertIsNotNone(theirs)
        t = theirs["mw"]
        print(_comparison_line("mw", ours, t, "pyteomics"))
        self.assertTrue(
            _within_tolerance(ours, t, "mw"),
            f"MW: ours={ours:.2f}, pyteomics={t:.2f}"
        )

    def test_pi_sst14(self):
        """pI — SST-14"""
        ours = _our_values(SST14)["pi"]
        theirs = pyteomics_adapter.compute(SST14)["pi"]
        print(_comparison_line("pi", ours, theirs, "pyteomics"))
        self.assertTrue(
            _within_tolerance(ours, theirs, "pi"),
            f"pI: ours={ours:.2f}, pyteomics={theirs:.2f}"
        )

    def test_protease_sites_exist(self):
        """프로테아제 절단 사이트가 0 이상 반환되는지 확인."""
        result = pyteomics_adapter.compute(SST14)
        self.assertIsNotNone(result)
        sites = result["protease_sites"]
        for enzyme, count in sites.items():
            self.assertIsNotNone(count, f"{enzyme} 절단 사이트 계산 실패")
            self.assertGreaterEqual(count, 0, f"{enzyme} 음수 사이트: {count}")
            print(f"  protease:{enzyme:<35s} | sites={count}")


# ═══════════════════════════════════════════════════════════════════════
#  N-way 교차 검증 (설치된 모든 패키지로 동시 비교)
# ═══════════════════════════════════════════════════════════════════════

class TestNWayCrossValidation(unittest.TestCase):
    """설치된 모든 외부 패키지를 동시에 비교하는 통합 테스트.

    패키지가 0개 설치되어 있어도 실패하지 않습니다 (skip 처리).
    2개 이상 설치 시 진정한 N-way 교차 검증이 됩니다.
    """

    def test_gravy_all_sources(self):
        """GRAVY — 설치된 모든 패키지와 SST-14 비교."""
        ours = _our_values(SST14)["gravy"]
        adapters = {
            "peptides": peptides_adapter,
            "modlamp": modlamp_adapter,
            "biopython": biopython_adapter,
        }
        n_compared = 0
        print(f"\n  GRAVY N-way (ours={ours:.4f}):")
        for name, adapter in adapters.items():
            if not adapter.is_available():
                print(f"    {name}: SKIP (미설치)")
                continue
            theirs = adapter.compute(SST14)
            if theirs and "gravy" in theirs:
                t = theirs["gravy"]
                ok = _within_tolerance(ours, t, "gravy")
                print(f"    {name}: {t:.4f} {'✅' if ok else '❌'}")
                self.assertTrue(ok, f"GRAVY: ours={ours:.4f}, {name}={t:.4f}")
                n_compared += 1
        if n_compared == 0:
            self.skipTest("외부 패키지 없음 — GRAVY N-way 검증 불가")

    def test_mw_all_sources(self):
        """MW — 설치된 모든 패키지와 SST-14 비교."""
        ours = _our_values(SST14)["mw"]
        adapters = {
            "peptides": peptides_adapter,
            "modlamp": modlamp_adapter,
            "biopython": biopython_adapter,
            "pyteomics": pyteomics_adapter,
        }
        n_compared = 0
        print(f"\n  MW N-way (ours={ours:.2f}):")
        for name, adapter in adapters.items():
            if not adapter.is_available():
                print(f"    {name}: SKIP (미설치)")
                continue
            theirs = adapter.compute(SST14)
            if theirs and "mw" in theirs:
                t = theirs["mw"]
                ok = _within_tolerance(ours, t, "mw")
                print(f"    {name}: {t:.2f} {'✅' if ok else '❌'}")
                self.assertTrue(ok, f"MW: ours={ours:.2f}, {name}={t:.2f}")
                n_compared += 1
        if n_compared == 0:
            self.skipTest("외부 패키지 없음 — MW N-way 검증 불가")

    def test_pi_all_sources(self):
        """pI — 설치된 모든 패키지와 SST-14 비교."""
        ours = _our_values(SST14)["pi"]
        adapters = {
            "peptides": peptides_adapter,
            "modlamp": modlamp_adapter,
            "biopython": biopython_adapter,
            "pyteomics": pyteomics_adapter,
        }
        n_compared = 0
        print(f"\n  pI N-way (ours={ours:.2f}):")
        for name, adapter in adapters.items():
            if not adapter.is_available():
                print(f"    {name}: SKIP (미설치)")
                continue
            theirs = adapter.compute(SST14)
            if theirs and "pi" in theirs:
                t = theirs["pi"]
                ok = _within_tolerance(ours, t, "pi")
                print(f"    {name}: {t:.2f} {'✅' if ok else '❌'}")
                self.assertTrue(ok, f"pI: ours={ours:.2f}, {name}={t:.2f}")
                n_compared += 1
        if n_compared == 0:
            self.skipTest("외부 패키지 없음 — pI N-way 검증 불가")


# ═══════════════════════════════════════════════════════════════════════
#  검증 커버리지 리포트
# ═══════════════════════════════════════════════════════════════════════

class TestCoverageReport(unittest.TestCase):
    """15개 메서드 중 몇 개가 교차 검증 가능한지 요약."""

    def test_print_coverage(self):
        """검증 커버리지 테이블 출력 (항상 PASS)."""
        methods = [
            "gravy", "boman_index", "instability_index", "aliphatic_index",
            "pi", "extinction_coeff", "n_end_rule", "hydrophobic_moment",
            "wimley_white", "net_charge", "mw", "protease_sites",
            "blosum62", "metal_coordination", "radiolysis",
        ]
        adapter_methods = {
            "peptides": {"gravy", "boman_index", "instability_index", "aliphatic_index",
                        "pi", "hydrophobic_moment", "net_charge", "mw"},
            "modlamp":  {"gravy", "boman_index", "instability_index", "aliphatic_index",
                        "pi", "hydrophobic_moment", "net_charge", "mw"},
            "biopython": {"gravy", "instability_index", "pi", "mw", "extinction_coeff"},
            "pyteomics": {"mw", "pi", "net_charge", "protease_sites"},
        }
        adapters_available = {
            "peptides": peptides_adapter.is_available(),
            "modlamp": modlamp_adapter.is_available(),
            "biopython": biopython_adapter.is_available(),
            "pyteomics": pyteomics_adapter.is_available(),
        }

        print("\n" + "=" * 80)
        print("  pharma_properties.py 15메서드 교차 검증 커버리지")
        print("=" * 80)
        header = f"  {'메서드':<25s}"
        for a in adapter_methods:
            status = "✅" if adapters_available[a] else "❌"
            header += f" | {a}{status}  "
        header += " | 검증수"
        print(header)
        print("  " + "-" * 75)

        total_verified = 0
        for m in methods:
            line = f"  {m:<25s}"
            count = 0
            for a, ms in adapter_methods.items():
                if m in ms:
                    if adapters_available[a]:
                        line += " |  ✅     "
                        count += 1
                    else:
                        line += " |  ⬜     "
                else:
                    line += " |  —      "
            line += f" | {count}"
            print(line)
            if count > 0:
                total_verified += 1

        print("  " + "-" * 75)
        print(f"  교차 검증 가능 메서드: {total_verified}/15")
        installed = sum(1 for v in adapters_available.values() if v)
        print(f"  설치된 외부 패키지: {installed}/4")
        if installed < 4:
            missing = [k for k, v in adapters_available.items() if not v]
            print(f"  미설치: {', '.join(missing)}")
            print(f"  → pip install {' '.join(missing)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
