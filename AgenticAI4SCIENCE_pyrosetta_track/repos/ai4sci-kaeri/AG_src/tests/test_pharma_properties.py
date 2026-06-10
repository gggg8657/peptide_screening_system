"""
Tests for the pharmacological property calculator module.

Covers all 13 calculation methods and 5 structural rules using
known properties of SST-14 (AGCKNFFWKTFTSC) and mutant analogs.
"""

import math
import sys
import os
import unittest

# Ensure the AG_src package is importable
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    ),
)

from AG_src.pipeline.pharma_properties import PharmaProperties


SST14 = "AGCKNFFWKTFTSC"


class TestPharmaPropertiesInit(unittest.TestCase):
    """Construction and validation."""

    def test_default_reference(self):
        pp = PharmaProperties()
        self.assertEqual(pp.reference_seq, SST14)

    def test_empty_sequence_raises(self):
        pp = PharmaProperties()
        with self.assertRaises(ValueError):
            pp.calculate_gravy("")

    def test_invalid_characters_raise(self):
        pp = PharmaProperties()
        with self.assertRaises(ValueError):
            pp.calculate_gravy("AGCKNFFWKTFTS1")

    def test_lowercase_accepted(self):
        pp = PharmaProperties()
        g1 = pp.calculate_gravy("AGCKNFFWKTFTSC")
        g2 = pp.calculate_gravy("agcknffwktftsc")
        self.assertAlmostEqual(g1, g2)


class TestGRAVY(unittest.TestCase):
    """Method 1: Kyte-Doolittle GRAVY."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_near_zero(self):
        """SST-14 GRAVY ≈ 0.03 (3 Phe + 2 Cys offset hydrophilic residues)."""
        gravy = self.pp.calculate_gravy(SST14)
        self.assertAlmostEqual(gravy, 0.029, delta=0.1)

    def test_all_ala(self):
        """Polyalanine GRAVY should be exactly 1.8."""
        self.assertAlmostEqual(self.pp.calculate_gravy("AAAA"), 1.8)

    def test_all_lys(self):
        """Polylysine is strongly hydrophilic."""
        self.assertAlmostEqual(self.pp.calculate_gravy("KKKK"), -3.9)


class TestBomanIndex(unittest.TestCase):
    """Method 2: Boman Index."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_moderate_binding(self):
        """SST-14 BI ≈ 0.60 — moderate binding (3 Phe reduce mean solubility)."""
        bi = self.pp.calculate_boman_index(SST14)
        self.assertGreater(bi, 0.0)
        self.assertAlmostEqual(bi, 0.598, delta=0.1)


class TestInstabilityIndex(unittest.TestCase):
    """Method 3: Instability Index (Guruprasad)."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_returns_float(self):
        ii = self.pp.calculate_instability_index(SST14)
        self.assertIsInstance(ii, float)

    def test_single_residue(self):
        """Single residue → 0.0 (no dipeptides)."""
        self.assertAlmostEqual(self.pp.calculate_instability_index("A"), 0.0)


class TestAliphaticIndex(unittest.TestCase):
    """Method 4: Aliphatic Index."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_value(self):
        ai = self.pp.calculate_aliphatic_index(SST14)
        # SST-14 has no Ala(0%), no Val, no Ile, no Leu → AI = 0 ... wait
        # SST-14 = AGCKNFFWKTFTSC → A at pos 1 → X(Ala) = 100*1/14 ≈ 7.14
        # no Val, Ile, Leu → AI ≈ 7.14
        self.assertGreater(ai, 0)

    def test_all_ala(self):
        """Pure Ala → AI = 100."""
        self.assertAlmostEqual(self.pp.calculate_aliphatic_index("AAAA"), 100.0)


