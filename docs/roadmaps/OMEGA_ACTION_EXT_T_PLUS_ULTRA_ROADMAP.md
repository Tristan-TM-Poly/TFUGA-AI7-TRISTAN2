# Ω-ACTION-EXT-T — Plus Ultra Roadmap

Cette roadmap transforme le MVP en système nerveux moteur externe OAK-safe.

## Phase 0 — Canon et noyau local

- ActionDNA
- RiskTensor
- OAKGate
- DryRunReport
- ActionManifest hashé
- ApprovalQueue locale
- ProofLedger JSONL append-only
- M⁻ Incident Codex
- OAKBench heuristique
- Connecteurs dry-run-only

## Phase 1 — Manifests complets

Ajouter un standard `action_manifest.schema.json` couvrant :

- intention ;
- cible ;
- système ;
- permissions ;
- scopes ;
- risques ;
- dry-run ;
- approbations ;
- rollback ;
- preuve attendue ;
- résidu observé ;
- M⁺/M⁻.

## Phase 2 — Connecteurs dry-run-first

Adapters prévus :

- GitHub : branche, fichier, issue, PR draft ;
- Gmail : brouillon seulement par défaut ;
- Calendar : événement brouillon/proposition ;
- Drive : fichier/manifest privé ;
- Local files : artefacts et rapports.

Aucun connecteur ne doit exécuter sans :

```text
manifest_hash + approval_state + policy_recheck + proof_ledger
```

## Phase 3 — Approval UI / Queue

Créer une file souveraine :

```text
approve | edit | reject | delay | require_ip_review | require_expert | convert_to_draft
```

## Phase 4 — OAKBench Action

Mesurer :

- succès intentionnel ;
- faux allow dangereux ;
- faux block excessif ;
- résidu ;
- temps sauvé ;
- rollback réussi ;
- incidents évités ;
- coût humain ;
- preuve produite.

## Phase 5 — Revenue Actuator prudent

Transformer opportunités en :

- brouillons d'offres ;
- pages produit privées ;
- CRM local ;
- follow-up drafts ;
- devis brouillons ;
- rapports de valeur.

Règle : aucun envoi commercial massif, paiement, contrat ou promesse publique sans approbation explicite.

## Phase 6 — Action Marketplace

Chaque workflow validé devient un ActionPack réutilisable :

- Professor Outreach ActionPack ;
- Patent Draft ActionPack ;
- Grant Application ActionPack ;
- GitHub Prototype Release ActionPack ;
- Calibration Certificate ActionPack ;
- Scientific Digest ActionPack.

## Règle finale

```text
Plus l'action touche humains, argent, droit, santé, sécurité, réputation, IP, public ou permissions,
plus elle exige simulation, approbation, preuve, rollback/compensation et M⁻.
```
