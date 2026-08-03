from __future__ import annotations

import json

from omega_tensor_repair_t import analyze_2d, audit_bundle, compile_spec


bundle = analyze_2d((1.0, 2.0), (3.0, -1.0))
print(json.dumps({"bundle": bundle.to_dict(), "oak": audit_bundle(bundle).to_dict()}, indent=2))

plan = compile_spec(
    {
        "left_dimension": 3,
        "right_dimension": 3,
        "preserve_inputs": True,
        "exact_reconstruction": True,
        "channels": [
            "full",
            "carrier",
            "symmetric",
            "symmetric_traceless",
            "trace",
            "antisymmetric",
            "blocks",
            "residual",
        ],
    }
)
print(json.dumps(plan.to_dict(), indent=2))
