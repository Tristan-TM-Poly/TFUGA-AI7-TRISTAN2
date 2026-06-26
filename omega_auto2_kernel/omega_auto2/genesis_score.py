from __future__ import annotations

RED_LOCK_WORDS = {
    "delete",
    "publish",
    "email",
    "spend",
    "permission",
    "secret",
    "medical_decision",
    "legal_commitment",
}


def score_genesis_idea(name: str, risk_words: list[str] | None = None) -> dict[str, object]:
    risk_words = risk_words or []
    red_locks = sorted(set(risk_words).intersection(RED_LOCK_WORDS))
    base_score = 0.82
    penalty = 0.20 * len(red_locks)
    score = max(0.0, round(base_score - penalty, 3))
    status = "blocked" if red_locks else "draft_ready"
    return {
        "name": name,
        "score": score,
        "status": status,
        "red_locks": red_locks,
        "oak_threshold": 0.75,
    }


def rank_genesis_ideas(names: list[str]) -> list[dict[str, object]]:
    return [score_genesis_idea(name) for name in names]
