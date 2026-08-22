"""Minimal regenerative constitution (BOOK0-MIN)."""
BOOK0 = (
    "OBSERVE",
    "RESIDUALIZE",
    "GENERATE",
    "TRANSFORM",
    "VERIFY",
    "DISTILL",
    "REGENERATE",
)

INVARIANTS = (
    "Generated != Verified",
    "Generator != Judge",
    "Simulation != Reality",
    "Capability != Authority",
    "Complexity must pay rent",
)

META_STOP_RULE = (
    "Create META^(n+1) only when measured verified capability, regenerability, "
    "transfer or optionality gain exceeds added complexity, risk, debt and compute."
)
