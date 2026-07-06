"""OAK claim style helper."""

EARLY_STATUS = {"A", "B", "C"}


def claim_mode(status: str) -> str:
    if status in EARLY_STATUS:
        return "hypothesis"
    if status in {"D", "E"}:
        return "tested"
    if status in {"F", "G"}:
        return "strong"
    return "unknown"


def safer_claim(status: str, text: str) -> str:
    mode = claim_mode(status)
    if mode == "hypothesis":
        return "Hypothesis: " + text
    if mode == "tested":
        return "Tested claim: " + text
    if mode == "strong":
        return "Strong claim: " + text
    return "Unclassified claim: " + text
