from omega_git_jkd import default_events, size_mode, summarize


def test_events_exist():
    items = default_events()
    assert len(items) == 3


def test_summary_counts():
    report = summarize(default_events())
    assert report["events"] == 3


def test_size_mode():
    assert size_mode(20) == "small"
    assert size_mode(121) == "split"
