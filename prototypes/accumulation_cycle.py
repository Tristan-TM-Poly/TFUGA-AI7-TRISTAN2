#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Accumulation Cycle

Local zero-deploy accumulation cycle:

1. Omni tensor harvest, offline by default.
2. Science-domain omni harvest across major science families.
3. General HGFM accumulator.
4. Science-domain HGFM accumulator.
5. Auto-genesis report.
6. SAGE dry-run diagnostic.

No publication, no deployment, no external write. Optional live public endpoints can
be enabled only with --live for the smaller omni harvester.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT / "core", ROOT / "prototypes"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import genesis_kernel
import hgfm_accumulator
import omni_tensor_harvester
import sage_orchestrator
import science_domain_hgfm_accumulator
import science_domain_omni_harvester

REPORT_PATH = ROOT / "reports" / "accumulation" / "accumulation_cycle_report.json"


def main(argv: list[str] | None = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Run local AT-1 accumulation cycle")
    parser.add_argument("--live", action="store_true", help="allow public endpoint reads in omni harvester")
    parser.add_argument("--permutation-checks", type=int, default=8)
    parser.add_argument("--science-permutation-checks", type=int, default=4)
    parser.add_argument("--hgfm-threshold", type=float, default=0.82)
    args = parser.parse_args(argv)

    started = time.time()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    omni_args = ["--permutation-checks", str(args.permutation_checks)]
    if args.live:
        omni_args.append("--live")

    omni_report = omni_tensor_harvester.main(omni_args)
    science_report = science_domain_omni_harvester.main(["--permutation-checks", str(args.science_permutation_checks)])
    hgfm_report = hgfm_accumulator.main(["--threshold", str(args.hgfm_threshold)])
    science_hgfm_report = science_domain_hgfm_accumulator.main(["--threshold", str(args.hgfm_threshold)])
    genesis_report = genesis_kernel.main()
    sage_code = sage_orchestrator.main(["--dry-run"])

    report = {
        "system": "AT-1 local accumulation cycle",
        "runtime_seconds": time.time() - started,
        "live": bool(args.live),
        "omni_axes": list(omni_report.get("axes", {}).keys()),
        "science_domain_count": int(science_report.get("domain_count", 0)),
        "science_families": sorted({payload.get("family", "unknown") for payload in science_report.get("domains", {}).values()}),
        "hgfm_summary": hgfm_report.get("summary", {}),
        "science_hgfm_summary": science_hgfm_report.get("summary", {}),
        "genesis_summary": genesis_report.get("summary", {}),
        "sage_exit_code": int(sage_code),
        "outputs": {
            "omni": "reports/jkd/omni_harvester_report.json",
            "science": "reports/jkd/science_domain_omni_report.json",
            "hgfm": "reports/hgfm/hgfm_accumulator_report.json",
            "hgfm_m_minus": "reports/hgfm/hgfm_m_minus_compact.json",
            "science_hgfm": "reports/hgfm/science_domain_hgfm_report.json",
            "science_hgfm_m_minus": "reports/hgfm/science_domain_m_minus_compact.json",
            "genesis": "reports/auto_genesis/auto_genesis_report.json",
            "sage": "reports/sage/sage_orchestrator_report.json",
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
