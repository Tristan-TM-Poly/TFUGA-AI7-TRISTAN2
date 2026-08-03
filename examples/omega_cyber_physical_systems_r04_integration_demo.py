from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from omega_cyber_physical_systems_t.integration import (  # noqa: E402
    IntegrationLedger,
    assess_activation,
    default_adapter_registry,
    execute_connector,
    normalize_exchange,
    probe_capabilities,
)
from omega_cyber_physical_systems_t.r04_fixtures import (  # noqa: E402
    invalid_json_loopback_spec,
    missing_executable_spec,
    nonzero_loopback_spec,
    normalized_demo_payloads,
    successful_loopback_spec,
    timeout_loopback_spec,
)
from omega_cyber_physical_systems_t.r04_oak import run_cps_r04_benchmarks  # noqa: E402


def main() -> int:
    registry = default_adapter_registry()
    capabilities = probe_capabilities(registry)
    success = execute_connector(successful_loopback_spec())
    failures = (
        execute_connector(nonzero_loopback_spec()),
        execute_connector(invalid_json_loopback_spec()),
        execute_connector(timeout_loopback_spec()),
        execute_connector(missing_executable_spec()),
    )
    exchanges = tuple(
        normalize_exchange(
            adapter_type,
            payload,
            source_id=f"example-{adapter_type.lower()}",
            source_execution_receipt_hash=(
                success.evidence_hash if adapter_type == "REFERENCE_LOOPBACK" else None
            ),
        )
        for adapter_type, payload in normalized_demo_payloads().items()
    )
    activations = (
        assess_activation("REFERENCE_LOOPBACK", success.connector_id, success),
        *(assess_activation("REFERENCE_LOOPBACK", item.connector_id, item) for item in failures),
        assess_activation("FMI_FMU", "unexecuted-fmi", None),
    )
    ledger = IntegrationLedger(
        registry=registry,
        capabilities=capabilities,
        receipts=(success, *failures),
        exchanges=exchanges,
        activations=activations,
    )
    oak = run_cps_r04_benchmarks()
    payload = {
        "registry_count": len(registry),
        "external_adapter_count": 6,
        "capability_available_count": sum(item.available for item in capabilities),
        "capability_active_count": sum(item.integration_active for item in capabilities),
        "successful_receipt": success.to_dict(),
        "negative_statuses": [item.status for item in failures],
        "valid_exchange_count": ledger.valid_exchange_count,
        "active_connector_count": ledger.active_connector_count,
        "failed_receipt_count": ledger.failed_receipt_count,
        "ledger_hash": ledger.evidence_hash,
        "oak": {
            "status": oak.status,
            "passed": oak.passed,
            "gate_count": len(oak.gates),
            "live_external_connection_proven": oak.live_external_connection_proven,
            "hardware_validated": oak.hardware_validated,
            "standards_compliance_claim": oak.standards_compliance_claim,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if oak.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
