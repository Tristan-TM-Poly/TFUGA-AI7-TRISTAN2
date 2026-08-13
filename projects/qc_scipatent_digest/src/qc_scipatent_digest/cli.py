from __future__ import annotations

import argparse
from pathlib import Path

from .models import DigestDocument
from .pipeline import run_pipeline


def fixture_documents() -> list[DigestDocument]:
    return [
        DigestDocument(
            id="pub-ffwt-battery-poly",
            type="publication",
            title="Multi-scale impedance signatures for lithium-ion battery degradation using wavelet features",
            year=2024,
            source="fixture-openalex-shaped",
            abstract="Wavelet features improve early battery health-state detection from electrochemical impedance signals.",
            authors_or_inventors=["Alexandre Tremblay", "Marie Gagnon"],
            institutions=["Polytechnique Montréal", "Université de Montréal"],
            topics=["battery", "impedance", "wavelet", "signal processing"],
        ),
        DigestDocument(
            id="pat-battery-health-qc",
            type="patent",
            title="Battery health monitoring using multiscale impedance feature extraction",
            year=2021,
            source="fixture-cipo-shaped",
            abstract="A method estimates battery state of health from impedance measurements and multiscale features.",
            authors_or_inventors=["Julie Roy", "Samir Haddad"],
            owners_or_assignees=["Polytechnique Montréal"],
            institutions=["Polytechnique Montréal"],
            topics=["battery", "impedance", "BMS"],
            claims=["measuring impedance", "extracting multiscale features", "battery management system"],
        ),
        DigestDocument(
            id="pub-laser-mems-poly",
            type="publication",
            title="Laser direct writing of micro-optical structures for MEMS sensors",
            year=2023,
            source="fixture-openalex-shaped",
            abstract="Laser direct writing fabricates micro-optical structures for MEMS sensors with improved alignment.",
            authors_or_inventors=["Sofia Nguyen"],
            institutions=["École Polytechnique de Montréal"],
            topics=["laser", "MEMS", "optical sensor", "photonics"],
        ),
        DigestDocument(
            id="pat-laser-mems-qc",
            type="patent",
            title="Laser-assisted fabrication of micro optical sensor arrays",
            year=2020,
            source="fixture-cipo-shaped",
            abstract="Laser fabrication forms aligned micro-optical structures for MEMS sensing arrays.",
            authors_or_inventors=["Nadia Pelletier"],
            owners_or_assignees=["Photonique Québec Inc."],
            institutions=["Photonique Québec Inc."],
            topics=["laser", "MEMS", "optical sensor"],
            claims=["laser direct writing", "micro optical structures", "substrate"],
        ),
        DigestDocument(
            id="pub-public-service-graph-enap",
            type="publication",
            title="Graph-based analysis of digital public service delays in provincial administration",
            year=2022,
            source="fixture-openalex-shaped",
            abstract="Public service delays are modeled as a graph of appointments, forms, requests and administrative decisions.",
            authors_or_inventors=["Camille Beaulieu"],
            institutions=["École nationale d’administration publique", "Québec"],
            topics=["public service", "graph", "administration", "workflow"],
        ),
        DigestDocument(
            id="pat-public-service-graph-qc",
            type="patent",
            title="Secure graph workflow for automated public service triage",
            year=2022,
            source="fixture-cipo-shaped",
            abstract="A workflow routes citizen requests through administrative rules and human review gates.",
            authors_or_inventors=["Louis Martel"],
            owners_or_assignees=["Université du Québec à Montréal"],
            institutions=["Université du Québec à Montréal"],
            topics=["public service", "graph", "workflow", "automation"],
            claims=["rule graph", "audit log", "human validation node"],
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ω-SCI-PATENT-QC-DIGEST-T reusable kernel")
    sub = parser.add_subparsers(dest="cmd", required=True)
    demo = sub.add_parser("plus-ultra", help="Run offline PLUS ULTRA fixture pipeline")
    demo.add_argument("--out", default="outputs/plus_ultra", help="Output directory")
    args = parser.parse_args(argv)
    if args.cmd == "plus-ultra":
        summary = run_pipeline(fixture_documents(), Path(args.out))
        print(f"PLUS ULTRA complete: {summary['documents']} documents, {summary['opportunities']} opportunities, {summary['bridges']} bridges")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
