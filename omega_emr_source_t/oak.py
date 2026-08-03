"""OAK validation for electromagnetic-source plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import SourcePlan


@dataclass(frozen=True)
class OAKCheck:
    check_id: str
    passed: bool
    severity: str
    evidence: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OAKReport:
    status: str
    checks: tuple[OAKCheck, ...]
    residual_risks: tuple[str, ...]
    next_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "checks": [check.to_dict() for check in self.checks],
            "residual_risks": list(self.residual_risks),
            "next_actions": list(self.next_actions),
        }


def audit_plan(plan: SourcePlan) -> OAKReport:
    viable = plan.recommended or plan.conditional
    checks = (
        OAKCheck(
            "target_well_formed",
            plan.target.center_frequency_hz > 0 and plan.target.power_w > 0,
            "error",
            "positive frequency and input power requirements",
        ),
        OAKCheck(
            "mechanism_identified",
            bool(viable),
            "error",
            f"{len(plan.recommended)} recommended and {len(plan.conditional)} conditional candidates",
        ),
        OAKCheck(
            "safety_routed",
            plan.safety_status not in {"blocked"},
            "error",
            f"SafetyGate status: {plan.safety_status}",
        ),
        OAKCheck(
            "measurement_plan_present",
            len(plan.metrology_plan) >= 4,
            "error",
            f"{len(plan.metrology_plan)} metrology actions",
        ),
        OAKCheck(
            "out_of_band_measurement",
            any("out-of-band" in item for item in plan.metrology_plan),
            "warning",
            "harmonic and parasitic emission verification",
        ),
        OAKCheck(
            "epistemic_status_explicit",
            "pending" in plan.epistemic_status,
            "warning",
            plan.epistemic_status,
        ),
        OAKCheck(
            "energy_conservation_assumption",
            any("Energy conservation" in item for item in plan.assumptions),
            "error",
            "source plan retains an explicit energy-balance constraint",
        ),
    )

    failed_errors = [
        check for check in checks if not check.passed and check.severity == "error"
    ]
    failed_warnings = [
        check for check in checks if not check.passed and check.severity == "warning"
    ]
    if failed_errors:
        status = "blocked"
    elif plan.safety_status in {"review", "institutional_only"} or failed_warnings:
        status = "review"
    else:
        status = "pass"

    residual = list(plan.safety_reasons)
    residual.extend(
        (
            "device-level efficiency and thermal behavior are not yet simulated",
            "atlas envelopes do not replace material and component data",
            "legal spectrum access and exposure limits are jurisdiction-dependent",
        )
    )
    next_actions = [
        "simulate the highest-ranked mechanism against a conventional baseline",
        "define detector calibration and uncertainty budgets before prototyping",
        "record predicted useful power, losses, heat and parasitic emissions",
    ]
    if plan.safety_status in {"blocked", "institutional_only"}:
        next_actions.insert(
            0,
            "keep the branch simulation-only or transfer it to an authorized facility",
        )
    elif plan.safety_status == "review":
        next_actions.insert(0, "complete the listed safety and regulatory reviews")

    return OAKReport(
        status=status,
        checks=checks,
        residual_risks=tuple(dict.fromkeys(residual)),
        next_actions=tuple(dict.fromkeys(next_actions)),
    )
