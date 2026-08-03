"""OAK audit for Wave 3 Identity Factory."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .catalog import SCHEMAS, schema_at_dimension, schema_by_id
from .compilers import compile_property_test, compile_smtlib_counterexample
from .dependency import IdentityDependencyGraph
from .factory import instantiate
from .falsify import test_identity
from .frontier import IdentityFrontierCodec
from .models import IdentityAddress


@dataclass(frozen=True)
class OAKCheck:
    name: str
    passed: bool
    measured: Any
    expected: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Wave3OAKReport:
    checks: tuple[OAKCheck, ...]
    status: str
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "checks": [check.to_dict() for check in self.checks],
            "theorem_claimed": self.theorem_claimed,
            "formal_proof_claimed": self.formal_proof_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def audit_wave3(seed: int = 2026) -> Wave3OAKReport:
    checks: list[OAKCheck] = []
    codec = IdentityFrontierCodec()
    checks.append(OAKCheck(
        "catalog_size", len(SCHEMAS) >= 20, len(SCHEMAS), "at least 20 declarative schemas"
    ))
    checks.append(OAKCheck(
        "logical_frontier", codec.size >= 10_000, codec.size, "at least 10,000 reversible candidates"
    ))

    sample = tuple(codec.iter_indices(1024, seed=seed))
    errors = sum(codec.encode(codec.decode(index)) != index for index in sample)
    checks.append(OAKCheck("frontier_roundtrip", errors == 0, errors, "0 codec errors"))
    checks.append(OAKCheck(
        "frontier_uniqueness", len(sample) == len(set(sample)), len(set(sample)),
        "1024 unique deterministic indices",
    ))

    graph = IdentityDependencyGraph(SCHEMAS).audit()
    checks.append(OAKCheck(
        "dependency_graph", graph.valid, graph.to_dict(), "closed acyclic dependency graph"
    ))

    true_address = IdentityAddress(
        "adjoint.product", 3, "complex", "dense", "none", "smoke"
    )
    true_schema, true_instance = instantiate(true_address)
    true_report = test_identity(true_schema, true_instance, seed=seed, trials=8)
    checks.append(OAKCheck(
        "known_identity_fixture", true_report.passed,
        true_report.maximum_relative_residual, "<= 1e-8",
    ))

    weak_address = IdentityAddress(
        "projection.idempotence", 3, "real", "dense", "drop_all", "smoke"
    )
    weak_schema, weak_instance = instantiate(weak_address)
    weak_report = test_identity(weak_schema, weak_instance, seed=seed, trials=8)
    checks.append(OAKCheck(
        "assumption_weakening_falsifies", weak_report.counterexample is not None,
        None if weak_report.counterexample is None else weak_report.counterexample.relative_residual,
        "a concrete counterexample after dropping projection",
    ))

    python_target = compile_property_test(true_schema, true_instance, trials=4, seed=seed)
    smt_schema = schema_at_dimension(schema_by_id("commutator.identity_zero"), 2)
    _, smt_instance = instantiate(IdentityAddress(
        "commutator.identity_zero", 2, "real", "dense", "none", "smoke"
    ))
    smt_target = compile_smtlib_counterexample(smt_schema, smt_instance)
    checks.append(OAKCheck(
        "property_test_target",
        python_target.status == "GENERATED_UNEXECUTED" and not python_target.formally_verified,
        python_target.status,
        "generated but unexecuted and not formally verified",
    ))
    checks.append(OAKCheck(
        "smt_counterexample_target",
        "(check-sat)" in smt_target.source and not smt_target.formal_proof_claimed,
        smt_target.status,
        "finite counterexample target with no proof claim",
    ))

    safe = all(
        not schema.theorem_claimed
        and not schema.formal_proof_claimed
        and not schema.scientific_validation_claimed
        for schema in SCHEMAS
    )
    checks.append(OAKCheck("claim_boundaries", safe, safe, "all generated claim flags false"))

    passed = all(check.passed for check in checks)
    return Wave3OAKReport(
        checks=tuple(checks),
        status=(
            "OAK_PASS_SOFTWARE_RESEARCH_FIXTURES_R0_3_WAVE_3"
            if passed else "OAK_FAIL_SOFTWARE_RESEARCH_FIXTURES_R0_3_WAVE_3"
        ),
    )
