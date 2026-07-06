def test_shape_small():
    from omega_patent_thesis_t.completeness import completeness_score
    from omega_patent_thesis_t.seed import example_seed
    from omega_patent_thesis_t.shape import shape_label

    item = example_seed()
    assert completeness_score(item) == 1.0
    assert shape_label(item) == "full"
