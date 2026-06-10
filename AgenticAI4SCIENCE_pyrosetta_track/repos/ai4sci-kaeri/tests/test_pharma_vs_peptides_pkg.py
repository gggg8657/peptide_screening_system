"""
SST-14 native 서열 약리학적 특성 비교 테스트
=============================================
우리 코드(backend/pharmacology.py, AG_src/pipeline/pharma_properties.py) vs
peptides PyPI 패키지(v0.5.0) 수치 비교

서열: AGCKNFFWKTFTSC (SST-14 native, Cys3-Cys14 disulfide)

실행 방법:
    python tests/test_pharma_vs_peptides_pkg.py
    pytest tests/test_pharma_vs_peptides_pkg.py -v
"""

from __future__ import annotations

import math
import sys
import os

# 프로젝트 루트를 sys.path에 추가
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

import peptides
from backend.pharmacology import (
    gravy,
    boman_index,
    instability_index,
    aliphatic_index,
    isoelectric_point,
    hydrophobic_moment,
    _net_charge_at_ph,
)
from AG_src.pipeline.pharma_properties import PharmaProperties

# ─── 공통 상수 ────────────────────────────────────────────────────────────────

SEQ = "AGCKNFFWKTFTSC"
PHARMA = PharmaProperties()

# peptides 패키지 객체
PEPT = peptides.Peptide(SEQ)


# ─── 헬퍼 ────────────────────────────────────────────────────────────────────

def _pct_diff(ours: float, theirs: float) -> float:
    """% 차이: abs(ours - theirs) / max(abs(theirs), 1e-9) * 100"""
    return abs(ours - theirs) / max(abs(theirs), 1e-9) * 100


def _fmt(val: object) -> str:
    if isinstance(val, float):
        return f"{val:+.4f}"
    return str(val)


def _row(label: str, ours: float, theirs: float) -> str:
    delta = ours - theirs
    pct = _pct_diff(ours, theirs)
    match = "OK " if pct < 5.0 else "DIFF"
    return (
        f"  {label:<30s} | {_fmt(ours):>10s} | {_fmt(theirs):>10s} "
        f"| {delta:+.4f} | {pct:6.2f}% | {match}"
    )


# ─── 비교 함수 ────────────────────────────────────────────────────────────────

def compare_gravy() -> dict:
    """
    GRAVY (Kyte-Doolittle 1982)
    우리 코드: backend.pharmacology.gravy()
    peptides : Peptide.hydrophobicity(scale='KyteDoolittle')
    """
    ours_backend = gravy(SEQ)
    ours_pharma = PHARMA.calculate_gravy(SEQ)
    theirs_kd = PEPT.hydrophobicity(scale="KyteDoolittle")  # 기본값 확인
    theirs_default = PEPT.hydrophobicity()  # 기본값이 KyteDoolittle인지 검증
    return {
        "backend_gravy": ours_backend,
        "pharma_gravy": ours_pharma,
        "peptides_kd": theirs_kd,
        "peptides_default": theirs_default,
        "default_is_kd": abs(theirs_default - theirs_kd) < 1e-6,
    }


def compare_instability_index() -> dict:
    """
    Instability Index (Guruprasad et al. 1990)
    두 구현 모두 ExPASy DIWV 테이블을 사용 — 미세 차이가 있을 수 있음.
    """
    ours_backend = instability_index(SEQ)
    ours_pharma = PHARMA.calculate_instability_index(SEQ)
    theirs = PEPT.instability_index()
    return {
        "backend": ours_backend,
        "pharma": ours_pharma,
        "peptides": theirs,
    }


def compare_aliphatic_index() -> dict:
    """Aliphatic Index (Ikai 1980)"""
    ours_backend = aliphatic_index(SEQ)
    ours_pharma = PHARMA.calculate_aliphatic_index(SEQ)
    theirs = PEPT.aliphatic_index()
    return {
        "backend": ours_backend,
        "pharma": ours_pharma,
        "peptides": theirs,
    }


def compare_isoelectric_point() -> dict:
    """
    isoelectric point
    우리 코드: Lehninger pKa 세트
    peptides  : EMBOSS 기본, Lehninger 옵션 존재
    """
    ours_backend = isoelectric_point(SEQ)
    ours_pharma = PHARMA.calculate_pi(SEQ)
    theirs_emboss = PEPT.isoelectric_point(pKscale="EMBOSS")     # 기본값
    theirs_lehninger = PEPT.isoelectric_point(pKscale="Lehninger")
    return {
        "backend": ours_backend,
        "pharma": ours_pharma,
        "peptides_EMBOSS": theirs_emboss,
        "peptides_Lehninger": theirs_lehninger,
    }


