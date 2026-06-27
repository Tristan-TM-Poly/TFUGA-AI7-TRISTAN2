import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "omega_auto2_issue_planner_v4.py"


def load_module():
    spec = importlib.util.spec_from_file_location("omega_auto2_issue_planner_v4", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaAuto2IssuePlannerV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_select_cards_respects_allowlist_order_and_limit(self):
        cards = [
            {"slug": "usage_metering_core_algorithm_v1"},
            {"slug": "api_gateway_input_schema_v1"},
            {"slug": "api_gateway_output_schema_v1"},
        ]
        selected = self.module.select_cards(cards, 2)
        self.assertEqual([card["slug"] for card in selected], [
            "api_gateway_input_schema_v1",
            "api_gateway_output_schema_v1",
        ])

    def test_issue_title(self):
        card = {"slug": "api_gateway_input_schema_v1"}
        self.assertEqual(self.module.issue_title(card), "Omega AUTO2 P0: api_gateway_input_schema_v1")

    def test_issue_body_mentions_oak_and_metadata(self):
        card = {
            "slug": "api_gateway_input_schema_v1",
            "domain": "platform_api",
            "sector": "api_gateway",
            "atom": "input_schema",
            "priority": "P0",
            "score": 88.0,
            "disclosure_level": "public",
            "human_review": False,
        }
        body = self.module.issue_body(card, control_issue=112)
        self.assertIn("Parent control issue: #112", body)
        self.assertIn("OAK checks", body)
        self.assertIn("api_gateway_input_schema_v1", body)


if __name__ == "__main__":
    unittest.main()
