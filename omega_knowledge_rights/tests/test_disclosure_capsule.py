import unittest

from omega_knowledge_rights.disclosure_capsule import (
    DisclosureCapsuleError,
    assess_cumulative_reconstruction,
    compile_capsule,
    compile_capsule_with_reconstruction_gate,
)
from omega_knowledge_rights.knowledge_rights import Request


class DisclosureCapsuleCourt(unittest.TestCase):
    def setUp(self):
        self.genome = {
            "asset_id": "asset-1",
            "policy_version": "0.3-test",
            "origin": "test",
            "custodian": "owner",
            "classification": "CONFIDENTIAL",
            "privacy_status": "NO_SPECIAL_CATEGORY",
            "ip_status": "UNASSESSED",
            "publication_status": "PRIVATE",
            "allowed_purposes": ["research", "supplier_eval"],
            "allowed_operations": ["READ"],
            "forbidden_operations": ["EXPORT", "PUBLISH", "TRAIN"],
            "release_triggers": [],
            "protected_disclosure_kernel": {"enabled": True, "contexts": ["lawful_report"]},
            "evidence_refs": [],
        }
        self.request = Request(
            actor="researcher-a",
            asset_id="asset-1",
            purpose="research",
            operation="READ",
            timestamp="2026-08-19T12:00:00Z",
        )
        self.source = {
            "summary": "public-safe summary",
            "method": "bounded method",
            "secret_equation": "E=private",
            "private_contact": "private@example.invalid",
        }
        self.spec = {
            "capsule_id": "research-r1",
            "asset_id": "asset-1",
            "operation": "READ",
            "actors": ["researcher-a"],
            "purposes": ["research"],
            "include_fields": ["summary", "method"],
            "required_fields": ["summary"],
            "exclude_fields": ["secret_equation", "private_contact"],
        }

    def test_allowlist_projection_omits_everything_else(self):
        result = compile_capsule(self.genome, self.request, self.source, self.spec)
        self.assertEqual(result["payload"], {"summary": "public-safe summary", "method": "bounded method"})
        self.assertEqual(result["manifest"]["disclosed_fields"], ["method", "summary"])
        self.assertEqual(result["manifest"]["omitted_fields"], ["private_contact", "secret_equation"])
        self.assertFalse(result["manifest"]["semantic_redaction_claimed"])

    def test_denied_policy_cannot_compile_capsule(self):
        denied = Request(
            actor="researcher-a", asset_id="asset-1", purpose="research",
            operation="EXPORT", timestamp="2026-08-19T12:00:00Z",
        )
        with self.assertRaisesRegex(DisclosureCapsuleError, "decision: DENY"):
            compile_capsule(self.genome, denied, self.source, {**self.spec, "operation": "EXPORT"})

    def test_actor_scope_fails_closed(self):
        other = Request(
            actor="researcher-b", asset_id="asset-1", purpose="research",
            operation="READ", timestamp="2026-08-19T12:00:00Z",
        )
        with self.assertRaisesRegex(DisclosureCapsuleError, "actor_not_allowed"):
            compile_capsule(self.genome, other, self.source, self.spec)

    def test_required_source_field_must_exist(self):
        with self.assertRaisesRegex(DisclosureCapsuleError, "missing required source fields"):
            compile_capsule(self.genome, self.request, {"method": "x"}, self.spec)

    def test_include_exclude_conflict_is_rejected(self):
        bad = {**self.spec, "exclude_fields": ["summary"]}
        with self.assertRaisesRegex(DisclosureCapsuleError, "conflicts"):
            compile_capsule(self.genome, self.request, self.source, bad)

    def test_cumulative_reconstruction_detects_newly_triggered_rule(self):
        history = [{"disclosed_fields": ["secret_part_a"]}]
        candidate = {"disclosed_fields": ["secret_part_b"]}
        rules = [{"rule_id": "reconstruct-secret", "required_fields": ["secret_part_a", "secret_part_b"]}]
        result = assess_cumulative_reconstruction(history, candidate, rules)
        self.assertFalse(result["safe_to_add"])
        self.assertEqual(result["newly_triggered_rule_ids"], ["reconstruct-secret"])

    def test_safe_candidate_remains_safe(self):
        history = [{"disclosed_fields": ["secret_part_a"]}]
        candidate = {"disclosed_fields": ["summary"]}
        rules = [{"rule_id": "reconstruct-secret", "required_fields": ["secret_part_a", "secret_part_b"]}]
        result = assess_cumulative_reconstruction(history, candidate, rules)
        self.assertTrue(result["safe_to_add"])
        self.assertEqual(result["newly_triggered_rule_ids"], [])

    def test_preexisting_risk_is_not_misattributed_to_candidate(self):
        history = [{"disclosed_fields": ["a", "b"]}]
        candidate = {"disclosed_fields": ["summary"]}
        rules = [{"rule_id": "already", "required_fields": ["a", "b"]}]
        result = assess_cumulative_reconstruction(history, candidate, rules)
        self.assertTrue(result["safe_to_add"])
        self.assertEqual(result["already_triggered_rule_ids"], ["already"])
        self.assertEqual(result["newly_triggered_rule_ids"], [])

    def test_reconstruction_gate_blocks_candidate(self):
        risky_spec = {**self.spec, "include_fields": ["summary", "secret_equation"], "exclude_fields": []}
        history = [{"disclosed_fields": ["method"]}]
        rules = [{"rule_id": "method-plus-equation", "required_fields": ["method", "secret_equation"]}]
        with self.assertRaisesRegex(DisclosureCapsuleError, "cumulative_reconstruction_risk"):
            compile_capsule_with_reconstruction_gate(
                self.genome, self.request, self.source, risky_spec,
                history_manifests=history, reconstruction_rules=rules,
            )

    def test_reconstruction_assessment_is_order_independent_for_field_sets(self):
        rules = [{"rule_id": "r", "required_fields": ["a", "b"]}]
        left = assess_cumulative_reconstruction(
            [{"disclosed_fields": ["a"]}], {"disclosed_fields": ["b", "c"]}, rules
        )
        right = assess_cumulative_reconstruction(
            [{"disclosed_fields": ["a"]}], {"disclosed_fields": ["c", "b"]}, rules
        )
        self.assertEqual(left, right)

    def test_duplicate_rule_ids_are_rejected(self):
        rules = [
            {"rule_id": "dup", "required_fields": ["a"]},
            {"rule_id": "dup", "required_fields": ["b"]},
        ]
        with self.assertRaisesRegex(DisclosureCapsuleError, "duplicate reconstruction rule"):
            assess_cumulative_reconstruction([], {"disclosed_fields": ["a"]}, rules)


if __name__ == "__main__":
    unittest.main()