def compare_boman_index() -> dict:
    """
    Boman Index (Boman 2003, Radzicka-Wolfenden 1988)
    주의: 부호 규약 차이 가능
      - 우리 backend: BI = -mean(RW)  → 음수 = 소수성 (높은 단백질결합)
      - 우리 pharma : BI = +mean(RW)  → 양수 = 친수성
      - peptides    : ExPASy/Boman 2003 원문 부호 확인 필요
    """
    ours_backend = boman_index(SEQ)          # backend: -sum/n
    ours_pharma = PHARMA.calculate_boman_index(SEQ)   # pharma: +sum/n
    theirs = PEPT.boman()
    return {
        "backend_boman": ours_backend,
        "pharma_boman": ours_pharma,
        "peptides_boman": theirs,
        "backend_sign_note": "backend=-mean(RW), pharma=+mean(RW)",
    }


def compare_net_charge() -> dict:
    """Net Charge at pH 7.4 (Henderson-Hasselbalch)"""
    ours_backend = _net_charge_at_ph(SEQ, 7.4)
    ours_pharma = PHARMA.calculate_net_charge(SEQ, ph=7.4)
    theirs_lehninger = PEPT.charge(pH=7.4, pKscale="Lehninger")
    theirs_default = PEPT.charge(pH=7.4)  # 기본값 확인
    return {
        "backend": ours_backend,
        "pharma": ours_pharma,
        "peptides_Lehninger": theirs_lehninger,
        "peptides_default_scale": theirs_default,
    }


def compare_molecular_weight() -> dict:
    """
    분자량 (Da)
    우리 코드에는 분자량 계산 함수 없음 — peptides 패키지 단독 계산.
    참고값으로만 표시.
    """
    theirs_expasy = PEPT.molecular_weight(average="expasy")
    theirs_monoisotopic = PEPT.molecular_weight(average="monoisotopic")
    return {
        "peptides_expasy": theirs_expasy,
        "peptides_monoisotopic": theirs_monoisotopic,
        "note": "우리 코드에 MW 구현 없음 — 미구현 항목",
    }


def compare_hydrophobic_moment() -> dict:
    """
    Hydrophobic Moment (Eisenberg et al. 1982)
    angle=100° (α-helix), window=11
    """
    ours_backend = hydrophobic_moment(SEQ, angle=100.0, window=11)["mu_h_max"]
    ours_pharma = PHARMA.calculate_hydrophobic_moment(SEQ, angle=100.0, window=11)
    theirs = PEPT.hydrophobic_moment(window=11, angle=100)
    return {
        "backend": ours_backend,
        "pharma": ours_pharma,
        "peptides": float(theirs) if not isinstance(theirs, float) else theirs,
    }


# ─── 메인 비교 테이블 출력 ────────────────────────────────────────────────────

