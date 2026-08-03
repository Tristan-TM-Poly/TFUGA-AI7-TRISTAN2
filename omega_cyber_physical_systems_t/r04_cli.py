"""Command-line interface for Ω-CPS R0.4 integration receipts."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .integration import (
    IntegrationLedger,
    assess_activation,
    default_adapter_registry,
    execute_connector,
    normalize_exchange,
    probe_capabilities,
)
from .r04_fixtures import (
    invalid_json_loopback_spec,
    missing_executable_spec,
    nonzero_loopback_spec,
    normalized_demo_payloads,
    successful_loopback_spec,
    timeout_loopback_spec,
)
from .r04_oak import run_cps_r04_benchmarks


def _emit(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _negative_spec(case: str):
    return {
        "nonzero": nonzero_loopback_spec,
        "invalid-json": invalid_json_loopback_spec,
        "timeout": timeout_loopback_spec,
        "missing-executable": missing_executable_spec,
    }[case]()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-cps-r04")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("benchmark")
    subparsers.add_parser("capabilities")
    subparsers.add_parser("execute-demo")

    negative = subparsers.add_parser("negative-demo")
    negative.add_argument(
        "--case",
        choices=("nonzero", "invalid-json", "timeout", "missing-executable"),
        default="nonzero",
    )

    normalize = subparsers.add_parser("normalize-demo")
    normalize.add_argument(
        "--adapter",
        choices=("FMI_FMU", "MODELICA", "SPICE", "ROS2", "CAN", "OPCUA", "REFERENCE_LOOPBACK"),
        default="FMI_FMU",
    )

    subparsers.add_parser("ledger-demo")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "benchmark":
        report = run_cps_r04_benchmarks()
        _emit(report.to_dict())
        return 0 if report.passed else 2

    if args.command == "capabilities":
        registry = default_adapter_registry()
        probes = probe_capabilities(registry)
        _emit(
            {
                "registry": [item.to_dict() for item in registry],
                "capabilities": [item.to_dict() for item in probes],
                "available_count": sum(item.available for item in probes),
                "integration_active_count": sum(item.integration_active for item in probes),
                "execution_proven_count": sum(item.execution_proven for item in probes),
                "hardware_validated": False,
                "standards_compliance_claim": False,
            }
        )
        return 0

    if args.command == "execute-demo":
        receipt = execute_connector(successful_loopback_spec())
        _emit(receipt.to_dict())
        return 0 if receipt.success else 2

    if args.command == "negative-demo":
        receipt = execute_connector(_negative_spec(args.case))
        _emit(receipt.to_dict())
        return 0 if not receipt.success and not receipt.integration_active else 2

    if args.command == "normalize-demo":
        payload = normalized_demo_payloads()[args.adapter]
        exchange = normalize_exchange(
            args.adapter,
            payload,
            source_id=f"cli-fixture-{args.adapter.lower()}",
        )
        _emit(exchange.to_dict())
        return 0 if exchange.valid else 2

    if args.command == "ledger-demo":
        registry = default_adapter_registry()
        capabilities = probe_capabilities(registry)
        success = execute_connector(successful_loopback_spec())
        failure = execute_connector(nonzero_loopback_spec())
        exchanges = tuple(
            normalize_exchange(adapter, payload, source_id=f"ledger-fixture-{adapter.lower()}")
            for adapter, payload in normalized_demo_payloads().items()
        )
        activations = (
            assess_activation("REFERENCE_LOOPBACK", success.connector_id, success),
            assess_activation("REFERENCE_LOOPBACK", failure.connector_id, failure),
            assess_activation("OPCUA", "unexecuted-opcua", None),
        )
        ledger = IntegrationLedger(
            registry=registry,
            capabilities=capabilities,
            receipts=(success, failure),
            exchanges=exchanges,
            activations=activations,
        )
        _emit(ledger.to_dict())
        return 0 if ledger.active_connector_count == 1 else 2

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
