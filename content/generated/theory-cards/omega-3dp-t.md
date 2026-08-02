# Ω-3DP-T — Fabrication additive vérifiable

**Identifiant :** `omega-3dp-t`  
**Version :** `R0.2-public`  
**Maturité :** `architecture`  
**Preuve :** `pré-prototype`

## Résumé

Relie géométrie, matériau, procédé, trajectoire, capteurs, défauts et métrologie dans un jumeau numérique auditable.

## Statut épistémique

Une pièce imprimée n’est pas une pièce qualifiée; essais, tolérances et traçabilité restent indispensables.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- fabrication
- matériaux
- métrologie

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.46 |
| utilite | 0.76 |
| testabilite | 0.77 |
| simplicite | 0.51 |
| valeur | 0.75 |
| protection | 0.62 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-3dp-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-3DP-T propose un cadre structuré pour relie géométrie, matériau, procédé, trajectoire, capteurs, défauts et métrologie dans un jumeau numérique auditable.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-3dp-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-3DP-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-3dp-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-3DP-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Générer des coupons de calibration et mesurer anisotropie, porosité et gauchissement.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.
- `shares_domain` → `omega-bat-t` — Domaine partagé: matériaux
- `shares_domain` → `omega-oem-mtd-t` — Domaine partagé: matériaux
- `shares_domain` → `omega-calib-t` — Domaine partagé: métrologie
- `shares_domain` → `omega-fcryst-t` — Domaine partagé: matériaux

## Relations entrantes


## Risques

- surpromesse
- preuve insuffisante

## Artefacts attendus

- fiche publique
- rapport OAK
- prochaine expérience
- spécification
- schéma
- protocole de test

## Prochaine action

Générer des coupons de calibration et mesurer anisotropie, porosité et gauchissement.

## Provenance

- Source: `docs/theory_cards/OMEGA_3DP_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
