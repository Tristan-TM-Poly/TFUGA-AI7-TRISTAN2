import json

from omega_vla_t.r03.wave3 import (
    IdentityAddress, IdentityDependencyGraph, IdentityFrontierCodec,
    SCHEMAS, instantiate, schema_at_dimension, schema_by_id, test_identity,
)


def test_catalog_dependency_graph_and_frontier_roundtrip():
    assert len(SCHEMAS) >= 20
    graph = IdentityDependencyGraph(SCHEMAS)
    assert graph.audit().valid
    assert len(graph.topological_order()) == len(SCHEMAS)

    codec = IdentityFrontierCodec()
    assert codec.size > 10_000
    indices = tuple(codec.iter_indices(2048, seed=19))
    assert len(indices) == len(set(indices))
    assert all(codec.encode(codec.decode(index)) == index for index in indices)


def test_known_identities_are_numerically_supported():
    cases = [
        IdentityAddress("adjoint.product", 4, "complex", "dense", "none", "smoke"),
        IdentityAddress("commutator.leibniz_right", 3, "real", "dense", "none", "smoke"),
        IdentityAddress("tensor.mixed_product", 2, "complex", "dense", "none", "smoke"),
        IdentityAddress("unitary.inverse_adjoint", 4, "complex", "unitary", "none", "smoke"),
    ]
    for address in cases:
        schema, instance = instantiate(address)
        report = test_identity(schema, instance, seed=7, trials=6)
        assert report.passed, report.to_dict()
        assert report.theorem_claimed is False


def test_assumption_weakening_emits_minimized_counterexample():
    address = IdentityAddress(
        "projection.idempotence", 3, "real", "dense", "drop_all", "smoke"
    )
    schema, instance = instantiate(address)
    report = test_identity(schema, instance, seed=3, trials=8)
    assert not report.passed
    assert report.counterexample is not None
    assert report.counterexample.relative_residual > 1e-8
    assert report.counterexample.counterexample_id.startswith("mminus-")


def test_schema_digest_is_deterministic():
    first = schema_at_dimension(schema_by_id("adjoint.sum"), 5)
    second = schema_at_dimension(schema_by_id("adjoint.sum"), 5)
    assert first.digest() == second.digest()
    json.loads(first.canonical_json())