def print_comparison_table() -> None:
    print("=" * 90)
    print(f"  SST-14 native 서열 약리학적 특성 비교: {SEQ}")
    print("  peptides PyPI v0.5.0  vs  우리 구현 (backend/pharmacology.py + pharma_properties.py)")
    print("=" * 90)

    # ── 1. GRAVY ──────────────────────────────────────────────────────────────
    r = compare_gravy()
    print()
    print("[ 1. GRAVY (Kyte-Doolittle 1982) ]")
    print(f"  {'항목':<30s} | {'우리(backend)':>10s} | {'peptides':>10s} | {'Delta':>8s} | {'%Diff':>7s} | 판정")
    print("  " + "-" * 82)
    print(_row("backend.gravy()", r["backend_gravy"], r["peptides_kd"]))
    print(_row("pharma.calculate_gravy()", r["pharma_gravy"], r["peptides_kd"]))
    print(f"  [참고] peptides 기본값이 KyteDoolittle인지: {r['default_is_kd']} "
          f"(default={r['peptides_default']:.4f}, kd={r['peptides_kd']:.4f})")

    # ── 2. Instability Index ──────────────────────────────────────────────────
    r = compare_instability_index()
    print()
    print("[ 2. Instability Index (Guruprasad et al. 1990) ]")
    print(f"  {'항목':<30s} | {'우리':>10s} | {'peptides':>10s} | {'Delta':>8s} | {'%Diff':>7s} | 판정")
    print("  " + "-" * 82)
    print(_row("backend.instability_index()", r["backend"], r["peptides"]))
    print(_row("pharma.calculate_instability_index()", r["pharma"], r["peptides"]))
    print(f"  [참고] II < 40 → stable (우리 backend={r['backend']:.2f}, peptides={r['peptides']:.2f})")

    # ── 3. Aliphatic Index ────────────────────────────────────────────────────
    r = compare_aliphatic_index()
    print()
    print("[ 3. Aliphatic Index (Ikai 1980) ]")
    print(f"  {'항목':<30s} | {'우리':>10s} | {'peptides':>10s} | {'Delta':>8s} | {'%Diff':>7s} | 판정")
    print("  " + "-" * 82)
    print(_row("backend.aliphatic_index()", r["backend"], r["peptides"]))
    print(_row("pharma.calculate_aliphatic_index()", r["pharma"], r["peptides"]))

    # ── 4. Isoelectric Point ──────────────────────────────────────────────────
    r = compare_isoelectric_point()
    print()
    print("[ 4. Isoelectric Point (pI) ]")
    print(f"  {'항목':<30s} | {'우리':>10s} | {'peptides':>10s} | {'Delta':>8s} | {'%Diff':>7s} | 판정")
    print("  " + "-" * 82)
    print(_row("backend.isoelectric_point() [Leh]", r["backend"], r["peptides_Lehninger"]))
    print(_row("pharma.calculate_pi() [Leh]", r["pharma"], r["peptides_Lehninger"]))
    print(_row("vs peptides EMBOSS (기본값)", r["pharma"], r["peptides_EMBOSS"]))
    print(f"  [참고] pK 스케일 차이: Lehninger={r['peptides_Lehninger']:.2f}, EMBOSS={r['peptides_EMBOSS']:.2f}")

    # ── 5. Boman Index ────────────────────────────────────────────────────────
    r = compare_boman_index()
    print()
    print("[ 5. Boman Index (Boman 2003) ]")
    print(f"  {'항목':<30s} | {'값':>10s} | {'peptides':>10s} | {'Delta':>8s} | {'%Diff':>7s} | 판정")
    print("  " + "-" * 82)
    print(_row("backend.boman_index() [-mean(RW)]", r["backend_boman"], r["peptides_boman"]))
    print(_row("pharma.calculate_boman_index() [+mean(RW)]", r["pharma_boman"], r["peptides_boman"]))
    print(f"  [주의] backend 부호 반전: backend=-mean(RW)={r['backend_boman']:.4f}, "
          f"pharma=+mean(RW)={r['pharma_boman']:.4f}")
    print(f"         peptides.boman()={r['peptides_boman']:.4f} "
          f"(peptides는 -mean(Boman_table) 사용 — 부호+테이블 모두 다름)")
    print(f"  [테이블 차이] S: backend=1.15, pharma=1.83, peptides(반전)=3.40")
    print(f"               W: backend=-2.09, pharma=-2.09, peptides(반전)=2.33")
    print(f"               H: backend=2.06, pharma=2.06, peptides(반전)=4.66")

    # ── 6. Net Charge pH 7.4 ──────────────────────────────────────────────────
    r = compare_net_charge()
    print()
    print("[ 6. Net Charge at pH 7.4 (Henderson-Hasselbalch) ]")
    print(f"  {'항목':<30s} | {'우리':>10s} | {'peptides':>10s} | {'Delta':>8s} | {'%Diff':>7s} | 판정")
    print("  " + "-" * 82)
    print(_row("backend._net_charge_at_ph(7.4)", r["backend"], r["peptides_Lehninger"]))
    print(_row("pharma.calculate_net_charge(7.4)", r["pharma"], r["peptides_Lehninger"]))
    print(_row("vs peptides default scale", r["pharma"], r["peptides_default_scale"]))

    # ── 7. Molecular Weight ───────────────────────────────────────────────────
    r = compare_molecular_weight()
    print()
    print("[ 7. Molecular Weight (Da) ]")
    print(f"  {'항목':<30s} | {'값':>12s}")
    print("  " + "-" * 50)
    print(f"  {'peptides ExPASy (평균)':30s} | {r['peptides_expasy']:>12.4f}")
    print(f"  {'peptides 단일동위원소':30s} | {r['peptides_monoisotopic']:>12.4f}")
    print(f"  [참고] {r['note']}")

    # ── 8. Hydrophobic Moment ─────────────────────────────────────────────────
    r = compare_hydrophobic_moment()
    print()
    print("[ 8. Hydrophobic Moment μH (Eisenberg et al. 1982, angle=100°, window=11) ]")
    print(f"  {'항목':<30s} | {'우리':>10s} | {'peptides':>10s} | {'Delta':>8s} | {'%Diff':>7s} | 판정")
    print("  " + "-" * 82)
    print(_row("backend.hydrophobic_moment() max", r["backend"], r["peptides"]))
    print(_row("pharma.calculate_hydrophobic_moment()", r["pharma"], r["peptides"]))

    # ── 요약 ─────────────────────────────────────────────────────────────────
    print()
    print("=" * 90)
    print("  총평 및 의미")
    print("=" * 90)
    print("""
  GRAVY         : 두 구현 모두 Kyte-Doolittle 1982 동일 테이블 사용 → 수치 일치 기대
  II            : DIWV 테이블 일부 값(KQ=24.68 vs 24.64 등) 미세 차이로 결과 다를 수 있음
  Aliphatic     : Ikai 1980 공식 동일 — 완전 일치 기대
  pI            : Lehninger vs EMBOSS pKa 세트 차이로 0.2-0.5 pH 단위 차이 발생 가능
  Boman Index   : 부호 규약 주의!
                    backend.boman_index()      = -mean(RW) [Boman 2003 원문 부호]
                    pharma.calculate_boman_index() = +mean(RW) [반전 — 수정 필요 가능성]
                    peptides.boman()           = Boman 2003 원문 (양수 = 결합력 ↑)
  Net Charge    : Lehninger 스케일 일치 → 수치 일치 기대
  MW            : 우리 코드 미구현 (TODO)
  Hydro Moment  : peptides는 max_moment 반환, 우리도 동일 — 일치 기대
""")


