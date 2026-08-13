from __future__ import annotations

import re
from collections import defaultdict


def normalize_entity(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def cluster_people(names: list[str]) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = defaultdict(list)
    for name in names:
        key = normalize_entity(name).split(" ")[-1] if normalize_entity(name) else "unknown"
        clusters[key].append(name)
    return dict(sorted(clusters.items()))


def entity_warnings(clusters: dict[str, list[str]]) -> list[str]:
    warnings: list[str] = []
    for key, names in clusters.items():
        unique = sorted(set(names))
        if len(unique) > 1:
            warnings.append(f"review_cluster:{key}:{'|'.join(unique)}")
    return warnings
