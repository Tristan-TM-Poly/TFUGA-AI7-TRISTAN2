from __future__ import annotations


def build_blueprints() -> list[dict]:
    return [
        {
            "name": "Digest API Kernel",
            "purpose": "Expose the pipeline as a reusable local/service kernel.",
            "inputs": ["verified document records", "verified patent records"],
            "outputs": ["opportunity queue", "OAK report", "canon cards"],
            "oak_locks": ["no live data without source policy", "no public claim without OAK-IP"],
        },
        {
            "name": "Quebec Science-IP Atlas",
            "purpose": "Map public research and IP signals into reviewable opportunity clusters.",
            "inputs": ["institution metadata", "publication metadata", "patent metadata"],
            "outputs": ["atlas pages", "review queue", "bridge graph"],
            "oak_locks": ["no legal conclusion", "no confidential invention disclosure"],
        },
        {
            "name": "OAK Research Assistant",
            "purpose": "Convert digest outputs into questions, checks, and next actions.",
            "inputs": ["opportunities", "release assessment"],
            "outputs": ["questions", "risk flags", "next build plan"],
            "oak_locks": ["human review for IP/legal/commercial steps"],
        },
    ]
