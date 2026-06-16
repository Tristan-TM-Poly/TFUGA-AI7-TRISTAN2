#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: Accumulation Cycle

Local zero-deploy accumulation cycle:

1. Omni tensor harvest, offline by default.
2. Science-domain omni harvest across major science families.
3. Canadian/Quebec university research metadata harvest.
4. Science-domain OAK micro-oracle benchmark suite.
5. General HGFM accumulator.
6. Science-domain HGFM accumulator.
7. Canadian research HGFM accumulator.
8. Transversal Invariant Miner (TIM).
9. Auto-genesis report.
10. SAGE dry-run diagnostic.

No publication, no deployment, no external write. Optional live public endpoints can
be enabled only with --live for the smaller omni harvester and --canada-live for
OpenAlex metadata.
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

import canadian_research_hgfm_accumulator
import canadian_university_research_harvester
import genesis_kernel
import hgfm_accumulator
import omni_tensor_harvester
import sage_orchestrator
import science_domain_hgfm_accumulator
import science_domain_oak_benchmark_suite
import science_domain_omni_harvester
import transversal_invariant_miner

REPORT_PATH = ROOT / "reports" / "accumulation" / "accumulation_cycle_report.json"


def main(argv: list[str] | None = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Run local AT-1 accumulation cycle")
    parser.add_argument("--live", action="store_true", help="allow public endpoint reads in omni harvester")
    parser.add_argument("--canada-live", action="store_true", help="allow OpenAlex reads in Canadian research harvester")
    parser.add_argument("--permutation-checks", type=int, default=8)
    parser.add_argument("--science-permutation-checks", type=int, default=4)
    parser.add_argument("--science-oak-permutation-checks", type=int, default=3)
    parser.add_argument("--canada-permutation-checks", type=int, default=3)
    parser.add_argument("--canada-works-per-institution", type=int, default=6)
    parser.add_argument("--canada-priority", choices=["all", "P0", "P1"], default="P0")
    parser.add_argument("--hgfm-threshold", type=float, default=0.82)
    parser.add_argument("--tim-threshold", type=float, default=0.88)
    args = parser.parse_args(argv)

    started = time.time()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    omni_args = ["--permutation-checks", str(args.permutation_checks)]
    if args.live:
        omni_args.append("--live")

    canada_args = [
        "--priority", str(args.canada_priority),
        "--works-per-institution", str(args.canada_works_per_institution),
        "--permutation-checks", str(args.canada_permutation_checks),
    ]
    if args.canada_live:
        canada_args.append("--live")

    omni_report = omni_tensor_harvester.main(omni_args)
    science_report = science_domain_omni_harvester.main(["--permutation-checks", str(args.science_permutation_checks)])
    canada_report = canadian_university_research_harvester.main(canada_args)
    science_oak_report = science_domain_oak_benchmark_suite.main(["--permutation-checks", str(args.science_oak_permutation_checks)])
    hgfm_report = hgfm_accumulator.main(["--threshold", str(args.hgfm_threshold)])
    science_hgfm_report = science_domain_hgfm_accumulator.main(["--threshold", str(args.hgfm_threshold)])
    canada_hgfm_report = canadian_research_hgfm_accumulator.main(["--threshold", str(args.hgfm_threshold)])
    tim_report = transversal_invariant_miner.main(["--threshold", str(args.tim_threshold)])
    genesis_report = genesis_kernel.main()
    sage_code = sage_orchestrator.main(["--dry-run"])

    report = {
        "system": "AT-1 local accumulation cycle",
        "runtime_seconds": time.time() - started,
        "live": bool(args.live),
        "canada_live": bool(args.canada_live),
        "omni_axes": list(omni_report.get("axes", {}).keys()),
        "science_domain_count": int(science_report.get("domain_count", 0)),
        "science_families": sorted({payload.get("family", "unknown") for payload in science_report.get("domains", {}).values()}),
        "canada_research_summary": canada_report.get("summary", {}),
        "science_oak_summary": science_oak_report.get("summary", {}),
        "hgfm_summary": hgfm_report.get("summary", {}),
        "science_hgfm_summary": science_hgfm_report.get("summary", {}),
        "canada_hgfm_summary": canada_hgfm_report.get("summary", {}),
        "transversal_summary": tim_report.get("summary", {}),
        "genesis_summary": genesis_report.get("summary", {}),
        "sage_exit_code": int(sage_code),
        "outputs": {
            "omni": "reports/jkd/omni_harvester_report.json",
            "science": "reports/jkd/science_domain_omni_report.json",
            "canada_research": "reports/canada_research/canadian_university_research_report.json",
            "science_oak": "reports/science_oak/science_oak_benchmark_report.json",
            "hgfm": "reports/hgfm/hgfm_accumulator_report.json",
            "hgfm_m_minus": "reports/hgfm/hgfm_m_minus_compact.json",
            "science_hgfm": "reports/hgfm/science_domain_hgfm_report.json",
            "science_hgfm_m_minus": "reports/hgfm/science_domain_m_minus_compact.json",
            "canada_hgfm": "reports/hgfm/canadian_research_hgfm_report.json",
            "canada_hgfm_m_minus": "reports/hgfm/canadian_research_m_minus_compact.json",
            "transversal": "reports/transversal/transversal_invariants.json",
            "transversal_m_minus": "reports/transversal/transversal_m_minus.json",
            "genesis": "reports/auto_genesis/auto_genesis_report.json",
            "sage": "reports/sage/sage_orchestrator_report.json",
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
