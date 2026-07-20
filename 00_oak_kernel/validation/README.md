# OAK PR Cartographer — automatisation

Ce noyau applique le contrat `pr_manifest.json` et le ledger `evidence/pr_<PR>.jsonl`.

## Modes

- **Pull Request** : analyse uniquement la PR courante et échoue sur les blocages structurels, identitaires, de dépendance, de preuve ou de CI déjà constatés.
- **Planifié** : cartographie quotidiennement toutes les PR ouvertes en mode advisory.
- **Manuel** : `workflow_dispatch` produit le registre global sur demande.

## Sorties CI

- `pr_registry.json`
- `pr_registry.md`
- `m_minus.jsonl`

Les sorties sont ajoutées au résumé GitHub Actions et publiées comme artefact immuable.

## Doctrine

Le meilleur verdict automatique est `READY_FOR_HUMAN_REVIEW`. Le système ne fusionne jamais une PR et n'active pas l'auto-merge.
