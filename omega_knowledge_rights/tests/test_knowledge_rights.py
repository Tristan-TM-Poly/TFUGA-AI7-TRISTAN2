import copy
import unittest

from omega_knowledge_rights.knowledge_rights import (
    PolicyError,
    Request,
    evaluate,
    make_disclosure_receipt,
)


def genome():
    return {
        "asset_id": "asset-001",
        "policy_version": "0.2-test",
        "origin": "authorized-test",
        "custodian": "research-team",
        "classification": "CONFIDENTIAL",
        "privacy_status": "no-personal-data",
        "ip_status": "unresolved-test",
        "publication_status": "not-public",
        "allowed_purposes": ["technical-evaluation"],
        "allowed_operations": ["READ", "BENCHMARK"],
        "forbidden_operations": ["PUBLISH", "EXPORT", "TRAIN"],
        "expires_at": "2026-12-31T23:59:59Z",
        "release_triggers": [],
        "protected_disclosure_kernel": {
            "enabled": True,
            "contexts": ["legally-required", "protected-reporting"],
        },
        "evidence_refs": ["test-evidence"],
        "rules": [],
    }


def request(operation="READ", purpose="technical-evaluation", **kwargs):
    values = {
        "actor": "reviewer@example.org",
        "asset_id": "asset-001",
        "purpose": purpose,
        "operation": operation,
        "timestamp": "2026-08-19T12:00:00Z",
        "context": "standard",
    }
    values.update(kwargs)
    return Request(**values)


class KnowledgeRightsCourt(unittest.TestCase):
    def test_explicit_read_is_allowed(self):
        decision = evaluate(genome(), request("READ"))
        self.assertEqual(decision.outcome, "ALLOW")

    def test_read_never_implies_ai_training(self):
        decision = evaluate(genome(), request("TRAIN"))
        self.assertEqual(decision.outcome, "DENY")
        self.assertIn("operation_explicitly_forbidden", decision.reasons)

    def test_unlisted_operation_fails_closed(self):
        g = genome()
        g["forbidden_operations"].remove("EXPORT")
        decision = evaluate(g, request("EXPORT"))
        self.assertEqual(decision.outcome, "DENY")
        self.assertIn("operation_not_explicitly_allowed", decision.reasons)

    def test_wrong_purpose_fails_closed(self):
        decision = evaluate(genome(), request("READ", purpose="marketing"))
        self.assertEqual(decision.outcome, "DENY")
        self.assertIn("purpose_not_explicitly_allowed", decision.reasons)

    def test_expired_permission_denied(self):
        decision = evaluate(
            genome(),
            request("READ", timestamp="2027-01-01T00:00:00Z"),
        )
        self.assertEqual(decision.outcome, "DENY")
        self.assertIn("permission_expired", decision.reasons)

    def test_protected_disclosure_escalates_not_suppresses(self):
        decision = evaluate(
            genome(),
            request("READ", context="protected-reporting"),
        )
        self.assertEqual(decision.outcome, "ESCALATE")
        self.assertIn("qualified_review_required", decision.reasons)

    def test_scoped_deny_overrides_base_allow(self):
        g = genome()
        g["rules"] = [
            {
                "rule_id": "deny-reviewer-read",
                "effect": "DENY",
                "actors": ["reviewer@example.org"],
                "purposes": ["technical-evaluation"],
                "operations": ["READ"],
            }
        ]
        decision = evaluate(g, request("READ"))
        self.assertEqual(decision.outcome, "DENY")
        self.assertIn("scoped_rule_denies", decision.reasons)

    def test_conflicting_scoped_rules_fail_closed(self):
        g = genome()
        g["rules"] = [
            {
                "rule_id": "allow-a",
                "effect": "ALLOW",
                "actors": ["reviewer@example.org"],
                "purposes": ["technical-evaluation"],
                "operations": ["READ"],
            },
            {
                "rule_id": "deny-b",
                "effect": "DENY",
                "actors": ["reviewer@example.org"],
                "purposes": ["technical-evaluation"],
                "operations": ["READ"],
            },
        ]
        decision = evaluate(g, request("READ"))
        self.assertEqual(decision.outcome, "DENY")
        self.assertEqual(
            decision.conflict_rule_ids,
            ("allow-a", "deny-b"),
        )

    def test_base_policy_direct_conflict_is_invalid(self):
        g = genome()
        g["allowed_operations"].append("TRAIN")
        with self.assertRaises(PolicyError):
            evaluate(g, request("READ"))

    def test_receipt_is_hash_stable_with_fixed_time(self):
        payload = {"files": ["summary.md"], "version": 1}
        receipt_a = make_disclosure_receipt(
            genome(), request("READ"), payload, decided_at="2026-08-19T12:01:00Z"
        )
        receipt_b = make_disclosure_receipt(
            genome(), request("READ"), copy.deepcopy(payload), decided_at="2026-08-19T12:01:00Z"
        )
        self.assertEqual(receipt_a["receipt_sha256"], receipt_b["receipt_sha256"])
        self.assertEqual(len(receipt_a["manifest_sha256"]), 64)

    def test_non_allow_cannot_emit_disclosure_receipt(self):
        with self.assertRaises(PolicyError):
            make_disclosure_receipt(
                genome(), request("PUBLISH"), {"files": ["secret.txt"]},
                decided_at="2026-08-19T12:01:00Z",
            )


if __name__ == "__main__":
    unittest.main()
