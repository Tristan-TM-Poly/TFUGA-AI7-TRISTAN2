from tools.useful_work_catalog import list_work_options


def test_catalog_returns_limited_options():
    options = list_work_options(3)
    assert len(options) == 3
    assert options[0] == "create_index"


def test_catalog_handles_zero_limit():
    assert list_work_options(0) == ()
