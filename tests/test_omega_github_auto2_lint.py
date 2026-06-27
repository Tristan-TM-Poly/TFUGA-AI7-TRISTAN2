import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
FACTORY_SCRIPT = ROOT / "scripts" / "omega_github_auto2_factory.py"
LINT_SCRIPT = ROOT / "scripts" / "omega_github_auto2_lint.py"
CONFIG = ROOT / "configs" / "omega_github_auto2_top1024.json"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OmegaGitHubAuto2LintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.factory = load(FACTORY_SCRIPT, "factory")
        cls.linter = load(LINT_SCRIPT, "linter")
        cls.config = cls.factory.load_config(str(CONFIG))
        cls.cards = cls.factory.build_cards(cls.config)

    def test_valid_cards_pass_lint(self):
        self.assertEqual(self.linter.lint_cards(self.cards), [])

    def test_duplicate_slugs_fail_lint(self):
        bad = [dict(card) for card in self.cards]
        bad[1]["slug"] = bad[0]["slug"]
        errors = self.linter.lint_cards(bad)
        self.assertTrue(any("not unique" in error for error in errors))

    def test_sensitive_card_without_review_fails_lint(self):
        bad = [dict(card) for card in self.cards]
        target = next(card for card in bad if card["disclosure_level"] == "patent_review")
        target["human_review"] = False
        errors = self.linter.lint_cards(bad)
        self.assertTrue(any("sensitive card lacks human review" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