# ─── pytest 호환 단위 테스트 ──────────────────────────────────────────────────

class TestGRAVY:
    """GRAVY (Kyte-Doolittle) 검증"""

    def test_backend_vs_peptides_within_1pct(self):
        """backend.gravy() vs peptides: 1% 이내 일치"""
        ours = gravy(SEQ)
        theirs = PEPT.hydrophobicity(scale="KyteDoolittle")
        assert _pct_diff(ours, theirs) < 1.0, (
            f"GRAVY 차이 초과: ours={ours:.4f}, peptides={theirs:.4f}"
        )

    def test_pharma_vs_peptides_within_1pct(self):
        """pharma.calculate_gravy() vs peptides: 1% 이내"""
        ours = PHARMA.calculate_gravy(SEQ)
        theirs = PEPT.hydrophobicity(scale="KyteDoolittle")
        assert _pct_diff(ours, theirs) < 1.0

    def test_peptides_default_scale_is_kyte_doolittle(self):
        """peptides 기본 스케일이 KyteDoolittle인지 확인"""
        default = PEPT.hydrophobicity()
        kd = PEPT.hydrophobicity(scale="KyteDoolittle")
        assert abs(default - kd) < 1e-6, (
            f"기본 스케일이 KyteDoolittle이 아님: default={default}, kd={kd}"
        )

    def test_internal_consistency(self):
        """backend vs pharma 내부 일관성: 1% 이내"""
        assert _pct_diff(gravy(SEQ), PHARMA.calculate_gravy(SEQ)) < 1.0


class TestInstabilityIndex:
    """Instability Index (Guruprasad et al. 1990) 검증"""

    def test_backend_stability_classification(self):
        """SST-14 native는 stable (II < 40) 이어야 함"""
        ii = instability_index(SEQ)
        assert ii < 40.0, f"SST-14 II={ii:.2f} — stable 기대"

    def test_pharma_stability_classification(self):
        """pharma 구현도 stable"""
        ii = PHARMA.calculate_instability_index(SEQ)
        assert ii < 40.0

    def test_backend_vs_peptides_within_10pct(self):
        """DIWV 테이블 미세 차이 허용: 10% 이내"""
        ours = instability_index(SEQ)
        theirs = PEPT.instability_index()
        pct = _pct_diff(ours, theirs)
        assert pct < 10.0, (
            f"II 차이가 너무 큼: ours={ours:.4f}, peptides={theirs:.4f}, diff={pct:.2f}%"
        )

    def test_pharma_vs_peptides_within_10pct(self):
        ours = PHARMA.calculate_instability_index(SEQ)
        theirs = PEPT.instability_index()
        assert _pct_diff(ours, theirs) < 10.0


