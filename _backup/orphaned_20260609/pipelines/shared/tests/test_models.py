import json

from pipelines.shared.models import (
    CrossSiloManifest,
    Modality,
    Silo,
    UnifiedCandidate,
)


class TestUnifiedCandidate:
    def _sample(self, **overrides) -> UnifiedCandidate:
        defaults = dict(
            id="test_001",
            silo=Silo.SILO_A,
            modality=Modality.SMALL_MOL,
            structure="CCO",
            raw_scores={"qed": 0.8, "dock_confidence": 0.9},
            bridge_metrics={"dg_est": -7.5, "feasibility": 0.8},
            confidence=0.9,
            provenance={"run_id": "r001", "arm": "arm1_smallmol"},
        )
        defaults.update(overrides)
        return UnifiedCandidate(**defaults)

    def test_create_silo_a(self):
        c = self._sample()
        assert c.silo == Silo.SILO_A
        assert c.modality == Modality.SMALL_MOL
        assert c.structure == "CCO"

    def test_create_silo_b(self):
        c = self._sample(
            id="silo_b_001",
            silo=Silo.SILO_B,
            modality=Modality.SST14_MUTANT,
            structure="AGCKNFFWKTFTSC",
            raw_scores={"dg": -8.5, "stability": 0.9},
        )
        assert c.silo == Silo.SILO_B
        assert c.modality == Modality.SST14_MUTANT

    def test_to_dict_serializable(self):
        c = self._sample()
        d = c.to_dict()
        assert d["silo"] == "silo_a"
        assert d["modality"] == "small_mol"
        assert isinstance(d["raw_scores"], dict)

    def test_to_json_roundtrip(self):
        c = self._sample()
        j = c.to_json()
        parsed = json.loads(j)
        restored = UnifiedCandidate.from_dict(parsed)
        assert restored.id == c.id
        assert restored.silo == c.silo
        assert restored.raw_scores == c.raw_scores

    def test_from_dict(self):
        data = {
            "id": "x",
            "silo": "silo_b",
            "modality": "de_novo",
            "structure": "MKTV",
            "raw_scores": {"plddt": 85.0},
            "confidence": 0.7,
        }
        c = UnifiedCandidate.from_dict(data)
        assert c.silo == Silo.SILO_B
        assert c.modality == Modality.DE_NOVO
        assert c.confidence == 0.7

    def test_bridge_metrics_defaults(self):
        c = UnifiedCandidate(
            id="bare",
            silo=Silo.SILO_A,
            modality=Modality.PEPTIDE_VARIANT,
            structure="AGCK",
            raw_scores={},
        )
        assert c.bridge_metrics == {}
        assert c.confidence == 0.0

    def test_all_modalities(self):
        for m in Modality:
            c = self._sample(modality=m)
            assert c.modality == m


class TestCrossSiloManifest:
    def test_empty_manifest(self):
        m = CrossSiloManifest(run_id="r1", timestamp="2026-02-20T12:00:00Z")
        assert m.total_candidates == 0
        assert m.candidates == []

    def test_manifest_with_candidates(self):
        c1 = UnifiedCandidate(
            id="a", silo=Silo.SILO_A, modality=Modality.SMALL_MOL,
            structure="C", raw_scores={"qed": 0.5},
        )
        c2 = UnifiedCandidate(
            id="b", silo=Silo.SILO_B, modality=Modality.SST14_MUTANT,
            structure="AGCK", raw_scores={"dg": -7.0},
        )
        m = CrossSiloManifest(
            run_id="r2", timestamp="2026-02-20",
            total_candidates=2, silo_a_count=1, silo_b_count=1,
            candidates=[c1, c2],
        )
        j = m.to_json()
        parsed = json.loads(j)
        assert parsed["total_candidates"] == 2
        assert len(parsed["candidates"]) == 2
        assert parsed["candidates"][0]["silo"] == "silo_a"
        assert parsed["candidates"][1]["silo"] == "silo_b"