class TestIsoelectricPoint(unittest.TestCase):
    """Method 5: pI calculation."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_pi_range(self):
        """pI should be physiological range for SST-14."""
        pi = self.pp.calculate_pi(SST14)
        self.assertGreater(pi, 5.0)
        self.assertLess(pi, 12.0)

    def test_all_asp(self):
        """Polyaspartate should be very acidic."""
        pi = self.pp.calculate_pi("DDDD")
        self.assertLess(pi, 4.0)


class TestExtinctionCoefficient(unittest.TestCase):
    """Method 6: ε₂₈₀."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_has_trp(self):
        """SST-14 has 1 Trp → ε₂₈₀ >= 5500."""
        ec = self.pp.calculate_extinction_coefficient(SST14)
        self.assertGreaterEqual(ec, 5500)

    def test_with_disulfide(self):
        """Including 1 disulfide bond adds 125."""
        ec_no_ss = self.pp.calculate_extinction_coefficient(SST14, n_disulfide=0)
        ec_ss = self.pp.calculate_extinction_coefficient(SST14, n_disulfide=1)
        self.assertEqual(ec_ss - ec_no_ss, 125)

    def test_no_aromatics(self):
        """Sequence without Trp/Tyr → ε = 0."""
        self.assertEqual(
            self.pp.calculate_extinction_coefficient("AAAKK"), 0
        )


class TestNendRuleHalflife(unittest.TestCase):
    """Method 7: N-end rule."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_ala_stable(self):
        """SST-14 starts with Ala → stable (>30 h)."""
        result = self.pp.calculate_nend_rule_halflife(SST14)
        self.assertEqual(result["n_terminal_residue"], "A")
        self.assertGreater(result["half_life_hours"], 30.0 - 0.1)
        self.assertEqual(result["category"], "stable")

    def test_arg_very_unstable(self):
        result = self.pp.calculate_nend_rule_halflife("RAAAAA")
        self.assertEqual(result["category"], "very_unstable")
        self.assertLessEqual(result["half_life_hours"], 1.0)


class TestHydrophobicMoment(unittest.TestCase):
    """Method 8: Eisenberg hydrophobic moment."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_returns_positive(self):
        mu = self.pp.calculate_hydrophobic_moment(SST14)
        self.assertGreater(mu, 0.0)

    def test_beta_sheet_angle(self):
        mu_beta = self.pp.calculate_hydrophobic_moment(SST14, angle=160.0)
        self.assertIsInstance(mu_beta, float)


class TestWimleyWhite(unittest.TestCase):
    """Method 9: Wimley-White interface energy."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_returns_dict(self):
        result = self.pp.calculate_wimley_white(SST14)
        self.assertIn("total_dG", result)
        self.assertIn("mean_dG", result)
        self.assertIn("per_residue", result)
        self.assertEqual(len(result["per_residue"]), 14)


class TestNetCharge(unittest.TestCase):
    """Method 10: Net charge at pH."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_positive_at_neutral(self):
        """SST-14 has Lys → positive charge at pH 7.4."""
        charge = self.pp.calculate_net_charge(SST14, ph=7.4)
        self.assertGreater(charge, 0)

    def test_more_positive_at_acidic(self):
        """Charge should be higher at pH 6.5 than 7.4."""
        c74 = self.pp.calculate_net_charge(SST14, ph=7.4)
        c65 = self.pp.calculate_net_charge(SST14, ph=6.5)
        self.assertGreater(c65, c74)


