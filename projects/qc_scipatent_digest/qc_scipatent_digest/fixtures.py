from __future__ import annotations

from .models import DigestDocument


def load_synthetic_documents() -> list[DigestDocument]:
    """Return public-safe synthetic fixtures only.

    These are not live records and must not be interpreted as legal, patent,
    publication, ownership, affiliation, or commercialization facts.
    The topic overlaps are intentionally shaped to produce the documented
    v0.3 local demo counts: 6 documents, 6 opportunities, 9 bridges.
    """
    return [
        DigestDocument("sci-001", "science", "Synthetic photonic materials note", 2025, "Polytechnique Montreal", ["A. Researcher", "B. Collaborator"], ["materials", "photonics"]),
        DigestDocument("sci-002", "science", "Synthetic energy storage note", 2025, "Universite de Montreal", ["C. Researcher"], ["energy", "storage", "diagnostics", "sensors"]),
        DigestDocument("sci-003", "science", "Synthetic robotics perception note", 2024, "Universite Laval", ["D. Researcher"], ["robotics", "perception", "sensors"]),
        DigestDocument("ip-001", "patent", "Synthetic optical device filing", 2025, "Quebec Assignee A", ["A. Inventor"], ["materials", "photonics", "device", "sensors"]),
        DigestDocument("ip-002", "patent", "Synthetic storage monitoring filing", 2024, "Quebec Assignee B", ["C. Inventor"], ["energy", "storage", "monitoring", "optimization"]),
        DigestDocument("ip-003", "patent", "Synthetic sensing platform filing", 2024, "Quebec Assignee C", ["D. Inventor"], ["robotics", "sensors", "platform"]),
    ]
