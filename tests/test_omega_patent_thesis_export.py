from omega_patent_thesis_t.export import export_pack
from omega_patent_thesis_t.review import review_card
from omega_patent_thesis_t.seed import example_seed
from omega_patent_thesis_t.summary import short_summary


def test_short_summary_mentions_record():
    text = short_summary(example_seed())
    assert "Technical Record Summary" in text
    assert "EXAMPLE-PATENT-T" in text


def test_review_card_has_boundary():
    card = review_card(example_seed())
    assert card["boundary"] == "structured review only"


def test_export_pack_contains_sections():
    pack = export_pack(example_seed())
    assert "summary" in pack
    assert "claim_tree" in pack
    assert "review" in pack
