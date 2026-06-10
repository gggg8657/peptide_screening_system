"""
Tests for SS bond Cys correction and MW in backend/pharmacology.py.

Covers:
- _net_charge_at_ph with ss_bond_cysteines
- isoelectric_point with ss_bond_cysteines
- charge_ph_profile with ss_bond_cysteines
- molecular_weight function
- compute_pharmacology integration (auto SS bond inference + MW key)
"""

from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)),
)

from backend.pharmacology import (
    _net_charge_at_ph,
    isoelectric_point,
    charge_ph_profile,
    molecular_weight,
    compute_pharmacology,
    protease_cleavage_sites,
    metal_coordination,
)

SST14 = "AGCKNFFWKTFTSC"
SST14_SS = {2, 13}  # Cys3 (idx 2) and Cys14 (idx 13)


# ─── _net_charge_at_ph ───────────────────────────────────────────────────────


class TestNetChargeAtPhSS(unittest.TestCase):

    def test_backward_compat_none(self):
        c1 = _net_charge_at_ph(SST14, 7.4)
        c2 = _net_charge_at_ph(SST14, 7.4, ss_bond_cysteines=None)
        self.assertAlmostEqual(c1, c2, places=10)

    def test_ss_bond_raises_charge(self):
        c_free = _net_charge_at_ph(SST14, 7.4)
        c_ss = _net_charge_at_ph(SST14, 7.4, ss_bond_cysteines=SST14_SS)
        self.assertGreater(c_ss, c_free)

    def test_empty_set_equals_free(self):
        c_free = _net_charge_at_ph(SST14, 7.4)
        c_empty = _net_charge_at_ph(SST14, 7.4, ss_bond_cysteines=set())
        self.assertAlmostEqual(c_free, c_empty, places=10)


# ─── isoelectric_point ───────────────────────────────────────────────────────


class TestIsoelectricPointSS(unittest.TestCase):

    def test_backward_compat_default(self):
        """No ss_bond_cysteines arg → same as None."""
        pi1 = isoelectric_point(SST14)
        pi2 = isoelectric_point(SST14, ss_bond_cysteines=None)
        self.assertAlmostEqual(pi1, pi2, places=10)

    def test_pi_increases_with_ss_bond(self):
        pi_free = isoelectric_point(SST14)
        pi_ss = isoelectric_point(SST14, ss_bond_cysteines=SST14_SS)
        self.assertGreater(pi_ss, pi_free)

    def test_sst14_baseline_pi(self):
        """Historical SST-14 pI ≈ 9.04 (free Cys)."""
        pi = isoelectric_point(SST14)
        self.assertAlmostEqual(pi, 9.04, delta=0.05)

    def test_sst14_corrected_pi(self):
        """SS-corrected pI ≈ 10.62."""
        pi = isoelectric_point(SST14, ss_bond_cysteines=SST14_SS)
        self.assertAlmostEqual(pi, 10.62, delta=0.10)

    def test_polylys_unaffected(self):
        """Polylysine has no Cys — SS set has no effect."""
        pi = isoelectric_point("KKKK")
        pi_ss = isoelectric_point("KKKK", ss_bond_cysteines={0, 1})
        self.assertAlmostEqual(pi, pi_ss, places=10)


# ─── charge_ph_profile ───────────────────────────────────────────────────────


class TestChargePHProfileSS(unittest.TestCase):

    def test_backward_compat_no_arg(self):
        p1 = charge_ph_profile(SST14)
        p2 = charge_ph_profile(SST14, ss_bond_cysteines=None)
        self.assertEqual(p1["charge_at_ph74"], p2["charge_at_ph74"])

    def test_ss_bond_changes_profile(self):
        p_free = charge_ph_profile(SST14)
        p_ss = charge_ph_profile(SST14, ss_bond_cysteines=SST14_SS)
        self.assertGreater(p_ss["charge_at_ph74"], p_free["charge_at_ph74"])

    def test_profile_has_required_keys(self):
        p = charge_ph_profile(SST14, ss_bond_cysteines=SST14_SS)
        self.assertIn("charge_at_ph74", p)
        self.assertIn("charge_at_ph65", p)
        self.assertIn("delta_charge_tumor_vs_plasma", p)
        self.assertIn("profile", p)