class TestProteaseSites(unittest.TestCase):
    """Method 11: Protease cleavage sites."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_has_sites(self):
        result = self.pp.count_protease_sites(SST14)
        # SST-14 has F, W, K, L, Y → should have some sites
        self.assertGreater(result["total"], 0)
        self.assertIn("chymotrypsin", result)
        self.assertIn("trypsin", result)
        self.assertIn("neprilysin", result)

    def test_dppiv_key_present(self):
        """dppiv key must exist in all results."""
        result = self.pp.count_protease_sites(SST14)
        self.assertIn("dppiv", result)
        self.assertIn("count", result["dppiv"])
        self.assertIn("positions", result["dppiv"])

    def test_sst14_no_dppiv_site(self):
        """SST-14 (AGCKNFFWKTFTSC): pos 2 = G(Gly), not P/A → no DPP-IV site."""
        result = self.pp.count_protease_sites(SST14)
        self.assertEqual(result["dppiv"]["count"], 0)

    def test_glp1_pattern_dppiv(self):
        """GLP-1 starts with His-Ala → pos 2 = Ala → DPP-IV site at position 2."""
        # HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR (GLP-1 7-36)
        glp1 = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
        result = self.pp.count_protease_sites(glp1)
        # Ala at position 2 (index 1), followed by E (not P) → site expected
        self.assertGreater(result["dppiv"]["count"], 0)
        self.assertIn(2, result["dppiv"]["positions"])

    def test_dppiv_pro_pro_resistance(self):
        """X-Pro-Pro: second Pro should NOT be a DPP-IV site (Pro-Pro resistance)."""
        # APP: Ala(1)-Pro(2)-Pro(3)-... → pos 2 is Pro but followed by Pro → no site
        seq = "APPNFFWK"
        result = self.pp.count_protease_sites(seq)
        # Position 2 = P, followed by P → blocked
        self.assertNotIn(2, result["dppiv"]["positions"])

    def test_dppiv_internal_xala_site(self):
        """Internal X-Ala (not last): should register as DPP-IV site."""
        seq = "GKAGFWK"  # Ala at index 2 (pos 3, 1-indexed), preceded by K, followed by G
        result = self.pp.count_protease_sites(seq)
        self.assertIn(3, result["dppiv"]["positions"])

    def test_total_includes_dppiv(self):
        """total count must equal sum of all four proteases including dppiv."""
        glp1 = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
        r = self.pp.count_protease_sites(glp1)
        expected = (
            r["chymotrypsin"]["count"]
            + r["trypsin"]["count"]
            + r["neprilysin"]["count"]
            + r["dppiv"]["count"]
        )
        self.assertEqual(r["total"], expected)


class TestBLOSUM62(unittest.TestCase):
    """Method 12: BLOSUM62 conservation score."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_identity_max_score(self):
        """SST-14 vs itself → all positions identical."""
        result = self.pp.calculate_blosum62_score(SST14)
        self.assertEqual(result["n_mutations"], 0)
        self.assertGreater(result["total_score"], 0)
        for pos in result["per_position"]:
            self.assertEqual(pos["category"], "identical")

    def test_single_mutation(self):
        """One position changed → n_mutations = 1."""
        mutant = "AGCKNFFWKTFTSA"  # C14→A
        result = self.pp.calculate_blosum62_score(mutant)
        self.assertEqual(result["n_mutations"], 1)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            self.pp.calculate_blosum62_score("AAAA")


