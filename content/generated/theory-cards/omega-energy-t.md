# Ω-ENERGY-T — Systèmes énergétiques de Tristan

**Identifiant :** `omega-energy-t`  
**Version :** `R0.2-public`  
**Maturité :** `architecture`  
**Preuve :** `MVP simulé`

## Résumé

Relie sources, stockage, conversion, réseau, contrôle, pertes, mesure, sécurité et économie dans un microgrid auditable.

## Statut épistémique

L’énergie ne se crée pas; tous rendements, pertes, bilans thermiques et incertitudes doivent être explicités.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- énergie
- contrôle
- simulation

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.42 |
| utilite | 0.84 |
| testabilite | 0.76 |
| simplicite | 0.49 |
| valeur | 0.70 |
| protection | 0.65 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-energy-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-ENERGY-T propose un cadre structuré pour relie sources, stockage, conversion, réseau, contrôle, pertes, mesure, sécurité et économie dans un microgrid auditable.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-energy-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-ENERGY-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-energy-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-ENERGY-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Livrer un microgrid PV–batterie–charge avec bilan énergétique et baselines de contrôle.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.
- `same_family` → `omega-opt-solar-t` — Famille partagée: energy
- `shares_domain` → `omega-lin-t` — Domaine partagé: contrôle
- `shares_domain` → `omega-game-t` — Domaine partagé: simulation
- `shares_domain` → `omega-mail-t` — Domaine partagé: simulation

## Relations entrantes

- `shares_domain` ← `omega-bat-t` — Domaine partagé: contrôle, énergie

## Risques

- surpromesse
- preuve insuffisante
- sécurité physique
- thermique
- rendement non validé

## Artefacts attendus

- fiche publique
- rapport OAK
- prochaine expérience
- spécification
- schéma
- protocole de test

## Prochaine action

Livrer un microgrid PV–batterie–charge avec bilan énergétique et baselines de contrôle.

## Provenance

- Source: `docs/theory_cards/OMEGA_ENERGY_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
