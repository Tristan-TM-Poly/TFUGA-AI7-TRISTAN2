from __future__ import annotations

import json
from pathlib import Path
import tempfile

from .models import OakResult, ValidationReceipt
from .proof import ProofArtifactBuilder
from .router import ImpactRouter
from .scanner import RepoTwinScanner


def _check(check_id: str, passed: bool, evidence: object) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "evidence": evidence}


def run_oakbench() -> OakResult:
    checks: list[dict[str, object]] = []
    warnings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="omega-intent-r03-") as tmp:
        root = Path(tmp)
        (root / "alpha").mkdir()
        (root / "beta").mkdir()
        (root / "tests").mkdir()
        (root / ".github/workflows").mkdir(parents=True)
        (root / "alpha/__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "beta/core.py").write_text("import alpha\nVALUE = alpha.VALUE\n", encoding="utf-8")
        (root / "tests/test_beta.py").write_text("import beta\ndef test_beta(): assert beta is not None\n", encoding="utf-8")
        (root / ".github/workflows/beta.yml").write_text(
            "name: Beta CI\non:\n  pull_request:\n    paths:\n      - 'beta/**'\n      - 'tests/test_beta.py'\nconcurrency:\n  cancel-in-progress: true\n",
            encoding="utf-8",
        )
        scanner = RepoTwinScanner()
        first = scanner.scan(root)
        second = scanner.scan(root)
        checks.append(_check("deterministic_manifest", first.root_digest == second.root_digest, first.root_digest))

        plan = ImpactRouter().route(first, ["alpha/__init__.py"])
        checks.append(_check("reverse_dependency_closure", "beta" in plan.affected_packages, plan.affected_packages))
        checks.append(_check("test_mapping", "tests/test_beta.py" in plan.affected_tests, plan.affected_tests))

        workflow_plan = ImpactRouter().route(first, ["beta/core.py"])
        checks.append(_check("workflow_path_routing", ".github/workflows/beta.yml" in workflow_plan.selected_workflows, workflow_plan.selected_workflows))

        builder = ProofArtifactBuilder()
        artifact = builder.build(
            root / "beta/core.py",
            root=root,
            provenance=("INTENT-OAK-R03",),
            validations=(ValidationReceipt("compile", "passed", "python -m compileall"),),
        )
        before = builder.verify(artifact, root / "beta/core.py")
        (root / "beta/core.py").write_text("import alpha\nVALUE = 99\n", encoding="utf-8")
        after = builder.verify(artifact, root / "beta/core.py")
        checks.append(_check("proof_integrity_before_tamper", before["passed"], before))
        checks.append(_check("proof_detects_tamper", not after["passed"], after))

        global_plan = ImpactRouter().route(first, ["pyproject.toml"])
        checks.append(_check("global_change_escalates", global_plan.full_suite_required, global_plan.to_dict()))
        checks.append(_check("no_remote_mutation_authority", plan.to_dict()["remote_mutations"] == 0, plan.to_dict()))

        encoded = json.dumps(first.to_dict(), sort_keys=True)
        checks.append(_check("manifest_json_serializable", bool(encoded), len(encoded)))
        if any(not rule.has_concurrency_cancellation for rule in first.workflows):
            warnings.append("At least one synthetic workflow lacks cancel-in-progress; CI router reports but does not mutate workflows.")

    return OakResult(
        passed=all(bool(item["passed"]) for item in checks),
        checks=tuple(checks),
        warnings=tuple(warnings),
    )
