from __future__ import annotations

import argparse
import json

from .public_sources import public_source_registry
from .r06_protocol import admission_gate, protocol_registry


def build_report(*, hypothesis: str | None = None, source: str | None = None) -> dict:
    report = {
        "stage": "R0.6_PUBLIC_DATA_PREREGISTRATION",
        "sources": public_source_registry(),
        "protocols": protocol_registry(),
        "epistemic_notice": (
            "This report freezes source-selection and evaluation rules before public-data measurement. "
            "It does not contain a biological result and cannot promote a hypothesis automatically."
        ),
        "automatic_biological_promotion": False,
    }
    if hypothesis is not None or source is not None:
        if hypothesis is None or source is None:
            raise ValueError("--hypothesis and --source must be supplied together")
        report["admission_gate"] = dict(admission_gate(hypothesis, source))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Ω-NEURO R0.6 public-data preregistration")
    parser.add_argument("--hypothesis", choices=("P1_DENDRITIC_ADDRESS", "P2_SYNAPTIC_STATE_TENSOR", "P3_HIGHER_ORDER_WIRING"))
    parser.add_argument("--source", choices=("allen_cell_types", "microns_mm3", "dandi_nwb"))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        report = build_report(hypothesis=args.hypothesis, source=args.source)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, sort_keys=True, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
