from pipelines.silo_b.src.filters import DrugabilityFilter, DuplicateFilter


def test_ng_deamidation_detection() -> None:
    seq = "AGCNGSFFWKTFTSC"
    f = DrugabilityFilter()
    assert f.check_ng_deamidation(seq) == [4]


def test_dg_isomerization_detection() -> None:
    seq = "AGCDGFWKTFTSC"
    f = DrugabilityFilter()
    assert f.check_dg_isomerization(seq) == [4]


def test_met_oxidation_detection() -> None:
    seq = "AGCMNFFWKTFTSC"
    f = DrugabilityFilter()
    assert f.check_met_oxidation(seq) == [4]


def test_hamming_distance() -> None:
    df = DuplicateFilter()
    assert df.hamming_distance("AAAA", "AAAB") == 1


def test_duplicate_filter() -> None:
    df = DuplicateFilter(min_hamming_distance=3)
    assert df.add_sequence("AGCKNFFWKTFTSC") is True
    assert df.add_sequence("AGCKNFFWKTFTCC") is False
    assert df.get_unique_count() == 1


def test_clean_sequence_passes() -> None:
    wildcard = "AGCKNFFWKTFTSC"
    df = DrugabilityFilter()
    result = df.filter_candidate(wildcard)
    assert result.passed
    assert result.ng_positions == []
    assert result.dg_positions == []
    assert result.met_positions == []
    assert not result.rejection_reasons
