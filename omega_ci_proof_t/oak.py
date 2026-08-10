from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .autonomy import AutonomyGate
from .claims import ClaimRegistry
from .evidence import EvidenceVerifier
from .ledger import ProofLedger
from .models import EvidenceBundle, ProofPlan


def run_oakbench(
    *,
    registry: ClaimRegistry | None = None,
    plan: ProofPlan | None = None,
    bundle: EvidenceBundle | None = None,
    ledger_path: str | Path | None = None,
) -> Mapping[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, message: str) -> None:
        checks.append({"check_id": check_id, "passed": passed, "message": message})

    gate = AutonomyGate()
    denied = gate.evaluate("A7")
    add("OAK-AUTONOMY-BOUNDARY", not denied.allowed and not denied.automatic_merge_allowed, "A4-A7 and auto-merge are disabled in R0.1")
    if registry is not None:
        ids = [claim.claim_id for claim in registry.all()]
        add("OAK-CLAIM-UNIQUENESS", len(ids) == len(set(ids)), "claim IDs are unique")
    if plan is not None:
        add("OAK-PLAN-DETERMINISM", plan.plan_id.startswith("PROOFPLAN-") and bool(plan.digest), "proof plan is content-addressed")
        add("OAK-PLAN-NO-REMOTE-MUTATION", plan.to_dict()["remote_mutations"] == 0, "proof planning performs no remote mutation")
    if bundle is not None:
        ok, errors = EvidenceVerifier().verify(bundle, required_test_ids=[test.test_id for test in plan.tests] if plan else ())
        add("OAK-EVIDENCE-INTEGRITY", ok, "; ".join(errors) if errors else "evidence bundle integrity verified")
        add("OAK-EVIDENCE-NO-AUTO-MERGE", not bundle.decision.automatic_merge_allowed, "evidence cannot authorize merge in A1-A3")
    if ledger_path is not None:
        ok, errors = ProofLedger(ledger_path).verify()
        add("OAK-LEDGER-CHAIN", ok, "; ".join(errors) if errors else "ledger hash chain verified")
    return {
        "schema": "omega-ci-proof-oak/v1",
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "theorem_claimed": False,
        "scientific_validation_claimed": False,
        "automatic_merge": False,
        "remote_mutations": 0,
    }
