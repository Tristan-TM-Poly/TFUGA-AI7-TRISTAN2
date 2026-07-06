from omega_patent_thesis_t.count import count_records
from omega_patent_thesis_t.level_summary import level_summary
from omega_patent_thesis_t.seed import example_seed


def test_count_records():
    items = (example_seed(), example_seed())
    assert count_records(items) == 2


def test_level_summary():
    items = (example_seed(),)
    assert level_summary(items)["review"] == 1
