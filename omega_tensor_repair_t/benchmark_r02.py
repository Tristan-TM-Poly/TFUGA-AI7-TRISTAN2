"""R0.2 benchmark: higher order, SU(2), factorization and hypergraphs."""

from __future__ import annotations

from .clebsch_gordan import su2_clebsch_gordan
from .factorization import low_rank_approximation
from .higher_order import outer_many
from .hypergraph import bundle_hypergraph, tower_hypergraph
from .projectors import analyze_2d
from .symmetry import default_rank2_tower_2d


def run_benchmark_r02() -> dict[str, object]:
    branches = [
        su2_clebsch_gordan(left, right)
        for left in range(1, 9)
        for right in range(1, 9)
    ]
    branch_exact = all(branch.exact for branch in branches)

    tensor = outer_many(((1.0, 2.0), (-1.0, 3.0), (0.5, 4.0)))
    symmetric = tensor.symmetrize()
    antisymmetric = tensor.antisymmetrize()
    symmetric_idempotent = (
        symmetric.subtract(symmetric.symmetrize()).norm_squared() <= 1e-24
    )
    antisymmetric_idempotent = (
        antisymmetric.subtract(antisymmetric.antisymmetrize()).norm_squared() <= 1e-24
    )

    matrix = ((3.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 1.0))
    rank_two = low_rank_approximation(matrix, 2)
    factorization_ok = (
        rank_two.residual_norm <= 1.000000000001
        and rank_two.captured_energy_fraction > 0.92
    )

    bundle_graph = bundle_hypergraph(
        analyze_2d((1.0, 2.0), (3.0, -1.0))
    ).to_dict()
    tower_graph = tower_hypergraph(default_rank2_tower_2d()).to_dict()
    graph_ok = len(bundle_graph["nodes"]) >= 9 and len(tower_graph["hyperedges"]) == 2

    passed = (
        branch_exact
        and symmetric_idempotent
        and antisymmetric_idempotent
        and factorization_ok
        and graph_ok
    )
    return {
        "status": "CERTIFIED_EXTENDED_SOFTWARE_FIXTURES_R0_2" if passed else "REJECTED_R0_2",
        "su2_branches": len(branches),
        "su2_dimension_conservation": branch_exact,
        "higher_order": {
            "rank": tensor.rank,
            "dimension": tensor.dimension,
            "symmetric_idempotent": symmetric_idempotent,
            "antisymmetric_idempotent": antisymmetric_idempotent,
        },
        "factorization": {
            "factor_count": len(rank_two.factors),
            "residual_norm": rank_two.residual_norm,
            "captured_energy_fraction": rank_two.captured_energy_fraction,
            "converged": rank_two.converged,
        },
        "hypergraphs": {
            "bundle_nodes": len(bundle_graph["nodes"]),
            "bundle_edges": len(bundle_graph["hyperedges"]),
            "tower_nodes": len(tower_graph["nodes"]),
            "tower_edges": len(tower_graph["hyperedges"]),
        },
        "claims": {
            "numerical_clebsch_gordan_coefficients_implemented": False,
            "optimal_svd_claimed": False,
            "higher_order_general_proof_claimed": False,
            "finite_extended_fixtures_certified": passed,
        },
    }
