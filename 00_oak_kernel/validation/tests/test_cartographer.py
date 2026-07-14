import copy
import importlib.util
import json
import unittest
import sys
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cartographer", ROOT / "cartographer.py")
cartographer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cartographer
assert SPEC.loader is not None
SPEC.loader.exec_module(cartographer)


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "pr_manifest.schema.json").read_text(encoding="utf-8"))
        cls.example = json.loads((ROOT / "pr_manifest.example.json").read_text(encoding="utf-8"))
        cls.evidence_schema = json.loads((ROOT / "evidence_record.schema.json").read_text(encoding="utf-8"))
        cls.validator = Draft7Validator(cls.schema)

    def errors(self, manifest):
        return list(self.validator.iter_errors(manifest))

    def test_valid_example(self):
        self.assertEqual([], self.errors(self.example))

    def test_unknown_property_is_rejected(self):
        bad = copy.deepcopy(self.example)
        bad["untyped_entropy"] = True
        self.assertTrue(self.errors(bad))

    def test_kernel_requires_baseline(self):
        bad = copy.deepcopy(self.example)
        bad["validation"]["baseline_comparison"] = {"required": False}
        self.assertTrue(self.errors(bad))

    def test_ci_passed_cannot_be_self_declared(self):
        bad = copy.deepcopy(self.example)
        bad["claim"]["status"] = "ci_passed"
        self.assertTrue(self.errors(bad))

    def test_evidence_schema_rejects_unknown_kind(self):
        raw = b'{"claim_id":"CLM-TEST-001","kind":"unknown","status":"pass"}\n'
        records, errors = cartographer.parse_ledger(raw, self.evidence_schema)
        self.assertEqual([], records)
        self.assertTrue(errors)

    def test_evidence_schema_accepts_canonical_record(self):
        raw = b'{"claim_id":"CLM-TEST-001","kind":"unit_test","status":"pass"}\n'
        records, errors = cartographer.parse_ledger(raw, self.evidence_schema)
        self.assertEqual(1, len(records))
        self.assertEqual([], errors)


class CoreTests(unittest.TestCase):
    def test_cycle_detection(self):
        cycles = cartographer.collect_cycles({1: [2], 2: [3], 3: [1], 4: []})
        self.assertIn([1, 2, 3, 1], cycles)

    def test_ledger_parser(self):
        raw = b'{"claim_id":"C","kind":"unit_test","status":"pass"}\n'
        records, errors = cartographer.parse_ledger(raw)
        self.assertEqual(1, len(records))
        self.assertEqual([], errors)

    def test_invalid_ledger_status(self):
        raw = b'{"claim_id":"C","kind":"unit_test","status":"maybe"}\n'
        records, errors = cartographer.parse_ledger(raw)
        self.assertEqual([], records)
        self.assertTrue(errors)

    def test_cli_supports_pr_number(self):
        parser = cartographer.build_parser()
        args = parser.parse_args(["--pr-number", "224"])
        self.assertEqual(224, args.pr_number)


if __name__ == "__main__":
    unittest.main()
