"""Executable deterministic demonstration of Ω-VLA R0.3 Wave 2 MAX."""

from __future__ import annotations

import json

import numpy as np

from omega_vla_t.r03.operators import OperatorExpr
from omega_vla_t.r03.types import MathType
from omega_vla_t.r03.wave2.benchmarks import logical_benchmark_frontier
from omega_vla_t.r03.wave2.campaigns import OperatorCampaignCodec
from omega_vla_t.r03.wave2.commutant import commutant_basis
from omega_vla_t.r03.wave2.egraph import EGraphBudget, saturate
from omega_vla_t.r03.wave2.families import default_family_catalog, materialize_reference
from omega_vla_t.r03.wave2.matrix_functions import matrix_exponential
from omega_vla_t.r03.wave2.properties import infer_properties


def main() -> None:
    catalog = default_family_catalog()
    laplacian = materialize_reference(
        "discrete_geometry.graphs_complexes.combinatorial_laplacian",
        8,
    )
    dense = laplacian.matrix.to_dense()
    properties = infer_properties(dense)
    commutant = commutant_basis(dense)

    operator_type = MathType.linear_operator(8, 8, domain_id="V", codomain_id="V")
    a = OperatorExpr.symbol("A", operator_type)
    identity = OperatorExpr.identity(operator_type)
    saturation = saturate(
        (a.commutator(identity) + (a @ identity)).adjoint().adjoint(),
        budget=EGraphBudget(
            max_rounds=8,
            max_expressions=1024,
            max_total_nodes=50_000,
            max_expression_nodes=256,
        ),
    )
    exponential = matrix_exponential(
        np.array([[0.0, -0.25], [0.25, 0.0]], dtype=np.complex128)
    )
    codec = OperatorCampaignCodec(catalog)
    plan = codec.plan(16, seed=2026, start_offset=0)

    payload = {
        "system": "Ω-VLA-T∞³",
        "version": "R0.3-OMEGA-WAVE-2-MAX",
        "catalog": catalog.summary(),
        "catalog_digest": catalog.digest(),
        "laplacian": {
            "shape": list(dense.shape),
            "nnz": laplacian.matrix.nnz,
            "digest": laplacian.matrix.digest(),
        },
        "supported_properties": sorted(
            value.property_name for value in properties if value.supported is True
        ),
        "commutant": {
            "nullity": commutant.nullity,
            "maximum_residual": commutant.maximum_commutator_residual,
        },
        "rewrite": {
            "expressions_discovered": saturation.expressions_discovered,
            "best_expression": saturation.best_expression.to_dict(),
            "best_cost": saturation.best_cost,
        },
        "matrix_exponential": {
            "method": exponential.method,
            "residual": exponential.residual,
            "passed": exponential.passed,
        },
        "campaign": {
            "logical_frontier_size": codec.size,
            "planned": plan.generated,
            "aggregate_digest": plan.aggregate_digest,
            "first_address": plan.addresses[0].to_dict(),
        },
        "benchmark_frontier": logical_benchmark_frontier(),
        "theorem_claimed": False,
        "formal_proof_claimed": False,
        "scientific_validation_claimed": False,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
