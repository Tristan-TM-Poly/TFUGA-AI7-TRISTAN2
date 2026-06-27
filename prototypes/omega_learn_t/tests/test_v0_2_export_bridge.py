from omega_learn_t.core import ErrorRecord, SkillSpec
from omega_learn_t.exporters import export_cards_csv
from omega_learn_t.github_bridge import issue_markdown
from omega_learn_t.memory_codec import cards_from_errors


def test_v0_2_export_and_bridge(tmp_path):
    cards = cards_from_errors([ErrorRecord(name="r", cause="c", correction="fix", future_test="test")])
    out = export_cards_csv(cards, tmp_path / "cards.csv")
    assert out.exists()
    assert "front,back,tags,due,card_type" in out.read_text(encoding="utf-8")

    spec = SkillSpec.from_mapping({"skill": "bridge", "goal": "make issue", "notes": "alpha alpha beta"})
    md = issue_markdown(spec, "learning_goal")
    assert "Learning Goal" in md
    assert "bridge" in md
