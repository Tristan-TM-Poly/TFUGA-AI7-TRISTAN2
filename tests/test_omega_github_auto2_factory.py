import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_github_auto2_factory.py"
CONFIG = ROOT / "configs" / "omega_github_auto2_top1024.json"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_github_auto2_factory", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_top1024_invariant():
    module = load_module()
    config = module.load_config(str(CONFIG))
    cards = module.build_cards(config)
    assert len(cards) == 1024
    assert len({card["slug"] for card in cards}) == 1024


def test_p0_cards_are_present():
    module = load_module()
    config = module.load_config(str(CONFIG))
    cards = module.build_cards(config)
    p0 = [card for card in cards if card["priority"] == "P0"]
    assert len(p0) >= 16
    assert any(card["sector"] == "api_gateway" for card in p0)
    assert any(card["sector"] == "spike_removal" for card in p0)
    assert any(card["sector"] == "pilot_proposals" for card in p0)


def test_human_review_for_review_sectors_and_pricing():
    module = load_module()
    config = module.load_config(str(CONFIG))
    cards = module.build_cards(config)
    assert all(card["human_review"] for card in cards if card["sector"] in config["stealth_ip_sectors"])
    assert all(card["human_review"] for card in cards if card["atom"] == "pricing_meter")
