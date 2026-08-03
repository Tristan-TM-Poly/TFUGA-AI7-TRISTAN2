from __future__ import annotations

from pathlib import PurePosixPath
from typing import Iterable

from .models import ArtifactSpec, IntentContract, sha256_digest


_KIND_PATHS = {
    "theory": "docs/theory.md",
    "system_graph": "generated/system-graph.json",
    "documentation": "README.md",
    "code": "src/kernel.py",
    "tests": "tests/test_kernel.py",
    "benchmark": "benchmarks/oakbench.py",
    "evidence": "evidence/evidence-bundle.json",
    "oak_report": "reports/oak-report.json",
    "product_hypothesis": "docs/product-card.md",
    "ip_report": "reports/ip-gate.json",
    "simulation": "simulations/reference.py",
    "schema": "schemas/contract.schema.json",
    "workflow": ".github/workflows/oakbench.yml",
}


class ArtifactCompiler:
    """Compile desired outputs into reviewable artifact specifications.

    R0.1 produces contracts and scaffold addresses, not claims that arbitrary
    implementations are complete or scientifically valid.
    """

    def compile(self, intent: IntentContract) -> tuple[ArtifactSpec, ...]:
        artifacts: list[ArtifactSpec] = []
        creation_slug = intent.root_creation.replace("_", "-")
        for position, kind in enumerate(intent.expected_outputs, start=1):
            relative = _KIND_PATHS.get(kind, f"generated/{kind}.json")
            path = str(PurePosixPath("generated") / "omega_mycelium_campaigns" / creation_slug / relative)
            artifact_id = f"artifact.{intent.intent_id}.{position:02d}.{kind}"
            private = kind in {"ip_report"}
            review = kind in {"product_hypothesis", "evidence"}
            required_visibility = "private_required" if private else ("review_required" if review else "public_safe")
            risk = "medium" if kind in {"ip_report", "product_hypothesis", "workflow"} else "low"
            dependencies: tuple[str, ...] = ()
            if kind == "tests":
                dependencies = tuple(item.artifact_id for item in artifacts if item.kind == "code")
            elif kind == "benchmark":
                dependencies = tuple(item.artifact_id for item in artifacts if item.kind in {"code", "tests"})
            elif kind in {"evidence", "oak_report"}:
                dependencies = tuple(item.artifact_id for item in artifacts if item.kind in {"tests", "benchmark"})
            elif kind == "product_hypothesis":
                dependencies = tuple(item.artifact_id for item in artifacts if item.kind == "oak_report")
            description = f"{kind} artifact planned for {intent.objective}"
            artifacts.append(
                ArtifactSpec(
                    artifact_id=artifact_id,
                    creation_id=intent.root_creation.replace("-", "_"),
                    kind=kind,
                    suggested_path=path,
                    description=description,
                    dependencies=dependencies,
                    required_visibility=required_visibility,
                    risk_level=risk,
                    generated_status="contract_only",
                    content_digest=sha256_digest(
                        {
                            "artifact_id": artifact_id,
                            "kind": kind,
                            "path": path,
                            "objective": intent.objective,
                        }
                    ),
                    metadata={
                        "implementation_complete": False,
                        "scientific_validation_claimed": False,
                    },
                )
            )
        return tuple(artifacts)


def artifact_dependency_map(artifacts: Iterable[ArtifactSpec]) -> dict[str, tuple[str, ...]]:
    return {artifact.artifact_id: artifact.dependencies for artifact in artifacts}
