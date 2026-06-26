# Ω-AUTO²-Kernel v0.9 — Local Release Pipeline

## Objectif

v0.9 ajoute un pipeline local de release qui regroupe les vérifications déjà présentes.

## Pipeline

```text
quality-gate → compare → snapshot → diff → release report
```

## Module

- `release.py`
  - `quality_gate(version)`
  - `release_pipeline(version, baseline)`
  - `release_markdown(version, baseline)`

## CLI

```bash
auto2 release-check canonical
auto2 release-check canonical --format json
auto2 release-check canonical --against fixtures/v0_7_canonical_snapshot.json
```

## OAK

Le pipeline ne publie rien, ne pousse rien et ne modifie aucun fichier. Il produit uniquement un rapport local Markdown ou JSON.

## Prochaine étape

v1.0 pourra stabiliser l'orchestrateur AUTO² avec Human Sovereignty Layer et un mode release candidate.