# ─── molecular_weight ────────────────────────────────────────────────────────


class TestMolecularWeight(unittest.TestCase):

    def test_sst14_reduced_matches_reference(self):
        """SST-14 reduced form should match peptides-package 1639.91 ±1 Da."""
        mw = molecular_weight(SST14, n_disulfide=0)
        self.assertAlmostEqual(mw["mw_average"], 1639.91, delta=1.0)

    def test_ss_bond_reduces_mw_by_2016(self):
        mw_red = molecular_weight(SST14, n_disulfide=0)
        mw_ss = molecular_weight(SST14, n_disulfide=1)
        self.assertAlmostEqual(
            mw_red["mw_average"] - mw_ss["mw_average"], 2.016, delta=0.01
        )

    def test_required_keys(self):
        mw = molecular_weight(SST14)
        for k in ("mw_average", "mw_monoisotopic", "n_residues", "n_disulfide"):
            self.assertIn(k, mw)

    def test_n_residues(self):
        self.assertEqual(molecular_weight(SST14)["n_residues"], 14)

    def test_monoisotopic_lte_average(self):
        mw = molecular_weight(SST14, n_disulfide=1)
        self.assertLessEqual(mw["mw_monoisotopic"], mw["mw_average"])

    def test_single_glycine(self):
        mw = molecular_weight("G", n_disulfide=0)
        self.assertAlmostEqual(mw["mw_average"], 75.07, delta=0.1)

    def test_polyalanine_5mer(self):
        seq = "AAAAA"
        mw = molecular_weight(seq, n_disulfide=0)
        expected = 89.09 * 5 - 4 * 18.015
        self.assertAlmostEqual(mw["mw_average"], expected, delta=0.1)

    def test_empty_sequence_returns_error(self):
        result = molecular_weight("")
        self.assertIn("error", result)

    def test_n_disulfide_stored(self):
        mw = molecular_weight(SST14, n_disulfide=3)
        self.assertEqual(mw["n_disulfide"], 3)


# ─── compute_pharmacology integration ────────────────────────────────────────


class TestComputePharmacologyIntegration(unittest.TestCase):

    def test_molecular_weight_key_present(self):
        result = compute_pharmacology(SST14)
        self.assertIn("molecular_weight", result)

    def test_sst14_mw_near_reference(self):
        """compute_pharmacology uses n_ss=1 for SST-14 → mw close to 1637.9."""
        result = compute_pharmacology(SST14)
        mw = result["molecular_weight"]["mw_average"]
        self.assertAlmostEqual(mw, 1637.9, delta=1.0)

    def test_isoelectric_point_corrected(self):
        """compute_pharmacology must apply SS bond correction for even Cys count."""
        result = compute_pharmacology(SST14)
        pi_corrected = result["isoelectric_point"]
        pi_free = isoelectric_point(SST14)  # no correction
        self.assertGreater(pi_corrected, pi_free)

    def test_charge_profile_corrected(self):
        result = compute_pharmacology(SST14)
        c74_corrected = result["charge_ph_profile"]["charge_at_ph74"]
        c74_free = charge_ph_profile(SST14)["charge_at_ph74"]
        self.assertGreater(c74_corrected, c74_free)

    def test_odd_cys_no_correction(self):
        """Odd Cys count → no auto-correction."""
        seq = "AGCKNFFWKTFTCC"  # 3 Cys
        result = compute_pharmacology(seq)
        pi_all = result["isoelectric_point"]
        pi_free = isoelectric_point(seq)
        self.assertAlmostEqual(pi_all, pi_free, places=10)

    def test_no_cys_no_correction(self):
        seq = "AGKNFFWKTFTS"
        result = compute_pharmacology(seq)
        pi_all = result["isoelectric_point"]
        pi_free = isoelectric_point(seq)
        self.assertAlmostEqual(pi_all, pi_free, places=10)


