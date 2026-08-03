"""Deterministic Ω-VLA Wave 3 demonstration."""
import json
from omega_vla_t.r03.wave3 import (
    IdentityAddress, IdentityFrontierCodec, audit_wave3, instantiate, test_identity,
)

true_address = IdentityAddress(
    "adjoint.product", 4, "complex", "dense", "none", "standard"
)
true_schema, true_instance = instantiate(true_address)
true_report = test_identity(true_schema, true_instance, seed=2026, trials=16)

weak_address = IdentityAddress(
    "projection.idempotence", 3, "real", "dense", "drop_all", "standard"
)
weak_schema, weak_instance = instantiate(weak_address)
weak_report = test_identity(weak_schema, weak_instance, seed=2026, trials=16)

codec = IdentityFrontierCodec()
payload = {
    "frontier": codec.manifest().to_dict(),
    "supported_identity": true_report.to_dict(),
    "weakened_identity": weak_report.to_dict(),
    "oak": audit_wave3().to_dict(),
    "theorem_claimed": False,
    "formal_proof_claimed": False,
    "scientific_validation_claimed": False,
}
print(json.dumps(payload, indent=2, sort_keys=True))
