#!/usr/bin/env python3
"""OAK-ServiceMeter for ServiceGraph-QC.

This prototype intentionally uses only the Python standard library. It parses a
small YAML subset used by the examples in this folder and produces an OAK-safe
service maturity report.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


WEIGHTS = {
    "resolution": 25,
    "accessibility": 15,
    "transparency": 15,
    "security": 15,
    "human_recourse": 10,
    "interoperability": 10,
    "cost_control": 10,
}

PENALTY_WEIGHTS = {
    "outage_risk": 10,
    "no_human_channel": 15,
    "no_rollback": 20,
    "no_accessibility_test": 15,
    "opaque_status": 10,
    "vendor_lock_in": 10,
    "repeated_documents": 5,
}

MATURITY = [
    (0, "L0", "papier opaque / service non maîtrisé"),
    (20, "L1", "numérisé superficiellement"),
    (35, "L2", "portail fragmenté"),
    (50, "L3", "parcours mesuré"),
    (65, "L4", "interopérabilité contrôlée"),
    (78, "L5", "omnicanal humain"),
    (88, "L6", "amélioration continue par M⁻"),
    (95, "L7", "proactif, vérifiable et résilient"),
]


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small YAML subset used in servicegraph examples.

    Supported forms:
      key: value
      key:
        - item
      key:
        nested: value

    This is not a general YAML parser; it is deliberately small and transparent
    so the MVP remains stdlib-only.
    """
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_mode: str | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        if indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = parse_scalar(value)
                current_key = None
                current_mode = None
            else:
                data[key] = []
                current_key = key
                current_mode = "unknown"
            continue

        if current_key is None:
            continue

        if line.startswith("- "):
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(parse_scalar(line[2:].strip()))
            current_mode = "list"
            continue

        if ":" in line:
            if current_mode in {"unknown", "map"} and not isinstance(data.get(current_key), dict):
                data[current_key] = {}
            subkey, subvalue = line.split(":", 1)
            data[current_key][subkey.strip()] = parse_scalar(subvalue.strip())
            current_mode = "map"

    return data


def clamp01(value: Any) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, x))


def maturity_level(score: float) -> tuple[str, str]:
    level = MATURITY[0]
    for candidate in MATURITY:
        if score >= candidate[0]:
            level = candidate
    return level[1], level[2]


def score_service(data: dict[str, Any]) -> dict[str, Any]:
    inputs = data.get("metric_inputs", {})
    penalties = data.get("penalties", {})

    positive = 0.0
    dimensions = {}
    for key, weight in WEIGHTS.items():
        value = clamp01(inputs.get(key, 0.0))
        contribution = value * weight
        dimensions[key] = round(contribution, 2)
        positive += contribution

    penalty_total = 0.0
    penalty_details = {}
    for key, weight in PENALTY_WEIGHTS.items():
        value = clamp01(penalties.get(key, 0.0))
        contribution = value * weight
        penalty_details[key] = round(contribution, 2)
        penalty_total += contribution

    score = max(0.0, min(100.0, positive - penalty_total))
    level, label = maturity_level(score)

    return {
        "service_id": data.get("service_id", "unknown"),
        "service_name": data.get("service_name", "unknown"),
        "oak_score": round(score, 2),
        "maturity_level": level,
        "maturity_label": label,
        "positive_points": round(positive, 2),
        "penalty_points": round(penalty_total, 2),
        "dimensions": dimensions,
        "penalties": penalty_details,
    }


def print_report(report: dict[str, Any], data: dict[str, Any]) -> None:
    print(f"# OAK-ServiceMeter — {report['service_name']}")
    print()
    print(f"service_id: {report['service_id']}")
    print(f"oak_score: {report['oak_score']}/100")
    print(f"maturity: {report['maturity_level']} — {report['maturity_label']}")
    print(f"positive_points: {report['positive_points']}")
    print(f"penalty_points: {report['penalty_points']}")
    print()
    print("## Dimensions")
    for key, value in report["dimensions"].items():
        print(f"- {key}: {value}")
    print()
    print("## Pénalités")
    for key, value in report["penalties"].items():
        if value:
            print(f"- {key}: -{value}")
    print()
    print("## Prochaines actions OAK")
    tests = data.get("oak_tests", [])
    if tests:
        for item in tests[:8]:
            print(f"- valider: {item}")
    else:
        print("- ajouter des tests OAK avant toute conclusion")
    print()
    print("## Rappel OAK-safe")
    print("Ce score est un outil de diagnostic, pas une vérité administrative ni une décision publique.")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python servicegraph_qc/oak_service_meter.py <service.yaml>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    data = parse_simple_yaml(path)
    report = score_service(data)
    print_report(report, data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
