def test_record_flow():
    from omega_patent_thesis_t.route import route_label
    from omega_patent_thesis_t.seed import example_seed
    from omega_patent_thesis_t.stage import record_stage

    item = example_seed()
    assert record_stage(item) == "C"
    assert route_label(item) == "make_pack"
