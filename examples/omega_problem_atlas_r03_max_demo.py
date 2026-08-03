"""Build and strictly audit the Ω-PROBLEM-ATLAS-T∞ R0.3 MAX fixture."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

from omega_millennium_t.r03 import audit_max_output_strict, compile_max_atlas


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="omega-problem-atlas-max-") as directory:
        output = Path(directory)
        report = compile_max_atlas(
            output,
            primary_budget=24,
            secondary_budget=72,
            experiment_budget=256,
        )
        audit = audit_max_output_strict(output)
        print(json.dumps({"report": report, "audit": audit}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
