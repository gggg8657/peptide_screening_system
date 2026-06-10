import math

from pipelines.silo_b.src.relax import MockComplexRelaxer, RelaxResult


class TestMockComplexRelaxer:
    def setup_method(self):
        self.relaxer = MockComplexRelaxer()

    def test_relax_returns_result(self):
        result = self.relaxer.relax("AGCKNFFWKTFTSC", docked_pose_tag="test")
        assert isinstance(result, RelaxResult)
        assert result.success is True
        assert result.error_msg is None

    def test_relaxed_dg_is_negative(self):
        result = self.relaxer.relax("AGCKNFFWKTFTSC", docked_pose_tag="")
        assert result.relaxed_dg < 0.0

    def test_clash_score_non_negative(self):
        result = self.relaxer.relax("AGCKNFFWKTFTSC", docked_pose_tag="")
        assert result.clash_score >= 0.0

    def test_backbone_rmsd_positive(self):
        result = self.relaxer.relax("AGCKNFFWKTFTSC", docked_pose_tag="")
        assert result.backbone_rmsd > 0.0

    def test_components_contain_three_body(self):
        result = self.relaxer.relax("AGCKNFFWKTFTSC", docked_pose_tag="")
        assert "e_complex" in result.components
        assert "e_peptide" in result.components
        assert "e_receptor" in result.components
        assert "dg_bind" in result.components

    def test_hydrophobic_sequence_stronger_binding(self):
        hydro = self.relaxer.relax("AAAIIIILLLLFFWW", docked_pose_tag="")
        polar = self.relaxer.relax("RRRRDDDDEEEEKKK", docked_pose_tag="")
        assert hydro.relaxed_dg < polar.relaxed_dg

    def test_wall_time_recorded(self):
        result = self.relaxer.relax("AGCKNFFWKTFTSC", docked_pose_tag="")
        assert result.wall_time_s >= 0.0

    def test_interface_energy_proportional(self):
        result = self.relaxer.relax("AGCKNFFWKTFTSC", docked_pose_tag="")
        assert result.interface_energy != 0.0