# ─── protease_cleavage_sites: DPP-IV ────────────────────────────────────────


class TestProteaseDPPIV(unittest.TestCase):
    """B9: DPP-IV cleavage sites in backend/pharmacology.py."""

    def test_dppiv_key_present(self):
        """dppiv key must be returned for any sequence."""
        r = protease_cleavage_sites(SST14)
        self.assertIn("dppiv", r)

    def test_sst14_no_dppiv(self):
        """SST-14 pos 2 = G → no DPP-IV site."""
        r = protease_cleavage_sites(SST14)
        self.assertEqual(r["dppiv"]["count"], 0)

    def test_glp1_pattern_pos2_ala(self):
        """GLP-1 His-Ala start → Ala at pos 2, DPP-IV site at position 2."""
        glp1 = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
        r = protease_cleavage_sites(glp1)
        self.assertGreater(r["dppiv"]["count"], 0)
        self.assertIn(2, r["dppiv"]["positions"])

    def test_pro_pro_resistance(self):
        """X-Pro-Pro: Pro blocked by downstream Pro."""
        r = protease_cleavage_sites("APPNFFWK")
        self.assertNotIn(2, r["dppiv"]["positions"])

    def test_total_sites_includes_dppiv(self):
        """total_sites must equal sum of all five proteases."""
        glp1 = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
        r = protease_cleavage_sites(glp1)
        expected = (
            r["chymotrypsin"]["count"]
            + r["trypsin"]["count"]
            + r["neprilysin"]["count"]
            + r["pepsin"]["count"]
            + r["dppiv"]["count"]
        )
        self.assertEqual(r["total_sites"], expected)


# ─── metal_coordination: Ga3+ from D/E ──────────────────────────────────────


class TestMetalCoordinationGa3(unittest.TestCase):
    """B10: Ga3+ coordination via Asp/Glu carboxylate in backend/pharmacology.py."""

    def test_sst14_no_de_no_ga3(self):
        """SST-14 has no D/E → Ga3+ only if His present; SST-14 has no His either."""
        r = metal_coordination(SST14)
        metals_flat = [
            m for res in r["coordinating_residues"] for m in res["preferred_metals"]
        ]
        # SST-14: C,C only → no Ga3+ source
        self.assertNotIn("Ga³⁺", metals_flat)

    def test_asp_yields_ga3(self):
        """Sequence with D → Ga3+ in preferred_metals for that residue."""
        r = metal_coordination("AGDKNFFWKTFTSC")
        asp_residues = [
            res for res in r["coordinating_residues"] if res["residue"] == "D"
        ]
        self.assertTrue(len(asp_residues) > 0)
        for res in asp_residues:
            self.assertIn("Ga³⁺", res["preferred_metals"])

    def test_glu_yields_ga3(self):
        """Sequence with E → Ga3+ in preferred_metals for that residue."""
        r = metal_coordination("AGEKN")
        glu_residues = [
            res for res in r["coordinating_residues"] if res["residue"] == "E"
        ]
        self.assertTrue(len(glu_residues) > 0)
        for res in glu_residues:
            self.assertIn("Ga³⁺", res["preferred_metals"])

    def test_his_still_has_ga3(self):
        """His coordination entry still includes Ga3+ (backward compat)."""
        r = metal_coordination("HAGKNFFWKTFTSC")
        his_residues = [
            res for res in r["coordinating_residues"] if res["residue"] == "H"
        ]
        self.assertTrue(len(his_residues) > 0)
        for res in his_residues:
            self.assertIn("Ga³⁺", res["preferred_metals"])


if __name__ == "__main__":
    unittest.main()