class TestMetalCoordination(unittest.TestCase):
    """Method 13: Metal-coordinating residues."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_has_cys(self):
        """SST-14 has 2 Cys → thiolate coordination."""
        result = self.pp.analyze_metal_coordination(SST14)
        self.assertEqual(len(result["residues"]["Cys_thiolate"]), 2)
        self.assertGreater(result["total_coordinating"], 0)

    def test_sst14_ga3_from_his(self):
        """SST-14 has no H → Ga3+ not listed (no His coordination path)."""
        result = self.pp.analyze_metal_coordination(SST14)
        # SST-14: AGCKNFFWKTFTSC — no His, no Asp, no Glu
        self.assertNotIn("Ga3+", result["potential_metals"])

    def test_ga3_from_asp(self):
        """Asp-containing sequence → Ga3+ must appear in potential_metals."""
        seq = "AGCKNDFWKTFTSC"  # N5→D (Asn to Asp)
        result = self.pp.analyze_metal_coordination(seq)
        self.assertIn("Ga3+", result["potential_metals"])

    def test_ga3_from_glu(self):
        """Glu-containing sequence → Ga3+ must appear in potential_metals."""
        seq = "AGCKNEFWKTFTSC"  # N5→E (Asn to Glu)
        result = self.pp.analyze_metal_coordination(seq)
        self.assertIn("Ga3+", result["potential_metals"])

    def test_ga3_from_his_still_present(self):
        """His-coordination path still yields Ga3+."""
        seq = "AGCKNHFWKTFTSC"  # N5→H
        result = self.pp.analyze_metal_coordination(seq)
        self.assertIn("Ga3+", result["potential_metals"])

    def test_de_sequence_metals(self):
        """D/E-only sequence → Ca2+, Mg2+, Lu3+, Ac3+, Ga3+ all present."""
        seq = "ADEGFWK"
        result = self.pp.analyze_metal_coordination(seq)
        for metal in ["Ca2+", "Mg2+", "Lu3+", "Ac3+", "Ga3+"]:
            self.assertIn(metal, result["potential_metals"])

    def test_no_coord_residues(self):
        """Sequence with no coordinating residues → empty potential_metals."""
        seq = "AAANFFWKTT"
        result = self.pp.analyze_metal_coordination(seq)
        self.assertEqual(result["potential_metals"], [])


class TestStructuralRules(unittest.TestCase):
    """5 structural integrity rules."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_all_pass(self):
        """Native SST-14 must pass all 5 rules."""
        result = self.pp.check_structural_rules(SST14)
        self.assertTrue(result["all_pass"])
        for name, rule in result["rules"].items():
            self.assertTrue(rule["pass"], f"Rule {name} failed for native SST-14")

    def test_c14t_disulfide_fail(self):
        """Analog C14→T breaks Cys3-Cys14 disulfide."""
        analog = "AGCKNFFWKTFTST"  # position 14: C→T
        result = self.pp.check_structural_rules(analog)
        self.assertFalse(result["rules"]["cys3_cys14_disulfide"]["pass"])
        self.assertFalse(result["all_pass"])

    def test_fwkt_mutation_fail(self):
        """Changing the pharmacophore → FAIL."""
        analog = "AGCKNFAWKTFTSC"  # F7→A  → pos 7-10 = AWKT
        result = self.pp.check_structural_rules(analog)
        self.assertFalse(result["rules"]["fwkt_pharmacophore"]["pass"])

    def test_k9_mutation_fail(self):
        """K9→A breaks salt bridge."""
        analog = "AGCKNFFWATFTSC"
        result = self.pp.check_structural_rules(analog)
        self.assertFalse(result["rules"]["k9_salt_bridge"]["pass"])


class TestCalculateAll(unittest.TestCase):
    """Composite calculate_all method."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_sst14_complete(self):
        result = self.pp.calculate_all(SST14)
        self.assertEqual(result["sequence"], SST14)
        self.assertEqual(result["length"], 14)
        self.assertIn("gravy", result)
        self.assertIn("boman_index", result)
        self.assertIn("instability_index", result)
        self.assertIn("aliphatic_index", result)
        self.assertIn("isoelectric_point", result)
        self.assertIn("extinction_coefficient", result)
        self.assertIn("nend_rule_halflife", result)
        self.assertIn("hydrophobic_moment_alpha", result)
        self.assertIn("structural_rules", result)
        self.assertIn("blosum62", result)


class TestBatchAnalyze(unittest.TestCase):
    """Batch mode."""

    def setUp(self):
        self.pp = PharmaProperties()

    def test_batch(self):
        seqs = {
            "native": SST14,
            "c14t": "AGCKNFFWKTFTST",
        }
        results = self.pp.batch_analyze(seqs)
        self.assertIn("native", results)
        self.assertIn("c14t", results)
        self.assertTrue(results["native"]["structural_rules"]["all_pass"])
        self.assertFalse(results["c14t"]["structural_rules"]["all_pass"])


if __name__ == "__main__":
    unittest.main()
