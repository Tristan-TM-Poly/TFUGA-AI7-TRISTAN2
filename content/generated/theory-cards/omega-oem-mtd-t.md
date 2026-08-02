# Ω-OEMMTD-T — Opto-électro-magnéto-mécano-thermodynamique

**Identifiant :** `omega-oem-mtd-t`  
**Version :** `R0.2-public`  
**Maturité :** `architecture`  
**Preuve :** `réduction aux cas connus`

## Résumé

Couple lumière, champs, charges, déformation, chaleur et transitions de phase dans des modèles multi-physiques.

## Statut épistémique

Toute extension doit respecter unités, conservation, entropie non négative et validation expérimentale.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- physique
- matériaux
- multi-physique

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.48 |
| utilite | 0.81 |
| testabilite | 0.75 |
| simplicite | 0.49 |
| valeur | 0.70 |
| protection | 0.59 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-oem-mtd-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-OEMMTD-T propose un cadre structuré pour couple lumière, champs, charges, déformation, chaleur et transitions de phase dans des modèles multi-physiques.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-oem-mtd-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-OEMMTD-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-oem-mtd-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-OEMMTD-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Implémenter un cas piézoélectrique ou thermoélectrique réduit et comparer à un solveur de référence.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.
- `same_family` → `omega-transform-t` — Famille partagée: science

## Relations entrantes

- `shares_domain` ← `omega-bat-t` — Domaine partagé: matériaux
- `shares_domain` ← `omega-3dp-t` — Domaine partagé: matériaux
- `same_family` ← `omega-lin-t` — Famille partagée: science
- `same_family` ← `omega-chem-log-lin-t` — Famille partagée: science
- `same_family` ← `omega-neg-t` — Famille partagée: science

## Risques

- surpromesse
- preuve insuffisante
- artefact numérique
- généralisation abusive

## Artefacts attendus

- fiche publique
- rapport OAK
- prochaine expérience
- spécification
- schéma
- protocole de test

## Prochaine action

Implémenter un cas piézoélectrique ou thermoélectrique réduit et comparer à un solveur de référence.

## Provenance

- Source: `docs/theory_cards/OMEGA_OEMMTD_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
