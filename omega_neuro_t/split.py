from __future__ import annotations

from hashlib import sha256
from typing import Iterable, List, Sequence, Tuple

from .dataset import NeuroObservation


def group_kfold(
    records: Sequence[NeuroObservation],
    *,
    folds: int = 5,
    seed: str = "omega-neuro",
) -> List[Tuple[List[NeuroObservation], List[NeuroObservation]]]:
    """Deterministic group-separated folds to prevent group leakage."""

    if folds < 2:
        raise ValueError("folds must be >= 2")
    groups = sorted({record.group_id for record in records})
    if len(groups) < folds:
        raise ValueError("number of unique groups must be >= folds")

    ordered = sorted(
        groups,
        key=lambda group: sha256(f"{seed}|{group}".encode("utf-8")).hexdigest(),
    )
    assignment = {group: index % folds for index, group in enumerate(ordered)}
    result: List[Tuple[List[NeuroObservation], List[NeuroObservation]]] = []
    for fold in range(folds):
        test = [record for record in records if assignment[record.group_id] == fold]
        train = [record for record in records if assignment[record.group_id] != fold]
        if not train or not test:
            raise RuntimeError("internal split invariant violated")
        train_groups = {record.group_id for record in train}
        test_groups = {record.group_id for record in test}
        if train_groups & test_groups:
            raise RuntimeError("group leakage detected")
        result.append((train, test))
    return result


def split_signature(splits: Iterable[Tuple[Sequence[NeuroObservation], Sequence[NeuroObservation]]]) -> str:
    """Hash the exact held-out sample IDs for reproducibility ledgers."""

    text = "\n".join(
        f"fold={index}:" + ",".join(sorted(record.sample_id for record in test))
        for index, (_, test) in enumerate(splits)
    )
    return sha256(text.encode("utf-8")).hexdigest()
