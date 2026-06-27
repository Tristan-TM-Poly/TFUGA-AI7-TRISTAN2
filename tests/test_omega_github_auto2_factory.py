import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_github_auto2_factory.py"
CONFIG = ROOT / "configs" / "omega_github_auto2_top1024.json"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_github_auto2_factory", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaGitHubAuto2FactoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.config = cls.module.load_config(str(CONFIG))
        cls.cards = cls.module.build_cards(cls.config)

    def test_top1024_invariant(self):
        self.assertEqual(len(self.cards), 1024)
        self.assertEqual(len({card["slug"] for card in self.cards}), 1024)

    def test_top16_focus_cards_exist(self):
        slugs = {card["slug"] for card in self.cards}
        for slug in self.module.TOP16_FOCUS:
            self.assertIn(slug, slugs)

    def test_p0_cards_are_present(self):
        p0 = [card for card in self.cards if card["priority"] == "P0"]
        self.assertGreaterEqual(len(p0), 16)
        self.assertTrue(any(card["sector"] == "api_gateway" for card in p0))
        self.assertTrue(any(card["sector"] == "spike_removal" for card in p0))
        self.assertTrue(any(card["sector"] == "pilot_proposals" for card in p0))

    def test_human_review_for_stealth_and_pricing(self):
        stealth = set(self.config["stealth_ip_sectors"])
        self.assertTrue(all(card["human_review"] for card in self.cards if card["sector"] in stealth))
        self.assertTrue(all(card["human_review"] for card in self.cards if card["atom"] == "pricing_meter"))

    def test_oak_tribunal_passes_with_locks(self):
        report = self.module.oak_tribunal(self.cards, self.config)
        self.assertEqual(report["status"], "PASS_WITH_LOCKS")
        self.assertTrue(report["judges"]["structure"])
        self.assertTrue(report["judges"]["revenue_claim_safety"])
        self.assertGreater(report["counts"]["human_review_cards"], 0)

    def test_dependency_graph_points_to_slugs(self):
        slugs = {card["slug"] for card in self.cards}
        for card in self.cards:
            for dep in card["depends_on"]:
                self.assertIn(dep, slugs)


if __name__ == "__main__":
    unittest.main()
