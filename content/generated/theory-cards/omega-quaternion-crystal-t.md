# Ω-QUATERNION-CRYSTAL-T — Quaternions, cristaux, déformation et stress

**Identifiant :** `omega-quaternion-crystal-t`  
**Version :** `R0.2-public`  
**Maturité :** `prototype`  
**Preuve :** `noyau 3D testé`

## Résumé

Sépare orientation quaternionique, transformation affine, tenseurs de contrainte/déformation et élasticité.

## Statut épistémique

Rotation, déformation et contrainte sont des objets distincts; les fusionner sans unités crée des erreurs.

Une architecture n’est pas une preuve; un prototype n’est pas un produit validé.

## Domaines

- quaternions
- cristallographie
- mécanique

## Profil OAK provisoire

| Dimension | Signal |
|---|---:|
| verite | 0.62 |
| utilite | 0.84 |
| testabilite | 0.91 |
| simplicite | 0.56 |
| valeur | 0.79 |
| protection | 0.58 |

Les scores servent à naviguer; ils ne sont ni probabilités de vérité ni certifications.

## Claims publics

### claim-omega-quaternion-crystal-t-01 — Portée publique et objet testable

- Type: `scope`
- Statut: `candidate`
- Énoncé: Ω-QUATERNION-CRYSTAL-T propose un cadre structuré pour sépare orientation quaternionique, transformation affine, tenseurs de contrainte/déformation et élasticité.
- Limite: La portée publique ne démontre ni supériorité générale, ni causalité, ni validité hors du domaine déclaré.
- Prochain test: Transformer l’objet en entrée, sortie, baseline, métrique et seuil reproductibles.

### claim-omega-quaternion-crystal-t-02 — Limite OAK obligatoire

- Type: `limit`
- Statut: `guardrail`
- Énoncé: La promotion de Ω-QUATERNION-CRYSTAL-T reste bloquée tant que hypothèses, unités, résidus, risques et contre-exemples ne sont pas exposés.
- Limite: Un garde-fou éditorial réduit la surpromesse mais ne valide pas le modèle sous-jacent.
- Prochain test: Auditer page, dépôt, tests et sources pour détecter une divergence réelle.

### claim-omega-quaternion-crystal-t-03 — Prochaine falsification ou réduction

- Type: `test-plan`
- Statut: `planned`
- Énoncé: La prochaine progression de Ω-QUATERNION-CRYSTAL-T doit produire une comparaison mesurée plutôt qu’une nouvelle extension nominale.
- Limite: Le plan peut échouer, être sous-dimensionné ou mesurer un proxy inadéquat.
- Prochain test: Étendre aux groupes ponctuels, désorientations minimales et champs EBSD avec incertitudes.

## Relations sortantes

- `crystallized_by` → `omega-tristan-self-os` — Traverse capture, canon, OAK, prototype, IP et valeur.
- `documented_by` → `omega-doc-t` — Claims, versions, limites et résidus restent documentés.
- `mapped_by` → `omega-atlas-t` — Coordonnées, provenance, statut, risques et routes restent navigables.
- `uncertainty_guard` → `omega-unc2-t` — Incertitudes, désaccords et domaines de validité restent explicites.
- `published_through` → `omega-web-tristan-t` — La couche publique expose seulement le résumé validé par les quatre gates.

## Relations entrantes


## Risques

- surpromesse
- preuve insuffisante

## Artefacts attendus

- fiche publique
- rapport OAK
- prochaine expérience
- code exécutable
- tests
- benchmark

## Prochaine action

Étendre aux groupes ponctuels, désorientations minimales et champs EBSD avec incertitudes.

## Provenance

- Source: `docs/theory_cards/OMEGA_QUATERNION_CRYSTAL_T.md`
- Mise à jour: `2026-08-02`

## Gates

```text
PUBLIC = OAKGate AND IPGate AND PrivacyGate AND SecurityGate
```

Aucune action externe automatique ou divulgation d’IP n’est autorisée par cette fiche.
