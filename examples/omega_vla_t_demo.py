"""Small Ω-VLA-T∞ R0.1 demonstration."""

import json

import numpy as np

from omega_vla_t import (
    LinearOperator,
    VectorSpace,
    audit_operator,
    graph_hodge_decomposition,
)


def main() -> None:
    metric = np.array([[2.0, 0.2], [0.2, 1.0]])
    space = VectorSpace(2, metric=metric, name="MeasuredState")
    operator = LinearOperator(
        np.array([[2.0, 1.0], [-0.5, 3.0]]),
        space,
        space,
        name="TristanOperatorFixture",
    )

    incidence = np.array(
        [
            [-1.0, 0.0, 1.0],
            [1.0, -1.0, 0.0],
            [0.0, 1.0, -1.0],
        ]
    )
    hodge = graph_hodge_decomposition(incidence, np.array([1.0, 2.0, 4.0]))

    payload = {
        "svd": operator.svd_report().to_dict(),
        "oak": audit_operator(operator, seed=17).to_dict(),
        "hodge": hodge.to_dict(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