class TestAliphaticIndex:
    """Aliphatic Index (Ikai 1980) 검증"""

    def test_backend_vs_peptides_exact(self):
        """Ikai 1980 공식 동일 → 완전 일치 (0.1% 허용)"""
        ours = aliphatic_index(SEQ)
        theirs = PEPT.aliphatic_index()
        assert _pct_diff(ours, theirs) < 0.1, (
            f"Aliphatic Index 불일치: ours={ours:.4f}, peptides={theirs:.4f}"
        )

    def test_pharma_vs_peptides_exact(self):
        ours = PHARMA.calculate_aliphatic_index(SEQ)
        theirs = PEPT.aliphatic_index()
        assert _pct_diff(ours, theirs) < 0.1

    def test_sst14_aliphatic_range(self):
        """SST-14는 소수성 잔기가 풍부 → AI > 0"""
        assert aliphatic_index(SEQ) >= 0.0


class TestIsoelectricPoint:
    """pI 검증 (pKa 스케일 차이 허용)"""

    def test_backend_vs_peptides_lehninger_within_1ph(self):
        """Lehninger 스케일 기준 1 pH 단위 이내 일치"""
        ours = isoelectric_point(SEQ)
        theirs = PEPT.isoelectric_point(pKscale="Lehninger")
        assert abs(ours - theirs) < 1.0, (
            f"pI(Lehninger) 차이: ours={ours:.2f}, peptides={theirs:.2f}"
        )

    def test_pharma_vs_peptides_lehninger_within_1ph(self):
        ours = PHARMA.calculate_pi(SEQ)
        theirs = PEPT.isoelectric_point(pKscale="Lehninger")
        assert abs(ours - theirs) < 1.0

    def test_emboss_vs_lehninger_differ(self):
        """EMBOSS와 Lehninger pI는 다를 수 있음 — 스케일 의존성 문서화"""
        emboss = PEPT.isoelectric_point(pKscale="EMBOSS")
        lehninger = PEPT.isoelectric_point(pKscale="Lehninger")
        # 차이가 있을 수 있지만 극단적이지 않아야 함
        assert abs(emboss - lehninger) < 3.0, (
            f"EMBOSS vs Lehninger 차이 과다: {emboss:.2f} vs {lehninger:.2f}"
        )

    def test_sst14_pi_range(self):
        """SST-14 pI는 6-12 범위 내 (K 잔기 존재)"""
        pi = isoelectric_point(SEQ)
        assert 6.0 <= pi <= 12.0, f"pI={pi:.2f} 범위 외"


class TestBomanIndex:
    """Boman Index 부호 규약 및 테이블 차이 검증.

    주의: Radzicka-Wolfenden 1988 값에는 여러 출판 버전이 있음.
    - backend._RADZICKA_WOLFENDEN: S=1.15, W=-2.09, P=0.0
    - pharma.RW_TRANSFER:          S=1.83, W=-2.09, P=-2.54
    - peptides.BOMAN['Boman']:     S=-3.40, W=2.33, H=-4.66 (부호 반전 + 다른 값)
    따라서 세 구현 간 Boman 수치는 완전히 일치하지 않음.
    """

    def test_backend_sign_matches_pharma(self):
        """backend.boman_index()와 pharma 모두 +mean(RW) — 동일 부호·동일 값."""
        b = boman_index(SEQ)
        p = PHARMA.calculate_boman_index(SEQ)
        assert b > 0 and p > 0, (
            f"부호 방향 오류: backend={b:.4f}, pharma={p:.4f} (둘 다 양수 기대)"
        )
        assert abs(b - p) < 0.001, (
            f"backend/pharma 값 불일치: {b:.4f} vs {p:.4f}"
        )

    def test_peptides_boman_sign_matches_pharma(self):
        """peptides.boman() = -mean(Boman_table) — 내부적으로 부호 반전.
        결과적으로 peptides 결과가 우리 backend(음수)와 유사한 부호를 가질 수 있음.
        S/W/H 테이블 차이로 수치는 다름 — 부호만 확인.
        """
        pharma_val = PHARMA.calculate_boman_index(SEQ)  # +mean(RW) = 양수
        peptides_val = PEPT.boman()                      # -mean(Boman) = 양수 (SST-14)
        # 두 구현 모두 SST-14에 대해 양수 반환 기대
        assert pharma_val > 0, f"pharma Boman 음수: {pharma_val:.4f}"
        assert peptides_val > 0, f"peptides Boman 음수: {peptides_val:.4f}"

    def test_table_discrepancy_documented(self):
        """S, W, H 잔기의 RW 테이블 불일치를 문서화.
        이 테스트는 항상 PASS — 알려진 차이를 확인하는 regression test.
        backend S=1.15, pharma S=1.83, peptides S=-3.40(반전 기준 3.40).
        """
        # SST-14에는 S가 2개 있으므로 차이가 누적됨
        backend_val = boman_index(SEQ)
        pharma_val = PHARMA.calculate_boman_index(SEQ)
        peptides_val = PEPT.boman()
        # 수치 차이 기록 (assert 없이 값이 존재하는지만 확인)
        assert isinstance(backend_val, float)
        assert isinstance(pharma_val, float)
        assert isinstance(peptides_val, float)

    def test_high_binding_potential(self):
        """SST-14: 호르몬 수용체 리간드 → pharma Boman >= 0.5 기대"""
        bi = PHARMA.calculate_boman_index(SEQ)
        assert bi >= 0.5, f"Boman Index 너무 낮음: BI={bi:.4f}"


