from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path

MODULE_PATH = Path("00_oak_kernel/validation/oakgate_v1.py")
SPEC = importlib.util.spec_from_file_location("oakgate_v1", MODULE_PATH)
oak = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = oak
assert SPEC.loader is not None
SPEC.loader.exec_module(oak)


class ClaimGraphTests(unittest.TestCase):
    def test_cycle_is_blocking(self):
        claims = [
            {"id": "CLM-A", "depends_on": ["CLM-B"]},
            {"id": "CLM-B", "depends_on": ["CLM-A"]},
        ]
        result = oak.claim_gate(claims)
        self.assertTrue(result.blocking)
        self.assertIn("CLAIM_DEPENDENCY_CYCLE", {f.code for f in result.findings})

    def test_missing_dependency_is_blocking(self):
        result = oak.claim_gate([{"id": "CLM-A", "depends_on": ["CLM-X"]}])
        self.assertIn("CLAIM_DEPENDENCY_MISSING", {f.code for f in result.findings})


class LedgerTests(unittest.TestCase):
    def schema(self):
        return json.loads(Path(".oak/schemas/evidence_record.schema.json").read_text())

    def record(self):
        value = {
            "evidence_id": "EVD-1",
            "claim_id": "CLM-A",
            "kind": "unit_test",
            "status": "pass",
            "producer": "test",
            "head_sha": "a" * 40,
            "base_sha": "b" * 40,
            "dependency_lock_hash": "c" * 64,
            "test_definition_hash": "d" * 64,
            "environment_hash": "e" * 64,
            "command": "python test",
            "exit_code": 0,
            "observed": "pass",
            "workflow_run_id": "1",
            "timestamp": "2026-07-14T00:00:00+00:00",
            "previous_record_sha256": oak.ZERO_HASH,
        }
        value["record_sha256"] = oak.record_hash(value)
        return value

    def test_tamper_is_detected(self):
        value = self.record()
        value["observed"] = "tampered"
        result = oak.ledger_gate([value], self.schema(), {"CLM-A"})
        self.assertIn("EVIDENCE_HASH_MISMATCH", {f.code for f in result.findings})

    def test_status_exit_contradiction(self):
        value = self.record()
        value["exit_code"] = 1
        value["record_sha256"] = oak.record_hash(value)
        result = oak.ledger_gate([value], self.schema(), {"CLM-A"})
        self.assertIn("EVIDENCE_CONTRADICTION", {f.code for f in result.findings})

    def test_append_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            first = self.record()
            for key in ("record_sha256", "previous_record_sha256"):
                first.pop(key)
            first["evidence_id"] = "EVD-1"
            oak.append_record(path, first)
            oak.append_record(path, dict(first, evidence_id="EVD-2"))
            records, errors = oak.load_jsonl([path])
            self.assertEqual([], errors)
            self.assertEqual(records[0]["record_sha256"], records[1]["previous_record_sha256"])


class FreshnessTests(unittest.TestCase):
    def test_stale_does_not_support_claim(self):
        context = {
            "head_sha": "a" * 40,
            "base_sha": "b" * 40,
            "dependency_lock_hash": "c" * 64,
            "test_definition_hash": "d" * 64,
            "environment_hash": "e" * 64,
        }
        record = {
            "evidence_id": "EVD-1", "claim_id": "CLM-A", "kind": "unit_test",
            "status": "pass", **context,
        }
        record["head_sha"] = "f" * 40
        result, passes = oak.freshness_gate(
            [record], [{"id": "CLM-A", "evidence_required": ["unit_test"]}], context
        )
        self.assertTrue(result.blocking)
        self.assertFalse(passes)
        self.assertIn("STALE_EVIDENCE", {f.code for f in result.findings})


class PolicyTests(unittest.TestCase):
    def base_manifest(self):
        return {
            "class": "K",
            "claims": [{"id": "CLM-A", "evidence_required": ["unit_test"]}],
            "capabilities": {"added": [], "removed": [], "forbidden": []},
            "rollback": {"supported": True},
            "self_review": {"required": True},
        }

    def policy(self):
        return {
            "classes": {"D": {"requires": ["review"]}, "K": {"requires": ["unit_test"]}},
            "path_rules": [
                {"pattern": ".github/workflows/**", "minimum_class": "K", "oak_self_review": True}
            ],
            "capabilities": {"forbidden": ["write_repository_contents"]},
        }

    def test_forbidden_capability(self):
        manifest = self.base_manifest()
        manifest["capabilities"]["added"] = ["write_repository_contents"]
        result = oak.policy_gate(manifest, self.policy(), [".github/workflows/x.yml"])
        self.assertIn("POLICY_FORBIDDEN_CAPABILITY", {f.code for f in result.findings})
        self.assertTrue(result.blocking)

    def test_protected_path_class(self):
        manifest = self.base_manifest()
        manifest["class"] = "D"
        result = oak.policy_gate(manifest, self.policy(), [".github/workflows/x.yml"])
        self.assertIn("POLICY_PATH_CLASS_TOO_LOW", {f.code for f in result.findings})


class SchemaTests(unittest.TestCase):
    def test_current_manifest(self):
        manifest = json.loads(Path(".oak/active/pr_233/manifest.json").read_text())
        schema = json.loads(Path(".oak/schemas/pr_manifest.schema.json").read_text())
        errors = list(oak.Draft7Validator(schema).iter_errors(manifest))
        self.assertEqual([], errors)

    def test_current_claims(self):
        manifest = json.loads(Path(".oak/active/pr_233/manifest.json").read_text())
        schema = json.loads(Path(".oak/schemas/claim.schema.json").read_text())
        validator = oak.Draft7Validator(schema)
        errors = [error for claim in manifest["claims"] for error in validator.iter_errors(claim)]
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
