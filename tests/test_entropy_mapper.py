from tools.entropy_mapper import map_entropy


def test_large_pr_gets_high_entropy_signals():
    report = map_entropy(scope="PR220", changed_files=156, additions=9955, connector_residue=5)
    names = {signal.name for signal in report.signals}
    assert "large_file_count" in names
    assert "large_addition_count" in names
    assert "connector_residue" in names


def test_small_scope_is_stable_size():
    report = map_entropy(scope="small", changed_files=2, additions=20)
    assert report.signals[0].name == "stable_size"
