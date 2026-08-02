#!/usr/bin/env python3
"""Generate the Ω-COMPANY-AUTOPILOT-T CVCD policy atlas.

The output is synthetic governance-test data. It is not legal advice, a legal
determination, a completed filing, a bank instruction, or authorization to act.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from omega_company_autopilot_t.policy_atlas import DIVISIONS, LAYERS, PROCESSES, RISK_MODES


def codes(prefix: str, values: tuple[str, ...]) -> dict[str, str]:
    width = max(2, len(str(len(values) - 1)))
    return {f"{prefix}{index:0{width}d}": value for index, value in enumerate(values)}


def generate(root: Path) -> dict[str, object]:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    division_codes = codes("d", DIVISIONS)
    process_codes = codes("p", PROCESSES)
    risk_codes = codes("r", RISK_MODES)
    autonomy_codes = {f"l{level}": level for level in range(6)}
    grid = "\n".join(
        f"{risk_code}|{autonomy_code}"
        for risk_code in risk_codes
        for autonomy_code in autonomy_codes
    ) + "\n"

    hashes: dict[str, str] = {}
    for layer in LAYERS:
        for division_code in division_codes:
            folder = root / layer / division_code
            folder.mkdir(parents=True, exist_ok=True)
            for process_code in process_codes:
                path = folder / f"{process_code}.cells"
                path.write_text(grid, encoding="utf-8")
                hashes[str(path.relative_to(root))] = hashlib.sha256(grid.encode("utf-8")).hexdigest()

    files_per_layer = len(DIVISIONS) * len(PROCESSES)
    cells_per_file = len(RISK_MODES) * len(autonomy_codes)
    records_per_layer = files_per_layer * cells_per_file
    manifest = {
        "version": "R0.1-cvcd",
        "status": "synthetic_governance_specification",
        "layers": list(LAYERS),
        "division_codes": division_codes,
        "process_codes": process_codes,
        "risk_codes": risk_codes,
        "autonomy_codes": autonomy_codes,
        "files_per_layer": files_per_layer,
        "cells_per_file": cells_per_file,
        "records_per_layer": records_per_layer,
        "total_files": files_per_layer * len(LAYERS),
        "total_records": records_per_layer * len(LAYERS),
        "external_execution_authorized": False,
        "legal_determination": False,
        "oak_boundary": "Cells are synthetic test specifications, not legal, fiscal, banking, employment, securities, IP-transfer, or government decisions.",
        "content_hashes": hashes,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("generated/omega_company_autopilot_r01_cvcd"))
    args = parser.parse_args()
    manifest = generate(args.root)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