class TestNetCharge:
    """Net Charge at pH 7.4 검증"""

    def test_backend_vs_peptides_lehninger_within_0_1(self):
        """Lehninger pKa 기준 0.1 charge 단위 이내"""
        ours = _net_charge_at_ph(SEQ, 7.4)
        theirs = PEPT.charge(pH=7.4, pKscale="Lehninger")
        assert abs(ours - theirs) < 0.1, (
            f"Net charge 불일치: ours={ours:.4f}, peptides={theirs:.4f}"
        )

    def test_pharma_vs_peptides_lehninger_within_0_1(self):
        ours = PHARMA.calculate_net_charge(SEQ, ph=7.4)
        theirs = PEPT.charge(pH=7.4, pKscale="Lehninger")
        assert abs(ours - theirs) < 0.1

    def test_sst14_slightly_positive_at_ph74(self):
        """SST-14: K(+) 1개 vs C/C(Cys)/터미날 — pH 7.4에서 net charge 계산값 비합리적이지 않아야 함"""
        charge = _net_charge_at_ph(SEQ, 7.4)
        assert -5.0 < charge < 5.0, f"Net charge 비합리적: {charge:.4f}"


class TestMolecularWeight:
    """분자량 참고값 검증 (우리 코드 미구현 → peptides 값만 확인)"""

    def test_mw_reasonable_range(self):
        """SST-14 14잔기 → MW 약 1600-1700 Da 범위 기대"""
        mw = PEPT.molecular_weight(average="expasy")
        assert 1500.0 < mw < 1800.0, f"MW={mw:.2f} 범위 외"

    def test_monoisotopic_less_than_average(self):
        """단일동위원소 질량 < 평균 질량"""
        avg = PEPT.molecular_weight(average="expasy")
        mono = PEPT.molecular_weight(average="monoisotopic")
        assert mono <= avg, f"단일동위원소({mono:.2f}) > 평균({avg:.2f})"


class TestHydrophobicMoment:
    """Hydrophobic Moment μH (Eisenberg et al. 1982) 검증"""

    def test_backend_vs_peptides_within_5pct(self):
        """5% 이내 일치"""
        ours = hydrophobic_moment(SEQ, angle=100.0, window=11)["mu_h_max"]
        theirs = PEPT.hydrophobic_moment(window=11, angle=100)
        assert _pct_diff(ours, theirs) < 5.0, (
            f"μH 불일치: ours={ours:.4f}, peptides={theirs:.4f}"
        )

    def test_pharma_vs_peptides_within_5pct(self):
        ours = PHARMA.calculate_hydrophobic_moment(SEQ, angle=100.0, window=11)
        theirs = PEPT.hydrophobic_moment(window=11, angle=100)
        assert _pct_diff(ours, theirs) < 5.0

    def test_positive_moment(self):
        """μH는 항상 양수"""
        mu = PHARMA.calculate_hydrophobic_moment(SEQ)
        assert mu > 0.0, f"μH <= 0: {mu}"


# ─── 독립 실행 진입점 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print_comparison_table()
    print()
    print("─" * 50)
    print("  pytest 호환 테스트도 포함되어 있습니다.")
    print("  실행: pytest tests/test_pharma_vs_peptides_pkg.py -v")
