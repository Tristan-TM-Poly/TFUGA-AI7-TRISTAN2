"""Conservative routing gate for electromagnetic-source prototypes."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .classifier import SpectralClassification, classify_frequency
from .models import Mechanism, PROTOTYPE_TIERS, SpectrumTarget

_TIER_INDEX = {name: index for index, name in enumerate(PROTOTYPE_TIERS)}


@dataclass(frozen=True)
class SafetyAssessment:
    status: str
    reasons: tuple[str, ...]
    required_controls: tuple[str, ...]
    required_prototype_tier: str
    local_build_permitted: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _max_tier(left: str, right: str) -> str:
    return PROTOTYPE_TIERS[max(_TIER_INDEX[left], _TIER_INDEX[right])]


def assess_safety(
    target: SpectrumTarget,
    mechanism: Mechanism | None = None,
    classification: SpectralClassification | None = None,
) -> SafetyAssessment:
    """Route a target to simulation, low-power work or regulated facilities.

    This function is deliberately conservative.  It does not certify a device,
    replace a laser/radiation safety officer, or determine legal transmitter
    authorization in a jurisdiction.
    """

    spectral = classification or classify_frequency(target.center_frequency_hz)
    reasons: list[str] = []
    controls: list[str] = [
        "document energy balance and expected emissions",
        "use calibrated detection with an uncertainty budget",
        "perform jurisdiction-specific regulatory review",
    ]
    required_tier = mechanism.minimum_prototype_tier if mechanism else "low_power_benchtop"
    hazards = set(mechanism.hazards if mechanism else ())

    if spectral.region in {"x_ray", "gamma"} or spectral.ionizing_candidate:
        required_tier = "institutional_facility"
        reasons.append("ionizing-capable photon energy or spectral region")
        controls.extend(
            (
                "simulation or licensed institutional facility only",
                "formal radiation protection program, shielding and dosimetry",
                "interlocks, controlled access and qualified supervision",
            )
        )

    institutional_hazards = {
        "radioactive_material",
        "nuclear",
        "accelerator",
        "ionizing_radiation",
        "plasma",
    }
    if hazards & institutional_hazards:
        required_tier = "institutional_facility"
        reasons.append("mechanism includes institutional radiation or accelerator hazards")

    if "high_voltage" in hazards:
        required_tier = _max_tier(required_tier, "certified_module")
        controls.append("use certified enclosed high-voltage equipment and interlocks")
    if "strong_magnetic_field" in hazards:
        required_tier = _max_tier(required_tier, "certified_module")
        controls.append("screen projectile, implant and access hazards")
    if "laser" in hazards:
        required_tier = _max_tier(required_tier, "certified_module")
        controls.extend(
            (
                "use an enclosed certified optical source",
                "classify accessible emission and control specular reflections",
            )
        )
    if "uv_exposure" in hazards or spectral.region == "ultraviolet":
        required_tier = _max_tier(required_tier, "certified_module")
        controls.append("fully enclose UV emission and verify leakage")
    if "chemical" in hazards or "pressurized_gas" in hazards:
        required_tier = _max_tier(required_tier, "certified_module")
        controls.append("obtain chemical and pressure-system review")

    if spectral.region in {"radio", "microwave_and_millimeter", "terahertz_and_submillimeter"}:
        controls.extend(
            (
                "prefer simulation, shielding and a matched dummy load",
                "measure harmonics and unintended emissions",
            )
        )
        if not target.allow_radiating_output:
            reasons.append("radiating output is not explicitly authorized")
        if target.power_w > 1.0:
            required_tier = _max_tier(required_tier, "institutional_facility")
            reasons.append("conservative high-power RF/microwave threshold exceeded")
            controls.append("formal RF exposure and EMC engineering review")

    if target.power_w > 0.005 and "laser" in hazards:
        required_tier = _max_tier(required_tier, "institutional_facility")
        reasons.append("optical power requires formal laser classification and controls")

    allowed_tier = _TIER_INDEX[target.max_prototype_tier]
    needed_tier = _TIER_INDEX[required_tier]
    local_build_permitted = needed_tier <= allowed_tier and required_tier != "institutional_facility"

    if needed_tier > allowed_tier:
        status = "blocked"
        reasons.append(
            f"required tier {required_tier} exceeds allowed tier {target.max_prototype_tier}"
        )
    elif required_tier == "institutional_facility":
        status = "institutional_only"
    elif reasons or required_tier == "certified_module":
        status = "review"
    else:
        status = "pass"

    return SafetyAssessment(
        status=status,
        reasons=tuple(dict.fromkeys(reasons)),
        required_controls=tuple(dict.fromkeys(controls)),
        required_prototype_tier=required_tier,
        local_build_permitted=local_build_permitted,
    )
