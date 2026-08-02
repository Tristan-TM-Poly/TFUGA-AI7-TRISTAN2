"""Run the complete Ω-REVOLUTION-DIVERSIFICATION-T∞ R0.1 demo."""

from __future__ import annotations

import json
from pathlib import Path

from omega_revolution_diversification_t import (
    RevolutionDiversificationCompiler,
    build_demo_cells,
    canonical_truth_audit_fixture,
)


def main() -> None:
    output = Path("generated/omega_revolution_diversification_r0_1")
    compiled = RevolutionDiversificationCompiler(
        cells=build_demo_cells(),
        repository_snapshots=(canonical_truth_audit_fixture(),),
    ).export(output)
    print(
        json.dumps(
            {
                "output": str(output),
                "metrics": compiled.metrics,
                "manifest_sha256": compiled.manifest["manifest_sha256"],
                "boundary": (
                    "Fixture validation is not independent scientific or market validation."
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
