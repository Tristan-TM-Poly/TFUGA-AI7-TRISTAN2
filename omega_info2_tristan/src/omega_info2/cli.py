"""Command-line interface for Ω-INFO²-T."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .claim_extractor import extract_candidate_claims
from .graph import Info2Graph
from .half_life import freshness_score
from .models import InfoObject, InfoScores, MetaInformation, Provenance, ProvenanceStep, RawObject
from .oak_gate import OAKInfoGate
from .router import route_information
from .source_trust import SourceTrustInput, score_source


def build_info_object_from_text(text: str, source: str | None, domain: str) -> InfoObject:
    source_trust = score_source(
        SourceTrustInput(
            reputation=0.5,
            traceability=0.6 if source else 0.2,
            reproducibility=0.4,
            freshness=0.6,
            independence=0.5,
            opacity=0.2 if source else 0.6,
        )
    )
    obj = InfoObject(
        id="info2_cli_object",
        raw_object=RawObject(type="text", location=source, content_preview=text[:280]),
        claims=extract_candidate_claims(text, domain=domain),
        meta=MetaInformation(source=source, domain=domain),
        provenance=Provenance(
            extraction_tool="omega-info2-cli",
            extraction_version="0.1.0",
            transformations=[ProvenanceStep(operation="read_text", tool="stdlib", confidence=0.95)],
        ),
        scores=InfoScores(
            truth=0.45,
            utility=0.60,
            fertility=0.60,
            novelty=0.50,
            testability=0.70,
            risk=0.30,
            freshness=freshness_score(0, domain="general"),
            source_trust=source_trust,
            compression_gain=0.40,
        ),
    )
    OAKInfoGate().evaluate(obj)
    route_information(obj)
    return obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ω-INFO²-T information-of-information evaluator")
    parser.add_argument("input", nargs="?", help="Text file to evaluate. If omitted, stdin is used.")
    parser.add_argument("--source", default=None, help="Source/provenance label")
    parser.add_argument("--domain", default="general", help="Information domain")
    parser.add_argument("--graph", action="store_true", help="Output Info2Graph instead of InfoObject")
    args = parser.parse_args(argv)

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
        source = args.source or args.input
    else:
        text = sys.stdin.read()
        source = args.source

    obj = build_info_object_from_text(text, source=source, domain=args.domain)
    payload = Info2Graph.from_info_object(obj).to_dict() if args.graph else obj.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
