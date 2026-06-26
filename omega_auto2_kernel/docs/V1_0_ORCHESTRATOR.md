# Ω-AUTO²-Kernel v1.0 — Orchestrator + Human Sovereignty Layer

## Objectif

v1.0 stabilise AUTO² comme orchestrateur local OAK-safe.

## Modules

- `sovereignty.py` : Human Sovereignty Layer et red locks.
- `orchestrator.py` : agrège release pipeline, snapshot, diff et souveraineté.

## CLI

```bash
auto2 orchestrate canonical
auto2 orchestrate canonical --actions local_report dry_run
auto2 orchestrate canonical --actions public_publish
```

## Règle OAK

Le mode v1.0 reste local/draft. Il ne publie rien, ne supprime rien, ne dépense rien, ne change aucune permission et n'envoie aucun message externe.

## Red locks

- `delete_files`
- `public_publish`
- `external_email`
- `spend_money`
- `change_permissions`
- `ip_disclosure`
- `legal_commitment`
- `medical_decision`
- `unsafe_physical_action`

## Statut

Si release pipeline passe et aucun red lock n'est touché, l'orchestrateur produit `release_candidate`. Sinon il produit `blocked`.
