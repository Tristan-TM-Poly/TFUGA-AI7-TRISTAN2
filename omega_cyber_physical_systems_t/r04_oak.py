"""OAKBench for Ω-CPS R0.4 external adapter receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .integration import (
    ADAPTER_TYPES,
    EXTERNAL_ADAPTER_TYPES,
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


@dataclass(frozen=True)
class CPSR04OAKGate:
    gate_id: str
    passed: bool
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "passed": self.passed,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class CPSR04OAKReport:
    gates: tuple[CPSR04OAKGate, ...]
    ledger: IntegrationLedger
    status: str
    passed: bool
    physics_certified: bool = False
    hardware_validated: bool = False
    safety_certified: bool = False
    standards_compliance_claim: bool = False
    live_external_connection_proven: bool = False
    permanent_total_cap: None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "gates": [gate.to_dict() for gate in self.gates],
            "ledger": self.ledger.to_dict(),
            "status": self.status,
            "passed": self.passed,
            "physics_certified": self.physics_certified,
            "hardware_validated": self.hardware_validated,
            "safety_certified": self.safety_certified,
            "standards_compliance_claim": self.standards_compliance_claim,
            "live_external_connection_proven": self.live_external_connection_proven,
            "permanent_total_cap": self.permanent_total_cap,
        }


def run_cps_r04_benchmarks() -> CPSR04OAKReport:
    registry = default_adapter_registry()
    capabilities = probe_capabilities(registry)

    success_a = execute_connector(successful_loopback_spec())
    success_b = execute_connector(successful_loopback_spec())
    nonzero = execute_connector(nonzero_loopback_spec())
    invalid = execute_connector(invalid_json_loopback_spec())
    timeout = execute_connector(timeout_loopback_spec())
    missing = execute_connector(missing_executable_spec())
    receipts = (success_a, nonzero, invalid, timeout, missing)

    payloads = normalized_demo_payloads()
    exchanges = tuple(
        normalize_exchange(
            adapter_type,
            payload,
            source_id=f"fixture-{adapter_type.lower()}",
            source_execution_receipt_hash=(
                success_a.evidence_hash if adapter_type == "REFERENCE_LOOPBACK" else None
            ),
        )
        for adapter_type, payload in payloads.items()
    )

    activations = (
        assess_activation("REFERENCE_LOOPBACK", success_a.connector_id, success_a),
        assess_activation("REFERENCE_LOOPBACK", nonzero.connector_id, nonzero),
        assess_activation("FMI_FMU", "fixture-fmi", None),
    )
    ledger = IntegrationLedger(
        registry=registry,
        capabilities=capabilities,
        receipts=receipts,
        exchanges=exchanges,
        activations=activations,
    )

    gates = (
        CPSR04OAKGate(
            "adapter_registry_complete",
            tuple(item.adapter_type for item in registry) == ADAPTER_TYPES,
            {"adapter_types": list(ADAPTER_TYPES)},
        ),
        CPSR04OAKGate(
            "capability_probe_never_activates",
            all(not item.integration_active and not item.execution_proven for item in capabilities),
            {
                "available_count": sum(item.available for item in capabilities),
                "active_count": sum(item.integration_active for item in capabilities),
            },
        ),
        CPSR04OAKGate(
            "real_subprocess_receipt_success",
            success_a.success
            and success_a.process_started
            and success_a.exit_code == 0
            and success_a.output_valid
            and success_a.integration_active,
            {
                "status": success_a.status,
                "exit_code": success_a.exit_code,
                "evidence_hash": success_a.evidence_hash,
            },
        ),
        CPSR04OAKGate(
            "semantic_receipt_deterministic",
            success_a.evidence_hash == success_b.evidence_hash,
            {
                "first": success_a.evidence_hash,
                "second": success_b.evidence_hash,
            },
        ),
        CPSR04OAKGate(
            "nonzero_exit_blocked",
            not nonzero.success and not nonzero.integration_active and nonzero.status == "NONZERO_EXIT",
            {"status": nonzero.status, "exit_code": nonzero.exit_code},
        ),
        CPSR04OAKGate(
            "invalid_json_blocked",
            not invalid.success and not invalid.integration_active and invalid.status == "INVALID_JSON",
            {"status": invalid.status},
        ),
        CPSR04OAKGate(
            "timeout_blocked",
            not timeout.success and timeout.timed_out and timeout.status == "TIMEOUT",
            {"status": timeout.status, "timed_out": timeout.timed_out},
        ),
        CPSR04OAKGate(
            "missing_executable_blocked",
            not missing.success
            and not missing.process_started
            and missing.status == "EXECUTABLE_NOT_FOUND",
            {"status": missing.status},
        ),
        CPSR04OAKGate(
            "all_exchange_contracts_normalized",
            len(exchanges) == len(ADAPTER_TYPES)
            and all(item.valid for item in exchanges)
            and {item.adapter_type for item in exchanges} == set(ADAPTER_TYPES),
            {
                "exchange_count": len(exchanges),
                "valid_count": sum(item.valid for item in exchanges),
            },
        ),
        CPSR04OAKGate(
            "external_replay_not_live",
            all(
                item.replay_only and not item.live_connection_claim
                for item in exchanges
                if item.adapter_type in EXTERNAL_ADAPTER_TYPES
            ),
            {
                "external_exchange_count": sum(
                    item.adapter_type in EXTERNAL_ADAPTER_TYPES for item in exchanges
                )
            },
        ),
        CPSR04OAKGate(
            "activation_requires_matching_success_receipt",
            activations[0].active
            and not activations[1].active
            and not activations[2].active,
            {"activations": [item.to_dict() for item in activations]},
        ),
        CPSR04OAKGate(
            "epistemic_boundaries_explicit",
            not ledger.physics_certified
            and not ledger.hardware_validated
            and not ledger.safety_certified
            and not ledger.standards_compliance_claim
            and all(not item.hardware_validated for item in receipts)
            and all(not item.standards_compliance_claim for item in receipts),
            {
                "physics_certified": ledger.physics_certified,
                "hardware_validated": ledger.hardware_validated,
                "safety_certified": ledger.safety_certified,
                "standards_compliance_claim": ledger.standards_compliance_claim,
            },
        ),
        CPSR04OAKGate(
            "no_permanent_total_cap",
            ledger.permanent_total_cap is None
            and all(item.permanent_total_cap is None for item in receipts),
            {"permanent_total_cap": ledger.permanent_total_cap},
        ),
    )
    passed = all(gate.passed for gate in gates)
    return CPSR04OAKReport(
        gates=gates,
        ledger=ledger,
        status=(
            "CERTIFIED_COMPUTATIONAL_EXTERNAL_ADAPTER_RECEIPTS_R0_4"
            if passed
            else "FAILED_COMPUTATIONAL_EXTERNAL_ADAPTER_RECEIPTS_R0_4"
        ),
        passed=passed,
    )
