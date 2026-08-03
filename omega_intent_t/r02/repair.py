from __future__ import annotations

from typing import Any

from .models import FailureRecord, RepairAction, stable_digest


_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...], str, bool, bool], ...] = (
    (
        "syntax",
        ("syntaxerror", "parse error", "unexpected indent", "invalid syntax"),
        ("compile_target", "run_formatter", "rerun_focused_test"),
        "normal",
        True,
        False,
    ),
    (
        "import",
        ("modulenotfounderror", "importerror", "cannot import name"),
        ("inspect_dependency_graph", "verify_package_export", "rerun_import_smoke_test"),
        "normal",
        True,
        False,
    ),
    (
        "schema",
        ("validationerror", "schema", "jsonschema"),
        ("validate_schema", "minimize_invalid_fixture", "rerun_schema_contract"),
        "normal",
        True,
        False,
    ),
    (
        "test",
        ("assertionerror", "test failed", "pytest", "expected"),
        ("reproduce_failure", "minimize_fixture", "patch_candidate", "rerun_regression_test"),
        "normal",
        True,
        False,
    ),
    (
        "benchmark",
        ("regression", "slower", "latency", "throughput", "memory"),
        ("reproduce_benchmark", "compare_baseline", "profile_hot_path", "record_tradeoff"),
        "elevated",
        False,
        True,
    ),
    (
        "security",
        ("vulnerability", "secret", "cve", "injection", "unsafe"),
        ("quarantine_output", "perform_security_review", "add_negative_regression_test"),
        "irreversible",
        False,
        True,
    ),
    (
        "ip",
        ("license", "copyright", "patent", "proprietary", "attribution"),
        ("quarantine_output", "run_ip_gate", "resolve_provenance_and_license"),
        "ip_sensitive",
        False,
        True,
    ),
    (
        "resource",
        ("out of memory", "memoryerror", "timeout", "quota", "rate limit", "disk full"),
        ("checkpoint_progress", "reduce_batch", "shard_work", "resume_from_checkpoint"),
        "normal",
        True,
        False,
    ),
)


class RepairPlanner:
    def classify(self, failure: FailureRecord) -> str:
        haystack = " ".join(
            [failure.phase, failure.message, failure.exception_type, *failure.evidence]
        ).lower()
        for category, needles, _, _, _, _ in _RULES:
            if any(needle in haystack for needle in needles):
                return category
        return "unknown"

    def plan(self, failure: FailureRecord) -> RepairAction:
        category = self.classify(failure)
        for rule_category, _, validations, risk, automatic, human_gate in _RULES:
            if category == rule_category:
                break
        else:
            validations = ("reproduce_failure", "collect_more_evidence", "human_triage")
            risk = "elevated"
            automatic = False
            human_gate = True
        identity = {
            "failure_id": failure.failure_id,
            "category": category,
            "validations": validations,
        }
        return RepairAction(
            action_id=f"REPAIR-{stable_digest(identity)[:20].upper()}",
            failure_id=failure.failure_id,
            category=category,
            objective=f"Repair {category} failure for {failure.work_unit_id} without hiding residuals.",
            validations=tuple(validations),
            risk=risk,
            automatic_candidate=automatic,
            human_gate=human_gate,
        )

    def corrective_intent(
        self,
        failure: FailureRecord,
        action: RepairAction,
        *,
        parent_intent_id: str,
    ) -> dict[str, Any]:
        return {
            "schema": "omega-intent-corrective-intent/v2",
            "objective": action.objective,
            "expected_outputs": ["minimal_reproducer", "patch_candidate", "regression_test", "repair_report"],
            "epistemic_constraints": [
                "preserve_failure_evidence",
                "do_not_claim_repair_before_validation",
                "record_rejected_patch_candidates_in_m_minus",
            ],
            "completion_conditions": list(action.validations),
            "mode": "focused",
            "metadata": {
                "parent_intent_id": parent_intent_id,
                "failure": failure.to_dict(),
                "repair_action": action.to_dict(),
            },
        }
