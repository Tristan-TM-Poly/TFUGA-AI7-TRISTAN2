from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .graph import DepthGraph
from .registry import CreationRoot, creation_roots


def root_readme(root: CreationRoot) -> str:
    return f"""# {root.name}

- **Identifiant :** `{root.node_id}`
- **Profondeur :** `n = 0`
- **Catégorie :** `{root.category}`
- **Statut OAK initial :** `{root.status.value}`

Cette page est la racine de la décomposition récursive Ω-DEPTH-T∞.

## Contrat de progression

La prochaine étape est de créer les systèmes de profondeur `n = 1`, puis de répéter :

```text
création → systèmes → sous-systèmes → modules → composants
→ opérateurs → fonctions → tests → cas → preuves → résidus
```

La profondeur observée n'est jamais une limite permanente. Une branche s'arrête localement
lorsqu'elle devient suffisamment atomique, testable, interfacée et probatoire.
"""


def scaffold_roots(
    output_dir: str | Path,
    roots: Iterable[CreationRoot] | None = None,
) -> dict[str, int | str]:
    selected = tuple(roots or creation_roots())
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    registry: list[dict[str, object]] = []

    for root in selected:
        directory = output / f"{root.index:02d}_{root.slug}"
        directory.mkdir(parents=True, exist_ok=True)
        node = root.to_node()
        (directory / "node.json").write_text(
            json.dumps(node.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (directory / "README.md").write_text(root_readme(root), encoding="utf-8")
        registry.append(
            {
                "index": root.index,
                "slug": root.slug,
                "id": root.node_id,
                "name": root.name,
                "category": root.category,
                "oak_status": root.status.value,
                "directory": directory.name,
            }
        )

    (output / "root-registry.json").write_text(
        json.dumps(
            {
                "schema_version": "omega-depth-t-root-registry-r0.1",
                "root_count": len(registry),
                "roots": registry,
                "boundary": (
                    "These are depth-zero roots. Their future observed depth is governed "
                    "by evidence and resource budgets, not a permanent fixed maximum."
                ),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"root_count": len(registry), "output_dir": str(output)}


def graph_from_root(root: CreationRoot) -> DepthGraph:
    return DepthGraph((root.to_node(),))
