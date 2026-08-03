from __future__ import annotations

import json
from pathlib import Path
import tempfile

from omega_millennium_t.r03 import audit_output, compile_atlas


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="omega-problem-atlas-") as temp:
        output = Path(temp) / "atlas"
        report = compile_atlas(
            output,
            primary_budget=6,
            secondary_budget=24,
            experiment_budget=64,
        )
        audit = audit_output(output)
        print(json.dumps({"report": report, "audit": audit}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
